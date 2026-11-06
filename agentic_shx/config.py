"""Configuration management for Agentic-SHX."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".agentic_shx"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_HISTORY_PATH = DEFAULT_CONFIG_DIR / "history.txt"


def _load_env_file(env_path: Path):
    """Simple parser for .env files without external dependencies."""
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

# Check local workspace .env first, then home dir .env
_load_env_file(Path.cwd() / ".env")
_load_env_file(Path.home() / ".env")


@dataclass
class Settings:
    """User and runtime settings."""
    model: str = os.getenv("SHX_MODEL", "gemini/gemini-3.8-flash")
    temperature: float = 0.2
    max_tokens: int = 4096
    max_steps: int = 30
    
    # Permissions & Safety
    auto_approve_safe_commands: bool = True
    always_ask_write: bool = False
    
    # Shell settings
    shell_timeout_seconds: int = 120
    max_output_length: int = 8000

    # API Keys & Custom Base URLs
    api_keys: Dict[str, str] = field(default_factory=dict)
    api_bases: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        path = config_path or DEFAULT_CONFIG_PATH
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                # Filter only valid fields
                valid_fields = {f for f in cls.__dataclass_fields__}
                filtered = {k: v for k, v in data.items() if k in valid_fields}
                return cls(**filtered)
            except Exception as e:
                print(f"[Warning] Failed to load config from {path}: {e}. Using defaults.")
        return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        path = config_path or DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(self), f, default_flow_style=False)
