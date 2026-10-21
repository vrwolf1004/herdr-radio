# 개발

코드 구조, 확인 방법, 방송국과 액션을 추가할 때 함께 고칠 곳을 정리합니다. 동작 방식과 dock 공유는 [architecture.md](architecture.md)에 있습니다.

## 파일 구조

```text
herdr-radio/
├── README.md, README.ko.md      짧은 소개 (영문, 한글)
├── herdr-plugin.toml            herdr 매니페스트: startup, hook, 액션, pane 선언 (OS별)
├── config.example.json          방송국 설정 예시
├── .gitattributes               줄바꿈 정규화 (LF)
├── docs/                        사용법, 문제 해결, 구조, 개발, 할 일
├── src/
│   ├── radio.py                 명령(ensure, host, start, stop, menu, status, play)과 host 루프, Radio Browser 검색, 재생
│   ├── genres.json              메뉴의 장르별 추천 방송 (config.json의 genres가 있으면 그것을 씀)
│   ├── herdr_api.py             herdr CLI와 socket 호출 (feedbag의 파일을 가져온 사본)
│   ├── i18n.py                  언어 결정과 t(key, **values)
│   └── locales/<언어>.json      화면 문구 (en, ko, ru, fr, es, de, ja)
├── tests/
│   └── test_radio.py             설정, pane 선택, 플레이어 탐색, 검색 캐시 등의 unittest
```

`tests/test_radio.py`에는 방송국 설정 처리, pane 선택, 플레이어 식별, 외부 명령 제한 시간, 검색 캐시 테스트가 있습니다. 실행하려면 플러그인 폴더에서 다음 명령을 사용합니다.

```sh
python -m unittest discover -s tests
```

## 실행해서 확인하기

자동 테스트가 없으므로, 바꾼 뒤에는 실제로 실행해 봅니다.

1. 플러그인 폴더에서 문법을 먼저 확인합니다. Windows는 `python`, Linux/macOS는 `python3`을 씁니다.

   ```sh
   python -X utf8 -m py_compile src/radio.py src/herdr_api.py src/i18n.py
   ```

2. 메뉴를 직접 띄워 봅니다. herdr 안의 pane에서 실행해야 herdr CLI가 응답합니다.

   ```sh
   python -X utf8 src/radio.py menu
   ```

3. 재생, 정지, 상태를 확인합니다.

   ```sh
   python -X utf8 src/radio.py play 1
   python -X utf8 src/radio.py status
   python -X utf8 src/radio.py stop
   ```

## 문구를 추가하거나 바꿀 때

1. 모든 언어 파일(`src/locales/*.json`)에 같은 키를 넣습니다.
2. 자리표시자(`{name}` 등)는 모든 언어에서 같아야 합니다.
3. 코드에서는 `t("key", ...)`로 씁니다.
4. 메뉴와 사이드바 줄의 폭을 실제 터미널에서 확인합니다. 한글과 일본어는 두 칸으로 셉니다.

## 방송국을 추가할 때

방송국은 `config.json`에 씁니다. 형식과 등록 방법은 [사용법](usage.ko.md)의 "2. 방송국 등록"에 있습니다. 추천 장르를 바꾸려면 `src/genres.json`이나 `config.json`의 `genres`를 고칩니다. 사용법의 "추천 장르 바꾸기"를 보세요.

## 액션을 추가할 때

`play-N` 액션은 `herdr-plugin.toml`에 Windows와 Linux/macOS 항목을 한 쌍씩 둡니다. 번호는 1~6까지 있습니다. 6개를 넘기려면 두 항목을 같은 형식으로 추가하고, `cmd_play`의 범위는 `config.json` 길이로 정해지므로 코드는 고치지 않아도 됩니다. 자세한 내용은 [architecture.md](architecture.md)의 "새 방송국 액션 추가"를 보세요.

새 액션을 추가하면 다음도 함께 고칩니다.

1. `herdr-plugin.toml`에 Windows(`-windows` id)와 Linux/macOS 항목을 함께 추가합니다. herdr는 액션 id 중복을 허용하지 않습니다.
2. `src/radio.py`의 명령 분기를 추가합니다.
3. `docs/usage.md`와 `docs/usage.ko.md`의 액션 표를 고칩니다.

## 문서 맞추기

- `usage.md`(영문)와 `usage.ko.md`(한국어)는 같은 내용을 가져야 합니다. 한쪽을 고치면 다른 쪽도 고칩니다.
- 문제 해결 항목은 [troubleshooting.md](troubleshooting.md)에 한국어와 영문을 함께 둡니다.
- 메뉴 입력이나 키가 바뀌면 사용법의 "메뉴 사용법" 표를 확인합니다.
