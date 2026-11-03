"""Unit tests for SkillManager and ReadSkillTool."""

from pathlib import Path
from agentic_shx.skills.manager import SkillManager
from agentic_shx.skills.tool import ReadSkillTool

def test_skill_discovery_and_reading(tmp_path):
    # Create mock skill directory
    skill_dir = tmp_path / ".shx" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: A test skill\n---\nDetailed skill instructions here.",
        encoding="utf-8"
    )

    sm = SkillManager(workspace_cwd=tmp_path)
    assert "my-skill" in sm.skills
    assert sm.skills["my-skill"].description == "A test skill"

    # Test prompt generation
    prompt = sm.get_skills_prompt()
    assert "my-skill" in prompt

    # Test ReadSkillTool
    tool = ReadSkillTool(manager=sm)
    res = tool.execute(skill_name="my-skill")
    assert res.success is True
    assert "Detailed skill instructions here." in res.output

