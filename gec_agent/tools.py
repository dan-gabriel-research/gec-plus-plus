"""
Tool definitions available to the EI loop.
Extend this to add more grounding capabilities.
"""

import subprocess
import textwrap


def get_tool_definitions() -> list:
    return [
        {
            "name": "run_python",
            "description": (
                "Execute Python code and return output. "
                "Use for calculations, verification, data processing."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why you are running this code"
                    }
                },
                "required": ["code", "reason"]
            }
        },
        {
            "name": "read_file",
            "description": "Read the contents of a file by path.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "write_file",
            "description": "Write text content to a file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"},
                    "content": {"type": "string", "description": "Text to write"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "list_directory",
            "description": "List files in a directory.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                },
                "required": ["path"]
            }
        }
    ]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "run_python":
        return _run_python(inputs.get("code", ""))
    elif name == "read_file":
        return _read_file(inputs.get("path", ""))
    elif name == "write_file":
        return _write_file(inputs.get("path", ""), inputs.get("content", ""))
    elif name == "list_directory":
        return _list_directory(inputs.get("path", "."))
    return f"Unknown tool: {name}"


def _run_python(code: str) -> str:
    try:
        result = subprocess.run(
            ["python3", "-c", textwrap.dedent(code)],
            capture_output=True, text=True, timeout=15
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if err:
            out += f"\n[stderr] {err}"
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timed out after 15 seconds"
    except Exception as e:
        return f"Error: {e}"


def _read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading '{path}': {e}"


def _write_file(path: str, content: str) -> str:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to '{path}'"
    except Exception as e:
        return f"Error writing '{path}': {e}"


def _list_directory(path: str) -> str:
    import os
    try:
        entries = os.listdir(path)
        return "\n".join(sorted(entries)) or "(empty)"
    except Exception as e:
        return f"Error listing '{path}': {e}"
