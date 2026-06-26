"""
CSMI — Causal Self-Modeling Integration layer

Before generating any response, the agent runs a self-assessment:
what is my confidence, where might I be wrong, what consistency risks exist?
This assessment causally shapes the actual response — not decorative reflection,
but information that modifies generation before it happens.
"""

import json
import re

CSMI_SYSTEM = """You are performing a pre-response self-assessment.

Analyze the incoming message against your state and history.
Output ONLY a JSON object — no markdown, no explanation:

{
  "confidence": <float 0-1>,
  "uncertainty_sources": [<string>, ...],
  "verification_needed": [<string>, ...],
  "consistency_risks": [<string>, ...],
  "approach": "<one sentence: how will you handle this carefully?>"
}

Be precise and honest. Overconfidence here propagates into a worse response."""


class CSMILayer:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def assess(self, user_message: str, tci_state: dict,
               conversation_history: list) -> dict:
        context = self._build_context(tci_state, conversation_history)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=CSMI_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"{context}\n\nIncoming message: {user_message}"
            }]
        )

        text = response.content[0].text.strip()
        return self._parse(text)

    def _build_context(self, state: dict, history: list) -> str:
        parts = []

        if state.get("session_count", 0) > 0:
            parts.append(f"Prior sessions: {state['session_count']}")

        constraints = state.get("consistency_constraints", [])
        if constraints:
            listed = "\n".join(f"  - {c}" for c in constraints[-8:])
            parts.append(f"Active commitments:\n{listed}")

        corrections = state.get("user_corrections", [])
        if corrections:
            listed = "\n".join(f"  - {c}" for c in corrections[-4:])
            parts.append(f"Prior user corrections:\n{listed}")

        if history:
            recent = history[-4:]
            lines = "\n".join(
                f"  {m['role']}: {str(m['content'])[:150]}" for m in recent
            )
            parts.append(f"Recent conversation:\n{lines}")

        return "\n\n".join(parts) if parts else "No prior context."

    @staticmethod
    def _parse(text: str) -> dict:
        fallback = {
            "confidence": 0.7,
            "uncertainty_sources": [],
            "verification_needed": [],
            "consistency_risks": [],
            "approach": "Respond carefully."
        }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return fallback
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return fallback
