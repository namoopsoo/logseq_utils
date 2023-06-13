import requests
import re
import os
import time
from pathlib import Path


def get_block(block_uuid):
    token = os.getenv("LOGSEQ_TOKEN")
    url = "http://127.0.0.1:12315/api"
    headers = {"Content-Type": "application/json",
              "Authorization": f"Bearer {token}"}
    payload = {
    "method": "logseq.Editor.getBlock",  
      "args": [block_uuid, 
               {"includeChildren": True}]
    }
    # "args": ["Test page", "This is a new block", {"isPageBlock": true}]}
    response = requests.post(url, json=payload, headers=headers)
    return response


def get_page(name, include_children=False):
    token = os.getenv("LOGSEQ_TOKEN")
    url = "http://127.0.0.1:12315/api"
    headers = {"Content-Type": "application/json",
              "Authorization": f"Bearer {token}"}
    payload = {
    "method": "logseq.Editor.getPage",  
      "args": [name, 
               {"includeChildren": include_children}]
    }
    response = requests.post(url, json=payload, headers=headers)
    return response
  


def get_page_blocks_tree(name):
    token = os.getenv("LOGSEQ_TOKEN")
    url = "http://127.0.0.1:12315/api"
    headers = {"Content-Type": "application/json",
              "Authorization": f"Bearer {token}"}
    payload = {
    "method": "logseq.Editor.getPageBlocksTree",  
      "args": [name]
    }
    response = requests.post(url, json=payload, headers=headers)
    return response
  

def build_markdown_from_page_blocks(blocks, level_offset=0):
    print("DEBUG", [x["level"] for x in blocks])

    stuff = []
    for block in blocks:

        # Replace embed
        if match := re.match(
            r"^{{embed \(\(([a-zA-Z0-9-]+)\)\)}}$",
            block["content"]
        ):
            block_uuid = match.groups()[0]
            print("yes", block_uuid)

            response = get_block(block_uuid)
            assert response.status_code == 200

            new_block = response.json()
            new_block["level"] = block["level"]

            stuff.append({"level": new_block["level"], "content": new_block["content"]})
            if new_block["children"]:
                stuff.extend(
                    build_markdown_from_page_blocks(
                        new_block["children"],
                        level_offset=(level_offset + new_block["level"])
                    ))

        else:
            stuff.append(
                {"level": block["level"] + level_offset,
                 "content": block["content"]})
            if block["children"]:
                stuff.extend(
                    build_markdown_from_page_blocks(
                        block["children"], level_offset=level_offset)
                )

    return stuff

def build_markdown(page_name, target_loc):
    response = get_page(page_name)
    assert response.status_code == 200 and response.json()

    response = get_page_blocks_tree(page_name)
    assert response.status_code == 200 and response.json()
    blocks = response.json()

    blog_date = blocks[0]["properties"]["blogDate"]

    stuff = build_markdown_from_page_blocks(blocks)

    page_title = page_name.split("/")[1]  # 
    if match := re.match(r"(\d{4}-\d{2}-\d{2})-(.*)", page_title):
        date_from_title, page_title = match.groups()
    print("page_title", page_title)

    page_title = page_title.replace("-", " ")
    print("page_title", page_title)

    text = [
        "---",
        f"date: {date_from_title}",
        f"title: {page_title}",
        "---",
    ] + [x["content"] for x in stuff]
    path = Path(target_loc)
    assert path.parent.is_dir()

    path.write_text("\n".join(text))
    ...
