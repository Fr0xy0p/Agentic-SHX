"""Tool to inspect and activate specialized skills."""

from typing import Optional, Dict, Any
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.skills.manager import SkillManager

class ReadSkillTool(BaseTool):
    """Tool to read the full SKILL.md guide for a skill."""

    name = "read_skill"
    description = "Read the detailed instructions and workflow rules for an available skill by name."
    parameters = {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "Name of the skill to read (e.g. 'code-review', 'git-workflow')."
            }
        },
        "required": ["skill_name"]
    }

    def __init__(self, manager: SkillManager):
        self.manager = manager

    def execute(self, skill_name: str, **kwargs) -> ToolResult:
        skill = self.manager.get_skill(skill_name)
        if not skill:
            avail = list(self.manager.skills.keys())
            return ToolResult(
                success=False,
                output="",
                error=f"Skill '{skill_name}' not found. Available skills: {avail}"
            )
        header = f"=== Skill: {skill.name} ===\nDescription: {skill.description}\nPath: {skill.path}\n\n"
        return ToolResult(success=True, output=header + skill.instructions)

