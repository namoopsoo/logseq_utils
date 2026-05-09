# logseq_utils


## notes_importer

`notes_importer.py` offers utilities for importing Apple Notes exports into Logseq. Apple Notes exporter was used, from here , https://github.com/kzaremski/apple-notes-exporter/ . The latest one that was tested with notes_importer.py below, is `Apple Notes Exporter Version 0.4 (5)`, but I would love to also test on Version 2.0 that I saw was released around April 2026 !


### One shot usage
Note, currently, one strict requirement is that all the note files need to start prefixed by `yyyy-mm-dd` and that is used to append to corresponding journal dated markdown files , `logseq_graph_dir/journals/yyyy_mm_dd.md`. 

Apple Notes Exporter markdown style is changed to the longdown outline style expected by logseq.

```sh
workdir=/Users/you/where-you-exported-your-apple-notes
notes_dir=$workdir/iCloud/Notes

# A staging area for intermediate results
staging_dir=$workdir/staging_dir

logseq_dir=/Users/you/path/to/your/logseq_graph_dir

python notes_importer.py auto \
  --input-dir $notes_dir \
  --logseq-dir $logseq_dir \
  --staging-dir $staging_dir
```

### Debug Usage
The above one shot command can also be run in three separate steps for debugging purposes.

```sh
notes_dir=xxxx
staging_dir=xxxx
logseq_dir=xxxx

python notes_importer.py process-images \
  --input-dir $notes_dir --output-dir $staging_dir

python notes_importer.py longdown \
  --input-dir $staging_dir/processed_markdown \
  --output-dir $staging_dir/longdown

python notes_importer.py append-to-logseq \
  --input-dir $staging_dir/longdown \
  --logseq-dir $logseq_dir \
  --assets-dir ${staging_dir}/assets

```

`process-images` copies markdown files while extracting embedded images into an `assets` directory. `longdown` runs the `longdown` tool on the processed markdown. `append-to-logseq` appends content from the input directory to matching files in the output directory and adds a bullet indicating the source is the Apple Notes exporter.



## logseq hug publish

Note this is currently just the landing page for the utils behind the blog post, https://michal.piekarczyk.xyz/post/2023-06-12-logseq-publish-hugo-with-python/ , for the purposes of publishing a single log-seq page to markdown, along with any block embeds it has, by talking to a local logseq server REST API.