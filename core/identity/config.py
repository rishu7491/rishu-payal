"""Payal configuration model and defaults."""

from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from .schemas import IdentitySchema, PersonaSchema, SecuritySchema, AppSchema


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    primary_provider: str = "agy_bridge"
    agy_bridge_url: str = "http://127.0.0.1:8788/v1"
    agy_model: str = "gemini-3.8-flash-low"
    api_key: str = "local"
    timeout_seconds: int = 120
    llamacpp_url: str = "http://127.0.0.1:8080/v1"
    llamacpp_model: str = "default"


class KaliConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vbox_manage_path: str = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    vm_name: str = "kali-linux-2026.3-virtualbox-amd64"
    guest_user: str = "kali"
    guest_password: str = "kali"
    wsl_distro: str = "kali-linux"


class PayalConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    config_version: str = "1.0.0"
    app: AppSchema = Field(default_factory=AppSchema)
    identity: IdentitySchema = Field(default_factory=IdentitySchema)
    persona: PersonaSchema = Field(default_factory=PersonaSchema)
    security: SecuritySchema = Field(default_factory=SecuritySchema)
    model: ModelConfig = Field(default_factory=ModelConfig)
    kali: KaliConfig = Field(default_factory=KaliConfig)
    workspace_root: Path = Field(default_factory=Path.cwd)


CONFIG = PayalConfig()
