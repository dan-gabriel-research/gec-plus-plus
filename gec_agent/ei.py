"""
EI — Embodied Integration layer

Enforces a tight action-perception loop: one tool call at a time,
mandatory integration before the next action.

Vanilla agents batch tool calls or pipeline them without grounding.
EI enforcement means every observation causally updates the agent's
state before the next decision — genuine grounding, not deferred lookup.
"""

EI_ENFORCEMENT = """
GROUNDED ACTION RULES (enforce strictly):
1. Call only ONE tool per turn.
2. After receiving a tool result, write an integration note:
   "Observed: [what the tool returned]. This [confirms/updates/contradicts] [prior belief].
    Next action: [what to do based on this observation]."
3. Only after that integration may you call another tool.
4. Never assume a result — always observe first, then act.
"""


class EILoop:
    def __init__(self, client, model: str, tools: list):
        self.client = client
        self.model = model
        self.tools = tools
        self.observation_log = []

    def run(self, messages: list, system: str,
            max_iterations: int = 12) -> tuple:
        """
        Run the serialized action-perception loop.
        Returns (final_text, observation_log).
        """
        from .tools import execute_tool

        enhanced_system = system + "\n\n" + EI_ENFORCEMENT
        current_messages = [dict(m) for m in messages]
        self.observation_log = []

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=enhanced_system,
                messages=current_messages,
                tools=self.tools if self.tools else None
            )

            if response.stop_reason == "end_turn":
                text = "".join(
                    b.text for b in response.content if hasattr(b, "text")
                )
                return text, self.observation_log

            if response.stop_reason == "tool_use":
                # Add assistant turn
                current_messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Find the first (and only allowed) tool call
                tool_block = next(
                    (b for b in response.content if b.type == "tool_use"),
                    None
                )
                if not tool_block:
                    break

                result = execute_tool(tool_block.name, tool_block.input)

                self.observation_log.append({
                    "tool": tool_block.name,
                    "input": tool_block.input,
                    "result": result
                })

                current_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": str(result)
                    }]
                })
            else:
                # Unexpected stop — extract any text and return
                text = "".join(
                    b.text for b in response.content if hasattr(b, "text")
                )
                return text, self.observation_log

        return "Reached iteration limit.", self.observation_log
