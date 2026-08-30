"""
dslighting/workflows/search/dsflow_workflow.py

DSFlow meta-optimizer (two-stage selection):

Stage 1 (coarse): Stop each candidate after its first LLM call and score the plan cheaply.
Stage 2 (fine): Run the full workflow only for top-k candidates and grade via benchmark.

Implementation details (operators, grading, operator library, auto-sync, telemetry, etc.)
live under `dslighting.tools.dsflow.*`. This file intentionally keeps only the algorithmic
orchestration visible for maintainability and to preserve the public import path:
`from dslighting.workflows.search.dsflow_workflow import DSFlowWorkflow`.
"""

import hashlib
import logging
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from dslighting.tools.dsflow.core.models import EvalCandidate, TaskContext
from dslighting.tools.dsflow.core.optimizer import DSFlowWorkflowBase
from dslighting.workflows.templates.dsflow import get_initial_dsflow_workflow_code

logger = logging.getLogger(__name__)


class DSFlowWorkflow(DSFlowWorkflowBase):
    """
    Public DSFlow entrypoint used by `WorkflowFactory`.

    This subclass keeps `optimize()` readable (core two-stage algorithm),
    while delegating all heavy lifting to the implementation base class.
    """

    async def optimize(self) -> str:  # noqa: D401
        meta_started_at = datetime.now(timezone.utc)
        meta_perf_start = time.perf_counter()
        usage_before = self.llm_service.get_usage_summary()

        # Preflight benchmark contract.
        if (
            not self.benchmark
            or not hasattr(self.benchmark, "set_mode")
            or not hasattr(self.benchmark, "grade")
        ):
            raise NotImplementedError(
                "DSFlowWorkflow requires a benchmark with `set_mode` and `grade`."
            )
        if not self.benchmark.problems:
            raise ValueError(
                f"No problems found for benchmark '{self.benchmark.name}'. DSFlow cannot proceed."
            )

        competition_ids = [
            p.get("competition_id") for p in self.benchmark.problems if p.get("competition_id")
        ]
        if not competition_ids:
            raise ValueError("Benchmark problems must contain at least one 'competition_id'.")

        # Prepare tasks (may sample multiple competitions for multi-task optimization).
        logger.info("DSFlow starting meta-optimization (two-stage evaluation)...")
        self.benchmark.set_mode("validation")
        default_task_count = 1 if len(competition_ids) <= 1 else min(3, len(competition_ids))
        task_sample_size = int(getattr(self.dsflow_config, "task_sample_size", default_task_count))
        task_sample_size = max(1, min(task_sample_size, len(competition_ids)))
        task_sample_strategy = (
            str(getattr(self.dsflow_config, "task_sample_strategy", "first")).strip().lower()
        )

        if task_sample_strategy == "random":
            selected_ids = random.sample(competition_ids, k=task_sample_size)
        else:
            selected_ids = competition_ids[:task_sample_size]
        tasks = self._prepare_tasks(selected_ids)
        if not tasks:
            raise ValueError("Failed to prepare any task contexts for DSFlow optimization.")

        # Make operator library operators available before mutations.
        self._register_library_operators(tasks)

        # Provide multi-task hint to encourage generalizable improvements.
        task_hint = "\n\n".join(
            f"## {t.competition_id}\n{t.raw_description[:600].strip()}" for t in tasks
        )

        # Core two-stage loop:
        # - Default: coarse-only during search; fine only once at the end.
        # - Optional (slower): fine-evaluate top-k each generation.
        best_code = ""
        try:
            if bool(getattr(self.dsflow_config, "fine_evaluate_each_generation", False)):
                best_code = await self._optimize_fine_each_generation(
                    tasks=tasks, task_hint=task_hint
                )
                return best_code

            best_code = await self._optimize_final_fine_eval(tasks=tasks, task_hint=task_hint)
            return best_code
        finally:
            meta_ended_at = datetime.now(timezone.utc)
            duration_seconds = round(time.perf_counter() - meta_perf_start, 4)
            usage_after = self.llm_service.get_usage_summary()
            meta_usage_delta = {
                "prompt_tokens": usage_after.get("prompt_tokens", 0)
                - usage_before.get("prompt_tokens", 0),
                "completion_tokens": usage_after.get("completion_tokens", 0)
                - usage_before.get("completion_tokens", 0),
                "total_tokens": usage_after.get("total_tokens", 0)
                - usage_before.get("total_tokens", 0),
                "total_cost": round(
                    float(usage_after.get("total_cost", 0.0) - usage_before.get("total_cost", 0.0)),
                    12,
                ),
                "call_count": usage_after.get("call_count", 0) - usage_before.get("call_count", 0),
            }
            self._record_score(
                round_num=-1,
                fitness=0.0,
                code=best_code or "",
                score_type="meta_summary",
                extra={
                    "started_at": meta_started_at.isoformat().replace("+00:00", "Z"),
                    "ended_at": meta_ended_at.isoformat().replace("+00:00", "Z"),
                    "duration_seconds": duration_seconds,
                    "usage_delta": meta_usage_delta,
                    "usage_total": usage_after,
                },
            )

    async def _optimize_fine_each_generation(self, tasks: list[TaskContext], task_hint: str) -> str:
        """
        Legacy (slower but more feedback): do coarse screening then fine-evaluate top-k each generation.
        """
        best_code = get_initial_dsflow_workflow_code()
        best_round = 0

        candidates_by_round: dict[int, EvalCandidate] = {
            best_round: EvalCandidate(
                code=best_code,
                modification="Initial (baseline)",
                round_num=best_round,
            )
        }
        recorded_coarse_rounds: set[int] = set()
        recorded_fitness_rounds: set[int] = set()

        if self._progress_enabled():
            logger.info("DSFlow progress: initial candidate fine evaluation (baseline) ...")
        best_fitness = await self._fine_evaluate(best_code, tasks)

        base = candidates_by_round[best_round]
        base.fitness = best_fitness
        base.fine_evaluated = True
        self._record_score(
            round_num=best_round,
            fitness=best_fitness,
            code=best_code,
            score_type="fitness",
            extra={"modification": base.modification},
        )
        recorded_fitness_rounds.add(best_round)
        logger.info("Initial workflow fitness: %.4f", best_fitness)

        round_counter = best_round

        for gen in range(1, self.max_generations + 1):
            logger.info("--- DSFlow Generation %d/%d ---", gen, self.max_generations)

            parent = candidates_by_round.get(best_round) or EvalCandidate(
                code=best_code,
                modification="Parent (carry-over)",
                round_num=best_round,
            )
            population: list[EvalCandidate] = [
                EvalCandidate(
                    code=best_code,
                    modification=parent.modification,
                    round_num=best_round,
                    coarse_score=parent.coarse_score,
                    fitness=best_fitness,
                    fine_evaluated=True,
                )
            ]

            # Generate variants from the current best workflow.
            for i in range(1, self.population_size):
                round_counter += 1
                optimized_code, modification, thought = await self._mutate_workflow(
                    parent_code=best_code,
                    parent_score=best_fitness,
                    parent_round_num=best_round,
                    task_hint=task_hint,
                )
                cand = EvalCandidate(
                    code=optimized_code,
                    modification=modification or f"Variant {i}",
                    round_num=round_counter,
                    thought=thought,
                )
                population.append(cand)
                candidates_by_round[cand.round_num] = cand

            # Stage 1: coarse filter by plan quality.
            rep = tasks[0]
            for idx, cand in enumerate(population, start=1):
                if self._progress_enabled():
                    logger.info(
                        "DSFlow progress: gen %d/%d coarse %d/%d (round=%d)",
                        gen,
                        self.max_generations,
                        idx,
                        len(population),
                        cand.round_num,
                    )
                cand.coarse_score = await self._coarse_score(
                    workflow_code=cand.code,
                    modification=cand.modification,
                    raw_description=rep.raw_description,
                    base_report=rep.base_report,
                    data_dir=rep.data_dir,
                    output_filename=f"coarse_submission_{uuid.uuid4().hex[:6]}.csv",
                )

                stored = candidates_by_round.get(cand.round_num)
                if stored is None:
                    candidates_by_round[cand.round_num] = cand
                    stored = cand
                stored.coarse_score = cand.coarse_score

                if cand.round_num not in recorded_coarse_rounds:
                    self._record_score(
                        round_num=cand.round_num,
                        fitness=cand.coarse_score,
                        code=cand.code,
                        score_type="coarse",
                        extra={"modification": cand.modification},
                    )
                    recorded_coarse_rounds.add(cand.round_num)

            ranked = sorted(population, key=lambda c: c.coarse_score, reverse=True)
            selected = ranked[: self.selected_candidates_count]
            selected_rounds = {c.round_num for c in selected}

            logger.info(
                "Coarse filter selected %d/%d candidates.",
                len(selected),
                len(population),
            )

            # Stage 2: fine evaluation only for selected candidates.
            fine_total = len(
                [c for c in selected if not (c.round_num == best_round and c.code == best_code)]
            )
            fine_done = 0
            for cand in population:
                # Avoid re-evaluating (and re-recording) the current best workflow.
                if cand.round_num == best_round and cand.code == best_code:
                    cand.fitness = best_fitness
                    cand.fine_evaluated = True
                    continue
                if cand.round_num not in selected_rounds:
                    cand.fitness = 0.0
                    cand.fine_evaluated = False
                    continue

                fine_done += 1
                if self._progress_enabled():
                    logger.info(
                        "DSFlow progress: gen %d/%d fine %d/%d (round=%d, coarse=%.3f)",
                        gen,
                        self.max_generations,
                        fine_done,
                        max(1, fine_total),
                        cand.round_num,
                        cand.coarse_score,
                    )

                cand.fitness = await self._fine_evaluate(
                    workflow_code=cand.code,
                    tasks=tasks,
                )
                cand.fine_evaluated = True

                self._record_operator_library_outcome(
                    workflow_code=cand.code,
                    success=cand.fitness > best_fitness,
                    tasks=tasks,
                )

                stored = candidates_by_round.get(cand.round_num)
                if stored is None:
                    candidates_by_round[cand.round_num] = cand
                    stored = cand
                stored.fitness = cand.fitness
                stored.fine_evaluated = True

                if cand.round_num not in recorded_fitness_rounds:
                    self._record_score(
                        round_num=cand.round_num,
                        fitness=cand.fitness,
                        code=cand.code,
                        score_type="fitness",
                        extra={
                            "coarse_score": cand.coarse_score,
                            "modification": cand.modification,
                        },
                    )
                    recorded_fitness_rounds.add(cand.round_num)

                # Persist experience (relative to current best).
                if cand.round_num != best_round:
                    self.experience.record_experience(
                        parent_round=best_round,
                        child_round=cand.round_num,
                        modification=cand.modification,
                        score_before=best_fitness,
                        score_after=cand.fitness,
                    )

            gen_best = max(population, key=lambda c: c.fitness)
            logger.info(
                "Generation %d best: fitness=%.4f coarse=%.3f (%s)",
                gen,
                gen_best.fitness,
                gen_best.coarse_score,
                gen_best.modification,
            )

            if gen_best.fitness > best_fitness:
                best_code = gen_best.code
                best_fitness = gen_best.fitness
                best_round = gen_best.round_num
                logger.info(
                    "New global best found: round=%d fitness=%.4f", best_round, best_fitness
                )

        final_best, selection_extra = self._select_final_candidate(
            list(candidates_by_round.values())
        )
        logger.info(
            "Final selection: fitness=%.4f coarse=%.3f (round=%d, %s)",
            final_best.fitness,
            final_best.coarse_score,
            final_best.round_num,
            selection_extra.get("modification", ""),
        )
        self._record_final_selection(candidate=final_best, selection_extra=selection_extra)
        logger.info("DSFlow optimization finished. Best fitness: %.4f", final_best.fitness)

        self._auto_sync_custom_operators()
        return final_best.code

    async def _optimize_final_fine_eval(self, tasks: list[TaskContext], task_hint: str) -> str:
        """
        Default (fast) mode:
        - Search using coarse plan screening only.
        - Run fine evaluation once at the end on baseline + top-k by coarse score.
        """
        rep = tasks[0]

        best_code = get_initial_dsflow_workflow_code()
        best_round = 0
        round_counter = best_round

        # Always include the baseline in the final fine evaluation as a safety net.
        baseline = EvalCandidate(
            code=best_code,
            modification="Initial (baseline)",
            round_num=best_round,
        )
        if self._progress_enabled():
            logger.info("DSFlow progress: baseline coarse screening (round=%d) ...", best_round)
            logger.info(
                "DSFlow coarse screening runs the candidate workflow to capture plan/python_code "
                "(NOT executing the generated python_code). Prompts shown next come from candidate operators "
                "like DSProblemAnalysis/DSCodeGen, not from the meta-optimizer prompt."
            )
        baseline.coarse_score = await self._coarse_score(
            workflow_code=baseline.code,
            modification=baseline.modification,
            raw_description=rep.raw_description,
            base_report=rep.base_report,
            data_dir=rep.data_dir,
            output_filename=f"coarse_submission_{uuid.uuid4().hex[:6]}.csv",
        )
        self._record_score(
            round_num=baseline.round_num,
            fitness=baseline.coarse_score,
            code=baseline.code,
            score_type="coarse",
            extra={"modification": baseline.modification},
        )
        best_coarse = baseline.coarse_score

        all_candidates: list[EvalCandidate] = [baseline]

        for gen in range(1, self.max_generations + 1):
            logger.info("--- DSFlow Generation %d/%d (coarse-only) ---", gen, self.max_generations)

            population: list[EvalCandidate] = [
                EvalCandidate(
                    code=best_code,
                    modification="Parent (carry-over)",
                    round_num=best_round,
                    coarse_score=best_coarse,
                )
            ]

            for i in range(1, self.population_size):
                round_counter += 1
                optimized_code, modification, thought = await self._mutate_workflow(
                    parent_code=best_code,
                    parent_score=best_coarse,
                    parent_round_num=best_round,
                    task_hint=task_hint,
                )
                population.append(
                    EvalCandidate(
                        code=optimized_code,
                        modification=modification or f"Variant {i}",
                        round_num=round_counter,
                        thought=thought,
                    )
                )

            # Stage 1: coarse filter by plan quality (only score new variants).
            for idx, cand in enumerate(population, start=1):
                if cand.round_num == best_round and cand.code == best_code:
                    cand.coarse_score = best_coarse
                    continue

                if self._progress_enabled():
                    logger.info(
                        "DSFlow progress: gen %d/%d coarse %d/%d (round=%d)",
                        gen,
                        self.max_generations,
                        idx,
                        len(population),
                        cand.round_num,
                    )

                cand.coarse_score = await self._coarse_score(
                    workflow_code=cand.code,
                    modification=cand.modification,
                    raw_description=rep.raw_description,
                    base_report=rep.base_report,
                    data_dir=rep.data_dir,
                    output_filename=f"coarse_submission_{uuid.uuid4().hex[:6]}.csv",
                )

                self._record_score(
                    round_num=cand.round_num,
                    fitness=cand.coarse_score,
                    code=cand.code,
                    score_type="coarse",
                    extra={"modification": cand.modification},
                )
                if cand.round_num != best_round:
                    self.experience.record_experience(
                        parent_round=best_round,
                        child_round=cand.round_num,
                        modification=cand.modification,
                        score_before=best_coarse,
                        score_after=cand.coarse_score,
                    )

            all_candidates.extend(population[1:])

            gen_best = max(population, key=lambda c: c.coarse_score)
            logger.info(
                "Generation %d coarse best: score=%.3f (%s)",
                gen,
                gen_best.coarse_score,
                gen_best.modification,
            )

            if gen_best.coarse_score > best_coarse:
                best_code = gen_best.code
                best_coarse = gen_best.coarse_score
                best_round = gen_best.round_num
                logger.info(
                    "New coarse best found: round=%d coarse=%.3f",
                    best_round,
                    best_coarse,
                )

        ranked = sorted(all_candidates, key=lambda c: c.coarse_score, reverse=True)

        # Stage 2: fine evaluation for only a few candidates (baseline + top-k by coarse score).
        max_fine = max(1, min(9, self.selected_candidates_count + 1))
        fine_candidates: list[EvalCandidate] = []
        seen: set[str] = set()

        def _add_unique(c: EvalCandidate) -> None:
            digest = hashlib.sha1((c.code or "").encode("utf-8")).hexdigest()
            if digest in seen:
                return
            seen.add(digest)
            fine_candidates.append(c)

        _add_unique(baseline)
        for cand in ranked:
            if len(fine_candidates) >= max_fine:
                break
            _add_unique(cand)

        if self._progress_enabled():
            logger.info(
                "DSFlow progress: final fine evaluation on %d candidate(s) (baseline + top-%d).",
                len(fine_candidates),
                self.selected_candidates_count,
            )

        baseline_fitness: Optional[float] = None

        for idx, cand in enumerate(fine_candidates, start=1):
            if self._progress_enabled():
                logger.info(
                    "DSFlow progress: final fine %d/%d (round=%d, coarse=%.3f)",
                    idx,
                    len(fine_candidates),
                    cand.round_num,
                    cand.coarse_score,
                )

            cand.fitness = await self._fine_evaluate(workflow_code=cand.code, tasks=tasks)
            cand.fine_evaluated = True

            self._record_score(
                round_num=cand.round_num,
                fitness=cand.fitness,
                code=cand.code,
                score_type="fitness",
                extra={
                    "coarse_score": cand.coarse_score,
                    "modification": cand.modification,
                },
            )
            if baseline_fitness is None:
                baseline_fitness = cand.fitness

            self._record_operator_library_outcome(
                workflow_code=cand.code,
                success=baseline_fitness is not None and cand.fitness > baseline_fitness,
                tasks=tasks,
            )

        final_best, selection_extra = self._select_final_candidate(fine_candidates)
        logger.info(
            "Final selection: fitness=%.4f coarse=%.3f (round=%d, %s)",
            final_best.fitness,
            final_best.coarse_score,
            final_best.round_num,
            selection_extra.get("modification", ""),
        )
        if selection_extra.get("selection_mode") == "weighted":
            logger.info(
                "Final selection details: combined=%.4f norm_fine=%.4f (weights fine=%.3f coarse=%.3f, norm=%s)",
                selection_extra.get("combined_score", 0.0),
                selection_extra.get("normalized_fine", 0.0),
                selection_extra.get("weight_fine", 0.0),
                selection_extra.get("weight_coarse", 0.0),
                selection_extra.get("normalization", ""),
            )

        self._record_final_selection(candidate=final_best, selection_extra=selection_extra)
        logger.info("DSFlow optimization finished. Best fitness: %.4f", final_best.fitness)

        # Auto-sync custom operators after optimization
        self._auto_sync_custom_operators()

        return final_best.code


__all__ = ["DSFlowWorkflow"]
