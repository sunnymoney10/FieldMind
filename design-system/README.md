# FieldMind

**Know the brains of the operation.** FieldMind helps a field rep understand who runs a business and how its decisions get made before they walk in: what it found, how sure it is, and the one thing to find out first.

Belief: *Everything has a story. Every insight has a source.*

Use this system for every FieldMind screen, page, deck and marketing piece. Without it, AI-made work drifts toward a generic look.

## The idea

One line, one point. The line is every source FieldMind reads. The point is where they meet: the one finding that changes the visit.

The **mark** is a brain drawn as one bold, continuous line (in the spirit of the Higgsfield and Muse marks). The line is **the operation**: all the available data, folded into how the business works. It starts at the stem, runs the lobes, and folds inward to a citron point in a carbon ring: **the brains behind the operation**, the one finding that changes the visit. See *Logos*.

## Principles

1. **One pink per screen.** `signal-pink` marks the single thing to do (Log visit, Save visit, Research). Selection is shown in `ink`/`carbon`, links are underlined `ink`, and status never uses pink.
2. **Daylight first.** Reps read outdoors. The default theme is Daylight (`paper` = Raw Paper); Night follows the phone's dark mode.
3. **Clarity over effect.** No gradients, glass, glows or blur. Text meets 4.5:1 in both themes; nothing under 13px; every tap target is at least `target-min` (44px).
4. **Say how sure.** Every answer carries one of three certainty levels (see *Certainty*). Never claim more than the sources show.
5. **Leave out what wasn't found.** No rows of "Unknown". An empty section disappears.

## Voice

FieldMind talks like a sharp colleague in the passenger seat.

- **Lead with the answer.** "Owner: Sam Ratto."
- **Say how sure.** "Likely", "may be out of date", "not confirmed".
- **Name the next step.** "Ask who signs for the utility account."
- **Plain field words.** No internal terms, file names, IDs or scores. Sentence case everywhere.

| Instead of | Write |
|---|---|
| Business ownership: Sam Ratto (older information, 2023) | Owner: Sam Ratto (2023, may be out of date) |
| Not found: operations, property, HVAC/facilities | *(leave it out)* |
| Experiment 001 benchmark | Research quality |

## Three voices in type

- **FieldMind** speaks in **Inter** (`sans`) for everything a rep reads, with the `ss04` set on so I, l and 1 are distinct and zeros stay plain (suite numbers and addresses). Titles, business names and the wordmark use **Inter Display** (`display`) at 800, tracked tight (-0.015em; wordmark -0.035em). The mark carries the personality; the text stays clear in sunlight.
- **The source** speaks in IBM Plex Mono (`mono`): only a site name and date, at 14px.
- **The rep** writes in Caveat (`hand`), in `pink-text`: their own notes and marketing annotations only.

Fonts are Google-hosted: load `Inter:opsz,wght@14..32,400..800` (the optical-size axis gives the display cut at large sizes), `IBM Plex Mono:wght@500` and `Caveat:wght@600`. If reps still misread characters in sun, test Atkinson Hyperlegible Next for body text.

## Color jobs

| Token | Job |
|---|---|
| `signal-pink` | The one action, the mark, the Find-out-first shadow |
| `citron` | The point: the dot in the brain, and tags for this stop's open question |
| `iron-oxide` | Conflict, Don't contact, overdue |
| `aluminum` | Plain info tags |
| `carbon` / `raw-paper` | Fixed dark and light for icons and fills |
| `paper`, `surface`, `ink`, `ink-muted`, `line` | The themed ground and text |

`signal-pink-print` (#E72D7D) is for print only: carbon text on it is 3.96:1, below the 4.5:1 minimum.

## Layout

- Phone first: 390px wide, `space-4` side margins, cards at `radius-lg` on `paper`.
- Primary actions sit at the bottom (footer buttons, the center Research button), within thumb reach.
- Brief order: name, address, one tag → Find out first → Overview / Business / Energy / Notes → footer Research · Sources · **Log visit**.

## Don'ts

- No second pink element on a screen.
- No citron text on paper; no pink status tags.
- Don't redraw, fill or break the brain line, add a second dot, or turn the mark into a glowing AI swirl. No literal buildings, doors or storefronts in the mark: it is about the operation, not the property.
- No uppercase or mono labels in the app (print only).
- No glowing AI swirls, gradients or sparkle icons.
