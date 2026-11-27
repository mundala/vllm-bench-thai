"""Join scoring/scores.csv with scoring/key.json and print mean scores per model."""
import collections
import csv
import json
from pathlib import Path

COLS = ["correct", "fluent", "register", "followed"]
key = json.loads(Path("scoring/key.json").read_text(encoding="utf-8"))
acc = collections.defaultdict(lambda: collections.defaultdict(list))
with Path("scoring/scores.csv").open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if all(row[c].strip() for c in COLS):
            for c in COLS:
                acc[key[row["id"]]][c].append(int(row[c]))
print("| model | n | " + " | ".join(COLS) + " | overall |")
print("|---|---|" + "---|" * 5)
for model, d in acc.items():
    means = [sum(d[c]) / len(d[c]) for c in COLS]
    print(f"| {model} | {len(d['correct'])} | "
          + " | ".join(f"{x:.2f}" for x in means) + f" | {sum(means) / len(COLS):.2f} |")
