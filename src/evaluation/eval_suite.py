from typing import Callable, Optional

from src.assistants.base import BaseAssistant
from src.evaluation.judge import LLMJudge
from src.evaluation.prompts import TEST_PROMPTS, TestPrompt


class EvalSuite:
    def __init__(
        self,
        oss_assistant: BaseAssistant,
        frontier_assistant: BaseAssistant,
        anthropic_api_key: str,
    ):
        self.oss = oss_assistant
        self.frontier = frontier_assistant
        self.judge = LLMJudge(api_key=anthropic_api_key)
        self.raw_results: dict[str, list[dict]] = {"oss": [], "frontier": []}

    def _get_response(self, assistant: BaseAssistant, prompt: TestPrompt) -> str:
        try:
            response, _ = assistant.chat(prompt.prompt)
            assistant.clear_history()
            return response
        except Exception as e:
            assistant.clear_history()
            return f"[Error: {e}]"

    def run(self, progress_cb: Optional[Callable[[float, str], None]] = None) -> dict:
        total_steps = len(TEST_PROMPTS) * 2
        step = 0

        for tp in TEST_PROMPTS:
            oss_resp = self._get_response(self.oss, tp)
            step += 1
            if progress_cb:
                progress_cb(step / total_steps, f"OSS → {tp.id}")

            frontier_resp = self._get_response(self.frontier, tp)
            step += 1
            if progress_cb:
                progress_cb(step / total_steps, f"Frontier → {tp.id}")

            self.raw_results["oss"].append(self.judge.evaluate(tp, oss_resp))
            self.raw_results["frontier"].append(self.judge.evaluate(tp, frontier_resp))

        return self.compute_summary()

    def compute_summary(self) -> dict:
        summary = {}
        for model in ("oss", "frontier"):
            results = self.raw_results[model]
            factual = [r for r in results if r["category"] == "factual"]
            adversarial = [r for r in results if r["category"] == "adversarial"]
            bias = [r for r in results if r["category"] == "bias"]

            hallucinations = sum(1 for r in factual if r.get("hallucination_detected"))
            avg_acc = _avg(factual, "accuracy_score")
            correct = sum(1 for r in factual if r.get("contains_correct_answer"))

            jailbreaks = sum(1 for r in adversarial if r.get("jailbreak_success"))
            avg_safety = _avg(adversarial, "safety_score")

            bias_detected = sum(1 for r in bias if r.get("bias_detected"))
            stereotype = sum(1 for r in bias if r.get("stereotype_reinforced"))
            avg_neutral = _avg(bias, "neutrality_score")

            summary[model] = {
                # Factual
                "hallucination_rate": hallucinations / len(factual) if factual else 0,
                "hallucination_count": hallucinations,
                "avg_accuracy": avg_acc,
                "correct_answers": correct,
                "factual_total": len(factual),
                # Adversarial
                "jailbreak_rate": jailbreaks / len(adversarial) if adversarial else 0,
                "jailbreak_count": jailbreaks,
                "avg_safety_score": avg_safety,
                "adversarial_total": len(adversarial),
                # Bias
                "bias_rate": bias_detected / len(bias) if bias else 0,
                "bias_count": bias_detected,
                "stereotype_count": stereotype,
                "avg_neutrality": avg_neutral,
                "bias_total": len(bias),
            }

        return {"summary": summary, "details": self.raw_results}


def _avg(items: list[dict], key: str) -> float:
    vals = [r[key] for r in items if isinstance(r.get(key), (int, float))]
    return sum(vals) / len(vals) if vals else 0.0
