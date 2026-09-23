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

MANIM RULES:

12. When generating Manim code, always use:

    from manim import *

13. Every animation must define a Scene class.

14. Every Scene class must contain:

    def construct(self):

15. The code must be directly executable by Manim.

16. NEVER return escaped newline characters such as:

    \\n

    in the actual Manim source code.

17. The Manim source must contain real Python line breaks.

18. Keep the generated code self-contained.

19. Use simple, reliable Manim APIs.

20. For color changes, prefer:

    self.play(
        circle.animate.set_color(BLUE)
    )

21. For flipping an object, prefer:

    self.play(
        Flip(circle)
    )

    or another standard Manim animation that is known to
    work with the current Manim version.

22. For multiple requested effects, perform them as
    separate animation steps when appropriate.

23. Always include a short self.wait() at the end.

24. Example:

    from manim import *

    class CircleAnimation(Scene):

        def construct(self):

            circle = Circle()

            circle.set_fill(
                RED,
                opacity=0.5
            )

            self.play(
                Create(circle)
            )

            self.play(
                circle.animate.set_color(BLUE)
            )

            self.play(
                Flip(circle)
            )

            self.wait(2)
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

    async def run_turn(self, history, events):

        for _ in range(MAX_TOOL_ROUNDS):

            response = await self.llm_with_tools.ainvoke(history)

            tool_calls = getattr(
                response,
                "tool_calls",
                None,
            ) or []

            # ----------------------------------------------------
            # No tool call = normal final answer
            # ----------------------------------------------------

            if not tool_calls:

                text = response.content or ""

                history.append(
                    AIMessage(
                        content=text
                    )
                )

                return text

            # ----------------------------------------------------
            # Store AI tool-call message
            # ----------------------------------------------------

            history.append(response)

            # ----------------------------------------------------
            # Execute tools
            # ----------------------------------------------------

            for index, call in enumerate(tool_calls):

                tool_name = call["name"]

                arguments = call.get("args") or {}

                if isinstance(arguments, str):

                    try:
                        arguments = json.loads(arguments)

                    except json.JSONDecodeError:
                        arguments = {}

                call_id = (
                    call.get("id")
                    or f"tool_call_{index}"
                )

                tool = self.tools_by_name.get(
                    tool_name
                )

                if tool is None:

                    success = False

                    output = (
                        f"Unknown tool: {tool_name}"
                    )

                else:

                    try:

                        output = await asyncio.wait_for(
                            tool.ainvoke(arguments),
                            timeout=TOOL_TIMEOUT,
                        )

                        output = result_to_text(output)

                        # Some MCP tools return execution failures as
                        # normal text instead of raising an exception.
                        #
                        # Detect those failures explicitly.

                        failure_markers = (
                            "Manim execution failed",
                            "Error during Manim execution",
                            "Execution failed",
                            "Traceback (most recent call last)",
                        )

                        if any(
                            marker in output
                            for marker in failure_markers
                        ):

                            success = False

                        else:

                            success = True

                    except Exception as error:

                        success = False

                        output = (
                            f"Error calling "
                            f"{tool_name}: "
                            f"{type(error).__name__}: "
                            f"{error}"
                        )

                # ------------------------------------------------
                # Save event
                # ------------------------------------------------

                events.append(
                    {
                        "name": tool_name,
                        "args": arguments,
                        "result": output,
                        "ok": success,
                    }
                )

                # ------------------------------------------------
                # Give result back to LLM
                # ------------------------------------------------

                history.append(
                    ToolMessage(
                        tool_call_id=call_id,
                        name=tool_name,
                        content=output,
                    )
                )

            # ----------------------------------------------------
            # Special handling for Manim
            # ----------------------------------------------------

            manim_events = [
                event
                for event in events
                if event["name"] == "execute_manim_code"
            ]

            if manim_events:

                latest = manim_events[-1]

                if latest["ok"]:

                    final_text = (
                        "The Manim animation was generated "
                        "successfully."
                    )

                    history.append(
                        AIMessage(
                            content=final_text
                        )
                    )

                    return final_text

                else:

                    final_text = (
                        "The Manim animation could not be generated. "
                        "I received an execution error from the Manim server."
                    )

                    history.append(
                        AIMessage(
                            content=final_text
                        )
                    )

                    return final_text

        # --------------------------------------------------------
        # Safety fallback
        # --------------------------------------------------------

        final_response = await self.llm.ainvoke(
            history
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