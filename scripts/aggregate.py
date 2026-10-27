#!/usr/bin/env python3
"""Panel TR — count panel answers: RUN/responses/*.json -> RUN/data/{panel_data.md,panel_data.json,all_answers.md,chart_*.png}.

Counts are done here (deterministic), never by the language model. Also runs honesty checks:
  - schema: every expected persona answered, required fields present, values in range;
  - evidence: every `dayanak` points at a frame/shot that was actually shown (else = hallucination flag);
  - card echo: a persona repeats a sentence from its own card instead of reacting to the stimulus;
  - convergence: word overlap of objections+fixes inside a batch vs across batches (one-voice panel flag).

Lite: totals + age-band table + 2 charts, and a ready quick report RUN/PANEL_REPORT.md.
Pro:  + tables and charts for every segment dimension, A/B comparison and order effect; the full
      report is written by a fresh subagent from `panel.py report-prompt` (quick report kept as data/quick_report.md).

    python scripts/aggregate.py RUN [--title "Kafe reels v2"] [--real-people "2 müdavim; 1 kafe sahibi"]
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import TAG, VERSION, age_band, edition, font, is_pro, load_personas  # noqa: E402

# diverging blue <-> red with neutral grey midpoint; chart chrome tokens
C_YES, C_MAYBE, C_NO = (42, 120, 214), (240, 239, 236), (227, 73, 72)
INK, INK2, MUTED, SURF, RING = (11, 11, 11), (82, 81, 78), (137, 135, 129), (252, 252, 251), (195, 194, 183)
STOP = set("ve ile bir bu da de çok daha için ama gibi ne o şu mi mı mu mü ya en olsun var yok ki her "
           "olarak daha sonra bence ben biz sen".split())
DEFAULT_REAL_PEOPLE = ("hedef kitlenizden 3-5 gerçek kişi (en az biri şüpheci, biri 45 yaş üstü, biri "
                       "hedef şehrin dışından)")


def norm_yn(v: str | None) -> str:
    v = (v or "").strip().lower()
    if v.startswith(("evet", "yes")):
        return "evet"
    if v.startswith(("bel", "maybe", "kararsız")):
        return "belki"
    if v.startswith(("hay", "no")):
        return "hayır"
    return "?"


def shown_refs(run: Path, plan: dict) -> set[str]:
    refs = set()
    for d in plan["stimulus"].values():
        m = json.loads((run / d / "stimulus.json").read_text(encoding="utf-8"))
        for f in m["frames"]:
            t = f["t"]
            if isinstance(t, (int, float)):
                refs.add(f"t={float(t):.1f}")
            else:
                refs.add(str(t))
            refs.add(Path(f["file"]).name)
        refs.update(Path(s).name for s in m.get("sheets", []))
    return refs


def ref_ok(ref: str, shown: set[str]) -> bool:
    s = ref.strip()
    m = re.match(r"(?i)^t\s*=?\s*(\d+(?:[.,]\d+)?)", s)
    if m:
        return f"t={float(m.group(1).replace(',', '.')):.1f}" in shown
    return any(s == x or (len(s) > 4 and s in x) for x in shown)


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-zçğıöşüâî]+", (s or "").lower()) if len(w) > 2 and w not in STOP}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def group_keys(p: dict) -> dict:
    if p["panel"] == "viewer":
        return {"Yaş": p["age_band"], "Cinsiyet": p["gender"], "Yer": p["city_size"], "Instagram": p["ig_usage"],
                "Yeni şey deneme": p.get("deneme", "?")}
    return {"Segment": p["segment"], "Yaş": age_band(p["age"]), "Yer": p["city_size"], "Teknoloji": p["tech"]}


ORDER = {"Yaş": ["18-24", "25-34", "35-44", "45-54", "55+"], "Yer": ["metropol", "anadolu", "ilce_koy"],
         "Instagram": ["yogun", "orta", "hafif"], "Teknoloji": ["yuksek", "orta", "dusuk"],
         "Yeni şey deneme": ["duzenli", "ara_sira", "nadiren", "hic"]}


def table(rows: list[dict], dim: str, opt: str) -> tuple[list[str], list[tuple]]:
    g = defaultdict(list)
    for r in rows:
        g[r["groups"][dim]].append(r["opts"][opt])
    if dim in ORDER:
        keys = [k for k in ORDER[dim] if k in g] + [k for k in sorted(g) if k not in ORDER[dim]]
    else:
        keys = sorted(g)
    out = []
    for k in keys:
        xs = g[k]
        n = len(xs)
        stop = sum(1 for x in xs if x["stop"] == "evet")
        act = {v: sum(1 for x in xs if x["act"] == v) for v in ("evet", "belki", "hayır")}
        cred = [x["cred"] for x in xs if isinstance(x["cred"], (int, float))]
        price = [x["price_mid"] for x in xs if x["price_mid"] is not None]
        out.append((k, n, stop, act, round(statistics.mean(cred), 1) if cred else None,
                    int(statistics.median(price)) if price else None))
    return keys, out


def chart(rows_by_group: list[tuple], title: str, path: Path, field: str):
    """100 % stacked horizontal bars (hayır | belki | evet) per group, counts written in ink."""
    W, left, right, top, bar_h, gap = 1100, 230, 40, 110, 46, 18
    H = top + len(rows_by_group) * (bar_h + gap) + 90
    im = Image.new("RGB", (W, H), SURF)
    d = ImageDraw.Draw(im)
    d.text((24, 22), title, font=font(30), fill=INK)
    lx = 24
    for lab, col in (("evet", C_YES), ("belki", C_MAYBE), ("hayır", C_NO)):
        d.rounded_rectangle([lx, 70, lx + 22, 92], 4, fill=col, outline=RING if col == C_MAYBE else None)
        d.text((lx + 30, 68), lab, font=font(22), fill=INK2)
        lx += 130
    span = W - left - right
    for i, (name, n, counts) in enumerate(rows_by_group):
        y = top + i * (bar_h + gap)
        d.text((24, y + 10), f"{name}  (n={n})", font=font(22), fill=INK)
        x = left
        for lab, col in (("evet", C_YES), ("belki", C_MAYBE), ("hayır", C_NO)):
            c = counts.get(lab, 0)
            if not c:
                continue
            w = span * c / n
            d.rounded_rectangle([x, y, x + w - 2, y + bar_h], 4, fill=col,
                                outline=RING if col == C_MAYBE else None)
            txt = str(c)
            tw = d.textlength(txt, font=font(22))
            if w > tw + 10:
                d.text((x + (w - tw) / 2, y + 11), txt, font=font(22), fill=(255, 255, 255) if col != C_MAYBE else INK)
            x += w
    d.text((24, H - 50), f"Sentetik panel (Panel TR) — gerçek pazar verisi değil. Alan: {field}", font=font(20), fill=MUTED)
    im.save(path)


def slug(s: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ ", "cgiosuCGIOSU_")
    return re.sub(r"[^a-z0-9_]", "", s.translate(tr).lower())


def assumption_share(ids: set[str], people: dict) -> float:
    tr = [t for i in ids for t in people[i]["traits"]]
    return sum(1 for t in tr if t.rstrip().endswith("[varsayım]")) / max(1, len(tr))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--title", help="report title (default: run folder name)")
    ap.add_argument("--real-people", default=DEFAULT_REAL_PEOPLE,
                    help="who the 3-5 real people should be (goes into the honesty box)")
    args = ap.parse_args()
    run = Path(args.run)
    pro = is_pro()
    plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
    people = {p["id"]: p for p in load_personas()}
    shown = shown_refs(run, plan)
    (run / "data").mkdir(exist_ok=True)
    issues, rows, raw_by_batch = [], [], defaultdict(list)
    for b in plan["batches"]:
        f = run / b["output"]
        if not f.exists():
            issues.append(f"batch {b['batch']:02d}: cevap dosyası yok ({f.name})")
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append(f"batch {b['batch']:02d}: geçersiz JSON ({e})")
            continue
        got = {d.get("persona_id"): d for d in data}
        for pid in b["personas"]:
            if pid not in got:
                issues.append(f"{pid}: cevap yok")
                continue
            if pid not in people:
                issues.append(f"{pid}: bu sürümün persona dosyalarında yok")
                continue
            d, p = got[pid], people[pid]
            opts_raw = d["secenekler"] if plan["ab"] else {"tek": d}
            opts = {}
            for lab, q in opts_raw.items():
                real = b["ab_key"][lab] if plan["ab"] else "tek"
                fp = q.get("fiyat_beklentisi") or None
                mid = None
                if isinstance(fp, dict):
                    nums = [v for v in (fp.get("min_tl"), fp.get("max_tl")) if isinstance(v, (int, float))]
                    mid = statistics.mean(nums) if nums else None
                refs = q.get("dayanak") or []
                bad = [r for r in refs if not ref_ok(str(r), shown)]
                if len(refs) < 2:
                    issues.append(f"{pid} ({real}): 2'den az dayanak ({refs})")
                if bad:
                    issues.append(f"{pid} ({real}): gösterilmeyen kareye atıf {bad}")
                cred = (q.get("guvenilirlik") or {}).get("puan")
                if isinstance(cred, str) and cred.strip().isdigit():
                    cred = int(cred.strip())
                if not (isinstance(cred, (int, float)) and 1 <= cred <= 5):
                    issues.append(f"{pid} ({real}): güvenilirlik puanı geçersiz ({cred})")
                    cred = None
                opts[real] = {
                    "stop": norm_yn((q.get("ilk_3_saniye") or {}).get("durur_mu")),
                    "stop_why": (q.get("ilk_3_saniye") or {}).get("neden", ""),
                    "what": q.get("ne_anlatiyor", ""), "cred": cred,
                    "act": norm_yn((q.get("aksiyon") or {}).get("karar")),
                    "act_what": (q.get("aksiyon") or {}).get("ne_yapar", ""),
                    "act_why": (q.get("aksiyon") or {}).get("gercekci_neden", ""),
                    "price": fp, "price_mid": mid, "objection": q.get("en_buyuk_itiraz", ""),
                    "fix": q.get("tek_somut_duzeltme", ""), "refs": refs, "cant_see": q.get("goremedigim", ""),
                    "quote": q.get("kendi_sozleriyle", ""),
                }
            # card echo: the persona repeats its own card instead of reacting to the stimulus
            said = " ".join(" ".join(str(v) for v in o.values()) for o in opts.values()).casefold()
            for phrase in re.findall(r"'([^']{12,})'", p.get("voice", "")):
                if phrase.casefold() in said:
                    issues.append(f"{pid}: kart yankısı — voice cümlesi aynen tekrar edildi ('{phrase}')")
            for t in p["traits"]:
                core = TAG.sub("", t).strip().rstrip(".").casefold()
                if len(core) >= 30 and core in said:
                    issues.append(f"{pid}: kart yankısı — kart özelliği aynen tekrar edildi ('{core[:60]}…')")
            pref = None
            if plan["ab"]:
                sec = str((d.get("tercih") or {}).get("secim", "")).strip()
                pref = b["ab_key"].get(sec[:1], "hiçbiri") if sec[:1] in ("1", "2") else "hiçbiri"
            row = {"id": pid, "batch": b["batch"], "groups": group_keys(p), "opts": opts, "pref": pref,
                   "pref_why": (d.get("tercih") or {}).get("neden", "") if plan["ab"] else "",
                   "first_shown": b["ab_key"]["1"] if plan["ab"] else None,
                   "label": f"{pid} {p['name']}, {p['age']}, {p['city']} ({p.get('segment') or p.get('age_band')})"}
            rows.append(row)
            raw_by_batch[b["batch"]].append(
                set().union(*[words(o["objection"] + " " + o["fix"]) for o in opts.values()]))
    if not rows:
        sys.exit("no answers found — check RUN/responses/*.json")

    options = ["A", "B"] if plan["ab"] else ["tek"]
    main_dim = "Yaş" if plan["panel"] == "viewer" else "Segment"
    dims = list(rows[0]["groups"]) if pro else [main_dim]
    price_col = plan["panel"] == "buyer"
    L = [f"# Panel verisi ({plan['panel']}, {len(rows)} kişi, {len(plan['batches'])} grup) — Panel TR {VERSION} {edition()}",
         "", "Script tarafından sayıldı. Sentetik panel: gerçek pazar verisi değildir.", ""]
    js = {"n": len(rows), "panel": plan["panel"], "edition": edition(), "tables": {}, "issues": issues, "totals": {}}
    charts = []
    for opt in options:
        if plan["ab"]:
            L += [f"## Seçenek {opt}", ""]
        n = len(rows)
        stop = sum(1 for r in rows if r["opts"][opt]["stop"] == "evet")
        act = {v: sum(1 for r in rows if r["opts"][opt]["act"] == v) for v in ("evet", "belki", "hayır")}
        cred = [r["opts"][opt]["cred"] for r in rows if r["opts"][opt]["cred"]]
        cmean = round(statistics.mean(cred), 1) if cred else None
        js["totals"][opt] = {"n": n, "stop": stop, "act": act, "cred_mean": cmean}
        L += [f"**Toplam:** ilk 3 sn'de durur {stop}/{n} · aksiyon evet {act['evet']} / belki {act['belki']} / "
              f"hayır {act['hayır']} · güvenilirlik ort. {cmean if cmean is not None else '–'}/5", ""]
        for dim in dims:
            keys, tab = table(rows, dim, opt)
            js["tables"][f"{opt}:{dim}"] = tab
            L += [f"### {dim}", "", "| grup | n | ilk 3 sn durur | aksiyon evet | belki | hayır | güven ort. |"
                  + (" fiyat medyan TL |" if price_col else ""),
                  "|---|---|---|---|---|---|---|" + ("---|" if price_col else "")]
            for k, n_, st, ac, cr, pr in tab:
                L.append(f"| {k} | {n_} | {st}/{n_} | {ac['evet']}/{n_} | {ac['belki']} | {ac['hayır']} | "
                         f"{cr if cr is not None else '–'} |" + (f" {pr if pr else '–'} |" if price_col else ""))
            L.append("")
        suffix = "" if opt == "tek" else f"_{opt}"
        _, tab = table(rows, main_dim, opt)
        chart([(k, n_, ac) for k, n_, _, ac, _, _ in tab], f"Aksiyon ({main_dim}){' — ' + opt if suffix else ''}",
              run / "data" / f"chart_aksiyon{suffix}.png", "aksiyon.karar")
        chart([(k, n_, {"evet": st, "hayır": n_ - st}) for k, n_, st, _, _, _ in tab],
              f"İlk 3 saniyede durur mu ({main_dim}){' — ' + opt if suffix else ''}",
              run / "data" / f"chart_ilk3sn{suffix}.png", "ilk_3_saniye.durur_mu")
        charts += [f"chart_aksiyon{suffix}.png", f"chart_ilk3sn{suffix}.png"]
        L += [f"![aksiyon](chart_aksiyon{suffix}.png)", f"![ilk 3 sn](chart_ilk3sn{suffix}.png)", ""]
        if pro:                                          # segment charts for every other dimension
            for dim in dims:
                if dim == main_dim:
                    continue
                _, tab = table(rows, dim, opt)
                name = f"chart_aksiyon_{slug(dim)}{suffix}.png"
                chart([(k, n_, ac) for k, n_, _, ac, _, _ in tab], f"Aksiyon ({dim}){' — ' + opt if suffix else ''}",
                      run / "data" / name, "aksiyon.karar")
                charts.append(name)
                L.append(f"![aksiyon — {dim}]({name})")
            L.append("")
    if plan["ab"]:
        pref = defaultdict(int)
        by_first = defaultdict(lambda: defaultdict(int))
        for r in rows:
            pref[r["pref"]] += 1
            by_first[r["first_shown"]][r["pref"]] += 1
        L += ["## A/B tercihi", "", f"A: {pref['A']} · B: {pref['B']} · hiçbiri: {pref['hiçbiri']}", "",
              "Sıra etkisi (önce gösterilen seçenek → tercih):"]
        for fs, c in by_first.items():
            L.append(f"- önce {fs} görenler: A {c['A']}, B {c['B']}, hiçbiri {c['hiçbiri']}")
        L.append("")
        js["ab"] = {"pref": dict(pref)}
    # convergence
    within = [jaccard(a, b) for sets in raw_by_batch.values() for a, b in itertools.combinations(sets, 2)]
    across = [jaccard(a, b) for (b1, s1), (b2, s2) in itertools.combinations(raw_by_batch.items(), 2)
              for a in s1 for b in s2]
    w = statistics.mean(within) if within else 0
    x = statistics.mean(across) if across else 0
    conv = "UYARI: grup içi cevaplar belirgin şekilde benzer (tek sesli olma riski)" if (x and w > 1.5 * x and w > 0.12) \
        else "grup içi ve gruplar arası benzerlik yakın (belirgin tek seslilik yok)"
    L += ["## Güvenilirlik kontrolleri", "",
          f"- Kelime örtüşmesi (itiraz+düzeltme, Jaccard): grup içi {w:.2f}, gruplar arası {x:.2f} → {conv}",
          f"- Dayanak / şema / kart yankısı sorunları: {len(issues)}"] + [f"  - {i}" for i in issues] + [""]
    js["convergence"] = {"within": round(w, 3), "across": round(x, 3), "verdict": conv}
    share = assumption_share({r["id"] for r in rows}, people)
    js["assumption_share"] = round(share, 3)
    (run / "data" / "panel_data.md").write_text("\n".join(L), encoding="utf-8")
    (run / "data" / "panel_data.json").write_text(json.dumps({**js, "rows": rows}, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    A = ["# Tüm cevaplar (persona bazında)", ""]
    for r in sorted(rows, key=lambda r: r["id"]):
        A += [f"## {r['label']} — grup {r['batch']:02d}"]
        for opt, o in r["opts"].items():
            tag = f"[{opt}] " if plan["ab"] else ""
            A += [f"- {tag}durur: {o['stop']} — {o['stop_why']}",
                  f"- {tag}ne anlatıyor: {o['what']}",
                  f"- {tag}güven: {o['cred']} · aksiyon: {o['act']} ({o['act_what']}) — {o['act_why']}"]
            if o["price"]:
                A.append(f"- {tag}fiyat: {json.dumps(o['price'], ensure_ascii=False)}")
            A += [f"- {tag}itiraz: {o['objection']}", f"- {tag}düzeltme: {o['fix']}",
                  f"- {tag}dayanak: {', '.join(map(str, o['refs']))}" + (f" · göremediği: {o['cant_see']}" if o['cant_see'] else ""),
                  f"- {tag}söz: “{o['quote']}”"]
        if plan["ab"]:
            A.append(f"- tercih: {r['pref']} — {r['pref_why']}")
        A.append("")
    (run / "data" / "all_answers.md").write_text("\n".join(A), encoding="utf-8")
    quick = quick_report(run, plan, rows, js, issues, share, args.title or run.name, args.real_people, main_dim)
    target = run / ("data/quick_report.md" if pro else "PANEL_REPORT.md")
    target.write_text(quick, encoding="utf-8")
    print(f"{len(rows)} answers, {len(issues)} issues -> {run / 'data'}; charts: {', '.join(charts)}; report: {target}")


def quick_report(run, plan, rows, js, issues, share, title, real_people, main_dim) -> str:
    """Deterministic quick report (Lite's PANEL_REPORT.md). No clustering: objections and fixes verbatim."""
    rel = "data/" if not is_pro() else ""
    t = js["totals"]["tek"] if "tek" in js["totals"] else None
    L = [f"# Panel raporu (hızlı) — {title}", "",
         f"Panel TR {VERSION} · {edition()} · {plan['panel']} paneli · {len(rows)} sentetik kişi · "
         f"{len(plan['batches'])} bağımsız grup", ""]
    L += ["## Bir bakışta", ""]
    for opt, tt in js["totals"].items():
        lab = "" if opt == "tek" else f"Seçenek {opt}: "
        L.append(f"- {lab}İlk 3 saniyede durur: **{tt['stop']}/{tt['n']}** · aksiyon evet **{tt['act']['evet']}** / "
                 f"belki {tt['act']['belki']} / hayır {tt['act']['hayır']} · güvenilirlik ort. "
                 f"**{tt['cred_mean'] if tt['cred_mean'] is not None else '–'}/5**")
    tab = js["tables"].get(f"{'tek' if t else 'A'}:{main_dim}", [])
    if tab:
        best = max(tab, key=lambda r: (r[3]["evet"] + 0.5 * r[3]["belki"]) / r[1])
        worst = min(tab, key=lambda r: (r[3]["evet"] + 0.5 * r[3]["belki"]) / r[1])
        L.append(f"- En sıcak grup: {best[0]} (evet {best[3]['evet']}/{best[1]}, belki {best[3]['belki']}); "
                 f"en soğuk grup: {worst[0]} (evet {worst[3]['evet']}/{worst[1]}, hayır {worst[3]['hayır']}).")
    L.append(f"- Güvenilirlik kontrolleri: {len(issues)} sorun; {js['convergence']['verdict']}.")
    L += ["", "## Grafikler", "", f"![Aksiyon]({rel}chart_aksiyon.png)" if t else f"![Aksiyon A]({rel}chart_aksiyon_A.png)",
          "", f"![İlk 3 saniye]({rel}chart_ilk3sn.png)" if t else f"![İlk 3 saniye A]({rel}chart_ilk3sn_A.png)", ""]
    L += [f"## {main_dim} grubuna göre", "", "| grup | n | ilk 3 sn durur | aksiyon evet | belki | hayır | güven ort. |",
          "|---|---|---|---|---|---|---|"]
    for k, n_, st, ac, cr, _ in tab:
        L.append(f"| {k} | {n_} | {st}/{n_} | {ac['evet']}/{n_} | {ac['belki']} | {ac['hayır']} | {cr if cr is not None else '–'} |")
    opt0 = "tek" if t else "A"
    L += ["", "## İtirazlar (kişinin kendi sözüyle, kümelenmemiş)", ""]
    for r in sorted(rows, key=lambda r: r["id"]):
        o = r["opts"][opt0]
        L.append(f"- **{r['id']}** ({r['groups'].get(main_dim)}, {r['groups'].get('Yer', '')}; aksiyon: {o['act']}): {o['objection']}")
    L += ["", "## Önerilen tek düzeltmeler", ""]
    for r in sorted(rows, key=lambda r: r["id"]):
        L.append(f"- **{r['id']}**: {r['opts'][opt0]['fix']}")
    L += ["", "## Kendi sözleriyle", ""]
    for r in sorted(rows, key=lambda r: r["id"]):
        L.append(f"- **{r['id']}** — “{r['opts'][opt0]['quote']}”")
    L += ["", "## Güvenilirlik kontrolleri", "",
          f"- Kelime örtüşmesi (itiraz+düzeltme): grup içi {js['convergence']['within']:.2f}, "
          f"gruplar arası {js['convergence']['across']:.2f} → {js['convergence']['verdict']}",
          f"- Dayanak / şema / kart yankısı sorunları: {len(issues)}"] + [f"  - {i}" for i in issues]
    L += ["", "> ### ⚠️ Bu gerçek pazar verisi değildir",
          "> Bu sonuçlar bir dil modelinin, kanıta dayalı kişi kartlarıyla canlandırdığı **sentetik** bir paneldir.",
          "> Gerçek insanların ne yapacağını ölçmez; yalnızca gözden kaçmış sorunları yakalamaya yarar.",
          f"> Bu paneldeki kart özelliklerinde [varsayım] (kanıtsız) oranı: %{round(share * 100)}. Kişiler "
          "videoyu izlemedi ve sesi duymadı; kareleri ve yazılı ses açıklamasını gördü.",
          f"> **Karar vermeden önce 3–5 gerçek kişiye gösterin:** {real_people}.",
          "> Sorulacak 3 soru: (1) ilk 3 saniyede durur muydun, (2) ne anlattığını tek cümleyle söyle,",
          "> (3) bunu görünce ne yapardın?", "",
          "_Tüm cevaplar: `data/all_answers.md` · sayılar: `data/panel_data.md`._", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
