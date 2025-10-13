#!/usr/bin/env python3
"""
MARK-I Context Integration Demo

This demonstrates the key use cases for the Enhanced System Context Collection:
1. User runs app -> Collector gathers context once
2. AI wants to know -> Collector provides cached data instantly  
3. New chat session -> Send complete system profile to AI
4. Task execution -> Provide relevant context for intelligent decisions
"""

import json
import time
from datetime import datetime
from pathlib import Path

from mark_i.context.context_manager import ContextManager
from mark_i.context.collectors.hardware_collector import HardwareCollector
from mark_i.context.collectors.application_collector import ApplicationCollector
from mark_i.context.collectors.ui_collector import UICollector
from mark_i.context.collectors.network_collector import NetworkCollector
from mark_i.context.collectors.user_collector import UserCollector


class MarkIContextIntegration:
    """Demonstrates MARK-I context integration for AI assistance"""
    
    def __init__(self):
        self.context_manager = ContextManager()
        self._setup_collectors()
        
    def _setup_collectors(self):
        """Setup all context collectors"""
        collectors = [
            HardwareCollector(),
            ApplicationCollector(), 
            UICollector(),
            NetworkCollector(),
            UserCollector()
        ]
        
        for collector in collectors:
            self.context_manager.register_collector(collector)
    
    def use_case_1_app_startup_context_gathering(self):
        """
        USE CASE 1: User runs MARK-I app -> Collector gathers context once
        This happens when MARK-I starts up and needs to understand the environment
        """
        print("🚀 USE CASE 1: App Startup - Initial Context Gathering")
        print("=" * 60)
        
        print("📱 MARK-I starting up...")
        print("🔍 Gathering comprehensive system context...")
        
        start_time = time.time()
        context_data = self.context_manager.collect_all()
        collection_time = time.time() - start_time
        
        print(f"✅ Context collected in {collection_time:.2f} seconds")
        print(f"📊 Data from {context_data['collectors_count']} collectors")
        print(f"💾 Cached for future AI queries")
        
        # Show what was collected
        self._show_context_summary(context_data)
        
        return context_data
    
    def use_case_2_ai_requests_context(self):
        """
        USE CASE 2: AI wants to know system info -> Collector provides cached data instantly
        This happens during task execution when AI needs environmental context
        """
        print("\n🤖 USE CASE 2: AI Requests Context Data")
        print("=" * 60)
        
        print("🧠 AI: 'I need to understand the current system environment'")
        
        start_time = time.time()
        # Get cached context (should be instant)
        context_data = self.context_manager.get_current_context()
        response_time = time.time() - start_time
        
        if context_data:
            print(f"⚡ Context provided in {response_time*1000:.1f}ms (from cache)")
            print("📋 AI now has complete environmental awareness:")
            
            # Extract key info for AI
            ai_context = self._prepare_ai_context(context_data)
            print(json.dumps(ai_context, indent=2))
        else:
            print("❌ No cached context available - collecting fresh data...")
            context_data = self.context_manager.collect_all()
            ai_context = self._prepare_ai_context(context_data)
        
        return ai_context
    
    def use_case_3_new_chat_session_profile(self):
        """
        USE CASE 3: New chat session -> Send complete system profile to AI
        This happens when user starts a new conversation with MARK-I
        """
        print("\n💬 USE CASE 3: New Chat Session - System Profile")
        print("=" * 60)
        
        print("👤 User: Starting new chat session...")
        print("🤖 MARK-I: Preparing system profile for AI context...")
        
        # Get current context
        context_data = self.context_manager.get_current_context()
        if not context_data:
            print("🔄 No recent context - gathering fresh data...")
            context_data = self.context_manager.collect_all()
        
        # Create comprehensive system profile for AI
        system_profile = self._create_system_profile(context_data)
        
        print("📤 Sending system profile to AI:")
        print("-" * 40)
        print(f"🖥️  System: {system_profile['system_info']}")
        print(f"⚡ Hardware: {system_profile['hardware_summary']}")
        print(f"🌐 Network: {system_profile['network_status']}")
        print(f"👤 User: {system_profile['user_context']}")
        print(f"🛠️  Environment: {system_profile['development_environment']}")
        
        # Simulate AI receiving this context
        ai_prompt = self._create_ai_initialization_prompt(system_profile)
        print(f"\n🧠 AI Context Prompt:")
        print("-" * 40)
        print(ai_prompt)
        
        return system_profile
    
    def use_case_4_task_execution_context(self, user_task: str):
        """
        USE CASE 4: Task execution -> Provide relevant context for intelligent decisions
        This happens when user gives MARK-I a specific task to perform
        """
        print(f"\n🎯 USE CASE 4: Task Execution with Context")
        print("=" * 60)
        
        print(f"👤 User Task: '{user_task}'")
        print("🤖 MARK-I: Analyzing task and gathering relevant context...")
        
        # Get current context
        context_data = self.context_manager.get_current_context()
        
        # Extract task-relevant context
        relevant_context = self._extract_task_relevant_context(user_task, context_data)
        
        print("📋 Task-Relevant Context:")
        for key, value in relevant_context.items():
            print(f"   {key}: {value}")
        
        # Create AI prompt with task and context
        ai_task_prompt = self._create_task_execution_prompt(user_task, relevant_context)
        print(f"\n🧠 AI Task Prompt:")
        print("-" * 40)
        print(ai_task_prompt)
        
        return relevant_context
    
    def use_case_5_continuous_monitoring(self):
        """
        USE CASE 5: Continuous monitoring -> Update context as system changes
        This demonstrates background context updates
        """
        print(f"\n🔄 USE CASE 5: Continuous Context Monitoring")
        print("=" * 60)
        
        print("⏰ Starting background context monitoring...")
        
        # Start background collection (every 30 seconds)
        self.context_manager.start_background_collection(interval=30)
        
        print("✅ Background monitoring active")
        print("📊 Context will be updated every 30 seconds")
        print("🔍 Changes in system state will be automatically detected")
        
        # Simulate some time passing
        print("\n⏳ Simulating system changes over time...")
        for i in range(3):
            time.sleep(2)  # Shortened for demo
            print(f"   📈 Monitoring cycle {i+1}/3...")
        
        # Stop background monitoring
        self.context_manager.stop_background_collection()
        print("⏹️  Background monitoring stopped")
    
    def _show_context_summary(self, context_data):
        """Show a summary of collected context"""
        print("\n📊 Context Summary:")
        print("-" * 30)
        
        for collector_key, data in context_data.get('context', {}).items():
            if 'error' in data:
                print(f"❌ {collector_key}: {data['error']}")
            else:
                collector_name = data.get('_metadata', {}).get('collector', collector_key)
                print(f"✅ {collector_name}: Data collected")
    
    def _prepare_ai_context(self, context_data):
        """Prepare context data for AI consumption"""
        ai_context = {
            'timestamp': context_data.get('collection_timestamp'),
            'system_capabilities': {},
            'current_state': {},
            'user_environment': {}
        }
        
        # Extract key information for AI
        for collector_key, data in context_data.get('context', {}).items():
            if 'hardware' in collector_key and 'error' not in data:
                ai_context['system_capabilities']['hardware'] = {
                    'cpu_cores': data.get('cpu', {}).get('cores_logical', 0),
                    'memory_gb': data.get('memory', {}).get('total_gb', 0),
                    'gpu_available': len(data.get('gpu', [])) > 0
                }
            elif 'network' in collector_key and 'error' not in data:
                ai_context['current_state']['network'] = {
                    'online': data.get('connectivity', {}).get('internet_available', False),
                    'quality': data.get('connectivity', {}).get('connection_quality', 'unknown')
                }
            elif 'user' in collector_key and 'error' not in data:
                ai_context['user_environment'] = {
                    'username': data.get('profile', {}).get('username', 'unknown'),
                    'current_directory': data.get('working_context', {}).get('current_directory', 'unknown')
                }
        
        return ai_context
    
    def _create_system_profile(self, context_data):
        """Create comprehensive system profile for new chat sessions"""
        profile = {
            'system_info': 'Unknown System',
            'hardware_summary': 'Unknown Hardware',
            'network_status': 'Unknown Network',
            'user_context': 'Unknown User',
            'development_environment': 'Unknown Environment'
        }
        
        for collector_key, data in context_data.get('context', {}).items():
            if 'hardware' in collector_key and 'error' not in data:
                cpu = data.get('cpu', {})
                memory = data.get('memory', {})
                profile['hardware_summary'] = f"{cpu.get('cores_logical', 0)}-core CPU, {memory.get('total_gb', 0):.1f}GB RAM"
                
                system = data.get('system', {})
                profile['system_info'] = f"{system.get('platform', 'Unknown')} {system.get('platform_release', '')}"
                
            elif 'network' in collector_key and 'error' not in data:
                conn = data.get('connectivity', {})
                if conn.get('internet_available'):
                    quality = conn.get('connection_quality', 'unknown')
                    latency = conn.get('latency_ms', 0)
                    profile['network_status'] = f"Online ({quality}, {latency}ms latency)"
                else:
                    profile['network_status'] = "Offline"
                    
            elif 'user' in collector_key and 'error' not in data:
                user_profile = data.get('profile', {})
                working_context = data.get('working_context', {})
                profile['user_context'] = f"User: {user_profile.get('username', 'unknown')}"
                
                dev_tools = working_context.get('development_tools', [])
                if dev_tools:
                    profile['development_environment'] = f"Development tools: {', '.join(dev_tools[:5])}"
                else:
                    profile['development_environment'] = "Standard user environment"
        
        return profile
    
    def _create_ai_initialization_prompt(self, system_profile):
        """Create AI initialization prompt with system context"""
        return f"""
MARK-I System Context for New Session:

System Information:
- Platform: {system_profile['system_info']}
- Hardware: {system_profile['hardware_summary']}
- Network: {system_profile['network_status']}
- User: {system_profile['user_context']}
- Environment: {system_profile['development_environment']}

Instructions for AI:
- Use this context to provide intelligent, system-aware assistance
- Adapt suggestions based on available hardware capabilities
- Consider network status for cloud-based operations
- Personalize responses based on user environment
- Leverage development tools when suggesting automation solutions

Ready to assist with context-aware automation and intelligent task execution.
"""
    
    def _extract_task_relevant_context(self, task, context_data):
        """Extract context relevant to the specific task"""
        relevant = {}
        
        task_lower = task.lower()
        
        # Determine what context is relevant based on task keywords
        if any(word in task_lower for word in ['automate', 'script', 'code', 'develop']):
            relevant['task_type'] = 'development'
            # Include development tools, current directory, etc.
            
        elif any(word in task_lower for word in ['network', 'internet', 'download', 'upload']):
            relevant['task_type'] = 'network_operation'
            # Include network status, connectivity, etc.
            
        elif any(word in task_lower for word in ['performance', 'cpu', 'memory', 'system']):
            relevant['task_type'] = 'system_operation'
            # Include hardware specs, current usage, etc.
        
        # Extract relevant context from collected data
        if context_data:
            for collector_key, data in context_data.get('context', {}).items():
                if 'error' not in data:
                    if relevant.get('task_type') == 'development' and 'user' in collector_key:
                        relevant['current_directory'] = data.get('working_context', {}).get('current_directory')
                        relevant['development_tools'] = data.get('working_context', {}).get('development_tools', [])
                    elif relevant.get('task_type') == 'network_operation' and 'network' in collector_key:
                        relevant['internet_available'] = data.get('connectivity', {}).get('internet_available')
                        relevant['connection_quality'] = data.get('connectivity', {}).get('connection_quality')
                    elif relevant.get('task_type') == 'system_operation' and 'hardware' in collector_key:
                        relevant['cpu_usage'] = data.get('cpu', {}).get('usage_percent')
                        relevant['memory_usage'] = data.get('memory', {}).get('usage_percent')
        
        return relevant
    
    def _create_task_execution_prompt(self, task, relevant_context):
        """Create AI prompt for task execution with relevant context"""
        return f"""
MARK-I Task Execution Request:

User Task: "{task}"

Relevant System Context:
{json.dumps(relevant_context, indent=2)}

Instructions for AI:
- Analyze the task requirements against available system capabilities
- Use the provided context to make intelligent automation decisions
- Suggest the most appropriate tools and approaches for this environment
- Consider system limitations and optimize for current conditions
- Provide step-by-step guidance tailored to this specific setup

Execute task with full environmental awareness.
"""


def main():
    """Demonstrate all MARK-I context integration use cases"""
    print("🤖 MARK-I Enhanced Context Integration Demo")
    print("=" * 80)
    
    integration = MarkIContextIntegration()
    
    # USE CASE 1: App startup context gathering
    context_data = integration.use_case_1_app_startup_context_gathering()
    
    # USE CASE 2: AI requests context
    ai_context = integration.use_case_2_ai_requests_context()
    
    # USE CASE 3: New chat session profile
    system_profile = integration.use_case_3_new_chat_session_profile()
    
    # USE CASE 4: Task execution with context
    integration.use_case_4_task_execution_context("Help me automate my Python development workflow")
    
    # USE CASE 5: Continuous monitoring
    integration.use_case_5_continuous_monitoring()
    
    print(f"\n🎉 All use cases demonstrated successfully!")
    print("🚀 MARK-I context system is ready for intelligent AI integration!")


if __name__ == "__main__":
    main()