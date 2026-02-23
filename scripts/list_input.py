import os, json

INPUT_DIR = r"C:\agent\input"
files = []
for root, _, filenames in os.walk(INPUT_DIR):
    for fn in filenames:
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, INPUT_DIR)
        files.append(rel)

print(json.dumps({"files": files}, ensure_ascii=False, indent=2))