#!/usr/bin/env python

from sys import exit

class FileManager:
    """I don't feel a need to make any comments here because it's pretty clear what this does."""
    @staticmethod
    def readFileContents(fname: str) -> str:
        try:
            with open(fname, "r") as f:
                # Yeah, I'm loading that shit into memory. All of it. Too late now.
                return f.read()
        except Exception as e:
            print(f"File manager could not read file: {fname} ({e})")
            exit(1)
