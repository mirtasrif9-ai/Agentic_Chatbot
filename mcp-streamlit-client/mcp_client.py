import asyncio
import json
import re
import shutil
from collections import Counter

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import (
    CUSTOM_SERVER_PYTHON,
    CUSTOM_SERVER_SCRIPT,

    MANIM_SERVER_PYTHON,
    MANIM_SERVER_SCRIPT,
    MANIM_EXECUTABLE,

    WEATHER_PYTHON,
    WEATHER_SERVER_DIR,
    ACCUWEATHER_API_KEY,

    REMOTE_MCP_URL,
    REMOTE_TOKEN,

    SERVER_LOAD_TIMEOUT,
    REMOTE_SERVER_TIMEOUT,
)


# ============================================================
# Server metadata
# ============================================================

SERVER_INFO = {

    "custom-local": {
        "scope": "LOCAL",
        "transport": "STDIO",
        "label": "Custom Tools",
    },

    "manim": {
        "scope": "LOCAL",
        "transport": "STDIO",
        "label": "Manim",
    },

    "weather": {
        "scope": "LOCAL",
        "transport": "STDIO",
        "label": "Weather",
    },

    "custom-remote": {
        "scope": "REMOTE",
        "transport": "STREAMABLE HTTP",
        "label": "Deployed Custom Tools",
    },
}


# ============================================================
# Build MCP server configuration
# ============================================================

def build_servers():

    servers = {}
    skipped = {}

    # --------------------------------------------------------
    # Custom Tools
    # --------------------------------------------------------

    servers["custom-local"] = {
        "transport": "stdio",

        "command": str(
            CUSTOM_SERVER_PYTHON
        ),

        "args": [
            str(CUSTOM_SERVER_SCRIPT)
        ],
    }

    # --------------------------------------------------------
    # Manim
    # --------------------------------------------------------

    servers["manim"] = {

        "transport": "stdio",

        "command": str(
            MANIM_SERVER_PYTHON
        ),

        "args": [
            str(MANIM_SERVER_SCRIPT)
        ],

        "env": {
            "MANIM_EXECUTABLE": str(
                MANIM_EXECUTABLE
            )
        },
    }

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    if ACCUWEATHER_API_KEY:

        servers["weather"] = {

            "transport": "stdio",

            "command": str(
                WEATHER_PYTHON
            ),

            "args": [
                "-c",
                (
                    "from mcp_weather.weather "
                    "import mcp; mcp.run()"
                ),
            ],

            "cwd": str(
                WEATHER_SERVER_DIR
            ),

            "env": {
                "ACCUWEATHER_API_KEY":
                    ACCUWEATHER_API_KEY
            },
        }

    else:

        skipped["weather"] = (
            "ACCUWEATHER_API_KEY is not configured."
        )

    # --------------------------------------------------------
    # Remote Horizon MCP
    # --------------------------------------------------------

    remote_config = {

        "transport": "streamable_http",

        "url": REMOTE_MCP_URL,
    }

    if REMOTE_TOKEN:

        remote_config["headers"] = {
            "Authorization":
                f"Bearer {REMOTE_TOKEN}"
        }

    servers["custom-remote"] = remote_config

    return servers, skipped


# ============================================================
# Validate local servers
# ============================================================

def validate_server(spec):

    problems = []

    transport = spec.get(
        "transport"
    )

    if transport == "stdio":

        command = spec.get(
            "command"
        )

        if not command:

            problems.append(
                "Missing command."
            )

        elif not (
            shutil.which(command)
            or __import__("pathlib").Path(command).exists()
        ):

            problems.append(
                f"Command not found: {command}"
            )

        for arg in spec.get(
            "args",
            []
        ):

            if (
                isinstance(arg, str)
                and arg.lower().endswith(".py")
                and not __import__("pathlib")
                .Path(arg)
                .exists()
            ):

                problems.append(
                    f"Python script not found: {arg}"
                )

        for key, value in spec.get(
            "env",
            {}
        ).items():

            if (
                key.endswith(
                    "EXECUTABLE"
                )
                and not __import__("pathlib")
                .Path(value)
                .exists()
            ):

                problems.append(
                    f"{key} not found: {value}"
                )

    elif transport in (
        "streamable_http",
        "sse",
        "http",
    ):

        if not spec.get("url"):

            problems.append(
                "Missing remote URL."
            )

    else:

        problems.append(
            f"Unsupported transport: {transport}"
        )

    return problems


# ============================================================
# Error helpers
# ============================================================

def flatten_errors(error):

    if isinstance(
        error,
        BaseExceptionGroup
    ):

        output = []

        for item in error.exceptions:

            output.extend(
                flatten_errors(item)
            )

        return output

    return [error]


def describe_error(error):

    parts = []

    for item in flatten_errors(error):

        if isinstance(
            item,
            TimeoutError
        ):

            parts.append(
                "TimeoutError: no response in time"
            )

        else:

            parts.append(
                f"{type(item).__name__}: {item}"
            )

    return " | ".join(parts)


# ============================================================
# Resolve duplicate tool names
# ============================================================

def resolve_tool_collisions(
    tools_by_server
):

    counts = Counter(
        tool.name
        for tools in tools_by_server.values()
        for tool in tools
    )

    for server, tools in (
        tools_by_server.items()
    ):

        for index, tool in enumerate(
            tools
        ):

            if counts[tool.name] > 1:

                safe_server_name = re.sub(
                    r"[^a-zA-Z0-9_]",
                    "_",
                    server,
                )

                tools[index] = (
                    tool.model_copy(
                        update={
                            "name":
                                f"{safe_server_name}_{tool.name}"
                        }
                    )
                )


# ============================================================
# Load tools
# ============================================================

async def load_tools(
    client,
    server_names,
):

    tools_by_server = {}
    tools_by_name = {}

    failed = {}
    warnings = []

    for server_name in server_names:

        try:

            timeout = (
                REMOTE_SERVER_TIMEOUT
                if server_name
                == "custom-remote"
                else SERVER_LOAD_TIMEOUT
            )

            tools = await asyncio.wait_for(
                client.get_tools(
                    server_name=server_name
                ),
                timeout=timeout,
            )

        except Exception as error:

            failed[
                server_name
            ] = describe_error(error)

            continue

        tools_by_server[
            server_name
        ] = list(tools)

    # --------------------------------------------------------
    # Prefix remote tools
    # --------------------------------------------------------

    if "custom-remote" in tools_by_server:

        prefixed = []

        for tool in tools_by_server[
            "custom-remote"
        ]:

            prefixed.append(
                tool.model_copy(
                    update={
                        "name":
                            "remote_"
                            + tool.name,

                        "description":
                            "[DEPLOYED REMOTE MCP] "
                            + (
                                tool.description
                                or ""
                            ),
                    }
                )
            )

        tools_by_server[
            "custom-remote"
        ] = prefixed

    # --------------------------------------------------------
    # Resolve any remaining collisions
    # --------------------------------------------------------

    resolve_tool_collisions(
        tools_by_server
    )

    # --------------------------------------------------------
    # Build lookup
    # --------------------------------------------------------

    for server, tools in (
        tools_by_server.items()
    ):

        clean_tools = []

        for tool in tools:

            if tool.name in tools_by_name:

                warnings.append(
                    f"Duplicate tool '{tool.name}' "
                    f"from '{server}' ignored."
                )

                continue

            tools_by_name[
                tool.name
            ] = tool

            clean_tools.append(
                tool
            )

        tools_by_server[
            server
        ] = clean_tools

    return (
        tools_by_server,
        tools_by_name,
        failed,
        warnings,
    )


# ============================================================
# Public connection function
# ============================================================

async def connect_to_mcp_servers():

    servers, skipped = (
        build_servers()
    )

    good_servers = {}

    for name, config in (
        servers.items()
    ):

        problems = validate_server(
            config
        )

        if problems:

            skipped[name] = (
                "; ".join(problems)
            )

        else:

            good_servers[
                name
            ] = config

    client = MultiServerMCPClient(
        good_servers
    )

    (
        tools_by_server,
        tools_by_name,
        failed,
        warnings,
    ) = await load_tools(
        client,
        list(good_servers.keys())
    )

    return {
        "client": client,
        "tools_by_server":
            tools_by_server,
        "tools_by_name":
            tools_by_name,
        "failed":
            failed,
        "skipped":
            skipped,
        "warnings":
            warnings,
    }


# ============================================================
# Convert tool output to readable text
# ============================================================

def result_to_text(result):

    if isinstance(
        result,
        tuple
    ) and result:

        result = result[0]

    if isinstance(
        result,
        str
    ):

        return result

    if isinstance(
        result,
        list
    ):

        parts = []

        for item in result:

            if isinstance(
                item,
                str
            ):

                parts.append(item)

            elif isinstance(
                item,
                dict
            ):

                if "text" in item:

                    parts.append(
                        item["text"]
                    )

            elif getattr(
                item,
                "text",
                None
            ):

                parts.append(
                    item.text
                )

        if parts:

            return "\n".join(parts)

    try:

        return json.dumps(
            result,
            default=str,
            ensure_ascii=False,
        )

    except Exception:

        return str(result)