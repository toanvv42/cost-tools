# Repository Guidelines

## Project Structure & Module Organization
- `aws_cost_tools/`: Source package
  - `reporter.py`: `AWSCostReporter`, `ReportConfig`, enums, CSV export
  - `cli.py`: CLI entry (`cost-tools`)
  - `examples.py`: Runnable report examples (`cost-tools-examples`)
- `pyproject.toml`: Build metadata, deps, ruff config
- `uv.lock`: Locked dependencies
- `README.md`: Usage and examples

## Build, Test, and Development Commands
- Create env (uv): `uv venv && source .venv/bin/activate && uv sync`
- Run CLI: `uv run cost-tools --days 7 --group-by service`
- Run examples: `uv run cost-tools-examples`
- Lint: `uv run ruff check .` (auto-fix: `--fix`)
- Format: `uv run ruff format .`
- Type-check: `uv run mypy aws_cost_tools`
- Tests (pytest): `uv run pytest -q`

## Coding Style & Naming Conventions
- Python 3.8+; prefer type hints everywhere.
- Ruff configured: line length 100, double quotes, spaces indentation.
- Modules: snake_case; classes: PascalCase; functions/vars: snake_case; constants: UPPER_SNAKE_CASE.
- Public CLI stays in `cli.py`; shared logic belongs in `reporter.py` (keep CLI thin).

## Testing Guidelines
- Framework: pytest. Place tests under `tests/`, name `test_*.py`.
- Mock AWS (e.g., stub Cost Explorer client); do not call live AWS in unit tests.
- Cover: config → CE request shaping, filter building, grouping, CSV export paths.
- Run locally: `uv run pytest -q`; add focused tests for new behavior.

## Commit & Pull Request Guidelines
- Commits: short, imperative, scoped (e.g., `add cli examples`, `fix ruff errors`).
- Prefer small, reviewable changes with passing lint/type/tests.
- PRs must include: purpose/summary, before/after notes, usage examples (commands), and links to issues.
- Include CSV snippets or logs when relevant; avoid committing credentials or real account IDs.

## Security & Configuration Tips
- AWS Cost Explorer requires region `us-east-1`; ensure credentials grant `ce:GetCostAndUsage` and `ce:GetDimensionValues`.
- Use `--profile` to select credentials; never commit keys, tokens, or account IDs.
- Large ranges may be slow; consider narrower `--days` or fewer groupings.

## Architecture Overview
- `AWSCostReporter` builds CE queries from `ReportConfig`, executes via `boto3`, and exports results to CSV.
- CLI parses flags (dates, filters, groupings), constructs `ReportConfig`, and delegates work to the reporter.

