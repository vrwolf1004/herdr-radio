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
  - If `winget` is unavailable on Windows, put `mpv.exe` at `C:\Program Files\mpv\mpv.exe` or `C:\Program Files\MPV Player\mpv.exe`; the plugin checks both paths.
  - macOS: `brew install mpv`
  - Linux: install `mpv` with your package manager

If Python is not on PATH, the plugin will not run. Check with `python --version`. The herdr server inherits PATH at startup, so restart it after changing PATH.

On Windows, if the menu cannot find either player, it displays an `i` prompt. Pressing it runs `winget install shinchiro.mpv` in the pane. Close and reopen the menu when the installation finishes so the player is detected.

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

Type an input in the `menu` pane and press Enter. The genre list and the station list share one table. Inputs are read as whole lines, so Korean jamo keys such as `ㅅ` do not work here.

| Input | Genre list | Station list |
| --- | --- | --- |
| number | Opens that genre. The last entry, `My stations`, is your `config.json` list | Plays that station |
| `a number` | — | Saves that station to `config.json` without playing it (not available in `My stations`) |
| `s` | Stops playback | Stops playback |
| `k keyword` | Searches Radio Browser. Enter a result number to play it | — |
| `i` | On Windows, installs mpv with `winget` when neither mpv nor ffplay is found | — |
| `b` or Enter | — | Goes back to the genre list |
| `q` or Enter | Redraws the menu (the pane stays open) | — |

A genre shows 5 recommended stations. After `k keyword` search, enter a result number to play it or `a number` to save it to `config.json`.

The recommended stations were checked to play in October 2026. If one stops working, search for it with `k station name` to get a current address.

Search returns up to 10 results, ordered by click count, with broken stations hidden. Stream addresses change often, so search again if a station stops working.
Search results are cached in `search-cache.json` in the plugin state folder for 10 minutes per normalized keyword (case-insensitive, surrounding whitespace ignored). Repeating a search during that window reuses its saved results.
The search server that answered last is tried first. This memory is kept only while the program runs; it is lost when the program is restarted.
If every search server fails, the menu shows only a short message ("Could not reach the Radio Browser server"). The full error text is written as one line in `host.log` in the state folder; see [troubleshooting.md](troubleshooting.md).

The list is redrawn in the same place, so old screens do not pile up in the scrollback. On the station list, a cassette picture is drawn above the list (its reels turn while a station plays). If the pane is too short for the whole screen, the cassette picture is hidden so the list still fits. Enlarge the pane to see it again. Ctrl+C closes the menu and returns you to a PowerShell prompt.

## 6. Troubleshooting

Common problems and checks are in [troubleshooting.md](troubleshooting.md) (Korean items first, then English).

## 7. Notes

- The plugin runs with your user permissions and no sandbox. Read the code before installing.
- Each stream has its own terms of use. Use it for personal listening.

## Documentation

- [Usage (한국어)](usage.ko.md)
- [Troubleshooting](troubleshooting.md): common problems (Korean, with English items)
- [Architecture](architecture.md): how the block works (Korean)
- [Development](development.md): code layout, checks, adding stations and actions (Korean)
- [TODO](todo.md): improvement list (Korean)
