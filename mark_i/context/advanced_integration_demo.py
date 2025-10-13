"""
Advanced Context-Driven Decision Making Demo

This demo showcases the advanced context-driven decision making and optimization
capabilities including adaptive decision engine, context history tracking,
and pattern recognition for intelligent system adaptation.
"""

import logging
import time

from mark_i.core.architecture_config import ComponentConfig
from mark_i.context.environment_monitor import EnvironmentMonitor
from mark_i.context.system_context_integration import SystemContextIntegration
from mark_i.context.context_driven_optimizer import ContextDrivenOptimizer
from mark_i.context.adaptive_decision_engine import AdaptiveDecisionEngine, DecisionCriteriaWeights
from mark_i.context.context_history_tracker import ContextHistoryTracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_adaptive_decision_making():
    """Demonstrate advanced adaptive decision making capabilities."""
    print("🧠 MARK-I Advanced Context-Driven Decision Making Demo")
    print("=" * 65)

    try:
        # Create configuration
        config = ComponentConfig()
        config.monitoring_interval = 3.0
        config.decision_interval = 8.0
        config.learning_mode = "hybrid"
        config.confidence_threshold = 0.5

        # Initialize components
        print("\n📊 Initializing Advanced Context Components...")
        env_monitor = EnvironmentMonitor(config)
        context_integration = SystemContextIntegration(config)
        optimizer = ContextDrivenOptimizer(config, env_monitor)
        decision_engine = AdaptiveDecisionEngine(config, env_monitor, optimizer)
        history_tracker = ContextHistoryTracker(config)

        # Start all components
        print("\n🚀 Starting Advanced Context System...")
        components = [
            ("Environment Monitor", env_monitor.start_monitoring),
            ("Context Integration", context_integration.start_integration),
            ("Optimizer", optimizer.start_optimization),
            ("Decision Engine", decision_engine.start_decision_making),
            ("History Tracker", history_tracker.start_tracking),
        ]

        for name, start_func in components:
            if start_func():
                print(f"✅ {name} started")
            else:
                print(f"❌ Failed to start {name}")
                return

        # Let the system collect initial data
        print("\n⏳ Collecting initial context data (20 seconds)...")
        time.sleep(20)

        # Demonstrate decision making
        print("\n🎯 Advanced Decision Making Analysis:")
        print("-" * 50)

        # Get current context
        current_env = env_monitor.get_current_environment()
        if current_env:
            # Add context to history tracker
            history_tracker.add_context_snapshot(current_env)

            # Make a contextual decision
            decision = decision_engine.make_contextual_decision("system_optimization", current_env)

            print(f"Decision Type: {decision.decision_type}")
            print(f"Selected Alternative: {decision.selected_alternative.get('type', 'unknown')}")
            print(f"Overall Score: {decision.overall_score:.3f}")
            print(f"Confidence: {decision.confidence.value}")
            print(f"Reasoning:")
            for reason in decision.reasoning[:3]:
                print(f"  - {reason}")

            # Show criteria scores
            print(f"\nCriteria Evaluation:")
            for criteria, score in decision.criteria_scores.items():
                print(f"  {criteria.value}: {score:.3f}")

            # Execute the decision
            if decision_engine.execute_decision(decision):
                print(f"\n✅ Decision executed successfully")

                # Simulate feedback after some time
                time.sleep(5)

                # Provide positive feedback
                feedback_outcomes = {"performance_improvement": 0.3, "resource_efficiency": 0.4, "user_satisfaction": 0.7}
                decision_engine.provide_feedback(decision.decision_id, 0.8, feedback_outcomes)
                print(f"📝 Provided feedback: score=0.8")
            else:
                print(f"❌ Failed to execute decision")

        # Demonstrate pattern detection
        print("\n🔍 Pattern Detection and Learning:")
        print("-" * 50)

        # Add more context snapshots to enable pattern detection
        for i in range(10):
            current_env = env_monitor.get_current_environment()
            if current_env:
                history_tracker.add_context_snapshot(current_env)
            time.sleep(2)

        # Detect patterns
        patterns = history_tracker.detect_patterns()
        if patterns:
            print(f"Detected {len(patterns)} new patterns:")
            for pattern in patterns[:3]:
                print(f"  - {pattern.pattern_type.value}: {pattern.description}")
                print(f"    Confidence: {pattern.confidence:.3f}, Frequency: {pattern.frequency.value}")
        else:
            print("No new patterns detected (need more data)")

        # Show decision insights
        print("\n📈 Decision Engine Insights:")
        print("-" * 50)

        insights = decision_engine.get_decision_insights()
        stats = insights.get("decision_statistics", {})
        performance = insights.get("performance_metrics", {})

        print(f"Total Decisions: {stats.get('total_decisions', 0)}")
        print(f"Success Rate: {stats.get('success_rate', 0):.2f}")
        print(f"Average Confidence: {performance.get('average_confidence', 0):.2f}")
        print(f"Patterns Learned: {stats.get('patterns_learned', 0)}")

        # Show criteria analysis
        criteria_analysis = insights.get("criteria_analysis", {})
        if criteria_analysis:
            print(f"\nTop Performing Criteria:")
            sorted_criteria = sorted(criteria_analysis.items(), key=lambda x: x[1].get("average_score", 0), reverse=True)
            for criteria, data in sorted_criteria[:3]:
                print(f"  {criteria}: avg_score={data.get('average_score', 0):.3f}, " f"weight={data.get('weight', 0):.3f}")

        # Demonstrate criteria adaptation
        print("\n⚙️  Adaptive Criteria Weighting:")
        print("-" * 50)

        # Create custom criteria weights
        custom_weights = DecisionCriteriaWeights()
        custom_weights.performance = 0.4  # Emphasize performance
        custom_weights.efficiency = 0.3  # Emphasize efficiency
        custom_weights.stability = 0.2
        custom_weights.user_experience = 0.1

        decision_engine.adapt_decision_criteria(custom_weights)
        print("✅ Adapted decision criteria to emphasize performance and efficiency")

        # Make another decision with new criteria
        time.sleep(3)
        current_env = env_monitor.get_current_environment()
        if current_env:
            adapted_decision = decision_engine.make_contextual_decision("performance_optimization", current_env)
            print(f"\nAdapted Decision:")
            print(f"  Strategy: {adapted_decision.selected_alternative.get('strategy', 'unknown')}")
            print(f"  Performance Score: {adapted_decision.criteria_scores.get('performance', 0):.3f}")
            print(f"  Efficiency Score: {adapted_decision.criteria_scores.get('efficiency', 0):.3f}")

        # Demonstrate context predictions
        print("\n🔮 Context Predictions:")
        print("-" * 50)

        predictions = history_tracker.predict_context_changes(horizon_minutes=15)
        if predictions:
            print(f"Generated {len(predictions)} predictions:")
            for pred in predictions[:2]:
                print(f"  - {pred.get('description', 'Unknown prediction')}")
                print(f"    Confidence: {pred.get('confidence', 0):.3f}")
                print(f"    Type: {pred.get('prediction_type', 'unknown')}")
        else:
            print("No predictions available (need more historical data)")

        # Show context summary
        print("\n📊 Context History Summary:")
        print("-" * 50)

        summary = history_tracker.get_context_summary(time_range_hours=1)
        if "error" not in summary:
            print(f"Snapshots Analyzed: {summary.get('snapshots_analyzed', 0)}")

            system_metrics = summary.get("system_metrics", {})
            cpu_stats = system_metrics.get("cpu_usage", {})
            memory_stats = system_metrics.get("memory_usage", {})

            print(f"CPU Usage: avg={cpu_stats.get('average', 0):.1f}%, " f"max={cpu_stats.get('max', 0):.1f}%")
            print(f"Memory Usage: avg={memory_stats.get('average', 0):.1f}%, " f"max={memory_stats.get('max', 0):.1f}%")

            top_apps = summary.get("top_applications", [])
            if top_apps:
                print(f"Top Applications:")
                for app in top_apps[:3]:
                    print(f"  - {app['name']}: {app['frequency']} occurrences")

        # Let the system run for final observations
        print("\n⏳ Final system observation (10 seconds)...")
        time.sleep(10)

        # Show final statistics
        print("\n📈 Final System Statistics:")
        print("-" * 50)

        final_insights = decision_engine.get_decision_insights()
        final_stats = final_insights.get("decision_statistics", {})

        print(f"Total Decisions Made: {final_stats.get('total_decisions', 0)}")
        print(f"Successful Decisions: {final_stats.get('successful_decisions', 0)}")
        print(f"Final Success Rate: {final_stats.get('success_rate', 0):.2f}")
        print(f"Adaptations Performed: {final_stats.get('adaptations_performed', 0)}")

        pattern_insights = history_tracker.get_pattern_insights()
        if "error" not in pattern_insights:
            print(f"Total Patterns Detected: {pattern_insights.get('total_patterns', 0)}")

            recent_patterns = pattern_insights.get("recent_patterns", [])
            if recent_patterns:
                print(f"Recent Patterns:")
                for pattern in recent_patterns[:2]:
                    print(f"  - {pattern['type']}: {pattern['description']}")

    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")

    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        try:
            cleanup_components = [
                ("Decision Engine", decision_engine.stop_decision_making if "decision_engine" in locals() else None),
                ("History Tracker", history_tracker.stop_tracking if "history_tracker" in locals() else None),
                ("Optimizer", optimizer.stop_optimization if "optimizer" in locals() else None),
                ("Context Integration", context_integration.stop_integration if "context_integration" in locals() else None),
                ("Environment Monitor", env_monitor.stop_monitoring if "env_monitor" in locals() else None),
            ]

            for name, stop_func in cleanup_components:
                if stop_func:
                    stop_func()
                    print(f"✅ {name} stopped")

        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    print("\n🎉 Advanced Context-Driven Decision Making Demo Complete!")


def demo_multi_criteria_decision_making():
    """Demonstrate multi-criteria decision making capabilities."""
    print("\n🎯 Multi-Criteria Decision Making Demo")
    print("=" * 45)

    try:
        config = ComponentConfig()
        config.max_alternatives = 4
        config.confidence_threshold = 0.4

        env_monitor = EnvironmentMonitor(config)
        optimizer = ContextDrivenOptimizer(config, env_monitor)
        decision_engine = AdaptiveDecisionEngine(config, env_monitor, optimizer)

        print("Starting multi-criteria decision system...")
        env_monitor.start_monitoring()
        decision_engine.start_decision_making()

        time.sleep(10)  # Let system initialize

        # Get context and make decision
        context = env_monitor.get_current_environment()
        if context:
            print("\n🔍 Evaluating Multiple Alternatives:")

            decision = decision_engine.make_contextual_decision("resource_optimization", context)

            print(f"Alternatives Considered: {len(decision.alternatives)}")
            print(f"Selected: {decision.selected_alternative.get('type', 'unknown')}")

            # Show detailed criteria evaluation
            print(f"\nDetailed Criteria Scores:")
            for criteria, score in decision.criteria_scores.items():
                print(f"  {criteria.value.replace('_', ' ').title()}: {score:.3f}")

            print(f"\nDecision Reasoning:")
            for i, reason in enumerate(decision.reasoning, 1):
                print(f"  {i}. {reason}")

            # Show expected outcomes
            if decision.expected_outcomes:
                print(f"\nExpected Outcomes:")
                for outcome, value in decision.expected_outcomes.items():
                    print(f"  {outcome.replace('_', ' ').title()}: {value:+.3f}")

    except Exception as e:
        logger.error(f"Multi-criteria demo error: {e}")

    finally:
        try:
            if "decision_engine" in locals():
                decision_engine.stop_decision_making()
            if "env_monitor" in locals():
                env_monitor.stop_monitoring()
        except:
            pass


if __name__ == "__main__":
    # Run the main advanced demo
    demo_adaptive_decision_making()

    # Run multi-criteria decision making demo
    demo_multi_criteria_decision_making()
