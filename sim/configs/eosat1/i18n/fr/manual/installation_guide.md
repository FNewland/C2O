# Guide d'installation de SpaceMissionSimulation

**Manual-Scope:** system — documentation du système de formation, ne fait pas partie du manuel d'opérations de vol.

## Démarrage rapide

Cloner le dépôt, créer un environnement virtuel, installer les paquets et lancer le simulateur.

**Linux/macOS :**
```bash
git clone <repo-url> && cd SpaceMissionSimulation && python3.11 -m venv .venv && source .venv/bin/activate && pip install -e packages/smo-common && pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner && bash start.sh
```

**Windows (PowerShell) :**
```powershell
git clone <repo-url>; cd SpaceMissionSimulation; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e packages/smo-common; pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner; python -m smo_simulator.server --config configs/eosat1/
```

---

## Prérequis

- **Python 3.11 ou supérieur** (3.11 recommandé, compatible 3.12/3.13)
- **pip** (fourni avec Python)
- **Git** (pour cloner le dépôt)
- **~500 Mo d'espace disque** (pour l'environnement virtuel et les paquets)
- **Navigateur web récent** (Chrome, Firefox ou Edge)
- **Ni Node.js ni npm requis** — projet entièrement en Python

---

## Instructions propres à chaque plateforme

### Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip git
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install python3.11 git
```

### macOS

```bash
brew install python@3.11 git
```

### Windows

1. Télécharger Python 3.11 depuis [python.org](https://www.python.org/downloads/)
   - Pendant l'installation, cocher **« Add Python to PATH »**
2. Installer Git depuis [git-scm.com](https://git-scm.com/)
3. Utiliser PowerShell ou Git Bash pour les commandes

---

## Étapes d'installation (toutes plateformes)

1. **Cloner le dépôt :**
   ```bash
   git clone <repo-url>
   cd SpaceMissionSimulation
   ```

2. **Créer un environnement virtuel :**
   ```bash
   python3.11 -m venv .venv
   ```

3. **Activer l'environnement virtuel :**
   - **Linux/macOS :**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (PowerShell) :**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Git Bash) :**
     ```bash
     source .venv/Scripts/activate
     ```

4. **Installer les paquets SMO :**
   ```bash
   pip install -e packages/smo-common
   pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
   ```

5. **Facultatif : installer les dépendances des outils d'orbite (Orbit Tools) :**
   ```bash
   pip install sgp4 numpy aiohttp
   ```

---

## Lancement du simulateur

### Linux/macOS

```bash
bash start.sh
```

### Windows

Lancer chaque service séparément :

```powershell
# Terminal 1: Simulator
python -m smo_simulator.server --config configs/eosat1/

# Terminal 2: Mission Control System
python -m smo_mcs.server --config configs/eosat1/ --port 9090

# Terminal 3: Planner
python -m smo_planner.server --config configs/eosat1/ --port 9091
```

---

## Ports des services

| Service | Port | URL |
|---------|------|-----|
| Simulateur | 8080 | http://localhost:8080 |
| MCS (système de contrôle de mission) | 9090 | http://localhost:9090 |
| Planificateur | 9091 | http://localhost:9091 |
| Visualiseur de TM différée | 8092 | http://localhost:8092 |
| Outils d'orbite (Orbit Tools) | 8093 | http://localhost:8093 |

---

## Installation hors ligne (Cyber Range)

Pour les environnements sans accès à Internet :

1. **Préconstruire les wheels sur une machine connectée :**
   ```bash
   pip wheel -w wheels/ -e packages/smo-common -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
   ```

2. **Copier l'intégralité du répertoire du projet sur la machine cible**

3. **Lancer le script d'installation sur la machine cible :**
   ```bash
   bash start.sh
   ```
   Le script `start.sh` détecte automatiquement le répertoire `wheels/` et effectue l'installation hors ligne à partir de celui-ci.

---

## Vérification

1. **Vérifier que tous les services se chargent :**
   - Ouvrir chaque URL de la section [Ports des services](#service-ports)
   - Vérifier que chaque page se charge sans erreur

2. **Lancer les tests automatisés :**
   ```bash
   pytest
   ```
   À lancer depuis le répertoire racine du projet.

3. **Vérifier le flux de télémesure :**
   - Ouvrir le MCS à l'adresse http://localhost:9090
   - Vérifier que les données de servitude (HK) se mettent à jour en temps réel
   - Surveiller les trames de télémesure pour y retrouver les valeurs attendues

---

## Dépannage

### Conflits de ports

Si un service ne démarre pas parce que le port est déjà utilisé :

**Linux/macOS :**
```bash
lsof -i :8080
```

**Windows (PowerShell) :**
```powershell
netstat -ano | findstr :8080
```

Arrêter le processus en conflit ou changer de port au lancement du service.

### Redirection HTTPS de Chrome

Si Chrome redirige automatiquement vers HTTPS :
- Utiliser `http://127.0.0.1:PORT` au lieu de `localhost:PORT`
- Ou désactiver la redirection HTTPS dans les paramètres du navigateur

### Problèmes de version de Python

Vérifier la version de Python :
```bash
python3 --version
```
Elle doit être **3.11 ou supérieure**. Si nécessaire, indiquer le chemin complet : `python3.11`.

### Modules manquants

S'assurer que l'environnement virtuel est activé :
```bash
# You should see (.venv) at the start of your prompt
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\Activate.ps1  # Windows
```

Puis réinstaller les paquets :
```bash
pip install -e packages/smo-common
pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner
```

### Les outils d'orbite (Orbit Tools) ne démarrent pas

Installer manuellement les dépendances facultatives :
```bash
pip install sgp4 numpy aiohttp
```

---

## Configuration

Les fichiers de configuration de la mission se trouvent dans `configs/eosat1/` :

- **Définition de la mission :** `configs/eosat1/mission.yaml`
- **Paramètres d'orbite :** `configs/eosat1/orbit.yaml`
- **Sous-systèmes :** `configs/eosat1/subsystems/*.yaml`
- **Définitions de télémesure :** `configs/eosat1/telemetry/`
- **Procédures et scripts :** `configs/eosat1/procedures/`

Modifier ces fichiers pour adapter la mission, l'orbite et le comportement des sous-systèmes.

---

## Assistance

Pour tout problème ou toute question, consulter la documentation du projet ou contacter l'équipe de développement.
