# herdr-radio

[Radio Browser](https://www.radio-browser.info/) 방송국을 검색하거나 직접 등록한 방송국을 화면 없이 재생하는 [herdr](https://herdr.dev/) 플러그인입니다. herdr 사이드바 하단(`herdr-dock` 블록)에 지금 재생 중인 방송과 상태를 보여 줍니다.

```text
 ● radio
   ▶ 재생 중
   Jazz Radio Bl…
```

## 요구 사항

- Python 3.8 이상 (표준 라이브러리만 사용)
- [mpv](https://mpv.io/) 또는 ffplay
  - Windows: `winget install shinchiro.mpv` (명령줄용 빌드). `mpv.net`은 GUI 전용이라 `mpv` 명령이 없습니다.
  - macOS: `brew install mpv`
  - Linux: 배포판 패키지 관리자로 `mpv` 설치

## 설치

```
herdr plugin install vrwolf1004/herdr-radio
```

설치 후 방송국을 등록합니다. 설정 파일은 herdr 플러그인 설정 폴더(`herdr plugin config-dir herdr-radio`)의 `config.json`입니다. 형식은 [config.example.json](config.example.json)을 참고하세요.

## 사이드바 줄 추가

herdr는 사이드바 레이아웃에 들어 있는 토큰만 그립니다. herdr `config.toml`의 `[ui.sidebar.agents]`에 아래 줄을 넣고 `herdr server reload-config`를 실행하세요.

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", "machine", { token = "workspace", rules = [{ equals = "herdr-dock", hide = true }] }, "tab"],
  ["agent"],
  [{ token = "$rd_state", fg = "#1db954" }],
  [{ token = "$rd_now", fg = "#9aa0a6" }],
]
```

- `$rd_*` 토큰은 radio 블록에만 보고되므로 다른 agent 행에는 나오지 않습니다.
- `herdr-dock`은 feedbag과 같은 공용 workspace입니다. feedbag을 함께 쓰면 두 블록이 같은 dock에 모이고, 맨 아래 정렬은 feedbag이 담당합니다.
- `ui.agent_panel_sort`는 기본값 `"spaces"`로 두세요.

## 액션

| 액션 | 설명 |
| --- | --- |
| `start` | 마지막으로 재생한 방송을 다시 틀고, 없으면 `config.json`의 첫 방송을 틉니다 |
| `stop` | 재생을 멈춥니다. 사이드바 블록은 남고 상태만 `■ 정지`로 바뀝니다 |
| `menu` | 검색 pane을 엽니다. 키워드를 입력하면 Radio Browser에서 찾고, Enter만 치면 `config.json` 목록을 보여 줍니다 |

Windows에서는 액션 id 뒤에 `-windows`가 붙습니다.

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 주의

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다를 수 있습니다. 개인 청취 용도로 사용하세요.
- 스트림 주소는 자주 바뀌므로 재생이 안 되면 `menu`에서 다시 검색하세요.
- pane을 닫아도 재생은 계속됩니다. 완전히 끄려면 `stop` 액션을 쓰세요.

## 라이선스

미정 (`herdr_api.py`는 [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag)(MIT)에서 가져왔습니다.)
