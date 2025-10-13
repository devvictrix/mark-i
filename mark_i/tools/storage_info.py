#!/usr/bin/env python3
"""
MARK-I Storage Information Tool
Display comprehensive storage and system information.
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

def main():
    """Display comprehensive storage information."""
    print("🗄️ MARK-I Storage Information")
    print("=" * 60)
    
    # Initialize storage manager
    storage_manager = StorageManager()
    
    # System Information
    print("\n🖥️ SYSTEM INFORMATION")
    print("-" * 30)
    print(storage_manager.export_os_info())
    
    # Storage Structure
    print(f"\n📁 STORAGE STRUCTURE")
    print("-" * 30)
    
    storage_root = storage_manager.storage_root
    print(f"Storage Root: {storage_root}")
    print(f"")
    
    # Show directory tree
    def show_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        if current_depth >= max_depth:
            return
            
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                show_tree(item, prefix + extension, max_depth, current_depth + 1)
    
    show_tree(storage_root)
    
    # Storage Statistics
    print(f"\n📊 STORAGE STATISTICS")
    print("-" * 30)
    stats = storage_manager.get_storage_stats()
    
    total_files = 0
    total_size_mb = 0.0
    
    for storage_type, stat in stats.items():
        files = stat['file_count']
        size_mb = stat['total_size_mb']
        total_files += files
        total_size_mb += size_mb
        
        # Visual bar for size
        max_size = max([s['total_size_mb'] for s in stats.values()]) or 1
        bar_length = int((size_mb / max_size) * 20) if max_size > 0 else 0
        bar = "█" * bar_length + "░" * (20 - bar_length)
        
        print(f"{storage_type:10} │{bar}│ {files:3d} files │ {size_mb:6.2f} MB")
    
    print("-" * 50)
    print(f"{'TOTAL':10} │{'█' * 20}│ {total_files:3d} files │ {total_size_mb:6.2f} MB")
    
    # Git Ignore Status
    print(f"\n🚫 GIT IGNORE STATUS")
    print("-" * 30)
    
    gitignore_path = storage_root.parent / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        ignored_patterns = [
            "storage/os/*",
            "storage/cache/*", 
            "storage/logs/*"
        ]
        
        for pattern in ignored_patterns:
            if pattern in gitignore_content:
                print(f"✅ {pattern}")
            else:
                print(f"❌ {pattern} - NOT IGNORED!")
    else:
        print("❌ .gitignore file not found")
    
    # Environment Information
    print(f"\n🌍 ENVIRONMENT")
    print("-" * 30)
    
    env_vars = [
        "USER", "HOME", "PWD", "SHELL", 
        "XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE", "DISPLAY"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"{var:18}: {value}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 30)
    
    recommendations = []
    
    # Check if OS files are being ignored
    if "storage/os/*" not in gitignore_content:
        recommendations.append("Add 'storage/os/*' to .gitignore")
    
    # Check storage sizes
    if total_size_mb > 100:
        recommendations.append("Consider cleaning up old files (>100MB total)")
    
    # Check for empty directories
    empty_dirs = []
    for storage_type, stat in stats.items():
        if stat['file_count'] == 0 and storage_type not in ['logs', 'cache']:
            empty_dirs.append(storage_type)
    
    if empty_dirs:
        recommendations.append(f"Empty storage directories: {', '.join(empty_dirs)}")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ Storage system looks good!")
    
    print(f"\n🎯 SUMMARY")
    print("-" * 30)
    print(f"OS ID: {storage_manager.get_os_id()}")
    print(f"Storage Root: {storage_root}")
    print(f"Total Files: {total_files}")
    print(f"Total Size: {total_size_mb:.2f} MB")
    print(f"System: {storage_manager.get_os_info().get('pretty_name', 'Unknown')}")
    
    print(f"\n✅ Storage information complete!")

if __name__ == "__main__":
    main()