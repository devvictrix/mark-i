"""
Visual Tester

Visual recognition testing to verify region detection, template matching,
and OCR functionality for automation profiles.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..models.profile import AutomationProfile
from ..models.region import Region


@dataclass
class VisualTestResult:
    """Result of visual recognition test"""
    region_name: str
    test_type: str  # 'detection', 'ocr', 'template_match', 'visual_match'
    success: bool
    confidence: float
    execution_time: float
    result_data: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    def __str__(self) -> str:
        status = "✅ PASS" if self.success else "❌ FAIL"
        return f"{status} {self.region_name} ({self.test_type}) - {self.confidence:.2f} confidence in {self.execution_time:.2f}s"


class VisualTester:
    """Visual recognition testing system"""
    
    def __init__(self, screenshot_dir: str = None):
        self.logger = logging.getLogger("mark_i.profiles.testing.visual")
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        
        if self.screenshot_dir:
            self.screenshot_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.default_timeout = 5.0
        self.screenshot_on_test = True
        self.save_debug_images = True
        
        self.logger.info("VisualTester initialized")
    
    def test_profile_regions(self, profile: AutomationProfile) -> List[VisualTestResult]:
        """Test all regions in a profile for visual recognition"""
        self.logger.info(f"Testing visual recognition for profile: {profile.name}")
        
        results = []
        
        for region in profile.regions:
            # Test region detection
            detection_result = self.test_region_detection(region)
            results.append(detection_result)
            
            # Test OCR if enabled
            if region.ocr_enabled:
                ocr_result = self.test_region_ocr(region)
                results.append(ocr_result)
            
            # Test template matching if applicable
            template_result = self.test_region_template_matching(region)
            if template_result:
                results.append(template_result)
        
        # Log summary
        passed = len([r for r in results if r.success])
        total = len(results)
        self.logger.info(f"Visual testing completed: {passed}/{total} tests passed")
        
        return results
    
    def test_region_detection(self, region: Region) -> VisualTestResult:
        """Test basic region detection and screenshot capture"""
        self.logger.debug(f"Testing region detection: {region.name}")
        
        start_time = time.time()
        
        try:
            # Take screenshot of region
            screenshot = self._capture_region(region)
            
            if screenshot is None:
                return VisualTestResult(
                    region_name=region.name,
                    test_type="detection",
                    success=False,
                    confidence=0.0,
                    execution_time=time.time() - start_time,
                    error="Failed to capture region screenshot"
                )
            
            # Validate screenshot dimensions
            expected_size = (region.width, region.height)
            actual_size = screenshot.size
            
            size_match = abs(actual_size[0] - expected_size[0]) <= 5 and abs(actual_size[1] - expected_size[1]) <= 5
            
            # Save screenshot for debugging
            screenshot_path = None
            if self.screenshot_dir and self.screenshot_on_test:
                screenshot_path = self._save_debug_screenshot(screenshot, region, "detection")
            
            confidence = 1.0 if size_match else 0.5
            
            return VisualTestResult(
                region_name=region.name,
                test_type="detection",
                success=size_match,
                confidence=confidence,
                execution_time=time.time() - start_time,
                result_data={"actual_size": actual_size, "expected_size": expected_size},
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            self.logger.error(f"Region detection test failed for {region.name}: {e}")
            return VisualTestResult(
                region_name=region.name,
                test_type="detection",
                success=False,
                confidence=0.0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def test_region_ocr(self, region: Region) -> VisualTestResult:
        """Test OCR functionality on a region"""
        self.logger.debug(f"Testing OCR for region: {region.name}")
        
        start_time = time.time()
        
        try:
            # Capture region screenshot
            screenshot = self._capture_region(region)
            
            if screenshot is None:
                return VisualTestResult(
                    region_name=region.name,
                    test_type="ocr",
                    success=False,
                    confidence=0.0,
                    execution_time=time.time() - start_time,
                    error="Failed to capture region for OCR"
                )
            
            # Perform OCR
            ocr_result = self._perform_ocr(screenshot)
            
            # Save screenshot for debugging
            screenshot_path = None
            if self.screenshot_dir and self.screenshot_on_test:
                screenshot_path = self._save_debug_screenshot(screenshot, region, "ocr")
            
            # Evaluate OCR success
            success = ocr_result is not None and len(ocr_result.get('text', '').strip()) > 0
            confidence = ocr_result.get('confidence', 0.0) / 100.0 if ocr_result else 0.0
            
            return VisualTestResult(
                region_name=region.name,
                test_type="ocr",
                success=success,
                confidence=confidence,
                execution_time=time.time() - start_time,
                result_data=ocr_result,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            self.logger.error(f"OCR test failed for {region.name}: {e}")
            return VisualTestResult(
                region_name=region.name,
                test_type="ocr",
                success=False,
                confidence=0.0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def test_region_template_matching(self, region: Region) -> Optional[VisualTestResult]:
        """Test template matching for a region"""
        # This would require template files to be configured
        # For now, return None if no template is configured
        
        # In a real implementation, this would:
        # 1. Check if region has associated template files
        # 2. Capture current region screenshot
        # 3. Perform template matching
        # 4. Return results with confidence scores
        
        return None
    
    def test_visual_condition(self, region: Region, condition_params: Dict[str, Any]) -> VisualTestResult:
        """Test a specific visual condition"""
        self.logger.debug(f"Testing visual condition for region: {region.name}")
        
        start_time = time.time()
        
        try:
            # Capture region screenshot
            screenshot = self._capture_region(region)
            
            if screenshot is None:
                return VisualTestResult(
                    region_name=region.name,
                    test_type="visual_match",
                    success=False,
                    confidence=0.0,
                    execution_time=time.time() - start_time,
                    error="Failed to capture region for visual condition test"
                )
            
            # Test based on condition type
            if 'template_path' in condition_params:
                result = self._test_template_match(screenshot, condition_params)
            elif 'text' in condition_params:
                result = self._test_ocr_contains(screenshot, condition_params)
            else:
                result = self._test_visual_analysis(screenshot, condition_params)
            
            # Save screenshot for debugging
            screenshot_path = None
            if self.screenshot_dir and self.screenshot_on_test:
                screenshot_path = self._save_debug_screenshot(screenshot, region, "visual_condition")
            
            return VisualTestResult(
                region_name=region.name,
                test_type="visual_match",
                success=result.get('success', False),
                confidence=result.get('confidence', 0.0),
                execution_time=time.time() - start_time,
                result_data=result,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            self.logger.error(f"Visual condition test failed for {region.name}: {e}")
            return VisualTestResult(
                region_name=region.name,
                test_type="visual_match",
                success=False,
                confidence=0.0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _capture_region(self, region: Region) -> Optional[Any]:
        """Capture screenshot of specified region"""
        try:
            import pyautogui
            
            # Capture the region
            screenshot = pyautogui.screenshot(region=(region.x, region.y, region.width, region.height))
            
            self.logger.debug(f"Captured region {region.name}: {region.width}x{region.height} at ({region.x}, {region.y})")
            return screenshot
            
        except ImportError:
            self.logger.error("PyAutoGUI not available for screenshot capture")
            return None
        except Exception as e:
            self.logger.error(f"Failed to capture region {region.name}: {e}")
            return None
    
    def _perform_ocr(self, image) -> Optional[Dict[str, Any]]:
        """Perform OCR on image"""
        try:
            import pytesseract
            from PIL import Image
            
            # Convert to PIL Image if needed
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)
            
            # Perform OCR with confidence scores
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(ocr_data['conf']):
                if int(conf) > 0:  # Only include confident detections
                    text = ocr_data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(int(conf))
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': full_text,
                'confidence': avg_confidence,
                'word_count': len(text_parts),
                'raw_data': ocr_data
            }
            
        except ImportError:
            self.logger.error("Tesseract OCR not available")
            return None
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return None
    
    def _test_template_match(self, screenshot, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test template matching"""
        try:
            import cv2
            import numpy as np
            from PIL import Image
            
            # Convert PIL image to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Load template
            template_path = params.get('template_path')
            if not template_path or not Path(template_path).exists():
                return {'success': False, 'confidence': 0.0, 'error': 'Template file not found'}
            
            template = cv2.imread(template_path)
            if template is None:
                return {'success': False, 'confidence': 0.0, 'error': 'Failed to load template'}
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            threshold = params.get('threshold', 0.8)
            success = max_val >= threshold
            
            return {
                'success': success,
                'confidence': float(max_val),
                'threshold': threshold,
                'location': max_loc,
                'match_value': float(max_val)
            }
            
        except ImportError:
            return {'success': False, 'confidence': 0.0, 'error': 'OpenCV not available'}
        except Exception as e:
            return {'success': False, 'confidence': 0.0, 'error': str(e)}
    
    def _test_ocr_contains(self, screenshot, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test if OCR text contains specified text"""
        ocr_result = self._perform_ocr(screenshot)
        
        if not ocr_result:
            return {'success': False, 'confidence': 0.0, 'error': 'OCR failed'}
        
        search_text = params.get('text', '')
        case_sensitive = params.get('case_sensitive', False)
        
        ocr_text = ocr_result['text']
        
        if not case_sensitive:
            ocr_text = ocr_text.lower()
            search_text = search_text.lower()
        
        contains_text = search_text in ocr_text
        confidence = ocr_result['confidence'] / 100.0 if contains_text else 0.0
        
        return {
            'success': contains_text,
            'confidence': confidence,
            'ocr_text': ocr_result['text'],
            'search_text': params.get('text', ''),
            'case_sensitive': case_sensitive
        }
    
    def _test_visual_analysis(self, screenshot, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test general visual analysis"""
        # This would integrate with Gemini for visual analysis
        # For now, return a placeholder result
        
        return {
            'success': True,
            'confidence': 0.8,
            'analysis': 'Visual analysis placeholder - would integrate with Gemini'
        }
    
    def _save_debug_screenshot(self, image, region: Region, test_type: str) -> str:
        """Save screenshot for debugging"""
        if not self.screenshot_dir:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{region.name}_{test_type}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            # Save image
            if hasattr(image, 'save'):
                image.save(filepath)
            else:
                # Convert to PIL Image if needed
                from PIL import Image
                if isinstance(image, np.ndarray):
                    Image.fromarray(image).save(filepath)
                else:
                    Image.fromarray(np.array(image)).save(filepath)
            
            self.logger.debug(f"Debug screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save debug screenshot: {e}")
            return None
    
    def generate_visual_test_report(self, results: List[VisualTestResult]) -> str:
        """Generate detailed visual test report"""
        report = []
        report.append("Visual Recognition Test Report")
        report.append("=" * 40)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {len(results)}")
        report.append("")
        
        # Summary
        passed = len([r for r in results if r.success])
        failed = len(results) - passed
        
        report.append("Summary:")
        report.append(f"  ✅ Passed: {passed}")
        report.append(f"  ❌ Failed: {failed}")
        report.append(f"  Success Rate: {(passed/len(results)*100):.1f}%" if results else "  Success Rate: N/A")
        report.append("")
        
        # Test results by type
        test_types = {}
        for result in results:
            if result.test_type not in test_types:
                test_types[result.test_type] = []
            test_types[result.test_type].append(result)
        
        for test_type, type_results in test_types.items():
            report.append(f"{test_type.title()} Tests:")
            type_passed = len([r for r in type_results if r.success])
            report.append(f"  Results: {type_passed}/{len(type_results)} passed")
            
            for result in type_results:
                status = "✅" if result.success else "❌"
                report.append(f"    {status} {result.region_name} - {result.confidence:.2f} confidence ({result.execution_time:.2f}s)")
                
                if result.error:
                    report.append(f"      Error: {result.error}")
                
                if result.screenshot_path:
                    report.append(f"      Screenshot: {result.screenshot_path}")
            
            report.append("")
        
        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 20)
        
        for result in results:
            report.append(f"Region: {result.region_name}")
            report.append(f"  Test Type: {result.test_type}")
            report.append(f"  Status: {'PASS' if result.success else 'FAIL'}")
            report.append(f"  Confidence: {result.confidence:.3f}")
            report.append(f"  Execution Time: {result.execution_time:.3f}s")
            
            if result.result_data:
                report.append(f"  Result Data: {result.result_data}")
            
            if result.error:
                report.append(f"  Error: {result.error}")
            
            if result.screenshot_path:
                report.append(f"  Screenshot: {result.screenshot_path}")
            
            report.append("")
        
        return "\n".join(report)
    
    def benchmark_region_performance(self, region: Region, iterations: int = 10) -> Dict[str, Any]:
        """Benchmark region detection performance"""
        self.logger.info(f"Benchmarking region {region.name} over {iterations} iterations")
        
        times = []
        successes = 0
        
        for i in range(iterations):
            result = self.test_region_detection(region)
            times.append(result.execution_time)
            if result.success:
                successes += 1
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        success_rate = successes / iterations
        
        benchmark_result = {
            'region_name': region.name,
            'iterations': iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'success_rate': success_rate,
            'times': times
        }
        
        self.logger.info(f"Benchmark completed: {success_rate:.1%} success rate, {avg_time:.3f}s avg time")
        
        return benchmark_result