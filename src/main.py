#!/usr/bin/env python

"""
author: Micajah Bullard
email: micbul@unc.edu
"""

import argparse
import os
import multiprocessing
from tokenizer import Tokenizer
from file_manager import FileManager
from database_manager import DatabaseManager
from generator import Generator
import numpy as np
import pandas as pd

class Main:
    """The main class, which is where the program begins its execution."""
    def __init__(self, data_dir: str, system: str = "", output: str = "results.csv",
                 db_path: str = "grams.db"):
        self.data_dir = data_dir
        self.system = system    # tokenizer: "" for characters, "c" for C tokens
        self.output = output    # CSV file the test results are written to
        self.db_path = db_path  # SQLite file the n-gram probabilities are saved to

    def __call__(self):
        """The main point of execution for the program."""
        self.processes = int(input("Please input a number of processes: "))
        processes = []
        results = multiprocessing.Queue()  # each worker sends back its result rows
        n = 2
        for i in range(self.processes):
            p = multiprocessing.Process(target=self._worker, args=(n, results), name=f"Process-{i}")
            p.start()
            processes.append(p)
            n += 1
        # Collect before joining: a process can't exit while its queue data is unread
        rows = []
        for _ in processes:
            rows.extend(results.get())

        for p in processes:
            p.join()

        failed = [p.name for p in processes if p.exitcode != 0]
        if failed:
            print(f"Warning: these processes failed and have no results: {', '.join(failed)}")
        if not rows:
            print("No results to save.")
            return

        df = pd.DataFrame(rows).sort_values(["n", "file"]).reset_index(drop=True)
        df.to_csv(self.output, index=False)
        print(f"Saved {len(df)} result rows to {self.output}")

    def _worker(self, n: int, results):
        rows = []
        try:
            grams, total = self._train(n)
            # Each process opens its own connection; they can't be shared
            db = DatabaseManager(self.db_path)
            try:
                db.save_counts(grams, n, self.system)
            finally:
                db.close()
            print(f"Saved {len(grams)} {n}-grams to {self.db_path}")
            rows = self._test(n, grams, total) # a bit on the nose, huh?
        finally:
            # Always report back, even on failure, so the parent never waits forever
            results.put(rows)

    def _train(self, n):
        """You won't believe what this one does!"""
        grams = dict()
        total = 0
        training_dir = os.path.join(self.data_dir, "training")
        for f in os.listdir(training_dir):
            file_buf = FileManager.readFileContents(os.path.join(training_dir, f))
            tokens = Tokenizer.tokenize(file_buf, system=self.system)
            # It just goes on and on and none of it makes any sense
            # - Backrooms (2026)
            for i in range(n, len(tokens) + 1):
                # The last n tokens, as a tuple so token boundaries are kept
                cur = tuple(tokens[i-n:i])
                # Then we need to add it to grams
                if cur not in grams:
                    grams[cur] = 1
                else:
                    grams[cur] += 1
            total += max(len(tokens) - n + 1, 0)

        return grams, total

    def _test(self, n, grams, total) -> list[dict]:
        """
        This one actually just calculates negative log loss over the test data.
        Returns one result row per test file.
        """
        rows = []
        nll = 0
        count = 0
        testing_dir = os.path.join(self.data_dir, "testing")
        for f in os.listdir(testing_dir):
            file_buf = FileManager.readFileContents(os.path.join(testing_dir, f))
            tokens = Tokenizer.tokenize(file_buf, system=self.system)
            file_nll = 0
            file_count = 0
            unseen = 0
            for i in range(n, len(tokens) + 1):
                gram = tuple(tokens[i-n:i])
                if gram not in grams:
                    file_nll -= np.log(1 / total)
                    unseen += 1
                else:
                    file_nll -= np.log(grams[gram] / total)
                file_count += 1

            rows.append({
                "n": n,
                "tokenizer": self.system or "char",
                "file": f,
                "test_ngrams": file_count,
                "unseen_ngrams": unseen,
                "nll": file_nll,
                "avg_nll": file_nll / file_count if file_count else float("nan"),
                "train_total": total,
            })
            nll += file_nll
            count += file_count
        avg = nll / count if count else float("nan")
        print(f"""
        === {n} GRAMS ===
        Testing Loss:   {nll}
        Avg Loss:       {avg}
        Total Seen:     {total}
        =================
        """)
        return rows

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and test n-gram models.")
    parser.add_argument("data_dir", nargs="?", default="data",
                        help="folder containing training/ and testing/ (default: data)")
    parser.add_argument("--tokenizer", choices=["char", "c"], default="char",
                        help="char: raw characters (default); c: C tokens via Pygments")
    parser.add_argument("--output", default="results.csv",
                        help="CSV file to save test results to (default: results.csv)")
    parser.add_argument("--db", default="grams.db",
                        help="SQLite file for n-gram probabilities (default: grams.db)")
    gen = parser.add_argument_group("generation (uses an already-trained model; skips training)")
    gen.add_argument("--generate", metavar="FILE.c",
                     help="write generated code to this file instead of training")
    gen.add_argument("--n", type=int, default=3, help="which n-gram model to use (default: 3)")
    gen.add_argument("--length", type=int, default=300,
                     help="number of tokens to generate (default: 300)")
    gen.add_argument("--seed", type=int, help="random seed, for repeatable output")
    args = parser.parse_args()
    system = "" if args.tokenizer == "char" else "c"

    if args.generate:
        db = DatabaseManager(args.db)
        try:
            Generator(db, args.n, system, args.seed).write(args.generate, args.length)
        except ValueError as e:
            parser.error(str(e))
        finally:
            db.close()
        print(f"Wrote {args.length} generated tokens to {args.generate}")
    else:
        m = Main(args.data_dir, system, args.output, args.db)
        m()
