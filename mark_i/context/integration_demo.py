"""
Enhanced System Context Integration Demo

This demo shows how the enhanced context awareness and environment monitoring
components work together to provide comprehensive system understanding and
intelligent adaptation.
"""

import logging
import time
from typing import Dict, Any

from mark_i.core.architecture_config import ComponentConfig
from mark_i.context.environment_monitor import EnvironmentMonitor
from mark_i.context.system_context_integration import SystemContextIntegration
from mark_i.context.context_driven_optimizer import ContextDrivenOptimizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_enhanced_context_integration():
    """Demonstrate enhanced system context integration capabilities."""
    print("🤖 MARK-I Enhanced System Context Integration Demo")
    print("=" * 60)
    
    try:
        # Create configuration
        config = ComponentConfig()
        config.monitoring_interval = 5.0
        config.integration_mode = "active"
        config.context_scope = "comprehensive"
        
        # Initialize components
        print("\n📊 Initializing Environment Monitor...")
        env_monitor = EnvironmentMonitor(config)
        
        print("🔗 Initializing System Context Integration...")
        context_integration = SystemContextIntegration(config)
        
        print("⚡ Initializing Context-Driven Optimizer...")
        optimizer = ContextDrivenOptimizer(config, env_monitor)
        
        # Start monitoring
        print("\n🚀 Starting enhanced context monitoring...")
        if env_monitor.start_monitoring():
            print("✅ Environment monitoring started")
        else:
            print("❌ Failed to start environment monitoring")
            return
        
        if context_integration.start_integration():
            print("✅ System context integration started")
        else:
            print("❌ Failed to start system context integration")
            return
        
        if optimizer.start_optimization():
            print("✅ Context-driven optimization started")
        else:
            print("❌ Failed to start context-driven optimization")
            return
        
        # Let the system run for a bit to collect data
        print("\n⏳ Collecting system data for 15 seconds...")
        time.sleep(15)
        
        # Demonstrate capabilities
        print("\n📈 System Context Analysis:")
        print("-" * 40)
        
        # Get current environment
        current_env = env_monitor.get_current_environment()
        if current_env:
            system_metrics = current_env.get("system_metrics", {})
            print(f"CPU Usage: {system_metrics.get('cpu_usage', 0):.1f}%")
            print(f"Memory Usage: {system_metrics.get('memory_percent', 0):.1f}%")
            print(f"Active Applications: {len(current_env.get('applications', {}))}")
            print(f"System Health: {current_env.get('system_health', 'unknown')}")
        
        # Get application relationships
        relationships = env_monitor.get_application_relationships()
        print(f"\nApplication Relationships: {len(relationships)} discovered")
        
        # Show context integration status
        integration_summary = context_integration.get_context_summary()
        print(f"\nContext Integration Status:")
        print(f"  Mode: {integration_summary.get('integration_status', {}).get('mode', 'unknown')}")
        print(f"  Context Updates: {integration_summary.get('statistics', {}).get('context_updates', 0)}")
        print(f"  Adaptations Suggested: {integration_summary.get('statistics', {}).get('adaptations_suggested', 0)}")
        
        # Show optimization status
        opt_status = optimizer.get_optimization_status()
        print(f"\nOptimization Status:")
        print(f"  Current Strategy: {opt_status.get('current_state', {}).get('strategy', 'unknown')}")
        print(f"  Decisions Made: {opt_status.get('statistics', {}).get('decisions_made', 0)}")
        print(f"  Patterns Learned: {opt_status.get('statistics', {}).get('patterns_learned', 0)}")
        
        # Demonstrate change detection
        print("\n🔍 Change Detection:")
        print("-" * 40)
        changes = env_monitor.detect_environment_changes()
        if changes:
            print(f"Detected {len(changes)} environmental changes:")
            for change in changes[:3]:  # Show first 3 changes
                print(f"  - {change.get('type', 'unknown')}: {change.get('metric', 'N/A')} "
                      f"changed by {change.get('change', 0):.1f}")
        else:
            print("No significant changes detected")
        
        # Demonstrate optimization decision making
        print("\n🎯 Optimization Decision Making:")
        print("-" * 40)
        if current_env:
            decision = optimizer.make_optimization_decision(current_env)
            print(f"Recommended Strategy: {decision.strategy.value}")
            print(f"Context State: {decision.context_state.value}")
            print(f"Confidence: {decision.confidence:.2f}")
            print("Reasoning:")
            for reason in decision.reasoning[:3]:  # Show first 3 reasons
                print(f"  - {reason}")
        
        # Let the system run a bit more to show adaptation
        print("\n⏳ Monitoring adaptations for 10 more seconds...")
        time.sleep(10)
        
        # Show final statistics
        print("\n📊 Final Statistics:")
        print("-" * 40)
        
        final_integration_summary = context_integration.get_context_summary()
        final_opt_status = optimizer.get_optimization_status()
        
        print(f"Total Context Updates: {final_integration_summary.get('statistics', {}).get('context_updates', 0)}")
        print(f"Total Adaptations: {final_integration_summary.get('statistics', {}).get('adaptations_suggested', 0)}")
        print(f"Total Optimization Cycles: {final_opt_status.get('statistics', {}).get('optimization_cycles', 0)}")
        print(f"Success Rate: {final_opt_status.get('statistics', {}).get('recent_success_rate', 0):.2f}")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        try:
            if 'optimizer' in locals():
                optimizer.stop_optimization()
            if 'context_integration' in locals():
                context_integration.stop_integration()
            if 'env_monitor' in locals():
                env_monitor.stop_monitoring()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    print("\n🎉 Enhanced System Context Integration Demo Complete!")


def demo_context_pattern_learning():
    """Demonstrate context pattern learning capabilities."""
    print("\n🧠 Context Pattern Learning Demo")
    print("=" * 40)
    
    try:
        config = ComponentConfig()
        config.monitoring_interval = 2.0
        config.pattern_learning_enabled = True
        
        env_monitor = EnvironmentMonitor(config)
        optimizer = ContextDrivenOptimizer(config, env_monitor)
        
        print("Starting pattern learning monitoring...")
        env_monitor.start_monitoring()
        optimizer.start_optimization()
        
        # Simulate different usage patterns
        patterns_to_simulate = [
            "idle_period",
            "light_usage",
            "heavy_processing",
            "memory_intensive"
        ]
        
        for pattern in patterns_to_simulate:
            print(f"\n📋 Simulating {pattern} pattern...")
            time.sleep(5)  # Let the system observe the pattern
            
            # Get current optimization parameters
            current_env = env_monitor.get_current_environment()
            if current_env:
                optimal_params = optimizer.get_optimal_parameters(current_env)
                print(f"  Optimal monitoring frequency: {optimal_params.monitoring_frequency:.1f}s")
                print(f"  Processing intensity: {optimal_params.processing_intensity:.2f}")
        
        # Show learned patterns
        opt_status = optimizer.get_optimization_status()
        patterns_learned = opt_status.get('learned_patterns', 0)
        print(f"\n🎓 Learned {patterns_learned} context patterns")
        
    except Exception as e:
        logger.error(f"Pattern learning demo error: {e}")
    
    finally:
        try:
            if 'optimizer' in locals():
                optimizer.stop_optimization()
            if 'env_monitor' in locals():
                env_monitor.stop_monitoring()
        except:
            pass


if __name__ == "__main__":
    # Run the main demo
    demo_enhanced_context_integration()
    
    # Run pattern learning demo
    demo_context_pattern_learning()