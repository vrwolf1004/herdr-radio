#!/usr/bin/env python3
"""herdr-radio: Radio Browser 방송국을 검색하거나 config.json 의 방송국을 화면 없이 재생한다.

동작 방식
  - 공용 "herdr-dock" workspace 에 pane 하나를 두고 가짜 agent(radio)로 등록한다.
    dock 이 없으면 만들고, 이미 있으면(다른 플러그인이 만든 경우) pane 을 나눠 들어간다.
  - 그 pane 에서 host 루프가 돈다. 재생 상태(방송 이름, 재생 중/정지)를 $rd_now, $rd_state 토큰으로 사이드바에 올린다.
  - 재생은 detached mpv 프로세스다. pane 을 닫아도 재생은 이어진다.

명령
  ensure   dock 과 host 를 확인하고 없으면 띄운다 (startup / event hook)
  host     dock pane 안에서 도는 루프. 사이드바 토큰 갱신
  start    마지막 방송(없으면 config.json 첫 방송)을 재생한다
  stop     재생을 멈춘다 (host 는 그대로 두고 상태만 정지로 바뀐다)
  menu     검색 또는 config.json 목록에서 골라 재생하는 pane
  status   재생 상태를 출력한다
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request

import herdr_api
import i18n

# Windows 에서 콘솔 프로그램(powershell, tasklist, taskkill)이 터미널 창을 띄우지 않게 한다.
NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

PLUGIN_ID = "herdr-radio"
SOURCE = f"plugin:{PLUGIN_ID}"
# feedbag 과 같은 공용 dock 을 쓴다. 맨 아래 고정은 feedbag 이 하고, 여기서는 자기 블록만 관리한다.
DOCK_LABEL = "herdr-dock"
AGENT_ID = "radio"
DISPLAY_AGENT = "radio"

TICK_SECONDS = 1
LAYOUT_EVERY_TICKS = 5        # 맨 아래 위치 확인, agent 재등록, 재생 상태 확인 주기
HEARTBEAT_STALE_SECONDS = 10
TOKEN_TTL_MS = 15_000
NAME_WIDTH = 14               # 사이드바에 올릴 방송 이름 길이

API_HOSTS = [
    "de1.api.radio-browser.info",
    "nl1.api.radio-browser.info",
    "at1.api.radio-browser.info",
]
USER_AGENT = "herdr-radio/0.2"


# ---------------------------------------------------------------- 경로 / 상태 파일


def state_dir_path():
    path = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    if path:
        return path
    base = os.environ.get("LOCALAPPDATA") if herdr_api.IS_WINDOWS else os.path.expanduser("~/.local/state")
    return os.path.join(base or os.path.expanduser("~"), "herdr", "plugins", PLUGIN_ID)


def config_dir_path():
    """herdr 가 주는 설정 폴더. 없으면 herdr 기본 위치(plugins/config/herdr-radio)를 본다."""
    path = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if path:
        return path
    base = os.environ.get("APPDATA") if herdr_api.IS_WINDOWS else os.path.expanduser("~/.config")
    return os.path.join(base or os.path.expanduser("~"), "herdr", "plugins", "config", PLUGIN_ID)


class State:
    """state dir 안의 작은 파일들. host 와 액션이 서로 다른 프로세스라 파일로 주고받는다."""

    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def path(self, name):
        return os.path.join(self.directory, name)

    def read(self, name):
        try:
            with open(self.path(name), encoding="utf-8") as file:
                return file.read().strip() or None
        except OSError:
            return None

    def write(self, name, value):
        with open(self.path(name), "w", encoding="utf-8") as file:
            file.write(value)

    def remove(self, name):
        try:
            os.remove(self.path(name))
        except OSError:
            pass

    def touch_heartbeat(self):
        self.write("heartbeat", str(time.time()))

    def host_alive(self):
        beat = self.read("heartbeat")
        try:
            return beat is not None and time.time() - float(beat) < HEARTBEAT_STALE_SECONDS
        except ValueError:
            return False


# ---------------------------------------------------------------- 설정 / 방송 목록


def clean_stations(items):
    """{"name", "url", "country"} 목록을 고른다. 빈 url 은 건너뛰고, name 이 없으면 url 을 쓴다."""
    stations = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            continue
        name = item.get("name")
        name = name.strip() if isinstance(name, str) and name.strip() else url.strip()
        country = item.get("country")
        country = country.strip() if isinstance(country, str) else ""
        stations.append({"name": name, "url": url.strip(), "country": country})
    return stations


def read_config():
    path = os.path.join(config_dir_path(), "config.json")
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_stations():
    """config.json 의 stations 를 읽는다. 항목은 {"name": ..., "url": ...} 이다."""
    # 형식이 틀린 부분(목록이 아닌 stations, 문자열 항목 등)은 건너뛰고 나머지만 쓴다.
    return clean_stations(read_config().get("stations"))


GENRES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "genres.json")


def load_genres():
    """장르별 추천 방송 목록. config.json 에 "genres" 가 있으면 그것을, 없으면 src/genres.json 을 쓴다.
    항목은 {"name": 장르 이름, "stations": [...]} 이고, 방송이 하나도 없는 장르는 뺀다."""
    genres = read_config().get("genres")
    if not isinstance(genres, list):
        try:
            with open(GENRES_PATH, encoding="utf-8") as file:
                genres = json.load(file).get("genres")
        except (OSError, ValueError, AttributeError):
            genres = []
    result = []
    for genre in genres if isinstance(genres, list) else []:
        if not isinstance(genre, dict):
            continue
        stations = clean_stations(genre.get("stations"))
        name = genre.get("name")
        if stations and isinstance(name, str) and name.strip():
            result.append({"name": name.strip(), "stations": stations})
    return result


# ---------------------------------------------------------------- Radio Browser


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
        except (OSError, ValueError) as error:  # ValueError: 응답이 JSON 이 아닐 때
            last_error = error
    raise RuntimeError(i18n.t("error.radio_browser", detail=last_error))


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


# ---------------------------------------------------------------- 재생


# herdr 가 띄운 프로세스는 PATH 를 바꾸기 전 환경을 물려받을 수 있으므로 알려진 설치 위치도 본다.
KNOWN_PLAYER_PATHS = [
    r"C:\Program Files\MPV Player\mpv.exe",
    r"C:\Program Files\mpv\mpv.exe",
]


def find_player():
    for exe in ("mpv", "ffplay"):
        path = shutil.which(exe)
        if path:
            return exe, path
    for path in KNOWN_PLAYER_PATHS:
        if os.path.exists(path):
            return "mpv", path
    return None, None


PLAYER_MARKER = "herdr-radio"  # 플레이어 창 제목. 명령줄에 들어가서 프로세스를 찾는 표식이 된다.
PLAYER_TITLE_ARG = f"--title={PLAYER_MARKER}"  # mpv 인자 형식 (host 명령줄에는 없다)


def player_pids():
    """이 플러그인이 띄운 플레이어 프로세스 pid 목록.

    pid 파일은 상태 폴더가 어긋나면 사라질 수 있으므로, 명령줄의 마커로 직접 찾는다.
    """
    # 플레이어 인자에만 있는 표식으로 찾는다. host 명령줄의 "herdr-radio" 경로와는 겹치지 않는다.
    if os.name == "nt":
        script = (
            "Get-CimInstance Win32_Process -Filter \"Name='mpv.exe' OR Name='ffplay.exe'\" | "
            f"Where-Object {{ $_.CommandLine -like '*{PLAYER_TITLE_ARG}*' -or $_.CommandLine -like '*-window_title {PLAYER_MARKER}*' }} | "
            "ForEach-Object { $_.ProcessId }"
        )
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, **NO_WINDOW, text=True,
        ).stdout
        return [int(line) for line in out.split() if line.isdigit()]
    found = []
    for pattern in (PLAYER_TITLE_ARG, f"-window_title {PLAYER_MARKER}"):
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout
        found += [int(line) for line in out.split() if line.isdigit()]
    return [pid for pid in set(found) if pid != os.getpid()]


def process_alive(pid):
    """pid 프로세스가 살아 있는지. Windows 는 API 로 확인해서 PowerShell 을 띄우지 않는다."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# 무거운 프로세스 검색 결과를 잠깐 기억한다. 검색은 pid 파일이 없을 때만 한다.
_scan_cache = {"at": 0.0, "playing": False}
SCAN_INTERVAL_SECONDS = 30


def is_playing(state):
    raw = state.read("player.pid")
    if raw and raw.isdigit():
        if process_alive(int(raw)):
            return True
        state.remove("player.pid")  # 끝난 플레이어의 기록은 지운다
        if state.read("last_end") == "playing":
            state.write("last_end", "failed")  # 정지 없이 끝났다 = 스트림 끊김이나 연결 실패
    now = time.time()
    if now - _scan_cache["at"] < SCAN_INTERVAL_SECONDS:
        return _scan_cache["playing"]
    _scan_cache.update(at=now, playing=bool(player_pids()))
    return _scan_cache["playing"]


def stop(state):
    _scan_cache.update(at=0.0, playing=False)  # 정지 직후 예전 결과가 남지 않게 한다
    state.write("last_end", "stopped")
    pids = set(player_pids())
    raw = state.read("player.pid")
    if raw and raw.isdigit():
        pids.add(int(raw))
    state.remove("player.pid")
    for pid in pids:
        if os.name == "nt":
            # /T 로 자식 프로세스까지 함께 끝낸다.
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, **NO_WINDOW)
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    return bool(pids)


def ipc_address(state):
    """mpv IPC 주소. Windows 는 이름 있는 파이프, 그 밖은 상태 폴더의 소켓 파일."""
    if os.name == "nt":
        return r"\\.\pipe\herdr-radio-mpv"
    return state.path("mpv.sock")


def send_mpv(state, command):
    """mpv 에 JSON 명령을 보내고 응답을 돌려준다. 실행 중인 mpv 가 없으면 None."""
    message = (json.dumps({"command": command}) + "\n").encode("utf-8")
    address = ipc_address(state)
    try:
        if os.name == "nt":
            with open(address, "r+b", buffering=0) as pipe:
                pipe.write(message)
                return json.loads(pipe.readline().decode("utf-8") or "{}")
        import socket
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        try:
            client.connect(address)
            client.sendall(message)
            return json.loads(client.makefile("rb").readline().decode("utf-8") or "{}")
        finally:
            client.close()
    except (OSError, ValueError):
        return None


def cmd_volume(args, delta):
    """재생 중인 mpv 의 볼륨을 delta 만큼 바꾼다."""
    state = State(args.state)
    response = send_mpv(state, ["add", "volume", delta])
    if response is None or response.get("error") not in (None, "success"):
        print(i18n.t("msg.volume_fail"))
        return 1
    level = send_mpv(state, ["get_property", "volume"])
    if level and level.get("data") is not None:
        print(f"volume: {int(level['data'])}")
    return 0


def cmd_volume_up(args):
    return cmd_volume(args, 5)


def cmd_volume_down(args):
    return cmd_volume(args, -5)


def play(state, station):
    # 이전 재생이 있으면 먼저 끊는다.
    stop(state)
    name, path = find_player()
    if not path:
        raise RuntimeError(i18n.t("error.no_player"))
    if name == "mpv":
        # network-timeout: 연결이 실패하면 몇 초 뒤 종료해서 실패를 감지할 수 있게 한다
        # input-ipc-server: 볼륨 같은 명령을 소켓으로 받는다 (mpv 전용)
        args = [path, "--no-video", "--no-terminal", "--really-quiet", "--network-timeout=5",
                f"--input-ipc-server={ipc_address(state)}", PLAYER_TITLE_ARG, station["url"]]
    else:
        args = [path, "-nodisp", "-loglevel", "quiet", "-window_title", PLAYER_MARKER, station["url"]]

    kwargs = {}
    if os.name == "nt":
        # 콘솔 pane 을 닫아도 재생이 이어지도록 분리한다.
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    state.write("player.pid", str(proc.pid))
    # 마지막 방송을 기억해 두면 start 액션이 같은 방송을 다시 튼다.
    state.write("station.json", json.dumps({"name": station["name"], "url": station["url"]}, ensure_ascii=False))
    state.write("last_end", "playing")
    return proc.pid


def last_station(state):
    raw = state.read("station.json")
    if raw:
        try:
            return json.loads(raw)
        except ValueError:
            pass
    stations = load_stations() or [s for g in load_genres() for s in g["stations"]]
    return stations[0] if stations else None


# ---------------------------------------------------------------- dock workspace / pane


def find_workspace(workspaces):
    for workspace in workspaces:
        if workspace.get("label") == DOCK_LABEL:
            return workspace["workspace_id"]
    return None


def workspace_panes(workspace_id):
    panes = herdr_api.cli("pane", "list").get("panes", [])
    return [p for p in panes if p["workspace_id"] == workspace_id]


def claimed_by_others(state_dir):
    """같은 plugins 폴더의 다른 플러그인이 pane.id 로 찜해 둔 pane 목록. 그 pane 은 건드리지 않는다."""
    plugins_dir = os.path.dirname(os.path.abspath(state_dir))
    own = os.path.basename(os.path.abspath(state_dir))
    claimed = set()
    for name in os.listdir(plugins_dir) if os.path.isdir(plugins_dir) else []:
        if name == own:
            continue
        try:
            with open(os.path.join(plugins_dir, name, "pane.id"), encoding="utf-8") as f:
                claimed.add(f.read().strip())
        except OSError:
            pass
    return claimed


def pick_pane(panes, stored_pane, agent_panes, claimed=frozenset()):
    """dock 안에서 host 를 띄울 pane. 기억해 둔 pane 이 살아 있고 다른 플러그인이 찜하지 않았으면 그것,
    아니면 빈 pane 하나(다른 플러그인이 찜하지 않은 것). 없으면 None 이고 호출한 쪽이 split 한다."""
    ids = [p["pane_id"] for p in panes]
    if stored_pane in ids and stored_pane not in claimed:
        return stored_pane
    free = [p["pane_id"] for p in panes
            if not p.get("label") and not p.get("tokens") and p["pane_id"] not in agent_panes
            and p["pane_id"] not in claimed]
    return free[0] if free else None


def ensure_workspace(state):
    """공용 dock workspace 와 그 안의 radio pane 을 확보한다."""
    workspaces = herdr_api.cli("workspace", "list").get("workspaces", [])
    workspace_id = find_workspace(workspaces)
    if workspace_id is None:
        created = herdr_api.cli("workspace", "create", "--label", DOCK_LABEL, "--cwd", state.directory, "--no-focus")
        workspace_id = created["workspace"]["workspace_id"]
        state.remove("pane.id")
    state.write("workspace.id", workspace_id)
    panes = workspace_panes(workspace_id)
    agent_panes = {a["pane_id"] for a in herdr_api.cli("agent", "list").get("agents", [])}
    pane_id = pick_pane(panes, state.read("pane.id"), agent_panes, claimed_by_others(state.directory))
    if pane_id is None:
        anchor = panes[0]["pane_id"] if panes else None
        if anchor is None:
            raise herdr_api.HerdrError(f"workspace {workspace_id} has no pane")
        split = herdr_api.cli("pane", "split", anchor, "--direction", "down", "--cwd", state.directory)
        pane_id = split["pane"]["pane_id"]
    state.write("pane.id", pane_id)
    return workspace_id, pane_id


def keep_at_bottom(workspace_id):
    workspaces = herdr_api.request("workspace.list", {}).get("workspaces", [])
    ids = [w["workspace_id"] for w in workspaces]
    if workspace_id not in ids:
        return
    if ids[-1] != workspace_id:
        herdr_api.try_request("workspace.move", {"workspace_id": workspace_id, "insert_index": len(ids)})


# ---------------------------------------------------------------- host (dock pane 안)


def short_name(name):
    name = name.strip() or "?"
    return name if len(name) <= NAME_WIDTH else name[: NAME_WIDTH - 1] + "…"


def host_command(state_dir, config_dir, pane_id):
    script = os.path.abspath(__file__)
    command = [sys.executable, "-X", "utf8", script, "host", "--state", state_dir, "--pane", pane_id]
    if config_dir:
        command += ["--config", config_dir]
    return command


def start_detached(state_dir, command):
    """host 를 pane 밖의 분리 프로세스로 띄운다. dock pane 은 목록(menu)이 쓴다.

    콘솔 창은 만들지 않고, 오류는 host.log 에 남긴다 (DEVNULL 이면 죽은 이유를 알 수 없다)."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    log = open(os.path.join(state_dir, "host.log"), "a", encoding="utf-8")
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        **kwargs,
    )


def cmd_ensure(args):
    state = State(args.state)
    if state.host_alive():
        return 0
    _, pane_id = ensure_workspace(state)
    # 사이드바 토큰과 agent 등록을 맡는 host 는 pane 밖에서 돈다.
    start_detached(args.state, host_command(args.state, args.config, pane_id))
    # dock pane 에는 방송국 목록을 띄운다. 번호를 치면 바로 재생된다.
    herdr_api.cli("pane", "run", pane_id, *menu_command(args.state, args.config))
    return 0


def menu_command(state_dir, config_dir):
    script = os.path.abspath(__file__)
    command = [sys.executable, "-X", "utf8", script, "menu", "--state", state_dir]
    if config_dir:
        command += ["--config", config_dir]
    return command


class Host:
    """메인 루프(1초)는 heartbeat 와 토큰 갱신만 한다.
    재생 확인과 agent 등록(socket 대기, PowerShell)은 느릴 수 있어서 워커 스레드가 맡는다.
    워커가 멈춰도 토큰은 마지막 값으로 계속 나간다."""

    def __init__(self, args):
        self.state = State(args.state)
        self.pane_id = args.pane
        self.workspace_id = self.state.read("workspace.id")
        self.socket_failures = 0
        self.playing = False
        self.station = None
        self.failed = False
        self.lock = threading.Lock()
        self.stopping = threading.Event()

    def refresh_status(self):
        playing = is_playing(self.state)
        station = last_station(self.state)
        failed = self.state.read("last_end") == "failed"
        with self.lock:
            self.playing = playing
            self.station = station
            self.failed = failed

    def snapshot(self):
        with self.lock:
            return self.playing, self.station, self.failed

    def report(self):
        playing, station, failed = self.snapshot()
        if playing and station:
            now = short_name(station["name"])
            tokens = {"rd_now": now, "rd_state": i18n.t("token.playing")}
        elif failed and station:
            # 재생이 실패했을 때는 방송 이름과 함께 실패를 보여 준다
            tokens = {"rd_now": short_name(station["name"]), "rd_state": i18n.t("token.failed")}
        else:
            tokens = {"rd_now": "-", "rd_state": i18n.t("token.stopped")}
        ok = herdr_api.try_request("pane.report_metadata", {
            "pane_id": self.pane_id,
            "source": SOURCE,
            "display_agent": DISPLAY_AGENT,
            "tokens": tokens,
            "ttl_ms": TOKEN_TTL_MS,
        })
        self.socket_failures = 0 if ok else self.socket_failures + 1

    def register_agent(self):
        playing, _, _ = self.snapshot()
        herdr_api.try_request("pane.report_agent", {
            "pane_id": self.pane_id,
            "source": SOURCE,
            "agent": AGENT_ID,
            "state": "working" if playing else "idle",
        })
        if self.workspace_id:
            try:
                keep_at_bottom(self.workspace_id)
            except (herdr_api.HerdrError, ValueError):
                pass

    def worker(self):
        """재생 확인과 agent 등록을 LAYOUT 주기마다 한다. 메인 루프와 따로 돈다."""
        while not self.stopping.is_set():
            try:
                self.refresh_status()
                self.register_agent()
            except OSError:
                pass  # 다음 주기에 다시 시도한다
            self.stopping.wait(LAYOUT_EVERY_TICKS * TICK_SECONDS)

    def run(self):
        self.state.remove("starting")
        threading.Thread(target=self.worker, daemon=True).start()
        try:
            while self.socket_failures < 10:
                self.state.touch_heartbeat()
                self.report()
                time.sleep(TICK_SECONDS)
        finally:
            self.stopping.set()
            herdr_api.try_request("pane.release_agent", {"pane_id": self.pane_id, "source": SOURCE, "agent": AGENT_ID})
            self.state.remove("heartbeat")


def cmd_host(args):
    try:
        Host(args).run()
    except KeyboardInterrupt:
        pass  # Ctrl+C 로 직접 멈춘 것이므로 트레이스백 없이 끝낸다
    return 0


# ---------------------------------------------------------------- 액션


def cmd_start(args):
    state = State(args.state)
    if is_playing(state):
        print(i18n.t("msg.already_playing"))
        cmd_ensure(args)
        return 0
    station = last_station(state)
    if station is None:
        print(i18n.t("msg.no_station"))
        return 1
    try:
        play(state, station)
    except RuntimeError as error:
        print(error)
        return 1
    print(i18n.t("msg.playing", name=station["name"]))
    cmd_ensure(args)
    return 0


def cmd_stop(args):
    state = State(args.state)
    print(i18n.t("msg.stopped") if stop(state) else i18n.t("msg.not_playing"))
    return 0


def cmd_status(args):
    state = State(args.state)
    station = last_station(state)
    label = station["name"] if station else "-"
    print(f"{i18n.t('state.playing' if is_playing(state) else 'state.stopped')}: {label}")
    return 0


def station_lines(options):
    if not options:
        return [i18n.t("menu.empty")]
    lines = []
    for index, station in enumerate(options, 1):
        country = f" ({station['country']})" if station.get("country") else ""
        lines.append(f"{index:2}. {station['name']}{country}")
    return lines


def print_stations(options):
    for line in station_lines(options):
        print(line)


def play_and_report(args, station):
    try:
        play(State(args.state), station)
    except RuntimeError as error:
        print(error)
        return False
    cmd_ensure(args)
    print(i18n.t("msg.playing", name=station["name"]))
    return True


def save_station(station):
    """검색한 방송을 config.json 의 stations 에 추가한다. 이미 있으면 False."""
    os.makedirs(config_dir_path(), exist_ok=True)
    path = os.path.join(config_dir_path(), "config.json")
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict) or not isinstance(data.get("stations"), list):
        data = {"stations": []}
    if any(isinstance(item, dict) and item.get("url") == station["url"] for item in data["stations"]):
        return False
    data["stations"].append({"name": station["name"], "url": station["url"]})
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return True


def step_list(current):
    """next/prev 가 돌 목록. 지금 방송이 config.json 에 있으면 config.json, 추천 장르에 있으면 그 장르."""
    stations = load_stations()
    url = current.get("url") if current else None
    if url and url not in (s["url"] for s in stations):
        for genre in load_genres():
            if any(s["url"] == url for s in genre["stations"]):
                return genre["stations"]
    return stations


def cmd_step(args, delta):
    """지금 방송이 든 목록에서 다음(delta=1) 또는 이전(delta=-1) 방송을 튼다."""
    current = last_station(State(args.state))
    stations = step_list(current)
    if not stations:
        print(i18n.t("msg.step_none"))
        return 1
    urls = [s["url"] for s in stations]
    if current and current.get("url") in urls:
        index = (urls.index(current["url"]) + delta) % len(stations)
    else:
        index = 0 if delta > 0 else len(stations) - 1
    return 0 if play_and_report(args, stations[index]) else 1


def cmd_next(args):
    return cmd_step(args, 1)


def cmd_prev(args):
    return cmd_step(args, -1)


def cmd_play(args):
    """config.json 의 N번째 방송을 재생한다. 방송국별 액션이 이 명령을 부른다."""
    stations = load_stations()
    index = args.index
    if not 1 <= index <= len(stations):
        print(i18n.t("msg.no_index", index=index, count=len(stations)))
        return 1
    return 0 if play_and_report(args, stations[index - 1]) else 1


def clear_screen():
    # 매번 화면을 지우고 다시 그린다. 셸 기록이나 이전 출력이 목록 아래에 남지 않게 한다.
    sys.stdout.write("\x1b[H\x1b[2J")


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def display_width(text):
    """터미널에서 차지하는 칸 수. 한글과 전각 문자는 두 칸으로 센다."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def panel(*sections, min_inner=44, max_inner=70):
    """timekit 패널처럼 테두리 상자에 담아 출력한다. 섹션 사이는 가로줄로 나눈다.
    각 섹션은 줄 목록이고, 한 문자열 안의 줄바꿈도 줄로 나눈다. ANSI 색 코드는 칸 수에서 뺀다."""
    rows = []
    for index, section in enumerate(sections):
        if index:
            rows.append(None)
        for line in section:
            rows += (line.splitlines() or [""])
    widths = [display_width(ANSI_RE.sub("", row)) for row in rows if row is not None]
    inner = min(max_inner, max([min_inner] + [w + 2 for w in widths]))
    print("╭" + "─" * inner + "╮")
    for row in rows:
        if row is None:
            print("├" + "─" * inner + "┤")
            continue
        width = display_width(ANSI_RE.sub("", row))
        print("│ " + row + " " * max(0, inner - 1 - width) + "│")
    print("╰" + "─" * inner + "╯")


def search_and_pick(args, keyword):
    try:
        options = search(keyword) if keyword else []
    except RuntimeError as error:
        print(error)
        return
    if not options:
        print(i18n.t("menu.no_results"))
        return
    print_stations(options)
    pick_station(args, options, input(i18n.t("menu.pick_result_add")))


def pick_station(args, options, picked, can_save=True):
    """번호 = 재생, a 번호 = config.json 에 저장. 처리했으면 True."""
    picked = picked.strip().lower()
    if can_save and picked.startswith("a ") and picked[2:].strip().isdigit():
        number = int(picked[2:].strip())
        if 1 <= number <= len(options):
            station = options[number - 1]
            saved = save_station(station)
            print(i18n.t("msg.saved" if saved else "msg.exists", name=station["name"]))
            return True
        return False
    if picked.isdigit() and 1 <= int(picked) <= len(options):
        play_and_report(args, options[int(picked) - 1])
        return True
    return False


def station_menu(args, title, options, can_save):
    """한 장르(또는 config.json)의 방송 목록. b 나 빈 입력이면 장르 목록으로 돌아간다."""
    state = State(args.state)
    while True:
        clear_screen()
        panel(
            [f"=== {title} ==="],
            station_lines(options),
            [i18n.t("menu.genre_help_save" if can_save else "menu.genre_help").strip()],
        )
        choice = input("> ").strip()
        if choice in ("", "b"):
            return
        if choice == "s":
            print(i18n.t("msg.stopped") if stop(state) else i18n.t("msg.not_playing"))
            continue
        if not pick_station(args, options, choice, can_save):
            print(i18n.t("menu.unknown"))


def menu(args):
    """장르 목록을 보여 주고, 장르를 고르면 그 장르의 추천 방송을 보여 준다. 명령:
    번호 = 장르 선택, s = 정지, k 키워드 = Radio Browser 검색, q = 닫기"""
    state = State(args.state)
    while True:
        clear_screen()
        genres = load_genres()
        stations = load_stations()
        # 마지막 항목은 사용자가 config.json 에 넣은 방송국이다.
        entries = [(g["name"], g["stations"], True) for g in genres]
        entries.append((i18n.t("menu.my_stations", count=len(stations)), stations, False))
        panel(
            [i18n.t("menu.genres_title")],
            [f"{index:2}. {name}" for index, (name, _, _) in enumerate(entries, 1)],
            [i18n.t("menu.help").strip()],
        )
        choice = input("> ").strip()

        if choice in ("", "q"):
            # 목록 pane 은 닫히지 않게 다시 그린다. 정지는 s, 종료는 Ctrl+C 또는 pane 닫기.
            print()
            continue
        if choice == "s":
            print(i18n.t("msg.stopped") if stop(state) else i18n.t("msg.not_playing"))
            continue
        if choice.startswith("k "):
            search_and_pick(args, choice[2:].strip())
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(entries):
            station_menu(args, *entries[int(choice) - 1])
            continue
        print(i18n.t("menu.unknown"))


def safe_menu(args):
    """Ctrl+C 나 pane 닫기(입력 종료)로 끝날 때 트레이스백 없이 끝낸다."""
    try:
        return menu(args)
    except (KeyboardInterrupt, EOFError):
        return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="radio.py")
    parser.add_argument("command", nargs="?", default="menu",
                        choices=["ensure", "host", "start", "stop", "menu", "status", "play", "next", "prev", "volume-up", "volume-down"])
    parser.add_argument("index", nargs="?", type=int, default=0)
    parser.add_argument("--state", default=state_dir_path())
    parser.add_argument("--config", default=os.environ.get("HERDR_PLUGIN_CONFIG_DIR") or "")
    parser.add_argument("--pane", default=os.environ.get("HERDR_PANE_ID"))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    # --config 로 받은 폴더를 환경변수에 넣어, 모든 경로가 같은 설정을 보게 한다.
    if args.config:
        os.environ["HERDR_PLUGIN_CONFIG_DIR"] = args.config
    commands = {
        "ensure": cmd_ensure,
        "host": cmd_host,
        "start": cmd_start,
        "stop": cmd_stop,
        "menu": safe_menu,
        "status": cmd_status,
        "play": cmd_play,
        "next": cmd_next,
        "volume-up": cmd_volume_up,
        "volume-down": cmd_volume_down,
        "prev": cmd_prev,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
