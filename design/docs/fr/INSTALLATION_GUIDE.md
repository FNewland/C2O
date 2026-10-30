# SpaceCDF — Guide d'installation

> Guide pas à pas pour installer SpaceCDF à partir du dépôt GitHub
> public. Il s'adresse aux personnes ayant **très peu d'expérience
> logicielle** : aucune connaissance de Python, de Git ou de Node.js n'est
> supposée. Chaque étape indique la commande exacte à saisir, ce qui doit
> se produire et que faire si ce n'est pas le cas.

**Public visé.** Étudiantes et étudiants, enseignants et ingénieurs qui
souhaitent exécuter SpaceCDF sur leur propre ordinateur portable. Si vous
devez seulement utiliser une instance de SpaceCDF hébergée par quelqu'un
d'autre, ce guide ne vous concerne pas : votre enseignant vous fournira
une URL.

**Durée.** Environ 30 minutes la première fois, dont 20 minutes de
téléchargement de paquets.

**Systèmes d'exploitation.** Le guide couvre **macOS**, **Windows 11** et
**Ubuntu Linux 22.04+**. Les différences sont signalées dans des encadrés
de couleur.

---

## Installation rapide (scripts automatisés)

Si Python 3.11+, Node.js 18+ et Git sont déjà installés, vous pouvez
utiliser les scripts d'installation automatisée au lieu de suivre les
étapes manuelles ci-dessous.

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

### Docker (backend uniquement)

```bash
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF
docker compose up --build -d    # Starts backend + PostgreSQL + Redis
cd frontend && npm install && npm run dev   # Frontend runs locally
```

### Options des scripts

| Option | macOS/Linux | Windows | Description |
|---|---|---|---|
| Installation complète | `./install.sh` | `.\install.ps1` | Backend + frontend (par défaut) |
| Backend uniquement | `./install.sh --backend` | `.\install.ps1 -Backend` | Paquets Python uniquement |
| Frontend uniquement | `./install.sh --frontend` | `.\install.ps1 -Frontend` | npm install uniquement |
| Avec IA | `./install.sh --ai` | `.\install.ps1 -AI` | Inclut le paquet facultatif Claude AI |
| Vérification seule | `./install.sh --check` | `.\install.ps1 -Check` | Vérifie les prérequis |
| Docker | `./install.sh --docker` | — | Configuration Docker Compose |

Les scripts vérifient les prérequis, créent un environnement virtuel,
installent tous les paquets et exécutent un test de fumée. Si vous
préférez comprendre chaque étape, poursuivez avec l'installation manuelle
ci-dessous.

---

## 1. Configuration requise

SpaceCDF s'exécute entièrement sur votre propre ordinateur. Une fois
installé, il ne nécessite pas de connexion à Internet (sauf pour
télécharger les mises à jour).

### 1.1 Minimum

| Ressource | Minimum | Recommandé |
|---|---|---|
| Système d'exploitation | macOS 12 · Windows 11 · Ubuntu 22.04 | macOS 14+ · Windows 11 · Ubuntu 24.04 |
| Processeur | N'importe quel double cœur 64 bits | Quatre cœurs ou mieux |
| Mémoire vive | 4 Go | 8 Go ou plus |
| Espace disque (outil seul) | 700 Mo | 1,2 Go |
| Espace disque (avec la bibliothèque complète des normes ECSS) | 1,5 Go | 2 Go |
| Python | 3.11 ou 3.12 | 3.12 |
| Node.js | 18 LTS | 20 LTS ou plus récent |
| Navigateur | Chrome 120, Firefox 120, Safari 17, Edge 120 | Dernière version de Chrome / Firefox |

### 1.2 Répartition de l'espace disque

Voici les empreintes réellement mesurées après une installation propre :

| Composant | Taille | Facultatif ? |
|---|---|---|
| Code source (`packages/`, `frontend/`, `docs/`, `scripts/`) | ≈ 200 Mo | Requis |
| Environnement virtuel Python (dépendances du backend) | ≈ 230 Mo | Requis |
| `node_modules` du frontend (outils de construction) | ≈ 170 Mo | Requis |
| PDF des normes ECSS en vigueur | ≈ 145 Mo | Facultatif |
| Archive des manuels ECSS | ≈ 370 Mo | Facultatif |

Vous pouvez supprimer sans risque les deux dossiers de PDF ECSS après
l'installation si vous n'avez pas besoin des normes hors ligne.

### 1.3 Performances

Sur un ordinateur portable courant, la boucle de conception converge en
**moins de 100 millisecondes** pour une petite mission, et le dossier
documentaire complet (Word + Excel + Markdown avec figures intégrées) est
produit en **une seconde environ**. La consommation maximale de mémoire
vive est de **≈ 150 Mo** par mission active.

---

## 2. Installation des prérequis

Trois logiciels d'appui sont nécessaires avant de pouvoir installer
SpaceCDF lui-même.

### 2.1 Installer Python 3.11+

#### macOS

1. Ouvrez l'application Terminal (appuyez sur ⌘-Espace, tapez *Terminal*,
   appuyez sur Entrée).
2. Tapez ce qui suit et appuyez sur Entrée :

   ```bash
   python3 --version
   ```

3. Si la réponse est `Python 3.11.x` ou supérieure, cette étape est
   terminée. Sinon, continuez.
4. Installez **Homebrew** si ce n'est pas déjà fait. Collez cette ligne
   unique dans le Terminal et appuyez sur Entrée :

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

5. Installez Python avec Homebrew :

   ```bash
   brew install python@3.12
   ```

#### Windows 11

1. Ouvrez votre navigateur et allez sur <https://www.python.org/downloads/windows/>.
2. Cliquez sur **Download Python 3.12** (ou 3.11 — les deux conviennent).
3. **Important.** À l'ouverture du programme d'installation, **cochez la
   case « Add Python to PATH »** avant de cliquer sur *Install Now*.
4. Une fois l'installation terminée, ouvrez **PowerShell** (appuyez sur la
   touche Windows, tapez *powershell*, appuyez sur Entrée) et tapez :

   ```powershell
   python --version
   ```

   Vous devez voir `Python 3.12.x`.

#### Ubuntu Linux 22.04+

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

### 2.2 Installer Node.js 18+

Node.js sert à construire l'interface web de SpaceCDF.

#### macOS

```bash
brew install node
node --version
```

#### Windows 11

1. Allez sur <https://nodejs.org/en/download> et téléchargez le programme
   d'installation **LTS** pour Windows.
2. Lancez le programme d'installation et acceptez toutes les valeurs par
   défaut.
3. Ouvrez une **nouvelle** fenêtre PowerShell (une fenêtre ouverte avant
   l'installation ne verra pas le nouveau Node.js) et tapez :

   ```powershell
   node --version
   ```

   Vous devez voir `v20.x.x` ou `v22.x.x`.

#### Ubuntu Linux

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
```

### 2.3 Installer Git

Git est le programme qu'utilise SpaceCDF pour se télécharger depuis
GitHub.

#### macOS

Git est fourni avec les outils de développement en ligne de commande.
Tapez dans le Terminal :

```bash
git --version
```

S'il vous propose d'installer les outils de développement, cliquez sur
**Install** et patientez environ cinq minutes.

#### Windows 11

1. Allez sur <https://git-scm.com/download/win>.
2. Lancez le programme d'installation et acceptez toutes les valeurs par
   défaut.
3. Une fois l'installation terminée, ouvrez un nouveau PowerShell et
   tapez :

   ```powershell
   git --version
   ```

#### Ubuntu Linux

```bash
sudo apt install -y git
git --version
```

> **Vous êtes bloqué ?** À ce stade, vous devez disposer de trois
> commandes fonctionnelles : `python3 --version` (3.11 ou ultérieure),
> `node --version` (18 ou ultérieure) et `git --version`. Si l'une d'elles
> échoue encore après le redémarrage du terminal, reportez-vous au §7
> *Dépannage* avant de continuer.

---

## 3. Télécharger SpaceCDF

Choisissez le dossier dans lequel vous rangez vos projets. Dans les
exemples ci-dessous, il s'agit de votre répertoire personnel (`~`) ;
remplacez-le par l'emplacement de votre choix.

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

Cette commande télécharge environ 200 Mo de code source et peut prendre
quelques minutes sur une connexion lente.

---

## 4. Installer le backend (Python)

Le backend est le moteur qui exécute les 20 agents de conception et
produit les documents.

### 4.1 Créer un environnement virtuel Python

Un *environnement virtuel* isole les dépendances Python de SpaceCDF de
tout le reste de votre ordinateur.

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

Si PowerShell refuse avec une erreur de « stratégie d'exécution »
(*execution policy*), exécutez ceci **une seule fois** dans une fenêtre
PowerShell lancée *en tant qu'administrateur* :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Fermez puis rouvrez PowerShell et relancez l'activation.

**Vérification.** Une fois l'environnement activé, l'invite doit être
précédée de `(.venv)`.

### 4.2 Installer les paquets Python de SpaceCDF

L'environnement virtuel étant actif, installez les quatre paquets du
backend. Cela télécharge environ 230 Mo de dépendances et prend environ
5 minutes.

```bash
pip install --upgrade pip
pip install -e packages/spacecdf-common
pip install -e packages/spacecdf-agents
pip install -e packages/spacecdf-kb
pip install -e packages/spacecdf-server
```

Vous devez voir « Successfully installed … » quatre fois.

### 4.3 Test de fumée du backend

```bash
python scripts/run_design.py configs/examples/6u_eo_cubesat.yaml
```

Au bout d'une seconde environ, vous devez voir une bannière `MISSION: EOSAT-1 Multispectral
Imager` puis un affichage des bilans de masse, de puissance, de coût et
des autres bilans, suivi de `CONVERGED`. Si vous en êtes là, le backend
fonctionne.

---

## 5. Installer le frontend (interface web)

Dans une **deuxième** fenêtre de terminal — laissez la première tourner —,
placez-vous dans le dossier `frontend` et installez les outils de
construction JavaScript.

```bash
cd ~/SpaceCDF/frontend         # or:   cd $HOME\SpaceCDF\frontend
npm install
```

`npm install` télécharge environ 170 Mo et prend de 3 à 6 minutes la
première fois. Des avertissements peuvent s'afficher : ils sont normaux
tant que la commande se termine par une ligne `added <N> packages`.

---

## 6. Premier lancement

Vous avez besoin de **deux terminaux ouverts simultanément** : l'un pour
le serveur backend, l'autre pour le frontend.

### 6.1 Démarrer le backend (terminal 1)

```bash
cd ~/SpaceCDF                # or:  cd $HOME\SpaceCDF
source .venv/bin/activate     # macOS / Linux
# .venv\Scripts\Activate.ps1 # Windows
uvicorn spacecdf_server.app:app --reload --port 8000
```

Vous devez voir des lignes se terminant par `Uvicorn running on http://0.0.0.0:8000`.
Laissez ce terminal ouvert.

### 6.2 Démarrer le frontend (terminal 2)

```bash
cd ~/SpaceCDF/frontend       # or:  cd $HOME\SpaceCDF\frontend
npm run dev
```

Vous devez voir une ligne se terminant par `Local:   http://localhost:5173/`.

### 6.3 Ouvrir SpaceCDF dans votre navigateur

Ouvrez <http://localhost:5173> dans Chrome, Firefox, Safari ou Edge. Vous
devez voir l'écran d'accueil de SpaceCDF.

> **Critère de réussite.** Sur l'écran d'accueil, cliquez sur **New
> study** (nouvelle étude). Si vous pouvez nommer une étude et atteindre
> l'étape 1 (*Mission Need*, besoin de mission) sans bannière d'erreur,
> SpaceCDF est entièrement installé.

### 6.4 Exécuter votre première conception

1. Depuis l'écran d'accueil, cliquez sur **New study**. Nommez-la `My First Mission`.
2. À l'étape 1 (*Mission Need*), choisissez un problème type dans la liste
   des suggestions, puis cliquez sur **Continue** (continuer).
3. Étape 2 (*Concept*) : acceptez la valeur par défaut.
4. Étape 3 (*Requirements*) : choisissez « SSO at 500 km » et une charge
   utile.
5. Étape 4 (*Design*) : cliquez sur le grand bouton **Run Design**. Les
   20 agents convergent en moins d'une seconde.
6. Ouvrez l'onglet **Exports** et cliquez sur **Generate SRR**. Au bout
   d'une seconde, un dossier `.docx`, `.xlsx` et `.md` vous est proposé au
   téléchargement.

Si vous en êtes là, félicitations : vous faites tourner un centre de
conception concourante complet sur votre propre machine.

---

## 7. Dépannage

### « Command not found: python3 » (macOS / Linux)

Vous avez sauté le §2.1. Reprenez cette section, puis fermez et rouvrez
le terminal pour qu'il prenne en compte le nouveau `PATH`.

### « Activate.ps1 cannot be loaded because running scripts is disabled » (Windows)

Vous devez autoriser les scripts PowerShell. Dans un PowerShell lancé en
tant qu'administrateur :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Rouvrez ensuite PowerShell et relancez l'activation.

### Erreurs de `pip install` mentionnant `wheel` ou `setuptools`

Mettez d'abord pip à jour, puis réessayez :

```bash
pip install --upgrade pip setuptools wheel
```

### Erreurs de `npm install`

Si l'installation échoue en cours de route, supprimez l'installation
partielle et réessayez :

```bash
rm -rf node_modules package-lock.json   # macOS / Linux
# Remove-Item -Recurse -Force node_modules,package-lock.json   # Windows
npm install
```

### « Port 8000 already in use » ou « Port 5173 already in use »

Un autre programme utilise ce port. Fermez-le ou choisissez un autre
port :

```bash
uvicorn spacecdf_server.app:app --reload --port 8100
```

Si vous changez le port du backend, mettez aussi à jour
`frontend/vite.config.ts` pour que le frontend sache où le trouver.

### Le navigateur affiche « ERR_CONNECTION_REFUSED »

Le backend (port 8000) ou le frontend (port 5173) ne tourne pas. Passez
dans chaque terminal et vérifiez que les deux sont toujours actifs.

### Les conceptions ne convergent pas

Consultez le panneau des avertissements à l'étape 4. Une cause fréquente
est le choix d'une charge utile qui consomme plus de puissance que la
classe de satellite ne peut en fournir : choisissez une charge utile plus
petite ou une classe de satellite plus grande.

### L'export de documents échoue

Assurez-vous que l'environnement virtuel actif est bien celui dans lequel
vous avez installé les paquets. L'invite doit afficher `(.venv)`. Sinon,
réactivez-le.

---

## 8. Compléments facultatifs

### 8.1 Exécution avec Docker Compose

Docker Compose démarre le backend, PostgreSQL et Redis dans des
conteneurs. Le frontend s'exécute toujours en local (il a besoin de
Node.js pour le rechargement à chaud).

```bash
cd ~/SpaceCDF
docker compose up --build -d     # Backend + Postgres + Redis
cd frontend && npm run dev        # Frontend (local)
```

Ouvrez <http://localhost:5173>. L'API du backend est accessible à `http://localhost:8000`.

Pour arrêter :

```bash
docker compose down               # Stop containers
docker compose down -v            # Stop and delete database volume
```

### 8.2 Exécution avec PostgreSQL au lieu de SQLite

Par défaut, SpaceCDF utilise SQLite (persistance dans `spacecdf.db`). Pour
des déploiements de production multi-utilisateurs, passez à
PostgreSQL 16+ :

```bash
export DATABASE_URL=postgresql+asyncpg://spacecdf:spacecdf_dev@localhost:5432/spacecdf
```

Vous pouvez aussi ajouter cette ligne à votre fichier `.env`. La
configuration Docker Compose utilise PostgreSQL automatiquement.

### 8.3 Activer la conception assistée par l'IA (facultatif)

SpaceCDF peut, en option, utiliser Claude AI pour des conseils de
conception, la décomposition des exigences, l'analyse de compromis, etc.

```bash
source .venv/bin/activate
pip install -e packages/spacecdf-ai
```

Définissez ensuite votre clé d'API dans `.env` :

```
ANTHROPIC_API_KEY=sk-ant-...
```

Les fonctions d'IA s'activent capacité par capacité dans
`configs/genai.yaml`. Si le paquet n'est pas installé ou si la clé est
absente, SpaceCDF fonctionne en mode entièrement manuel, sans erreur.

### 8.4 Accès à distance avec Tailscale

Pour partager votre instance locale avec des collègues, installez
Tailscale (<https://tailscale.com/download>) sur les deux machines et
utilisez votre adresse IP tailnet.

### 8.5 Conserver la bibliothèque des normes ECSS hors ligne

Les deux dossiers ECSS (`Active ECSS Standards_PDF-files …` et
`ECSS-Handbooks_…`) occupent environ 500 Mo. Si vous en avez l'usage,
conservez-les à la racine du dépôt. Sinon, vous pouvez les déplacer sur un
disque externe ou les supprimer : l'outil se contente alors de citer les
normes par leur référence.

---

## 9. Mettre à jour SpaceCDF

Pour récupérer la dernière version depuis GitHub :

```bash
cd ~/SpaceCDF               # or:  cd $HOME\SpaceCDF
git pull
source .venv/bin/activate    # macOS / Linux
pip install -e packages/spacecdf-common -e packages/spacecdf-agents -e packages/spacecdf-kb -e packages/spacecdf-server
cd frontend
npm install
```

Redémarrez ensuite les deux terminaux du §6.

---

## 10. Désinstallation

SpaceCDF réside entièrement dans son propre dossier et dans
l'environnement virtuel Python. Pour le supprimer complètement :

```bash
# macOS / Linux
rm -rf ~/SpaceCDF
```

```powershell
# Windows
Remove-Item -Recurse -Force $HOME\SpaceCDF
```

Les installations de Python, de Node.js et de Git sont indépendantes et
restent sur votre machine pour d'autres logiciels.

---

## Déclaration — IA générative (AIG)

Ce guide d'installation a été produit avec l'assistance de l'IA
générative dans le cadre du flux de travail du centre de conception
concourante SpaceCDF. Le backend de SpaceCDF (Python · matplotlib ·
python-docx · WeasyPrint) a servi à rédiger, mettre en forme et vérifier
les étapes qui suivent ; les valeurs de configuration requise (mémoire
vive, disque, temps de convergence) ont été mesurées en exécutant l'outil.
Le cadrage éditorial et la formulation finale restent de la
responsabilité de l'équipe enseignante de SpaceCDF.

*L'attribution suit le cadre AIG (assisté par l'IA générative) —
Peters (2023), Logos IA-EN, CC BY-NC-SA 4.0 —
[https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/](https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/)*

Tout livrable du cours qui intègre du contenu de ce guide — ou de tout
document exporté par SpaceCDF — doit porter le badge AIG et une courte
note décrivant l'usage qui a été fait de l'IA générative.

---

*SpaceCDF · uOttawa · École de conception et d'innovation pédagogique en génie (ECIPG)*
