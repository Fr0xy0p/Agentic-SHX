"""Tool to create and update artifacts."""

from typing import Optional, Dict, Any
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.artifacts.manager import ArtifactManager

class CreateArtifactTool(BaseTool):
    """Tool to create structured markdown documents and plans."""

    name = "create_artifact"
    description = (
        "Create or update a structured Markdown artifact (e.g. implementation plan, design doc, "
        "investigation report, or changelog). Set request_feedback=True if you require user approval before proceeding."
    )
    parameters = {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Basename of the artifact file (e.g. 'implementation_plan.md', 'architecture.md')."
            },
            "title": {
                "type": "string",
                "description": "Human-readable title of the document."
            },
            "content": {
                "type": "string",
                "description": "Full Markdown content."
            },
            "summary": {
                "type": "string",
                "description": "Short multi-line summary of what this document covers."
            },
            "request_feedback": {
                "type": "boolean",
                "description": "Whether to request explicit user feedback or approval before executing the contents."
            }
        },
        "required": ["filename", "title", "content"]
    }

    def __init__(self, manager: ArtifactManager):
        self.manager = manager

    def execute(
        self,
        filename: str,
        title: str,
        content: str,
        summary: str = "",
        request_feedback: bool = False,
        **kwargs
    ) -> ToolResult:
        try:
            art = self.manager.save_artifact(
                filename=filename,
                title=title,
                content=content,
                summary=summary,
                request_feedback=request_feedback
            )
            return ToolResult(
                success=True,
                output=f"Artifact '{art.title}' saved to {art.path} (request_feedback={request_feedback})",
                metadata={"artifact_path": str(art.path), "request_feedback": request_feedback}
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to create artifact: {str(e)}")

