# Järviseudun ratatilastot

Väylätilastot yhdeksälle Järviseudun ja lähialueen frisbeegolfradalle Luoma-ahon Frisbeegolfradan tilastosivun tyylillä.

Data haetaan Disc Golf Metrixin ratasivuilta automaattisesti joka maanantai (GitHub Actions, `.github/workflows/paivita.yml`).

Sivu: `index.html` (radan voi avata suoraan osoitteen perään lisättävällä tunnuksella, esim. `#vimpelin-frisbeegolfrata`).

| Rata | Paikkakunta | Väyliä | Par | Keskitulos | Metrix | Kuva | Data |
|---|---|---|---|---|---|---|---|
| Alajärvi DiscGolfPark | Alajärvi | 18 | 56 | 61.10 | [7406](https://discgolfmetrix.com/course/7406) | [kuva](kuvat/alajarvi-discgolfpark.png) | [json](data/alajarvi-discgolfpark.json) |
| Valkealampi DiscGolfPark | Alajärvi (Lehtimäki) | 18 | 57 | 66.04 | [35822](https://discgolfmetrix.com/course/35822) | [kuva](kuvat/valkealampi-discgolfpark.png) | [json](data/valkealampi-discgolfpark.json) |
| Vimpelin frisbeegolfrata – Vatpakka | Vimpeli | 21 | 66 | 68.51 | [25370](https://discgolfmetrix.com/course/25370) | [kuva](kuvat/vimpelin-frisbeegolfrata.png) | [json](data/vimpelin-frisbeegolfrata.json) |
| Välijoki DiscGolfPark | Lappajärvi | 20 | 67 | 74.81 | [35723](https://discgolfmetrix.com/course/35723) | [kuva](kuvat/valijoki-discgolfpark.png) | [json](data/valijoki-discgolfpark.json) |
| Lappajärven urheilupuisto | Lappajärvi | 9 | 27 | 26.07 | [20240](https://discgolfmetrix.com/course/20240) | [kuva](kuvat/lappajarven-urheilupuisto.png) | [json](data/lappajarven-urheilupuisto.json) |
| Patanan frisbeegolfrata | Veteli | 18 | 56 | 58.78 | [18840](https://discgolfmetrix.com/course/18840) | [kuva](kuvat/patanan-frisbeegolfrata.png) | [json](data/patanan-frisbeegolfrata.json) |
| Paavonkallio DiscGolfCenter | Perho | 19 | 60 | 64.12 | [35170](https://discgolfmetrix.com/course/35170) | [kuva](kuvat/paavonkallio-discgolfcenter.png) | [json](data/paavonkallio-discgolfcenter.json) |
| Evijärven Frisbeegolf – Nissinkangas | Evijärvi | 18 | 55 | 55.48 | [15204](https://discgolfmetrix.com/course/15204) | [kuva](kuvat/evijarven-frisbeegolf.png) | [json](data/evijarven-frisbeegolf.json) |
| Lapua Frisbeegolf – Simpsiö | Lapua | 18 | 60 | 71.51 | [6393](https://discgolfmetrix.com/course/6393) | [kuva](kuvat/lapua-frisbeegolf.png) | [json](data/lapua-frisbeegolf.json) |

## Sisältö

- `index.html` – väylätilastosivu, kaikki radat valittavissa
- `kuvat/` – väylätilastotaulukko kuvana jokaisesta radasta
- `data/` – radan tiedot JSON-muodossa (`radat.json` sisältää kaikki)

Vaikeus = väylän keskitulos suhteessa pariin (1 = vaikein). Luokitus = birdie tai parempi -osuus kaikista tuloksista: HELPPO ≥ 15 % (par 4–5: 20 %), EROTTELEVA ≥ 5 %, muuten VAIKEA. Metrix ei julkaise väyläkohtaisia pituuksia.

## Päivitys

- Ajastus: maanantaisin klo 6–7 Suomen aikaa. Ajon voi käynnistää myös käsin: **Actions → Päivitä ratatilastot → Run workflow**.
- `scripts/paivita.py` hakee jokaisen radan Metrix-sivun, laskee tilastot ja päivittää `data/`-tiedostot sekä `index.html`:n datan. Jos jonkin radan haku epäonnistuu, sen edellinen data säilyy.
- `scripts/kuvat.py` piirtää kuvat uudelleen kansioon `kuvat/`.
- Uuden radan saa mukaan lisäämällä sen `config.json`-tiedostoon (Metrix-ID, tunniste, nimi ja paikkakunta).
