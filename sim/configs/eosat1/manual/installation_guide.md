# SpaceMissionSimulation Installation Guide {#spacemissionsimulation-installation-guide}

**Manual-Scope:** system — training-system documentation, not part of the flight operations manual.

## Quick Start {#quick-start}

Clone the repository, set up a virtual environment, install packages, and run the simulator.

**Linux/macOS:**
```bash
git clone <repo-url> && cd SpaceMissionSimulation && python3.11 -m venv .venv && source .venv/bin/activate && pip install -e packages/smo-common && pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner && bash start.sh
```

**Windows (PowerShell):**
```powershell
git clone <repo-url>; cd SpaceMissionSimulation; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e packages/smo-common; pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner; python -m smo_simulator.server --config configs/eosat1/
```

---

## Prerequisites {#prerequisites}

- **Python 3.11+** (3.11 recommended, 3.12/3.13 compatible)
- **pip** (bundled with Python)
- **Git** (for cloning the repository)
- **~500MB disk space** (for venv and packages)
- **Modern web browser** (Chrome, Firefox, or Edge)
- **No Node.js or npm required** — pure Python project

---

## Platform-Specific Instructions {#platform-specific-instructions}

### Linux (Ubuntu/Debian) {#linux-ubuntudebian}

```bash
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip git
```

### Linux (Fedora/RHEL) {#linux-fedorarhel}

```bash
sudo dnf install python3.11 git
```

### macOS {#macos}

```bash
brew install python@3.11 git
```

### Windows {#windows}

1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
   - During installation, check **"Add Python to PATH"**
2. Install Git from [git-scm.com](https://git-scm.com/)
3. Use PowerShell or Git Bash for commands

---

## Installation Steps (All Platforms) {#installation-steps-all-platforms}

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd SpaceMissionSimulation
   ```

2. **Create a virtual environment:**
   ```bash
   python3.11 -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Linux/macOS:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Git Bash):**
     ```bash
     source .venv/Scripts/activate
     ```

4. **Install SMO packages:**
   ```bash
   pip install -e packages/smo-common
   pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
   ```

5. **Optional: Install Orbit Tools dependencies:**
   ```bash
   pip install sgp4 numpy aiohttp
   ```

---

## Running the Simulator {#running-the-simulator}

### Linux/macOS {#linuxmacos}

```bash
bash start.sh
```

### Windows {#windows-1}

Run each service separately:

```powershell
# Terminal 1: Simulator
python -m smo_simulator.server --config configs/eosat1/

# Terminal 2: Mission Control System
python -m smo_mcs.server --config configs/eosat1/ --port 9090

# Terminal 3: Planner
python -m smo_planner.server --config configs/eosat1/ --port 9091
```

---

## Service Ports {#service-ports}

| Service | Port | URL |
|---------|------|-----|
| Simulator | 8080 | http://localhost:8080 |
| MCS (Mission Control System) | 9090 | http://localhost:9090 |
| Planner | 9091 | http://localhost:9091 |
| Delayed TM Viewer | 8092 | http://localhost:8092 |
| Orbit Tools | 8093 | http://localhost:8093 |

---

## Offline Installation (Cyberrange) {#offline-installation-cyberrange}

For environments without internet access:

1. **Pre-build wheels on a connected machine:**
   ```bash
   pip wheel -w wheels/ -e packages/smo-common -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
   ```

2. **Copy the entire project directory to the target machine**

3. **Run the installation script on the target machine:**
   ```bash
   bash start.sh
   ```
   The `start.sh` script automatically detects the `wheels/` directory and installs from it offline.

---

## Verification {#verification}

1. **Check all services load:**
   - Open each URL listed in the [Service Ports](#service-ports) section
   - Verify that each page loads without errors

2. **Run automated tests:**
   ```bash
   pytest
   ```
   Run from the project root directory.

3. **Verify telemetry flow:**
   - Open the MCS at http://localhost:9090
   - Check that housekeeping (HK) data is updating in real-time
   - Monitor telemetry frames for expected values

---

## Troubleshooting {#troubleshooting}

### Port Conflicts {#port-conflicts}

If a service fails to start due to port already in use:

**Linux/macOS:**
```bash
lsof -i :8080
```

**Windows (PowerShell):**
```powershell
netstat -ano | findstr :8080
```

Kill the conflicting process or change the port when starting the service.

### Chrome HTTPS Redirect {#chrome-https-redirect}

If Chrome automatically redirects to HTTPS:
- Use `http://127.0.0.1:PORT` instead of `localhost:PORT`
- Or disable HTTPS redirect in browser settings

### Python Version Issues {#python-version-issues}

Verify your Python version:
```bash
python3 --version
```
Must be **3.11 or higher**. If needed, specify the full path: `python3.11`.

### Missing Modules {#missing-modules}

Ensure your virtual environment is activated:
```bash
# You should see (.venv) at the start of your prompt
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\Activate.ps1  # Windows
```

Then reinstall packages:
```bash
pip install -e packages/smo-common
pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
```

### Orbit Tools Won't Start {#orbit-tools-wont-start}

Install the optional dependencies manually:
```bash
pip install sgp4 numpy aiohttp
```

---

## Configuration {#configuration}

Mission configuration files are located in `configs/eosat1/`:

- **Mission definition:** `configs/eosat1/mission.yaml`
- **Orbit parameters:** `configs/eosat1/orbit.yaml`
- **Subsystems:** `configs/eosat1/subsystems/*.yaml`
- **Telemetry definitions:** `configs/eosat1/telemetry/`
- **Procedures and scripts:** `configs/eosat1/procedures/`

Modify these files to customize the mission, orbit, and subsystem behavior.

---

## Support {#support}

For issues or questions, please refer to the project documentation or contact the development team.
