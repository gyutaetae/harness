---
name: plan-and-build
description: >-
  Codex 기반 자율 구현 하네스. 사용자의 요구를 받아 초기기획 → clarify(9단계) →
  context-gather → plan(task/phase 분해) → generate(codex 직렬 실행) → evaluate
  파이프라인을 단계별 sub-agent로 실행한다. 각 단계는 전용 prompt 파일을 따르며
  결과를 artifact 파일로 다음 단계에 전달한다. 사용자가 "하네스 시작",
  "plan-and-build", "task 만들어줘", "phase 실행" 등을 말할 때 사용한다.
disable-model-invocation: true
---

# plan-and-build

Codex CLI 기반 자율 구현 하네스의 메인 orchestrator. 모든 sub-agent prompt와 artifact는
파일 시스템을 통해 전달된다.

## 핵심 원칙

1. **단계별 sub-agent**: 각 stage는 `agents/0N-*.md`의 prompt를 따르는 별도 sub-agent로 동작한다.
   orchestrator는 stage 진입 시 해당 파일을 읽고 그 페르소나/지시를 채택한다.
2. **artifact 기반 전달**: 모든 stage 출력은 `tasks/{id}-{name}/artifacts/0N-*.md`에 저장한다.
   다음 stage는 이전 artifact를 반드시 읽고 시작한다.
3. **사용자 프롬프트 자동 기록**: clarify 9단계 동안 사용자가 입력한 모든 프롬프트 원문을
   `tasks/{id}-{name}/prompts/clarify/0N-*.md`에 즉시 저장한다.
4. **로컬 CLI 우선**: 모든 구현은 로컬 CLI만으로 가능해야 한다. 사용자 개입이 불가피한 지점은
   `docs/user-intervention.md`에 명시한다.
5. **brand-new repo 친화**: context-gather와 evaluate는 코드베이스 상황에 따라 스킵 가능하다.

## 디렉토리 규약

```
.codex/skills/plan-and-build/
  SKILL.md                  ← 본 파일
  agents/
    01-initial-plan.md      ← 초기기획 sub-agent
    02-clarify.md           ← clarify 9단계 sub-agent
    03-context-gather.md    ← context gather sub-agent
    04-plan.md              ← task/phase 생성 sub-agent
    05-evaluate.md          ← MVP 후 평가 sub-agent

prompts/
  task-created.md           ← task/phase 파일 생성 규격 (plan stage가 따름)

scripts/
  run_phases.py             ← codex 직렬 실행 runner
  gen_docs_diff.py          ← phase 0 후 docs-diff.md 생성
  _utils.py                 ← 공용 유틸

tasks/
  index.json                ← 전체 task 목록
  {id}-{name}/
    index.json              ← 이 task의 phase 목록
    artifacts/
      01-initial-plan.md
      02-clarify.md
      03-context.md         ← (있을 경우)
      05-evaluate.md        ← (있을 경우)
    prompts/
      clarify/
        01-feasibility.md   ← clarify 9단계 사용자 프롬프트 원문
        02-tech-stack.md
        ... 09-final-doc.md
    phase0.md
    phase1.md ... phaseN.md
    phase{N}-output.json    ← runner가 저장하는 codex 출력
    docs-diff.md            ← phase 0 후 자동 생성
```

## 파이프라인 (5 + 1 stages)

진입 시 사용자 입력 한 줄 요구를 `$INITIAL_BRIEF`로 두고 아래 순서를 따른다.
각 stage 종료 시 artifact가 디스크에 존재하는지 검증한 뒤 다음 stage로 넘어간다.

### Stage 1. 초기기획 (initial-plan)

`agents/01-initial-plan.md`를 읽고 그 지시대로 진행한다. 사용자와 대화하며 4가지를 확정한다:
요구사항 / 구현 디테일 / 제약 조건 / 완료 기준.

산출물: `tasks/{id}-{name}/artifacts/01-initial-plan.md`

이 stage가 끝나면 task ID와 name이 결정되어야 한다 (kebab-case slug).

### Stage 2. clarify

`agents/02-clarify.md`를 읽고 9개 sub-step을 순서대로 진행한다:

1. 구현가능성 검증 (feasibility)
2. 기술스택 선정 (tech-stack)
3. 사용흐름 점검 (user-flow)
4. 화면 설계 (ui-design)
5. API 설계 (api-design)
6. 데이터 설계 (data-design)
7. 코드아키텍처 설계 (architecture)
8. 기술적 결정사항 점검 (tech-decisions)
9. 최종문서 생성에 대한 논의점 (final-doc)

**자동 기록 의무**: 각 sub-step 시작 시 사용자에게 질문하고, 사용자의 응답을
받자마자 그 원문을 `tasks/{id}-{name}/prompts/clarify/{NN}-{slug}.md`에 즉시
저장한다(요약/수정 금지).

산출물: `tasks/{id}-{name}/artifacts/02-clarify.md` (9단계 합의 결과 요약)
+ `tasks/{id}-{name}/prompts/clarify/01~09-*.md` (사용자 프롬프트 원문)

### Stage 3. context-gather (옵션)

빈 코드베이스이면 **스킵**. 코드베이스 판정:

```
git ls-files | wc -l   → 0 또는 README/설정 파일만 있으면 빈 코드베이스
```

스킵 시 `tasks/{id}-{name}/artifacts/03-context.md`에 한 줄만 적는다:
`Skipped: empty codebase.`

스킵 안 할 시 `agents/03-context-gather.md` 지시에 따라 explore 한 후 artifact 생성.

### Stage 4. plan

`agents/04-plan.md`를 읽고, 추가로 `prompts/task-created.md`의 규격을 정확히 숙지한다.
이전 artifact 3개를 모두 input으로 받아 task/phase 파일을 생성한다.

산출물:
- `tasks/index.json` 업데이트
- `tasks/{id}-{name}/index.json`
- `tasks/{id}-{name}/phase0.md` (문서 업데이트 phase)
- `tasks/{id}-{name}/phase1.md ~ phaseN.md` (구현 phase)

### Stage 5. generate

`scripts/run_phases.py {task-dir}`를 실행한다. orchestrator가 직접 코드를 작성하지 않는다.
runner는 각 phase를 독립 codex 세션으로 직렬 실행한다.

```bash
python scripts/run_phases.py {id}-{name}
```

실패 시 runner가 종료한다. 사용자에게 실패한 phase의 `index.json` status를 `pending`으로
되돌리고 재실행하라고 안내한다.

### Stage 6. evaluate (옵션)

간단한 MVP면 **스킵**. 스킵 판정 기준은 `agents/01-initial-plan.md`에서 사용자가 명시한
"완료 기준"을 본다 — 단순 동작 확인 수준이면 스킵.

스킵 안 할 시 `agents/05-evaluate.md`를 따른다. 산출물:
`tasks/{id}-{name}/artifacts/05-evaluate.md`

## Sub-agent 호출 방식

orchestrator(이 SKILL.md를 따르는 IDE 세션)는 각 stage 진입 시:

1. 해당 `agents/0N-*.md` 파일을 Read 도구로 읽는다.
2. 그 파일이 정의하는 페르소나/입력/출력 스펙을 채택한다.
3. 입력으로 명시된 이전 artifact들을 모두 Read 한다.
4. stage 작업을 수행한다 (사용자 인터랙션 또는 분석).
5. 명시된 artifact를 Write 한다.
6. artifact 존재 검증 후 다음 stage로.

**plan stage**의 task/phase 파일 생성은 가능하면 별도 codex 서브세션으로 위임할 수 있지만,
필수는 아니다. orchestrator가 직접 작성해도 무방하다.
**generate stage**는 항상 `scripts/run_phases.py` subprocess로만 실행한다 (orchestrator가
구현 코드를 절대 직접 작성하지 않는다).

## 시작 트리거

사용자 입력 예시:
- "하네스 시작: <요구사항>"
- "plan-and-build: <요구사항>"
- "이거 만들어줘: <요구사항>"

이때 orchestrator는 즉시 Stage 1 (`agents/01-initial-plan.md`)로 진입한다.

## 재진입 / 부분 실행

사용자가 특정 stage만 다시 하길 원하면:
- "clarify 다시" → Stage 2부터 재실행, 기존 artifact는 백업 후 덮어씀
- "phase 재실행" → `python scripts/run_phases.py {id}-{name}` 만 호출
- "task 만들기만 해줘" → Stage 4까지만 실행, generate는 사용자가 직접

## 중요 규칙

- artifact 파일을 절대 건너뛰지 말 것. 모든 stage는 명시된 artifact를 생성해야 한다.
- clarify 사용자 프롬프트는 받자마자 즉시 저장 (대화 종료 후 모아서 저장 금지).
- task ID는 `tasks/index.json`의 마지막 ID + 1. 처음이면 0.
- task name은 kebab-case slug, 1~2단어.
- 모든 timestamp는 ISO 8601 + KST (`+0900`).
