import re
import csv
import argparse
from datetime import datetime
from pathlib import Path
import polars as pl

import argparse

def bake_options():
    return [
        [['--verbose', '-v'],
            {'action': 'store_true',  # stores boolean
                'help': 'pass to to be verbose with commands'},
            ],
        [['--source-dir', '-s'],
            {'action': 'store',
                'help': 'Dir to read files from.'},],
        [['--pattern', '-s'],
            {'action': 'store',
                'help': 'glob pattern for journals'},],
    ]


def read_kwargs():
    parser = argparse.ArgumentParser()

    [parser.add_argument(*x[0], **x[1])
            for x in bake_options()]

    # Collect args from user.
    kwargs = dict(vars(parser.parse_args()))
    return kwargs


def parse_clock_line(line):
    pattern = r"CLOCK: \[(.*?)\]--\[(.*?)\]"
    match = re.search(pattern, line)
    if match:
        start_str, end_str = match.groups()
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %a %H:%M:%S")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d %a %H:%M:%S")
        duration = end_dt - start_dt
        return start_dt, end_dt, duration
    return None, None, None

def extract_time_blocks(filepath):
    rows = []
    with open(filepath, 'r', encoding='utf-8') as file:
        current_task = None
        for line in file:
            line = line.strip()
            if line.startswith('- '):
                current_task = line[2:]
            elif line.startswith('CLOCK:'):
                start_dt, end_dt, duration = parse_clock_line(line)
                if start_dt and end_dt:
                    rows.append({
                        'Date': start_dt.date(),
                        'Start': start_dt.time(),
                        'End': end_dt.time(),
                        'Duration (mins)': round(duration.total_seconds() / 60),
                        'Task': current_task,
                        'Tags': parse_tags_from_task(current_task),
                    })
    return rows

def parse_tags_from_task(task_line):
    if not task_line:
        return []

    tags = []

    # Match [[tag with spaces]]
    tags += re.findall(r"\[\[([^\]]+)\]\]", task_line)

    # Match #tag (without brackets)
    tags += re.findall(r"#([a-zA-Z0-9/_\-]+)", task_line)

    return tags

def iterate_across_journals(journals_dir, pattern):
    out_vec = []
    for input_md_file in Path(journals_dir).glob(pattern):
        ...
        parsed_rows = extract_time_blocks(input_md_file)

        out_vec.extend(parsed_rows)

    return out_vec

if __name__ == '__main__':

    kwargs = read_kwargs()
    journals_dir = kwargs["source_dir"]
    pattern = kwargs["pattern"]
    if not pattern:
        pattern = "*.md"

    out_vec = iterate_across_journals(journals_dir, pattern)

    df = pl.from_dicts(out_vec)