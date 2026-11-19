#!/usr/bin/env python

from pygments.lexers import CLexer
from pygments.token import Comment, Name, Number, Operator, String

# Placeholder emitted in place of every identifier in "c" mode
IDENTIFIER = "<ID>"

# C operators, longest first, for maximal-munch splitting. Pygments emits
# multi-character operators like ">=" as separate one-character tokens.
_C_OPERATORS = sorted([
    "<<=", ">>=", "...",
    "->", "++", "--", "<<", ">>", "<=", ">=", "==", "!=", "&&", "||",
    "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "##",
], key=len, reverse=True)


def _split_operators(run: str) -> list[str]:
    """Split a run of adjacent operator characters into C operators."""
    out = []
    i = 0
    while i < len(run):
        for op in _C_OPERATORS:
            if run.startswith(op, i):
                out.append(op)
                i += len(op)
                break
        else:
            out.append(run[i])
            i += 1
    return out


class Tokenizer:
    def __init__(self):
        pass

    @staticmethod
    def tokenize(text: str, **kwargs) -> list[str]:
        """I can't believe it's not butter!"""
        system: str = kwargs.get('system', "") # "" means just use characters

        if system == "":
            return list(text)
        if system == "c":
            return Tokenizer._tokenize_c(text)

        raise ValueError(f"Unknown tokenizer system: {system!r}")

    @staticmethod
    def _tokenize_c(text: str) -> list[str]:
        """
        Lex C source with Pygments.
        - Comments are dropped.
        - Identifiers (variables, functions, labels, macros) become <ID>.
        - Preprocessor lines become a single token like "#include".
        - String/char literals are merged back into one token.
        """
        tokens: list[str] = []
        string_buf: list[str] = []   # pieces of the current string literal
        op_buf: list[str] = []       # adjacent operator characters
        in_preproc = False

        def flush_string():
            if string_buf:
                tokens.append(''.join(string_buf))
                string_buf.clear()

        def flush_ops():
            if op_buf:
                tokens.extend(_split_operators(''.join(op_buf)))
                op_buf.clear()

        for ttype, value in CLexer().get_tokens(text):
            # Checked before whitespace so literals like " " are kept intact
            if ttype in String:
                flush_ops()
                string_buf.append(value)
                continue

            if value.isspace():
                # Whitespace ends operator runs, string literals, and
                # (if it contains a newline) preprocessor directives.
                flush_ops(); flush_string()
                if '\n' in value:
                    in_preproc = False
                continue

            if ttype in Comment.Preproc or ttype in Comment.PreprocFile:
                flush_ops(); flush_string()
                if value == '#':
                    in_preproc = True
                    tokens.append('#')
                elif in_preproc and tokens and tokens[-1] == '#':
                    # First word after '#': the directive name
                    tokens[-1] = '#' + value.split()[0]
                # The rest of the directive (macro bodies, file names) is skipped
                continue

            if ttype in Comment:
                flush_ops(); flush_string()
                continue

            flush_string()

            # Pygments sometimes lexes "-1" as one number; C sees "-" then "1"
            if ttype in Number and value[0] in "+-":
                op_buf.append(value[0])
                value = value[1:]

            if ttype in Operator:
                op_buf.append(value)
            else:
                flush_ops()
                tokens.append(IDENTIFIER if ttype in Name else value)

        flush_ops()
        flush_string()
        return tokens
