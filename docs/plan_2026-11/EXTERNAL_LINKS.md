# External links — open references used by the workbooks (ops)

Background knowledge the C2O tools do not carry is linked from the logbook's
Workbook tab ("Where to find this") to a public, open-access page. The links
are kept in `sim/configs/eosat1/worksheets/worksheet_where.yaml` (`links:`);
this list mirrors them with the reason and the date each URL was checked.
`sim/tests/test_content/test_worksheet_where.py` fails if a link in the map is
missing here.

Rules:

- **https only.** The logbook server (`smo_common/logbook/worksheets.py`
  `localise_where`) drops any other scheme, and the browser (`where.js`)
  checks again. The documentation viewer (`tools/doc_viewer.py`
  `link_target`) turns only relative links and https URLs into links; any
  other scheme (`javascript:`, `data:`, `http:`, `file:`, `//host`) keeps its
  text and loses the link.
- **New window.** Every external link opens with `target="_blank"
  rel="noopener noreferrer"` and is marked ↗; links to other C2O tools open
  (or focus) that tool's own window.
- **Preference:** ESA / NASA / ECSS / CCSDS / CelesTrak first; Wikipedia only
  where nothing better is open. French pages when they exist (`url_fr`).

| Key | URL | Title | Why | Where used | Checked |
|---|---|---|---|---|---|
| `ecss-pus` | https://ecss.nl/wp-content/uploads/2016/06/ECSS-E-ST-70-41C15April2016.pdf | ECSS-E-ST-70-41C, Telemetry and telecommand packet utilization (PUS-C), 15 April 2016 | The PUS services the cards command (S3 HK, S5 events, S9 time, S12 monitoring, S19 event-action, S20 parameters) — the standard behind every `TC(x,y)` | WB-5.6-C008 step 1 (S12 monitoring) | 2026-11-04 (fetched: PDF, title confirmed) |
| `ecss-ops` | https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/ | ECSS-E-ST-70-11C, Space segment operability (31 July 2008; Rev.1 2025 also listed) | Operability, procedures, handover and anomaly practice — the frame of the observer and handover sheets and of WB-5.7-FR §4 | WB-5.4-N012 (voice-loop tone), WB-5.5-OBS (procedure adherence) | 2026-11-04 (fetched; page links the PDF, notes Rev.1 supersedes) |
| `celestrak-tle` | https://celestrak.org/columns/v04n03/ | CelesTrak, "Frequently Asked Questions: Two-Line Element Set Format" | What each TLE field means, for the flight-dynamics workshop and the orbit determination row | WB-5.4-FD Ex. 1, WB-5.5-L003 step 4 | 2026-11-04 (fetched; line-by-line field tables) |
| `esa-orbits` | https://www.esa.int/ESA_Multimedia/Images/2024/12/Where_and_why_we_whizz_around_Earth | ESA, "Where and why we whizz around Earth" | Orbit types, sun-synchronous orbits for Earth observation (fixed geometry to the Sun) | WB-5.0 orbit altitude | 2026-11-04 (fetched; explains sun-synchronous orbits) |
| `wiki-sso` | https://en.wikipedia.org/wiki/Sun-synchronous_orbit | Sun-synchronous orbit (Wikipedia) | Why the node precesses with the Sun and what the local time of the node means (LTAN) | WB-5.0 LTAN | 2026-11-04 (fetched; title confirmed) |
| `wiki-elements` | https://en.wikipedia.org/wiki/Orbital_elements | Orbital elements (Wikipedia) | a, e, i, RAAN, argument of perigee, anomaly — what Orbit tools shows under Orbit at epoch | WB-5.4-FD Ex. 2 formula, WB-5.5-L003 step 4 | 2026-11-04 (fetched) |
| `wiki-ebn0` | https://en.wikipedia.org/wiki/Eb/N0 | Eb/N0 (Wikipedia) | Energy per bit to noise density and its link to the bit error rate the TT&C page shows | WB-5.1.4 BER reading | 2026-11-04 (fetched) |
| `wiki-linkbudget` | https://en.wikipedia.org/wiki/Link_budget | Link budget (Wikipedia) | Gains and losses from transmitter to receiver: the frame of the COM-006 link budget report | WB-5.6-C006 step 8 | 2026-11-04 (fetched) |
| `wiki-dop` | https://en.wikipedia.org/wiki/Dilution_of_precision | Dilution of precision (Wikipedia) | What the GPS PDOP the AOC page shows means | WB-5.5-L003 step 1 (PDOP) | 2026-11-04 (fetched) |
| `nasa-soa` | https://www.nasa.gov/smallsat-institute/sst-soa | NASA, State-of-the-Art of Small Spacecraft Technology | Small-satellite bus, power, GNC, communications and operations — the background of the orientation check | WB-5.0 platform | 2026-11-04 (fetched; chapter list confirmed) |

French versions: none of the pages above has a French version that could be
fetched from this environment (fr.wikipedia.org is not reachable from the
build sandbox, and the ESA, ECSS, CCSDS, CelesTrak and NASA pages are English
only). The French labels say "(en anglais)". When a French page is confirmed,
add it as `url_fr` in `worksheet_where.yaml` and here; the logbook then serves
it to French users and falls back to the English URL if it is not https.

Not used, and why:

- CCSDS 301.0-B-4 (time code formats, CUC) and CCSDS 131.0-B (TM coding): the
  official public.ccsds.org PDFs could not be fetched to confirm their URLs;
  the manual (12 *Time and clocks* §3, 05 *TTC* §2.4) covers what the sheets
  ask. Add them once the URLs are confirmed.
