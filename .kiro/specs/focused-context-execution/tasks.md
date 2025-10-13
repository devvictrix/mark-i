# Implementation Plan

- [x] 1. Create application detection prompt and constants
  - Define the APPLICATION_DETECTION_PROMPT template for identifying target application windows
  - Add model preference constants for focused context detection (use fast model like gemini-1.5-flash)
  - Create confidence threshold constants for application detection
  - _Requirements: 1.1, 1.2_

- [x] 2. Implement core focused context detection logic in StrategicExecutor
  - [x] 2.1 Create _determine_and_crop_context method
    - Implement method to analyze command and screenshot for target application
    - Add logic to query GeminiAnalyzer with APPLICATION_DETECTION_PROMPT
    - Parse response to extract bounding box coordinates and confidence
    - _Requirements: 1.1, 4.1_

  - [x] 2.2 Add bounding box validation logic
    - Create _validate_bounding_box method to check coordinates are within screen bounds
    - Validate minimum window dimensions (e.g., 100x100 pixels)
    - Ensure positive width and height values
    - _Requirements: 1.4, 3.3_

  - [x] 2.3 Implement image cropping functionality
    - Add logic to crop numpy array based on validated bounding box
    - Calculate and store coordinate offset (x, y) from screen origin
    - Handle edge cases where cropping fails
    - _Requirements: 1.2, 4.1_

- [x] 3. Enhance context dictionary structure
  - [x] 3.1 Update context creation in StrategicExecutor
    - Add use_focused_context boolean flag to context dictionary
    - Include coordinate_offset tuple in context
    - Add focused_region_config for cropped area specifications
    - Store original_screen_dimensions for reference
    - _Requirements: 4.1, 4.2_

  - [x] 3.2 Update fullscreen context handling
    - Modify existing fullscreen_region_config creation to work with focused context
    - Ensure backward compatibility with existing full-screen execution
    - _Requirements: 1.4, 4.3_

- [x] 4. Implement coordinate translation in ActionExecutor
  - [x] 4.1 Add coordinate offset application logic
    - Create _apply_coordinate_offset method to translate relative to absolute coordinates
    - Update _get_target_coords method to use coordinate offsets when available
    - Handle both focused and full-screen contexts transparently
    - _Requirements: 1.3, 4.4_

  - [x] 4.2 Update coordinate calculation for gemini elements
    - Modify center_of_gemini_element and top_left_of_gemini_element calculations
    - Apply coordinate offset when context indicates focused execution
    - Maintain existing behavior for full-screen contexts
    - _Requirements: 1.3, 4.4_

- [x] 5. Integrate focused context into strategic execution flow
  - [x] 5.1 Update execute_command method in StrategicExecutor
    - Add focused context determination step before plan generation
    - Store focused context results for use throughout execution
    - Pass appropriate context (focused or full-screen) to AgentCore
    - _Requirements: 1.1, 1.2, 4.1_

  - [x] 5.2 Update tactical execution calls
    - Modify calls to gemini_decision_module.execute_nlu_task to use focused context
    - Ensure cropped images are passed instead of full screenshots when applicable
    - Update context_region_names and region configurations accordingly
    - _Requirements: 1.2, 4.2_

- [x] 6. Add fallback and error handling mechanisms
  - [x] 6.1 Implement graceful degradation logic
    - Add fallback to full-screen execution when application detection fails
    - Handle low confidence detection results (below threshold)
    - Log appropriate warnings when falling back to full-screen mode
    - _Requirements: 1.4, 3.3_

  - [x] 6.2 Add error recovery for coordinate translation
    - Handle cases where coordinate offset application fails
    - Provide meaningful error messages for debugging
    - Ensure system continues functioning even with coordinate translation errors
    - _Requirements: 1.3, 4.4_

- [x] 7. Add logging and status updates for focused context execution
  - Add status update callbacks for focused context detection start/success/failure
  - Include focused context information in execution logs
  - Add debug logging for bounding box coordinates and cropping operations
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 8. Create unit tests for focused context functionality
  - [ ]* 8.1 Test application detection logic
    - Write tests for _determine_and_crop_context method with various command types
    - Test bounding box validation with edge cases (negative coords, oversized windows)
    - Mock GeminiAnalyzer responses for consistent testing
    - _Requirements: 1.1, 3.3_

  - [ ]* 8.2 Test coordinate translation functionality
    - Write tests for _apply_coordinate_offset method
    - Test coordinate calculations with various offset values
    - Verify correct translation from relative to absolute coordinates
    - _Requirements: 1.3_

  - [ ]* 8.3 Test fallback behavior
    - Test graceful degradation when application detection fails
    - Verify full-screen execution when focused context is not applicable
    - Test error handling for invalid bounding boxes
    - _Requirements: 1.4_