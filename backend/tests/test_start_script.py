import os
from pathlib import Path
import subprocess
import textwrap


def test_start_script_fails_when_port_is_occupied_by_another_process(tmp_path: Path):
    script_path = Path.cwd() / "scripts" / "start_intel_workbench.sh"
    root_dir = tmp_path / "workspace"
    root_dir.mkdir()

    backend_server = subprocess.Popen(
        ["python3", "-m", "http.server", "18000", "--bind", "127.0.0.1"],
        cwd=root_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    frontend_server = subprocess.Popen(
        ["python3", "-m", "http.server", "15173", "--bind", "127.0.0.1"],
        cwd=root_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=Path.cwd(),
            env={
                **os.environ,
                "INTEL_WORKBENCH_ROOT": str(root_dir),
                "INTEL_BACKEND_URL": "http://127.0.0.1:18000",
                "INTEL_FRONTEND_URL": "http://127.0.0.1:15173",
                "INTEL_BACKEND_CMD": textwrap.dedent(
                    """\
                    python3 - <<'PY'
                    raise SystemExit(1)
                    PY
                    """
                ).strip(),
                "INTEL_FRONTEND_CMD": textwrap.dedent(
                    """\
                    python3 - <<'PY'
                    raise SystemExit(1)
                    PY
                    """
                ).strip(),
                "INTEL_OPEN_CMD": "true",
            },
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "process exited" in result.stderr
    finally:
        backend_server.terminate()
        frontend_server.terminate()
        backend_server.wait(timeout=5)
        frontend_server.wait(timeout=5)
