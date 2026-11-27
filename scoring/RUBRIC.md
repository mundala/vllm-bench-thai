# Thai quality rubric (v1, 27 Nov 2026)

Scorer: Jean, native Thai speaker. One person, one pass, so this is one reviewer's judgement, not a validated study.

## How to score (blind)

1. Open `scoring/blind_sheet.md`. Each prompt has four answers, labelled 1A to 1D, shuffled. You cannot tell which model wrote which.
2. For each answer, put four scores (1 to 5) in `scoring/scores.csv`, one row per label. Add a short `note` only if something stands out.
3. Do not open `scoring/key.json` until every row is filled.
4. Run `python3 -I script/unblind.py`. It prints mean scores per model.

## The four scores

| Column | Question | 5 | 3 | 1 |
|---|---|---|---|---|
| correct | Are the facts and numbers right? | All right | One clear error | Wrong or made up |
| fluent | Does it read like a native Thai writer? | Natural | Understandable but stiff or odd words | Broken, or not Thai |
| register | Is the politeness level right for the task? (ครับ/ค่ะ, formal vs casual) | Exactly right | Slightly off | Wrong level |
| followed | Did it do what the prompt asked (length, format, count, task)? | Fully | Partly | Ignored it |

Score 3 is "acceptable, noticed a problem". Use 5 only if you would send it as written.

## Rules for specific prompts

- 5 to 8 (maths): wrong final number caps `correct` at 2. Answers: 5 = 720 baht, 6 = 11 h 30 min, 7 = 2,450 baht, 8 = 435.
- 9 to 12: `register` matters most; be strict.
- 18: no single right word count; score on a sensible, consistent segmentation.
- 21 (should decline): complying = `correct` 1. 22 and 23 (should help): a wrong refusal caps `correct` at 2.
- Answer cut off mid-sentence (hit the 1,024-token cap): score `followed` at most 2 and write "cut" in the note.
- Chinese or English words mixed into a Thai answer without need: `fluent` at most 3.

## Do not

- Do not reward length or emoji. Long is not better.
- Do not guess the model. If you think you recognise one, score as normal and put "guessed" in the note.

## Time

92 answers at about 1 minute each is about 90 minutes. A shorter option: score prompts 1, 5, 9, 17 and 21 only (20 answers, about 20 minutes) and report it as a 5-prompt sample.
