# 구조 및 동작 방식

herdr-radio는 재생을 담당하는 mpv 프로세스와, 상태를 사이드바에 올리는 host 루프로 나뉩니다. 두 부분은 파일과 프로세스 이름으로만 연결되어 있어서, 액션 프로세스와 host 프로세스가 서로 직접 통신하지 않습니다.

## 프로세스

```text
startup / workspace.created hook ── ensure ──┬─ detached host (pane 밖, host.log)
                                             │   └─ 1초마다 heartbeat, 매초 $rd_now/$rd_state 토큰 갱신
                                             │      5초마다 재생 상태 확인, agent 재등록, 맨 아래 위치 확인
                                             └─ herdr-dock 의 radio pane: menu (목록)

start / stop / menu / play-N action ─────────── 목록 pane 과 같은 명령을 실행

play ── detached mpv (--title=herdr-radio) ── pane 과 무관하게 계속 재생
```

- 재생은 host의 자식이 아닙니다. `DETACHED_PROCESS`(Windows) 또는 `start_new_session`(Unix)으로 분리합니다. 그래서 pane을 닫아도 소리가 이어집니다.
- host도 pane 밖의 분리 프로세스입니다. Windows에서는 `CREATE_NO_WINDOW`로 띄워 콘솔 창을 만들지 않고, stderr는 상태 폴더의 `host.log`에 남깁니다. 예전에는 `DEVNULL`로 버려서 host가 왜 죽는지 알 수 없었습니다.
- Windows에서 host가 실행하는 보조 프로세스(`powershell`, `tasklist`, `taskkill`)와 herdr CLI 호출에도 `CREATE_NO_WINDOW`를 붙입니다. 이것이 없으면 5초마다 터미널 창이 뜨고 꺼집니다.
- host가 죽으면 토큰 ttl(15초)이 지나 사이드바 값이 사라집니다. 재생 자체는 멈추지 않습니다.
- hook은 heartbeat가 10초 안에 갱신됐으면 아무것도 하지 않습니다.

## dock 공유

`herdr-dock`은 feedbag과 같은 공용 workspace입니다. 규칙은 feedbag의 `architecture.md` "herdr-dock 공용 규칙"을 따릅니다.

1. `herdr-dock`을 찾고, 없으면 `workspace create --no-focus`로 만듭니다.
2. 빈 pane(라벨·토큰·agent 없음)이 있으면 쓰고, 없으면 `pane split --direction down`으로 나눕니다.
3. `pane.report_agent`로 `radio` 가짜 agent를 등록합니다. 같은 pane에서 `menu`를 실행해 방송국 목록을 보여 줍니다.
4. 5초마다 `workspace.move`로 dock을 맨 뒤에 둡니다. feedbag도 같은 일을 하므로 누가 먼저 해도 결과는 같습니다.

## 재생 상태 판단

`is_playing`은 상태 파일을 믿지 않고 플레이어 프로세스를 직접 찾습니다.

| 플랫폼 | 찾는 방법 |
| --- | --- |
| Windows | PowerShell `Get-CimInstance Win32_Process`로 `mpv.exe`/`ffplay.exe` 중 명령줄에 `herdr-radio`가 들어간 것 |
| Linux/macOS | `pgrep -f herdr-radio` |

플레이어 창 제목(`--title=herdr-radio`, `-window_title herdr-radio`)이 표식입니다. `player.pid` 파일은 보조 수단이고, 상태 폴더가 어긋나도 프로세스로 찾을 수 있게 했습니다.

## 상태 파일

`HERDR_PLUGIN_STATE_DIR` 아래(없으면 `%LOCALAPPDATA%\herdr\plugins\herdr-radio`)에 둡니다. 설정 폴더는 `HERDR_PLUGIN_CONFIG_DIR`이고, 없으면 `%APPDATA%\herdr\plugins\config\herdr-radio`를 봅니다.

| 파일 | 내용 |
| --- | --- |
| `workspace.id`, `pane.id` | dock workspace와 host pane |
| `heartbeat` | host 생존 확인 시각 |
| `starting` | ensure 중복 실행 방지 |
| `host.log` | host의 stderr. 오류가 여기에 남습니다 |
| `player.pid` | 마지막으로 띄운 플레이어 pid (보조) |
| `station.json` | 마지막 방송 이름과 URL. `start`가 같은 방송을 다시 틉니다 |

방송 목록은 상태 폴더가 아니라 설정 폴더(`HERDR_PLUGIN_CONFIG_DIR`)의 `config.json`입니다.

## 파일

| 파일 | 역할 |
| --- | --- |
| `src/radio.py` | 명령(ensure, host, start, stop, menu, status, play), host 루프, Radio Browser 검색, 재생 |
| `src/herdr_api.py` | herdr CLI와 socket 호출. feedbag의 파일을 가져온 사본입니다 |
| `config.example.json` | 방송국 설정 예시 |
| `herdr-plugin.toml` | 플랫폼별 startup, hook, 액션, pane 선언 |

## 새 방송국 액션 추가

`play-N` 액션은 `herdr-plugin.toml`에 Windows와 Linux/macOS 항목을 한 쌍씩 둡니다. 번호는 1~6까지 있습니다. 6개를 넘기려면 두 항목을 같은 형식으로 추가하고, `cmd_play`의 범위는 `config.json` 길이로 정해지므로 코드는 고치지 않아도 됩니다.
