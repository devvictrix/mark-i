#!/usr/bin/env python3
"""Quick test script to verify screen capture works on Ubuntu 24.04"""

import sys
sys.path.insert(0, '.')

from mark_i.engines.capture_engine import CaptureEngine
import cv2

print("Testing MARK-I Screen Capture on Ubuntu 24.04...")
print("=" * 60)

# Initialize capture engine
capture = CaptureEngine()

print(f"\nScreen dimensions: {capture.get_primary_screen_width()}x{capture.get_primary_screen_height()}")

# Test capture a small region
test_region = {
    "name": "test_capture",
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600
}

print(f"\nAttempting to capture region: {test_region}")
result = capture.capture_region(test_region)

if result is not None:
    print(f"✅ SUCCESS! Captured image shape: {result.shape}")
    print(f"✅ Image type: {result.dtype}")
    print(f"✅ Screen capture is working on Ubuntu 24.04!")
    
    # Save test image
    cv2.imwrite('/tmp/mark_i_test_capture.png', result)
    print(f"✅ Test image saved to: /tmp/mark_i_test_capture.png")
else:
    print("❌ FAILED: Screen capture returned None")
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 MARK-I Eye-Brain-Hand system is ready for Ubuntu 24.04!")
