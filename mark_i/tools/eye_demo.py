#!/usr/bin/env python3
"""
MARK-I Eye Demonstration
Simple script to show what MARK-I's Eye can see and detect.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.cv_analyzer import CVAnalyzer
import cv2
import numpy as np
from PIL import Image

def main():
    """Run a simple Eye demonstration."""
    print("👁️ MARK-I Eye Demonstration")
    print("=" * 50)
    
    # Initialize engines
    print("🔧 Initializing Eye components...")
    capture_engine = CaptureEngine()
    cv_analyzer = CVAnalyzer()
    
    print(f"📺 Screen Resolution: {capture_engine.get_primary_screen_width()}x{capture_engine.get_primary_screen_height()}")
    print(f"🖼️ Capture Method: {getattr(capture_engine, 'capture_tool', 'ImageGrab')}")
    
    # Capture screen
    print("\n📸 Capturing current screen...")
    screen_region = {
        "name": "eye_demo_capture",
        "x": 0,
        "y": 0,
        "width": capture_engine.get_primary_screen_width(),
        "height": capture_engine.get_primary_screen_height()
    }
    
    start_time = time.time()
    captured_image = capture_engine.capture_region(screen_region)
    capture_time = time.time() - start_time
    
    if captured_image is None:
        print("❌ Screen capture failed!")
        return
    
    print(f"✅ Screen captured in {capture_time*1000:.1f}ms")
    print(f"📐 Image shape: {captured_image.shape}")
    
    # Analyze with Computer Vision
    print("\n👁️ Analyzing with Computer Vision...")
    start_time = time.time()
    cv_results = cv_analyzer.analyze_image_comprehensive(captured_image)
    cv_time = time.time() - start_time
    
    print(f"✅ CV analysis completed in {cv_time*1000:.1f}ms")
    
    # Display results
    print("\n🔍 WHAT MARK-I'S EYE SEES:")
    print("=" * 50)
    
    # Image info
    img_info = cv_results.get("image_info", {})
    print(f"📊 Image: {img_info.get('width')}x{img_info.get('height')} pixels")
    print(f"🎨 Channels: {img_info.get('channels')}")
    
    # Visual complexity
    complexity = cv_results.get("visual_complexity", {})
    print(f"🧠 Visual Complexity: {complexity.get('complexity_level', 'unknown').upper()}")
    print(f"📈 Edge Density: {complexity.get('edge_density', 0):.4f}")
    
    # Detection summary
    summary = cv_results.get("summary", {})
    print(f"\n🎯 DETECTIONS SUMMARY:")
    print(f"   Total Objects: {summary.get('total_detections', 0)}")
    print(f"   Shapes: {summary.get('shape_count', 0)}")
    print(f"   Text Regions: {summary.get('text_region_count', 0)}")
    print(f"   UI Elements: {summary.get('ui_element_count', 0)}")
    
    # Show some examples
    detections = cv_results.get("detections", {})
    
    print(f"\n🔺 SHAPES DETECTED:")
    shapes = detections.get("shapes", [])[:5]  # Show first 5
    for i, shape in enumerate(shapes, 1):
        bbox = shape.get("bbox", {})
        print(f"   {i}. {shape.get('shape_type', 'unknown').title()} - "
              f"Size: {bbox.get('width')}x{bbox.get('height')} - "
              f"Confidence: {shape.get('confidence')}/10")
    
    print(f"\n📝 TEXT REGIONS DETECTED:")
    text_regions = detections.get("text_regions", [])[:5]  # Show first 5
    for i, region in enumerate(text_regions, 1):
        bbox = region.get("bbox", {})
        print(f"   {i}. Text Area - "
              f"Size: {bbox.get('width')}x{bbox.get('height')} - "
              f"Aspect Ratio: {region.get('aspect_ratio', 1.0):.2f} - "
              f"Confidence: {region.get('confidence')}/10")
    
    print(f"\n🖱️ UI ELEMENTS DETECTED:")
    ui_elements = detections.get("ui_elements", [])[:5]  # Show first 5
    for i, element in enumerate(ui_elements, 1):
        bbox = element.get("bbox", {})
        print(f"   {i}. {element.get('ui_type', 'unknown').title()} - "
              f"Size: {bbox.get('width')}x{bbox.get('height')} - "
              f"Confidence: {element.get('confidence')}/10")
    
    # Save annotated image
    print(f"\n💾 Saving annotated image...")
    try:
        annotated_image = cv_analyzer.draw_detections(captured_image, cv_results)
        
        # Save the image
        output_path = "mark_i_eye_view.png"
        cv2.imwrite(output_path, annotated_image)
        print(f"✅ Saved annotated image to: {output_path}")
        print(f"🖼️ Open this file to see what MARK-I's Eye detected!")
        
    except Exception as e:
        print(f"❌ Failed to save annotated image: {e}")
    
    print(f"\n🎉 Eye demonstration complete!")
    print(f"📊 Performance Summary:")
    print(f"   Screen Capture: {capture_time*1000:.1f}ms")
    print(f"   CV Analysis: {cv_time*1000:.1f}ms")
    print(f"   Total Objects: {summary.get('total_detections', 0)}")
    
    # Performance assessment
    total_time = capture_time + cv_time
    if total_time < 1.0:
        print(f"✅ EXCELLENT: Eye performance is very fast ({total_time*1000:.1f}ms total)")
    elif total_time < 3.0:
        print(f"✅ GOOD: Eye performance is acceptable ({total_time*1000:.1f}ms total)")
    else:
        print(f"⚠️ SLOW: Eye performance needs optimization ({total_time*1000:.1f}ms total)")

if __name__ == "__main__":
    main()