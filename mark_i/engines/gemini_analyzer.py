import logging
import time
import json
from typing import Optional, Dict, Any, Union, List, Tuple
import os

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold
from google.generativeai.types import BlockedPromptException, StopCandidateException
from google.api_core import exceptions as google_api_exceptions

from PIL import Image
import cv2
import numpy as np

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.core.app_config import MODEL_PREFERENCE_REASONING, MODEL_PREFERENCE_FAST

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.gemini_analyzer")

try:
    from google.generativeai.types import Content, Part

    logger.debug("Imported 'Content' and 'Part' from 'google.generativeai.types'")
except ImportError:
    try:
        from google.generativeai import Content, Part

        logger.debug("Imported 'Content' and 'Part' from 'google.generativeai'")
    except ImportError:
        logger.warning("'Content' and/or 'Part' types not found. Using 'Any' for type hints.")
        Content = Any
        Part = Any

DEFAULT_SAFETY_SETTINGS_DATA: List[Dict[str, Any]] = [
    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
]
DEFAULT_GENERATION_CONFIG = GenerationConfig()

# --- Focused Context Execution Constants ---
# Confidence threshold for application detection (0.0 to 1.0)
FOCUSED_CONTEXT_CONFIDENCE_THRESHOLD = 0.7

# Minimum window dimensions for focused context (width, height in pixels)
FOCUSED_CONTEXT_MIN_WINDOW_SIZE = (100, 100)

# Application detection prompt template for identifying target application windows
APPLICATION_DETECTION_PROMPT = """
Analyze the screenshot and identify the primary application window that would be most relevant for this command: "{command}"

Look for:
1. The main application window that the user likely wants to interact with
2. Active/focused windows vs background windows  
3. Dialog boxes or modal windows that might be part of the target application

Respond with a JSON object containing the bounding box of the target application window:
{{
  "found_target_application": true/false,
  "application_name": "detected application name",
  "bounding_box": {{
    "x": left_coordinate,
    "y": top_coordinate, 
    "width": window_width,
    "height": window_height
  }},
  "confidence": 0.0-1.0
}}

If no clear target application can be identified, set found_target_application to false.
"""


class GeminiAnalyzer:
    def __init__(self, api_key: str, default_model_name: Optional[str] = None):
        self.api_key = api_key
        self.client_initialized = False
        self.safety_settings: Optional[List[Any]] = None
        self.generation_config = DEFAULT_GENERATION_CONFIG
        # --- v18.0.2 REFACTOR: Default model is the first in the fast preference chain ---
        self.default_model_name = default_model_name or MODEL_PREFERENCE_FAST[0]
        # --- END REFACTOR ---

        if not self.api_key or not isinstance(self.api_key, str):
            logger.critical("GeminiAnalyzer CRITICAL ERROR: API key is missing or invalid.")
            return
        try:
            genai.configure(api_key=self.api_key)
            self.safety_settings = []
            if hasattr(genai, "SafetySetting"):
                for ss_data in DEFAULT_SAFETY_SETTINGS_DATA:
                    self.safety_settings.append(genai.SafetySetting(harm_category=ss_data["category"], threshold=ss_data["threshold"]))
            self.client_initialized = True
            logger.info("GeminiAnalyzer initialized. Client configured.")
        except Exception as e:
            self.client_initialized = False
            logger.critical(f"GeminiAnalyzer CRITICAL FAILURE: Could not configure API client: {e}.", exc_info=True)

    def _attempt_sdk_call_with_fallback(
        self, api_contents: List[Union[str, Image.Image]], model_preference: List[str], gen_config: GenerationConfig, safety_settings: Optional[List[Any]]
    ) -> Dict[str, Any]:
        last_error_response: Dict[str, Any] = {"status": "error_api", "error_message": "All preferred models failed.", "text_content": None, "json_content": None, "raw_gemini_response": None}

        for model_name in model_preference:
            log_prefix = f"GeminiQuery (Attempting Model: '{model_name}')"
            logger.info(f"{log_prefix}: Sending query...")
            try:
                model_instance = genai.GenerativeModel(model_name=model_name, generation_config=gen_config, safety_settings=safety_settings)
                sdk_response = model_instance.generate_content(api_contents, stream=False)
                processed_response = self._process_sdk_response(sdk_response, log_prefix)
                processed_response["model_used"] = model_name
                return processed_response

            except google_api_exceptions.ResourceExhausted as e_quota:
                error_msg = f"Gemini API quota exceeded for model '{model_name}'. Trying next model if available."
                logger.warning(f"{log_prefix}: {error_msg} (Raw: {e_quota})")
                last_error_response = {"status": "error_quota", "error_message": error_msg, "raw_gemini_response": str(e_quota)}
                continue

            except Exception as e:
                error_msg = f"Gemini API call failed for model '{model_name}' ({type(e).__name__}): {e}"
                logger.error(f"{log_prefix}: {error_msg}", exc_info=True)
                last_error_response = {"status": "error_api", "error_message": error_msg, "raw_gemini_response": str(e)}
                break

        last_error_response["model_used"] = model_preference[-1] if model_preference else "N/A"
        if last_error_response["status"] == "error_quota":
            last_error_response["error_message"] = "Gemini API quota exceeded for all fallback models. Please check your usage limits."
        return last_error_response

    def _validate_and_prepare_api_input(self, prompt: str, image_data: Optional[np.ndarray], log_prefix: str) -> Tuple[Optional[List[Union[str, Image.Image]]], Optional[Dict[str, Any]]]:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            error_msg = "Input error: Prompt cannot be empty or just whitespace."
            logger.error(f"{log_prefix}: {error_msg}")
            return None, {"status": "error_input", "error_message": error_msg}

        pil_image_for_sdk: Optional[Image.Image] = None
        if image_data is not None:
            if not isinstance(image_data, np.ndarray) or image_data.size == 0:
                error_msg = "Input error: Provided image_data is invalid (empty or not NumPy array)."
                logger.error(f"{log_prefix}: {error_msg}")
                return None, {"status": "error_input", "error_message": error_msg}
            # --- BUG FIX ---
            # The original check was `image_data.shape != 3` which is always true for an image.
            # The correct check is for the number of dimensions and the channel count.
            if image_data.ndim != 3 or image_data.shape[2] != 3:
            # --- END BUG FIX ---
                error_msg = f"Input error: Provided image_data is not a 3-channel (BGR) image. Shape: {image_data.shape}"
                logger.error(f"{log_prefix}: {error_msg}")
                return None, {"status": "error_input", "error_message": error_msg}
            try:
                img_rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                pil_image_for_sdk = Image.fromarray(img_rgb)
                logger.debug(f"{log_prefix}: Prepared image (Size: {pil_image_for_sdk.width}x{pil_image_for_sdk.height}) for API call.")
            except Exception as e_img_prep:
                error_msg = f"Error preparing image for Gemini: {e_img_prep}"
                logger.error(f"{log_prefix}: {error_msg}", exc_info=True)
                return None, {"status": "error_input", "error_message": error_msg}

        api_contents: List[Union[str, Image.Image]] = [prompt]
        if pil_image_for_sdk:
            api_contents.append(pil_image_for_sdk)
        return api_contents, None

    def _process_sdk_response(self, api_sdk_response: Optional[Any], log_prefix: str) -> Dict[str, Any]:
        processed_result: Dict[str, Any] = {
            "status": "error_api",
            "text_content": None,
            "json_content": None,
            "error_message": "Failed to process SDK response or response was None.",
            "raw_gemini_response": str(api_sdk_response) if api_sdk_response else "None",
        }
        if api_sdk_response is None:
            return processed_result
        processed_result["raw_gemini_response"] = str(api_sdk_response)

        if hasattr(api_sdk_response, "prompt_feedback") and api_sdk_response.prompt_feedback and api_sdk_response.prompt_feedback.block_reason:
            processed_result["status"] = "blocked_prompt"
            processed_result["error_message"] = f"Prompt blocked by API. Reason: {api_sdk_response.prompt_feedback.block_reason.name}. Ratings: {api_sdk_response.prompt_feedback.safety_ratings}"
            logger.warning(f"{log_prefix}: {processed_result['error_message']}")
            return processed_result

        if not api_sdk_response.candidates:
            processed_result["error_message"] = "No candidates in Gemini response."
            logger.warning(f"{log_prefix}: {processed_result['error_message']}")
            return processed_result

        first_candidate = api_sdk_response.candidates[0]
        finish_reason = getattr(first_candidate, "finish_reason", None)

        if finish_reason and finish_reason.name.upper() != "STOP":
            processed_result["status"] = "blocked_response"
            processed_result["error_message"] = f"Response generation stopped. Reason: {finish_reason.name}. Safety: {getattr(first_candidate, 'safety_ratings', 'N/A')}"
            logger.warning(f"{log_prefix}: {processed_result['error_message']}")
            if hasattr(first_candidate, "content") and first_candidate.content and first_candidate.content.parts:
                processed_result["text_content"] = "".join(part.text for part in first_candidate.content.parts if hasattr(part, "text")).strip()
            return processed_result

        processed_result["status"] = "success"
        processed_result["error_message"] = None
        processed_result["text_content"] = (
            "".join(part.text for part in first_candidate.content.parts if hasattr(part, "text")).strip()
            if hasattr(first_candidate, "content") and first_candidate.content and first_candidate.content.parts
            else ""
        )

        if processed_result["text_content"]:
            text_for_json = processed_result["text_content"]
            if text_for_json.startswith("```json"):
                text_for_json = text_for_json[7:]
            elif text_for_json.startswith("```"):
                text_for_json = text_for_json[3:]
            if text_for_json.endswith("```"):
                text_for_json = text_for_json[:-3]
            text_for_json = text_for_json.strip()
            try:
                processed_result["json_content"] = json.loads(text_for_json)
                logger.debug(f"{log_prefix}: Response parsed as JSON.")
            except json.JSONDecodeError:
                logger.debug(f"{log_prefix}: Response not valid JSON.")
                processed_result["json_content"] = None
        else:
            processed_result["json_content"] = None

        logger.info(f"{log_prefix}: Query processing successful. JSON: {processed_result['json_content'] is not None}.")
        return processed_result

    def query_vision_model(
        self,
        prompt: str,
        image_data: Optional[np.ndarray] = None,
        model_preference: Optional[List[str]] = None,
        model_name_override: Optional[str] = None,
        custom_generation_config: Optional[GenerationConfig] = None,
        custom_safety_settings: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if model_name_override:
            effective_model_preference = [model_name_override]
        elif model_preference:
            effective_model_preference = model_preference
        else:
            effective_model_preference = [self.default_model_name]

        result: Dict[str, Any] = {
            "status": "error_client",
            "text_content": None,
            "json_content": None,
            "error_message": "Client not initialized.",
            "model_used": effective_model_preference if effective_model_preference else "N/A",
            "latency_ms": 0,
            "raw_gemini_response": None,
        }

        if not self.client_initialized:
            logger.error(f"GeminiQuery: {result['error_message']}")
            result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return result

        api_contents, input_error = self._validate_and_prepare_api_input(prompt, image_data, "GeminiQuery")
        if input_error:
            result.update(input_error)
            result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return result

        effective_gen_config = custom_generation_config or self.generation_config
        effective_safety_settings = custom_safety_settings if custom_safety_settings is not None else self.safety_settings

        result = self._attempt_sdk_call_with_fallback(api_contents or [], effective_model_preference, effective_gen_config, effective_safety_settings)

        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"GeminiQuery (Final Status): '{result['status']}' on model '{result.get('model_used', 'N/A')}'. Latency: {result['latency_ms']}ms.")
        return result