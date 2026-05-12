# Task Creation Prompt

이 프롬프트는 plan stage의 sub-agent가 사용하는 task/phase 파일 생성 규격이다.
`agents/04-plan.md`가 이 파일을 읽고 정확히 따라야 한다.

이전 stage들의 artifact가 컨텍스트에 존재한다고 가정하고, 직렬 phase 실행을 위한
task 파일들을 생성한다.

---

## 산출물 목록

1. `/tasks/index.json` (top-level task index 갱신/생성)
2. `/tasks/{id}-{name}/index.json` (task-level phase index)
3. `/tasks/{id}-{name}/phase0.md` (문서 업데이트 phase, 필수)
4. `/tasks/{id}-{name}/phase1.md ~ phaseN.md` (구현 phase들)

`docs-diff.md`는 **runner가 자동 생성**하므로 여기서 만들지 않는다.

---

## 0. task ID와 이름 결정

- 사용자가 지정하지 않았다면, `/tasks/index.json`의 `tasks` 배열에서 마지막 `id + 1`을 새 ID로 사용. 없으면 0.
- 이름은 kebab-case slug. 해당 task의 핵심 목적을 한 단어~두 단어로 표현.
- 디렉토리명: `{id}-{name}` (예: `0-mvp`, `1-auth`, `2-billing`)

## 1. `/tasks/index.json` (top-level task index)

이미 존재하면 `tasks` 배열에 새 항목 추가. 없으면 새로 생성.

```json
{
  "tasks": [
    {
      "id": 0,
      "name": "mvp",
      "dir": "0-mvp",
      "status": "pending",
      "created_at": "2026-05-04T02:00:00+0900"
    }
  ]
}
```

- `status`: 모든 phase 완료 시 `"completed"`, 하나라도 실패 시 `"error"`, 그 외 `"pending"`.
- `created_at`만 생성 시 기록. `completed_at`, `failed_at`은 `scripts/run_phases.py`가 자동 기록.
- 타임스탬프: ISO 8601 + KST `+0900`.

## 2. `/tasks/{id}-{name}/index.json` (task-level phase index)

```json
{
  "project": "<프로젝트명>",
  "task": "<task-name>",
  "prompt": "<사용자가 이 task 논의를 시작할 때 입력한 최초 프롬프트 원문>",
  "totalPhases": 5,
  "created_at": "2026-05-04T02:00:00+0900",
  "phases": [
    { "phase": 0, "name": "docs-update", "status": "pending" },
    { "phase": 1, "name": "data-model", "status": "pending" },
    { "phase": 2, "name": "api-handlers", "status": "pending" },
    { "phase": 3, "name": "web-ui", "status": "pending" },
    { "phase": 4, "name": "integration-test", "status": "pending" }
  ]
}
```

- `prompt`: 사용자가 해당 task 논의를 요청할 때 최초로 입력한 프롬프트 원문 (initial-plan stage의 `$INITIAL_BRIEF`).
- `name`은 kebab-case slug, 1~2단어.
- 모든 phase 초기 status는 `"pending"`.
- phase-level timestamp(`started_at`, `completed_at`, `failed_at`)는 runner가 자동 기록.

## 3. `/tasks/{id}-{name}/phase0.md` (문서 업데이트 — 필수)

phase 0는 **반드시 문서 업데이트**다. spec.md / architecture.md / ADR 등을 갱신한다.

빈 코드베이스에서 처음 시작하는 task라면 `docs/spec.md`, `docs/architecture.md` 등을
**새로 생성**하는 것도 phase 0의 일이다.

`docs-diff.md`는 phase 0 완료 후 `scripts/gen_docs_diff.py`가 자동 생성하므로
에이전트가 직접 만들지 않는다.

## 4. `/tasks/{id}-{name}/phase{N}.md` (각 phase마다 1개)

각 파일은 **독립 codex 세션이 이 파일 하나만 보고 작업을 완수할 수 있을 정도로**
자기완결적이어야 한다. phase 실행은 별도 codex 세션이 진행한다는 점을 명심.

### 필수 구조

```markdown
# Phase {N}: {Phase 이름}

## 사전 준비

먼저 아래 문서들을 반드시 읽고 프로젝트의 전체 아키텍처와 설계 의도를 완전히 이해하라:

- {관련 문서 경로 — spec.md, architecture.md, ADR 등}
- `/tasks/{id}-{name}/docs-diff.md` (이번 task의 문서 변경 기록)

그리고 이전 phase의 작업물을 반드시 확인하라:

- {이전 phase에서 생성/수정된 파일 경로}

이전 phase에서 만들어진 코드를 꼼꼼히 읽고, 설계 의도를 이해한 뒤 작업하라.

## 작업 내용

{구체적인 구현 지시. 파일 경로, 클래스/함수 시그니처, 로직 설명을 포함.
코드 스니펫은 인터페이스/시그니처 수준만 제시하고, 구현체는 codex에 맡겨라.
단, 설계 의도에서 벗어나면 안 되는 핵심 규칙은 명확히 박아넣어라.}

## Acceptance Criteria

{구체적인 검증 커맨드. 예:}
\`\`\`bash
pytest tests/foo/         # 모든 테스트 통과
ruff check src/foo/        # 린트 에러 없음
\`\`\`

## AC 검증 방법

위 AC 커맨드를 실행하라. 모두 통과하면 `/tasks/{id}-{name}/index.json`의 phase {N} status를 `"completed"`로 변경하라.
수정 3회 이상 시도해도 실패하면 status를 `"error"`로 변경하고, 에러 내용을 index.json의 해당 phase에 `"error_message"` 필드로 기록하라.

## 주의사항

- {이 phase에서 하지 말아야 할 것, 엣지 케이스, 호환성 주의사항}
- 기존 테스트를 깨뜨리지 마라.
```

### phase 파일 작성 원칙

1. **Phase 0 = 문서 업데이트**: 구현 phase 들어가기 전에 spec/architecture를 먼저 갱신한다.
2. **자기완결성**: "이전 대화에서 논의한 바와 같이" 같은 참조 절대 금지. 필요한 정보는 전부 파일 안에.
3. **사전 준비 필수**: 관련 문서 + `docs-diff.md` + 이전 phase 산출물 경로 명시.
4. **시그니처 수준 지시**: 함수/클래스 인터페이스만 제시. 내부 구현은 codex 재량. 단,
   핵심 비즈니스 규칙(멱등성, 보안, 데이터 무결성)은 반드시 명시.
5. **AC = 실행 가능 커맨드**: "동작해야 한다" 같은 추상 서술 금지. `pytest`, `npm test` 등 실행 가능 커맨드.
6. **scope 최소화**: 한 phase = 한 모듈/레이어. 여러 모듈 동시 수정 필요 시 쪼갠다.
7. **주의사항은 구체적으로**: "조심해라" 대신 "X를 하지 마라. 이유: Y" 형식.

---

## 실행 예시

```bash
# task 생성 후
python scripts/run_phases.py 0-mvp

# 특정 phase 에러 시: index.json 수정 후 재실행
# error phase의 status를 "pending"으로 변경
python scripts/run_phases.py 0-mvp
```

## scripts/run_phases.py 자동 동작

- 각 phase 파일 내용을 통째로 prompt에 임베딩하여 codex 서브세션 호출
- phase 0 완료 후 `scripts/gen_docs_diff.py`를 자동 호출해 `docs-diff.md` 생성
- 각 phase 완료 후 자동 커밋 (git 저장소인 경우):
  - `feat({task-name}): phase {N} — {phase-name}` (codex가 직접 커밋 안 한 변경분)
  - `chore({task-name}): phase {N} output + timestamps` (runner housekeeping)
- 스피너 + 진행상황 표시 (현재 phase / 전체 phase / 경과시간)
