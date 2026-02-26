"""API route modules."""

from data_cataloger.web.routes.cataloging import router as cataloging_router
from data_cataloger.web.routes.export import router as export_router
from data_cataloger.web.routes.graph import router as graph_router
from data_cataloger.web.routes.progress import router as progress_router
from data_cataloger.web.routes.tables import router as tables_router

__all__ = [
    "tables_router",
    "graph_router",
    "progress_router",
    "cataloging_router",
    "export_router",
]
