# SpaceCDF — Installation Guide

> A step-by-step guide for installing SpaceCDF from the public GitHub
> repository.  Written for users with **minimal software experience** — no
> Python, Git, or Node.js background is assumed.  Each step gives the exact
> command to type, what should happen, and what to do if it does not.

**Audience.** University students, instructors, and engineers who want to
run SpaceCDF on their own laptop.  If you only need to use a SpaceCDF
instance someone else is hosting, you do not need this guide — your
instructor will give you a URL.

**Time required.** About 30 minutes the first time, of which 20 minutes is
package downloads.

**Operating systems.** The guide covers **macOS**, **Windows 11**, and
**Ubuntu Linux 22.04+**.  Differences are flagged in coloured callouts.

---

## Quick Install (Automated Scripts)

If you already have Python 3.11+, Node.js 18+, and Git installed, you can
use the automated installation scripts instead of following the manual
steps below.

### macOS / Linux

```bash
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
chmod +x install.sh
./install.sh
```

### Windows 11 (PowerShell)

```powershell
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
.\install.ps1
```

### Docker (backend only)

```bash
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
docker compose up --build -d    # Starts backend + PostgreSQL + Redis
cd frontend && npm install && npm run dev   # Frontend runs locally
```

### Script Options

| Flag | macOS/Linux | Windows | Description |
|---|---|---|---|
| Full install | `./install.sh` | `.\install.ps1` | Backend + frontend (default) |
| Backend only | `./install.sh --backend` | `.\install.ps1 -Backend` | Python packages only |
| Frontend only | `./install.sh --frontend` | `.\install.ps1 -Frontend` | npm install only |
| With AI | `./install.sh --ai` | `.\install.ps1 -AI` | Include optional Claude AI package |
| Check only | `./install.sh --check` | `.\install.ps1 -Check` | Verify prerequisites |
| Docker | `./install.sh --docker` | — | Docker Compose setup |

The scripts check prerequisites, create a virtual environment, install all
packages, and run a smoke test.  If you prefer to understand each step,
continue with the manual installation below.

---

## 1. System Requirements

SpaceCDF runs entirely on your own computer.  It does not need an internet
connection once it is installed (except for downloading updates).

### 1.1 Minimum

| Resource | Minimum | Recommended |
|---|---|---|
| Operating system | macOS 12 · Windows 11 · Ubuntu 22.04 | macOS 14+ · Windows 11 · Ubuntu 24.04 |
| CPU | Any 64-bit dual-core | Quad-core or better |
| RAM | 4 GB | 8 GB or more |
| Disk space (just the tool) | 700 MB | 1.2 GB |
| Disk space (with full ECSS standards library) | 1.5 GB | 2 GB |
| Python | 3.11 or 3.12 | 3.12 |
| Node.js | 18 LTS | 20 LTS or newer |
| Browser | Chrome 120, Firefox 120, Safari 17, Edge 120 | Latest Chrome / Firefox |

### 1.2 Where the disk space goes

These are the actual measured footprints after a clean install:

| Component | Size | Optional? |
|---|---|---|
| Source code (`packages/`, `frontend/`, `docs/`, `scripts/`) | ≈ 200 MB | Required |
| Python virtual environment (backend dependencies) | ≈ 230 MB | Required |
| Frontend `node_modules` (build tools) | ≈ 170 MB | Required |
| ECSS active-standards PDFs | ≈ 145 MB | Optional |
| ECSS handbooks archive | ≈ 370 MB | Optional |

You can safely delete the two ECSS PDF folders after installation if you do
not need the standards offline.

### 1.3 Performance

On a typical laptop the design loop converges in **under 100 milliseconds**
for a small mission and the full document bundle (Word + Excel + Markdown
with embedded figures) renders in **about one second**.  Peak RAM use is
**≈ 150 MB** per active mission.

---

## 2. Install Prerequisites

You need three pieces of supporting software before you can install
SpaceCDF itself.

### 2.1 Install Python 3.11+

#### macOS

1. Open the Terminal application (press ⌘-Space, type *Terminal*, press
   Return).
2. Type the following and press Return:

   ```bash
   python3 --version
   ```

3. If the response is `Python 3.11.x` or higher, you are done with this
   step.  Otherwise, continue.
4. Install **Homebrew** if you do not already have it.  Paste this single
   line into the Terminal and press Return:

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

5. Install Python via Homebrew:

   ```bash
   brew install python@3.12
   ```

#### Windows 11

1. Open your browser and go to <https://www.python.org/downloads/windows/>.
2. Click **Download Python 3.12** (or 3.11 — either works).
3. **Important.** When the installer opens, **tick the box that says
   "Add Python to PATH"** before clicking *Install Now*.
4. After installation, open **PowerShell** (press the Windows key, type
   *powershell*, press Return) and type:

   ```powershell
   python --version
   ```

   You should see `Python 3.12.x`.

#### Ubuntu Linux 22.04+

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

### 2.2 Install Node.js 18+

Node.js builds the SpaceCDF web interface.

#### macOS

```bash
brew install node
node --version
```

#### Windows 11

1. Go to <https://nodejs.org/en/download> and download the **LTS**
   Windows installer.
2. Run the installer and accept all defaults.
3. Open a **new** PowerShell window (any window opened before installation
   will not see the new Node.js) and type:

   ```powershell
   node --version
   ```

   You should see `v20.x.x` or `v22.x.x`.

#### Ubuntu Linux

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
```

### 2.3 Install Git

Git is the program SpaceCDF uses to download itself from GitHub.

#### macOS

Git ships with the developer command-line tools.  Type in Terminal:

```bash
git --version
```

If it asks you to install the developer tools, click **Install** and wait
about five minutes.

#### Windows 11

1. Go to <https://git-scm.com/download/win>.
2. Run the installer and accept all defaults.
3. After installation, open a new PowerShell and type:

   ```powershell
   git --version
   ```

#### Ubuntu Linux

```bash
sudo apt install -y git
git --version
```

> **Stuck?**  At this point you should have three working commands:
> `python3 --version` (3.11 or later), `node --version` (18 or later),
> and `git --version`.  If any one of these still fails after restarting
> the terminal, jump to §7 *Troubleshooting* before continuing.

---

## 3. Download SpaceCDF

Choose a folder where you keep your projects.  In the examples below the
folder is your home directory (`~`); change it to wherever you like.

### macOS / Linux

```bash
cd ~
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
```

### Windows 11

```powershell
cd $HOME
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
```

This downloads about 200 MB of source code and may take a few minutes on a
slow connection.

---

## 4. Install the Backend (Python)

The backend is the engine that runs the 20 design agents and produces
documents.

### 4.1 Create a Python virtual environment

A *virtual environment* keeps SpaceCDF's Python dependencies isolated from
anything else on your computer.

#### macOS / Linux

```bash
cd ~/SpaceCDF
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows 11

```powershell
cd $HOME\SpaceCDF
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell refuses with an "execution policy" error, run this **one
time only** in an *Administrator* PowerShell window:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then close and reopen PowerShell and try the activation again.

**Verify.**  Once activated, the prompt should be prefixed with `(.venv)`.

### 4.2 Install the SpaceCDF Python packages

With the virtual environment active, install the four backend packages.
This downloads about 230 MB of dependencies and takes about 5 minutes.

```bash
pip install --upgrade pip
pip install -e packages/spacecdf-common
pip install -e packages/spacecdf-agents
pip install -e packages/spacecdf-kb
pip install -e packages/spacecdf-server
```

You should see "Successfully installed …" four times.

### 4.3 Smoke-test the backend

```bash
python scripts/run_design.py configs/examples/6u_eo_cubesat.yaml
```

After about a second you should see a `MISSION: EOSAT-1 Multispectral
Imager` banner and a printout of mass, power, cost, and other budgets,
followed by `CONVERGED`.  If you reach this point the backend is working.

---

## 5. Install the Frontend (Web Interface)

In a **second** terminal window, leave the first one running, navigate to
the `frontend` folder, and install the JavaScript build tools.

```bash
cd ~/SpaceCDF/frontend         # or:   cd $HOME\SpaceCDF\frontend
npm install
```

`npm install` downloads about 170 MB and takes 3–6 minutes the first time.
You may see warnings — these are normal as long as the command finishes
with a `added <N> packages` line.

---

## 6. First Launch

You need **two terminals open at once**: one for the backend server and one
for the frontend.

### 6.1 Start the backend (Terminal 1)

```bash
cd ~/SpaceCDF                # or:  cd $HOME\SpaceCDF
source .venv/bin/activate     # macOS / Linux
# .venv\Scripts\Activate.ps1 # Windows
uvicorn spacecdf_server.app:app --reload --port 8000
```

You should see lines ending in `Uvicorn running on http://0.0.0.0:8000`.
Leave this terminal open.

### 6.2 Start the frontend (Terminal 2)

```bash
cd ~/SpaceCDF/frontend       # or:  cd $HOME\SpaceCDF\frontend
npm run dev
```

You should see a line ending in `Local:   http://localhost:5173/`.

### 6.3 Open SpaceCDF in your browser

Open <http://localhost:5173> in Chrome, Firefox, Safari, or Edge.  You
should see the SpaceCDF welcome screen.

> **Success criterion.**  On the welcome screen, click **New study**.  If
> you can name a study and reach Step 1 (*Mission Need*) without an error
> banner, SpaceCDF is fully installed.

### 6.4 Run your first design

1. From the welcome screen click **New study**.  Name it `My First Mission`.
2. In Step 1 (*Mission Need*), pick any sample problem from the suggestions
   list, then click **Continue**.
3. Step 2 (*Concept*): accept the default.
4. Step 3 (*Requirements*): pick "SSO at 500 km" and one payload.
5. Step 4 (*Design*): click the big **Run Design** button.  The 20 agents
   converge in under a second.
6. Open the **Exports** tab and click **Generate SRR**.  After a second a
   `.docx`, `.xlsx`, and `.md` bundle is offered as a download.

If you reach this point, congratulations — you are running a complete
concurrent design facility on your own machine.

---

## 7. Troubleshooting

### "Command not found: python3" (macOS / Linux)

You skipped §2.1.  Run that section again, then close and reopen the
terminal so it picks up the new `PATH`.

### "Activate.ps1 cannot be loaded because running scripts is disabled" (Windows)

You need to allow PowerShell scripts.  In an Administrator PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then reopen PowerShell and try the activation again.

### `pip install` errors mentioning `wheel` or `setuptools`

Update pip first, then retry:

```bash
pip install --upgrade pip setuptools wheel
```

### `npm install` errors

If the install fails partway through, delete the partial install and try
again:

```bash
rm -rf node_modules package-lock.json   # macOS / Linux
# Remove-Item -Recurse -Force node_modules,package-lock.json   # Windows
npm install
```

### "Port 8000 already in use" or "Port 5173 already in use"

Another program is using that port.  Either close it or pick a different
port:

```bash
uvicorn spacecdf_server.app:app --reload --port 8100
```

If you change the backend port, also update `frontend/vite.config.ts` so
the frontend knows where to find it.

### The browser shows "ERR_CONNECTION_REFUSED"

Either the backend (port 8000) or the frontend (port 5173) is not running.
Switch to each terminal and confirm both are still alive.

### Designs do not converge

Look at the warnings panel in Step 4.  A common cause is asking for a
payload that draws more power than the spacecraft class can carry — pick
a smaller payload or a larger spacecraft class.

### Document export fails

Make sure your virtual environment is the one in which you installed the
packages.  The prompt should say `(.venv)`.  If not, re-activate it.

---

## 8. Optional Add-ons

### 8.1 Run with Docker Compose

Docker Compose starts the backend, PostgreSQL, and Redis in containers.
You still run the frontend locally (it needs Node.js for hot-reload).

```bash
cd ~/SpaceCDF
docker compose up --build -d     # Backend + Postgres + Redis
cd frontend && npm run dev        # Frontend (local)
```

Open <http://localhost:5173>.  The backend API is at `http://localhost:8000`.

To stop:

```bash
docker compose down               # Stop containers
docker compose down -v            # Stop and delete database volume
```

### 8.2 Run with PostgreSQL instead of SQLite

By default SpaceCDF uses SQLite (persists to `spacecdf.db`).  For
multi-user production deployments, switch to PostgreSQL 16+:

```bash
export DATABASE_URL=postgresql+asyncpg://spacecdf:spacecdf_dev@localhost:5432/spacecdf
```

Or add that line to your `.env` file.  The Docker Compose setup uses
PostgreSQL automatically.

### 8.3 Enable AI-Assisted Design (Optional)

SpaceCDF can optionally use Claude AI for design advice, requirements
decomposition, trade analysis, and more.

```bash
source .venv/bin/activate
pip install -e packages/spacecdf-ai
```

Then set your API key in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

AI features are controlled per-capability in `configs/genai.yaml`.  If the
package is not installed or the key is missing, SpaceCDF runs in fully
manual mode with no errors.

### 8.4 Remote access via Tailscale

If you want to share your local instance with colleagues, install
Tailscale (<https://tailscale.com/download>) on both machines and use
your tailnet IP.  Detailed steps are in `docs/REMOTE_ACCESS.md`.

### 8.5 Keep the ECSS standards library offline

The two ECSS folders (`Active ECSS Standards_PDF-files …` and
`ECSS-Handbooks_…`) take about 500 MB.  If you want them, keep them in
the repository root.  If not, you can move them to an external drive or
delete them — the tool falls back to citing the standards by reference.

---

## 9. Updating SpaceCDF

To pull the latest version from GitHub:

```bash
cd ~/SpaceCDF               # or:  cd $HOME\SpaceCDF
git pull
source .venv/bin/activate    # macOS / Linux
pip install -e packages/spacecdf-common -e packages/spacecdf-agents -e packages/spacecdf-kb -e packages/spacecdf-server
cd frontend
npm install
```

Then restart the two terminals from §6.

---

## 10. Uninstalling

SpaceCDF lives entirely inside its own folder and the Python virtual
environment.  To remove it completely:

```bash
# macOS / Linux
rm -rf ~/SpaceCDF
```

```powershell
# Windows
Remove-Item -Recurse -Force $HOME\SpaceCDF
```

The Python, Node.js, and Git installations are independent and remain on
your machine for other software to use.

---

## Acknowledgement — Generative AI (AIG)

This installation guide was produced with the assistance of generative
AI as part of the SpaceCDF Concurrent Design Facility workflow. The
SpaceCDF backend (Python · matplotlib · python-docx · WeasyPrint) was
used to draft, render and verify the steps that follow; the system
requirement figures (RAM, disk, convergence time) were measured by
running the tool. Editorial framing and final wording remain owned by
the SpaceCDF teaching team.

*Attribution follows the AIG (Assisted by Generative AI) framework —
Peters (2023), Logos IA-EN, CC BY-NC-SA 4.0 —
[https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/](https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/)*

Any course deliverable that incorporates content from this guide — or
from any document exported by SpaceCDF — must carry the AIG badge and
a short note describing how generative AI was used.

---

*SpaceCDF · uOttawa · School of Engineering Design and Teaching Innovation (SEDTI)*
