from pathlib import Path


def test_start_script_uses_localhost_urls():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "start_intel_workbench.sh"
    script = script_path.read_text(encoding="utf-8")

    assert 'BACKEND_URL="${INTEL_BACKEND_URL:-http://127.0.0.1:8000/api/health}"' in script
    assert 'FRONTEND_URL="${INTEL_FRONTEND_URL:-http://127.0.0.1:5173}"' in script
    assert 'FRONTEND_CMD="${INTEL_FRONTEND_CMD:-./node_modules/.bin/vite --host 0.0.0.0 --port 5173}"' in script
