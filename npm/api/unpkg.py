"""Unpkg API client for file structure retrieval."""
import logging
from typing import Dict, Any, List, Optional
from npm.config import get_config
from npm.utils.http import get_json, get_text, HttpError

logger = logging.getLogger(__name__)


class UnpkgClient:
    """Client for Unpkg CDN to retrieve package file structures."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize client.
        
        Args:
            base_url: Unpkg base URL (uses config if None).
        """
        if base_url is None:
            config = get_config()
            base_url = config.unpkg_url
        
        self.base_url = base_url.rstrip("/")
    
    def get_file_tree(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get file tree structure for a package.
        
        Args:
            name: Package name.
            version: Package version (uses "latest" if None).
            
        Returns:
            File tree structure as nested dictionary.
            
        Raises:
            HttpError: If request fails.
        """
        if version is None:
            version = "latest"
        
        url = f"{self.base_url}/{name}@{version}/?meta"
        
        try:
            data = get_json(url)
            tree = self._parse_file_tree(data)
            logger.info(f"Retrieved file tree for {name}@{version}")
            return tree
        except HttpError as e:
            logger.error(f"Error fetching file tree for {name}@{version}: {e}")
            raise
    
    def get_file_content(
        self,
        name: str,
        file_path: str,
        version: Optional[str] = None
    ) -> str:
        """Get content of a specific file.
        
        Args:
            name: Package name.
            file_path: Path to file within package.
            version: Package version (uses "latest" if None).
            
        Returns:
            File content as string.
            
        Raises:
            HttpError: If request fails.
        """
        if version is None:
            version = "latest"
        
        # Remove leading slash if present
        file_path = file_path.lstrip("/")
        url = f"{self.base_url}/{name}@{version}/{file_path}"
        
        try:
            content = get_text(url)
            logger.debug(f"Retrieved file {file_path} from {name}@{version}")
            return content
        except HttpError as e:
            logger.error(f"Error fetching file {file_path}: {e}")
            raise
    
    def get_readme(self, name: str, version: Optional[str] = None) -> str:
        """Get README content.
        
        Args:
            name: Package name.
            version: Package version (uses "latest" if None).
            
        Returns:
            README content as string.
        """
        readme_files = ["README.md", "README", "readme.md", "Readme.md"]
        
        for readme_file in readme_files:
            try:
                content = self.get_file_content(name, readme_file, version)
                logger.info(f"Found README for {name}")
                return content
            except HttpError:
                continue
        
        logger.warning(f"No README found for {name}")
        return ""
    
    def _parse_file_tree(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse unpkg metadata into file tree structure.
        
        Args:
            data: Raw unpkg metadata.
            
        Returns:
            Parsed file tree structure.
        """
        def build_tree(files: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Build nested tree from flat file list."""
            tree = {}
            
            for file_info in files:
                path = file_info.get("path", "")
                if not path:
                    continue
                
                parts = path.lstrip("/").split("/")
                current = tree
                
                # Navigate/create nested structure
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Leaf node (file)
                        current[part] = {
                            "type": file_info.get("type", "file"),
                            "size": file_info.get("size", 0),
                            "path": path,
                        }
                    else:
                        # Directory node
                        if part not in current:
                            current[part] = {}
                        current = current[part]
            
            return tree
        
        files = data.get("files", [])
        return {
            "name": data.get("name", ""),
            "version": data.get("version", ""),
            "files": build_tree(files),
            "file_count": len(files),
        }

