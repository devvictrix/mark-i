#!/usr/bin/env python3
"""
MARK-I AI Integration Example

Simple example showing how to use the production-ready AI context integration.
"""

from mark_i.context import get_ai_context_provider

def main():
    """Demonstrate simple AI context integration"""
    print("🤖 MARK-I AI Context Integration Example")
    print("=" * 50)
    
    # Get the AI context provider
    ai_context = get_ai_context_provider()
    
    print("✅ AI Context Provider initialized")
    
    # Example 1: Get system profile for new chat session
    print("\n📋 System Profile for AI:")
    print("-" * 30)
    system_profile = ai_context.get_system_profile_for_ai()
    
    print(f"🖥️  System: {system_profile['system']['platform']} {system_profile['system']['version']}")
    print(f"⚡ Hardware: {system_profile['hardware']['cpu_cores']}-core CPU, {system_profile['hardware']['memory_total_gb']:.1f}GB RAM")
    print(f"🌐 Network: {'🟢 Online' if system_profile['network']['internet_available'] else '🔴 Offline'}")
    print(f"👤 User: {system_profile['user']['username']}")
    print(f"📁 Directory: {system_profile['user']['current_directory']}")
    
    # Example 2: Create AI prompt with context
    print("\n🧠 AI Prompt with Context:")
    print("-" * 30)
    user_task = "Help me set up a Python development environment"
    ai_prompt = ai_context.create_ai_prompt_with_context(user_task, include_full_context=True)
    
    print(ai_prompt)
    
    # Example 3: Get task-specific context
    print("\n🎯 Task-Specific Context:")
    print("-" * 30)
    task_context = ai_context.get_task_context_for_ai("Write a Python script to automate file organization")
    
    print(f"Task Category: {task_context['task_category']}")
    print(f"Available Tools: {task_context['capabilities'].get('development_tools', [])[:5]}")
    print(f"Working Directory: {task_context['current_state'].get('working_directory', 'Unknown')}")
    
    print("\n🎉 AI integration ready!")
    print("🚀 MARK-I can now provide intelligent, context-aware assistance!")

if __name__ == "__main__":
    main()