import os

def walk_backwards(path):
    while 1:
        yield path
        next_path = os.path.dirname(path)
        if path == next_path:
            break
        path = next_path
