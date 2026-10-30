"""French text for the textbook figures (used by i18n_fig.tr when FIG_LANG=fr).

Keys are the exact strings each English generator sets (titles, labels, ticks,
legend entries, annotations, table cells, including the numbers its f-strings
produce). Values are European French per i18n/STYLE_FR.md and glossary.csv:
decimal comma, units after a no-break space, guillemets, bilan, PIRE/TEB,
SCAO, k€, Go. Plain spaces are fine here — i18n_fig applies the no-break /
narrow no-break spaces (before units, ':', ';', '?', inside « »,
thousands groups) when it renders the string.

Bare numbers and strings made only of numbers, units, symbols and acronyms
(e.g. '−164.1 dB', 'PDR', '300 km') need no entry: i18n_fig converts them.
If a generator's English text changes, its old key no longer matches and the
French build prints FR-MISSING for the new string.

To refresh the list of source strings:
    FIG_HARVEST=/tmp/h python3 make_all.py     # writes /tmp/h/<figure>.json
"""

# Strings that recur across figures
COMMON = {
    "Phase A": "Phase A",
    "Phase B": "Phase B",
    "Phase C": "Phase C",
    "Phase D": "Phase D",
    "Phase E": "Phase E",
    "Phase F": "Phase F",
    "Payload": "Charge utile",
    "Commissioning": "Recette en orbite",
    "Nominal operations": "Opérations nominales",
    "Thermal": "Thermique",
    "Power": "Énergie",
    "Comms": "Télécom",
    "Stakeholder need": "Besoin des parties prenantes",
    "Space segment": "Segment spatial",
    "Ground segment": "Segment sol",
    "User segment": "Segment utilisateur",
    "Gain (dBi)": "Gain (dBi)",
    "Launch": "Lancement",
    "Operations": "Opérations",
}

PER_FIGURE = {
# ---------------------------------------------------------------- Ch 11
"fig_antenna_pattern": {
    "Angle from boresight (deg)": "Angle par rapport à l'axe de visée (°)",
    "3 m parabolic dish — G = 35 dBi, HPBW ≈ 3.1°": "Parabole 3 m — G = 35 dBi, ouverture ≈ 3,1°",
    "S-band patch — G = 6 dBi, HPBW ≈ 80°": "Patch bande S — G = 6 dBi, ouverture ≈ 80°",
    "half-power beamwidth\n(shaded)": "ouverture à\nmi-puissance (grisée)",
    "sidelobes\n(−17.6 dB first)": "lobes secondaires\n(premier à −17,6 dB)",
    "half-power beamwidth (shaded)": "ouverture à mi-puissance (zone grisée)",
    "Antenna gain patterns at 2.25 GHz — high-gain dish vs low-gain patch":
        "Diagrammes de rayonnement à 2,25 GHz — parabole à grand gain et patch à faible gain",
},
# ---------------------------------------------------------------- Ch 10
"fig_aocs_loop": {
    "Controller": "Correcteur",
    "control law\n(PD / PID)": "loi de commande\n(PD / PID)",
    "Actuators": "Actionneurs",
    "wheels, magnetorquers,\nthrusters": ("roues, magnétocoupleurs,\npropulseurs", 0.9),
    "Spacecraft dynamics": "Dynamique de l'engin",
    "reference\nattitude $q_{ref}$": "attitude de\nréférence $q_{ref}$",
    "error": "erreur",
    "torque\ndemand": "couple\ndemandé",
    "Disturbance torques $T_{ext}$": "Couples perturbateurs $T_{ext}$",
    "gravity gradient, drag, SRP,\nresidual magnetic dipole (§10.2)":
        ("gradient de gravité, traînée, radiation solaire,\ndipôle magnétique résiduel (§10.2)", 0.86),
    "true\nattitude\n$q, \\omega$": "attitude\nréelle\n$q, \\omega$",
    "Sensors": "Capteurs",
    "star tracker, Sun sensors,\nmagnetometer, gyros": ("senseur stellaire, senseurs\nsolaires, magnétomètre, gyros", 0.88),
    "Attitude estimator": "Estimateur d'attitude",
    "Kalman filter fuses the\nmeasurements into $\\hat{q}, \\hat{\\omega}$":
        "le filtre de Kalman fusionne\nles mesures en $\\hat{q}, \\hat{\\omega}$",
    "measurements": "mesures",
    "estimated\nattitude $\\hat{q}$": "attitude\nestimée $\\hat{q}$",
    "sensor noise, bias, misalignment": "bruit, biais et désalignement des capteurs",
    "The loop runs in the flight software; the same structure applies to every "
    "sensor/actuator architecture in this chapter.":
        "La boucle s'exécute dans le logiciel de vol ; la même structure vaut pour toutes "
        "les architectures capteurs/actionneurs du chapitre.",
},
# ---------------------------------------------------------------- Ch 09
"fig_battery_dod": {
    "1 year LEO (~5500 cycles)": "1 an en LEO (env. 5500 cycles)",
    "Typical 5-yr LEO design:\nDoD = 30 % → 27 k cycles": "Conception type, LEO 5 ans :\nDoD = 30 % → 27 000 cycles",
    "Depth of discharge (% of full capacity)": "Profondeur de décharge (% de la capacité totale)",
    "Cycles to end of life (knee)": "Cycles jusqu'à la fin de vie (coude)",
    "Battery cycle life vs DoD — Li-ion families (illustrative)":
        "Durée de vie en cycles selon la DoD — familles Li-ion (indicatif)",
    "Heritage (LiCoO2)": "Ancienne génération (LiCoO2)",
    "Aerospace (NCA/NMC)": "Qualité spatiale (NCA/NMC)",
    "LFP (high-life)": "LFP (longue durée de vie)",
    "5-year LEO (27 500 cycles)": "LEO 5 ans (27 500 cycles)",
    "10-year LEO (55 000 cycles)": "LEO 10 ans (55 000 cycles)",
},
# ---------------------------------------------------------------- Ch 07
"fig_beta_eclipse": {
    "ISS envelope ±(i + 23.4°) = ±75°": "Enveloppe ISS ±(i + 23,4°) = ±75°",
    "β* = 70° at 400 km — fully sunlit beyond": "β* = 70° à 400 km — sans éclipse au-delà",
    "SSO band -24° … -17° (set by LTAN)": "Bande SSO −24° … −17° (fixée par la LTAN)",
    "Day of year": "Jour de l'année",
    "β-angle (deg)": "Angle β (°)",
    "β-angle through the year": "Angle β au cours de l'année",
    "ISS-like (51.6°, 400 km)": "Type ISS (51,6°, 400 km)",
    "SSO 10:30 LTAN (98°, 600 km)": "SSO, LTAN 10:30 (98°, 600 km)",
    "max 39 % at β = 0 (400 km)": "max. 39 % à β = 0 (400 km)",
    "max 37 % (600 km)": "max. 37 % (600 km)",
    "fully sunlit for |β| ≥ β*:\nβ* = 70° (400 km), 66° (600 km)":
        "sans éclipse pour |β| ≥ β* :\nβ* = 70° (400 km), 66° (600 km)",
    "Eclipse fraction of orbit (%)": "Fraction d'éclipse de l'orbite (%)",
    "Eclipse fraction vs β-angle": "Fraction d'éclipse selon l'angle β",
},
# ---------------------------------------------------------------- Ch 13
"fig_bom_tree": {
    "Item ID": "Réf. article",
    "Description": "Désignation",
    "Qty": "Qté",
    "Mass\n(g)": "Masse\n(g)",
    "Power\n(W)": "Puiss.\n(W)",
    "Cost\n(kEUR)": "Coût\n(k€)",
    "Lowest\nTRL": "TRL\nmin.",
    "Longest\nlead (wk)": "Délai\n(sem.)",
    "Indent = BOM level (0 spacecraft, 1 subsystem, 2 assembly, 3 component, 4 part).\n"
    "Bold rows are roll-ups of the rows beneath them.":
        "Retrait = niveau de nomenclature (0 satellite, 1 sous-système, 2 ensemble, 3 composant, 4 pièce).\n"
        "Les lignes en gras consolident les lignes situées en dessous.",
    "Spacecraft": "Satellite",
    "Structure": "Structure",
    "Electrical power (EPS)": "Énergie (EPS)",
    "Solar array assembly": "Générateur solaire",
    "Solar cell string": "Chaîne de cellules",
    "Azur 3G30C cell": "Cellule Azur 3G30C",
    "Bypass diode": "Diode de dérivation",
    "Substrate panel": "Panneau substrat",
    "Battery assembly": "Ensemble batterie",
    "Power board": "Carte d'alimentation",
    "On-board computer": "Calculateur de bord",
    "Attitude control": "Contrôle d'attitude",
    "Communications": "Télécommunications",
    "Payload (imager)": "Charge utile (imageur)",
    "Harness": "Harnais",
    "Roll-up rules: mass, power and cost are quantity-weighted sums of the children;\n"
    "TRL is the minimum and lead time the maximum over the children.  "
    "Leaf values are per unit (illustrative).":
        "Consolidation : masse, puissance et coût sont les sommes des enfants pondérées par les quantités ;\n"
        "le TRL est le minimum et le délai le maximum des enfants. Valeurs des feuilles par unité (indicatives).",
},
# ---------------------------------------------------------------- Ch 02
"fig_canadian_sector": {
    "The Canadian space sector — illustrative map of actors": "Le secteur spatial canadien — carte indicative des acteurs",
    "Federal": "Fédéral",
    "· Canadian Space Agency (CSA)": "· Agence spatiale canadienne (ASC)",
    "· ISED (spectrum / RSSSA)": "· ISDE (spectre / LSTS)",
    "· Global Affairs Canada (export)": ("· Affaires mondiales Canada (export.)", 0.92),
    "Industry primes": "Maîtres d'œuvre",
    "New space": "New Space",
    "· GHGSat (methane)": "· GHGSat (méthane)",
    "Universities & labs": "Universités et laboratoires",
    "Funding": "Financement",
    "· CSA STDP": "· ASC — PDTS",
    "· CSA FAST": "· ASC — VITES (FAST)",
    "· CSA CSEP": "· ASC — CSEP",
    "· NSERC / CFI · Provincial": "· CRSNG / FCI · provinces",
    "International ties": "Liens internationaux",
    "· NASA Artemis · ISS": "· NASA Artemis · ISS",
    "· ESA cooperation": "· Coopération avec l'ESA",
    "· ITU · COPUOS": "· UIT · CUPEEA",
    "· Five Eyes (defence)": "· Groupe des cinq (défense)",
    "End users": "Utilisateurs finaux",
    "· Climate / GHG monitoring · Arctic surveillance · Maritime traffic":
        "· Surveillance du climat et des GES · surveillance de l'Arctique · trafic maritime",
    "· Remote-area connectivity (broadband / IoT)": "· Connectivité des régions éloignées (haut débit / IdO)",
    "· Defence ISR · Disaster response · Forestry & agriculture":
        "· Renseignement et surveillance (défense) · catastrophes · forêts et agriculture",
    "· Indigenous community-led monitoring": "· Surveillance menée par les communautés autochtones",
    "· MDA · Telesat": "· MDA · Telesat",
    "· Magellan · Maxar Canada": "· Magellan · Maxar Canada",
    "· ABB Canada": "· ABB Canada",
    "· Kepler Communications": "· Kepler Communications",
    "· NorthStar (SSA)": "· NorthStar (SSA)",
    "· Mission Control · ExoFly": "· Mission Control · ExoFly",
    "· UTIAS · McGill · uOttawa": "· UTIAS · McGill · uOttawa",
    "· Western · Calgary · UBC": "· Western · Calgary · UBC",
    "· Concordia · Sherbrooke": "· Concordia · Sherbrooke",
    "· York · Laval · Dalhousie": "· York · Laval · Dalhousie",
},
# ---------------------------------------------------------------- Ch 12
"fig_cds_envelope": {
    "deployment switches\n(−Z rail ends, ≥ 1 per\naccessible rail face)":
        "interrupteurs de déploiement\n(extrémités −Z des rails,\n≥ 1 par face accessible)",
    "6.5 mm protrusion\nenvelope on ±X/±Y faces\n(between rails, stowed)":
        "saillie max. 6,5 mm\nsur les faces ±X/±Y\n(entre les rails, replié)",
    "RBF pin access\n(accessible in the deployer)": "accès à la goupille RBF\n(dans le déployeur)",
    "CG within 2 cm of the\ngeometric centre": "CdG à moins de 2 cm\ndu centre géométrique",
    "hard-anodised Al rails\n(4 ×, 8.5 × 8.5 mm)": "rails Al anodisé dur\n(4 ×, 8,5 × 8,5 mm)",
    "rail-end contact pads\n(stand-offs)": "patins de contact en bout\nde rail (entretoises)",
    "Side view (X–Z)": "Vue de côté (X–Z)",
    "CG box\n±20 mm": "boîte CdG\n±20 mm",
    "rails slide in the deployer guide channels;\nno protrusion beyond the rail envelope except\n"
    "the 6.5 mm allowance between the rails":
        "les rails coulissent dans les glissières du déployeur ;\naucune saillie hors de l'enveloppe des rails, "
        "sauf\nla tolérance de 6,5 mm entre les rails",
    "PC/104 stack inside": "pile PC/104 à l'intérieur",
    "End view (X–Y), 1U cross-section": "Vue en bout (X–Y), section 1U",
},
# ---------------------------------------------------------------- Ch 04
"fig_conops_timeline": {
    "Mission operations timeline (representative LEO mission)":
        "Chronologie des opérations (mission LEO représentative)",
    "LEOP": "LEOP",
    "Days 0–7": "Jours 0 à 7",
    "Sequential power-on,\nantenna deploy,\nfirst contact, detumble":
        ("mise sous tension\nséquentielle, antenne\ndéployée, 1er contact,\namortissement", 0.88),
    "Weeks 1–6": "Semaines 1 à 6",
    "Subsystem checkouts,\npayload calibration,\nfirst light":
        ("vérification des\nsous-systèmes,\nétalonnage charge utile,\npremière lumière", 0.88),
    "Years 1–N": "Années 1 à N",
    "Pass planning, imaging, downlink,\nmomentum management,\nanomaly response":
        "planification des passages, prises\nde vue, transmission au sol, gestion\ndu moment cinétique, anomalies",
    "EOL / disposal": "Fin de vie",
    "≤ 25-yr clock": "délai ≤ 25 ans",
    "De-orbit burn /\npassivation;\ndecay clock starts":
        "manœuvre de désorbitation /\npassivation ; le décompte\nde rentrée commence",
    "time": "temps",
},
# ---------------------------------------------------------------- Ch 16
"fig_cost_funnel": {
    "point estimate": "estimation ponctuelle",
    "Parametric  ± 30–50 %": "Paramétrique  ± 30–50 %",
    "Analogy  ± 20–40 %": "Analogique  ± 20–40 %",
    "Bottom-up  ± 10–20 %": "Ascendante  ± 10–20 %",
    "Phase 0/A": "Phase 0/A",
    "Estimate accuracy, ± 1σ (% of estimate)": "Précision de l'estimation, ± 1σ (% de l'estimation)",
    "Lifecycle phase (design maturity)": "Phase du cycle de vie (maturité de la conception)",
    "± 1σ accuracy band": "bande de précision ± 1σ",
},
"fig_cost_scurve": {
    "Total mission cost (kEUR)": "Coût total de la mission (k€)",
    "Probability that cost ≤ x": "Probabilité que le coût soit ≤ x",
    "point estimate (CBE)\n456.8 kEUR → P47": "estimation ponctuelle (CBE)\n456,8 k€ → P47",
    "right-skewed tail →": "queue asymétrique à droite →",
    "cost reserve P50 → P80\n= 31 kEUR": "réserve pour coûts P50 → P80\n= 31 k€",
    "Monte Carlo, 200 000 draws, elements independent:\n"
    "  COTS bus hardware (5.0): normal, ± 10 %\n"
    "  Custom payload (4.0): lognormal, ± 30 %\n"
    "  Integration and test (6.0): lognormal, ± 25 %\n"
    "  Software (7.0): triangular, ± 40 %\n"
    "  PM / SE / MA (1.0–3.0): uniform, ± 25 %\n"
    "  Launch (8.0): normal, ± 15 %\n"
    "  Ground segment (9.0): normal, ± 10 %\n"
    "  Operations (10.0): uniform, ± 25 %":
        ("Monte-Carlo, 200 000 tirages, éléments indépendants :\n"
        "  Matériel plateforme COTS (5.0) : normale, ± 10 %\n"
        "  Charge utile spécifique (4.0) : log-normale, ± 30 %\n"
        "  Intégration et essais (6.0) : log-normale, ± 25 %\n"
        "  Logiciel (7.0) : triangulaire, ± 40 %\n"
        "  GP / IS / AM (1.0–3.0) : uniforme, ± 25 %\n"
        "  Lancement (8.0) : normale, ± 15 %\n"
        "  Segment sol (9.0) : normale, ± 10 %\n"
        "  Opérations (10.0) : uniforme, ± 25 %", 0.9),
},
# ---------------------------------------------------------------- Ch 04
"fig_data_pipeline": {
    "Instrument": ("Instrument", 0.88),
    "GB/day =\nrate × duty\ncycle": "Go/jour =\ndébit × rapport\ncyclique",
    "On-board\nstorage": "Stockage\nà bord",
    "GB ≥ 1 day\nof data\n(2× margin)": "Go ≥ 1 jour\nde données\n(marge 2×)",
    "Downlink": ("Liaison\ndescendante", 0.8),
    "GB/pass =\nrate × contact\ntime": "Go/passage =\ndébit × durée\nde contact",
    "Ground\nreception": ("Réception\nau sol", 0.94),
    "passes/day,\nstation\nnetwork": "passages/jour,\nréseau de\nstations",
    "Processing\nL0→L1→L2": ("Traitement\nL0→L1→L2", 0.88),
    "latency (h):\nalgorithms,\ncompute": "latence (h) :\nalgorithmes,\ncalcul",
    "Archive": "Archive",
    "catalogue,\nAPI, long-term\nstorage": "catalogue,\nAPI, stockage\nà long terme",
    "User\ndelivery": ("Livraison aux\nutilisateurs", 0.82),
    "latency (h):\nnetwork\nbandwidth": "latence (h) :\nbande passante\ndu réseau",
    "RF link\n(S/X-band)": "liaison RF\n(bande S/X)",
    "terrestrial\nnetwork": "réseau\nterrestre",
    "Sustainability condition: daily downlink capacity ≥ daily data generated,\n"
    "otherwise on-board storage fills.":
        "Condition de viabilité : capacité quotidienne de transmission ≥ données produites par jour,\n"
        "sinon le stockage à bord se remplit.",
},
# ---------------------------------------------------------------- Ch 11
"fig_data_volume": {
    "0.0023 GB/day": "0,0023 Go/jour",
    "0.24 GB/day": "0,24 Go/jour",
    "0.96 GB/day": "0,96 Go/jour",
    "12 GB/day": "12 Go/jour",
    "48 GB/day": "48 Go/jour",
    "UHF 9.6 kbit/s": "UHF 9,6 kbit/s",
    "S-band 1 Mbit/s": "Bande S 1 Mbit/s",
    "S-band 4 Mbit/s": "Bande S 4 Mbit/s",
    "X-band 50 Mbit/s": "Bande X 50 Mbit/s",
    "X-band 200 Mbit/s": "Bande X 200 Mbit/s",
    "Daily downlink capacity (GB/day, log)": "Capacité quotidienne de transmission (Go/jour, log)",
    "Daily downlink capacity by band  (4 × 8-min passes, single polar station)":
        "Capacité quotidienne de transmission par bande  (4 passages de 8 min, une station polaire)",
    "HK only (5 MB)": "Servitude seule (5 Mo)",
    "Imager, 1 band (0.5 GB)": "Imageur, 1 bande (0,5 Go)",
    "4-band imager (2.5 GB)": "Imageur 4 bandes (2,5 Go)",
    "SAR, compressed (30 GB)": "SAR, compressé (30 Go)",
    "Hyperspectral (60 GB)": "Hyperspectral (60 Go)",
    "payload\nproduction:": ("production\ncharge utile :", 0.85),
},
# ---------------------------------------------------------------- Ch 18
"fig_fdir_hierarchy": {
    "Level 0": "Niveau 0",
    "Hardware": "Matériel",
    "Detection: built-in watchdog": "Détection : chien de garde intégré",
    "Response: component reset": "Réponse : réinitialisation du composant",
    "Latency: milliseconds": "Latence : millisecondes",
    "e.g. processor watchdog timer": "p. ex. chien de garde du processeur",
    "Level 1": "Niveau 1",
    "Unit": "Équipement",
    "Detection: unit-level monitoring": "Détection : surveillance au niveau équipement",
    "Response: unit reconfiguration": "Réponse : reconfiguration de l'équipement",
    "Latency: seconds": "Latence : secondes",
    "e.g. EPS over-current trip": "p. ex. disjonction sur surintensité EPS",
    "Level 2": "Niveau 2",
    "Subsystem": "Sous-système",
    "Detection: subsystem health check": "Détection : contrôle de santé du sous-système",
    "Response: subsystem fallback mode": "Réponse : mode de repli du sous-système",
    "Latency: seconds to minutes": "Latence : secondes à minutes",
    "e.g. switch to backup star tracker": "p. ex. bascule sur le senseur stellaire de secours",
    "Level 3": "Niveau 3",
    "System": "Système",
    "Detection: system-level anomaly detection": "Détection : détection d'anomalies au niveau système",
    "Response: mode change: enter Safe": "Réponse : changement de mode (passage en survie)",
    "Latency: minutes": "Latence : minutes",
    "e.g. transition to safe mode": "p. ex. passage en mode survie",
    "Level 4": "Niveau 4",
    "Ground": "Sol",
    "Detection: human-in-the-loop diagnosis": "Détection : diagnostic avec opérateur humain",
    "Response: ground-command recovery": "Réponse : reprise par télécommande sol",
    "Latency: hours to days": "Latence : heures à jours",
    "e.g. anomaly investigation and patch": "p. ex. analyse d'anomalie et correctif",
    "What each layer does": "Rôle de chaque niveau",
    "FDIR layer": "Niveau FDIR",
    "escalate if the fault is not cleared": "escalade si le défaut persiste",
    "ground override: every autonomous action is\nvisible in telemetry and reversible by command":
        "primauté du sol : toute action autonome est\nvisible en télémesure et réversible par télécommande",
    "faults enter at the lowest layer that can detect them; the ground is the top level":
        "un défaut est pris en charge au plus bas niveau capable de le détecter ; le sol est le niveau supérieur",
},
"fig_fspl": {
    "1000 km LEO slant": "LEO, oblique 1000 km",
    "polar pass, low elevation": "passage polaire, faible élévation",
    "GEO direct": "GEO, zénith",
    "Slant range (km, log)": "Distance oblique (km, log)",
    "Free-space path loss (dB)": "Affaiblissement en espace libre (dB)",
    "Free-space path loss vs slant range across frequency bands":
        "Affaiblissement en espace libre selon la distance oblique, par bande de fréquences",
    "VHF (150 MHz)": "VHF (150 MHz)",
    "UHF (435 MHz)": "UHF (435 MHz)",
    "S-band (2.2 GHz)": "Bande S (2,2 GHz)",
    "X-band (8.0 GHz)": "Bande X (8,0 GHz)",
    "Ka-band (26 GHz)": "Bande Ka (26 GHz)",
},
# ---------------------------------------------------------------- Ch 17
"fig_ground_segment": {
    "GROUND SEGMENT": "SEGMENT SOL",
    "Ground-station network": "Réseau de stations sol",
    "• Antenna(s)\n• RF front-end (LNA, PA)\n• Modem / baseband\n• Tracking (Doppler, pointing)\n"
    "• Data capture\n• Timing (GPS-disciplined)":
        "• Antenne(s)\n• Tête RF (LNA, PA)\n• Modem / bande de base\n• Poursuite (Doppler, pointage)\n"
        "• Acquisition des données\n• Horloge (asservie au GPS)",
    "Mission control\nsystem (MCS)": "Système de contrôle\nde mission (MCS)",
    "• Telemetry processing\n• Telecommand generation\n• Scheduling\n• Monitoring, limit checks\n"
    "• Anomaly management":
        ("• Traitement de la télémesure\n• Génération des TC\n• Ordonnancement\n"
         "• Surveillance, seuils\n• Gestion des anomalies", 0.94),
    "Flight\ndynamics\n(FDS)": "Dynamique\ndu vol\n(FDS)",
    "• Orbit\n  determination\n• Orbit\n  prediction\n• Manoeuvre\n  planning\n• Conjunction\n  assessment":
        "• Restitution\n  d'orbite\n• Prédiction\n  d'orbite\n• Manœuvres\n• Conjonctions",
    "Data network (LAN / VPN between sites)": "Réseau de données (LAN / VPN entre sites)",
    "Mission planning system": "Planification de mission",
    "• Pass scheduling\n• Resource planning (power, data)\n• Conflict resolution":
        "• Planification des passages\n• Ressources (énergie, données)\n• Résolution des conflits",
    "Data processing and archive": "Traitement et archives",
    "• Level 0–2 processing\n• Archive / catalogue\n• Distribution to users":
        "• Traitement des niveaux 0 à 2\n• Archive / catalogue\n• Diffusion aux utilisateurs",
    "Space segment\n(spacecraft)": "Segment spatial\n(satellite)",
    "RF interface: telecommand up,\ntelemetry and payload data down":
        "Interface RF : télécommande montante,\ntélémesure et données charge utile descendantes",
    "User\nsegment": "Segment\nutilisateur",
    "products": "produits",
},
# ---------------------------------------------------------------- Ch 07
"fig_ground_track": {
    "start (ascending node)": "départ (nœud ascendant)",
    "Ottawa": "Ottawa",
    "Longitude (deg)": "Longitude (°)",
    "Latitude (deg)": "Latitude (°)",
    "Ground track — 600 km Sun-synchronous orbit (i = 97.79°), 1.5 revolutions":
        "Trace au sol — orbite héliosynchrone à 600 km (i = 97,79°), 1,5 révolution",
},
# ---------------------------------------------------------------- Ch 22
"fig_gsd": {
    "Aperture diameter (cm)": "Diamètre d'ouverture (cm)",
    "GSD vs aperture — diffraction and pixel limits  (visible band, λ = 550 nm)":
        "GSD selon l'ouverture — limites de diffraction et de pixel  (visible, λ = 550 nm)",
    "diffraction-limited @ 400 km": "limite de diffraction à 400 km",
    "diffraction-limited @ 500 km": "limite de diffraction à 500 km",
    "diffraction-limited @ 700 km": "limite de diffraction à 700 km",
    "diffraction-limited @ 1000 km": "limite de diffraction à 1000 km",
    "pixel-limited @ 500 km (p = 6 µm, f/D = 5)": "limite pixel à 500 km (p = 6 µm, f/D = 5)",
},
# ---------------------------------------------------------------- Ch 07
"fig_hohmann": {
    "ΔV₁ = 2397 m/s (perigee burn)": "ΔV₁ = 2397 m/s (poussée au périgée)",
    "ΔV₂ = 1456 m/s (apogee burn)": "ΔV₂ = 1456 m/s (poussée à l'apogée)",
    "Total ΔV = 3854 m/s\nTransfer time = 5.29 h": "ΔV total = 3854 m/s\nDurée du transfert = 5,29 h",
    "Hohmann transfer — LEO (400 km) → GEO": "Transfert de Hohmann — LEO (400 km) → GEO",
    "Initial circular orbit (400 km altitude)": "Orbite circulaire initiale (altitude 400 km)",
    "Final circular orbit (GEO, 35786 km)": "Orbite circulaire finale (GEO, 35 786 km)",
    "Hohmann transfer ellipse (half)": "Ellipse de transfert de Hohmann (moitié)",
},
# ---------------------------------------------------------------- Ch 22
"fig_j2_nodal": {
    "Inclination (deg)": "Inclinaison (°)",
    "Nodal regression rate Ω̇ (°/day)": "Vitesse de régression nodale Ω̇ (°/jour)",
    "J₂ nodal regression vs inclination — Sun-synchronous condition shown":
        "Régression nodale due à J₂ selon l'inclinaison — avec la condition d'héliosynchronisme",
    "SSO target Ω̇ = +0.9856 °/day": "Ω̇ visée en SSO = +0,9856 °/jour",
    "i = 98.2° at 700 km": "i = 98,2° à 700 km",
},
"fig_kepler_proof": {
    "ISS (400 km)": "ISS (400 km)",
    "Sentinel-2 (786 km)": "Sentinel-2 (786 km)",
    "GPS (20 184 km)": "GPS (20 184 km)",
    "GEO (35 786 km)": "GEO (35 786 km)",
    "Altitude (km, log)": "Altitude (km, log)",
    "Orbital period (min, log)": "Période orbitale (min, log)",
    "Kepler's third law — circular-orbit period vs altitude, checked against known orbits":
        "Troisième loi de Kepler — période d'une orbite circulaire selon l'altitude, comparée à des orbites connues",
},
}

PER_FIGURE.update({
# ---------------------------------------------------------------- Ch 02
"fig_licensing_timeline": {
    "critical path": "chemin critique",
    "formal application": "demande formelle",
    "ITU API filing (by ISED)": "dépôt de l'API à l'UIT (par ISDE)",
    "MIFR entry → radio licence": "inscription au MIFR → licence radio",
    "Start spectrum work in Phase A: ITU coordination alone can take\nlonger than the whole development schedule.":
        "Lancez les démarches de spectre dès la phase A : la seule coordination UIT peut durer\n"
        "plus longtemps que tout le calendrier de développement.",
    "Months after project kick-off": "Mois après le lancement du projet",
    "ISED pre-application (2–4 wk)": "Préconsultation ISDE (2–4 sem.)",
    "ISED technical review (3–6 mo)": "Examen technique ISDE (3–6 mois)",
    "ITU coordination (2–7 yr)": "Coordination UIT (2–7 ans)",
    "RSSSA operating licence (EO)": "Licence d'exploitation LSTS (OT)",
    "Export permits (EIPA; ITAR TAA)": "Licences d'exportation (LLEI ; TAA ITAR)",
},
# ---------------------------------------------------------------- Ch 01
"fig_lifecycle": {
    "Concept\nStudies": "Études\nde concept",
    "Pre-Phase A": "Pré-phase A",
    "Concept &\nTech Dev": "Concept et\ndév. techno.",
    "Preliminary\nDesign": "Conception\npréliminaire",
    "Final\nDesign": "Conception\nfinale",
    "Assembly,\nIntegration\n& Test": "Assemblage,\nintégration\net essais",
    "Operations &\nSustainment": "Exploitation\net maintien",
    "Closeout": "Clôture",
    "NASA reviews": "Revues NASA",
    "ECSS reviews": "Revues ECSS",
    "Project lifecycle phases and review gates — NASA vs ECSS":
        "Phases du cycle de vie et jalons de revue — NASA et ECSS",
},
# ---------------------------------------------------------------- Ch 11
"fig_link_budget": {
    "→ EIRP = +7.5 dBW": "→ PIRE = +7,5 dBW",
    "Transmit power (2 W)": "Puissance d'émission (2 W)",
    "Tx antenna gain (patch)": "Gain d'antenne d'émission (patch)",
    "Tx line losses": "Pertes de ligne à l'émission",
    "Free-space path loss (2.25 GHz, 1695 km)": "Affaiblissement en espace libre (2,25 GHz, 1695 km)",
    "Atmospheric loss (10° elevation)": "Affaiblissement atmosphérique (élévation 10°)",
    "Pointing loss": "Perte de dépointage",
    "Polarisation loss": "Perte de polarisation",
    "Rx antenna gain (3 m dish)": "Gain d'antenne de réception (parabole 3 m)",
    "System noise temperature (150 K)": "Température de bruit du système (150 K)",
    "Boltzmann constant (−10·log k)": "Constante de Boltzmann (−10·log k)",
    "Cumulative C/N₀ (dBHz)": "C/N₀ cumulé (dBHz)",
    "S-band downlink link budget — waterfall (500 km SSO, 10° elevation)":
        "Bilan de liaison descendante en bande S — cascade (SSO 500 km, élévation 10°)",
    "Received C/N₀ = 83.4 dBHz": "C/N₀ reçu = 83,4 dBHz",
    "Required C/N₀ = 73.0 dBHz (5 Mbit/s)": "C/N₀ requis = 73,0 dBHz (5 Mbit/s)",
    "Link margin = 83.4 − 73.0 = +10.4 dB": "Marge de liaison = 83,4 − 73,0 = +10,4 dB",
},
# ---------------------------------------------------------------- Ch 08
"fig_mass_budget": {
    "Payload — 2.4 kg": "Charge utile — 2,4 kg",
    "Structure — 1.8 kg": "Structure — 1,8 kg",
    "Power (SA + battery) — 1.6 kg": "Énergie (GS + batterie) — 1,6 kg",
    "AOCS — 1.0 kg": "SCAO — 1,0 kg",
    "Comms — 0.6 kg": "Télécom — 0,6 kg",
    "OBC / harness — 0.5 kg": "OBC / harnais — 0,5 kg",
    "Propulsion — 0.4 kg": "Propulsion — 0,4 kg",
    "Thermal — 0.2 kg": "Thermique — 0,2 kg",
    "Dry-mass distribution — 8.5 kg CBE": "Répartition de la masse sèche — CBE 8,5 kg",
    "Phase A\n20%×20%": ("Phase A\n20 %×20 %", 0.82),
    "Phase B\n10%×15%": ("Phase B\n10 %×15 %", 0.82),
    "Phase C\n5%×10%": ("Phase C\n5 %×10 %", 0.82),
    "Phase D\n0%×5%": ("Phase D\n0 %×5 %", 0.82),
    "(equipment maturity × system margin, Table 8.3)": "(maturité des équipements × marge système, tableau 8.3)",
    "Mass (kg)": "Masse (kg)",
    "ECSS margin envelope by phase": "Enveloppe de marges ECSS par phase",
    "Dry mass (CBE)": "Masse sèche (CBE)",
    "Margin: equipment + system (compound)": "Marge : équipements + système (cumulées)",
},
# ---------------------------------------------------------------- Ch 18
"fig_mode_state_machine": {
    # mode names are flight-software enums (DNT); descriptions are translated
    "SAFE MODE": "SAFE (mode survie)",
    "magnetorquers only": "magnétocoupleurs seuls",
    "standby, Sun-pointing, 4.0 W": ("veille, pointage Soleil, 4,0 W", 0.9),
    "fine pointing, 8.0 W": "pointage fin, 8,0 W",
    "reduced ops, 3.5 W": ("activité réduite, 3,5 W", 0.8),
    "S-band, 10.0 W": "bande S, 10,0 W",
    "survival only, magnetic Sun-pointing, beacon, 2.0 W — holds until the ground intervenes":
        "survie seule, pointage solaire magnétique, balise, 2,0 W — maintenu jusqu'à intervention du sol",
    "separation from deployer": "séparation du déployeur",
    "angular rate < threshold": "vitesse angulaire < seuil",
    "schedule, SoC > limit": "planning, SoC > limite",
    "complete": "terminé",
    "station in view, link up": "station en visibilité, liaison établie",
    "complete / LOS": "terminé / LOS",
    "Sun not\nin view": "Soleil\nnon visible",
    "Sun in\nview": "Soleil\nvisible",
    "fault": "défaut",
    "ground command only": "télécommande sol uniquement",
    "rate limit exceeded": "vitesse limite dépassée",
},
# ---------------------------------------------------------------- Ch 04
"fig_moe_mop_tpm": {
    "operational problem stated by the users": "problème opérationnel des utilisateurs",
    "“Timely crop assessments for food security”": "« Évaluer les cultures à temps pour la sécurité alimentaire »",
    "MoE · Measure of Effectiveness": "MoE · mesure d'efficacité",
    "how well the system satisfies the need": "degré de satisfaction du besoin",
    "“% of crop assessments delivered within\n5 days of acquisition”":
        "« % des évaluations de cultures livrées\ndans les 5 jours suivant l'acquisition »",
    "users / stakeholders — evaluated in Phase E": "utilisateurs / parties prenantes — évaluée en phase E",
    "Mission objective": "Objectif de mission",
    "specific, measurable goal": "but précis et mesurable",
    "“Provide 10 m GSD multispectral imagery,\nrevisit ≤ 5 days, data latency ≤ 24 h”":
        "« Fournir une imagerie multispectrale de GSD 10 m,\nrevisite ≤ 5 jours, latence des données ≤ 24 h »",
    "MoP · Measure of Performance": "MoP · mesure de performance",
    "technical performance of the system": "performance technique du système",
    "“GSD ≤ 10 m at nadir”": "« GSD ≤ 10 m au nadir »",
    "systems engineer — verified in Phase C/D": "ingénieur système — vérifiée en phase C/D",
    "Technical requirement": "Exigence technique",
    "verifiable “shall” statement": "énoncé « doit » vérifiable",
    "“The payload shall achieve GSD ≤ 10 m at nadir\nfrom the operational orbit”":
        "« La charge utile doit atteindre une GSD ≤ 10 m\nau nadir depuis l'orbite opérationnelle »",
    "TPM · Technical Performance Measure": "TPM · indicateur de perf. technique",
    "design parameter tracked over time": "paramètre de conception suivi dans le temps",
    "“Current best estimate of imager mass\nversus the 1.5 kg allocation”":
        "« Meilleure estimation actuelle de la masse\nde l'imageur face à l'allocation de 1,5 kg »",
    "design team — tracked in every phase": "équipe de conception — suivi à chaque phase",
    "Level": "Niveau",
    "Agricultural-monitoring example  ·  owner and when evaluated":
        "Exemple de surveillance agricole  ·  responsable et moment de l'évaluation",
},
# ---------------------------------------------------------------- Ch 08
"fig_n2_matrix": {
    "AOCS": "SCAO",
    "Thermal": "Therm.",
    "Payload": ("Ch. utile", 0.92),
    "Struct.": "Struct.",
    "Prop.": "Prop.",
    "from ↓ / to →": "de ↓ / vers →",
    "Mechanical (M)": "Mécanique (M)",
    "Electrical (E)": "Électrique (E)",
    "Thermal (T)": "Thermique (T)",
    "Data (D)": "Données (D)",
    "RF (R)": "RF (R)",
    "Optical (O)": "Optique (O)",
    "Software (S)": "Logiciel (S)",
    "Interface type": "Type d'interface",
    "N² interface matrix — 6U CubeSat (illustrative), read row → column":
        "Matrice N² des interfaces — CubeSat 6U (indicatif), lecture ligne → colonne",
},
# ---------------------------------------------------------------- Ch 17
"fig_ops_timeline": {
    "Early operations": "Premières opérations",
    "72 h: separation, beacon,\ndeployments, health check": "72 h : séparation, balise,\ndéploiements, bilan de santé",
    "weeks 1–4: subsystem checkout, AOCS calibration, payload first light":
        "semaines 1 à 4 : vérification des sous-systèmes, étalonnage SCAO, première lumière",
    "to month 3: performance characterisation, procedure refinement":
        "jusqu'au mois 3 : caractérisation des performances, mise au point des procédures",
    "routine science or service; orbit maintenance; automated passes":
        "science ou service de routine ; maintien à poste ; passages automatisés",
    "24/7  (3 shifts)": "24 h/24, 7 j/7  (3 quarts)",
    "16/7  (2 shifts)": "16 h/24, 7 j/7  (2 quarts)",
    "8/5  (1 shift, or automated)": "8 h/24, 5 j/7  (1 quart, ou automatisé)",
    "Staffing": "Effectifs",
    "Weeks after launch": "Semaines après le lancement",
    "month 1": "mois 1",
    "month 3": "mois 3",
    "month 6": "mois 6",
    "month 12": "mois 12",
},
# ---------------------------------------------------------------- Ch 03
"fig_orbital_lifetime": {
    "decays within 5 yr — compliant everywhere": "rentrée en moins de 5 ans — conforme partout",
    "5–25 yr — IADC-compliant, not FCC": "5 à 25 ans — conforme IADC, pas FCC",
    "> 25 yr — non-compliant without active de-orbit": "> 25 ans — non conforme sans désorbitation active",
    "Initial circular altitude (km)": "Altitude circulaire initiale (km)",
    "Natural orbital lifetime (years, log)": "Durée de vie orbitale naturelle (années, log)",
    "Approximate orbital lifetime vs altitude (drag-decay rule of thumb — illustrative)":
        "Durée de vie orbitale approximative selon l'altitude (règle empirique de traînée — indicatif)",
    "FCC 5-year rule": "Règle FCC des 5 ans",
    "IADC 25-year rule": "Règle IADC des 25 ans",
},
# ---------------------------------------------------------------- Ch 17
"fig_pass_geometry": {
    "minimum elevation mask 5°": "masque d'élévation minimale 5°",
    "≥ 30° elevation: high-rate downlink window": "élévation ≥ 30° : fenêtre de transmission à haut débit",
    "Time from AOS (min)": "Temps depuis l'AOS (min)",
    "Elevation (deg)": "Élévation (°)",
    "S-band pass geometry — high-latitude station, 450 km SSO (illustrative)":
        "Géométrie d'un passage en bande S — station à haute latitude, SSO 450 km (indicatif)",
},
# ---------------------------------------------------------------- Ch 10
"fig_pointing_tree": {
    "Star tracker NEA": "NEA du senseur stellaire",
    "Gyro bias residual": "Biais gyrométrique résiduel",
    "Time-tag uncertainty": "Incertitude d'étiquetage temporel",
    "RW micro-vibration": "Microvibrations des RW",
    "Disturbance torque (gravity grad.)": "Couple perturbateur (gradient de gravité)",
    "Disturbance torque (drag)": "Couple perturbateur (traînée)",
    "Thruster minimum impulse": "Impulsion minimale des propulseurs",
    "Mounting alignment": "Alignement de montage",
    "Thermal distortion": "Distorsion thermique",
    "Structural flexure": "Flexion structurale",
    "Contribution (1σ, millidegrees)": "Contribution (1σ, millidegrés)",
    "Pointing error budget — total RSS = 47.9 m°  ·  allocation ≤ 60 m°":
        "Bilan d'erreurs de pointage — RSS totale = 47,9 m°  ·  allocation ≤ 60 m°",
    "Allocation 60 m°": "Allocation 60 m°",
    "Total RSS 47.9 m°": "RSS totale 47,9 m°",
    "Knowledge group\nRSS = 13.3 m°": "Groupe connaissance\nRSS = 13,3 m°",
    "Control group\nRSS = 24.3 m°": "Groupe commande\nRSS = 24,3 m°",
    "Alignment group\nRSS = 39.1 m°": "Groupe alignement\nRSS = 39,1 m°",
},
# ---------------------------------------------------------------- Ch 09
"fig_power_modes": {
    "Generation (W)": "Production (W)",
    "Power generation across one orbit — sunlit arc and eclipse":
        "Production d'énergie sur une orbite — arc ensoleillé et éclipse",
    "eclipse": "éclipse",
    "Solar-array generation": "Production du générateur solaire",
    "Eclipse": "Éclipse",
    "Time in orbit (min)": "Temps sur l'orbite (min)",
    "Load (W)": "Charge (W)",
    "Stacked load profile by subsystem (illustrative)": "Profil de charge cumulé par sous-système (indicatif)",
    "Bus / OBC / AOCS": "Plateforme / OBC / SCAO",
    "Thermal heaters": "Réchauffeurs thermiques",
    "Payload imaging (sunlit only)": "Prise de vue (au soleil uniquement)",
    "Comms downlink": "Transmission au sol",
},
# ---------------------------------------------------------------- Ch 12
"fig_propulsion_map": {
    "Cold gas · < 1 W (valve)": "Gaz froid · < 1 W (vanne)",
    "Warm gas / resistojet\n5–15 W": "Gaz chaud / résistojet\n5–15 W",
    "Green monopropellant\n2–10 W (preheat)": "Monergol vert\n2–10 W (préchauffage)",
    "Electrospray / FEEP\n20–60 W": "Électronébulisation / FEEP\n20–60 W",
    "Hall effect\n50–300 W": "Effet Hall\n50–300 W",
    "CubeSat power envelope ≈ 20–60 W during firing:\nelectrospray fits; Hall-effect thrusters need ≥ 50 W":
        "Puissance disponible sur CubeSat ≈ 20–60 W en poussée :\n"
        "l'électronébulisation convient ; l'effet Hall exige ≥ 50 W",
    "cold gas: Isp 60 s,\n1.05 kg propellant": "gaz froid : Isp 60 s,\n1,05 kg d'ergols",
    "green monopropellant: Isp 235 s,\n0.249 kg propellant": "monergol vert : Isp 235 s,\n0,249 kg d'ergols",
    "electrospray: Isp 1200 s,\n0.048 kg propellant": "électronébulisation : Isp 1200 s,\n0,048 kg d'ergols",
    "Thrust": "Poussée",
    "Specific impulse $I_{sp}$ (s)": "Impulsion spécifique $I_{sp}$ (s)",
    "§12.2.5 design points (ΔV = 112 m/s, 5 kg dry)": "Points de conception du §12.2.5 (ΔV = 112 m/s, 5 kg à sec)",
    "CubeSat propulsion options: specific impulse versus thrust":
        "Options de propulsion pour CubeSat : impulsion spécifique selon la poussée",
},
# ---------------------------------------------------------------- Ch 15
"fig_rbd_wheels": {
    "Configuration A: three wheels in series": "Configuration A : trois roues en série",
    "all three must work (series)": "les trois doivent fonctionner (série)",
    "Wheel 1": "Roue 1",
    "Wheel 2": "Roue 2",
    "Wheel 3": "Roue 3",
    "Wheel 4": "Roue 4",
    "one wheel failure ends 3-axis control": "la panne d'une roue met fin au contrôle 3 axes",
    "Configuration B: four wheels, 3-of-4 voting": "Configuration B : quatre roues, vote 3 sur 4",
    "any three of the four must work (k-of-n)": "3 roues quelconques sur 4 doivent fonctionner (k sur n)",
    "3\nof\n4": "3\nsur\n4",
    "one wheel may fail: any three of the four span all three axes\n(pyramid geometry, Chapter 10 §10.3)":
        "une roue peut tomber en panne : trois roues quelconques couvrent les trois axes\n"
        "(géométrie pyramidale, chapitre 10, §10.3)",
},
# ---------------------------------------------------------------- Ch 02
"fig_regulatory_framework": {
    "Space activity": "Activité spatiale",
    "design · build · launch\noperate · distribute data": ("concevoir · fabriquer · lancer\nexploiter · diffuser", 0.82),
    "CSA": "ASC",
    "Canadian Space Agency Act\ncoordination, policy, funding": "Loi sur l'Agence spatiale canadienne\ncoordination, politique, financement",
    "ISED": "ISDE",
    "Radiocommunication Act (radio licence)\nRSSSA (remote-sensing licence)":
        ("Loi sur la radiocommunication (radio)\nLSTS (licence de télédétection)", 0.92),
    "GAC": "AMC",
    "Export and Import Permits Act (ECL)\nControlled Goods Program":
        ("LLEI (licences d'export. et d'import.)\nProgramme des marchandises contrôlées", 0.9),
    "DND / DRDC": "MDN / RDDC",
    "National Defence Act\ndual-use technology, classification": "Loi sur la défense nationale\ndouble usage, classification",
    "Transport Canada": "Transports Canada",
    "launch operations\n(no statute yet — future)": "opérations de lancement\n(pas encore de loi — à venir)",
    "ITU": "UIT",
    "Radio Regulations\nfrequency coordination, MIFR": ("Règlement des radiocom. (RR)\ncoordination des fréquences, MIFR", 0.85),
    "UN COPUOS": "CUPEEA (ONU)",
    "treaty obligations: registration,\ndebris-mitigation guidelines":
        ("traités : immatriculation,\nlignes directrices sur les débris", 0.92),
    "missile-technology controls\n(ECL Group 6)": "technologies de missiles\n(LMEC, groupe 6)",
    "ITU filings are submitted\nby ISED on Canada's behalf": "les dossiers UIT sont déposés\npar ISDE au nom du Canada",
    "MTCR controls enter the\nECL administered by GAC": "les contrôles du MTCR sont intégrés\nà la LMEC administrée par AMC",
    "Federal regulators and their statutes": "Organismes fédéraux et leurs lois",
    "International bodies": "Organismes internationaux",
},
# ---------------------------------------------------------------- Ch 05
"fig_requirement_hierarchy": {
    "Stakeholder\nneed": "Besoin des\nparties prenantes",
    "Mission\nrequirement": "Exigence\nde mission",
    "System\nrequirements": "Exigences\nsystème",
    "Subsystem\nrequirements": "Exigences\nsous-système",
    "Component\nrequirements": "Exigences\ncomposant",
    "“Timely agricultural monitoring\nfor food security”": "« Surveillance agricole en temps utile\npour la sécurité alimentaire »",
    "The system shall provide multispectral imagery\nwith GSD ≤ 10 m and revisit ≤ 5 days over the\ntarget region":
        "Le système doit fournir une imagerie multispectrale\nde GSD ≤ 10 m avec une revisite ≤ 5 jours\nsur la région cible",
    "derives": "dérive",
    "The payload shall achieve\nGSD ≤ 10 m at nadir from\nthe operational orbit":
        ("La charge utile doit atteindre\nune GSD ≤ 10 m au nadir\ndepuis l'orbite opérationnelle", 0.9),
    "The AOCS shall provide\npointing accuracy ≤ 0.1°\n(3σ) during imaging":
        "Le SCAO doit assurer une\nprécision de pointage ≤ 0,1°\n(3σ) pendant la prise de vue",
    "The comms system shall\ndownlink ≥ 5 GB/day": "Les télécom. doivent\ntransmettre au sol\n≥ 5 Go/jour",
    "decomposes into": "se décompose en",
    "The telescope aperture\nshall be ≥ 80 mm": "L'ouverture du télescope\ndoit être ≥ 80 mm",
    "The star tracker shall\nprovide ≤ 5 arcsec attitude\nknowledge (3σ)":
        "Le senseur stellaire doit\nassurer une connaissance\nd'attitude ≤ 5″ (3σ)",
    "The X-band transmitter\nshall provide ≥ 2 W\nRF power": "L'émetteur en bande X\ndoit fournir ≥ 2 W\nde puissance RF",
    "Component level": "Niveau composant",
    "optics, detector, baffle\nspecifications": "spéc. de l'optique, du\ndétecteur et du baffle",
    "allocates to": "s'alloue à",
    "star-tracker optical head,\nIMU, wheel specifications": "spéc. de la tête optique,\nde l'IMU et des roues",
    "transmitter, antenna,\ncable-loss specifications": "spéc. de l'émetteur, de\nl'antenne, pertes câbles",
    "Every requirement traces up to its\nparent and down to its children (§5.4.3)":
        "Chaque exigence se trace vers son parent\net vers ses enfants (§5.4.3)",
},
# ---------------------------------------------------------------- Ch 15
"fig_risk_matrix": {
    "1\nNegligible": "1\nNégligeable",
    "2\nMinor": "2\nMineure",
    "3\nModerate": "3\nModérée",
    "4\nMajor": "4\nMajeure",
    "5\nCatastrophic": "5\nCatastrophique",
    "1\nVery low": "1\nTrès faible",
    "2\nLow": "2\nFaible",
    "3\nMedium": "3\nMoyenne",
    "4\nHigh": "4\nÉlevée",
    "5\nVery high": "5\nTrès élevée",
    "Severity (consequence)": "Gravité (conséquence)",
    "Likelihood": "Vraisemblance",
    "Risk matrix (ECSS-M-ST-80C 5×5) — worked example": "Matrice des risques (ECSS-M-ST-80C, 5 × 5) — exemple résolu",
    "R1 Reaction-wheel failure   R2 Battery degradation   R3 Star-tracker glare\n"
    "R4 Ground-link outage   R5 Schedule slip   R6 Cosmic-ray SEU":
        "R1 Panne de roue de réaction   R2 Dégradation de la batterie   R3 Éblouissement du senseur stellaire\n"
        "R4 Coupure de la liaison sol   R5 Glissement du calendrier   R6 SEU dû au rayonnement cosmique",
},
# ---------------------------------------------------------------- Ch 10
"fig_rw_momentum": {
    "Micro wheel 1 mN m s": "Micro-roue 1 mN m s",
    "Small wheel 10 mN m s": "Petite roue 10 mN m s",
    "Medium wheel 40 mN m s": "Roue moyenne 40 mN m s",
    "Orbits since last desaturation": "Orbites depuis la dernière désaturation",
    "Accumulated momentum (mN m s, log)": "Moment cinétique accumulé (mN m s, log)",
    "Momentum accumulation — 3U CubeSat, 500 km": "Accumulation du moment cinétique — CubeSat 3U, 500 km",
    "Worst-case accumulation, 1.5 µN m": "Accumulation au pire cas, 1,5 µN m",
    "Dipole uncertainty band (0.5–1.5×)": "Bande d'incertitude du dipôle (0,5–1,5×)",
    "Residual dipole (0.05 A m²)": "Dipôle résiduel (0,05 A m²)",
    "Aerodynamic drag (solar max)": "Traînée aérodynamique (max. solaire)",
    "Gravity gradient (500 km)": "Gradient de gravité (500 km)",
    "Aerodynamic drag (solar min)": "Traînée aérodynamique (min. solaire)",
    "Solar radiation pressure": "Pression de radiation solaire",
    "Disturbance torque (µN m, log)": "Couple perturbateur (µN m, log)",
    "Disturbance torques — 3U CubeSat at 500 km": "Couples perturbateurs — CubeSat 3U à 500 km",
},
"fig_rw_pyramid": {
    "Four-wheel pyramid, cant angle β above the X–Y plane":
        "Pyramide à 4 roues, inclinaison β sur le plan X–Y",
    "+Z out of page": "+Z sortant de la page",
    "View along +Z: azimuths 90° apart": "Vue selon +Z : azimuts à 90°",
    "Columns of the distribution matrix D (wheel spin axes in the body frame):\n"
    "w1 = (cos β, 0, sin β)     w2 = (0, cos β, sin β)     w3 = (−cos β, 0, sin β)     w4 = (0, −cos β, sin β)":
        "Colonnes de la matrice de répartition D (axes de rotation des roues dans le repère satellite) :\n"
        "w1 = (cos β ; 0 ; sin β)     w2 = (0 ; cos β ; sin β)     w3 = (−cos β ; 0 ; sin β)     w4 = (0 ; −cos β ; sin β)",
},
# ---------------------------------------------------------------- Ch 01
"fig_seh_processes": {
    "NASA SEH — 17 common technical processes (NPR 7123.1)":
        "NASA SEH — les 17 processus techniques communs (NPR 7123.1)",
    "SYSTEM DESIGN": "CONCEPTION DU SYSTÈME",
    "1. Stakeholder Expectations Definition": "1. Définition des attentes des parties prenantes",
    "2. Technical Requirements Definition": "2. Définition des exigences techniques",
    "3. Logical Decomposition": "3. Décomposition logique",
    "4. Design Solution Definition": "4. Définition de la solution de conception",
    "PRODUCT REALISATION": "RÉALISATION DU PRODUIT",
    "5. Product Implementation": "5. Mise en œuvre du produit",
    "6. Product Integration": "6. Intégration du produit",
    "7. Product Verification": "7. Vérification du produit",
    "8. Product Validation": "8. Validation du produit",
    "9. Product Transition": "9. Transition du produit",
    "TECHNICAL MANAGEMENT": "MANAGEMENT TECHNIQUE",
    "10. Technical Planning": "10. Planification technique",
    "11. Requirements Management": "11. Gestion des exigences",
    "12. Interface Management": "12. Gestion des interfaces",
    "13. Technical Risk Management": "13. Gestion des risques techniques",
    "14. Configuration Management": "14. Gestion de configuration",
    "15. Technical Data Management": "15. Gestion des données techniques",
    "16. Technical Assessment": "16. Évaluation technique",
    "17. Decision Analysis": "17. Analyse de décision",
},
# ---------------------------------------------------------------- Ch 11
"fig_signal_noise": {
    "BER = 10⁻⁵": "TEB = 10⁻⁵",
    "BER = 10⁻⁷": "TEB = 10⁻⁷",
    "coding gain ≈ 5 dB": "gain de codage ≈ 5 dB",
    "Eb/N₀ (dB)": "Eb/N₀ (dB)",
    "Bit error rate": "Taux d'erreur binaire",
    "Eb/N₀ → BER for common modulations (theoretical, AWGN channel)":
        "Eb/N₀ → TEB pour les modulations courantes (théorique, canal à BBAG)",
    "BPSK / QPSK, uncoded": "BPSK / QPSK, non codé",
    "8-PSK, uncoded": "8-PSK, non codé",
    "Non-coherent FSK": "FSK non cohérente",
    "BPSK + conv. + RS(255,223) (≈ 5 dB gain)": "BPSK + conv. + RS(255,223) (gain ≈ 5 dB)",
},
# ---------------------------------------------------------------- Ch 09
"fig_solar_array": {
    "Orbit-average load (W)": "Charge moyenne sur l'orbite (W)",
    "Required array power, BOL (W)": "Puissance requise du générateur, BOL (W)",
    "Load → BOL power (Steps 2–3)": "Charge → puissance BOL (étapes 2 et 3)",
    "eclipse fraction = 0.00": "fraction d'éclipse = 0,00",
    "eclipse fraction = 0.20": "fraction d'éclipse = 0,20",
    "eclipse fraction = 0.38": "fraction d'éclipse = 0,38",
    "η_sun = 0.90, η_ecl = 0.79\nL_d·L_T = 0.86 (3 yr, 65 °C)": "η_sun = 0,90, η_ecl = 0,79\nL_d·L_T = 0,86 (3 ans, 65 °C)",
    "EOSat-3U: 16.0 W BOL\n→ 0.053 m² at θ = 23°": "EOSat-3U : 16,0 W BOL\n→ 0,053 m² à θ = 23°",
    "Array area A$_{SA}$ (m²)": "Surface du générateur A$_{SA}$ (m²)",
    "BOL power → array area (Step 4)": "Puissance BOL → surface du générateur (étape 4)",
    "Sun angle θ = 0°": "Angle solaire θ = 0°",
    "Sun angle θ = 23°": "Angle solaire θ = 23°",
    "Sun angle θ = 45°": "Angle solaire θ = 45°",
    "η_cell = 0.295, S = 1361 W/m²\nf_pack = 0.85, f_cover = 0.97": "η_cell = 0,295, S = 1361 W/m²\nf_pack = 0,85, f_cover = 0,97",
    "Solar-array sizing nomograph — A = P_BOL / (η_cell · S · cos θ · f_pack · f_cover)":
        "Abaque de dimensionnement du générateur solaire — A = P_BOL / (η_cell · S · cos θ · f_pack · f_cover)",
},
# ---------------------------------------------------------------- Ch 01
"fig_system_v": {
    "System-V model — decomposition · integration and verification":
        "Cycle en V — décomposition · intégration et vérification",
    "traceability: each requirement ↔ the activity that verifies it":
        "traçabilité : chaque exigence ↔ l'activité qui la vérifie",
    "Mission needs": "Besoins de la mission",
    "System requirements": "Exigences système",
    "Subsystem specs": "Spéc. sous-systèmes",
    "Component specs": "Spéc. composants",
    "Mission acceptance": "Recette de la mission",
    "System V&V": "V&V système",
    "Subsystem test": "Essais sous-systèmes",
    "Component test": "Essais composants",
    "Implementation": "Réalisation",
    "(build · inspect · unit test)": ("(fabriquer · inspecter · tester)", 0.95),
    "DECOMPOSITION": "DÉCOMPOSITION",
    "INTEGRATION & VERIFICATION": "INTÉGRATION ET VÉRIFICATION",
    "decompose": "décomposer",
    "integrate": "intégrer",
},
# ---------------------------------------------------------------- Ch 14
"fig_test_flow": {
    "Receive flight hardware": "Réception du matériel de vol",
    "Initial functional test (baseline)": "Essai fonctionnel initial (référence)",
    "Sine vibration, 3 axes": "Vibrations sinusoïdales, 3 axes",
    "Random vibration, 3 axes": "Vibrations aléatoires, 3 axes",
    "Post-vibration functional test": "Essai fonctionnel après vibrations",
    "Anomaly?": "Anomalie ?",
    "Thermal vacuum, 4–8 cycles\n(functional test at each extreme)": "Vide thermique, 4 à 8 cycles\n(essai fonctionnel à chaque extrême)",
    "Post-TVAC functional test": "Essai fonctionnel après TVAC",
    "EMC test (if required)": "Essai CEM (si exigé)",
    "Mass and CG measurement": "Mesure de masse et de CdG",
    "Deployer fit check": "Contrôle d'insertion (déployeur)",
    "Final functional test": "Essai fonctionnel final",
    "Pack and ship to launch site": "Expédition au site de lancement",
    "no": "non",
    "Investigate and\nresolve": "Analyser et\nrésoudre",
    "yes": "oui",
    "re-test": "nouvel essai",
    "Vibration levels": "Niveaux de vibrations",
    "Qualification: MPE + 3 dB, 2 min per axis\nAcceptance: MPE, 1 min per axis\nProto-flight: MPE + 3 dB, 1 min per axis":
        "Qualification : MPE + 3 dB, 2 min par axe\nRecette : MPE, 1 min par axe\nProtovol : MPE + 3 dB, 1 min par axe",
    "Thermal-vacuum levels": "Niveaux de vide thermique",
    "Qualification: predicted ± 15 °C, 8 cycles\nAcceptance: predicted ± 10 °C, 4 cycles\n"
    "Proto-flight: predicted ± 10 °C, 4–8 cycles\nVacuum < 10⁻⁵ mbar; ≥ 1 h dwell at each extreme":
        "Qualification : prévision ± 15 °C, 8 cycles\nRecette : prévision ± 10 °C, 4 cycles\n"
        "Protovol : prévision ± 10 °C, 4 à 8 cycles\nVide < 10⁻⁵ mbar ; palier ≥ 1 h à chaque extrême",
    "Environmental test": "Essai d'environnement",
    "Functional test": "Essai fonctionnel",
    "Measurement / inspection": "Mesure / inspection",
    "MPE = maximum predicted environment": "MPE = environnement maximal prévu",
},
# ---------------------------------------------------------------- Ch 09
"fig_thermal_balance": {
    "typical electronics operating band (−40 … +60 °C)": "plage typique de l'électronique (−40 … +60 °C)",
    "White paint (Z93)\nα/ε = 0.15/0.92 = 0.16": "Peinture blanche (Z93)\nα/ε = 0,15/0,92 = 0,16",
    "Black paint (Chemglaze)\nα/ε = 0.95/0.85 = 1.12": "Peinture noire (Chemglaze)\nα/ε = 0,95/0,85 = 1,12",
    "Aluminised Kapton\nα/ε = 0.40/0.63 = 0.63": "Kapton aluminisé\nα/ε = 0,40/0,63 = 0,63",
    "Machined Al 6061\nα/ε = 0.35/0.10 = 3.50": "Al 6061 usiné\nα/ε = 0,35/0,10 = 3,50",
    "α / ε  (solar absorptance / IR emittance)": "α / ε  (absorptivité solaire / émissivité IR)",
    "Equilibrium temperature (°C)": "Température d'équilibre (°C)",
    "Radiative thermal equilibrium — flat plate, LEO orbit-average":
        "Équilibre thermique radiatif — plaque plane, moyenne sur une orbite LEO",
    "Sun + Earth IR (LEO orbit-average)": "Soleil + IR terrestre (moyenne sur l'orbite LEO)",
    "Eclipse only (no Sun): -61 °C": "Éclipse seule (sans Soleil) : −61 °C",
    "Polished Al and MLI outer layers (α/ε ≈ 5–9) lie off-scale to the right.":
        "Al poli, couches externes de MLI (α/ε ≈ 5–9) : hors échelle.",
},
"fig_thermal_schematic": {
    "deep space  T ≈ 2.7 K (sink)": "espace profond  T ≈ 2,7 K (puits)",
    "Earth — albedo $\\alpha_E$ ≈ 0.30, IR $q_{IR}$ ≈ 240 W/m²": "Terre — albédo $\\alpha_E$ ≈ 0,30, IR $q_{IR}$ ≈ 240 W/m²",
    "Sun\n$S$ = 1361 W/m²": "Soleil\n$S$ = 1361 W/m²",
    "$Q_{int}$\nelectronics\ndissipation": ("$Q_{int}$\ndissipation\nélectronique", 0.9),
    "zenith face (radiator)": "face zénith (radiateur)",
    "nadir face": "face nadir",
    "Sun-facing\nside, $\\alpha_s$": "face au\nSoleil, $\\alpha_s$",
    "coatings:\n$\\alpha_s/\\varepsilon$": ("revêtements :\n$\\alpha_s/\\varepsilon$", 0.85),
    "direct solar\n$\\alpha_s A_{sun} S$": "solaire direct\n$\\alpha_s A_{sun} S$",
    "albedo\n$\\alpha_s A_{alb} F_{alb}\\, \\alpha_E S$": "albédo\n$\\alpha_s A_{alb} F_{alb}\\, \\alpha_E S$",
    "Earth IR\n$\\varepsilon A_{IR} F_{IR}\\, q_{IR}$": "IR terrestre\n$\\varepsilon A_{IR} F_{IR}\\, q_{IR}$",
    "radiated to space\n$Q_{out} = \\varepsilon \\sigma A_{rad} T^4$": "rayonné vers l'espace\n$Q_{out} = \\varepsilon \\sigma A_{rad} T^4$",
    "Hot case": "Cas chaud",
    "$S$ = 1414 W/m² (perihelion)\nall units on: max $Q_{int}$\nworst Sun angle: max $A_{sun}$\n"
    "EOL coatings: $\\alpha_s$ increased\nalbedo 0.35":
        "$S$ = 1414 W/m² (périhélie)\ntous équipements en marche : $Q_{int}$ max.\npire angle solaire : $A_{sun}$ max.\n"
        "revêtements EOL : $\\alpha_s$ accru\nalbédo 0,35",
    "Cold case": "Cas froid",
    "eclipse: no solar, no albedo\nsafe mode: min $Q_{int}$\nBOL coatings: $\\alpha_s$ lowest\n"
    "Earth IR 200 W/m²\nfull deep-space view":
        "éclipse : ni Soleil ni albédo\nmode survie : $Q_{int}$ min.\nrevêtements BOL : $\\alpha_s$ minimal\n"
        "IR terrestre 200 W/m²\nvue complète sur l'espace profond",
    "steady state: $Q_{in} = Q_{out}$\n$T = [(Q_{abs} + Q_{int})/(\\varepsilon\\sigma A_{rad})]^{1/4}$":
        "régime permanent : $Q_{in} = Q_{out}$\n$T = [(Q_{abs} + Q_{int})/(\\varepsilon\\sigma A_{rad})]^{1/4}$",
},
# ---------------------------------------------------------------- Ch 07
"fig_tid_altitude": {
    "≈ 600 km: COTS with modest\nshielding below, radiation a\ndesign driver above":
        "≈ 600 km : COTS avec blindage\nmodeste en dessous ; au-dessus,\nle rayonnement dimensionne",
    "Orbit altitude (km)": "Altitude de l'orbite (km)",
    "Total ionising dose (krad(Si) / year)": "Dose ionisante totale (krad(Si) / an)",
    "1 mm Al shielding": "Blindage Al 1 mm",
    "2 mm Al shielding": "Blindage Al 2 mm",
    "4 mm Al shielding": "Blindage Al 4 mm",
    "§7.6.1 table range (2 mm Al)": "Plage du tableau du §7.6.1 (2 mm Al)",
    "Trapped-proton dose versus altitude and shielding (LEO–MEO)":
        "Dose due aux protons piégés selon l'altitude et le blindage (LEO–MEO)",
},
# ---------------------------------------------------------------- Ch 13
"fig_trl": {
    "Technology readiness level (TRL) ladder": "Échelle des niveaux de maturité technologique (TRL)",
    "Basic principles observed": "Principes de base observés",
    "Technology concept formulated": "Concept technologique formulé",
    "Analytical / experimental proof of concept": "Preuve de concept analytique / expérimentale",
    "Component validation in laboratory": "Composant validé en laboratoire",
    "Component validation in relevant environment": "Composant validé en environnement représentatif",
    "System/subsystem demo in relevant environment": "Système/sous-système démontré en env. représentatif",
    "System prototype demo in space": "Prototype du système démontré dans l'espace",
    "System qualified through test and demo": "Système qualifié par essais et démonstration",
    "Flight-proven in successful mission": "Éprouvé en vol lors d'une mission réussie",
    "Research and internal R&D —\nnot selectable for flight": "Recherche et R&D interne —\nnon retenable pour le vol",
    "Ground evidence; CubeSat buses\ntypically buy COTS at TRL ≥ 6": "Preuves au sol ; les plateformes CubeSat\nachètent en général du COTS de TRL ≥ 6",
    "First in-orbit demonstration —\nthe costliest gap to cross (6 → 7)": "Première démonstration en orbite —\nl'écart le plus coûteux à franchir (6 → 7)",
    "Operational missions —\nflight heritage drives selection": "Missions opérationnelles —\nl'héritage en vol guide le choix",
},
# ---------------------------------------------------------------- Ch 12
"fig_tsiolkovsky": {
    "CubeSat deorbit / station-keeping (~100 m/s)": ("Désorbitation / maintien à poste (~100 m/s)", 0.88),
    "constellation phasing (~300 m/s)": "phasage de constellation (~300 m/s)",
    "LEO → GTO injection (~1.5 km/s)": "injection LEO → GTO (~1,5 km/s)",
    "LEO → GEO Hohmann (~3.9 km/s)": "Hohmann LEO → GEO (~3,9 km/s)",
    "Mass ratio m₀ / m_f": "Rapport de masse m₀ / m_f",
    "Tsiolkovsky — Δv vs mass ratio for selected Isp": "Tsiolkovski — Δv selon le rapport de masse, pour divers Isp",
    "Isp = 70 s (cold gas)": "Isp = 70 s (gaz froid)",
    "Isp = 220 s (monopropellant)": "Isp = 220 s (monergol)",
    "Isp = 320 s (bipropellant)": "Isp = 320 s (biergol)",
    "Isp = 1500 s (Hall thruster)": "Isp = 1500 s (propulseur à effet Hall)",
    "Isp = 2200 s (ion thruster)": "Isp = 2200 s (propulseur ionique)",
},
# ---------------------------------------------------------------- Ch 16
"fig_wbs_tree": {
    # WBS element numbers are identifiers: keep the point
    "1.0": "1.0",
    "2.0": "2.0",
    "3.0": "3.0",
    "4.0": "4.0",
    "5.0": "5.0",
    "6.0": "6.0",
    "7.0": "7.0",
    "8.0": "8.0",
    "9.0": "9.0",
    "10.0": "10.0",
    "5.1": "5.1",
    "5.2": "5.2",
    "5.3": "5.3",
    "5.4": "5.4",
    "5.5": "5.5",
    "5.6": "5.6",
    "5.7": "5.7",
    "5.8": "5.8",
    "Mission Total": "Total mission",
    "Programme\nManagement": "Gestion de\nprogramme",
    "Systems\nEngineering": "Ingénierie\nsystème",
    "Mission\nAssurance": "Assurance\nmission",
    "Spacecraft\nBus Hardware": "Matériel de\nla plateforme",
    "Integration\nand Test": "Intégration\net essais",
    "Software\n(flight + ground)": "Logiciel\n(vol + sol)",
    "Launch\nServices": "Services de\nlancement",
    "Ground\nSegment": "Segment\nsol",
    "Structure and\nmechanisms": ("Structure et\nmécanismes", 0.9),
    "EPS (array,\nbattery, board)": ("EPS (générateur,\nbatterie, carte)", 0.8),
    "AOCS (sensors\n+ actuators)": ("SCAO (capteurs\n+ actionneurs)", 0.82),
    "TT&C (radio\n+ antenna)": "TT&C (radio\n+ antenne)",
    "OBC and data\nhandling": ("OBC et gestion\ndes données", 0.85),
    "Thermal\ncontrol": "Contrôle\nthermique",
    "Propulsion\n(if applicable)": ("Propulsion\n(le cas échéant)", 0.82),
    "Harness and\ncabling": "Harnais et\ncâblage",
    "Level 2 of 5.0": "Niveau 2 de 5.0",
    "Management (1–3)": "Management (1–3)",
    "Space segment (4–6)": "Segment spatial (4–6)",
    "Software (7)": "Logiciel (7)",
    "Launch (8)": "Lancement (8)",
    "Ground and operations (9–10)": "Sol et opérations (9–10)",
    "Percentages are a typical starting allocation for a university or small-company CubeSat;\n"
    "4.0, 6.0 and 7.0 also have Level-2 elements (not shown).":
        "Pourcentages : allocation de départ typique pour un CubeSat universitaire ou de petite entreprise ;\n"
        "4.0, 6.0 et 7.0 ont aussi des éléments de niveau 2 (non représentés).",
},
})
