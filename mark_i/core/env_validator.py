import os
import logging
from typing import Dict, Any, List, Callable, NamedTuple

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.core.env_validator")


class EnvConfig(NamedTuple):
    """A typed container for the validated environment variables."""

    APP_ENV: str
    GEMINI_API_KEY: str
    GEMINI_MODELS_PRO: List[str]
    GEMINI_MODELS_FLASH: List[str]
    GEMINI_MODELS_NANO: List[str]


def _parse_str_list(value: str) -> List[str]:
    """Parses a comma-separated string into a list of non-empty, stripped strings."""
    if not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


# The schema defining all expected environment variables for the application.
ENV_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "APP_ENV",
        "required": False,
        "default": "production",
        "type": str,
        "description": "The application environment (development, production).",
        "validator": lambda v: v in ["development", "uat", "production"],
    },
    {"name": "GEMINI_API_KEY", "required": True, "default": None, "type": str, "description": "The API key for Google Gemini services."},
    {
        # --- FIX: Changed name to plural to match EnvConfig ---
        "name": "GEMINI_MODELS_PRO",
        "required": False,
        "default": "gemini-pro-latest",
        "type": _parse_str_list,
        "description": "Comma-separated list of models for high-level reasoning.",
    },
    {
        # --- FIX: Changed name to plural to match EnvConfig ---
        "name": "GEMINI_MODELS_FLASH",
        "required": False,
        "default": "gemini-flash-latest",
        "type": _parse_str_list,
        "description": "Comma-separated list of models for fast, tactical execution.",
    },
    {
        # --- FIX: Changed name to plural to match EnvConfig ---
        "name": "GEMINI_MODELS_NANO",
        "required": False,
        "default": "gemini-flash-lite-latest",
        "type": _parse_str_list,
        "description": "Comma-separated list of lightweight models for simple parsing tasks.",
    },
]


def load_and_validate_env() -> EnvConfig:
    """
    Loads, validates, and type-casts environment variables based on the ENV_SCHEMA.
    This is the single source of truth for environment-based configuration.

    Raises:
        ValueError: If a required environment variable is missing or fails validation.

    Returns:
        An EnvConfig object with the validated configuration.
    """
    logger.info("--- Validating Environment Variables ---")
    validated_config: Dict[str, Any] = {}

    for var_def in ENV_SCHEMA:
        name = var_def["name"]
        raw_value = os.getenv(name)

        # 1. Check for presence and handle required variables
        if raw_value is None:
            if var_def["required"]:
                err_msg = f"Required environment variable '{name}' is not set. Description: {var_def['description']}"
                logger.critical(err_msg)
                raise ValueError(err_msg)
            else:
                # --- FIX: Ensure default for lists is processed by the type caster ---
                cast_default = var_def["type"](var_def["default"]) if var_def["type"] is _parse_str_list else var_def["default"]
                validated_config[name] = cast_default
                logger.info(f"'{name}' not set, using default value: {cast_default}")
                continue

        # 2. Type casting
        try:
            cast_value = var_def["type"](raw_value)
        except Exception as e:
            err_msg = f"Environment variable '{name}' with value '{raw_value}' could not be cast to the expected type. Error: {e}"
            logger.critical(err_msg)
            raise ValueError(err_msg) from e

        # 3. Custom validation
        validator = var_def.get("validator")
        if validator and not validator(cast_value):
            err_msg = f"Environment variable '{name}' with value '{cast_value}' failed validation."
            logger.critical(err_msg)
            raise ValueError(err_msg)

        validated_config[name] = cast_value
        log_value = cast_value if name != "GEMINI_API_KEY" else f"Loaded (length: {len(cast_value)})"
        logger.info(f"'{name}' loaded and validated. Value: {log_value}")

    logger.info("--- Environment Variable Validation Complete ---")
    return EnvConfig(**validated_config)
