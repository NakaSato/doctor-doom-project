"""
ML Model Management Utilities
=============================

Model loading, downloading, and version management for the ML pipeline.
"""
import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model metadata and version information."""
    name: str
    version: str
    stage: int
    format: str  # onnx, coreml, pytorch
    size_mb: float
    sha256: str
    created_at: str
    metrics: Dict
    description: str
    download_url: Optional[str] = None


@dataclass
class ModelRegistry:
    """Registry of available models."""
    models: List[ModelInfo]
    default_versions: Dict[int, str]  # stage -> version


class ModelManager:
    """
    Manage ML model lifecycle: download, load, version tracking.
    
    Supports:
    - Local model storage
    - Model versioning
    - Integrity verification (SHA256)
    - Multiple formats (ONNX, CoreML, PyTorch)
    """
    
    def __init__(self, model_dir: str = "/app/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry_path = self.model_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> ModelRegistry:
        """Load model registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                return ModelRegistry(
                    models=[ModelInfo(**m) for m in data['models']],
                    default_versions=data.get('default_versions', {})
                )
        
        # Initialize empty registry
        return ModelRegistry(models=[], default_versions={})
    
    def _save_registry(self):
        """Save model registry to disk."""
        data = {
            'models': [asdict(m) for m in self.registry.models],
            'default_versions': self.registry.default_versions
        }
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_model(self, model_info: ModelInfo):
        """
        Register a new model in the registry.
        
        Args:
            model_info: Model metadata
        """
        # Check if version already exists
        for i, existing in enumerate(self.registry.models):
            if (existing.name == model_info.name and 
                existing.version == model_info.version):
                logger.warning(f"Model {model_info.name} v{model_info.version} already exists")
                self.registry.models[i] = model_info
                break
        else:
            self.registry.models.append(model_info)
        
        # Set as default if first model for this stage
        if model_info.stage not in self.registry.default_versions:
            self.registry.default_versions[model_info.stage] = model_info.version
        
        self._save_registry()
        logger.info(f"Registered model: {model_info.name} v{model_info.version}")
    
    def get_model_path(self, stage: int, version: Optional[str] = None) -> Optional[Path]:
        """
        Get path to model file.
        
        Args:
            stage: Pipeline stage (1-4)
            version: Model version (uses default if None)
        
        Returns:
            Path to model file or None if not found
        """
        if version is None:
            version = self.registry.default_versions.get(stage)
        
        if version is None:
            return None
        
        # Search for model
        for model in self.registry.models:
            if model.stage == stage and model.version == version:
                model_path = self.model_dir / f"stage{stage}" / f"model.{model.format}"
                if model_path.exists():
                    return model_path
        
        return None
    
    def verify_model_integrity(self, model_path: Path, expected_sha256: str) -> bool:
        """
        Verify model file integrity using SHA256.
        
        Args:
            model_path: Path to model file
            expected_sha256: Expected SHA256 hash
        
        Returns:
            True if integrity verified
        """
        if not model_path.exists():
            return False
        
        sha256_hash = hashlib.sha256()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        computed_hash = sha256_hash.hexdigest()
        return computed_hash == expected_sha256
    
    def list_models(self) -> List[ModelInfo]:
        """List all registered models."""
        return self.registry.models
    
    def get_default_model(self, stage: int) -> Optional[ModelInfo]:
        """Get default model for a stage."""
        version = self.registry.default_versions.get(stage)
        if version is None:
            return None
        
        for model in self.registry.models:
            if model.stage == stage and model.version == version:
                return model
        return None


class ModelDownloader:
    """
    Download models from remote storage (S3, HTTP, etc.).
    
    Supports:
    - S3 (AWS)
    - HTTP/HTTPS
    - Local file system
    """
    
    def __init__(self, cache_dir: str = "/app/models/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_from_s3(
        self,
        s3_uri: str,
        output_path: Path,
        aws_profile: Optional[str] = None
    ) -> Path:
        """
        Download model from S3.
        
        Args:
            s3_uri: S3 URI (s3://bucket/path/to/model)
            output_path: Local output path
            aws_profile: AWS profile name (optional)
        
        Returns:
            Path to downloaded file
        """
        try:
            import boto3
            from botocore.config import Config
            
            # Parse S3 URI
            parts = s3_uri.replace('s3://', '').split('/')
            bucket_name = parts[0]
            key = '/'.join(parts[1:])
            
            # Create S3 client
            session_kwargs = {}
            if aws_profile:
                session_kwargs['profile_name'] = aws_profile
            
            session = boto3.Session(**session_kwargs)
            s3_client = session.client('s3', config=Config(
                retries={'max_attempts': 3}
            ))
            
            # Download
            logger.info(f"Downloading {s3_uri} to {output_path}")
            s3_client.download_file(bucket_name, key, str(output_path))
            
            logger.info(f"Downloaded {output_path.stat().st_size / 1e6:.2f} MB")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            raise
    
    def download_from_http(self, url: str, output_path: Path) -> Path:
        """
        Download model from HTTP/HTTPS URL.
        
        Args:
            url: Download URL
            output_path: Local output path
        
        Returns:
            Path to downloaded file
        """
        import requests
        from tqdm import tqdm
        
        logger.info(f"Downloading {url} to {output_path}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Downloaded {output_path.stat().st_size / 1e6:.2f} MB")
        return output_path
    
    def copy_from_local(self, source_path: Path, output_path: Path) -> Path:
        """
        Copy model from local path.
        
        Args:
            source_path: Source file path
            output_path: Destination path
        
        Returns:
            Path to copied file
        """
        logger.info(f"Copying {source_path} to {output_path}")
        shutil.copy2(source_path, output_path)
        return output_path


def setup_models(model_dir: str = "/app/models") -> Dict[int, str]:
    """
    Setup all models for the ML pipeline.
    
    Creates directory structure and downloads/initializes models.
    
    Args:
        model_dir: Base model directory
    
    Returns:
        Dictionary mapping stage to model path
    """
    manager = ModelManager(model_dir)
    
    # Check if models already exist
    model_paths = {}
    for stage in range(1, 5):
        path = manager.get_model_path(stage)
        if path and path.exists():
            model_paths[stage] = str(path)
            logger.info(f"Stage {stage}: Found existing model at {path}")
        else:
            logger.warning(f"Stage {stage}: No model found. Please download or train models.")
    
    # If no models found, create placeholder structure
    if not model_paths:
        logger.info("Creating model directory structure...")
        
        for stage in range(1, 5):
            stage_dir = Path(model_dir) / f"stage{stage}"
            stage_dir.mkdir(parents=True, exist_ok=True)
            
            # Create placeholder info file
            info_file = stage_dir / "model_info.json"
            info = {
                'stage': stage,
                'status': 'missing',
                'message': 'Model not found. Please download or train.',
                'expected_formats': ['onnx', 'coreml']
            }
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
    
    return model_paths


def compute_model_hash(model_path: Path) -> str:
    """
    Compute SHA256 hash of model file.
    
    Args:
        model_path: Path to model file
    
    Returns:
        SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(model_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def export_model_info(
    name: str,
    version: str,
    stage: int,
    format: str,
    model_path: Path,
    metrics: Dict,
    description: str
) -> ModelInfo:
    """
    Create ModelInfo from trained model.
    
    Args:
        name: Model name
        version: Version string
        stage: Pipeline stage (1-4)
        format: Model format (onnx, coreml, pytorch)
        model_path: Path to model file
        metrics: Performance metrics
        description: Model description
    
    Returns:
        ModelInfo object
    """
    size_mb = model_path.stat().st_size / 1e6
    sha256 = compute_model_hash(model_path)
    
    return ModelInfo(
        name=name,
        version=version,
        stage=stage,
        format=format,
        size_mb=round(size_mb, 2),
        sha256=sha256,
        created_at=datetime.now().isoformat(),
        metrics=metrics,
        description=description
    )


# Example usage
if __name__ == "__main__":
    # Initialize model manager
    manager = ModelManager("/app/models")
    
    # List all models
    print("Registered models:")
    for model in manager.list_models():
        print(f"  {model.name} v{model.version} (stage {model.stage})")
    
    # Get default model for stage 1
    stage1_model = manager.get_default_model(1)
    if stage1_model:
        print(f"\nStage 1 default: {stage1_model.name} v{stage1_model.version}")
        print(f"  Format: {stage1_model.format}")
        print(f"  Size: {stage1_model.size_mb} MB")
        print(f"  Metrics: {stage1_model.metrics}")
