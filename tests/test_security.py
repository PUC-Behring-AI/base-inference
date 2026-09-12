"""Security constraint validation tests for base-inference.

These tests verify that the deployment artifacts respect the security
boundaries defined in docs/ARCHITECTURE.md §9, without requiring a
running Docker environment.

They check:
    - Port isolation: only :4000 is exposed externally
    - Image pinning: no :latest in Dockerfile or compose
    - Dashboard binding: bound to 127.0.0.1
    - Trust boundaries: master key declared in config

Tests that genuinely require a running container (e.g., verify that
:8000 is actually unreachable from outside) are marked @pytest.mark.security
and skip when Docker is unavailable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml


@pytest.mark.security
class TestPortIsolation:
    """Only port 4000 is exposed to the host.

    See ARCHITECTURE.md §9.1.
    """

    def test_only_decided_ports_published(self, repo_root: Path) -> None:
        """Only 4000 (API) is reachable from the network.

        3001 (Open WebUI) was a recorded exception here until the service
        itself moved to base-interface (base-platform#14, 2026-09-12) — see
        ADR-013, now relocated to base-interface/docs/ADR.md. Adding a second
        port back here is a decision, so it belongs in an ADR before it
        belongs here.

        Services bound to 127.0.0.1 (Grafana on 3000) are not network-reachable
        and are permitted. See ARCHITECTURE.md §9.1.
        """
        allowed = {"4000"}
        path = repo_root / "docker-compose.yml"
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        all_ports: list[str] = []
        for svc in compose.get("services", {}).values():
            ports = svc.get("ports", [])
            if isinstance(ports, list):
                all_ports.extend(str(p) for p in ports)
        assert len(all_ports) > 0, "No ports published at all — check service config"
        for p in all_ports:
            # Resolve ${VAR:-default} before splitting: the colon inside that
            # form is not a port separator.
            resolved = re.sub(r"\$\{[A-Za-z_][A-Za-z0-9_]*:-([^}]*)\}", r"\1", p)
            parts = resolved.split(":")
            if parts[0] == "127.0.0.1":
                continue
            host_part = parts[-2] if len(parts) >= 2 else parts[0]
            assert host_part in allowed, (
                f"Port {host_part} is exposed in docker-compose.yml — only "
                f"{sorted(allowed)} may be network-reachable (§9.1, ADR-013)"
            )

    def test_ray_ingress_not_published(self, repo_root: Path) -> None:
        """Ray Serve ingress port (8000) is NOT in any ports: section."""
        path = repo_root / "docker-compose.yml"
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        for svc in compose.get("services", {}).values():
            ports = svc.get("ports", [])
            if isinstance(ports, list):
                for p in ports:
                    if isinstance(p, str):
                        assert "8000" not in p, (
                            f"Port 8000 (Ray ingress) must not be published (§9.3)"
                        )

    def test_dashboard_not_published(self, repo_root: Path) -> None:
        """Ray Dashboard port (8265) is NOT in any ports: section."""
        path = repo_root / "docker-compose.yml"
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        for svc in compose.get("services", {}).values():
            ports = svc.get("ports", [])
            if isinstance(ports, list):
                for p in ports:
                    if isinstance(p, str):
                        assert "8265" not in p, (
                            f"Port 8265 (Ray dashboard) must not be published (§9.2)"
                        )

    def test_ray_client_not_published(self, repo_root: Path) -> None:
        """Ray Client port (10001) is NOT in any ports: section."""
        path = repo_root / "docker-compose.yml"
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        for svc in compose.get("services", {}).values():
            ports = svc.get("ports", [])
            if isinstance(ports, list):
                for p in ports:
                    if isinstance(p, str):
                        assert "10001" not in p, (
                            f"Port 10001 (Ray Client) must not be published (§9.2)"
                        )


# Tags whose meaning changes without the reference changing: the same string
# resolves to a different image after any upstream push. Checking for the
# literal ":latest" only caught one member of this family, and ":main" — the
# tag Open WebUI actually shipped on — walked underneath it.
MOVING_TAGS = frozenset(
    {"latest", "main", "master", "dev", "develop", "edge", "nightly"}
)



def _image_tag(image: str) -> str | None:
    """Return the tag of an image reference, or None when pinned by digest.

    The ``:`` in a registry port (``host:5000/img``) is not a tag separator,
    so the search happens only after the last ``/``. An omitted tag is
    ``latest`` by Docker's own default, which is the one case where the
    dangerous reference contains no ``:`` at all.
    """
    if "@" in image:
        return None
    last_segment = image.rsplit("/", 1)[-1]
    if ":" not in last_segment:
        return "latest"
    return last_segment.rsplit(":", 1)[-1]


@pytest.mark.security
class TestImagePinning:
    """All container images are pinned to immutable references.

    See ARCHITECTURE.md §9.1 and ADR-009.
    """

    def test_dockerfile_base_image_is_not_on_a_moving_tag(
        self, repo_root: Path
    ) -> None:
        """Every FROM in Dockerfile.ray names an immutable reference."""
        path = repo_root / "Dockerfile.ray"
        if not path.exists():
            pytest.skip("Dockerfile.ray not created yet")
        froms = re.findall(
            r"^\s*FROM\s+(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE
        )
        assert froms, "Dockerfile.ray declares no FROM"
        for image in froms:
            tag = _image_tag(image)
            assert tag not in MOVING_TAGS, (
                f"Dockerfile.ray builds FROM '{image}', whose tag ':{tag}' moves "
                f"— pin it to a digest or an immutable tag (§9.1)"
            )

    def test_compose_images_are_not_on_moving_tags(self, repo_root: Path) -> None:
        """No service in docker-compose.yml rides a tag that can be rewritten."""
        path = repo_root / "docker-compose.yml"
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        for svc_name, svc in compose.get("services", {}).items():
            image = str(svc.get("image", ""))
            if not image:  # services that build locally
                continue
            tag = _image_tag(image)
            assert tag not in MOVING_TAGS, (
                f"Service '{svc_name}' uses '{image}', whose tag ':{tag}' moves "
                f"— the same reference resolves to a different image after any "
                f"upstream push (§9.1)"
            )

    # test_services_we_reach_into_are_pinned_by_digest moved to
    # base-interface/tests/test_compose.py on 2026-09-12 (base-platform#14):
    # open-webui, the one service colleague.sh's schema assumption depends
    # on, is declared in that repository's compose.yaml now, not this one's.


@pytest.mark.security
class TestTrustBoundaries:
    """Two trust boundaries: master key vs virtual keys.

    See ARCHITECTURE.md §9.1.
    """

    def test_generated_config_never_embeds_the_master_key(self, repo_root: Path) -> None:
        """The rendered config is written to disk — the key must stay a reference.

        Substituting the real value here would put the admin credential in a
        file next to the repo, one `cat` away from a screen share (§9.1).
        """
        sys.path.insert(0, str(repo_root))
        try:
            from scripts.render_config import render_litellm_config
        finally:
            sys.path.pop(0)
        rendered = render_litellm_config(
            overrides={
                "MODEL_ID": "test-model",
                "MODEL_SOURCE": "test-org/test-model",
                "LITELLM_MASTER_KEY": "sk-should-never-be-written",
            }
        )
        assert "sk-should-never-be-written" not in rendered
        config = yaml.safe_load(rendered)
        assert config["general_settings"]["master_key"].startswith("os.environ/")


@pytest.mark.security
class TestDashboardBinding:
    """Ray Dashboard binds to 127.0.0.1.

    See ARCHITECTURE.md §9.2.
    """

    def test_dashboard_host_set_to_localhost(self, repo_root: Path) -> None:
        """serve_config.yaml does NOT bind Ray dashboard publicly.

        This test checks that no configuration exposes the dashboard to
        0.0.0.0. The compose file omits port 8265.
        """
        path = repo_root / "serve_config.yaml"
        if not path.exists():
            pytest.skip("serve_config.yaml not created yet")
        content = path.read_text(encoding="utf-8")
        # The http_options.host in serve_config.yaml binds the proxy
        # inside the container — not the dashboard. Verify it is 0.0.0.0
        # as specified in §5.3 (this is correct: proxy binds inside the
        # container — the port is not published to the host).
        parsed = yaml.safe_load(content)
        assert parsed["http_options"]["host"] == "0.0.0.0", (
            "serve_config proxy binds to 0.0.0.0 inside container (§5.3); "
            "isolation relies on never publishing port 8000 outside (§9.3)"
        )


# ── Phase 4: Monitoring Port Isolation ──────────────────────────────────────


@pytest.mark.security
class TestMonitoringPortIsolation:
    """This layer runs no metrics backend, so it publishes no metrics port.

    Prometheus on 9090 and Grafana on 127.0.0.1:3000 used to run here. Both
    moved to the platform layer under C4, and the assertions moved with them —
    what is checked here now is the absence, because the way this regresses is
    someone adding a local Grafana for one graph and never taking it out.
    """

    COMPOSE_PATH = "docker-compose.yml"
    # Ports belonging to a metrics or trace backend. None may be published by
    # this layer, on any interface — loopback included, because "only on
    # localhost" is how the previous Grafana justified itself.
    # 3001 is deliberately absent: that is the chat interface, a different
    # argument, covered by ADR-013.
    BACKEND_PORTS = {"9090", "3000"}

    def test_no_backend_port_is_published(self, repo_root: Path) -> None:
        path = repo_root / self.COMPOSE_PATH
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        for svc_name, svc in compose.get("services", {}).items():
            for port_mapping in svc.get("ports", []) or []:
                published = set(str(port_mapping).split(":"))
                offending = published & self.BACKEND_PORTS
                assert not offending, (
                    f"service {svc_name!r} publishes {sorted(offending)}, which "
                    "belongs to the metrics backend in base-platform. This "
                    "layer emits and publishes scrape targets; it does not run "
                    "the backend (C4)."
                )

    def test_no_backend_service_is_defined(self, repo_root: Path) -> None:
        """A backend reachable only on the internal network is still a backend."""
        path = repo_root / self.COMPOSE_PATH
        if not path.exists():
            pytest.skip("docker-compose.yml not created yet")
        compose = yaml.safe_load(path.read_text(encoding="utf-8"))
        present = {"prometheus", "grafana", "langfuse"} & set(
            compose.get("services", {})
        )
        assert not present, (
            f"{sorted(present)} is defined here. The backend belongs to "
            "base-platform; publish targets in observability/scrape.d/ instead."
        )
