"""Factory for SendGrid sender."""

from functools import lru_cache

from app.web.settings import settings
from app.core.utilities.sendgrid_utility import SendgridSender


@lru_cache()
def get_sendgrid_sender() -> SendgridSender:
    """
    Factory function to create a SendgridSender instance.
    Uses lru_cache to ensure a single instance is created.

    Returns:
        SendgridSender: An instance of the SendgridSender
    """
    return SendgridSender(sendgrid_api_key=settings.sendgrid_api_key)
