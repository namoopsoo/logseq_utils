# logseq_utils

Note this is currently just the landing page for the utils behind the blog post, https://michal.piekarczyk.xyz/post/2023-06-12-logseq-publish-hugo-with-python/ , for the purposes of publishing a single log-seq page to markdown, along with any block embeds it has, by talking to a local logseq server REST API.

## notes_importer

`notes_importer.py` offers utilities for importing Apple Notes exports into Logseq.

Usage:

```
python notes_importer.py process-images --input-dir <notes> --output-dir <step1>
python notes_importer.py longdown --input-dir <step1>/journals --output-dir <step2>
python notes_importer.py append-to-logseq --input-dir <step2> --output-dir <logseq-journals>
```

`process-images` copies markdown files while extracting embedded images into an `assets` directory. `longdown` runs the `longdown` tool on the processed markdown. `append-to-logseq` appends content from the input directory to matching files in the output directory and adds a bullet indicating the source is the Apple Notes exporter.
