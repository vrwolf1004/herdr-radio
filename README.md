# herdr-radio

[Radio Browser](https://www.radio-browser.info/) 의 공개 방송국 목록을 검색해서, 화면 없이 소리만 재생하는 [herdr](https://herdr.dev/) 플러그인입니다.

## 요구 사항

- Python 3.8 이상 (표준 라이브러리만 사용)
- [mpv](https://mpv.io/) 또는 ffplay
  - Windows: `winget install mpv`
  - macOS: `brew install mpv`
  - Linux: 배포판 패키지 관리자로 `mpv` 설치

## 설치

```
herdr plugin install vrwolf1004/herdr-radio
```

## 사용법

- **radio: search and play station** 액션: 검색 pane 이 열립니다. 방송국 이름을 입력하고 번호를 고르면 재생합니다.
- **radio: stop playback** 액션: 재생을 멈춥니다.

재생은 별도 프로세스로 돌기 때문에 pane 을 닫아도 계속 들립니다.

## 주의

- 플러그인은 샌드박스 없이 사용자 권한으로 실행됩니다. 설치 전에 코드를 확인하세요.
- 방송 스트림마다 이용 조건이 다를 수 있습니다. 개인 청취 용도로 사용하세요.
- 스트림 주소는 자주 바뀌므로 재생이 안 되면 다시 검색하세요.

## 라이선스

미정
