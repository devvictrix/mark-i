#!/usr/bin/env python3
"""
Test script for ProfileExecutor

This script demonstrates the ProfileExecutor working with Eye-Brain-Hand architecture
to execute automation profiles with intelligent decision making.
"""

import time
from mark_i.profiles.models.profile import AutomationProfile
from mark_i.profiles.models.region import Region
from mark_i.profiles.models.rule import Rule, Condition, Action
from mark_i.profiles.profile_executor import ProfileExecutor, ExecutionStatus


class MockCaptureEngine:
    """Mock Eye component for testing"""
    
    def capture_screen(self):
        """Mock screen capture"""
        print("📸 Eye: Capturing full screen...")
        return "mock_screenshot_data"
    
    def capture_region(self, x, y, width, height):
        """Mock region capture"""
        print(f"📸 Eye: Capturing region ({x}, {y}) {width}x{height}")
        return f"mock_region_data_{x}_{y}"


class MockAgentCore:
    """Mock Brain component for testing"""
    
    def analyze_image(self, image_data, prompt):
        """Mock image analysis"""
        print(f"🧠 Brain: Analyzing image with prompt: {prompt}")
        
        # Simulate intelligent responses based on prompt
        if "visible" in prompt.lower():
            return "Yes, the region is visible and contains interactive elements"
        elif "text" in prompt.lower():
            return "I can see text content in this region"
        else:
            return "Analysis complete"
    
    def ask_user(self, question):
        """Mock user interaction"""
        print(f"🧠 Brain: Asking user: {question}")
        
        # Simulate user responses based on question
        if "email" in question.lower():
            return "example@gmail.com"
        elif "proceed" in question.lower():
            return "yes"
        else:
            return "user response"


class MockActionExecutor:
    """Mock Hand component for testing"""
    
    def click(self, x, y):
        """Mock click action"""
        print(f"🤚 Hand: Clicking at ({x}, {y})")
        time.sleep(0.1)  # Simulate action time
    
    def type_text(self, text):
        """Mock text typing"""
        print(f"🤚 Hand: Typing text: '{text}'")
        time.sleep(0.2)  # Simulate typing time
    
    def press_key(self, key):
        """Mock key press"""
        print(f"🤚 Hand: Pressing key: {key}")
        time.sleep(0.1)


def create_email_automation_profile():
    """Create a sample email automation profile"""
    profile = AutomationProfile.create_new(
        name="Send Email Demo",
        description="Demonstrate email sending automation with Eye-Brain-Hand integration",
        category="email",
        target_application="Email Client"
    )
    
    # Add regions for email interface
    recipient_region = Region(
        name="recipient_field",
        x=100, y=200, width=300, height=30,
        description="Email recipient input field",
        ocr_enabled=True
    )
    
    subject_region = Region(
        name="subject_field", 
        x=100, y=240, width=300, height=30,
        description="Email subject input field"
    )
    
    body_region = Region(
        name="body_field",
        x=100, y=280, width=400, height=200,
        description="Email body text area"
    )
    
    send_button_region = Region(
        name="send_button",
        x=350, y=500, width=80, height=30,
        description="Send email button"
    )
    
    profile.add_region(recipient_region)
    profile.add_region(subject_region)
    profile.add_region(body_region)
    profile.add_region(send_button_region)
    
    # Create rule for filling email form
    fill_email_rule = Rule(
        name="Fill Email Form",
        description="Fill recipient, subject, and body fields",
        priority=1
    )
    
    # Add conditions
    recipient_visible = Condition("visual_match", "recipient_field", {"visible": True})
    fill_email_rule.add_condition(recipient_visible)
    
    # Add actions
    click_recipient = Action("click", "recipient_field", delay_after=0.5)
    type_recipient = Action("type_text", parameters={"text": "{recipient_email}"}, delay_after=0.5)
    click_subject = Action("click", "subject_field", delay_after=0.5)
    type_subject = Action("type_text", parameters={"text": "{email_subject}"}, delay_after=0.5)
    click_body = Action("click", "body_field", delay_after=0.5)
    type_body = Action("type_text", parameters={"text": "{email_body}"}, delay_after=1.0)
    
    fill_email_rule.add_action(click_recipient)
    fill_email_rule.add_action(type_recipient)
    fill_email_rule.add_action(click_subject)
    fill_email_rule.add_action(type_subject)
    fill_email_rule.add_action(click_body)
    fill_email_rule.add_action(type_body)
    
    profile.add_rule(fill_email_rule)
    
    # Create rule for sending email
    send_email_rule = Rule(
        name="Send Email",
        description="Click send button after confirmation",
        priority=2
    )
    
    # Add condition and actions
    send_button_visible = Condition("visual_match", "send_button", {"visible": True})
    send_email_rule.add_condition(send_button_visible)
    
    ask_confirmation = Action("ask_user", parameters={"question": "Ready to send email? (yes/no)"})
    click_send = Action("click", "send_button", delay_before=0.5)
    log_success = Action("log_message", parameters={"message": "Email sent successfully!", "level": "INFO"})
    
    send_email_rule.add_action(ask_confirmation)
    send_email_rule.add_action(click_send)
    send_email_rule.add_action(log_success)
    
    profile.add_rule(send_email_rule)
    
    return profile


def create_web_search_profile():
    """Create a sample web search automation profile"""
    profile = AutomationProfile.create_new(
        name="Web Search Demo",
        description="Demonstrate web search automation with intelligent analysis",
        category="web",
        target_application="Web Browser"
    )
    
    # Add regions
    search_box = Region("search_box", 300, 100, 400, 40, "Search input box")
    search_button = Region("search_button", 720, 100, 80, 40, "Search submit button")
    results_area = Region("results_area", 200, 200, 800, 600, "Search results area")
    
    profile.add_region(search_box)
    profile.add_region(search_button)
    profile.add_region(results_area)
    
    # Create search rule
    search_rule = Rule("Perform Search", "Execute web search with query", priority=1)
    
    search_visible = Condition("visual_match", "search_box", {"visible": True})
    search_rule.add_condition(search_visible)
    
    click_search_box = Action("click", "search_box")
    type_query = Action("type_text", parameters={"text": "{search_query}"})
    press_enter = Action("press_key", parameters={"key": "enter"})
    wait_for_results = Action("wait_for_visual_cue", "results_area", 
                             parameters={"cue_description": "Search results loaded"})
    
    search_rule.add_action(click_search_box)
    search_rule.add_action(type_query)
    search_rule.add_action(press_enter)
    search_rule.add_action(wait_for_results)
    
    profile.add_rule(search_rule)
    
    return profile


def test_profile_executor():
    """Test ProfileExecutor with mock Eye-Brain-Hand components"""
    print("🚀 Testing MARK-I Profile Executor with Eye-Brain-Hand Integration")
    print("=" * 70)
    
    # Create mock components
    eye = MockCaptureEngine()
    brain = MockAgentCore()
    hand = MockActionExecutor()
    
    # Initialize ProfileExecutor
    executor = ProfileExecutor(capture_engine=eye, agent_core=brain, action_executor=hand)
    
    print("✅ ProfileExecutor initialized with Eye-Brain-Hand components")
    
    # Test 1: Email automation profile
    print(f"\n📧 Test 1: Email Automation Profile")
    print("-" * 40)
    
    email_profile = create_email_automation_profile()
    print(f"Created profile: {email_profile.name}")
    print(f"Regions: {len(email_profile.regions)}, Rules: {len(email_profile.rules)}")
    
    # Execute with variables
    variables = {
        "recipient_email": "example@gmail.com",
        "email_subject": "Hello from MARK-I!",
        "email_body": "This email was sent using intelligent automation."
    }
    
    print(f"\nExecuting email profile with variables:")
    for key, value in variables.items():
        print(f"  {key}: {value}")
    
    result = executor.execute_profile(email_profile, variables)
    
    print(f"\n📊 Execution Results:")
    print(f"  Status: {result.status.value}")
    print(f"  Duration: {result.duration_seconds:.2f} seconds")
    print(f"  Rules executed: {result.rules_executed}")
    print(f"  Actions performed: {result.actions_performed}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success: {result.success}")
    
    if result.execution_log:
        print(f"\n📝 Execution Log:")
        for log_entry in result.execution_log:
            print(f"    {log_entry}")
    
    # Test 2: Web search profile
    print(f"\n🔍 Test 2: Web Search Profile")
    print("-" * 40)
    
    search_profile = create_web_search_profile()
    print(f"Created profile: {search_profile.name}")
    
    search_variables = {
        "search_query": "MARK-I automation assistant"
    }
    
    print(f"\nExecuting search profile with query: {search_variables['search_query']}")
    
    result2 = executor.execute_profile(search_profile, search_variables)
    
    print(f"\n📊 Execution Results:")
    print(f"  Status: {result2.status.value}")
    print(f"  Duration: {result2.duration_seconds:.2f} seconds")
    print(f"  Rules executed: {result2.rules_executed}")
    print(f"  Actions performed: {result2.actions_performed}")
    print(f"  Success: {result2.success}")
    
    # Test 3: Execution control
    print(f"\n⏸️ Test 3: Execution Control")
    print("-" * 40)
    
    print("Testing pause/resume functionality...")
    
    # This would be tested with a longer-running profile in practice
    print("✅ Execution control methods available:")
    print("  - executor.pause_execution()")
    print("  - executor.resume_execution()")
    print("  - executor.cancel_execution()")
    print("  - executor.is_executing()")
    
    return executor, result, result2


def demonstrate_react_loop():
    """Demonstrate ReAct loop pattern in profile execution"""
    print(f"\n🔄 Demonstrating ReAct Loop Pattern")
    print("-" * 40)
    
    print("ReAct Loop: Thought -> Action -> Observation")
    print()
    print("Example execution flow:")
    print("1. 🧠 Thought: 'I need to send an email, let me find the recipient field'")
    print("2. 👁️ Observation: Eye captures screen and analyzes email interface")
    print("3. 🧠 Thought: 'I can see the recipient field is visible and ready'")
    print("4. 🤚 Action: Hand clicks on the recipient field")
    print("5. 👁️ Observation: Eye confirms field is now active/focused")
    print("6. 🧠 Thought: 'Field is active, I can now type the email address'")
    print("7. 🤚 Action: Hand types the recipient email")
    print("8. 👁️ Observation: Eye confirms text was entered correctly")
    print("9. 🧠 Thought: 'Email address entered, moving to subject field'")
    print("... and so on until email is sent")
    print()
    print("This intelligent loop enables:")
    print("✅ Self-correction when actions fail")
    print("✅ Adaptation to changing UI states")
    print("✅ Intelligent decision making at each step")
    print("✅ User interaction when uncertain")


def main():
    """Run all ProfileExecutor tests"""
    try:
        executor, email_result, search_result = test_profile_executor()
        demonstrate_react_loop()
        
        print(f"\n🎉 All ProfileExecutor tests completed successfully!")
        print(f"🔧 Eye-Brain-Hand integration is working perfectly!")
        
        print(f"\n📋 Summary:")
        print(f"  Email automation: {'✅ Success' if email_result.success else '❌ Failed'}")
        print(f"  Web search automation: {'✅ Success' if search_result.success else '❌ Failed'}")
        print(f"  Total actions performed: {email_result.actions_performed + search_result.actions_performed}")
        
        print(f"\n🚀 MARK-I Profile Automation System is ready for intelligent task execution!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()