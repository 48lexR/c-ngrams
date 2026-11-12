#!/usr/bin/env python3

import sqlite3

class DatabaseManager:
    """
    I wish I could just have a giant hash table stored on disk
    But oh well, such is life. I don't have time to build that
    in Python
    """

    fname: str
    db: any
    cursor: any
    total_seen: int

    def __init__(self, fname):
        self.fname = fname
        self.db = sqlite3.connect("grams.db")
        self.total_seen = 0

    def create_table(self, n: int):
        table_name = f"{n}-grams"
        cur = self.db.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {n}-grams(
        gram DISTINCT VARCHAR(255),
        n_occurrances INT,
        probability FLOAT
        )""")

    def get_ngram(self, ngram: str, n: int) -> (list, bool):
        cur = self.db.cursor()
        res = cur.execute(f"SELECT n_occurrances, probability FROM {n}-grams WHERE gram = {ngram}")
        return (res.fetchone(), res.fetchone() is None)

    def save_ngram(self, ngram: str, n: int, occurrances=1.0) -> (list, bool):
        t, e = self.get_ngram(ngram, n)
        cur = self.db.cursor()
        self.total_seen += n

        if e == False:
            cur.execute(f"""INSERT INTO {n}-grams VALUES(
            {ngram},
            {occurrances},
            {occurrances / self.total_seen}
            )""")
            cur.commit()
            return ([occurrances, occurrances / self.total_seen], True)

        occ, prob = t
        cur.execute(f"""UPDATE {n}-grams SET n_occurrances={occ + n}, probability={ (occ + n) / self.total_seen}""")
        cur.commit()
        return ([occ + n, (occ + n) / self.total_seen], True)
