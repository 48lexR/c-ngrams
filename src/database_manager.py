#!/usr/bin/env python3

import json
import sqlite3
from typing import Optional


def _encode(tokens) -> str:
    """Store a token sequence as JSON so tokens containing spaces stay separate."""
    return json.dumps(list(tokens), ensure_ascii=False)


def _decode(text: str) -> tuple:
    return tuple(json.loads(text))


from typing import Any, Optional
class DatabaseManager:
    """
    I wish I could just have a giant hash table stored on disk
    But oh well, such is life. I don't have time to build that
    in Python

    There is one table per (tokenizer, n), e.g. grams_c_3. Each row is an
    n-gram split into its context (the first n-1 tokens) and the token that
    follows, with how often it occurred and P(token | context).
    """

    fname: str
    db: Any
    total_seen: int

    def __init__(self, fname: str = "grams.db"):
        self.fname = fname
        self.db = sqlite3.connect(fname)
        self.total_seen = 0

    @staticmethod
    def _table(n: int) -> str:
        return f"grams_{int(n)}"

    def create_table(self, n: int):
        cur = self.db.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {self._table(n)}(
        gram TEXT PRIMARY KEY,
        n_occurrences INT
        )""")
        self.db.commit()

    def get_ngram(self, ngram: str, n: int) -> tuple[Optional[tuple], bool]:
        """Returns (row, not_found). row is (n_occurrences, probability) or None."""
        cur = self.db.cursor()
        res = cur.execute(f"SELECT n_occurrences FROM {self._table(n)} WHERE gram = ?", (ngram,))
        row = res.fetchone()
        if row is None:
            return (None, True)
        occ = row[0]
        prob = occ / self.total_seen if self.total_seen else 0.0
        return ((occ, prob), False)

    def save_ngram(self, ngram: str, n: int, occurrences: int = 1) -> tuple[list, bool]:
        self.create_table(n)
        row, not_found = self.get_ngram(ngram, n)
        cur = self.db.cursor()
        self.total_seen += occurrences

        if not_found:
            cur.execute(f"INSERT INTO {self._table(n)} VALUES (?, ?)", (ngram, occurrences))
            self.db.commit()
            return ([occurrences, occurrences / self.total_seen], True)

        occ, _ = row
        new_occ = occ + occurrences
        cur.execute(f"UPDATE {self._table(n)} SET n_occurrences = ? WHERE gram = ?", (new_occ, ngram))
        self.db.commit()
        return ([new_occ, new_occ / self.total_seen], True)
