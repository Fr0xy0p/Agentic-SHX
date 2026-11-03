---
name: code-review
description: Comprehensive guidelines for reviewing pull requests, inspecting diffs, and checking style
---

# Code Review Skill

When performing a code review:
1. First run `git_diff` to inspect all uncommitted or staged changes.
2. Check for:
   - Logic correctness and boundary edge cases
   - Missing error handling or unhandled exceptions
   - Type hints consistency
   - Any sensitive secrets or credentials accidentally committed
3. Run `bash` with `pytest` to verify that existing test suites pass.
4. Output a structured markdown review containing:
   - Summary of Changes
   - Strengths
   - Critical Issues / Bugs
   - Minor Suggestions & Code Quality
