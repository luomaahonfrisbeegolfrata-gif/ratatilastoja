#!/usr/bin/env python3
"""Ottaa väylätilastotaulukosta kuvan jokaisesta radasta kansioon kuvat/."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
radat = json.loads((ROOT / "data" / "radat.json").read_text(encoding="utf-8"))
(ROOT / "kuvat").mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1880, "height": 900})
    pg.goto((ROOT / "index.html").as_uri())
    pg.wait_for_timeout(500)
    for r in radat:
        pg.evaluate(f"select('{r['slug']}')")
        pg.wait_for_timeout(150)
        pg.locator(".card-bottom").screenshot(path=str(ROOT / "kuvat" / f"{r['slug']}.png"))
        print("kuva", r["slug"])
    b.close()
