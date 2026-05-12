"""codex exec 헤드리스 세션 래퍼.

각 세션은 (a) system prompt 템플릿 파일과 (b) task prompt 문자열을 받아
subprocess로 Codex CLI를 실행하고, 지정된 출력 경로의 frontmatter를 파싱해 반환한다.

CLI 플래그가 버전에 따라 다를 수 있어 상단 상수로 뽑아두었다. 환경에 맞춰 조정.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


import os as _os
import shlex as _shlex
import shutil as _shutil

# __file__ = <repo>/.codex/skills/persuasion-review/scripts/session_runner.py
# -> parents[4] = <repo>
REPO_ROOT = Path(__file__).resolve().parents[4]

CODEX_BIN = _os.environ.get("CODEX_BIN") or _shutil.which("codex") or "codex"
CODEX_MODEL = _os.environ.get("CODEX_MODEL")
CODEX_PERMISSION_FLAGS = _shlex.split(_os.environ.get(
    "CODEX_PERMISSION_FLAGS",
    "--dangerously-bypass-approvals-and-sandbox",
))


@dataclass
class SessionResult:
    output_path: Path
    frontmatter: dict
    body: str
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""

    @property
    def decision(self) -> str:
        return str(self.frontmatter.get("decision", "error"))

    @property
    def confidence(self) -> int:
        try:
            return int(self.frontmatter.get("confidence", 0))
        except (TypeError, ValueError):
            return 0

    @property
    def ok(self) -> bool:
        return self.error is None


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Markdown 문자열에서 --- 로 감싼 YAML frontmatter를 추출."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, text
    return meta, parts[2].lstrip("\n")


DEFAULT_ALLOWED_TOOLS = ("Read", "Write")


def run_session(
    *,
    system_prompt_path: Path,
    task_prompt: str,
    output_path: Path,
    timeout_sec: int = 600,
    allowed_tools: tuple[str, ...] = DEFAULT_ALLOWED_TOOLS,
) -> SessionResult:
    """codex headless 세션을 1회 실행하고 결과 파일을 파싱해 반환.

    allowed_tools: 원본 prompt의 도구 제약을 Codex 호환 안내로 전달한다.
    """
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_msg_file = tempfile.NamedTemporaryFile(
        prefix="persuasion-review-",
        suffix="-last-message.txt",
        delete=False,
    )
    last_msg_path = Path(last_msg_file.name)
    last_msg_file.close()

    full_prompt = f"""{system_prompt}

---

# Codex compatibility

The source prompt was ported from an older tool format. Interpret tool names this way:

- Read: inspect local files.
- Write: create or replace exactly the requested output file.
- Bash: run shell commands only when the prompt explicitly allows it.

Allowed tool classes for this session: {", ".join(allowed_tools)}.
If you cannot write the requested output file directly, return the complete
markdown file content as your final answer.

---

# Task

{task_prompt}
"""

    cmd = [
        CODEX_BIN,
        "exec",
        "--skip-git-repo-check",
        *CODEX_PERMISSION_FLAGS,
    ]
    if CODEX_MODEL:
        cmd.extend(["--model", CODEX_MODEL])
    cmd.extend([
        "--output-last-message", str(last_msg_path),
        full_prompt,
    ])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired as exc:
        return SessionResult(
            output_path=output_path,
            frontmatter={"decision": "error", "confidence": 0},
            body="",
            error=f"timeout after {timeout_sec}s",
            stdout=(exc.stdout or ""),
            stderr=(exc.stderr or ""),
        )
    except FileNotFoundError:
        return SessionResult(
            output_path=output_path,
            frontmatter={"decision": "error", "confidence": 0},
            body="",
            error=f"'{CODEX_BIN}' 바이너리를 찾을 수 없음. PATH 확인.",
        )

    if proc.returncode != 0:
        return SessionResult(
            output_path=output_path,
            frontmatter={"decision": "error", "confidence": 0},
            body="",
            error=f"subprocess failed (code {proc.returncode})",
            stdout=proc.stdout[-2000:],
            stderr=proc.stderr[-2000:],
        )

    if not output_path.exists():
        last_message = (
            last_msg_path.read_text(encoding="utf-8")
            if last_msg_path.exists()
            else ""
        )
        if last_message.lstrip().startswith("---"):
            output_path.write_text(last_message, encoding="utf-8")

    if not output_path.exists():
        return SessionResult(
            output_path=output_path,
            frontmatter={"decision": "error", "confidence": 0},
            body="",
            error="output file not created by session",
            stdout=proc.stdout[-2000:],
            stderr=proc.stderr[-2000:],
        )

    content = output_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    return SessionResult(
        output_path=output_path,
        frontmatter=fm,
        body=body,
        stdout=proc.stdout[-2000:],
        stderr=proc.stderr[-2000:],
    )
