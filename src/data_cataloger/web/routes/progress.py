"""SSE progress endpoint for real-time cataloging updates."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from data_cataloger.web.dependencies import get_database_name

router = APIRouter(prefix="/api/progress", tags=["progress"])

# Global progress state (in production, use Redis or similar)
progress_state: dict[str, dict[str, Any]] = {}


async def progress_generator(
    database_name: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Generate SSE events for cataloging progress."""
    last_index = 0

    while True:
        state = progress_state.get(database_name, {})

        if state.get("completed"):
            yield {
                "event": "cataloging:completed",
                "data": json.dumps({
                    "total_tables": state.get("total", 0),
                    "duration_seconds": state.get("duration", 0),
                }),
            }
            break

        current_index = state.get("current_index", 0)
        if current_index > last_index:
            yield {
                "event": "table:completed",
                "data": json.dumps({
                    "table_name": state.get("current_table", ""),
                    "index": current_index,
                    "total": state.get("total", 0),
                }),
            }
            last_index = current_index

        # Heartbeat to keep connection alive
        yield {"event": "heartbeat", "data": json.dumps({"status": "alive"})}

        await asyncio.sleep(1)


@router.get("")
async def progress_stream(
    database_name: Annotated[str, Depends(get_database_name)],
) -> EventSourceResponse:
    """SSE stream for cataloging progress updates."""
    return EventSourceResponse(progress_generator(database_name))


def update_progress(
    database_name: str,
    table_name: str,
    index: int,
    total: int,
) -> None:
    """Update progress state (called from cataloging pipeline)."""
    progress_state[database_name] = {
        "current_table": table_name,
        "current_index": index,
        "total": total,
        "completed": False,
    }


def complete_progress(database_name: str, duration: float) -> None:
    """Mark cataloging as complete."""
    state = progress_state.get(database_name, {})
    state["completed"] = True
    state["duration"] = duration
    progress_state[database_name] = state
