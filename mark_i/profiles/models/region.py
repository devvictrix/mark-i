"""
Region Model

Defines screen regions for automation targeting and visual analysis.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
import json


@dataclass
class Region:
    """Screen region definition for automation"""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str
    
    # Region properties
    monitor_index: int = 0
    is_relative: bool = False
    parent_region: Optional[str] = None
    
    # Visual properties
    expected_colors: Optional[List[Tuple[int, int, int]]] = None
    template_image: Optional[str] = None
    ocr_enabled: bool = False
    
    # Behavior
    retry_count: int = 3
    timeout_seconds: int = 5
    
    def __post_init__(self):
        """Validate region parameters after initialization"""
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Region '{self.name}' must have positive width and height")
        
        if self.x < 0 or self.y < 0:
            raise ValueError(f"Region '{self.name}' coordinates must be non-negative")
    
    @property
    def center_x(self) -> int:
        """Get the center X coordinate of the region"""
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        """Get the center Y coordinate of the region"""
        return self.y + self.height // 2
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get region bounds as (x, y, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this region"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def overlaps_with(self, other: 'Region') -> bool:
        """Check if this region overlaps with another region"""
        return not (self.x + self.width < other.x or 
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or 
                   other.y + other.height < self.y)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert region to dictionary for serialization"""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'description': self.description,
            'monitor_index': self.monitor_index,
            'is_relative': self.is_relative,
            'parent_region': self.parent_region,
            'expected_colors': self.expected_colors,
            'template_image': self.template_image,
            'ocr_enabled': self.ocr_enabled,
            'retry_count': self.retry_count,
            'timeout_seconds': self.timeout_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Region':
        """Create region from dictionary"""
        return cls(
            name=data['name'],
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            description=data['description'],
            monitor_index=data.get('monitor_index', 0),
            is_relative=data.get('is_relative', False),
            parent_region=data.get('parent_region'),
            expected_colors=data.get('expected_colors'),
            template_image=data.get('template_image'),
            ocr_enabled=data.get('ocr_enabled', False),
            retry_count=data.get('retry_count', 3),
            timeout_seconds=data.get('timeout_seconds', 5)
        )
    
    def to_json(self) -> str:
        """Convert region to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Region':
        """Create region from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)