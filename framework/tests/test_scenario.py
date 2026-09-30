import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "scenario.py"
SPEC = importlib.util.spec_from_file_location("scenario", MODULE_PATH)
assert SPEC and SPEC.loader
scenario = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scenario)


class ScenarioTests(unittest.TestCase):
    def test_registry_covers_every_supported_endpoint(self) -> None:
        registry = scenario.load_json(scenario.ENDPOINTS_PATH)
        self.assertEqual(
            {"azure", "entra-id", "github", "azure-devops"},
            set(registry["endpoints"]),
        )
        for endpoint, config in registry["endpoints"].items():
            self.assertTrue(config["preferred_servers"], endpoint)
            for server_name in config["preferred_servers"]:
                server = registry["servers"][server_name]
                self.assertIn(endpoint, server["endpoints"])

    def test_repository_scenarios_are_valid(self) -> None:
        paths = scenario.scenario_paths()
        self.assertTrue(paths)
        for path in paths:
            self.assertEqual([], scenario.validate_scenario(path), path)

    def test_dry_run_plan_never_allows_writes(self) -> None:
        plan = scenario.build_plan(scenario.scenario_paths()[0], "dry-run")
        self.assertFalse(plan["safety"]["writes_allowed"])

    def test_cross_plane_plan_preserves_source_and_impact_endpoints(self) -> None:
        path = scenario.ROOT / "use-cases" / "azure" / "vs002" / "scenario.json"
        plan = scenario.build_plan(path, "dry-run")
        self.assertEqual("azure", plan["source_endpoint"])
        self.assertEqual("entra-id", plan["endpoint"])

    def test_artifact_cannot_escape_scenario(self) -> None:
        manifest = json.loads(scenario.scenario_paths()[0].read_text())
        manifest["artifacts"][0]["path"] = "../outside.txt"
        with tempfile.TemporaryDirectory(dir=scenario.ROOT / "use-cases") as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(manifest))
            errors = scenario.validate_scenario(path)
        self.assertTrue(any("escapes" in error for error in errors))

    def test_lab_impact_requires_approval_and_canary(self) -> None:
        manifest = json.loads(scenario.scenario_paths()[0].read_text())
        manifest["modes"]["lab-impact"]["requires_operator_approval"] = False
        manifest["modes"]["lab-impact"]["canary_targets"] = []
        with tempfile.TemporaryDirectory(dir=scenario.ROOT / "use-cases") as directory:
            path = Path(directory) / "scenario.json"
            for artifact in manifest["artifacts"]:
                artifact_path = Path(directory) / artifact["path"]
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text("fixture")
            path.write_text(json.dumps(manifest))
            errors = scenario.validate_scenario(path)
        self.assertIn("lab-impact requires operator approval", errors)
        self.assertIn("lab-impact requires at least one canary target", errors)


if __name__ == "__main__":
    unittest.main()