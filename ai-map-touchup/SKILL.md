---
name: ai-map-touchup
description: Proofread and repair AI-generated illustrated maps (Google Flow / Nano Banana, Gemini, DALL·E, Midjourney route maps, travel day maps, campus or event maps) so they match the real itinerary and geography. Audits every map for typos, duplicate labels, English leftovers, wrong landmark sides and dotted route lines that skip, reverse or wander, then fixes them — first with the image tool's edit prompt, and when that fails or is blocked, deterministically with a bundled Pillow/OpenCV script that erases wrong lines and labels, redraws dotted routes with direction arrows, rotates street names onto roads, and adds leg badges and legend entries. Use whenever someone says a generated map has 오타, 중복 라벨, 잘못된 동선/점선, 위치가 틀렸다, "지도 고쳐줘", "동선 점선 맞는지 확인해", "fix the route lines on this map", or wants AI map images cleaned up before putting them in a report.
---

# AI map touch-up

Image models draw convincing maps that are quietly wrong: a label printed twice, a time glued onto the wrong card, a dotted route that jumps from stop 2 straight to stop 4, a landmark on the wrong side of the street. Prompt-based edits fix text well but rarely move or delete lines. This skill is the loop that gets a map to "correct enough to follow": audit against the plan, try a model edit, then finish locally with exact pixel operations.

## 1. Audit before touching anything

Write down the ground truth first, per map: the ordered stops (with times), which stops are alternatives ("3A 또는 3B"), restaurants, and any real-geography facts that matter (which side of a street a landmark is on, which station is used). Then look at the map at full size and in zoomed crops, and list every defect in these buckets:

- **Text:** typos in place and street names, English labels where the map should be Korean, a time or price attached to the wrong label, the legend title untranslated.
- **Duplicates:** the same place name twice (e.g. a card "오페라하우스" plus a printed "Opera House"), a pin number used twice, the same restaurant listed twice, compass words (NORTH/WEST) the design doesn't need.
- **Routes:** for each leg i → i+1, is there a line, does it start and end at the right pins, does the arrow point the right way, does it follow streets rather than cut through buildings or water, and is there any stray line that belongs to no leg. Missing legs and stray stubs are the most common faults.
- **Geography:** landmarks on the correct side of streets and harbours, street labels on the street they name (a "Kent St" label lying on an east–west road is wrong for a north–south street).

Why: users notice these one round at a time ("오타 고쳐줘" → "중복 라벨도" → "점선이 맞는지 확인해"). Auditing all buckets at once avoids three more rounds.

## 2. Try the image tool's edit first, but verify

Removing a stop from a map is more than its pin: also its label card, the route legs to and from it, its walker/train icons and the title or inset heading that names it. Put all of them on the audit list before editing.

If the map came from a tool with an edit mode (Google Flow, Gemini), send one edit that lists every text fix explicitly and says "keep everything else exactly the same". Name exact strings to delete or replace. Then check the result against the audit list — edits often fix text but ignore line changes, or move things you didn't ask about.

For Google Flow browser specifics (uploading a map that was not made in Flow, the rights dialog, staying on the page until the edit finishes, the download menu, reCAPTCHA), read `references/flow-editing.md`.

Flow is good at whole-stop changes on an uploaded map when the instruction pins down the place by neighbouring labels: "add a dark blue pin numbered 6 on the green lawn just south of the "달링 쿼터" label, a white label card with "…" and "19:15–19:45", and a red dotted walking route from pin 2 to pin 6", or "remove pin 5 and its label card, fill with the surrounding background, renumber pin 6 to 5". Check that it did not degrade small text elsewhere (legend lines are the usual casualty); paste the old legend back with a crop if so.

If the tool shows a CAPTCHA, an "unusual activity" notice or a connection error for its bot check, do not try to solve or get around it. Switch to step 3, which needs no external service, and tell the user why.

## 3. Finish locally with `scripts/map_touchup.py`

Requires Python 3 with `pillow`, `numpy` and `opencv-python-headless`. On Windows run with `python -I`.

1. **Find coordinates.** `python -I scripts/map_touchup.py grid map.jpg zoom.png x1,y1,x2,y2 --scale 2` produces a zoomed crop with pixel ticks. Read off label boxes, pin tips, and road centre lines. Do this for every region you will touch; guessing from the full image misses by 10–20 px, enough to clip a neighbouring character.
2. **Write a spec.** A JSON list of ops applied in order (full reference in the script's docstring; worked example in `examples/rainy-day-route-fix.json`). The usual order:
   - `strip_color` — remove all old route lines of one colour at once, with `protect` boxes around pins, legend swatches, coloured text and red-roofed buildings. Use this when routes are wrong enough to redraw; it's cleaner than erasing segment by segment.
   - `inpaint` — small leftovers: dots under protect boxes, a label lying on a road.
   - `fill` — labels on flat blocks (sample a clean patch of the same block). Large inpaint boxes smear road white into blocks, so prefer fill there.
   - `copy_line` — a label lying across a road and the block next to it: rebuild the box from one clean row (vertical roads) or column (horizontal roads). Edges stay sharp where `fill` would leave a square patch.
   - `palette_fill` — several pins, labels and dotted lines on a flat-coloured map (a dark night inset, pastel blocks). It learns the map's own fill colours, replaces marks with the nearest clean pixel and snaps the boxes to those colours, so halos and dots vanish without smears. Protect neighbouring labels with `keep` (a street name half inside a box gets eaten otherwise) and pass small fills the sample misses (a park, one green block) in `extra_rgb`; finish any leftover patch with a `fill`.
   - `text` — replacement labels; `angle` puts street names along their road (≈84–90° for north–south streets).
   - `route` — one op per leg, points along road centre lines, ending just short of the next pin. Each leg gets a mid-route arrow so direction stays readable where legs meet.
   - `badge` — "1 → 2" style tags beside each leg when legs share or cross roads.
   - `legend_entry` — when you add a new line colour (e.g. orange for an optional stop).
3. **Run and inspect.** `python -I scripts/map_touchup.py apply map.jpg out.jpg spec.json`, then view the whole image and zoomed crops of every edited region. Look specifically for: clipped characters next to an erased label, smears, leftover dots, a new line crossing text, badges covering labels. Adjust the spec and rerun from the original image, never from a previous output, so fixes don't stack artefacts.

Design rules that made the result readable:

- Alternative stops get their own colour (orange dotted) and a legend line, not a second red line.
- Two legs on the same road: route them on different streets where possible; otherwise rely on badges and arrows rather than drawing them on top of each other.
- Keep pins, cards and the title untouched; you are correcting, not redesigning.

## 4. Deliver

Save finals with a new version suffix rather than overwriting earlier versions. When a map exists in a date-free and a dated version, edit one and derive the other by redrawing only the title box, so both stay identical. If the maps live in a report, replace each image and confirm the report now shows the new files. In the summary, list what changed per map and be explicit about anything still imperfect (an approximate position, a faint smear), and remind that these are illustrations, not navigation maps.

## Privacy

Itinerary maps often show the hotel and dates. Don't publish the map images anywhere public unless the user asks; example specs in this repo contain coordinates only.
