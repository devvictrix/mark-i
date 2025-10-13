#!/usr/bin/env python3
"""
MARK-I Fast Capture Benchmark
Test the ultra-fast screen capture performance.
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

from mark_i.engines.fast_capture import FastCaptureEngine
import cv2
import numpy as np

def main():
    """Test fast capture performance."""
    print("⚡ MARK-I Fast Capture Benchmark")
    print("=" * 50)
    
    # Initialize fast capture engine
    print("🔧 Initializing fast capture engine...")
    capture_engine = FastCaptureEngine()
    
    print(f"📺 Screen: {capture_engine.get_screen_width()}x{capture_engine.get_screen_height()}")
    print(f"🎯 Method: {capture_engine.capture_method}")
    
    # Test 1: Single capture test
    print(f"\n📸 Single Capture Test...")
    start_time = time.time()
    frame = capture_engine.capture_screen_fast(width=640, height=480)
    single_time = time.time() - start_time
    
    if frame is not None:
        print(f"✅ Success: {single_time*1000:.1f}ms ({frame.shape})")
        fps_single = 1.0 / single_time
        print(f"🎯 Theoretical FPS: {fps_single:.1f}")
    else:
        print("❌ Single capture failed!")
        return
    
    # Test 2: Rapid capture test (10 frames)
    print(f"\n🚀 Rapid Capture Test (10 frames)...")
    times = []
    successful = 0
    
    for i in range(10):
        start_time = time.time()
        frame = capture_engine.capture_screen_fast(width=640, height=480)
        end_time = time.time()
        
        if frame is not None:
            times.append(end_time - start_time)
            successful += 1
            print(f"   Frame {i+1}: {(end_time - start_time)*1000:.1f}ms")
        else:
            print(f"   Frame {i+1}: FAILED")
    
    if times:
        avg_time = np.mean(times)
        min_time = min(times)
        max_time = max(times)
        fps_avg = 1.0 / avg_time
        
        print(f"\n📊 Rapid Test Results:")
        print(f"   Success Rate: {successful}/10 ({successful*10}%)")
        print(f"   Average: {avg_time*1000:.1f}ms ({fps_avg:.1f} FPS)")
        print(f"   Best: {min_time*1000:.1f}ms ({1.0/min_time:.1f} FPS)")
        print(f"   Worst: {max_time*1000:.1f}ms ({1.0/max_time:.1f} FPS)")
    
    # Test 3: Full benchmark
    print(f"\n🏁 Full Benchmark (100 captures)...")
    benchmark_results = capture_engine.benchmark_capture(iterations=100)
    
    print(f"📈 Benchmark Results:")
    print(f"   Method: {benchmark_results['method']}")
    print(f"   Success Rate: {benchmark_results['success_rate']*100:.1f}%")
    print(f"   Average FPS: {benchmark_results['fps']:.1f}")
    print(f"   Average Time: {benchmark_results['avg_time_ms']:.1f}ms")
    print(f"   Best Time: {benchmark_results['min_time_ms']:.1f}ms")
    print(f"   Worst Time: {benchmark_results['max_time_ms']:.1f}ms")
    print(f"   Test Resolution: {benchmark_results['test_resolution']}")
    
    # Performance assessment
    fps = benchmark_results['fps']
    print(f"\n🎯 PERFORMANCE ASSESSMENT:")
    
    if fps >= 30:
        print("✅ EXCELLENT: True real-time performance (30+ FPS)")
        print("   🎮 Suitable for gaming/high-speed applications")
    elif fps >= 15:
        print("✅ VERY GOOD: High-speed real-time (15+ FPS)")
        print("   🎯 Suitable for real-time AI vision")
    elif fps >= 10:
        print("✅ GOOD: Real-time capable (10+ FPS)")
        print("   👁️ Suitable for interactive applications")
    elif fps >= 5:
        print("⚠️ ACCEPTABLE: Near real-time (5+ FPS)")
        print("   📊 Suitable for monitoring applications")
    else:
        print("❌ TOO SLOW: Not real-time capable (<5 FPS)")
        print("   🐌 Needs optimization")
    
    # Test 4: Different resolutions
    print(f"\n📐 Resolution Performance Test:")
    resolutions = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (1280, 720, "HD"),
        (1920, 1080, "Full HD")
    ]
    
    for width, height, name in resolutions:
        # Skip if larger than screen
        if width > capture_engine.get_screen_width() or height > capture_engine.get_screen_height():
            continue
            
        times = []
        for _ in range(5):  # 5 samples per resolution
            start_time = time.time()
            frame = capture_engine.capture_screen_fast(width=width, height=height)
            end_time = time.time()
            
            if frame is not None:
                times.append(end_time - start_time)
        
        if times:
            avg_time = np.mean(times)
            fps = 1.0 / avg_time
            print(f"   {name} ({width}x{height}): {avg_time*1000:.1f}ms ({fps:.1f} FPS)")
    
    # Save a test capture
    print(f"\n💾 Saving test capture...")
    test_frame = capture_engine.capture_screen_fast(width=800, height=600)
    if test_frame is not None:
        cv2.imwrite("fast_capture_test.png", test_frame)
        print("✅ Saved test capture to: fast_capture_test.png")
    
    print(f"\n🎉 Fast capture benchmark complete!")

if __name__ == "__main__":
    main()