# herdr-radio

[**English**](README.md) | [한국어](README.ko.md)

UI languages: English · Korean · Russian · French · Spanish · German · Japanese

Search Radio Browser or play saved stations without managing a player window. Playback status appears in herdr's sidebar.
The startup/workspace `ensure` check verifies that the radio pane exists, so it can restore the block after the pane is closed.

## Dashboard design

Agents sidebar: `radio > <station>` while playing, `radio` when stopped.

Radio menu (main screen):

```text
╭────────────────────────────────────────────────────╮
│                🐺  herdr-radio  🌕                 │
├────────────────────────────────────────────────────┤
│             ╭─╮          ╭─╮                       │
│             │|│ ▓▒░░▒▓▓▒░ │|│                       │
│             ╰─╯          ╰─╯                       │
│                  ▶ PLAY                            │
├────────────────────────────────────────────────────┤
│ === Genres ===                                     │
│  1. Jazz                                           │
│  2. Classical                                      │
│  3. K-pop                                          │
│  4. Rock / Blues                                   │
│  5. Ambient / Chill                                │
│  6. News                                           │
├────────────────────────────────────────────────────┤
│ playing: Jazz Radio                 Ctrl+H help    │
╰────────────────────────────────────────────────────╯
```

Press `Ctrl+H` to open the help popup over the list. Press `Ctrl+H` again to close it:

```text
        ╭──────────────────────────────────────╮
        │             Ctrl+H help              │
        ├──────────────────────────────────────┤
        │ [number] genre   [s] stop            │
        │ [k keyword] search   [t] theme       │
        │ [l] language   [Ctrl+C] quit         │
        ╰──────────────────────────────────────╯
```

Station screen (after choosing a genre): the same cassette and bottom line, with the station list. `Ctrl+H` shows `[number] play   [b] back   [s] stop   [a number] save`.

### Keys

Type the key and press Enter.

| Key | Action |
| --- | --- |
| number | Open a genre; on the station screen, play that station |
| `b` | Back (station screen) |
| `a number` | Save a station to `config.json` (station screen) |
| `s` | Stop playback |
| `k keyword` | Search Radio Browser |
| `t` | Next theme: phosphor green → amber → terminal default (saved) |
| `l` | Next language: system → en → ko → ru → fr → es → de → ja → system (saved) |
| `Ctrl+H` | Show or hide the help popup (Windows, when the input line is empty) |
| `Ctrl+C` | Quit the menu |

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
- [Additional sections](docs/readme-extras.md): sections moved out of this README

## Support the project

If this project is useful to you, consider buying the developer a coffee.

[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://ko-fi.com/dev_ohyt)
