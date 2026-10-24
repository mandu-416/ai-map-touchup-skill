# Editing maps in Google Flow (Nano Banana) via Claude in Chrome

Lessons from repeated map-fix rounds. Read before driving Flow in a browser.

## Uploading a map that was not made in Flow

- The project's 「미디어 업로드」 button opens a native file picker the browser tools cannot drive, and there is no file input in the page until it is clicked. Capture it instead: in the page run JavaScript that overrides `HTMLInputElement.prototype.click` to keep `type=file` inputs (append them to the body with an aria-label) instead of opening the picker, click 「미디어 업로드」 from that script, then find the captured input and use the file-upload tool on it.
- Flow then shows 「이 이미지를 사용할 권리」 with 취소 / 동의. That is a terms agreement: ask the user and let them click 동의 themselves; never accept it for them.
- The page can freeze after a large upload (screenshots time out). Reload the project URL; the upload is kept in the project's media.

## Sending an edit

- Open the image, choose edit, type the instruction, submit. Long `type` actions can time out even though the text went in: take a screenshot, and if the text is there, click the submit button instead of retyping.
- Stay on the edit page until the result appears (about 50–60 s). Navigating away within a few seconds cancels the edit silently.
- Afterwards reload the edit page and compare against the audit list. If nothing changed, the edit probably never ran.

## Writing the instruction

- Start with "Keep everything else exactly the same. Fix only:" and number each fix.
- Quote exact strings: `Change "점심: 슈크 13:00" to "점심: 슈크"`, `Delete the words "WEST", "EAST" and "NORTH"`.
- Text replacements and deletions work well. Freehand line surgery (re-routing one leg between existing pins) rarely works, so do that locally with `scripts/map_touchup.py`.
- Whole-stop edits work well when you locate the place by neighbouring labels: add a numbered pin + label card + dotted walk from an existing pin, or remove a pin with its card and renumber the next one.
- The submit arrow moves when the prompt box grows or the window is resized (device-pixel-ratio changes); take a screenshot and click the arrow you see, or the edit never starts.
- Positional fixes ("move the George St label to the east side of Town Hall") sometimes work, but verify them.

## Downloading

- On narrow windows the download button is inside the ⋮ menu: 미디어 다운로드 → 원본 크기.
- The file lands in Downloads as `<original name>_<timestamp>.jpg`; copy it to a working folder before editing.
- Downloading needs the user's OK. Get it once for the batch and say which files.

## When Flow refuses or blocks

- An "unusual activity" notice, a reCAPTCHA prompt, or a "reCAPTCHA 서비스에 연결할 수 없습니다" error means stop using Flow for now. Do not solve, click through or work around bot checks.
- A single later retry is fine if the block was a one-off. Otherwise download what you have (with permission) and finish locally.
- Tell the user that Flow blocked the edit and that you switched to local fixes.
