# Editing maps in Google Flow (Nano Banana) via Claude in Chrome

Lessons from repeated map-fix rounds. Read before driving Flow in a browser.

## Sending an edit

- Open the image, choose edit, type the instruction, submit. Long `type` actions can time out even though the text went in: take a screenshot, and if the text is there, click the submit button instead of retyping.
- Stay on the edit page until the result appears (about 50–60 s). Navigating away within a few seconds cancels the edit silently.
- Afterwards reload the edit page and compare against the audit list. If nothing changed, the edit probably never ran.

## Writing the instruction

- Start with "Keep everything else exactly the same. Fix only:" and number each fix.
- Quote exact strings: `Change "점심: 슈크 13:00" to "점심: 슈크"`, `Delete the words "WEST", "EAST" and "NORTH"`.
- Text replacements and deletions work well. Adding, moving or deleting lines rarely works, so do line work locally with `scripts/map_touchup.py`.
- Positional fixes ("move the George St label to the east side of Town Hall") sometimes work, but verify them.

## Downloading

- On narrow windows the download button is inside the ⋮ menu: 미디어 다운로드 → 원본 크기.
- Downloading needs the user's OK. Get it once for the batch and say which files.

## When Flow refuses or blocks

- An "unusual activity" notice, a reCAPTCHA prompt, or a "reCAPTCHA 서비스에 연결할 수 없습니다" error means stop using Flow for now. Do not solve, click through or work around bot checks.
- A single later retry is fine if the block was a one-off. Otherwise download what you have (with permission) and finish locally.
- Tell the user that Flow blocked the edit and that you switched to local fixes.
