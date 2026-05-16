# ============================================================================
# SpaceCDF — Automated Installation Script (Windows PowerShell)
# ============================================================================
#
# Usage (run from SpaceCDF root directory):
#   .\install.ps1              # Full install (backend + frontend)
#   .\install.ps1 -Backend     # Backend only
#   .\install.ps1 -Frontend    # Frontend only
#   .\install.ps1 -Check       # Check prerequisites only
#   .\install.ps1 -AI          # Include optional AI package
#
# If PowerShell refuses to run this script:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#
# Requirements: Python 3.11+, Node.js 18+, Git
# ============================================================================

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$AI,
    [switch]$Check,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-Info($msg)    { Write-Host "[INFO]  $msg" -ForegroundColor Blue }
function Write-Ok($msg)      { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn($msg)    { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg)    { Write-Host "[FAIL]  $msg" -ForegroundColor Red }
function Write-Header($msg)  { Write-Host "`n=== $msg ===`n" -ForegroundColor White }

# ── Resolve flags ───────────────────────────────────────────────────────────
if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Backend] [-Frontend] [-AI] [-Check] [-Help]"
    exit 0
}

$InstallBackend  = -not $Frontend
$InstallFrontend = -not $Backend
if ($Backend -and $Frontend) {
    $InstallBackend  = $true
    $InstallFrontend = $true
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ── Prerequisite checks ────────────────────────────────────────────────────
function Test-Prerequisites {
    Write-Header "Checking prerequisites"
    $ok = $true

    # Python
    try {
        $pyVersion = & python --version 2>&1
        if ($pyVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 11) {
                Write-Ok "Python $($Matches[0])"
            } else {
                Write-Fail "Python $($Matches[0]) — need 3.11 or later"
                Write-Host "       Download from: https://www.python.org/downloads/"
                $ok = $false
            }
        }
    } catch {
        Write-Fail "Python not found"
        Write-Host "       Download from: https://www.python.org/downloads/"
        Write-Host "       IMPORTANT: Tick 'Add Python to PATH' during install"
        $ok = $false
    }

    # Node.js
    try {
        $nodeVersion = (& node --version 2>&1) -replace '^v', ''
        $nodeMajor = [int]($nodeVersion -split '\.')[0]
        if ($nodeMajor -ge 18) {
            Write-Ok "Node.js $nodeVersion"
        } else {
            Write-Fail "Node.js $nodeVersion — need 18 or later"
            $ok = $false
        }
    } catch {
        Write-Fail "Node.js not found"
        Write-Host "       Download from: https://nodejs.org/en/download"
        $ok = $false
    }

    # Git
    try {
        $gitVersion = & git --version 2>&1
        Write-Ok $gitVersion
    } catch {
        Write-Fail "Git not found"
        Write-Host "       Download from: https://git-scm.com/download/win"
        $ok = $false
    }

    Write-Host ""
    if ($ok) {
        Write-Ok "All prerequisites satisfied"
    } else {
        Write-Fail "Missing prerequisites — install them and re-run this script"
        exit 1
    }
}

# ── Backend installation ────────────────────────────────────────────────────
function Install-Backend {
    Write-Header "Installing Python backend"
    Set-Location $ScriptDir

    # Create venv
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating Python virtual environment..."
        & python -m venv .venv
        Write-Ok "Virtual environment created"
    } else {
        Write-Info "Virtual environment already exists"
    }

    # Activate
    & .\.venv\Scripts\Activate.ps1
    Write-Info "Virtual environment activated"

    # Upgrade pip
    Write-Info "Upgrading pip..."
    & pip install --upgrade pip setuptools wheel --quiet

    # Install packages
    Write-Info "Installing spacecdf-common..."
    & pip install -e packages/spacecdf-common --quiet
    Write-Ok "spacecdf-common installed"

    Write-Info "Installing spacecdf-kb..."
    & pip install -e packages/spacecdf-kb --quiet
    Write-Ok "spacecdf-kb installed"

    Write-Info "Installing spacecdf-agents..."
    & pip install -e packages/spacecdf-agents --quiet
    Write-Ok "spacecdf-agents installed"

    Write-Info "Installing spacecdf-server..."
    & pip install -e packages/spacecdf-server --quiet
    Write-Ok "spacecdf-server installed"

    if ($AI) {
        Write-Info "Installing spacecdf-ai (optional)..."
        & pip install -e packages/spacecdf-ai --quiet
        Write-Ok "spacecdf-ai installed"
        Write-Warn "Set ANTHROPIC_API_KEY in .env to enable AI features"
    }

    # Create .env
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item .env.example .env
        Write-Info "Created .env from .env.example"
    }

    # Smoke test
    Write-Header "Running backend smoke test"
    try {
        & python -c "from spacecdf_common.models import Mission; print('OK')" 2>$null
        Write-Ok "spacecdf-common imports OK"
    } catch {
        Write-Warn "spacecdf-common import failed"
    }

    try {
        & python -c "from spacecdf_server.app import app; print('OK')" 2>$null
        Write-Ok "spacecdf-server imports OK"
    } catch {
        Write-Warn "spacecdf-server import failed"
    }
}

# ── Frontend installation ───────────────────────────────────────────────────
function Install-Frontend {
    Write-Header "Installing frontend (React + Vite)"
    Set-Location "$ScriptDir\frontend"

    Write-Info "Installing npm dependencies..."
    & npm install --loglevel warn
    Write-Ok "Frontend dependencies installed"

    Set-Location $ScriptDir
}

# ── Summary ─────────────────────────────────────────────────────────────────
function Show-Summary {
    Write-Header "Installation complete"

    Write-Host "SpaceCDF is ready to use." -ForegroundColor Green
    Write-Host ""
    Write-Host "To start SpaceCDF:"
    Write-Host ""
    Write-Host "  Terminal 1 (backend):"
    Write-Host "    .\.venv\Scripts\Activate.ps1"
    Write-Host "    uvicorn spacecdf_server.app:app --reload --port 8000"
    Write-Host ""
    Write-Host "  Terminal 2 (frontend):"
    Write-Host "    cd frontend; npm run dev"
    Write-Host ""
    Write-Host "  Then open: http://localhost:5173"
    Write-Host ""
    Write-Host "  API docs:    http://localhost:8000/docs"
    Write-Host ""
}

# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "  +=========================================================+" -ForegroundColor Cyan
Write-Host "  |              SpaceCDF - Installation Script              |" -ForegroundColor Cyan
Write-Host "  |       AI-Powered Concurrent Design Facility              |" -ForegroundColor Cyan
Write-Host "  +=========================================================+" -ForegroundColor Cyan
Write-Host ""

Test-Prerequisites

if ($Check) { exit 0 }

if ($InstallBackend)  { Install-Backend }
if ($InstallFrontend) { Install-Frontend }

Show-Summary
