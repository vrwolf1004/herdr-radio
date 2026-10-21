# herdr-radio

[English](README.md) | **한국어**

[Radio Browser](https://www.radio-browser.info/) 방송국을 검색하거나 직접 등록한 방송국을 화면 없이 재생하는 [herdr](https://herdr.dev/) 플러그인입니다. herdr 사이드바 하단(`herdr-dock` 블록)에 지금 재생 중인 방송과 상태를 보여 줍니다.

- Windows, Linux, macOS 지원
- Python 3.8 이상, 표준 라이브러리만 사용
- [mpv](https://mpv.io/) 또는 ffplay 필요
- herdr 0.9.0 이상
- 7개 언어 지원: 한국어, 영어, 일본어, 러시아어, 프랑스어, 스페인어, 독일어

사이드바 블록:

```text
 ● radio
   ▶ 재생 중
   Jazz Radio Bl…
```

재생이 정지 없이 끝나면(연결 실패, 스트림 끊김) `✖ 실패`와 방송 이름이 나옵니다.

메뉴 (`radio` pane):

```text
╭─────────────────────────────────────────────────────╮
│                 🐺  herdr-radio  🌕                 │
├─────────────────────────────────────────────────────┤
│  1. Jazz                                            │
│  2. Classical                                       │
│  3. K-pop                                           │
│  4. Lo-fi                                           │
│  5. News                                            │
│  6. 내 방송국 (config.json, 2)                      │
├─────────────────────────────────────────────────────┤
│ [번호] 장르   [s] 정지   [k 키워드] 검색   [q] 닫기 │
╰─────────────────────────────────────────────────────╯
>
```

장르를 고르면 추천 방송 5개가 나옵니다.

```text
╭────────────────────────────────────────────╮
│            🐺  herdr-radio  🌕             │
├────────────────────────────────────────────┤
│  1. Radio Swiss Jazz (CH)                  │
│  2. Jazz Radio (FR)                        │
│  3. Jazz Radio Blues (FR)                  │
│  4. 101 Smooth Jazz (US)                   │
│  5. 100 Greatest Jazz Lounge Bar (CA)      │
├────────────────────────────────────────────┤
│ [번호] 재생   [b] 뒤로   [s] 정지          │
│ [a 번호] config.json 에 저장               │
╰────────────────────────────────────────────╯
>
```

## 설치

```sh
herdr plugin install vrwolf1004/herdr-radio --yes
```

설치 후 방송국을 몇 개 등록하고, herdr `config.toml`에 radio 줄을 추가하세요. [사용법](docs/usage.ko.md) (영문: [usage.md](docs/usage.md))을 참고하세요.

로컬 사본으로 개발하려면 다음과 같이 연결합니다.

```sh
git clone https://github.com/vrwolf1004/herdr-radio.git
herdr plugin link ./herdr-radio
```

### 플레이어 설치

- **Windows:** `winget install shinchiro.mpv` (명령줄 빌드). `mpv.net`은 GUI 전용이라 `mpv` 명령이 없습니다.
- **macOS:** `brew install mpv`
- **Linux:** 배포판 패키지 관리자로 `mpv`를 설치합니다.

Windows에서 두 플레이어를 모두 찾지 못하면 메뉴에 `i`를 눌러 `winget install shinchiro.mpv`를 실행하는 안내가 나옵니다. 설치한 뒤에는 플레이어를 다시 찾도록 메뉴를 닫고 다시 여세요.

## 방송국 등록

`herdr plugin config-dir herdr-radio`로 설정 폴더를 확인하고 `config.json`을 편집합니다. 형식은 [config.example.json](config.example.json)을 참고하세요.

```json
{
  "stations": [
    { "name": "Jazz Radio Blues", "url": "http://jazzblues.ice.infomaniak.ch/jazzblues-high.mp3" }
  ]
}
```

메뉴에서 검색 결과의 방송을 `a 번호`로 저장할 수도 있습니다.

## 사이드바 줄

herdr는 사이드바 레이아웃에 들어 있는 토큰만 그립니다. `config.toml`의 `[ui.sidebar.agents]`에 아래 줄을 넣고 `herdr server reload-config`를 실행하세요.

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", "machine", { token = "workspace", rules = [{ equals = "herdr-dock", hide = true }] }, "tab"],
  ["agent"],
  [{ token = "$rd_state", fg = "#1db954" }],
  [{ token = "$rd_now", fg = "#9aa0a6" }],
]
```

- `$rd_*` 토큰은 radio 블록에만 나오므로 다른 agent 행에는 영향이 없습니다.
- `herdr-dock`은 herdr-ai-feedbag과 함께 쓰는 공용 workspace입니다. 두 플러그인을 함께 설치하면 블록이 같은 dock에 모이고, dock은 맨 아래에 놓입니다. radio만 설치해도 radio 워커가 dock을 맨 아래로 유지합니다.
- `ui.agent_panel_sort`는 기본값 `"spaces"`로 두세요.

## 액션

| 액션 | 설명 |
| --- | --- |
| `start` | 마지막으로 재생한 방송을 다시 틉니다. 없으면 `config.json`의 첫 방송(그것도 없으면 첫 추천 방송)을 틉니다 |
| `stop` | 재생을 멈춥니다. 블록은 남고 `■ 정지`로 바뀝니다 |
| `menu` | 방송국 pane을 엽니다. 장르(Jazz, Classical, K-pop, Lo-fi, News)를 고르면 추천 방송 5개가 나오고, `내 방송국`에는 `config.json` 목록이 나옵니다. `k 키워드`로 Radio Browser를 검색합니다 |
| `play-1` … `play-6` | `config.json`의 N번째 방송을 틉니다 |
| `next` / `prev` | 지금 방송이 든 목록(`config.json` 또는 추천 장르)에서 다음 또는 이전 방송을 틉니다 |
| `volume-up` / `volume-down` | 재생 중인 mpv의 볼륨을 5만큼 올리거나 내립니다 (mpv 전용) |

Windows에서는 각 액션 id 뒤에 `-windows`를 붙입니다.

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 언어

메뉴와 사이드바 문구는 아래 순서에서 처음 찾은 언어를 씁니다.

1. 환경변수 `HERDR_RADIO_LANG` (예: `en`)
2. `config.json`의 `"lang"` 값
3. OS 언어
4. 지원하지 않는 언어이면 영어

## 참고

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다를 수 있습니다. 개인 청취 용도로 쓰세요.
- 스트림 주소는 자주 바뀝니다. 재생이 안 되면 `menu`에서 다시 검색하세요.
- pane을 닫아도 재생은 계속됩니다. 끄려면 `stop` 액션을 쓰세요.

## 문서

- [사용법 (한국어)](docs/usage.ko.md)
- [Usage guide (English)](docs/usage.md)
- [문제 해결](docs/troubleshooting.md)
- [개발과 확인 방법](docs/development.md)
- [구조 및 동작 방식 (한국어)](docs/architecture.md)
- [TODO (한국어)](docs/todo.md)

영어 README는 [README.md](README.md)에 있습니다.

## 라이선스

미정. `herdr_api.py`는 [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag)(MIT)에서 가져왔습니다.
