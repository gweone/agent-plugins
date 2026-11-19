# Plugins: optional recommendations

Plugins are **recommendations, never requirements**. No file type needs one: everything in
the other references is the default with no plugins, and the task proceeds without them.
Plugins differ per workstation, so when one happens to be installed it may improve a result
for some file types, and the agent can use it after the checks below.

## Check

```bash
markitdown --list-plugins        # for example: "ocr   (package: markitdown_ocr)"
markitdown --help | grep -i llm  # does this version's CLI have model options?
```

- None are installed by default. An installed plugin is ignored unless you pass `-p`
  (`--use-plugins`).
- More plugins can be found by searching GitHub for the `#markitdown-plugin` topic.

## Procedure

1. **List** the installed plugins and note which file types each covers (`pip show <package>`,
   and the package description on PyPI).
2. **Decide** whether one would help. For scanned PDFs and images an OCR plugin may; without
   one the default route still works (report the gap, or choose another route with the user).
3. **Read its requirements**: a model client, an API key, network access, cost.
4. **Check the data flow.** If it sends content to an external service, get approval first,
   exactly as for the Azure options. Prefer not to send confidential documents.
5. **Try it on the one file** with `-p` and compare with the default result. Re-run the
   checks in [formats and limits](formats-and-limits.md): a plugin can change the output
   format, not only add text.
6. **Report** which plugin you used and anything still unread.
7. **Recommend a plugin that is not installed by asking.** Name the plugin and why it would
   help, what it needs (for example a model client and API key) and what it sends out, then
   ask whether it may be installed, or whether the user prefers a different plugin. Install
   only after a yes. If they decline, continue with the default route; meanwhile carry on
   with the parts of the task that do not need it.

## The OCR plugin (`ocr`, package `markitdown-ocr`)

Observed with markitdown-ocr 0.1.2 on markitdown 0.1.9. A real OCR call was **not** run (it
needs a model API key), so what OCR output looks like is taken from the plugin's README and
source, not from a test.

- **Purpose** (per its README): extract text from images inside PDF, Word, PowerPoint and
  Excel files using an LLM vision model, with a full-page OCR fallback for scanned PDFs.
- **Needs a model client in the Python API.** Install with `pip install markitdown-ocr`
  (`'markitdown-ocr[llm]'` adds the `openai` client), then:

  ```python
  from markitdown import MarkItDown
  from openai import OpenAI              # any OpenAI-compatible client

  md = MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model="<approved model>")
  text = md.convert("scan.pdf").text_content
  ```

- **The 0.1.9 CLI cannot configure it.** The plugin's README shows
  `--llm-client` / `--llm-model` flags; this version rejected them as unrecognized
  arguments, and `--help` has no model options. With the CLI alone, `-p` cannot OCR. Use the
  Python API, or check `markitdown --help` again on a newer version.
- **No client means OCR is silently skipped.** `-p` on a scanned PDF returned only
  `## Page 1`; a plain image returned nothing. Do not read that as "the page is blank".
- **`-p` changes PDF output.** `## Page N` headings replace the form-feed separators, even
  for text PDFs, so the empty-output check must ignore those headings
  ([formats and limits](formats-and-limits.md#verification-snippets)). A Word file was
  unchanged.
- **Data flow:** page images go to the model provider. Approval first.
- **Treat OCR text as less reliable than extracted text.** According to the plugin source,
  OCR text is wrapped in `*[Image OCR]` ... `[End OCR]*` blocks; check numbers, names and
  dates against the image before you rely on them.
