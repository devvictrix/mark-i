#!/usr/bin/env python3
"""
MARK-I Storage System Test
Test the storage manager and OS detection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mark_i.core.storage_manager import StorageManager
import json

def main():
    """Test the storage system."""
    print("🗄️ MARK-I Storage System Test")
    print("=" * 50)
    
    # Initialize storage manager
    print("🔧 Initializing Storage Manager...")
    storage_manager = StorageManager()
    
    # Display OS information
    print(f"\n📊 OS Detection Results:")
    print("-" * 30)
    print(storage_manager.export_os_info())
    
    # Test storage paths
    print(f"\n📁 Storage Paths:")
    print("-" * 20)
    storage_types = ["os", "images", "logs", "cache", "knowledge", "profiles", "root"]
    
    for storage_type in storage_types:
        path = storage_manager.get_storage_path(storage_type)
        exists = "✅" if path.exists() else "❌"
        print(f"   {storage_type:10}: {exists} {path}")
    
    # Test JSON storage
    print(f"\n💾 Testing JSON Storage...")
    test_data = {
        "test_key": "test_value",
        "timestamp": "2024-01-01T00:00:00",
        "numbers": [1, 2, 3, 4, 5]
    }
    
    # Store test data
    stored_path = storage_manager.store_json_data(test_data, "test_data.json", "cache")
    print(f"   Stored: {stored_path}")
    
    # Load test data
    loaded_data = storage_manager.load_json_data("test_data.json", "cache")
    if loaded_data == test_data:
        print("   ✅ JSON storage/loading works correctly")
    else:
        print("   ❌ JSON storage/loading failed")
    
    # Test image storage (simulate)
    print(f"\n🖼️ Testing Image Storage...")
    test_image_data = b"fake_image_data_for_testing"
    
    try:
        image_path = storage_manager.store_image(test_image_data, "test_image.png", "screenshots")
        print(f"   ✅ Image stored: {image_path}")
    except Exception as e:
        print(f"   ❌ Image storage failed: {e}")
    
    # Get storage statistics
    print(f"\n📊 Storage Statistics:")
    print("-" * 25)
    stats = storage_manager.get_storage_stats()
    
    total_files = 0
    total_size_mb = 0.0
    
    for storage_type, stat in stats.items():
        files = stat['file_count']
        size_mb = stat['total_size_mb']
        total_files += files
        total_size_mb += size_mb
        
        print(f"   {storage_type:10}: {files:3d} files, {size_mb:6.2f} MB")
    
    print(f"   {'TOTAL':10}: {total_files:3d} files, {total_size_mb:6.2f} MB")
    
    # Show OS file content
    print(f"\n🖥️ OS Information File:")
    print("-" * 25)
    os_file = storage_manager.get_storage_path("os") / "latest.json"
    if os_file.exists():
        with open(os_file, 'r') as f:
            os_data = json.load(f)
        
        print(f"   File: {os_file}")
        print(f"   System: {os_data.get('system', 'Unknown')}")
        if os_data.get('system') == 'Linux':
            print(f"   Distribution: {os_data.get('pretty_name', 'Unknown')}")
            print(f"   Desktop: {os_data.get('desktop_environment', 'Unknown')}")
            print(f"   Session: {os_data.get('session_type', 'Unknown')}")
        print(f"   Detected: {os_data.get('detected_at', 'Unknown')}")
    else:
        print("   ❌ OS information file not found")
    
    # Test cleanup (dry run)
    print(f"\n🧹 Storage Cleanup Test:")
    print("-" * 25)
    for storage_type in ["cache", "logs", "images"]:
        # Don't actually clean, just show what would be cleaned
        print(f"   {storage_type}: Ready for cleanup (test mode)")
    
    print(f"\n✅ Storage system test completed!")
    print(f"🎯 OS ID: {storage_manager.get_os_id()}")
    print(f"📁 Storage root: {storage_manager.storage_root}")

if __name__ == "__main__":
    main()