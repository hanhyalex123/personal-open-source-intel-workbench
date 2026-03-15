import os
from pathlib import Path
import socket
import subprocess
import textwrap


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return handle.getsockname()[1]


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
                "INTEL_HIGRESS_REQUIRED": "false",
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


def test_start_script_honors_backend_python_override(tmp_path: Path):
    script_path = Path.cwd() / "scripts" / "start_intel_workbench.sh"
    root_dir = tmp_path / "workspace"
    bin_dir = tmp_path / "bin"
    backend_port = _free_port()
    frontend_port = _free_port()
    root_dir.mkdir()
    bin_dir.mkdir()
    real_python3 = subprocess.check_output(["bash", "-lc", "command -v python3"], text=True).strip()

    bad_python = bin_dir / "python3"
    bad_python.write_text("#!/bin/bash\nexit 1\n", encoding="utf-8")
    bad_python.chmod(0o755)

    backend_wrapper = tmp_path / "backend-python"
    backend_wrapper.write_text(
        textwrap.dedent(
            """\
            #!/bin/bash
            if [[ "$1" == "-m" && "$2" == "backend.server" ]]; then
              exec REAL_PYTHON3 -m http.server BACKEND_PORT --bind 127.0.0.1
            fi
            exec REAL_PYTHON3 "$@"
            """
        )
        .replace("REAL_PYTHON3", real_python3)
        .replace("BACKEND_PORT", str(backend_port)),
        encoding="utf-8",
    )
    backend_wrapper.chmod(0o755)

    try:
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=Path.cwd(),
            env={
                **os.environ,
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "INTEL_WORKBENCH_ROOT": str(root_dir),
                "INTEL_BACKEND_PYTHON": str(backend_wrapper),
                "INTEL_BACKEND_URL": f"http://127.0.0.1:{backend_port}",
                "INTEL_FRONTEND_URL": f"http://127.0.0.1:{frontend_port}",
                "INTEL_FRONTEND_CMD": f"{real_python3} -m http.server {frontend_port} --bind 127.0.0.1",
                "INTEL_OPEN_CMD": "true",
                "INTEL_HIGRESS_REQUIRED": "false",
            },
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "架构师开源情报站 is running." in result.stdout
    finally:
        subprocess.run(["bash", str(Path.cwd() / "scripts" / "stop_intel_workbench.sh")], cwd=Path.cwd(), env={**os.environ, "INTEL_WORKBENCH_ROOT": str(root_dir)}, check=False)
