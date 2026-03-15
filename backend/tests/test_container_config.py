from pathlib import Path


def test_docker_compose_passes_openai_env_to_backend_container():
    compose_text = (Path.cwd() / "docker-compose.yml").read_text(encoding="utf-8")

    assert "OPENAI_API_KEY: ${OPENAI_API_KEY:-}" in compose_text
    assert "OPENAI_API_URL: ${OPENAI_API_URL:-}" in compose_text
    assert "OPENAI_MODEL: ${OPENAI_MODEL:-}" in compose_text
    assert "OPENAI_PROVIDER: ${OPENAI_PROVIDER:-}" in compose_text
    assert "OPENAI_PROTOCOL: ${OPENAI_PROTOCOL:-}" in compose_text
    assert "ghcr.io/${GHCR_IMAGE_PREFIX:-hanhyalex123/personal-open-source-intel-workbench}/backend:local" in compose_text
    assert "ghcr.io/${GHCR_IMAGE_PREFIX:-hanhyalex123/personal-open-source-intel-workbench}/frontend:local" in compose_text


def test_publish_workflow_uses_path_style_ghcr_names():
    workflow_text = (Path.cwd() / ".github" / "workflows" / "publish-ghcr.yml").read_text(encoding="utf-8")

    assert "images: ghcr.io/${{ github.repository }}/${{ matrix.image_name }}" in workflow_text


def test_e2e_script_accepts_openai_env_as_primary_credentials():
    script_text = (Path.cwd() / "scripts" / "e2e_incus_container.sh").read_text(encoding="utf-8")

    assert 'OPENAI_API_KEY="$(resolve_env_value OPENAI_API_KEY)"' in script_text
    assert 'if [[ -z "$PACKY_API_KEY" && -n "$OPENAI_API_KEY" ]]; then' in script_text
    assert 'Either PACKY_API_KEY or OPENAI_API_KEY is required' in script_text
