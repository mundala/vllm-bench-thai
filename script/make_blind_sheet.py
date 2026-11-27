"""Build a blind scoring pack from results/run2/answers_readable.md.

Writes scoring/blind_sheet.md (read this), scoring/scores.csv (fill this) and
scoring/key.json (do NOT open until scoring is done; git-ignored).
The seed is fixed, so the shuffle is reproducible.
"""
import csv
import json
import random
import re
from pathlib import Path

SEED = 2026
SRC = Path("results/run2/answers_readable.md")
OUT = Path("scoring")

parts = re.split(r"\n## Prompt (\d+)\n", SRC.read_text(encoding="utf-8"))
prompts = {}
for i in range(1, len(parts), 2):
    question, *answers = re.split(r"\n### (\S+) \(\d+ chars\)\n", parts[i + 1])
    by_config = {
        answers[j]: answers[j + 1].strip().rstrip("-").strip()
        for j in range(0, len(answers), 2)
    }
    prompts[int(parts[i])] = (question.strip().strip("-").strip(), by_config)

rnd = random.Random(SEED)
key, rows = {}, []
sheet = [
    "# Blind scoring sheet\n",
    "Score each answer in scoring/scores.csv. Labels (A to D) are shuffled per prompt. "
    "Do not open key.json.\n",
]
for n in sorted(prompts):
    question, by_config = prompts[n]
    configs = list(by_config)
    rnd.shuffle(configs)
    sheet.append(f"\n---\n\n## Prompt {n}\n\n{question}\n")
    for label, config in zip("ABCD", configs):
        key[f"{n}{label}"] = config
        sheet.append(f"\n### {n}{label}\n\n{by_config[config]}\n")
        rows.append([f"{n}{label}", "", "", "", "", ""])

(OUT / "blind_sheet.md").write_text("\n".join(sheet), encoding="utf-8")
with (OUT / "scores.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "correct", "fluent", "register", "followed", "note"])
    writer.writerows(rows)
(OUT / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
print(len(prompts), "prompts,", len(rows), "answers")
