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

메뉴 (`radio` pane):

```text
=== 방송국 목록 (config.json) ===
 1. Jazz Radio Blues
 2. Adroit Jazz Underground

번호: 재생  |  s: 정지  |  k 키워드: 검색  |  q: 닫기
>
```

## 설치

```sh
herdr plugin install vrwolf1004/herdr-radio
```

설치 후 방송국을 몇 개 등록하고, herdr `config.toml`에 radio 줄을 추가하세요. [사용법](docs/usage.md)을 참고하세요.

로컬 사본으로 개발하려면 다음과 같이 연결합니다.

```sh
git clone https://github.com/vrwolf1004/herdr-radio.git
herdr plugin link ./herdr-radio
```

### 플레이어 설치

- **Windows:** `winget install shinchiro.mpv` (명령줄 빌드). `mpv.net`은 GUI 전용이라 `mpv` 명령이 없습니다.
- **macOS:** `brew install mpv`
- **Linux:** 배포판 패키지 관리자로 `mpv`를 설치합니다.

## 방송국 등록

`herdr plugin config-dir herdr-radio`로 설정 폴더를 확인하고 `config.json`을 편집합니다. 형식은 [config.example.json](config.example.json)을 참고하세요.

```json
{
  "stations": [
    { "name": "Jazz Radio Blues", "url": "http://jazzblues.ice.infomaniak.ch/jazzblues-high.mp3" }
  ]
}
```

## 사이드바 줄 추가

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

- `$rd_*` 토큰은 radio 블록에만 보고되므로 다른 agent 행에는 나오지 않습니다.
- `herdr-dock`은 herdr-ai-feedbag과 같은 공용 workspace입니다. 두 플러그인을 함께 쓰면 블록이 같은 dock에 모이고, 맨 아래 정렬은 herdr-ai-feedbag이 담당합니다.
- `ui.agent_panel_sort`는 기본값 `"spaces"`로 두세요.

## 액션

| 액션 | 설명 |
| --- | --- |
| `start` | 마지막으로 재생한 방송을 다시 틉니다. 없으면 `config.json`의 첫 방송을 틉니다 |
| `stop` | 재생을 멈춥니다. 블록은 남고 상태만 `■ 정지`로 바뀝니다 |
| `menu` | 방송국 pane을 엽니다. 키워드를 입력하면 Radio Browser에서 찾고, Enter만 치면 `config.json` 목록을 보여 줍니다 |
| `play-1` … `play-6` | `config.json`의 N번째 방송을 바로 틉니다 |

Windows에서는 액션 id 뒤에 `-windows`가 붙습니다.

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 언어

메뉴와 사이드바 문구는 다음 순서로 정해집니다.

1. 환경변수 `HERDR_RADIO_LANG` (예: `en`)
2. 설정 파일 `config.json`의 `"lang"` 값
3. OS 언어
4. 영어 (지원하지 않는 언어일 때)

## 주의

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다를 수 있습니다. 개인 청취 용도로 사용하세요.
- 스트림 주소는 자주 바뀌므로 재생이 안 되면 `menu`에서 다시 검색하세요.
- pane을 닫아도 재생은 계속됩니다. 완전히 끄려면 `stop` 액션을 쓰세요.

## 문서

- [사용법](docs/usage.md)
- [구조 및 동작 방식](docs/architecture.md)
- [TODO](docs/todo.md)

영문 README는 [README.md](README.md)입니다.

## 라이선스

미정 (`herdr_api.py`는 [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag)(MIT)에서 가져왔습니다.)

---

## 프로젝트 응원하기

프로젝트가 도움이 되셨다면 커피 한 잔으로 개발을 응원해 주세요.

[![Ko-fi에서 응원하기](https://img.shields.io/badge/Ko--fi-%EC%9D%91%EC%9B%90%ED%95%98%EA%B8%B0-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
