# herdr-radio

[English](README.md) | [**한국어**](README.ko.md)

지원 언어: 영어 · 한국어 · 러시아어 · 프랑스어 · 스페인어 · 독일어 · 일본어

Radio Browser를 검색하거나 저장한 방송국을 별도 플레이어 창 관리 없이 재생합니다. herdr 사이드바에서 재생 상태를 확인할 수 있습니다.
시작/workspace `ensure` 확인은 radio pane의 실제 존재 여부도 확인하므로 pane을 닫은 뒤 블록을 복구할 수 있습니다.

## 대시보드 디자인

Agents 사이드바: 재생 중이면 `radio > <방송 이름>`, 정지 중이면 `radio`로 표시합니다.

라디오 메뉴 (기본 화면):

```text
╭────────────────────────────────────────────────────╮
│                🐺  herdr-radio  🌕                 │
├────────────────────────────────────────────────────┤
│             ╭─╮          ╭─╮                       │
│             │|│ ▓▒░░▒▓▓▒░ │|│                       │
│             ╰─╯          ╰─╯                       │
│                  ▶ PLAY                            │
├────────────────────────────────────────────────────┤
│ === 장르 ===                                        │
│  1. Jazz                                           │
│  2. Classical                                      │
│  3. K-pop                                          │
│  4. Rock / Blues                                   │
│  5. Ambient / Chill                                │
│  6. News                                           │
├────────────────────────────────────────────────────┤
│ 재생 : Jazz Radio                   Ctrl+H 도움말   │
╰────────────────────────────────────────────────────╯
```

`Ctrl+H`를 누르면 목록 위에 도움말 팝업이 뜹니다. 다시 누르면 닫힙니다:

```text
        ╭──────────────────────────────────────╮
        │            Ctrl+H 도움말             │
        ├──────────────────────────────────────┤
        │ [번호] 장르   [s] 정지               │
        │ [k 키워드] 검색   [t] 테마           │
        │ [l] 언어   [Ctrl+C] 종료             │
        ╰──────────────────────────────────────╯
```

장르를 고른 뒤의 방송 목록 화면도 같은 카세트와 하단 줄을 쓰며, `Ctrl+H`에서 `[번호] 재생   [b] 뒤로   [s] 정지   [a 번호] 저장`을 보여 줍니다.

### 키

키를 치고 Enter를 누릅니다.

| 키 | 기능 |
| --- | --- |
| 번호 | 장르 열기 (방송 목록 화면에서는 그 방송 재생) |
| `b` | 뒤로 (방송 목록 화면) |
| `a 번호` | 방송을 `config.json`에 저장 (방송 목록 화면) |
| `s` | 재생 정지 |
| `k 키워드` | Radio Browser 검색 |
| `t` | 다음 테마: 형광 녹색 → 호박색 → 터미널 기본색 (저장됨) |
| `l` | 다음 언어: 시스템 → en → ko → ru → fr → es → de → ja → 시스템 (저장됨) |
| `Ctrl+H` | 도움말 팝업 열기/닫기 (Windows, 입력 줄이 비어 있을 때) |
| `Ctrl+C` | 메뉴 종료 |

## 설치

```sh
herdr plugin install vrwolf1004/herdr-radio --yes
```

## 액션

| 액션 | 기능 |
| --- | --- |
| `start` / `stop` | 마지막 방송 재생 또는 재생 중지 |
| `menu` | 장르 탐색, Radio Browser 검색, 방송 재생·저장 |
| `play-1` … `play-6` | 설정 목록에서 해당 방송 재생 |
| `next` / `prev` | 다음 또는 이전 방송 재생 |
| `volume-up` / `volume-down` | mpv 볼륨을 5만큼 조절 |

Windows에서는 각 액션 ID 뒤에 `-windows`를 붙입니다. 플레이어 설치와 설정은 [사용법](docs/usage.ko.md)을 참고하세요.

## 요구 사항

- Windows, Linux, macOS
- herdr 0.9.0 이상
- Python 3.8 이상, 표준 라이브러리만 사용
- mpv 또는 ffplay

## 문서

- [사용법 (한국어)](docs/usage.ko.md)
- [Usage guide (English)](docs/usage.md)
- [문제 해결](docs/troubleshooting.md)
- [개발](docs/development.md)
- [구조 및 동작 방식](docs/architecture.md)
- [할 일](docs/todo.md)
- [추가 항목](docs/readme-extras.ko.md): README에서 옮긴 항목

## 프로젝트 응원하기

프로젝트가 도움이 되셨다면 커피 한 잔으로 개발을 응원해 주세요.

[![Ko-fi에서 응원하기](https://img.shields.io/badge/Ko--fi-%EC%9D%91%EC%9B%90%ED%95%98%EA%B8%B0-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
