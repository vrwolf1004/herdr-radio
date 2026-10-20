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

### 추천 장르 바꾸기

메뉴의 장르와 추천 방송은 플러그인 안의 [src/genres.json](../src/genres.json)에 있습니다. 바꾸고 싶으면 `config.json`에 같은 형식의 `genres`를 넣습니다. `genres`가 있으면 기본 목록 대신 그것만 보여 줍니다.

```json
{
  "stations": [],
  "genres": [
    {
      "name": "Jazz",
      "stations": [
        { "name": "Radio Swiss Jazz", "country": "CH", "url": "http://stream.srg-ssr.ch/m/rsj/mp3_128" }
      ]
    }
  ]
}
```

`play N` 액션은 `genres`가 아니라 `stations`의 N번째 방송을 틉니다.

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
- 재생이 정지 없이 끝나면(연결 실패, 스트림 끊김) 블록에 `✖ 실패`와 방송 이름이 나옵니다. 정지하거나 다시 틀면 사라집니다.
- 맨 아래 고정은 feedbag이 담당합니다. feedbag이 없으면 radio 블록이 맨 아래에 있다는 보장이 없습니다.
- `ui.agent_panel_sort`는 기본값 `"spaces"`로 둡니다.

블록 예시:

```text
 ● radio
   ▶ 재생 중
   Jazz Radio Bl…
```

dock의 radio pane에는 방송국 목록(메뉴)이 떠 있습니다. 상태를 갱신하는 host 루프는 pane 밖의 분리 프로세스로 돌기 때문에, 목록을 닫아도 사이드바는 계속 갱신됩니다.

## 4. 액션

| 액션 (Windows) | 액션 (Linux/macOS) | 설명 |
| --- | --- | --- |
| `start-windows` | `start` | 마지막으로 재생한 방송을 다시 틀고, 없으면 `config.json`의 첫 방송(그것도 없으면 첫 추천 방송)을 틉니다 |
| `stop-windows` | `stop` | 재생을 멈춥니다. 블록은 남고 상태만 `■ 정지`로 바뀝니다 |
| `menu-windows` | `menu` | 방송국 선택 pane을 엽니다 |
| `play-N-windows` | `play-N` | `config.json`의 N번째 방송(1~6)을 바로 틉니다 |
| `next-windows` | `next` | 지금 방송이 든 목록(`config.json` 또는 추천 장르)에서 다음 방송을 틉니다. 끝에 오면 처음으로 돌아갑니다 |
| `prev-windows` | `prev` | 이전 방송을 틉니다. 처음에 오면 끝으로 돌아갑니다 |
| `volume-up-windows` | `volume-up` | 재생 중인 mpv의 볼륨을 5 올립니다 (mpv 전용) |
| `volume-down-windows` | `volume-down` | 재생 중인 mpv의 볼륨을 5 내립니다 (mpv 전용) |

실행 예:

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 5. 메뉴 사용법

`menu` pane에서 입력하고 Enter를 누릅니다. 장르 목록과 방송 목록의 입력을 한 표에 모았습니다. 입력은 줄 단위로 받으므로 한글 자모(`ㅅ` 등)는 쓸 수 없습니다.

| 입력 | 장르 목록 | 방송 목록 |
| --- | --- | --- |
| 번호 | 그 장르를 엽니다. 마지막 `내 방송국`은 `config.json` 목록입니다 | 그 방송을 재생합니다 |
| `a 번호` | 검색 결과의 방송을 `config.json`에 저장합니다. 재생하지는 않습니다. 이미 있으면 알려 줍니다 | 그 방송을 `config.json`에 저장합니다 (`내 방송국`에서는 쓸 수 없습니다) |
| `s` | 재생을 멈춥니다 | 재생을 멈춥니다 |
| `k 키워드` | Radio Browser에서 검색합니다. 결과 번호를 한 번 더 입력하면 재생합니다 | — |
| `b` 또는 Enter | — | 장르 목록으로 돌아갑니다 |
| `q` 또는 Enter | 메뉴를 닫지 않고 다시 그립니다 | — |

장르를 열면 추천 방송 5개가 나옵니다.

추천 방송은 2026년 10월에 재생을 확인한 목록입니다. 스트림 주소가 바뀌어 재생이 안 되면 `k 방송 이름`으로 검색해 새 주소를 쓰세요.

검색 결과는 `hidebroken`과 클릭 수 순으로 최대 10개입니다. 스트림 주소는 자주 바뀌므로 재생이 안 되면 다시 검색하세요.

목록은 같은 자리에서 다시 그리므로 스크롤백에 이전 화면이 쌓이지 않습니다. 방송 목록 화면은 위쪽에 카세트 그림이 나오고, 재생 중에는 릴이 돕니다. pane이 화면 전체를 담기에 너무 낮으면 카세트 그림을 숨겨 목록이 들어가게 합니다. pane을 키우면 다시 보입니다. 번호를 누르면 재생이 시작되고 목록이 다시 나옵니다. 메뉴 자체를 끄려면 Ctrl+C를 누르세요. 이때는 PowerShell 프롬프트가 나타납니다.

## 6. 문제 해결

자주 겪는 문제와 확인 방법은 [troubleshooting.md](troubleshooting.md)에 있습니다 (한국어 항목을 먼저, 영문 항목을 뒤에 둡니다).

## 7. 주의

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다릅니다. 개인 청취 용도로 쓰세요.

## 문서

- [Usage (English)](usage.md)
- [문제 해결](troubleshooting.md): 자주 겪는 문제 (한국어, 영문 항목 포함)
- [구조 및 동작 방식](architecture.md): 블록이 동작하는 방식
- [개발](development.md): 코드 구조, 확인 방법, 방송국과 액션 추가
- [할 일](todo.md): 개선 목록
