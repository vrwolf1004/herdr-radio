# 사용법

herdr-radio는 방송국을 화면 없이 재생하고, 재생 상태를 herdr 사이드바 하단 블록에 보여 주는 플러그인입니다. 설치와 기본 개념은 [README](../README.md)를 참고하세요. 이 문서는 설정과 실제 사용 방법을 설명합니다.

## 1. 설치와 요구 사항

```sh
herdr plugin install vrwolf1004/herdr-radio
```

로컬 사본으로 개발할 때는 link를 씁니다.

```sh
herdr plugin link C:/work/app/herdr-radio
```

- Python 3.8 이상 (표준 라이브러리만 사용)
- mpv 또는 ffplay
  - Windows: `winget install shinchiro.mpv`로 명령줄 빌드를 설치합니다. `mpv.net`은 GUI 전용이라 `mpv` 명령이 없습니다.
  - Windows에서 `winget`이 없으면 mpv 압축 파일을 받아 `C:\Program Files\mpv\mpv.exe`에 두면 플러그인이 이 위치도 찾습니다.
  - macOS: `brew install mpv`
  - Linux: 배포판 패키지 관리자로 `mpv` 설치

Python이 PATH에 없으면 플러그인이 실행되지 않습니다. 확인 방법은 `python --version`입니다. herdr 서버는 시작 시점의 PATH를 물려받으므로, PATH를 바꾼 뒤에는 서버를 재시작해야 합니다.

## 2. 방송국 등록

설정 파일 위치는 다음 명령으로 확인합니다.

```sh
herdr plugin config-dir herdr-radio
```

그 폴더의 `config.json`에 방송국을 넣습니다. 형식은 [config.example.json](../config.example.json)과 같습니다.

```json
{
  "stations": [
    { "name": "Jazz Radio Blues", "url": "http://jazzblues.ice.infomaniak.ch/jazzblues-high.mp3" }
  ]
}
```

- `name`은 사이드바와 메뉴에 표시됩니다. 생략하면 URL이 이름으로 쓰입니다.
- `url`이 비어 있는 항목은 무시됩니다.
- 파일을 고친 뒤에는 재시작이 필요 없습니다. 메뉴와 `play N` 액션이 매번 다시 읽습니다.

## 3. 사이드바 줄

herdr는 `config.toml`에 들어 있는 토큰만 그립니다. `[ui.sidebar.agents]`에 radio 줄을 넣습니다.

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", "machine", { token = "workspace", rules = [{ equals = "herdr-dock", hide = true }] }, "tab"],
  ["agent"],
  [{ token = "$rd_state", fg = "#1db954" }],
  [{ token = "$rd_now", fg = "#9aa0a6" }],
]
```

feedbag을 함께 쓰면 두 블록이 같은 `herdr-dock`에 모입니다. `$fb_*` 줄도 같은 `rows`에 넣으세요. 넣은 뒤에는 `herdr server reload-config`를 실행합니다.

- `$rd_*` 토큰은 radio 블록에만 보고되므로 다른 agent 행에는 나오지 않습니다.
- 맨 아래 고정은 feedbag이 담당합니다. feedbag이 없으면 radio 블록이 맨 아래에 있다는 보장이 없습니다.
- `ui.agent_panel_sort`는 기본값 `"spaces"`로 둡니다.

블록 예시:

```text
 ● radio
   ▶ 재생 중
   Jazz Radio Bl…
```

## 4. 액션

| 액션 (Windows) | 액션 (Linux/macOS) | 설명 |
| --- | --- | --- |
| `start-windows` | `start` | 마지막으로 재생한 방송을 다시 틀고, 없으면 `config.json`의 첫 방송을 틉니다 |
| `stop-windows` | `stop` | 재생을 멈춥니다. 블록은 남고 상태만 `■ 정지`로 바뀝니다 |
| `menu-windows` | `menu` | 방송국 선택 pane을 엽니다 |
| `play-N-windows` | `play-N` | `config.json`의 N번째 방송(1~6)을 바로 틉니다 |

실행 예:

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 5. 메뉴 사용법

`menu` pane은 다음 입력을 받습니다.

| 입력 | 동작 |
| --- | --- |
| 번호 | `config.json` 목록에서 그 방송을 재생합니다 |
| `s` | 재생을 멈춥니다 |
| `k 키워드` | Radio Browser에서 검색합니다. 결과 번호를 한 번 더 입력하면 재생합니다 |
| `q` 또는 Enter | 메뉴를 닫습니다 |

검색 결과는 `hidebroken`과 클릭 수 순으로 최대 10개입니다. 스트림 주소는 자주 바뀌므로 재생이 안 되면 다시 검색하세요.

## 6. 자주 겪는 문제

- **`mpv 또는 ffplay가 필요합니다`**: 플레이어가 PATH에 없습니다. 2번 항목처럼 설치하고 서버를 재시작하세요.
- **사이드바에 블록이 안 보임**: `config.toml`의 `$rd_*` 줄이 있는지 확인하고 `herdr server reload-config`를 실행합니다.
- **재생은 되는데 상태가 `정지`**: 플레이어가 PowerShell로 찾는 프로세스 이름(`mpv.exe`, `ffplay.exe`)과 다를 수 있습니다. 두 이름 중 하나로 실행되는지 확인하세요.
- **`Radio Browser 서버에 연결하지 못했습니다`**: 공개 서버 세 곳이 모두 응답하지 않습니다. 네트워크를 확인하고 잠시 뒤 다시 시도하세요.
- **pane을 닫아도 재생이 계속됨**: 정상 동작입니다. 완전히 끄려면 `stop` 액션을 쓰세요.

## 7. 주의

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다릅니다. 개인 청취 용도로 쓰세요.
