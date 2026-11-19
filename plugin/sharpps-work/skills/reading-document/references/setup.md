# Setup: markitdown

Check first: `markitdown --version`. If it prints `markitdown 0.1.x` or newer, setup is
done. Installing packages is a change to the machine, so ask before doing it.

## Python version trap

`markitdown` requires **Python 3.10 to 3.14**. On Python 3.9, `pip install markitdown` does
not fail: it quietly installs an old `0.0.1a1` alpha that has no `markitdown`
command. After any install, confirm the version rather than trusting a clean pip run. Use a
newer interpreter (`python3.12 --version`) for the venv below.

## Install (recommended: a dedicated venv)

```bash
python3.12 -m venv ~/.venvs/markitdown        # any Python 3.10+
~/.venvs/markitdown/bin/pip install 'markitdown[all]'
mkdir -p ~/.local/bin && ln -sf ~/.venvs/markitdown/bin/markitdown ~/.local/bin/markitdown
markitdown --version
```

`pipx install 'markitdown[all]'` or `uv tool install 'markitdown[all]'` install the same
package if those tools are present. Avoid installing into the system Python.

## Extras: install what you need

The base package is small. Each format family needs its extra:

| Extra | Adds |
|---|---|
| `pdf`, `docx`, `pptx`, `xlsx`, `xls` | PDF, Word, PowerPoint, Excel (`.xlsx`, `.xls`) |
| `outlook` | Outlook `.msg` |
| `audio-transcription`, `youtube-transcription` | Audio and YouTube transcripts |
| `az-doc-intel`, `az-content-understanding` | The Azure options below |
| `all` | Everything above |

Pick several with `'markitdown[pdf,docx,xlsx]'`. With the right extra missing, the
conversion fails with a message telling you to `pip install 'markitdown[docx, ...]'`;
install the extra it names, then retry.

## Options worth knowing

```text
markitdown [FILE] [-o OUT] [-x EXT] [-m MIME] [-c CHARSET] [--keep-data-uris]
           [-p | --use-plugins] [--list-plugins]
           [-d -e ENDPOINT]              # Azure Document Intelligence (uploads the file)
           [--use-cu --cu-endpoint URL]  # Azure Content Understanding (uploads the file)
```

- With no `FILE` it reads stdin. When the type cannot be sniffed, give a hint:
  `cat file.docx | markitdown -x .docx`.
- `--keep-data-uris` keeps embedded images as full base64 data URIs. The default truncates
  them to a short placeholder, which is what you want when reading.
- `-d` / `--use-cu` replace the offline conversion with a cloud service. Only with explicit
  approval, an approved endpoint, and a document you may upload.
- `--list-plugins` shows installed third-party plugins; `-p` enables them. None are installed
  by default, and an installed plugin is ignored without `-p`. See [plugins](plugins.md).

## Python API (for batches or custom handling)

```python
from markitdown import MarkItDown

md = MarkItDown()                       # offline conversion
result = md.convert("report.docx")      # path, URL, or file object
text = result.text_content
```

Image descriptions are an API-only feature: the 0.1.9 CLI has no option for them. In the package
source, `llm_client`, `llm_model` and `llm_prompt` are read from the constructor and used
only by the image and PowerPoint converters; this sends images to that model's provider, so
treat it like the Azure options (approval first).

## Upgrade and remove

```bash
~/.venvs/markitdown/bin/pip install -U 'markitdown[all]'
rm -rf ~/.venvs/markitdown ~/.local/bin/markitdown      # remove (only if you installed it)
```

Tested with markitdown 0.1.9 on Python 3.12.
