# Scenario Framework

Every example is a self-contained folder under `use-cases/<endpoint>/<id>/`. Its `scenario.json` declares the endpoint, delivery artifacts, benign target-agent task, MCP dependencies, expected evidence, and permitted execution modes.

## Commands

```bash
python3 framework/scripts/scenario.py validate --all
python3 framework/scripts/scenario.py plan use-cases/entra/vs001/scenario.json --mode dry-run
python3 -m unittest discover -s framework/tests -v
```

The planner does not invoke an LLM or MCP tool. It emits a deterministic execution contract for an evaluator agent, CI job, or demo harness.

## Add an endpoint

1. Register the endpoint and preferred production MCP server in `framework/endpoints.json`.
2. Add a launch example under `mcp/`.
3. Copy `use-cases/_template/` into the endpoint folder.
4. Keep weaponized skills and payloads inside the scenario folder as inert fixtures.
5. Add endpoint-specific scripts only when a common MCP server does not expose the required operation.
6. Validate all manifests before running an exercise.

`dry-run` is mandatory and can never allow writes. `lab-impact` is optional and requires operator approval plus explicit disposable canary targets.