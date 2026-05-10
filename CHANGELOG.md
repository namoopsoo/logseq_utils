# CHANGELOG


# 2026-05-09

## Fixed
- Fixed  importer bug , was writing to original markdown file names, when converting, not to logseq format journal file names. 
- Fixed weird longdown npm bug where image tag square bracket  `![]()` was getting escaped to `\![]\()` . To do that,  replaced call to external npm longdown command with a  custom longdown converter. 

# Added
- And a end to end auto command that calls the three low level steps. 
- And added a integration test for new auto command

# 2025-08-..

Initial notes importer. Three subcommands , for converting Apple Notes Exporter markdown to the style expected by logseq . 

