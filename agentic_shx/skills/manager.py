"""Skills discovery, parsing, and management."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import yaml

DEFAULT_GLOBAL_SKILLS_DIR = Path.home() / ".agentic_shx" / "skills"

@dataclass
class Skill:
    name: str
    description: str
    path: Path
    instructions: str


class SkillManager:
    """Discovers and provides skills to the agent."""

    def __init__(self, workspace_cwd: Optional[Path] = None, global_dir: Optional[Path] = None):
        self.workspace_cwd = workspace_cwd or Path.cwd()
        self.global_dir = global_dir or DEFAULT_GLOBAL_SKILLS_DIR
        self.skills: Dict[str, Skill] = {}
        self.discover_skills()

    def discover_skills(self) -> None:
        """Scan workspace (.shx/skills) and global (~/.agentic_shx/skills) for SKILL.md files."""
        search_dirs = [
            self.global_dir,
            self.workspace_cwd / ".shx" / "skills",
        ]
        for base in search_dirs:
            if not base.exists():
                continue
            for skill_dir in base.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    self._parse_skill_file(skill_file)

    def _parse_skill_file(self, skill_file: Path) -> None:
        try:
            content = skill_file.read_text(encoding="utf-8")
            name = skill_file.parent.name
            description = ""
            instructions = content

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1]
                    instructions = parts[2].strip()
                    try:
                        fm = yaml.safe_load(frontmatter_str) or {}
                        name = fm.get("name", name)
                        description = fm.get("description", "")
                    except Exception:
                        pass

            self.skills[name] = Skill(
                name=name,
                description=description,
                path=skill_file,
                instructions=instructions
            )
        except Exception:
            pass

    def get_skills_prompt(self) -> str:
        """Formatted skills prompt block for system prompt."""
        if not self.skills:
            return ""
        lines = ["AVAILABLE SKILLS:", "You can activate specialized skills by reading their instructions:"]
        for s in self.skills.values():
            lines.append(f"- **{s.name}** ({s.path}): {s.description}")
        return "\n".join(lines) + "\n"

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())

