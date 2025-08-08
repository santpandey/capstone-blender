"""
Safe and efficient loader for Blender API registry
Handles the 2.8MB JSON file with proper error handling and optimization
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache

from .models import (
    CompressedAPI, 
    APICategory, 
    SearchError,
    extract_keywords_from_description,
    normalize_api_name
)

class APIRegistryLoader:
    """
    Loads and processes the Blender API registry with optimization and error handling
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = Path(registry_path) if registry_path else Path("blender_api_registry.json")
        self.logger = logging.getLogger(__name__)
        
        # Cache for loaded data
        self._raw_data: Optional[Dict[str, Any]] = None
        self._compressed_apis: Optional[List[CompressedAPI]] = None
        self._load_time: Optional[float] = None
        
        # Statistics
        self.load_stats = {
            "total_apis": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "load_time_ms": 0.0,
            "file_size_mb": 0.0
        }
    
    def load_registry(self, force_reload: bool = False) -> List[CompressedAPI]:
        """
        Load the API registry with caching and error handling
        
        Args:
            force_reload: Force reload even if already cached
            
        Returns:
            List of compressed API objects
            
        Raises:
            SearchError: If loading fails
        """
        if self._compressed_apis is not None and not force_reload:
            self.logger.info("Using cached API registry")
            return self._compressed_apis
        
        start_time = time.time()
        
        try:
            # Validate file exists and is readable
            self._validate_registry_file()
            
            # Load raw JSON data
            self._load_raw_data()
            
            # Convert to compressed format
            self._convert_to_compressed_apis()
            
            # Update statistics
            load_time = (time.time() - start_time) * 1000
            self.load_stats["load_time_ms"] = load_time
            self._load_time = time.time()
            
            self.logger.info(
                f"Successfully loaded {len(self._compressed_apis)} APIs in {load_time:.2f}ms"
            )
            
            return self._compressed_apis
            
        except Exception as e:
            self.logger.error(f"Failed to load API registry: {e}")
            raise SearchError(
                f"Failed to load API registry: {str(e)}",
                error_code="REGISTRY_LOAD_FAILED",
                details={"file_path": str(self.registry_path), "error": str(e)}
            )
    
    def _validate_registry_file(self) -> None:
        """Validate that the registry file exists and is accessible"""
        if not self.registry_path.exists():
            raise SearchError(
                f"Registry file not found: {self.registry_path}",
                error_code="REGISTRY_FILE_NOT_FOUND"
            )
        
        if not self.registry_path.is_file():
            raise SearchError(
                f"Registry path is not a file: {self.registry_path}",
                error_code="REGISTRY_PATH_INVALID"
            )
        
        # Check file size
        file_size = self.registry_path.stat().st_size
        self.load_stats["file_size_mb"] = file_size / (1024 * 1024)
        
        if file_size == 0:
            raise SearchError(
                "Registry file is empty",
                error_code="REGISTRY_FILE_EMPTY"
            )
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            self.logger.warning(f"Large registry file detected: {file_size / (1024*1024):.1f}MB")
    
    def _load_raw_data(self) -> None:
        """Load raw JSON data with proper error handling"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self._raw_data = json.load(f)
            
            if not isinstance(self._raw_data, dict):
                raise SearchError(
                    "Registry file must contain a JSON object",
                    error_code="REGISTRY_FORMAT_INVALID"
                )
            
            self.load_stats["total_apis"] = len(self._raw_data)
            self.logger.info(f"Loaded raw data with {len(self._raw_data)} entries")
            
        except json.JSONDecodeError as e:
            raise SearchError(
                f"Invalid JSON in registry file: {str(e)}",
                error_code="REGISTRY_JSON_INVALID",
                details={"json_error": str(e)}
            )
        except UnicodeDecodeError as e:
            raise SearchError(
                f"Encoding error in registry file: {str(e)}",
                error_code="REGISTRY_ENCODING_ERROR",
                details={"encoding_error": str(e)}
            )
    
    def _convert_to_compressed_apis(self) -> None:
        """Convert raw data to compressed API format"""
        if self._raw_data is None:
            raise SearchError("Raw data not loaded", error_code="RAW_DATA_NOT_LOADED")
        
        compressed_apis = []
        successful_conversions = 0
        failed_conversions = 0
        
        for api_name, api_data in self._raw_data.items():
            try:
                compressed_api = self._convert_single_api(api_name, api_data)
                if compressed_api:
                    compressed_apis.append(compressed_api)
                    successful_conversions += 1
                else:
                    failed_conversions += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to convert API {api_name}: {e}")
                failed_conversions += 1
                continue
        
        self._compressed_apis = compressed_apis
        self.load_stats["successful_conversions"] = successful_conversions
        self.load_stats["failed_conversions"] = failed_conversions
        
        if failed_conversions > 0:
            self.logger.warning(f"Failed to convert {failed_conversions} APIs")
        
        if successful_conversions == 0:
            raise SearchError(
                "No APIs were successfully converted",
                error_code="NO_APIS_CONVERTED"
            )
    
    def _convert_single_api(self, api_name: str, api_data: Dict[str, Any]) -> Optional[CompressedAPI]:
        """
        Convert a single API entry to compressed format
        
        Args:
            api_name: The API name (e.g., "bpy.ops.mesh.bevel")
            api_data: The raw API data from JSON
            
        Returns:
            CompressedAPI object or None if conversion fails
        """
        try:
            # Extract basic information
            description = str(api_data.get("description", "")).strip()
            if len(description) > 200:
                description = description[:197] + "..."
            
            # Determine category from API name
            category = self._determine_category(api_name)
            
            # Extract parameters (names only for efficiency)
            parameters = []
            if "parameters" in api_data and isinstance(api_data["parameters"], dict):
                parameters = list(api_data["parameters"].keys())
            
            # Extract or generate tags
            tags = api_data.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            
            # Generate search keywords from description
            search_keywords = extract_keywords_from_description(description)
            
            # Add API name components as keywords
            name_parts = api_name.replace("bpy.ops.", "").split(".")
            search_keywords.extend(name_parts)
            
            # Remove duplicates from search keywords
            search_keywords = list(dict.fromkeys(search_keywords))  # Preserves order
            
            # Generate common use cases based on API name and description
            common_use_cases = self._generate_use_cases(api_name, description)
            
            # Calculate popularity score (placeholder - could be enhanced with usage data)
            popularity_score = self._calculate_popularity_score(api_name, category)
            
            return CompressedAPI(
                id=normalize_api_name(api_name),
                name=api_name,
                category=category,
                description=description,
                parameters=parameters,
                tags=tags,
                search_keywords=search_keywords,
                common_use_cases=common_use_cases,
                popularity_score=popularity_score
            )
            
        except Exception as e:
            self.logger.debug(f"Error converting API {api_name}: {e}")
            return None
    
    def _determine_category(self, api_name: str) -> APICategory:
        """Determine API category from the API name"""
        api_lower = api_name.lower()
        
        if "mesh" in api_lower:
            return APICategory.MESH_OPERATORS
        elif "object" in api_lower:
            return APICategory.OBJECT_OPERATORS
        elif "geometry" in api_lower or "node" in api_lower:
            return APICategory.GEOMETRY_NODES
        elif "shader" in api_lower or "material" in api_lower:
            return APICategory.SHADER_NODES
        elif "anim" in api_lower or "keyframe" in api_lower:
            return APICategory.ANIMATION_OPERATORS
        elif "scene" in api_lower or "render" in api_lower:
            return APICategory.SCENE_OPERATORS
        else:
            return APICategory.UNKNOWN
    
    def _generate_use_cases(self, api_name: str, description: str) -> List[str]:
        """Generate common use cases based on API name and description"""
        use_cases = []
        api_lower = api_name.lower()
        desc_lower = description.lower()
        
        # Common patterns for use case generation
        if "bevel" in api_lower:
            use_cases.extend(["smooth edges", "rounded corners", "chamfer"])
        elif "extrude" in api_lower:
            use_cases.extend(["extend geometry", "create depth", "add volume"])
        elif "subdivide" in api_lower:
            use_cases.extend(["add detail", "increase resolution", "smooth surface"])
        elif "duplicate" in api_lower:
            use_cases.extend(["copy objects", "replicate geometry", "create instances"])
        elif "scale" in api_lower:
            use_cases.extend(["resize objects", "change proportions", "uniform scaling"])
        elif "rotate" in api_lower:
            use_cases.extend(["change orientation", "spin objects", "angular transformation"])
        
        # Add generic use cases based on category
        category = self._determine_category(api_name)
        if category == APICategory.MESH_OPERATORS:
            use_cases.append("mesh modeling")
        elif category == APICategory.OBJECT_OPERATORS:
            use_cases.append("object manipulation")
        
        return list(dict.fromkeys(use_cases))  # Remove duplicates
    
    def _calculate_popularity_score(self, api_name: str, category: APICategory) -> float:
        """Calculate a popularity score for the API (0-1)"""
        # This is a simple heuristic - could be enhanced with real usage data
        score = 0.5  # Base score
        
        # Common operations get higher scores
        common_operations = [
            "add", "delete", "select", "move", "scale", "rotate", 
            "extrude", "bevel", "subdivide", "duplicate"
        ]
        
        api_lower = api_name.lower()
        for operation in common_operations:
            if operation in api_lower:
                score += 0.1
                break
        
        # Mesh operations are generally more popular
        if category == APICategory.MESH_OPERATORS:
            score += 0.1
        
        # Clamp to [0, 1]
        return min(max(score, 0.0), 1.0)
    
    @lru_cache(maxsize=100)
    def get_apis_by_category(self, category: APICategory) -> List[CompressedAPI]:
        """Get all APIs for a specific category (cached)"""
        if self._compressed_apis is None:
            self.load_registry()
        
        return [api for api in self._compressed_apis if api.category == category]
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get loading statistics"""
        stats = self.load_stats.copy()
        if self._load_time:
            stats["loaded_at"] = self._load_time
            stats["cache_age_seconds"] = time.time() - self._load_time
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._raw_data = None
        self._compressed_apis = None
        self._load_time = None
        self.get_apis_by_category.cache_clear()
        self.logger.info("Registry cache cleared")
    
    def validate_loaded_data(self) -> bool:
        """Validate that loaded data is consistent and complete"""
        if self._compressed_apis is None:
            return False
        
        try:
            # Check that we have APIs
            if len(self._compressed_apis) == 0:
                return False
            
            # Check that all APIs have required fields
            for api in self._compressed_apis[:10]:  # Sample check
                if not api.id or not api.name:
                    return False
                if not isinstance(api.category, APICategory):
                    return False
            
            # Check category distribution
            categories = {}
            for api in self._compressed_apis:
                cat = api.category
                categories[cat] = categories.get(cat, 0) + 1
            
            # Should have multiple categories
            if len(categories) < 2:
                self.logger.warning("Only one API category found - this may indicate an issue")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return False
