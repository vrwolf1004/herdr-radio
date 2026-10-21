# 문제 해결 / Troubleshooting

자주 겪는 문제와 확인 방법입니다. 한국어 항목을 먼저 두고, 같은 내용의 영문 항목을 아래에 둡니다.

## 한국어

- **`mpv 또는 ffplay가 필요합니다`**: 플레이어가 PATH에 없습니다. [사용법](usage.ko.md)의 1번 항목처럼 설치하고 서버를 재시작하세요.
- **메뉴에서 `i`로 mpv를 설치하지 못함**: 이 기능은 Windows의 `winget`이 필요합니다. 설치 출력에 나온 오류를 확인하고, `winget install shinchiro.mpv`를 직접 실행하거나 [mpv 설치 안내](https://mpv.io/installation/)에 따라 설치하세요. 설치 후에는 메뉴를 닫고 다시 여세요.
- **사이드바에 블록이 안 보임**: `config.toml`의 `$rd_*` 줄이 있는지 확인하고 `herdr server reload-config`를 실행합니다. 줄이 있는데도 안 보이면 host가 돌지 않는 것입니다. 아래 "host가 안 돎" 항목을 보세요.
- **터미널 창이 뜨고 바로 꺼짐**: 예전 설치본이 남아 있을 때 생깁니다. 다시 설치하세요.

  ```sh
  herdr plugin uninstall herdr-radio
  herdr plugin install vrwolf1004/herdr-radio --yes
  ```

- **host가 안 돎**: 상태 폴더의 `host.log`에 오류가 남습니다 (`%LOCALAPPDATA%\herdr\plugins\herdr-radio\host.log`). 설치 폴더에서 `python src/radio.py ensure`를 실행하면 host를 다시 띄웁니다.
- **목록에 방송국이 없음**: `config.json`이 `herdr plugin config-dir herdr-radio`가 보여 주는 폴더에 있는지 확인하세요.
- **재생은 되는데 상태가 `정지`**: 플러그인이 띄운 플레이어만 인식합니다. 명령줄에 `herdr-radio` 표식(`--title=herdr-radio`)이 있는 `mpv.exe`/`ffplay.exe`를 찾습니다. 직접 띄운 mpv는 표식이 없어서 인식되지 않습니다.
- **`Radio Browser 서버에 연결하지 못했습니다`**: 공개 서버 세 곳이 모두 응답하지 않습니다. 네트워크를 확인하고 잠시 뒤 다시 시도하세요.
- **pane을 닫아도 재생이 계속됨**: 정상 동작입니다. 완전히 끄려면 `stop` 액션을 쓰세요.
- **사이드바에 `✖ 실패`가 나옴**: 정지하지 않았는데 플레이어가 끝났다는 뜻입니다. 스트림이 끊겼거나 주소가 틀렸을 수 있습니다. `menu`에서 다른 방송을 고르거나 `start`를 다시 실행하세요. 정지하거나 다시 틀면 표시가 사라집니다.
- **`재생 중인 mpv가 없어서 볼륨을 바꿀 수 없습니다`**: 볼륨 액션은 재생 중인 mpv에만 동작합니다. 방송을 먼저 틀고 다시 실행하세요. ffplay로 재생 중이면 볼륨을 바꿀 수 없습니다.

## English

- **`mpv or ffplay is required` (mpv 또는 ffplay가 필요합니다)**: the player is not on PATH. Install it as in section 1 of the [usage guide](usage.md) and restart the server.
- **Installing mpv with `i` in the menu fails**: this Windows-only shortcut needs `winget`. Check the installation output, run `winget install shinchiro.mpv` yourself, or follow the [mpv installation guide](https://mpv.io/installation/). Close and reopen the menu after installation.
- **The sidebar block does not appear**: check that the `$rd_*` rows are in `config.toml` and run `herdr server reload-config`. If the rows exist but the block still does not appear, the host is not running. See "Host is not running" below.
- **A terminal window flashes open and closes**: an old installed copy is still present. Reinstall:

  ```sh
  herdr plugin uninstall herdr-radio
  herdr plugin install vrwolf1004/herdr-radio --yes
  ```

- **Host is not running**: errors are written to `host.log` in the state folder (`%LOCALAPPDATA%\herdr\plugins\herdr-radio\host.log`). Run `python src/radio.py ensure` from the install folder to start it again.
- **The menu has no stations**: confirm that `config.json` is in the folder shown by `herdr plugin config-dir herdr-radio`.
- **Playing, but the state shows `stopped`**: the plugin only recognises the player it started, identified by the `--title=herdr-radio` argument. A mpv you started yourself is not recognised.
- **`Radio Browser 서버에 연결하지 못했습니다` (cannot reach Radio Browser)**: all three public servers failed. Check your network and try again later.
- **Playback continues after closing the pane**: this is expected. Use the `stop` action to turn it off.
- **The sidebar shows `✖ failed`**: the player ended without a stop, usually because the stream dropped or the address is wrong. Pick another station in `menu`, or run `start` again. Stopping or starting playback clears it.
- **`재생 중인 mpv가 없어서 볼륨을 바꿀 수 없습니다` (no mpv is playing, so the volume cannot change)**: volume actions work only with a running mpv. Start a station first. Volume cannot be changed while ffplay is playing.

## 관련 문서 / Related

- [사용법 (한국어)](usage.ko.md) / [Usage (English)](usage.md)
- [구조 및 동작 방식](architecture.md)
