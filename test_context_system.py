#!/usr/bin/env python3
"""
Test script for the Enhanced System Context Collection System

This script demonstrates the comprehensive context awareness capabilities
that will provide rich environmental data to MARK-I's AI for intelligent
automation decisions.
"""

import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the context system
from mark_i.context.context_manager import ContextManager
from mark_i.context.collectors.hardware_collector import HardwareCollector
from mark_i.context.collectors.application_collector import ApplicationCollector
from mark_i.context.collectors.ui_collector import UICollector
from mark_i.context.collectors.network_collector import NetworkCollector
from mark_i.context.collectors.user_collector import UserCollector


def main():
    """Test the complete context collection system"""
    print("🚀 MARK-I Enhanced System Context Collection Test")
    print("=" * 60)
    
    # Initialize the context manager
    context_manager = ContextManager()
    
    # Register all collectors
    collectors = [
        HardwareCollector(),
        ApplicationCollector(),
        UICollector(),
        NetworkCollector(),
        UserCollector()
    ]
    
    print(f"📋 Registering {len(collectors)} context collectors...")
    for collector in collectors:
        context_manager.register_collector(collector)
        print(f"   ✅ {collector.name}")
    
    print(f"\n🔍 Collecting comprehensive system context...")
    
    # Collect all context data
    try:
        context_data = context_manager.collect_all()
        
        print(f"✅ Context collection completed!")
        print(f"📊 Collected data from {context_data['collectors_count']} collectors")
        print(f"⏰ Collection timestamp: {context_data['collection_timestamp']}")
        
        # Display summary of collected data
        print(f"\n📈 Context Data Summary:")
        print("-" * 40)
        
        for collector_key, data in context_data['context'].items():
            collector_name = data.get('_metadata', {}).get('collector', collector_key)
            
            if 'error' in data:
                print(f"❌ {collector_name}: ERROR - {data['error']}")
            else:
                print(f"✅ {collector_name}: SUCCESS")
                
                # Show key metrics for each collector
                if 'hardware' in collector_key.lower():
                    show_hardware_summary(data)
                elif 'application' in collector_key.lower():
                    show_application_summary(data)
                elif 'ui' in collector_key.lower():
                    show_ui_summary(data)
                elif 'network' in collector_key.lower():
                    show_network_summary(data)
                elif 'user' in collector_key.lower():
                    show_user_summary(data)
        
        # Save detailed context to file
        output_file = Path("context_collection_test.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed context data saved to: {output_file}")
        print(f"📁 File size: {output_file.stat().st_size / 1024:.1f} KB")
        
        # Show how this data would be used by AI
        print(f"\n🤖 AI Integration Preview:")
        print("-" * 40)
        show_ai_integration_example(context_data)
        
        print(f"\n🎉 Context collection system test completed successfully!")
        print(f"🔧 MARK-I now has comprehensive environmental awareness!")
        
    except Exception as e:
        print(f"❌ Context collection failed: {str(e)}")
        import traceback
        traceback.print_exc()


def show_hardware_summary(data):
    """Show hardware context summary"""
    if 'cpu' in data:
        cpu = data['cpu']
        print(f"   🖥️  CPU: {cpu.get('model', 'Unknown')} ({cpu.get('cores_logical', 0)} cores)")
        print(f"       Usage: {cpu.get('usage_percent', 0):.1f}%")
    
    if 'memory' in data:
        memory = data['memory']
        print(f"   💾 Memory: {memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 0):.1f}GB ({memory.get('usage_percent', 0):.1f}%)")
    
    if 'gpu' in data and data['gpu']:
        gpu_count = len([gpu for gpu in data['gpu'] if 'error' not in gpu])
        print(f"   🎮 GPUs: {gpu_count} detected")
    
    if 'displays' in data and data['displays']:
        display_count = len([d for d in data['displays'] if d.get('connected', False)])
        print(f"   🖥️  Displays: {display_count} connected")


def show_application_summary(data):
    """Show application context summary"""
    if 'installed' in data:
        total_apps = sum(len(apps) for apps in data['installed'].values())
        print(f"   📱 Installed Apps: {total_apps} total")
        
        for category, apps in data['installed'].items():
            if apps and category != 'other':
                print(f"       {category.title()}: {len(apps)}")
    
    if 'running' in data:
        running_count = len(data['running'])
        print(f"   🏃 Running Processes: {running_count}")


def show_ui_summary(data):
    """Show UI context summary"""
    if 'desktop_environment' in data:
        de = data['desktop_environment']
        print(f"   🖥️  Desktop: {de.get('name', 'Unknown')} ({de.get('session_type', 'Unknown')})")
    
    if 'window_manager' in data:
        wm = data['window_manager']
        print(f"   🪟 Window Manager: {wm.get('name', 'Unknown')}")
    
    if 'active_windows' in data:
        window_count = len(data['active_windows'])
        print(f"   📱 Active Windows: {window_count}")


def show_network_summary(data):
    """Show network context summary"""
    if 'connectivity' in data:
        conn = data['connectivity']
        status = "🟢 Online" if conn.get('internet_available') else "🔴 Offline"
        print(f"   🌐 Internet: {status}")
        
        if conn.get('latency_ms'):
            print(f"       Latency: {conn['latency_ms']:.1f}ms ({conn.get('connection_quality', 'unknown')})")
    
    if 'interfaces' in data:
        active_interfaces = len([iface for iface in data['interfaces'] if iface.get('is_up')])
        print(f"   🔌 Network Interfaces: {active_interfaces} active")
    
    if 'vpn' in data and data['vpn'].get('active'):
        print(f"   🔒 VPN: Active")


def show_user_summary(data):
    """Show user context summary"""
    if 'profile' in data:
        profile = data['profile']
        print(f"   👤 User: {profile.get('username', 'Unknown')} ({profile.get('real_name', '')})")
        print(f"       Groups: {len(profile.get('groups', []))}")
    
    if 'working_context' in data:
        context = data['working_context']
        print(f"   📁 Current Dir: {context.get('current_directory', 'Unknown')}")
        
        if 'active_projects' in context:
            project_count = len(context['active_projects'])
            print(f"       Active Projects: {project_count}")


def show_ai_integration_example(context_data):
    """Show how this context data would be used by AI"""
    print("When MARK-I receives a task, it will send this rich context to the AI:")
    print()
    
    # Create a sample AI prompt with context
    ai_context = {
        "system_info": "Ubuntu 24.04 LTS with GNOME desktop",
        "hardware": "Multi-core CPU with sufficient memory",
        "network": "Online with good connectivity",
        "applications": "Development environment with code editors and terminals",
        "user_context": "Active developer working on Python projects"
    }
    
    sample_prompt = f"""
MARK-I System Context:
{json.dumps(ai_context, indent=2)}

User Task: "Help me automate my development workflow"

With this context, the AI can:
- Understand the user's Ubuntu/GNOME environment
- Know what development tools are available
- Adapt automation for the specific hardware capabilities
- Consider network connectivity for cloud operations
- Personalize suggestions based on user behavior patterns
"""
    
    print(sample_prompt)
    print("🎯 This enables intelligent, context-aware automation decisions!")


if __name__ == "__main__":
    main()