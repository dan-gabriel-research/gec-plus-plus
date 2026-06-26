"""
GECAgent — orchestrates TCI, CSMI, EI, and AVI layers.

Every call to .chat() runs through all four layers in sequence:
  1. Load TCI state (who am I, what do I know, what have I committed to?)
  2. CSMI pre-check (what's my confidence, where might I fail?)
  3. EI loop (act → observe → integrate → act again)
  4. AVI check (does this contradict what I've said before?)
  5. Update TCI state (what changed? write it back.)
"""

import json
import re
import uuid
from datetime import datetime

import anthropic

from .tci import TCIStore
from .csmi import CSMILayer
from .ei import EILoop
from .avi import AVIChecker
from .tools import get_tool_definitions

_STATE_UPDATE_SYSTEM = """Update the agent's persistent state JSON based on this exchange.

Rules:
- Add new consistency_constraints for any explicit commitments made
- Record user_corrections if the user corrected the agent
- Update ongoing_tasks (add, update status, or close tasks)
- Update user_profile with newly observed preferences or expertise
- Increment knowledge_built with new factual information established
- Keep lists bounded (max 30 items each; drop oldest if over)

Return ONLY the complete updated JSON. No markdown, no explanation."""


class GECAgent:
    """
    Minimum viable GEC++ agent.

    Instantiate with a unique agent_id — state persists under that ID.
    Call .chat(message) to interact.
    Call .end_session() to flush state before the process exits.
    """

    def __init__(self, agent_id: str = "default",
                 model: str = "claude-sonnet-4-6",
                 db_path: str = "gec_state.db"):
        self.agent_id = agent_id
        self.model = model
        self.session_id = str(uuid.uuid4())

        self.client = anthropic.Anthropic()
        self.tci = TCIStore(agent_id, db_path)
        self.csmi = CSMILayer(self.client, model)
        self.avi = AVIChecker(self.client, model)

        self.conversation_history: list = []
        self.state = self.tci.load()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def chat(self, user_message: str, verbose: bool = False) -> str:
        """Process a message through all four GEC++ layers."""

        # 1. CSMI — self-assess before generating
        if verbose:
            print("[CSMI] Self-assessing...")
        assessment = self.csmi.assess(
            user_message, self.state, self.conversation_history
        )
        if verbose:
            conf = assessment.get("confidence", "?")
            risks = assessment.get("uncertainty_sources", [])
            print(f"       confidence={conf:.0%}  risks={risks[:2]}")

        # 2. Build system prompt from TCI state + CSMI output
        system = self._build_system(assessment)

        # 3. EI — serialized grounded tool loop
        if verbose:
            print("[EI]   Running grounded action loop...")
        messages = self.conversation_history + [
            {"role": "user", "content": user_message}
        ]
        ei = EILoop(self.client, self.model, get_tool_definitions())
        response, observations = ei.run(messages, system)
        if verbose and observations:
            print(f"       {len(observations)} tool observation(s)")

        # 4. AVI — consistency check, auto-revise if needed
        if verbose:
            print("[AVI]  Checking consistency...")
        response, report = self.avi.check(
            response, self.state, self.conversation_history
        )
        if verbose:
            score = report.get("consistency_score", 1.0)
            fixed = len([c for c in report.get("contradictions", [])
                         if c.get("severity") == "high"])
            print(f"       score={score:.2f}  high-severity fixed={fixed}")

        # 5. Update conversation history
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": response}
        )

        # 6. Log and update TCI state
        self.tci.log_exchange(self.session_id, user_message, response)
        self._update_state(user_message, response)

        return response

    def end_session(self):
        """Flush state to disk at end of session."""
        self.state["session_count"] = self.state.get("session_count", 0) + 1
        self.state["last_updated"] = datetime.now().isoformat()
        self.tci.save(self.state)

    @property
    def session_summary(self) -> dict:
        """Quick snapshot for inspection."""
        return {
            "agent_id": self.agent_id,
            "session_count": self.state.get("session_count", 0),
            "constraints": len(self.state.get("consistency_constraints", [])),
            "corrections": len(self.state.get("user_corrections", [])),
            "ongoing_tasks": len(self.state.get("ongoing_tasks", [])),
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _build_system(self, assessment: dict) -> str:
        s = self.state
        lines = ["You are a GEC++-enhanced assistant.\n"]

        # TCI context
        if s.get("session_count", 0) > 0:
            profile = s.get("user_profile", {})
            name = profile.get("name") or "the user"
            style = profile.get("communication_style", "unknown")
            prefs = ", ".join(profile.get("preferences", [])[:4]) or "none noted"

            lines.append(f"## Persistent Context ({s['session_count']} prior sessions)")
            lines.append(f"User: {name} | Style: {style} | Preferences: {prefs}")

            constraints = s.get("consistency_constraints", [])
            if constraints:
                lines.append("\nCommitments to maintain:")
                lines.extend(f"  - {c}" for c in constraints[-10:])

            corrections = s.get("user_corrections", [])
            if corrections:
                lines.append("\nPrior corrections — do not repeat these mistakes:")
                lines.extend(f"  - {c}" for c in corrections[-5:])

            tasks = s.get("ongoing_tasks", [])
            if tasks:
                lines.append("\nOngoing tasks:")
                lines.extend(
                    f"  - {t.get('name','?')}: {t.get('status','?')}"
                    for t in tasks[:4]
                )

        # CSMI context
        conf = assessment.get("confidence", 0.7)
        uncertainties = assessment.get("uncertainty_sources", [])
        approach = assessment.get("approach", "")
        lines.append(f"\n## Self-Assessment")
        lines.append(f"Confidence: {conf:.0%}")
        if uncertainties:
            lines.append(f"Watch for: {'; '.join(uncertainties[:3])}")
        if approach:
            lines.append(f"Approach: {approach}")

        lines.append(
            "\nMaintain every commitment listed above. "
            "Acknowledge uncertainty where flagged. "
            "One tool call at a time."
        )

        return "\n".join(lines)

    def _update_state(self, user_message: str, response: str):
        """Ask Claude to update the TCI state based on this exchange."""
        try:
            update = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=_STATE_UPDATE_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Current state:\n{json.dumps(self.state, indent=2)}\n\n"
                        f"User: {user_message}\n\n"
                        f"Agent: {response[:1200]}\n\n"
                        f"Return updated state JSON."
                    )
                }]
            )
            text = update.content[0].text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                new_state = json.loads(match.group())
                self.state = new_state
                self.tci.save(self.state)
        except Exception:
            # Never crash on state update failure — keep current state
            pass
