# Tiddl (Fork)

> **Attribution Notice:**
> This is a modified fork of [tiddl](https://github.com/oskvr37/tiddl), originally created by [oskvr37](https://github.com/oskvr37).
> This project retains the original [Apache License 2.0](LICENSE). All credit for the foundational work goes to the original author.

## About This Fork

I am actively maintaining and updating this project to fit my personal workflow and needs. Community contributions are welcome. If you have bug fixes, feature requests, or improvements, feel free to open an issue or submit a Pull Request.

---

Download tracks and videos from Tidal with maximum quality. `tiddl` is a CLI application written in Python.

> **Disclaimer:**
> This app is for personal use only and is not affiliated with Tidal. Users must ensure their use complies with Tidal's terms of service and local copyright laws. Downloaded tracks are for personal use and may not be shared or redistributed. The developer assumes no responsibility for misuse of this app.

---

> **Important:** Make sure you have `ffmpeg` installed on your system, as it is required to convert downloaded tracks to the proper format.

## Usage

Run the app with the `tiddl` command:

    $ tiddl
    Usage: tiddl [OPTIONS] COMMAND [ARGS]...

    tiddl - download tidal tracks

    ╭─ Options ──────────────────────────────────────────────────────────────────╮
    │ --omit-cache            --no-omit-cache      [default: no-omit]            │
    │ --debug                 --no-debug           [default: no-debug]           │
    │ --install-completion                         Install completion for the c..│
    │ --show-completion                            Show completion for the curr..│
    │ --help                                       Show this messaged exit.      │
    ╰────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ─────────────────────────────────────────────────────────────────╮
    │ auth       Manage Tidal authentication.                                    │
    │ download   Download Tidal resources.                                       │
    ╰────────────────────────────────────────────────────────────────────────────╯

## Authentication

Log in to the app with your Tidal account by running:

```bash
tiddl auth login
```

Follow the on-screen instructions to complete the authentication process.

## Downloading

You can download tracks, videos, albums, artists, playlists, and mixes:

```bash
tiddl download url <url>
```

> **Tip:** You don't have to paste full URLs. Shortened formats like `track/103805726` or `album/103805723` will also work. Run `tiddl download` to see all available download options.

### Quality Options

| Quality  | File Extension | Details               |
| -------- | -------------- | --------------------- |
| `LOW`    | `.m4a`         | 96 kbps               |
| `NORMAL` | `.m4a`         | 320 kbps              |
| `HIGH`   | `.flac`        | 16-bit, 44.1 kHz      |
| `MAX`    | `.flac`        | Up to 24-bit, 192 kHz |

### Output Formatting

You can format filenames and organize downloaded resources into specific directories using templates.
For example, setting the output flag to `"{album.artist}/{album.title}/{item.number:02d}. {item.title}"` will structure your downloads like this:

    Music
    └── Kanye West
        └── Graduation
            ├── 01. Good Morning.flac
            ├── 02. Champion.flac
            ├── 03. Stronger.flac
            └── ...

> **Note:** Learn more about file templating in the [docs](docs/templating.md).

---

## Configuration

Configuration files are stored in your home directory by default (`~/.tiddl`).
You can (and should) create a `config.toml` file to customize the app's behavior. You can copy the [example config](docs/config.example.toml) to get started.

## Environment Variables

- **`TIDDL_PATH`**: Set a custom path for the `tiddl` app directory.
  _Example:_ `TIDDL_PATH=~/custom/tiddl tiddl auth login`
- **`TIDDL_AUTH`**: Override default credentials if authentication stops working.
  _Format:_ `TIDDL_AUTH=<CLIENT_ID>;<CLIENT_SECRET>`

---

## Development & Contributing

This fork enforces strict code quality, type safety, and security standards using a modern Python tooling stack. Contributions are welcome. Please ensure your PRs pass all local checks before submitting.

### Tooling Stack

- **[prek](https://github.com/j178/prek)**: A fast, drop-in replacement for `pre-commit` written in Rust, used to run all checks automatically.
- **[ty](https://github.com/astral-sh/ty)**: A high-performance Python type checker.
- **[ruff](https://github.com/astral-sh/ruff)**: An extremely fast Python linter and code formatter.
- **[bandit](https://github.com/PyCQA/bandit)**: A security linter to find common security issues in Python code.
- **[import-linter](https://github.com/import-linter/import-linter)**: Impose constraints on the imports between your Python modules.

### Where things live

`core` is the library. It never imports `cli`, `typer` or `rich`.
Every shape of data has exactly one home, so look here first:

| You are looking for                                  | Look in         |
| ---------------------------------------------------- | --------------- |
| Literals, enums                                      | `types.py`      |
| Constants                                            | `constants.py`  |
| Exceptions                                           | `exceptions.py` |
| Protocols and callback types                         | `protocols.py`  |
| Pydantic models and dataclasses                      | `models/`       |
| ... shapes we receive from Tidal                     | `models/tidal/` |
| ... shapes we define (settings, options, plans, ...) | `models/*.py`   |

Everything else (`api`, `auth`, `metadata`, `utils`, `download`) is behavior.
A helper dataclass used by a single module may stay in that module, as a private name.

#### Layers

Each layer may import only from the ones below it (checked by `lint-imports`,
see `[tool.importlinter]` in `pyproject.toml`).

```
cli
 └─ core.download
     └─ api · auth · metadata · utils · protocols     (never import each other)
         └─ models
             └─ constants
                 └─ types · exceptions                 (import nothing from tiddl)
```

A type belongs in the lowest layer that can hold it: everything it references
must be in that layer or below. If a type needs something from a higher layer,
the type belongs there too.

### Setup for Development

1.  Clone the repository:

```bash
git clone https://github.com/jazzify/tiddl
cd tiddl
```

2.  Create and setup your development environment:

```bash
uv sync
```

3.  Install the `prek` hooks:

```bash
# Install prek from https://prek.j178.dev/dev/installation/
prek install
```

---

## Using Docker

**Coming soon**

---

## Resources

- [Tidal API Wiki](https://github.com/Dniel97/RedSea/wiki/Tidal-API) (API endpoints reference)
- [Tidal-Media-Downloader](https://github.com/yaronzz/Tidal-Media-Downloader) (Original inspiration)

---

## License

This project is licensed under the **Apache License 2.0**.
See the [LICENSE](LICENSE) file for full details. The original copyright and attribution notices have been preserved in accordance with the license terms.
