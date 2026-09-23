
import asyncio
import json

import streamlit as st

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from agent import (
    MCPAgent,
    SYSTEM_PROMPT,
)

from mcp_client import (
    connect_to_mcp_servers,
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="MCP Command Center",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Theme — Baby Orange · Glassy · Premium
# ============================================================

def inject_css():

    st.markdown(
        """
        <style>

        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap'
        );

        :root {

            /* Surfaces */
            --bg-1: #fff8f2;
            --bg-2: #fff1e3;
            --bg-3: #ffe8d4;

            --glass: rgba(255, 255, 255, 0.72);
            --glass-2: rgba(255, 252, 247, 0.85);
            --glass-3: rgba(255, 245, 235, 0.55);

            /* Ink */
            --ink: #3d2817;
            --ink-2: #5c3d28;
            --muted: #a1876f;
            --muted-2: #c4a98f;

            /* Orange accents */
            --o-1: #ffb380;
            --o-2: #ff9a56;
            --o-3: #f57a3a;
            --o-4: #d95a2a;
            --o-5: #b8421a;

            /* Lines / borders */
            --line: #f5dcc8;
            --line-2: #ecc9a8;
            --line-3: #dcb48e;

            /* Shadows */
            --sh-sm: 0 6px 20px rgba(200, 120, 60, 0.08);
            --sh-md: 0 14px 40px rgba(200, 120, 60, 0.12);
            --sh-lg: 0 26px 70px rgba(200, 120, 60, 0.16);
            --sh-glow: 0 0 0 4px rgba(255, 154, 86, 0.10);
        }


        html, body, [class*="css"] {
            font-family: "Inter", system-ui, sans-serif;
        }


        .stApp {

            background:

                radial-gradient(
                    circle at 12% -5%,
                    rgba(255, 183, 128, 0.42),
                    transparent 32%
                ),

                radial-gradient(
                    circle at 92% 4%,
                    rgba(255, 209, 168, 0.55),
                    transparent 34%
                ),

                radial-gradient(
                    circle at 50% 110%,
                    rgba(255, 154, 86, 0.16),
                    transparent 40%
                ),

                linear-gradient(
                    180deg,
                    var(--bg-1) 0%,
                    var(--bg-2) 48%,
                    var(--bg-3) 100%
                );

            color: var(--ink);
            min-height: 100vh;
        }


        [data-testid="stHeader"] {
            background: transparent;
        }


        .block-container {
            max-width: 1480px;
            padding: 2rem 2.6rem 4rem;
        }


        /* ---------- Animations ---------- */

        @keyframes riseIn {

            from {
                opacity: 0;
                transform: translateY(14px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }


        @keyframes softPulse {

            0%, 100% {
                opacity: 1;
            }

            50% {
                opacity: 0.55;
            }
        }


        .rise {
            animation: riseIn .55s cubic-bezier(.16,1,.3,1) both;
        }


        /* ---------- Hero ---------- */

        .hero {

            position: relative;
            overflow: hidden;

            background:

                linear-gradient(
                    125deg,
                    rgba(255, 250, 245, 0.94) 0%,
                    rgba(255, 236, 220, 0.94) 55%,
                    rgba(255, 222, 198, 0.94) 100%
                );

            border: 1px solid rgba(255, 255, 255, 0.7);

            border-radius: 26px;

            padding: 1.6rem 1.9rem 1.5rem;

            margin-bottom: 1.6rem;

            box-shadow: var(--sh-lg);

            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);
        }


        .hero::after {

            content: "";

            position: absolute;

            width: 320px;
            height: 320px;

            right: -110px;
            top: -150px;

            border-radius: 50%;

            background:

                radial-gradient(
                    circle,
                    rgba(255, 154, 86, 0.28),
                    transparent 70%
                );

            pointer-events: none;
        }


        .hero::before {

            content: "";

            position: absolute;

            width: 180px;
            height: 180px;

            left: -60px;
            bottom: -110px;

            border-radius: 50%;

            background:

                radial-gradient(
                    circle,
                    rgba(255, 179, 128, 0.32),
                    transparent 70%
                );

            pointer-events: none;
        }


        .hero-title {

            position: relative;

            font-family: "Plus Jakarta Sans", sans-serif;

            font-size: 2.05rem;

            font-weight: 800;

            letter-spacing: -0.045em;

            color: var(--ink);

            line-height: 1.1;
        }


        .hero-title span {

            background:

                linear-gradient(
                    120deg,
                    var(--o-3) 0%,
                    var(--o-2) 55%,
                    var(--o-1) 100%
                );

            -webkit-background-clip: text;
            background-clip: text;

            -webkit-text-fill-color: transparent;
        }


        .hero-sub {

            position: relative;

            color: var(--ink-2);

            margin-top: 0.55rem;

            font-size: 0.9rem;

            font-weight: 500;

            opacity: 0.85;
        }


        .pill-row {

            position: relative;

            display: flex;

            flex-wrap: wrap;

            gap: 0.5rem;

            margin-top: 1.05rem;
        }


        .pill {

            display: inline-flex;

            align-items: center;

            gap: 0.42rem;

            background: rgba(255, 255, 255, 0.72);

            border: 1px solid var(--line-2);

            border-radius: 999px;

            padding: 0.4rem 0.8rem;

            font-size: 0.72rem;

            font-weight: 700;

            color: var(--ink-2);

            letter-spacing: 0.01em;

            backdrop-filter: blur(10px);

            -webkit-backdrop-filter: blur(10px);

            box-shadow: var(--sh-sm);
        }


        .pill .dot {

            width: 7px;
            height: 7px;

            border-radius: 50%;

            background: var(--o-2);

            box-shadow:
                0 0 0 3px rgba(255, 154, 86, 0.20);
        }


        .pill.live .dot {

            background: #55c98a;

            box-shadow:
                0 0 0 3px rgba(85, 201, 138, 0.20);

            animation:
                softPulse 2.4s ease-in-out infinite;
        }


        /* ---------- Sidebar ---------- */

        section[data-testid="stSidebar"] {

            background:

                linear-gradient(
                    180deg,
                    rgba(255, 249, 242, 0.94) 0%,
                    rgba(255, 240, 226, 0.94) 100%
                );

            border-right: 1px solid var(--line);

            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }


        section[data-testid="stSidebar"] > div {
            padding-top: 1.4rem;
        }


        .side-title {

            font-family: "Plus Jakarta Sans", sans-serif;

            font-size: 1.06rem;

            font-weight: 800;

            color: var(--ink);

            letter-spacing: -0.02em;

            margin-bottom: 0.15rem;
        }


        .side-sub {

            color: var(--muted);

            font-size: 0.78rem;

            font-weight: 500;

            margin-bottom: 1rem;
        }


        .server-card {

            position: relative;

            background: var(--glass);

            border: 1px solid var(--line);

            border-radius: 16px;

            padding: 0.85rem 0.9rem 0.8rem;

            margin-bottom: 0.75rem;

            box-shadow: var(--sh-sm);

            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);

            transition:
                transform 0.2s cubic-bezier(.16,1,.3,1),
                box-shadow 0.2s;
        }


        .server-card:hover {

            transform: translateY(-2px);

            box-shadow: var(--sh-md);
        }


        .server-head {

            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 0.5rem;

            margin-bottom: 0.35rem;
        }


        .server-name {

            font-family: "Plus Jakarta Sans", sans-serif;

            font-size: 0.86rem;

            font-weight: 800;

            color: var(--ink);

            letter-spacing: -0.01em;
        }


        .badge {

            display: inline-flex;

            align-items: center;

            gap: 0.3rem;

            border-radius: 999px;

            padding: 0.2rem 0.55rem;

            font-size: 0.58rem;

            font-weight: 800;

            letter-spacing: 0.08em;
        }


        .badge.local {

            color: var(--o-5);

            background:
                rgba(255, 154, 86, 0.12);

            border:
                1px solid rgba(255, 154, 86, 0.30);
        }


        .badge.remote {

            color: #8a4a17;

            background:
                rgba(255, 204, 150, 0.35);

            border:
                1px solid rgba(217, 90, 42, 0.30);
        }


        .transport {

            color: var(--muted);

            font-size: 0.65rem;

            font-weight: 700;

            letter-spacing: 0.03em;

            margin-bottom: 0.55rem;
        }


        .server-tool {

            display: flex;

            align-items: center;

            gap: 0.45rem;

            background:
                rgba(255, 250, 245, 0.9);

            border:
                1px solid rgba(245, 220, 200, 0.75);

            border-radius: 9px;

            padding: 0.32rem 0.5rem;

            color: var(--ink-2);

            font-size: 0.72rem;

            font-weight: 600;

            margin-top: 0.28rem;
        }


        .server-tool .dot {

            width: 5px;
            height: 5px;

            border-radius: 50%;

            background: var(--o-2);

            box-shadow:
                0 0 0 2px rgba(255, 154, 86, 0.18);

            flex: none;
        }


        /* ---------- Chat ---------- */

        [data-testid="stChatMessage"] {

            background: var(--glass-2);

            border: 1px solid var(--line);

            border-radius: 20px !important;

            padding: 1rem 1.1rem !important;

            margin-bottom: 0.85rem !important;

            box-shadow: var(--sh-sm);

            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);

            transition:
                transform 0.2s cubic-bezier(.16,1,.3,1),
                box-shadow 0.2s;
        }


        [data-testid="stChatMessage"]:hover {
            box-shadow: var(--sh-md);
        }


        [data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-user"]
        ) {

            background:

                linear-gradient(
                    135deg,
                    rgba(255, 240, 226, 0.96),
                    rgba(255, 227, 205, 0.96)
                );

            border-color: var(--line-2);
        }


        [data-testid="stChatMessage"] p {

            line-height: 1.65;

            color: var(--ink);
        }


        [data-testid="stChatMessage"] pre {

            border-radius: 12px !important;

            border:
                1px solid var(--line) !important;

            background:
                rgba(255, 250, 245, 0.9) !important;
        }


        /* ---------- Tool events ---------- */

        .tool-event {

            background: var(--glass);

            border: 1px solid var(--line);

            border-radius: 14px;

            padding: 0.75rem 0.85rem;

            margin-bottom: 0.5rem;

            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);

            box-shadow: var(--sh-sm);
        }


        .tool-event-head {

            display: flex;

            align-items: center;

            gap: 0.5rem;

            flex-wrap: wrap;

            margin-bottom: 0.4rem;
        }


        .tool-event-name {

            font-family:
                "Plus Jakarta Sans", sans-serif;

            font-size: 0.82rem;

            font-weight: 800;

            color: var(--ink);
        }


        .tool-event-badge {

            display: inline-flex;

            align-items: center;

            gap: 0.28rem;

            border-radius: 999px;

            padding: 0.18rem 0.5rem;

            font-size: 0.58rem;

            font-weight: 800;

            letter-spacing: 0.06em;
        }


        .tool-event-badge.ok {

            color: #1f7a4d;

            background:
                rgba(85, 201, 138, 0.14);

            border:
                1px solid rgba(85, 201, 138, 0.32);
        }


        .tool-event-badge.fail {

            color: #a3300c;

            background:
                rgba(217, 90, 42, 0.12);

            border:
                1px solid rgba(217, 90, 42, 0.32);
        }


        .tool-event-badge.loc {

            color: var(--o-5);

            background:
                rgba(255, 154, 86, 0.12);

            border:
                1px solid rgba(255, 154, 86, 0.30);
        }


        .tool-event-label {

            color: var(--muted);

            font-size: 0.62rem;

            font-weight: 800;

            letter-spacing: 0.1em;

            text-transform: uppercase;

            margin: 0.55rem 0 0.25rem;
        }


        .tool-output {

            border:
                1px solid var(--line);

            border-radius: 10px;

            background:
                rgba(255, 252, 248, 0.95);

            padding: 0.6rem 0.7rem;

            font-family:
                "SFMono-Regular",
                Consolas,
                monospace;

            font-size: 0.72rem;

            line-height: 1.5;

            color: #4b2f1c;

            white-space: pre-wrap;

            word-break: break-word;

            max-height: 340px;

            overflow: auto;
        }


        /* ---------- Buttons ---------- */

        .stButton > button {

            width: 100%;

            border-radius: 999px !important;

            border:
                1px solid var(--line-2) !important;

            background:
                rgba(255, 255, 255, 0.78) !important;

            color:
                var(--o-4) !important;

            font-weight:
                700 !important;

            font-size:
                0.82rem !important;

            padding:
                0.55rem 1rem !important;

            box-shadow:
                var(--sh-sm) !important;

            backdrop-filter:
                blur(12px);

            -webkit-backdrop-filter:
                blur(12px);

            transition:
                all 0.22s cubic-bezier(.16,1,.3,1) !important;
        }


        .stButton > button:hover {

            background:

                linear-gradient(
                    135deg,
                    var(--o-2),
                    var(--o-3)
                ) !important;

            color:
                #fff !important;

            border-color:
                var(--o-3) !important;

            transform:
                translateY(-2px);

            box-shadow:
                var(--sh-md) !important;
        }


        /* ---------- Inputs ---------- */

        [data-testid="stChatInput"] textarea,
        [data-testid="stTextInput"] input {

            background:
                rgba(255, 253, 250, 0.96) !important;

            border:
                1px solid var(--line-2) !important;

            border-radius:
                14px !important;

            color:
                var(--ink) !important;

            box-shadow:
                var(--sh-sm) !important;
        }


        [data-testid="stChatInput"] textarea:focus,
        [data-testid="stTextInput"] input:focus {

            border-color:
                var(--o-2) !important;

            box-shadow:
                var(--sh-glow) !important;
        }


        [data-testid="stAlert"] {

            border-radius:
                14px !important;

            box-shadow:
                var(--sh-sm);
        }


        hr {
            border-color:
                var(--line) !important;
        }


        @media (max-width: 900px) {

            .block-container {
                padding:
                    1.3rem 1rem 3rem;
            }

            .hero {
                padding:
                    1.2rem 1.15rem 1.1rem;

                border-radius:
                    20px;
            }

            .hero-title {
                font-size:
                    1.65rem;
            }
        }


        @media (prefers-reduced-motion: reduce) {

            .rise {
                animation:
                    none;
            }

            .stButton > button {
                transition:
                    none !important;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ============================================================
# Persistent event loop
# ============================================================

def get_event_loop():
    """
    Return one persistent asyncio event loop for the
    current Streamlit session.

    MCP connections are created and used on this same
    event loop. This prevents:

        RuntimeError: Event loop is closed
    """

    loop = st.session_state.get("event_loop")

    if loop is None or loop.is_closed():

        loop = asyncio.new_event_loop()

        st.session_state.event_loop = loop

    return loop


# ============================================================
# Hero
# ============================================================

st.markdown(
    '<div class="hero rise">'

    '<div class="hero-title">'
    'MCP <span>Command Center</span>'
    '</div>'

    '<div class="hero-sub">'
    'Local AI agent powered by Qwen2.5:3b, '
    'LangGraph and multiple MCP servers.'
    '</div>'

    '<div class="pill-row">'

    '<span class="pill live">'
    '<span class="dot"></span>'
    'Ollama'
    '</span>'

    '<span class="pill live">'
    '<span class="dot"></span>'
    'MCP Client'
    '</span>'

    '<span class="pill">'
    '<span class="dot"></span>'
    'Qwen2.5:3b'
    '</span>'

    '<span class="pill">'
    '<span class="dot"></span>'
    'Local + Remote MCP'
    '</span>'

    '</div>'

    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# Session initialization
# ============================================================

def initialize():

    if st.session_state.get("initialized"):
        return

    with st.spinner("Connecting to MCP servers..."):

        try:

            # IMPORTANT:
            # MCP client creation and tool discovery happen
            # on our persistent event loop.

            loop = get_event_loop()

            result = loop.run_until_complete(
                connect_to_mcp_servers()
            )

            # Create agent after MCP tools are available.

            agent = MCPAgent()

            agent.initialize(
                result["tools_by_name"]
            )

            # Save everything in Streamlit session state.

            st.session_state.agent = agent

            st.session_state.mcp_client = (
                result["client"]
            )

            st.session_state.tools_by_server = (
                result["tools_by_server"]
            )

            st.session_state.tools_by_name = (
                result["tools_by_name"]
            )

            st.session_state.failed = (
                result["failed"]
            )

            st.session_state.skipped = (
                result["skipped"]
            )

            st.session_state.warnings = (
                result["warnings"]
            )

            st.session_state.history = [
                SystemMessage(
                    content=SYSTEM_PROMPT
                )
            ]

            st.session_state.transcript = []

            st.session_state.initialized = True

            st.session_state.initialization_error = None

        except Exception as error:

            st.session_state.initialization_error = (
                f"{type(error).__name__}: {error}"
            )

            st.session_state.initialized = True


initialize()


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="side-title">'
        'MCP Network'
        '</div>'

        '<div class="side-sub">'
        'Connected servers and tools'
        '</div>',

        unsafe_allow_html=True,
    )


    tools_by_server = (
        st.session_state.get(
            "tools_by_server",
            {},
        )
    )


    if not tools_by_server:

        st.warning(
            "No MCP tools loaded."
        )


    for server_name, tools in (
        tools_by_server.items()
    ):

        if server_name == "custom-remote":

            scope = "REMOTE"
            badge_class = "remote"

        else:

            scope = "LOCAL"
            badge_class = "local"


        transport = {

            "custom-local":
                "STDIO",

            "manim":
                "STDIO",

            "weather":
                "STDIO",

            "custom-remote":
                "STREAMABLE HTTP",

        }.get(
            server_name,
            "MCP",
        )


        rows = "".join(

            f'<div class="server-tool">'

            f'<span class="dot"></span>'

            f'<span>{tool.name}</span>'

            f'</div>'

            for tool in tools

        )


        st.markdown(

            f'<div class="server-card">'

            f'<div class="server-head">'

            f'<div class="server-name">'
            f'{server_name}'
            f'</div>'

            f'<span class="badge {badge_class}">'
            f'{scope}'
            f'</span>'

            f'</div>'

            f'<div class="transport">'
            f'{transport} · {len(tools)} tool(s)'
            f'</div>'

            f'{rows}'

            f'</div>',

            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # Failed servers
    # --------------------------------------------------------

    for server, error in (
        st.session_state.get(
            "failed",
            {},
        ).items()
    ):

        st.error(
            f"{server}\n\n{error}"
        )


    # --------------------------------------------------------
    # Skipped servers
    # --------------------------------------------------------

    for server, reason in (
        st.session_state.get(
            "skipped",
            {},
        ).items()
    ):

        st.warning(
            f"{server}\n\n{reason}"
        )


    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    for warning in (
        st.session_state.get(
            "warnings",
            [],
        )
    ):

        st.info(warning)


    st.divider()


    # ========================================================
    # Reload MCP Servers
    # ========================================================

    if st.button(
        "Reload MCP Servers",
        use_container_width=True,
    ):

        old_loop = (
            st.session_state.get(
                "event_loop"
            )
        )

        if old_loop is not None:

            try:

                # Give pending callbacks a chance to finish.

                if not old_loop.is_closed():

                    old_loop.run_until_complete(
                        asyncio.sleep(0)
                    )

                    old_loop.close()

            except Exception:
                pass


        # Clear Streamlit state.

        for key in list(
            st.session_state.keys()
        ):

            del st.session_state[key]


        st.rerun()


    # ========================================================
    # Clear Conversation
    # ========================================================

    if st.button(
        "Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.history = [
            SystemMessage(
                content=SYSTEM_PROMPT
            )
        ]

        st.session_state.transcript = []

        st.rerun()


# ============================================================
# Tool event rendering
# ============================================================

def render_tool_events(events):

    for event in events:

        ok = event["ok"]

        name = event["name"]

        icon = "✓" if ok else "✕"

        status_class = (
            "ok"
            if ok
            else "fail"
        )


        location = (

            "REMOTE"

            if name.startswith(
                "remote_"
            )

            else "LOCAL"

        )


        with st.expander(

            f"{icon} {name} · {location}",

            expanded=False,

        ):

            st.markdown(

                f'<div class="tool-event">'

                f'<div class="tool-event-head">'

                f'<span class="tool-event-name">'
                f'{name}'
                f'</span>'

                f'<span class="tool-event-badge '
                f'{status_class}">'

                f'{icon} '
                f'{"success" if ok else "error"}'

                f'</span>'

                f'<span class="tool-event-badge loc">'
                f'{location}'
                f'</span>'

                f'</div>'

                f'</div>',

                unsafe_allow_html=True,
            )


            st.markdown(

                '<div class="tool-event-label">'
                'Arguments'
                '</div>',

                unsafe_allow_html=True,
            )


            st.code(

                json.dumps(

                    event["args"],

                    indent=2,

                    ensure_ascii=False,

                    default=str,

                ),

                language="json",

            )


            st.markdown(

                '<div class="tool-event-label">'
                'Tool output'
                '</div>',

                unsafe_allow_html=True,
            )


            st.code(

                event.get(
                    "result",
                    "",
                ),

                language="text",

            )


# ============================================================
# Existing conversation
# ============================================================

for item in (
    st.session_state.get(
        "transcript",
        [],
    )
):

    with st.chat_message(
        item["role"]
    ):

        render_tool_events(
            item.get(
                "tools",
                [],
            )
        )


        if item.get("error"):

            st.error(
                item["content"]
            )

        else:

            st.markdown(
                item["content"]
            )


# ============================================================
# Chat input
# ============================================================

user_text = st.chat_input(
    "Ask your MCP agent anything..."
)


if user_text:

    # --------------------------------------------------------
    # User message
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(
            user_text
        )


    # --------------------------------------------------------
    # Add user message to agent history
    # --------------------------------------------------------

    history = (
        st.session_state.history
    )

    history.append(
        HumanMessage(
            content=user_text
        )
    )


    events = []

    answer = ""

    error = False


    # --------------------------------------------------------
    # Agent response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        try:

            with st.spinner(
                "Agent is thinking..."
            ):

                # IMPORTANT:
                # Use the SAME event loop that created
                # the MCP client.

                loop = get_event_loop()

                answer = (
                    loop.run_until_complete(
                        st.session_state.agent.run_turn(
                            history,
                            events,
                        )
                    )
                )


        except Exception as exc:

            error = True

            answer = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )


        # ----------------------------------------------------
        # Show MCP tool events
        # ----------------------------------------------------

        render_tool_events(
            events
        )


        # ----------------------------------------------------
        # Show answer
        # ----------------------------------------------------

        if error:

            st.error(
                answer
            )

        else:

            st.markdown(
                answer
                or
                "_No response returned._"
            )


    # --------------------------------------------------------
    # Save transcript
    # --------------------------------------------------------

    st.session_state.transcript.append(

        {
            "role": "user",

            "content": user_text,
        }

    )


    st.session_state.transcript.append(

        {

            "role": "assistant",

            "content": answer,

            "tools": events,

            "error": error,

        }

    )
