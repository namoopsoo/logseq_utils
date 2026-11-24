import pytest

from untagger import convert_outside_fences


@pytest.mark.parametrize(
    "original, expected, count",
    [
        pytest.param(
            "#foo/bar #foo-bar #google.com. #blah,",
            "[[foo/bar]] [[foo-bar]] [[google.com]]. [[blah]],",
            4,
            id="namespaces-domains-and-punctuation",
        ),
        pytest.param(
            "# Heading\nhttps://example.com/#anchor #foo+bar",
            "# Heading\nhttps://example.com/#anchor #foo+bar",
            0,
            id="leave-other-hash-syntax-alone",
        ),
        pytest.param(
            "- #café\r\n- #after",
            "- [[café]]\r\n- [[after]]",
            2,
            id="preserve-crlf-and-missing-final-newline",
        ),
    ],
)
def test_convert_prose(original, expected, count):
    assert convert_outside_fences(original) == (expected, count, None)


def test_preserve_code_in_a_logseq_list():
    original = """- #before
  - ```python
    # keep this comment
    print(" #inside")
    ```
  - #after
"""
    expected = """- [[before]]
  - ```python
    # keep this comment
    print(" #inside")
    ```
  - [[after]]
"""
    assert convert_outside_fences(original) == (expected, 2, None)


def test_closing_fence_requires_matching_character_and_sufficient_length():
    original = """````markdown
```
#still-inside
~~~~
#also-inside
`````
#outside
"""
    expected = """````markdown
```
#still-inside
~~~~
#also-inside
`````
[[outside]]
"""
    assert convert_outside_fences(original) == (expected, 1, None)


def test_preserve_tilde_fenced_code():
    original = "~~~sh\n#inside\n~~~\n#outside\n"
    expected = "~~~sh\n#inside\n~~~\n[[outside]]\n"
    assert convert_outside_fences(original) == (expected, 1, None)


@pytest.mark.parametrize("tail", ["", "``` not a closing fence\n", "~~~\n"])
def test_unclosed_fence_discards_even_edits_before_the_fence(tail):
    original = f"#before\n```python\n#inside\n{tail}"
    assert convert_outside_fences(original) == (original, 0, 2)


@pytest.mark.parametrize(
    "original, expected, count",
    [
        ("#[[some foo]]", "[[some foo]]", 1),
        ("#[[foo/bar]] #[[google.com]].", "[[foo/bar]] [[google.com]].", 2),
        ("#[[some foo]], #bare", "[[some foo]], [[bare]]", 2),
        ("#[[one]] #[[two words]]", "[[one]] [[two words]]", 2),
        ("[[some foo]]", "[[some foo]]", 0),
        ("#[[unfinished", "#[[unfinished", 0),
        ("#[[foo #bar baz]]", "[[foo #bar baz]]", 1),
    ],
)
def test_bracketed_tags(original, expected, count):
    assert convert_outside_fences(original) == (expected, count, None)


def test_bracketed_tags_inside_fences_are_preserved():
    original = "#[[before]]\n```markdown\n#[[inside]] #inside\n```\n#[[after]]\n"
    expected = "[[before]]\n```markdown\n#[[inside]] #inside\n```\n[[after]]\n"
    assert convert_outside_fences(original) == (expected, 2, None)


def test_unclosed_fence_cancels_bracketed_tag_conversion():
    original = "#[[before]]\n```markdown\n#[[inside]]\n"
    assert convert_outside_fences(original) == (original, 0, 2)
