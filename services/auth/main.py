"""
Auth Service - Port 8004
Handles authentication, authorization, and user management.
Issues JWT tokens for API access.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import asyncpg
import os

app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service",
    version="1.0.0"
)

security = HTTPBearer(auto_error=False)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/doctor_doom"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "operator"


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class User(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: str
    is_active: bool = True


# Database pool
db_pool: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(settings.DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    async with db_pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = true",
            user_id
        )
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(**dict(user_row))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/v1/auth/register", response_model=User)
async def register(user: UserCreate):
    """Register a new user."""
    async with db_pool.acquire() as conn:
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", user.email
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_id = f"usr_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        hashed_password = get_password_hash(user.password)
        
        await conn.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, role, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id, user.email, hashed_password, user.full_name, user.role, datetime.utcnow().isoformat()
        )
        
        return User(
            id=user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            created_at=datetime.utcnow().isoformat(),
            is_active=True
        )


@app.post("/api/v1/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT tokens."""
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1 AND is_active = true",
            credentials.email
        )
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"], "role": user["role"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user["id"], "type": "refresh"}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = true",
            user_id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        new_access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"], "role": user["role"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token = create_refresh_token(
            data={"sub": user["id"], "type": "refresh"}
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )


@app.get("/api/v1/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@app.put("/api/v1/auth/me")
async def update_user(
    full_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile."""
    async with db_pool.acquire() as conn:
        if full_name:
            await conn.execute(
                "UPDATE users SET full_name = $1 WHERE id = $2",
                full_name, current_user.id
            )
        
        updated = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", current_user.id
        )
        return User(**dict(updated))


@app.post("/api/v1/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (invalidate token - requires token blacklist)."""
    # Placeholder - implement token blacklist with Redis
    return {"status": "logged_out"}


# Admin endpoints
@app.get("/api/v1/auth/users")
async def list_users(current_user: User = Depends(get_current_user)):
    """List all users (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, email, full_name, role, created_at, is_active FROM users"
        )
        return [dict(r) for r in rows]


@app.put("/api/v1/auth/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate a user (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = false WHERE id = $1", user_id
        )
        return {"status": "deactivated", "user_id": user_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
