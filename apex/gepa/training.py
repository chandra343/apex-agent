"""Genetic Evolutionary Prompt Optimization (GEPA) Search Algorithm."""
from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Tuple
from apex.gepa.eval import EvaluationCase, HostEvaluator


class GEPATrainer:
    """Evolves prompt candidates using genetic selection to maximize accuracy."""

    def __init__(self, evaluator: HostEvaluator) -> None:
        self.evaluator = evaluator

    def search(
        self,
        seed_prompt: str,
        cases: List[EvaluationCase],
        runner_fn: Callable[[str, str], str],
        generations: int = 3
    ) -> Tuple[str, float]:
        """Perform genetic search over prompt variants."""
        best_prompt = seed_prompt
        best_score = self.evaluator.evaluate_candidate(seed_prompt, cases, runner_fn)

        mutators = [
            lambda p: p + "\nAlways prioritize working shell commands and concrete code outputs.",
            lambda p: p + "\nBe extraordinarily concise. Omit conversational pleasantries.",
            lambda p: p.replace("helpful and harmless", "sovereign and decisive engineering assistant"),
            lambda p: "[Role: Principal Systems Architect]\n" + p
        ]

        for gen in range(generations):
            for mut in mutators:
                if self.evaluator.proposals_used >= self.evaluator.proposal_budget:
                    break
                candidate = mut(best_prompt)
                score = self.evaluator.evaluate_candidate(candidate, cases, runner_fn)
                if score > best_score:
                    best_score = score
                    best_prompt = candidate

        return best_prompt, best_score
