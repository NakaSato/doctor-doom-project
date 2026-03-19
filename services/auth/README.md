# Auth Service

**Port:** 8004

Handles authentication, authorization, and user management.

## Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Token refresh mechanism
- User management

## Endpoints

### Public
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### Protected
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update profile
- `POST /api/v1/auth/logout` - Logout

### Admin
- `GET /api/v1/auth/users` - List all users
- `PUT /api/v1/auth/users/{id}/deactivate` - Deactivate user

## Roles

- `operator` - Basic access
- `admin` - User management
- `super_admin` - Full access

## Security

- Password hashing: bcrypt
- JWT algorithm: HS256
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days

**Important:** Change `JWT_SECRET_KEY` in production!
