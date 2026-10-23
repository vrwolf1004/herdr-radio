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

## 개선 제안 (2026-10-23)

### 1. 방송 검색이 호스트를 차례로 기다림

- **현상**: `api_get` 은 호스트 3개를 순서대로 시도하고, 호스트마다 10초 제한을 둔다(`src/radio.py:68-72`, `:210`). 앞의 두 호스트가 응답하지 않으면 세 번째까지 가기 전에 최대 20초 동안 검색 결과 없이 기다린다. 마지막으로 성공한 호스트를 기억하지 않아 매번 같은 순서로 실패를 겪는다.
- **개선안**: 호스트 요청을 동시에 보내 먼저 응답한 결과를 쓰거나, 마지막으로 성공한 호스트를 먼저 시도한다. 제한 시간을 줄이는 것도 검토한다.
- **범위**: `src/radio.py` (`api_get`), `docs/usage.md`, `docs/usage.ko.md` (검색 설명)
- **확인**: 호스트 한 곳을 막아 두고 메뉴 검색 시간을 재서 줄어드는지 본다. 실행하지 않았다(확인 필요).
→ 완료: 마지막으로 응답한 호스트를 먼저 시도한다 (프로그램 안에서만 기억, 파일에 쓰지 않음).

### 2. 요청 User-Agent 의 버전이 manifest 와 다름

- **현상**: `USER_AGENT = "herdr-radio/0.2"` 이다(`src/radio.py:73`). `herdr-plugin.toml` 의 `version` 은 0.5.5 다. 버전을 코드에 따로 적어 두면 올릴 때 빠지기 쉽다.
- **개선안**: manifest 의 버전과 맞추거나, 버전을 한 곳에서 읽도록 한다.
- **범위**: `src/radio.py` (`USER_AGENT`)
- **확인**: 두 버전 문자열을 `grep` 으로 비교하고, 바꾼 뒤 `tests/test_radio.py` 를 실행한다.
→ 완료: User-Agent 버전을 PLUGIN_VERSION 상수로 두고, 테스트가 manifest 와 비교한다.

### 3. 검색 실패 메시지에 내부 예외 문구가 그대로 나옴

- **현상**: 모든 호스트가 실패하면 마지막 예외 객체를 `detail` 로 넣어 `RuntimeError` 를 낸다(`src/radio.py:212-214`). 예외 문구(예: HTTP 상태, SSL 오류)가 사용자 메시지에 그대로 붙는다.
- **개선안**: 사용자에게는 짧은 원인 분류(네트워크, 응답 형식)만 보이고, 원문은 로그 파일에 남긴다.
- **범위**: `src/radio.py` (`api_get`), `src/locales/*.json` (`error.radio_browser`)
- **확인**: 네트워크를 끊은 상태에서 검색해 메뉴에 나오는 문구를 본다. 실행하지 않았다(확인 필요).
