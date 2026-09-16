"""A small MCP SDK v2 port of the official Time reference server.

Adapted from:
https://github.com/modelcontextprotocol/servers/tree/main/src/time

The original code is licensed under the MIT License. See LICENSE.
This file has been modified to use MCPServer from MCP Python SDK v2.
"""

import argparse
from datetime import datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from tzlocal import get_localzone_name


class TimeResult(BaseModel):
    timezone: str
    datetime: str
    day_of_week: str
    is_dst: bool


class TimeConversionResult(BaseModel):
    source: TimeResult
    target: TimeResult
    time_difference: str


READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def get_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ToolError(f"Invalid timezone: {timezone_name}") from error


def get_local_timezone(override: str | None = None) -> str:
    if override:
        get_zoneinfo(override)
        return override

    try:
        return get_localzone_name()
    except ZoneInfoNotFoundError:
        return "UTC"


def create_server(local_timezone: str | None = None) -> MCPServer:
    local_tz = get_local_timezone(local_timezone)
    mcp = MCPServer("mcp-time")

    @mcp.tool(annotations=READ_ONLY)
    def get_current_time(
        timezone: Annotated[
            str,
            Field(
                description=(
                    "IANA timezone name, for example 'America/New_York' or "
                    f"'Europe/London'. Use '{local_tz}' when the user does not "
                    "specify a timezone."
                )
            ),
        ],
    ) -> TimeResult:
        """Get the current time in a specific timezone."""
        current_time = datetime.now(get_zoneinfo(timezone))
        return TimeResult(
            timezone=timezone,
            datetime=current_time.isoformat(timespec="seconds"),
            day_of_week=current_time.strftime("%A"),
            is_dst=bool(current_time.dst()),
        )

    @mcp.tool(annotations=READ_ONLY)
    def convert_time(
        source_timezone: Annotated[
            str,
            Field(description="Source IANA timezone name."),
        ],
        time: Annotated[
            str,
            Field(description="Time to convert in 24-hour HH:MM format."),
        ],
        target_timezone: Annotated[
            str,
            Field(description="Target IANA timezone name."),
        ],
    ) -> TimeConversionResult:
        """Convert today's time from one timezone to another."""
        source_tz = get_zoneinfo(source_timezone)
        target_tz = get_zoneinfo(target_timezone)

        try:
            parsed_time = datetime.strptime(time, "%H:%M").time()
        except ValueError as error:
            raise ToolError(
                "Invalid time format. Expected HH:MM in 24-hour format."
            ) from error

        today = datetime.now(source_tz)
        source_time = datetime.combine(today.date(), parsed_time, source_tz)
        target_time = source_time.astimezone(target_tz)

        source_offset = source_time.utcoffset() or timedelta()
        target_offset = target_time.utcoffset() or timedelta()
        hours_difference = (target_offset - source_offset).total_seconds() / 3600
        if hours_difference.is_integer():
            time_difference = f"{hours_difference:+.1f}h"
        else:
            time_difference = (
                f"{hours_difference:+.2f}".rstrip("0").rstrip(".") + "h"
            )

        return TimeConversionResult(
            source=TimeResult(
                timezone=source_timezone,
                datetime=source_time.isoformat(timespec="seconds"),
                day_of_week=source_time.strftime("%A"),
                is_dst=bool(source_time.dst()),
            ),
            target=TimeResult(
                timezone=target_timezone,
                datetime=target_time.isoformat(timespec="seconds"),
                day_of_week=target_time.strftime("%A"),
                is_dst=bool(target_time.dst()),
            ),
            time_difference=time_difference,
        )

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provide time queries and timezone conversions over MCP."
    )
    parser.add_argument("--local-timezone", help="Override the local timezone.")
    args = parser.parse_args()
    create_server(args.local_timezone).run()


if __name__ == "__main__":
    main()
