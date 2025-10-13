"""
Computer Vision Analyzer for MARK-I
Provides OpenCV-based visual analysis to complement AI-based perception.
"""

import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.cv_analyzer")

class CVAnalyzer:
    """Computer Vision analyzer using OpenCV for basic visual detection."""
    
    def __init__(self):
        """Initialize the CV analyzer."""
        self.initialized = True
        logger.info("CVAnalyzer initialized")
    
    def detect_edges(self, image: np.ndarray, threshold1: int = 50, threshold2: int = 150) -> np.ndarray:
        """Detect edges in the image using Canny edge detection."""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply Canny edge detection
            edges = cv2.Canny(gray, threshold1, threshold2)
            return edges
            
        except Exception as e:
            logger.error(f"Error in edge detection: {e}")
            return np.zeros_like(image[:,:,0] if len(image.shape) == 3 else image)
    
    def detect_contours(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect contours (shapes) in the image."""
        try:
            # Get edges
            edges = self.detect_edges(image)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detected_shapes = []
            
            for i, contour in enumerate(contours):
                # Filter out very small contours
                area = cv2.contourArea(contour)
                if area < 100:  # Minimum area threshold
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate shape properties
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                
                # Determine shape type based on number of vertices
                shape_type = "unknown"
                if len(approx) == 3:
                    shape_type = "triangle"
                elif len(approx) == 4:
                    # Check if it's a square or rectangle
                    aspect_ratio = float(w) / h
                    if 0.95 <= aspect_ratio <= 1.05:
                        shape_type = "square"
                    else:
                        shape_type = "rectangle"
                elif len(approx) > 4:
                    # Check if it's circular
                    area_ratio = area / (cv2.contourArea(cv2.convexHull(contour)))
                    if area_ratio > 0.85:
                        shape_type = "circle"
                    else:
                        shape_type = "polygon"
                
                detected_shapes.append({
                    "id": i,
                    "type": "shape",
                    "shape_type": shape_type,
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "area": int(area),
                    "vertices": len(approx),
                    "confidence": min(10, max(1, int(area / 1000)))  # Simple confidence based on size
                })
            
            logger.debug(f"Detected {len(detected_shapes)} shapes")
            return detected_shapes
            
        except Exception as e:
            logger.error(f"Error in contour detection: {e}")
            return []
    
    def detect_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect potential text regions using MSER (Maximally Stable Extremal Regions)."""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Create MSER detector
            mser = cv2.MSER_create()
            
            # Detect regions
            regions, _ = mser.detectRegions(gray)
            
            text_regions = []
            
            for i, region in enumerate(regions):
                # Get bounding rectangle for the region
                x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
                
                # Filter based on aspect ratio and size (typical for text)
                aspect_ratio = float(w) / h
                area = w * h
                
                # Text regions typically have certain characteristics
                if (0.1 < aspect_ratio < 10 and  # Not too thin or too wide
                    area > 50 and  # Not too small
                    area < image.shape[0] * image.shape[1] * 0.5):  # Not too large
                    
                    text_regions.append({
                        "id": i,
                        "type": "text_region",
                        "bbox": {"x": x, "y": y, "width": w, "height": h},
                        "area": int(area),
                        "aspect_ratio": round(aspect_ratio, 2),
                        "confidence": min(10, max(1, int(area / 500)))
                    })
            
            logger.debug(f"Detected {len(text_regions)} potential text regions")
            return text_regions
            
        except Exception as e:
            logger.error(f"Error in text region detection: {e}")
            return []
    
    def detect_ui_elements(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect potential UI elements using template matching and contour analysis."""
        try:
            ui_elements = []
            
            # Detect rectangular shapes that might be buttons or UI elements
            shapes = self.detect_contours(image)
            
            for shape in shapes:
                if shape["shape_type"] in ["rectangle", "square"]:
                    bbox = shape["bbox"]
                    
                    # UI elements typically have certain size characteristics
                    width, height = bbox["width"], bbox["height"]
                    area = width * height
                    aspect_ratio = width / height
                    
                    # Classify based on size and aspect ratio
                    ui_type = "unknown"
                    confidence = shape["confidence"]
                    
                    if 20 <= width <= 200 and 15 <= height <= 50 and 1.5 <= aspect_ratio <= 8:
                        ui_type = "button"
                        confidence = min(10, confidence + 2)
                    elif 50 <= width <= 400 and 15 <= height <= 30 and aspect_ratio >= 3:
                        ui_type = "text_field"
                        confidence = min(10, confidence + 1)
                    elif width >= 100 and height >= 100 and 0.5 <= aspect_ratio <= 2:
                        ui_type = "window"
                        confidence = min(10, confidence + 1)
                    elif 10 <= width <= 50 and 10 <= height <= 50 and 0.5 <= aspect_ratio <= 2:
                        ui_type = "icon"
                        confidence = min(10, confidence + 1)
                    
                    ui_elements.append({
                        "id": len(ui_elements),
                        "type": "ui_element",
                        "ui_type": ui_type,
                        "bbox": bbox,
                        "area": area,
                        "aspect_ratio": round(aspect_ratio, 2),
                        "confidence": confidence
                    })
            
            logger.debug(f"Detected {len(ui_elements)} potential UI elements")
            return ui_elements
            
        except Exception as e:
            logger.error(f"Error in UI element detection: {e}")
            return []
    
    def analyze_image_comprehensive(self, image: np.ndarray) -> Dict[str, Any]:
        """Perform comprehensive computer vision analysis on the image."""
        try:
            logger.debug("Starting comprehensive CV analysis")
            
            # Run all detection methods
            shapes = self.detect_contours(image)
            text_regions = self.detect_text_regions(image)
            ui_elements = self.detect_ui_elements(image)
            
            # Combine all detections
            all_detections = shapes + text_regions + ui_elements
            
            # Calculate image statistics
            height, width = image.shape[:2]
            total_pixels = height * width
            
            # Edge density (measure of visual complexity)
            edges = self.detect_edges(image)
            edge_pixels = np.count_nonzero(edges)
            edge_density = edge_pixels / total_pixels
            
            analysis_result = {
                "image_info": {
                    "width": width,
                    "height": height,
                    "total_pixels": total_pixels,
                    "channels": len(image.shape) if len(image.shape) == 3 else 1
                },
                "visual_complexity": {
                    "edge_density": round(edge_density, 4),
                    "complexity_level": self._classify_complexity(edge_density)
                },
                "detections": {
                    "shapes": shapes,
                    "text_regions": text_regions,
                    "ui_elements": ui_elements,
                    "total_objects": len(all_detections)
                },
                "summary": {
                    "total_detections": len(all_detections),
                    "shape_count": len(shapes),
                    "text_region_count": len(text_regions),
                    "ui_element_count": len(ui_elements)
                }
            }
            
            logger.info(f"CV analysis complete: {len(all_detections)} objects detected")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                "error": str(e),
                "detections": {"shapes": [], "text_regions": [], "ui_elements": []},
                "summary": {"total_detections": 0}
            }
    
    def _classify_complexity(self, edge_density: float) -> str:
        """Classify visual complexity based on edge density."""
        if edge_density < 0.05:
            return "simple"
        elif edge_density < 0.15:
            return "moderate"
        elif edge_density < 0.25:
            return "complex"
        else:
            return "very_complex"
    
    def draw_detections(self, image: np.ndarray, detections: Dict[str, Any]) -> np.ndarray:
        """Draw detection results on the image for visualization."""
        try:
            # Create a copy for drawing
            result_image = image.copy()
            
            # Color scheme for different types
            colors = {
                "shape": (0, 255, 0),      # Green
                "text_region": (255, 0, 0), # Blue
                "ui_element": (0, 0, 255),  # Red
            }
            
            # Draw all detections
            all_objects = (detections.get("detections", {}).get("shapes", []) +
                          detections.get("detections", {}).get("text_regions", []) +
                          detections.get("detections", {}).get("ui_elements", []))
            
            for obj in all_objects:
                bbox = obj.get("bbox", {})
                x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
                
                obj_type = obj.get("type", "unknown")
                color = colors.get(obj_type, (255, 255, 255))
                
                # Draw bounding box
                cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)
                
                # Draw label
                label = f"{obj.get('shape_type', obj.get('ui_type', obj_type))}"
                confidence = obj.get("confidence", 0)
                label += f" ({confidence}/10)"
                
                # Put text with background
                (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(result_image, (x, y - text_height - 5), (x + text_width, y), color, -1)
                cv2.putText(result_image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return result_image
            
        except Exception as e:
            logger.error(f"Error drawing detections: {e}")
            return image