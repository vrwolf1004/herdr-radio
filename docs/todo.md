# TODO

개선할 점 목록입니다. 위에 있을수록 먼저 할 일입니다. 코드를 읽어 찾은 항목이라 실행으로 확인하지 않은 것은 "확인 필요"로 표시했습니다.

## 버그 (확인 필요)

- [x] **Linux/macOS에서 host를 재생 중으로 오인할 수 있음**
  - `is_playing`과 `stop`이 `pgrep -f herdr-radio`를 씁니다.
  - host 프로세스의 명령줄에는 `--state .../herdr/plugins/herdr-radio`가 들어 있어서 매치될 수 있습니다.
  - 결과: 재생하지 않아도 `▶ 재생 중`으로 보이고, `stop`이 host 프로세스에 SIGTERM을 보내 블록이 사라질 수 있습니다.
  - 고칠 방향: 플레이어 이름(`mpv`, `ffplay`)으로 먼저 거르고, 마커는 `--title`처럼 플레이어 인자에만 씁니다. Windows 쪽 필터와 맞춥니다.
  - 확인 방법: Linux 또는 macOS에서 `start` 후 `stop`을 실행해 host가 살아 있는지 봅니다.

- [x] **검색 응답 오류가 메뉴를 멈춤**
  - `api_get`은 `OSError`만 잡습니다. 응답이 JSON이 아니면 `json.load`가 `ValueError`를 던지고, `menu`의 `RuntimeError` 처리에 걸리지 않아 pane이 종료됩니다.
  - 고칠 방향: `ValueError`도 잡아 다음 서버로 넘기거나 `RuntimeError`로 바꿉니다.

- [x] **config.json 형식 오류에 약함**
  - `load_stations`는 `item.get`을 가정합니다. 항목이 문자열이거나 `stations`가 목록이 아니면 예외가 납니다.
  - 고칠 방향: 타입을 확인하고, 잘못된 항목은 건너뛰면서 `menu`에 경고를 한 줄 보여 줍니다.

## 성능

- [x] **Windows에서 5초마다 PowerShell을 띄움**
  - 처리: pid 파일의 프로세스는 `OpenProcess`로 확인하고(3ms), 검색은 pid 파일이 없을 때만 30초에 한 번 합니다.
  - `is_playing`은 `player_pids`를 호출하고, 그때마다 `powershell -Command`를 실행합니다. 콘솔 창이 깜빡이거나 1초 가까이 걸릴 수 있습니다.
  - 고칠 방향: `tasklist /FI "IMAGENAME eq mpv.exe" /FO CSV /NH`처럼 가벼운 명령을 쓰거나, 플레이어 pid를 `player.pid`에 기록하고 `OpenProcess`로 살아 있는지만 확인합니다.
  - 측정 방법: `Measure-Command { python src/radio.py status }`로 소요 시간을 잽니다.

- [x] **조회와 재생 확인을 같은 루프에서 처리**
  - 처리: 재생 확인과 agent 등록은 워커 스레드가 맡고, 1초 루프는 heartbeat와 토큰 갱신만 합니다.
  - host 루프에서 `search`는 쓰지 않지만, 재생 상태 확인과 `workspace.list`/`pane.list` 호출이 1초 루프 안에 있습니다. 사용량 블록 개발 때 확인된 "루프가 멈추면 애니메이션이 멈춤"과 같은 문제입니다.
  - 고칠 방향: 프로세스 확인을 5초 주기에서 스레드로 옮깁니다.

## 기능

- [x] **방송국 추가 메뉴 항목**: 검색 결과에서 방송국을 `config.json`에 저장하는 옵션을 둡니다. 지금은 URL을 손으로 옮겨야 합니다.
- [x] **볼륨 조절**: mpv는 IPC 소켓이나 `--input-ipc-server`로 볼륨을 바꿀 수 있습니다. 액션 `volume-up`, `volume-down`을 추가합니다. ffplay는 지원하지 않으므로 mpv 전용으로 명시합니다.
- [x] **재생 실패 감지**: 플레이어가 바로 종료되면 `station.json`은 그대로이고 사이드바에는 `정지`로 보입니다. 실패 이유(스트림 끊김, 404)를 `$rd_state`에 `✖ 실패`처럼 구분해 올립니다.
- [x] **다음/이전 방송 액션**: `station.json`과 `config.json` 순서를 써서 이동합니다.
- [x] **검색 결과 캐시**: 같은 키워드는 10분 동안 상태 폴더의 `search-cache.json`에서 읽습니다 (`cached_search`).

## 문서, 배포

- [ ] **라이선스 정하기**: README가 "미정"입니다. `herdr_api.py`가 MIT 코드를 가져왔으므로 MIT 등 호환되는 라이선스를 정하고 `LICENSE` 파일을 추가합니다.
- [x] **`.gitattributes` 추가**: 커밋마다 줄바꿈 경고가 납니다. `* text=auto eol=lf`를 넣습니다. feedbag 저장소의 같은 항목과 맞춥니다.
- [x] **버전 올리기**: 현재 `herdr-plugin.toml`의 `version`은 0.4.0입니다.
- [x] **README에 `docs/` 링크 추가**: 설치 방법은 README, 설정과 사용법은 `docs/usage.md`(영문)와 `docs/usage.ko.md`(한국어)로 나눕니다.
- [x] **GitHub 저장소 설정**: topic `herdr-plugin`과 설명이 이미 있는 것을 GitHub API로 확인했습니다.

## 공용 dock (herdr-dock)

- [ ] **dock 코드 중복 정리**: `find_workspace`, `ensure_workspace`, `keep_at_bottom`이 feedbag과 거의 같습니다. feedbag의 todo "dock 규칙 정리"와 함께 공용 모듈로 빼는 방안을 검토합니다. 두 플러그인 모두 `herdr_api.py`를 복사해 쓰고 있으므로 같이 정리합니다.
- [x] **radio 블록이 맨 아래에 있지 않을 때**: feedbag이 없으면 `keep_at_bottom`만 믿어야 합니다. feedbag todo의 "다른 블록만 있을 때 순서"와 같은 문제입니다.
  - 처리: radio 워커가 5초마다 `keep_at_bottom`을 호출합니다. dock을 맨 위로 옮긴 뒤 8초 만에 맨 아래로 돌아오는 것을 확인했습니다.

## 테스트

- [x] **프로세스 탐색을 실행 파일 기준으로 제한하고 시간 제한 추가** (`PLAYER_PATTERNS`는 mpv·ffplay 실행 파일과 마커 인자만 맞추고, 모든 외부 명령에 5초 제한을 둠. `tests/test_radio.py`)
  - Unix `pgrep -f`는 명령행 문자열만으로 다른 프로세스를 찾을 수 있고, OS별 탐색 명령에 명시적 timeout이 없다. 실행 파일 식별과 시간 초과 테스트를 추가한다.
- [ ] **저장 PID의 프로세스 재사용 방지 (확인 필요)**
  - PID가 재사용되면 다른 프로세스를 재생 중으로 오인하거나 중지할 수 있다. 실행 파일/명령 식별을 함께 저장하는 방안을 재현 테스트 후 결정한다.

- [x] **테스트 디렉터리 만들기**: `tests/test_radio.py` 15개 (short_name, pick_pane, 방송국 목록, 검색 응답, 플레이어 패턴, 제한 시간, 검색 캐시).
  - `short_name`: 긴 이름이 `NAME_WIDTH`에서 잘리고 `…`이 붙는지
  - `pick_pane`: 기억한 pane이 살아 있으면 그것을, 아니면 라벨·토큰이 없는 빈 pane을 고르는지
  - `load_stations`: 빈 url을 건너뛰고 name이 없으면 url을 쓰는지
  - `search` 응답 처리: 빈 `url_resolved`를 `url`로 대체하는지 (HTTP는 가짜 응답으로 막습니다)

## 실행 확인에서 찾은 개선점 (2026-10-21)

- [x] **ensure 가 heartbeat 만 보고 일찍 끝남** (pane 이 있는지도 확인하도록 고쳤다. `PaneAliveTest`. 살아 있는 블록에 다시 실행해도 pane 이 늘지 않음을 확인했다): `cmd_ensure`는 heartbeat 가 살아 있으면 바로 끝난다. pane 을 닫은 뒤 10초 안에 다시 실행하면 블록이 올라오지 않았다. 고칠 방향: pane 이 실제로 있는지도 확인하고, host 가 끝날 때 heartbeat 를 지운다. 확인: pane 을 닫고 바로 `ensure` 를 실행.
- [ ] **블록을 빼는 명령이 없음**: `stop` 은 재생만 멈추고 블록은 그대로 둔다. 블록 제거 명령을 추가할지 정한다.
- [ ] **pane 을 닫을 때 재생 정리 확인 필요**: host 가 끝나도 mpv 가 남는지 확인하고, 남으면 정리 방법을 정한다.
