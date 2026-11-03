"""Artifact storage, metadata, and lifecycle management."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

DEFAULT_ARTIFACTS_DIR = Path.home() / ".agentic_shx" / "artifacts"

def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Artifact:
    filename: str
    title: str
    path: Path
    summary: str
    content: str
    request_feedback: bool = False
    user_facing: bool = True
    created_at: str = field(default_factory=_utc_now_str)


class ArtifactManager:
    """Manages markdown artifacts for the active session."""

    def __init__(self, session_id: str, base_dir: Optional[Path] = None):
        self.session_id = session_id
        self.artifacts_dir = (base_dir or DEFAULT_ARTIFACTS_DIR) / session_id
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts: Dict[str, Artifact] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        for md_file in self.artifacts_dir.glob("*.md"):
            meta_file = md_file.with_suffix(".json")
            summary = ""
            req_fb = False
            title = md_file.stem.replace("_", " ").title()
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    summary = data.get("summary", "")
                    req_fb = data.get("request_feedback", False)
                    title = data.get("title", title)
                except Exception:
                    pass
            content = md_file.read_text(encoding="utf-8") if md_file.exists() else ""
            self.artifacts[md_file.name] = Artifact(
                filename=md_file.name,
                title=title,
                path=md_file,
                summary=summary,
                content=content,
                request_feedback=req_fb
            )

    def save_artifact(
        self,
        filename: str,
        title: str,
        content: str,
        summary: str = "",
        request_feedback: bool = False,
        user_facing: bool = True
    ) -> Artifact:
        clean_name = filename if filename.endswith(".md") else f"{filename}.md"
        file_path = self.artifacts_dir / clean_name
        file_path.write_text(content, encoding="utf-8")

        meta = {
            "title": title,
            "summary": summary,
            "request_feedback": request_feedback,
            "user_facing": user_facing,
            "updated_at": _utc_now_str()
        }
        meta_path = self.artifacts_dir / f"{clean_name}.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        art = Artifact(
            filename=clean_name,
            title=title,
            path=file_path,
            summary=summary,
            content=content,
            request_feedback=request_feedback,
            user_facing=user_facing
        )
        self.artifacts[clean_name] = art
        return art

    def list_artifacts(self) -> List[Artifact]:
        return list(self.artifacts.values())

    def get_artifact(self, filename: str) -> Optional[Artifact]:
        clean_name = filename if filename.endswith(".md") else f"{filename}.md"
        return self.artifacts.get(clean_name)
