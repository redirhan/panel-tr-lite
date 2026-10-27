# Panel TR — a Turkish synthetic focus group (Claude Code skill)

> **Pro edition coming soon.** To join the waitlist, DM "PANEL" to [@redirhanstudio](https://instagram.com/redirhanstudio) on Instagram.

Before you post a reel, a landing page, a carousel or an offer aimed at Turkey, show it to **10-54 different
people from Turkey**: a 19-year-old student in Eskişehir, a young hazelnut farmer near Ordu, a shopkeeper in
Denizli who uses Facebook more than Instagram, a mother of two in Gaziantep, a retiree who believes nothing
until he sees the price… Each answers in their own words, in Turkish: **would I stop in the first 3 seconds,
what is this, how credible is it, what would I do, what bothered me, the one thing I would change.**

Panel TR is a [Claude Code](https://docs.claude.com/en/docs/claude-code) skill. Claude subagents play the
people, a Python script does the counting, and every report ends with an honesty box.

> ### What Panel TR is not
> - **Not market research and not a sales forecast.** The answers are **synthetic**: a language model playing
>   persona cards. "4 of 10 said maybe" does not mean 40 % of the real audience.
> - It does not replace talking to real people. The report tells you whom to ask (3-5 real people) and what.
> - The personas do not watch the video or hear the sound: they see frames, screenshots and the audio
>   description you write.
> - About half of the card traits are marked `[varsayım]` (assumption) because there is no public measured data
>   on Turkish personality and taste. Age, gender, platform use, prices and rules are cited (TÜİK, DataReportal,
>   NapoleonCat, Click Analytic, the Official Gazette…). Every report prints the assumption share.
>
> **What it is for:** catching problems before a real audience does — an unclear offer, unreadable small type,
> an opening that stops nobody, something that puts off one age group.

## Editions

| | **Lite** (free, MIT) | **Pro** (paid, EULA) |
|---|---|---|
| Viewer cards | 10 (5 age bands) | 30 (5 age bands, 20+ provinces; metropolitan, Anatolian, district/village) |
| Buyer cards (business owners, marketers, agencies) | — | 24 across 10 segments (café/restaurant, bar/venue, fashion/retail, real estate, gym, events, creators, corporate marketing, agency, e-commerce) |
| Video / website / post stimulus | ✓ | ✓ |
| Quick report + 2 charts | ✓ | ✓ |
| A/B test (blind, counterbalanced) | — | ✓ |
| Segment tables and charts (age, gender, city type, Instagram use, segment, tech…) | — | ✓ |
| Report writer (clustered objections, ranked fixes) | — | ✓ |
| Price-expectation question (buyer panel) | — | ✓ |

The personas answer in Turkish; the skill instructions and scripts work from any Claude Code session.

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code) (subagents + image reading)
- macOS or Linux, Python 3.10+
- `ffmpeg` for video (macOS: `brew install ffmpeg`, Debian/Ubuntu: `sudo apt install ffmpeg`)
- Playwright + **Firefox** (or WebKit) for websites. Chrome/Chromium is never used.

## Install

```bash
mkdir -p ~/.claude/skills
unzip panel-tr-lite-v1.0.zip -d ~/.claude/skills/        # or panel-tr-pro-v1.0.zip
cd ~/.claude/skills/panel-tr
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install firefox             # website mode only (or: install webkit)
cp config.example.yaml config.yaml                         # optional: runs folder, browser, base rates
.venv/bin/python scripts/panel.py doctor
.venv/bin/python scripts/panel.py validate
```

You can also put the folder in a project's `.claude/skills/panel-tr/`.

## Quick start

In Claude Code:

> Run `~/Desktop/opening_reel.mp4` through Panel TR. It will appear in the Instagram Reels feed, posted by
> @mycafe. A quick check is enough.

Claude loads the skill, writes down the on-screen text and audio with you, builds the stimulus, runs 10 people in
2 independent subagents, counts, and brings back `PANEL_REPORT.md`. By hand:

```bash
S=~/.claude/skills/panel-tr; PY=$S/.venv/bin/python
RUN=$($PY $S/scripts/panel.py init-run --slug opening-reel)
# fill RUN/inputs/context.txt, onscreen.txt, audio.txt, caption.txt (in Turkish, neutral, no "our version")
$PY $S/scripts/make_stimulus.py video ~/Desktop/opening_reel.mp4 $RUN/stimulus \
    --onscreen $RUN/inputs/onscreen.txt --audio $RUN/inputs/audio.txt --caption $RUN/inputs/caption.txt
$PY $S/scripts/panel.py plan --run $RUN --panel viewer --n 10 --batches 2 \
    --stimulus $RUN/stimulus --context-file $RUN/inputs/context.txt
# in Claude Code, one fresh general-purpose subagent per RUN/batches/batch_NN.md:
#   "Read RUN/batches/batch_01.md and do exactly what it says. Write only the JSON file it names."
$PY $S/scripts/aggregate.py $RUN --title "Opening reel v1"
```

Website: `make_stimulus.py site https://example.com RUN/stimulus` (or a local `.html`).
Post: `make_stimulus.py post a.jpg,b.jpg RUN/stimulus --caption caption.txt`.

## Example run (fictional)

`examples/demo-kafe-reel/` — a 12-second silent opening reel for a made-up café ("Mavi Kozalak Kahve", Eskişehir),
drawn with Pillow, run end to end through the Lite panel (10 people, 2 batches):

- Stop in the first 3 s: **0/10** · action yes **0** / maybe **4** / no **6** · mean credibility **2.8/5**
- Most frequent request (7 of 10, in their own words): **real footage instead of a drawing** — the room, coffee being
  poured, the shop front or the owner's face ("çizimle güven gelmez" — a drawing doesn't build trust, V16).
- Single-person but concrete finds: **no price** — "the second one is free, but how much is the first?" (V23), a
  time-limited offer with a tiny date line (V09), an **empty orange box** at 6 s (V19), address/hours lines
  **unreadable** for a 63-year-old (V27).
- Checks: 0 evidence errors (nobody cited a frame that was not shown), no one-voice batches. Batch 2 was re-run with a
  fresh subagent after one card was edited; totals stayed the same (the wording changed).

Report: [`examples/demo-kafe-reel/PANEL_REPORT.md`](examples/demo-kafe-reel/PANEL_REPORT.md) (Turkish).

## Adapting it to your audience

- **Base rate:** `config.yaml` → `calibration`. Your own account's real engagement rate makes the panel more realistic.
- **Age weights:** `config.yaml` → `viewer_age_weights` (your Instagram Insights age split).
- **Your own sources and cards:** add a `.md` under `sources/` whose lines start with `Fnn ...`, register a two-letter
  key in `sources/index.yaml`, cite it in cards as `[KEY:Fnn]`, then `panel.py validate`. Keep client data on your
  own machine; never put it in a shared package.

## FAQ

**How accurate is it compared with a real survey?**
No accuracy claim. Panel TR is a pre-screen that finds obvious problems before real people see the work. In our own
runs the most useful output was not the numbers but the concrete fixes (unreadable text, missing price, empty frame).

**Why does almost everyone say "no"?**
The prompt carries a real base rate: on an average reel very few viewers do anything. A panel where most people say
"I'd DM them" is a red flag. The panel is there to find problems, not to be polite.

**How much of my Claude usage does it take?**
A 10-person quick check ≈ 2 subagents reading ~6-8 images each. A 30-person full panel ≈ 6 subagents + 1 report
writer. Panel TR itself calls no paid API.

**Does my data go anywhere?**
No. The scripts write everything to a local run folder. Images reach Claude only as part of your own Claude Code
session.

**Why not Chrome?**
Website mode deliberately launches only Playwright's Firefox or WebKit. There is no Chrome/Chromium code path.

**Windows?**
Tested on macOS and Linux. WSL should work but is not supported.

**What changes from Lite to Pro?**
Same scripts; the Pro package unlocks 54 cards, A/B, segment charts and the report writer. Your run folders stay as
they are.

## Licence

- **Lite:** MIT (`LICENSE`).
- **Pro:** commercial EULA (`LICENSE` = `EULA.md`): personal and agency use, reports are yours; no resale or
  redistribution of the skill files.
- Third-party components: `THIRD_PARTY_NOTICES.md`.

Redirhan Studio · redirhan.com
