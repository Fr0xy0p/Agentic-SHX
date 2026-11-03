"""Unit tests for SessionManager and transcript logging."""

import json
from pathlib import Path
from agentic_shx.session.manager import SessionManager, SessionEvent

def test_session_manager_creation_and_logging(tmp_path):
    sm = SessionManager(session_id="test-session-1", base_dir=tmp_path)
    assert sm.session_id == "test-session-1"

    # Log events
    sm.log_event("USER_INPUT", "Hello agent")
    sm.log_event("MODEL_OUTPUT", "Hello user", {"tokens": 10})
    sm.set_title_from_prompt("Hello agent test prompt")

    events = sm.load_events()
    assert len(events) == 2
    assert events[0].type == "USER_INPUT"
    assert events[0].content == "Hello agent"
    assert events[1].type == "MODEL_OUTPUT"
    assert events[1].metadata["tokens"] == 10

    # Check session listing
    all_sessions = SessionManager.list_all_sessions(base_dir=tmp_path)
    assert len(all_sessions) == 1
    assert all_sessions[0]["id"] == "test-session-1"
    assert "Hello agent" in all_sessions[0]["title"]

