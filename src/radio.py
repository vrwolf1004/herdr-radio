#!/usr/bin/env python3
"""herdr-radio: Radio Browser 방송국을 검색해서 화면 없이 소리만 재생한다.

표준 라이브러리만 쓴다. 재생은 mpv(없으면 ffplay)에 맡긴다.
사용법: radio.py menu | stop | status
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import urllib.parse
import urllib.request

API_HOSTS = [
    "de1.api.radio-browser.info",
    "nl1.api.radio-browser.info",
    "at1.api.radio-browser.info",
]
USER_AGENT = "herdr-radio/0.1"


def state_dir():
    # herdr 가 주입하는 상태 폴더를 우선 쓰고, 없으면 사용자 홈 아래에 둔다.
    path = os.environ.get("HERDR_PLUGIN_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), ".herdr-radio"
    )
    os.makedirs(path, exist_ok=True)
    return path


def pid_file():
    return os.path.join(state_dir(), "player.pid")


def api_get(path, params):
    query = urllib.parse.urlencode(params)
    last_error = None
    # 공개 서버 중 하나가 죽어 있을 수 있으므로 순서대로 시도한다.
    for host in API_HOSTS:
        req = urllib.request.Request(
            f"https://{host}{path}?{query}", headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.load(resp)
        except OSError as error:
            last_error = error
    raise RuntimeError(f"Radio Browser 서버에 연결하지 못했습니다: {last_error}")


def search(keyword, limit=10):
    stations = api_get(
        "/json/stations/search",
        {
            "name": keyword,
            "limit": limit,
            "hidebroken": "true",
            "order": "clickcount",
            "reverse": "true",
        },
    )
    results = []
    for station in stations:
        url = station.get("url_resolved") or station.get("url") or ""
        if not url:
            continue
        results.append(
            {
                "name": (station.get("name") or "").strip(),
                "country": station.get("country") or "",
                "url": url,
            }
        )
    return results


def find_player():
    for exe in ("mpv", "ffplay"):
        path = shutil.which(exe)
        if path:
            return exe, path
    return None, None


def stop():
    if not os.path.exists(pid_file()):
        return False
    with open(pid_file(), encoding="utf-8") as f:
        raw = f.read().strip()
    os.remove(pid_file())
    if not raw.isdigit():
        return False
    pid = int(raw)
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    return True


def play(url):
    # 이전 재생이 있으면 먼저 끊는다.
    stop()
    name, path = find_player()
    if not path:
        raise RuntimeError("mpv 또는 ffplay가 필요합니다. Windows: winget install mpv")
    if name == "mpv":
        args = [path, "--no-video", "--no-terminal", "--really-quiet", url]
    else:
        args = [path, "-nodisp", "-loglevel", "quiet", url]

    kwargs = {}
    if os.name == "nt":
        # 콘솔 pane 을 닫아도 재생이 이어지도록 분리한다.
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    with open(pid_file(), "w", encoding="utf-8") as f:
        f.write(str(proc.pid))
    return proc.pid


def menu():
    keyword = input("방송국 이름 검색 (예: jazz, bbc, kbs): ").strip()
    if not keyword:
        return 0
    try:
        results = search(keyword)
    except RuntimeError as error:
        print(error)
        return 1
    if not results:
        print("검색 결과가 없습니다.")
        return 0

    for index, station in enumerate(results, 1):
        print(f"{index:2}. {station['name']} ({station['country']})")

    choice = input("번호 선택 (Enter=취소, s=정지): ").strip().lower()
    if choice == "s":
        print("정지했습니다." if stop() else "재생 중인 방송이 없습니다.")
        return 0
    if not choice.isdigit() or not 1 <= int(choice) <= len(results):
        return 0

    station = results[int(choice) - 1]
    try:
        play(station["url"])
    except RuntimeError as error:
        print(error)
        return 1
    print(f"재생 중: {station['name']}")
    print("이 pane 을 닫아도 재생은 계속됩니다. 정지는 stop 액션을 쓰세요.")
    return 0


def main(argv):
    command = argv[1] if len(argv) > 1 else "menu"
    if command == "menu":
        return menu()
    if command == "stop":
        print("정지했습니다." if stop() else "재생 중인 방송이 없습니다.")
        return 0
    if command == "status":
        print("재생 중" if os.path.exists(pid_file()) else "정지 상태")
        return 0
    print(f"알 수 없는 명령: {command}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
