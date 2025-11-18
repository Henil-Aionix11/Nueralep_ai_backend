"""Configuration Manager."""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from app.core.config.types import CONFIG_TYPES


class ConfigurationManager:
    """Manages application configuration by loading and validating YAML config files.

    The manager loads all YAML files from the config directory and validates them
    against their corresponding Pydantic models defined in CONFIG_TYPES.
    """

    def __init__(self) -> None:
        self._config_dir = Path(__file__).parent
        self._configs: dict[str, Any] = {}
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load and validate all configuration files from the config directory."""
        for config_file in self._config_dir.glob("*.yaml"):
            if config_file.name in CONFIG_TYPES:
                try:
                    # Load YAML
                    with config_file.open(encoding="utf-8") as f:
                        raw_config = yaml.safe_load(f)

                    # Validate with Pydantic model
                    model_class = CONFIG_TYPES[config_file.name]
                    validated_config = model_class(**raw_config)

                    # Store the validated config
                    config_name = config_file.stem
                    self._configs[config_name] = validated_config

                    logger.info(
                        f"Loaded configuration: {config_name}",
                        payload={"file": config_file.name},
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load configuration: {config_file.name}",
                        payload={"error": str(e)},
                    )
                    raise RuntimeError(
                        f"Invalid configuration in {config_file.name}: {e!s}",
                    ) from e

    def get_config(self, name: str) -> Any:
        """Get a specific configuration by name."""
        if name not in self._configs:
            raise KeyError(f"Configuration '{name}' not found")
        return self._configs[name]

    @property
    def configs(self) -> dict[str, Any]:
        """Get all configurations."""
        return self._configs


# Create a singleton instance
config_manager = ConfigurationManager()
