"""
AVI — Affective Valence Index layer (approximation)

True AVI requires homeostatic stakes baked into training.
This layer approximates it by treating consistency as a stake:
the agent has "something to lose" when it contradicts itself.

Every response is checked against:
  - Prior statements in the current session
  - Consistency constraints accumulated across sessions (from TCI)

High-severity contradictions trigger automatic revision.
"""

import json
import re

AVI_CHECK_SYSTEM = """You are a consistency auditor.

Check whether the RESPONSE contradicts:
1. Prior conversation turns provided
2. Active consistency constraints listed

Output ONLY JSON — no markdown:
{
  "is_consistent": <bool>,
  "contradictions": [
    {"prior": "<prior claim>", "new": "<conflicting claim>", "severity": "low|medium|high"}
  ],
  "consistency_score": <float 0-1>,
  "overconfident_claims": ["<claim>"]
}

Only flag real contradictions — different phrasing of the same idea is not a contradiction.
Severity "high" = direct factual reversal or broken commitment."""

AVI_REVISE_SYSTEM = """Revise the response to resolve contradictions with prior statements.
Preserve the helpful content. Fix only the inconsistencies listed.
Return the revised response as plain text, no explanation."""


class AVIChecker:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def check(self, response: str, tci_state: dict,
              conversation_history: list) -> tuple:
        """
        Returns (response, consistency_report).
        Response may be revised if high-severity contradictions found.
        """
        constraints = tci_state.get("consistency_constraints", [])
        # Need something to check against
        if not constraints and len(conversation_history) < 2:
            return response, {"is_consistent": True, "consistency_score": 1.0,
                              "contradictions": []}

        history_text = "\n".join(
            f"{m['role']}: {str(m['content'])[:300]}"
            for m in conversation_history[-6:]
        )
        constraints_text = (
            "\n".join(f"- {c}" for c in constraints[-15:])
            if constraints else "None yet."
        )

        check_response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=AVI_CHECK_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Conversation so far:\n{history_text}\n\n"
                    f"Active constraints:\n{constraints_text}\n\n"
                    f"Response to audit:\n{response}"
                )
            }]
        )

        report = self._parse(check_response.content[0].text)

        # Revise if high-severity contradictions detected
        high = [c for c in report.get("contradictions", [])
                if c.get("severity") == "high"]
        if high and not report.get("is_consistent", True):
            response = self._revise(response, high, conversation_history)

        return response, report

    def _revise(self, response: str, contradictions: list,
                history: list) -> str:
        conflict_text = "\n".join(
            f"- New claim '{c['new']}' contradicts prior '{c['prior']}'"
            for c in contradictions
        )
        revision = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=AVI_REVISE_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Original response:\n{response}\n\n"
                    f"Contradictions to resolve:\n{conflict_text}"
                )
            }]
        )
        return revision.content[0].text

    @staticmethod
    def _parse(text: str) -> dict:
        fallback = {"is_consistent": True, "contradictions": [],
                    "consistency_score": 1.0, "overconfident_claims": []}
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return fallback
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return fallback
