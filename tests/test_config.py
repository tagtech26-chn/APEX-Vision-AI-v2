import pytest

from app.core.config import Settings


def test_invalid_port_is_rejected() -> None:
    settings = Settings()
    settings.port = 70000
    with pytest.raises(ValueError, match="APEX_PORT"):
        settings.validate()


def test_invalid_provider_is_rejected() -> None:
    settings = Settings()
    settings.ai_provider = "unknown"
    with pytest.raises(ValueError, match="APEX_AI_PROVIDER"):
        settings.validate()


def test_render_dimensions_are_validated() -> None:
    settings = Settings()
    settings.render_max_dim = 128
    with pytest.raises(ValueError, match="APEX_RENDER_MAX_DIM"):
        settings.validate()
