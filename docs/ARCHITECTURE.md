# Architecture

High-level flow:

1) Task setup
   - Select workflow
   - Select benchmark/task id
   - Set data directory

2) Workflow execution
   - Generate plan/code
   - Execute in sandbox
   - Iterate with review

3) Evaluation and logging
   - Score submissions
   - Save artifacts and logs

Reference layout:

- run_benchmark.py: CLI entry point
- dsat/: workflows, services, operators
- benchmarks/: competition registries and graders
- data/: prepared competitions

Add diagrams under assets/diagrams and link them here.
