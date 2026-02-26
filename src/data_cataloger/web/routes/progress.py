"""SSE progress endpoint for real-time cataloging updates."""

import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass, field
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from data_cataloger.web.dependencies import get_database_name

router = APIRouter(prefix="/api/progress", tags=["progress"])


@dataclass
class TableEvent:
    """Event data for a cataloged table."""
    table_name: str
    description: str
    sensitivity: str
    example_queries: list[str]
    schema_name: str = "public"
    foreign_keys: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CatalogingState:
    """State for an active cataloging session."""
    total_tables: int = 0
    processed_tables: int = 0
    current_table: str = ""
    completed: bool = False
    duration: float = 0.0
    events: list[TableEvent] = field(default_factory=list)
    event_index: int = 0  # Track which events have been sent


# Global progress state (in production, use Redis or similar)
progress_state: dict[str, CatalogingState] = {}


async def progress_generator(
    database_name: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Generate SSE events for cataloging progress with full table data."""
    last_event_index = 0

    while True:
        state = progress_state.get(database_name)
        
        if state is None:
            # No cataloging started yet, send heartbeat
            yield {"event": "heartbeat", "data": json.dumps({"status": "waiting"})}
            await asyncio.sleep(1)
            continue

        # Send any new table events
        while last_event_index < len(state.events):
            event = state.events[last_event_index]
            yield {
                "event": "table:cataloged",
                "data": json.dumps({
                    "table_name": event.table_name,
                    "description": event.description,
                    "sensitivity": event.sensitivity,
                    "example_queries": event.example_queries,
                    "schema_name": event.schema_name,
                    "foreign_keys": event.foreign_keys,
                    "index": last_event_index + 1,
                    "total": state.total_tables,
                }),
            }
            last_event_index += 1

        if state.completed:
            yield {
                "event": "cataloging:completed",
                "data": json.dumps({
                    "total_tables": state.total_tables,
                    "duration_seconds": state.duration,
                }),
            }
            break

        # Heartbeat to keep connection alive
        yield {
            "event": "heartbeat", 
            "data": json.dumps({
                "status": "processing",
                "current_table": state.current_table,
                "processed": state.processed_tables,
                "total": state.total_tables,
            })
        }

        await asyncio.sleep(0.5)


@router.get("")
async def progress_stream(
    database_name: Annotated[str, Depends(get_database_name)],
) -> EventSourceResponse:
    """SSE stream for cataloging progress updates."""
    return EventSourceResponse(progress_generator(database_name))


def init_cataloging(database_name: str, total_tables: int) -> None:
    """Initialize cataloging session."""
    progress_state[database_name] = CatalogingState(
        total_tables=total_tables,
        processed_tables=0,
        current_table="",
        completed=False,
        events=[],
    )


def emit_table_event(
    database_name: str,
    table_name: str,
    description: str,
    sensitivity: str,
    example_queries: list[str],
    schema_name: str,
    foreign_keys: list[dict[str, str]],
) -> None:
    """Emit event when a table is cataloged."""
    state = progress_state.get(database_name)
    if state is None:
        return
    
    event = TableEvent(
        table_name=table_name,
        description=description,
        sensitivity=sensitivity,
        example_queries=example_queries,
        schema_name=schema_name,
        foreign_keys=foreign_keys,
    )
    state.events.append(event)
    state.processed_tables += 1
    state.current_table = table_name


def complete_cataloging(database_name: str, duration: float) -> None:
    """Mark cataloging as complete."""
    state = progress_state.get(database_name)
    if state is None:
        return
    state.completed = True
    state.duration = duration


def reset_cataloging(database_name: str) -> None:
    """Reset cataloging state for a new session."""
    if database_name in progress_state:
        del progress_state[database_name]
