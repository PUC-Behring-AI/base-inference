"""Configuration file schema validation tests.

These tests validate that infrastructure configuration files
(Dockerfile.ray, serve_config.yaml, docker-compose.yml, config.yaml,
.env.example, observability/scrape.d/inference.yml) conform to the
structure defined in docs/ARCHITECTURE.md.

Each test skips gracefully if the target file has not been created
yet (later phase), so this module is safe to run from Phase 1 onward.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


# ── Helpers ─────────────────────────────────────────────────────────────

def _read_yaml(path: Path) -> Any:
    """Return parsed YAML, or None if file is absent.

    Not annotated as `dict | None`: a Prometheus `scrape_config_files`
    fragment is a bare list, and pinning this to a mapping would make the
    fragment's own tests lie about what they parsed.
    """
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw)


# ── serve_config.yaml (§5.3) ────────────────────────────────────────────

SERVE_CONFIG_REQUIRED_KEYS = [
    "proxy_location",
    "http_options",
    "applications",
]


@pytest.mark.config
class TestServeConfig:
    """serve_config.yaml structure per §5.3 of the architecture."""

    @pytest.fixture
    def config(self, config_files: dict[str, Path]) -> dict | None:
        return _read_yaml(config_files["serve_config"])

    def test_exists(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet (Phase 2)")
        assert isinstance(config, dict)

    def test_has_required_keys(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        for key in SERVE_CONFIG_REQUIRED_KEYS:
            assert key in config, f"Missing required key: {key}"

    def test_proxy_location(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        assert config.get("proxy_location") == "EveryNode"

    def test_http_options_host(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        opts = config.get("http_options", {})
        # Per §9.2: binds 0.0.0.0 inside the container only
        assert opts.get("host") == "0.0.0.0"

    def test_http_options_port(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        opts = config.get("http_options", {})
        assert opts.get("port") == 8000

    def test_applications_is_list(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        apps = config.get("applications", [])
        assert isinstance(apps, list), "applications must be a list"
        assert len(apps) > 0, "at least one application required"

    def test_first_app_has_route_prefix(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("serve_config.yaml not created yet")
        apps = config.get("applications", [])
        if not apps:
            pytest.skip("no applications defined yet")
        assert "/" in apps[0].get("route_prefix", "")


# ── docker-compose.yml (§5.4, §10.2) ────────────────────────────────────

COMPOSE_REQUIRED_SERVICES = ["ray-head", "litellm", "dcgm-exporter"]


@pytest.mark.config
class TestDockerCompose:
    """docker-compose.yml structure per §5.4 and §10.2."""

    @pytest.fixture
    def config(self, config_files: dict[str, Path]) -> dict | None:
        return _read_yaml(config_files["docker_compose"])

    def test_exists(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("docker-compose.yml not created yet (Phase 2)")
        assert isinstance(config, dict)

    def test_has_required_services(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("docker-compose.yml not created yet")
        services = config.get("services", {})
        for svc in COMPOSE_REQUIRED_SERVICES:
            assert svc in services, f"Missing required service: {svc}"

    def test_ray_head_ipc(self, config: dict | None) -> None:
        """Ray requires ipc=host for shared-memory multiprocessing."""
        if config is None:
            pytest.skip("docker-compose.yml not created yet")
        svc = config.get("services", {}).get("ray-head", {})
        assert svc.get("ipc") == "host", "ray-head needs ipc: host"

    def test_ray_head_shm_size(self, config: dict | None) -> None:
        if config is None:
            pytest.skip("docker-compose.yml not created yet")
        svc = config.get("services", {}).get("ray-head", {})
        assert "shm_size" in svc, "ray-head needs shm_size set"


# ── LiteLLM config (§4.3) ──────────────────────────────────────────────
# There is no config.yaml on disk to validate. LiteLLM consumes
# rendered_litellm_config.yaml, which render_config.py builds from a dict in
# code — so the assertions run against that function's output, which is what
# the container actually receives. A file used to sit at the repo root looking
# canonical while nothing read it; issue #10 records what that cost.

LITELLM_REQUIRED_KEYS = ["model_list", "general_settings"]


@pytest.mark.config
class TestLiteLLMConfig:
    """The generated LiteLLM config, per §4.3."""

    @pytest.fixture
    def config(self, repo_root: Path) -> dict:
        sys.path.insert(0, str(repo_root))
        try:
            from scripts.render_config import render_litellm_config
        finally:
            sys.path.pop(0)
        rendered = render_litellm_config(
            overrides={"MODEL_ID": "test-model", "MODEL_SOURCE": "test-org/test-model"}
        )
        return yaml.safe_load(rendered)

    def test_has_required_keys(self, config: dict) -> None:
        for key in LITELLM_REQUIRED_KEYS:
            assert key in config, f"Missing required key: {key}"

    def test_model_list_has_entries(self, config: dict) -> None:
        assert len(config.get("model_list", [])) > 0, "model_list must have at least one entry"

    def test_models_route_to_ray_ingress(self, config: dict) -> None:
        for entry in config["model_list"]:
            assert entry["litellm_params"]["api_base"] == "http://ray-head:8000/v1"

    def test_master_key_is_an_env_reference(self, config: dict) -> None:
        """The rendered file lands on disk — the key must stay a reference."""
        master = config.get("general_settings", {}).get("master_key", "")
        assert master.startswith("os.environ/"), (
            f"master_key must be an env reference, got {master!r}"
        )

    def test_no_stale_config_yaml_at_repo_root(self, repo_root: Path) -> None:
        """A second file that looks canonical and is never read (issue #10)."""
        assert not (repo_root / "config.yaml").exists(), (
            "config.yaml is not consumed by anything — delete it rather than "
            "let it drift out of step with _render_litellm_config()"
        )


# ── observability/scrape.d/inference.yml (C4) ───────────────────────────
#
# The backend moved to base-platform. What this layer keeps is the file
# declaring its own targets, which base-platform mounts and reads through
# `scrape_config_files`. The assertions below moved with the file: they no
# longer check a server's configuration, they check that this layer asks for
# exactly the three targets it emits on.

EXPECTED_TARGETS = ["ray-head:8080", "litellm:4000", "dcgm-exporter:9400"]


@pytest.mark.config
class TestScrapeTargets:
    """What this layer publishes for the platform layer's backend to scrape."""

    @pytest.fixture
    def jobs(self, config_files: dict[str, Path]) -> list | None:
        return _read_yaml(config_files["scrape"])

    def test_exists_and_is_a_job_list(self, jobs: list | None) -> None:
        assert jobs is not None, (
            "observability/scrape.d/inference.yml is missing — without it the "
            "platform layer's backend scrapes nothing from this layer, and "
            "nothing says so"
        )
        assert isinstance(jobs, list), (
            "a scrape_config_files fragment is a LIST of jobs, not a mapping "
            "with a scrape_configs key — Prometheus reads it as a bare list"
        )

    def test_targets_match_the_services_this_layer_runs(
        self, jobs: list | None
    ) -> None:
        assert jobs is not None
        found: set[str] = set()
        for job in jobs:
            for group in job.get("static_configs", []):
                for target in group.get("targets", []):
                    found.add(target)
        for expected in EXPECTED_TARGETS:
            assert expected in found, (
                f"scrape target {expected!r} missing — got {sorted(found)}"
            )

    def test_every_job_is_labelled_with_this_layer(self, jobs: list | None) -> None:
        """Series from five layers land in one backend, so the label is not
        decoration: without it, `layer=` cannot separate them."""
        assert jobs is not None
        for job in jobs:
            for group in job.get("static_configs", []):
                labels = group.get("labels", {})
                assert labels.get("layer") == "inference", (
                    f"job {job.get('job_name')!r} is missing layer=inference"
                )

    def test_no_global_section(self, jobs: list | None) -> None:
        """`global` belongs to the backend, and this is not the backend.

        A fragment carrying its own global block is silently ignored, which
        looks like a working scrape interval and is not one.
        """
        assert jobs is not None
        assert isinstance(jobs, list), "a fragment with a global: block is a mapping"


# ── .env.example ────────────────────────────────────────────────────────

REQUIRED_ENV_VARS = ["HF_TOKEN", "LITELLM_MASTER_KEY", "MODEL_ID", "MODEL_SOURCE"]


@pytest.mark.config
class TestEnvExample:
    """.env.example documents all required env vars."""

    def test_declares_required_vars(self, config_files: dict[str, Path]) -> None:
        path = config_files["env_example"]
        if not path.exists():
            pytest.skip(".env.example not created yet (Phase 2)")
        content = path.read_text(encoding="utf-8")
        for var in REQUIRED_ENV_VARS:
            assert var in content, f".env.example missing required var: {var}"
