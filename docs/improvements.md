# 개선 문서

- 작성 기준: 2026-10-22, 커밋 `875782b` (`git log -1 --format=%h`)
- 공용 도크 모듈: `src/dock_layout.py` 는 복사본. `load_dock_layout()`(`src/radio.py:36`)이 설치된 herdr-dock-grid 원본을 먼저 찾고, 없으면 이 복사본을 쓴다. 복사본은 herdr-dock-grid 0.7.1 원본과 내용이 같다(diff 확인).
- 할 일 목록: [todo.md](todo.md). 이미 적힌 항목은 옮기지 않고 거기서 관리한다.
- 표기: "확인됨" = 현재 코드에서 직접 본 내용. "확인 필요" = 코드로 추정만 했고 실행해 보지 않음.

## 개선 항목

- **[중간] 공용 herdr CLI 호출에 시간 제한이 없음** (확인 필요)
  - 근거: `src/herdr_api.py:42`(`cli()`), `src/herdr_api.py:140`(`installed_plugin_path()`)
  - herdr 가 응답하지 않으면 호출이 끝나지 않는다. 고칠 때는 herdr-dock-grid 원본을 먼저 바꾸고 복사본을 맞춘다(공용 모듈 규칙).

- **[낮음] `winget install` 에 대기 상한이 없음** (확인 필요)
  - 근거: `src/radio.py:999-1008`(`install_player()`, 실행은 `:1005`)
  - 콘솔 창을 숨기지 않는 것은 의도다(설치 진행이 pane 에 보이도록). 대신 설치가 멈추면 명령이 계속 기다린다. 대기 시간 안내 문구를 넣거나 설치 방법을 README 에 적는 정도로 충분할지 정한다.

- **[낮음] 저장소에 CI가 없음** (확인됨)
  - 근거: 저장소 루트에 `.github/` 가 없다. herdr-stockpulse 의 `.github/workflows/test.yml` 을 참고할 수 있다.

## 관련 기존 항목 (todo.md)

- 저장 PID 재사용 방지: [todo.md](todo.md) 의 "테스트" 절
- `stop` 으로 블록 제거, 재생 정리 확인: [todo.md](todo.md) 의 "실행 확인에서 찾은 개선점" 절
- 2x2 배치 공용화: [todo.md](todo.md) 의 "공용 dock" 절
