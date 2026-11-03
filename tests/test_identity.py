import pytest

from core.identity import (
    get_identity,
    load_config,
    load_persona,
    get_identity as identity,
)

from core.identity.schemas import SecuritySchema


def test_payal_identity():
    result = get_identity()

    assert result.name == "Payal"
    assert result.owner == "Rishu"


def test_persona_languages():
    persona = load_persona()

    assert "Hindi" in identity().languages
    assert persona.verify_before_claiming_success is True


def test_security_defaults():
    security = SecuritySchema()

    assert security.default_permission_level == 1
    assert security.require_approval_for_kali is True


def test_config_loads():
    config = load_config()

    assert config.model.primary_provider == "agy_bridge"
    assert config.config_version == "1.0.0"


def test_invalid_permission_level():
    with pytest.raises(Exception):
        SecuritySchema(default_permission_level=5)

