# Usage

herdr-radio plays Radio Browser stations with no window, and shows the playback state in the bottom block of the herdr sidebar. For installation and the basic idea, see the [README](../README.md). This guide covers configuration and everyday use.

## 1. Installation and requirements

```sh
herdr plugin install vrwolf1004/herdr-radio --yes
```

For development from a local copy, use `link`:

```sh
herdr plugin link C:/work/app/herdr-radio
```

- Python 3.8 or later (standard library only)
- mpv or ffplay
  - Windows: `winget install shinchiro.mpv` installs the command-line build. `mpv.net` is GUI-only and has no `mpv` command.
  - If `winget` is unavailable on Windows, put `mpv.exe` at `C:\Program Files\mpv\mpv.exe`; the plugin checks this path too.
  - macOS: `brew install mpv`
  - Linux: install `mpv` with your package manager

If Python is not on PATH, the plugin will not run. Check with `python --version`. The herdr server inherits PATH at startup, so restart it after changing PATH.

## 2. Registering stations

Find the config folder with:

```sh
herdr plugin config-dir herdr-radio
```

Put stations in `config.json` in that folder. The format follows [config.example.json](../config.example.json).

```json
{
  "stations": [
    { "name": "Jazz Radio Blues", "url": "http://jazzblues.ice.infomaniak.ch/jazzblues-high.mp3" }
  ]
}
```

- `name` is shown in the sidebar and the menu. If omitted, the URL is used.
- Entries with an empty `url` are ignored.
- No restart is needed after editing the file. The menu and the `play-N` actions read it every time.

### Changing the recommended genres

The menu's genres and recommended stations live in [src/genres.json](../src/genres.json) inside the plugin. To change them, add a `genres` list in the same format to `config.json`. When `genres` is present, the menu shows it instead of the built-in list.

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

The `play-N` actions play the Nth entry of `stations`, not of `genres`.

## 3. Sidebar rows

herdr draws only the tokens listed in `config.toml`. Add the radio rows to `[ui.sidebar.agents]`:

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", "machine", { token = "workspace", rules = [{ equals = "herdr-dock", hide = true }] }, "tab"],
  ["agent"],
  [{ token = "$rd_state", fg = "#1db954" }],
  [{ token = "$rd_now", fg = "#9aa0a6" }],
]
```

If you also use herdr-ai-feedbag, both blocks share the same `herdr-dock` workspace. Add the `$fb_*` rows to the same `rows` list. Then run `herdr server reload-config`.

- The `$rd_*` tokens appear only on the radio block, so other agent rows are not affected.
- If playback ends without a stop (connection failure, broken stream), the block shows `✖ failed` and the station name. Stopping or starting playback again clears it.
- The dock stays at the bottom through herdr-ai-feedbag if it is installed. Without it, the radio worker moves the dock back to the bottom every 5 seconds.
- Keep `ui.agent_panel_sort` at its default, `"spaces"`.

Block example:

```text
 ● radio
   ▶ playing
   Jazz Radio Bl…
```

The radio pane in the dock shows the station menu. The host loop that updates the sidebar runs as a detached process outside the pane, so the sidebar keeps updating after you close the menu.

## 4. Actions

| Action (Windows) | Action (Linux/macOS) | Description |
| --- | --- | --- |
| `start-windows` | `start` | Plays the last station again. If there is none, plays the first station in `config.json` (or the first recommended station) |
| `stop-windows` | `stop` | Stops playback. The block stays and shows `■ stopped` |
| `menu-windows` | `menu` | Opens the station pane |
| `play-N-windows` | `play-N` | Plays the Nth station in `config.json` (N = 1 to 6) |
| `next-windows` | `next` | Plays the next station in the list the current station is in (`config.json` or a recommended genre). After the last one, it wraps to the first |
| `prev-windows` | `prev` | Plays the previous station. Before the first one, it wraps to the last |
| `volume-up-windows` | `volume-up` | Raises the volume of the running mpv by 5 (mpv only) |
| `volume-down-windows` | `volume-down` | Lowers the volume of the running mpv by 5 (mpv only) |

Examples:

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## 5. Using the menu

The `menu` pane accepts these inputs:

| Input | What it does |
| --- | --- |
| number | Opens that genre. The last entry, `My stations`, is your `config.json` list |
| `s` | Stops playback |
| `k keyword` | Searches Radio Browser. Enter a result number to play it |
| `a number` | Saves that search result to `config.json` without playing it. Reports if it is already saved |
| `q` or Enter | Redraws the menu (the pane stays open) |

A genre shows 5 recommended stations and accepts these inputs:

| Input | What it does |
| --- | --- |
| number | Plays that station |
| `a number` | Saves that station to `config.json` (not available in `My stations`) |
| `s` | Stops playback |
| `b` or Enter | Goes back to the genre list |

The recommended stations were checked to play in October 2026. If one stops working, search for it with `k station name` to get a current address.

Search returns up to 10 results, ordered by click count, with broken stations hidden. Stream addresses change often, so search again if a station stops working.

The screen is cleared and redrawn on each input. Ctrl+C closes the menu and returns you to a PowerShell prompt.

## 6. Troubleshooting

- **`mpv 또는 ffplay가 필요합니다` (mpv or ffplay is required)**: the player is not on PATH. Install it as in section 1 and restart the server.
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

## 7. Notes

- The plugin runs with your user permissions and no sandbox. Read the code before installing.
- Each stream has its own terms of use. Use it for personal listening.
