# C2O — from Concept to Orbit · du Concept à l'Orbite

C2O is an open teaching platform for space-mission engineering. Students **design** a mission in a concurrent design facility, then **fly** it from a mission control centre against a spacecraft simulator. Everything is available in English and French.

*C2O est une plateforme pédagogique ouverte d'ingénierie des missions spatiales. Les équipes **conçoivent** une mission dans une installation de conception simultanée, puis la **pilotent** depuis un centre de contrôle face à un simulateur de satellite. Tout est disponible en anglais et en français.*

**What is in each folder, with diagrams:** [docs/REPO_MAP.md](docs/REPO_MAP.md) · *[en français](docs/REPO_MAP_fr.md)*

| Folder | What it is |
|---|---|
| [`design/`](design/) | **Design.** SpaceCDF concurrent design facility: requirements, budgets, design agents, trade studies, ECSS documents, export to the simulator. FastAPI + React. Also the course books, the open textbook *Concurrent Spacecraft Design* and the Moodle course builder. |
| [`sim/`](sim/) | **Simulate and operate.** EOSAT-1 spacecraft simulator, mission control system (MCS), planner, RF/radio bridge, space-link agent and ground-station gateway (`smo-link`), operations manual and procedures, the VR interface kit. Python. |
| [`video/`](video/) | **Course videos.** Storyboards and the pipeline that records the real screens, narrates them in English and French and makes the H5P interactive versions. |
| [`shared/`](shared/) | **One look.** Design tokens and the pictorial displays used by both the consoles and SpaceCDF. |
| [`deploy/`](deploy/) | **c2o.live** on Google Cloud: set-up, the `c2o` command, start and stop. |
| [`docs/`](docs/) | Cross-project plans, the UI brief, testing notes and the folder map. |

## Quick start

**Simulator and mission control**, all on one machine:
```bash
cd sim && ./start.sh                    # MCS http://localhost:9090, planner :9091, simulator :8080
```
To split the two halves (simulator on a laptop, consoles on a server) and for the radio, see [`sim/packages/smo-link/README.md`](sim/packages/smo-link/README.md).

**SpaceCDF:**
```bash
cd design && ./install.sh               # then backend on :8000, frontend on :5173 (see design/README.md)
```

**Course books and the open textbook:** see [`design/docs/i18n/BUILD_FR.md`](design/docs/i18n/BUILD_FR.md).

## Keeping English and French in sync
Each project has `python3 -m tools.i18n status|check` (run inside `sim/` or `design/`). Author rulings on content questions are in `sim/docs/i18n/RULINGS.md`.

## Licences
See [LICENSE.md](LICENSE.md): the simulator is GPL-3.0, SpaceCDF is MIT, and the books are CC BY 4.0.

## History
This repository joins two earlier projects, both with their full history: SpaceMissionSimulator (now `sim/`) and SpaceCDF (now `design/`).
