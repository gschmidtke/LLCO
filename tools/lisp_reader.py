"""Minimal AutoLISP reader for LLCO. Reads text into nested Python lists; executes nothing.

Handles: ; line comments, ;| block comments |;, strings with \\ escapes, quote ('),
dotted pairs (kept as the symbol '.'), and unbalanced input (reported, not fatal).
Symbols are lower-cased (AutoLISP is case-insensitive); strings keep their case.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Str:
    value: str


@dataclass(frozen=True)
class Quote:
    form: object


TOKEN = re.compile(r'''
    (?P<block>;\|.*?\|;)            |
    (?P<comment>;[^\n]*)            |
    (?P<string>"(?:\\.|[^"\\])*")   |
    (?P<open>\()                    |
    (?P<close>\))                   |
    (?P<quote>')                    |
    (?P<ws>\s+)                     |
    (?P<atom>[^\s()'";]+)
''', re.S | re.X)


def tokenize(text):
    pos, line = 0, 1
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:  # stray character (e.g. unterminated string): skip it
            if text[pos] == "\n":
                line += 1
            pos += 1
            continue
        kind = m.lastgroup
        tok = m.group(kind)
        if kind not in ("block", "comment", "ws"):
            yield kind, tok, line
        line += tok.count("\n")
        pos = m.end()


def read(text):
    """Return (forms, problems). Each list form is a Python list; its first-token line is in .line"""
    stack, problems = [[]], []
    pending_quote = []
    for kind, tok, line in tokenize(text):
        if kind == "open":
            stack.append(Form()); stack[-1].line = line
            pending_quote.append(False)
            continue
        if kind == "close":
            if len(stack) == 1:
                problems.append(f"line {line}: unmatched ')'")
                continue
            form = stack.pop()
            pending_quote.pop()
            stack[-1].append(form)
            _apply_quotes(stack[-1])
            continue
        if kind == "quote":
            stack[-1].append(QUOTE_MARK)
            continue
        item = Str(tok[1:-1]) if kind == "string" else tok.lower()
        stack[-1].append(item)
        _apply_quotes(stack[-1])
    while len(stack) > 1:
        form = stack.pop()
        problems.append(f"unclosed '(' opened at line {getattr(form, 'line', '?')}")
        stack[-1].append(form)
    return stack[0], problems


class Form(list):
    line = None


QUOTE_MARK = object()


def _apply_quotes(container):
    """Fold a QUOTE_MARK followed by an item into Quote(item)."""
    while len(container) >= 2 and container[-2] is QUOTE_MARK:
        item = container.pop()
        container.pop()
        container.append(Quote(item))
