#!/usr/bin/env python3
"""
MARK-I Optimized Capture Test
Test the optimized screen capture system.
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

from mark_i.engines.optimized_capture import OptimizedCaptureEngine
import cv2
import numpy as np

def main():
    """Test optimized capture performance."""
    print("⚡ MARK-I Optimized Capture Test")
    print("=" * 50)
    
    # Initialize optimized capture engine
    print("🔧 Initializing optimized capture engine...")
    capture_engine = OptimizedCaptureEngine()
    
    print(f"📺 Screen: {capture_engine.get_screen_width()}x{capture_engine.get_screen_height()}")
    
    # Test 1: Single capture test
    print(f"\n📸 Single Capture Test...")
    start_time = time.time()
    frame = capture_engine.capture_center_region(640)
    single_time = time.time() - start_time
    
    if frame is not None:
        print(f"✅ Success: {single_time*1000:.1f}ms ({frame.shape})")
        fps_single = 1.0 / single_time
        print(f"🎯 Theoretical FPS: {fps_single:.1f}")
        
        # Save test image
        cv2.imwrite("optimized_capture_test.png", frame)
        print("💾 Saved test capture: optimized_capture_test.png")
    else:
        print("❌ Single capture failed!")
        return
    
    # Test 2: Speed test with different sizes
    print(f"\n🚀 Speed Test (Different Sizes)...")
    
    test_sizes = [
        (320, "Small (320x320)"),
        (640, "Medium (640x640)"),
        (1280, "Large (1280x720)")
    ]
    
    for size, description in test_sizes:
        print(f"\n   Testing {description}:")
        times = []
        successful = 0
        
        for i in range(5):  # 5 captures per size
            start_time = time.time()
            if size == 1280:
                frame = capture_engine.capture_screen_optimized(0, 0, 1280, 720)
            else:
                frame = capture_engine.capture_center_region(size)
            end_time = time.time()
            
            if frame is not None:
                times.append(end_time - start_time)
                successful += 1
                print(f"     Capture {i+1}: {(end_time - start_time)*1000:.1f}ms")
            else:
                print(f"     Capture {i+1}: FAILED")
        
        if times:
            avg_time = np.mean(times)
            fps = 1.0 / avg_time
            print(f"   📊 Average: {avg_time*1000:.1f}ms ({fps:.1f} FPS)")
            
            # Performance assessment
            if fps >= 10:
                print("   ✅ REAL-TIME CAPABLE")
            elif fps >= 5:
                print("   ⚠️ NEAR REAL-TIME")
            else:
                print("   ❌ TOO SLOW")
    
    # Test 3: Cache performance test
    print(f"\n🗄️ Cache Performance Test...")
    
    # First capture (no cache)
    start_time = time.time()
    frame1 = capture_engine.capture_center_region(320)
    time1 = time.time() - start_time
    
    # Second capture (should use cache)
    start_time = time.time()
    frame2 = capture_engine.capture_center_region(320)
    time2 = time.time() - start_time
    
    if frame1 is not None and frame2 is not None:
        print(f"   First capture: {time1*1000:.1f}ms")
        print(f"   Cached capture: {time2*1000:.1f}ms")
        speedup = time1 / time2 if time2 > 0 else 1.0
        print(f"   Cache speedup: {speedup:.1f}x")
        
        if speedup > 2.0:
            print("   ✅ CACHE WORKING WELL")
        elif speedup > 1.2:
            print("   ⚠️ CACHE HELPING")
        else:
            print("   ❌ CACHE NOT EFFECTIVE")
    
    # Test 4: Full benchmark
    print(f"\n🏁 Full Benchmark...")
    benchmark_results = capture_engine.benchmark_optimized_capture(iterations=10)
    
    print(f"\n📈 Benchmark Results:")
    for scenario, results in benchmark_results.items():
        fps = results['fps']
        success_rate = results['success_rate'] * 100
        avg_time = results['avg_time_ms']
        
        print(f"   {scenario}:")
        print(f"     FPS: {fps:.1f}")
        print(f"     Success: {success_rate:.0f}%")
        print(f"     Avg Time: {avg_time:.1f}ms")
        
        if fps >= 10:
            status = "✅ REAL-TIME"
        elif fps >= 5:
            status = "⚠️ NEAR REAL-TIME"
        else:
            status = "❌ TOO SLOW"
        print(f"     Status: {status}")
    
    # Find best performing scenario
    best_scenario = max(benchmark_results.items(), key=lambda x: x[1]['fps'])
    best_fps = best_scenario[1]['fps']
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"Best Performance: {best_scenario[0]} at {best_fps:.1f} FPS")
    
    if best_fps >= 15:
        print("✅ EXCELLENT: MARK-I Eye can achieve real-time performance!")
        print("   🎯 Ready for real-time vision applications")
    elif best_fps >= 10:
        print("✅ GOOD: MARK-I Eye is real-time capable")
        print("   👁️ Suitable for interactive applications")
    elif best_fps >= 5:
        print("⚠️ ACCEPTABLE: Near real-time performance")
        print("   📊 Suitable for monitoring applications")
    else:
        print("❌ NEEDS IMPROVEMENT: Performance too slow for real-time")
        print("   🔧 Consider further optimizations")
    
    # Performance stats
    stats = capture_engine.get_performance_stats()
    print(f"\n📊 Performance Stats:")
    print(f"   Cache Size: {stats['cache_size']}")
    print(f"   Cache Age: {stats['cache_age_ms']:.1f}ms")
    print(f"   Screen: {stats['screen_resolution']}")
    
    print(f"\n🎉 Optimized capture test complete!")

if __name__ == "__main__":
    main()