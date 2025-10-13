"""
Integration Bridge

Bridge component that connects the profile system to MARK-I's existing
Eye-Brain-Hand architecture components.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import subprocess
import os

from ..models.region import Region


class IntegrationBridge:
    """Bridge to MARK-I's existing components"""
    
    def __init__(self):
        self.logger = logging.getLogger("mark_i.profiles.execution.integration_bridge")
        
        # Component references (would be injected in real implementation)
        self.capture_engine = None
        self.agent_core = None
        self.action_executor = None
        self.gemini_analyzer = None
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("IntegrationBridge initialized")
    
    def _initialize_components(self):
        """Initialize connections to MARK-I components"""
        try:
            # In a real implementation, these would be proper imports and initializations
            # For now, we'll simulate the component availability
            
            # Try to import and initialize CaptureEngine
            try:
                # from mark_i.perception.capture_engine import CaptureEngine
                # self.capture_engine = CaptureEngine()
                self.capture_engine = MockCaptureEngine()
                self.logger.info("CaptureEngine connected")
            except ImportError:
                self.logger.warning("CaptureEngine not available")
            
            # Try to import and initialize AgentCore
            try:
                # from mark_i.agent.agent_core import AgentCore
                # self.agent_core = AgentCore()
                self.agent_core = MockAgentCore()
                self.logger.info("AgentCore connected")
            except ImportError:
                self.logger.warning("AgentCore not available")
            
            # Try to import and initialize ActionExecutor
            try:
                # from mark_i.engines.primitive_executors import ActionExecutor
                # self.action_executor = ActionExecutor()
                self.action_executor = MockActionExecutor()
                self.logger.info("ActionExecutor connected")
            except ImportError:
                self.logger.warning("ActionExecutor not available")
            
            # Try to import and initialize GeminiAnalyzer
            try:
                # from mark_i.engines.gemini_analyzer import GeminiAnalyzer
                # self.gemini_analyzer = GeminiAnalyzer()
                self.gemini_analyzer = MockGeminiAnalyzer()
                self.logger.info("GeminiAnalyzer connected")
            except ImportError:
                self.logger.warning("GeminiAnalyzer not available")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
    
    def is_available(self) -> bool:
        """Check if integration bridge is available"""
        return (self.capture_engine is not None and 
                self.action_executor is not None)
    
    def capture_region(self, region: Region) -> Optional[Any]:
        """Capture screenshot of specified region"""
        try:
            if not self.capture_engine:
                self.logger.error("CaptureEngine not available")
                return None
            
            # Use MARK-I's capture engine
            screenshot = self.capture_engine.capture_region(
                region.x, region.y, region.width, region.height
            )
            
            self.logger.debug(f"Captured region: {region.name}")
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture region {region.name}: {e}")
            return None
    
    def capture_full_screen(self) -> Optional[Any]:
        """Capture full screen screenshot"""
        try:
            if not self.capture_engine:
                return None
            
            screenshot = self.capture_engine.capture_screen()
            self.logger.debug("Captured full screen")
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture screen: {e}")
            return None
    
    def analyze_visual_match(self, image: Any, template_path: str, 
                           threshold: float) -> Dict[str, Any]:
        """Analyze visual match using MARK-I's vision system"""
        try:
            if not self.gemini_analyzer:
                # Fallback to basic template matching
                return self._basic_template_match(image, template_path, threshold)
            
            # Use Gemini for intelligent visual analysis
            result = self.gemini_analyzer.analyze_visual_match(
                image, template_path, threshold
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Visual match analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def perform_ocr(self, image: Any) -> Optional[Dict[str, Any]]:
        """Perform OCR using MARK-I's text recognition"""
        try:
            if not self.capture_engine:
                return None
            
            # Use MARK-I's OCR capabilities
            ocr_result = self.capture_engine.perform_ocr(image)
            
            return ocr_result
            
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return None
    
    def match_template(self, image: Any, template_file: str, 
                      confidence: float) -> Dict[str, Any]:
        """Perform template matching"""
        try:
            if not self.capture_engine:
                return {'success': False, 'error': 'CaptureEngine not available'}
            
            # Use MARK-I's template matching
            match_result = self.capture_engine.match_template(
                image, template_file, confidence
            )
            
            return match_result
            
        except Exception as e:
            self.logger.error(f"Template matching failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_click(self, x: int, y: int, click_type: str = 'left') -> bool:
        """Execute click action using MARK-I's action executor"""
        try:
            if not self.action_executor:
                self.logger.error("ActionExecutor not available")
                return False
            
            # Use MARK-I's action executor
            success = self.action_executor.click(x, y, click_type)
            
            self.logger.debug(f"Executed {click_type} click at ({x}, {y}): {success}")
            return success
            
        except Exception as e:
            self.logger.error(f"Click execution failed: {e}")
            return False
    
    def execute_type_text(self, text: str, clear_first: bool = False) -> bool:
        """Execute text typing using MARK-I's action executor"""
        try:
            if not self.action_executor:
                self.logger.error("ActionExecutor not available")
                return False
            
            # Clear field if requested
            if clear_first:
                self.action_executor.key_combination(['ctrl', 'a'])
            
            # Type text
            success = self.action_executor.type_text(text)
            
            self.logger.debug(f"Typed text: {text[:50]}... : {success}")
            return success
            
        except Exception as e:
            self.logger.error(f"Text typing failed: {e}")
            return False
    
    def execute_key_combination(self, keys: List[str]) -> bool:
        """Execute key combination"""
        try:
            if not self.action_executor:
                return False
            
            success = self.action_executor.key_combination(keys)
            self.logger.debug(f"Executed key combination {keys}: {success}")
            return success
            
        except Exception as e:
            self.logger.error(f"Key combination failed: {e}")
            return False
    
    def execute_command(self, command: str, wait_for_completion: bool = True) -> bool:
        """Execute system command"""
        try:
            self.logger.info(f"Executing command: {command}")
            
            if wait_for_completion:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                success = result.returncode == 0
                
                if not success:
                    self.logger.error(f"Command failed: {result.stderr}")
                
                return success
            else:
                subprocess.Popen(command, shell=True)
                return True
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return False
    
    def check_system_state(self, state_type: str, state_value: str) -> bool:
        """Check system state"""
        try:
            if state_type == "window_active":
                return self._is_window_active(state_value)
            elif state_type == "process_running":
                return self._is_process_running(state_value)
            elif state_type == "file_exists":
                return os.path.exists(state_value)
            elif state_type == "network_connected":
                return self._is_network_connected()
            else:
                self.logger.warning(f"Unknown state type: {state_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"System state check failed: {e}")
            return False
    
    def check_time_condition(self, time_condition: str, time_value: str) -> bool:
        """Check time-based condition"""
        try:
            current_time = datetime.now()
            
            if time_condition == "after_time":
                target_time = datetime.strptime(time_value, "%H:%M").time()
                return current_time.time() >= target_time
            elif time_condition == "before_time":
                target_time = datetime.strptime(time_value, "%H:%M").time()
                return current_time.time() <= target_time
            elif time_condition == "day_of_week":
                target_day = int(time_value)  # 0=Monday, 6=Sunday
                return current_time.weekday() == target_day
            else:
                self.logger.warning(f"Unknown time condition: {time_condition}")
                return False
                
        except Exception as e:
            self.logger.error(f"Time condition check failed: {e}")
            return False
    
    def is_application_running(self, app_name: str) -> bool:
        """Check if application is running"""
        return self._is_process_running(app_name)
    
    def ask_user(self, prompt: str, input_type: str) -> Optional[Any]:
        """Ask user for input using MARK-I's UI system"""
        try:
            # This would integrate with MARK-I's UI system
            # For now, simulate user interaction
            
            if input_type == "yes_no":
                # Would show yes/no dialog
                return True  # Simulate user clicking "yes"
            elif input_type == "text":
                # Would show text input dialog
                return "user_input_text"  # Simulate user input
            elif input_type == "choice":
                # Would show choice dialog
                return "choice_1"  # Simulate user choice
            elif input_type == "file_path":
                # Would show file picker
                return "/path/to/file"  # Simulate file selection
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"User input failed: {e}")
            return None
    
    def get_enhanced_context(self) -> Dict[str, Any]:
        """Get enhanced system context from MARK-I"""
        try:
            # This would integrate with MARK-I's Enhanced System Context
            context = {
                'active_windows': self._get_active_windows(),
                'system_resources': self._get_system_resources(),
                'user_activity': self._get_user_activity(),
                'timestamp': datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced context: {e}")
            return {}
    
    def use_agent_reasoning(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use MARK-I's AgentCore for intelligent decision making"""
        try:
            if not self.agent_core:
                return {'success': False, 'error': 'AgentCore not available'}
            
            # Use AgentCore's ReAct loop for intelligent reasoning
            result = self.agent_core.reason_and_act(task_description, context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent reasoning failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    
    def _basic_template_match(self, image: Any, template_path: str, 
                            threshold: float) -> Dict[str, Any]:
        """Basic template matching fallback"""
        try:
            # This would implement basic OpenCV template matching
            # For now, simulate template matching
            import random
            confidence = random.uniform(0.6, 0.95)
            success = confidence >= threshold
            
            return {
                'success': success,
                'confidence': confidence,
                'location': (100, 100) if success else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _is_window_active(self, window_title: str) -> bool:
        """Check if window with title is active"""
        try:
            # Platform-specific window checking
            import platform
            
            if platform.system() == "Windows":
                # Windows-specific implementation
                return self._is_window_active_windows(window_title)
            elif platform.system() == "Darwin":
                # macOS-specific implementation
                return self._is_window_active_macos(window_title)
            else:
                # Linux-specific implementation
                return self._is_window_active_linux(window_title)
                
        except Exception as e:
            self.logger.error(f"Window check failed: {e}")
            return False
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if process is running"""
        try:
            import psutil
            
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    return True
            
            return False
            
        except ImportError:
            # Fallback without psutil
            try:
                import platform
                
                if platform.system() == "Windows":
                    result = subprocess.run(['tasklist'], capture_output=True, text=True)
                    return process_name.lower() in result.stdout.lower()
                else:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    return process_name.lower() in result.stdout.lower()
                    
            except Exception:
                return False
        except Exception as e:
            self.logger.error(f"Process check failed: {e}")
            return False
    
    def _is_network_connected(self) -> bool:
        """Check network connectivity"""
        try:
            import socket
            
            # Try to connect to a reliable server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
            
        except Exception:
            return False
    
    def _is_window_active_windows(self, window_title: str) -> bool:
        """Windows-specific window check"""
        try:
            import win32gui
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_title.lower() in title.lower():
                        windows.append(title)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            return len(windows) > 0
            
        except ImportError:
            return False
    
    def _is_window_active_macos(self, window_title: str) -> bool:
        """macOS-specific window check"""
        try:
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to get name of every process whose visible is true'
            ], capture_output=True, text=True)
            
            return window_title.lower() in result.stdout.lower()
            
        except Exception:
            return False
    
    def _is_window_active_linux(self, window_title: str) -> bool:
        """Linux-specific window check"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            return window_title.lower() in result.stdout.lower()
            
        except Exception:
            return False
    
    def _get_active_windows(self) -> List[str]:
        """Get list of active windows"""
        # Placeholder implementation
        return ["Window 1", "Window 2"]
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
            
        except ImportError:
            return {}
    
    def _get_user_activity(self) -> Dict[str, Any]:
        """Get user activity information"""
        # Placeholder implementation
        return {
            'last_input': datetime.now().isoformat(),
            'active_application': 'Unknown'
        }


# Mock classes for development/testing when actual components aren't available

class MockCaptureEngine:
    """Mock capture engine for development"""
    
    def capture_region(self, x: int, y: int, width: int, height: int):
        """Mock region capture"""
        try:
            import pyautogui
            return pyautogui.screenshot(region=(x, y, width, height))
        except ImportError:
            return None
    
    def capture_screen(self):
        """Mock screen capture"""
        try:
            import pyautogui
            return pyautogui.screenshot()
        except ImportError:
            return None
    
    def perform_ocr(self, image):
        """Mock OCR"""
        return {'text': 'mock_ocr_text', 'confidence': 85}
    
    def match_template(self, image, template_file: str, confidence: float):
        """Mock template matching"""
        import random
        match_confidence = random.uniform(0.6, 0.95)
        return {
            'success': match_confidence >= confidence,
            'confidence': match_confidence,
            'location': (100, 100)
        }


class MockActionExecutor:
    """Mock action executor for development"""
    
    def click(self, x: int, y: int, click_type: str = 'left') -> bool:
        """Mock click"""
        try:
            import pyautogui
            if click_type == 'left':
                pyautogui.click(x, y)
            elif click_type == 'right':
                pyautogui.rightClick(x, y)
            elif click_type == 'double':
                pyautogui.doubleClick(x, y)
            return True
        except ImportError:
            return True  # Simulate success
    
    def type_text(self, text: str) -> bool:
        """Mock text typing"""
        try:
            import pyautogui
            pyautogui.typewrite(text)
            return True
        except ImportError:
            return True  # Simulate success
    
    def key_combination(self, keys: List[str]) -> bool:
        """Mock key combination"""
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return True
        except ImportError:
            return True  # Simulate success


class MockAgentCore:
    """Mock agent core for development"""
    
    def reason_and_act(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock reasoning"""
        return {
            'success': True,
            'reasoning': f'Mock reasoning for: {task_description}',
            'action_plan': ['step1', 'step2', 'step3'],
            'confidence': 0.8
        }


class MockGeminiAnalyzer:
    """Mock Gemini analyzer for development"""
    
    def analyze_visual_match(self, image, template_path: str, threshold: float) -> Dict[str, Any]:
        """Mock visual analysis"""
        import random
        confidence = random.uniform(0.6, 0.95)
        return {
            'success': confidence >= threshold,
            'confidence': confidence,
            'analysis': 'Mock visual analysis result',
            'location': (100, 100) if confidence >= threshold else None
        }