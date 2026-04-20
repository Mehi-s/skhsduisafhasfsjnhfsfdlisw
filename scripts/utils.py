
import os

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
