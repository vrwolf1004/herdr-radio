# herdr-radio

[**English**](README.md) | [한국어](README.ko.md)

UI languages: English · Korean · Russian · French · Spanish · German · Japanese

Search Radio Browser or play saved stations without managing a player window. Playback status appears in herdr's sidebar.

## Dashboard design

Agents sidebar:

```text
 ● radio
   ▶ playing
   Jazz Radio Bl…
```

Radio menu:

```text
╭────────────────────────────────────────────────────────────╮
│                    🐺  herdr-radio  🌕                     │
├────────────────────────────────────────────────────────────┤
│  1. Jazz                                                   │
│  2. Classical                                              │
│  3. K-pop                                                  │
│  4. Lo-fi                                                  │
│  5. News                                                   │
│  6. My stations (config.json, 2)                           │
├────────────────────────────────────────────────────────────┤
│ [Number] genre   [s] stop   [k keyword] search   [q] close │
╰────────────────────────────────────────────────────────────╯
```

## Installation

```sh
herdr plugin install vrwolf1004/herdr-radio --yes
```

## Actions

| Action | What it does |
| --- | --- |
| `start` / `stop` | Start the last station or stop playback |
| `menu` | Browse genres, search Radio Browser, and choose or save stations |
| `play-1` … `play-6` | Play a station from your configured list |
| `next` / `prev` | Play the next or previous station |
| `volume-up` / `volume-down` | Change mpv volume by 5 |

On Windows, append `-windows` to each action ID. See the [usage guide](docs/usage.md) for player installation and configuration.

## Requirements

- Windows, Linux, or macOS
- herdr 0.9.0 or later
- Python 3.8 or later; standard library only
- mpv or ffplay

## Documentation

- [Usage guide (English)](docs/usage.md)
- [사용법 (한국어)](docs/usage.ko.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development](docs/development.md)
- [Architecture](docs/architecture.md)
- [TODO](docs/todo.md)

## License

Undecided. `herdr_api.py` is taken from [herdr-ai-feedbag](https://github.com/vrwolf1004/herdr-ai-feedbag) (MIT).

## Support the project

If this project is useful to you, consider buying the developer a coffee.

[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
