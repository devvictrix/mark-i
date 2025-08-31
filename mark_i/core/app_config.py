import os
import logging
from typing import List

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.core.env_validator import load_and_validate_env, EnvConfig

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.core.app_config")

# --- Centralized AI Model and App Configuration ---
# This module is the single source of truth for all environment-based configurations.
# It runs the validator once at startup and exports the validated, typed results.

try:
    VALIDATED_CONFIG: EnvConfig = load_and_validate_env()
except ValueError as e:
    logger.critical(f"Fatal configuration error: {e}. The application cannot start.", exc_info=True)
    # In a real application, you might want to show a popup here before exiting.
    exit(1)

# --- Export validated variables for other modules to import ---

# The most powerful and intelligent model(s), used for complex reasoning and planning.
GEMINI_MODELS_PRO: List[str] = VALIDATED_CONFIG.GEMINI_MODELS_PRO

# The fast, efficient workhorse model(s), used for tactical, step-by-step execution.
GEMINI_MODELS_FLASH: List[str] = VALIDATED_CONFIG.GEMINI_MODELS_FLASH

# The fastest, lightweight model(s) for simple, high-frequency tasks.
GEMINI_MODELS_NANO: List[str] = VALIDATED_CONFIG.GEMINI_MODELS_NANO

# --- Construct Model Preference Chains ---
# By using dict.fromkeys, we create an ordered set to remove duplicates
# while preserving the specified order of preference.
MODEL_PREFERENCE_REASONING: List[str] = list(dict.fromkeys(GEMINI_MODELS_PRO + GEMINI_MODELS_FLASH))
MODEL_PREFERENCE_FAST: List[str] = list(dict.fromkeys(GEMINI_MODELS_FLASH + GEMINI_MODELS_NANO))

logger.info("--- AI Model Preference Chains Constructed ---")
logger.info(f"  Reasoning Chain:   {MODEL_PREFERENCE_REASONING}")
logger.info(f"  Fast Chain:        {MODEL_PREFERENCE_FAST}")
logger.info("------------------------------------------")
