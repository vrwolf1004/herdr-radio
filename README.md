# herdr-radio

[**English**](README.md) | [한국어](README.ko.md)

Search [Radio Browser](https://www.radio-browser.info/) stations or play the ones you saved, with no window to manage. The herdr sidebar's bottom block (`herdr-dock`) shows what is playing and whether playback is running.

- Windows, Linux, and macOS
- Python 3.8+; standard library only
- [mpv](https://mpv.io/) or ffplay
- herdr 0.9.0+
- 7 languages: English, Korean, Japanese, Russian, French, Spanish, German

Sidebar block:

```text
 ● radio
   ▶ playing
   Jazz Radio Bl…
```

Menu (the `radio` pane):

```text
=== Stations (config.json) ===
 1. Jazz Radio Blues
 2. Adroit Jazz Underground

Number: play  |  s: stop  |  k keyword: search  |  q: close
>
```

## Install

```sh
herdr plugin install vrwolf1004/herdr-radio
```

Then save a few stations and add the radio rows to herdr's `config.toml`. See the [usage guide](docs/usage.md).

To develop from a local copy:

```sh
git clone https://github.com/vrwolf1004/herdr-radio.git
herdr plugin link ./herdr-radio
```

### Install a player

- **Windows:** `winget install shinchiro.mpv` (the command-line build). `mpv.net` is GUI-only and has no `mpv` command.
- **macOS:** `brew install mpv`
- **Linux:** install `mpv` with your package manager.

## Configure stations

Open the config folder with `herdr plugin config-dir herdr-radio` and edit `config.json`. See [config.example.json](config.example.json) for the format.

```json
{
  "stations": [
    { "name": "Jazz Radio Blues", "url": "http://jazzblues.ice.infomaniak.ch/jazzblues-high.mp3" }
  ]
}
```

## Sidebar rows

herdr draws only the tokens listed in your sidebar layout. Add these rows to `[ui.sidebar.agents]` in `config.toml`, then run `herdr server reload-config`:

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", "machine", { token = "workspace", rules = [{ equals = "herdr-dock", hide = true }] }, "tab"],
  ["agent"],
  [{ token = "$rd_state", fg = "#1db954" }],
  [{ token = "$rd_now", fg = "#9aa0a6" }],
]
```

- The `$rd_*` tokens appear only on the radio block, so other agent rows are unaffected.
- `herdr-dock` is the shared workspace used by herdr-ai-feedbag. If both plugins are installed, their blocks share the dock, and herdr-ai-feedbag keeps the dock at the bottom.
- Keep `ui.agent_panel_sort` at its default, `"spaces"`.

## Actions

| Action | Description |
| --- | --- |
| `start` | Plays the last station again. If there is none, plays the first station in `config.json` |
| `stop` | Stops playback. The block stays and shows `■ stopped` |
| `menu` | Opens the station pane. Type a keyword to search Radio Browser, or press Enter to see your `config.json` list |
| `play-1` … `play-6` | Plays the Nth station in `config.json` |
| `next` / `prev` | Plays the next or previous station in `config.json` |
| `volume-up` / `volume-down` | Changes the volume of the running mpv by 5 (mpv only) |

On Windows, append `-windows` to each action id:

```sh
herdr plugin action invoke start-windows --plugin herdr-radio   # windows
herdr plugin action invoke start --plugin herdr-radio           # linux / macos
```

## Language

The menu and sidebar text follow the first match in this list:

1. The `HERDR_RADIO_LANG` environment variable (for example, `en`)
2. The `"lang"` value in `config.json`
3. Your OS language
4. English, if the OS language is not supported

## Notes

- The plugin runs with your user permissions and no sandbox. Read the code before installing.
- Each stream has its own terms of use. Use it for personal listening.
- Stream addresses change often. If a station stops working, search for it again in `menu`.
- Closing the pane does not stop playback. Use the `stop` action to turn it off.

## Documentation

- [Usage guide (English)](docs/usage.md)
- [Architecture](docs/architecture.md)
- [TODO](docs/todo.md)

Korean documents are in the same `docs/` folder. The Korean README is [README.ko.md](README.ko.md).

## License

Undecided. `herdr_api.py` is taken from [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag) (MIT).

---

## Support the project

If this project is useful to you, consider buying the developer a coffee.

[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
