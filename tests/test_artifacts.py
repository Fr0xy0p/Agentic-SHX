"""Unit tests for ArtifactManager and CreateArtifactTool."""

from pathlib import Path
from agentic_shx.artifacts.manager import ArtifactManager
from agentic_shx.artifacts.tool import CreateArtifactTool

def test_artifacts_lifecycle(tmp_path):
    mgr = ArtifactManager(session_id="session-art-1", base_dir=tmp_path)
    tool = CreateArtifactTool(manager=mgr)

    res = tool.execute(
        filename="plan.md",
        title="Implementation Plan",
        content="# Plan\n\nPhase 1: Build\nPhase 2: Test",
        summary="Two phase plan",
        request_feedback=True
    )
    assert res.success is True

    # Inspect artifact
    art = mgr.get_artifact("plan.md")
    assert art is not None
    assert art.title == "Implementation Plan"
    assert art.request_feedback is True
    assert "# Plan" in art.content

    # List
    all_arts = mgr.list_artifacts()
    assert len(all_arts) == 1
    assert all_arts[0].filename == "plan.md"
