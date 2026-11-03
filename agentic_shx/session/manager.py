"""Session and event transcript persistence."""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

DEFAULT_SESSIONS_DIR = Path.home() / ".agentic_shx" / "sessions"

def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class SessionEvent:
    """An atomic event in the conversation trajectory."""
    type: str  # USER_INPUT, MODEL_THINKING, MODEL_OUTPUT, TOOL_CALL, TOOL_RESULT, ARTIFACT, SUBAGENT
    content: Any
    timestamp: str = field(default_factory=_utc_now_str)
    step_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manages session creation, transcript streaming, and resumption."""

    def __init__(self, session_id: Optional[str] = None, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DEFAULT_SESSIONS_DIR
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.session_dir = self.base_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_file = self.session_dir / "transcript.jsonl"
        self.meta_file = self.session_dir / "metadata.json"
        self.step_counter = 0

        if not self.meta_file.exists():
            self._save_metadata({"created_at": _utc_now_str(), "title": "New Session"})

    def log_event(self, event_type: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Append an event to the JSONL transcript."""
        self.step_counter += 1
        event = SessionEvent(
            type=event_type,
            content=content,
            step_index=self.step_counter,
            metadata=metadata or {}
        )
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def _save_metadata(self, data: Dict[str, Any]) -> None:
        current = {}
        if self.meta_file.exists():
            try:
                current = json.loads(self.meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        current.update(data)
        current["updated_at"] = _utc_now_str()
        current["steps"] = self.step_counter
        self.meta_file.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def set_title_from_prompt(self, prompt: str) -> None:
        clean_title = prompt.strip().split("\n")[0][:60]
        self._save_metadata({"title": clean_title})

    def load_events(self) -> List[SessionEvent]:
        """Load all transcript events."""
        events = []
        if self.transcript_file.exists():
            with open(self.transcript_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            d = json.loads(line)
                            events.append(SessionEvent(**d))
                        except Exception:
                            continue
        return events

    @classmethod
    def list_all_sessions(cls, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """List all past sessions with metadata."""
        target_dir = base_dir or DEFAULT_SESSIONS_DIR
        if not target_dir.exists():
            return []
        sessions = []
        for d in sorted(target_dir.iterdir(), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
            if d.is_dir():
                meta_p = d / "metadata.json"
                if meta_p.exists():
                    try:
                        data = json.loads(meta_p.read_text(encoding="utf-8"))
                        data["id"] = d.name
                        sessions.append(data)
                    except Exception:
                        pass
        return sessions
