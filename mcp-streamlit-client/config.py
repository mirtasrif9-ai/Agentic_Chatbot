import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Environment loading
# ============================================================
#
# Load .env from mcp-streamlit-client/ (this file's folder)
# regardless of where Streamlit is launched from.
#
# A second, non-overriding load from the project root is
# included so shared secrets can also live there if needed.

CONFIG_DIR = Path(__file__).resolve().parent

load_dotenv(CONFIG_DIR / ".env")
load_dotenv(CONFIG_DIR.parent / ".env", override=False)


# ============================================================
# General
# ============================================================

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)


# ============================================================
# Base project directory
# ============================================================

BASE_DIR = Path(
    r"D:\AI_Trainning\Practices\Agentic_Chatbot"
)


# ============================================================
# Custom Tools MCP Server - LOCAL
# ============================================================

CUSTOM_SERVER_DIR = (
    BASE_DIR / "custom-mcp-server"
)

CUSTOM_SERVER_PYTHON = (
    CUSTOM_SERVER_DIR
    / "venv"
    / "Scripts"
    / "python.exe"
)

CUSTOM_SERVER_SCRIPT = (
    CUSTOM_SERVER_DIR
    / "server.py"
)


# ============================================================
# Manim MCP Server - LOCAL
# ============================================================

MANIM_SERVER_DIR = (
    BASE_DIR
    / "manim-mcp"
)

MANIM_SERVER_PYTHON = (
    MANIM_SERVER_DIR
    / "venv"
    / "Scripts"
    / "python.exe"
)

MANIM_SERVER_SCRIPT = (
    MANIM_SERVER_DIR
    / "manim-mcp-server"
    / "src"
    / "manim_server.py"
)

MANIM_EXECUTABLE = (
    MANIM_SERVER_DIR
    / "venv"
    / "Scripts"
    / "manim.exe"
)


# ============================================================
# Weather MCP Server - LOCAL
# ============================================================

WEATHER_SERVER_DIR = (
    BASE_DIR
    / "weather-mcp"
    / "mcp-weather"
)

WEATHER_PYTHON = (
    WEATHER_SERVER_DIR
    / ".venv"
    / "Scripts"
    / "python.exe"
)

ACCUWEATHER_API_KEY = os.getenv(
    "ACCUWEATHER_API_KEY"
)


# ============================================================
# Custom Tools MCP Server - REMOTE (FastMCP Cloud)
# ============================================================
#
# .env keys used here:
#   HORIZON_MCP_URL  -> REMOTE_MCP_URL
#   FASTMCP_TOKEN    -> REMOTE_TOKEN

REMOTE_MCP_URL = os.getenv(
    "HORIZON_MCP_URL",
    "https://age-calculator-mcp-server.fastmcp.app/mcp",
)

REMOTE_TOKEN = (
    os.getenv("FASTMCP_TOKEN") or ""
).strip()


# ============================================================
# Timeouts
# ============================================================

SERVER_LOAD_TIMEOUT = 90
REMOTE_SERVER_TIMEOUT = 300
TOOL_TIMEOUT = 180

MAX_TOOL_ROUNDS = 5