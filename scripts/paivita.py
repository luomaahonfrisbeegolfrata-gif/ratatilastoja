#!/usr/bin/env python3
"""Hakee ratojen väylätilastot Disc Golf Metrixin ratasivuilta ja päivittää
data/*.json-tiedostot sekä index.html-sivun upotetun datan.

Ajetaan GitHub Actionsissa maanantaisin (.github/workflows/paivita.yml).
Jos jonkin radan haku tai jäsennys epäonnistuu, radan edellinen data säilyy.

Käyttö:  python3 scripts/paivita.py            (hakee Metrixistä)
         python3 scripts/paivita.py --html DIR (lukee tallennetut sivut DIR/<id>.html)
"""
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (compatible; ratatilastoja/1.0; +https://github.com/luomaahonfrisbeegolfrata-gif/ratatilastoja)"

# Taulukon rivien nimet Metrixissä (englanti, varalla suomi)
ROWS = [
    ("par", ["par"]),
    ("avg", ["avg", "keskiarvo", "ka"]),
    ("rank", ["difficulty", "vaikeus"]),
    ("ace", ["hole in one"]),
    ("eagle", ["eagle -2", "eagle"]),
    ("birdie", ["birdie -1", "birdie"]),
    ("par0", ["par 0"]),
    ("bogey", ["bogey 1", "bogey"]),
    ("double", ["double bogey 2", "double bogey", "tuplabogi"]),
    ("triple", ["triple bogey 3", "triple bogey", "triplabogi"]),
    ("other", ["other >3", "other", "muu"]),
]


def fetch(course_id):
    req = urllib.request.Request(f"https://discgolfmetrix.com/course/{course_id}",
                                 headers={"User-Agent": UA, "Accept-Language": "fi,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def text(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).replace("\xa0", " ").strip()


def tables(src):
    return re.findall(r'<table class="data">(.*?)</table>', src, re.S)


def rows_of(tbl):
    return [[text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S)]


def num(s):
    s = s.strip().replace(",", ".")
    return float(s) if s else 0.0


def parse_stats(src):
    tbl = next((t for t in tables(src) if "Birdie" in t or "birdie" in t), None)
    if not tbl:
        raise ValueError("väylätilastotaulukkoa ei löytynyt")
    rows = rows_of(tbl)
    head = rows[0]
    holes = [h for h in head[1:] if h.strip().isdigit()]
    n = len(holes)
    if n < 3:
        raise ValueError(f"liian vähän väyliä ({n})")
    found = {}
    for r in rows[1:]:
        label = r[0].lower().strip()
        for key, names in ROWS:
            if key in found:
                continue
            if label in names:
                found[key] = [num(c) for c in r[1:1 + n]]
                break
    # Metrix jättää rivin pois, jos sillä ei ole yhtään tulosta (esim. Hole in one)
    missing = [k for k in ("par", "par0") if k not in found]
    if missing:
        raise ValueError("puuttuvat rivit: " + ", ".join(missing))
    for k, _ in ROWS:
        if k not in found and k not in ("avg", "rank"):
            found[k] = [0.0] * n
    out = []
    for i in range(n):
        h = {k: int(found[k][i]) for k, _ in ROWS if k in found and k not in ("avg", "rank")}
        h["n"] = i + 1
        h["scores"] = sum(h[k] for k in ("ace", "eagle", "birdie", "par0", "bogey", "double", "triple", "other"))
        if h["scores"] == 0:
            raise ValueError(f"väylällä {i + 1} ei tuloksia")
        out.append(h)
    return out


def parse_length(src):
    m = re.search(r"(?:Pituus|Length):\s*</span>\s*([\d\s]+)\s*m", src)
    return int(m.group(1).replace(" ", "")) if m else None


def parse_events(src):
    h = re.search(r"<h2>[^<]*10\+[^<]*</h2>", src)
    if not h:
        return []
    m = re.search(r'<table class="data">(.*?)</table>', src[h.end():], re.S)
    if not m:
        return []
    ev = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        a = re.search(r'href="/(\d+)"[^>]*>(.*?)</a>', tds[1], re.S)
        if not a or not re.match(r"\d{4}-\d\d-\d\d", text(tds[0])):
            continue
        pl = re.sub(r"\D", "", text(tds[2]))
        ev.append(dict(pvm=text(tds[0]), nimi=text(a.group(2)).replace("→", "–"),
                       pelaajia=int(pl or 0), url=f"https://discgolfmetrix.com/{a.group(1)}"))
    return ev[:3]


def luokitus(par, pct):
    hi = 15 if par == 3 else 20
    if pct >= hi:
        return dict(label="HELPPO", cls="cell-green")
    if pct >= 5:
        return dict(label="EROTTELEVA", cls="cell-orange")
    return dict(label="VAIKEA", cls="cell-red")


def build(cfg, H, length, events, haettu):
    N = len(H)
    for h in H:
        p = h["par"]
        h["avg"] = (h["ace"] * 1 + h["eagle"] * (p - 2) + h["birdie"] * (p - 1) + h["par0"] * p + h["bogey"] * (p + 1)
                    + h["double"] * (p + 2) + h["triple"] * (p + 3) + h["other"] * (p + 4)) / h["scores"]
    order = sorted(range(N), key=lambda i: H[i]["avg"] - H[i]["par"])
    for r, i in enumerate(order):
        H[i]["rank"] = r + 1  # 1 = helpoin
    plays = [h["scores"] for h in H]
    tot = sum(plays)
    s = lambda k: sum(h[k] for h in H)
    diff = [N + 1 - h["rank"] for h in H]  # 1 = vaikein
    q = lambda d: "cell-red" if d <= N / 4 else "cell-orange" if d <= N / 2 else "cell-yellow" if d <= 3 * N / 4 else "cell-green"
    bpct = [round((h["birdie"] + h["eagle"] + h["ace"]) / h["scores"] * 100, 1) for h in H]
    risk = [(h["double"] + h["triple"] + h["other"]) / h["scores"] for h in H]
    risk_tot = (s("double") + s("triple") + s("other")) / tot

    def row(k):
        return [h[k] for h in H] + [s(k), f"{s(k) / tot * 100:.1f}%"]

    pvm = dt.date.fromisoformat(haettu).strftime("%-d.%-m.%Y")
    return dict(
        id=cfg["id"], slug=cfg["slug"], nimi=cfg["nimi"], paikka=cfg["paikka"], osoite=cfg.get("osoite", ""),
        layout=cfg.get("layout"), vayla_count=N, haettu=haettu,
        lahde=f"https://discgolfmetrix.com/course/{cfg['id']}",
        pituus_total=f"{length}m" if length else "-",
        par=[str(h["par"]) for h in H] + [str(s("par")), "-"],
        avg=[f"{h['avg']:.2f}" for h in H] + [f"{sum(h['avg'] for h in H):.2f}", "-"],
        over_all=[round(h["avg"] - h["par"], 2) for h in H],
        difficulty=[str(d) for d in diff] + ["-", "-"],
        diffCls=[q(d) for d in diff] + ["cell-dark", "cell-dark"],
        luokitus=[dict(**luokitus(h["par"], p), pct=p, basis="kaikki") for h, p in zip(H, bpct)],
        birdie_pct=bpct,
        risk=[f"{r * 100:.1f}%" for r in risk] + [f"{risk_tot * 100:.1f}%", "-"],
        hio=row("ace"), eagle=row("eagle"), birdie=row("birdie"), par0=row("par0"), bogey=row("bogey"),
        dbl=row("double"), tpl=row("triple"), other=row("other"),
        plays_per_hole=plays, kilpailut=events,
        note=(f"Väyläjakaumat: Metrixin ratasivun tilastot kaikista radalle kirjatuista tuloksista "
              f"(n≈{round(tot / N)} tulosta/väylä), haettu {pvm}. Vaikeus = väylän keskitulos suhteessa pariin "
              f"(1 = vaikein). Luokitus = birdie- tai parempi -osuus kaikilla pelaajilla; HELPPO ≥ 15 % "
              f"(par 4–5: 20 %), EROTTELEVA ≥ 5 %, muuten VAIKEA. Keskitulokset laskettu Metrixin "
              f"tulosjakaumasta (Other >3 = +4). Väyläkohtaisia pituuksia Metrix ei julkaise."),
    )


def embed(radat):
    page = ROOT / "index.html"
    src = page.read_text(encoding="utf-8")
    data = json.dumps(radat, ensure_ascii=False)
    new, n = re.subn(r"/\*DATA\*/.*?/\*END\*/", lambda _: f"/*DATA*/{data}/*END*/", src, flags=re.S)
    if n != 1:
        raise SystemExit("index.html: datamerkkejä /*DATA*/ … /*END*/ ei löytynyt")
    page.write_text(new, encoding="utf-8")


def main():
    html_dir = Path(sys.argv[sys.argv.index("--html") + 1]) if "--html" in sys.argv else None
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["radat"]
    haettu = dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).date().isoformat()
    radat, virheet = [], []
    for i, c in enumerate(cfg):
        path = DATA / f"{c['slug']}.json"
        try:
            src = (html_dir / f"{c['id']}.html").read_text(encoding="utf-8") if html_dir else fetch(c["id"])
            H = parse_stats(src)
            old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            events = parse_events(src) or old.get("kilpailut", [])
            length = parse_length(src) or (int(old["pituus_total"][:-1]) if old.get("pituus_total", "-") != "-" else None)
            d = build(c, H, length, events, haettu)
            path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"OK   {c['nimi']}: {len(H)} väylää, {sum(d['plays_per_hole'])} tulosta")
        except Exception as e:  # pidetään vanha data
            virheet.append(c["nimi"])
            print(f"VIRHE {c['nimi']}: {e} – edellinen data säilytetään")
            d = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        if d:
            radat.append(d)
        if not html_dir and i < len(cfg) - 1:
            time.sleep(3)  # ei kuormiteta Metrixiä
    (DATA / "radat.json").write_text(json.dumps(radat, ensure_ascii=False), encoding="utf-8")
    embed(radat)
    if len(virheet) == len(cfg):
        raise SystemExit("Yhdenkään radan haku ei onnistunut.")


if __name__ == "__main__":
    main()
