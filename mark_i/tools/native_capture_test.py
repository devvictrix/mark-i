#!/usr/bin/env python3
"""
MARK-I Native Capture Test
Test the ultra-fast native screen capture.
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

from mark_i.engines.native_capture import NativeCaptureEngine
import cv2
import numpy as np

def main():
    """Test native capture performance."""
    print("⚡ MARK-I Native Capture Test")
    print("=" * 50)
    
    # Initialize native capture engine
    print("🔧 Initializing native capture engine...")
    capture_engine = NativeCaptureEngine()
    
    print(f"📺 Screen: {capture_engine.get_screen_width()}x{capture_engine.get_screen_height()}")
    print(f"🎯 Method: {capture_engine.capture_method}")
    
    # Test 1: Single capture test
    print(f"\n📸 Single Capture Test...")
    start_time = time.time()
    frame = capture_engine.capture_screen_native(width=640, height=480)
    single_time = time.time() - start_time
    
    if frame is not None:
        print(f"✅ Success: {single_time*1000:.1f}ms ({frame.shape})")
        fps_single = 1.0 / single_time
        print(f"🎯 Theoretical FPS: {fps_single:.1f}")
        
        # Save test image
        cv2.imwrite("native_capture_test.png", frame)
        print("💾 Saved test capture: native_capture_test.png")
    else:
        print("❌ Single capture failed!")
        return
    
    # Test 2: Speed test (10 rapid captures)
    print(f"\n🚀 Speed Test (10 captures)...")
    times = []
    successful = 0
    
    for i in range(10):
        start_time = time.time()
        frame = capture_engine.capture_screen_native(width=320, height=240)  # Small for speed
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
        
        print(f"\n📊 Speed Test Results:")
        print(f"   Success Rate: {successful}/10 ({successful*10}%)")
        print(f"   Average: {avg_time*1000:.1f}ms ({fps_avg:.1f} FPS)")
        print(f"   Best: {min_time*1000:.1f}ms ({1.0/min_time:.1f} FPS)")
        print(f"   Worst: {max_time*1000:.1f}ms ({1.0/max_time:.1f} FPS)")
        
        # Real-time assessment
        if fps_avg >= 30:
            print("   ✅ EXCELLENT: True real-time (30+ FPS)")
        elif fps_avg >= 15:
            print("   ✅ VERY GOOD: High-speed real-time (15+ FPS)")
        elif fps_avg >= 10:
            print("   ✅ GOOD: Real-time capable (10+ FPS)")
        elif fps_avg >= 5:
            print("   ⚠️ ACCEPTABLE: Near real-time (5+ FPS)")
        else:
            print("   ❌ TOO SLOW: Not real-time (<5 FPS)")
    
    # Test 3: Full benchmark
    print(f"\n🏁 Full Benchmark (50 captures)...")
    benchmark_results = capture_engine.benchmark_native_capture(iterations=50)
    
    print(f"\n📈 Benchmark Results:")
    print(f"   Method: {benchmark_results['method']}")
    print(f"   Success Rate: {benchmark_results['success_rate']*100:.1f}%")
    print(f"   Average FPS: {benchmark_results['fps']:.1f}")
    print(f"   Average Time: {benchmark_results['avg_time_ms']:.1f}ms")
    print(f"   Best Time: {benchmark_results['min_time_ms']:.1f}ms")
    print(f"   Worst Time: {benchmark_results['max_time_ms']:.1f}ms")
    print(f"   Test Resolution: {benchmark_results['test_resolution']}")
    
    # Final assessment
    fps = benchmark_results['fps']
    print(f"\n🎯 FINAL ASSESSMENT:")
    
    if fps >= 30:
        print("✅ EXCELLENT: True real-time performance achieved!")
        print("   🎮 Ready for high-speed applications")
        print("   🎯 MARK-I Eye can work in real-time!")
    elif fps >= 15:
        print("✅ VERY GOOD: High-speed real-time performance")
        print("   🎯 MARK-I Eye is ready for real-time vision!")
    elif fps >= 10:
        print("✅ GOOD: Real-time capable")
        print("   👁️ MARK-I Eye can handle interactive tasks")
    elif fps >= 5:
        print("⚠️ ACCEPTABLE: Near real-time")
        print("   📊 MARK-I Eye suitable for monitoring")
    else:
        print("❌ TOO SLOW: Needs optimization")
        print("   🔧 Consider different capture method")
    
    print(f"\n🎉 Native capture test complete!")
    print(f"🚀 MARK-I Eye performance: {fps:.1f} FPS")

if __name__ == "__main__":
    main()