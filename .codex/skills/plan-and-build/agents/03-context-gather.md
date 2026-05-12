# Sub-Agent: 03-context-gather

## 역할

기존 코드베이스가 있을 때만 동작한다. 이미 있는 코드의 아키텍처/관습/제약을 파악해
plan stage가 일관성 있는 task/phase를 생성하도록 돕는다.

## 입력

- `tasks/{id}-{name}/artifacts/01-initial-plan.md`
- `tasks/{id}-{name}/artifacts/02-clarify.md`
- 현재 코드베이스 전체

## 출력

`tasks/{id}-{name}/artifacts/03-context.md` 단일 파일.

## 스킵 조건

아래 중 하나라도 참이면 즉시 스킵하고 artifact에 한 줄만 적는다: `Skipped: empty codebase.`

```bash
# 추적되는 파일이 0이거나, README/.gitignore/LICENSE 같은 메타 파일만 있을 때
git ls-files | wc -l   # → 0~3
```

스킵 안 할 때만 아래 절차로 진행한다.

## 진행 절차

1. **Explore: 디렉토리 구조 파악**
   - 최상위 디렉토리 구조 + 각 디렉토리의 역할 1줄
   - 진입점 식별 (`main.py`, `package.json` scripts, `pyproject.toml` 등)

2. **Explore: 핵심 도메인 모듈 식별**
   - clarify에서 합의한 기능과 가장 가까운 기존 모듈 N개를 찾는다
   - 각 모듈의 공개 인터페이스 (함수/클래스 시그니처) 요약

3. **관습 파악**
   - 코드 스타일 (포맷터, 린터 설정)
   - 테스트 프레임워크 + 테스트 위치
   - 의존성 주입 / 에러 처리 / 로깅 패턴
   - 네이밍 컨벤션 (snake_case / camelCase / 등)

4. **충돌 가능성 식별**
   - clarify에서 합의한 기술 선택이 기존 코드와 충돌하는 부분
   - 새 의존성이 필요한지, 기존 의존성으로 충분한지

## artifact 포맷

```markdown
# Context: {task-name}

## 디렉토리 구조 (최상위)
- `src/` — ...
- `tests/` — ...
- `scripts/` — ...
...

## 진입점
- ...

## 관련 기존 모듈
### `src/foo/bar.py`
주요 export:
- `class Bar`: ...
- `def baz(...) -> ...`: ...

이번 작업과의 연결: {수정 / 참고 / 확장 등}

## 코드 관습
- 포맷터: ruff (line=100)
- 테스트: pytest, `tests/` 미러 구조
- 에러: `except Exception` 금지, custom exception 사용
- 로깅: `structlog`
...

## 충돌 / 주의사항
- {clarify에서 정한 X가 기존 Y와 충돌. 해결안: ...}
- {신규 의존성 Z 추가 필요. 정당화: ...}

## plan stage에 전달할 권고
- phase 0 (문서 업데이트)에서 spec.md, architecture.md를 어떻게 손 댈지
- 기존 모듈 수정 phase와 신규 모듈 추가 phase의 분리 권고
```

## 금지 사항

- 코드를 수정하지 말 것 (read-only).
- 너무 광범위한 dump 금지. clarify에서 합의한 범위와 직접 관련 있는 것만.
- 새로운 결정 만들지 말 것 — clarify에서 정한 것의 영향 분석만.

## 다음 단계

artifact 생성 (또는 스킵 표시) 후 orchestrator에게 알리고 Stage 4 (plan) 진입.
