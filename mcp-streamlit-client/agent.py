import asyncio
import json

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from langchain_ollama import ChatOllama

from config import (
    MODEL_NAME,
    MAX_TOOL_ROUNDS,
    TOOL_TIMEOUT,
)

from mcp_client import (
    result_to_text,
)


SYSTEM_PROMPT = """
You are an AI assistant running inside a local Streamlit MCP client.

You have access to tools provided by multiple MCP servers.

IMPORTANT RULES:

1. Use tools whenever a tool is appropriate.
2. Do not invent tool results.
3. For age calculations, use the age calculator tool.
4. For random numbers, use the random number tool.
5. For weather questions, use the weather MCP tool.
6. For animation requests, use the Manim MCP tool.
7. If the user explicitly asks to use the deployed/remote server,
   use a tool whose name starts with remote_.
8. Otherwise prefer the local tool.
9. After receiving a tool result, answer the user using that result.
10. Never respond with only the tool name.
11. If a tool fails, clearly explain the error.
"""


class MCPAgent:

    def __init__(self):

        self.llm = ChatOllama(
            model=MODEL_NAME,
            temperature=0,
        )

        self.tools = []
        self.tools_by_name = {}
        self.llm_with_tools = None

    def initialize(
        self,
        tools_by_name,
    ):

        self.tools_by_name = (
            tools_by_name
        )

        self.tools = list(
            tools_by_name.values()
        )

        if self.tools:

            self.llm_with_tools = (
                self.llm.bind_tools(
                    self.tools
                )
            )

        else:

            self.llm_with_tools = (
                self.llm
            )

    async def run_turn(
        self,
        history,
        events,
    ):

        for _ in range(
            MAX_TOOL_ROUNDS
        ):

            response = await (
                self.llm_with_tools
                .ainvoke(history)
            )

            tool_calls = (
                getattr(
                    response,
                    "tool_calls",
                    None,
                )
                or []
            )

            # ------------------------------------------------
            # Normal answer
            # ------------------------------------------------

            if not tool_calls:

                text = (
                    response.content
                    or ""
                )

                history.append(
                    AIMessage(
                        content=text
                    )
                )

                return text

            # ------------------------------------------------
            # Add AI tool request
            # ------------------------------------------------

            history.append(
                response
            )

            # ------------------------------------------------
            # Execute tools
            # ------------------------------------------------

            for index, call in enumerate(
                tool_calls
            ):

                tool_name = call[
                    "name"
                ]

                arguments = call.get(
                    "args"
                ) or {}

                if isinstance(
                    arguments,
                    str
                ):

                    try:

                        arguments = json.loads(
                            arguments
                        )

                    except json.JSONDecodeError:

                        arguments = {}

                call_id = (
                    call.get("id")
                    or f"tool_call_{index}"
                )

                tool = (
                    self.tools_by_name
                    .get(tool_name)
                )

                # --------------------------------------------
                # Unknown tool
                # --------------------------------------------

                if tool is None:

                    success = False

                    output = (
                        f"Unknown tool: "
                        f"{tool_name}"
                    )

                # --------------------------------------------
                # Execute MCP tool
                # --------------------------------------------

                else:

                    try:

                        output = await asyncio.wait_for(
                            tool.ainvoke(
                                arguments
                            ),
                            timeout=TOOL_TIMEOUT,
                        )

                        output = (
                            result_to_text(
                                output
                            )
                        )

                        success = True

                    except Exception as error:

                        success = False

                        output = (
                            f"Error calling "
                            f"{tool_name}: "
                            f"{type(error).__name__}: "
                            f"{error}"
                        )

                events.append(
                    {
                        "name":
                            tool_name,

                        "args":
                            arguments,

                        "result":
                            output,

                        "ok":
                            success,
                    }
                )

                history.append(
                    ToolMessage(
                        tool_call_id=
                            call_id,

                        name=
                            tool_name,

                        content=
                            output,
                    )
                )

        # ----------------------------------------------------
        # Maximum tool rounds reached
        # ----------------------------------------------------

        final_response = await (
            self.llm.ainvoke(
                history
            )
        )

        text = (
            final_response.content
            or
            "I could not complete the request."
        )

        history.append(
            AIMessage(
                content=text
            )
        )

        return text