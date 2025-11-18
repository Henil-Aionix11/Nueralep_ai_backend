"""This module contains the AppEnv enum.

This enum represents the possible application runtime environments.

Attributes:
    AppEnv {class} -- AppEnv enum class.
"""

from app.core.enums.base_enum import BaseEnum


class AppEnv(BaseEnum):
    """Possible application runtime environments.

    Attributes:
        LOCAL {str} -- Local development environment with detailed logging
        DEV {str} -- Development environment on AWS
        STAGE {str} -- Staging environment
        PROD {str} -- Production environment
    """

    LOCAL = "local"
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"
