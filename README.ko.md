# herdr-radio

[English](README.md) | [**한국어**](README.ko.md)

지원 언어: 영어 · 한국어 · 러시아어 · 프랑스어 · 스페인어 · 독일어 · 일본어

Radio Browser를 검색하거나 저장한 방송국을 별도 플레이어 창 관리 없이 재생합니다. herdr 사이드바에서 재생 상태를 확인할 수 있습니다.

## 대시보드 디자인

Agents 사이드바:

```text
 ● radio
   ▶ 재생 중
   Jazz Radio Bl…
```

라디오 메뉴:

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
```

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

## 라이선스

미정입니다. `herdr_api.py`는 [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag)의 MIT 코드를 가져왔습니다.

## 프로젝트 응원하기

프로젝트가 도움이 되셨다면 커피 한 잔으로 개발을 응원해 주세요.

[![Ko-fi에서 응원하기](https://img.shields.io/badge/Ko--fi-%EC%9D%91%EC%9B%90%ED%95%98%EA%B8%B0-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
