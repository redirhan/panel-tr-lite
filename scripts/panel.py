#!/usr/bin/env python3
"""Panel TR: persona checks, panel selection, batch prompts, aggregator prompt.

    panel.py doctor                        check Python deps, ffmpeg, Playwright browser, config, edition
    panel.py validate                      every trait cites [KEY:Fnn|line] that exists, or [varsayım]
    panel.py cite V07                      print a persona's traits next to the cited source lines
    panel.py init-run --slug kafe-reel     create RUNS_DIR/<date>_<slug>/inputs/ with templates
    panel.py plan --run RUN --panel viewer --n 10 --batches 2 --stimulus RUN/stimulus --context-file ctx.txt
    panel.py plan ... --dry-run            print who would be picked, write nothing
    panel.py plan ... --stimulus-a RUN/stimulus_A --stimulus-b RUN/stimulus_B      (A/B test, Pro)
    panel.py report-prompt --run RUN --title "..." --real-people "..."             (Pro)

Writes only inside RUN. Edition: EDITION file (lite|pro) or PANEL_TR_EDITION.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import random
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SKILL, TAG, VERSION, age_band, config_path, edition, is_pro, load_config,  # noqa: E402,F401
                    load_personas, load_sources, persona_dir, require_pro, resolve_cite, runs_dir,
                    source_lines, system_summary)

DEFAULT_ACTION = {
    "viewer": "Bunu gördükten sonra bir şey yapar mıydın: hesabı takip etmek, DM atıp bir şey sormak, "
              "kaydetmek/paylaşmak, gidip denemek ya da satın almak? Hangisini, neden?",
    "buyer": "Bunu sunan firmaya kendi işin için ulaşır mıydın: DM atmak, teklif istemek ya da satın almak? "
             "Hangisini, neden?",
}
PRICE_Q = ("Bu işi/ürünü senin için yapsalar ya da sana satsalar tek seferlik ya da aylık ne kadar öderdin? "
           "(TL, KDV hariç; 'ödemem' de geçerli cevap.)")


# ---------------------------------------------------------------- validate / cite
def cmd_validate(_a) -> int:
    src = load_sources()
    lines_cache: dict[str, list[str]] = {}
    errors, n_traits, n_assume = [], 0, 0
    ids = set()
    people = load_personas()
    if not people:
        errors.append(f"no persona files found in {persona_dir()}")
    for k, f in src.items():
        if not f.exists():
            errors.append(f"sources/index.yaml: {k} -> missing file {f.name}")
    for p in people:
        if p["id"] in ids:
            errors.append(f"{p['id']}: duplicate id")
        ids.add(p["id"])
        need = ["id", "panel", "name", "age", "gender", "city", "city_size", "ig_usage", "tech", "stance",
                "voice", "traits"] + (["age_band", "deneme"] if p.get("panel") == "viewer" else ["segment"])
        for key in need:
            if key not in p:
                errors.append(f"{p['id']}: missing {key}")
        if p.get("panel") == "viewer" and "age" in p and p.get("age_band") != age_band(int(p["age"])):
            errors.append(f"{p['id']}: age {p['age']} does not match age_band {p.get('age_band')}")
        for t in p.get("traits", []):
            n_traits += 1
            m = TAG.search(t)
            if not m:
                errors.append(f"{p['id']}: no [KAYNAK:Fnn] or [varsayım] tag: {t}")
                continue
            if m.group(1) == "varsayım":
                n_assume += 1
                continue
            key = m.group(2)
            if key not in src:
                errors.append(f"{p['id']}: unknown source key {key}")
                continue
            if key not in lines_cache:
                if not src[key].exists():
                    continue
                lines_cache[key] = source_lines(src[key])
            if resolve_cite(lines_cache[key], m.group(3), m.group(4)) is None:
                errors.append(f"{p['id']}: citation {key}:{m.group(3)}{'-' + m.group(4) if m.group(4) else ''} "
                              f"not found in {src[key].name}")
    for e in errors:
        print("ERROR", e)
    share = n_assume / max(1, n_traits)
    print(f"Panel TR {VERSION} ({edition()}): {len(ids)} personas, {n_traits} traits, "
          f"{n_assume} [varsayım] ({share:.0%}), {len(errors)} errors")
    return 1 if errors else 0


def cmd_cite(a) -> int:
    src = load_sources()
    for p in load_personas():
        if p["id"] != a.id:
            continue
        print(f"{p['id']} {p['name']} {p['age']} {p['city']} — {p['stance']}")
        for t in p["traits"]:
            m = TAG.search(t)
            print(f"\n• {t}")
            if m and m.group(2) and m.group(2) in src:
                lines = source_lines(src[m.group(2)])
                for i in resolve_cite(lines, m.group(3), m.group(4)) or []:
                    print(f"    {m.group(2)}:{i}: {lines[i - 1][:200]}")
        return 0
    print("no such persona")
    return 1


def cmd_doctor(_a) -> int:
    ok = True
    cfg = load_config()
    print(f"Panel TR {VERSION} — edition: {edition()} — {system_summary()}")
    print(f"skill dir: {SKILL}")
    print(f"config: {config_path() or '(none, defaults; copy config.example.yaml to config.yaml)'}")
    print(f"runs_dir: {runs_dir()}")
    print(f"personas: {persona_dir()}  ({len(load_personas('viewer'))} viewers, {len(load_personas('buyer'))} buyers)")
    for mod, why in [("yaml", "required"), ("PIL", "required"), ("playwright", "site mode"),
                     ("faster_whisper", "optional transcript"), ("whisper", "optional transcript")]:
        try:
            importlib.import_module(mod)
            print(f"  [ok] python: {mod}")
        except ImportError:
            print(f"  [{'MISSING' if why == 'required' else '--'}] python: {mod} ({why})")
            ok = ok and why != "required"
    for tool in ("ffmpeg", "ffprobe"):
        print(f"  [{'ok' if shutil.which(tool) else '--'}] {tool} (video mode)")
    print(f"  browser for site mode: {cfg['browser']} (Chrome/Chromium never used)")
    if sys.version_info < (3, 10):
        print("  [MISSING] Python 3.10+ required")
        ok = False
    return 0 if ok else 1


def cmd_init_run(a) -> int:
    base = Path(a.root).expanduser() if a.root else runs_dir()
    run = base / f"{dt.date.today().isoformat()}_{re.sub(r'[^a-z0-9-]+', '-', a.slug.lower()).strip('-')}"
    inp = run / "inputs"
    inp.mkdir(parents=True, exist_ok=True)
    templates = {
        "context.txt": "Kişi bunu nerede ve nasıl görüyor? (ör. Reels akışında karşına çıkıyor; paylaşan hesap "
                       "@ornek; açıklama metni var/yok.) Kimin yaptığını, neyi hedeflediğini, hangi sürümü "
                       "tercih ettiğinizi YAZMAYIN.\n",
        "onscreen.txt": "# Videodaki her ekran yazısı, zaman aralığıyla ve ekranda göründüğü gibi:\n# 0.0-2.5 METİN\n",
        "audio.txt": "# Duyulanlar, olgu olarak: müzik/konuşma/efekt var mı, hangi saniyeden, görüntüyle uyumlu mu.\n",
        "caption.txt": "",
    }
    for name, body in templates.items():
        f = inp / name
        if not f.exists():
            f.write_text(body, encoding="utf-8")
    print(run)
    return 0


# ---------------------------------------------------------------- selection
def diversity_pick(pool: list[dict], k: int, rng: random.Random, taken: list[dict]) -> list[dict]:
    """Greedy: prefer personas whose (gender, city_size, ig_usage, tech, deneme, segment) are least seen."""
    pool = pool[:]
    rng.shuffle(pool)
    chosen = []
    for _ in range(min(k, len(pool))):
        seen = taken + chosen

        def novelty(p):
            score = 0
            for f in ("gender", "city_size", "ig_usage", "tech", "deneme", "segment"):
                if f in p:
                    score -= sum(1 for s in seen if s.get(f) == p.get(f))
            return score
        best = max(pool, key=novelty)
        chosen.append(best)
        pool.remove(best)
    return chosen


def out_of_target(p: dict) -> bool:
    """Viewer who rarely tries new places/products or buys online (deneme = hic|nadiren)."""
    return p.get("deneme") in ("hic", "nadiren")


def select(panel: str, n: int, seed: int, ids: list[str] | None, segments: list[str] | None,
           out_share: float = 0.2, local: str | None = None) -> list[dict]:
    people = load_personas(panel)
    if ids:
        byid = {p["id"]: p for p in people}
        missing = [i for i in ids if i not in byid]
        if missing:
            sys.exit(f"unknown persona ids for this edition/panel: {', '.join(missing)}")
        return [byid[i] for i in ids]
    if n > len(people):
        print(f"note: only {len(people)} {panel} personas in this edition; panel size reduced to {len(people)}")
        n = len(people)
    if n == len(people):                                     # whole set (e.g. Lite's 10 cards)
        return list(people)
    rng = random.Random(seed)
    if panel == "viewer":
        # Mostly in-target people, a fixed share of out-of-target ones (their "hayır" is targeting info).
        is_local = (lambda p: local.casefold() in p["city"].casefold()) if local else (lambda p: True)
        n_out = max(1, round(n * out_share))
        outs = diversity_pick([p for p in people if out_of_target(p)], n_out, rng, [])
        bands = defaultdict(list)
        for p in people:
            if not out_of_target(p):
                bands[p["age_band"]].append(p)
        # seats per band over the WHOLE panel (>= 1 per band when n >= 5), minus the out-of-target seats
        VIEWER_WEIGHTS = load_config()["viewer_age_weights"]
        alloc = {b: (1 if n >= len(VIEWER_WEIGHTS) else 0) for b in VIEWER_WEIGHTS}
        left = n - sum(alloc.values())
        raw = {b: left * w / sum(VIEWER_WEIGHTS.values()) for b, w in VIEWER_WEIGHTS.items()}
        for b in raw:
            alloc[b] += int(raw[b])
        for b in sorted(raw, key=lambda b: raw[b] - int(raw[b]), reverse=True)[:n - sum(alloc.values())]:
            alloc[b] += 1
        for p in outs:
            alloc[p["age_band"]] = max(0, alloc[p["age_band"]] - 1)
        while sum(alloc.values()) > n - len(outs):          # an out-of-target seat landed on a 0 band
            alloc[max(alloc, key=alloc.get)] -= 1
        chosen = list(outs)
        for b, k in alloc.items():   # local people first (e.g. --local İzmir), others only to fill
            loc = [p for p in bands[b] if is_local(p)]
            got = diversity_pick(loc, k, rng, chosen)
            chosen += got + diversity_pick([p for p in bands[b] if p not in loc], k - len(got), rng, chosen + got)
        short = n - len(chosen)                              # a band ran out of cards: fill from the rest
        if short > 0:
            rest = [p for p in people if p not in chosen]
            rest.sort(key=out_of_target)                     # in-target first
            chosen += diversity_pick([p for p in rest if not out_of_target(p)], short, rng, chosen)
            chosen += diversity_pick([p for p in rest if out_of_target(p)], n - len(chosen), rng, chosen)
    else:
        segs = defaultdict(list)
        for p in people:
            if not segments or p["segment"] in segments:
                segs[p["segment"]].append(p)
        chosen, order = [], list(segs)
        rng.shuffle(order)
        while len(chosen) < n and any(segs.values()):
            for s in order:
                if segs[s] and len(chosen) < n:
                    pick = diversity_pick(segs[s], 1, rng, chosen)[0]
                    segs[s].remove(pick)
                    chosen.append(pick)
    # always keep at least one sceptic / out-of-target person in the panel
    sceptic = lambda p: any(w in p["stance"] for w in ("supheci", "hic", "karsit", "muhafazakar", "mesafeli")) or \
        p.get("deneme") == "hic"
    if not any(sceptic(p) for p in chosen):
        extra = [p for p in people if sceptic(p) and p not in chosen]
        if extra:
            chosen[-1] = rng.choice(extra)
    return chosen


# ---------------------------------------------------------------- prompts
def schema(panel: str, ab: bool) -> str:
    q = {
        "ilk_3_saniye": {"durur_mu": "evet|hayır", "neden": "..."},
        "ne_anlatiyor": "...",
        "guvenilirlik": {"puan": "1-5 (sayı)", "neden": "..."},
        "aksiyon": {"karar": "evet|belki|hayır", "ne_yapar": "takip|DM|kaydet/paylaş|gider|teklif ister|satın alır|hiçbiri",
                    "gercekci_neden": "..."},
        "fiyat_beklentisi": ({"min_tl": "sayı ya da null", "max_tl": "sayı ya da null",
                              "birim": "tek_seferlik|aylik|reel_basi", "not": "..."} if panel == "buyer" else None),
        "en_buyuk_itiraz": "...",
        "tek_somut_duzeltme": "...",
        "dayanak": ["t=0.0", "t=12.0"],
        "goremedigim": "... ya da boş",
        "kendi_sozleriyle": "kişinin ağzından tek cümle",
    }
    if ab:
        obj = {"persona_id": "V07", "secenekler": {"1": q, "2": "aynı alanlar"},
               "tercih": {"secim": "1|2|hiçbiri", "neden": "..."}}
    else:
        obj = {"persona_id": "V07", **q}
    return json.dumps([obj], ensure_ascii=False, indent=1)


def stimulus_block(stim_dir: Path, label: str | None) -> str:
    text = (stim_dir / "stimulus.md").read_text(encoding="utf-8")
    absd = str(stim_dir.resolve())
    text = re.sub(r"`((?:frames|shots|post)/[^`]+|sheet_[^`]+)`", lambda m: f"`{absd}/{m.group(1)}`", text)
    text = text.replace("`frames/tXXX.XX.jpg`", f"`{absd}/frames/tXXX.XX.jpg`")
    text = re.sub(r"^# ", "### ", text, flags=re.M).replace("\n## ", "\n#### ")
    head = f"## {label}\n\n" if label else ""
    return head + text


def persona_card(p: dict) -> str:
    q = {k: v for k, v in p.items() if k not in ("traits", "panel", "stance")}   # stance = our sorting label
    q["özellikler"] = [TAG.sub("", t).strip() for t in p["traits"]]
    return "```yaml\n" + yaml.safe_dump(q, allow_unicode=True, sort_keys=False, width=110) + "```"


def rel_to(run: Path, p) -> str:
    """Store paths relative to the run folder when possible (portable plan.json)."""
    p = Path(p).resolve()
    try:
        return str(p.relative_to(run.resolve()))
    except ValueError:
        return str(p)


def cmd_plan(a) -> int:
    run = Path(a.run)
    ab = bool(a.stimulus_a and a.stimulus_b)
    if a.panel == "buyer":
        require_pro("alıcı paneli (--panel buyer)")
    if ab:
        require_pro("A/B testi (--stimulus-a/--stimulus-b)")
    if not ab and not a.stimulus:
        sys.exit("give --stimulus DIR or --stimulus-a and --stimulus-b")
    for d in ([a.stimulus] if not ab else [a.stimulus_a, a.stimulus_b]):
        if not a.dry_run and not (Path(d) / "stimulus.md").exists():
            sys.exit(f"{d}/stimulus.md not found — run make_stimulus.py first")
    calib = a.calibration or load_config()["calibration"][a.panel]
    ids = a.ids.split(",") if a.ids else None
    segs = a.segments.split(",") if a.segments else None
    chosen = select(a.panel, a.n, a.seed, ids, segs, a.out_share, a.local)
    rng = random.Random(a.seed + 1)
    rng.shuffle(chosen)
    k = max(1, min(a.batches, len(chosen)))
    batches = [chosen[i::k] for i in range(k)]
    if a.dry_run:
        print(f"[dry-run] {edition()} — {len(chosen)} {a.panel} personas in {k} batches (nothing written)")
        for bi, members in enumerate(batches, 1):
            print(f"  batch {bi:02d}: " + ", ".join(
                f"{p['id']} {p['name']} {p['age']} {p['city_size']}" for p in members))
        return 0
    (run / "batches").mkdir(parents=True, exist_ok=True)
    (run / "responses").mkdir(exist_ok=True)
    context = Path(a.context_file).read_text(encoding="utf-8").strip() if a.context_file else (a.context or "")
    if not context:
        sys.exit("give --context or --context-file (neutral: where/how the person meets the material)")
    tpl = (SKILL / "prompts" / "persona_batch.md").read_text(encoding="utf-8")
    tpl = re.sub(r"<!--.*?-->\n*", "", tpl, flags=re.S)
    plan = {"panel_tr": VERSION, "edition": edition(), "panel": a.panel, "seed": a.seed, "ab": ab,
            "context": context, "calibration": calib,
            "action_question": a.action or DEFAULT_ACTION[a.panel],
            "stimulus": {k: rel_to(run, v) for k, v in
                         ({"single": a.stimulus} if not ab else {"A": a.stimulus_a, "B": a.stimulus_b}).items()},
            "batches": []}
    for bi, members in enumerate(batches, 1):
        if ab:   # counterbalance: odd batches see A first, even batches B first
            order = ["A", "B"] if bi % 2 else ["B", "A"]
            key = {"1": order[0], "2": order[1]}
            stim = "\n\n".join(stimulus_block(Path(getattr(a, f"stimulus_{key[s].lower()}")), f"Video/Seçenek {s}")
                               for s in ("1", "2"))
            ab_rule = ("8. İki seçenek var (Seçenek 1 ve 2). Hangisinin kimin tercihi olduğunu bilmiyorsun. "
                       "Her seçenek için soruları ayrı cevapla, sonra `tercih` alanında birini seç ya da "
                       "'hiçbiri' de.")
        else:
            key, stim, ab_rule = None, stimulus_block(Path(a.stimulus), None), ""
        out_json = (run / "responses" / f"batch_{bi:02d}.json").resolve()
        body = (tpl.replace("{{BATCH_ID}}", f"{bi:02d}").replace("{{N}}", str(len(members)))
                .replace("{{CONTEXT}}", context).replace("{{RUN_DIR}}", str(run.resolve()))
                .replace("{{STIMULUS_BLOCK}}", stim)
                .replace("{{CALIBRATION}}", calib)
                .replace("{{AB_RULE}}", ab_rule)
                .replace("{{ACTION_QUESTION}}", plan["action_question"])
                .replace("{{PRICE_QUESTION}}", PRICE_Q if a.panel == "buyer" else "(bu panelde sorulmuyor; null yaz)")
                .replace("{{OUTPUT_PATH}}", str(out_json))
                .replace("{{SCHEMA}}", schema(a.panel, ab))
                .replace("{{PERSONAS}}", "\n\n".join(persona_card(p) for p in members)))
        bf = run / "batches" / f"batch_{bi:02d}.md"
        bf.write_text(body, encoding="utf-8")
        plan["batches"].append({"batch": bi, "prompt": rel_to(run, bf), "output": rel_to(run, out_json),
                                "personas": [p["id"] for p in members], "ab_key": key})
    (run / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(chosen)} personas in {k} batches -> {run / 'batches'}")
    for b in plan["batches"]:
        print(f"  batch {b['batch']:02d}: {', '.join(b['personas'])}" + (f"  key={b['ab_key']}" if ab else ""))
    return 0


def cmd_report_prompt(a) -> int:
    require_pro("rapor yazarı (report-prompt)")
    run = Path(a.run)
    plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
    ids = {i for b in plan["batches"] for i in b["personas"]}
    people = [p for p in load_personas() if p["id"] in ids]
    tr = [t for p in people for t in p["traits"]]
    share = sum(1 for t in tr if t.rstrip().endswith("[varsayım]")) / max(1, len(tr))
    tpl = (SKILL / "prompts" / "aggregator.md").read_text(encoding="utf-8")
    tpl = re.sub(r"<!--.*?-->\n*", "", tpl, flags=re.S)
    body = (tpl.replace("{{TITLE}}", a.title).replace("{{RUN_DIR}}", str(run.resolve()))
            .replace("{{ASSUMPTION_SHARE}}", f"%{round(share * 100)}")
            .replace("{{REAL_PEOPLE}}", a.real_people))
    out = run / "aggregator_prompt.md"
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out}  ([varsayım] share in this panel: {share:.0%})")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("doctor")
    ir = sub.add_parser("init-run")
    ir.add_argument("--slug", required=True)
    ir.add_argument("--root", help="override runs_dir from config")
    c = sub.add_parser("cite")
    c.add_argument("id")
    p = sub.add_parser("plan")
    p.add_argument("--run", required=True)
    p.add_argument("--panel", choices=["viewer", "buyer"], required=True)
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--batches", type=int, default=6)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--ids", help="explicit persona ids, comma-separated (overrides --n)")
    p.add_argument("--segments", help="buyer segments to draw from, comma-separated")
    p.add_argument("--out-share", type=float, default=0.2,
                   help="viewer panels: share of out-of-target people (deneme = hic/nadiren), default 0.2")
    p.add_argument("--local", help="viewer panels: prefer in-target people whose city contains this (e.g. İzmir)")
    p.add_argument("--stimulus")
    p.add_argument("--stimulus-a")
    p.add_argument("--stimulus-b")
    p.add_argument("--context")
    p.add_argument("--context-file")
    p.add_argument("--action", help="override the action question (Turkish)")
    p.add_argument("--calibration", help="override the real-world base-rate sentence (default: config.yaml)")
    p.add_argument("--dry-run", action="store_true", help="print the selection and batches, write nothing")
    r = sub.add_parser("report-prompt")
    r.add_argument("--run", required=True)
    r.add_argument("--title", required=True)
    r.add_argument("--real-people", required=True)
    a = ap.parse_args()
    sys.exit({"validate": cmd_validate, "cite": cmd_cite, "plan": cmd_plan, "doctor": cmd_doctor,
              "init-run": cmd_init_run, "report-prompt": cmd_report_prompt}[a.cmd](a))


if __name__ == "__main__":
    main()
