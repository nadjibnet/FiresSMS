"""API token validation."""
import os
import logging

logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("API_TOKEN", "changeme")


def validate_token(token):
    """Return True if the supplied token matches the configured API token."""
    if token != API_TOKEN:
        logger.warning("Unauthorized token: %s", token)
        return False
    return True
