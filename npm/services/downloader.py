"""Package download service."""
import logging
import tarfile
from pathlib import Path
from typing import Optional
import requests
from npm.config import get_config
from npm.utils.http import get_session

logger = logging.getLogger(__name__)


class PackageDownloader:
    """Service for downloading NPM packages."""
    
    def __init__(self, download_dir: Optional[Path] = None):
        """Initialize downloader.
        
        Args:
            download_dir: Directory for downloads (uses config if None).
        """
        if download_dir is None:
            config = get_config()
            download_dir = config.download_dir
        
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.registry_url = get_config().npm_registry_url
    
    def download_package(
        self,
        name: str,
        version: str = "latest",
        extract: bool = True
    ) -> Path:
        """Download an NPM package.
        
        Args:
            name: Package name.
            version: Package version.
            extract: Whether to extract the tarball.
            
        Returns:
            Path to downloaded/extracted package.
            
        Raises:
            Exception: If download fails.
        """
        logger.info(f"Downloading {name}@{version}")
        
        # Get package metadata
        session = get_session()
        metadata_url = f"{self.registry_url}/{name}"
        response = session.get(metadata_url)
        response.raise_for_status()
        metadata = response.json()
        
        # Resolve version
        if version == "latest":
            version = metadata["dist-tags"]["latest"]
        
        # Get tarball URL
        version_data = metadata["versions"].get(version)
        if not version_data:
            raise ValueError(f"Version {version} not found")
        
        tarball_url = version_data["dist"]["tarball"]
        
        # Download tarball
        package_dir = self.download_dir / name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        tarball_path = package_dir / f"{name}-{version}.tgz"
        
        logger.info(f"Downloading from {tarball_url}")
        response = session.get(tarball_url, stream=True)
        response.raise_for_status()
        
        # Save tarball
        with open(tarball_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded to {tarball_path}")
        
        # Extract if requested
        if extract:
            extract_dir = package_dir / version
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(tarball_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            logger.info(f"Extracted to {extract_dir}")
            return extract_dir
        
        return tarball_path
    
    def get_download_size(self, name: str, version: str = "latest") -> int:
        """Get download size without downloading.
        
        Args:
            name: Package name.
            version: Package version.
            
        Returns:
            Size in bytes.
        """
        session = get_session()
        metadata_url = f"{self.registry_url}/{name}"
        response = session.get(metadata_url)
        response.raise_for_status()
        metadata = response.json()
        
        if version == "latest":
            version = metadata["dist-tags"]["latest"]
        
        version_data = metadata["versions"].get(version)
        if version_data:
            return version_data["dist"].get("unpackedSize", 0)
        
        return 0

