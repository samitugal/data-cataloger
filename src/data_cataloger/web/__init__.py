"""Web interface for Data Cataloger.

Provides web-based visualization and interaction with the database catalog.
Enables browsing tables, viewing relationships, and searching metadata.
"""

from data_cataloger.web.app import app, create_app

__all__ = ["app", "create_app"]
