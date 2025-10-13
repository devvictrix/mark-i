#!/usr/bin/env python3
"""
MARK-I Real-Time Vision Demo
Test the real-time, focused vision system.
"""

import os
import sys
import time
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mark_i.engines.realtime_vision import RealtimeVisionEngine, FocusRegion
import cv2
import numpy as np

class RealtimeVisionDemo:
    """Demo for real-time vision system."""
    
    def __init__(self):
        self.vision_engine = RealtimeVisionEngine()
        self.running = True
        self.stats_history = []
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping real-time vision demo...")
        self.running = False
    
    def setup_focus_regions(self):
        """Setup example focus regions for testing."""
        print("🎯 Setting up focus regions...")
        
        # Get screen dimensions
        screen_w = self.vision_engine.capture_engine.get_screen_width()
        screen_h = self.vision_engine.capture_engine.get_screen_height()
        
        # Critical region - top-left corner (where important UI usually is)
        critical_region = FocusRegion(
            name="critical_ui",
            x=0,
            y=0,
            width=screen_w // 4,
            height=screen_h // 4,
            priority="critical",
            color="red",
            update_rate=30.0  # 30 FPS for critical regions
        )
        
        # Important region - center area (main content)
        important_region = FocusRegion(
            name="main_content",
            x=screen_w // 4,
            y=screen_h // 4,
            width=screen_w // 2,
            height=screen_h // 2,
            priority="important",
            color="yellow",
            update_rate=15.0  # 15 FPS for important regions
        )
        
        # Monitor region - bottom area (status bars, etc.)
        monitor_region = FocusRegion(
            name="status_area",
            x=0,
            y=3 * screen_h // 4,
            width=screen_w,
            height=screen_h // 4,
            priority="monitor",
            color="green",
            update_rate=5.0   # 5 FPS for monitoring
        )
        
        # Add regions with callbacks
        self.vision_engine.add_focus_region(critical_region, self.critical_callback)
        self.vision_engine.add_focus_region(important_region, self.important_callback)
        self.vision_engine.add_focus_region(monitor_region, self.monitor_callback)
        
        print(f"✅ Setup {len(self.vision_engine.focus_regions)} focus regions")
        for region in self.vision_engine.focus_regions:
            print(f"   🎯 {region.name}: {region.color} ({region.priority}) @ {region.update_rate}Hz")
    
    def critical_callback(self, data):
        """Handle critical region updates."""
        changes = data.get("changes", 0)
        if changes > 0.05:  # 5% change threshold
            print(f"🔴 CRITICAL: {data['region'].name} - {changes:.1%} change detected!")
    
    def important_callback(self, data):
        """Handle important region updates."""
        features = data.get("features", {})
        brightness = features.get("brightness", 0)
        if brightness > 200:  # Bright content detected
            print(f"🟡 IMPORTANT: {data['region'].name} - Bright content detected ({brightness:.0f})")
    
    def monitor_callback(self, data):
        """Handle monitor region updates."""
        # Just log periodically
        if hasattr(self, '_last_monitor_log'):
            if time.time() - self._last_monitor_log < 5.0:
                return
        
        self._last_monitor_log = time.time()
        print(f"🟢 MONITOR: {data['region'].name} - Status check OK")
    
    def run_demo(self):
        """Run the real-time vision demo."""
        print("🚀 MARK-I Real-Time Vision Demo")
        print("=" * 50)
        
        # Setup focus regions
        self.setup_focus_regions()
        
        # Start real-time vision
        print("\n▶️ Starting real-time vision engine...")
        self.vision_engine.start_realtime_vision()
        
        print("📊 Monitoring performance (Press Ctrl+C to stop)...")
        print("Legend: 🔴 Critical | 🟡 Important | 🟢 Monitor")
        print("-" * 50)
        
        # Performance monitoring loop
        last_stats_time = time.time()
        
        while self.running:
            try:
                time.sleep(1.0)  # Update stats every second
                
                # Get performance stats
                stats = self.vision_engine.get_performance_stats()
                self.stats_history.append(stats)
                
                # Display stats every 5 seconds
                if time.time() - last_stats_time >= 5.0:
                    self.display_performance_stats(stats)
                    last_stats_time = time.time()
                
            except KeyboardInterrupt:
                break
        
        # Stop vision engine
        print("\n🛑 Stopping vision engine...")
        self.vision_engine.stop_realtime_vision()
        
        # Show final summary
        self.show_final_summary()
    
    def display_performance_stats(self, stats):
        """Display current performance statistics."""
        fps = stats.get("fps", 0)
        frame_time = stats.get("avg_frame_time_ms", 0)
        is_realtime = stats.get("is_realtime", False)
        
        # Performance indicator
        if is_realtime:
            status = "✅ REAL-TIME"
            color = "🟢"
        elif fps >= 5:
            status = "⚠️ ACCEPTABLE"
            color = "🟡"
        else:
            status = "❌ TOO SLOW"
            color = "🔴"
        
        print(f"{color} FPS: {fps:.1f} | Frame Time: {frame_time:.1f}ms | {status}")
    
    def show_final_summary(self):
        """Show final performance summary."""
        if not self.stats_history:
            return
        
        print("\n" + "=" * 50)
        print("📊 FINAL PERFORMANCE SUMMARY")
        print("=" * 50)
        
        # Calculate averages
        avg_fps = np.mean([s.get("fps", 0) for s in self.stats_history])
        avg_frame_time = np.mean([s.get("avg_frame_time_ms", 0) for s in self.stats_history])
        realtime_percentage = np.mean([s.get("is_realtime", False) for s in self.stats_history]) * 100
        
        print(f"📈 Average FPS: {avg_fps:.1f}")
        print(f"⏱️ Average Frame Time: {avg_frame_time:.1f}ms")
        print(f"🎯 Real-time Performance: {realtime_percentage:.1f}%")
        print(f"🎯 Focus Regions: {len(self.vision_engine.focus_regions)}")
        
        # Performance assessment
        if avg_fps >= 10:
            print("✅ EXCELLENT: True real-time performance achieved!")
        elif avg_fps >= 5:
            print("✅ GOOD: Acceptable real-time performance")
        elif avg_fps >= 2:
            print("⚠️ MODERATE: Needs optimization for real-time")
        else:
            print("❌ POOR: Not suitable for real-time applications")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_frame_time > 100:
            print("   🔧 Optimize screen capture speed")
        if realtime_percentage < 80:
            print("   🔧 Reduce focus region complexity")
        if avg_fps < 10:
            print("   🔧 Consider smaller capture regions")
        
        print(f"\n🎉 Demo completed! Check the performance above.")

def main():
    """Run the real-time vision demo."""
    demo = RealtimeVisionDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()