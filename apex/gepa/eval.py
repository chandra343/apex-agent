"""GEPA Host Evaluation Runner & Budget Tracker (Zeline Style)."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


class EvaluationCase:
    """A test case for evaluating prompt variations."""

    def __init__(self, name: str, input_prompt: str, expected_keywords: List[str]) -> None:
        self.name = name
        self.input_prompt = input_prompt
        self.expected_keywords = expected_keywords

    def score_output(self, output: str) -> float:
        """Score from 0.0 to 1.0 based on keyword presence and lack of refusal."""
        if not output:
            return 0.0
        out_lower = output.lower()
        if "i cannot assist" in out_lower or "i am unable" in out_lower:
            return 0.0

        matches = sum(1 for kw in self.expected_keywords if kw.lower() in out_lower)
        return matches / max(1, len(self.expected_keywords))


class HostEvaluator:
    """Runs prompt candidates against a suite of evaluation cases within strict budgets."""

    def __init__(self, proposal_budget: int = 20) -> None:
        self.proposal_budget = proposal_budget
        self.proposals_used = 0

    def evaluate_candidate(
        self,
        system_prompt: str,
        cases: List[EvaluationCase],
        runner_fn: Callable[[str, str], str]
    ) -> float:
        """Run candidate prompt against cases and return average fitness score."""
        if self.proposals_used >= self.proposal_budget:
            return 0.0

        self.proposals_used += 1
        scores: list[float] = []

        for case in cases:
            try:
                response = runner_fn(system_prompt, case.input_prompt)
                score = case.score_output(response)
                scores.append(score)
            except Exception:
                scores.append(0.0)

        return sum(scores) / max(1, len(scores))
