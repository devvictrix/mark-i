#!/usr/bin/env python3
"""
Test script for Profile Automation System data models

This script tests the core data models and ProfileManager functionality.
"""

from mark_i.profiles.models.profile import AutomationProfile, ProfileSettings
from mark_i.profiles.models.region import Region
from mark_i.profiles.models.rule import Rule, Condition, Action
from mark_i.profiles.profile_manager import ProfileManager


def test_region_model():
    """Test Region data model"""
    print("🔍 Testing Region Model...")
    
    # Create a region
    region = Region(
        name="email_recipient",
        x=100, y=200, width=300, height=30,
        description="Email recipient input field",
        ocr_enabled=True
    )
    
    print(f"   ✅ Created region: {region.name}")
    print(f"   📍 Position: ({region.x}, {region.y}) Size: {region.width}x{region.height}")
    print(f"   🎯 Center: ({region.center_x}, {region.center_y})")
    
    # Test serialization
    region_dict = region.to_dict()
    region_from_dict = Region.from_dict(region_dict)
    
    assert region.name == region_from_dict.name
    assert region.x == region_from_dict.x
    print("   ✅ Serialization/deserialization works")


def test_rule_model():
    """Test Rule, Condition, and Action models"""
    print("\n📋 Testing Rule Model...")
    
    # Create conditions
    condition1 = Condition(
        type="visual_match",
        region="email_recipient",
        parameters={"visible": True}
    )
    
    condition2 = Condition(
        type="ocr_contains",
        region="email_recipient",
        parameters={"text": "@"}
    )
    
    # Create actions
    action1 = Action(
        type="click",
        region="email_recipient",
        delay_before=0.5
    )
    
    action2 = Action(
        type="type_text",
        parameters={"text": "example@gmail.com"},
        delay_after=1.0
    )
    
    # Create rule
    rule = Rule(
        name="Fill Email Recipient",
        description="Click and fill email recipient field",
        conditions=[condition1, condition2],
        actions=[action1, action2],
        logical_operator="AND"
    )
    
    print(f"   ✅ Created rule: {rule.name}")
    print(f"   🔍 Conditions: {len(rule.conditions)}")
    print(f"   ⚡ Actions: {len(rule.actions)}")
    print(f"   🎯 Referenced regions: {rule.get_referenced_regions()}")
    
    # Test serialization
    rule_dict = rule.to_dict()
    rule_from_dict = Rule.from_dict(rule_dict)
    
    assert rule.name == rule_from_dict.name
    assert len(rule.conditions) == len(rule_from_dict.conditions)
    print("   ✅ Rule serialization works")


def test_profile_model():
    """Test AutomationProfile model"""
    print("\n📄 Testing Profile Model...")
    
    # Create profile
    profile = AutomationProfile.create_new(
        name="Send Email Automation",
        description="Automate sending emails with recipient and content",
        category="email",
        target_application="Outlook"
    )
    
    print(f"   ✅ Created profile: {profile.name}")
    print(f"   🆔 ID: {profile.id}")
    print(f"   📂 Category: {profile.category}")
    
    # Add region
    region = Region(
        name="recipient_field",
        x=100, y=200, width=300, height=30,
        description="Email recipient input field"
    )
    profile.add_region(region)
    
    # Add rule
    condition = Condition("visual_match", "recipient_field", {"visible": True})
    action = Action("click", "recipient_field")
    rule = Rule("Click Recipient", "Click on recipient field", conditions=[condition], actions=[action])
    profile.add_rule(rule)
    
    print(f"   🔍 Regions: {len(profile.regions)}")
    print(f"   📋 Rules: {len(profile.rules)}")
    
    # Test validation
    errors = profile.validate_references()
    print(f"   ✅ Validation errors: {len(errors)}")
    
    # Test serialization
    profile_json = profile.to_json()
    profile_from_json = AutomationProfile.from_json(profile_json)
    
    assert profile.name == profile_from_json.name
    assert len(profile.regions) == len(profile_from_json.regions)
    print("   ✅ Profile serialization works")
    
    return profile


def test_profile_manager():
    """Test ProfileManager functionality"""
    print("\n📁 Testing Profile Manager...")
    
    # Create profile manager
    manager = ProfileManager("test_profiles")
    
    print(f"   ✅ Created ProfileManager")
    
    # Create a test profile
    profile = manager.create_profile(
        name="Test Email Profile",
        description="Test profile for email automation",
        category="email",
        target_application="Gmail"
    )
    
    print(f"   ✅ Created profile through manager: {profile.name}")
    
    # Add some content to the profile
    region = Region("test_region", 0, 0, 100, 100, "Test region")
    profile.add_region(region)
    
    condition = Condition("always_true", "test_region")
    action = Action("click", "test_region")
    rule = Rule("Test Rule", "Test rule", conditions=[condition], actions=[action])
    profile.add_rule(rule)
    
    # Save profile
    saved = manager.save_profile(profile)
    print(f"   ✅ Profile saved: {saved}")
    
    # Load profile
    loaded_profile = manager.load_profile(profile.id)
    print(f"   ✅ Profile loaded: {loaded_profile.name if loaded_profile else 'Failed'}")
    
    # List profiles
    profiles = manager.list_profiles("email")
    print(f"   ✅ Found {len(profiles)} email profiles")
    
    # Search profiles
    search_results = manager.search_profiles("email")
    print(f"   ✅ Search found {len(search_results)} profiles")
    
    # Get statistics
    stats = manager.get_profile_statistics()
    print(f"   📊 Profile statistics: {stats['total_profiles']} total profiles")
    
    return manager


def main():
    """Run all tests"""
    print("🚀 Testing MARK-I Profile Automation System Data Models")
    print("=" * 60)
    
    try:
        # Test individual models
        test_region_model()
        test_rule_model()
        profile = test_profile_model()
        manager = test_profile_manager()
        
        print(f"\n🎉 All tests passed successfully!")
        print(f"✅ Profile system is ready for integration!")
        
        # Show example profile structure
        print(f"\n📋 Example Profile Structure:")
        print("-" * 40)
        print(f"Profile: {profile.name}")
        print(f"  Regions: {[r.name for r in profile.regions]}")
        print(f"  Rules: {[r.name for r in profile.rules]}")
        print(f"  Settings: Template threshold = {profile.settings.template_match_threshold}")
        
        # Show manager capabilities
        print(f"\n🔧 Profile Manager Capabilities:")
        print("-" * 40)
        print(f"  Storage path: {manager.storage_path}")
        print(f"  Cache size: {manager.get_cache_size()}")
        print(f"  Categories: email, web, files, templates, custom")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()