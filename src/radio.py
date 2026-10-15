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
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import herdr_api
import i18n

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
    return os.environ.get("HERDR_PLUGIN_CONFIG_DIR") or state_dir_path()


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


def load_stations():
    """config.json 의 stations 를 읽는다. 항목은 {"name": ..., "url": ...} 이다."""
    path = os.path.join(config_dir_path(), "config.json")
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return []
    stations = []
    for item in data.get("stations", []):
        url = (item.get("url") or "").strip()
        if url:
            stations.append({"name": (item.get("name") or url).strip(), "url": url, "country": ""})
    return stations


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
        except OSError as error:
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


def player_pids():
    """이 플러그인이 띄운 플레이어 프로세스 pid 목록.

    pid 파일은 상태 폴더가 어긋나면 사라질 수 있으므로, 명령줄의 마커로 직접 찾는다.
    """
    if os.name == "nt":
        script = (
            "Get-CimInstance Win32_Process -Filter \"Name='mpv.exe' OR Name='ffplay.exe'\" | "
            f"Where-Object {{ $_.CommandLine -like '*{PLAYER_MARKER}*' }} | "
            "ForEach-Object { $_.ProcessId }"
        )
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True,
        ).stdout
        return [int(line) for line in out.split() if line.isdigit()]
    out = subprocess.run(["pgrep", "-f", PLAYER_MARKER], capture_output=True, text=True).stdout
    return [int(line) for line in out.split() if line.isdigit() and int(line) != os.getpid()]


def is_playing(state):
    if player_pids():
        return True
    state.remove("player.pid")  # 플레이어가 없으면 남은 기록을 지운다
    return False


def stop(state):
    pids = set(player_pids())
    raw = state.read("player.pid")
    if raw and raw.isdigit():
        pids.add(int(raw))
    state.remove("player.pid")
    for pid in pids:
        if os.name == "nt":
            # /T 로 자식 프로세스까지 함께 끝낸다.
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    return bool(pids)


def play(state, station):
    # 이전 재생이 있으면 먼저 끊는다.
    stop(state)
    name, path = find_player()
    if not path:
        raise RuntimeError(i18n.t("error.no_player"))
    if name == "mpv":
        args = [path, "--no-video", "--no-terminal", "--really-quiet", f"--title={PLAYER_MARKER}", station["url"]]
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
    return proc.pid


def last_station(state):
    raw = state.read("station.json")
    if raw:
        try:
            return json.loads(raw)
        except ValueError:
            pass
    stations = load_stations()
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


def pick_pane(panes, stored_pane, agent_panes):
    """dock 안에서 host 를 띄울 pane. 기억해 둔 pane 이 살아 있으면 그것, 아니면 빈 pane 하나."""
    ids = [p["pane_id"] for p in panes]
    if stored_pane in ids:
        return stored_pane
    free = [p["pane_id"] for p in panes
            if not p.get("label") and not p.get("tokens") and p["pane_id"] not in agent_panes]
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
    pane_id = pick_pane(panes, state.read("pane.id"), agent_panes)
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


def start_detached(command):
    """host 를 pane 밖의 분리 프로세스로 띄운다. dock pane 은 목록(menu)이 쓴다."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def cmd_ensure(args):
    state = State(args.state)
    if state.host_alive():
        return 0
    _, pane_id = ensure_workspace(state)
    # 사이드바 토큰과 agent 등록을 맡는 host 는 pane 밖에서 돈다.
    start_detached(host_command(args.state, args.config, pane_id))
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
    def __init__(self, args):
        self.state = State(args.state)
        self.pane_id = args.pane
        self.workspace_id = self.state.read("workspace.id")
        self.socket_failures = 0
        self.playing = False
        self.station = None

    def refresh_status(self):
        self.playing = is_playing(self.state)
        self.station = last_station(self.state)

    def report(self):
        if self.playing and self.station:
            now = short_name(self.station["name"])
            tokens = {"rd_now": now, "rd_state": i18n.t("token.playing")}
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
        herdr_api.try_request("pane.report_agent", {
            "pane_id": self.pane_id,
            "source": SOURCE,
            "agent": AGENT_ID,
            "state": "working" if self.playing else "idle",
        })
        if self.workspace_id:
            try:
                keep_at_bottom(self.workspace_id)
            except (herdr_api.HerdrError, ValueError):
                pass

    def run(self):
        self.state.remove("starting")
        tick = 0
        try:
            while self.socket_failures < 10:
                self.state.touch_heartbeat()
                if tick % LAYOUT_EVERY_TICKS == 0:
                    self.refresh_status()
                    self.register_agent()
                self.report()
                tick += 1
                time.sleep(TICK_SECONDS)
        finally:
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


def print_stations(options):
    for index, station in enumerate(options, 1):
        country = f" ({station['country']})" if station.get("country") else ""
        print(f"{index:2}. {station['name']}{country}")


def play_and_report(args, station):
    try:
        play(State(args.state), station)
    except RuntimeError as error:
        print(error)
        return False
    cmd_ensure(args)
    print(i18n.t("msg.playing", name=station["name"]))
    return True


def cmd_play(args):
    """config.json 의 N번째 방송을 재생한다. 방송국별 액션이 이 명령을 부른다."""
    stations = load_stations()
    index = args.index
    if not 1 <= index <= len(stations):
        print(i18n.t("msg.no_index", index=index, count=len(stations)))
        return 1
    return 0 if play_and_report(args, stations[index - 1]) else 1


def menu(args):
    """방송국 목록을 보여 주고 번호로 재생한다. 명령:
    번호 = 재생, s = 정지, k 키워드 = Radio Browser 검색, q = 닫기"""
    state = State(args.state)
    while True:
        stations = load_stations()
        print(i18n.t("menu.title"))
        if stations:
            print_stations(stations)
        else:
            print(i18n.t("menu.empty"))
        print(i18n.t("menu.help"))
        choice = input("> ").strip()

        if choice in ("", "q"):
            # 목록 pane 은 닫히지 않게 다시 그린다. 정지는 s, 종료는 Ctrl+C 또는 pane 닫기.
            print()
            continue
        if choice == "s":
            print(i18n.t("msg.stopped") if stop(state) else i18n.t("msg.not_playing"))
            continue
        if choice.startswith("k "):
            keyword = choice[2:].strip()
            try:
                options = search(keyword) if keyword else []
            except RuntimeError as error:
                print(error)
                continue
            if not options:
                print(i18n.t("menu.no_results"))
                continue
            print_stations(options)
            picked = input(i18n.t("menu.pick_result")).strip()
            if picked.isdigit() and 1 <= int(picked) <= len(options):
                play_and_report(args, options[int(picked) - 1])
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(stations):
            play_and_report(args, stations[int(choice) - 1])
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
                        choices=["ensure", "host", "start", "stop", "menu", "status", "play"])
    parser.add_argument("index", nargs="?", type=int, default=0)
    parser.add_argument("--state", default=state_dir_path())
    parser.add_argument("--config", default=os.environ.get("HERDR_PLUGIN_CONFIG_DIR") or "")
    parser.add_argument("--pane", default=os.environ.get("HERDR_PANE_ID"))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    commands = {
        "ensure": cmd_ensure,
        "host": cmd_host,
        "start": cmd_start,
        "stop": cmd_stop,
        "menu": safe_menu,
        "status": cmd_status,
        "play": cmd_play,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
