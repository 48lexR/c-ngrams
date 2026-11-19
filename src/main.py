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
# from database_manager import DatabaseManager
import numpy as np

class Main:
    """The main class, which is where the program begins its execution."""

    def __init__(self, data_dir: str, system: str = ""):
        self.data_dir = data_dir
        self.system = system  # tokenizer: "" for characters, "c" for C tokens

    def __call__(self):
        """The main point of execution for the program."""
        self.processes = int(input("Please input a number of processes: "))
        processes = []
        n = 2
        for i in range(self.processes):
            p = multiprocessing.Process(target=self._worker, args=(n,), name=f"Process-{i}")
            p.start()
            processes.append(p)
            n += 1

        for p in processes:
            p.join()

    def _worker(self, n: int):
        grams, total = self._train(n)
        self._test(n, grams, total) # a bit on the nose, huh?

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

    def _test(self, n, grams, total):
        """This one actually just calculates negative log loss over the test data"""
        nll = 0
        count = 0
        testing_dir = os.path.join(self.data_dir, "testing")
        for f in os.listdir(testing_dir):
            file_buf = FileManager.readFileContents(os.path.join(testing_dir, f))
            tokens = Tokenizer.tokenize(file_buf, system=self.system)

            for i in range(n, len(tokens) + 1):
                gram = tuple(tokens[i-n:i])
                if gram not in grams:
                    nll -= np.log(1 / total)
                else:
                    nll -= np.log(grams[gram] / total)
                count += 1
        avg = nll / count if count else float("nan")
        print(f"""
        === {n} GRAMS ===
        Testing Loss:   {nll}
        Avg Loss:       {avg}
        Total Seen:     {total}
        =================
        """)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and test n-gram models.")
    parser.add_argument("data_dir", nargs="?", default="data",
                        help="folder containing training/ and testing/ (default: data)")
    parser.add_argument("--tokenizer", choices=["char", "c"], default="char",
                        help="char: raw characters (default); c: C tokens via Pygments")
    args = parser.parse_args()
    m = Main(args.data_dir, "" if args.tokenizer == "char" else "c")
    m()
