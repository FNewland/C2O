# Partie 2 — Opérations d'un CubeSat {: .part-divider}

Cette partie du manuel constitue le volume « opérations » du programme
SpaceCDF. Elle est le complément pratique des séances 5.1 – 5.4
(les notions de concepts d'opérations de la partie 1).

La partie 2 s'appuie sur un unique satellite de référence fictif —
**EOSAT-1**, un CubeSat de 6 unités sur une orbite héliosynchrone à 513 km —
que la promotion SpaceCDF pilote à l'aide d'un simulateur associé.

Comment lire la partie 2 :

- **Les chapitres 5 – 7** définissent la salle de contrôle : les neuf
  postes d'opérateur, les consoles qu'ils occupent, les outils et les
  types de commandes qu'ils utilisent, et la discipline de boucle vocale
  qui assure la cohésion de l'équipe.
- **Les chapitres 8 – 11** décrivent les opérations de passage de bout en bout :
  passages nominaux, LEOP, recette en orbite, et les schémas de reprise
  que suivent les opérateurs lorsqu'une anomalie se déclenche.
- **Le chapitre 12** traite des opérations de contingence : l'état d'esprit et
  le cadre de décision permettant de réagir à l'imprévu, les classes de
  contingence et l'arbre de décision du traitement des anomalies.
- **Les chapitres 13 – 15** constituent la documentation de référence de travail :
  calculs de l'opérateur, catalogue des procédures et cartes de référence
  télémesure / FDIR / surveillance.

Le **cahier d'exercices du cours SpaceCDF** qui l'accompagne comporte une fiche
par chapitre, ainsi que des listes de vérification « confirmer et noter » pour
chaque procédure, des fiches d'anomalie et des formulaires de passation.

---

# Chapitre 5 — Vue d'ensemble des opérations


## 5.1 De la conception aux opérations

Les ingénieurs qui spécifient un satellite ne sont pas, en général,
ceux qui le pilotent. La discipline est différente. La conception est une
activité individuelle ou en petit groupe, consignée par écrit et vérifiée par
rapport aux exigences avant que quoi que ce soit ne bouge. **Les opérations
sont une performance d'équipe** — répétée, sous contrainte de temps, coordonnée
à la voix et sans indulgence pour l'ambiguïté. Le satellite ne fait pas de pause
pour laisser l'opérateur réfléchir.

Cette partie couvre la **transition de la conception aux opérations** : comment
un CubeSat 6U (la mission de référence EOSAT-1, §5.7) est piloté par
une équipe de salle de contrôle depuis la séparation du lanceur jusqu'aux
opérations de prise de vue de routine, les procédures que l'équipe exécute
passage après passage, les contingences auxquelles elle se prépare, et les
calculs que tout opérateur en console doit savoir faire de tête ou au dos
de la main courante.

Le chapitre s'appuie sur des normes publiées d'opérabilité et de procédures :
ECSS-E-ST-70-11C *Space segment operability*,
ECSS-E-ST-70-32C *Test and operations procedures*, les *Space Flight
Program and Project Management Requirements* de la NASA ([NPR 7120.5F](https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7120&s=5F)) et le modèle de référence
des opérations de mission du CCSDS (*Mission Operations Reference Model*, CCSDS 520.0-G-4).
Les références aux services PUS suivent l'ECSS-E-ST-70-41C et le livre vert
PUS du CCSDS (660.0-G-3).

## 5.2 L'arc d'une mission opérationnelle

La vie opérationnelle d'un satellite se découpe nettement en phases. Le
mandat de l'opérateur, les procédures disponibles, la cadence de
commande et les effectifs de l'équipe diffèrent tous d'une phase à l'autre.

Tableau 5.1 — Phases opérationnelles de la mission, avec leur durée, leur périmètre et les familles de procédures associées.

| Phase | Durée typique | Rôle des opérations | Famille de procédures |
|---|---|---|---|
| Phase 3 — Chargeur d'amorçage / premier contact | heures | Acquérir la liaison ; amorcer le logiciel applicatif ; synchroniser le temps ; premier bilan de santé | LEOP-001..002, LEOP-006 |
| Phase 4 — LEOP | 0–72 h | Mise sous tension séquentielle ; déploiement de l'antenne ; amortissement des vitesses angulaires ; acquisition du Soleil | LEOP-003..007 |
| Phase 5 — Recette en orbite | 1–4 semaines | Vérification des sous-systèmes ; étalonnage des capteurs ; mise sous tension de la charge utile ; première lumière | COM-001..013 |
| Phase 6 — Opérations nominales | durée de vie de la mission | Prise de vue de routine, liaison descendante, gestion du moment cinétique, transitions d'éclipse, maintien de l'orbite | NOM-001..013 |
| (toute phase) — Contingence | minutes à heures | Une règle FDIR se déclenche ; l'opérateur réagit | CTG-001..030 |
| (toute phase) — Urgence | heures | Passage en mode survie ; reprise après défaillance de plusieurs systèmes | EMG-001..006 |
| Retrait de service (exécuté en phase 6, pas une phase propre) | des semaines de poussées, puis 1,5 à 4,2 ans de décroissance | Poussée d'abaissement du périgée à 390 km, passivation, puis décroissance orbitale | NOM-014 |

La suite de la partie 2 décrit la séquence nominale de chaque phase, les
contingences courantes et les vérifications de l'opérateur pour chacune. Le
simulateur qui accompagne ce contenu est cité lorsque c'est utile,
mais le contenu du manuel porte sur **ce qu'un opérateur doit savoir**, et non
sur ce que fait un simulateur particulier.

## 5.3 Ce qu'un opérateur doit savoir faire

Un opérateur qui a étudié cette partie doit être capable de :

1. Occuper n'importe lequel des **neuf postes de la salle de contrôle** (chapitre 6),
   lire sa mosaïque de télémesure, reconnaître les tendances hors nominal
   et exécuter les commandes de son poste avec l'autorisation du FD.
2. **Conduire un cycle de planification de bout en bout** (chapitre 7) : choisir
   des cibles de prise de vue, construire une séquence d'activités, lancer le
   détecteur de conflits, envoyer le plan à bord et vérifier son exécution.
3. **Exécuter une procédure nominale** comme opérateur principal (chapitre 8) :
   tenir le fichier de procédure, annoncer chaque étape sur la boucle vocale,
   demander le GO du FD avant chaque action commandée.
4. **Exécuter une procédure de contingence ou d'urgence** en réponse à
   un déclenchement FDIR (chapitre 12), et rédiger proprement la fiche
   d'anomalie qui en résulte.
5. **Critiquer le quart d'une autre équipe** à l'aide de la grille d'observation
   à quatre axes (annexe de cette partie), avec horodatages et recommandations
   précises.
6. **Effectuer les vérifications de l'opérateur** qu'exige chaque quart
   (chapitre 13) : horaires de passage, prévision du SoC en sortie d'éclipse,
   RSS du bilan de pointage, analyse des lacunes de la TM différée, contrôle de
   vraisemblance de la marge de liaison.

## 5.4 Les neuf postes de la salle de contrôle

Une véritable salle de contrôle des opérations compte entre 6 et 12 postes
selon la taille et la phase de la mission. Les opérations d'EOSAT-1 adoptent la
**structure à neuf postes** suivante, qui reflète les effectifs des salles de
contrôle de mission industrielles pour une petite mission d'observation de la Terre
et ce que mettent en œuvre les bancs de formation aux opérations.

Tableau 5.2 — Les neuf postes d'opérateur de la salle de contrôle, avec leur mandat et leur sous-système principal.

| # | Poste | Mandat (en une phrase) | Sous-système principal |
|---|----------|------------------------|-------------------------|
| 1 | Directeur de vol (FD) | Seule autorité sur la boucle ; donne chaque GO ; ne commande pas. | Tous — conscience de la situation, autorité de décision |
| 2 | Contrôleur satellite / FDIR et systèmes (SPACON) | Pilote l'exécution des procédures ; surveille la FDIR ; évalue les anomalies. | OBDH, règles FDIR, panneau des procédures |
| 3 | Ingénieur SCAO | Détermination et contrôle d'attitude ; attitude pour l'exécution des manœuvres. | Roues de réaction, deux senseurs stellaires, gyros, magnétomètre, magnétocoupleurs |
| 4 | Ingénieur EPS | Batterie, générateurs solaires, matrice de commutation des lignes d'alimentation, délestage. | Tension du bus, SoC, courant par ligne, régulateur |
| 5 | Ingénieur thermique | Commande des réchauffeurs, performances des radiateurs, zones charge utile/FPA. | Zones, rapport cyclique des réchauffeurs, refroidisseur du FPA |
| 6 | Ingénieur TT&C / communications | Liaison radio avec le sol ; transpondeur, codage, débit. | Émission, marge de liaison, TEB, compteur de trames |
| 7 | Ingénieur opérations charge utile | Instrument scientifique ; acquisition, stockage et file de liaison descendante des images. | Imageur, FPA, mémoire de masse, qualité d'image |
| 8 | Dynamique du vol (FDS) / analyste orbite | Restitution d'orbite, prévision des passages, planification des manœuvres, criblage des conjonctions. | GPS, propagateur d'orbite, planning des contacts |
| 9 | Ingénieur segment sol / contrôleur réseau | Antenne sol, bande de base, vue d'état radio (RF), réseau. | Pointage de l'antenne, santé de la bande de base, chaîne RF |
| — | Responsable de mission / interface client | Communication externe, comptes rendus au client, décisions au niveau mission. | (hors console ; zone d'observation) |

> **La liste des postes du simulateur n'est pas la même.** Le MCS
> définit **sept** postes de console dans `mcs/positions.yaml` :
> `flight_director`, `fdir_systems` (« FDIR / Systèmes » [FDIR / Systems]), `eps_tcs`
> (« Puissance et thermique » [Power & Thermal]), `aocs` (« Dynamique du vol » [Flight Dynamics]), `ttc`,
> `payload_ops` et `propulsion`. La salle à neuf postes ci-dessus s'y
> rattache ainsi : l'EPS et le thermique occupent tous deux `eps_tcs` ; l'ingénieur
> SCAO et l'analyste FDS travaillent tous deux depuis `aocs` ; le segment
> sol et le responsable de mission n'ont aucun poste MCS. Le seul
> poste que le tableau de service de la salle doit ajouter et que le tableau
> ci-dessus ne nomme pas est l'**ingénieur propulsion** — EOSAT-1 emporte un module
> de monergol vert de 1U (66,9 m/s au total), et `propulsion` est le
> seul poste dont les `allowed_func_ids` incluent les commandes de poussée
> (fonctions S8 108–118). Dans une répétition à neuf places, l'opérateur FDS
> cumule normalement la fonction propulsion, car la FDS produit le
> vecteur de manœuvre que la propulsion exécute.

Dans de nombreuses salles de contrôle (y compris le banc de référence EOSAT-1),
les postes d'ingénieur EPS et d'ingénieur thermique partagent une même image de
console MCS — le poste `eps_tcs`, avec les onglets EPS+TCS ; ils sont assis
**côte à côte**, de sorte que l'autorité de commande passe de l'un à l'autre grâce à
la proximité physique et à une seule annonce sur la boucle vocale.

Le poste FDS travaille depuis la console MCS `aocs` (intitulée
*Dynamique du vol*) ainsi que depuis un poste de travail extérieur au banc MCS : il
ingère la télémesure GPS, propage l'orbite, produit
le planning des passages que suit le reste de l'équipe et calcule
les vecteurs de manœuvre si nécessaire. Le poste `aocs` comporte aussi un
onglet PROP en **lecture seule** : la dynamique du vol peut suivre une poussée mais
ne peut pas en commander une.

L'ingénieur segment sol travaille depuis un poste de travail secondaire et
est le **seul opérateur qui surveille en routine la chaîne RF de la station sol
de bout en bout** — pointage de l'antenne, santé de la bande de base et
vue d'état radio (présence de porteuse, état de verrouillage, balayage,
estimation Doppler). Il est la voix du réseau sol sur
la boucle.

Le responsable de mission est *hors console* : il s'assoit au fond de la
salle, sur la boucle mais sans commander, et a la charge du rapport d'état
destiné au client et des décisions externes au niveau de la mission.

Le chapitre 6 décrit chaque poste en détail : le mandat, la
console, la télémesure à surveiller, les commandes habituellement envoyées,
le contenu de la passation, les dépendances entre postes et les
modes de défaillance courants.

## 5.5 Fonctionnement de l'équipe : passages, quarts et boucle vocale

Les opérations s'organisent autour des **passages** : les périodes de l'orbite
pendant lesquelles le satellite est en contact avec une station sol. L'orbite
de référence d'EOSAT-1 (héliosynchrone, 513 km, 97,39°, heure locale du nœud
ascendant 10 h 00) produit des passages d'au plus 9 minutes environ
(7,5 minutes en moyenne) au-dessus des cinq stations polaires du référentiel
pédagogique (Iqaluit, Troll, Svalbard, Inuvik et O'Higgins), avec
environ 8 à 13 contacts par station sol et par jour selon la
latitude de la station.

Les quarts s'organisent autour du planning des contacts. Dans l'industrie, un quart
LEOP fonctionne **en continu (24/7) en trois quarts de huit heures** jusqu'à la fin de
la phase 4 ; la recette en orbite se déroule généralement en **journées de 16 heures
avec deux quarts** ; les opérations nominales fonctionnent habituellement en **8/5 avec
automatisation** pour couvrir les autres passages de la journée. La discipline de
passage est la même dans tous ces cas : les opérateurs sont à leur console, sur
la boucle vocale, prêts à commander, de l'AOS moins 5 minutes jusqu'à
la LOS plus 5 minutes.

Entre deux passages, l'équipe **débriefe** le passage qui vient de s'achever
(débriefing à chaud de 5 minutes), **replanifie** le passage suivant (panneau de
planification), **lit par anticipation** le fichier de procédure de l'activité de la
phase suivante, et **se repose, s'hydrate et mange** — ces quatre activités sont
d'égale importance pour la mission au cours d'une LEOP de plusieurs jours.

La **boucle vocale** est la colonne vertébrale de la salle. Chaque poste est sur
la boucle ; chaque action commandée est couplée à la voix. La discipline sur
la boucle compte plus que toute autre compétence individuelle de l'opérateur —
les données de l'industrie attribuent ~80 % des anomalies « récupérables rendues
irrécupérables » à des défaillances de la boucle vocale, et non à des erreurs de
lecture de la télémesure. Le chapitre 9 traite en détail de la discipline de boucle.

## 5.6 L'agencement physique de la salle de contrôle

La salle des opérations est agencée en **fer à cheval
de consoles face à un mur d'écrans central**. Le siège du directeur de vol
se trouve au sommet du fer à cheval ; les huit consoles d'opérateur
l'encadrent ; le responsable de mission et le directeur de mission s'assoient à
l'extrémité ouverte du fer à cheval, derrière le FD. Le matériel de boucle vocale
(casques à téléphone logiciel) se trouve à chaque place. Le mur d'écrans affiche la
carte principale des stations sol et le compte à rebours AOS/LOS.

<svg viewBox="0 0 760 420" xmlns="http://www.w3.org/2000/svg" style="max-width:720px; font-family:'Calibri','Helvetica Neue',Arial,sans-serif; font-size:11px;">
  <!-- Display wall -->
  <rect x="170" y="20" width="420" height="50" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="380" y="42" text-anchor="middle" fill="#92400e" font-weight="bold">Mur d'écrans</text>
  <text x="380" y="58" text-anchor="middle" fill="#92400e" font-size="10">Trace au sol · compte à rebours AOS/LOS · bandeau d'alerte principal</text>

  <!-- Horseshoe outline -->
  <path d="M 130 120 Q 130 250 200 320 L 560 320 Q 630 250 630 120 Z" fill="none" stroke="#80746c" stroke-width="1.2" stroke-dasharray="4 4"/>

  <!-- FD seat at apex -->
  <rect x="320" y="100" width="120" height="48" rx="6" fill="#8f001a" stroke="#5e0011" stroke-width="2"/>
  <text x="380" y="122" text-anchor="middle" fill="white" font-weight="bold">Directeur de vol</text>
  <text x="380" y="138" text-anchor="middle" fill="white" font-size="10">(siège du FD)</text>

  <!-- Inner ring: 6 console positions -->
  <g font-size="10.5">
    <rect x="170" y="170" width="90" height="40" rx="4" fill="#e0e7ff" stroke="#4338ca"/>
    <text x="215" y="195" text-anchor="middle" fill="#1e1b4b" font-weight="bold">SPACON</text>
    <rect x="270" y="170" width="80" height="40" rx="4" fill="#e0e7ff" stroke="#4338ca"/>
    <text x="310" y="195" text-anchor="middle" fill="#1e1b4b" font-weight="bold">AOCS</text>
    <rect x="360" y="170" width="80" height="40" rx="4" fill="#dcfce7" stroke="#15803d"/>
    <text x="400" y="195" text-anchor="middle" fill="#14532d" font-weight="bold">EPS</text>
    <rect x="450" y="170" width="80" height="40" rx="4" fill="#dcfce7" stroke="#15803d"/>
    <text x="490" y="195" text-anchor="middle" fill="#14532d" font-weight="bold">Thermique</text>
    <rect x="540" y="170" width="80" height="40" rx="4" fill="#fee2e2" stroke="#b91c1c"/>
    <text x="580" y="195" text-anchor="middle" fill="#7f1d1d" font-weight="bold">TT&amp;C</text>
  </g>

  <!-- Second ring: Payload + FDS + Ground Seg -->
  <g font-size="10.5">
    <rect x="170" y="240" width="90" height="40" rx="4" fill="#fef3c7" stroke="#d97706"/>
    <text x="215" y="265" text-anchor="middle" fill="#92400e" font-weight="bold">Charge utile</text>
    <rect x="270" y="240" width="100" height="40" rx="4" fill="#cffafe" stroke="#0e7490"/>
    <text x="320" y="265" text-anchor="middle" fill="#164e63" font-weight="bold">FDS</text>
    <rect x="430" y="240" width="160" height="40" rx="4" fill="#cffafe" stroke="#0e7490"/>
    <text x="510" y="265" text-anchor="middle" fill="#164e63" font-weight="bold">Segment sol</text>
  </g>

  <!-- Back area: Mission Manager + coach -->
  <rect x="220" y="350" width="320" height="42" rx="4" fill="#f3f4f6" stroke="#6b7280" stroke-dasharray="3 3"/>
  <text x="380" y="370" text-anchor="middle" fill="#374151" font-weight="bold">Responsable de mission + directeur de mission</text>
  <text x="380" y="385" text-anchor="middle" fill="#374151" font-size="9.5">(hors console, zone d'observation au fond de la salle)</text>

  <!-- Eye-line arrows from FD to operators (showing line-of-sight requirement) -->
  <g stroke="#8f001a" stroke-width="0.7" stroke-dasharray="2 2" fill="none" opacity="0.5">
    <line x1="380" y1="148" x2="215" y2="170"/>
    <line x1="380" y1="148" x2="310" y2="170"/>
    <line x1="380" y1="148" x2="400" y2="170"/>
    <line x1="380" y1="148" x2="490" y2="170"/>
    <line x1="380" y1="148" x2="580" y2="170"/>
  </g>
  <text x="125" y="125" font-size="9" fill="#8f001a">Ligne de vue du FD</text>
</svg>

*Figure 5.1 — Agencement des consoles de la salle de contrôle. Le siège du directeur de vol occupe le sommet d'un fer à cheval et dispose d'une ligne de vue vers chaque place d'opérateur (lignes rouges tiretées). Les opérateurs sous-système (SPACON, AOCS, EPS, thermique, TT&C) forment l'anneau intérieur ; charge utile, FDS et segment sol forment l'anneau extérieur. Le responsable de mission et le directeur de mission s'assoient au fond, sur la boucle mais sans commander.*

L'agencement compte. Un étudiant qui commande depuis la place EPS doit
pouvoir **croiser le regard du FD** avant d'envoyer une commande de mise sous
tension, car le GO est donné à la voix et du regard. Un étudiant à la place
charge utile doit pouvoir **voir le compte à rebours AOS** sans se
retourner. Il ne s'agit pas d'une ergonomie arbitraire ; elle influe directement sur la
performance du quart et elle est notée sur l'axe *Occupation de l'espace*
de la fiche d'évaluation par les pairs.

## 5.7 Ce que nous pilotons — EOSAT-1 en 600 mots

EOSAT-1 est un **CubeSat de 6 unités** construit au laboratoire SmallSat d'uOttawa,
lancé en juin 2026 sur une orbite héliosynchrone à **513 km
d'altitude et 97,39° d'inclinaison**, avec une heure locale du nœud ascendant
de 10 h 00 ; il traverse donc l'ombre de la Terre à chaque orbite. Sa mission : la surveillance des courants océaniques le long des
côtes canadiennes à l'aide d'un imageur multispectral à quatre bandes (bandes à 443,
560, 665 et 865 nm — respectivement bleu, vert, rouge et proche infrarouge,
choisies pour maximiser la sensibilité au carbone organique
dissous et à la chlorophylle de surface).

Le satellite a une masse de **12,0 kg à sec** (12,40 kg en masse humide, avec 400 g
d'ergol). La charge électrique moyenne sur l'orbite, tous les systèmes nominaux en marche, est
de **≈ 28,8 W** ; la charge instantanée de crête pendant un passage charge utile est
plus élevée encore dès que l'imageur, le refroidisseur du FPA et l'émetteur sont allumés.
Les deux ailes déployables portent chacune 0,120 m² de cellules et ont une
puissance nominale de **70,1 W en BOL à β = 0** ; la production de crête de l'ensemble du satellite,
panneaux de structure compris, est de **88,6 W**, et la production moyenne sur l'orbite en fin de vie
est de 45,1 W à l'angle bêta le moins productif de l'année (β = −31,2°) —
soit une marge nominale de +16,3 W, ou 1,57×. Sur l'année, β reste entre
−20,8° et −31,2° ; comme l'entraînement du générateur ne suit le Soleil
qu'à cos β près, le plus grand |β| donne la plus faible production, bien
que son éclipse soit la plus courte. Le stockage est assuré par une **batterie Li-ion
de 100 Wh** (classe GomSpace NanoPower BPX, 8S-1P ; `eps.yaml`
`voltage_nom` 26,4 V, 29,2 V à 100 % de SoC, 21,5 V à 0 %). *(Ce
sont des valeurs dérivées de composants de vol : 12–18 W de réserve de puissance
moyenne sur l'orbite pour la charge utile, c'est ce que fournit un vrai 6U avec ailes déployables. Ne vous
attendez pas aux +40 W de marge qu'afficherait un bilan mal dimensionné.)*

Le satellite emporte **deux émetteurs** : une chaîne principale en bande S
(antenne patch déployable, liaison descendante à 2200 MHz / liaison montante à 2025 MHz) pour
la commande et la télémesure à plein débit, et une **balise UHF séparée
à antenne fouet** à 437,5 MHz, 1 W, qui transporte la HK SID 11 et rien
d'autre. La distinction compte en opérations : éteindre l'amplificateur de puissance
bande S interrompt toute la télémesure en bande S, tandis que la balise continue
d'émettre. C'est une seconde radio, pas un mode de la première.

Le contrôle d'attitude repose sur 4 roues en pyramide, avec des magnétocoupleurs pour la
gestion du moment cinétique (le pointage FINE est assuré sur trois roues si l'une
est perdue, signalé comme dégradé). Les capteurs sont **deux senseurs stellaires,
ST1 et ST2** (détermination d'attitude principale ; la tête active est
sélectionnée avec `ST_SELECT`, fonction S8 6), des senseurs solaires grossiers sur les
six faces (pour le mode survie et l'acquisition du Soleil), un magnétomètre (sans rechange),
**trois gyros monoaxes sans unité redondante** et un récepteur
GPS (restitution d'orbite). Les performances de pointage se lisent sur
`aocs.total_pointing_err_3sig` (0x02AA, somme quadratique (RSS) des erreurs de connaissance et
de contrôle) et sont surveillées sur `aocs.att_error` (0x0217), dont les
bandes d'alarme sont ±1.0° en jaune et ±2.0° en rouge ; les performances mesurées en FINE_POINT
sont de 0,021° en moyenne sur quatre roues et de 0,019° sur un
ensemble dégradé à trois roues.

Le contrôle d'orbite est assuré par un **module de monergol vert de 1U**, 400 g
d'ergol, 66,9 m/s de delta-V total, utilisé pour l'évitement de débris, une
compensation limitée de la traînée et la poussée de retrait de service en fin de
vie. Avec un coefficient balistique de 77,9 kg/m², la décroissance naturelle
depuis 513 km prend 5,0 ans à activité solaire moyenne et 14,2 ans au minimum
solaire, ce qui ne respecte pas la règle de retrait de service en 5 ans après la
mission. La mission se termine donc par NOM-014 : une poussée rétrograde
d'abaissement du périgée de 34,3 m/s, réalisée en six poussées de 5,72 m/s,
amène le périgée de 513 km à 390 km ; la rentrée prend ensuite 1,5 an à activité
moyenne et 4,2 ans au minimum solaire. Le bilan de ΔV (`prop.yaml`) demande
64,1 m/s — 15,1 m/s de compensation de la traînée sur deux ans à 513 km, 6,1 m/s
de travail d'orbite et d'évitement de collision, les 34,3 m/s du retrait de
service et 8,6 m/s de marge — pour 66,9 m/s disponibles (+4,4 % ; +2,6 % par
rapport à la valeur intégrée en mode « blowdown » de 65,8 m/s). À partir de la
mi-mission, au moins 38 m/s restent réservés au retrait de service.

Ces durées de décroissance proviennent de l'intégration de traînée du projet
avec l'atmosphère exponentielle CIRA-72, le minimum solaire étant modélisé à
0,35 × cette table. Avec NRLMSIS 2.1 et un minimum solaire maintenu pendant des
années, la décroissance depuis 390 km prend 7,2 ans. La vérification croisée
consignée dans `prop.yaml` utilise NRLMSIS 2.1 avec une densité moyenne globale :
F10.7 = 140 donne 4,7 ans depuis 513 km, proche des 5,0, mais un F10.7 = 70
maintenu donne 33 ans — une borne supérieure, car un minimum solaire ne dure
pas des décennies. Un périgée de 360 km et 42,8 m/s respecterait 5 ans même
sous cette borne, mais le bilan de ΔV ne boucle pas. Deux modèles
d'atmosphère respectables divergent de plusieurs années : c'est l'incertitude
qu'un plan de retrait de service doit absorber.

Le **segment sol** est un réseau polaire de cinq stations en bande S
(le référentiel pédagogique dans toute la partie 2) :

- **Iqaluit** (Nunavut, 63,75° N) : principale, propriété d'uOttawa, antenne de 9 m,
  G/T 20,0 dB/K.
- **Troll** (Antarctique, 72,01° S) : location KSAT, 7,3 m, G/T 18,5.
- **Svalbard** (78,23° N) : 11,3 m, G/T 21,5.
- **Inuvik** (68,32° N) : 13,0 m, G/T 22,0.
- **O'Higgins** (63,32° S) : 9 m, G/T 20,0.

Les cinq stations ont un masque d'élévation minimale de 5° ; la géométrie de référence
est `orbit.yaml`, complétée pour la RF par
`planning/ground_stations.yaml`.

Les opérations de la mission se découpent en **phases** :

Tableau 5.3 — Plan des phases de la mission EOSAT-1, du lancement au retrait de service, avec durées et activités.

| Phase | Nom | Durée | Activité |
|-------|------|----------|----------|
| 0 | PRE_SEPARATION | (lancement) | Sur le lanceur ; tout est éteint, aucun cycle de sous-système |
| 1 | SEPARATION_TIMER | minutes | Libération par le déployeur, vitesses résiduelles de séparation (tip-off), minuterie d'inhibition en cours |
| 2 | INITIAL_POWER_ON | minutes | Le PDM met sous tension les lignes non commutables (OBC, TTC RX) |
| 3 | BOOTLOADER_OPS | heures | Balise UHF (SID 11 uniquement), chargeur d'amorçage de l'OBC, première AOS |
| 4 | LEOP | 0–72 h | Amortissement des vitesses angulaires, déploiement de l'antenne et des ailes, mise sous tension séquentielle, HK complète |
| 5 | COMMISSIONING | 1–4 semaines | Vérifications des sous-systèmes, étalonnage, première lumière |
| 6 | NOMINAL | mission nominale | Prise de vue de routine, liaison descendante, bilans de santé |

La partie 2 traite en détail opérationnel les phases **3, 4, 5 et 6** — LEOP,
recette en orbite et opérations nominales de routine. Les phases 0–2 (lancement,
minuterie de séparation, mise sous tension initiale) se déroulent avant le premier contact
sol et sont entièrement autonomes. L'énumération ne comporte aucune phase de retrait de service :
le retrait de service en fin de vie (NOM-014) est exécuté en phase 6, ce
qu'exige le verrouillage d'armement de la propulsion. Il comprend les poussées
d'abaissement du périgée, puis la passivation (ergol épuisé, inhibition de la
propulsion verrouillée, roues arrêtées, régulateur de charge coupé, émetteurs
éteints), puis la décroissance orbitale.

Le compteur de phase est `eps.spacecraft_phase` (0x0129), transporté dans
la HK SID 4. **Les transitions de phase sont des déclarations du sol** — c'est l'équipe
de direction de la mission qui déclare la phase, avec la
télécommande `SYS_SET_MISSION_PHASE` (S8 fonction 120) ; rien à bord ne la fait avancer au-delà de 4 (LEOP).

La documentation complète du satellite de référence se trouve dans le dépôt
du simulateur, sous `configs/eosat1/manual/00..12_*.md`. Les chapitres les plus cités
à la lecture de la partie 2 sont 00 (vue d'ensemble de la mission), 07 (opérations
orbitales) et 09 (LEOP, `09_leop.md` ; la référence des commandes est
elle aussi numérotée 09).

## 5.8 Guide de lecture

La familiarisation de l'opérateur doit suivre cet ordre :

1. **Ce chapitre (5.0) en entier** — la mission, les phases, la salle de
   contrôle.
2. **Chapitre 6** — chaque poste, en détail. Lisez d'abord le poste qui vous est
   attribué ; parcourez les autres pour savoir à qui vous parlez
   sur la boucle.
3. **Chapitre 7, §§7.1–7.5** — l'interface du MCS, les panneaux du MPS, le panneau des
   procédures, le panneau FDIR.
4. **Chapitre 8** — opérations de passage : de l'ouverture NOM-001 jusqu'à la
   passation NOM-012, le déroulement de routine.
5. **Chapitre 9** — discipline de boucle vocale. À lire avant tout quart
   pendant lequel vous serez sur la boucle.
6. **Chapitres 10 et 11** — séquences LEOP et de recette en orbite,
   procédure par procédure.
7. **Chapitre 12** — opérations de contingence : le cadre de décision
   et l'arbre de décision du traitement des anomalies (§12.3). À lire avant tout quart
   susceptible de faire face à une contingence.
8. **Chapitre 13** — les calculs et vérifications de l'opérateur que vous ferez
   à chaque quart.
9. **Chapitres 14 et 15** — le catalogue des procédures et la référence
   télémesure / commandes / FDIR, conservés à la console pour consultation.
10. **§14.4 et §14.5** — les fiches de procédures de contingence et les
    fiches de procédures d'urgence. À lire avec le chapitre 12 avant tout
    quart susceptible de faire face à une contingence.
11. **la note de référence** — la note de réconciliation des sources de référence —
    à lire si votre simulateur vous donne des valeurs qui
    contredisent ce manuel.

Normes externes citées dans toute la partie 2. **Le résumé
exécutif seul** suffit en première lecture ; le vocabulaire est employé
librement tout au long du texte.

Tableau 5.4 — Normes externes d'opérabilité et de procédures citées dans toute la partie 2.

| Norme | Objet |
|---|---|
| ECSS-E-ST-70C | Le volet opérateur du contrat sol/bord |
| ECSS-E-ST-70-11C | Ce que signifie l'« opérabilité » pour le segment spatial |
| ECSS-E-ST-70-32C | La forme d'un fichier de procédure |
| ECSS-E-ST-70-41C | Norme d'utilisation des paquets (PUS) — structuration de la télémesure et de la télécommande |
| CCSDS 520.0-G-4 | Modèle de référence et vocabulaire des opérations de mission |
| CCSDS 660.0-G-3 | Livre vert PUS — notes de mise en œuvre |
| NASA NPR 7120.5F | *Space Flight Program and Project Management Requirements* |

Les URL complètes figurent dans la section Références à la fin de cette partie.

---


### 5.20 Concepts d'opérations de mission

> **Lectures attendues avant cette séance.** Manuel en libre accès *Conception concourante d'engins spatiaux* (REL), chap. 18, §§ 18.1 à 18.5 (ConOps, modes opérationnels, architecture FDIR, procédures opérationnelles, traitement des anomalies) ; ce livre, §§ 5.2 à 5.5 ; ECSS-E-ST-70-11C *Space segment operability* — §4 *General requirements* (opérabilité), §5.7 *On-board autonomy* et §5.7.5 *On-board fault management* (FDIR) (numéros de clauses de l'édition du 31 juillet 2008 ; l'édition en vigueur est la Rev.1 du 15 octobre 2025) ; NASA-HDBK-1002 *Fault Management Handbook* (Draft 2, 2 avril 2012) ; NASA *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, annexe S — *Concept of Operations Annotated Outline*.



**Prérequis :** §7.20 et REL, chap. 17 (architecture du segment sol assimilée)
**Références :** ECSS-E-ST-70-11C (*Space Segment Operability*), ECSS-E-ST-70-32C (*Procedures*), ECSS-E-ST-70-41C (*Packet Utilisation Standard*), NPR 7120.5F, NASA *Fault Management Handbook* (NASA-HDBK-1002)

---

### Objectifs d'apprentissage

À la fin de cette séance, les participants seront capables de :
1. Définir un concept d'opérations (ConOps) avec ses modes opérationnels et ses transitions
2. Concevoir une architecture FDIR (détection, isolation et reprise des défaillances)
3. Rédiger des procédures opérationnelles pour les opérations de routine et de contingence
4. Décrire le processus de traitement des anomalies et ses niveaux d'escalade
5. Planifier les modes opérationnels du satellite et leurs critères d'entrée et de sortie

---

### 1. Concept d'opérations (ConOps)
Le ConOps fait le pont entre la conception technique et la réalité opérationnelle. Il décrit COMMENT le système sera utilisé, et pas seulement CE QU'il peut faire.

*[Source : [ECSS-E-ST-70-11C](https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/) (*Space Segment Operability*) ; IEEE 1362 (*Concept of Operations Document*)]*

#### Structure d'un ConOps

Un document ConOps complet couvre :

1. **Vue d'ensemble de la mission** -- objectifs, parties prenantes, critères de succès
2. **Description du système** -- segment spatial, segment sol, segment utilisateur
3. **Scénarios opérationnels** -- opérations nominales, opérations de contingence
4. **Modes opérationnels** -- définition, transitions, contraintes
5. **Gestion des ressources** -- bilans de puissance, de données et d'ergols dans le temps
6. **Plan de communication** -- planning des contacts, flux de données, exigences de latence
7. **Plan d'effectifs** -- personnel, quarts, besoins de formation
8. **Maintenance et logistique** -- mises à jour logicielles, maintenance des équipements sol

#### Modes opérationnels

Tout satellite possède un ensemble défini de modes opérationnels. Chaque mode précise quels sous-systèmes sont actifs, la consommation électrique et les débits.

Tableau 5.5 — Modes opérationnels du satellite avec puissance consommée, débit, durée et conditions d'entrée.

| Mode | Description | Puissance (W) | Débit | Durée typique | Condition d'entrée |
|------|------------|-----------|-----------|-----------------|----------------|
| **Survie** | Fonctionnalités minimales ; survie uniquement | 5-10 | Balise uniquement (1 bit/s) | Jusqu'à l'intervention du sol | Détection autonome d'un défaut |
| **Amortissement (detumbling)** | Arrêter la rotation après le déploiement | 8-12 | HK uniquement (100 bit/s) | Minutes à heures | Après la séparation ; vitesse angulaire élevée |
| **Attente** | Pointage solaire ; tous les sous-systèmes prêts | 12-18 | Télémesure HK (1 kbit/s) | Entre les activités | Après l'amortissement ; périodes d'inactivité |
| **Science** | Charge utile en fonctionnement ; attitude contrôlée | 25-40 | Données scientifiques (variable) | Selon la cible | Programmé ; attitude atteinte |
| **Liaison descendante** | Transfert de données à haut débit vers le sol | 20-30 | Plein débit (2-10 Mbit/s) | Pendant le contact avec la station sol | Station sol en visibilité ; liaison établie |
| **Manœuvre** | Correction d'orbite ou désaturation | 15-25 | HK uniquement | Minutes | Programmé ; contraintes respectées |
| **Éclipse** | Opérations réduites pendant l'éclipse | 8-15 | HK uniquement (100 bit/s) | ~35 min (LEO) | Soleil hors du champ |

#### Machine à états des transitions de mode

![Machine à états des transitions de mode du satellite, avec les états nominaux (vert), d'attente (orange) et d'anomalie (rouge) et les déclencheurs étiquetés qui font passer le satellite de l'un à l'autre.](../assets/figures/fig_mode_transition_state_machine.svg)

*Machine à états des transitions de mode du satellite, avec les états nominaux (vert), d'attente (orange) et d'anomalie (rouge) et les déclencheurs étiquetés qui font passer le satellite de l'un à l'autre.*

#### Exemple de mission réelle : les opérations de PROBA-2

PROBA-2 de l'ESA (lancé en 2009, toujours opérationnel en 2026) illustre des opérations matures de classe CubeSat :
- **5 modes opérationnels :** attente, science, manœuvre, survie, arrêt
- **Opérations autonomes :** 95 % des activités de routine automatisées grâce à la chronologie bord
- **Contacts sol :** 4-6 passages par jour via la station ESA de Redu (bande S)
- **Taux d'anomalies :** ~2-3 par an nécessitant une intervention du sol (après la recette en orbite initiale)
- **Leçon clé :** investir dans l'autonomie bord réduit considérablement le coût des opérations

*[Source : ESA PROBA-2 Operations Team, « PROBA-2: Over a Decade of Operations », SpaceOps 2020]*

---

### 2. Architecture FDIR
La FDIR (détection, isolation et reprise des défaillances) est la capacité autonome du satellite à détecter des défaillances, à déterminer quel composant est défaillant et à prendre des mesures correctives -- le tout sans intervention du sol.

*[Source : NASA *Fault Management Handbook* (NASA-HDBK-1002) ; [ECSS-E-ST-70-11C](https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/) section 5.3]*
*[URL : [https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002](https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002)]*

#### Pourquoi la FDIR est essentielle pour les CubeSats

- **Contacts sol limités :** les CubeSats en LEO sont hors de visibilité ~85 % du temps
- **Aucune intervention humaine à bord :** contrairement à l'ISS, aucun astronaute ne peut « réparer » les problèmes
- **Contraintes thermiques :** un mode survie doit maintenir les limites thermiques en quelques minutes
- **Contraintes de puissance :** sans délestage, la batterie peut se décharger complètement en une seule éclipse

#### Hiérarchie FDIR (niveaux)

Tableau 5.6 — Hiérarchie FDIR à cinq niveaux, des chiens de garde matériels à la reprise commandée par le sol.

| Niveau | Détection | Réponse | Latence | Exemple |
|-------|-----------|----------|---------|---------|
| **0 -- Matériel** | Chien de garde intégré | Réinitialisation du composant | Millisecondes | Temporisateur chien de garde du processeur |
| **1 -- Équipement** | Surveillance au niveau de l'équipement | Reconfiguration de l'équipement | Secondes | Disjonction sur surintensité de l'EPS |
| **2 -- Sous-système** | Bilan de santé du sous-système | Mode de repli du sous-système | Secondes à minutes | Basculement sur le senseur stellaire de secours |
| **3 -- Système** | Détection d'anomalie au niveau système | Changement de mode (p. ex. passage en survie) | Minutes | Transition en mode survie |
| **4 -- Sol** | Diagnostic avec intervention humaine | Reprise par commande sol | Heures à jours | Investigation d'anomalie + correctif |

#### Machine à états FDIR

![Machine à états FDIR : NORMAL → MONITOR → DETECT → ISOLATE → RECOVER → EVALUATE, avec les niveaux de défaut qui déclenchent chaque transition.](../assets/figures/fig_fdir_state_machine.svg)

*Machine à états FDIR : NORMAL → MONITOR → DETECT → ISOLATE → RECOVER → EVALUATE, avec les niveaux de défaut qui déclenchent chaque transition (la même machine à états sert de référence opérationnelle au §15.4).*

#### Règles FDIR courantes sur les CubeSats

Tableau 5.7 — Règles FDIR courantes sur les CubeSats, avec méthode de détection, seuil et réponse autonome.

| Défaut | Méthode de détection | Seuil | Réponse |
|-------|-----------------|-----------|----------|
| Blocage du processeur | Temporisateur chien de garde | Aucun signal de vie pendant 60 s | Réinitialisation matérielle (niveau 0) |
| Sous-tension batterie | Surveillance de tension de l'EPS | V_bat < 6,0 V | Délestage ; passage en mode survie |
| Surchauffe de la batterie | Capteur de température | T_bat > 45 °C | Désactiver la charge ; réduire les charges électriques |
| Perte d'attitude | Aucune solution d'attitude pendant 5 min | Expiration de l'indicateur de santé du SCAO | Passage en mode amortissement |
| Perte de communication | Aucune liaison montante pendant 48 h | Sur temporisation | Réinitialiser le TTC ; revenir en mode balise |
| Corruption mémoire | Compteur d'erreurs EDAC | > 10 erreurs non corrigibles/h | Nettoyage mémoire ; redémarrage sur la copie de secours |
| Anomalie de courant du générateur solaire | Capteur de courant | I_SA < valeur attendue − 30 % | Vérifier l'attitude ; passage en attente |
| Survitesse d'une roue de réaction | Surveillance de la vitesse des roues | Omega > 5000 tr/min | Réduire le moment cinétique ; désaturation |

#### Principes de conception clés

1. **Le mode survie doit toujours fonctionner** -- c'est le dernier recours ; il doit être testé de manière exhaustive
2. **D'abord rester opérationnel, puis se mettre en sécurité** -- tenter de poursuivre la mission avant d'abandonner
3. **Aucun défaut unique ne doit entraîner la perte de la mission** -- recouper avec l'AMDEC (FMECA)
4. **Capacité de forçage depuis le sol** -- toute action autonome doit pouvoir être commandée depuis le sol
5. **Journalisation** -- enregistrer tous les événements de défaut en mémoire non volatile pour analyse ultérieure

---

### 3. Procédures opérationnelles
*[Source : [ECSS-E-ST-70-32C](https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedures/) (*Procedure Definition Language*) ; ECSS-E-ST-70-01C section 5.6]*

#### Types de procédures

Tableau 5.8 — Quatre types de procédures, distingués par leur objet, leur mode d'exécution et un exemple.

| Type | Objet | Exécution | Exemple |
|------|---------|-----------|---------|
| **Nominale** | Opérations programmées de routine | Automatisée (chronologie) ou manuelle | Séquence d'observation scientifique |
| **Contingence** | Réponse à des types d'anomalies connus | Semi-automatisée ; décision de l'opérateur | Reprise après passage en mode survie |
| **Urgence** | Réponse à des événements inattendus critiques | Manuelle ; décision en temps réel | Reprise après perte de communication |
| **Maintenance** | Étalonnage ou mises à jour périodiques | Manuelle programmée | Étalonnage du magnétomètre |

#### Structure d'une procédure (ECSS-E-ST-70-32C)

Chaque procédure comporte :
1. **Identifiant** -- numéro de procédure unique (p. ex. NOM-001)
2. **Objet** -- ce que la procédure accomplit
3. **Préconditions** -- état du système requis avant le démarrage
4. **Étapes** -- liste ordonnée d'actions, de vérifications et de décisions
5. **Résultats attendus** -- ce qui doit se produire à chaque étape
6. **Actions de reprise** -- que faire si les résultats attendus ne sont pas observés
7. **Postconditions** -- état du système après un déroulement réussi

#### Exemple : procédure d'observation scientifique

```
Procédure : NOM-SCI-001 « Acquisition d'une cible d'observation de la Terre »
Préconditions : mode = attente, SoC batterie > 60%, cible dans le FOV sous 10 min

Étape 1 : vérifier que le mode ADCS = pointage fin
  Attendu : état ADCS = FINE, erreur de pointage < 0.1 deg
  Sinon : attendre 60 s, réessayer. Toujours pas atteint -> ABORT, rester en attente

Étape 2 : commander la mise sous tension (ON) de la charge utile
  Attendu : la HK charge utile indique alimentation = ON sous 5 s
  Sinon : renvoyer la commande d'alimentation. Après 3 échecs -> ABORT, consigner une anomalie

Étape 3 : attendre la stabilisation thermique de la charge utile (90 s)
  Attendu : température de la charge utile dans sa plage opérationnelle

Étape 4 : commander la charge utile en mode prise de vue
  Attendu : état charge utile = IMAGING, compteur de trames en progression

Étape 5 : attendre l'acquisition de la cible (heure de début prédite par le sol)
  Attendu : la prise de vue commence à l'heure prédite +/- 5 s

Étape 6 : acquérir les images pendant la durée programmée

Étape 7 : commander la charge utile en attente
  Attendu : état charge utile = STANDBY

Étape 8 : commander la mise hors tension (OFF) de la charge utile (s'il n'y a plus de cible sur cette orbite)
  Attendu : la HK charge utile indique alimentation = OFF

Postconditions : mode = attente, images stockées en mémoire de masse
```

---

### 4. Processus de traitement des anomalies
*[Source : NASA-HDBK-1002 (*Fault Management Handbook*) ; procédures des commissions d'examen des anomalies (*Anomaly Review Board*) de l'ESA]*

#### Niveaux d'escalade des anomalies

Tableau 5.9 — Quatre niveaux de gravité des anomalies, avec délai de réponse, autorité et exemple de déclencheur.

| Niveau | Gravité | Délai de réponse | Autorité | Exemple |
|-------|----------|--------------|-----------|---------|
| **Vert** | Information | Jour ouvré suivant | Ingénieur d'opérations | Paramètre mineur hors de la plage attendue |
| **Jaune** | Avertissement | Sous 4 heures | Opérateur principal | Performances d'un sous-système dégradées |
| **Orange** | Grave | Sous 1 heure | Directeur de vol | Changement de mode nécessaire ; impact sur la mission |
| **Rouge** | Critique | Immédiat | Chef de projet + FD | Menace pour la mission ; passage en mode survie |

#### Déroulement du traitement des anomalies

```
1. DETECT (détecter) : alarme de télémesure ou observation d'un opérateur
2. ASSESS (évaluer) : s'agit-il d'un type d'anomalie connu ? Consulter la bibliothèque de procédures
   -> Connu : exécuter la procédure de contingence
   -> Inconnu : continuer à l'étape 3
3. DIAGNOSE (diagnostiquer) : recueillir de la télémesure complémentaire, corréler les événements, formuler une hypothèse
4. PLAN (planifier) : élaborer le plan de réponse (peut nécessiter un comité de revue d'anomalie)
5. EXECUTE (exécuter) : appliquer les commandes de reprise (vérifier chaque étape)
6. VERIFY (vérifier) : confirmer que le système est revenu dans l'état attendu
7. DOCUMENT (documenter) : consigner l'anomalie, la cause première, la réponse et le retour d'expérience
```

#### Champs du formulaire de rapport d'anomalie

Tableau 5.10 — Champs standard requis sur un formulaire écrit de rapport d'anomalie.

| Champ | Description |
|-------|------------|
| **Identifiant de l'anomalie** | Identifiant unique (p. ex. ANO-2026-042) |
| **Date/heure (UTC)** | Moment de la détection de l'anomalie |
| **Gravité** | Vert / jaune / orange / rouge |
| **Sous-système concerné** | EPS, AOCS, TTC, charge utile, etc. |
| **Observation** | Ce qui a été observé (valeurs TM, tendances) |
| **Diagnostic** | Analyse des causes profondes |
| **Mesure prise** | Commandes envoyées, procédures exécutées |
| **Résultat** | État du système après la réponse |
| **Statut** | Ouverte / résolue / en cours d'investigation |
| **Retour d'expérience** | Mesures préventives pour l'avenir |

#### Exemple de mission réelle : la défaillance des roues de réaction de Kepler

Le télescope spatial Kepler de la NASA a perdu sa roue de réaction n° 2 en juillet 2012, puis sa roue n° 4 en mai 2013. Le traitement de l'anomalie :

1. **Détection :** couple de frottement élevé dans la télémesure HK de la roue n° 2
2. **Évaluation :** signature de dégradation connue ; surveillance renforcée
3. **Défaillance :** la roue n° 2 a cessé de fonctionner. La mission s'est poursuivie sur 3 roues.
4. **Seconde défaillance :** la roue n° 4 est tombée en panne 10 mois plus tard. Il ne restait que 2 roues -- insuffisant pour le pointage fin.
5. **Reprise :** l'équipe d'ingénierie a élaboré le concept de mission « K2 », qui utilise la pression de radiation solaire comme « troisième roue virtuelle »
6. **Résultat :** K2 a fonctionné plus de 4 années supplémentaires et découvert plus de 2700 exoplanètes candidates

*Enseignement : des solutions de contournement opérationnelles créatives peuvent sauver des missions. La FDIR doit être conçue pour une dégradation progressive, et non selon le principe « mode survie ou rien ».*

*[Source : Howell et al., « The K2 Mission: Characterization and Early Results », PASP, 2014]*

---

### 5. Exercice sur les concepts d'opérations
#### Consignes

1. **Éditeur de ConOps** dans SpaceCDF :
   - Définissez tous les modes opérationnels de votre mission (au moins 5)
   - Fixez les conditions d'entrée et de sortie de chaque mode
   - Vérifiez que le bilan de puissance est bouclé dans chaque mode (en particulier survie et éclipse)

2. **Conception de la FDIR :**
   - Définissez 5 règles FDIR pour votre mission (défaut, détection, seuil, réponse)
   - Vérifiez que le bilan de puissance du mode survie est tenable indéfiniment
   - Contrôle : chaque réponse FDIR peut-elle être forcée depuis le sol ?

3. **Fiche 5.2 :**
   - Complétez le tableau des modes opérationnels
   - Rédigez une procédure nominale (observation scientifique ou liaison descendante)
   - Rédigez une procédure de contingence (reprise après mode survie)
   - Remplissez le tableau des règles FDIR

#### Pistes de discussion

- « Quelle est la pire anomalie qui pourrait toucher votre satellite ? Comment y répondriez-vous ? »
- « Si le satellite passe en mode survie le vendredi soir et que le prochain contact sol a lieu le lundi, survivra-t-il ? »
- « Quel degré d'autonomie le satellite doit-il avoir ? Où se situe la frontière entre décision à bord et décision au sol ? »

#### Tâches de la fiche 5.2

1. Complétez le tableau des modes opérationnels (5 modes ou plus, avec puissance, débit, entrée/sortie)
2. Concevez la machine à états FDIR (au moins 5 règles)
3. Rédigez une procédure nominale et une procédure de contingence
4. Remplissez le formulaire de traitement d'anomalie pour un scénario hypothétique
5. Estimez les besoins en effectifs d'opérations par phase de mission

---

### Références citées

Tableau 5.11 — Références citées pour la séance « Concepts d'opérations de mission », avec URL.

| # | Référence | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70-11C (*Space Segment Operability*) | [https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/](https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/) |
| 2 | ECSS-E-ST-70-32C (*Procedures*) | [https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/](https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/) |
| 3 | NASA *Fault Management Handbook* (NASA-HDBK-1002) | [https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002](https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002) |
| 4 | ESA PROBA-2 Operations, SpaceOps 2020 | [https://www.spaceops.org/](https://www.spaceops.org/) |
| 5 | Howell et al., K2 Mission, PASP 2014 | [https://doi.org/10.1086/676406](https://doi.org/10.1086/676406) |
| 6 | ECSS-E-ST-70-41C (*Packet Utilisation Standard*) | [https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/](https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/) |

---

### Synthèse de la séance

Tableau 5.12 — Synthèse de la séance : points clés des différents thèmes des concepts d'opérations.

| Thème | Point clé |
|-------|-------------|
| ConOps | Définit COMMENT le système est exploité : modes, transitions, plannings, effectifs |
| Modes opérationnels | Survie, amortissement, attente, science, liaison descendante, manœuvre, éclipse (ensemble minimal) |
| Transitions de mode | Définies par des conditions d'entrée et de sortie ; le mode survie est toujours accessible depuis n'importe quel mode |
| FDIR | 5 niveaux : matériel -> équipement -> sous-système -> système -> sol ; le mode survie est le dernier recours |
| Procédures | Nominale (routine), contingence (défauts connus), urgence (inconnus), maintenance |
| Traitement des anomalies | Détecter -> évaluer -> diagnostiquer -> planifier -> exécuter -> vérifier -> documenter |
| Principes de conception | Le mode survie doit toujours fonctionner ; rester opérationnel avant de se mettre en sécurité ; forçage sol toujours possible |

## 5.9 Références

- ECSS-E-ST-70-11C — *Space segment operability* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/)
- CCSDS 520.0-G-4 — *Mission Operations Reference Model* — [public.ccsds.org](https://public.ccsds.org/Pubs/520x0g4.pdf)
- NASA NPR 7120.5F — *NASA Space Flight Program and Project Management Requirements* — [nodis3.gsfc.nasa.gov](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)

# Chapitre 6 — La salle de contrôle : les neuf postes en détail

Ce chapitre est la référence de l'opérateur : une section par
poste. Pour chacun, vous trouverez le **mandat**, la **console**
(onglets visibles et place du poste dans la salle), la
**télémesure à surveiller** (principales mnémoniques et leurs limites), les **commandes
habituellement envoyées** (avec service PUS et identifiant de fonction), le
**contenu de la passation** (ce que l'opérateur sortant doit transmettre à
la relève) et les **dépendances entre postes** (à qui parler
en premier).

Les descriptions de postes valent **pour EOSAT-1 uniquement**. Dans l'industrie,
les postes réels sont plus larges et leurs frontières s'estompent — mais la
discipline *un opérateur, un mandat, un ensemble de télémesures,
un ensemble de commandes* est universelle.

> **Postes dans l'outil et hors outil.** Le MCS définit **sept**
> postes de console dans `mcs/positions.yaml` : `flight_director`,
> `fdir_systems` (la place SPACON), `eps_tcs` (« Puissance et thermique » [Power & Thermal]),
> `aocs` (« Dynamique du vol » [Flight Dynamics]), `ttc`, `payload_ops` et
> `propulsion`. Chaque poste reçoit un ensemble d'onglets filtré, une
> liste de sous-systèmes et — sauf le directeur de vol, qui dispose de
> `allowed_commands: all` — une liste d'autorisation explicite `allowed_func_ids`,
> de sorte qu'un bouton que le poste n'a pas le droit d'actionner s'affiche
> désactivé. Deux des neuf postes de la salle sont tenus *hors outil* : le
> **responsable de mission** suit le programme de la mission à l'extérieur
> (outil de suivi du programme, communications client, planning), et le poste
> **segment sol** pilote l'outil de simulation RF plutôt que le
> MCS — sa vue principale est la page radio servie par
> `smo-rfsim`, et non un onglet de poste. L'ingénieur **système de dynamique du vol**
> travaille depuis un logiciel de restitution d'orbite sur un poste de travail séparé
> *et* depuis la console `aocs`. Lorsque ce chapitre dit
> « passer à l'onglet EPS », il faut l'entendre par rapport au MCS ; lorsqu'il dit
> « le FD appelle le GO/NO-GO », il s'agit d'une action au casque — le MCS n'a ni
> bouton GO/NO-GO ni fonction de boucle vocale.

## 6.1 Directeur de vol (FD)

**Mandat.** Le FD est l'unique point d'autorité sur la boucle.
Rien ne se produit à bord du satellite sans un GO du FD. Le FD ne
**commande pas** — il autorise les autres à commander. Le FD
conduit les tours de table GO/NO-GO avant chaque action commandée. Le FD
annonce *no-go* et ramène l'équipe au dernier état vérifié
lorsque la situation n'est pas claire.

**Autorité.** La plus élevée de la salle. Seul le responsable de mission
la surpasse pour les décisions au niveau de la mission (p. ex. « faut-il tenter la
première lumière pendant ce passage alors que le senseur stellaire est dégradé ? » — le FD
recommande, le responsable de mission décide).

**Console.** Tous les onglets sont visibles — `overview`, `eps`, `aocs`, `tcs`,
`obdh`, `ttc`, `payload`, `prop`, `commanding`, `pus`,
`procedures`, `trends`, `manual` — ainsi que les quatre vues réservées au FD
déclarées dans `mcs/displays.yaml` : le *tableau de bord système* (une
vue de santé composite), le *moniteur de puissance*, le *planning des
contacts* (prochaine AOS/LOS, station, temps restant avant l'AOS), le *panneau des
procédures* (avancement, étape en cours, état) et le *panneau FDIR*
(niveau d'alerte et nombre d'alarmes). Les deux écrans du FD sont généralement
configurés ainsi : **gauche** = tableau de bord système + planning des contacts ;
**droite** = fichier de la procédure en cours, avec l'étape active
en surbrillance. Le MCS ne comporte pas de messagerie de boucle vocale ; la boucle passe par les
casques.

**Télémesure à surveiller.** Le FD n'*interprète* pas la télémesure —
c'est le travail de l'opérateur sous-système. Le FD surveille l'**état** :
la phase dans laquelle se trouve le satellite (`eps.spacecraft_phase`, 0x0129,
transporté dans la HK SID 4), le niveau d'alerte FDIR et le nombre d'alarmes
(`fdir.level` 0x0700, `fdir.active_alarms` 0x0701,
`fdir.critical_alarms` 0x0702, `fdir.high_alarms` 0x0703 — les
quatre paramètres du panneau FDIR), ainsi que l'état global OK/jaune/rouge
du tableau de bord système. Si un
poste annonce *yellow* (jaune), le FD veut le savoir dans les 5 secondes ; si
un poste annonce *red* (rouge), le FD veut le savoir sur la boucle, nominativement,
avec le paramètre et la valeur.

**Commandes habituellement envoyées.** Aucune, *par discipline* — et non du fait de
l'outil. Le poste `flight_director` est le seul à disposer de
`allowed_commands: all`, si bien que le MCS laisse le FD envoyer n'importe quoi ;
la règle selon laquelle le FD autorise plutôt qu'il ne commande est une
convention de salle que l'équipe fait respecter sur la boucle. Le MCS ne comporte aucune
seconde clé du FD. Ce que l'outil fournit, en revanche, c'est un
**indicateur de criticité sur chaque télécommande** dans
`commands/tc_catalog.yaml` — `nominal`, `caution` ou `critical`
(`OBC_REBOOT`, `OBC_SWITCH_UNIT`, `PROP_ARM`, `PROP_SET_BURN`,
`SYS_SET_MISSION_PHASE` ; l'émetteur doit appuyer sur ARMER avant ENVOYER pour celles-ci) —
et la discipline de double clé de ce cours est la suivante : rien de ce qui est marqué
*caution* ou *critical* ne quitte la console sans un GO prononcé par le FD et
collationné nominativement.

**Contenu de la passation.** Lorsqu'un FD passe le quart au FD qui le relève,
le briefing doit couvrir :

1. **La phase en cours** et le temps restant avant la limite de la phase suivante.
2. **Toutes les anomalies actives** et la procédure qui traite chacune d'elles.
3. **Les travaux en cours** — procédures commencées mais non achevées.
4. **Le prochain passage** — station, heure d'AOS, activités prévues, et
   l'opérateur responsable de chaque étape majeure.
5. **Les engagements envers le client** actifs pendant ce quart (le responsable de mission
   en fournit la liste).
6. **Tout GO accordé mais pas encore exécuté** — ce sont
   les pièges à loup.
7. **Le climat de la boucle vocale** — l'équipe est-elle soudée ? fatiguée ? distraite ?
   Le FD qui prend la relève a besoin de cette lecture humaine.

Un modèle formel de *passation de quart* NOM-012 est fourni dans le
cahier d'exercices ; le temps cible pour le remplir est de 6 minutes.

**Dépendances entre postes.** Le FD parle à tout le monde. Par
ordre de priorité pendant un passage : SPACON (qui conduit la procédure),
TT&C (santé de la liaison), l'opérateur sous-système à l'origine de l'action (celui
qui s'apprête à commander), segment sol (santé de la station), AOCS
(pointage), puis EPS/thermique/charge utile/FDS selon les besoins.

**Modes de défaillance courants (propres au FD).** Surinvestir le
poste — dire aux opérateurs quoi commander au lieu de leur demander
leur évaluation. Se taire sur la boucle pendant un moment
tendu — les opérateurs interprètent le silence comme « le FD réfléchit », et
c'est précisément pendant cette pause que surviennent les mauvaises commandes. Accorder le GO
prématurément — *toujours* interroger tous les postes concernés, même lorsque la
réponse semble évidente.

## 6.2 Contrôleur satellite / FDIR et systèmes (SPACON)

**Mandat.** Le SPACON est responsable de l'**exécution des procédures**. Il
tient le fichier de procédure, annonce chaque étape sur la boucle vocale, vérifie
la vérification et demande le GO du FD avant chaque action commandée.
Il assure aussi la veille FDIR — lorsque le panneau FDIR s'allume, le
SPACON est l'opérateur qui lit la règle, identifie la
procédure de contingence à appliquer et recommande la réponse au
FD.

**Autorité.** Autorité sur les procédures. Autorité de commande dans le cadre des
étapes autorisées, avec le GO du FD. Recommande le passage en mode survie ; seul le
FD autorise le passage en mode survie.

**Console.** Le poste `fdir_systems` : overview, obdh,
commanding, pus, procedures, trends, manual. C'est le seul
poste, en dehors du FD, à disposer de l'**onglet PUS**, et le seul
autorisé à utiliser le service 12 (surveillance bord) et le service 19 (événement-action).
Le SPACON dispose de deux écrans : **gauche** = panneau des procédures + panneau
FDIR ; **droite** = télémesure OBDH (état de l'OBC, mémoire, santé des bus,
cause de redémarrage).

**Télémesure à surveiller.** Mode de l'OBC (`obdh.mode`, 0x0300, SID 4),
image en cours d'exécution (`obdh.sw_image`, 0x0311 — 0 = chargeur d'amorçage,
1 = logiciel applicatif), OBC actif et état de l'OBC de secours (`obdh.active_obc`
0x030C, `obdh.obc_b_status` 0x030D), sélection et santé des bus
(`obdh.active_bus` 0x030E, `obdh.bus_a_status` 0x030F,
`obdh.bus_b_status` 0x0310), nombre et cause des redémarrages
(`obdh.reboot_count` 0x030A, `obdh.last_reboot_cause` 0x0316),
rapports d'événements récents (le journal des événements S5) et compteurs de commandes :
reçues `obdh.tc_rx_count` (0x0304), acceptées `obdh.tc_acc_count`
(0x0305), rejetées `obdh.tc_rej_count` (0x0306) — et, à côté,
`obdh.last_tc_error_code` (0x0315), le code d'échec S1 du
refus le plus récent. Lisez le code, pas seulement le compteur : un
compteur de rejets qui s'incrémente sans code ne vous apprend rien.
Jaune à 5 rejets sur 30 s glissantes ; rouge à 10. Notez qu'il n'existe **aucun
paramètre `fdir_table_id` ni aucune notion de table de règles** — voir la
remarque sur la commande ci-dessous.

**Commandes habituellement envoyées.** Toutes les commandes pilotées par procédure passent
*par* le SPACON. Commandes OBDH directes dont le SPACON est responsable :

- `OBC_REBOOT` (S8 func_id 52) — redémarrer l'OBC.
- `OBC_SWITCH_UNIT` (S8 func_id 53) — basculer sur l'OBC redondant.
- `OBC_BOOT_APP` (S8 func_id 55) — amorcer le logiciel applicatif depuis le
  chargeur d'amorçage.
- `SET_TIME` (S9.1) — synchroniser l'horloge de bord ;
  `OBC_GPS_TIME_SYNC` (S8 func_id 80) pour la mise à jour à partir du GPS.
- `EA_ENABLE` / `EA_DISABLE` (S19.4 / S19.5, argument `ea_id`) —
  activer ou inhiber individuellement des règles événement-action. Le simulateur
  ne permet pas de permuter des tables de règles ; l'isolation propre à la
  phase de recette en orbite s'obtient en inhibant les règles nominales tandis que les règles
  LEOP restent activées, puis en les réactivant une par une une fois
  la recette en orbite close. `EA_ADD` (S19.1) et `EA_DELETE` (S19.2)
  définissent et suppriment des règles ; `EA_REPORT_DEFS` (S19.8) en fait le vidage.
- `MON_ENABLE_DEF` / `MON_DISABLE_DEF` (S12.3 / S12.4) — les
  surveillances de limites bord, que seul ce poste peut commander.

**Contenu de la passation.** Procédure en cours (numéro d'étape,
dernière étape vérifiée), toutes les anomalies FDIR et leur état
(déclenchée/acquittée/effacée), toute règle événement-action ou surveillance
S12 désactivée manuellement (et pourquoi), tendance du taux de rejet
des commandes et dernier code d'échec de TC.

**Dépendances entre postes.** En permanence avec le FD (chaque demande
de GO). En permanence avec l'opérateur responsable de l'étape
active (p. ex. l'ingénieur SCAO si l'étape est une commande de roue). Avec le
segment sol si une TC est rejetée par le satellite — le rejet provient
parfois de la liaison montante (un bit inversé), et non du bord.

**Modes de défaillance courants.** Sauter des étapes de vérification pour tenir le
planning. Lire la procédure par anticipation et précommander
(« amorcer l'étape suivante ») — précommander sans GO explicite du FD
est une violation de procédure. Omettre de consigner une anomalie parce que
l'équipe est occupée à la traiter.

## 6.3 Ingénieur SCAO

**Mandat.** Détermination et contrôle d'attitude : le système de contrôle d'attitude
et d'orbite (SCAO ; AOCS sur la console). Lit les
capteurs d'attitude (deux senseurs stellaires, senseurs solaires grossiers, gyros,
magnétomètre, GPS), les actionneurs (quatre roues de réaction, magnétocoupleurs)
et la machine à états du SCAO. Rend compte des performances de pointage
à chaque passage. Est responsable de l'**attitude** pendant une manœuvre —
la poussée elle-même relève du poste propulsion.

**Autorité.** Autorité de commande sur le sous-système SCAO avec le GO du FD
(`allowed_func_ids` 0–15, 84–91 et 96). Recommande les transitions de mode
du SCAO ; le FD les autorise. **Aucune** commande de propulsion : les fonctions
108–118 sont délibérément absentes de la liste d'autorisation de ce poste, si bien que
tous les boutons de son onglet PROP sont désactivés.

**Console.** Le poste `aocs`, intitulé *Dynamique du vol* :
overview, aocs, prop (lecture seule), commanding, procedures, trends,
manual. L'onglet AOCS affiche les quaternions d'attitude et de référence,
les vitesses angulaires, les voies d'erreur de pointage, les vitesses et
températures des roues, la santé des capteurs, l'entier de mode du SCAO — **et, depuis
le lot 2026-08b, le mode commandé à côté du mode effectif**
(`aocs.commanded_mode` 0x0297, `aocs.mode_demoted` 0x0298), ce qui
permet de distinguer un phénomène transitoire d'un satellite qui a
discrètement abandonné son mode de mission.

**Télémesure à surveiller.**

Tableau 6.1 — Paramètres de télémesure du SCAO, avec SID et plages nominale, jaune et rouge.

| Mnémonique | ID hexa | SID | Nominal | Jaune | Rouge |
|---|---|---|---|---|---|
| `aocs.mode` | 0x020F | 2 | 4 (NOMINAL) / 5 (FINE_POINT) | 2 (DETUMBLE) / 3 (COARSE_SUN) | 0 (OFF) / 1 (SAFE_BOOT) |
| `aocs.rate_roll` / `rate_pitch` / `rate_yaw` | 0x0204–06 | 2 | < 0.01 °/s | ±0.5 | ±2.0 |
| `aocs.att_error` | 0x0217 | 2 | < 0.3° | ±1.0 | ±2.0 |
| `aocs.st1_status` / `st2_status` | 0x0240 / 0x0243 | 2 | 2 (poursuite) | 1 (amorçage) / 3 (aveuglé) | 0 (éteint) / 4 (défaillant) |
| `aocs.rw1_speed`..`rw4_speed` | 0x0207–0A | 2 | < 3000 tr/min | ±5000 | ±5500 (vitesse limite) |
| `aocs.gyro_units_on` | 0x0294 | 2 | 3 | 2 | 0–1 (aucune référence de vitesse) |
| `aocs.gps_fix` | 0x0274 | 2 | 3 (3D+vitesse) | 1–2 | 0 (aucune solution) > 10 min |
| `aocs.h_env_frac` | 0x02BA | 7 | < 50 % | > 70 % | > 90 % (désaturer immédiatement) |

(Entiers de mode selon `aocs/aocs_mode_codes.yaml`, qui est la
seule source de référence : 0 = OFF, 1 = SAFE_BOOT, 2 = DETUMBLE,
3 = COARSE_SUN, 4 = NOMINAL, 5 = FINE_POINT, 6 = SLEW, 7 = DESAT,
8 = ECLIPSE, 9 = INERTIAL. Les anciennes fiches et les anciennes éditions de ce
manuel étaient systématiquement **décalées d'une unité** — vérifiez chaque numéro de mode
que vous lisez par rapport à ce fichier. Notez aussi que le bloc de
détermination, y compris la valeur de l'enveloppe de moment cinétique, se trouve dans la HK **SID 7**,
qui est désactivée à l'amorçage et doit être activée avec `HK_ENABLE`.)

**Commandes habituellement envoyées.**

- `AOCS_SET_MODE` (S8 func_id 0) avec l'entier de mode.
- `AOCS_ENABLE_WHEEL` / `AOCS_DISABLE_WHEEL` (S8 func_id 3 / 2)
  avec `wheel_idx`.
- `RW_SET_SPEED_BIAS` (S8 func_id 8) avec `wheel_idx`, `bias_rpm`
  — le biais est **ajouté à** la vitesse actuelle ; ce n'est pas une consigne
  absolue. `AOCS_RW_RAMP_DOWN` (func_id 14) amène progressivement une roue à une
  vitesse cible ; `wheel_idx=255` désigne les quatre roues. Les vitesses de roue
  (0x0207–0x020A) sont de la **télémesure en lecture seule** : ces deux commandes
  sont le seul moyen de les modifier depuis le sol.
- `ST1_POWER` / `ST2_POWER` (S8 func_id 4 / 5) avec `on`, et
  `ST_SELECT` (S8 func_id 6) avec `unit` — 1 ou 2 — pour choisir la
  tête active. Deux senseurs stellaires, deux commandes.
- `MTQ_ENABLE` (S8 func_id 9) avec `enable`.
- `AOCS_DESATURATE` (S8 func_id 1) — exécute le déchargement du moment cinétique selon
  NOM-007. `AOCS_SET_DESAT_INHIBIT` (func_id 96) verrouille l'inhibition des déchargements.
- `AOCS_GYRO_CALIBRATION` (S8 func_id 13) — l'étalonnage du biais des gyros
  est calculé **à bord** ; il n'existe pas d'envoi d'un biais calculé au sol.
- `AOCS_EST_RESET` (S8 func_id 91) — réinitialise le MEKF ; vérifiez ensuite
  `aocs.est_source` (0x02C1) pour savoir quels capteurs il
  utilise réellement.
- `AOCS_SET_TARGET_QUAT` (func_id 86) / `AOCS_SET_TARGET_GEO`
  (func_id 87) / `AOCS_SLEW_TO` (func_id 10) — cibles de pointage.
- Les gyros sont alimentés individuellement en tant qu'équipements S2 :
  `S2_AOCS_GYROSCOPE_0/1/2` (S2.1). Il y en a trois, un
  par axe, et **aucune unité redondante**.

**Contenu de la passation.** Mode SCAO actuel et temps écoulé depuis la dernière
transition (`aocs.time_in_mode`, 0x0264), et concordance du mode
effectif avec le mode commandé ; tendance de l'erreur de pointage sur le
passage ; utilisation de l'enveloppe de moment cinétique et toute roue approchant
la vitesse limite de 5500 tr/min ; senseur stellaire sélectionné
(`aocs.st_selected`, 0x0244) et santé des deux ; fonctionnement éventuel du mode FINE
en mode dégradé sur trois roues (`aocs.fine_degraded`,
0x0299) ; toute inhibition de désaturation encore verrouillée.

**Dépendances entre postes.** Avec la FDS pour la planification des manœuvres
(la FDS produit le vecteur) et avec la propulsion, qui arme et déclenche
la poussée pendant que l'AOCS maintient l'attitude de poussée. Avec la charge utile pour le pointage
pendant la prise de vue (la charge utile demande le mode de pointage fin 60 s avant
la prise de vue). Avec le SPACON pour les règles FDIR qui concernent l'attitude (elles sont
nombreuses — saturation du moment cinétique, perte du senseur stellaire, désaccord des gyros).

**Modes de défaillance courants.** Commander NOMINAL (mode 4) avant
que l'amortissement des vitesses angulaires ait convergé — et cet amortissement est réellement lent : la
loi B-dot est pilotée par le magnétomètre, avec un dipôle saturant à
1,6 A·m² par axe, si bien qu'un culbutage de 14 °/s à la séparation met de l'ordre de
3,5 × 10³ s à s'amortir et passe sous le seuil de sortie de 0,5 °/s
vers 1166 s. Toute attente d'un amortissement rapide est erronée.
Mal lire l'entier de mode (le décalage d'une unité décrit ci-dessus se produit
précisément ici). Ne pas remarquer le moment cinétique qui s'accumule sur de nombreuses
orbites. S'attendre à ce qu'une désaturation se termine en cinq minutes : un
déchargement réaliste dure **20 à 50 minutes**, il inhibe la prise de vue pendant son exécution, il
comporte un délai d'attente et il ramène le satellite dans le mode qu'il occupait avant la désaturation.

## 6.4 Ingénieur EPS

**Mandat.** Tout ce qui touche à la puissance. Responsable de l'état de charge de la batterie,
des courants des générateurs solaires, de la tension du bus, du profil de charge électrique et de la
matrice de commutation des lignes d'alimentation. Annonce l'entrée et la sortie d'éclipse. Premier
poste à reconnaître qu'un sous-système consomme plus qu'il ne
devrait.

**Autorité.** Autorité de commande sur le sous-système d'alimentation électrique (EPS) (marche/arrêt des
lignes d'alimentation, paramètres du régulateur de charge) avec le GO du FD. Demande le
délestage (le FD l'autorise).

**Console.** Overview, EPS, TCS, commanding, procedures, trends,
manual. Image de console `eps_tcs` partagée avec l'ingénieur thermique dans le
simulateur ; dans le programme d'opérations, les deux opérateurs sont assis côte à côte et
l'ingénieur EPS se concentre sur l'onglet *EPS* tandis que l'ingénieur thermique se concentre sur
l'onglet *TCS*.

**Télémesure à surveiller.**

Tableau 6.2 — Paramètres de télémesure de l'EPS, avec SID et plages nominale, jaune et rouge.

*(La batterie est en 8S — 26,4 V nominaux, 29,2 V à 100 % de SoC et
21,5 V à 0 %. C'est élevé pour un 6U, où les bus 2S sont courants ;
c'est ce que modélise `eps.yaml` : considérez donc les valeurs de tension ci-dessous comme
propres au simulateur. Les plages sont celles livrées dans `mcs/limits.yaml`.)*

| Mnémonique | ID hexa | SID | Nominal | Jaune | Rouge |
|---|---|---|---|---|---|
| `eps.bat_soc` | 0x0101 | 1 | 70–95 % | < 25 % | < 15 % |
| `eps.bat_voltage` | 0x0100 | 1 | 26–29 V | < 23.0 | < 22.0 |
| `eps.bus_voltage` | 0x0105 | 1 | 27–29 V | < 27.0 | < 26.5 |
| `eps.sa_a_current` / `sa_b_current` | 0x0103 / 0x0104 | 1 | nominal côté éclairé | faible (éclairé) | ≈ 0 (éclairé) |
| `eps.bus_load_current` | 0x0148 | 1 | somme des neuf lignes | tendance à la hausse | disjonction d'une ligne |
| Courant par ligne (9 lignes, 0–8) | 0x0118–0x011F, 0x014B | 1 | nominal par ligne | jaune par ligne | rouge par ligne |
| `eps.bat_temp` | 0x0102 | 1 | 5–25 °C | < 2 ou > 40 | < 0 ou > 45 |
| `eps.wing_status` | 0x0144 | 1 | bits 0+1 positionnés (deux ailes déployées) | bit 4/5 (en cours) | aucun bit positionné après la LEOP |

L'**échelle FDIR de sous-tension se déclenche à 24,5 V**, au-dessus de la
plage jaune de `eps.bat_voltage` — le satellite peut donc commencer à
délester avant que la limite de tension batterie ne déclenche une alarme. Surveillez le bus.

**Commandes habituellement envoyées.**

- `EPS_POWER_ON` (S8 func_id 19) avec `line_index`.
- `EPS_POWER_OFF` (S8 func_id 20) avec `line_index`.
- `EPS_RESET_OC_FLAG` (S8 func_id 21) avec `line_index` — effacer une
  disjonction sur surintensité.
- `EPS_EMERGENCY_LOAD_SHED` (S8 func_id 25) avec `stage` (0–3).
- `EPS_SET_CHARGE_RATE` (S8 func_id 23) — forcer le courant de charge.
- `EPS_DEPLOY_WING` (S8 func_id 81) avec `wing`, et
  `EPS_WING_STATUS` (func_id 82).

Il y a **neuf lignes d'alimentation, d'indices 0 à 8** : 0 obc, 1 ttc_rx,
2 ttc_tx, 3 payload, 4 fpa_cooler, 5 htr_bat, 6 htr_obc,
7 aocs_wheels, 8 prop. Les lignes 0 et 1 ne sont pas commutables ; toute
ligne commutable est **à OFF par défaut à la mise sous tension**, d'où l'existence de
LEOP-007. L'EPS comptabilise chaque ligne d'après l'état réel du matériel
qu'elle alimente, et non d'après la position de l'interrupteur — une ligne sous tension mais
inactive ne coûte presque rien.

**Contenu de la passation.** Tendance du SoC de la batterie sur le passage ; SoC
prévu à la prochaine sortie d'éclipse ; toute ligne consommant plus que la valeur nominale ; niveau de
délestage actuellement actif (le cas échéant) ; tendance de la température de la batterie ;
courants par aile (`eps.sa_wing_py_current` 0x0146,
`eps.sa_wing_my_current` 0x0147) — une asymétrie entre les deux ailes
révèle une dégradation de panneau ou un mécanisme d'entraînement du générateur grippé
(`sada_stuck`).

**Dépendances entre postes.** Avec le thermique (les réchauffeurs sont la
plus grosse charge électrique commandée et l'EPS voit leur rapport cyclique). Avec la
charge utile (l'appel de courant à la mise sous tension de la charge utile est le plus gros pic de charge
prévisible ; coordonné avec l'EPS avant le passage). Avec la FDS (heures d'éclipse —
l'EPS les utilise pour prévoir le SoC).

**Modes de défaillance courants.** Ne pas anticiper la profondeur de l'éclipse
avant de commander une activité à forte charge. Lire un courant de charge
en jaune sans le signaler parce que « d'habitude, on tourne un peu haut ».
Oublier de réactiver la ligne après un essai manuel de délestage.

## 6.5 Ingénieur thermique

**Mandat.** Contrôle thermique. Responsable de la commande des réchauffeurs, des performances
des radiateurs, des températures de la zone charge utile (critiques pour le FPA),
des températures de la zone batterie et du refroidisseur du FPA.

**Autorité.** Autorité de commande sur le TCS (marche/arrêt des réchauffeurs,
consignes des réchauffeurs, activation du refroidisseur du FPA) avec le GO du FD.

**Console.** Overview, EPS, TCS, commanding, procedures, trends,
manual. Image `eps_tcs` partagée (voir la remarque sur l'EPS ci-dessus).

**Télémesure à surveiller.**

Tableau 6.3 — Paramètres de télémesure du contrôle thermique, avec SID et plages nominale, jaune et rouge.

| Mnémonique | ID hexa | SID | Nominal | Jaune | Rouge |
|---|---|---|---|---|---|
| `tcs.temp_battery` | 0x0407 | 3 | 5–25 °C | < 2 ou > 40 | < 0 ou > 45 |
| `tcs.temp_obc` | 0x0406 | 3 | 10–30 °C | < 5 ou > 60 | < 0 ou > 70 |
| `tcs.temp_fpa` | 0x0408 | 3 | −15 (à la consigne) | < −22 ou > 14 | < −25.5 ou > 17.5 |
| `tcs.cooler_fpa` | 0x040C | 3 | ON / OFF (commandé) | (sans objet) | OFF INATTENDU |
| `tcs.htr_duty_battery` / `htr_duty_obc` | 0x040E / 0x040F | 3 | 10–60 % | > 80 % | 100 % saturé |
| `tcs.htr_total_power` | 0x0411 | 3 | < 12 W installés | > 12.5 | > 14 |
| `tcs.fpa_cooler_floor_c` | 0x0424 | (à la demande) | sous la consigne | à moins de 2 K | au-dessus de la consigne |
| `tcs.fpa_cooler_margin_k` | 0x0425 | (à la demande) | > 2 K | 0–2 K | ≤ 0 (consigne inatteignable) |

**Commandes habituellement envoyées.**

- `HEATER_BATTERY` / `HEATER_OBC` / `HEATER_THRUSTER` (S8 func_id
  40/41/42) avec `on=0/1` — commande des réchauffeurs circuit par circuit.
- `HEATER_SET_SETPOINT` (S8 func_id 44) avec `circuit`, `on_temp`,
  `off_temp` ; `HEATER_AUTO_MODE` (func_id 45) avec `circuit`.
- `EPS_FPA_COOLER` (S8 func_id 17) ou `FPA_COOLER` (S8 func_id 43)
  avec `on=0/1`.
- `PAYLOAD_COOLER_SETPOINT` (S8 func_id 36) — l'argument `setpoint`
  est un **uint16 en centikelvins**, `raw = round((T_degC + 273.15)
  × 100)`, si bien que −15 °C donne 25815 = 0x64D7. L'enveloppe commandable est
  [−20 °C, 0 °C] ; en dehors, la TC est rejetée avec l'erreur S1.8
  0x0003, et non écrêtée silencieusement.

*(Note de la rédaction. Les imageurs multispectraux des missions réelles fonctionnent avec des consignes
de FPA bien plus froides — souvent proches de −50 °C — pour réduire le courant
d'obscurité. Le refroidisseur d'EOSAT-1 est un **cryoréfrigérateur Stirling
miniature**, et non un empilement Peltier, mais il est petit : son
efficacité est modélisée à 23 % de celle de Carnot
(`fpa_cooler_carnot_fraction`, 15 W en entrée), si bien que sa puissance frigorifique
s'effondre à mesure que l'écart de température augmente et que l'enveloppe
commandable s'arrête à −20 °C. C'est pourquoi `fpa_cooler_margin_k`
(0x0425) existe : « le refroidisseur peine » est un état lisible,
et une marge négative est la réponse honnête à un FPA qui ne sera pas
prêt. L'expression « Peltier envelope » subsiste dans quelques
fichiers générés ; la machine modélisée est bien un Stirling.)*

**Contenu de la passation.** Toutes les zones dans leur plage ? Un réchauffeur à
rapport cyclique saturé (signe d'un chemin thermique défaillant) ? État du refroidisseur du FPA,
température et marge de refroidissement restante — essentiel pour la recette de la charge utile.
Toute tendance thermique liée à l'orbite (entrée/sortie d'éclipse).

**Dépendances entre postes.** Avec l'EPS (puissance des réchauffeurs, puissance
du refroidisseur). Avec la charge utile (la température du FPA est une contrainte stricte pour
la prise de vue). Avec l'AOCS (l'angle solaire influe sur l'efficacité des radiateurs —
l'équipe doit parfois coordonner un léger biais d'attitude pour
des raisons thermiques).

**Modes de défaillance courants.** Mettre en marche le refroidisseur du FPA avant
que la zone charge utile soit à la bonne température de base — cela gaspille
l'énergie du refroidisseur et peut provoquer un surrefroidissement. Ne pas repérer un réchauffeur bloqué en marche
(rapport cyclique de 100 %) parce qu'il ne produit aucune télémesure rouge avant que la
zone soit déjà hors plage.

## 6.6 Ingénieur TT&C / communications

**Mandat.** Les liaisons radio avec le sol — au pluriel. Responsable du
transpondeur en bande S (liaison montante + liaison descendante), des paramètres de
codage et de modulation, de la marge de liaison, de l'échelle de débits TM **et de
l'émetteur de balise UHF séparé**. Configure le satellite pour
chaque type de passage.

**Autorité.** Autorité de commande sur le sous-système TT&C avec le GO du FD
(`allowed_func_ids` 63–79). Annonce *link is up* et *link is
down* sur la boucle.

**Console.** Overview, TTC, commanding, procedures, trends, manual.

**Télémesure à surveiller.**

Tableau 6.4 — Paramètres de télémesure TT&C, avec SID et plages nominale, jaune et rouge.

| Mnémonique | ID hexa | SID | Nominal | Jaune | Rouge |
|---|---|---|---|---|---|
| `ttc.tx_active` | 0x0525 | 6 | 1 (émission) | (sans objet) | 0 alors que 1 est attendu |
| `ttc.link_status` | 0x0501 | 6 | **2 = LOCKED** | 1 = ACQUIRING | 0 = NO_LINK |
| `ttc.pa_on` | 0x0516 | 6 | 1 pendant le passage | (sans objet) | 0 pendant le passage |
| `ttc.tx_fwd_power` | 0x050D | 6 | 27–33 dBm | baisse de > 3 dB | ≈ 0 |
| `ttc.carrier_lock` / `bit_sync` / `frame_sync` | 0x0510–0x0512 | 6 | 1 | (sans objet) | 0 pendant le passage |
| `ttc.eb_n0` | 0x0519 | 6 | > 10 dB | 4–10 dB | < 4 dB |
| `ttc.ber` (log10) | 0x050C | 6 | < −7 | −7 à −5 | < −8 ou > −4 |
| `ttc.cmd_rx_count` | 0x0513 | 6 | croissant | figé | décroissant (!) |
| `ttc.pa_temp` | 0x050F | 6 | < 55 °C | limite de la plage 0–55 | < −10 ou > 65 |
| `ttc.link_margin` | 0x0503 | 6 | > 6 dB | 3–6 dB | < 3 dB |
| `ttc.tm_data_rate` | 0x0506 | 6 | 16000 bit/s (LOW, routine) | 128000 (HIGH, vidages) | < 16000 (balise de secours) |
| `ttc.tm_tier` / `tm_tier_cmd` | 0x0539 / 0x053A | 6 | égaux | différents (un verrou refuse) | indice hors de l'échelle |
| `ttc.downlink_mode` | 0x053C | 6 | 1 pendant un vidage | 0 avec HIGH commandé | hors de {0,1} |

Pour `link_status`, **LOCKED vaut 2**, et non 1. La valeur 1 signifie verrouillage de la porteuse
sans synchronisation trame — acquisition en cours, pas verrouillé. C'est l'erreur
de lecture la plus fréquente dans les documents livrés.

**Commandes habituellement envoyées.**

- `EPS_TRANSPONDER_TX` (S8 func_id 18) `on=1` — met sous tension la
  chaîne d'émission.
- `TTC_PA_ON` (S8 func_id 66) / `TTC_PA_OFF` (S8 func_id 67) —
  marche/arrêt de l'amplificateur de puissance.
- `TTC_SET_DATA_RATE` (S8 func_id 65) — `rate=0` sélectionne LOW
  (16 kbit/s BPSK, conv(7,1/2)+RS — opérations de routine et
  repli FDIR), `rate=1` sélectionne HIGH (128 kbit/s QPSK, RS(255,223)
  — vidages uniquement). Le troisième palier, BEACON (1 kbit/s), s'active avec
  `TTC_SET_BEACON_MODE` et ne se sélectionne pas ici. HIGH est *verrouillé* : il
  exige une antenne déployée, le mode DOWNLINK activé et une élévation ≥ 10°,
  et une condition non remplie produit un rejet S1.8 (erreur 0x0007)
  qui nomme la condition — jamais d'écrêtage silencieux.
- `TTC_SET_DOWNLINK_MODE` (S8 func_id 79) — `on=1` ; c'est la
  condition de mode du palier HIGH, sans laquelle le palier HIGH de la fonction 65 est
  inaccessible.
- `TTC_SET_TX_POWER` (S8 func_id 68) — `level`.
- `TTC_SET_MODULATION` (S8 func_id 74) — 0=BPSK, 1=QPSK, 2=8PSK,
  3=OQPSK.
- `TTC_SET_BEACON_MODE` (S8 func_id 70) — `on=1` fait descendre la liaison en bande S
  au *palier* balise à 1 kbit/s.
- `TTC_BEACON_TX_ON` / `TTC_BEACON_TX_OFF` (S8 func_id 97 / 98) —
  l'**émetteur de balise UHF**, qui est un boîtier distinct du
  palier balise ci-dessus. L'éteindre est une commande `caution`.
- `TTC_DEPLOY_ANTENNA` (S8 func_id 69) — à usage unique, dans LEOP-007.
- `CONNECTION_TEST` (S17.1) — test de connexion de la liaison.

> **Le point pédagogique de ce poste.** EOSAT-1 possède deux
> émetteurs. `TTC_PA_OFF` coupe la chaîne principale en bande S et, avec
> elle, tous les paquets de télémesure sauf la SID 11 — et la balise UHF
> à antenne fouet à 437,5 MHz, 1 W, continue d'émettre la SID 11 indépendamment de
> l'amplificateur, de la ligne d'alimentation `ttc_tx`, du transpondeur ou de l'antenne
> patch en bande S. `ttc.tx_active` (0x0525) est le témoin de la bande S ;
> `ttc.beacon_active` (0x0527) est celui de la balise, et les deux sont
> indépendants par construction. Lorsqu'un opérateur dit « nous avons perdu la
> télémesure », la première question est *quelle radio*.

**Contenu de la passation.** État et configuration actuels de la liaison ; le
palier actif et le palier commandé, et leur concordance ; tendance du TEB ; toute
préoccupation concernant la température de l'amplificateur ; marge de liaison prévue pour le prochain passage
compte tenu de la géométrie orbitale ; état commandé de l'émetteur de balise ;
le *débit de veille* (le palier sur lequel le satellite est configuré pour
démarrer après le prochain passage).

**Dépendances entre postes.** Avec le segment sol (gain de l'antenne
sol, température du LNA sol, état de la station). Avec la
charge utile (le débit doit correspondre au rythme de production des données de la charge utile,
faute de quoi la mémoire de masse se remplit ou se vide). Avec la FDS
(Doppler et distance prévus pour le prochain passage).

**Modes de défaillance courants.** Ne pas ramener la liaison au palier LOW
en fin de passage — le palier HIGH coûte 11 W sur la ligne TX contre
5 W en LOW. Commander HIGH et supposer que la commande a pris : si l'antenne,
le mode DOWNLINK ou la condition d'élévation de 10° ne sont pas remplis, la commande est
**rejetée**, et l'indice révélateur est un désaccord entre `ttc.tm_tier` et
`ttc.tm_tier_cmd`. Confondre le *palier* balise (`TTC_SET_BEACON_MODE`,
toujours en bande S) avec l'*émetteur* de balise (`TTC_BEACON_TX_ON`,
UHF, une autre radio). Omettre de consigner la configuration de la liaison dans la main
courante, si bien que le quart suivant ne sait pas dans quelle configuration il va démarrer.

## 6.7 Ingénieur opérations charge utile

**Mandat.** L'instrument scientifique. Responsable de l'imageur
multispectral, du FPA, de la chronologie d'acquisition des images, de la chaîne de traitement
des données scientifiques (stockage à bord, compression, priorisation pour la
liaison descendante) et de l'évaluation de la qualité d'image.

**Autorité.** Autorité de commande sur la charge utile avec le GO du FD.
Arrête la chronologie scientifique du passage.

**Console.** Overview, Payload, commanding, procedures, trends,
manual. Ce poste dispose aussi du service 2, de sorte que les équipements de la charge utile
— FPA (0x0600), refroidisseur (0x0601), lampe d'étalonnage (0x0602),
obturateur (0x0603), compression (0x0604) — sont accessibles d'ici.

**Télémesure à surveiller.**

Tableau 6.5 — Paramètres de télémesure de la charge utile, avec SID et plages nominale, jaune et rouge.

| Mnémonique | ID hexa | SID | Nominal | Jaune | Rouge |
|---|---|---|---|---|---|
| `payload.mode` | 0x0600 | 5 | 0 OFF / 1 STANDBY / 2 IMAGING / 3 CALIBRATION | inattendu | FAULT |
| `payload.fpa_temp` | 0x0601 | 5 | −15 (à la consigne) | < −22.5 ou > 13.5 | < −26 ou > 17 |
| `payload.fpa_ready` | 0x0610 | 5 | 1 avant une acquisition | 0 avec refroidisseur en marche | 0 au moment de l'acquisition |
| `payload.cooler_pwr` | 0x0602 | 5 | ≈ 15 W en refroidissement | (sans objet) | 0 W alors qu'un refroidissement est attendu |
| `payload.image_count` | 0x0605 | 5 | croissant selon le plan | figé | baisse inattendue |
| `payload.store_used` | 0x0604 | 5 | < 80 % | > 90 % | > 95 % (plein) |
| `payload.last_scene_quality` | 0x060D | 5 | % élevé | en baisse | corrompue |
| `payload.snr` | 0x0616 | 5 | 30–55 dB | 20–30 dB | < 20 dB |
| `payload.checksum_errors` | 0x0609 | 5 | 0 | toute erreur | en hausse |

**Commandes habituellement envoyées.**

- `EPS_POWER_ON(line_index=3)` (S8 func_id 19) — mettre sous tension la ligne
  d'alimentation de la charge utile, puis `PAYLOAD_SET_MODE(mode=1)` (S8 func_id 26) pour
  amener la charge utile en attente. Il n'existe pas de code d'opération unique
  `PAYLOAD_POWER_ON` dans le catalogue des télécommandes.
- `PAYLOAD_SET_MODE` (S8 func_id 26) — 0=OFF, 1=STANDBY,
  2=IMAGING, **3=CALIBRATION**. Les modes 1, 2 et 3 demandent tous le
  refroidisseur du FPA ; le mode 0 le libère, et la demande pilote désormais à la fois
  l'indicateur de refroidisseur du TCS et la ligne d'alimentation `fpa_cooler` de l'EPS.
- `PAYLOAD_CAPTURE` (S8 func_id 28) avec `scene_id`, `lines`.
- `PAYLOAD_START_CALIBRATION` (S8 func_id 37) avec `mode` ;
  `PAYLOAD_STOP_CALIBRATION` (func_id 38). L'étalonnage d'obscurité n'exige
  plus le mode IMAGING.
- `PAYLOAD_SET_SHUTTER` (S8 func_id 119) avec `position` — une
  commande absolue de l'obturateur ; `PAYLOAD_CYCLE_SHUTTER` (func_id 93)
  le fait fonctionner. `PAYLOAD_CAL_LAMP` (func_id 95) avec `on`.
- `S13_CREATE_TRANSFER` → `S13_REPORT_STATUS` (S13.1 / S13.9) —
  déroulement canonique de la liaison descendante de gros volumes de données ;
  `PAYLOAD_INITIATE_TRANSFER` (S8 func_id 94) prépare une scène.
- `PAYLOAD_DELETE_IMAGE` (S8 func_id 30) — purger une image déjà transmise au sol.

Cinq codes d'échec de refus d'étalonnage méritent d'être mémorisés,
car ce sont ceux que ce poste verra réellement :
**0x0024** refus parce que la charge utile est en IMAGING, **0x0025** FPA
non prêt, **0x0026** obturateur dans la mauvaise position, **0x0027**
lampe dans le mauvais état, **0x0028** acquisition tentée avec
l'obturateur fermé. (0x0021–0x0023 restent les codes de pointage pour l'acquisition.)

La chaîne d'images est réelle de bout en bout : **les images n'apparaissent pas
d'elles-mêmes.** Rien n'est acquis sans avoir été commandé, et rien
n'arrive au sol sans avoir été transféré.

**Contenu de la passation.** Mode actuel de la charge utile ; température du FPA et
état de `payload.fpa_ready` (et, s'il n'est pas positionné, la marge du refroidisseur
en 0x064B) ; occupation du stockage et vitesse de remplissage prévue ; nombre de produits
et volume (0x0648 / 0x0647) ; qualité d'image sur l'ensemble du quart ;
file de liaison descendante en attente.

**Dépendances entre postes.** Avec l'AOCS (mode de pointage fin nécessaire
60 s avant la prise de vue). Avec le thermique (température du FPA). Avec le TT&C
(le débit de liaison descendante doit absorber le volume d'images). Avec la FDS
(géométrie des cibles de prise de vue — la charge utile peut demander à la FDS la
fauchée au sol prévue lors de l'acquisition).

**Modes de défaillance courants.** Commander la prise de vue avant que le pointage fin
soit établi. Ne pas transmettre au sol avant la saturation du stockage.
Confondre « qualité d'image OK » et « contenu de l'image utile » — les
deux ne sont pas identiques, et c'est aux opérations charge utile de faire la distinction.

## 6.8 Système de dynamique du vol (FDS) / analyste orbite

**Mandat.** Restitution d'orbite, planification des manœuvres, prévision
des passages, criblage des conjonctions, modélisation des éclipses. Dans le MCS,
l'analyste FDS occupe le poste `aocs`, intitulé
*Dynamique du vol* précisément pour cette raison ; dans l'industrie, cette place
est parfois appelée *analyste orbite* ou *analyste de mission*
selon l'agence.

**Autorité.** Aucune autorité de commande directe sur la poussée.
Produit le **vecteur de manœuvre** et compare le delta-V obtenu
au plan ; le poste propulsion arme et déclenche
(`PROP_SET_BURN` S8 fonction 110, `PROP_ARM` 108, `PROP_EXECUTE` 111).
Produit le **plan de passage** que suit l'équipe. NOM-004 (planification) et
NOM-013 (exécution) exigent toutes deux les postes `flight_director`, `aocs` et
`propulsion`.

**Console.** Le poste MCS `aocs` — y compris un **onglet PROP
en lecture seule**, sur lequel tous les boutons de commande s'affichent désactivés — plus
un poste de travail secondaire. Logiciels : `tools/orbit_tools.py` (propagateur
d'orbite, prédicteur d'AOS/LOS) et le planificateur.

**Télémesure et données à surveiller.** L'état GPS fourni par `aocs.gps_lat`,
`aocs.gps_lon`, `aocs.gps_alt` (0x0210–0x0212), avec
`aocs.gps_fix` (0x0274), `aocs.gps_pdop` (0x0275) et
`aocs.gps_num_sats` (0x0276) comme voies de qualité. Ce sont des
**paramètres à la demande** — ils ne figurent pas dans le balayage périodique de la SID 2 ;
la FDS les interroge donc avec `GET_PARAM` (S20.3) plutôt que
d'attendre la télémesure de servitude. Le propagateur d'orbite du poste de travail
FDS est réinitialisé à chaque passage à partir de ces valeurs et propagé
pour prévoir les contacts des 24 h suivantes. Après une poussée, surveillez
`prop.orbit_epoch_version` (0x0B19) et `prop.sma_km` (0x0B1A) :
le segment sol recalcule le jeu d'éléments, si bien que les passages et les éclipses
se déplacent réellement — 1 m/s apporte environ +1,800 km de demi-grand axe et
avance le passage de 33,5 s à +24 h.

**Commandes envoyées.** Aucune directement. Produits :

- Planning des passages (transmis au TT&C, au segment sol et à la charge utile).
- Planning des éclipses (transmis à l'EPS et au thermique).
- Vecteur de manœuvre (transmis à la propulsion ; l'AOCS maintient l'attitude).
- Alertes de conjonction (transmises au FD ; rarement exploitables pendant une
  semaine de formation en salle de contrôle, mais la procédure existe).

**Contenu de la passation.** Planning des passages des 24 h suivantes (imprimé) ; heures
des prochaines entrée et sortie d'éclipse ; tout travail de planification de manœuvre
en cours ; toute alerte de conjonction.

**Dépendances entre postes.** Le plus grand nombre d'échanges de la salle.
La FDS produit les horaires sur lesquels s'appuient tous les autres postes.

**Modes de défaillance courants.** Utiliser des données GPS périmées (à rafraîchir
à chaque passage). Produire des horaires de passage dans le mauvais repère
(repère satellite au lieu de station sol). Oublier de signaler une
éclipse imminente à l'EPS et au thermique.

## 6.9 Ingénieur segment sol / contrôleur réseau

**Mandat.** Le côté sol de la liaison radio. Pointage et santé
de l'antenne, équipements de bande de base, connectivité réseau entre le MCS
et la station, passage de relais d'une station à l'autre. Dans l'industrie, les intitulés réels
incluent *contrôleur réseau*, *opérateur sol*, *opérateur
antenne*, selon l'agence.

**Autorité.** Autorité de commande sur la station sol
(pointage de l'antenne, configuration de la bande de base) avec le GO du FD. Annonce la station
**ready** ou **not ready** avant l'AOS.

**Console.** Poste de travail secondaire. Logiciels : le planificateur (accès
complet, y compris la sélection de la station pour le prochain passage), un accès en
lecture à l'onglet de télémesure TTC et la **page radio servie par
`smo-rfsim`** — voyants de verrouillage porteuse / synchronisation bit / synchronisation trame, estimation
Doppler, constellation et diagramme de l'œil. L'ingénieur segment sol est le
principal observateur de la chaîne radio de la station sol. La passerelle RF
fonctionne selon l'un de trois modes (`PACKET`, `FRAME`, `RF`, réglé dans
`rfsim.yaml`) ; seul `RF` produit les vues au niveau du modem.

**Télémesure à surveiller.**

Tableau 6.6 — Éléments du segment sol surveillés par l'ingénieur segment sol, avec indicateurs de préoccupation.

| Élément | Où | Nominal | Préoccupation |
|---|---|---|---|
| Antenne / poursuite, par station | `ttc.gs_equipment_status` (0x0524), bit 0 | bit positionné = sain | bit non positionné avant l'AOS |
| LNA, HPA de liaison montante, oscillateur de référence | `ttc.gs_equipment_status` bits 1–3 | 15 = les quatre sains | un bit non positionné |
| Station active | `ttc.active_gs` (0x0523) | indice (à partir de 1) dans `orbit.yaml` | 0 = hors contact |
| Bande de base — Eb/N0 | page radio rfsim | cohérent avec l'émission du satellite | une incohérence suggère un problème de chaîne RF |
| Bande de base — synchronisation trame | page radio rfsim / `ttc.frame_sync` (0x0512) | verrouillée pendant le passage | perte pendant le passage |

**Commandes envoyées.** **Aucune vers le satellite, et aucune non plus vers la
station sol** — le catalogue ne contient aucune télécommande `GS_*`.
Le poste segment sol travaille entièrement au moyen des
outils côté sol :

- Sélection de la station pour le prochain passage (planificateur).
- Mode de la passerelle RF et configuration de la chaîne de traitement (`rfsim.yaml`, page radio).
- La santé des équipements de station est *observée* au moyen de
  `ttc.gs_equipment_status` ; elle est maintenue par la station sol,
  et non par une commande de l'opérateur.

**Contenu de la passation.** Disponibilité des stations pour chaque passage à venir ;
toute préoccupation sur la santé des antennes ; toute dégradation du réseau constatée pendant
le quart ; configuration de la bande de base utilisée (débit, codage).

**Dépendances entre postes.** Avec le TT&C en permanence (le
côté bord et le côté sol de la même liaison). Avec la FDS pour la
sélection de la station passage par passage.

**Modes de défaillance courants.** Ne pas s'apercevoir que l'antenne
poursuit le mauvais créneau du planning. Manquer une resynchronisation
de la bande de base qui a fait perdre une partie d'un passage.

## 6.10 Responsable de mission / interface client

**Mandat.** Communication externe et décisions au niveau de la mission.
Le responsable de mission **n'est pas sur la boucle opérationnelle** — il
écoute, il comprend, il traduit. Il est la voix du client
dans la salle et la voix de la salle auprès du client.

**Autorité.** Décisions au niveau de la mission uniquement (p. ex. *faut-il
tenter la première lumière demain compte tenu de l'anomalie d'aujourd'hui ?*). Il ne
passe pas outre le FD pour les décisions relevant du quart ; le FD ne passe pas
outre le responsable de mission pour les décisions relevant de la mission.

**Console.** Aucune console opérationnelle. Un ordinateur portable pour les comptes rendus de quart et
les communications client. S'assoit au fond de la salle.

**Produits.**

- **Point quotidien au client** — court résumé écrit du
  quart, envoyé en fin de journée. Modèle dans le cahier d'exercices.
- **Bulletin d'anomalie** — si une anomalie injectée entraîne une
  perte significative (première lumière reportée, cible de prise de vue manquée),
  le responsable de mission rédige le bulletin destiné au client.
- **Rapport de quart** — classe le journal de mission officiel du quart.

**Contenu de la passation.** Engagements envers le client en cours ; toute communication
externe en attente ; décisions au niveau de la mission prises ou
reportées.

**Dépendances entre postes.** Avec le FD (état opérationnel). Avec les
opérations charge utile (état des livrables scientifiques). Hors de la
salle, avec le client (représenté, lors des répétitions, par
le directeur de mission).

**Modes de défaillance courants.** Dériver vers des discussions opérationnelles
sur la boucle — cela brouille l'autorité. Ne pas consigner le compromis
au niveau de la mission lorsque le FD prend une décision en cours de quart.

---

# Chapitre 7 — Outils, consoles et types de commandes

Ce chapitre est la référence des outils de l'opérateur. Vous l'utiliserez lors de
la visite de familiarisation avec la console d'opérations et pendant les opérations courantes. Traitez-le
comme le manuel de bord d'un cockpit : on ne le lit pas de la première à la dernière page ; on y
cherche le passage dont on a besoin *tout de suite*.

## 7.1 Le système de contrôle de mission (MCS) en un coup d'œil

Le MCS est une application web unique servie à l'adresse `[http://localhost:9090/`](http://localhost:9090/`) dans
la salle de contrôle. La console de chaque opérateur en exécute une instance,
configurée pour le poste de cet opérateur (le fichier `mcs/positions.yaml`
du simulateur associe à chaque poste les onglets qu'il affiche).
Deux autres applications web fonctionnent à côté et se confondent facilement avec lui :
le simulateur / console instructeur sur le port **8080** et le système de
planification de mission sur le port **9091** (§7.3).

Le MCS comporte cinq zones :

<svg viewBox="0 0 760 460" xmlns="http://www.w3.org/2000/svg" style="max-width:720px; font-family:'Calibri','Helvetica Neue',Arial,sans-serif; font-size:11px;">
  <!-- Top header -->
  <rect x="20" y="20" width="720" height="60" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="380" y="40" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="12">EN-TÊTE (toujours visible)</text>
  <text x="380" y="58" text-anchor="middle" fill="#92400e" font-size="10">indicatif · phase · temps bord · état du passage · bandeau d'alerte rouge</text>

  <!-- Left rail -->
  <rect x="20" y="90" width="120" height="280" rx="4" fill="#e0e7ff" stroke="#4338ca" stroke-width="2"/>
  <text x="80" y="115" text-anchor="middle" fill="#1e1b4b" font-weight="bold">COLONNE GAUCHE</text>
  <text x="80" y="132" text-anchor="middle" fill="#1e1b4b" font-size="9">(onglets)</text>
  <g font-size="9" fill="#1e1b4b">
    <text x="35" y="160">• overview</text>
    <text x="35" y="178">• eps</text>
    <text x="35" y="196">• aocs</text>
    <text x="35" y="214">• tcs</text>
    <text x="35" y="232">• obdh</text>
    <text x="35" y="250">• ttc</text>
    <text x="35" y="268">• payload</text>
    <text x="35" y="286">• commanding</text>
    <text x="35" y="304">• procedures</text>
    <text x="35" y="322">• manual</text>
    <text x="35" y="340">• fdir_panel</text>
    <text x="35" y="358">… selon le poste</text>
  </g>

  <!-- Centre: telemetry mosaic -->
  <rect x="150" y="90" width="430" height="180" rx="4" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
  <text x="365" y="115" text-anchor="middle" fill="#14532d" font-weight="bold" font-size="12">CENTRE — MOSAÏQUE DE TÉLÉMESURE</text>
  <text x="365" y="132" text-anchor="middle" fill="#14532d" font-size="9">(grille de widgets de l'onglet courant)</text>
  <g stroke="#15803d" fill="#fff" stroke-width="0.5">
    <rect x="170" y="145" width="115" height="50"/>
    <rect x="290" y="145" width="115" height="50"/>
    <rect x="410" y="145" width="115" height="50"/>
    <rect x="170" y="200" width="115" height="50"/>
    <rect x="290" y="200" width="115" height="50"/>
    <rect x="410" y="200" width="115" height="50"/>
  </g>
  <g font-size="8" fill="#14532d" text-anchor="middle">
    <text x="227" y="172">bus_voltage</text><text x="227" y="184">28.1 V</text>
    <text x="347" y="172">battery_soc</text><text x="347" y="184">84 %</text>
    <text x="467" y="172">aocs.mode</text><text x="467" y="184">NOMINAL</text>
    <text x="227" y="227">fpa_temp</text><text x="227" y="239">−15.0 °C</text>
    <text x="347" y="227">link_margin</text><text x="347" y="239">8.2 dB</text>
    <text x="467" y="227">ttc.ber</text><text x="467" y="239">1e-8</text>
  </g>

  <!-- Procedure panel (collapsible) -->
  <rect x="150" y="280" width="430" height="90" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="365" y="305" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="12">PANNEAU DES PROCÉDURES (repliable)</text>
  <text x="365" y="322" text-anchor="middle" fill="#92400e" font-size="9">liste d'étapes numérotées · responsable · action · vérification · boutons Begin/Verify/Skip</text>
  <line x1="170" y1="335" x2="560" y2="335" stroke="#d97706" stroke-width="0.5"/>
  <text x="180" y="350" fill="#92400e" font-size="9">▸ Étape 7 : TT&amp;C — TTC_PA_ON — vérifier ttc.pa_on = 1</text>
  <text x="180" y="362" fill="#92400e" font-size="9">▸ Étape 8 : AOCS — attendre un pointage &lt; 0.05° avant la prise de vue</text>

  <!-- Right rail -->
  <rect x="590" y="90" width="150" height="280" rx="4" fill="#fee2e2" stroke="#b91c1c" stroke-width="2"/>
  <text x="665" y="115" text-anchor="middle" fill="#7f1d1d" font-weight="bold">COLONNE DROITE</text>
  <text x="665" y="132" text-anchor="middle" fill="#7f1d1d" font-size="9">(espace de travail opérateur)</text>
  <g font-size="10" fill="#7f1d1d">
    <text x="605" y="160" font-weight="bold">Panneau FDIR</text>
    <text x="615" y="174" font-size="8">toutes les règles actives</text>
    <text x="615" y="186" font-size="8">gravité 0–4</text>
    <text x="605" y="215" font-weight="bold">Historique des cmd</text>
    <text x="615" y="229" font-size="8">envois récents</text>
    <text x="615" y="241" font-size="8">+ journal de vérif. S1</text>
    <text x="605" y="270" font-weight="bold">Panneau de commande</text>
    <text x="615" y="284" font-size="8">saisie / GO du FD (voix) /</text>
    <text x="615" y="296" font-size="8">ARMER si critique / ENVOYER</text>
    <text x="615" y="320" font-size="8" fill="#374151">▸ S8 func: 55</text>
    <text x="615" y="332" font-size="8" fill="#374151">▸ OBC_BOOT_APP</text>
    <text x="615" y="344" font-size="8" fill="#374151">[ ENVOYER ]</text>
  </g>

  <!-- Footer bar -->
  <rect x="20" y="385" width="720" height="55" rx="4" fill="#f3f4f6" stroke="#6b7280" stroke-width="1"/>
  <text x="380" y="405" text-anchor="middle" fill="#374151" font-weight="bold" font-size="11">BARRE D'ÉTAT (en bas)</text>
  <text x="380" y="423" text-anchor="middle" fill="#374151" font-size="9.5">état de connexion · temps avant la prochaine AOS · horodatage de la dernière commande · initiales de l'opérateur</text>
</svg>

*Figure 7.1 — Zones du MCS. L'en-tête est toujours visible en haut. La colonne gauche liste les onglets propres au poste. Le centre se partage entre la mosaïque de télémesure (en haut, grille de widgets épinglés) et le panneau des procédures (en bas, repliable). La colonne droite est la zone de travail de l'opérateur — panneau FDIR, historique des commandes et panneau de commande — et c'est la zone la plus utilisée pendant un passage.*

### En-tête

Cinq champs, toujours visibles :

1. **Indicatif.** `EOSAT-1`.
2. **Phase.** Entier de 0 à 6 suivi du nom : 0 PRE_SEPARATION, 1
   SEPARATION_TIMER, 2 INITIAL_POWER_ON, 3 BOOTLOADER_OPS, 4 LEOP,
   5 COMMISSIONING, 6 NOMINAL. **Les phases 5 et 6 se règlent par télécommande.**
   L'équipe de direction de la mission les déclare avec `SYS_SET_MISSION_PHASE`
   (S8 fonction 120) ; la console instructeur (`set_phase`, plage 0–6) et les scripts
   de scénario ne sont que des forçages de l'instructeur ; le
   satellite avance aussi de lui-même 1→2→3 à l'expiration de la minuterie
   de séparation. Ne cherchez pas de TC `SET_PHASE` dans le
   catalogue — cette mnémonique existait autrefois comme alias de
   `OBC_BOOT_APP` (S8 fonction 55) et a été supprimée en 2026-08 précisément
   parce qu'elle incitait un opérateur qui voulait faire avancer la phase à
   redémarrer l'OBC.
3. **Temps bord.** Horloge de bord au format `YYYY-MM-DDTHH:MM:SSZ`.
   Jaune si la dérive dépasse 1 s par rapport au sol ; rouge si elle dépasse 5 s.
4. **État du passage.** `IN PASS (Svalbard, T-LOS 04:32)` ou `BETWEEN
   PASSES (next: Iqaluit AOS T+18:21)`. La station nommée est
   `ttc.active_gs` (0x0523), un indice à partir de 1 dans la liste des cinq
   stations de `orbit.yaml` ; 0 signifie hors contact.
5. **Bandeau d'alerte.** Vide en situation nominale ; barre rouge dès qu'une
   règle FDIR active est de gravité 3 ou 4.

### Colonne gauche — onglets

L'ensemble d'onglets dépend du poste de l'opérateur. L'ensemble complet
(dix-huit onglets, visibles par le FD uniquement) est le suivant :

Tableau 7.1 — Catalogue complet des onglets de la colonne gauche du MCS, avec la fonction de chacun.

| Onglet | Usage |
|---|---|
| `system_dashboard` | Vue de santé composite de tous les sous-systèmes |
| `power_monitor` | Vue de tendances dédiée à l'EPS |
| `fdir_panel` | Toutes les règles actives, toutes les définitions de règles |
| `contact_schedule` | Passages des 24 h à venir, par station |
| `procedure_panel` | Charger et exécuter des procédures |
| `overview` | Synthèse de santé commune à tous les postes |
| `eps` | Mosaïque de télémesure de l'EPS |
| `aocs` | Visualisation du SCAO + télémesure |
| `tcs` | Zones du TCS + rapports cycliques des réchauffeurs |
| `obdh` | État de l'OBC, chien de garde, mémoire, bus |
| `ttc` | Transpondeur, marge de liaison, TEB |
| `payload` | État de l'imageur, FPA, stockage |
| `prop` | Propulsion : réservoir, vannes, état d'armement, avancement de la poussée |
| `commanding` | Constructeur de commandes directes |
| `pus` | Vue brute des services PUS (avancé) |
| `procedures` | Visionneuse des fichiers de procédure (navigateur en lecture seule) |
| `trends` | Tendances des paramètres sur une longue fenêtre |
| `manual` | Lecteur du manuel du satellite |

Les correspondances entre postes et onglets figurent au chapitre 6 et dans `mcs/positions.yaml`.

### Centre — mosaïque de télémesure

Une grille de widgets, un par paramètre ou groupe de paramètres. Chaque
widget affiche la valeur actuelle, les unités, la coloration des limites (plages verte/jaune/
rouge) et une mini-courbe de tendance. Cliquez sur un widget pour l'agrandir
en un tracé plein écran avec une fenêtre d'historique sélectionnable.

La mosaïque est **configurée selon le poste** : chaque opérateur voit par défaut les
paramètres qui concernent son poste, mais tout
opérateur peut épingler n'importe quel paramètre sur sa mosaïque pour la durée du quart.
L'épinglage survit à une déconnexion/reconnexion.

### Indicateurs d'état de la télémesure

- **Vert** — valeur dans la plage nominale.
- **Jaune** — valeur dans la plage jaune ; ce n'est pas un déclencheur FDIR, mais
  l'opérateur doit le signaler sur la boucle.
- **Rouge** — valeur dans la plage rouge ; en général, un déclencheur FDIR se déclenche
  simultanément.
- **Dégradé / périmé** — la valeur est plus ancienne que ne le permet sa propre cadence
  de liaison descendante. Les seuils sont **dérivés, paramètre par paramètre, de
  la structure HK qui le transporte** (`mcs/staleness.yaml`), et non
  d'un délai d'attente global unique : une valeur est fraîche tant que son âge est inférieur à
  `max(10 s, interval × 0.9)`, dégradée tant qu'il est inférieur à
  `max(20 s, interval × 1.5)`, et périmée au-delà. C'est important
  car la SID 3 (TCS) est transmise toutes les 60 s et la SID 11 (balise)
  toutes les 30 s — avec une règle uniforme de 10 s, ces vues apparaîtraient
  périmées la plupart du temps. Périmé n'est *pas* synonyme de rouge — périmé
  signifie *je ne connais pas la valeur*.
- **Non activé** — toutes les structures HK qui transportent le paramètre sont
  désactivées, ou n'ont jamais été reçues. Ce n'est pas un défaut de liaison : seules
  les SID **1 (EPS)** et **11 (balise)** sont activées à l'amorçage du logiciel
  applicatif ; la bonne réponse est donc `HK_ENABLE` (TC(3,5)), et non
  une chasse au problème radio.
- **Signalé** — marqué par l'opérateur. Clic droit sur un widget → Flag. Le
  signalement reste en place pendant tout le quart et est repris dans la main courante.

### Panneau des procédures

Zone repliable située en bas du centre. Affiche la procédure chargée
sous la forme d'une liste d'étapes numérotées en trois colonnes : **responsable**
(poste responsable de l'étape), **action** (commandée ou
observée), **vérification** (la télémesure qui confirme l'étape).
Chaque étape comporte trois boutons : *Begin*, *Verify*, *Mark Skipped*.
L'état d'une étape est l'un des suivants : `pending`, `in-progress`, `verified`,
`skipped`, `failed`.

Les procédures horodatent automatiquement chaque changement d'état. Ce journal
est versé dans la main courante en fin de quart.

### Panneau FDIR

Zone supérieure de la colonne droite. Liste toutes les règles de surveillance (les **46**
définitions de `monitoring/s12_definitions.yaml`, chacune déclarée
`WARNING` ou `ALARM`) et toutes les règles événement-action (les **32** règles
de `monitoring/s19_rules.yaml`) actuellement actives, avec un code couleur selon la
gravité. Lorsqu'une règle se déclenche, le panneau :

1. Affiche le nom de la règle et la valeur du paramètre déclencheur.
2. Émet une brève tonalité sonore à l'apparition de chaque nouvelle alarme.
3. Ajoute une ligne à la liste des « anomalies actives ».
4. Propose la procédure de contingence canonique. Le lien alarme →
   procédure est une donnée, et non un savoir oral : `mcs/alarm_procedures.yaml`
   effectue la résolution d'abord par identifiant de paramètre, puis par identifiant d'événement, puis par
   sous-système — si bien qu'une surintensité sur l'un quelconque des courants
   des lignes 0 à 7 (0x0118–0x011F) renvoie à CTG-012 *Traitement d'une
   surintensité*.

Le SPACON et le FD surveillent en permanence le panneau FDIR pendant un
passage. Les autres opérateurs s'en remettent à l'alerte sonore et à la ligne FDIR
qui apparaît dans leur onglet overview.

### Messagerie de la boucle vocale

Le MCS actuel ne comporte **aucun** canal texte : la boucle vocale passe
uniquement par les casques, et le trafic *informatif non prioritaire*
(p. ex. « PAYLOAD: storage 42 % used ») passe sur la boucle ou dans la
main courante. Un canal texte de secours est envisagé dans les travaux
prévus sur l'architecture web ; ne planifiez pas un quart en comptant
dessus. Dans tous les cas, les intentions de commande passent uniquement par la voix.

### Panneau de commande

Zone inférieure de la colonne droite. Le constructeur de commandes du poste. Trois
modes de saisie :

- **Commande du catalogue** — choisissez le mnémonique dans `tc_catalog.yaml` ;
  le constructeur remplit le service, l'identifiant de fonction et les champs typés,
  et affiche l'hexadécimal assemblé et son nombre d'octets.
- **Commande directe** — pour les commandes ponctuelles. L'opérateur choisit le
  service et le sous-type, puis saisit (ou colle) les données en hexadécimal ;
  *DÉCODER HEXA → CHAMPS* les vérifie par rapport au catalogue.
- **Commandes rapides** — préréglages à un seul appui propres au poste. Une
  entrée que le poste n'a pas le droit d'envoyer est affichée comme refusée,
  avec le nom du poste qui en est propriétaire.

Chaque commande passe par les étapes suivantes :

1. **Contrôle d'autorité.** *ENVOYER* n'est activé que si le poste
   détient l'autorité de commande (`mcs/positions.yaml`) ; sinon, le
   serveur refuse la commande.
2. **GO du FD.** L'opérateur demande le GO sur la boucle vocale. Le FD interroge
   les postes concernés et donne son autorisation. L'outil ne l'enregistre
   ni ne l'impose ; c'est une discipline de salle.
3. **ARMER.** Pour les commandes *critical*, l'opérateur à l'origine de la commande
   doit appuyer sur *ARMER* avant *ENVOYER* (une commande rapide critique est armée
   au premier appui et exécutée par un second appui dans les 8 s).
   Il n'existe pas de bouton *Second-Key* pour le FD ; une seconde clé côté FD
   fait partie des idées pour les travaux prévus sur l'architecture web, et
   n'est pas une fonction actuelle. Les autres commandes sautent cette étape.
4. **Envoi.** La commande part vers l'émetteur de la station
   sol. Le satellite répond par la chaîne de vérification S1 :
   **S1.1** succès de l'acceptation, **S1.3** début d'exécution,
   **S1.5** avancement, **S1.7** fin d'exécution. Un refus est
   renvoyé sous la forme **S1.2** (échec de l'acceptation), **S1.4** (échec du début
   d'exécution) ou **S1.8** (échec de l'exécution), chacun portant un
   code d'échec sur 16 bits et, sur ce satellite, un message d'échec lisible
   ajouté en clair — de sorte que la console affiche *pourquoi*
   (« Capture refused: AOCS not in FINE_POINT », 0x0021) plutôt
   qu'un simple nombre. Un refus déclenche aussi l'événement `COMMAND_REJECTED`
   0x030B.

Le résultat des commandes est journalisé automatiquement dans l'historique des
commandes et le journal de vérification : horodatage, la commande elle-même,
le résultat de l'envoi et la réponse S1 du satellite. Le FD ayant autorisé
n'est pas consigné ; le SPACON note le GO dans la main courante.

**La criticité est déclarée dans le catalogue, pas laissée à la mémoire.**
`commands/tc_catalog.yaml` marque cinq commandes `critical` —
`OBC_REBOOT` (52), `OBC_SWITCH_UNIT` (53), `PROP_ARM` (108),
`PROP_SET_BURN` (110) et `SYS_SET_MISSION_PHASE` (120) — et
quatorze autres `caution`. L'armement (ARMER) est exigé pour l'ensemble critique.

## 7.2 Ensembles d'onglets par poste (aide-mémoire)

Tableau 7.2 — Aide-mémoire de la visibilité des onglets du MCS selon le poste, pour les sept consoles configurées.

| Clé du poste | Nom affiché | Onglets visibles |
|---|---|---|
| `flight_director` | Direction de vol (Flight Director) | Les dix-huit (system_dashboard, power_monitor, fdir_panel, contact_schedule, procedure_panel, overview, eps, aocs, tcs, obdh, ttc, payload, prop, commanding, pus, procedures, trends, manual) |
| `eps_tcs` | Puissance et thermique (Power & Thermal) | overview, eps, tcs, commanding, procedures, trends, manual |
| `aocs` | Dynamique du vol (Flight Dynamics) | overview, aocs, prop (lecture seule), commanding, procedures, trends, manual |
| `ttc` | TT&C | overview, ttc, commanding, procedures, trends, manual |
| `payload_ops` | Opérations charge utile (Payload Operations) | overview, payload, commanding, procedures, trends, manual |
| `fdir_systems` | FDIR / Systèmes (FDIR / Systems) | overview, obdh, commanding, pus, procedures, trends, manual |
| `propulsion` | Propulsion | overview, prop, tcs, commanding, procedures, trends, manual |

Notez ce que contient réellement le fichier : **sept** postes de console,
et non neuf. L'EPS et le thermique partagent une seule console *Puissance et thermique* ;
il n'existe pas de poste SPACON, FDS ou segment sol distinct dans
`mcs/positions.yaml` — ce sont des rôles de salle que le cours attribue en
plus des sept consoles configurées. La propulsion est un poste
à part entière (le module de monergol vert de 1U est un matériel réellement piloté).

L'onglet `overview` est toujours visible pour tous les postes — c'est
la conscience de la situation partagée.

L'autorité de commande est contrôlée séparément de la visualisation :
`allowed_services` et `allowed_func_ids` déterminent quels boutons sont
actifs. La dynamique du vol peut *voir* l'onglet PROP, mais les func_ids 108–118
sont délibérément absents de sa liste, si bien que tous les boutons de propulsion
s'affichent désactivés pour cet opérateur.


![Vue combinée du modèle OSI à 7 couches et de la pile de protocoles spatiaux équivalente (application → PUS → paquet spatial CCSDS → trame de transfert TM/TC → CLTU/CADU → RF), avec les types de services PUS et la structure en octets des paquets.](../assets/figures/fig_tm_pus_cltu_cadu_stack.svg)

*Vue combinée du modèle OSI à 7 couches et de la pile de protocoles spatiaux équivalente (application → PUS → paquet spatial CCSDS → trame de transfert TM/TC → CLTU/CADU → RF), avec les types de services PUS et la structure en octets des paquets.*

## 7.3 Le système de planification de mission (MPS)

Le MPS est une application web distincte, sur son propre port,
<http://localhost:9091/> (une mise en page
grand écran est disponible à `/wide`). Trois postes l'utilisent couramment :

- **Opérations charge utile** — pour la sélection des cibles de prise de vue et la
  programmation des activités.
- **FDS** — pour la prévision des passages et la planification des fenêtres de manœuvre.
- **Segment sol** — pour la disponibilité des stations et l'allocation des ressources
  passage par passage.

### Panneaux du MPS

1. **Sélecteur de cibles de prise de vue.** Une carte du monde sur laquelle les
   cibles de courants océaniques préchargées depuis
   `planning/imaging_targets.yaml` sont superposées sous forme de cadres — chaque cible
   est un cadre délimité en latitude/longitude (`OCM-001` Gulf Stream, `OCM-002`
   Kuroshio, `OCM-003` Agulhas, …), avec une `priority`, un intervalle
   `revisit_days` et une condition `min_solar_elevation_deg`.
   Ce sont les champs sur lesquels on filtre. Les cibles ne sont pas
   propres à une bande : les quatre bandes « couleur de l'océan » de l'imageur (443, 560,
   665, 865 nm) se configurent à chaque acquisition avec
   `PAYLOAD_SET_BAND_CONFIG`, et non par cible.
2. **Catalogue des types d'activités.** Issu de `planning/activity_types.yaml`.
   Dix types : `imaging_pass`, `data_dump`, `calibration`,
   `housekeeping_collection`, `software_upload`,
   `momentum_desaturation`, `thermal_rebalance`, `load_shedding`,
   `fdir_recovery`, `orbit_manoeuvre`. Chaque type a un profil de
   puissance, un profil thermique, une exigence de pointage et une
   durée.
3. **Planning des stations sol.** Tableau des passages par station pour les
   24 h suivantes sur les **cinq** stations (Iqaluit, Troll, Svalbard,
   Inuvik, O'Higgins), calculé à partir du propagateur d'orbite.
   Colonnes : AOS, élévation maximale, LOS, durée, station, qualité de
   visibilité. L'élévation maximale n'est pas décorative — le palier HIGH à 128 kbit/s
   est verrouillé à 10° d'élévation, si bien qu'un passage dont le point culminant est inférieur à 10° peut
   servir à la commande et à la télémesure de servitude, mais pas au vidage d'images.
4. **Détecteur de conflits.** Lorsque vous placez une activité dans un passage,
   le détecteur de conflits vérifie : le temps de basculement entre activités
   consécutives, le bilan de puissance (charge cumulée par rapport à la puissance disponible), l'enveloppe
   thermique (aucune zone ne sort de sa plage), le bilan de pointage (aucune
   activité demandée dans un mode de pointage incapable de la satisfaire).
   Les conflits apparaissent en rouge ; les avertissements en jaune.
5. **Exportateur de plan.** Convertit le plan préparé en fichier de séquence
   d'activités que l'OBC ingère au moyen de la programmation temporelle S11 —
   `SCHEDULE_TC` est **S11.4**, encadrée par `ENABLE_SCHEDULE` (S11.13),
   `DISABLE_SCHEDULE` (S11.9), `DELETE_SCHEDULED` (S11.7),
   `DELETE_ALL_SCHEDULED` (S11.11) et `LIST_SCHEDULE` (S11.17).

Le MPS est en lecture seule pour la plupart des postes ; les opérateurs opérations charge utile, FDS
et segment sol disposent d'un accès en écriture.

## 7.4 Le panneau des procédures — fonctionnement

Dans le simulateur, les procédures sont des fichiers Markdown situés sous
`configs/eosat1/procedures/{leop,commissioning,nominal,contingency,emergency}/`.
Elles sont indexées dans `procedures/procedure_index.yaml`. Le panneau des
procédures du MCS lit cet index.

### Structure d'un fichier de procédure

Toutes les fiches de procédure livrées ont la même structure — ouvrez
`procedures/nominal/routine_health_check.md` en parallèle de ce texte et
suivez :

```
# {ID}: {Title}
**Subsystem:** {ALL | EPS | AOCS | …}
**Phase:** {LEOP | COMMISSIONING | NOMINAL | …}
**Revision:** {n.n}
**Approved:** {authority}

## Purpose
…

## Prerequisites
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] …

## Procedure Steps

### Step 1 --- {name}
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- EPS housekeeping
**Verify:** `eps.bat_soc` (0x0101) > 50 % within 10 s
**GO/NO-GO:** {what to do if it fails}

## Off-Nominal Handling
- …

## Post-Conditions
- [ ] …
```

Notez la forme d'une étape : ce n'est pas un tableau à quatre colonnes mais un ensemble
d'étiquettes en gras — **TC**, **Verify**, **Action**, **Note**,
**GO/NO-GO**, **Trend**, **Flag**. Chaque commande est écrite avec
ses arguments **à l'intérieur** des accents graves (backticks), le service et le
sous-type étant précisés à côté, et chaque vérification nomme à la fois
la mnémonique du paramètre et son identifiant hexadécimal. Rédigez vos propres fiches de la
même façon ; un nom de commande dont les arguments flottent en dehors de la
portion de code est le défaut le plus fréquent relevé dans ce
matériel pédagogique.

Les fiches exécutables par la machine sont signalées dans l'index. Huit fiches sont
exécutables de bout en bout (NOM-002, NOM-003, NOM-004, NOM-008,
NOM-009, CTG-001, CTG-008, EMG-006) ; l'exécuteur ne
signale plus de succès pour une procédure qui n'a rien fait, et il échoue
en position sûre sur tout type d'étape qu'il ne comprend pas. Une fiche qui
ne commande délibérément rien est déclarée avec `advisory: true`
et un `advisory_reason` dans son entrée d'index — CTG-020 (défaillance de l'antenne
de la station sol) en est l'exemple livré.

### Exécuter une procédure

1. **Charger.** Rechercher la procédure dans l'index du panneau ; cliquer pour la
   charger. La procédure devient la *procédure active* du
   quart. Une seule procédure active à la fois (selon la règle fixée par le FD).
2. **Commencer.** Le SPACON clique sur *Begin step 1*. L'état de l'étape
   passe à `in-progress`.
3. **Annoncer.** Le poste *responsable* de l'étape est appelé sur la boucle
   vocale (« AOCS, beginning ST1_POWER »).
4. **Demander le GO.** Le responsable demande le GO. Le FD fait le tour de table. Le FD autorise.
5. **Exécuter.** Le responsable clique sur la TC préremplie du
   panneau de commande et actionne la première clé. Seconde clé si nécessaire.
   Envoi.
6. **Vérifier.** Le responsable lit la télémesure de vérification sur la
   boucle. Le SPACON clique sur *Verify step 1* après confirmation.
7. **Recommencer** pour l'étape suivante.

Une procédure comporte habituellement de 5 à 15 étapes et dure de quelques minutes
(LEOP-006 *Synchronisation temporelle*) à 40 minutes (LEOP-007 *Mise sous tension
séquentielle*) en temps réel. L'ensemble nominal va de **NOM-001 à
NOM-013** ; notez que `nominal/clock_sync.md` est **NOM-008** et que
NOM-006 est *Chargement de logiciel* — une correspondance que l'ancien matériel pédagogique
présentait à l'envers.

### Sauter et suspendre

- **Sauter (Skip).** Autorisé uniquement si la vérification de l'étape confirme que
  l'état est déjà atteint (p. ex. l'étape dit « activer le réchauffeur batterie »
  mais la télémesure indique que le réchauffeur est déjà activé). Le saut est
  consigné avec la valeur de télémesure qui le justifie.
- **Suspendre (Hold).** Autorisé si l'opérateur a besoin de temps pour évaluer la situation. La
  procédure est mise en pause ; l'équipe peut se concerter ; le FD autorise la
  reprise. Les suspensions sont consignées avec leur durée.

Tout ce qui n'est ni un saut vérifié ni une suspension autorisée est une
**violation de procédure** — consignée comme telle dans la main courante et
discutée lors du débriefing.

## 7.5 Le panneau FDIR — fonctionnement

Les règles FDIR (détection, isolation et reprise des défaillances) se trouvent dans
`monitoring/s12_definitions.yaml` (règles de surveillance — ce qui est
surveillé) et `monitoring/s19_rules.yaml` (règles événement-action —
ce qu'il faut faire lorsque quelque chose se déclenche). Le panneau FDIR du MCS lit
les deux.

### Structure d'une règle

Chaque règle comporte :

- un **nom** (lisible, p. ex. `eps_overcurrent_payload`) ;
- le **paramètre** surveillé (p. ex. `eps.payload_line_current_a`) ;
- un **seuil** et une **durée de persistance** (p. ex. `> 0.6 A for > 2 s`) ;
- une **gravité** (niveau 0 informatif → niveau 4 candidat au mode
  survie). Ne confondez pas la **gravité** FDIR (0–4) avec le **niveau
  d'autonomie** bord (0–3) ; ce sont des échelles différentes et le manuel
  n'emploie jamais l'une pour l'autre ;
- une **action** — pour une règle S19, l'`action_func_id` que le satellite
  invoque de façon autonome lorsque son événement déclencheur survient (chaque règle
  porte un `ea_id`, un déclencheur et un identifiant de fonction). Les surveillances S12
  n'ont pas d'action ; elles lèvent un événement de dépassement de limite et alertent le
  sol.

Les deux fichiers constituent la liste des règles : **32 règles événement-action S19** et
**46 définitions de surveillance S12**. Lisez-les directement — il n'existe pas de
document d'index séparé.

### Échelle d'escalade de la gravité

Tableau 7.3 — Échelle de gravité FDIR, avec action par défaut et réponse attendue de l'opérateur à chaque niveau.

| Niveau | Signification | Action par défaut | Réponse de l'opérateur |
|-------|---------|----------------|-------------------|
| 0 | Information | Journalisation seule | Signaler sur la boucle ; aucune action |
| 1 | Attention | Journalisation + alerte | En discuter au prochain débriefing |
| 2 | Avertissement | Journalisation + alerte + atténuation autonome si elle est définie | Exécuter la procédure de reprise |
| 3 | Grave | Autonome + alerte sol + signalement pour le prochain passage | Exécuter la reprise + fiche d'anomalie |
| 4 | Critique | Candidat au mode survie (autonome si la règle le prévoit) | Confirmer le passage en mode survie, informer le responsable de mission |

Le panneau FDIR applique un code couleur selon la gravité. Un déclenchement de niveau 3 ou 4
fait apparaître le bandeau d'alerte rouge dans l'en-tête du MCS.

### Acquitter ou effacer

- **Acquitter.** L'opérateur confirme qu'il a vu le déclenchement de la
  règle. Coupe l'alerte sonore. N'efface PAS la règle ;
  le paramètre est toujours en infraction.
- **Effacer.** Possible uniquement lorsque le paramètre est revenu
  dans sa plage. La règle passe de « active » à « historique » dans le
  panneau. Toujours précédé d'une fiche d'anomalie.

### Forçage manuel

Une règle FDIR peut être désactivée par le SPACON avec l'autorisation du FD
(p. ex. pendant l'étalonnage d'un capteur réputé défaillant dont la lecture sortira de sa plage
pour une raison prévue). Les règles désactivées apparaissent sur
le panneau en gris avec la mention *Manual override*. Elles sont réactivées
au moyen d'une étape de procédure appariée.


![Architecture du segment sol : liaison RF entre le satellite et la station sol, composants du MOC (serveur TM/TC, MPS, FDS, archive), POC et interfaces externes.](../assets/figures/fig_ground_segment_architecture.svg)

*Architecture du segment sol : liaison RF entre le satellite et la station sol, composants du MOC (serveur TM/TC, MPS, FDS, archive), POC et interfaces externes.*

## 7.6 Introduction aux services PUS

Le satellite communique avec le sol au moyen de la **norme d'utilisation des paquets**
(*Packet Utilization Standard*, PUS, ECSS-E-ST-70-41C / CCSDS 660.0-G-3). Elle définit
un ensemble de *services* et de *sous-services* que le satellite doit
mettre en œuvre. Les opérateurs n'écrivent pas de trames PUS — c'est le MCS qui s'en charge — mais
ils lisent bel et bien des identifiants de services PUS dans les fichiers de procédure et dans le
panneau de commande.

EOSAT-1 déclare **quinze** services dans `mcs/pus_services.yaml`,
et tous les quinze figurent dans `commands/tc_catalog.yaml`. Les
sous-types de liaison montante (TC) ci-dessous sont ceux que le catalogue définit
réellement ; la colonne liaison descendante (TM) indique ce qui revient.

Tableau 7.5 — Les services PUS mis en œuvre sur EOSAT-1, avec leurs sous-services et leur rôle pour l'opérateur.

| Service | Sous-types TC | Sous-types TM | Rôle | Où vous le rencontrez |
|---|---|---|---|---|
| **S1** | — | 1, 2, 3, 4, 5, 7, 8 | Vérification des télécommandes | Chaque TC produit une chaîne S1 |
| **S2** | 1, 6 | 6 | Accès aux équipements | Marche/arrêt direct d'un équipement nommé — recette en orbite et contingence uniquement |
| **S3** | 5, 6, 27, 31 | 25 | Données de servitude | `HK_ENABLE` **S3.5**, `HK_DISABLE` S3.6, `HK_REQUEST` **S3.27**, `HK_SET_INTERVAL` S3.31 ; le paquet HK lui-même est TM(3,25) |
| **S5** | 5, 6 | 1, 2, 3, 4 | Signalement d'événements | `EVENT_ENABLE`/`EVENT_DISABLE` ; le sous-type du rapport **est** la gravité |
| **S6** | 2, 5, 9 | 6, 10 | Gestion de la mémoire | Lecture/écriture/somme de contrôle de la mémoire de l'OBC (avancé) |
| **S8** | 1 | — | Gestion des fonctions | Le plus important — invoquer une fonction par son `func_id` |
| **S9** | 1, 2 | 2 | Gestion du temps | `SET_TIME` S9.1, `REQUEST_TIME` S9.2 |
| **S11** | 4, 7, 9, 11, 13, 17 | 5, 18 | Commande datée | Plan bord ; `SCHEDULE_TC` est S11.4 |
| **S12** | 1, 2, 3, 4, 6, 7, 12 | 9, 13 | Surveillance bord | Les 46 définitions de surveillance |
| **S13** | 1, 3, 5, 9 | 2, 4, 10 | Transfert de gros volumes de données | Séance de liaison descendante d'images scientifiques |
| **S15** | 1, 2, 9, 11, 13 | 14 | Stockage à bord | Les quatre mémoires de paquets (HK, événements, science, alarmes) |
| **S17** | 1 | 2 | Test de connexion | Test de santé de la liaison |
| **S18** | 1, 2, 3, 4, 6 | 7 | Procédures de contrôle bord | Chargement / démarrage / arrêt / rapport des OBCP |
| **S19** | 1, 2, 4, 5, 8 | 128 | Événement-action | Les 32 règles FDIR autonomes ; `EA_ENABLE` S19.4, `EA_DISABLE` S19.5 |
| **S20** | 1, 3 | 2 | Gestion des paramètres | `SET_PARAM` S20.1, `GET_PARAM` S20.3 |

Trois pièges PUS méritent d'être mémorisés, car ce sont ceux que
les éditions précédentes de ce cours présentaient de façon erronée :

- **`HK_ENABLE` est S3.5 et `HK_REQUEST` est S3.27.** Ni le sous-type 1,
  ni le sous-type 25 — 25 est le *paquet HK transmis au sol*, et non une
  demande de paquet.
- **S8 n'a qu'un seul sous-type : 1.** Il n'existe aucun schéma dans lequel
  le sous-type S8 désigne le sous-système. Le sous-système est implicite dans le
  bloc de `func_id`, et le `func_id` est le premier octet du
  champ de données de la TC.
- **Seules les SID 1 (EPS) et 11 (balise) sont activées à l'amorçage**
  (`simulation.yaml: default_enabled_sids: [1, 11]`, réappliqué par
  le moteur à chaque amorçage du logiciel applicatif). Tout le reste — AOCS,
  TCS, OBDH, charge utile, TT&C, la structure EPS étendue, PROP —
  nécessite un `HK_ENABLE` explicite.

La table des identifiants de structures HK (`telemetry/hk_structures.yaml`) est la suivante :

Tableau 7.5b — Identifiants des structures de télémesure de servitude, contenu et cadence de transmission.

| SID | Contenu | Période |
|---|---|---|
| 1 | EPS | 1 s (activée à l'amorçage) |
| 2 | AOCS | 4 s |
| 3 | TCS | 60 s |
| 4 | Plateforme / OBDH | 8 s |
| 5 | Charge utile | 8 s |
| 6 | TT&C | 8 s |
| 7 | Détermination SCAO | 4 s |
| 8 | Gestion de puissance de l'EPS (étendue) | 8 s |
| 9 | PROP | 8 s |
| 11 | Balise | 30 s (activée à l'amorçage) |

C'est **S8** que vous rencontrerez le plus souvent dans les procédures — c'est le moyen par lequel le
sol demande au satellite de faire autre chose que transmettre de la
télémesure ou accepter une modification de paramètre. Chaque invocation S8
porte un *identifiant de fonction*. Le catalogue des identifiants de fonction d'EOSAT-1 se trouve dans
`commands/tc_catalog.yaml` ; la référence générée, exacte au bit près —
chaque argument avec son type, son décalage, son unité, son facteur d'échelle, sa plage et un
exemple hexadécimal résolu — est `manual/09_command_reference.md`. Un
sous-ensemble de travail figure au §7.7 ci-dessous.

## 7.7 Fonctions bord (identifiant de fonction S8 — sous-ensemble de travail de l'opérateur)

La base de données des télécommandes d'EOSAT-1 (`commands/tc_catalog.yaml`) définit les
identifiants de fonction S8 **0–98** pour l'ensemble des sous-systèmes, un bloc hérité
**100–107** pour les boutons d'action rapide EPS/TCS, le bloc
propulsion **108–118**, et 119 (`PAYLOAD_SET_SHUTTER`). Les tableaux
ci-dessous listent tous les identifiants de fonction que l'opérateur rencontrera au cours d'un
passage opérationnel typique, regroupés par poste détenteur de
l'autorité de commande. Ils sont extraits directement de
`tc_catalog.yaml` — le fichier catalogue fait foi,
et `manual/09_command_reference.md` est généré à partir de lui.

**Les arguments se placent à l'intérieur des accents graves.** Le catalogue comporte désormais
un schéma d'arguments typé — nom, type, décalage en octets, unité,
étalonnage brut↔physique, plage autorisée et valeur par défaut — si bien qu'il
existe une bonne réponse pour chaque argument et aucune raison d'écrire
un nom de commande nu. Écrivez `PAYLOAD_COOLER_SETPOINT(setpoint=-15.0 degC)`,
et non « PAYLOAD_COOLER_SETPOINT, setpoint moins quinze ». Les valeurs
hors de la plage déclarée sont **rejetées** avec l'erreur TM(1,8)
0x0003, et jamais écrêtées silencieusement.

### AOCS (func_id 0–15, 84–91, 96)

Tableau 7.6a — Identifiants de fonction S8 du SCAO pour la commande des modes, des roues, des capteurs et
des actionneurs.

| Func ID | Nom | Rôle |
|---|---|---|
| 0 | `AOCS_SET_MODE(mode=…)` | Régler le mode du SCAO. `mode` uint8 : 0=OFF, 1=SAFE_BOOT, 2=DETUMBLE, 3=COARSE_SUN, 4=NOMINAL (nadir), 5=FINE_POINT, 6=SLEW, 7=DESAT, 8=ECLIPSE, 9=INERTIAL. Le mode 5 est refusé avec TM(1,8) sauf si le masque de bits de préconditions `aocs.fine_ready` (0x02C5) vaut 0 |
| 1 | `AOCS_DESATURATE` | Lancer la désaturation des roues (sans argument) |
| 2 | `AOCS_DISABLE_WHEEL(wheel_idx=0…3)` | Désactiver une roue de réaction donnée |
| 3 | `AOCS_ENABLE_WHEEL(wheel_idx=0…3)` | Activer une roue de réaction donnée |
| 4 | `ST1_POWER(on=0/1)` | Marche/arrêt du senseur stellaire 1 |
| 5 | `ST2_POWER(on=0/1)` | Marche/arrêt du senseur stellaire 2 |
| 6 | `ST_SELECT(unit=1/2)` | Sélectionner le senseur stellaire principal (1=ST1, 2=ST2 ; 0 est refusé) — il y a **deux** têtes |
| 7 | *(retirée)* | Anciennement `MAG_SELECT`. EOSAT-1 embarque un **seul** magnétomètre : il n'y a rien à sélectionner ; la fonction 7 est refusée à bord avec 0x0007 |
| 8 | `RW_SET_SPEED_BIAS(wheel_idx=…, bias_rpm=… RPM)` | Biais de vitesse de roue, float32. Le biais est **ajouté** à la vitesse actuelle de la roue |
| 9 | `MTQ_ENABLE(enable=0/1)` | Activer / désactiver les magnétocoupleurs |
| 10 | `AOCS_SLEW_TO(q_x, q_y, q_z, q_w, rate_dps)` | Basculement vers un quaternion cible, cinq float32 |
| 11 | `AOCS_CHECK_MOMENTUM` | Interroger l'état du moment cinétique des roues |
| 12 | `AOCS_BEGIN_ACQUISITION` | Lancer l'acquisition d'attitude automatique |
| 13 | `AOCS_GYRO_CALIBRATION` | Exécuter l'étalonnage du biais des gyros **à bord**. Il ne s'agit pas de l'envoi d'un biais calculé au sol |
| 14 | `AOCS_RW_RAMP_DOWN(wheel_idx=…, target_rpm=… RPM)` | Ralentir progressivement une ou plusieurs roues ; `wheel_idx=255` désigne les quatre |
| 15 | `AOCS_SET_DEADBAND(deadband_deg=… deg)` | Régler la bande morte de l'erreur d'attitude, float32 |

Les vitesses de roue elles-mêmes sont de la télémesure en **lecture seule**
(0x0207–0x020A, températures 0x0218–0x021B) ; les fonctions 8 et 14 sont
la seule voie de commande pour les modifier. Le pointage fin fonctionne sur **trois**
roues — le bit 1 du masque de bits `aocs.fine_ready` 0x02C5 signifie
« moins de trois roues », et non moins de quatre.

Ajouts ultérieurs au SCAO (console Dynamique du vol, fonctions 84–91 et 96) :
84 `AOCS_GPS_SET_START_MODE`, 85 `AOCS_SET_POINTING_FRAME`,
86 `AOCS_SET_TARGET_QUAT`, 87 `AOCS_SET_TARGET_GEO(lat, lon, alt_m)`,
88 `AOCS_SET_CONTROL_BW(omega_n, zeta)`, 89 `AOCS_FINE_READY_CHECK`,
90 `AOCS_SET_MOM_MGMT(enable, entry_pct, exit_pct)`,
91 `AOCS_EST_RESET(mode=0 cold / 1 warm)`,
96 `AOCS_SET_DESAT_INHIBIT(inhibit=0/1)`.

### EPS (func_id 16–25, 81–83)

Tableau 7.6b — Identifiants de fonction S8 de l'EPS pour la commande des lignes d'alimentation, le
délestage, le déploiement des ailes, ainsi que les activations du refroidisseur et du transpondeur qui
se trouvent physiquement sur le bus de distribution de l'EPS.

| Func ID | Nom | Rôle |
|---|---|---|
| 16 | `EPS_PAYLOAD_MODE(mode=0/1/2)` | Mode d'alimentation de la charge utile (0=arrêt, 1=attente, 2=prise de vue) |
| 17 | `EPS_FPA_COOLER(on=0/1)` | Activer / désactiver la ligne du cryoréfrigérateur du FPA |
| 18 | `EPS_TRANSPONDER_TX(on=0/1)` | Activer / désactiver l'émission du transpondeur |
| 19 | `EPS_POWER_ON(line_index=0…8)` | Mettre une ligne d'alimentation sous tension (ON) |
| 20 | `EPS_POWER_OFF(line_index=0…8)` | Mettre une ligne d'alimentation hors tension (OFF) |
| 21 | `EPS_RESET_OC_FLAG(line_index=0…8)` | Réinitialiser l'indicateur de disjonction sur surintensité, réactiver la ligne |
| 22 | `EPS_SWITCH_LOAD(load_id=…, state=0/1)` | Commuter une charge électrique individuelle en marche/arrêt |
| 23 | `EPS_SET_CHARGE_RATE(rate_a=… A)` | Forcer le courant de charge de la batterie, float32 |
| 24 | `EPS_SOLAR_ARRAY_DRIVE(angle_deg=… deg)` | Orienter le générateur solaire, int16 |
| 25 | `EPS_EMERGENCY_LOAD_SHED(stage=0…3)` | Délestage immédiat |
| 81 | `EPS_DEPLOY_WING(wing=0/1/2)` | Déploiement d'aile par fil thermofusible (0=+Y, 1=−Y, 2=les deux) |
| 82 | `EPS_WING_STATUS` | Interroger l'état de déploiement des ailes (0x0144) |
| 83 | `EPS_SET_MODE(mode=…)` | Régler le mode de l'EPS |

**Il y a neuf lignes d'alimentation, d'indices 0 à 8**, et non sept :
0 `obc`, 1 `ttc_rx`, 2 `ttc_tx`, 3 `payload`, 4 `fpa_cooler`,
5 `htr_bat`, 6 `htr_obc`, 7 `aocs_wheels`, 8 `prop`. Les lignes 0 et 1
ne sont pas commutables et sont toujours sous tension ; **toute ligne commutable est
à OFF par défaut**, ce qui explique qu'un satellite fraîchement amorcé produise de la
télémesure et ne fasse rien d'autre tant que l'opérateur n'a pas mis les équipements
sous tension. Les indicateurs d'état des lignes sont 0x0110–0x0117 (ligne 8, prop, en 0x014A) et les courants
par ligne 0x0118–0x011F (ligne 8 en 0x014B) ; l'état de déploiement des ailes est 0x0144 (bit 0
+Y, bit 1 −Y, bits 4/5 en cours), avec les courants par aile en
0x0146 (+Y) et 0x0147 (−Y).

### Charge utile (func_id 26–39, 92–95, 119)

Tableau 7.6c — Identifiants de fonction S8 de la charge utile pour le mode de l'imageur, l'acquisition,
la gestion des scènes, l'étalonnage et la configuration du détecteur.

| Func ID | Nom | Rôle |
|---|---|---|
| 26 | `PAYLOAD_SET_MODE(mode=0…3)` | 0=OFF, 1=STANDBY, 2=IMAGING, **3=CALIBRATION**. Les modes 1/2/3 demandent tous le refroidisseur du FPA ; le mode 0 le libère |
| 27 | `PAYLOAD_SET_SCENE(scene_id=…)` | Régler l'identifiant de scène pour la prise de vue, uint16 |
| 28 | `PAYLOAD_CAPTURE(scene_id=…, lines=…)` | Déclencher l'acquisition — **caution** |
| 29 | `PAYLOAD_DOWNLOAD_IMAGE(scene_id=…)` | Mettre une image en file pour la liaison descendante |
| 30 | `PAYLOAD_DELETE_IMAGE(scene_id=…)` | Supprimer une image de la mémoire — **caution** |
| 31 | `PAYLOAD_MARK_BAD_SEGMENT(segment_id=…)` | Marquer un segment mémoire comme inutilisable — **caution** |
| 32 | `PAYLOAD_GET_IMAGE_CATALOG` | Demander le catalogue des images stockées |
| 33 | `PAYLOAD_SET_BAND_CONFIG(mask=…)` | Masque d'activation des bandes spectrales (443/560/665/865 nm) |
| 34 | `PAYLOAD_SET_INTEGRATION_TIME(blue_ms, green_ms, red_ms, nir_ms)` | Temps d'intégration par bande, uint16 ms chacun |
| 35 | `PAYLOAD_SET_GAIN(gain=… ×)` | Gain du détecteur, uint16 |
| 36 | `PAYLOAD_COOLER_SETPOINT(setpoint=… degC)` | Consigne de régulation du FPA — **caution**. Le champ transmis est un **uint16 en centikelvins** : `raw = round((T_degC + 273.15) × 100)`, si bien que −15,00 °C donne 25815 = `0x64D7`. Plage physique −20…0 °C (brut 25315…27315) ; en dehors, la TC est **rejetée** avec S1.8 / 0x0003, et non écrêtée |
| 37 | `PAYLOAD_START_CALIBRATION(mode=0/1/2)` | 0=DARK, 1=FLAT, 2=BOTH. S'exécute depuis le mode STANDBY **ou** CALIBRATION — **jamais** depuis IMAGING |
| 38 | `PAYLOAD_STOP_CALIBRATION` | Interrompre l'étalonnage |
| 39 | `PAYLOAD_SET_COMPRESSION(algorithm=…, ratio=… ×)` | Forcer la compression |
| 92 | `PAYLOAD_SELECT_FILTER(position=…)` | Position de la roue à filtres |
| 93 | `PAYLOAD_CYCLE_SHUTTER(cycles=… transitions)` | Manœuvre relative de l'obturateur |
| 94 | `PAYLOAD_INITIATE_TRANSFER(scene_id=…)` | Lancer un transfert d'image |
| 95 | `PAYLOAD_CAL_LAMP(on=0/1)` | Lampe d'étalonnage |
| 119 | `PAYLOAD_SET_SHUTTER(position=0/1)` | Amener l'obturateur à une position **absolue** (0=CLOSED, 1=OPEN) — **caution**. Idempotente, c'est le seul moyen d'atteindre un état *connu* de l'obturateur |

L'étalonnage a son propre vocabulaire de refus, de sorte que la console vous indique
quelle condition a échoué au lieu d'afficher « invalide dans le mode
actuel » de cinq façons différentes : **0x0024** refus pour cause d'IMAGING,
**0x0025** FPA non prêt thermiquement (0x0610), **0x0026** obturateur dans
la mauvaise position (0x063C), **0x0027** lampe d'étalonnage dans le
mauvais état (0x0615), **0x0028** acquisition tentée avec
l'obturateur fermé. Les codes 0x0021–0x0023 restent les conditions de pointage
pour l'acquisition (pas en FINE_POINT / erreur de pointage > 0,05° / vitesse > 0,005 °/s).
L'étalonnage d'obscurité n'exige plus le mode IMAGING.

### TCS (func_id 40–49)

Tableau 7.6d — Identifiants de fonction S8 du TCS pour les trois circuits de réchauffeurs,
le refroidisseur du FPA, les consignes de thermostat et la décontamination.

| Func ID | Nom | Rôle |
|---|---|---|
| 40 | `HEATER_BATTERY(on=0/1)` | Marche/arrêt du réchauffeur batterie |
| 41 | `HEATER_OBC(on=0/1)` | Marche/arrêt du réchauffeur de l'OBC |
| 42 | `HEATER_THRUSTER(on=0/1)` | Marche/arrêt du réchauffeur du propulseur (lit catalytique) |
| 43 | `FPA_COOLER(on=0/1)` | Marche/arrêt du refroidisseur du FPA (activation côté TCS) |
| 44 | `HEATER_SET_SETPOINT(circuit=…, on_temp=… degC, off_temp=… degC)` | Plage de thermostat d'un circuit, deux float32 |
| 45 | `HEATER_AUTO_MODE(circuit=…)` | Remettre le réchauffeur sous thermostat autonome |
| 46 | `TCS_SET_HEATER_DUTY_LIMIT(circuit=…, max_duty_pct=… %)` | Limiter le rapport cyclique du réchauffeur |
| 47 | `TCS_DECONTAMINATION_START(target_temp_c=… degC)` | Lancer le chauffage de décontamination |
| 48 | `TCS_DECONTAMINATION_STOP` | Interrompre la décontamination |
| 49 | `TCS_GET_THERMAL_MAP` | Demander l'état thermique de toutes les zones |

Le refroidisseur du FPA est un **cryoréfrigérateur Stirling miniature**, et non un
empilement Peltier, et son efficacité diminue à mesure que l'écart de
température augmente (`fpa_cooler_carnot_fraction`, 0,23). Deux
points de télémesure existent précisément pour que l'opérateur puisse le constater :
`tcs.fpa_cooler_floor_c` (0x0424), la température la plus froide que le
refroidisseur peut effectivement tenir dans l'état thermique présent, et
`tcs.fpa_cooler_margin_k` (0x0425), la marge entre ce plancher
et la consigne commandée. Une consigne inférieure au plancher n'est pas un
défaut — c'est une demande que la physique ne peut satisfaire.

### OBDH / SPACON (func_id 50–62, 80)

Tableau 7.6e — Identifiants de fonction S8 de l'OBDH pour le mode de l'OBC, le redémarrage, la sélection
de la redondance, le chien de garde et la synchronisation temporelle.

| Func ID | Nom | Rôle |
|---|---|---|
| 50 | `OBC_SET_MODE(mode=0/1/2)` | Régler le mode de l'OBC (0=nominal, 1=survie, 2=urgence) |
| 51 | `OBC_MEMORY_SCRUB` | Déclencher un nettoyage manuel de la mémoire |
| 52 | `OBC_REBOOT` | Forcer le redémarrage de l'OBC (retour au chargeur d'amorçage) — **critical** |
| 53 | `OBC_SWITCH_UNIT` | Basculer sur l'OBC redondant — **critical** |
| 54 | `OBC_SELECT_BUS(bus=0/1)` | Sélectionner le bus CAN actif (0=A, 1=B) — **caution** |
| 55 | `OBC_BOOT_APP` | Amorcer le logiciel applicatif depuis le chargeur d'amorçage — **caution**. Sans argument |
| 56 | `OBC_BOOT_INHIBIT(inhibit=0/1)` | Inhiber l'amorçage automatique (rester dans le chargeur d'amorçage) |
| 57 | `OBC_CLEAR_REBOOT_CNT` | Remettre à zéro le compteur de redémarrages |
| 58 | `OBC_SET_WATCHDOG_PERIOD(period_ticks=…)` | Configurer le délai du chien de garde, uint16 |
| 59 | `OBC_WATCHDOG_ENABLE` | Activer la surveillance par chien de garde |
| 60 | `OBC_WATCHDOG_DISABLE` | Désactiver la surveillance par chien de garde |
| 61 | `OBC_DIAGNOSTIC` | Demander un diagnostic de santé de l'OBC |
| 62 | `OBC_ERROR_LOG` | Demander les entrées récentes du journal d'erreurs |
| 80 | `OBC_GPS_TIME_SYNC` | Synchroniser l'horloge de bord sur le GPS — **caution** (peut invalider la solution d'attitude du SCAO ; rétablir avec `AOCS_EST_RESET`, fonction 91) |

`OBC_BOOT_APP` amorce l'image applicative et ne fait rien d'autre.
Elle portait autrefois un alias `SET_PHASE` ; cet alias a été **supprimé**
en 2026-08, car amorcer une image logicielle n'a rien à voir
avec la phase de la mission, et la mnémonique incitait les opérateurs
qui cherchaient à faire avancer la phase à redémarrer l'OBC. Il n'existe aucune
télécommande de phase — voir §7.1.

### TT&C (func_id 63–79, 97–98)

Tableau 7.6f — Identifiants de fonction S8 du TT&C pour la commutation des transpondeurs, le
débit, la puissance d'émission, la modulation, le mode de liaison descendante, les deux balises et la
mesure de distance (ranging).

| Func ID | Nom | Rôle |
|---|---|---|
| 63 | `TTC_SWITCH_PRIMARY` | Basculer sur le transpondeur principal |
| 64 | `TTC_SWITCH_REDUNDANT` | Basculer sur le transpondeur redondant |
| 65 | `TTC_SET_DATA_RATE(rate=0/1)` | Sélectionner un palier de l'échelle de débits TM : **0 = LOW (16 kbit/s, BPSK, conv(7,1/2)+RS) — opérations de routine** ; **1 = HIGH (128 kbit/s, QPSK, RS(255,223)) — vidages uniquement**. 255 = BEACON (1 kbit/s) ne se sélectionne pas ici |
| 66 | `TTC_PA_ON` | Activer l'amplificateur de puissance bande S |
| 67 | `TTC_PA_OFF` | Désactiver l'amplificateur de puissance bande S |
| 68 | `TTC_SET_TX_POWER(level=0/1/2)` | **0 = LOW 1.0 W, 1 = NOMINAL 2.0 W, 2 = HIGH 5.0 W** RF — **caution**. 5 W est le plafond (`pa_max_power_w`) ; un code inconnu est rejeté avec 0x0003, jamais écrêté |
| 69 | `TTC_DEPLOY_ANTENNA` | Déployer l'antenne du satellite (fil thermofusible) |
| 70 | `TTC_SET_BEACON_MODE(on=0/1)` | Verrouiller la chaîne bande S sur son palier balise à 1 kbit/s |
| 71 | `TTC_CMD_CHANNEL_START` | Ouvrir le canal de commande dédié (15 min) |
| 72 | `TTC_SET_UL_FREQ(freq_mhz=… MHz)` | Régler la fréquence de liaison montante, float32 |
| 73 | `TTC_SET_DL_FREQ(freq_mhz=… MHz)` | Régler la fréquence de liaison descendante, float32 |
| 74 | `TTC_SET_MODULATION(mode=0…3)` | 0=BPSK, 1=QPSK, 2=8PSK, 3=OQPSK |
| 75 | `TTC_SET_RX_GAIN(agc_db=… dB)` | Régler la consigne de CAG du récepteur, float32 |
| 76 | `TTC_RANGING_START` | Lancer une séquence de mesure de distance (ranging) |
| 77 | `TTC_RANGING_STOP` | Arrêter la séquence de mesure de distance |
| 78 | `TTC_SET_COHERENT_MODE(on=0/1)` | Marche/arrêt du mode cohérent du transpondeur |
| 79 | `TTC_SET_DOWNLINK_MODE(on=0/1)` | Entrer dans le mode DOWNLINK (vidage de la charge utile) ou en sortir. **C'est le verrou du palier HIGH** |
| 97 | `TTC_BEACON_TX_ON` | Mettre en marche l'**émetteur de balise UHF à antenne fouet** |
| 98 | `TTC_BEACON_TX_OFF` | Arrêter l'émetteur de balise UHF — **caution** |

**Trois paliers, pas deux.** L'échelle de débits TM de
`subsystems/ttc.yaml` est BEACON / LOW / HIGH = **1 / 16 /
128 kbit/s**. Le codage historique des arguments a été conservé tel quel —
`rate=0` signifie toujours « le débit bas » et `rate=1` toujours « le
débit haut » — mais ces valeurs sélectionnent désormais 16 kbit/s et 128 kbit/s au lieu
des 1 kbit/s et 64 kbit/s de l'ancienne configuration. HIGH est refusé
avec S1.8 / 0x0007 sauf si l'antenne est déployée, le mode DOWNLINK
est activé (fonction 79) et l'élévation est d'au moins 10°. Surveillez côte à côte les deux
paramètres de palier : `ttc.tm_tier_cmd` (0x053A) est ce que vous
avez demandé et `ttc.tm_tier` (0x0539) ce qui est réellement émis après les
verrous — une rétrogradation se manifeste par un désaccord entre les deux.

**Deux émetteurs, qui tombent en panne indépendamment.** EOSAT-1
emporte une chaîne principale en bande S (2025 MHz en montée / 2200 MHz en descente,
2 W nominaux, toute la HK temps réel, la relecture, les vidages d'images et la vérification
S1) *et* une balise UHF séparée à antenne fouet (437,5 MHz, 1 W
dans un dipôle, 1 kbit/s, transportant la HK **SID 11 et rien d'autre**).
Ce sont des radios distinctes, avec des amplificateurs, des antennes et des bilans
de liaison distincts. Les fonctions 66/67 et la ligne EPS `ttc_tx` coupent la liaison descendante
en **bande S** — `ttc.tx_active` (0x0525) passe à 0 et la télémesure bande S
s'interrompt — tandis que la balise continue d'émettre : `ttc.beacon_tx_on`
(0x0526) et `ttc.beacon_active` (0x0527) en sont indépendants par
construction. C'est ce qui permet de répondre à la question « l'OBC est-il vivant ? »
lorsque la chaîne principale est hors service. Ne confondez ni l'un ni l'autre avec
`ttc.beacon_mode` (0x0521), qui est un *échelon de l'échelle bande S*
sélectionné par la fonction 70 — trois choses différentes qui partagent un même mot.

### Propulsion (func_id 108–118)

Tableau 7.6g — Identifiants de fonction S8 de la propulsion. EOSAT-1 emporte un module de
monergol vert de 1U offrant **66,9 m/s** de delta-V total, utilisé pour
l'évitement de débris, un maintien d'orbite limité et la poussée de 34,3 m/s
d'abaissement du périgée en fin de vie (NOM-014). Ces fonctions relèvent de la console propulsion.

| Func ID | Nom | Rôle |
|---|---|---|
| 108 | `PROP_ARM(arm_code=…)` | Armer le module de propulsion — **critical** |
| 109 | `PROP_DISARM` | Revenir à l'état SAFED |
| 110 | `PROP_SET_BURN(dv_m_s=… m/s, direction=…, mode=…, t_start_cuc=… s)` | Charger une poussée — **critical** |
| 111 | `PROP_EXECUTE` | Exécuter la poussée chargée et armée |
| 112 | `PROP_ABORT` | Interrompre une poussée en cours |
| 113 | `PROP_ISO_OPEN(branch=…)` | Ouvrir une branche à vanne à verrouillage |
| 114 | `PROP_ISO_CLOSE(branch=…)` | Fermer une branche à vanne à verrouillage |
| 115 | `PROP_SET_LIMITS(att_err_max_deg, p_min_bar, catbed_max_c, t_burn_max_s)` | Régler les limites des verrous d'armement |
| 116 | `PROP_INHIBIT_SET(on=0/1)` | Verrouiller l'inhibition de la propulsion |
| 117 | `PROP_INHIBIT_CLR(key=…)` | Lever l'inhibition avec la clé |
| 118 | `PROP_GET_STATUS` | Rendre compte de l'état de la propulsion |

Chaque verrou d'armement possède son propre code d'échec (0x0B01–0x0B13),
reflet de l'`arm_inhibit_mask` en 0x0B15, si bien qu'un refus nomme la
condition au lieu de renvoyer un « non autorisé » générique. La télémesure
de propulsion commence en 0x0B00 et circule dans la HK **SID 9**. Une poussée entraîne le recalcul
du jeu d'éléments à bord, si bien que les passages et les éclipses se déplacent réellement
ensuite (1 m/s donne environ +1,800 km de demi-grand axe et
−33,5 s sur l'heure de passage à +24 h) — relisez le planning des contacts
après chaque manœuvre. La vitesse de simulation est limitée à ≤ 10× pendant
une poussée.

### Ce que vous ne trouverez *pas* dans le simulateur

Le manuel faisait autrefois référence à quelques noms de commandes « naturels » qui
ne figurent *pas* dans `tc_catalog.yaml`. Utilisez les solutions de remplacement ci-dessous :

| Ancien nom du manuel | À utiliser à la place |
|---|---|
| `OBC_NOOP` | (pas de commande de signal de vie ; le chien de garde gère la vivacité) |
| `OBC_WATCHDOG_KICK` | `OBC_WATCHDOG_ENABLE` (59) et `OBC_SET_WATCHDOG_PERIOD` (58) |
| `FDIR_LOAD_TABLE` | Activer/désactiver individuellement les règles avec `EA_ENABLE` (S19.4) et `EA_DISABLE` (S19.5) ; voir le chapitre 15 |
| `FDIR_ENABLE_RULE` / `FDIR_DISABLE_RULE` | `EA_ENABLE` / `EA_DISABLE` (S19.4 / S19.5) |
| `EPS_LOAD_SHED` | `EPS_EMERGENCY_LOAD_SHED` (25), étage 0–3 |
| `TCS_HEATER_ENABLE` / `TCS_HEATER_DISABLE` | Commandes par circuit `HEATER_BATTERY` / `HEATER_OBC` / `HEATER_THRUSTER` (40/41/42) avec `on=0/1` |
| `FPA_COOLER_ENABLE` | `EPS_FPA_COOLER` (17) et/ou `FPA_COOLER` (43) |
| `IMU_ENABLE` | Les gyros sont trois **équipements alimentables individuellement** — `S2_AOCS_GYROSCOPE_0/1/2`, d'identifiants d'équipement 0x0206, 0x0207, 0x0208 — commandés avec S2.1 `(device_id, state)`. Il n'y a ni centrale inertielle redondante, ni ligne d'alimentation de centrale inertielle, ni délai de démarrage à froid ; l'étalonnage du biais se fait à bord avec `AOCS_GYRO_CALIBRATION` (13) |
| `STAR_TRACKER_ENABLE` | `ST1_POWER` (4), `ST2_POWER` (5), `ST_SELECT` (6) |
| `WHEEL_ENABLE` / `WHEEL_DISABLE` | `AOCS_ENABLE_WHEEL` (3) / `AOCS_DISABLE_WHEEL` (2) |
| `MAGNETOTORQUER_ENABLE` | `MTQ_ENABLE` (9) |
| `MOMENTUM_DUMP_INITIATE` | `AOCS_DESATURATE` (1) |
| `TTC_TX_ENABLE` / `TTC_TX_DISABLE` | `EPS_TRANSPONDER_TX` (18) ou `EPS_POWER_ON/OFF(line_index=2)` pour la ligne `ttc_tx`, plus `TTC_PA_ON` / `TTC_PA_OFF` (66/67). Toutes ces commandes coupent uniquement la liaison descendante en **bande S** |
| `TTC_BEACON_ENABLE` | Déterminez de quelle balise il s'agit. L'**émetteur de balise UHF à antenne fouet** est `TTC_BEACON_TX_ON` / `TTC_BEACON_TX_OFF` (97/98). Le **échelon balise bande S à 1 kbit/s** est `TTC_SET_BEACON_MODE` (70) |
| `PAYLOAD_POWER_ON` / `PAYLOAD_POWER_OFF` | `EPS_POWER_ON(line_index=3)` (19) puis `PAYLOAD_SET_MODE` (26) |
| `PAYLOAD_MODE_SET` | `PAYLOAD_SET_MODE` (26) |
| `IMAGE_ACQUIRE` | `PAYLOAD_CAPTURE` (28) |
| `PAYLOAD_CALIBRATE` | `PAYLOAD_START_CALIBRATION(mode=0/1/2)` (37) |
| `SET_PHASE` | Rien. L'alias a été supprimé ; la phase de la mission est déclarée uniquement par la direction de la mission (§7.1) |
| `SHUTTER_OPEN` / `SHUTTER_CLOSE` | `PAYLOAD_SET_SHUTTER(position=0/1)` (119) — absolue, idempotente |
| `STORAGE_REQUEST_DOWNLINK` | `S13_CREATE_TRANSFER` (S13.1) puis interroger `S13_REPORT_STATUS` (S13.9) |

Le catalogue complet, y compris les identifiants hérités d'action rapide (100–107)
qui pilotent les boutons des vues EPS/TCS du MCS, se trouve dans
`commands/tc_catalog.yaml`, restitué au bit près dans
`manual/09_command_reference.md`.

## 7.8 Commandes directes et commandes pilotées par procédure

Tableau 7.12 — Quand utiliser chaque voie de commande (pilotée par procédure, directe, PUS brut), avec le risque associé.

| Voie | Quand l'utiliser | Risque |
|---|---|---|
| **Pilotée par procédure** | Chaque fois qu'une procédure existe pour ce que vous faites. | Le plus faible. Les paramètres de la commande préremplie sont validés. |
| **Directe depuis le panneau de commande** | (a) Actions ponctuelles pendant la reprise après anomalie, avec l'autorisation explicite du FD ; (b) les étapes « à corriger tout de suite » que vous avez répétées. | Erreurs de saisie de l'opérateur, paramètres mal mémorisés. Toujours plus lent que la voie procédure. |
| **Trame PUS brute** | Presque jamais. Réservée au débogage du simulateur. | Élevé. Aucune sécurité. |

Par défaut, la voie est *toujours* pilotée par procédure. Si vous avez
besoin d'une commande directe, demandez-vous : *existe-t-il une procédure que je devrais
charger d'abord ?*

## 7.9 Raccourcis clavier

Les raccourcis clavier ne sont pas normalisés d'un déploiement du MCS à l'autre — ils
diffèrent selon les installations et selon les postes de travail des opérateurs. Reportez-vous
à la carte aide-mémoire de votre installation pour les conventions locales
(focus sur la télémesure, focus sur la commande, sélecteur de commandes, affectation de la première /
seconde clé, marquage de l'heure dans le journal).

## 7.10 Pour aller plus loin

Tableau 7.14 — Fichiers sources et chemins de configuration pour la télémesure, les limites, les procédures et les catalogues de commandes.

| Thème | Source |
|---|---|
| Manuels des sous-systèmes | `configs/eosat1/manual/0*.md` |
| Référence des commandes générée | `configs/eosat1/manual/09_command_reference.md` |
| Analyses des rôles par poste | `configs/eosat1/mcs/role_analysis/*.md` |
| Onglets par poste / contrôle des commandes | `configs/eosat1/mcs/positions.yaml` |
| Paramètres de télémesure | `configs/eosat1/telemetry/parameters.yaml` |
| Structures HK et SID | `configs/eosat1/telemetry/hk_structures.yaml` |
| Politique de péremption de l'affichage | `configs/eosat1/mcs/staleness.yaml` |
| Limites de télémesure | `configs/eosat1/mcs/limits.yaml` |
| Lien alarme → procédure | `configs/eosat1/mcs/alarm_procedures.yaml` |
| Codes des modes du SCAO (référence) | `configs/eosat1/aocs/aocs_mode_codes.yaml` |
| Index des procédures | `configs/eosat1/procedures/procedure_index.yaml` |
| Règles FDIR | `configs/eosat1/monitoring/s19_rules.yaml` |
| Règles de surveillance | `configs/eosat1/monitoring/s12_definitions.yaml` |
| Mise en œuvre des services PUS | `configs/eosat1/mcs/pus_services.yaml` |
| Catalogue des commandes | `configs/eosat1/commands/tc_catalog.yaml` |
| Géométrie des stations sol (référence) | `configs/eosat1/orbit.yaml` |
| Compléments RF des stations sol | `configs/eosat1/planning/ground_stations.yaml` |
| Échelle de débits TM | `configs/eosat1/subsystems/ttc.yaml` |

Références externes :

- ECSS-E-ST-70-41C — *Packet Utilization Standard* —
  [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/)
- CCSDS 660.0-G-3 — livre vert PUS —
  [public.ccsds.org](https://public.ccsds.org/Pubs/660x0g3.pdf)
- ECSS-E-ST-70-11C — *Space segment operability* —
  [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/)
- ECSS-E-ST-70-32C — *Test and operations procedures* —
  [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/)

---


### 7.20 Chapitre 20 — Architecture du segment sol et des opérations

> **Lectures attendues avant cette séance.** Manuel en libre accès *Conception concourante d'engins spatiaux* (REL), chap. 17, §§ 17.1 à 17.4 (architecture du segment sol, analyse des contacts, pile de protocoles CCSDS, chronologie des opérations) ; ce livre, §7.1 et §7.3 ; ECSS-E-ST-70C *Ground systems and operations* (31 juillet 2008), §4.3 *Ground systems* ; CCSDS 130.0-G-4 *Overview of Space Communications Protocols* (livre vert, version 4, avril 2023, avec la modification rédactionnelle 1 de février 2024), sections 2 et 3 ; NASA *State-of-the-Art of Small Spacecraft Technology* (édition 2026, NASA/TP-20260003140), chap. 11 *Ground Data Systems and Mission Operations*.



**Prérequis :** semaine 2 terminée (cycle de conception complet jusqu'à l'estimation des coûts)
**Références :** ECSS-E-ST-70C (*Ground Systems*), ECSS-E-ST-70-01C (*Spacecraft On-Board Control Procedures*), CCSDS 131.0-B-4 (*TM Coding*), CCSDS 231.0-B-4 (*TC Coding*), CCSDS 133.0-B-2 (*Space Packet Protocol*), NASA *DSN Handbook* (810-005)

---

### Objectifs d'apprentissage

À la fin de cette séance, les participants seront capables de :
1. Décrire les composants d'une architecture de segment sol (antennes, MCS, FDS, réseaux)
2. Calculer le temps de contact avec une station sol et le volume de données par passage
3. Expliquer la pile de protocoles CCSDS des communications spatiales
4. Concevoir un réseau de stations sol pour une orbite et un besoin de liaison descendante donnés
5. Construire une chronologie des opérations de mission avec ses jalons clés

---

### 1. Architecture du segment sol
Le segment sol regroupe tout ce qui, au sol, soutient la mission spatiale. Il est souvent sous-estimé au début de la conception de la mission, alors qu'il représente 5-15 % du coût total de la mission et qu'il est essentiel à sa réussite.

*[Source : ECSS-E-ST-70C (*Ground Systems and Operations*) ; ECSS-E-ST-70-01C (*Spacecraft On-Board Control Procedures*)]*
*[URL : [https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/](https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/)]*

#### Composants du segment sol

L'architecture du segment sol — le réseau de stations sol, le système de contrôle de mission (MCS) et le système de dynamique du vol (FDS), avec leurs interfaces externes — est présentée dans la **figure de l'architecture du segment sol**, au §7.5.

#### Composants d'une station sol

Tableau 7.15 — Composants matériels d'une station sol, avec leur fonction et leur spécification typique.

| Composant | Fonction | Spécification typique |
|-----------|----------|---------------------|
| **Antenne** | Émettre les commandes en liaison montante, recevoir la télémesure en liaison descendante | Parabole de 3-13 m (bandes S/X) ; Yagi/tourniquet (UHF) |
| **Frontal RF** | Amplificateur faible bruit (LNA), amplificateur de puissance, filtres | Facteur de bruit du LNA < 1 dB ; amplificateur de puissance de 50-500 W |
| **Modem/bande de base** | Modulation/démodulation, codage/décodage | Conforme CCSDS ; BPSK/QPSK/8PSK |
| **Système de poursuite** | Pointage de l'antenne, poursuite Doppler, mesure de distance (ranging) | Poursuite automatique ou programmée |
| **Acquisition des données** | Enregistrer les données brutes de bande de base pour post-traitement | Baie de disques à haut débit |
| **Référence de temps** | Oscillateur asservi au GPS pour la synchronisation temporelle | Précision < 1 microseconde |

#### Système de contrôle de mission (MCS)

Tableau 7.16 — Fonctions du système de contrôle de mission, avec description et exemples d'outils.

| Fonction | Description | Outils |
|----------|------------|-------|
| **Traitement de la télémesure** | Décoder, décommuter, afficher et archiver les paquets TM | COSMOS, YAMCS, EGOS (ESA) |
| **Génération des télécommandes** | Créer, valider, coder et envoyer les paquets TC | Mêmes outils MCS |
| **Programmation des passages** | Programmer le temps d'antenne, planifier les fenêtres de visibilité | STK, GMAT, programmateurs sur mesure |
| **Surveillance et contrôle** | Surveillance de santé en temps réel, contrôle de limites, gestion des alarmes | Tableaux de bord du MCS |
| **Gestion des anomalies** | Détecter, diagnostiquer et résoudre les anomalies | Procédures + jugement d'expert |

#### Système de dynamique du vol (FDS)

Tableau 7.17 — Fonctions du système de dynamique du vol, avec description et données d'entrée requises.

| Fonction | Description | Entrées |
|----------|------------|--------|
| **Restitution d'orbite** | Calculer l'orbite actuelle à partir des données de poursuite | Distance, Doppler, GPS (si embarqué) |
| **Prévision d'orbite** | Propager l'orbite pour la planification des passages | Vecteur d'état actuel, modèles de perturbations |
| **Planification des manœuvres** | Calculer le delta-V nécessaire au maintien d'orbite | Orbite cible, modèle de propulsion |
| **Évaluation des conjonctions** | Prévoir les rapprochements avec des débris ou d'autres objets | Catalogue de TLE, orbite propre |
| **Planification de fin de vie** | Calculer la manœuvre de désorbitation ou le plan de passivation | Ergols restants, orbite cible |

---

### 2. Analyse des contacts avec les stations sol
Savoir quelle quantité de données peut être transférée par passage est fondamental pour la conception de la mission. Le bilan de données dépend de la géométrie du contact, du débit et de la durée du passage.

#### Géométrie du contact

Pour une orbite LEO circulaire, la visibilité d'une station sol est déterminée par la contrainte d'élévation minimale.

> **Distance oblique maximale à l'élévation minimale :**
>
> rho = R_E x (sqrt((h/R_E + 1)^2 - cos^2(epsilon)) - sin(epsilon))
>
> Où :
> - R_E = rayon terrestre (6371 km)
> - h = altitude de l'orbite
> - epsilon = angle d'élévation minimale (typiquement 5-10 degrés)
>
> Pour h = 500 km, epsilon = 5 degrés :
> rho = 6371 x (sqrt((500/6371 + 1)^2 - cos^2(5)) - sin(5))
> rho = 6371 x (sqrt(1.0785^2 - 0.9962^2) - 0.0872)
> rho = 6371 x (sqrt(1.1632 - 0.9924) - 0.0872)
> rho = 6371 x (sqrt(0.1708) - 0.0872)
> rho = 6371 x (0.4133 - 0.0872)
> rho = 6371 x 0.3261
> rho = 2077 km

> **Durée de passage maximale (passage au zénith) :**
>
> T_max = 2 x R_E x arccos(R_E x cos(epsilon) / (R_E + h)) / V_ground_track
>
> Approximation simplifiée en LEO :
> T_max ~ (2 x rho_max) / V_orbital x (R_E / (R_E + h))
>
> Pour une SSO à 500 km :
> V_orbital = sqrt(mu / (R_E + h)) = sqrt(3.986e14 / 6.871e6) = 7613 m/s
> T_max ~ 2 x 2077e3 / 7613 x (6371/6871) ~ 505 s ~ 8.4 minutes
>
> *Durée moyenne typique d'un passage (tous les passages ne sont pas au zénith) : ~6 minutes*

> **Volume de données par passage :**
>
> V_data = R_data x T_contact x eta_protocol
>
> Où :
> - R_data = débit de la liaison descendante (bit/s)
> - T_contact = durée du contact (secondes)
> - eta_protocol = efficacité protocolaire (typiquement 0.85-0.95 pour le CCSDS)
>
> Exemple : R = 2 Mbit/s, T = 360 s (moyenne de 6 min), eta = 0.9 :
> V_data = 2e6 x 360 x 0.9 = 648 Mbit = 81 Mo par passage

#### Fréquence des contacts

Tableau 7.18 — Passages quotidiens et estimations du volume de liaison descendante selon la latitude de la station sol, pour une SSO à 500 km.

| Orbite | Latitude de la station | Passages par jour | Durée moyenne | Volume quotidien de données (2 Mbit/s) |
|-------|-------------|----------------|-------------|---------------------------|
| SSO à 500 km | 52° N (p. ex. Waterloo) | 3-5 | 6 min | 243-405 Mo |
| SSO à 500 km | 69° N (p. ex. Kiruna) | 6-8 | 7 min | 567-756 Mo |
| 500 km, 51,6° (ISS) | 52° N | 2-4 | 5 min | 135-270 Mo |
| SSO à 500 km | Réseau SatNOGS (mondial) | 10-15 | 5 min | 675-1013 Mo |

*[Source : simulations STK ; validées à l'aide des journaux d'observation SatNOGS]*

#### Exemple résolu : bouclage du bilan de données

*Problème :* une mission d'observation de la Terre produit 500 Mo/jour d'images. Une seule station sol à 52° N de latitude suffit-elle avec une liaison descendante en bande S à 2 Mbit/s ?

*Calcul :*
- Passages par jour : ~4 (SSO à 500 km, depuis 52° N)
- Durée moyenne d'un passage : 6 min = 360 s
- Données par passage : 2e6 bit/s x 360 s x 0.9 / 8 = 81 Mo
- Capacité quotidienne : 4 x 81 = 324 Mo
- Besoin : 500 Mo/jour
- **Déficit : 176 Mo/jour -- le bilan n'est pas bouclé !**

*Solutions :*
1. Ajouter une seconde station sol à haute latitude (p. ex. Kiruna -> +6 passages -> +486 Mo)
2. Passer à un débit en bande X (10 Mbit/s -> 405 Mo/passage -> largement suffisant)
3. Réduire la production de données (rapport cyclique plus faible ou résolution d'image réduite)
4. Ajouter une compression des données à bord (2:1 sans perte -> besoin de 250 Mo/jour)
5. Utiliser le réseau SatNOGS pour des passages UHF supplémentaires (télémesure de servitude uniquement)

---

### 3. Pile de protocoles CCSDS
Le Comité consultatif pour les systèmes de données spatiales (CCSDS) définit les protocoles normalisés des communications spatiales, de façon analogue à TCP/IP pour les réseaux terrestres.

*[Source : CCSDS 131.0-B-4 (*TM Synchronization and Channel Coding*) ; CCSDS 231.0-B-4 (*TC Synchronization and Channel Coding*) ; CCSDS 133.0-B-2 (*Space Packet Protocol*)]*
*[URL : [https://public.ccsds.org/Pubs/131x0b4.pdf](https://public.ccsds.org/Pubs/131x0b4.pdf) (en libre accès)]*

#### Couches protocolaires

Tableau 7.19 — Couches de la pile de protocoles CCSDS, avec leur fonction et leurs équivalents terrestres.

| Couche | Norme CCSDS | Fonction | Équivalent au sol |
|-------|---------------|----------|----------------|
| **Application** | CCSDS 133.0 (*Space Packet*) | Paquets de données de mission et de servitude | HTTP/données applicatives |
| **Réseau** | CCSDS 732.0 (AOS) ou 132.0 (TM) | Canaux virtuels, multiplexage | Routage IP |
| **Liaison de données** | CCSDS 131.0 (codage TM) / 231.0 (codage TC) | FEC, synchronisation trame, CRC | Ethernet |
| **Physique** | CCSDS 401.0 (RF et modulation) | Modulation, fréquence, puissance | Couche physique |

#### Structure d'une trame de télémesure (TM)

La structure de la trame de transfert TM/TC — en-tête, champ de données et
champ de contrôle d'erreur, avec les champs identifiant du satellite, identifiant de canal virtuel et
compteur de trames dans l'en-tête — est présentée en contexte dans la figure de la pile protocolaire, au §7.2, qui décrit
toute la pile de protocoles, de la couche des services PUS jusqu'à la CADU sur la
liaison RF.

#### Options de correction d'erreurs directe (FEC)

Tableau 7.20 — Options de codes correcteurs d'erreurs, avec rendement, gain de codage et cas d'usage.

| Code | Rendement | Gain de codage (dB) | Cas d'usage |
|------|------|------------------|----------|
| Convolutif (7, 1/2) | 1/2 | 5,5 | CubeSats anciens |
| Reed-Solomon (255, 223) | 0,87 | 3,5 | Associé au code convolutif |
| Turbocode (rendement 1/2) | 1/2 | 7,5 | CubeSats à hautes performances |
| LDPC (rendement 7/8) | 7/8 | 6,0 | Haut débit, bonne efficacité spectrale |

*Les CubeSats modernes utilisent généralement un codage LDPC pour la liaison descendante (haut débit) et un code convolutif + RS pour la liaison montante (priorité à la robustesse).*

---

### 4. Construction de la chronologie des opérations
La chronologie des opérations (ou chronologie du concept d'opérations) définit toutes les activités majeures, du lancement à la fin de vie. Elle fait partie du ConOps et dimensionne la conception du segment sol.

#### Phases de la mission (point de vue des opérations)

Tableau 7.21 — Phases des opérations de la mission, avec durée, activités et modèle d'effectifs.

| Phase | Durée | Activités clés | Effectifs |
|-------|----------|---------------|---------|
| **LEOP** | 0-72 heures | Séparation, acquisition de la balise, déploiement du générateur solaire et de l'antenne, bilan de santé initial | 24/7 (3 quarts) |
| **Recette en orbite** | 1-4 semaines | Vérification des sous-systèmes, étalonnage du SCAO, première lumière de la charge utile | 16/7 (2 quarts) |
| **Premières opérations** | 1-3 mois | Caractérisation des performances, affinement des procédures | 8/5 (1 quart) |
| **Opérations nominales** | Durée de vie de la mission | Science/service de routine, maintien d'orbite | 8/5 ou automatisé |
| **Opérations prolongées** | Si approuvées | Opérations en mode dégradé, données réduites | Temps partiel |
| **Fin de vie** | 1-4 semaines | Passivation, manœuvre de désorbitation, dernière télémesure | 8/5 |

#### Chronologie des opérations (de type Gantt)

![Chronologie des opérations : phases de la mission (LEOP, recette en orbite, premières opérations, opérations nominales) et niveaux d'effectifs en console (24/7, 16/7, 8/5) sur la première année, par semaine depuis le lancement.](../assets/figures/fig_mission_phase_gantt.svg)

*Chronologie des opérations : phases de la mission (LEOP, recette en orbite, premières opérations, opérations nominales) et niveaux d'effectifs en console (24/7, 16/7, 8/5) sur la première année, par semaine depuis le lancement.*

#### Chronologie détaillée de la LEOP

Tableau 7.22 — Chronologie horaire de la LEOP sur les 72 premières heures, avec activités et critères de succès.

| Temps (après la séparation) | Activité | Critère de succès |
|------------------------|----------|-------------------|
| T+0 s | Séparation du déployeur | Interrupteurs de déploiement libérés |
| T+0 à T+30 min | Décompte de la minuterie de déploiement (pas de RF) | La minuterie tourne ; toutes les inhibitions sont levées |
| T+30 min | Déploiement de l'antenne | Balise détectée par la station sol |
| T+30 à T+60 min | Acquisition de la balise | Verrouillage de la porteuse ; balise décodée |
| T+1 h | Première liaison descendante de télémesure | Données de servitude reçues et validées |
| T+1 à T+6 h | Évaluation initiale de la santé | Tous les sous-systèmes transmettent une HK nominale |
| T+6 à T+12 h | Déploiement du générateur solaire (s'il est séparé) | Production de puissance confirmée |
| T+12 à T+24 h | Initialisation du SCAO | Détermination d'attitude active |
| T+24 à T+48 h | Étalonnage du SCAO (magnétomètre, senseur solaire) | Pointage dans la spécification grossière |
| T+48 à T+72 h | Validation de la chaîne de communication (duplex intégral) | Liaisons montante et descendante au débit opérationnel |

#### Planification des opérations dans SpaceCDF

L'**éditeur de ConOps** de SpaceCDF vous permet de :
- définir les phases de la mission avec leurs conditions de début et de fin ;
- préciser les modes opérationnels de chaque phase (survie, nominal, science, liaison descendante) ;
- fixer les besoins de contact sol de chaque phase (fréquence, durée) ;
- le système vérifie que la conception du segment sol soutient le concept d'opérations.

---

### 5. Exercice de conception du segment sol
#### Consignes

1. Onglet **Data Budget** -- examinez la production quotidienne de données par rapport à la capacité de liaison descendante
   - Le bilan de données est-il bouclé ? Sinon, identifiez le goulet d'étranglement
   - Combien de passages au-dessus des stations sol votre orbite offre-t-elle par jour ?

2. **Éditeur de ConOps** -- définissez les phases de la mission :
   - LEOP (durée, effectifs, besoins de contact)
   - Recette en orbite (activités, critères de succès)
   - Opérations nominales (rapport cyclique, volume de données, fréquence des contacts)

3. Sur la fiche 5.1 :
   - Calculez le volume de données par passage pour votre mission
   - Déterminez le nombre de stations sol nécessaires pour boucler le bilan de données
   - Construisez une chronologie de la LEOP
   - Esquissez une chronologie simplifiée des opérations (diagramme de Gantt)

#### Pistes de discussion

- « Que se passe-t-il si votre premier passage après le déploiement ne donne aucun signal ? »
- « Comment géreriez-vous un passage en mode survie à 3 h du matin un samedi ? »
- « Quel est le segment sol minimal capable de soutenir votre mission ? »

#### Tâches de la fiche 5.1

1. Calculez le temps de contact avec la station sol et le volume de données par passage
2. Concevez un réseau de stations sol (emplacements, tailles d'antenne, débits)
3. Construisez une chronologie de la LEOP (72 premières heures, résolution horaire)
4. Esquissez une chronologie des opérations de la mission (diagramme de Gantt, résolution hebdomadaire)
5. Estimez le coût du segment sol (antennes + MCS + FDS + personnel d'opérations)

---

### Références citées

Tableau 7.23 — Références citées pour la séance « Architecture du segment sol et des opérations », avec URL.

| # | Référence | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70C (*Ground Systems and Operations*) | [https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/](https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/) |
| 2 | CCSDS 131.0-B-4 (*TM Synchronization and Channel Coding*) | [https://public.ccsds.org/Pubs/131x0b4.pdf](https://public.ccsds.org/Pubs/131x0b4.pdf) |
| 3 | CCSDS 133.0-B-2 (*Space Packet Protocol*) | [https://public.ccsds.org/Pubs/133x0b2.pdf](https://public.ccsds.org/Pubs/133x0b2.pdf) |
| 4 | CCSDS 231.0-B-4 (*TC Synchronization and Channel Coding*) | [https://public.ccsds.org/Pubs/231x0b4.pdf](https://public.ccsds.org/Pubs/231x0b4.pdf) |
| 5 | Réseau SatNOGS | [https://network.satnogs.org/](https://network.satnogs.org/) |
| 6 | NASA *DSN Handbook* (810-005) | [https://deepspace.jpl.nasa.gov/dsndocs/810-005/](https://deepspace.jpl.nasa.gov/dsndocs/810-005/) |
| 7 | Logiciel de contrôle de mission YAMCS | [https://yamcs.org/](https://yamcs.org/) |

---

### Synthèse de la séance

Tableau 7.24 — Synthèse de la séance : points clés des thèmes segment sol et architecture des opérations.

| Thème | Point clé |
|-------|-------------|
| Segment sol | Réseau d'antennes + MCS + FDS + planification de mission + traitement des données |
| Analyse des contacts | Durée de passage ~6 min (LEO/SSO) ; volume de données = débit x durée x efficacité |
| Bilan de données | Doit être bouclé : production quotidienne <= capacité quotidienne de liaison descendante ; ajouter des stations sol ou augmenter le débit |
| CCSDS | Pile de protocoles normalisée : paquet spatial, trames AOS/TM, codage FEC, modulation RF |
| Chronologie des opérations | LEOP (24/7) -> recette en orbite (16/7) -> nominal (8/5 ou automatisé) |
| LEOP | 72 premières heures critiques : déploiement de l'antenne, acquisition de la balise, bilan de santé |
| SpaceCDF | L'éditeur de ConOps définit les phases ; l'onglet Data Budget valide le dimensionnement du segment sol |

## 7.11 Références

- ECSS-E-ST-70C — *Ground systems and operations* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70c-ground-systems-and-operations/)
- ECSS-E-ST-70-41C — *Telemetry and telecommand packet utilization* (PUS) — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/)
- CCSDS 132.0-B-3 — *TM Space Data Link Protocol* — [public.ccsds.org](https://public.ccsds.org/)
- CCSDS 232.0-B-4 — *TC Space Data Link Protocol* — [public.ccsds.org](https://public.ccsds.org/)
- CCSDS 660.0-G-3 — livre vert PUS — [public.ccsds.org](https://public.ccsds.org/Pubs/660x0g3.pdf)

# Chapitre 8 — Opérations de passage (routine)

Ce chapitre parcourt le **cycle de passage de routine** en
exploitation nominale (phase 6), c'est-à-dire le régime établi qui
suit la recette en orbite et qui occupe l'essentiel de la vie
opérationnelle de la mission. Un passage nominal se déroule ainsi :
briefing avant passage → AOS → ouverture de passage → activités en
cours de passage (prise de vue, liaison descendante, contrôle de
santé) → LOS → débriefing après passage → passation de consignes
(en fin de quart).

Les procédures citées dans ce chapitre vont de NOM-001 à
NOM-013 (le catalogue complet figure au chapitre 14). Chaque procédure est
parcourue étape par étape : annonce du FD, action de l'opérateur,
télémesure de vérification et renvoi en cas d'échec.


![Cycle d'un passage sol en couloirs d'activité pour les rôles FD, FE, charge utile et station sol, avec repères AOS/LOS et exemple de règle FDIR déclenchée en cours de passage.](../assets/figures/fig_ops_timeline.svg)

*Cycle d'un passage sol en couloirs d'activité pour les rôles FD, FE, charge utile et station sol, avec repères AOS/LOS et exemple de règle FDIR déclenchée en cours de passage.*

## 8.1 Vue d'ensemble du cycle de passage

Pour un satellite en SSO à 513 km comme EOSAT-1, un passage de routine dure
entre 3 et 9,4 minutes selon l'élévation maximale atteinte au
survol du nœud : 3 à 5 min pour un passage rasant à 5–10°, environ 9 min pour un
passage quasi zénithal, avec une moyenne mesurée de 7,5 minutes. Avec
le réseau de **cinq stations**, le satellite est en contact avec
au moins une station sur la plupart des orbites, souvent plusieurs fois. La
chronologie côté opérateurs :

Tableau 8.1 — Chronologie des activités du cycle de passage, du briefing avant passage au débriefing après passage.

| Temps par rapport à l'AOS | Activité | Responsable | Procédure |
|---|---|---|---|
| AOS-30 à AOS-15 min | Briefing avant passage ; revue du plan ; revue des fiches d'anomalie | FD | (aucune — briefing) |
| AOS-10 à AOS-5 min | Contrôle de disponibilité de la station ; prépositionnement de l'antenne ; bande de base prête | Segment sol | (NOM-001 étape 1) |
| AOS-2 à AOS | Pré-armement de l'émetteur ; attente de l'acquisition de la porteuse | TT&C | (NOM-001 étapes 2-3) |
| AOS | Verrouillage de la porteuse ; début de la télémesure de servitude complète. **`ttc.link_status` (0x0501) = 2 signifie LOCKED** ; 1 signifie seulement ACQUIRING (porteuse verrouillée sans synchronisation trame) et 0 signifie NO_LINK — ne pas interpréter une valeur non nulle comme une bonne liaison | TT&C + SPACON | NOM-001 (ouverture de passage) |
| AOS+1 min | S17.1 `CONNECTION_TEST` ; vérification complète de la HK ; balayage FDIR | SPACON | NOM-001 étapes 4–5 |
| AOS+2 à LOS-2 | Activités planifiées (prise de vue, liaison descendante) | selon le plan | NOM-002, NOM-003 |
| LOS-2 min | Contrôle de santé avant LOS ; entrée de fin de passage dans la main courante | SPACON | NOM-009 |
| LOS | Chaîne en bande S ramenée au palier LOW (16 kbit/s), mode DOWNLINK désactivé ; configuration consignée | TT&C | Clôture de NOM-001 |
| LOS+0 à LOS+15 | Débriefing à chaud ; clôture des fiches d'anomalie ; revue du passage suivant | FD | (passation NOM-012 en fin de quart) |

Le système de planification de mission (MPS) construit le plan de passage en amont ;
pendant le passage, le rôle de l'équipe est d'**exécuter le plan et de
traiter les anomalies**, non de planifier en temps réel.

## 8.2 Satellite de référence et géométrie des passages

Les sections qui suivent s'appuient sur la mission de référence EOSAT-1
(chapitre 5, §5.7), sur le segment sol (chapitre 7, §7.1)
et sur la salle de contrôle (chapitre 5, §5.4). Les étudiants
auront lu ces chapitres. Le briefing vise donc à *vérifier la compréhension*
plutôt qu'à présenter la matière pour la première fois.

Les quatre éléments du segment sol, tour à tour :

1. **Stations sol.** Ouvrez le panneau d'état des stations du MPS. Passez en revue
   les **cinq** stations — Iqaluit (63,7° N), Inuvik (68,3° N),
   Svalbard (78,2° N), Troll (72,0° S) et O'Higgins (63,3° S) —
   et montrez le compte à rebours jusqu'au prochain AOS de chacune. Vérifiez sur le
   MCS laquelle est active en ce moment : `ttc.active_gs` (0x0523) est un
   indice, commençant à 1, dans cette même liste.
2. **Bande de base.** Ouvrez le flux d'état de la bande de base de rfsim. Montrez
   l'Eb/N0 et l'état de synchronisation trame, tous deux actuellement nominaux puisque
   nous sommes *en* cours de passage.
3. **Système de contrôle de mission (MCS).** Ouvrez le tableau de bord MCS du FD
   sur `:9090`. Parcourez les zones (haut, gauche, centre, droite,
   procédure).
4. **Dynamique du vol.** Montrez le poste de travail FDS. Lisez la liste des
   passages dans le planning des contacts du planificateur sur `:9091`, et lancez
   `python3 tools/pass_gap_analysis.py --config configs/eosat1 --hours 24`
   pour obtenir les statistiques d'intervalles qui la sous-tendent.

Le briefing se termine sur la **géométrie des passages** : pourquoi une SSO polaire associée à des
stations sol polaires donne de nombreux passages courts par jour plutôt que
quelques passages plus longs. Voir la figure 8.1.

### 8.2.1 Géométrie des passages — SSO polaire au-dessus de stations polaires

Une orbite héliosynchrone à 513 km a une période d'environ 94,5 minutes.
Celle d'EOSAT-1 est une orbite **de milieu de matinée**, et non aube-crépuscule :
l'heure solaire locale au nœud ascendant est maintenue vers **10 h 00**, de sorte
que le satellite traverse l'ombre de la Terre à chaque orbite (de 33,2 à
35,2 minutes). Les cinq stations —
Svalbard (78,2° N), Inuvik (68,3° N), Iqaluit (63,7° N),
Troll (72,0° S) et O'Higgins (63,3° S) — sont situées à haute latitude,
près de la zone où convergent les traces au sol, de sorte que la plupart des passages aux nœuds ascendants ou
descendants amènent le satellite dans l'empreinte d'au moins une
station.

Résultat, mesuré sur 48 h à partir de l'époque de la mission avec
`tools/pass_gap_analysis.py` : **103 passages en 48 h** — soit
environ 51 par jour — avec un **intervalle médian de 33 minutes** et un **intervalle
maximal de 79 minutes**. (Le réseau à deux stations que supposaient les anciens supports de cours
donne 40 passages, un intervalle médian de 84 minutes et un intervalle maximal de 147 minutes ;
la configuration de référence à cinq stations est celle qu'utilise ce cours
d'un bout à l'autre.) La durée d'un passage va de **3 à 9,4 minutes** et l'élévation maximale
de la limite du masque de 5° jusqu'au zénith, selon la
géométrie du survol du nœud. Il n'y a toujours aucun contact lorsque le
satellite survole l'équateur ou les latitudes moyennes : les périodes de silence radio
sont normales, simplement plus courtes. L'EPS et le poste thermique doivent planifier
en conséquence.

Notez la conséquence opérationnelle de l'élévation : le palier HIGH à 128 kbit/s
n'est autorisé qu'au-dessus de **10° d'élévation**, de sorte qu'un passage qui ne monte jamais
au-dessus de 10° est utilisable pour la commande et la télémesure de servitude à 16 kbit/s,
mais ne transporte aucune image.

Exemple résolu : à 513 km, la durée géométrique de visibilité d'horizon à horizon
pour l'élévation maximale (passage au zénith) est

$$ t_{transit} = 2 \cdot \arccos\left(\frac{R_E + h_{station}}{R_E + h_{sat}}\right) \cdot \frac{T_{orbit}}{2\pi} $$

Avec $R_E = 6371$ km, $h_{sat} = 513$ km, $h_{station} \approx 0$
et $T_{orbit} = 5669$ s, la durée géométrique de visibilité est
$\approx 11.7$ minutes. En ajoutant le masque d'élévation de 5° —
$\lambda = \arccos\!\left(\frac{R_E\cos\varepsilon}{R_E+h}\right) - \varepsilon = 17.8°$,
soit un arc de $35.6°$ — le contact utile au zénith tombe à
$\approx 9.3$ minutes. Avec le masque et des passages réalistes
à élévation moyenne, la moyenne mesurée est de 7,5 minutes.

*Figure 8.1 — Schéma d'une orbite d'EOSAT-1 avec les cônes de visibilité des cinq stations (masque d'élévation de 5°). Les segments éclairés et en éclipse sont ombrés.*

## 8.5 Prise en main du système de planification de mission

Les opérateurs travaillent à leur poste, le MPS ouvert, et
réalisent l'exercice individuellement.

### Objectif de l'exercice

Construire, valider et exporter un plan de passage de 60 à 90 minutes pour le prochain
passage au-dessus d'Iqaluit. Le plan doit comprendre une activité de prise de vue et le
basculement associé, la liaison descendante de l'image obtenue et un
bilan de santé de routine.

### Étapes

1. **Ouvrez le MPS** à <http://localhost:9091/>.
2. **Ouvrez le planning des contacts.** Repérez le prochain passage au-dessus d'Iqaluit.
   Notez l'AOS, l'élévation maximale, la LOS et la durée. Si l'élévation maximale
   est inférieure à 10°, notez que ce passage ne peut pas accueillir de vidage et
   choisissez le passage de liaison descendante en conséquence.
3. **Ouvrez le sélecteur de cibles de prise de vue.** Choisissez trois cibles de
   courants océaniques (`OCM-…`) visibles pendant le passage ; le sélecteur indique
   la visibilité par passage et le seuil `min_solar_elevation_deg`
   de chaque cible.
4. **Placez une séquence basculement + image + basculement** dans le passage. Le
   vérificateur de conflits s'exécute automatiquement.
5. **Résolvez les conflits éventuels.** Conflits probables : temps de basculement trop
   court entre les cibles (ramener à deux cibles) ; puissance cumulée
   supérieure au bilan (supprimer une bande) ; liaison descendante demandée nécessitant
   le palier HIGH sur un passage qui ne dépasse jamais 10°.
6. **Ajoutez une activité de liaison descendante** pour la ou les images obtenues, dans
   le même passage ou dans le suivant (celui qui offre le plus long temps de
   contact).
7. **Ajoutez un bilan de santé de routine NOM-009** au début du
   passage.
8. **Lancez la vérification finale des conflits.** Elle doit être au vert.
9. **Exportez le plan.** Enregistrez le fichier sous
   `outputs/student_plans/<your-name>_day1.yaml`.
10. **Ouvrez le plan dans le panneau des procédures du MCS.** Vérifiez que la
    séquence d'activités apparaît comme prévu.

### À quoi ressemble un bon résultat

- Tous les conflits sont résolus (état vert).
- La durée du plan de passage correspond à la fenêtre de passage réelle, moins une marge de 60 s
  à chaque extrémité.
- Le contrôle de santé est la première activité (l'étape 1 de NOM-009 demande les
  SID HK des six sous-systèmes avec `HK_REQUEST(sid=…)` (S3.27) ; faites-le
  avant toute autre commande). N'oubliez pas que seuls les SID 1 et
  11 sont activés à l'amorçage : si un SID n'a jamais été activé pendant cette
  séance, il faut d'abord envoyer `HK_ENABLE(sid=…)` (S3.5).
- L'activité de liaison descendante correspond au volume d'image produit (règle
  empirique : `image_size_mb` vaut 4 Mo par séance de prise de vue ; au débit de 128 kbit/s du palier
  HIGH, cela fait 4 × 8 / 0,128 ≈ **250 s**, soit un peu plus de
  quatre minutes — une part importante d'un passage moyen de 7,5 minutes, qui
  exige en outre que le mode DOWNLINK soit activé et que l'élévation reste au-dessus de 10° pendant toute sa
  durée).

## 8.6 Rotation sur les postes MCS

Sept consoles configurées (§7.2), 15 minutes chacune, après un briefing
de 15 minutes : exactement le créneau 13 h 00 – 15 h 00. Chaque étudiant
passe par les sept au cours de l'après-midi. À chaque poste, la
personne en place lit à voix haute la fiche du poste (chapitre 6), puis
réalise une tâche propre au poste en observant la télémesure
en direct.

Tableau 8.2 — Tâches de la rotation attribuées à chaque poste de la salle de contrôle pendant la familiarisation.

| Poste | Tâche |
|---|---|
| Directeur de vol | Mener un tour de table GO/NO-GO sur le tableau de bord en direct. Interroger trois postes pour un *go for* `CONNECTION_TEST` (S17.1) — ce satellite ne dispose d'aucune commande NOOP ni de signal de vie ; consigner les réponses. |
| FDIR / Systèmes | Parcourir une règle FDIR sur le panneau FDIR ; en expliquer le déclencheur, le seuil, la gravité et la procédure de contingence vers laquelle `mcs/alarm_procedures.yaml` la renvoie. |
| Dynamique du vol (AOCS) | Lire l'erreur d'attitude actuelle sur le visualiseur et la comparer aux deux bilans : le contrôle de suivi nadir de NOM-001 (`aocs.att_error` 0x0217 < 1.0°) et le seuil de capture, bien plus strict (FINE_POINT, erreur de pointage totale < 0.05°, stabilité de vitesse < 0.005 °/s). |
| Puissance et thermique | Prévoir le SoC de la batterie en sortie de la prochaine éclipse à partir du planning des contacts ; puis identifier le réchauffeur dont le rapport cyclique est le plus élevé et prévoir s'il saturera à la prochaine éclipse. |
| TT&C | Commander la transition de débit LOW → HIGH à l'AOS : `TTC_SET_DOWNLINK_MODE(on=1)` (79) puis `TTC_SET_DATA_RATE(rate=1)` (65). Vérifier que `ttc.tm_tier` (0x0539) atteint effectivement 2 et ne reste pas rétrogradé sous `ttc.tm_tier_cmd` (0x053A). Lire la marge de liaison après la transition. Puis, avec l'autorisation du FD, observer l'effet de `TTC_PA_OFF` (67) : la télémesure en bande S s'arrête (`ttc.tx_active` 0x0525 → 0) tandis que la balise UHF, sur `ttc.beacon_active` (0x0527), continue d'émettre. |
| Opérations charge utile | Programmer une séance de prise de vue unique via le MPS. Vérifier que la température du FPA est à la consigne et que `FPA ready` (0x0610) = 1 avant de commander. |
| Propulsion | Lire le masque de verrouillages d'armement (`arm_inhibit_mask`, 0x0B15) et désigner le verrou qui bloque actuellement l'armement, sans rien commander. |

Les rôles de responsable de mission et de segment sol ne font pas partie de la
rotation : ce sont des rôles de salle plutôt que des consoles MCS
configurées, tenus par le directeur de mission ou par un opérateur
désigné pendant toute la journée.

Une fiche d'évaluation par poste figure dans le cahier d'exercices (WB-5.1), une par console. L'étudiant
y note une observation par poste.

## 8.7 Exercice d'équipe : plan de passage

Des équipes de 4 à 6 personnes (Borealis et Austral) travaillent en parallèle. Chaque équipe
rédige un plan de passage de 60 à 90 minutes pour le même passage
à venir au-dessus d'Iqaluit. Le plan doit comprendre :

- le minutage du passage (AOS – TCA – LOS) avec ses marges ;
- les procédures à exécuter, par identifiant de procédure ;
- la fenêtre de prise de vue, l'identifiant de la cible, la fauchée au sol prévue, la ou les
  bandes scientifiques choisies, le temps d'intégration ;
- la configuration de liaison descendante : quel échelon de l'échelle de débits (LOW 16 kbit/s BPSK
  conv(7,1/2)+RS, ou HIGH 128 kbit/s QPSK RS(255,223)), si le
  passage dépasse le seuil HIGH de 10° assez longtemps, et la durée
  prévue ;
- la contingence en cas d'anomalie : **deux** pannes plausibles et l'identifiant de
  procédure à appliquer pour chacune.

Les plans sont lus à voix haute à 16 h 30. L'autre équipe les critique selon l'axe *Technique*
de la fiche d'évaluation par les pairs.

## 8.8 Débriefing et lecture pour ce quart

Questions de débriefing :

1. Quel poste MCS vous a semblé le plus naturel ? Pourquoi ?
2. Qu'est-ce qui vous a surpris dans le minutage d'un passage au-dessus d'une station sol ?
   Le réseau à cinq stations s'est-il comporté comme vous l'attendiez ?
3. Quel point aimeriez-vous voir mieux documenté avant le prochain quart ?

Lecture pour ce quart : le chapitre 9 en entier, ainsi que les procédures du simulateur
`procedures/nominal/startup.md` (NOM-001) et
`procedures/contingency/ttc_link_loss.md` (CTG-003) — environ
45 minutes.

---

## 8.9 Références

- ECSS-E-ST-70C — *Ground systems and operations* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70c-ground-systems-and-operations/)
- CCSDS 520.0-G-4 — *Mission Operations Reference Model* — [public.ccsds.org](https://public.ccsds.org/Pubs/520x0g4.pdf)

# Chapitre 9 — Discipline de boucle vocale et exécution des procédures

La boucle vocale est la colonne vertébrale de la salle d'opérations. Chaque poste
est sur la boucle ; chaque action commandée est couplée à la voix. Ce
chapitre traite de la **discipline** à observer sur la boucle — les
schémas, le vocabulaire et les protocoles qui distinguent une
équipe qui traite une anomalie en 90 secondes d'une équipe qui
y met 5 minutes — ainsi que du **rythme d'exécution des procédures**,
qui fait correspondre les annonces vocales aux actions de commande.

Ce chapitre est un document de référence, utilisé par chaque opérateur avant
chaque quart. Les exercices d'entraînement figurent au §9.2.

## 9.1 Pourquoi la boucle vocale est importante

Données de l'industrie : dans environ 80 % des cas où une équipe d'opérations
de mission transforme une anomalie récupérable en anomalie irrécupérable, la
cause première remonte à une défaillance de la boucle vocale — une annonce manquée, une
instruction ambiguë, une conversation parallèle qui a masqué une
information importante — et non à une mauvaise lecture de la télémesure ou à une commande erronée.
La discipline de boucle vocale est la compétence d'opérateur qui a le plus fort
effet de levier, avant même l'interprétation de la télémesure.

## 9.2 Principes fondamentaux de la boucle vocale 

La discipline de boucle vocale est une compétence acquise qui distingue une
équipe qui traite une anomalie en 90 secondes d'une équipe qui
y met 5 minutes. Les références sont :

- ESA, *Operations Manual for Mission Control*, en particulier le
  chapitre consacré à la discipline de boucle ;
- les supports de la NASA APPEL sur les procédures vocales ;
- FAA, *Crew Resource Management* (CRM), AC-120-51E — la théorie
  sous-jacente de la coordination d'un équipage à plusieurs postes.

Trois exercices d'entraînement construisent cette compétence :

### Exercice 1 — Schéma d'adressage

Les opérateurs se mettent en binôme — l'un comme FD, l'autre comme opérateur
de sous-système — et enchaînent 10 annonces en binôme selon le schéma
`[ADDRESSEE], [SPEAKER] — [MESSAGE]` (destinataire, émetteur, message). Exemples :

- « AOCS, FD — pointing report. »
- « FD, AOCS — pointing 0.28° (NOMINAL), nominal. »
- « EPS, FD — eclipse-entry predictor. »
- « FD, EPS — eclipse-entry T+04:12, SoC at exit 78%. »

Notez les interférences de parole et les appels mal adressés.

### Exercice 2 — GO / NO-GO avec attente

Un scénario est posé : l'équipe s'apprête à commander la mise sous tension de la charge utile
pendant un passage. Le FD doit interroger l'EPS, le poste thermique et la charge utile pour obtenir un GO.
Chaque opérateur a reçu au préalable un *état secret* (p. ex. l'EPS voit déjà
une charge électrique inattendue, le poste thermique voit le FPA encore en cours de mise en température). Chacun
doit répondre honnêtement : *go*, *no-go* avec la raison, ou *hold* avec la
raison.

Le FD prend la décision et l'explique sur la boucle. Les
états secrets sont ensuite révélés et l'équipe en discute.

### Exercice 3 — Annonce d'anomalie

Une anomalie est injectée hors boucle (un paramètre passe au
jaune sur l'onglet d'un opérateur). L'opérateur doit :

1. reconnaître le changement ;
2. l'annoncer sur la boucle selon le format *« FD, [POSITION] — anomaly,
   [parameter], [value], [trend] »* (poste, paramètre, valeur, tendance) ;
3. attendre les directives du FD.

Mesurez le temps écoulé entre le premier changement de télémesure et la première
annonce de l'opérateur. L'objectif de l'équipe est de **moins de 15 secondes**.

### Référence de la boucle vocale : matériel, micro ouvert, vocabulaire et GO/NO-GO

Les principes ci-dessus sont complétés par un petit ensemble de
conventions permanentes que chaque poste doit connaître par cœur. Une version
carte aide-mémoire du vocabulaire des annonces figure dans le cahier d'exercices (WB-5.4-VC).

### Matériel

Un casque téléphonique logiciel de salle de contrôle par poste, tous réunis en conférence
sur un canal unique. Le responsable de mission est sur la boucle mais
y prend rarement la parole sur le plan opérationnel.

### Règle du micro ouvert

Les casques fonctionnent par défaut à l'alternat. Le micro ouvert (en permanence)
est réservé au FD pendant une phase critique (le FD annonce
« hot mike on » avant une séquence complexe et « hot mike off »
après).

### Vocabulaire des annonces

Tableau 7.4 — Vocabulaire normalisé des annonces sur la boucle vocale, avec leur signification et la réponse attendue.

| Annonce | Signification | Réponse |
|---|---|---|
| « Comm check 1-2-3 » | Essai de la boucle vocale | « FD copy, comm check loud and clear » |
| « Standby » | Je travaille ; je vais répondre | « Standby » ou attendre |
| « Standby plus 30 » | Attente, je reviens dans 30 s | (aucune réponse requise) |
| « Go for X » | Demande d'autorisation d'exécuter X | « Go » ou « No-go, [reason] » ou « Hold, [reason] » |
| « Hold » | Suspendre l'action en cours | Tous les postes s'arrêtent |
| « Resume » | Reprendre l'action suspendue | (l'action reprend) |
| « No-go » | Refus de la demande, avec la raison | (la suite relève de la décision du FD) |
| « AOS in N » | Acquisition du signal dans N minutes | (aucune réponse requise) |
| « AOS » | Le satellite est en visibilité | (le segment sol confirme la liaison) |
| « LOS in N » | Perte du signal dans N minutes | (aucune réponse requise) |
| « LOS » | Le satellite est hors visibilité | (les opérateurs terminent les étapes en cours) |
| « Pass closed » | Le passage est entièrement terminé, relâchement | (le débriefing commence) |
| « Anomaly, [parameter], [value] » | Télémesure hors plage | (le SPACON confirme l'état FDIR) |
| « Mark » | Noter l'heure pour le journal | (horodatage automatique dans la main courante) |
| « Loop discipline » | Le FD rappelle à l'ordre en cas d'interférences de parole | Tout le monde s'arrête et se resynchronise |

### Protocole GO / NO-GO

Avant toute action commandée qui modifie l'état du satellite :

1. Le FD interroge les postes concernés. (« AOCS, EPS, FDIR — go for
   ST1_POWER? »)
2. Chaque poste répond dans l'ordre du tour de table : « Go » / « No-go, [reason] »
   / « Hold, [reason] ».
3. Le FD déclare : « Go for ST1_POWER » ou « Hold on
   ST1_POWER, [reason] ».
4. Le responsable de l'action n'exécute que sur GO explicite du FD. Préparer la
   commande à l'avance (première clé) avant le GO est admis ; l'envoyer avant
   le GO est une infraction.



## 9.3 Déroulé de procédure — NOM-001 Ouverture de passage

NOM-001 est la procédure de référence d'*ouverture de passage*, exécutée au
début de chaque passage en exploitation nominale. Elle est présentée
ci-dessous au **format question-réponse (*challenge–response*) des QRH de l'aviation** : le SPACON
énonce la *question*, le responsable désigné donne la *réponse*, et la
colonne *action* indique la télécommande ou la lecture effective. Les opérateurs
inscrivent la valeur de télémesure réelle ou une coche dans la colonne
*Note / valeur réelle*.

**Document de référence :** `procedures/nominal/startup.md`.
**Postes responsables :** SPACON (pilote, détient le fichier de procédure) ·
TT&C · segment sol · FD.
**Déclencheur :** AOS-5 min pour tout passage planifié pendant la phase 6.
**Critère de réussite :** les dix étapes vérifiées ; entrée consignée dans le journal de passage.
**Durée estimée :** 3 à 6 minutes.

> **Actions mémorisées** (les opérateurs les effectuent *avant* d'ouvrir le
> fichier de procédure, par ordre de priorité) :
>
> 1. **Confirmer la poursuite par la station sol.**
> 2. **Vérifier que l'émetteur bord est sur ON avant AOS-2 min.**
> 3. **À l'AOS, écouter l'annonce de verrouillage de la porteuse.**

### Calculs préalables à la liste de vérification (effectués par l'opérateur avant l'étape 1 de NOM-001)

Tableau 9.1 — Calculs de l'opérateur avant le passage, avec section de référence et réponse typique attendue.

| Calcul | Référence | Réponse typique |
|---|---|---|
| Heure prévue de l'AOS | Planning des contacts (MPS) — voir §13.2 | nominale |
| SoC en sortie d'éclipse à l'AOS | Formule du §13.3 | > 55 % |
| RSS actuelle de l'erreur de pointage | Onglet AOCS — voir §13.4 | < 0,4° |
| Marge de liaison prévue au TCA | Onglet bilan de liaison du MPS — voir §13.6 | > 5 dB |

### Liste de vérification NOM-001

Tableau 9.2 — Liste de vérification question-réponse de NOM-001 (ouverture de passage), avec vérifications et renvois en cas d'échec.

| N° | Responsable | Question | Réponse attendue | Action / TC | Renvoi en cas d'échec | ☐ | Note / valeur réelle |
|---|---|---|---|---|---|:-:|---|
| 1 | Segment sol | « GS, stations in view tracking? » | « FD, GS — stations in view tracking. » | Lire le panneau d'état des stations du MPS — chaque station en visibilité affiche TRACKING | CTG-020 | ☐ | __________ |
| 2 | TT&C | « TT&C, tx state pre-AOS? » | « FD, TT&C — `ttc.tx_active` = 1, time-to-AOS T-1:30. » | Lire `tx_active` (0x0525) dans l'onglet TTC ; s'il vaut 0, `ttc.tx_gate_status` (0x052B) désigne le verrou qui bloque la liaison descendante | Vérifier le plan bord S11 | ☐ | __________ |
| 3 | TT&C | « TT&C, link status? » (à l'AOS) | « FD, TT&C — `ttc.link_status` 2 LOCKED, RSSI -98 dBm, margin 8.2 dB. » | Lire `link_status` (0x0501), `rssi` (0x0502), `link_margin` (0x0503) dans l'onglet TTC dans les 30 s qui suivent l'AOS | CTG-003 | ☐ | __________ |
| 4 | SPACON | « SPACON, link test. » | « FD, SPACON — S17.1 sent, response within 4 s. » | Panneau de commande : S17 sous-type 1 ; première clé ; GO du FD ; envoi | CTG-019 (pas de TM) | ☐ | __________ |
| 5 | SPACON | « SPACON, full HK? » | « FD, SPACON — SIDs 1, 2, 3, 4, 5, 6 streaming. » | Panneau FDIR + balayage visuel de la mosaïque de télémesure ; un SID manquant signifie que la ligne est alimentée mais que le SID n'a jamais reçu de `HK_ENABLE` (S3.5) | CTG-019 | ☐ | __________ |
| 6 | AOCS | « AOCS, mode and rates? » | « FD, AOCS — mode 4 NOMINAL, roll and yaw rates < 0.05 °/s, pitch -0.063 °/s. » | Onglet AOCS : `aocs.mode` (0x020F), `aocs.rate_roll/pitch/yaw` (0x0204–0x0206) | CTG-002 | ☐ | __________ |
| 7 | EPS | « EPS, bus and SoC? » | « FD, EPS — SoC 78 %, bus 28.1 V. » | Onglet EPS | CTG-001 (délestage) | ☐ | __________ |
| 8 | Thermique | « Thermal, zones? » | « FD, Thermal — all zones green. » | Onglet TCS | CTG-004 | ☐ | __________ |
| 9 | Charge utile | « Payload, state vs plan? » | « FD, Payload — mode per plan. » | Onglet charge utile | (selon le plan de passage) | ☐ | __________ |
| 10 | SPACON | « SPACON, log pass start. » | « FD, SPACON — entry logged at AOS+0:34. » | Main courante | (aucun) | ☐ | __________ |

Deux points de ce tableau piègent les nouveaux opérateurs. Premièrement, **la télémesure de servitude
n'est pas transmise par défaut** : l'ensemble activé à la mise sous tension est
`simulation.yaml` `default_enabled_sids: [1, 11]` — SID 1 (EPS) et SID 11
(la balise) — et le moteur réapplique exactement cet ensemble à chaque
amorçage du logiciel applicatif. Tous les autres SID (2 AOCS, 3 TCS, 4 OBDH/plateforme,
5 charge utile, 6 TT&C, 8 EPS étendu, 9 PROP) doivent être activés par commande avec
`HK_ENABLE(sid=N)` (**S3.5**), et la mise sous tension de la ligne d'un sous-système n'active
pas son SID. En exploitation nominale, ils sont déjà actifs depuis la
recette en orbite ; s'il en manque un, renvoyez le `HK_ENABLE` au lieu d'attendre qu'il
apparaisse. Un instantané ponctuel d'un SID quelconque s'obtient avec `HK_REQUEST(sid=N)` (**S3.27**).

Deuxièmement, en mode 4 (NOMINAL, suivi nadir), la vitesse de tangage n'est *pas* nulle :
le suivi nadir impose la vitesse orbitale autour de l'axe −Y du satellite, de sorte que `aocs.rate_pitch`
indique −0.063 ± 0.02 °/s. Une vitesse de tangage nulle signifie ici que le satellite
ne suit **pas** le nadir : c'est elle qui signale le défaut, et non la valeur nominale.

> **Point d'arrêt — GO de début de passage.** Le FD interroge tous les postes
> après l'étape 10 avec : *« All positions, pass start
> verified — GO for planned activities? »* Chaque poste
> répond GO / NO-GO / HOLD avec la raison. Le FD déclare le GO
> pour le passage avant toute commande en cours de passage.

### Postconditions

- Entrée créée dans le journal de passage avec l'heure de l'AOS, la marge de liaison de référence,
  le SoC à l'AOS et la RSS de l'erreur de pointage à l'AOS.
- Panneau FDIR balayé et sans alarme.
- Tous les postes sont prêts à exécuter le plan du passage.

### Écarts fréquents

- Sauter l'étape 4 (test de liaison S17). Sans elle, l'équipe
  découvre que la liaison montante est coupée lors de la première action commandée,
  environ 8 minutes après le début du passage.
- Consigner le début du passage en fin de passage plutôt qu'à l'AOS.
  La traçabilité du moment où le passage a réellement commencé est importante.

### Fiches exécutables par la machine, fiches consultatives et exécuteur

La plupart des fiches de procédure sont des documents lire-et-exécuter destinés à un humain. Un petit
sous-ensemble, explicitement repéré, est également **exécutable par la machine** : l'entrée d'index dans
`procedures/procedure_index.yaml` porte un lien `runnable:`, et le MCS
propose la fiche à l'exécution. Aujourd'hui, cela concerne **huit fiches** — NOM-002
(séance de prise de vue), NOM-003 (liaison descendante des données), NOM-004 (planification des manœuvres
de maintien d'orbite), NOM-008 (synchronisation de l'horloge), NOM-009 (bilan de santé
de routine), CTG-001 (délestage sur sous-tension), CTG-008 (panne du senseur
stellaire) et EMG-006 (emballement thermique). Il existe trois types de liens :
`activity_type` (la fiche correspond à une activité du planificateur), `steps_file`
(une liste d'étapes YAML de référence) et `markdown` (les étapes de commande sont dérivées
des annotations `**TC:**` de la fiche elle-même, ce qui n'est légitime que si
ces annotations constituent la *totalité* des commandes de la fiche).

Une fiche qui, délibérément, ne commande rien — une procédure purement segment sol,
par exemple — est déclarée comme telle avec `advisory: true` et un
`advisory_reason` dans son entrée d'index. Elle ne porte **aucun** lien `runnable:`
et le MCS la signale comme non exécutable. Ne voyez pas dans une fiche consultative une forme
affaiblie de fiche exécutable : c'est une déclaration à part entière selon laquelle le document ne contient
aucune télécommande.

Trois comportements de l'exécuteur comptent à la console :

- **Une procédure qui n'a rien fait n'est pas un succès.** L'exécuteur ne
  signale plus de succès pour une exécution au cours de laquelle aucune commande n'a réellement été
  envoyée. Une reprise qui exécutait silencieusement zéro étape était autrefois
  impossible à distinguer d'une reprise réussie ; c'est désormais un échec visible.
- **Les étapes `label` et `branch` s'exécutent réellement.** L'exécuteur du MCS adresse
  les étapes au moyen d'un compteur de programme plutôt que d'une boucle fixe, de sorte qu'une étape `branch`
  peut faire sauter l'exécution vers une étape étiquetée. Deux garde-fous indépendants garantissent que cela
  se termine : une borne `max_taken` par branche et un nombre maximal d'étapes pour l'ensemble de la procédure.
- **Les types d'étapes inconnus échouent en position sûre.** Si l'exécuteur rencontre un type d'étape qu'il
  ne comprend pas, il fait échouer la procédure au lieu de sauter
  l'étape et de continuer. Si vous voyez une exécution échouer sur une étape non reconnue,
  c'est la fiche qui est erronée, pas l'exécution.

## 9.4 Déroulé de procédure — CTG-003 Rétablissement après perte de liaison TTC

CTG-003 se déclenche lorsque `ttc.link_status` (0x0501) reste à 0 plus de 30 s
après l'AOS prévue, ou lorsqu'une liaison établie tombe en cours de passage.
LOCKED vaut **2**, et non 1 : une fiche ou une vue qui traite 1 comme « verrouillé » est
erronée. La procédure est présentée ci-dessous au
**format « problème d'abord » des QRH de l'aviation** : le symptôme, formulé en langage
courant par l'opérateur, sert de titre, et la page lui indique ce qu'il doit
s'attendre à voir, quelles peuvent en être les causes, ce qu'il faut tenter, et dans
quel ordre.

> # Ce que je constate : la liaison tombe en cours de passage
>
> **Premiers indicateurs (3 au plus, du plus au moins évident) :**
> 1. **`ttc.link_status` (0x0501) passe de 2 (LOCKED) à 0** — le symptôme le plus
>    évident.
> 2. **`ttc.link_margin` (0x0503) s'effondre** et `ttc.rssi` (0x0502)
>    chute avec elle.
> 3. **`ttc.tx_gate_status` (0x052B) indique quel verrou s'est ouvert** — bit 0 : PA
>    en marche ; bit 1 : ligne EPS `ttc_tx` alimentée ; bit 2 : station en visibilité ; bit 3 : émission en bande S
>    active. 0xDF correspond à une émission normale.
>
> Il n'existe aucune règle FDIR `ttc_link_loss` à attendre : la perte de liaison se diagnostique
> à partir de la télémesure, et non par le déclenchement d'une règle. Notez aussi que la **balise UHF
> est un émetteur distinct** : perdre la chaîne principale en bande S ne
> signifie pas nécessairement que le satellite est muet. Vérifiez `ttc.beacon_active`
> (0x0527) : le SID 11 sur la balise peut survivre à un PA bande S éteint.
>
> **Actions mémorisées (à effectuer AVANT de consulter cette page) :**
> 1. **Vérifier que la station sol est toujours en poursuite** (consulter le panneau
>    d'état des stations du MPS : si elle n'est PAS en poursuite, le problème ne vient
>    *pas* du satellite).
> 2. **Noter l'attitude actuelle du satellite** — des basculements rapides peuvent
>    faire tomber brièvement la liaison ; si un basculement est en cours, attendre 10 s.
> 3. **Annoncer « Mark »** sur la boucle afin que le débriefing après passage dispose de
>    l'instant exact de la perte.
>
> **Hypothèses de cause (de la plus à la moins fréquente) :**
> - **Marge du trajet RF trop faible** — limite d'ombre solaire, masquage de l'antenne
>   sol, baisse d'élévation en cours de passage.
> - **Surchauffe de l'amplificateur d'émission bord** — `ttc.pa_temp` (0x050F)
>   élevée ; la règle `ttc_pa_overheat_pa_off` éteint le PA.
> - **Resynchronisation de la bande de base de la station sol** — récupérable en quelques secondes.
> - **Chute de la puissance d'émission incidente bord** — `ttc.tx_fwd_power`
>   (0x050D) faible ; `ttc.pa_on` (0x0516) = 0.
> - **Brouillage par un événement à particules solaires** — rare ; affecte les passages
>   polaires lors d'épisodes de météorologie de l'espace.
>
> **Arbre de décision :** le rétablissement suit l'échelle d'escalade ci-dessous.

![Échelle d'escalade du rétablissement après perte de liaison TTC : si link_status quitte 2, vérifier que la station sol est toujours en poursuite, puis commander en aveugle le transpondeur principal, basculer sur le transpondeur redondant, réessayer le principal, et vérifier la qualité de liaison et la santé des sous-systèmes, avec escalade vers EMG-004 (perte de communication) si rien ne rétablit la liaison.](../assets/figures/fig_link_loss_ladder.svg)

*Échelle d'escalade du rétablissement après perte de liaison TTC : si `link_status` quitte 2 (LOCKED), vérifier que la station sol est toujours en poursuite, puis commander en aveugle le transpondeur principal, basculer sur le transpondeur redondant, réessayer le principal, et vérifier la qualité de liaison et la santé des sous-systèmes, avec escalade vers EMG-004 (perte de communication) si rien ne rétablit la liaison.*

### Liste de vérification CTG-003 (lire-et-exécuter)

Tableau 9.3 — Liste de vérification lire-et-exécuter de CTG-003 (rétablissement après perte de liaison TTC), avec vérifications et renvois d'escalade.

| N° | Responsable | Question | Action / TC | Réponse attendue | Renvoi en cas d'échec | ☐ | Note / valeur réelle |
|---|---|---|---|---|---|:-:|---|
| 1 | TT&C | Confirmer la perte de liaison | Lire `ttc.link_status` (0x0501), `ttc.rssi` (0x0502), `ttc.link_margin` (0x0503) | `link_status` = 0, marge effondrée | (aucun) | ☐ | état _____ marge _____ |
| 2 | Segment sol | Le problème est-il au sol ? | Panneau d'état des stations du MPS ; vérifier la poursuite de l'antenne, la puissance de liaison montante, la précompensation Doppler, le brouillage RF local et la météo | Pointage de l'antenne correct, bande de base nominale | CTG-020 | ☐ | _____________ |
| 3 | TT&C | Réacquisition en aveugle sur le principal | `HK_REQUEST(sid=6)` (S3.27), puis attendre 30 s | `ttc.link_status` = 2 (LOCKED) dans les 30 s ; `ttc.rssi` > -95 dBm | (aucun) | ☐ | état : ____ |
| 4 | TT&C | Basculer sur le transpondeur redondant (GO du FD) | `TTC_SWITCH_REDUNDANT` (S8.1) — commande en aveugle, attendre 45 s | `link_status` = 2 dans les 45 s ; `ttc.mode` (0x0500) indique le redondant actif | (aucun) | ☐ | mode : ____ |
| 5 | TT&C | Réessayer le principal | `TTC_SWITCH_PRIMARY` (S8.1) — commande en aveugle, attendre 45 s | `link_status` = 2 dans les 45 s | EMG-004 | ☐ | état : ____ |
| 6 | TT&C | Vérifier la qualité de liaison | Lire `link_status`, `rssi`, `link_margin`, `ttc.mode` | `link_status` = 2, RSSI > -90 dBm, marge > 3.0 dB | (aucun) | ☐ | marge ____ dB |
| 7 | SPACON | Écarter une cause côté satellite | `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)`, `HK_REQUEST(sid=6)` (toutes S3.27) | `eps.bus_voltage` (0x0105) > 27.0 V ; `obdh.mode` (0x0300) ni en survie ni en urgence | (selon le constat) | ☐ | bus ____ V |
| 8 | SPACON | Consigner le rétablissement | Entrée dans la main courante avec chaque commande en aveugle et son horodatage | Main courante complète | (aucun) | ☐ | ID d'entrée : ________ |
| 9 | TT&C | Ouvrir une fiche d'anomalie | (formulaire de fiche) | Fiche enregistrée avec une hypothèse de cause | (aucun) | ☐ | fiche n° : _______ |

> **Critère de sortie.** Soit : (a) `ttc.link_status` = 2 (LOCKED) avec
> une marge > 3 dB ; soit (b) la liaison ne peut être rétablie sur aucun des deux transpondeurs et
> le FD déclare EMG-004 (perte de communication).
>
> **Si la liaison revient mais reste faible** (RSSI < -95 dBm ou marge < 1.5 dB),
> *descendre* d'un échelon dans l'échelle de débits TM, jusqu'à LOW (16 kbit/s), avec
> `TTC_SET_DATA_RATE(rate=0)` (S8.1, func 65). LOW est l'échelon des opérations
> de routine : il transporte l'ensemble complet de la télémesure de servitude, mais ne permet pas
> de vidage. L'échelle est BEACON / LOW / HIGH = 1 / 16 / 128 kbit/s.

**Liste des éléments de la fiche** (à renseigner avant de soumettre la
fiche) :

- ☐ Heure du premier indicateur
- ☐ Heure du rétablissement (ou de l'escalade vers EMG-004)
- ☐ Étape à laquelle la liaison a été rétablie (3, 4, 5 ou « non rétablie »)
- ☐ Hypothèse de cause première (marge RF / amplificateur / bande de base / alimentation / inconnue)
- ☐ Recommandation pour le passage suivant

### Pourquoi cette structure

La procédure monte en puissance de l'action *la moins intrusive* (écarter le segment
sol, puis une seule demande de télémesure de servitude en aveugle sur le transpondeur dont vous
disposez déjà) à l'action *la plus intrusive* (un basculement de transpondeur en aveugle, qui
vous fait perdre la configuration que vous connaissez et 45 s de temps de passage). Le principe
est emprunté à la réanimation cardio-pulmonaire : tenter d'abord ce qui ne coûte rien ; ne passer à l'échelon supérieur que si
cela ne fonctionne pas. Le même principe régit la plupart des procédures de contingence de
ce manuel.

### Ce que les opérateurs oublient souvent

- Sauter directement à l'étape 4 parce que *« le transpondeur est manifestement en panne »*.
  Les étapes 2 et 3 ne coûtent rien et indiquent si le problème se situe au
  sol ou à bord. Les sauter fait perdre des informations de diagnostic
  et peut vous laisser sur le transpondeur redondant sans raison.
- Oublier l'étape 9 (la fiche). Les anomalies qui
  « se sont résolues d'elles-mêmes pendant le passage » donnent quand même lieu à une fiche. Les
  fiches accumulées orientent la planification du passage suivant.

## 9.5 Entraînement à la passation de consignes — NOM-012

Source : `procedures/nominal/shift_handover.md`.

NOM-012 est le protocole dans lequel *le FD sortant briefe le FD entrant*. Durée
cible : **6 minutes**. Une passation plus longue signifie généralement que
le FD sortant n'a pas tenu la main courante à jour pendant le quart.

### Modèle NOM-012 (repris textuellement de la procédure)

Le FD sortant lit :

1. **Phase et temps.** « Le satellite est en phase 6, temps écoulé depuis le lancement
   T+ [jours]. Prochaine transition de phase : nominal, aucune prévue. »
2. **Dernier passage achevé.** « Dernier passage : Iqaluit, AOS T-22:45, LOS
   T-13:20. Nominal. »
3. **Anomalies ouvertes.** Les énumérer une à une avec le nom de la règle FDIR, l'état
   (active / acquittée / effacée) et la procédure de reprise
   en cours. « Anomalie ouverte : `eps_payload_load_yellow`,
   acquittée, CTG-012 étape 3 sur 7 achevée. »
4. **Travaux en cours.** Procédures commencées mais non terminées. « NOM-002,
   séance de prise de vue en cours, deux cibles sur trois acquises,
   la troisième reportée au passage suivant. »
5. **Prochain passage.** « Prochain passage : Troll, AOS T+05:12. Le plan prévoit
   NOM-001 (ouverture), NOM-002 pour acquérir la cible reportée,
   NOM-003 (liaison descendante), NOM-009 (bilan de santé). »
6. **Engagements envers le client.** « Le client attend le lot d'images 047 d'ici
   la fin de la journée ; nous suivons. »
7. **Autorisations GO en suspens.** « J'ai autorisé la désaturation des roues
   par l'AOCS ; l'AOCS ne l'a pas encore exécutée. Je recommande que
   le FD entrant reconfirme le GO avant l'exécution. »
8. **Ambiance sur la boucle.** « L'équipe est reposée, aucun problème de fatigue. »

Le FD entrant collationne **deux éléments précis** pour confirmer
sa compréhension (en général les anomalies ouvertes et les autorisations
GO en suspens).

### Exercice d'entraînement

Chaque équipe réalise deux passations. Les durées inférieures à 6 min sont validées ;
les durées supérieures à 8 min donnent lieu à une remarque au débriefing.

## 9.6 Atelier de dynamique du vol

Atelier animé par la personne qui tient le poste FDS, à l'intention de l'équipe. Trois exercices :

1. **Prévoir les trois prochaines heures d'AOS** à partir de l'orbite actuelle.
   Utilisez `tools/orbit_tools.py predict --hours 24`. Comparez avec le MPS.
2. **Calculer la durée de passage en fonction de l'élévation maximale.**
   Utilisez la formule géométrique du §8.2.1. Vérifiez que la durée du prochain
   passage correspond à la prévision géométrique à 30 s près.
3. **Expliquer l'éclipse.** Calculez la fraction d'éclipse sur les 24 prochaines
   heures. Identifiez l'éclipse la plus longue et sa durée. Prévoyez
   le SoC de la batterie à la sortie de cette éclipse à l'aide de :

$$ SoC_{exit} = SoC_{entry} - \frac{P_{avg} \cdot t_{eclipse}}{E_{battery}} \cdot 100\% $$

où $P_{avg}$ est la charge électrique moyenne pendant l'éclipse, $t_{eclipse}$ est exprimé en
heures et $E_{battery}$ est l'énergie de la batterie. EOSAT-1 emporte une batterie GomSpace
NanoPower BPX 8S-1P, donc $E_{battery} = 100$ Wh, et la charge
moyenne sur l'orbite dans le profil *nominal* est de 28,8 W (`docs/plan_2026-08b/POWER_SIZING.md`,
§6 ; 25,6 W au repos, 32,8 W avec la prise de vue en fonctionnement par intermittence). Utilisez environ 29 W sauf
indication contraire du plan de passage.

Application, pour une éclipse d'environ 35 min :
$SoC_{exit} = 85\% - \frac{29 \cdot 0.58}{100} \cdot 100\% = 85\% - 16.8\% = 68.2\%$.

Recoupez le résultat avec `tools/power_budget.py`, qui est le même
modèle que celui sur lequel est jugé le critère de bouclage.

## 9.7 Répétition à blanc 1 — passage nominal, sans panne

- **Scénario :** BP-1 `nominal_ops.yaml`.
- **Durée :** 90 min en temps réel à la vitesse de simulation 1×.
- **Procédures attendues :** NOM-001 → NOM-002 → NOM-003 → NOM-009 → LOS.
- **Injection de pannes :** aucune.
- **Productions :** main courante de chaque poste ; l'équipe d'observation utilise
  uniquement la fiche d'évaluation par les pairs *Communications*.

## 9.8 Répétition à blanc 2 — passage nominal avec une panne

- **Scénario :** BP-1 plus injection de `eps_overcurrent.yaml`
  (ligne = `payload`) à T+30 min dans le passage.
- **Réponse attendue :** CTG-012 *Traitement d'une surintensité*.
- **Critère de réussite :** anomalie détectée en moins de 30 s, isolée en moins de
  90 s, CTG-012 exécutée en entier, passage poursuivi jusqu'à la LOS.
- **Productions :** main courante de chaque opérateur + fiche d'anomalie ; l'équipe d'observation
  utilise la fiche d'évaluation par les pairs *Technique*.

## 9.9 Classe de maître de la boucle vocale (approfondissement)

Cette section va au-delà des principes fondamentaux du §9.2. Les bases suffisent
pour mener une équipe à travers des passages nominaux ; le contenu de la classe de maître est ce qui
permet à une équipe de traverser une anomalie à chaud en gardant son sang-froid.

### Pourquoi la discipline de boucle vocale l'emporte sur la compétence brute

Comme l'a indiqué le §9.1, ce sont les défaillances de la boucle vocale — et non les erreurs de lecture de la télémesure — qui
constituent la cause dominante de la transformation d'anomalies récupérables en anomalies irrécupérables.
Les opérateurs qui savent interpréter la télémesure mais ne savent pas tenir la boucle sont
dangereux ; ceux qui savent tenir la boucle mais sont lents sur la télémesure
peuvent être formés. Consacrez votre temps à la boucle.

### Trois schémas à intérioriser

#### Schéma 1 : destinataire, émetteur, message

Toujours : `[ADDRESSEE], [SENDER] — [MESSAGE].`

Pourquoi : le cerveau du destinataire se met en alerte en entendant son indicatif en
tête de message. Quand le message arrive, il écoute déjà
au lieu de chercher à décoder.

Contre-exemple : `"Hey, can you check the battery voltage?"` —
personne ne sait qui pose la question, personne ne sait qui est censé
répondre.

#### Schéma 2 : Standby — Working — Done

Ne restez jamais silencieux pendant une action en cours. La boucle s'attend à
vous entendre à intervalles de moins de 30 secondes. Si vous êtes occupé :

- `"Standby."` — je m'en occupe ; je vais répondre ;
- `"Standby plus 30."` — je reviens dans 30 secondes ;
- `"Working it."` — action en cours ;
- `"Done."` — action terminée (toujours accompagné de ce qui a été
  fait).

Le silence est le pire signal sur la boucle. Il peut signifier « je ne suis peut-être
plus là », « je ne vous ai pas entendu » ou « je suis perdu » — trois
choses différentes, toutes mauvaises.

#### Schéma 3 : collationnement des actions critiques

Pour toute action commandée qui modifie l'état du satellite, le
responsable de l'action collationne le GO du FD. Schéma :

- FD : `"AOCS, FD — go for ST1_POWER on, then mode 4 NOMINAL."`
- AOCS : `"FD, AOCS — going for ST1_POWER on, then mode 4 NOMINAL."`
  (puis exécution)

C'est le protocole qu'utilisent les avions de ligne pour les clairances du contrôle aérien.
Il intercepte les erreurs d'écoute, les oublis et les erreurs de clic. Il
coûte 1,5 seconde et sauve des missions.

### Le vocabulaire des annonces — extension « anomalie à chaud »

(Vocabulaire de base au §9.2 ; nous ajoutons ici les variantes propres
aux anomalies à chaud.)

Tableau 9.4 — Annonces étendues de la boucle vocale pour les anomalies à chaud, avec leur signification et leur cas d'emploi opérationnel.

| Annonce | Signification | Cas d'emploi |
|---|---|---|
| « Anomaly, [parameter], [value] » | Télémesure hors plage | Toujours donner le paramètre et la valeur ; le FD a besoin des deux |
| « FDIR active, [rule] » | Une règle FDIR s'est déclenchée | Rôle du SPACON ; tout le monde écoute le nom de la règle |
| « Recovery procedure, [ID] » | Appel d'une procédure de contingence ou d'urgence | Le SPACON annonce laquelle |
| « Safe mode candidate » | Anomalie de gravité 4 | C'est au FD de décider du passage effectif en mode survie |
| « GO for safe mode » | Le FD autorise le passage en mode survie | Prononcé uniquement par le FD ; exige l'acquittement du responsable de mission |
| « Loss of [system] » | Un sous-système semble défaillant | TT&C pour la perte de liaison, EPS pour la perte d'alimentation, etc. |
| « Recovered, [system] » | La défaillance a disparu | Pendant de « loss of » |
| « Holding, [reason] » | Suspension de la procédure | Tout le monde peut annoncer HOLD ; le FD autorise la reprise |
| « Continuing, on [step] » | Reprise après une attente | Le SPACON reprend la procédure |
| « Mark, [event] » | Horodater l'événement dans le journal | Annonce normalisée de consignation d'événement |
| « Working an anomaly » | Je suis concentré, ne me briefez que si c'est critique | Indique à la boucle que la personne qui parle est en pleine concentration |
| « Clear to talk » | Je suis de nouveau disponible | Pendant de « working an anomaly » |
| « Confidence? » | Demande à un opérateur son degré de confiance dans sa lecture | Outil du FD lorsque la télémesure est douteuse |
| « [N] percent / [low/med/high] » | Réponse sur le degré de confiance | Forme normalisée |

### Exemple de transcription de boucle — traitement d'une anomalie

Voici une transcription modèle d'un traitement de surintensité selon CTG-012
pendant COM-009. Lisez-la à voix haute en équipe pour en sentir
le rythme. Les annonces restent en anglais, conformément à la phraséologie de la boucle.

---

```
T+24:18  EPS: "FD, EPS — anomaly, payload line current,
              0.92 A trending up. FDIR alert imminent."
T+24:20  Event log: 0x010F PDU_OVERCURRENT (severity HIGH,
                     subsystem EPS) — the EPS trips the payload
                     line and latches its overcurrent flag.
T+24:21  SPACON: "FD, SPACON — event 0x010F PDU overcurrent trip,
                  payload line, severity HIGH. Line opened
                  on board, OC flag latched."
T+24:22  EPS: "FD, EPS — confirming, payload line current 0 A,
              bus stable at 28.0 V. Line is OFF."
T+24:23  FD: "Copy all. SPACON, recovery procedure?"
T+24:24  SPACON: "FD, SPACON — recovery is CTG-012 Overcurrent
                  Response, six steps. The on-board trip did the
                  isolation for us. Step 1 identify — payload
                  line, confirmed. Step 2 per-line current —
                  `eps.line_current_3` reads 0 A. Step 3
                  isolate — Payload confirms no demand."
T+24:26  FD: "Steps 4 and 5 — reset the OC flag and re-enable —
              are next-pass work, not this shift. We are not
              re-energising a line we haven't diagnosed.
              Payload, file the ticket."
T+24:28  Payload: "FD, Payload — going for ticket. Working it."
T+24:35  Payload: "FD, Payload — ticket 003 filed. Root cause
                  hypothesis: cold-start in-rush exceeded the
                  trip threshold; cooler-side draw spike unlikely.
                  Recommend re-attempt next pass after thermal
                  stabilisation."
T+24:38  Mission Manager: "FD, MM — customer bulletin?"
T+24:39  FD: "MM, FD — yes, draft a bulletin: payload power-on
              deferred to next pass; FPA cool-down delayed by
              one pass; First Light projection shifts from end
              of Pass 4 to start of Pass 5. Standby for FD
              edit."
T+24:42  MM: "FD, MM — drafting, will read for your edit at
              plus 5 minutes."
T+24:43  FD: "All positions — we're holding COM-009 retry until
              next AOS. Until then, run COM-007 OBDH checkout
              early; that's productive work that doesn't depend
              on payload. SPACON, lead. Pass continues."
T+24:45  SPACON: "FD, SPACON — going for COM-007. Loading procedure.
                 OBDH, ready?"
```

Observez le rythme : un indicateur à +18, une alerte FDIR deux secondes
plus tard, la reconnaissance quatre secondes après, une décision de reprise
quatre secondes plus tard encore. Entre le premier indicateur et « we're holding
COM-009 », il s'est écoulé 25 secondes. C'est un travail compétent.

### Défaillances fréquentes sur la boucle (et corrections)

#### Défaillance : interférences de parole

Deux personnes se mettent à parler en même temps. La correction normalisée
consiste pour le FD à annoncer `"Loop discipline."` : tout le monde s'arrête, le
FD désigne qui doit parler en premier, cette personne parle, puis
l'autre.

Si l'interférence a lieu *entre le FD et un opérateur*, le FD
cède la parole à l'opérateur (c'est généralement l'opérateur qui détient l'information
urgente ; la question du FD peut être répétée). Si elle a lieu entre deux
opérateurs, le FD en choisit un.

#### Défaillance : le FD silencieux

Le FD ne dit rien pendant 30 secondes ou plus au cours d'une anomalie active.
Les opérateurs ne savent plus s'ils doivent agir. Correction : le SPACON
annonce `"FD, status?"` et le FD doit répondre dans les 5 secondes,
au minimum par *« FD, standby. »*

#### Défaillance : le FD trop directif

Le FD ordonne des actions au lieu de demander leur évaluation aux opérateurs.
Symptômes : `"AOCS, do X"` au lieu de `"AOCS, FD —
recommend?"`. Les opérateurs se sentent rétrogradés ; leur implication baisse ; le
FD devient un point de défaillance cognitive unique.

Correction : le directeur de mission intervient en cours
de quart, annonce une attente de 30 secondes et rappelle au FD de *demander plutôt que
d'ordonner*.

#### Défaillance : collationnement omis

Le FD dit `"GO for ST1_POWER on"`, l'AOCS exécute sans
collationner. Si c'est une mauvaise TC qui vient d'être envoyée, personne ne s'en aperçoit
avant l'échec de la vérification.

Correction : le directeur de mission intervient immédiatement. L'opérateur
n'exécute plus rien sans collationnement.

#### Défaillance : l'avalanche d'acronymes

Les opérateurs enchaînent tant d'acronymes que personne ne comprend
ce qui a été dit. Symptômes : `"FD, AOCS — STR at FAULT, gyros in
DRA, resetting EST for ADQS."` — prononcé vite, en sigles,
sans nommer ni paramètre ni commande.

Correction : à la réunion de planification suivante, l'équipe convient d'un
répertoire d'abréviations. Les nouveaux opérateurs sont briefés avant de rejoindre
la boucle.


### Ce qu'il faut pratiquer

Exercices en binôme, 15 minutes chacun, avant tout quart à fort enjeu :

1. **Exercice de collationnement.** Une personne joue le FD et donne une série de
   commandes. L'autre collationne chacune d'elles.
2. **Exercice de discipline de boucle.** Deux personnes provoquent délibérément des interférences de parole
   sur un scénario écrit ; une troisième annonce `"Loop discipline"` et
   relance l'échange.
3. **Exercice d'annonce d'anomalie.** Une personne lit une valeur de
   télémesure ; l'autre doit formuler l'annonce en moins de 5 secondes.
4. **Exercice HOLD et reprise.** Dérouler une procédure de 90 secondes avec une
   annonce HOLD surprise à mi-parcours. S'entraîner à la reprise.

---

## 9.10 Références

- ECSS-E-ST-70-32C — *Test and operations procedures* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/)
- Supports de la NASA APPEL sur la boucle vocale et les opérations de mission — [appel.nasa.gov](https://appel.nasa.gov/)
- FAA AC 120-71 — *Standard Operating Procedures* — [www.faa.gov](https://www.faa.gov/regulations_policies/advisory_circulars/)
- FAA *Crew Resource Management* AC 120-51E — [www.faa.gov](https://www.faa.gov/regulations_policies/advisory_circulars/)

# Chapitre 10 — Opérations LEOP

Ce chapitre couvre les opérations depuis la séparation du lanceur jusqu'à
la fin de la **phase de lancement et de début d'orbite (LEOP)**,
période pendant laquelle le satellite passe de la phase 3
(BOOTLOADER_OPS : seuls l'OBC et le récepteur sont alimentés et
l'image du chargeur d'amorçage s'exécute) à la phase 4 (LEOP), puis en sort
pour entrer en phase 5 (COMMISSIONING) : les ailes solaires déployées, la suite AOCS alimentée,
l'amortissement des vitesses angulaires (detumbling) convergé vers le maintien au Soleil COARSE_SUN,
le temps synchronisé et l'orbite restituée. La charge utile, le refroidisseur, les roues et les
senseurs stellaires restent éteints ; ils relèvent de la recette en orbite. Notez que le déploiement de l'**antenne
bande S** n'est *pas* une étape de la LEOP : c'est l'étape 0 de COM-006
(`TTC_DEPLOY_ANTENNA`, S8.1 func 69), car l'échelon LOW de l'échelle
de débits n'en a pas besoin et que la LEOP ne requiert jamais le échelon HIGH. Les codes de phase figurent dans
`eps.spacecraft_phase` (0x0129) : 0 pré-séparation, 1 minuterie de séparation,
2 mise sous tension initiale, 3 opérations sous chargeur d'amorçage, 4 LEOP, 5 recette en orbite, 6 nominal.
La déclaration finale de la phase 5 se fait à la fin de LEOP-003, la dernière fiche
de la LEOP, avec la télécommande de vol `SYS_SET_MISSION_PHASE(phase=5)` (S8 fonction 120) ;
rien à bord ne fait avancer la phase au-delà de 4 de lui-même.

La LEOP est la phase de la mission où les enjeux sont les plus élevés. C'est la *première*
fois que tout doit fonctionner, sans possibilité de répétition à blanc. Une vraie
LEOP se déroule **24 h/24, 7 j/7, en trois quarts de huit heures** ; ce manuel
en propose une présentation condensée, adaptée à la formation, dans laquelle la
séquence LEOP est répartie sur une suite de passages au-dessus des stations sol.

## 10.1 Conditions d'entrée en phase LEOP

- **Point de reprise de la simulation :** BP-2 *LEOP Day Start*
  (`scenarios/first_contact.yaml`).
- **Phase au départ :** 3 (BOOTLOADER_OPS).
- **Visibilité initiale :** Iqaluit, AOS à T+0 du scénario.
- Indicateur **`override_passes`** positionné afin que la visibilité soit maintenue pendant le passage.
- **Facteur d'accélération :** 1×.

## 10.3 Briefing de phase de mission

Le satellite vient de sortir de la minuterie de séparation (phase 2, mise sous tension
initiale) et se trouve en phase 3, BOOTLOADER_OPS. L'OBC exécute le
*chargeur d'amorçage*, qui n'émet **que le SID 11 (balise)** : l'ensemble activé à la mise sous tension
est `default_enabled_sids: [1, 11]`, et sous le chargeur d'amorçage seule la
structure de balise est produite. Ni l'antenne bande S ni les ailes
solaires ne sont déployées : `ttc.antenna_deployed` (0x0520) = 0 et
`eps.wing_status` (0x0144) = 0x00. L'état des lignes
au démarrage à froid est le suivant : `obc` et `ttc_rx` sur ON (non commutables) ;
`ttc_tx`, `htr_bat`, `htr_obc`, `aocs_wheels`, `payload`, `fpa_cooler`
et `prop` tous sur **OFF**. Le satellite est donc à l'écoute dans un seul sens :
muet sur la liaison descendante jusqu'à ce que la première télécommande acceptée arme
l'émetteur.

L'AOCS est en **mode 0 (OFF)** — il n'amortit pas les vitesses angulaires, il n'est même pas cadencé — avec
des vitesses de culbutage résiduelles d'environ 1–2 °/s dues à l'impulsion de séparation.
L'amortissement n'a *pas* encore eu lieu ; il est commandé à l'étape 5 de LEOP-007.
Le SoC de la batterie est de 90 % (`simulation.yaml` `eps.initial.soc_pct`). Le
premier AOS au-dessus d'Iqaluit a lieu à T+0 dans le scénario.

L'objectif de l'équipe pendant le quart est d'amener le satellite de la
phase 3 (chargeur d'amorçage) à la phase 4 (LEOP), jusqu'au point où
l'équipe de direction de la mission peut déclarer la phase 5 (COMMISSIONING).

## 10.4 Ordre d'exécution des procédures

Les sept procédures LEOP, dans leur ordre d'exécution, avec leur durée
prévue et le poste pilote :

Tableau 10.1 — Ordre d'exécution des procédures LEOP, avec poste pilote, durée et étape critique.

| N° | Procédure | Poste pilote | Durée (simulation) | Étape critique |
|---|-----------|---------------|----------------|---------------|
| 1 | LEOP-001 Première acquisition du signal et amorçage de l'OBC | TT&C + SPACON | ~6 min | Étape 5 : `OBC_BOOT_APP`, puis étape 5a : lever le mode balise |
| 2 | LEOP-002 Bilan de santé initial | SPACON + tous les postes | ~8 min | SID 1, 3, 4 et 6 dans la plage ; lignes AOCS, charge utile, refroidisseur et prop confirmées OFF |
| 3 | LEOP-004 Vérification du générateur solaire | EPS | ~10 min | Étape 0 : `EPS_DEPLOY_WING(wing=2)` ; étape 6 : symétrie des ailes |
| 4 | LEOP-007 Mise sous tension séquentielle | SPACON + EPS + AOCS | un contact de 8 min | Étapes 3–5 : ligne de la suite AOCS sous tension et SID 2 activé ; magnétomètre, magnétocoupleurs et GPS en service ; mode → 2 DETUMBLE |
| 5 | LEOP-005 Acquisition du Soleil | AOCS | limitée par l'amortissement | Étape 3 : passage automatique en 3 COARSE_SUN — observé, non commandé |
| 6 | LEOP-006 Synchronisation temporelle | SPACON | ~5 min | Étape 4 : `SET_TIME`, résidu < 1.0 s ; étape 6a : SID 12 et asservissement GPS |
| 7 | LEOP-003 Restitution d'orbite initiale | FDS + FD | ~15 min sur deux points | Étape 7 : `SYS_SET_MISSION_PHASE(phase=5, flags=0)` — la fin de la LEOP |

Notez l'ordre. C'est celui de `procedures/procedure_index.yaml` et des
états d'entrée et de sortie de chaque fiche. Les ailes sont déployées
(LEOP-004) juste après le bilan de santé, avant que quoi que ce soit
d'autre ne consomme. LEOP-007 n'alimente ensuite que ce dont le reste de
la LEOP a besoin — les réchauffeurs si leurs zones ont besoin de chaleur,
la ligne de la suite AOCS, le magnétomètre, les magnétocoupleurs et le
récepteur GPS — et commande DETUMBLE. La ligne charge utile et le
refroidisseur du FPA sont des charges de la recette en orbite (COM-009,
COM-010) ; les roues de réaction restent DISABLED jusqu'à COM-004, et les
senseurs stellaires et les gyroscopes restent éteints jusqu'à COM-003.
LEOP-005 ne commande rien : l'AOCS passe de lui-même de DETUMBLE à
COARSE_SUN et, sans senseur stellaire en service, y reste. LEOP-006 règle
d'abord l'horloge depuis le sol, puis seulement l'asservit au GPS ;
LEOP-001 ne règle volontairement **pas** l'horloge (son étape 6 se borne
à noter qu'elle n'est pas réglée).

LEOP-003 est une procédure menée en console, et non autonome. Elle lit la
solution GPS, transmet le TLE affiné aux outils sol — rien n'est envoyé au
satellite — et clôt la LEOP par la déclaration de la phase 5, la seule
télécommande qui fait sortir le satellite de la phase 4. LEOP-004 est la
**vérification du générateur solaire**, et non son « déploiement », et
elle ne décrit *pas* quelque chose qui a déjà eu lieu : au démarrage à
froid, les deux ailes sont repliées (`eps.wing_status` 0x0144 = 0x00), et
l'étape 0 de la fiche commande réellement `EPS_DEPLOY_WING(wing=2)`.
Prévoyez-en le temps.

## 10.5 Guide par poste pour la LEOP

### Directeur de vol

- Avant le passage : confirmer les affectations de poste des deux équipes.
  Faire un contrôle de communication sur la boucle.
- Pendant le passage : demander le GO pour chaque action commandée.
  Surveiller l'indicateur de phase. Autoriser l'enchaînement LEOP-001 →
  -002 → -004 → -007 → -005 → -006 → -003.
- Critère du passage : à la fin de la LEOP, les deux ailes sont indiquées
  déployées dans `eps.wing_status` (0x0144), l'AOCS maintient le Soleil en
  mode 3 sur les magnétocoupleurs, l'horloge est référencée, l'orbite est
  restituée, et la phase vaut 5 après un tour de table unanime et la
  télécommande `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (étape 7 de
  LEOP-003). Seules les charges de la LEOP sont en service : les lignes
  charge utile, refroidisseur et prop sont OFF et les roues désactivées.
- Écueils : se précipiter sur LEOP-007 avant que LEOP-002 ait confirmé la
  santé du satellite. Accorder un GO pour une commande COARSE_SUN, quelle
  qu'elle soit — le passage est automatique, fixé par la physique de la loi
  B-dot, et la machine de modes se promeut d'elle-même quand les vitesses
  sont réellement descendues. Attendre que la phase avance d'elle-même :
  rien à bord ne la fait passer au-delà de 4.

### SPACON

- Avant le passage : charger le jeu de procédures LEOP dans le panneau des procédures.
  Il n'existe **ni table FDIR LEOP ni table FDIR nominale** entre lesquelles
  basculer : le simulateur arme toutes les règles en permanence, et chaque
  définition événement-action s'active ou se désactive individuellement avec
  `EA_ENABLE` (S19.4) et `EA_DISABLE` (S19.5). Si une règle doit être
  inhibée pendant une étape, inhiber cette règle par son `ea_id` et inscrire l'identifiant dans
  la main courante afin qu'elle soit réactivée.
- Pendant le passage : piloter l'exécution des procédures. Surveiller la transition d'image dans
  `obdh.sw_image` (**0x0311**) : 0 = chargeur d'amorçage, 1 = logiciel applicatif. Il
  n'existe ni paramètre `obdh.obc_mode` ni compteur de réarmement du chien de garde ; les
  indices d'un redémarrage sont `obdh.uptime` (0x0308), `obdh.reboot_count`
  (0x030A) et `obdh.last_reboot_cause` (0x0316).
- Étape critique : `OBC_BOOT_APP` (étape 5 de LEOP-001). L'OBDH vérifie le
  CRC de l'application sur une fenêtre de 10 s avant que `sw_image` ne change ; une
  courte interruption de télémesure à ce moment est donc normale. Ce qui n'est **pas** automatique, c'est la
  télémesure de servitude : l'amorçage de l'application réapplique
  `default_enabled_sids: [1, 11]`, si bien qu'après l'amorçage vous disposez du SID 1 et du
  SID 11 et de rien d'autre tant que vous n'avez pas envoyé `HK_ENABLE` (S3.5) pour chacun des SID  3, 4 et 6 — puis 2 dans LEOP-007 et 12 dans LEOP-006 (le SID 5 attend
  la ligne charge utile : COM-009 le demande).
- Écueils : déclarer LEOP-001 terminée sans les `HK_ENABLE`s.
  Oublier l'étape 5a : l'amorçage de l'application ne désactive **pas** le mode
  balise, et tant que `ttc.beacon_mode` (0x0521) vaut 1, toute
  `TTC_SET_DATA_RATE` est refusée avec l'erreur S1.8 `0x0007`.

### AOCS

- Avant le passage : examiner les vitesses de culbutage résiduelles du
  briefing du scénario (~1–2 °/s, en partie amorties depuis la
  séparation). Noter que le modèle AOCS ne s'exécute même pas : la ligne
  est éteinte et le mode vaut 0 (OFF).
- Pendant le passage : passif jusqu'à l'étape 3 de LEOP-007. Prendre
  ensuite la main : `HK_ENABLE(sid=2)` (S3.5) pour voir quoi que ce soit ;
  à l'étape 4, activer les deux éléments de DETUMBLE —
  `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` et
  `MTQ_ENABLE(enable=1)` (S8.1 **func 9**) — ainsi que le récepteur GPS ;
  à l'étape 5, envoyer `AOCS_SET_MODE(mode=2)` — DETUMBLE — avec S8.1
  **func 0**, exemptée de la condition de mode du sous-système et donc la
  commande qui fait sortir l'AOCS de OFF. La commande de mode refuse
  franchement si un élément manque : `0x0A20` pas de magnétomètre,
  `0x0A21` pas de magnétocoupleurs, `0x0004` ligne éteinte.
- Étape critique : l'étape 5 de LEOP-007 et l'attente qui suit, qui est
  LEOP-005. L'amortissement repose sur une loi B-dot pilotée par le
  magnétomètre, et il est lent (voir le §10.11). On n'entre pas en
  COARSE_SUN à la main : la machine de modes promeut d'elle-même DETUMBLE
  → COARSE_SUN dès que la norme de la vitesse angulaire est restée sous
  0,5 °/s pendant 30 secondes consécutives. Sans senseur stellaire sous
  tension, elle y reste jusqu'à la recette en orbite ; les roues restent
  désactivées jusqu'à COM-004.
- Écueils : commander le mode 3, quel que soit le moment. Interpréter la
  *hausse* de la vitesse sur un axe comme une loi de commande défaillante —
  la loi B-dot n'amortit que la composante de la vitesse perpendiculaire
  au champ local, si bien que l'énergie passe réellement d'un axe à
  l'autre pendant que la norme totale décroît. Juger la loi sur la RSS des
  trois vitesses, jamais sur un seul axe. L'état des magnétocoupleurs est
  dans `aocs.mtq_enabled` (0x025E), leurs rapports cycliques en
  0x0258–0x025A.

### EPS

- Avant le passage : SoC de 90 % ; `obc` et `ttc_rx` sous tension et non
  commutables ; toutes les lignes commutables OFF. Il y a **neuf** lignes
  d'alimentation, d'indices 0–8 : 0 obc, 1 ttc_rx, 2 ttc_tx, 3 payload,
  4 fpa_cooler, 5 htr_bat, 6 htr_obc, 7 aocs_wheels, 8 prop.
  `EPS_POWER_ON` / `EPS_POWER_OFF` / `EPS_RESET_OC_FLAG` prennent toutes
  un `line_index` dans 0–8.
- Pendant le passage : piloter d'abord LEOP-004 — chaque aile consomme
  ~2 A pendant 30 s lors de son déploiement. Dans LEOP-007, surveiller la
  consommation de chaque nouvelle ligne (`eps.line_current_0`…`_7`,
  0x0118–0x011F ; la ligne 8, prop, est `eps.line_current_8`, 0x014B) et
  l'indicateur de ligne (`eps.pl_*`, 0x0110–0x0117). Chaque nouvelle ligne
  est un petit événement de commande à part entière, avec GO du FD. Noter
  que l'EPS comptabilise d'après l'état réel des actionneurs, et non
  d'après la position de l'interrupteur de ligne — une ligne de
  réchauffeur sous tension mais coupée par le thermostat ne consomme pas
  sa puissance nominale.
- Point critique : l'étape 2 de LEOP-007 est conditionnelle. `htr_bat`
  (`EPS_POWER_ON(line_index=5)`, S8.1 **func 19**) n'est mise sous tension
  que si `tcs.temp_battery` est sous +5 °C, et `htr_obc` (`line_index=6`)
  que si `tcs.temp_obc` est sous 0 °C ; consigner les lignes alimentées,
  car COM-002 lit cet enregistrement. L'étape 6 confirme que les lignes
  charge utile, refroidisseur et prop sont toujours OFF et que la marge est
  positive.
- Écueils : ne pas repérer un pic de courant inattendu à la première mise
  sous tension d'un réchauffeur (l'appel de courant est normal ; une
  consommation élevée durable ne l'est pas).

### Thermique

- Avant le passage : toutes les zones passives (aucun réchauffeur en
  marche) ; la zone batterie peut se trouver en bas de plage.
- Pendant le passage : donner à l'EPS les températures des zones batterie
  et OBC avant l'étape 2 de LEOP-007 — ce sont elles qui décident si une
  ligne de réchauffeur est mise sous tension. Si c'est le cas, suivre
  l'évolution de la température de sa zone et le rapport cyclique du
  réchauffeur.
- Écueils : ne pas remarquer que la zone batterie met ~15 minutes à
  rejoindre sa plage après la première activation de `htr_bat`. Juger
  d'avance le réchauffeur batterie « bloqué à l'arrêt ».

### TT&C

- Avant le passage : confirmer la réception de la balise par la station en visibilité, et confirmer
  que le démodulateur est sur l'échelon **BEACON** : 1000 bit/s BPSK,
  conv(7,1/2)+RS, 1 kBd. C'est le seul débit qu'émet le chargeur d'amorçage.
- Pendant le passage : piloter LEOP-001 (acquisition de la liaison). À l'étape 5a, désactiver le mode balise
  avec `TTC_SET_BEACON_MODE(on=0)` (S8.1, func 70), puis sélectionner l'échelon
  **LOW** — 16 000 bit/s, 16 kBd — avec `TTC_SET_DATA_RATE(rate=0)`
  (S8.1, func 65). LOW est le débit des opérations de routine ; HIGH (128 kbit/s)
  est un débit de vidage et n'est pas utilisé en LEOP. Rôle passif ensuite pour le reste
  du passage.
- Écueils : s'attendre à pouvoir sélectionner HIGH. Les verrous sont, dans l'ordre :
  mode balise désactivé → LOW sélectionnable ; antenne déployée (`TTC_DEPLOY_ANTENNA`,
  func 69) **et** mode de liaison descendante activé (func 79) **et** élévation ≥ 10° →
  HIGH sélectionnable. Chaque verrou non levé renvoie S1.8 `0x0007` avec un avis
  d'échec qui nomme le verrou en toutes lettres : lisez l'avis, pas le code.
  Notez aussi que désactiver le *mode* balise n'est pas la même chose qu'éteindre
  l'émetteur de balise UHF : la balise est un émetteur **distinct**
  (`TTC_BEACON_TX_ON/OFF`, func 97/98), qui continue
  d'émettre le SID 11 même lorsque le PA bande S est éteint.

### Charge utile

- Avant le passage : ligne charge utile OFF, mode charge utile OFF, ligne
  du refroidisseur du FPA OFF.
- Pendant le passage : passif pendant toute la LEOP. LEOP-007 ne touche
  pas à la charge utile : la ligne charge utile, le passage en STANDBY avec
  `PAYLOAD_SET_MODE(mode=1)` (S8.1, func 26) — et non `SET_PAYLOAD_MODE`,
  que le catalogue associe à une autre commande — et le SID 5 viennent
  dans COM-009, la ligne du refroidisseur et `FPA_COOLER(on=1)` (func 43)
  dans COM-010. L'étape 6 de LEOP-007 confirme que les lignes charge utile
  et refroidisseur sont toujours OFF.
- Écueils : s'attendre à ce que le FPA atteigne une température froide
  arbitraire. L'enveloppe de consigne commandable va de **−20 °C à 0 °C**,
  −15 °C par défaut, et la disponibilité (`payload.fpa_ready`, 0x0610)
  suit la consigne *active*, et non une valeur fixe. Autre écueil : être
  distrait, hors de la boucle, et manquer son tour lors d'un tour de table
  GO/NO-GO général.

### FDS

- Avant le passage : produire le planning des passages sur 24 heures. Le
  remettre au FD, à la TT&C et au segment sol.
- Pendant le passage : passif jusqu'à la mise en service du récepteur GPS
  à l'étape 4 de LEOP-007 (`S2_AOCS_GPS_RECEIVER`, sur la ligne de la
  suite AOCS) ; un démarrage à froid peut prendre jusqu'à 15 min. Le SID
  12 est activé dans LEOP-006. Piloter ensuite LEOP-003 : vérifier le
  point, lire le vecteur d'état, comparer à l'orbite du lanceur et envoyer
  le TLE affiné aux outils sol.
- Écueils : utiliser le TLE fourni par le lanceur au lieu du vecteur
  d'état frais issu du GPS une fois celui-ci disponible. Chercher une
  commande pour charger l'orbite à bord — il n'y en a pas.

### Segment sol

- Avant le passage : vérifier que l'antenne d'Iqaluit est sur la cible. Vérifier que la bande de base
  est dans la configuration balise du chargeur d'amorçage (bas débit, bande
  étroite).
- Pendant le passage : piloter l'étape 1 de LEOP-001 (confirmer la poursuite de l'antenne, armer le forçage
  de passage, *Pass Override*). À l'étape **5a** de LEOP-001, reconfigurer le démodulateur de
  1 kBd à **16 kBd** *avant* d'attendre les SID des sous-systèmes : le démodulateur
  de balise ne se verrouillera pas à 16 kbit/s.
- Écueils : manquer le signal de reconfiguration de la bande de base ; l'équipe se retrouve
  avec le satellite sur l'échelon LOW et le sol encore sur l'échelon
  balise, et interprète le silence qui en résulte comme une panne du satellite.

### Responsable de mission

- Avant le passage : briefer les éventuels observateurs extérieurs (représentants du client qui assistent
  à la simulation LEOP).
- Pendant le passage : écoute passive. Noter tout élément destiné au bulletin
  client.



Le directeur de mission choisit **une** injection principale par équipe, plus une
injection secondaire facultative, enchaînée si la principale est résolue proprement.

Tableau 10.2 — Scénarios d'injection d'anomalies LEOP par niveau de difficulté, avec premiers indicateurs et procédures de reprise.

| Difficulté | Fichier de scénario | Ce que voient d'abord les étudiants | Procédure de reprise |
|---|---|---|---|
| Facile | `ttc_no_tm_at_aos.yaml` | Balise présente, la télémesure de servitude complète n'arrive jamais malgré OBC_BOOT_APP | CTG-019 Absence de TM en début de passage |
| Facile | `eps_overcurrent.yaml` | Surintensité soudaine sur une ligne d'alimentation pendant la mise sous tension séquentielle | CTG-012 Traitement d'une surintensité |
| Moyen | `aocs_actuator_stuck.yaml` | RW-1 (indice 0) se bloque à T+120 s — vitesse figée et insensible aux commandes de couple, température de la roue en hausse | CTG-026 Reprise après blocage d'un actionneur SCAO (CTG-007 Anomalie de roue de réaction pour le cas général) |
| Moyen | `aocs_star_tracker_failure.yaml` | Le senseur stellaire se dégrade après l'acquisition du Soleil | CTG-008 Panne du senseur stellaire |
| Difficile | `obc_watchdog.yaml` | Réinitialisation de l'OBC par le chien de garde en plein déploiement | CTG-010 Reprise après chien de garde OBDH |
| Difficile | `obc_bus_failure.yaml` | Le bus CAN A tombe pendant la mise sous tension séquentielle | CTG-017 Basculement sur panne de bus |
| Très difficile | `gs_antenna_failure.yaml` | Antenne d'Iqaluit dégradée en cours de passage ; reprise par Troll | CTG-020 Panne d'antenne de station sol |

Chaque injection dispose d'une fiche aide-mémoire d'une page au chapitre 14 (catalogue des procédures).

## 10.7 Critères GO/NO-GO de fin de passage (récapitulatif)

Tableau 10.3 — Critères GO/NO-GO de fin de passage évalués pour les deux équipes en formation.

| Critère | Passage 1 (équipe A) | Passage 2 (équipe B) |
|---|---|---|
| Logiciel applicatif de l'OBC en cours d'exécution (`obdh.sw_image` 0x0311 = 1) | ✓ | ✓ |
| Mode balise désactivé (`ttc.beacon_mode` 0x0521 = 0), liaison descendante au palier LOW (`ttc.tm_tier` 0x0539 = 1) | ✓ | ✓ |
| Temps bord réglé, résidu < 1.0 s | ✓ | ✓ |
| SID 1–6 activés et émis | ✓ | ✓ |
| Les deux ailes solaires déployées (`eps.wing_status` 0x0144 = 0x03) | ✓ | ✓ |
| Ligne du réchauffeur de batterie sur ON (`eps.pl_htr_bat` 0x0115 = 1) | ✓ | ✓ |
| Ligne `aocs_wheels` sur ON, AOCS en mode 2 DETUMBLE et vitesses en baisse | ✓ | ✓ |
| Norme de la vitesse angulaire sous le seuil de sortie de 0.5 °/s ; le mode est passé de lui-même en 3 COARSE_SUN | facultatif | ✓ |
| Fiche d'anomalie ouverte pour chaque injection | ✓ | ✓ |

Le directeur de mission se tient derrière le poste du FD et n'intervient
que par exception :

- **Discipline de boucle vocale.** Si l'équipe commence à se couper la parole,
  arrêter l'échange sur la boucle, nommer la règle, relancer.
- **Respect des procédures.** Si un poste commande sans GO du
  FD, arrêter, consigner, traiter comme une infraction à la sécurité.
- **Traitement des anomalies.** Si l'équipe est bloquée plus de 5 minutes, donner un
  indice au niveau du panneau FDIR (sans nommer la procédure).
- **Pression temporelle.** Horloge en temps réel : pas de pause de la simulation pour
  discuter. Le passage se termine quand l'orbite le veut.

## 10.9 Structure du débriefing

1. **Débriefing à chaud.** Le FD de chaque équipe lit les faits marquants
   de la main courante. Pas encore de critique.
2. **Retour sur l'anomalie.** L'équipe d'opérateurs déroule
   le traitement de l'anomalie ; l'équipe d'observation la questionne.
3. **Restitution de l'évaluation par les pairs.** Chaque équipe d'observation lit sa
   fiche à voix haute (Communications + Technique). L'équipe d'opérateurs
   répond par un point accepté et un point défendu par axe.
4. **Synthèse du retour d'expérience.** Le directeur de mission regroupe le tout
   en une liste unique, consignée dans le registre de retour d'expérience de la promotion.
5. **Briefing.** Lecture : fiches de procédure COM-001 à
   COM-008.

## 10.10 Lignes rouges

- **Aucune commande sans autorisation du FD.** Infraction → le directeur de mission
  interrompt le quart, l'équipe consigne l'infraction, sans pénalité si
  la leçon en est tirée.
- **Aucune pause du simulateur pour gagner un exercice.** L'horloge tourne.
- **Pas de FD silencieux.** Le FD doit être sur la boucle. S'il est trop directif,
  le directeur de mission annonce une attente de 30 s et réinitialise le poste.

---


## 10.11 Déroulés détaillés des procédures LEOP

Cette section détaille chaque procédure LEOP sous la forme d'un guide minute par minute
et poste par poste pour la phase LEOP. Les fiches de référence
du chapitre 14 sont destinées à la consultation en console ; ce
chapitre constitue le support de *formation* que l'équipe lit le mardi
soir, la veille du jour de la LEOP.

Pour chaque procédure, nous traitons :

- la **préparation préalable** — ce que l'équipe doit avoir prêt avant
  de commencer ;
- le **guide étape par étape** — chaque étape, avec la sollicitation du FD, l'annonce
  attendue du responsable, la télémesure de vérification et le
  *pourquoi* (la raison physique ou opérationnelle de l'étape) ;
- les **écarts fréquents** — ce qui se passe réellement mal et comment
  s'en sortir sans abandonner la procédure ;
- les **points de décision** — les moments où le FD a un véritable choix
  à faire ;
- les **pistes de débriefing** — ce qu'il faut examiner lors de la revue après le quart.

### LEOP-001 — Première acquisition du signal et amorçage de l'OBC (déroulé approfondi)

LEOP-001 représente les 5 à 12 minutes les plus déterminantes de toute la
mission. L'équipe dispose d'*une seule* fenêtre au-dessus d'Iqaluit pour faire passer le satellite
de l'état « séparé du lanceur et en culbutage » à l'état « logiciel applicatif de l'OBC en cours d'exécution
avec télémesure de servitude complète ». Si la fenêtre est manquée, la prochaine occasion sera le passage suivant
au-dessus d'Iqaluit (90 minutes plus tard, avec une situation énergétique dégradée et un
client inquiet).

#### Préparation préalable (avant AOS-5 min)

Le directeur de mission vérifie avec l'équipe :

1. **Affectation des postes confirmée.** Le TT&C est l'opérateur pilote
   de cette procédure ; le SPACON pilote le panneau des procédures ; le FD
   autorise chaque action commandée ; le segment sol est responsable de
   l'antenne et de la bande de base.
2. **Procédure chargée.** `procedures/leop/first_acquisition.md`
   est la procédure active dans le panneau.
3. **Essai de communication effectué.** Les neuf postes sont sur la boucle et
   audibles.
4. **Briefing avant passage.** Le FD lit à voix haute la liste de vérification LEOP avant passage
   (cahier d'exercices WB-5.5-PB). Chaque poste confirme qu'il est prêt.
5. **Langue de la boucle vocale déclarée.** Annonces en anglais (phraséologie
   normalisée, quelle que soit la langue de l'équipe). Consignée dans la main
   courante.
6. **Formulaires de fiche d'anomalie vierges imprimés à chaque console.**
7. **Salle de contrôle aménagée.** Le FD a une vue directe sur le TT&C et le
   SPACON (les deux opérateurs les plus actifs dans cette procédure).

À AOS-2 min, le FD annonce *« Two minutes to AOS. All positions,
report ready. »* Chaque poste répond dans l'ordre : *« FD, [POSITION] —
ready. »* Toute réponse *not ready* à ce stade appelle une décision immédiate
du FD : poursuivre ou suspendre (HOLD).

#### Guide étape par étape

**Étape 1 — Configurer le récepteur de la station sol et forcer le passage (Pass Override)**

Tableau 10.4 — Détail de l'étape 1 de LEOP-001 : configuration du récepteur de la station sol et forçage du passage.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « Ground Segment, FD — go for GS configure and pass override. » |
| Responsable | Ingénieur segment sol |
| Annonce attendue du responsable | « FD, Ground Seg — go for GS configure and pass override. » → exécution → « FD, Ground Seg — Iqaluit tracking ready, pass override armed. » |
| Action | Dans le MPS : pointer l'antenne d'Iqaluit sur l'azimut et l'élévation prévus à l'AOS ; activer la poursuite automatique sur la liaison descendante en bande S ; régler le démodulateur sur l'échelon **BEACON** (1000 bit/s BPSK, conv(7,1/2)+RS, 1 kBd), seul débit émis par le chargeur d'amorçage. Dans le MCS : activer le forçage de passage (`pass_override = 1`, paramètre 0x05FF). |
| Vérification | Le panneau de la station sol affiche TRACKING_READY ; l'en-tête du MCS affiche `Pass Override: ARMED`. |
| Raison d'être de l'étape | Le satellite est muet (aucune porteuse à poursuivre). La poursuite automatique ne peut pas s'accrocher sur rien : nous devons pointer l'antenne nous-mêmes à l'aide des éphémérides prévues. Le forçage de passage indique au MCS de « considérer le satellite en contact indépendamment des calculs d'orbite », ce qui permet de préparer des TC avant que le satellite ne réponde effectivement. |
| Critère GO / NO-GO du FD | L'antenne pointe effectivement : si le basculement de l'antenne est en cours, elle n'est pas encore stabilisée ; attendre. |

**Étape 2 — Envoyer la première TC montante (test de connexion)**

Tableau 10.5 — Détail de l'étape 2 de LEOP-001 : première liaison montante au moyen du test de connexion S17.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « TT&C, FD — go for first uplink, S17 connection test. » |
| Responsable | Ingénieur TT&C |
| Annonce attendue du responsable | « FD, TT&C — go for first uplink, S17.1. » → exécution → « FD, TT&C — S17 sent, awaiting S1 ack and S17.2 report. » |
| Action | Dans le panneau de commande : service S17, sous-service 1, sans données d'application. Première clé. (Pas de seconde clé pour S17 : c'est un test de connectivité, à faible risque.) |
| Vérification | Dans les 10 s : acquittement d'acceptation S1.1 reçu ; dans les 10 s : rapport de test de connexion S17.2 reçu ; `eps.pl_ttc_tx` (**0x0112**) indique 1 — l'émetteur est armé automatiquement par la temporisation de maintien. |
| Raison d'être de l'étape | Nous ne savons pas encore si la liaison fonctionne de bout en bout. S17 est le moyen le moins coûteux et le moins intrusif de le vérifier, et il figure sur la liste des TC autorisées en mode amorçage : il est donc accepté avant le chargement de l'image applicative. L'acquittement d'acceptation confirme la liaison montante sol-bord ; la réponse au test de connexion confirme la liaison descendante bord-sol. La **maintien automatique de l'émetteur (auto-TX hold-down)** est le mécanisme qui fait apparaître la liaison descendante au démarrage à froid : toute TC acceptée met de façon autonome la ligne `ttc_tx` sous tension pendant la durée `simulation.yaml` `ttc.auto_tx_hold_s`, fixée pour EOSAT-1 à **300 s (5 minutes)** et réarmée à chaque TC acceptée par la suite. Cinq minutes sans commande, et l'émetteur se coupe ; envoyez n'importe quelle TC pour le rétablir. |
| Écart fréquent | Acquittement S1 reçu mais pas de S17.2 : la liaison montante fonctionne mais la liaison descendante n'est pas décodée. Passer à l'étape 3 (contrôle du verrouillage de la porteuse) avant de conclure à un échec. |

**Étape 3 — Vérifier le verrouillage de la porteuse et la qualité de liaison**

Tableau 10.6 — Détail de l'étape 3 de LEOP-001 : vérification du verrouillage de la porteuse et relevés de qualité de liaison.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « TT&C, FD — report link quality. » |
| Responsable | TT&C |
| Annonce attendue du responsable | « FD, TT&C — link status 2, LOCKED, RSSI minus 102 dBm, margin 5.8 dB, nominal. » |
| Action | Lire `ttc.link_status` (0x0501), `ttc.rssi` (0x0502), `ttc.link_margin` (0x0503). Consigner le décalage Doppler mesuré à l'intention de la dynamique du vol. |
| Vérification | Dans les 30 s qui suivent l'étape 2 : `ttc.link_status` = **2** (LOCKED) ; `rssi > -110 dBm` ; `link_margin > 3.0 dB`. LOCKED vaut 2 ; 1 ne correspond pas au verrouillage, et toute vue ou fiche qui affirme le contraire est erronée. |
| Raison d'être de l'étape | La liaison peut être limite : une marge de 1 dB peut suffire aujourd'hui mais se dégrader au passage suivant. Nous consignons dès maintenant des valeurs de référence pour disposer d'un point de comparaison si la liaison se dégrade plus tard dans la mission. |
| Écart fréquent | RSSI -111 dBm, marge 2 dB : la marge satisfait au critère (gate), mais consigner une *mise en garde marge faible* dans la main courante. Le FD décide s'il faut continuer avec cette marge ou attendre le passage suivant. |

**Étape 4 — Confirmer que l'OBC est sous chargeur d'amorçage**

Tableau 10.7 — Détail de l'étape 4 de LEOP-001 : confirmation, par le SID 11, que l'OBC est toujours sous chargeur d'amorçage.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « SPACON, FD — go for beacon SID request. » |
| Responsable | SPACON |
| Annonce attendue du responsable | « FD, SPACON — go for HK request SID 11. » → exécution → « FD, SPACON — beacon received, OBC in bootloader (sw_image 0). » |
| Action | `HK_REQUEST(sid=11)` — **S3.27**. (`HK_ENABLE` correspond à S3.5 ; ni l'une ni l'autre ne correspond à S3.1 ou S3.25.) |
| Vérification | Paquet de balise reçu ; `obdh.sw_image` (**0x0311**) = 0 (BOOTLOADER) dans les 10 s. |
| Raison d'être de l'étape | Nous devons confirmer que l'OBC est bien en mode chargeur d'amorçage et non dans un état inattendu (p. ex. amorçage partiel de l'application lors d'un essai précédent). Le SID 11 est la seule structure qu'émet le chargeur d'amorçage, et il contient `obdh.sw_image` : il prouve donc à la fois que le satellite est vivant et quelle image s'exécute. Aucun SID de sous-système n'est encore émis périodiquement, ce qui est attendu et ne constitue pas une panne. |
| Écart fréquent | `sw_image = 1` déjà : l'OBC a déjà amorcé l'application. Cela signifie soit que le chargeur d'amorçage a enchaîné de lui-même (inhabituel ; une commande d'amorçage explicite est normalement nécessaire), soit que le dernier essai a laissé l'OBC sur l'application. Sauter l'étape 5 ; vérifier plutôt la télémesure de servitude complète avec la télémesure de vérification de l'étape 5. |

**Étape 5 — Amorcer l'OBC sur l'image applicative** (l'*étape critique*)

Tableau 10.8 — Détail de l'étape 5 de LEOP-001 : amorçage de l'application de l'OBC en double clé, seconde clé par le FD.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « ALL POSITIONS, FD — going for OBC application boot. SPACON, ready? » |
| | « FD, SPACON — ready. » |
| | « EPS, ready? » → « FD, EPS — ready, bus 28.4 V, SoC 89 %. » |
| | « AOCS, ready? » → « FD, AOCS — ready, no commands pending. » |
| | « TT&C, ready? » → « FD, TT&C — ready, link nominal. » |
| | « GO for OBC application boot. » |
| Responsable | SPACON (avec seconde clé du FD) |
| Annonce attendue du responsable | « FD, SPACON — first-key. FD second-key. Sending OBC_BOOT_APP. » → exécution → (pause de 10 s) « FD, SPACON — sw_image 1, application running, SIDs 1 and 11 only. Enabling 3, 4 and 6. » |
| Action | `OBC_BOOT_APP` — service S8, sous-type 1, **func_id 55**. (Aucun mécanisme ne fait désigner le sous-système par le *sous-type* S8 : le sous-type vaut 1 et c'est le func_id qui identifie la fonction.) TC de criticité élevée — double clé : le SPACON donne la première clé, le FD la seconde. Ensuite `HK_ENABLE(sid=3)`, `HK_ENABLE(sid=4)`, `HK_ENABLE(sid=6)`, toutes en **S3.5**. |
| Vérification | Dans les 5 s : acquittement S1.1. La fin d'exécution S1.7 suit la vérification CRC d'environ 10 s. Dans les 15 s : `obdh.sw_image` (0x0311) = 1 (APPLICATION). Apparaissent alors **le SID 1 (EPS) et le SID 11 (balise), et seulement ces deux-là** : l'amorçage de l'application réapplique `simulation.yaml` `default_enabled_sids: [1, 11]`, si bien que tous les autres SID sont désactivés à l'amorçage. Après les trois `HK_ENABLE`, les SID 3, 4 et 6 apparaissent en l'espace d'une période de structure (SID 3 = 60 s, SID 4 = 8 s, SID 6 = 8 s). Les SID 2 (AOCS) et 5 (charge utile) sont activés dans LEOP-007, une fois leurs lignes alimentées. |
| Raison d'être de l'étape | Jusqu'ici, l'OBC n'exécutait que le code du chargeur d'amorçage, aux fonctionnalités limitées. L'amorçage de l'image applicative lance le logiciel de mission complet, y compris la FDIR, l'ordonnanceur, le répartiteur de commandes et le collecteur de télémesure de servitude. L'OBDH vérifie le CRC de l'application sur une fenêtre de 10 s avant la transition. L'exigence de double clé tient au fait qu'un mauvais amorçage (p. ex. image corrompue) pourrait rendre l'OBC définitivement inutilisable. |
| Point de décision | Si l'acquittement S1.1 est reçu mais que S1.7 (fin d'exécution) n'arrive pas dans les 30 s, l'application n'a pas démarré. Le FD doit décider : réessayer depuis le chargeur d'amorçage, ou appliquer CTG-010 (reprise après chien de garde OBDH). Réessayer convient si l'équipe dispose de temps dans le passage ; CTG-010 est le choix le plus sûr si le temps de passage est compté. |
| Écart fréquent | Un SID activé *avant* l'amorçage reste muet ensuite. C'est l'amorçage qui réapplique `[1, 11]`, et non une panne : renvoyer `HK_ENABLE(sid=N)` après l'amorçage. Deuxième écart : l'équipe tente `TTC_SET_DATA_RATE` à ce stade et reçoit S1.8 `0x0007`. L'amorçage de l'application ne désactive **pas** le mode balise : c'est l'objet de l'étape 5a. |

**Étape 5a — Désactiver le mode balise et passer à l'échelon LOW**

Tableau 10.8a — Détail de l'étape 5a de LEOP-001 : désactivation du mode balise et passage de l'échelle de débits TM à l'échelon LOW.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « TT&C, FD — go for beacon-mode clear and LOW rung. » |
| Responsable | TT&C (le segment sol reconfigure le démodulateur) |
| Annonce attendue du responsable | « FD, TT&C — going for TTC_SET_BEACON_MODE off. » → exécution → « FD, TT&C — beacon_mode 0. Going for data rate LOW. » → exécution → « FD, TT&C — tm_tier 1, 16 000 bps, 16 kBd. Ground Seg, demod to 16 kBd. » |
| Action | `TTC_SET_BEACON_MODE(on=0)` (S8.1, **func 70**), puis `TTC_SET_DATA_RATE(rate=0)` (S8.1, **func 65**) pour LOW. Le segment sol reconfigure le démodulateur de 1 kBd à 16 kBd *avant* l'arrivée attendue des SID des sous-systèmes. |
| Vérification | `ttc.beacon_mode` (0x0521) = 0 dans les 10 s ; `ttc.tm_data_rate` (0x0506) = 16000 ; `ttc.tm_tier` (0x0539) = 1 (LOW) ; `ttc.tm_symbol_rate` (0x053B) = 16000 Bd. S1.7, et **non** S1.8. |
| Raison d'être de l'étape | Le mode balise conditionne toute l'échelle de débits : tant qu'il est verrouillé, BEACON est le seul palier autorisé et LOW comme HIGH sont refusés. Il s'agit d'une étape distincte et délibérée, car l'échelon balise est la bouée de sauvetage : le satellite ne le quitte jamais par accident. LOW transporte l'ensemble complet de la télémesure de servitude périodique en occupant moins de 10 % du canal ; l'échelon BEACON à 1 kbit/s n'y parvient pas (l'ensemble HK livré représente ~1588 bit/s de canal, soit 159 % de l'échelon balise, et l'arriéré ne fait que croître). |
| Écart fréquent | S1.8 `0x0007` sur la commande de débit. Lire l'avis d'échec, qui nomme le verrou en toutes lettres : « TM rate is forced to the beacon tier in beacon mode (LOW refused) ». Le même texte apparaît dans l'événement S5 `0x030B COMMAND_REJECTED`. Renvoyer la désactivation du mode balise. |

**Étape 6 — Synchroniser le temps bord**

Tableau 10.9 — Détail de l'étape 6 de LEOP-001 : synchronisation du temps bord et vérification de la dérive.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « SPACON, FD — go for time sync. » |
| Responsable | SPACON |
| Annonce attendue du responsable | « FD, SPACON — go for SET_TIME. » → exécution → « FD, SPACON — time set, drift 0.18 s. » |
| Action | `SET_TIME(cuc_seconds=T_corrected)` — service S9, sous-type 1 — avec l'heure UTC sol courante exprimée en secondes CUC. Laisser l'argument **à l'intérieur** des accents graves : une annotation dont l'argument est écrit à l'extérieur est extraite comme un `SET_TIME` sans argument, et la trame transmise contient `cuc_seconds = 0` — une remise à zéro de l'époque, et non une synchronisation. `SET_TIME` ne figure pas sur la liste des TC autorisées en mode amorçage ; cette commande ne fonctionne donc qu'après l'étape 5. |
| Vérification | Dans les 5 s : acquittement + fin d'exécution. Dans les 10 s : `REQUEST_TIME` (**S9.2** — `TIME_REPORT_REQUEST` n'est qu'un alias ; le nom du catalogue est `REQUEST_TIME`) renvoie TM(9,2) avec `abs(T_obc − T_ground) < 1.0 s`. |
| Raison d'être de l'étape | L'horloge de l'OBC est restée telle qu'elle était au lancement et peut être décalée de plusieurs dizaines de secondes. Une synchronisation à mieux qu'une seconde est importante car (a) les télécommandes datées S11 s'exécutent selon l'horloge de l'OBC, (b) les horodatages de la télémesure doivent concorder avec le sol pour la corrélation des journaux, (c) l'AOCS utilise le temps pour la propagation d'orbite. |
| Écart fréquent | Dérive > 1 s après le premier réglage : la latence aller-retour sol-bord (typiquement 200 à 500 ms) n'a pas été compensée. Renvoyer avec une avance de compensation (le FD saura s'il faut l'autoriser ; en général, il suffit de renvoyer la commande 10 s plus tard). |

**Étape 7 — Demander la télémesure de servitude de l'EPS (contrôle de vraisemblance de l'alimentation)**

Tableau 10.10 — Détail de l'étape 7 de LEOP-001 : demande de télémesure de servitude de l'EPS et contrôle de vraisemblance de l'alimentation.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « SPACON, FD — go for EPS HK. » → « EPS, prepare to read. » |
| Responsable | Le SPACON demande ; l'EPS lit |
| Annonce attendue du responsable | SPACON : « FD, SPACON — HK SID 1 received. » → EPS : « FD, EPS — bus 28.2 V, SoC 89 %, all switchable lines off, draws nominal. » |
| Action | `HK_REQUEST(sid=1)` — S3.27. |
| Vérification | `eps.bus_voltage` (0x0105) ∈ [26.0, 30.0] V ; `eps.bat_soc` (0x0101) > 50 % ; `eps.power_gen` (0x0107) transmis — la valeur sera faible, car le satellite est en culbutage et non pointé vers le Soleil, et les ailes sont encore repliées. |
| Raison d'être de l'étape | L'état de l'EPS détermine si nous pouvons enchaîner sur la mise sous tension séquentielle de LEOP-007. Si le SoC est trop bas (< 50 %), nous sommes en situation de survie énergétique : délester d'abord, reporter la recette en orbite, reconstituer le SoC au cours des orbites suivantes. |

**Étape 8 — Consigner et rendre compte**

Tableau 10.11 — Détail de l'étape 8 de LEOP-001 : consignation des valeurs de référence et compte rendu de fin.

| Élément | Détail |
|---------|--------|
| Sollicitation du FD | « All positions, FD — LEOP-001 complete, recording log entries. » |
| Responsable | Chaque poste consigne dans sa main courante |
| Éléments consignés | Heure de l'AOS, heure d'armement du forçage, heure de la première TC acceptée (S17 de l'étape 2), heure de l'amorçage de l'application, résidu de synchronisation temporelle, valeurs du contrôle de vraisemblance de l'EPS, marge de liaison de référence. |
| Raison d'être de l'étape | L'archive de la promotion a besoin de ces heures pour les comparer aux exécutions des promotions suivantes. La marge de liaison de référence sert de base à l'évaluation de la marge lors de chaque passage ultérieur. |

#### Écarts fréquents et conduite du FD

Tableau 10.12 — Écarts fréquents de LEOP-001, leur signification et l'action de reprise du FD.

| Écart | Signification | Action du FD |
|-----------|---------------|-----------|
| `pass_override` non engagé avant l'étape 2 | La TC sera rejetée (pas de poursuite de porteuse) | Arrêter ; engager le forçage ; renvoyer S17 |
| Acquittement S1 reçu mais rejet de commande 0x0004 | TC envoyée au chargeur d'amorçage alors qu'elle ne figure pas sur la liste des TC autorisées en mode amorçage | Identifier la TC ; si elle est antérieure à OBC_BOOT_APP, la reporter après l'étape 5 |
| Aucune balise reçue à l'étape 4 | Le satellite est dans un état où l'émission du SID 11 est désactivée (rare ; généralement un problème lié à la séparation) | Suspendre la procédure ; vérifier que le satellite se trouve effectivement dans la géométrie prévue (appeler le FDS) ; si c'est le cas, passer à EMG-004 (perte de communication) |
| `obdh.sw_image` ne change pas après OBC_BOOT_APP | Le compte à rebours de vérification du CRC à l'amorçage dure 10 s | Attendre 30 s, redemander le SID 11 (qui contient `sw_image`) ; s'il vaut toujours 0, le CRC de l'application est en échec : faire remonter à l'ingénieur OBDH et envisager `OBC_BOOT_INHIBIT(0)` puis `OBC_REBOOT` |
| OBC_BOOT_APP renvoie l'acquittement S1.1 mais pas S1.7 dans les 30 s | L'application n'a pas démarré | Attendre 60 s ; toujours pas de S1.7 : appliquer CTG-010 (reprise après chien de garde OBDH) |
| `SET_TIME` rejetée avec 0x0006 | La transition d'amorçage de l'application n'est pas terminée (concurrence avec la fenêtre CRC de 10 s) | Attendre 5 s et réessayer |
| Dérive de synchronisation > 5 s après le premier SET_TIME | Référence de temps sol erronée, ou quartz de l'horloge bord endommagé | Vérifier la référence sol ; si elle est confirmée correcte, consigner une anomalie et continuer (une forte dérive se corrige plus tard) |
| SID 3, 4 ou 6 muets après l'amorçage | Les `HK_ENABLE` ont été envoyées avant l'amorçage, et l'amorçage a réappliqué `default_enabled_sids: [1, 11]` | Renvoyer `HK_ENABLE(sid=N)` (S3.5) pour chaque SID manquant *après* l'amorçage |
| La liaison descendante se tait ~5 minutes après la dernière TC | La temporisation de maintien de l'auto-TX a expiré | Envoyer n'importe quelle TC ; son acceptation réarme la temporisation de 300 s et réalimente `ttc_tx` |

#### Points de décision à simuler

1. **À l'étape 5, l'EPS annonce un SoC de 38 % (sous le seuil de 50 %).**
   Le FD doit décider : amorcer quand même l'application (on obtient la télémesure de servitude complète, mais
   on perd la marge d'avant l'amorçage), ou suspendre et laisser le SoC se reconstituer pendant
   l'orbite suivante. De vraies équipes LEOP ont fait l'un et l'autre choix ; tous deux se
   défendent.

2. **À l'étape 5, le FD donne le GO, mais le TT&C signale que la marge de liaison
   est tombée à 1,5 dB pendant l'attente de l'amorçage.** La mise sous tension de l'émetteur,
   armée automatiquement à l'étape 2, a pu faire chauffer l'amplificateur
   et dégrader la liaison. Le FD doit décider : continuer avec une liaison
   limite, ou suspendre et laisser refroidir l'amplificateur. Continuer est le choix
   habituel (la marge reste positive) ; la suspension se justifie si la marge
   a chuté *rapidement* (signe d'une dégradation réelle).

3. **À l'étape 6, le résidu de synchronisation temporelle reste supérieur à 1 s après
   trois tentatives.** Le FD doit décider : accepter le résidu (le consigner comme
   anomalie, prévoir une investigation au quart suivant), ou appliquer la procédure de reprise
   de la synchronisation temporelle. Le seuil de 1 s est prudent ; jusqu'à 5 s, l'écart est
   tolérable pour la plupart des activités de la mission. Accepter le résidu
   et continuer est généralement la bonne décision.

#### Pistes de débriefing (après le passage)

Pour l'équipe d'opérateurs :

- Quel a été votre délai entre l'AOS et la première TC acceptée ? (Référence
  de l'industrie : < 30 s.)
- Quel a été votre délai entre l'AOS et l'exécution de l'application de l'OBC ?
  (Référence de l'industrie : < 4 min pour un passage sans incident.)
- Y a-t-il eu un GO qui, avec le recul, aurait dû être un
  HOLD ?
- Y a-t-il eu un HOLD que, avec le recul, vous auriez dû
  franchir ?
- Quelles valeurs de référence avez-vous consignées ? Figurent-elles toutes dans votre main
  courante ?

Pour l'équipe d'observation :

- La discipline de boucle vocale a-t-elle été rigoureuse pendant le tour de table
  d'autorisation d'OBC_BOOT_APP ?
- Le FD a-t-il obtenu un « ready » explicite de chaque poste interrogé ?
- Le FD a-t-il correctement donné la seconde clé pour la TC de criticité élevée après la première clé
  du SPACON ?
- La période d'attente après l'amorçage a-t-elle été silencieuse (bien : opérateurs
  en surveillance) ou bavarde (mal : attention dispersée) ?

---

### LEOP-007 — Mise sous tension séquentielle (déroulé approfondi)

LEOP-007 n'alimente que ce dont le reste de la LEOP a besoin, et rien de
plus. Ses six étapes tiennent dans un contact de 8 minutes ; l'attente de
l'amortissement qui suit relève de la physique et non de la charge de
travail, et elle appartient à LEOP-005. La procédure fait passer le
satellite de « ailes déployées, toutes les lignes commutables OFF sauf
`ttc_tx`, AOCS sur OFF » à « AOCS en DETUMBLE sur le magnétomètre et les
magnétocoupleurs, GPS en acquisition ». Chaque mise sous tension de ligne
est une petite cérémonie : GO du FD, premier verrou du responsable,
vérification par le SPACON, entrée au journal, ligne suivante.

#### Préparation préalable

LEOP-007 commence après LEOP-004 (vérification du générateur solaire).
L'équipe dispose de :

- Logiciel applicatif en service (`obdh.sw_image` 0x0311 = 1), mode balise
  levé, liaison descendante sur l'échelon LOW, SID de HK 1, 3, 4, 6 et 11
  en flux.
- Deux ailes déployées et productrices (`eps.wing_status` 0x0144 = 0x03).
- SoC de l'EPS > 60 % et bus à 26–30 V (l'étape 1 vérifie les deux). Les
  ajouts sont modestes : +~6 W pour `htr_bat` et +~3 W pour `htr_obc` si
  leurs zones ont besoin de chaleur, et +~12 W pour la suite AOCS.
- Une horloge toujours non réglée : la synchronisation temporelle est
  LEOP-006, après cette fiche.
- Aucune table FDIR à charger : toutes les règles sont armées en
  permanence, et les définitions événement-action sont inhibées une à une
  avec `EA_DISABLE` (S19.5) et rétablies avec `EA_ENABLE` (S19.4).

#### Guide étape par étape (six étapes)

Pour chaque mise sous tension de ligne, le schéma est le suivant :

1. L'EPS recommande au FD : *« FD, EPS — recommend enable htr_bat. »*
2. Le FD interroge : *« SPACON, AOCS, Thermal — go for htr_bat enable? »*
3. Chacun répond : *« FD, [POSITION] — go. »*
4. Le FD : *« Go for htr_bat enable. »*
5. L'EPS actionne le premier verrou (pas de second verrou pour les mises sous tension de routine).
6. L'EPS annonce le courant : *« FD, EPS — htr_bat 0.35 A, nominal. »*
7. Le SPACON vérifie et consigne : *« FD, SPACON — htr_bat verified, log entry. »*

Le tableau complet :

Tableau 10.13 — Mise sous tension séquentielle de LEOP-007 en six étapes, avec responsables, préconditions et points de vigilance.

| N° | Responsable | Action | Précondition | Comportement attendu | Points de vigilance |
|---|-------|--------|---------------|---------------------|-----------|
| 1 | EPS | Vérifier l'état de référence de l'EPS : `HK_REQUEST(sid=1)` (S3.27) | logiciel applicatif en service, ailes déployées | `eps.bus_voltage` (0x0105) 26–30 V ; `eps.bat_soc` (0x0101) > 60 % ; `eps.power_gen` (0x0107) > 0 W | SoC sous 60 % — attendre, ne pas lancer la séquence |
| 2 | EPS + Thermique | Lignes de réchauffeurs **selon le besoin** : `EPS_POWER_ON(line_index=5)` (S8.1, **func 19**) seulement si `tcs.temp_battery` (0x0407) < +5 °C ; `EPS_POWER_ON(line_index=6)` seulement si `tcs.temp_obc` (0x0406) < 0 °C | bus stable, SoC > 60 % | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 en 5 s pour chaque ligne alimentée ; +~6 W / +~3 W | alimenter un réchauffeur dont la zone n'a pas besoin ; courant élevé durable (court-circuit du réchauffeur) |
| 3 | EPS → AOCS | Alimenter la ligne de la suite AOCS et activer sa HK : `EPS_POWER_ON(line_index=7)`, puis `HK_ENABLE(sid=2)` (**S3.5**) | étape 2 faite | `eps.pl_aocs_wheels` (0x0117) = 1 ; SID 2 émis en moins d'un intervalle ; +~12 W | s'attendre à voir les roues démarrer — la ligne alimente la suite, et `aocs.wheels_enabled` (0x0260) reste à 0 jusqu'à COM-004 ; SID 2 muet — alimenter la ligne n'active **pas** le SID |
| 4 | AOCS | Activer les éléments de DETUMBLE et le récepteur GPS : `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` ; `MTQ_ENABLE(enable=1)` (S8.1, **func 9**) ; `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | SID 2 émis | `aocs.mtq_enabled` (0x025E) = 1 en 10 s ; le délai d'acquisition du premier point GPS commence | commander DETUMBLE d'abord — refus avec `0x0A20` (pas de magnétomètre) ou `0x0A21` (pas de magnétocoupleurs) |
| 5 | AOCS | Commander DETUMBLE : `AOCS_SET_MODE(mode=2)` (S8.1, **func 0**) | deux éléments activés | `aocs.mode` (0x020F) = 2 en 10 s ; `aocs.mag_enabled` (0x025C) = 1 ; `aocs.mag_field_total` (0x0277) 5–70 µT ; vitesses (0x0204–0x0206) en baisse en 60 s | refus avec `0x0004` — l'écriture de la ligne n'a pas pris ; champ nul — le magnétomètre est éteint et la loi B-dot est aveugle |
| 6 | EPS | Confirmer l'état d'alimentation de sortie : `HK_REQUEST(sid=1)` | DETUMBLE actif | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) et `aocs.wheels_enabled` (0x0260) tous à 0 ; marge de puissance positive | toute mise sous tension prématurée — la ligne charge utile relève de COM-009, celle du refroidisseur de COM-010 |

Après l'étape 6, l'AOCS amortit. LEOP-005 observe le passage automatique
en COARSE_SUN et LEOP-003 déclare la phase 5 : rien dans LEOP-007 ne
commande le mode 3 ni la phase.

#### Pourquoi l'amortissement est si long

L'étape 5 fait passer le satellite en DETUMBLE, et l'attente qui suit est la
partie de la LEOP que les équipes évaluent systématiquement mal ; il vaut donc la peine d'être
précis sur la physique.

DETUMBLE est une véritable loi **B-dot** pilotée par le magnétomètre, et non par les
gyroscopes : la commande de bord dérive le vecteur champ *mesuré* et
commande un dipôle magnétique

$$ \mathbf{m} = -k\,\dot{\mathbf{B}}, \qquad k = 5\times10^{5}\ \mathrm{A\,m^2/(T\,s^{-1})} $$

chacun des trois barreaux saturant à **1,6 A·m²**. Comme
$\dot{\mathbf{B}}_{body} = -\boldsymbol{\omega}\times\mathbf{B}$, le couple
vaut

$$ \boldsymbol{\tau} = \mathbf{m}\times\mathbf{B} = -k\,|\mathbf{B}|^{2}\,\boldsymbol{\omega}_{\perp} $$

— un pur amortisseur de vitesse, qui n'a besoin ni de connaissance de l'attitude ni de gyromètre.
Il en découle deux conséquences, toutes deux visibles dans l'onglet AOCS :

1. **Seule la composante de $\boldsymbol{\omega}$ perpendiculaire à
   $\mathbf{B}$ est amortie à chaque instant.** La direction du champ balaie
   le repère satellite au fil du culbutage et du déplacement du satellite
   dans le champ le long de l'orbite, de sorte que l'énergie passe réellement **d'un axe à l'autre** pendant que la
   norme totale diminue. Mesurée à partir de (1,0 ; 0,8 ; 0,5) °/s, `rate_roll` est *en hausse*, à
   1,05 °/s, à t = 50 s, alors que la norme est déjà passée de 1,37
   à 1,28 °/s. Un axe isolé en hausse ne signifie pas une loi de commande défaillante. Jugez
   la convergence sur la RSS des trois vitesses.
2. **Elle est lente.** La constante de temps sur la vitesse vaut
   $\tau = I/(k|\mathbf{B}|^{2}) = 0.18/(5\times10^{5}\cdot(3\times10^{-5})^{2}) \approx 400$ s,
   et les barreaux saturent au-delà d'environ 1 °/s, si bien que la convergence prend de l'ordre de
   $10^{3}$ s, et non quelques dizaines de secondes. Mesures sur ce modèle à partir de
   $|\omega_0| = 1.37$ °/s : 1,13 °/s à 100 s, 0,95 à 200 s, 0,63 à 600 s,
   0,55 à 900 s, et **passage sous le seuil de sortie de 0.5 °/s à t = 1166 s**, soit environ
   20 minutes. À partir d'un culbutage de séparation à 14 °/s, il faut **~3,5 × 10³ s**
   (le balayage de gain dans `subsystems/aocs.yaml`, exécuté avec un pas de 1 s, relève
   4322 s jusqu'au même seuil, soit environ les trois quarts d'une orbite).

Conclusion : toute affirmation selon laquelle l'amortissement serait l'affaire de quelques minutes est fausse. La mention
de la fiche elle-même, « < 0.5 °/s within 5–15 min », est optimiste pour tout culbutage autre que le plus
faible ; prévoyez une part substantielle d'une orbite, et attendez-vous à ce que la transition
de mode DETUMBLE → COARSE_SUN se fasse d'elle-même, trente secondes
après que la norme de la vitesse angulaire est restée pour la première fois sous le seuil.

Notez aussi ce que le mode n'utilise *pas*. La loi B-dot repose uniquement sur le magnétomètre :
éteindre le magnétomètre arrête net l'amortissement alors que tous les gyroscopes
fournissent toujours des mesures parfaites. C'est cela, et non une panne de gyroscope, la véritable signature
de défaillance de DETUMBLE. Augmenter le gain n'aide pas : le balayage montre que
$k = 1.5\times10^{6}$ est *pire* (4914 s), car un gain plus élevé amplifie
le bruit du magnétomètre dérivé plus vite qu'il n'ajoute d'amortissement, et
$k = 4\times10^{6}$ ne converge pas du tout.

#### Points de décision à simuler

1. **L'appel de courant de l'étape 2 est de 1,2 A (environ 3,4 fois les
   0,35 A nominaux)** sur une ligne de réchauffeur dont la zone batterie
   froide avait besoin. Il peut s'agir d'un vrai défaut du sous-système ou
   d'un appel de courant au démarrage à froid. L'EPS recommande d'attendre
   60 s pour observer la tendance ; le FD doit décider. Si le courant
   revient au nominal en 30 s, poursuivre ; s'il reste élevé, appliquer
   CTG-012 (réponse à une surintensité).

2. **Étape 5 : `AOCS_SET_MODE(mode=2)` est refusée.** Lire le code d'échec
   avant toute chose. `0x0004` signifie que l'écriture de la ligne de la
   suite AOCS n'a pas pris — renvoyer `EPS_POWER_ON(line_index=7)` et
   vérifier `eps.pl_aocs_wheels` (0x0117). `0x0A20` signifie pas de
   magnétomètre et `0x0A21` pas de magnétocoupleurs : l'étape 4 n'a pas
   pris. Renvoyer la commande de mode à l'identique sera de nouveau refusé
   pour la même raison. Il n'existe pas de magnétomètre redondant. Les
   roues n'ont rien à voir ici : elles sont encore désactivées, et
   l'amortissement se fait entièrement avec les magnétocoupleurs.

3. **Après l'étape 5 (LEOP-005) : les vitesses plafonnent à 0,6 °/s et ne
   baissent plus.** Deux interprétations : la loi converge mais la
   géométrie est momentanément défavorable (la vitesse est presque
   parallèle à **B**, il reste donc peu de composante perpendiculaire à
   amortir) ; ou le magnétomètre a été perdu et la loi B-dot ne commande
   plus rien. Les distinguer : lire `aocs.mtq_x/y/z_duty` (0x0258–0x025A)
   et `aocs.mtq_enabled` (0x025E). Des rapports cycliques non nuls avec une
   vitesse bloquée relèvent de la géométrie — attendre quelques minutes
   que le champ tourne. Des rapports cycliques nuls signalent un vrai
   défaut.

4. **Après l'étape 6 : pas encore de point GPS.** Un démarrage à froid
   prend jusqu'à 15 minutes depuis la mise sous tension de l'étape 4. Rien
   dans LEOP-007 ne l'attend : LEOP-006 règle d'abord l'horloge depuis le
   sol et ne l'asservit au GPS qu'une fois le point acquis, et LEOP-003 se
   replie sur la distance et le Doppler mesurés au sol s'il n'y a toujours
   pas de point après 30 minutes. La question n'est pas d'attendre ou non,
   mais de savoir si quelqu'un a commencé à traiter l'absence de point
   comme une raison de suspendre.

#### Écarts fréquents

Tableau 10.14 — Écarts fréquents de LEOP-007, avec causes premières probables et actions de reprise.

| Écart | Cause première probable | Reprise |
|-----------|-------------------|----------|
| Étape 2 nominale, consommation à l'étape 3 durablement supérieure aux attentes | Variation du courant du générateur solaire masquant l'échelon propre à la ligne | Attendre 30 s sur la partie éclairée de l'orbite ; l'EPS comptabilise d'après l'état réel des actionneurs : comparer donc au courant de la ligne, et non au total du bus |
| Le SID 2 n'apparaît jamais après la mise sous tension de la ligne `aocs_wheels` | `HK_ENABLE(sid=2)` n'a jamais été envoyée — alimenter une ligne n'active pas son SID | Envoyer `HK_ENABLE(sid=2)` (S3.5) ; le SID 2 apparaît en moins d'un intervalle |
| `AOCS_SET_MODE` refusée avec 0x0004 après la mise sous tension | L'écriture de la ligne EPS n'a pas pris | Renvoyer `EPS_POWER_ON(line_index=7)`, vérifier `eps.pl_aocs_wheels` (0x0117) = 1, puis réessayer la commande de mode |
| `AOCS_SET_MODE` refusée avec 0x0A20 ou 0x0A21 | L'élément magnétomètre ou magnétocoupleurs de l'étape 4 n'a pas pris | Renvoyer `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` ou `MTQ_ENABLE(enable=1)`, puis réessayer |
| La vitesse sur un axe *augmente* pendant l'amortissement | Attendu — la loi B-dot n'amortit que la composante perpendiculaire, l'énergie passe donc d'un axe à l'autre | Rien. Juger la RSS, pas l'axe |
| Les vitesses augmentent sur tous les axes | Polarité des magnétocoupleurs inversée | Commander immédiatement `AOCS_SET_MODE(mode=0)` (OFF) et investiguer avant de revenir en DETUMBLE |
| L'amortissement ne progresse pas du tout et les rapports cycliques des barreaux sont nuls | Magnétomètre perdu — la loi B-dot ne repose que sur le magnétomètre | Redémarrer le magnétomètre (unité unique, pas de rechange vers laquelle basculer) ; la bonne santé des gyroscopes n'apprend rien ici |

#### Pistes de débriefing

- Durée totale de *commande* de LEOP-007 (elle tient dans un contact de
  8 minutes), indiquée séparément de l'attente de l'amortissement, qui
  relève de la physique et que l'équipe ne peut pas accélérer.
- Tous les GO du FD ont-ils été explicitement demandés, ou certains
  ont-ils été accordés au passage, d'un simple *« allez-y »* ?
- Toutes les consommations étaient-elles dans l'enveloppe attendue à la
  première lecture ?
- Quelqu'un a-t-il commandé COARSE_SUN au lieu de l'attendre, ou
  interprété la hausse de la vitesse sur un seul axe comme une défaillance
  de la loi de commande ?

---

### LEOP-006 — Synchronisation temporelle (l'étape que tout le monde rate)

LEOP-006 est courte, et ses étapes sont pour l'essentiel mécaniques : vérifier que l'OBC
répond (étape 1), lire l'horloge (étape 2), calculer le décalage (étape 3),
envoyer `SET_TIME` (étape 4), vérifier le résidu (étape 5), confirmer la dérive
(étape 6), consigner (étape 7). C'est l'étape 2 qui mérite une lecture attentive car,
jusqu'à sa réécriture, elle rendait le `delta_t` de l'étape 3 *impossible à obtenir*, et non
simplement imprécis. Elle comportait trois erreurs, et toutes trois sont
du type d'erreur à traquer partout ailleurs dans ce manuel :

1. **Elle citait un alias.** La fiche indiquait `TIME_REPORT_REQUEST`. La
   commande du catalogue est **`REQUEST_TIME`** (S9.2). L'alias est résolu au
   niveau de la transmission, si bien que la commande fonctionne ; mais un opérateur qui cherche
   la mnémonique de la fiche dans le panneau de commande ne la trouve pas.
2. **Elle demandait un paramètre sans demander la structure qui le
   transporte.** L'étape invitait l'opérateur à lire `ttc.range_km`
   (0x0509) mais ne demandait jamais que le SID 4. Or 0x0509 se trouve dans le **SID HK 6** ;
   la distance nécessaire au temps de propagation aller n'arrivait donc jamais.
3. **Sa valeur d'OWLT était fausse d'un facteur trois.** `ttc.range_km` est
   la distance oblique *géométrique* et elle est publiée qu'une station
   soit en visibilité ou non : pour l'orbite de référence d'EOSAT-1, elle vaut environ 6530 km
   hors contact et 1000–2100 km pendant un passage, soit **3–22 ms**, et non
   « 2–8 ms ». Cela reste négligeable devant le seuil LEOP de 1.0 s,
   ce qui explique précisément pourquoi on la consigne avant de passer à la suite. Une fiche qui cite une
   valeur que le satellite ne produit jamais apprend à l'opérateur à ne pas vérifier.

L'étape 2 livrée demande donc trois éléments ensemble :

- `REQUEST_TIME` (S9.2) : la réponse est une TM(9,2), reçue dans les 10 s ;
  consigner la valeur CUC rapportée comme `T_obc` et l'heure UTC sol au moment
  de la réception comme `T_ground` ;
- `HK_REQUEST(sid=6)` (S3.27) : télémesure de servitude TT&C, **pour la distance
  oblique**. Calculer
  `OWLT_ms = ttc.range_km (0x0509) / 299792.458 × 1000` ; on attend 3–22 ms ;
- `HK_REQUEST(sid=4)` (S3.27) : télémesure de servitude plateforme, **pour le recoupement
  de l'horloge**. L'horloge de l'OBC est également transmise en continu sous la forme de
  `obdh.obc_time` (0x0309). La valeur de la TM(9,2) et 0x0309 doivent concorder
  à la période d'échantillonnage du SID 4 près (8 s). Elles arrivent par des voies
  différentes — l'une par un rapport de temps explicite, l'autre par un échantillon de télémesure de servitude —
  de sorte qu'un désaccord signifie que le service de temps et l'échantillonneur de télémesure de servitude
  ne s'accordent pas sur l'horloge, ce qui est une panne *différente* d'une horloge
  erronée.

Le critère GO de l'étape 2 réunit les trois conditions : une TM(9,2) valide avec une valeur
CUC plausible, la distance oblique consignée, et 0x0309 en accord.

Deux autres points de cette fiche valent pour la suite. Premièrement, `SET_TIME` à l'étape 4
doit être écrite avec son argument **à l'intérieur** des accents graves :
`SET_TIME(cuc_seconds=T_corrected)`. Écrit à l'extérieur, l'extracteur
produit une étape `SET_TIME` sans argument et la trame transmise contient
`cuc_seconds = 0` : une remise à zéro de l'époque, et non une synchronisation. Deuxièmement, le seuil
d'acceptation LEOP est de 1.0 s et le seuil de dérive de 100 ppm ; la
synchronisation fine à mieux que 0,1 s relève de l'exploitation nominale et appartient
à **NOM-008** (`nominal/clock_sync.md`). NOM-006 correspond au chargement de logiciel.

## 10.12 Références

- ECSS-E-ST-70-11C — *Space segment operability* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/)

# Chapitre 11 — Opérations de recette en orbite

****

Ce chapitre couvre les opérations depuis la fin de la LEOP jusqu'à la
**première lumière** — le moment où la charge utile a été mise sous
tension, étalonnée et a acquis une image de qualité scientifique d'une
cible. Il s'agit de la phase 5 (COMMISSIONING) du tableau des phases de
mission (§5.7).

Dans un planning opérationnel type, la recette en orbite s'étend sur
environ 4 passages au-dessus des stations sol, avec un travail
important entre les passages (stabilisation thermique du plan focal,
traitement de l'étalonnage des capteurs, planification de la géométrie
de la première lumière).

## 11.1 Conditions d'entrée dans la phase de recette en orbite

- **Point de reprise de la simulation :** BP-3 *Commissioning Day Start*
  (`scenarios/commissioning_day_start.yaml` — NOUVEAU ; spécification au §5.10).
- **Phase au départ :** 4 (LEOP). La phase 5 est COMMISSIONING.
- **Visibilité initiale :** Iqaluit, AOS à T+0 du scénario.
- **Passages prévus pendant le quart :** 4. Le référentiel pédagogique
  est le **réseau complet de cinq stations** (Iqaluit, Troll, Svalbard,
  Inuvik, O'Higgins) : les quatre passages du quart sont donc choisis
  dans un réseau qui offre environ 51 passages par jour, avec un écart
  médian de 33 min.
- **Facteur d'accélération :** fixé par le directeur de mission.
- **Le changement de phase est une déclaration du sol.** L'équipe de
  direction de mission déclare la phase du satellite avec `SYS_SET_MISSION_PHASE`
  (S8 fonction 120). Rien à bord ne la fait avancer au-delà de 4 (LEOP) : l'étape
  de procédure qui l'envoie ne doit donc pas être sautée.

## 11.3 Point sur la phase de mission

Le satellite vient de sortir de la LEOP. Antennes déployées ; logiciel
applicatif en fonctionnement ; amortissement terminé (vitesses
angulaires < 0,05°/s) ; temps synchronisé ; FDIR en configuration
réservée à la LEOP. La charge utile est sur OFF ; le plan focal (FPA)
est à son équilibre non refroidi (+8 à +14 °C). Batterie à 90 % de
SoC. L'objectif du quart est la **première lumière** — une image
acquise et transmise au sol — avant la fin du passage 4.

## 11.4 Ordre d'exécution des procédures sur 4 passages

Treize fiches de recette en orbite sont fournies, de COM-001 à COM-013.
La séquence de quatre passages ci-dessous en exécute onze ; COM-013
(recette complète du SCAO) est une reprise consolidée utilisée lors des
séances de rattrapage et ne figure pas dans la chronologie nominale.

Tableau 11.1 — Exécution des procédures de recette en orbite sur quatre passages, avec l'activité critique de chaque passage.

| Passage | Procédures | Activité critique |
|---|---|---|
| 1 | COM-001 Vérification de l'EPS ; COM-002 Vérification du TCS ; COM-004 Vérification des actionneurs SCAO ; COM-003 Étalonnage des capteurs SCAO | Les quatre roues sont activées et le satellite atteint pour la première fois le NOMINAL piloté par les roues (mode 4) ; chaque roue est polarisée dans les deux sens puis ramenée à zéro ; le biais gyroscopique est ensuite étalonné à bord dans ce NOMINAL |
| 2 | COM-005 Transitions de modes SCAO ; COM-006 Vérification de la liaison TTC ; COM-007 Vérification de l'OBDH ; COM-008 Configuration de la FDIR | L'échelle des modes AOCS est parcourue jusqu'à FINE_POINT ; les deux échelons de l'échelle de débits TM sont caractérisés ; la pile de protection (S12, S19, verrouillage du délestage) est inventoriée et testée |
| 3 | COM-009 Mise sous tension de la charge utile ; COM-010 Activation du refroidisseur du FPA | Démarrage du refroidisseur — un cryoréfrigérateur de type Stirling de 15 W fait passer le FPA d'environ +11 °C à la consigne de −15 °C en une dizaine de minutes |
| 4 | COM-011 Étalonnage de la charge utile ; COM-012 Première lumière | Séries d'obscurité et de champ plat acquises en mode CALIBRATION (3), puis une image d'une cible de courant océanique capturée et transmise au sol |

État visé en fin de quart : phase 5 ou ultérieure (recette en orbite
terminée ou reportée) — déclarée par l'équipe de direction de mission —,
charge utile étalonnée, une image exploitable acquise (ou report
formel justifié).

## 11.5 Conduite à tenir par poste pendant la recette en orbite

### Directeur de vol

- Avant le quart : présenter à l'équipe la séquence des quatre
  passages. Confirmer les critères de réussite de chaque passage.
- Au fil des passages : faire respecter la règle *une procédure à la
  fois*. Autoriser l'enchaînement COM-001 → -002 → -003 → -004 au
  passage 1 et COM-005 → -006 → -007 → -008 au passage 2.
- Le passage 3 est le pivot : mise sous tension de la charge utile et
  démarrage du refroidisseur. Autoriser avec prudence : avec 15 W, le
  refroidisseur du FPA est la plus grosse charge électrique du
  satellite — plus que l'émetteur sur son palier HIGH (11 W) — et
  l'EPS doit être prêt.
- Le passage 4 est le point d'engagement. Si le pointage est incertain
  ou si la mémoire est presque pleine, autoriser un *report formel*
  plutôt que de prendre l'image coûte que coûte.
- Écueils : déborder sur le COM-005 du passage 2 (les transitions de
  modes prennent du temps à vérifier) ; arriver au passage 3 encore au
  milieu du COM-008.

### SPACON

- Avant le quart : charger les 13 procédures de recette en orbite dans
  l'index des procédures. Être prêt à changer rapidement de procédure
  active.
- Au fil des passages : suivre quels sous-systèmes sont désormais
  « recettés » et lesquels sont « en attente ». Dès que le COM-008
  charge la table FDIR nominale, plusieurs nouvelles surveillances
  s'arment et se déclenchent si les sous-systèmes concernés ne sont
  pas réellement nominaux.
- Écueils : oublier d'acquitter une règle FDIR alors que l'étape
  suivante de la procédure exige que le paramètre soit repassé au vert
  (la règle s'efface parfois d'elle-même ; parfois elle doit être
  acquittée).

### AOCS

- Pilote au passage 1 : COM-004 Vérification des actionneurs. Chacune
  des quatre roues est polarisée avec `RW_SET_SPEED_BIAS` puis ramenée
  à zéro avec `AOCS_RW_RAMP_DOWN`. Les vitesses de roue (0x0207–0x020A)
  sont des télémesures en lecture seule ; il n'existe aucun chemin
  `SET_PARAM` vers une vitesse de roue.
- Pilote au passage 2 : COM-005, transitions de modes NOMINAL (4) →
  FINE_POINT (5) → NOMINAL (4), INERTIAL (9) et retour, maintien
  COARSE_SUN (3) et DESAT (7). Chaque transition commandée fait l'objet
  d'une TC distincte et d'une vérification distincte ; les retours
  automatiques s'observent, ils ne se commandent pas.
- En appui au passage 4 : la prise de vue exige FINE_POINT ; l'AOCS
  envoie `AOCS_SET_MODE(mode=5)` après que
  `AOCS_FINE_READY_CHECK` a lu `aocs.fine_ready` (0x02C5) = 0.
- Écueils : ne pas vérifier que le widget d'erreur de pointage se
  stabilise après une transition de mode (la transition est rapide ; la
  *stabilisation* prend 30 à 60 s, et `aocs.settle_time_s` 0x02C4
  l'indique).

### EPS

- Pilote au passage 1 : le COM-001 Vérification de l'EPS établit les
  valeurs de référence du bus, de la batterie et de la production. La
  matrice des lignes d'alimentation compte **neuf** lignes, d'indices
  0 à 8 (`obc`, `ttc_rx`, `ttc_tx`, `payload`, `fpa_cooler`,
  `htr_bat`, `htr_obc`, `aocs_wheels`, `prop`) ; les lignes 0 et 1 ne
  sont pas commutables et toutes les lignes commutables sont sur OFF
  par défaut.
- Critique au passage 3 : mise sous tension de la charge utile (2,4 W
  en STANDBY) plus démarrage du refroidisseur (15 W). Dans cette
  configuration, la charge totale du satellite atteint environ 39 W,
  pour une production en phase éclairée d'environ 54–71 W selon
  l'angle bêta. Lancer l'opération dans la partie éclairée de l'orbite.
- Écueils : ne pas remarquer que le SoC de la batterie baisse plus vite
  que ne le prévoyait le modèle d'éclipse (signe d'une fuite de courant
  ou d'un générateur solaire moins performant que prévu).

### Thermique

- Pilote au passage 1 : COM-002 Vérification du TCS — les circuits de
  réchauffeurs sont sollicités un par un et leurs consignes de
  thermostat relues dans `tcs.setpoint_bat` (0x0330) et
  `tcs.setpoint_obc` (0x0331) ; les rapports cycliques sont consignés à
  partir de `tcs.htr_duty_battery` (0x040E) et `tcs.htr_duty_obc`
  (0x040F).
- Critique au passage 3 : mise en route du refroidisseur du FPA. La
  mise en froid est rapide : depuis l'équilibre non refroidi (environ
  +11 °C), le détecteur entre dans la bande de consigne de −15 °C en
  une dizaine de minutes, avec une vitesse initiale d'environ 4 °C/min
  qui décroît exponentiellement. Le refroidisseur est un
  **cryoréfrigérateur Stirling miniature** fonctionnant à environ 23 %
  du rendement de Carnot, et non un empilement Peltier ; il régule sur
  la consigne — il ne descend jamais en dessous.
- Écueils : ne pas remarquer que le rapport cyclique d'un réchauffeur
  est *anormalement bas* — la zone reçoit peut-être de la chaleur d'une
  source inattendue (p. ex. une alimentation intempestive de la charge
  utile).

### TT&C

- Pilote au passage 2 : COM-006 Vérification de la liaison TTC.
  Configure la chaîne en bande S (ligne, amplificateur de puissance,
  sortie du mode balise, déploiement d'antenne), puis établit la marge
  de référence sur les deux échelons opérationnels de l'échelle de
  débits, LOW (16 kbit/s) et HIGH (128 kbit/s).
- Critique au passage 4 : transmettre au sol l'image de la première
  lumière. Un produit de 4 Mio occupe 262 s de canal en HIGH, 328 s
  avec la provision protocolaire de 20 % du planificateur — environ
  les trois quarts d'un passage moyen.
- Écueils : ne pas passer au palier HIGH avant la mise en file de
  l'image ; la transmission prend alors plus d'un passage entier en LOW
  et est interrompue par la LOS. Noter que le palier HIGH est *refusé*
  en dessous de 10° d'élévation ; ce rejet est un comportement voulu,
  pas une panne.

### Charge utile

- En appui au passage 2 : la COM-007 Vérification de l'OBDH comprend
  un contrôle du stockage de la charge utile.
- Pilote au passage 3 : COM-009 mise sous tension, COM-010 mise en
  route du refroidisseur.
- Pilote au passage 4 : COM-011 Étalonnage, COM-012 Première lumière.
- Écueils : commander `PAYLOAD_CAPTURE` avant que `payload.fpa_ready`
  (0x0610) ne soit positionné. La qualité de l'image est dégradée, mais
  la vérification de la procédure réussit parce que l'*acquisition* a
  réussi. L'évaluation de la qualité est une étape de vérification
  distincte.

### FDS

- En appui au passage 1 : confirmer la précision de l'orbite (le point
  GPS du dernier passage du jour de LEOP date maintenant de plusieurs
  orbites ; le rafraîchir).
- Pilote au passage 4 : calculer l'empreinte au sol de la cible de
  courant océanique choisie — fauchée de 273 km en travers de la trace,
  environ 59 km le long de la trace pour la bande standard de 2048 lignes. Les
  transmettre au poste Charge utile pour les paramètres de
  `PAYLOAD_CAPTURE`.
- Écueils : confondre la fauchée (273 km, une largeur d'empreinte) avec
  la distance d'échantillonnage au sol (GSD, 33,4 m, une grandeur par pixel). Ce sont deux
  propriétés du même instrument, et aucune ne remplace l'autre.

### Segment sol

- Tous les passages : piloter la préparation des stations avant chaque
  passage. Suivre les quatre passages ; assurer une transition propre
  entre les stations du réseau de cinq stations.
- Critique au passage 3 : la mise en froid se stabilise en une dizaine
  de minutes ; elle tient donc confortablement dans un seul passage de
  7–8 minutes plus les premières minutes du suivant. Confirmer que la
  TM est enregistrée à bord et demander la relecture avec `DUMP_STORE`
  (S15.9) au prochain AOS pour toute partie de la rampe tombée dans
  l'intervalle sans visibilité.

### Responsable de mission

- Suivre l'état de la première lumière. Préparer le bulletin client :
  « EOSAT-1 a obtenu sa première lumière à [heure], cible [nom], image
  en file d'attente pour transmission au sol. »



Tableau 11.2 — Scénarios d'injection d'anomalies pendant la recette en orbite, par gravité, avec premiers indices et reprises.

| Gravité | Fichier de scénario | Ce que voient les étudiants | Reprise |
|---|---|---|---|
| Facile | `eps_overcurrent.yaml` (ligne=`payload`) | Surintensité à la mise sous tension de la charge utile | CTG-012 Traitement d'une surintensité |
| Facile | `gs_rf_degradation.yaml` | Le TEB augmente en cours de passage | CTG-014 Anomalie de TEB |
| Moyen | `fpa_overtemp.yaml` | Le refroidisseur du FPA n'atteint pas la consigne de −15 °C ; `payload.cooler_margin_k` (0x064B) devient ≤ 0 | CTG-004 Dépassement thermique + mise en sécurité de la charge utile |
| Moyen | `payload_corrupt_image.yaml` | La première image arrive corrompue | CTG-015 Reprise après image corrompue |
| Difficile | `aocs_sensor_cascade.yaml` | Le senseur stellaire se dégrade ; le bilan de pointage n'est plus respecté | CTG-008 Panne du senseur stellaire → CTG-002 + report de la première lumière |
| Difficile | `eps_progressive_load_shed.yaml` | La dégradation de la batterie impose un délestage progressif pendant la mise en route du refroidisseur | CTG-001 Délestage sur sous-tension |
| Très difficile | `aocs_wheel_failure.yaml` suivi de `transponder_failure.yaml` | Une roue se bloque en fin de passage 3, puis le transpondeur tombe en panne au passage suivant | CTG-007 → CTG-003 |

Fiches aide-mémoire au chapitre 14 (Catalogue des procédures).

## 11.7 Critères de réussite (révision)

Tableau 11.3 — Critères de réussite de fin de recette en orbite, évalués pour les deux équipes en formation.

| Critère | Série de passages 1 (équipe A) | Série de passages 2 (équipe B) |
|---|---|---|
| Phase COMMISSIONING (5) déclarée par la direction de mission | ✓ | ✓ |
| Vérification de l'EPS terminée sans défaut | ✓ | ✓ |
| AOCS NOMINAL (mode 4) atteint, `aocs.att_error` < 0.5° | ✓ | ✓ |
| Table FDIR nominale chargée | ✓ | ✓ |
| Charge utile sous tension (ligne 3 alimentée *et* `payload.mode` = 1) | ✓ | ✓ |
| FPA dans la bande de consigne [−16.5, −14.5] °C et `payload.fpa_ready` (0x0610) = 1 | ✓ | ✓ |
| Image de première lumière acquise (ou formellement reportée) | ✓ | ✓ |
| Fiches d'anomalie ouvertes pour toutes les injections | ✓ | ✓ |

L'option « formellement reportée » est réelle : si l'équipe diagnostique
correctement que le pointage est insuffisant et choisit de reporter la
prise de vue, elle réussit. Si elle prend l'image malgré tout et
produit une image inexploitable, elle échoue.

## 11.8 Débriefing

Même structure que le débriefing de la LEOP. Les fiches d'observation
utilisées aujourd'hui sont **Équipe** et **Occupation de l'espace**
(les deux autres ont servi mercredi).

---


## 11.9 Déroulement détaillé des procédures de recette en orbite

Le jour 4 fait passer l'équipe de « LEOP terminée, tous les sous-systèmes
en fonctionnement » à « première lumière acquise et transmise au sol ».
Sur quatre passages au-dessus des stations sol (comprimés en 2,5 heures
de temps réel), onze des treize procédures de recette en orbite fournies
s'exécutent à peu près dans cet ordre. Ce chapitre est le support de
*formation* que l'équipe lit le mercredi soir.

### COM-001 — Vérification de l'EPS (déroulement approfondi)

La vérification de l'EPS est la première étape de la recette en orbite,
car toutes les étapes suivantes supposent que la puissance est fournie,
régulée et comptabilisée correctement.

#### Préparation préalable

- Satellite en phase 4 (LEOP terminée).
- COARSE_SUN (mode 3) atteint — pointage solaire, l'attitude de repli
  récupérable.
- Au moins 2 orbites de HK post-LEOP archivées (pour que l'ingénieur
  EPS dispose de données de tendance).
- `eps.bat_soc` (0x0101) > 70 %.

#### Conduite étape par étape

**Étape 1 — Mesure de référence de la tension du bus**

- GO du FD non requis (lecture seule).
- EPS : « FD, EPS — bus 28.1 V, nominal 28.0 ± 0.5 V band. »
- Vérification : `eps.bus_voltage` ∈ [27.5, 28.5] V.
- Pourquoi : c'est la **référence** à laquelle toutes les mesures
  suivantes sont comparées. Si le bus est à 27,6 V au début de la
  recette en orbite, l'équipe sait que c'est sa valeur normale, et
  27,6 V en pleine prise de vue n'a rien d'inquiétant.

**Étape 2 — Tension et SoC de la batterie**

- EPS : « FD, EPS — battery 28.4 V, SoC 84 percent. »
- Vérification : `eps.bat_voltage` (0x0100) dans la plage modélisée de
  la batterie ; `eps.bat_soc` (0x0101) > 70 %.
- Pourquoi : la batterie est une GomSpace NanoPower BPX 8S-1P —
  **100 Wh, 3 Ah, 28,8 V nominaux**, un boîtier de 0,33 U d'éléments
  18650. Sur EOSAT-1, sa tension aux bornes va de `soc_0_v` = 21.5 V
  à vide à `soc_100_v` = 29.2 V à pleine charge, 26,4 V en nominal. Il
  s'agit d'une chaîne de huit éléments en série, et non d'une batterie
  4S ; c'est elle qui rend possible le bus régulé d'environ 28 V. Ne pas
  confondre `eps.bat_voltage` (0x0100, la batterie) avec
  `eps.bus_voltage` (0x0105, le bus régulé) — ce sont deux paramètres
  distincts, avec des plages différentes.

**Étape 3 — Performances du générateur solaire en phase éclairée**

- EPS : « FD, EPS — power gen 58 W, beta 32 degrees, in
  predicted range. »
- Vérification : `eps.power_gen` (0x0107) dans la bande éclairée
  [40, 75] W.
- Pourquoi : le générateur comprend 0,198 m² de cellules fixées sur
  cinq faces de la structure (la face −Z, orientée vers le nadir, porte l'ouverture de l'imageur
  et le radiateur et n'a pas de cellules), plus **0,120 m² de cellules
  par aile déployable** sur un mécanisme d'entraînement à un axe — soit
  0,438 m² de cellules au total une fois déployé. La constante dans le
  plan du générateur, après l'ensemble des pertes, vaut 292 W/m² en BOL
  et **267,9 W/m² en EOL à trois ans** ; les ailes seules fournissent
  donc 2 × 0,120 × 292 = **70,1 W en BOL** (ce qui correspond exactement
  à la valeur nominale du MMA eHaWK de classe 6U), et la production
  crête du satellite complet atteint **88,6 W**. En phase éclairée, les
  mesures se situent entre environ 54 et 71 W selon l'angle bêta
  solaire ; une mesure très inférieure dans une géométrie favorable
  signale des cellules dégradées ou un mécanisme d'entraînement du
  générateur solaire bloqué, et une mesure supérieure à environ 89 W
  indique que la géométrie a été mal modélisée.

**Étape 4 — Surveillance de la décharge en éclipse** (cette étape couvre
une éclipse)

- EPS : « FD, EPS — eclipse entry T-zero. Power gen dropped to
  0.1 W in 18 s, nominal. »
- Mi-éclipse : « FD, EPS — at +15 min, bus 27.8 V, SoC 78 percent,
  drop rate 0.5 percent per minute. »
- Sortie d'éclipse : « FD, EPS — at exit, bus 27.6 V, SoC 69 percent,
  reservoir margin healthy. »
- Vérification : `eps.power_gen` ~0 W dans les 30 s suivant l'entrée en
  éclipse ; baisse du SoC < 1.5 %/min ; `eps.bus_voltage` > 27.0 V à
  mi-éclipse.
- Pourquoi : c'est le test de *survie*. L'orbite dure 5669 s (94,5 min)
  et la fraction d'éclipse varie sur l'année entre 0,351 et 0,372 ;
  une éclipse dure donc **de 33,2 à 35,2 minutes**. Avec une batterie de
  100 Wh et une charge nominale moyenne sur l'orbite d'environ 28,8 W,
  une éclipse de 34 minutes coûte environ 16,3 % de SoC, soit environ
  0,5 %/min. Le seuil de vérification de 1,5 %/min est un plafond, pas
  une valeur attendue : une mesure proche de ce plafond révèle une
  charge que vous n'avez pas commandée. L'échelle de protection
  ci-dessous est monotone — délestage dans le modèle à 25,0 V (environ
  45 % de SoC), FDIR `safe_mode_eps` à **24,5 V** (environ 39 %), puis
  les paliers de SoC à 30 / 20 / 10 %.

**Étape 5 — Reprise de la charge en sortie d'éclipse**

- EPS : « FD, EPS — at exit + 45 s, power gen 52 W, charging,
  recovery profile nominal. »
- À la sortie + 2 min : « FD, EPS — SoC trending up, will fully recover
  before next eclipse entry in 60 min. »
- Vérification : `eps.power_gen` > 35 W dans les 60 s ; SoC en hausse
  dans les 120 s.
- Pourquoi : détecte un défaut du régulateur de charge qui empêcherait
  la batterie de se recharger — avec, en cascade, une perte totale
  d'alimentation en 24 heures. Noter que la charge présente des pertes
  coulombiennes (rendement 0,94) et décroît linéairement jusqu'à zéro
  au-dessus de 90 % de SoC (phase à tension constante) : les dix
  derniers points reviennent donc bien plus lentement que les dix
  premiers.

**Étape 6 — Vérification du bilan de puissance**

- L'EPS calcule : production moyenne sur l'orbite, consommation
  moyenne, SoC en fin d'éclipse, marge.
- « FD, EPS — orbit-average generation 45.1 watts, load 28.8 watts,
  margin plus 16.3 watts, ratio 1.57. End-of-eclipse SoC predicted
  69 percent under nominal load. Healthy. »
- Vérification : marge positive ; SoC en fin d'éclipse > 50 %.
- Pourquoi : une seule orbite positive ne prouve rien — il faut prédire
  le régime établi. Sur l'année, β va de −20,8° à −31,2°. Le cas
  dimensionnant pour la production est l'EOL à **β = −31,2°**, pour lequel
  la production moyenne sur l'orbite vaut 45,1 W : l'entraînement du
  générateur ne suit le Soleil qu'à cos β près, si bien que le plus
  grand |β| donne la plus faible production, bien que son éclipse soit la plus
  courte. En regard :

  | Profil | Production (W) | Charge (W) | Marge (W) | Rapport |
  |---|---|---|---|---|
  | quiescent | 45,1 | 25,6 | +19,5 | 1,76 |
  | **nominal** | **45,1** | **28,8** | **+16,3** | **1,57** |
  | nominal_imaging | 45,1 | 32,8 | +12,3 | 1,38 |
  | manoeuvre | 45,1 | 32,1 | +12,9 | 1,40 |
  | worst (cas d'abus) | 45,1 | 46,8 | −1,7 | 0,96 |

  À β = −20,8°, la décharge la plus profonde (l'éclipse la plus longue),
  la production est de 47,0 W et le cas nominal boucle à 1,63×. En début
  de vie, ces deux valeurs sont 49,1 W et 51,2 W. Le profil `worst` est volontairement
  négatif — il maintient FINE pendant une orbite entière, fait tourner
  le refroidisseur en continu, prend des images pendant l'éclipse et
  vide la mémoire en HIGH à chaque passage. **Un 6U capable de tenir ce
  régime aurait besoin d'un générateur solaire qu'aucun 6U ne peut
  emporter.** La réponse de l'ingénieur consiste à faire fonctionner la
  prise de vue par intermittence, et c'est précisément la leçon que
  l'exercice doit enseigner. Si la marge est positive mais faible
  (< 2 W), toute charge imprévue (réchauffeur bloqué en marche) peut la
  faire basculer dans le négatif.

**Étape 7 — Régulation de la tension du bus lors d'un transitoire de charge**

- L'EPS se coordonne avec la charge utile : « FD, EPS, Payload — going
  for load-transient test. »
- Charge utile : « FD, Payload — first-key `PAYLOAD_SET_MODE(mode=1)`. »
  (Le FD valide en second.)
- (1 s plus tard) : « FD, Payload — payload at STANDBY, total load up
  2.4 watts, about 0.09 amps at 28 volts. Bus held 28.0 V,
  transient dip 0.15 V for 80 ms. »
- (5 s plus tard) : « FD, Payload — first-key `PAYLOAD_SET_MODE(mode=0)`. »
  La charge utile revient sur OFF.
- Vérification : le bus reste dans [27.0, 29.0] V pendant le
  transitoire.
- Pourquoi : c'est la seule étape de la recette en orbite qui perturbe
  *volontairement* le bus. L'imageur lui-même est une petite charge —
  le composant de référence (Simera Sense TriScape100) consomme
  **2,4 W au repos et 5,5 W en prise de vue**, et le fait que la prise
  de vue coûte *plus* que le repos est une contrainte physique que
  l'ancienne documentation présentait à l'envers. Le saut vraiment
  important intervient une fiche plus loin, au démarrage du
  refroidisseur de 15 W. Si le creux dépasse ici 1 V, le régulateur est
  à sa limite et les futures commandes de mise sous tension de la charge
  utile doivent être séquencées avec plus de soin.

#### Points de décision

- **Étape 3 : l'angle bêta s'écarte de la prédiction de plus de 10°.**
  L'attitude du satellite est peut-être erronée (nouveau calcul FDS) ou
  le modèle d'orbite est faux (nouvelle restitution d'orbite par le
  FDS). Troisième possibilité : un **mécanisme d'entraînement du
  générateur solaire bloqué** (`sada_stuck`) : l'angle d'entraînement
  0x0133 devient plat, les ailes reviennent à un fonctionnement d'ailes
  fixes et la production moyenne sur l'orbite chute d'environ 36 %, avec
  une ondulation caractéristique, une fois par orbite, sur les courants
  de chaque aile 0x0146 (+Y) et 0x0147 (−Y). Noter que 0x0110–0x0113
  sont des indicateurs d'état des *lignes* d'alimentation, pas de la
  télémesure du générateur. Dans tous les cas, consigner avant de
  poursuivre.
- **Étape 6 : la marge prédite est négative.** NE PAS poursuivre avec
  COM-002 et les suivantes. Lancer l'analyse de délestage CTG-001 et
  reporter la recette en orbite jusqu'à ce que l'équipe ait identifié
  la charge parasite.

### COM-002 — Vérification du TCS (déroulement approfondi)

#### Préparation préalable

- COM-001 terminée et GO.
- ≥ 1 orbite complète de HK thermique archivée.
- SoC > 60 %. Les deux lignes de réchauffeurs sont `htr_bat` (8 W) et
  `htr_obc` (4 W), et l'EPS les comptabilise à partir de l'état du
  *thermostat* publié par le TCS, et non de l'interrupteur de ligne —
  une ligne sur ON dont le thermostat est satisfait ne consomme rien.

#### Conduite étape par étape (4 étapes de fond)

**Étape 1 — Demander la HK thermique**

- Thermique : « FD, Thermal — `HK_REQUEST(sid=3)`. temp_obc 22 C,
  temp_battery 14 C, FPA at plus 11 C, all nominal. »
- Vérification : `tcs.temp_obc` (0x0406) ∈ [−5, +45] ;
  `tcs.temp_battery` transmis et dans la bande ; `payload.fpa_temp`
  (0x0601) transmis.
- Pourquoi : état thermique de référence avant de solliciter les
  réchauffeurs. Noter que la structure TCS est le **SID 3**, à une
  cadence de 60 s — la plus lente de l'ensemble de servitude, car les
  constantes de temps thermiques se comptent en minutes.

**Étape 2 — Solliciter chaque réchauffeur individuellement**

- La PDM compte **deux** circuits de réchauffeurs, et non quatre :
  `htr_bat` (ligne 5, 8 W) et `htr_obc` (ligne 6, 4 W).
- Pour chacun : Thermique : « FD, Thermal — go for exercise [heater]. »
  GO du FD. Le poste Thermique active le réchauffeur, surveille le
  rapport cyclique et la tendance de la zone, puis rétablit la commande
  automatique.
- Après la sollicitation : « FD, Thermal — [heater] duty cycle averaged
  35 percent, zone rose 3 C, response nominal. »
- Vérification : le rapport cyclique reste < 80 % ; la zone atteint la
  bande de consigne dans le délai prévu.
- Pourquoi : détecte les réchauffeurs bloqués en marche ou à l'arrêt.
  Détecte aussi les fils de réchauffeur en court-circuit (rapport
  cyclique proche de 100 % sans hausse de température).

**Étape 3 — Vérification de la régulation thermostatique**

- Le poste Thermique observe `tcs.temp_battery` (0x0407) pendant une
  demi-orbite, `htr_bat` étant en automatique.
- « FD, Thermal — htr_bat cycled 3 times in last 30 min,
  hysteresis 2.5 C, control law nominal. »
- Vérification : hystérésis observée ; cycles marche/arrêt réguliers.
- Pourquoi : la régulation thermostatique distingue le réchauffeur qui
  se déclenche de façon aléatoire (FET bloqué en conduction) de celui
  qui ne cycle pas mais maintient la température (un équilibre fortuit
  entre phase éclairée et éclipse).

**Étape 4 — Performances du radiateur en éclipse**

- Le poste Thermique surveille toutes les zones pendant une éclipse.
- « FD, Thermal — in eclipse, all zones drifted within band,
  largest drift OBC zone minus 4 C in 30 min, recovered on
  Sun-side. No runaway. »
- Vérification : zones stables ; aucun emballement, ni vers le haut ni
  vers le bas.
- Pourquoi : confirme que le radiateur dissipe la chaleur comme prévu
  et que le chemin thermique entre les composants internes et le
  radiateur est intact.

### COM-004 — Vérification des actionneurs SCAO (déroulement approfondi)

Quatre roues de réaction en pyramide (azimuts 45/135/225/315°,
élévation de 30° au-dessus du plan XY), plus trois barreaux
magnétocoupleurs. La fiche active les roues, commande le NOMINAL piloté
par les roues, recette chaque roue individuellement, puis démontre le
fonctionnement de la voie magnétique de déchargement du moment cinétique.

#### Préparation préalable

- COM-001 et COM-002 terminées ; COM-003 n'a **pas** encore été
  exécutée (décision Q16). Senseurs stellaires et gyroscopes sont encore
  éteints — il y a **deux** senseurs stellaires, ST1 et ST2, sélectionnés
  avec `ST_SELECT` (S8 func 6), et COM-003 les met en service après
  cette fiche.
- `aocs.mode` (0x020F) = 3 (COARSE_SUN), le maintien de la LEOP ;
  l'étape 2 de la fiche commande NOMINAL une fois les roues activées.
- Vitesses angulaires < 0,5 °/s sur tous les axes, lues dans
  `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205),
  `aocs.rate_yaw` (0x0206). Il n'existe pas de paramètre
  `aocs.body_rates`.
- `eps.bat_soc` (0x0101) > 65 %.

#### La chaîne de commande — à lire avant les étapes

Les vitesses de roue en **0x0207–0x020A sont des télémesures en lecture
seule.** Elles ne peuvent pas être commandées avec `SET_PARAM`, et
0x0280–0x0283 ne sont pas des consignes de vitesse de roue. Les deux
commandes qui font tourner une roue sont :

- `RW_SET_SPEED_BIAS(wheel_idx, bias_rpm)` — Service 8,
  Subtype 1, **func_id 8**. La polarisation s'**ajoute à la vitesse
  courante de la roue** : la référence de l'étape 3 sert donc de base à
  toutes les vérifications suivantes. Polariser deux fois de +2000 ne
  place pas la roue à 2000 tr/min ; cela la place à la référence +4000.
- `AOCS_RW_RAMP_DOWN(wheel_idx, target_rpm)` — Service 8,
  Subtype 1, **func_id 14**. `wheel_idx = 255` signifie *toutes les
  roues* et constitue l'arrêt d'urgence de cette fiche.

Les températures des roues sont en **0x0218–0x021B**. 0x028A–0x028D sont
les pourcentages de santé des têtes des senseurs solaires grossiers
(`aocs.css_head_health_py/my/pz/mz`) et n'ont rien à voir avec les
roues ; les lire pour contrôler une température est une erreur de
diagnostic classique.

#### Conduite étape par étape

**Étape 1 — Activer les quatre roues**

- AOCS : « FD, AOCS — first-key `AOCS_ENABLE_WHEEL(wheel_idx=0)` »,
  puis `wheel_idx` 1, 2 et 3 (S8 func_id 3), une commande par roue.
- Vérification : `aocs.wheels_enabled` (0x0260) = 4 en 10 s.
- Pourquoi : le chargeur d'amorçage laisse toutes les roues DISABLED et
  rien d'autre dans le catalogue n'en active une. Ne pas quitter la fiche
  avec moins de trois roues.

**Étape 2 — Commander le NOMINAL piloté par les roues**

- AOCS : « FD, AOCS — first-key `AOCS_SET_MODE(mode=4)`, NOMINAL. » Le
  FD valide en second.
- Vérification : `aocs.mode` (0x020F) = 4 (ou 8 en éclipse) en 300 s ;
  `aocs.commanded_mode` (0x0297) = 4.
- Pourquoi : sans senseur stellaire, rien ne fait sortir l'AOCS du
  maintien COARSE_SUN de la LEOP ; la fiche commande donc NOMINAL
  elle-même. Le simulateur l'accepte sans senseur ; la connaissance
  d'attitude reste sur la voie grossière Soleil–magnétomètre jusqu'à
  COM-003. C'est cette étape qui rend COM-003 possible : son seuil
  d'étalonnage de 0,10 °/s est atteint en NOMINAL piloté par les roues,
  jamais dans le maintien par magnétocoupleurs seuls (décision Q16).

**Étape 3 — Consigner les vitesses de roue de référence**

- AOCS : « FD, AOCS — `HK_REQUEST(sid=2)`. RW1 through RW4 reading
  plus 1180, minus 1210, plus 1195, minus 1205 rpm. Recorded as
  baseline. »
- Pourquoi : les roues tout juste activées reprennent aussitôt la charge
  de contrôle, des vitesses non nulles en NOMINAL sont donc attendues ;
  cette référence sert de base à tous les contrôles ci-dessous.

**Étapes 4 et 5 — Chaque roue à tour de rôle**

- AOCS : « FD, AOCS — first-key `RW_SET_SPEED_BIAS(wheel_idx=0,
  bias_rpm=2000.0)`. » Le FD valide en second.
- Vérification : `aocs.rw1_speed` (0x0207) atteint la référence
  +1800 à +2200 tr/min en 60 s ; `aocs.att_error` (0x0217) < 5°.
- AOCS : « first-key `RW_SET_SPEED_BIAS(wheel_idx=0,
  bias_rpm=-4000.0)` » — fait passer la roue par zéro jusqu'à la
  référence −2000.
- AOCS : « first-key `AOCS_RW_RAMP_DOWN(wheel_idx=0,
  target_rpm=0.0)` » — retour à < 100 tr/min en 60 s.
- Répéter pour `wheel_idx` 1, 2, 3.
- Pourquoi : le passage par zéro est tout l'intérêt de l'essai. Le
  frottement des roulements et l'asymétrie de friction se manifestent
  au passage par zéro, pas à haute vitesse.

**Étape 6 — Températures des roues**

- `GET_PARAM(param_id=0x0218)` … `0x021B`, toutes dans [−10, +55] °C.

**Étape 7 — Essai de désaturation du moment cinétique**

- AOCS : « FD, AOCS — first-key `AOCS_DESATURATE` » (S8, func_id 1).
- Vérification : `aocs.mode` (0x020F) = 7 (DESAT) ;
  `aocs.h_body_mag` (0x02B9) en baisse vers la bande morte de
  5.0 × 10⁻⁴ N·m·s.
- **Compter de 20 à 50 minutes**, et non cinq à dix. Voir le §13.7 pour
  en comprendre la raison.

#### Points de décision

- **Une roue n'atteint pas la polarisation commandée.** Vérifier que la
  ligne des roues est alimentée — `eps.pl_aocs_wheels` (0x0117) — et
  son courant sur `eps.line_current_7` (0x011F). Si l'alimentation est
  nominale et que la roue ne répond pas, la déclarer en panne et
  poursuivre : **le satellite tient FINE_POINT sur trois roues.**
  Trois quelconques des quatre roues de la pyramide engendrent toujours
  R³ (conditionnement de 2,175), et le mode FINE mesuré sur 3 roues
  tient une erreur de pointage moyenne de 0,0188°, contre 0,0208° sur
  quatre. Ce que perd le jeu dégradé, c'est l'espace nul — régulation
  de la polarisation et évitement des passages par zéro — si bien que
  la gigue est plus forte et que le mode est signalé par
  `aocs.fine_degraded` (0x0299).
- **L'erreur d'attitude dépasse 10° pendant l'essai d'une roue.**
  Arrêter immédiatement avec `AOCS_RW_RAMP_DOWN(wheel_idx=255,
  target_rpm=0.0)`.
- **La désaturation ne réduit pas le moment cinétique.** Vérifier
  `aocs.mtq_enabled` (0x025E) ; l'activation des MTQ est S8 func 9 et
  les rapports cycliques des barreaux sont en 0x0258–0x025A. Un
  déchargement est beaucoup moins efficace près de l'équateur
  magnétique — réessayer au-dessus d'un pôle.

### COM-005 — Transitions de modes SCAO (déroulement approfondi)

NOMINAL → FINE_POINT et retour, puis INERTIAL, le maintien COARSE_SUN
et DESAT. Depuis la décision Q16, l'AOCS est en NOMINAL depuis COM-004.
Chaque transition est une procédure distincte à l'intérieur de celle-ci.

**Les codes de mode sont ceux de `aocs/aocs_mode_codes.yaml`, et aucun
autre :**

| Code | Mode | Code | Mode |
|---|---|---|---|
| 0 | OFF | 5 | FINE_POINT |
| 1 | SAFE_BOOT | 6 | SLEW |
| 2 | DETUMBLE | 7 | DESAT |
| 3 | COARSE_SUN | 8 | ECLIPSE |
| 4 | NOMINAL | 9 | INERTIAL |

Les anciennes versions de ce manuel et de plusieurs fiches de procédure
fournies étaient systématiquement **décalées d'une unité** par rapport à
ce tableau — elles appelaient COARSE_SUN 2 et NOMINAL 3. Considérez
comme suspect tout numéro de mode que vous n'avez pas vérifié
vous-même dans le YAML. Il n'existe aucun mode appelé SAFE_POINT ni
NOMINAL_POINT.

#### Conduite étape par étape

**Étape 1 — Confirmer l'état de départ**

- AOCS : « FD, AOCS — mode 4 NOMINAL, body rates roll minus 0.02,
  pitch plus 0.01, yaw minus 0.03 deg per second, all below the
  0.05 threshold. »
- Remarque : l'amortissement repose réellement sur une loi B-dot
  pilotée par le magnétomètre, m = −k dB/dt, les barreaux saturant à
  1,6 A·m² par axe. Il converge *lentement* — à partir d'un culbutage de
  séparation de 14°/s, le modèle met environ 4300 s pour atteindre le
  seuil de sortie de DETUMBLE à 0,5°/s. Toute affirmation selon laquelle
  l'amortissement est rapide est fausse, et c'est précisément pour cela
  qu'il est terminé avant le début de cette fiche.

**Étape 2 — Verrouiller NOMINAL**

- AOCS : « FD, AOCS — first-key `AOCS_SET_MODE(mode=4)`, NOMINAL. » Le
  FD valide en second.
- « FD, AOCS — mode change command accepted. »
- (30 s plus tard) « FD, AOCS — nadir acquisition in progress, body
  rates settling. »
- (60 s plus tard) « FD, AOCS — mode 4 NOMINAL confirmed, nadir
  pointing achieved, `aocs.att_error` 0.42 deg. »
- Vérification : `aocs.mode` (0x020F) = 4 en 60 s ;
  `aocs.att_error` (0x0217) < 0.5° en 120 s.
- Pourquoi : l'AOCS vole en NOMINAL depuis COM-004 ; la commande verrouille
  `aocs.commanded_mode` (0x0297) = 4, le chemin de retour sur lequel se
  règle chaque transition automatique. COARSE_SUN (3) reste l'attitude
  *récupérable* — Soleil sur les panneaux, faibles vitesses angulaires —
  sur laquelle se replier si NOMINAL échoue.

**Étape 3 — Contrôler les préconditions du mode FINE avant de le commander**

- AOCS : « FD, AOCS — `AOCS_FINE_READY_CHECK` » (S8 func 89).
- Vérification : `aocs.fine_ready` (0x02C5) = 0 — **tous les bits à
  zéro**. Le masque de bits est le suivant : bit 0, senseur stellaire
  voyant moins de 5 étoiles ; **bit 1, moins de TROIS roues
  disponibles** ; bit 2, MEKF non convergé ; bit 3, vitesses angulaires
  élevées ; bit 4, moment cinétique supérieur à 70 % de l'enveloppe ;
  bit 5, estimateur en propagation seule ; bit 6, basculement non
  inactif depuis 60 s.
- Pourquoi le bit 1 compte : il signifie *moins de trois*, et non moins
  de quatre. Trois roues constituent une configuration FINE pilotable ;
  deux, non.

**Étape 4 — Transition vers FINE_POINT**

- AOCS : « FD, AOCS — first-key `AOCS_SET_MODE(mode=5)`, FINE_POINT. »
  Le FD valide en second.
- (60 s) « FD, AOCS — mode 5 confirmed, total pointing error
  3-sigma 0.020 deg on 0x02AA, inside the 0.05 deg imaging gate. »
- Vérification : `aocs.mode` (0x020F) = 5 en 30 s ;
  `aocs.total_pointing_err_3sig` (0x02AA) < 0.05° en 300 s.

**Étape 5 — Vérifier la décomposition du bilan de pointage**

- AOCS : « FD, AOCS — knowledge error 0x02A7 reading 18 arcsec
  3-sigma, control error 0x02A8 0.0188 deg, RSS 0.020 deg on
  0x02AA. Geolocation error 0x02C7 180 metres, about five ground
  pixels at 33.4 metre GSD. »
- Les sources de l'estimateur en service se lisent sous forme de masque
  de bits dans `aocs.est_source` (0x02C1) : bit 0, senseur stellaire ;
  bit 1, CSS ; bit 2, magnétomètre ; bit 3, gyromètre. L'étalonnage du
  biais des gyromètres est une activité **bord**
  (`AOCS_GYRO_CALIBRATION`, S8 func 13), et non un chargement calculé au
  sol, et les trois axes gyrométriques n'ont aucune unité redondante
  derrière eux.

#### Points de décision

- **Étape 4 : FINE non atteint en 300 s.** Relire 0x02C5 — il indiquera
  la raison. Deux voies : attendre (le MEKF a parfois simplement besoin
  de plus de temps pour converger) ; ou revenir en NOMINAL (mode 4) et
  lancer la procédure d'anomalie AOCS. Pratique courante dans
  l'industrie : attendre une fois, puis revenir en repli.

### COM-006 — Vérification de la liaison TTC

Cette fiche a été réécrite pendant la phase 5, et cette réécriture
mérite d'être comprise plutôt que survolée : l'ancienne version
mesurait une liaison qu'elle n'avait jamais mise en marche, et
affirmait un état final qu'elle n'avait jamais commandé.

**L'échelle de débits compte trois échelons**, définis dans
`subsystems/ttc.yaml` :

| Palier | Débit | Argument `rate` | Rôle |
|---|---|---|---|
| BEACON | 1 kbit/s | non sélectionnable par func 65 | Amorçage / balise de survie |
| LOW | 16 kbit/s | `rate=0` | **Opérations de routine** et repli en mode survie |
| HIGH | 128 kbit/s | `rate=1` | Télémesure différée et vidages d'images ; soumis à conditions et à mériter |

L'ancien codage binaire est conservé : 0 signifie toujours « le débit
bas » et 1 toujours « le débit haut » — ce sont les débits eux-mêmes
qui ont changé. 1 kbit/s n'a jamais été un débit d'exploitation :
l'ensemble de servitude fourni génère 1378,5 bit/s de paquets PUS, soit
1588 bit/s sur le canal après RS(255,223) et la mise en trames TM ; une
liaison à 1 kbit/s est donc saturée à 159 % avant même d'envoyer quoi
que ce soit d'autre.

#### Conduite étape par étape

**Étape 0 — Configurer la chaîne en bande S** (cette étape est la
raison d'être de la réécriture)

L'échelle de débits est conditionnée par quatre éléments ; tant que les
quatre ne sont pas satisfaits, les deux paliers opérationnels sont
refusés avec l'erreur S1.8 `0x0007` :

- `EPS_POWER_ON(line_index=2)` (S8 func 19) — la ligne `ttc_tx`.
  Vérifier `eps.pl_ttc_tx` (0x0112) = 1.
- `TTC_PA_ON` (S8 func 66) — l'amplificateur de puissance en bande S.
  Vérifier `ttc.pa_on` (0x0516) = 1.
- `TTC_SET_BEACON_MODE(on=0)` (S8 func 70) — libérer le palier balise
  forcé. Vérifier `ttc.beacon_mode` (0x0521) = 0. Le mode balise
  **survit à un amorçage du logiciel applicatif** : un satellite peut
  donc arriver à cette fiche encore verrouillé.
- `TTC_DEPLOY_ANTENNA` (S8 func 69). Vérifier
  `ttc.antenna_deployed` (0x0520) = 1. Le déploiement par fil thermofusible
  est irréversible.

Confirmer ensuite que la chaîne émet réellement : `ttc.tx_active`
(0x0525) = 1. S'il vaut 0, `ttc.tx_gate_status` (0x052B) indique
l'autorisation manquante (bit 0, PA ; bit 1, ligne `ttc_tx` ; bit 2,
station en visibilité ; bit 6, antenne).

- TT&C : « FD, TT&C — S-band chain configured, PA on, beacon tier
  released, antenna deployed, `tx_active` reads 1. »

**Un point pédagogique qui trouve sa place ici.** EOSAT-1 possède
**deux émetteurs** : la chaîne principale en bande S et une balise UHF
distincte à antenne fouet, sur la ligne non commutable `ttc_rx`. Couper
le PA, ou ouvrir la ligne `ttc_tx`, arrête la télémesure en bande S —
et la balise continue d'émettre. C'est pourquoi la HK SID 11 continue
d'arriver d'un satellite dont la chaîne en bande S est entièrement mal
configurée, et c'est le diagnostic le plus utile lors d'un passage sans
télémesure. Ne pas confondre `ttc.beacon_mode` (0x0521, le *palier TM
forcé* sur l'échelle en bande S) avec `ttc.beacon_tx_on` (0x0526,
l'*émetteur* UHF).

**Étape 1 — Liaison de référence, palier LOW**

- `HK_REQUEST(sid=6)` (Service 3, **Subtype 27**) — télémesure de
  servitude TT&C.
- Vérification : `ttc.link_status` (0x0501) = **2** (LOCKED — et non
  1) ; `ttc.rssi` (0x0502) > −100 dBm ; `ttc.link_margin` (0x0503)
  > 6.0 dB.

**Étape 2a — Établir la référence de chaque échelon**

- `TTC_SET_DATA_RATE(rate=0)` (S8 func 65) — LOW.
  Vérifier `ttc.tm_data_rate` (0x0506) = 16000 et `ttc.tm_tier`
  (0x0539) = 1. Consigner la marge : compter 55–59 dB à 30° d'élévation.
- `TTC_SET_DOWNLINK_MODE(on=1)` (S8 func 79) — vérifier
  `ttc.downlink_mode` (0x053C) = 1.
- `TTC_SET_DATA_RATE(rate=1)` — HIGH. Vérifier 0x0506 = 128000,
  0x0539 = 2, et `ttc.tm_symbol_rate` (0x053B) = 64000 Bd — le passage
  en QPSK se voit sur l'analyseur de spectre de la station comme le
  même débit d'information dans une largeur de bande moitié moindre.
  Consigner la marge : compter 45–48 dB à 30°.
- **Calculer l'écart : marge(LOW) − marge(HIGH) doit valoir
  10,5 ± 0,5 dB.** Ce chiffre n'est pas empirique — il correspond au
  débit multiplié par 8 (−9,03 dB) plus le changement de codage, de
  conv+RS 7,5 dB à RS 6,0 dB (−1,5 dB). Un jeu de mesures qui ne le
  montre pas révèle une erreur de modélisation, et non un problème de
  liaison.
- Revenir ensuite en arrière : `TTC_SET_DATA_RATE(rate=0)` **et**
  `TTC_SET_DOWNLINK_MODE(on=0)`. Les deux, en deux commandes
  distinctes.

**Étape 2b — Confirmer la condition d'élévation du palier HIGH**

- Lorsque le passage redescend sous 10° sur `ttc.contact_elevation`
  (0x050A), tenter `TTC_SET_DATA_RATE(rate=1)`.
- Vérification : la commande est **rejetée** par un échec d'exécution
  S1.8 qui désigne la condition d'élévation, et 0x0506 reste à 16000.
- C'est un comportement voulu, pas une anomalie. Un palier refusé est
  la manière dont le satellite signale au sol qu'une règle n'a pas été
  respectée ; un plafonnement silencieux la masquerait. Consigner le
  rejet comme preuve que la condition fonctionne.

**Étape 3 — Consigner les marges**

- Le SPACON consigne les marges LOW et HIGH par station et par
  élévation. Elles deviennent le référentiel du bilan de liaison de la
  mission.
- **Lisez les chiffres avant de les interpréter.** Le pire cas de toute
  la matrice fournie est HIGH à Troll à 5° d'élévation, et il vaut
  **33,7 dB**. Chaque échelon boucle avec des dizaines de dB, pour
  toutes les stations et toutes les géométries : cette liaison n'est pas
  limitée en puissance. Les seuils GO/NO-GO de 3 dB et 6 dB de la fiche
  sont des seuils de *vraisemblance* — une mesure proche de ces valeurs
  signifie que quelque chose ne va pas dans le modèle, l'attitude ou la
  station sol, et non que la géométrie est limite. De même, la condition
  de 10° sur HIGH est une condition de **politique d'exploitation**, et
  non une condition de marge.

**Étape 9 — Mettre la liaison en configuration sûre**

- `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)`,
  `TTC_SWITCH_PRIMARY` (S8 func 63).
- Vérification : `ttc.tm_tier` (0x0539) = 1 **et**
  `ttc.tm_tier_cmd` (0x053A) = 1 — le palier actif et le palier commandé
  doivent concorder ; `ttc.downlink_mode` (0x053C) = 0 ;
  `ttc.beacon_mode` (0x0521) = 0.
- L'antenne n'est **pas** repliée et le PA n'est **pas** coupé. Le
  déploiement est irréversible, et une fiche de recette en orbite qui se
  terminerait en rendant l'émetteur muet laisserait au passage suivant
  un satellite réduit à sa seule balise.
- La leçon : une configuration qu'une fiche *affirme* sans jamais la
  *commander* est une configuration dont le quart suivant hérite par
  chance.

### COM-007 — Vérification de l'OBDH

#### Conduite étape par étape

**Étape 1 — Vérifier le mode de l'OBC, le processeur et la mémoire**

- SPACON : « FD, SPACON — `HK_REQUEST(sid=4)`. `obdh.mode` (0x0300)
  reads NOMINAL, CPU load 0x0302 at 34 percent, mass-memory usage
  0x0303 at 21 percent, EDAC/SEU counter 0x0319 unchanged since
  boot. »
- Noter que la structure plateforme est le **SID 4**, et non le SID 3 —
  la table des SID de servitude est : 1 EPS, 2 AOCS, 3 TCS,
  4 OBDH/plateforme, 5 charge utile, 6 TT&C, 8 EPS étendu, 9 PROP,
  11 balise. Demander le mauvais SID puis s'interroger sur les
  paramètres reçus est l'une des erreurs de débutant les plus
  fréquentes.

**Étape 2 — Contrôler les compteurs TC/TM**

- `GET_PARAM(param_id=0x0304)` `obdh.tc_rx_count`,
  `0x0305` `obdh.tc_acc_count`, `0x0306` `obdh.tc_rej_count`,
  `0x0307` `obdh.tm_pkt_count`.
- SPACON : « FD, SPACON — received 214, accepted 214, rejected 0. »
- Attention : `obdh.sw_image` (0x0311) est l'*image en cours
  d'exécution* (0 = chargeur d'amorçage, 1 = logiciel applicatif), et
  non un compteur de rejets. L'avoir lu comme tel est un défaut passé
  documenté.

**Étape 3 — Chien de garde, puis excursion de mode**

- `OBC_DIAGNOSTIC` (S8 func 61) et `GET_PARAM(param_id=0x0316)` :
  chien de garde armé, `obdh.last_reboot_cause` = 0. La fiche du
  simulateur ne fait aucun vidage mémoire S6 ; la santé de la mémoire,
  ce sont les compteurs d'erreurs et de SEU de l'étape 1, lus deux fois.
- `OBC_SET_MODE(mode=1)`, puis `OBC_SET_MODE(mode=0)` (S8 func 50).
- SPACON : « FD, SPACON — watchdog armed, no resets; SAFE confirmed,
  NOMINAL restored, `obdh.mode` reads 0. »

**Étape 4 — Vérifier l'état des bus A/B**

- `obdh.active_bus` (0x030E), `obdh.bus_a_status` (0x030F),
  `obdh.bus_b_status` (0x0310).
- SPACON : « FD, SPACON — bus A active, both CAN buses report OK,
  no error counts. »

### COM-008 — Configuration de la FDIR

C'est l'une des étapes les plus lourdes de conséquences de la recette
en orbite. Sur EOSAT-1, la FDIR n'est pas un mécanisme unique mais
trois, et l'opérateur doit bien les distinguer :

- **Le jeu de règles FDIR** (`subsystems/fdir.yaml`) — 17 conditions
  sur des paramètres, chacune dotée d'un `level` et d'une action
  autonome nommée, évaluées à chaque pas de simulation.
- **La surveillance bord du service PUS 12**
  (`monitoring/s12_definitions.yaml`) — 46 définitions de limites,
  chacune marquée WARNING ou ALARM. Elles produisent des violations, et
  non des actions.
- **Les règles événement-action du service PUS 19**
  (`monitoring/s19_rules.yaml`) — 32 règles, chacune reliant une
  condition bord à une fonction S8 que le satellite exécute sans
  opérateur dans la boucle.

Une fois ces mécanismes armés, le satellite agit de lui-même. Si une
condition est *déjà* vraie (p. ex. un capteur dont la mesure est hors
bande), la réponse se déclenche immédiatement — c'est pourquoi le
contrôle préalable au chargement ci-dessous n'a rien d'une formalité.

**Gravité et autonomie sont deux échelles différentes. Ne les confondez
pas.**

- **La gravité FDIR va de 0 à 4** : 0 rien/normal, 1 INFO, 2 WARNING,
  3 ALARM, 4 CRITICAL. Elle répond à la question *à quel point est-ce
  grave*.
- **Le niveau d'autonomie va de 0 à 3** : 0 niveau unité (matériel,
  < 1 s — déclenchement d'une protection contre les surintensités du
  PCDU) ; 1 niveau sous-système (logiciel du sous-système, 1–10 s — un
  thermostat de réchauffeur) ; 2 niveau système (l'application FDIR de
  l'OBC, 10–60 s — une transition de mode ou un délestage) ; 3 niveau
  sol (l'équipe de contrôle du vol, de quelques minutes à quelques
  heures — reprise manuelle). Il répond à la question *qui est autorisé
  à agir*.

Un événement de gravité 4 traité au niveau d'autonomie 3 est un défaut
critique auquel seul le sol peut toucher. Un événement de gravité 1
traité au niveau d'autonomie 0 est un thermostat qui fait son travail.
Les deux nombres sont indépendants, ils sont signalés séparément, et un
opérateur qui prend l'un pour l'autre informera systématiquement mal le
FD.

#### Conduite étape par étape

**Étape 1 — Contrôle préalable au chargement**

- SPACON : « FD, SPACON — confirming all subsystems nominal
  before arming. »
- Chaque poste confirme : EPS, AOCS, Thermique, TT&C et Charge utile
  annoncent tous OK.

**Étape 2 — Vérifier que le jeu de règles est actif et relire les seuils**

- Le SPACON relit l'activation générale et le nombre de règles actives,
  puis passe en revue les seuils critiques et confirme qu'ils
  correspondent à l'échelle configurée — sous-tension `safe_mode_eps` à
  **24.5 V**, actions sur le SoC batterie à 20 % (mise hors tension de
  la charge utile) et à 15 % (mode survie de l'EPS), erreur d'attitude
  persistante > 5° pendant 420 s, température OBDH > 65 °C, nombre de
  redémarrages > 4.
- (attente de 15 s en surveillant le panneau FDIR) « FD, SPACON — nothing
  fired in the first 15 seconds; the rule set is happy with the current
  state. »

**Étape 3 — Injecter une condition de test sans danger**

- SPACON : « FD, SPACON — going to test that FDIR is actually
  monitoring. Brief telemetry perturbation on battery
  temperature. »
- (perturbe `tcs.temp_battery` (0x0407) jusque dans la bande d'alerte,
  puis rétablit la valeur)
- « FD, SPACON — the monitor tripped within 3 seconds at WARNING,
  no autonomous action. It cleared within 2 seconds of my
  restoring the value. FDIR is live. »

**Étape 4 — Vérifier qu'aucune action autonome n'a été exécutée**

- SPACON : « FD, SPACON — confirmed: the perturbation stayed below
  the threshold that carries an action, so nothing was commanded
  autonomously. Autonomy stayed at level 1. FDIR panel clean.
  GO COM-009. »
- Noter également que la génération de la télémesure de servitude est
  commandée, et non automatique : seuls les SID **1 et 11** sont activés
  à la mise sous tension, et le moteur réapplique exactement cet
  ensemble à l'amorçage du logiciel applicatif. Tout le reste nécessite
  `HK_ENABLE`, qui est le **Service 3, Subtype 5**. (`HK_REQUEST` est le
  Service 3, Subtype 27. Toute mention de S3 sous-type 1 ou 25 pour une
  demande de servitude est erronée.)

### COM-009 — Mise sous tension de la charge utile

#### Conduite étape par étape

**Contrôle préalable avant l'étape (environ 5 min avant la commande)**

- Charge utile : « FD, Payload — pre-flight: imaging-target catalogue
  loaded, calibration sets not yet taken, `payload.store_used`
  (0x0604) at 20 percent of the 20 GB store, `payload.product_count`
  (0x0648) zero. »
- EPS : « FD, EPS — battery 84 percent. The cooler is 15 watts and
  reaches setpoint in about ten minutes, so the ramp costs roughly
  2.5 watt-hours — two and a half percent of the 100 watt-hour
  pack. Well above the 50 percent red line. »
- Thermique : « FD, Thermal — FPA at plus 11 C, its uncooled
  equilibrium; cooler off, ready to receive the payload heat load. »

**Étape 1 — GO du FD**

- Le FD fait le tour de table de tous les postes : « EPS, Thermal,
  AOCS, TT&C — go for payload power-on? »
- Chacun : « FD, [POSTE] — go. »
- FD : « Go for payload power-on. »

**Étape 2 — Alimenter la ligne, puis commander le mode**

- Charge utile : « FD, Payload — first-key `EPS_POWER_ON(line_index=3)`,
  the payload line. » Le FD valide en second (criticité élevée).
- (2 s) « FD, Payload — accepted. `eps.pl_payload` (0x0113) reads 1. »
- Charge utile : « first-key `PAYLOAD_SET_MODE(mode=1)`, STANDBY. »
- (5 s) « FD, Payload — total load up 2.4 watts, about 0.09 amps at
  28 volts. Overcurrent trip on this line is 2.5 amps, so we are
  nowhere near it. »
- **L'ordre compte, et la fiche l'impose.** Un `PAYLOAD_SET_MODE`
  envoyé sans que la ligne EPS soit alimentée est annulé au pas de
  calcul suivant : la charge utile ne peut pas tenir un mode pour lequel
  elle n'a pas d'alimentation. Redemander le SID 5 après 60 s
  supplémentaires et confirmer que le mode est *resté* à 1 au lieu de
  retomber discrètement à 0.

**Étape 3 — Vérifier le mode**

- Charge utile : « FD, Payload — `payload.mode` (0x0600) reads 1 STANDBY,
  held over two housekeeping cycles. Mode change confirmed. »
- Les modes de la charge utile sont **0 OFF, 1 STANDBY, 2 IMAGING,
  3 CALIBRATION**. Le mode 3 est nouveau ; c'est un véritable mode de
  l'instrument, et non une variante de la prise de vue — voir COM-011.

**Étape 4 — Vérifier le stockage et l'état de santé**

- Charge utile : « FD, Payload — `payload.store_used` (0x0604) at
  20 percent of the 20 GB store; `payload.product_count` (0x0648)
  zero and `payload.product_mb` (0x0647) zero — no products on
  board. `payload.imager_status` (0x0611) shows no fault bits.
  Ready for COM-010. »

#### Points de décision

- **Courant de ligne nettement supérieur aux 2,4 W / 0,09 A attendus,
  mais inférieur au seuil de disjonction de 2,5 A.** Deux lectures
  possibles : un appel de courant au démarrage à froid qui se stabilise
  en 30 s (attendre) ; ou une consommation réellement bloquée à un
  niveau élevé (CTG-012 Traitement d'une surintensité). Attendre
  d'abord 30 s.
- **`payload.imager_status` (0x0611) présente un bit de défaut.** Le
  consigner, commander `PAYLOAD_SET_MODE(mode=0)`, et ne **pas** passer
  à la mise en route du refroidisseur.

### COM-010 — Activation du refroidisseur du FPA

C'est une étape rapide, contrairement à ce qu'affirmait autrefois ce
manuel. Le refroidisseur du FPA est un **cryoréfrigérateur Stirling
miniature**, et non un empilement thermoélectrique/Peltier, et le
modèle corrigé à un seul nœud le stabilise en une dizaine de minutes.

- Point de départ : l'**équilibre non refroidi, +8 à +14 °C**, et non
  les +5 °C ambiants que supposait l'ancien texte.
- Consigne : **−15 °C** (`payload.yaml fpa_cooler_target_c`). La bande
  d'acceptation est [−16.5, −14.5] °C.
- Vitesse initiale ≈ **4 °C/min**, décroissant exponentiellement. La
  rampe est du premier ordre, et non linéaire : une vitesse plus faible
  à T+5 qu'à T+2 est donc attendue et ne constitue pas une panne.
- Puissance : **15 W**, comptabilisée sur la ligne EPS 4
  (`fpa_cooler`).
- **Le modèle du FPA ne dépend pas de l'éclipse ni de la phase
  éclairée.** Toute procédure qui distingue la pente de mise en froid
  selon l'éclairement décrit un modèle qui n'existe pas. Cette fiche
  n'a pas besoin de couvrir une éclipse.

#### Conduite étape par étape

**Étape 1 — Vérifier que le FPA est à l'équilibre non refroidi, refroidisseur sur OFF**

- Thermique : « FD, Thermal — `payload.fpa_temp` (0x0601) at plus
  11.5 C, inside the plus-8 to plus-14 band. Cooler off, ready for
  enable. Marking cooldown T-zero. »

**Étape 2 — Activer le refroidisseur**

- Thermique : « FD, Thermal — first-key `FPA_COOLER(on=1)`, Service 8
  Subtype 1, func_id 43. » Le FD valide en second (criticité élevée,
  plus grosse charge unitaire du satellite).
- Vérification, et c'est tout l'objet de la fiche : **à la fois**
  `tcs.cooler_fpa` (0x040C) = 1 *et* `eps.pl_fpa_cooler` (0x0114)
  = 1. Le défaut historique était un chemin de commande qui
  positionnait l'indicateur du refroidisseur sans alimenter la ligne
  EPS : l'opérateur croyait le refroidisseur en marche, et le FPA ne
  refroidissait jamais. Tous les chemins de commande alimentent
  désormais la ligne ; si 0x040C et 0x0114 venaient de nouveau à
  diverger, ce serait le retour de ce défaut.
- (30 s) « FD, Thermal — `eps.power_cons` (0x0106) up 15 watts
  against baseline, bus holding 27.9 V. »

**Étape 3 — Surveiller la rampe (5 premières minutes)**

- Le poste Thermique relève `payload.fpa_temp` (0x0601) chaque minute.
- À T+2 min : en dessous de +4 °C.
- À T+5 min : en dessous de −8 °C.
- « FD, Thermal — on the exponential, rate falling as expected. »

**Étape 4 — Surveiller la stabilisation (5 à 15 minutes)**

- À T+10 min : dans [−16.0, −14.0] °C.
- À T+15 min : dans [−16.0, −15.0] °C.
- **Le détecteur ne descend jamais sous la bande de consigne.** Une
  mesure plus froide que −16.5 °C est un défaut de régulation, et non
  un refroidisseur trop performant ; la boucle régule sur la consigne,
  elle ne fonctionne pas en boucle ouverte.

**Étape 5 — Vérifier la disponibilité, pas la température**

- Vérification : `payload.fpa_temp` (0x0601) dans [−16.5, −14.5] °C
  **et** `payload.fpa_ready` (0x0610) = 1.
- C'est l'indicateur de disponibilité, et non une température retenue
  de mémoire, qui conditionne la prise de vue. Il comporte 60 s
  d'hystérésis : attendez-vous à ce qu'il se positionne environ une
  minute après que la température a été atteinte.
- Lire aussi `payload.cooler_floor_c` (0x064A) et
  `payload.cooler_margin_k` (0x064B). La marge doit être d'environ
  +5 K à la consigne de −15 °C pour un puits interne à +12 °C.
- La consigne elle-même est transmise sous forme d'**uint16 en
  centikelvins** : −15 °C correspond à 25815 cK = `0x64D7`. Une erreur
  d'unité, et la commande est refusée ou la consigne n'a aucun sens.

#### Points de décision (le terrain d'anomalies de ce quart)

- **`cooler_margin_k` (0x064B) ≤ 0.** Le refroidisseur ne peut
  physiquement pas atteindre la consigne commandée avec la température
  de puits et la charge actuelles. La solution est une **consigne plus
  chaude, pas une attente plus longue.** La capacité du refroidisseur
  se dégrade avec l'écart de température à franchir : il fonctionne à
  environ 23 % du rendement de Carnot ; maintenir −15 °C face à un
  puits à +12 °C représente donc un écart de 27 K, avec 22,5 W de
  chaleur parasite pompée pour 15 W en entrée — un COP requis de 1,50 (environ 16 % du rendement de Carnot, dans les 23 % du refroidisseur), alors
  qu'un Peltier à un étage plafonnerait vers 0,88 pour le même écart.
  Demandez un écart plus faible et vous l'obtiendrez.
- **Température qui baisse bien plus lentement que 4 °C/min.** Vérifier
  d'abord la consommation du refroidisseur : `payload.cooler_pwr`
  (0x0602) doit indiquer 15 W. S'il indique zéro alors que
  `tcs.cooler_fpa` vaut 1, vérifier `eps.pl_fpa_cooler` (0x0114) — la
  ligne, et non l'indicateur.
- **Stabilisation à une température plus chaude que −15 °C.**
  Poursuivre en acceptant la consigne plus chaude (RSB dégradé mais
  exploitable, consigné comme anomalie), ou abandonner et reporter la
  première lumière. Protocole des missions réelles : accepter la
  consigne sous-optimale, acquérir une image, et ne reporter que si la
  qualité de l'image est réellement médiocre.

### COM-011 — Étalonnage de la charge utile

#### Conduite étape par étape

L'étalonnage radiométrique est une activité **obturateur fermé / lampe
allumée** que l'instrument effectue dans **son propre mode :
CALIBRATION, `payload.mode` = 3.** L'ancienne conception obligeait
l'opérateur à passer d'abord en IMAGING — ce qui revenait à ouvrir
l'obturateur et à intégrer la scène avant de demander une image
d'obscurité, précisément ce qu'une image d'obscurité ne doit pas
contenir. L'étalonnage d'obscurité n'exige plus le mode IMAGING.

Cinq codes de refus dédiés existent ; ils méritent d'être mémorisés,
car chacun désigne exactement le problème :

| Code | Signification |
|---|---|
| 0x0024 | Étalonnage refusé car la charge utile est en IMAGING |
| 0x0025 | FPA non disponible |
| 0x0026 | Obturateur dans la mauvaise position |
| 0x0027 | Lampe dans le mauvais état |
| 0x0028 | Capture tentée avec l'obturateur fermé |

(0x0021–0x0023 restent les codes de refus liés au *pointage* lors de la
capture et forment une famille différente.)

**Étape 1 — Vérifier l'état préalable à l'étalonnage**

- Charge utile : « FD, Payload — `payload.mode` (0x0600) 1 STANDBY,
  `payload.fpa_temp` (0x0601) minus 15.2 C inside the band,
  `payload.fpa_ready` (0x0610) reads 1. »

**Étape 2 — Fermer l'obturateur**

- Charge utile : « FD, Payload — first-key
  `PAYLOAD_SET_SHUTTER(position=0)`, CLOSED » (S8 func 119). Il existe
  une commande de position absolue de l'obturateur ; on ne déplace pas
  l'obturateur par petites touches.
- Vérification : `payload.shutter_pos` (0x063C) = 0.

**Étape 3 — Acquérir la série d'obscurité**

- Charge utile : « first-key `PAYLOAD_CAL_LAMP(on=0)` » (S8 func 95) —
  lampe éteinte pour une image d'obscurité.
- Charge utile : « first-key `PAYLOAD_START_CALIBRATION(mode=0)` »
  (S8 func 37) — la phase DARK.
- Vérification : `payload.mode` (0x0600) = **3** (CALIBRATION) et
  `payload.calibration_active` (0x062A) = 1 en 15 s ; puis
  0x062A revient à 0 en 120 s avec
  `payload.cal_abort_reason` (0x0645) = 0.
- « FD, Payload — dark set complete, `payload.dark_frame_cnt`
  (0x0642) non-zero, mean dark signal 32 DN on the 12-bit 0–4095
  scale, standard deviation under 10 DN. No light leak. »

**Étape 3a — Acquérir la série de champ plat**

- Charge utile : `PAYLOAD_SET_SHUTTER(position=1)` OPEN, puis
  `PAYLOAD_CAL_LAMP(on=1)` — la lampe d'étalonnage **interne** ; il ne
  s'agit pas d'une acquisition au-dessus de l'océan.
- Vérification : `payload.cal_lamp_on` (0x0615) = 1 et
  `payload.shutter_pos` (0x063C) = 1.
- Charge utile : `PAYLOAD_START_CALIBRATION(mode=1)` — la phase FLAT.
- Vérification : `payload.cal_valid_mask` (0x0646) = 15 — les quatre
  bandes sont valides. Éteindre ensuite la lampe.
- L'ordre est libre : DARK puis FLAT ou FLAT puis DARK fonctionnent
  tous deux, et `PAYLOAD_START_CALIBRATION(mode=2)` exécute les deux en
  une seule commande.

**Étape 4 — Revenir en STANDBY et préparer le survol**

- Charge utile : `PAYLOAD_SET_MODE(mode=1)`,
  `PAYLOAD_SET_SHUTTER(position=1)`.
- AOCS : `AOCS_FINE_READY_CHECK` (S8 func 89) — confirmer
  `aocs.fine_ready` (0x02C5) = 0 — puis
  `AOCS_SET_MODE(mode=5)`, FINE_POINT.
- Vérification : `aocs.mode` (0x020F) = 5 en 30 s ;
  `aocs.att_error` (0x0217) < 0.1° en 300 s.
- « FD, Payload — calibration sets committed. GO COM-012. »

### COM-012 — Première lumière (la procédure phare)

#### Conduite étape par étape

**Étape 1 — GO du FD pour la première lumière**

- FD : « All positions, listen up. We're going for First Light.
  This is the customer-facing deliverable for Week 3. AOCS,
  pointing? »
- AOCS : « Mode 5 FINE_POINT, `aocs.total_pointing_err_3sig`
  (0x02AA) 0.020 deg, well inside the 0.05 deg imaging gate. »
- « FD: Thermal, FPA? »
- Thermique : « FPA at −15.2 C, in the −16.5 to −14.5 C band, and
  `payload.fpa_ready` (0x0610) reads 1. »
- « FD: Payload, cal frames? »
- Charge utile : « Dark and flat both taken, `cal_valid_mask` 15. »
- « FD: TT&C, downlink? »
- TT&C : « HIGH tier available above 10 degrees, margin 46 dB at
  TCA over Iqaluit. A 4 MiB product is 262 seconds of channel at
  128 kbps, 328 seconds with the protocol allowance — about
  three-quarters of the pass. »
- « FD: FDS, target? »
- FDS : « Target the Labrador Current outflow zone, scene centre
  52.5 N, 51.2 W. Footprint 273 km across-track by 59 km
  along-track for a 2048-line strip, 33.4 metre GSD. Sun glint
  angle 32 deg (acceptable), cloud cover 8 percent per latest
  forecast. »
- « FD: Ground Seg, downlink ready? »
- Segment sol : « All five stations configured; Iqaluit has the next
  pass and it clears 10 degrees, so the HIGH tier will hold. »
- « FD: Mission Manager, customer expecting this? »
- Responsable de mission : « Customer is watching the feed. Bulletin
  prepped. »
- « FD: GO FOR FIRST LIGHT. »

**Étape 2 — Capture**

- Charge utile : « FD, Payload — first-key `PAYLOAD_SET_MODE(mode=2)`,
  IMAGING. » Le FD valide en second. Vérifier `payload.mode` (0x0600) = 2
  en 30 s.
- Charge utile : « first-key `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` »
  (S8 func 28).
- (Au déclenchement) « FD, Payload — acquiring. »
- (8,4 s plus tard) « FD, Payload — strip complete. » La longueur de
  bande commandée vaut `lines / line_rate` = 2048 / 244 Hz =
  **8,4 secondes**, ce qui, à la vitesse de défilement de la trace au
  sol de 7,06 km/s, correspond à l'empreinte de 59 km le long de la
  trace annoncée par le FDS.
- La géolocalisation est horodatée **à bord** à partir des éphémérides
  à l'ouverture de l'obturateur ; ce n'est pas un champ commandé.

**Étape 3 — Vérifier le stockage de l'image**

- Charge utile : « FD, Payload — `payload.last_scene_id` (0x060C) reads 1,
  `payload.product_count` (0x0648) incremented, product size
  reported on `payload.product_mb` (0x0647). All four bands
  present, no CRC errors. »
- **Remarque sur la taille de l'image.** Le support de cours retient une
  image brute de 4 Mo (`image_size_mb`), alors que la géométrie du plan
  focal — 8192 px × 4 bandes × 12 bit × 2048 lignes — implique
  100,7 Mo. Cet écart est délibéré et documenté ; ce n'est pas une
  erreur à masquer : à 100,7 Mo, une image exigerait environ 1,75 heure
  de contact effectif au palier HIGH (128 kbps), soit quelque quatorze passages moyens, et aucun plan ne bouclerait jamais. À bord, le
  compresseur CCSDS-123 stocke de 1,0 à 2,7 Mo de l'image de 4 Mo selon
  le contenu de la scène.

**Étape 4 — Mettre en file pour la transmission au sol**

- Charge utile : « FD, Payload — first-key
  `S13_CREATE_TRANSFER(scene_id=1)` — Service 13, Subtype 1. »
  GO du FD.
- Vérification : la TM(13,2) renvoie l'identifiant de transfert, le
  nombre total de blocs et le **crc32 calculé par l'instrument sur le
  produit au moment de la capture**. Recalculer ce CRC au sol sur les
  blocs reçus : un produit corrompu ne concordera pas, et c'est ainsi
  qu'une image corrompue est diagnostiquée plutôt que devinée.
- Un transfert portant sur une scène absente du catalogue bord est
  **refusé** (erreur S1.8 0x0003 plus un NAK TM(13,4)). Utiliser
  `PAYLOAD_GET_IMAGE_CATALOG` (S8 func 32) pour voir ce qui se trouve
  réellement à bord.

**Étape 5 — Vérifier la réception au sol**

- Les blocs descendent avec `S13_DOWNLOAD_SEGMENT` (S13.3) et la
  session est close avec `S13_END_TRANSFER` (S13.5) ; l'avancement est
  interrogé avec `S13_REPORT_STATUS` (S13.9).
- (Passage suivant) Segment sol : « FD, Ground Seg — downlink complete,
  4 megabytes received in 262 seconds of channel at the HIGH tier,
  CRC matches the value the instrument reported at capture. »
- Noter que la clôture d'une session dont **tous** les blocs ont été
  envoyés supprime le produit à bord et libère son espace de stockage
  (événement 0x0614). Une session partielle ou interrompue laisse le
  produit en place — c'est exactement le cas « le passage a été perdu,
  nouveau vidage à l'orbite suivante » pour lequel le service existe.

**Étape 6 — Évaluation de la qualité**

- Charge utile : « FD, Payload — image quality assessment: mean DN
  per band 1840 / 2102 / 1654 / 891 on the 12-bit 0–4095 scale,
  contrast within expected range. `aocs.geoloc_err_m` (0x02C7)
  reads 180 metres at the 0.020 degree pointing error — about five
  ground pixels at 33.4 metre GSD. IMAGE IS SCIENCE USABLE. »
- Responsable de mission : « FD, MM — customer bulletin going out:
  EOSAT-1 First Light achieved at 14:32:18 UTC, target Labrador
  Current, downlink complete, science-usable image acquired. »

#### Points de décision

- **Étape 2 : `aocs.total_pointing_err_3sig` (0x02AA) dérive jusqu'à
  0.042 deg juste avant le déclenchement de la capture** — toujours
  sous le seuil de 0.05 deg, mais de justesse. Deux lectures
  possibles : reporter d'une orbite (rechercher une meilleure
  attitude) ; ou déclencher malgré tout (qualité d'image limite mais
  exploitable). Protocole des missions réelles : si la marge par rapport
  à la spécification est inférieure à 30 %, reporter. Ici,
  0.042 / 0.05 = 84 % du bilan consommé, soit 16 % de marge — reporter.
  Consulter 0x02C5 pendant l'attente : si le bit 1 est positionné, le
  satellite tient FINE sur trois roues (`aocs.fine_degraded` 0x0299 = 1)
  et le surcroît de gigue trouve une explication au lieu de rester
  mystérieux.
- **Étape 6 : l'évaluation de la qualité de l'image montre un DN moyen
  de 2900 dans la bande 443 (sursaturation)** — le temps d'intégration
  était trop long pour la luminance réelle de la scène. Le résultat est
  partiellement saturé. Décisions : déclarer la première lumière
  *acquise* (les données existent), mais la signaler pour une nouvelle
  acquisition au passage suivant avec une intégration plus courte. Le
  bulletin client dit la vérité : « Première lumière obtenue ; image
  partiellement saturée, nouvelle acquisition prévue. »

---

## 11.10 Références

- ECSS-E-ST-70-11C — *Space segment operability* (opérabilité du segment spatial) — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/)

# Chapitre 12 — Opérations de contingence

Les trois phases opérationnelles traitées jusqu'ici — passages
nominaux, LEOP et recette en orbite — partagent une propriété
déterminante : **vous savez ce qui vous attend.** Un passage nominal
déroule les procédures NOM-001 à NOM-013 dans un ordre écrit plusieurs
jours à l'avance. Un quart de LEOP suit un enchaînement de procédures
répété au simulateur jusqu'à ce que l'équipe puisse le réciter. La
recette en orbite est un scénario de quatre passages aux conditions
d'entrée et de sortie nommées. Le travail est exigeant, mais sa *forme*
est connue avant le début du passage.

Une contingence, c'est l'inverse. C'est le passage où survient quelque
chose qui n'était pas dans la chronologie. La compétence que développe
ce chapitre n'est pas « comment dérouler la procédure X » — celles-ci
figurent dans le catalogue (chapitre 14). C'est la compétence plus
générale qui consiste à bien réagir lorsque la situation à laquelle
vous faites face ne correspond à aucune fiche particulière dont vous
disposez.

## 12.1 Qu'est-ce qu'une contingence ?

Une contingence est toute situation dans laquelle l'équipe n'avait pas
prévu de se trouver à ce stade du passage : une règle FDIR se
déclenche alors qu'elle n'aurait pas dû, un paramètre de télémesure
sort de ses limites, une liaison est perdue, une roue sature trop tôt,
une charge apparaît sans que personne ne l'ait commandée. Le trait
distinctif n'est pas la gravité — une alerte FDIR de niveau 1 (caution) peut être une
contingence, alors qu'une répétition planifiée de passage en mode
survie n'en est pas une —, mais la *surprise*. L'équipe travaille
désormais hors scénario.

Voici le paradoxe apparent avec lequel vit toute organisation
d'exploitation, et que ce chapitre a pour objet de résoudre : **la
contingence réelle ne ressemble presque jamais exactement à celle pour
laquelle vous vous êtes entraîné, et pourtant c'est précisément le fait
d'entretenir un jeu complet de cas de contingence planifiés qui permet
de traiter celle que vous n'aviez pas prévue.** L'échelle de reprise
après perte de liaison que vous avez répétée n'anticipe pas la manière
précise dont *cette* liaison-ci tombe en panne ; la fiche de
sous-tension suppose un arbre de défaillances que la batterie réelle ne
suit pas. Et pourtant, l'opérateur qui a travaillé ces fiches retrouve
les bons réflexes en quelques secondes : mettre en sécurité le
sous-système touché, confirmer que le symptôme est réel, protéger
l'alimentation et l'attitude, parler sur la boucle, ne pas aggraver la
situation. Les cas planifiés n'ont pas de valeur parce que l'événement
réel leur ressemble. Ils en ont parce que leur répétition construit la
*structure de décision* — l'ordre des opérations, le réflexe de mettre
en sécurité avant de diagnostiquer, les automatismes des annonces —,
qui se transpose en bloc à une situation qu'aucune fiche ne décrit.

C'est pourquoi une équipe d'exploitation expérimentée conserve et
s'exerce sur un catalogue de contingences dont elle sait qu'elle ne
l'appliquera jamais à la lettre. Les fiches sont un outil de formation
autant qu'un manuel d'exploitation. Un opérateur qui a travaillé vingt
scénarios de contingence au simulateur n'a pas mémorisé vingt
solutions ; il a intériorisé une seule manière de penser les
difficultés, et cette manière de penser est générale.

## 12.2 L'état d'esprit face à la contingence et le cadre de décision

Lorsqu'un événement inattendu survient, les pires conséquences en
exploitation viennent non pas du défaut initial, mais de la réaction de
l'équipe — une commande précipitée qui aggrave le problème, un
diagnostic poursuivi pendant que la batterie se vide discrètement, une
reprise tentée avant que quiconque ait confirmé la réalité du symptôme.
Le cadre ci-dessous est le même quel que soit le sous-système concerné,
et il est volontairement ordonné. Son principe directeur est emprunté à
la médecine : *d'abord, ne pas nuire.* Chaque action doit être
réversible autant que possible et, en cas de doute sur la
réversibilité, la tendance doit être d'en faire moins, et non plus.

La première étape consiste à **reconnaître et confirmer**. L'indication
est-elle réelle, ou s'agit-il d'un artefact de télémesure — une trame
perdue isolée, un parasite de capteur, une valeur périmée conservée
depuis avant la LOS ? Recouper le paramètre suspect avec une source
indépendante : un second capteur, une grandeur dérivée, le compteur de
trames, la tendance plutôt que la valeur instantanée. Un nombre
étonnant d'« anomalies » s'évanouissent à cette étape. Confirmer coûte
quelques secondes ; réagir à un fantôme coûte le passage.

Une fois la réalité de la situation confirmée, la deuxième étape
consiste à **préserver le satellite**. Avant de comprendre *pourquoi*
quelque chose ne va pas, s'assurer que la situation ne peut pas
empirer. Mettre en sécurité le sous-système touché — passer une charge
utile défaillante en attente, interrompre une manœuvre, cesser
d'envoyer des commandes sur un défaut. Protéger les trois éléments qui
maintiennent le satellite en vie jusqu'à la prochaine éclipse et au
prochain trou de couverture : l'**alimentation** (la batterie se
vide-t-elle, une charge est-elle active sans avoir été commandée ?), la
**thermique** (des limites sont-elles approchées, les réchauffeurs
sont-ils disponibles ?) et l'**attitude** (le satellite tient-il son
pointage, les roues ou le pointage solaire sont-ils maîtrisés ?). La
préservation fait gagner du temps ; presque rien d'autre ne le fait.

Le satellite étant en sécurité, la troisième étape consiste à **isoler
la cause** : qu'est-ce qui a changé, et qu'est-ce qui est touché ? La
question de diagnostic la plus puissante en exploitation est : « Quelle
est la dernière chose que nous avons faite, et quelle est la dernière
chose que le satellite a faite de manière autonome ? » Corréler
l'apparition du symptôme avec l'historique des commandes, le journal
des événements FDIR, la géométrie orbitale (entrée en éclipse,
changement de station) et toute étape de procédure récente. Distinguer
le défaut *primaire* de ses *conséquences* — une sous-tension qui a
déclenché un délestage qui a coupé l'émetteur est un seul défaut à
trois symptômes, et non trois défauts.

La quatrième étape est la **décision** : reprendre maintenant, reporter
ou faire remonter. Reprendre maintenant si la cause est comprise, si la
reprise est prévue dans une fiche ou évidente, si le satellite est
stable et s'il reste assez de temps de passage pour vérifier le
résultat avant la LOS. Reporter si la situation est stable et bénigne
et si la reprise gagnerait à être menée avec une analyse, avec les
bonnes personnes ou lors d'un passage ultérieur — il n'y a aucun mérite
à réparer pendant ce passage ce qui peut attendre le suivant. Passer
en mode survie lorsque le satellite n'est pas stable, que la cause
n'est pas comprise ou que l'équipe manque de temps : le mode survie
n'est pas un échec des opérations, c'est le repli prévu dès la
conception, qui maintient le satellite en vie et pointé vers le Soleil
pendant que le sol traite le problème en différé. Seul le directeur de
vol autorise le passage en mode survie, et le responsable de mission en
est informé.

La cinquième étape se déroule en parallèle de toutes les autres :
**communiquer et consigner.** Chaque observation, hypothèse et action
est annoncée sur la boucle vocale au moment où elle se produit, selon
la discipline du chapitre 9 — annonces adressées, collationnements, GO
du FD avant toute action commandée. Chaque étape est horodatée dans la
main courante, et la fiche d'anomalie est ouverte immédiatement, et non
rédigée de mémoire après le passage. Une main courante propre est ce
qui permet au quart suivant, aux analystes et au constructeur de
reconstituer ce qui s'est passé.

## 12.3 Arbre de décision pour le traitement des anomalies

Le cadre du §12.2 correspond directement à la manière dont la FDIR
classe et oriente un événement sur le satellite de référence. L'arbre
de décision ci-dessous est l'expression opérationnelle de ce cadre : un
déclenchement autonome est classé selon sa gravité, et la gravité
détermine si l'équipe consigne et surveille, exécute une procédure de
reprise, ou traite l'événement comme un candidat au mode survie sur
lequel le directeur de vol doit statuer. Lisez-le comme l'étape
« décider » du §12.2 traduite en logigramme — la même logique
reconnaître, préserver, isoler, décider, indexée sur *la gravité de la
situation*.

**Deux échelles, et ce ne sont pas les mêmes.** EOSAT-1 signale une
**gravité FDIR** sur une échelle de **0 à 4** (0 rien, 1 INFO,
2 WARNING, 3 ALARM, 4 CRITICAL) et un **niveau d'autonomie** sur une
échelle de **0 à 3** (0 unité/matériel, 1 logiciel du sous-système,
2 application FDIR de l'OBC, 3 sol). La gravité indique à quel point la
situation est sérieuse ; le niveau d'autonomie indique qui est autorisé
à agir et avec quelle rapidité. L'arbre de décision ci-dessous est
indexé sur la **gravité**. Prendre une gravité pour un niveau
d'autonomie — ou l'inverse — est l'une des erreurs les plus tenaces en
console, car les deux nombres sont de petits entiers qui arrivent sur
le même panneau, et chacun est *plausible* à la place de l'autre.
Précisez à chaque fois, sur la boucle, duquel vous parlez.

![Arbre de décision pour le traitement des anomalies : un déclenchement FDIR est classé selon sa gravité (0 → simple consignation ; 1–2 → procédure de reprise ; 3–4 → candidat au mode survie, le directeur de vol autorisant le passage en mode survie ou ordonnant une procédure de reprise).](../assets/figures/fig_anomaly_decision_tree.svg)

*Arbre de décision pour le traitement des anomalies : un déclenchement FDIR est classé selon sa gravité (0 → simple consignation ; 1–2 → procédure de reprise ; 3–4 → candidat au mode survie, le directeur de vol autorisant le passage en mode survie ou ordonnant une procédure de reprise).*

Les plages de gravité sont ici les mêmes que celles du tableau de
l'échelle d'escalade FDIR (§15.4) : la gravité 0 est informative et
simplement consignée, les gravités 1–2 conduisent à une procédure de
reprise, et les gravités 3–4, sérieuses à critiques, font de
l'événement un candidat au mode survie. L'arbre décide du *type de
réponse* ; les fiches des §14.4 et §14.5 en fournissent les étapes. Le
niveau d'autonomie, signalé en parallèle, vous apprend encore autre
chose : si le satellite a déjà agi sans vous (niveaux 0–2) ou s'il
attend le sol (niveau 3).

## 12.4 Familles de contingences

Les contingences se regroupent en un petit nombre de familles. Un
opérateur qui reconnaît la famille à laquelle appartient une surprise a
déjà resserré la réponse, car chaque famille possède un geste de
préservation caractéristique et un ensemble de reprises prévues dans
des fiches. Les fiches de procédures de contingence se trouvent au
**chapitre 14, §14.4 (Fiches de procédures de contingence)** et les
fiches d'urgence — celles qui approchent du mode survie ou y font
entrer — au **§14.5 (Fiches de procédures d'urgence)**. Les familles
ci-dessous sont celles auxquelles un opérateur d'EOSAT-1 doit être
préparé.

**Perte des communications.** La liaison se dégrade ou est perdue :
`ttc.link_status` (0x0501) quitte la valeur **2 = LOCKED**,
`ttc.carrier_lock` (0x0510) ou `ttc.frame_sync` (0x0512) retombe à
zéro, le compteur de paquets TM cesse d'avancer, ou `ttc.ber` (0x050C)
augmente. Le premier geste de préservation consiste à confirmer que la
station sol poursuit toujours le satellite et que la géométrie permet
encore la liaison, avant de conclure à une panne bord. L'observation la
plus instructive est de savoir **si la balise UHF arrive toujours** : la
balise est un émetteur distinct, sur la ligne non commutable `ttc_rx` ;
la HK SID 11 survit donc à un PA bande S coupé, à une ligne `ttc_tx`
délestée, à un transpondeur en panne et à une antenne patch non
déployée. Balise présente mais bande S muette : le défaut est circonscrit
en une seule étape à la chaîne en bande S ; balise absente elle aussi :
le constat est bien plus grave. La réponse prévue dans les fiches suit
l'échelle de reprise après perte de liaison TTC — test passif de la
liaison, réduction du débit à LOW, augmentation de la puissance
d'émission autorisée par le FD —, avec escalade vers **EMG-004 Perte de
communication** seulement si aucun des échelons ne rétablit la
liaison. Le minuteur de perte de commande de 24 heures du satellite lui-même est
l'ultime filet de sécurité : si aucune télécommande valide n'arrive pendant 24 h,
le satellite bascule sur l'autre transpondeur (règle FDIR TTC-01 ; `cmd_loss_switch_timeout_s`
dans `ttc.yaml`). Le simulateur ne modélise pas encore ce basculement.

**Anomalies d'alimentation et de l'EPS.** Surintensité sur le bus,
sous-tension du bus ou charge non commandée. Le geste de préservation
consiste à protéger la batterie : délester d'abord les charges les moins
critiques et laisser la recharge en phase éclairée rétablir l'état de
charge, exactement comme le prévoit la procédure de délestage sur
sous-tension (CTG-001). L'ordre de délestage est fixe et doit être connu
par cœur : `payload` → `fpa_cooler` → `ttc_tx` → `aocs_wheels` → `prop`,
la propulsion venant volontairement en dernier, car couper cette ligne
en pleine poussée déclenche l'interruption bord de la poussée.
`eps.load_shed_stage` (0x0134) indique jusqu'où l'EPS est descendu dans
la liste. L'escalade passe par le délestage progressif (CTG-023) jusqu'à
**EMG-002 Perte totale d'alimentation** si la tension continue de
baisser. Les anomalies d'alimentation sont celles qui tolèrent le moins
le « diagnostiquer d'abord » — la batterie n'attend pas.

**Anomalies du SCAO et du pointage.** Saturation d'une roue de réaction,
panne d'un capteur (une tête de senseur solaire, un senseur stellaire ou
le magnétomètre), ou perte pure et simple de la connaissance ou du
contrôle de l'attitude. Le geste de préservation dépend du défaut : une
roue saturée exige une désaturation — et une désaturation est un
engagement de **20 à 50 minutes**, et non de cinq minutes ; elle se
planifie donc, elle ne s'improvise pas (§13.7). Un capteur en panne
exige de reconfigurer l'estimateur sur les capteurs survivants, au moyen
de `AOCS_EST_RESET` (S8 func 91) et de `aocs.est_source` (0x02C1),
plutôt que par une sélection manuelle des sources. La perte d'une roue
n'est généralement **pas** une urgence : FINE_POINT fonctionne sur trois
des quatre roues de la pyramide, ce que signale `aocs.fine_degraded`
(0x0299), et le bit de précondition de 0x02C5 qui bloque FINE signifie
« moins de **trois** roues », et non moins de quatre. Une véritable
perte d'attitude est un candidat au mode survie, car un satellite non
contrôlé menace l'alimentation et la thermique en quelques minutes. Le
mode survie en pointage solaire — COARSE_SUN, mode 3 — existe
précisément pour que, quoi qu'il arrive par ailleurs, les panneaux
fassent face au Soleil.

**Excursions thermiques.** Un sous-système dérive vers une limite de
température — le plus souvent l'ensemble plan focal de la charge utile
ou son refroidisseur. Le geste de préservation consiste à supprimer la
source de chaleur ou à rétablir la boucle de refroidissement et, si ni
l'un ni l'autre n'est immédiatement possible, à délester la charge en
cause. Les contingences thermiques évoluent généralement plus lentement
que les contingences d'alimentation, ce qui laisse le temps d'isoler la
cause, mais un refroidisseur qui s'emballe ou un réchauffeur bloqué
peuvent évoluer rapidement.

**Défauts de la charge utile.** L'instrument se comporte mal — il
n'entre pas dans un mode, renvoie des données corrompues, consomme une
puissance anormale ou ne refroidit pas. La charge utile étant critique
pour la mission mais pas pour la survie, le geste de préservation par
défaut est prudent : placer la charge utile dans un état d'attente sûr
et protéger la plateforme, puis enquêter. Une image perdue se rattrape à
l'orbite suivante ; un défaut de charge utile qui entraîne le bus dans
sa chute ne mérite pas d'être traqué en temps réel.

**Passages en mode survie déclenchés par la FDIR.** Le satellite a déjà
agi : une règle autonome l'a fait passer en mode survie, ou n'est plus
qu'à un déclenchement de le faire. C'est dans cette famille que les
deux échelles du §12.3 montrent toute leur utilité — la *gravité* vous
indique à quel point la situation sous-jacente était sérieuse, et le
*niveau d'autonomie* vous indique que la réponse vous a déjà échappé.
Ici, la contingence est en partie déjà traitée par conception, et le
rôle de l'équipe devient de confirmer que le passage en mode survie
était justifié, d'informer le responsable de mission, de préserver la
configuration et de *ne pas* tenter de sortir du mode survie au cours
du même passage. La reprise après un véritable passage en mode survie
est une activité en différé, impliquant plusieurs postes, sous
l'autorité explicite du FD et du responsable de mission.

## 12.5 Responsabilités de chaque poste en situation de contingence

Une contingence mobilise toute la salle, mais chaque poste y tient un
rôle distinct, tiré de sa mission permanente (chapitre 6). Ce qui change
en contingence, c'est le rythme et la discipline, et non la répartition
des responsabilités.

Le **directeur de vol** est maître de la décision. Le FD ralentit la
salle, impose la règle d'une seule action à la fois, accorde ou refuse
le GO pour chaque étape de reprise commandée, et est la seule voix qui
autorise le passage en mode survie. La tâche la plus difficile du FD
est de résister à l'envie de réparer vite ; en pratique, le cadre du
§12.2, c'est le FD qui maintient l'équipe dans la séquence
reconnaître-préserver-isoler-décider au lieu de sauter directement à
une solution.

Le **SPACON** déroule les procédures et tient la main courante. En
contingence, le SPACON charge la fiche de contingence ou d'urgence
appropriée, la déroule étape par étape sous le GO du FD, acquitte les
règles FDIR dans le bon ordre et ouvre immédiatement la fiche d'anomalie,
afin que la chronologie soit saisie au fil de l'eau plutôt que
reconstituée après coup.

L'opérateur **AOCS** protège l'attitude : il confirme que le satellite
tient toujours son pointage, surveille les vitesses de roue
(0x0207–0x020A, en lecture seule) et le moment cinétique du satellite
(`aocs.h_body_mag` 0x02B9), exécute les désaturations et est le premier
à signaler qu'un défaut fait d'une perte d'attitude un candidat au mode
survie. L'opérateur **EPS** protège l'alimentation : il surveille la
tension du bus et l'état de charge, exécute les délestages et annonce le
seuil à partir duquel l'équipe doit s'engager dans une urgence
d'alimentation. L'opérateur **Thermique** surveille les tendances de
température du sous-système touché, gère les réchauffeurs et le
refroidisseur, et indique si une charge peut rester alimentée ou doit
être délestée.

L'opérateur **TT&C** est responsable de la liaison : il établit si un
problème se situe sur la liaison ou sur le satellite, suit l'échelle de
reprise après perte de liaison et protège la capacité même à commander —
sans liaison, aucune reprise n'est possible. L'opérateur **Charge
utile** met l'instrument en sécurité et rend compte de son état, en
indiquant au FD ce qui peut être récupéré des données scientifiques et
ce qui est perdu. L'opérateur **FDS / dynamique du vol** fournit le
contexte orbital et géométrique — début de l'éclipse, lever de la
prochaine station, implication éventuelle d'une manœuvre — afin que les
décisions de l'équipe tiennent compte du temps et de la visibilité dont
elle dispose réellement.

L'opérateur **Segment sol** confirme que le sol est en bon état et
n'est pas la cause, exécute le basculement de station ou d'équipement
si c'est le cas, et maintient le chemin des données. Le **responsable
de mission** se situe au-dessus de la console : il est informé de chaque
contingence, consulté sur le passage en mode survie, maître du discours
tenu au client, et c'est lui qui décide si l'anomalie modifie le plan de
mission.

## 12.6 Quand la contingence est une situation que vous n'aviez pas prévue

Tôt ou tard, un passage produit une situation sans fiche
correspondante. La réponse n'est pas d'improviser librement ; elle
consiste à raisonner à partir du cadre et de la procédure planifiée la
*plus proche par analogie*. Demandez-vous à quelle famille (§12.4) le
symptôme ressemble le plus, et reprenez le geste de préservation de
cette famille même si le diagnostic est incertain — une chute de
tension inexpliquée est traitée comme une contingence d'alimentation et
reçoit un délestage prudent, une dérive de pointage inexpliquée est
traitée comme une contingence SCAO et l'estimateur est surveillé, car
les gestes de préservation sont sûrs par construction. Raisonnez
ensuite à partir des premiers principes sur la télémesure réelle :
qu'est-ce qui doit physiquement être vrai pour que le satellite montre
cela, et quelle est l'action la moins irréversible qui permette de
tester l'hypothèse principale ?

Deux partis pris servent bien l'opérateur lorsque la situation est
réellement nouvelle. Le premier consiste à **privilégier la mise en
sécurité et l'escalade** en cas d'incertitude : un satellite en mode
survie est un satellite que vous avez encore, et le coût d'un passage
inutile en mode survie se compte en heures de reprise, alors que celui
d'un passage tardif peut être la mission. Le second consiste à
**préférer l'action réversible** : attendre et observer avant de
commander, commander le plus petit pas qui apporte de l'information, et
ne jamais envoyer une commande dont vous ne pouvez pas annuler l'effet
tant que la cause reste inconnue. C'est exactement pour cela que les
cas planifiés comptent (§12.1) : ils sont la répétition qui rend ces
réflexes automatiques le jour où l'événement réel, jamais répété,
survient enfin.

## 12.7 Références

- ECSS-E-ST-70-11C — *Space segment operability* (opérabilité du segment spatial) — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/)
- ECSS-Q-ST-30C — *Dependability* (principes de FDIR et de tolérance aux pannes).
- ISO 17666 / ECSS-M-ST-80C — *Risk management*, appliquée au traitement des anomalies en vol.
- Fiches de procédures de contingence et d'urgence : chapitre 14, §14.4 (Contingence) et §14.5 (Urgence) ; échelle d'escalade FDIR, §15.4.

---

# Chapitre 13 — Calculs et contrôles de l'opérateur

****

Ce chapitre couvre les calculs et contrôles que tout opérateur en
console doit savoir effectuer — sans script, sans le panneau de
planification, avec un crayon et le dos de la main courante. Il s'agit
des *calculs de travail de l'opérateur*, distincts des analyses de
dynamique du vol que produit le FDS.

Six familles de calculs d'opérateur sont traitées :

Tableau 13.1 — Six familles de calculs d'opérateur, avec l'événement qui déclenche chacune.

| § | Famille | Quand l'effectuer |
|---|---|---|
| 13.2 | Arithmétique des horaires de passage — prédiction des AOS / TCA / LOS | À chaque briefing avant passage |
| 13.3 | Prédiction du SoC en sortie d'éclipse | À chaque passage traversant une éclipse |
| 13.4 | Bilan de pointage en RSS | Avant chaque séance de prise de vue |
| 13.5 | Analyse des lacunes de la TM différée | Lorsqu'une séquence de paquets TM présente un saut |
| 13.6 | Contrôle de vraisemblance de la marge de liaison | Lorsque la liaison se dégrade de manière inattendue |
| 13.7 | Planification de la désaturation en cas de saturation d'une roue | Lorsqu'une roue dépasse 75 % de sa vitesse limite |

Pour chacune : la formule, un exemple résolu, les plages typiques
(pour savoir quand un résultat est faux) et les conséquences
opérationnelles d'une erreur.

## 13.2 Arithmétique des horaires de passage

Pour une orbite circulaire à l'altitude $h$ au-dessus d'une station sol
de latitude géodésique $\phi_{gs}$, la **durée géométrique de transit
de l'AOS à la LOS** à l'élévation maximale (passage au zénith) vaut

$$ t_{transit} = \frac{T_{orbit}}{\pi} \arccos\!\left(\frac{R_E + h_{station}}{R_E + h_{sat}}\right) $$

**La période orbitale.** Le TLE d'EOSAT-1 indique un moyen mouvement de
15,24 tours par jour, donc

$$ T_{orbit} = \frac{86400}{15.24} = 5669\ \text{s} = 94.5\ \text{min} $$

**Exemple résolu — d'horizon à horizon.** Avec $R_E = 6371$ km et
$h = 513$ km, $\frac{R_E}{R_E+h} = \frac{6371}{6884} = 0.92548$, et
$\arccos(0.92548) = 22.26° = 0.38850$ rad. Donc

$$ t_{transit} = \frac{5669}{\pi}\times 0.38850 = 1804.5\times 0.38850 = 701\ \text{s} = 11.7\ \text{min} $$

**Avec le masque d'élévation de 5°** — celui qu'utilisent réellement
les cinq stations —, le demi-angle utile vaut

$$ \gamma = \arccos\!\left(\frac{R_E\cos\varepsilon}{R_E+h}\right) - \varepsilon
        = \arccos(0.92196) - 5° = 22.79° - 5° = 17.79° $$

$$ t_{contact} = \frac{2\gamma}{360°}\,T_{orbit} = \frac{35.57}{360}\times 5669 = 560\ \text{s} = 9.3\ \text{min} $$

C'est le **maximum au zénith**, et il concorde avec le plus long
passage mesuré de la mission, 565 s (l'altitude varie entre 503 et 530 km
au fil de l'orbite). Les passages réels ne sont, pour la
plupart, pas au zénith : la **durée moyenne mesurée d'un passage sur le
réseau de cinq stations est de 450 s (7,5 min)**. Quiconque annonce un
passage utile de onze minutes cite la valeur géométrique d'horizon à
horizon et a oublié le masque.

**Statistiques de réseau à connaître sans avoir à les chercher.** Le
référentiel pédagogique est le **réseau complet de cinq stations** —
Iqaluit, Troll, Svalbard, Inuvik et O'Higgins, toutes polaires, toutes
avec un masque de 5°. Mesures sur 48 h à partir de l'époque de la
mission :

| Réseau | Passages / jour | Écart médian | Écart max. |
|---|---|---|---|
| Iqaluit + Troll seules | 20,0 | 84 min | 147 min |
| **Les cinq stations** | **≈ 51** | **33 min** | **79 min** |

Cela représente environ 23 200 secondes de contact par jour, soit
environ 27 % du temps. Tous les exercices de planification de ce
manuel supposent les valeurs du réseau de cinq stations.

**Règle de travail de l'opérateur.** Avant chaque briefing avant
passage, lire l'entrée du planning de contacts et confirmer que :

1. l'heure d'AOS est dans le futur (et non dans le passé — le planning
   est parfois périmé d'une orbite) ;
2. l'élévation maximale est > 10°. Il ne s'agit pas de marge de liaison
   — la marge boucle avec des dizaines de dB même à 5° —, mais du fait
   que le **palier HIGH est conditionné à 10°** : un passage qui ne
   dépasse jamais 10° ne peut donc porter aucun vidage d'image ;
3. la durée du passage est dans la norme : 7 à 9,3 min pour un bon
   passage, 4 à 6 min pour un passage bas. Une durée annoncée supérieure
   à environ 9,5 min à cette altitude et avec ce masque est
   arithmétiquement impossible et signifie que le planning est faux.

## 13.3 Prédiction de l'état de charge en sortie d'éclipse

Pendant l'éclipse, la batterie se décharge à peu près à la puissance
moyenne $P_{avg}$ consommée sur l'orbite. Le SoC en sortie d'éclipse
vaut

$$ SoC_{exit} = SoC_{entry} - \frac{P_{avg} \cdot t_{eclipse}}{E_{battery}} \cdot 100\% $$

avec $P_{avg}$ en W, $t_{eclipse}$ en heures et $E_{battery}$ en Wh.

**Les trois grandeurs à y introduire.**

- $E_{battery} = 100$ **Wh**. La batterie est une GomSpace NanoPower BPX
  8S-1P : 100 Wh, 3 Ah, 28,8 V nominaux, environ 500 g. Un seul
  boîtier, un composant de vol réel.
- $t_{eclipse}$. L'orbite dure 5669 s et la fraction d'éclipse varie, sur
  l'année de l'orbite à 10 h 00, **de 0,351 à 0,372** ; l'éclipse dure
  donc **de 33,2 à 35,2 min**. Prendre 34 min = 0,567 h comme valeur de travail.
- $P_{avg} = 28.8$ **W**, la charge moyenne sur l'orbite dans le profil
  nominal. Il s'agit d'un **CubeSat 6U** : 6 W pour l'OBC et la PDU,
  1,5 W pour la chaîne de réception toujours alimentée, 5 W
  d'émetteur sur le palier LOW (11 W en HIGH), 9 W de SCAO en NOMINAL,
  2,4 W de charge utile en attente, 15 W de refroidisseur lorsqu'il
  fonctionne. Rien sur ce satellite ne consomme 70 W.

**Exemple résolu.** SoC à l'entrée en éclipse = 85 % ; $P_{avg} = 28.8$ W ;
$t_{eclipse} = 34$ min $= 0.567$ h ; $E_{battery} = 100$ Wh :

$$ SoC_{exit} = 85\% - \frac{28.8 \times 0.567}{100}\times 100\%
  = 85\% - 16.3\% = 68.7\% $$

Cela représente **16,3 Wh prélevés sur une batterie de 100 Wh**, soit un
rythme de décharge d'environ **0,48 %/min**. Vérifiez-le dans l'autre
sens : 28,8 W pendant 0,567 h font 16,3 Wh, et 16,3 / 100 = 16,3 %. Si
votre résultat n'est pas un pourcentage d'environ quinze pour une orbite
nominale, vous avez utilisé la mauvaise charge ou la mauvaise batterie.

**Le même calcul dans le cas extrême.** Prenons le profil `worst`
— FINE maintenu toute l'orbite, refroidisseur en marche continue, prise
de vue pendant l'éclipse, vidages en palier HIGH à chaque passage — à
46,8 W sur une éclipse de 35,2 min (0,587 h) : $46.8 \times 0.587 = 27.5$ Wh ;
le SoC baisse donc de 27,5 points, de 85 % à 57,5 %. C'est encore
survivable sur une orbite, mais ce profil est déficitaire en production
sur l'ensemble de l'orbite (45,1 W produits contre 46,8 W consommés) :
il ne se rétablit donc pas, et chaque orbite commence plus bas que la
précédente. C'est le profil type d'un bilan de puissance qui ne boucle
pas.

**Plage typique.** En exploitation nominale, le SoC en sortie d'éclipse
doit se situer **entre 65 et 80 %**. En dessous de 55 %, le profil de
charge en éclipse était faux ou il existe une charge parasite — ouvrir
une fiche. L'échelle de protection située en dessous est monotone et
mérite d'être mémorisée dans l'ordre : délestage dans le modèle à
**25,0 V** de tension bus (environ 45 % de SoC), FDIR `safe_mode_eps` à
**24,5 V** (environ 39 %), puis les paliers de délestage déclenchés par
le SoC à **30 / 20 / 10 %**, avec mise hors tension de la charge utile à
20 % et mode survie de l'EPS à 15 %. Le rôle de l'opérateur est
d'anticiper le premier de ces seuils, et non de regarder les protections
se déclencher.

## 13.4 Bilan de pointage en RSS

Les composantes de l'erreur de pointage sont statistiquement
indépendantes et se combinent en somme quadratique (RSS) :

$$ \theta_{total} = \sqrt{\theta_{ST,NEA}^2 + \theta_{ST,bias}^2 + \theta_{align}^2 + \theta_{control}^2} $$

Le satellite fait ce calcul pour vous et publie le résultat dans
`aocs.total_pointing_err_3sig` (**0x02AA**), sous la forme de la RSS
d'un terme de *connaissance* (`aocs.knowledge_err_3sig`, 0x02A7, en
**secondes d'arc**, issu de la covariance du MEKF) et d'un terme de
*contrôle* (`aocs.control_err`, 0x02A8, en **degrés**). Refaire le
calcul à la main permet de vérifier que la valeur publiée est crédible
— et de savoir quel terme traquer lorsqu'elle ne l'est pas.

**Les contributions du matériel.** Le senseur stellaire est un
nano-senseur de classe Blue Canyon NST : angle équivalent au bruit de
**6″ à 1σ** perpendiculairement à l'axe de visée (40″ autour de l'axe de
visée), biais thermoélastique basse fréquence de **3″ à 1σ**, défaut
d'alignement de montage de **15″**. Il y en a deux (ST1/ST2),
sélectionnés avec `ST_SELECT` (S8 func 6). Les gyromètres forment un
triplet de qualité tactique — ARW de 0,06°/√h, instabilité de biais
d'environ 0,1°/h — **sans unité redondante**, et leur biais est étalonné
**à bord** (`AOCS_GYRO_CALIBRATION`, S8 func 13).

**Exemple résolu (FINE_POINT, par axe, 3σ).**

| Terme | 1σ / biais | 3σ, degrés | Carré |
|---|---|---|---|
| Angle équivalent au bruit du ST, perpendiculaire à l'axe de visée | 6″ | 18″ = 0,0050° | 2,500 × 10⁻⁵ |
| Biais thermoélastique du ST | 3″ | 9″ = 0,0025° | 6,250 × 10⁻⁶ |
| Défaut d'alignement de montage | 15″ | 15″ = 0,0042° | 1,764 × 10⁻⁵ |
| Erreur de contrôle, FINE mesuré sur 3 roues | — | 0,0188° | 3,534 × 10⁻⁴ |
| **Somme** | | | **4,023 × 10⁻⁴** |

$$ \theta_{total} = \sqrt{4.023\times10^{-4}} = 0.0201° \approx 0.020° $$

Par rapport au **seuil de 0.05°** que COM-012 impose sur 0x02AA, il
reste 60 % du bilan disponible. Notez où passe réellement le bilan : le
terme de contrôle représente 88 % de la somme, et toute la chaîne du
senseur stellaire est presque négligeable. **Traquer l'erreur des
capteurs alors que le terme de contrôle domine, c'est gaspiller du temps
de passage.**

**Convertir en mètres.** Le satellite publie
`aocs.geoloc_err_m` (0x02C7) = altitude × erreur de pointage totale :

$$ 513\ \text{km} \times 0.0201° \times \frac{\pi}{180} = 513000 \times 3.51\times10^{-4} = 180\ \text{m} $$

— soit environ cinq pixels au sol pour la distance d'échantillonnage au sol (GSD) de 33,4 m de
l'instrument. Au seuil de 0.05°, elle atteindrait 448 m, soit environ
treize pixels.

**Règle de travail de l'opérateur.** Avant de commander
`AOCS_SET_MODE(mode=5)` pour une prise de vue, exécuter
`AOCS_FINE_READY_CHECK` (S8 func 89) et confirmer que
`aocs.fine_ready` (0x02C5) vaut **0**. Décomposer ensuite 0x02AA en
0x02A7 et 0x02A8. Si le terme de connaissance est le plus grand des
deux, l'estimateur présente un problème — vérifier `aocs.est_source`
(0x02C1) et `aocs.est_innov_rej_count` (0x02C2) —, car sur un satellite
en bonne santé le terme de contrôle domine d'un ordre de grandeur. Si le
bit 1 de 0x02C5 est positionné avec `aocs.fine_degraded`
(0x0299) = 1, vous tenez FINE sur **trois** roues : c'est autorisé et
cela tient 0,0188° contre 0,0208° sur quatre, mais la bande morte de
contrôle est quadruplée et la gigue à court terme est plus forte. Trois
roues, c'est un mode dégradé, pas une panne ; deux roues, c'est une
panne.

## 13.5 Analyse des lacunes de la TM différée

Les paquets de télémesure portent un compteur de séquence (en-tête de
paquet CCSDS, compteur sur 14 bits). Des sauts dans la séquence
signalent des paquets perdus — généralement à cause de la qualité de la
liaison, parfois à cause d'un débordement du stockage bord.

**Règle de travail de l'opérateur.** Lorsque le SPACON voit le compteur
d'acceptation des TC s'incrémenter alors que le rapport de fin
d'exécution S1.7 correspondant manque depuis plus de 15 s, vérifier :

1. `obdh.tm_pkt_count` (0x0307) s'incrémente-t-il, et
   `ttc.frame_sync` (0x0512) indique-t-il toujours 1 ? Sinon → la
   liaison est entièrement perdue, et non simplement retardée. Lancer
   CTG-003 Rétablissement après perte de liaison TTC. Vérifier d'abord
   la balise UHF : si le SID 11 arrive toujours, le défaut se situe dans
   la chaîne en bande S et non dans le satellite.
2. Comparer le compteur de séquence S1 *attendu* au compteur *reçu*.
   Les compteurs de séquence sont sur 14 bits et reviennent à zéro après
   16 384.
3. La taille de la lacune indique le nombre de paquets perdus. Si elle
   est < 5 paquets, il s'agit de l'évanouissement normal de fin de
   passage — consigner et poursuivre. Si elle est > 20, la liaison s'est
   dégradée en cours de passage ; examiner la tendance de `ttc.ber`
   (0x050C, échelle log₁₀) et de `ttc.rssi` (0x0502).
4. La plupart des TM manquées peuvent être récupérées en demandant, au
   passage suivant, une **relecture de la TM différée** depuis le
   stockage bord. Il s'agit de **`DUMP_STORE(store_id=1)` — service PUS
   15, sous-type 9** —, précédé de `STORE_STATUS` (S15.13) pour voir
   d'abord ce qui est stocké. Le service 15 est le stockage de la
   télémesure ; le service 13 est le transfert de gros volumes de
   données utilisé pour les *produits image*, un mécanisme entièrement
   différent. Programmer la relecture sur un passage qui dépasse 10° pour
   qu'elle s'effectue sur le palier HIGH : une orbite entière de
   télémesure de servitude enregistrée représente environ 1,1 Mo, soit
   70 s à 128 kbit/s, mais 9 minutes — plus qu'un passage — à
   16 kbit/s.

**Exemple résolu d'interprétation d'un tracé de TM différée.** Un tracé
typique de `seq_count` en fonction du temps bord montre :

- une rampe montante rectiligne (compteurs croissant de façon
  monotone) ;
- de légères irrégularités de la pente lorsque le débit de paquets
  varie entre des SID de servitude aux périodes de rapport différentes.
  Les cadences fournies sont **SID 1 (EPS) à 1 s**, SID 2 (AOCS) et
  SID 7 (détermination AOCS) à 4 s, SID 4 (plateforme), 5 (charge
  utile), 6 (TT&C), 8 (EPS étendu) et 9 (PROP) à 8 s, **SID 3 (TCS) à
  60 s**, et **SID 11 (balise) à 30 s**. L'EPS à 1 s domine le débit de
  paquets, ce qui explique pourquoi une lacune riche en paquets EPS
  paraît tellement plus large qu'une lacune riche en paquets TCS pour la
  même interruption en temps réel ;
- rappelons que seuls les SID **1 et 11** sont activés à la mise sous
  tension, et que le moteur réapplique exactement cet ensemble à
  l'amorçage du logiciel applicatif. Tout le reste nécessite `HK_ENABLE`
  (**S3.5**). Une « lacune » qui se révèle être un SID que personne n'a
  jamais activé n'est pas un problème de liaison ;
- un saut discontinu au point de retour à zéro (16383 → 0) — il ne
  s'agit *pas* d'une lacune, simplement d'arithmétique modulaire.

Une véritable lacune se présente comme un *palier* (aucun compteur
reçu), suivi d'un saut du compteur à la reprise de la réception. La
largeur du palier (en temps) est la durée de la lacune ; la différence
de compteur de part et d'autre du palier est le nombre de paquets
perdus.

## 13.6 Contrôle de vraisemblance de la marge de liaison

Marge de liaison disponible (dB) d'après la forme aide-mémoire du bilan
de liaison :

$$ M_{dB} = EIRP_{dBW} + G/T_{dB/K} + 228.6 - FSPL_{dB} - L_{atm} - L_{pol} - L_{impl} - 10\log_{10}(R_b) - \left[(E_b/N_0)_{req} - G_{coding}\right] $$

avec $228.6 = -10\log_{10}(k_B)$ et $R_b$ en bit/s. Le modèle fourni ne
comporte pas de terme distinct de perte de dépointage ; les pertes qu'il
retient sont l'affaiblissement atmosphérique de 0,5 dB, la perte de
polarisation de 0,3 dB et la perte d'implémentation de 2,0 dB.

**Les constantes, tirées de `subsystems/ttc.yaml` :**

- Liaison descendante à 2200 MHz, liaison montante à 2025 MHz.
- PIRE du satellite de **10,0 dBW** en référence plus **3,0 dBi** de gain
  d'antenne → **13,0 dBW**, pour 2 W RF. C'est aussi la radio que décrit
  le bilan de puissance : un émetteur-récepteur bande S de classe
  Endurosat, de 24 à 33 dBm en sortie, 1,2 W au repos, 11 W continus en
  pleine émission. **Il n'y a pas d'émetteur de 20 W sur ce
  satellite** — 20 W ne correspondent ni à une puissance RF que
  fournirait un amplificateur de CubeSat, ni à une consommation continue
  d'une radio de CubeSat.
- $E_b/N_0$ requis de **9,6 dB sans codage**, diminué du gain de codage
  du palier : 7,5 dB en LOW (convolutif + Reed-Solomon), 6,0 dB en HIGH
  (RS seul).
- G/T des stations : Svalbard 21,5, Inuvik 22,0, Iqaluit 20,0,
  O'Higgins 20,0, Troll 18,5 dB/K, avec un déclassement de 0,5 dB
  sous 30° d'élévation et de 1,5 dB sous 10°.

**Exemple résolu — Iqaluit, 30° d'élévation, palier LOW.**

D'abord la distance oblique :

$$ d = -R_E\sin\varepsilon + \sqrt{(R_E\sin\varepsilon)^2 + 2R_Eh + h^2}
     = -3185.5 + \sqrt{1.0147{\times}10^7 + 5.734{\times}10^6 + 2.025{\times}10^5} = 825\ \text{km} $$

$$ FSPL = 92.45 + 20\log_{10}(825) + 20\log_{10}(2.2) = 92.45 + 58.33 + 6.85 = 157.63\ \text{dB} $$

$$ M_{LOW} = 13.0 + 20.0 + 228.6 - 157.63 - 0.5 - 0.3 - 2.0 - 10\log_{10}(16000) - (9.6 - 7.5) $$
$$ = 261.6 - 157.63 - 2.8 - 42.04 - 2.1 = \mathbf{57.0\ dB} $$

**Même géométrie, palier HIGH.** Seuls deux termes changent — le débit
et le gain de codage :

$$ M_{HIGH} = 261.6 - 157.63 - 2.8 - 10\log_{10}(128000) - (9.6 - 6.0) $$
$$ = 261.6 - 157.63 - 2.8 - 51.07 - 3.6 = \mathbf{46.5\ dB} $$

**L'écart entre les échelons** vaut donc
$57.0 - 46.5 = \mathbf{10.5\ dB}$, et il se décompose exactement :
$-10\log_{10}(8) = -9.03$ dB pour le débit multiplié par 8, plus
$-1.5$ dB pour le changement de codage. L'écart BEACON→LOW vaut
$-10\log_{10}(16) = -12.04$ dB. **Tout jeu de mesures qui ne montre pas
ces deux écarts révèle une erreur de modélisation, et non un problème
de liaison.**

**Ce que signifient les chiffres.** Le pire cas de toute la matrice
station × élévation × palier est **HIGH à Troll à 5°, et il vaut
33,7 dB.** Cette liaison n'est limitée en puissance nulle part, pour
aucune station et dans aucune géométrie. Deux conséquences qu'un
opérateur doit intérioriser :

1. Les seuils de 3 dB et 6 dB des procédures sont des seuils de
   **vraisemblance**. Une mesure proche de ces valeurs ne signifie pas
   que la géométrie est limite ; elle signifie que le modèle, l'attitude
   ou la station sol est défaillant. Traiter une marge à un seul chiffre
   comme une alarme d'équipement, et non comme un compte rendu de
   liaison.
2. La condition de 10° sur le palier HIGH est une condition de
   **politique d'exploitation**, et non une condition de marge. HIGH
   boucle avec 33,7 dB à 5°. Il est refusé sous 10° parce que la
   transmission massive au sol est une activité planifiée, qui se
   mérite, et parce que la poursuite, la vitesse de variation du Doppler
   et les trajets multiples à basse élévation font d'un vidage QPSK à
   64 kBd un pari risqué.

**Règle de travail de l'opérateur.** Lorsque le poste TT&C annonce une
marge sur la boucle, la confronter au tableau de référence établi lors
de COM-006 :

1. Marge prédite pour la station, le palier et l'élévation en cours —
   p. ex. 57 dB, Iqaluit, LOW, 30°.
2. Marge réelle lue dans `ttc.link_margin` (0x0503).
3. Un écart de 1–2 dB relève de la variation normale. Un écart > 3 dB
   justifie un diagnostic avant la LOS.
4. Causes probables : dégradation de l'antenne sol (appeler le segment
   sol) ; baisse de la puissance d'émission commandée — vérifier
   `ttc.tx_fwd_power` (0x050D, dBm) et la valeur courante de
   `ttc.eirp_dbw` (0x052C), **et non** `ttc.carrier_lock` (0x0510),
   qui est un simple indicateur 0/1 ; dépointage d'attitude réduisant
   le gain d'antenne ; scintillation ionosphérique (un problème en UHF,
   rare en bande S).
5. Si la puissance incidente est nulle, vérifier `ttc.tx_active` (0x0525)
   et `ttc.tx_gate_status` (0x052B) avant de soupçonner le matériel —
   la chaîne n'a peut-être tout simplement pas l'autorisation d'émettre.

### 13.6.1 Arithmétique des volumes de données

La liaison n'étant pas limitée en puissance, la contrainte dimensionnante
est le **temps**, et c'est ce que l'opérateur doit réellement calculer.

**Une image.** Une image brute de 4 Mio représente $4 \times 1024^2 \times 8 =
33\,554\,432$ bits.

| | En HIGH (128 kbit/s) | En LOW (16 kbit/s) |
|---|---|---|
| Temps de canal brut | **262,1 s** | 2097 s |
| Avec la provision protocolaire de 20 % du planificateur | **327,7 s** | 2621 s |
| En fraction du passage moyen de 450 s | **73 %** | 582 % |

Une image occupe donc la majeure partie d'un passage, et l'activité
`data_dump` fournie dure **330 s** — une image, arrondie à l'excès, et
rien de plus. $n$ images exigent $n$ vidages. **En LOW, une image exige
plus d'un passage entier : la prise de vue n'est pas simplement plus
lente en LOW, elle est impossible.**

**La télémesure de servitude n'est pas gratuite.** L'ensemble HK fourni
génère 1378,5 bit/s de paquets PUS, soit **1588 bit/s sur le canal**
après RS(255,223) et la mise en trames TM — 134,5 Mbit, ou
**16,0 Mio, par jour**. Pour environ 23 300 s de contact quotidien :

| Palier | Temps de contact nécessaire / jour | Part du réseau |
|---|---|---|
| LOW (16 kbit/s) | 8410 s | **36 %** |
| HIGH (128 kbit/s) | 1051 s | 4,5 % |

Trente-six pour cent de l'ensemble du réseau de cinq stations, avant
même la première image. C'est le chiffre qui justifie que le palier LOW
soit à 16 kbit/s plutôt qu'à 8, et celui qui empêche un étudiant de
considérer la télémesure de servitude comme gratuite.

**Capacité quotidienne, pour fixer les idées :** le chiffre brut est
23 300 s × 128 kbps ≈ 355 Mio/jour ; en en retenant environ 64 % comme utilisable, on obtient
environ 227 Mio/jour si
chaque seconde de contact utilisable se faisait en HIGH, environ
28 Mio/jour si tout se faisait en LOW, et **environ 162 Mio/jour** pour
le mélange réaliste (HIGH au-dessus du seuil de 10°, LOW en dessous).
Face à 8–34 Mo/jour de données produites, la mission dispose d'une marge
— mais uniquement parce que les vidages sont programmés sur des passages
qui dépassent ce seuil.

**Géométrie de l'instrument, puisqu'on la demandera au FDS.** L'imageur
est un imageur multispectral à balayage de type « pushbroom » à grand
champ : 8192 px en travers de la trace au pas de 5,5 µm, pour une
focale de 84,5 mm, ce qui donne un champ total de 29,856°, une
**fauchée de 273 km** et une **distance d'échantillonnage au sol (GSD) de 33,4 m** depuis
513 km. La capture standard est une **bande de 2048 lignes** :

$$ \frac{2048\ \text{lignes}}{244\ \text{Hz}} = 8.4\ \text{s de balayage} $$

ce qui, à la vitesse de défilement de la trace au sol de 7,06 km/s,
donne **59 km le long de la trace**. Le second calcul ne concorde pas :

$$ 2048 \times 33.4\ \text{m} = 68.4\ \text{km le long de la trace} $$

car la cadence de lignes de 244 Hz a été dimensionnée à l'ancienne altitude
de 450 km (7,14 km/s ÷ 29,3 m). À 513 km, deux lignes successives sont
espacées de 28,9 m le long de la trace pour un pixel de 33,4 m en travers
de la trace : l'image est donc légèrement suréchantillonnée le long de la
trace ; une cadence adaptée à la vitesse serait d'environ 211 Hz.
`payload.yaml` consigne cette incohérence connue. Effectuer les deux calculs
reste le contrôle à faire : ici, il indique que l'empreinte à annoncer est
de 59 km. La lecture du plan focal se fait à
96 Mbit/s ($8192 \times 4\ \text{bandes} \times 12\ \text{bit}
\times 244\ \text{Hz}$) ; l'image brute physique fait donc 100,7 Mo. Le
support de cours utilise à la place **4 Mo** pour `image_size_mb`,
délibérément et ouvertement : à 100,7 Mo, une image exigerait environ
1,75 h de contact effectif au palier HIGH (environ 2,2 h avec la marge protocolaire de 20 %) et aucun plan ne bouclerait jamais. Ne
« corrigez » pas cet écart ; sachez qu'il existe.

## 13.7 Planification de la désaturation en cas de saturation des roues

Le moment cinétique stocké dans une roue de réaction vaut $H = I_{wheel}\,\omega$.
EOSAT-1 emporte quatre roues **de classe Sinclair RW-0.03** en pyramide
(azimuts 45/135/225/315°, élévation de 30° au-dessus du plan XY), avec
$I_{wheel} = 5.2\times10^{-5}$ kg·m² et $\omega_{max} = 5500$ tr/min :

$$ \omega_{max} = 5500 \times \frac{2\pi}{60} = 576.0\ \text{rad/s} $$

$$ H_{max} = 5.2\times10^{-5} \times 576.0 = 0.0300\ \text{N·m·s} = \mathbf{30\ mN·m·s} $$

ce qui correspond exactement à la capacité de stockage de moment
cinétique de la fiche technique — l'inertie du rotor en a été déduite,
si bien que les deux concordent par construction. Les roues étant en
pyramide, la capacité *selon les axes satellite* est supérieure à celle
d'une roue : $2\cos30°\cos45°\,H \approx 0.037$ N·m·s autour de X et
de Y, et $2H = 0.060$ N·m·s autour de Z.

**Couples perturbateurs** sur un 6U aux ailes déployées à 513 km, tels que
configurés dans `aocs.yaml` (le terme aérodynamique utilise une densité fixe
dimensionnée à 450 km ; il est donc prudent d'un facteur deux environ) :

| Source | Amplitude | Nature |
|---|---|---|
| Gradient de gravité | ≤ 4,5 × 10⁻⁷ N·m | cyclique (cas à 45° du nadir) |
| Dipôle magnétique résiduel (\|m\| ≈ 0,011 A·m²) | ~5 × 10⁻⁷ N·m | cyclique |
| Aérodynamique | ~2,3 × 10⁻⁷ N·m | **séculaire** dans le repère LVLH |
| Pression de radiation solaire | ~1,1 × 10⁻⁷ N·m | nulle en éclipse |

Borne RSS : $\sqrt{4.5^2+5.0^2+2.3^2+1.1^2}\times10^{-7} =
7.2\times10^{-7}$ N·m. Temps nécessaire pour remplir une roue à partir
de zéro à cette borne :

$$ t_{sat} = \frac{H_{max}}{\tau} = \frac{0.0300}{7.2\times10^{-7}} = 4.2\times10^{4}\ \text{s} = 11.6\ \text{h} \approx \mathbf{7.4\ orbits} $$

Avec la capacité selon l'axe X ou Y (0,037 N·m·s), on obtient environ
9 orbites ; avec le seul terme aérodynamique réellement **séculaire**,
environ 23 orbites. L'énoncé honnête est donc le suivant : *le moment
cinétique s'accumule sur une journée, pas sur une orbite* — l'essentiel
de la perturbation est cyclique et se compense de lui-même. Une roue qui
atteint le seuil de désaturation en moins d'une orbite vous signale une
perturbation dont vous n'avez pas tenu compte.

**C'est le moment cinétique, et non la vitesse des roues, qui sert de
variable de décision.** Une pyramide de quatre roues peut tourner à
5000 tr/min sur chaque roue avec un moment cinétique du satellite
**nul** — c'est la direction de l'espace nul —, et elle peut tourner à
1200 tr/min avec un moment cinétique important. Les paramètres à
surveiller sont `aocs.h_body_mag` (**0x02B9**) et le pourcentage
d'enveloppe `aocs.h_env_frac` (**0x02BA**). Le bit 4 de
`aocs.fine_ready` (0x02C5) se positionne dès que l'enveloppe atteint
70 %, et c'est l'avertissement honnête « un déchargement s'annonce »
sur lequel un planificateur doit agir.

**Règle de travail de l'opérateur.** Surveiller ensemble l'enveloppe et
la roue la plus rapide. 75 % de la limite de 5500 tr/min correspondent à
**4125 tr/min** ; la procédure NOM-007 *Gestion du moment cinétique*
déclare un déchargement REQUIS au-dessus de 4500 tr/min sur l'une
quelconque des roues, et FACULTATIF en dessous de 3000 tr/min sur toutes
les roues. Programmer le déchargement sur un **arc à haute latitude**,
en prévoyant une vraie marge de temps autour.

**Combien de temps dure réellement un déchargement.**

$$ \text{20 à 50 minutes.} $$

Mesures sur le modèle corrigé, à partir d'une charge de référence de
0,020 N·m·s : **0,005 N·m·s en 1521 s (25 min)** et **0,001 N·m·s en
2857 s (48 min)**. Le délai d'attente bord est de 3600 s ; un
déchargement qui l'atteint lève l'événement 0x020E
`AOCS_DESAT_INEFFECTIVE` et positionne `aocs.desat_ineffective`
(0x029C), au lieu de rester indéfiniment en DESAT. **N'intervenez pas
avant 3600 s**, sauf si une étape de vérification échoue effectivement —
l'ancienne échéance de 600 s interrompait tous les déchargements
pourtant sains.

L'ancienne valeur de « 5–8 minutes » résultait d'un calcul à couple
instantané, $0.020 / 4.8\times10^{-5}$, et elle est fausse pour une
raison qui mérite d'être comprise : **$\tau = m \times B$ est toujours
perpendiculaire à $B$** ; à chaque instant, seule la composante du
moment cinétique stocké perpendiculaire au champ local peut donc être
éliminée. Le reste attend que le champ balaie le satellite, ce qui se
produit à environ deux fois la fréquence orbitale. 5–8 minutes est la
bonne réponse pour la *composante* perpendiculaire ; 20–50 minutes est
la bonne réponse pour un déchargement complet. Forcer davantage sur les
barreaux n'aide pas — une loi en tout-ou-rien a été essayée puis
rejetée, car elle annule plus vite la composante perpendiculaire, ce qui
verrouille le vecteur moment cinétique sur $\hat{B}$ et le fait suivre
le champ.

**Ce que fait le satellite autour du déchargement.**

- La commande est `AOCS_DESATURATE` (S8 func 1) ; elle place le
  satellite en **DESAT, mode 7**.
- Elle est **refusée en FINE_POINT** (`DESAT_REFUSED_FINE`) et tant que
  `aocs.desat_inhibit` (0x029A) est verrouillé (`DESAT_INHIBITED`).
  Ces deux refus sont des comportements corrects, et non des anomalies.
- La désaturation automatique est **inhibée pendant la prise de vue**
  (`payload.mode` = 2) : un déchargement ne peut donc pas préempter une
  bande. C'est pourquoi CALIBRATION a dû devenir une nouvelle valeur de
  mode (3) plutôt qu'un simple renommage d'IMAGING.
- L'erreur d'attitude peut monter jusqu'à 2–3° pendant le
  déchargement ; la limite grossière est de 5°.
- **Ne commandez pas de mode ensuite.** DESAT revient au mode *depuis*
  lequel il a été activé, et le satellite se repromeut de lui-même en
  FINE_POINT dès que les préconditions de 0x02C5 sont restées
  satisfaites pendant 30 s. Confirmer avec `aocs.mode_demoted`
  (0x0298) = 0 et l'événement 0x020F `AOCS_MODE_RESTORED`. Commander
  NOMINAL à ce stade écrase le mode commandé par le sol et annule la
  repromotion — exactement le défaut qui a un jour laissé un satellite
  en pointage solaire pendant six orbites.

**Pourquoi la haute latitude, et non l'éclipse.** L'efficacité d'un
déchargement magnétique est une question de **géométrie**, et non
d'éclairement : elle dépend de l'intensité et de l'orientation du champ
local ; elle est donc maximale au-dessus des pôles et minimale près de
l'équateur magnétique. La pression de radiation solaire est le plus
faible des quatre termes perturbateurs, et son absence en éclipse ne
change rien de significatif. Programmer le déchargement sur un passage
polaire ; si les vitesses des roues ne baissent pas, `aocs.mtq_enabled`
(0x025E) et la position sur l'orbite sont les deux premières choses à
vérifier.

---

## 13.8 Exemple de quart résolu : tout assembler

Un briefing type avant passage exige que le FD connaisse, dans les 30
secondes qui suivent l'ouverture de l'entrée du planning de contacts :

1. **Heure d'AOS** (§13.2) : « Iqaluit AOS in 6 min 12 s, TCA at
   AOS+3:45, LOS at AOS+7:30. Max elevation 47°, so we clear the
   10° gate for most of the window. »
2. **Interaction avec l'éclipse** (§13.3) : « We exit eclipse at AOS−2:30
   with predicted SoC 69 percent. Pass starts in the lit segment. »
3. **Pointage** (§13.4) : « 0x02AA reads 0.020 degrees total,
   comfortably inside the 0.05 gate. The control term dominates at
   0.019; the star-tracker chain is a rounding error. 0x02C5 reads
   zero — four wheels, MEKF converged. »
4. **Marge de liaison** (§13.6) : « Predicted 46.5 dB at HIGH over Iqaluit
   at TCA; measured 46.2. Within the 1–2 dB normal band. HIGH tier
   available for the dump. »
5. **Données** (§13.6.1) : « One 4 MiB product queued. 328 seconds with
   the protocol allowance against a 450-second pass, most of it above 10
   degrees — it fits, with little to spare. No second dump this
   pass. »
6. **Roues** (§13.7) : « Envelope at 62 percent on 0x02BA, highest
   wheel 3850 rpm — 70 percent of the 5500 limit. Below the
   4125 threshold. Desat planned for the polar arc two orbits out,
   not this pass, and we will allow the full 3600-second timeout
   for it. »

Si les six réponses sont nettes, le briefing se termine en deux minutes
et l'équipe est prête pour les opérations.

---

## 13.9 Références

- ISO 8601 — *Date and time representations* (représentation de la date et de l'heure) — [www.iso.org](https://www.iso.org/iso-8601-date-and-time-format.html)

# Chapitre 14 — Catalogue des procédures (fiches aide-mémoire)

Ce chapitre est l'aide-mémoire de poche de l'opérateur : **une fiche par
page**, classée par catégorie et repérée par une couleur propre à chaque
famille de procédures. Chaque fiche comporte : un en-tête (avec l'icône du
poste responsable), un point d'entrée, un objectif, les issues défavorables
ou écarts possibles, un arbre de décision facultatif (pour les contingences)
et un tableau pas à pas avec TC/code, case de confirmation et remarques.

**Code couleur.** Vert = nominal · Bleu = LEOP · Violet =
recette en orbite · Orange = contingence · Rouge = urgence.

**Légende des icônes de poste (crochets de l'en-tête).** `[FD]` directeur de vol ·
`[FE]` ingénieur de vol · `[GS]` ingénieur station sol ·
`[PE]` ingénieur charge utile · `[SE]` ingénieur satellite ·
`[DH]` gestionnaire de données · `[TT]` ingénieur TT&C · `[OB]` ingénieur
OBDH · `[AOCS]` ingénieur SCAO · `[MULTI]` multiposte.

> **Note de la rédaction — supports papier cités par ces fiches.** Les
> fiches de procédure font référence à un *formulaire de fiche d'anomalie*,
> à un *bandeau « contingence active »* et à une *confirmation par seconde
> clé du FD*. Aucun de ces éléments n'est implémenté dans l'interface du MCS.
> En formation sur simulateur, ils sont suivis sur papier : chaque fiche porte
> une case de confirmation `□` pour la seconde clé du FD ; l'état « contingence
> active » est tenu dans le journal des annonces du FD sur la boucle vocale ;
> et les fiches d'anomalie sont remplies sur un formulaire papier que le
> SPACON classe en fin de quart. Adaptez ces règles aux conventions de votre
> installation si un déploiement fournit un équivalent électronique.

Les 70 procédures du simulateur se répartissent en 7 de LEOP, 13 de
recette en orbite, 14 nominales, 30 de contingence et 6 d'urgence. Les
fiches ci-dessous couvrent les quelque 57 procédures les plus lourdes de
conséquences du catalogue. Les fiches marquées **« voir §9.3 / §9.4 / §9.5 »**
pour NOM-001, CTG-003 et NOM-012 contiennent les procédures phares ; leurs
listes de vérification complètes en mode « lire et faire » figurent au
chapitre 9. Le reste du catalogue (essentiellement des opérations de remise
en ordre, de la maintenance programmée et des contingences peu fréquentes)
est répertorié au §14.6, avec les références des fichiers à consulter en
console.

> **Note de la rédaction — quel identifiant figure sur la fiche.** Chaque
> fiche de ce chapitre porte exactement l'identifiant de
> `configs/eosat1/procedures/procedure_index.yaml` ; l'identifiant
> annoncé sur la boucle vocale est donc le fichier qu'ouvre l'onglet
> Procédures du MCS. Deux identifiants nominaux ont changé lors du
> rapprochement du livre avec le simulateur : la fiche d'**exécution**
> de la manœuvre d'orbite est **NOM-013** (la NOM-005 du simulateur est
> la configuration HK) et NOM-006 est le chargement de logiciel (la
> NOM-008 du simulateur est la synchronisation d'horloge). Les fiches de
> contingence et d'urgence ont été renumérotées selon les identifiants
> du simulateur en octobre 2026 ; les numéros des tirages antérieurs
> figurent dans la note historique à la fin du §14.6. Les deux fiches de
> contingence provisoires du livre, CTG-B01 et CTG-B02, sont désormais
> des fiches du simulateur : **CTG-029** Reprise après panne de gyroscope
> et **CTG-030** Rejet de télécommande et échec de vérification. Le
> catalogue livré va de LEOP-001 à LEOP-007, de COM-001 à COM-013, de
> NOM-001 à NOM-014, de CTG-001 à CTG-030 (CTG-018 retirée au profit de
> CTG-021) et d'EMG-001 à EMG-006.

## 14.1 Fiches de procédure LEOP

> **Note de la rédaction — ordre d'exécution de la LEOP.** À partir de l'état
> initial de démarrage à froid, l'ordre est **LEOP-001 → LEOP-002 → LEOP-004 → LEOP-007 →
> LEOP-005 → LEOP-006 → LEOP-003**. Les ailes sont déployées (LEOP-004)
> avant que quoi que ce soit d'autre ne consomme ; LEOP-007 n'alimente que la
> suite AOCS et commande DETUMBLE ; LEOP-005 observe le passage automatique
> en COARSE_SUN ; LEOP-003 clôt la LEOP par la déclaration de la phase 5.

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[MULTI] LEOP-001 — Première acquisition du signal et amorçage de l'OBC</div>

**Point d'entrée :** premier passage au-dessus d'Iqaluit après l'expiration de la minuterie de séparation. Au démarrage à froid, le satellite ne fait qu'écouter : seuls `obc` et `ttc_rx` sont alimentés, `ttc_tx` est OFF et l'OBC est dans le chargeur d'amorçage — il n'y a donc aucune porteuse à acquérir passivement, et le passage commence avec le forçage de passage (Pass Override) engagé.

**Objectif :** établir la première voie de commande, faire sortir l'OBDH du chargeur d'amorçage vers l'image applicative, quitter le mode balise pour le échelon LOW, et laisser activées avant la LOS les structures HK de plateforme dont le passage a besoin.

**Issues défavorables possibles / écarts :**

- Pas de S1.1 en réponse à `CONNECTION_TEST` → le maintien automatique de l'émetteur (auto-TX hold-down) ne se déclenche que sur une TC acceptée ; vérifier le forçage de passage et la liaison montante, réessayer une fois, puis basculer sur Troll
- `OBC_BOOT_APP` est acquittée (S1.1) mais `obdh.sw_image` ne change pas d'état en 30 s → échec du CRC de l'application ; lancer CTG-010 Reprise après chien de garde OBDH / envisager `OBC_REBOOT`
- Liaison établie, pas de HK après l'amorçage → CTG-019 Absence de télémesure en début de passage (voie de commande en aveugle)
- `TTC_SET_DATA_RATE` refusée avec l'erreur S1.8 `0x0007` → mode balise toujours verrouillé ; renvoyer `TTC_SET_BEACON_MODE(on=0)`

**Arbre de décision :**

- SI S1.1 + S17.2 reçus ET `obdh.sw_image` = 1 ET les SID 1, 3, 4, 6, 11 arrivent → procédure GO, poursuivre avec LEOP-002
- SI S1.1 reçu mais pas de S1.7 pour la commande d'amorçage en 30 s → CTG-010
- SI aucune TC acceptée à AOS+2 min → attente (HOLD) ; si toujours rien à AOS+5 min → **EMG-004 Perte de communication**

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : pointer Iqaluit sur l'AOS prévue ; démodulateur sur le échelon BEACON | (panneau station du MPS) | □ | 1 kbit/s BPSK, 1 kBd — le seul débit émis par le chargeur d'amorçage |
| 2 | SPACON : engager le forçage de passage dans le MCS | `pass_override` (0x05FF) = 1 | □ | Au démarrage à froid, `ttc_tx` est OFF ; le forçage garantit la liaison montante |
| 3 | SPACON : envoyer la première TC (test de connexion) | `CONNECTION_TEST` (S17.1) | □ | S1.1 + S17.2 en 10 s ; le maintien auto-TX alimente `ttc_tx` pendant **300 s** (`simulation.yaml` `ttc.auto_tx_hold_s`), réarmé par chaque TC acceptée — cinq minutes sans commande et la liaison descendante tombe |
| 4 | TT&C : confirmer le verrouillage de la porteuse et la qualité de la liaison | `ttc.link_status` (0x0501) = 2 (LOCKED) | □ | `ttc.rssi` (0x0502) > −110 dBm ; `ttc.link_margin` (0x0503) > 3.0 dB |
| 5 | SPACON : vérifier que le satellite est toujours dans le chargeur d'amorçage | `HK_REQUEST(sid=11)` (S3.27) ; `obdh.sw_image` (0x0311) = 0 | □ | SID de balise uniquement ; pas encore de SID de sous-système |
| 6 | SPACON : commander l'amorçage de l'application de l'OBC (double validation) | `OBC_BOOT_APP` (S8 func_id 55) | □ | S1.1 en 5 s ; S1.7 après la vérification CRC d'environ 10 s ; `obdh.sw_image` = 1 en 15 s |
| 7 | SPACON : activer les structures HK de plateforme | `HK_ENABLE(sid=3)`, `HK_ENABLE(sid=4)`, `HK_ENABLE(sid=6)` (S3.5) | □ | L'amorçage réapplique `default_enabled_sids: [1, 11]` ; les SID 2 et 5 attendent LEOP-007 |
| 8 | TT&C : quitter le mode balise, puis sélectionner le échelon LOW | `TTC_SET_BEACON_MODE(on=0)` (S8 func_id 70) ; `TTC_SET_DATA_RATE(rate=0)` (S8 func_id 65) | □ | `ttc.beacon_mode` (0x0521) = 0 ; 16 kbit/s, `ttc.tm_tier` (0x0539) = 1 ; reconfigurer le démodulateur à 16 kBd |
| 9 | SPACON : synchroniser le temps bord | `SET_TIME(cuc_seconds=T_corrected)` (S9.1) | □ | L'horloge est à CUC 0 = **J2000** et `obdh.time_ref` (0x0A13) = 0 (NONE) — le chargeur d'amorçage l'a réinitialisée et `OBC_BOOT_APP` ne la restaure pas. Résidu < 1.0 s sur `REQUEST_TIME` (S9.2) ; `time_ref` → 1 (GROUND). La fiche complète est LEOP-006 |
| 10 | SPACON : contrôle de vraisemblance de l'EPS ; consigner la fin ; passer la main à LEOP-002 | `HK_REQUEST(sid=1)` (S3.27) | □ | « LEOP-001 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[MULTI] LEOP-002 — Bilan de santé initial</div>

**Point d'entrée :** immédiatement après l'annonce de fin de LEOP-001 ; SID 1, 3, 4, 6 et 11 en flux.

**Objectif :** chaque poste de sous-système confirme que les valeurs de référence sont dans la plage avant le début de la mise sous tension séquentielle ; produire un PASS/FAIL unique pour le FD.

**Issues défavorables possibles / écarts :**

- Un seul sous-système annonce FAIL → lancer la contingence de ce sous-système (p. ex. CTG-001 pour une sous-tension EPS, CTG-002 pour l'AOCS) avant de poursuivre
- Plusieurs FAIL → suspendre entièrement la LEOP ; le FD envisage EMG-001, passage en mode survie
- Un sous-système renvoie DEGRADED plutôt que FAIL → poursuivre à la discrétion du FD, mais consigner un point de surveillance
- Un indicateur de ligne vaut 1 pour la ligne AOCS, charge utile, refroidisseur ou `prop` → quelque chose a été alimenté trop tôt ; le consigner et suspendre LEOP-004 jusqu'à l'examen par le FD

**Arbre de décision :**

- SI tous les postes renvoient PASS → GO LEOP-004
- SI FAIL EPS → CTG-001 d'abord, puis relancer LEOP-002
- SI une ligne est alimentée trop tôt → suspendre, examen par le FD avant LEOP-004
- SI ≥ 2 FAIL → appeler le FD, envisager EMG-001

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : lire la tension batterie, le SoC, la tension du bus, les courants de ligne | `HK_REQUEST(sid=1)` (S3.27) | □ | SoC (0x0101) > 60 %, bus (0x0105) 27.0–29.5 V |
| 2 | Thermique : lire toutes les températures de zone | `HK_REQUEST(sid=3)` (S3.27) | □ | `tcs.temp_obc` (0x0406) −5…+45 °C ; `tcs.temp_battery` (0x0407) 0…+35 °C |
| 3 | TT&C : confirmer les paramètres de liaison | `HK_REQUEST(sid=6)` (S3.27) | □ | `ttc.link_status` (0x0501) = 2 ; RSSI > −105 dBm ; marge > 3.0 dB |
| 4 | OBDH : confirmer que l'OBC tourne, sans événement FDIR | `HK_REQUEST(sid=4)` (S3.27) | □ | `obdh.mode` (0x0300) = 0 ou 1 ; `obdh.cpu_load` (0x0302) < 70 % |
| 5 | EPS : confirmer que les sous-systèmes non alimentés sont éteints | `eps.pl_aocs_wheels` (0x0117), `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) = 0 (SID 1) | □ | Ne pas demander les SID 2 ou 5 : ils ne sont pas encore activés et leurs unités ne sont pas alimentées, ce sont donc les indicateurs de ligne qui servent de bilan de santé. Il n'y a ni mode AOCS ni télémesure des roues à lire avant LEOP-007 et COM-004 |
| 6 | SPACON : consolider un PASS/FAIL unique sur la boucle vocale | (journal de mission) | □ | « LEOP-002 PASS » ou liste des FAIL |
| 7 | FD : GO/no-GO pour LEOP-004 | (annonce du FD) | □ | Consigné au journal |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] LEOP-003 — Restitution d'orbite initiale</div>

**Point d'entrée :** après LEOP-006 — c'est la **dernière** fiche de la LEOP. Maintien au Soleil en COARSE_SUN ; horloge référencée (`obdh.time_ref` 0x0A13 = 1, 2 ou 3) ; récepteur GPS sous tension depuis LEOP-007 avec `aocs.gps_fix` (0x0274) ≥ 2 ; SID 12 de HK (GPS_NAV) activé dans LEOP-006.

**Objectif :** vérifier la solution de navigation GPS de bord, confirmer l'injection héliosynchrone à 513 km / 97,39°, transmettre le TLE affiné aux outils sol et déclarer la fin de la LEOP en commandant la phase de mission 5 (COMMISSIONING).

**Issues défavorables possibles / écarts :**

- `aocs.gps_fix` < 2 → confirmer que le récepteur est sous tension (`S2_AOCS_GPS_RECEIVER`, équipement 0x020F, LEOP-007) ; un démarrage à froid peut prendre 15 min. Sans point après 30 min, se replier sur la distance et le Doppler mesurés par le réseau de stations ; la déclaration de phase peut se faire sur une orbite restituée au sol avec l'accord du FD
- SID 12 absent de la liaison descendante → `HK_ENABLE(sid=12)` (S3.5) a été omise dans LEOP-006 ; la renvoyer
- Altitude hors de la plage de contrôle [495, 540] km → vérifier la qualité du point (`aocs.gps_pdop`, 0x0275) et prendre un second point ; l'injection elle-même n'est suspecte qu'en dehors de [400, 550] km
- Inclinaison à plus de 0,2° de 97,39° → signaler à la dynamique du vol ; la précession héliosynchrone et la durée de vie sont touchées
- `SYS_SET_MISSION_PHASE` refusée → `0x0C03` : l'OBC est revenu dans le chargeur d'amorçage (refaire l'étape 5 de LEOP-001 et LEOP-006) ; `0x0C04` : déclaration en arrière sans FORCE

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FDS : vérifier que la solution de navigation GPS descend | `HK_REQUEST(sid=12)` (S3.27) | □ | `aocs.gps_fix` (0x0274) ≥ 2 ; `aocs.gps_num_sats` (0x0276) ≥ 4 ; consigner `aocs.gps_pdop` (0x0275). La position vaut zéro sous le point de type 2 : attendre le point, ne rien en conclure |
| 2 | FDS : lire la position | `GET_PARAM(param_id=0x0210)`, `(param_id=0x0211)`, `(param_id=0x0212)` (S20.3) | □ | `aocs.gps_alt` (0x0212) dans la plage de contrôle [495, 540] km |
| 3 | FDS : lire le vecteur d'état ECEF | `GET_PARAM(param_id=0x0231)` … `(param_id=0x0236)` (S20.3) | □ | Norme de la position 6700–6950 km, norme de la vitesse 7400–7900 m/s ; consigner avec l'horodatage GPS |
| 4 | FDS : comparer à l'orbite prédite par le lanceur | (chaîne de traitement FDS) | □ | i à 0,2° près de 97,39°, e < 0,01, LTAN à 15 min près de 10 h 00 ; période comparée au TLE (15,24 tours/jour, 5669 s) |
| 5 | FDS : prendre un second point 10 min plus tard | `HK_REQUEST(sid=12)` (S3.27) | □ | `aocs.gps_alt` à 20 km près de l'étape 2 ; point toujours ≥ 2 |
| 6 | FDS : diffuser le rapport de restitution d'orbite et le TLE affiné aux outils sol | (planificateur, FDS, réseau de stations) | □ | Le TLE affiné met à jour la prédiction des passages au sol. **Rien n'est envoyé au satellite** : il n'existe aucune commande de chargement de l'orbite à bord |
| 7 | FD : tour de table GO/NO-GO, puis déclarer COMMISSIONING | `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (S8 func_id 120) | □ | **Critique** : relire l'argument. `eps.spacecraft_phase` (0x0129) = 5 en 5 s ; l'événement `MISSION_PHASE_CHANGED` (0x0055) indique 4 → 5. Cette fiche est la seule à l'envoyer. « LEOP-003 complete » : la LEOP est terminée |

**Remarque — la phase de mission est un verrouillage, pas une étiquette.** `SYS_SET_MISSION_PHASE` (S8 func_id 120, arguments `phase` 3–6 et `flags` bit 0 = FORCE) conditionne six mécanismes : les sous-systèmes qui s'exécutent, l'acceptation des télécommandes (en phase ≤ 3, seul le sous-ensemble du chargeur d'amorçage est accepté), le `sat.mode` dérivé (0x0001, bloqué sur SAFE en dessous de la phase 6), l'armement du modèle avancé de propagation de défaillance, les règles FDIR conditionnées par la phase, et le verrouillage d'armement de la propulsion (`min_phase: 6`). Une valeur hors plage est refusée avec `0x0C01`, les phases 0–2 avec `0x0C02`, une phase applicative alors que l'OBC est encore dans le chargeur d'amorçage avec `0x0C03`, et une transition en arrière avec `0x0C04`, sauf si FORCE est positionné. Ceci **remplace** la décision antérieure selon laquelle « la transition de phase se fait uniquement en console » : la télécommande existe et c'est par elle que l'on procède.

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] LEOP-004 — Vérification du générateur solaire</div>

**Point d'entrée :** après LEOP-002, sur une portion éclairée de l'orbite, SoC > 50 % (chaque aile consomme ~2 A pendant 30 s lors du déploiement). L'AOCS n'est pas encore alimenté, il n'y a donc aucune télémesure de vitesse angulaire : le déploiement est qualifié par rapport aux vitesses de séparation du lanceur.

**Objectif :** déployer les ailes +Y et −Y, confirmer le déploiement en télémesure et vérifier que le courant de chaque aile est cohérent avec l'angle solaire prévu.

**Issues défavorables possibles / écarts :**

- Une aile n'indique pas DEPLOYED en 45 s → nouvelle tentative sur une seule aile avec `EPS_DEPLOY_WING(wing=0)` (+Y) ou `(wing=1)` (−Y), approbation du FD requise ; en cas d'échec, évaluer le bilan de puissance avec une seule aile
- Courants des ailes asymétriques de plus de 30 % → consigner une anomalie ; poursuivre la LEOP avec un bilan de puissance réduit
- Courant qui oscille avec l'attitude → attendu avant l'amortissement des vitesses angulaires ; revérifier après LEOP-005

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : commander le déploiement des ailes (les deux) | `EPS_DEPLOY_WING(wing=2)` (S8 func_id 81) | □ | `eps.wing_status` (0x0144) bit 4/5 = déploiement en cours |
| 2 | EPS : confirmer que les deux ailes sont déployées | `eps.wing_status` (0x0144) = 0x03 | □ | bit0 = +Y, bit1 = −Y — 0x0144 est la seule source de vérité du déploiement |
| 3 | EPS : lire le courant de chaque aile | `eps.sa_wing_py_current` (0x0146), `eps.sa_wing_my_current` (0x0147) | □ | > 0.1 A chacune au Soleil ; 0x0110–0x0113 sont des indicateurs de LIGNE d'alimentation, pas de la télémesure du générateur |
| 4 | EPS : vérifier la symétrie des ailes et la production totale | `eps.power_gen` (0x0107) | □ | Ailes à 15 % l'une de l'autre ; > 20 W en culbutage, > 40 W une fois pointé vers le Soleil |
| 5 | SPACON : consigner la référence ; rendre compte au FD | (journal de mission) | □ | « LEOP-004 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] LEOP-005 — Acquisition du Soleil</div>

**Point d'entrée :** après LEOP-007 : AOCS en DETUMBLE (`aocs.mode` 0x020F = 2) sur le magnétomètre et les magnétocoupleurs, SID 2 en liaison descendante, roues DISABLED, SoC > 40 %.

**Objectif :** observer l'amortissement des vitesses angulaires par la loi B-dot et le passage **automatique** en COARSE_SUN (mode 3), puis vérifier un maintien au Soleil à bilan de puissance positif. Cette fiche ne commande aucun changement de mode.

**Issues défavorables possibles / écarts :**

- Vitesses angulaires sans décroissance après 15 min → vérifier `aocs.mtq_enabled` (0x025E) = 1 et `aocs.mag_enabled` (0x025C) = 1 ; si l'un des deux est retombé, le rétablir comme à l'étape 4 de LEOP-007 et recommander DETUMBLE avec `AOCS_SET_MODE(mode=2)` (S8 func_id 0)
- Vitesses sous 0,5 °/s mais aucun passage au bout de 30 min → ne **pas** commander le mode 3 ; confirmer que les vitesses sont sous le seuil sur les trois axes, de façon durable, puis appeler le FD
- Erreur d'attitude qui ne converge pas en COARSE_SUN → vérifier la confiance des capteurs solaires grossiers (`aocs.css_sun_confidence`, 0x0215) ; en éclipse, attendre la phase éclairée
- Les vitesses remontent → CTG-002 Anomalie SCAO

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : confirmer DETUMBLE et consigner les vitesses initiales | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.mode` (0x020F) = 2 ; vitesses (0x0204–0x0206) consignées ; 0,5–5 °/s par axe est typique après la séparation |
| 2 | AOCS : suivre l'amortissement — ne rien commander | `HK_REQUEST(sid=2)` (S3.27) toutes les 5 min | □ | Toutes les vitesses décroissent ; la loi B-dot les divise environ par deux toutes les 10–15 min. Un `aocs.mag_field_total` (0x0277) nul signifie que la loi B-dot est aveugle |
| 3 | AOCS : observer le passage automatique en COARSE_SUN | (observation) | □ | Vitesses sous 0,5 °/s pendant 30 s → `aocs.mode` = 3 de lui-même, en 1800 s au plus. Ne **pas** commander le mode 3 |
| 4 | AOCS : vérifier le maintien au Soleil | `HK_REQUEST(sid=2)` (S3.27) toutes les 60 s pendant 5 min | □ | `aocs.att_error` (0x0217) < 15° en 600 s ; `aocs.css_sun_confidence` (0x0215) > 0,5 ; vitesses < 0,5 °/s. Le maintien vole sur les magnétocoupleurs : s'attendre à une dérive de l'ordre du degré |
| 5 | EPS : vérifier la production pendant le maintien | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.power_gen` (0x0107) > 40 W ; SoC stable ou en hausse |
| 6 | SPACON : consigner l'état final de l'AOCS ; GO LEOP-006 | (journal de mission) | □ | « LEOP-005 complete ». Le satellite reste en COARSE_SUN : sans senseur stellaire sous tension, rien ne le promeut, et les roues restent désactivées jusqu'à COM-004 |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] LEOP-006 — Synchronisation temporelle</div>

**Point d'entrée :** après LEOP-005 ; OBC sur l'image APPLICATION (`obdh.sw_image` 0x0311 = 1) — `SET_TIME` ne figure pas dans la liste d'autorisation du chargeur d'amorçage — et `ttc.link_status` (0x0501) = 2.

**Objectif :** synchroniser l'horloge de bord sur l'UTC sol à 1.0 s près et vérifier la marche de l'horloge à mieux que 100 ppm. La synchronisation fine (< 0.1 s) est une activité des opérations nominales, NOM-008.

**L'horloge n'a jamais été réglée ; elle n'a pas simplement dérivé.** L'OBC fait tourner une horloge indépendante. Le chargeur d'amorçage la démarre à CUC 0 = l'époque de la mission **J2000** (2000-01-01T12:00:00 UTC, `mission.yaml` `time_epoch`) et `obdh.time_ref` (0x0A13) indique **0 (NONE)** ; `obdh.time_since_sync_s` (0x0A14) indique 4294967295 = jamais synchronisé. Chaque paquet émis avant cette fiche est daté de l'an 2000, et c'est le comportement correct, pas une erreur de décodage. **Une réinitialisation du chargeur d'amorçage ramène l'horloge à J2000 et `OBC_BOOT_APP` ne la restaure pas — chaque redémarrage impose donc de rejouer cette fiche.**

**Issues défavorables possibles / écarts :**

- Dérive ≥ 86 400 s **avec `time_ref` = 1 (GROUND)** → horloge réglée puis décalée de plusieurs jours ; HOLD et consulter l'ingénieur OBDH. Avec `time_ref` = 0 (NONE), un décalage de plusieurs années est la signature *attendue* de la LEOP — l'horloge compte depuis J2000
- `SET_TIME` rejetée → `SET_TIME` ne figure pas dans la liste d'autorisation du chargeur d'amorçage (vérifier `obdh.sw_image` 0x0311 = 1), ou la valeur sort de la plage de validation bord ; attendre 5 s et réessayer
- Résidu > 1.0 s après correction → la correction a pu manquer le front du PPS ; renvoyer avec un T_corrected mis à jour
- `time_ref` (0x0A13) indique de nouveau 0 (NONE) après une synchronisation réussie → l'OBC a redémarré ; vérifier `obdh.uptime` (0x0308) et `obdh.reboot_count` (0x030A) et rejouer la fiche
- Erreur de marche de l'horloge > 100 ppm → signaler l'oscillateur de l'OBC. Une unité saine tourne à ~**12 ppm** (≈ 1 s/jour) avec une dispersion de quelques ppm d'une unité à l'autre ; ~500 ppm (≈ 43 s/jour) est la signature de l'injection de panne `clock_drift` de l'instructeur, pas d'un composant vieillissant

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | SPACON : vérifier l'état de l'OBC et la liaison | `HK_REQUEST(sid=4)` (S3.27) ; `HK_REQUEST(sid=6)` (S3.27) | □ | `obdh.mode` (0x0300) = 0 ou 1 ; marge (0x0503) > 3.0 dB |
| 2 | SPACON : demander ENSEMBLE le rapport de temps et la distance oblique | `REQUEST_TIME` (S9.2) ; `HK_REQUEST(sid=6)` (S3.27) ; `HK_REQUEST(sid=4)` (S3.27) | □ | `REQUEST_TIME` est la commande du catalogue (`TIME_REPORT_REQUEST` n'en est qu'un alias). `ttc.range_km` (0x0509) se trouve dans le SID 6 — demandez-le, sinon l'OWLT n'arrive jamais |
| 2a | SPACON : lire la référence de temps avant de lire l'horloge | `obdh.time_ref` (0x0A13) ; `obdh.time_since_sync_s` (0x0A14) | □ | 0 NONE / 1 GROUND / 2 GPS / 3 HOLDOVER. Attendu ici : 0 et 4294967295 ; toute autre valeur signifie que quelqu'un a déjà réglé l'horloge — établir qui avant de poursuivre |
| 3 | SPACON : calculer l'OWLT et la dérive | OWLT_ms = `ttc.range_km` / 299792.458 × 1000 ; delta_t = T_obc − (T_ground − OWLT) | □ | T_obc = `obdh.obc_time` (0x0309) + `obdh.obc_time_fine` (0x0A12)/65536, en secondes CUC depuis J2000. Attendre 3–22 ms d'OWLT — deux ordres de grandeur sous le seuil de 1.0 s. Recouper 0x0309 avec la valeur de TM(9,2) ; elles doivent concorder à l'intervalle de 8 s du SID 4 près |
| 4 | SPACON : envoyer la correction de temps | `SET_TIME(cuc_seconds=T_corrected)` (S9.1) | □ | L'argument se place À L'INTÉRIEUR des backticks — un `SET_TIME` nu encode cuc_seconds = 0, soit une remise à zéro sur l'époque. Confirmer que T_corrected est rapporté à l'époque **J2000** : un horodatage Unix est trop grand de ~9.46e8 s et il est accepté. L'événement `OBC_TIME_SET` (0x030C) porte le saut signé |
| 5 | SPACON : vérifier le résidu | `REQUEST_TIME` (S9.2) ; `HK_REQUEST(sid=4)` (S3.27) | □ | Résidu en valeur absolue < 1.0 s ; `obdh.time_ref` (0x0A13) désormais = 1 (GROUND) et `time_since_sync_s` (0x0A14) reparti de 4294967295 ; `obdh.mode` inchangé |
| 6 | SPACON : valider la marche de l'horloge sur deux rapports | `REQUEST_TIME` (S9.2) | □ | drift_ppm = ((T_obc2 − T_obc1) − (T_gnd2 − T_gnd1))/interval × 1e6 ; accepter < 100 ppm, attendre ~12 ppm. Utiliser l'intervalle le plus long que permet le passage — 12 ppm sur 60 s font 0.7 ms, ce qui n'est pas mesurable. Sans signification si `time_ref` = 2 (GPS) : on mesure alors la boucle d'asservissement, pas l'oscillateur |
| 6a | SPACON : activer la HK de navigation GPS, puis asservir l'horloge au GPS dès que le récepteur a un point | `HK_ENABLE(sid=12)` (S3.5) ; `OBC_GPS_TIME_SYNC` (S8 func_id 80) | □ | Le SID 12 n'est pas activé par défaut : sans lui, LEOP-003 travaille à l'aveugle. Synchroniser seulement avec `aocs.gps_fix` (0x0274) ≥ 2 ; `obdh.time_ref` → 2 (GPS) en 15 s. Réglage sol d'abord, GPS ensuite : sur une horloge déjà à 1 s près, le saut GPS est de quelques millisecondes, bien en dessous du saut de 5 s qui force l'AOCS en SAFE_BOOT (CTG-027). Pas encore de point → envoyer la synchronisation au contact suivant |
| 7 | SPACON : consigner la nouvelle référence de dérive ; GO LEOP-003 | (journal de mission) | □ | « LEOP-006 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-leop" markdown="1">

<div class="procedure-card-header" markdown="1">[MULTI] LEOP-007 — Mise sous tension séquentielle</div>

**Point d'entrée :** après LEOP-004 : image applicative en service (`obdh.sw_image` = 1), liaison en LOW, ailes déployées et productrices, toutes les lignes commutables OFF sauf `ttc_tx`, AOCS sur OFF, satellite en culbutage aux vitesses de séparation ; SoC > 60 %, bus 26–30 V.

**Objectif :** n'alimenter que ce dont le reste de la LEOP a besoin, dans l'ordre des dépendances : les lignes de réchauffeurs si leurs zones ont besoin de chaleur, la ligne de la suite AOCS, le magnétomètre, les magnétocoupleurs et le récepteur GPS, puis DETUMBLE. La charge utile, le refroidisseur, les roues, les senseurs stellaires, les gyroscopes et la ligne `prop` restent éteints ; leurs fiches de recette les mettent en service.

**Issues défavorables possibles / écarts :**

- `AOCS_SET_MODE(mode=2)` refusée avec `0x0004` → l'écriture de la ligne n'a pas pris ; renvoyer `EPS_POWER_ON(line_index=7)`, vérifier `eps.pl_aocs_wheels` (0x0117), réessayer
- Refus avec `0x0A20` (pas de magnétomètre) → renvoyer `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` ; il n'existe pas de magnétomètre redondant
- Refus avec `0x0A21` (pas de magnétocoupleurs) → renvoyer `MTQ_ENABLE(enable=1)`
- Les vitesses augmentent en DETUMBLE → `AOCS_SET_MODE(mode=0)` et examiner la polarité du magnétomètre et des magnétocoupleurs
- SoC sous 40 % → arrêter, couper la dernière ligne alimentée, attendre un SoC > 60 %, reprendre ; bus sous 26 V → CTG-001
- Surintensité sur une ligne dans les 30 s suivant sa mise sous tension → CTG-012 Réponse à une surintensité ; la ligne reste éteinte

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : vérifier l'état de référence de l'EPS | `HK_REQUEST(sid=1)` (S3.27) | □ | Bus 26–30 V, SoC > 60 %, `eps.power_gen` > 0 W |
| 2 | EPS : alimenter les lignes de réchauffeurs seulement si leurs zones ont besoin de chaleur | `EPS_POWER_ON(line_index=5)` / `(line_index=6)` (S8 func_id 19) | □ | `htr_bat` seulement si `tcs.temp_battery` < +5 °C ; `htr_obc` seulement si `tcs.temp_obc` < 0 °C. Consigner les lignes alimentées : COM-002 lit cet enregistrement |
| 3 | EPS : alimenter la ligne de la suite AOCS et activer sa télémesure de servitude | `EPS_POWER_ON(line_index=7)` (S8 func_id 19) ; `HK_ENABLE(sid=2)` (S3.5) | □ | `eps.pl_aocs_wheels` (0x0117) = 1. La ligne alimente toute la suite AOCS ; elle n'active **pas** les roues : `aocs.wheels_enabled` (0x0260) reste à 0 jusqu'à COM-004 |
| 4 | AOCS : activer le capteur et les actionneurs de DETUMBLE, ainsi que le récepteur GPS | `S2_AOCS_MAGNETOMETER(device_id=521, state=1)` ; `MTQ_ENABLE(enable=1)` (S8 func_id 9) ; `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | □ | `aocs.mtq_enabled` (0x025E) = 1. Le délai d'acquisition du premier point GPS commence maintenant : LEOP-006 et LEOP-003 en ont besoin |
| 5 | AOCS : commander DETUMBLE | `AOCS_SET_MODE(mode=2)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 2 en 10 s ; `aocs.mag_enabled` (0x025C) = 1 ; `aocs.mag_field_total` (0x0277) 5–70 µT ; vitesses (0x0204–0x0206) en baisse en 60 s |
| 6 | EPS : confirmer l'état d'alimentation de sortie ; GO LEOP-005 | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) et `aocs.wheels_enabled` (0x0260) tous à 0 ; marge de puissance positive. « LEOP-007 complete » |

**Remarque.** Le satellite compte **neuf** lignes d'alimentation, d'indices 0–8 : `obc`, `ttc_rx`, `ttc_tx`, `payload`, `fpa_cooler`, `htr_bat`, `htr_obc`, `aocs_wheels`, `prop`. Il n'existe ni ligne IMU ni ligne de capteurs AOCS — les gyroscopes sont les équipements S2 `S2_AOCS_GYROSCOPE_0/1/2`, alimentés dans COM-003. La ligne charge utile est alimentée dans COM-009, celle du refroidisseur dans COM-010, et la ligne `prop` seulement pour la préparation des manœuvres (NOM-004 / NOM-013) et le retrait de service (NOM-014). Le passage en COARSE_SUN est automatique et s'observe dans LEOP-005 ; la déclaration de la phase 5 est l'étape 7 de LEOP-003.

</div>

<div style="page-break-before: always"></div>

## 14.2 Fiches de procédure de recette en orbite

> **Note de la rédaction — ordre d'exécution de la recette (décision Q16).**
> COM-001 → COM-002 → **COM-004 → COM-003** → COM-005 → … → COM-010 →
> COM-012 → COM-011 → COM-013. COM-004 active les roues et commande
> NOMINAL ; COM-003 étalonne ensuite les gyroscopes dans ce NOMINAL piloté
> par les roues, car son seuil de 0,10 °/s ne peut pas être atteint dans le
> maintien COARSE_SUN sans roues. Les fiches ci-dessous restent dans l'ordre
> des identifiants.

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] COM-001 — Vérification de l'EPS</div>

**Point d'entrée :** début du passage 1 de recette en orbite, satellite stable dans le maintien COARSE_SUN, phase 5, SoC > 70 %.

**Objectif :** établir la référence de la tension du bus, du SoC de la batterie et des performances du générateur, caractériser la décharge en éclipse et la recharge, vérifier un bilan énergétique moyen positif sur l'orbite, et vérifier la régulation du bus sous un transitoire de charge commandé.

**Issues défavorables possibles / écarts :**

- Tension du bus sous 27,0 V → vérifier le SoC ; sous 26,0 V → CTG-001 Délestage sur sous-tension et, avec l'accord du FD, `OBC_SET_MODE(mode=1)` (1 correspond à SAFE)
- Production inférieure à 35 W au soleil avec un bon pointage solaire → lire les courants de chaque aile (0x0146, 0x0147) ; consigner l'anomalie et évaluer un bilan sur une seule aile
- SoC inférieur à 50 % en fin d'éclipse → réduire la charge et reporter la recette des activités gourmandes en énergie

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : référence du bus, de la batterie et du SoC | `HK_REQUEST(sid=1)` (S3.27) ; `GET_PARAM(param_id=0x0100)`, `GET_PARAM(param_id=0x0101)` (S20.3) | □ | Bus (0x0105) 27.5–28.5 V ; `eps.bat_voltage` (0x0100) **26.9–29.2 V** à SoC > 70 % — la batterie est une 8S-1P de 100 Wh, 26.4 V nominaux, avec une tension à vide allant de 21.5 V à 0 % à 29.2 V à 100 %. Toute plage de 14.4–16.8 V est une valeur de batterie 4S et ne concerne pas ce satellite |
| 2 | EPS : mesurer les performances du générateur au soleil | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.power_gen` (0x0107) 40–65 W pointé Soleil, ailes déployées |
| 3 | EPS : suivre une décharge d'éclipse complète | `HK_REQUEST(sid=1)` à l'entrée / à mi-éclipse | □ | Production ≈ 0 W ; SoC en baisse < 1.5 %/min ; bus > 27.0 V |
| 4 | EPS : suivre la recharge après la sortie d'éclipse | `HK_REQUEST(sid=1)` à la sortie + 5 min | □ | `eps.power_gen` (0x0107) > 35 W dans les 60 s suivant la sortie ; `eps.bat_soc` (0x0101) en hausse |
| 5 | EPS : vérifier le bilan énergétique moyen sur l'orbite | `GET_PARAM(param_id=0x0108)` (S20.3) | □ | Production moyenne sur l'orbite > consommation moyenne sur l'orbite ; SoC en fin d'éclipse > 50 % |
| 6 | EPS : régulation du bus sous un transitoire de charge commandé — la ligne du réchauffeur batterie, et non la charge utile | `EPS_POWER_ON(line_index=5)` (S8 func_id 19) ; puis `EPS_POWER_OFF(line_index=5)` (func_id 20) seulement si la ligne était éteinte à l'entrée | □ | Consigner d'abord `eps.pl_htr_bat` (0x0115). Le bus reste à 26.5–29.5 V et revient à 27.0–29.0 V ; ligne revenue à son état d'entrée. La ligne charge utile est OFF jusqu'à COM-009 : une commande de mode de la charge utile ne constitue pas un transitoire |
| 7 | SPACON : consigner les références pour les opérations nominales | (journal de mission) | □ | « COM-001 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[SE] COM-002 — Vérification du TCS</div>

**Point d'entrée :** après la fin et le GO de COM-001 ; maintien COARSE_SUN, phase 5. Consigner d'abord `eps.pl_htr_bat` (0x0115) et `eps.pl_htr_obc` (0x0116) — l'étape 2 de LEOP-007 a pu en alimenter une — comme état d'entrée à rétablir.

**Objectif :** vérifier chaque zone thermique par rapport à sa plage prévue sur une orbite complète, exercer chaque circuit de réchauffeur avec sa ligne alimentée, lire les seuils du thermostat autonome de la batterie et vérifier l'interface du refroidisseur du FPA avant la recette de la charge utile.

**Issues défavorables possibles / écarts :**

- Réchauffeur en marche mais aucune réaction de la zone en 3 min → vérifier que la ligne est réellement alimentée (un réchauffeur dont la ligne est éteinte obéit à l'interrupteur et ne chauffe rien) ; puis CTG-004 Dépassement thermique ; déclarer le réchauffeur suspect
- Seuils du thermostat différents de +5 / +10 °C → émettre un rapport d'anomalie ; cette fiche lit les seuils, elle ne les modifie pas
- Deux réchauffeurs présentant la même signature de défaut → soupçonner un bus commun ; se coordonner avec l'EPS

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Thermique : lire la référence de toutes les zones, puis pendant la phase éclairée et l'éclipse | `HK_REQUEST(sid=3)` (S3.27) | □ | OBC (0x0406) −5…+45 °C ; batterie (0x0407) +5…+35 °C ; FPA (0x0408) +8…+14 °C non refroidi |
| 2 | Thermique : exercer le réchauffeur batterie avec sa ligne alimentée | `EPS_POWER_ON(line_index=5)` (S8 func_id 19) ; `HEATER_BATTERY(on=1)` / `(on=0)` (S8 func_id 40) ; `EPS_POWER_OFF(line_index=5)` seulement si OFF à l'entrée | □ | `eps.pl_htr_bat` (0x0115) = 1 ; température batterie en hausse ou stable en 180 s ; ligne rétablie |
| 3 | Thermique : exercer le réchauffeur de l'OBC avec sa ligne alimentée | `EPS_POWER_ON(line_index=6)` ; `HEATER_OBC(on=1)` / `(on=0)` (S8 func_id 41) ; `EPS_POWER_OFF(line_index=6)` seulement si OFF à l'entrée | □ | `eps.pl_htr_obc` (0x0116) = 1 ; `tcs.temp_obc` stable ou en hausse en 120 s ; ligne rétablie. La fonction 42 est le réchauffeur du lit catalytique du propulseur et reste intouchée hors préparation de manœuvre |
| 4 | Thermique : lire les seuils du thermostat autonome de la batterie | `GET_PARAM(param_id=0x0410)`, `GET_PARAM(param_id=0x0411)` (S20.3) | □ | Mise en marche à +5 °C, arrêt à +10 °C ; entre les deux, l'état précédent est conservé |
| 5 | Thermique : contrôle de l'interface du refroidisseur du FPA (avant activation) | `GET_PARAM(param_id=0x040C)`, `GET_PARAM(param_id=0x0114)` (S20.3) | □ | `tcs.cooler_fpa` = 0 ; `eps.pl_fpa_cooler` = 0 ; consigner la référence du FPA non refroidi pour COM-010 |
| 6 | SPACON : rédiger le rapport de référence thermique | (journal de mission) | □ | Consigner les profils de zone et les réponses des réchauffeurs |
| 7 | SPACON : consigner ; GO COM-004 | (journal de mission) | □ | « COM-002 complete ». COM-004 passe avant COM-003 (décision Q16) |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] COM-003 — Étalonnage des capteurs SCAO</div>

**Point d'entrée :** après COM-004 (décision Q16) : les quatre roues ENABLED (`aocs.wheels_enabled` 0x0260 = 4), AOCS en NOMINAL commandé sur les roues (`aocs.mode` 0x020F = 4, ou 8 en éclipse), senseurs stellaires et gyroscopes OFF, SoC > 60 %, ≥ 20 min de passage restantes.

**Objectif :** intégrer les trois gyroscopes et un senseur stellaire à la boucle de détermination, puis lancer l'étalonnage bord du biais gyroscopique, afin que la voie de vitesse soit compensée avant de demander au satellite de tenir un pointage fin.

**Pourquoi après COM-004.** L'étalonnage est refusé tant que la vitesse angulaire s'écarte de plus de **0,10 °/s** de la référence (`0x0A04`). Dans le maintien COARSE_SUN sans roues, le contrôle par magnétocoupleurs seuls oscille entre 0,1 et 0,4 °/s et n'atteint jamais ce seuil ; le NOMINAL piloté par les roues l'atteint. Le seuil reste à 0,10 °/s.

**Issues défavorables possibles / écarts :**

- Refus avec `0x0A02` → un gyroscope est éteint : lire `aocs.gyro_units_mask` (0x02D1) et l'alimenter avec la commande `S2_AOCS_GYROSCOPE_n` correspondante
- Refus avec `0x0A03` → aucun senseur stellaire dans la boucle : attendre le bit 0 de `aocs.est_source` (0x02C1) (étape 4), ou rétablir le senseur (CTG-008)
- Refus avec `0x0A04` → vitesse angulaire supérieure à 0,10 °/s : attendre la fin du basculement, de la désaturation ou du transitoire de roue (`aocs.mode` ≠ 7) et réessayer
- `AOCS_GYRO_CAL_ABORT` (0x0212) en cours d'arc → rien n'a été appliqué ; corriger la cause indiquée par `aocs.gyro_cal_reject` (0x02D0) et reprendre à l'étape 6
- Biais estimé supérieur à 0,5 °/s sur un axe → ne pas l'accepter ; relancer avec `duration_s=900` ; s'il persiste, émettre un rapport d'anomalie et passer à CTG-029
- Senseur non accroché en 120 s → le statut 3 signifie BLIND (Soleil ou Lune dans le champ), pas une panne ; attendre, ou sélectionner ST2 avec `ST_SELECT(unit=2)`
- Il n'existe ni étalonnage du magnétomètre à bord ni `MAG_SELECT` (la fonction 7 est refusée) : l'unique magnétomètre est utilisé tel quel

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : activer la télémesure de servitude de détermination AOCS | `HK_ENABLE(sid=2)`, `HK_ENABLE(sid=7)` (S3.5) | □ | Le SID 7 transporte les voies d'étalonnage 0x02C9–0x02D0 toutes les 4 s ; sans lui, l'étalonnage se déroule à l'aveugle |
| 2 | AOCS : alimenter les trois gyroscopes | `S2_AOCS_GYROSCOPE_0(device_id=518, state=1)`, `S2_AOCS_GYROSCOPE_1(device_id=519, state=1)`, `S2_AOCS_GYROSCOPE_2(device_id=520, state=1)` (S2.1) | □ | `aocs.gyro_units_on` (0x0294) = 3 ; `aocs.gyro_units_mask` (0x02D1) = 7 (bit 0 X, bit 1 Y, bit 2 Z). Ni unité redondante ni ligne d'alimentation IMU |
| 3 | AOCS : alimenter les deux senseurs stellaires, sélectionner ST1 | `ST1_POWER(on=1)` (func_id 4), `ST2_POWER(on=1)` (func_id 5), `ST_SELECT(unit=1)` (func_id 6) | □ | 1 = ST1, 2 = ST2, 0 est refusé. `aocs.st1_status` (0x0240) = 2 et `aocs.st1_num_stars` (0x0241) ≥ 5 en 120 s ; `aocs.st2_status` (0x0243) = 2 |
| 4 | AOCS : attendre le bit 0 de `aocs.est_source` — aucune commande de mode | (observation) | □ | Rester dans le NOMINAL laissé par COM-004. Bit 0 de `aocs.est_source` (0x02C1) (aide du senseur stellaire) positionné en 600 s ; `aocs.knowledge_err_3sig` (0x02A7) < 300 arcsec. La condition `0x0A03` est ce bit, et non le mode |
| 5 | AOCS : consigner le biais avant étalonnage | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.gyro_bias_x/y/z` (0x0270–0x0272) et `aocs.gyro_bias_resid` (0x02D2) ; quelques 1e-5 °/s sur une unité saine |
| 6 | AOCS : lancer l'étalonnage du biais gyroscopique À BORD | `AOCS_GYRO_CALIBRATION(action=0, duration_s=300)` (S8 func_id 13) | □ | `aocs.gyro_cal_state` (0x02C9) = 1 (RUNNING) en 20 s. Les codes de refus `0x0A01`–`0x0A05` sont mémorisés dans 0x02D0 ; le S1.7 arrive à la fin de l'arc. Il n'y a pas d'envoi d'un biais calculé au sol |
| 7 | AOCS : suivre l'arc de 300 s — ni basculement, ni désaturation, ni changement de mode | `HK_REQUEST(sid=7)` (S3.27) toutes les 30 s | □ | `aocs.gyro_cal_progress` (0x02CA) ≥ 100 en 330 s |
| 8 | AOCS : vérifier le résultat et consigner le biais | `GET_PARAM(param_id=0x02CB)` … `(param_id=0x02CD)` (S20.3) | □ | `aocs.gyro_cal_state` = 2 (COMPLETE), `aocs.gyro_cal_result` (0x02CF) = 1 ; chaque axe à ±0,5 °/s |
| 9 | AOCS : confirmer que la compensation a pris effet | `HK_REQUEST(sid=2)`, `HK_REQUEST(sid=7)` (S3.27) | □ | `aocs.gyro_bias_resid` (0x02D2) < 0,005 °/s ; `aocs.gyro_cal_comp_mag` (0x02CE) consigné |
| 10 | AOCS : contrôle de la détermination sur cinq minutes ; consigner ; GO COM-005 | `HK_REQUEST(sid=7)` (S3.27) toutes les 60 s pendant 5 min | □ | `aocs.knowledge_err_3sig` < 120 arcsec ; `aocs.control_err` (0x02A8) < 1,0°. « COM-003 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] COM-004 — Vérification des actionneurs SCAO</div>

**Point d'entrée :** passage 1 de recette en orbite, après le GO de COM-002 et **avant** COM-003 (décision Q16). AOCS dans le maintien COARSE_SUN de la LEOP (`aocs.mode` 0x020F = 3, ou 8 en éclipse), roues DISABLED, senseurs stellaires et gyroscopes OFF, vitesses angulaires < 0,5 °/s, `eps.pl_aocs_wheels` (0x0117) = 1 depuis LEOP-007, SoC > 65 %, ≥ 20 min de passage restantes.

**Objectif :** **activer les quatre roues de réaction** — aucune autre procédure du catalogue ne le fait — et commander le NOMINAL piloté par les roues ; puis faire monter et redescendre chaque roue en vitesse par rapport à sa référence, lire les températures des roues et répéter une désaturation magnétique. COM-003 étalonne ensuite les gyroscopes dans ce NOMINAL.

**C'est cette fiche qui confie l'autorité d'attitude aux roues.** Le chargeur d'amorçage démarre le satellite avec toutes les roues **DISABLED** et les laisse ainsi. Alimenter la ligne EPS `aocs_wheels` n'alimente que l'électronique de commande ; cette séparation est voulue, pour qu'une commutation de ligne d'alimentation ne puisse jamais rendre silencieusement l'autorité de commande à la boucle. Si l'on saute cette fiche, `aocs.wheels_enabled` (0x0260) reste à 0, NOMINAL et FINE_POINT n'ont aucun actionneur, et la règle FDIR sur `aocs.wheels_enabled < 2` fait passer l'AOCS en sécurité dès que la phase de mission atteint NOMINAL.

**Issues défavorables possibles / écarts :**

- Une roue n'indique pas son activation → réessayer une fois ; si elle reste désactivée, poursuivre avec les roues restantes — trois suffisent (`aocs.fine_degraded`, 0x0299) —, mais **ne pas quitter cette fiche avec moins de trois roues activées**
- Une roue n'atteint pas le biais commandé en 90 s → réduire le biais d'essai à +1000 tr/min à des fins de diagnostic ; vérifier `eps.pl_aocs_wheels` (0x0117) et `eps.line_current_7` (0x011F) ; si l'alimentation est nominale, déclarer la roue défaillante et appliquer CTG-007
- Température de roue > +55 °C pendant l'essai → arrêter cette roue, 10 min de refroidissement, revérifier avant de reprendre
- Erreur d'attitude > 10° pendant un essai de roue → arrêter immédiatement avec `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0.0)` — 255 désigne toutes les roues — et laisser l'attitude se rétablir avant de reprendre
- La désaturation ne réduit pas les vitesses des roues → vérifier `aocs.mtq_enabled` (0x025E) ; l'autorité magnétique est la plus faible près de l'équateur, réessayer donc lors d'un passage polaire

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : activer les quatre roues de réaction, une commande par roue | `AOCS_ENABLE_WHEEL(wheel_idx=0)`, `(wheel_idx=1)`, `(wheel_idx=2)`, `(wheel_idx=3)` (S8 func_id 3) | □ | `aocs.wheels_enabled` (0x0260) = 4 et `aocs.rw1_enabled`…`rw4_enabled` (0x0254–0x0257) = 1 en 10 s. Aucune autre commande du catalogue n'active une roue |
| 2 | AOCS : commander le NOMINAL piloté par les roues | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 4 (ou 8 en éclipse) en 300 s ; `aocs.commanded_mode` (0x0297) = 4. Accepté sans senseur stellaire : la connaissance d'attitude reste sur la voie grossière Soleil–magnétomètre jusqu'à COM-003 |
| 3 | AOCS : consigner les vitesses de référence des roues | `HK_REQUEST(sid=2)` (S3.27) | □ | 0x0207–0x020A ; les roues tout juste activées reprennent aussitôt la charge de contrôle, des vitesses non nulles sont donc normales — cette référence sert à tous les contrôles ci-dessous |
| 4 | AOCS : faire monter chaque roue en vitesse, la faire passer par zéro et revenir | `RW_SET_SPEED_BIAS(wheel_idx=N, bias_rpm=2000.0)`, puis `(bias_rpm=-4000.0)` (S8 func_id 8) | □ | Le biais **s'ajoute à la vitesse courante de la roue**. Référence +1800…+2200 tr/min en 60 s, puis référence −2200…−1800 tr/min en 120 s ; `aocs.att_error` (0x0217) < 5° tout du long |
| 5 | AOCS : ramener chaque roue à zéro | `AOCS_RW_RAMP_DOWN(wheel_idx=N, target_rpm=0.0)` (S8 func_id 14) | □ | < 100 tr/min en 60 s. Les vitesses 0x0207–0x020A sont en LECTURE SEULE — elles ne peuvent pas être réglées avec `SET_PARAM` |
| 6 | AOCS : lire les températures des roues | `GET_PARAM(param_id=0x0218)`…`(0x021B)` (S20.3) | □ | −10…+55 °C. 0x028A–0x028D sont les pourcentages de santé des têtes CSS, **pas** des températures de roues |
| 7 | AOCS : répétition de désaturation sur les magnétocoupleurs | `AOCS_DESATURATE` (S8 func_id 1) | □ | Vitesses tendant vers 0 tr/min ; `aocs.att_error` < 5°. Prévoir honnêtement une fenêtre de déchargement de **20–50 min** (voir CTG-007), et non les cinq à dix qu'une note de répétition pourrait suggérer |
| 8 | SPACON : rédiger le rapport de recette des roues ; consigner ; GO COM-003 | (journal de mission) | □ | « COM-004 complete » ; postcondition `aocs.wheels_enabled` (0x0260) = 4, AOCS en NOMINAL commandé |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] COM-005 — Transitions de modes SCAO</div>

**Point d'entrée :** après le GO de COM-003 : roues activées (`aocs.wheels_enabled` 0x0260 = 4 ; trois est acceptable, en mode dégradé), senseur stellaire dans la boucle, gyroscopes étalonnés, AOCS déjà en NOMINAL commandé (mode 4, ou 8 en éclipse) depuis COM-004.

**Objectif :** exercer chaque transition **commandée** utilisée par le concept d'opérations — NOMINAL → FINE_POINT → NOMINAL, NOMINAL → INERTIAL → NOMINAL, le maintien COARSE_SUN, la désaturation — et **observer** les transitions automatiques : le retour depuis le maintien, le passage en éclipse et la fin de DESAT. Commander ce qui se commande, attendre et vérifier ce qui est automatique, et ne jamais vérifier le mode que l'on vient de quitter.

**Issues défavorables possibles / écarts :**

- `AOCS_SET_MODE(mode=5)` refusée avec `0x0A22` → lire `aocs.fine_ready` (0x02C5) : un masque non nul désigne la condition non remplie (bit 0 ST < 5 étoiles, bit 1 moins de TROIS roues, bit 2 MEKF non convergé, bit 3 vitesses élevées, bit 4 moment cinétique ≥ 70 %, bit 5 propagation seule ou éclipse, bit 6 basculement non inactif depuis 60 s) ; en éclipse, attendre l'arc éclairé
- Pas de promotion automatique hors de COARSE_SUN dans la fenêtre → vérifier la validité des CSS (l'éclipse la bloque), `aocs.att_error` < 15° et la poursuite du senseur stellaire ; rétablir le senseur (CTG-008) plutôt que forcer le mode
- DESAT se termine avec `aocs.desat_ineffective` (0x029C) = 1 → l'autorité des magnétocoupleurs n'a pas suffi à temps ; recommencer sur un arc polaire
- Les vitesses remontent lors d'une transition → CTG-002 Anomalie SCAO

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : verrouiller le mode commandé | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | Déjà en mode 4 depuis COM-004 ; la commande verrouille `aocs.commanded_mode` (0x0297) = 4. Mode 4 ou 8 ; erreur < 1,0° en 600 s sur le côté éclairé |
| 2 | AOCS : NOMINAL → FINE_POINT par sa condition d'entrée | `AOCS_FINE_READY_CHECK` (S8 func_id 89) ; `AOCS_SET_MODE(mode=5)` (S8 func_id 0) | □ | D'abord `aocs.fine_ready` (0x02C5) = 0 ; puis mode 5 en 30 s, erreur < 0,1° en 300 s |
| 3 | AOCS : FINE_POINT → NOMINAL | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | Mode 4 en 30 s ; `aocs.commanded_mode` = 4 |
| 4 | AOCS : NOMINAL → INERTIAL et retour | `AOCS_SET_MODE(mode=9)`, puis `(mode=4)` (S8 func_id 0) | □ | Mode 9 en 30 s, puis mode 4 en 30 s. INERTIAL est le seul mode opérationnel qui se maintient à travers le terminateur |
| 5 | AOCS : commander le maintien COARSE_SUN, puis attendre le retour automatique | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | Mode 3 et `aocs.mode_demoted` (0x0298) = 1 en 30 s ; puis mode 4 de lui-même en 1800 s et l'indicateur de rétrogradation revenu à 0. Vérifier le mode PROMU, et non le mode 3 |
| 6 | AOCS : observer le passage en éclipse dans l'archive | (archive) | □ | Mode 4 ↔ 8 au terminateur, avec `aocs.commanded_mode` = 4 tout du long ; aucune commande |
| 7 | AOCS : désaturation, qui se termine d'elle-même | `AOCS_DESATURATE` (S8 func_id 1) | □ | Mode 7 (DESAT) en 30 s, puis retour au mode 4 en 900 s sans commande |
| 8 | SPACON : archiver la matrice des transitions ; consigner ; GO COM-006 | (journal de mission) | □ | Chaque ligne commandée porte sa TC et sa vérification, chaque ligne automatique son déclencheur et son heure. « COM-005 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] COM-006 — Vérification de la liaison TTC</div>

**Point d'entrée :** passage 1 de recette en orbite, après le GO de COM-005.

**Objectif :** configurer la chaîne en bande S pour la mesure, établir la référence de la marge de liaison sur les deux paliers opérationnels de l'échelle de débits TM, démontrer les conditions d'accès au palier HIGH, solliciter le transpondeur redondant et laisser la liaison en configuration sûre sur LOW.

**Issues défavorables possibles / écarts :**

- `TTC_SET_DATA_RATE(rate=1)` refusée avec l'erreur S1.8 `0x0007` → lire l'avis d'échec, qui nomme textuellement la condition non satisfaite (beacon mode latched / antenna stowed / DOWNLINK mode off / elevation < 10°) ; les quatre renvoient le même code
- Marge en HIGH inférieure à la prédiction → reporter les vidages à haut débit jusqu'à investigation ; consigner dans une fiche
- Verrouillage du récepteur instable lors d'un basculement de transpondeur → CTG-003 Rétablissement après perte de liaison TTC ; CTG-014 pour une anomalie de TEB

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | TT&C : alimenter la ligne de l'émetteur et l'amplificateur de puissance | `EPS_POWER_ON(line_index=2)` (S8 func_id 19) ; `TTC_PA_ON` (S8 func_id 66) | □ | `eps.pl_ttc_tx` (0x0112) = 1 ; `ttc.pa_on` (0x0516) = 1 |
| 2 | TT&C : libérer le palier balise forcé et déployer l'antenne | `TTC_SET_BEACON_MODE(on=0)` (func_id 70) ; `TTC_DEPLOY_ANTENNA` (func_id 69) | □ | `ttc.beacon_mode` (0x0521) = 0 ; `ttc.antenna_deployed` (0x0520) = 1 ; `ttc.tx_active` (0x0525) = 1 |
| 3 | TT&C : établir la référence du palier LOW | `TTC_SET_DATA_RATE(rate=0)` (S8 func_id 65) | □ | `ttc.tm_data_rate` (0x0506) = 16000 bit/s, `ttc.tm_tier` (0x0539) = 1 ; marge 55–59 dB à 30° |
| 4 | TT&C : passer en mode DOWNLINK, puis établir la référence HIGH | `TTC_SET_DOWNLINK_MODE(on=1)` (func_id 79) ; `TTC_SET_DATA_RATE(rate=1)` (func_id 65) | □ | 128000 bit/s, palier 2, `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (QPSK) ; marge 45–48 dB — un échelon de 10.5 ± 0.5 dB |
| 5 | TT&C : démontrer la condition d'élévation | `TTC_SET_DATA_RATE(rate=1)` sous 10° d'élévation | □ | REJETÉE avec l'erreur S1.8 `0x0007` ; la liaison reste en LOW |
| 6 | TT&C : basculer sur le transpondeur redondant et revenir | `TTC_SWITCH_REDUNDANT` (func_id 64) ; `TTC_SWITCH_PRIMARY` (func_id 63) | □ | `ttc.link_status` (0x0501) = 2 en 60 s dans chaque sens ; RSSI à 2 dB près |
| 7 | TT&C : mettre la liaison en configuration sûre ; consigner les résultats | `TTC_SET_DATA_RATE(rate=0)` ; `TTC_SET_DOWNLINK_MODE(on=0)` | □ | `ttc.tm_tier` = `ttc.tm_tier_cmd` (0x053A) = 1 ; le PA reste ON ; « COM-006 complete » |

**Remarque — deux émetteurs.** L'émetteur principal en bande S et la balise UHF à antenne fouet sont distincts. `TTC_PA_OFF` (func_id 67) arrête la TM en bande S (`ttc.tx_active` → 0) tandis que la balise continue d'émettre le SID 11 : le satellite peut être muet sur la chaîne principale et toujours vivant sur la balise. Ne concluez pas à la perte du satellite parce que la liaison descendante en bande S est muette.

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] COM-007 — Vérification de l'OBDH</div>

**Point d'entrée :** après COM-006 : AOCS en NOMINAL commandé, liaison descendante en LOW avec l'antenne déployée, OBC en NOMINAL (`obdh.mode` 0x0300 = 0), SoC > 60 %.

**Objectif :** vérifier la charge du processeur, la mémoire et les compteurs de paquets, la génération autonome de HK et le chien de garde, exercer l'excursion de mode de l'OBC NOMINAL → SAFE → NOMINAL, et **terminer en NOMINAL**.

**Issues défavorables possibles / écarts :**

- Chien de garde indiqué désarmé ou cause de réinitialisation inattendue → CTG-010 Reprise après chien de garde de l'OBDH
- Compteur d'erreurs mémoire ou de SEU en hausse entre deux lectures → CTG-016 Défaillance d'un segment mémoire ; reporter la mise sous tension de la charge utile
- La transition de mode échoue → réessayer une fois ; si NOMINAL reste inaccessible, ne poursuivre en SAFE qu'avec l'accord du FD et émettre un rapport d'anomalie

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | OBDH : vérifier le mode de l'OBC | `HK_REQUEST(sid=4)` (S3.27) | □ | `obdh.mode` (0x0300) = 0 (NOMINAL). Codage : 0 NOMINAL, 1 SAFE, 2 EMERGENCY |
| 2 | OBDH : vérifier la charge du processeur | `GET_PARAM(param_id=0x0302)` (S20.3) | □ | `obdh.cpu_load` 10–50 % |
| 3 | OBDH : vérifier la santé de la mémoire | `GET_PARAM(param_id=0x0303)`, `GET_PARAM(param_id=0x031E)`, `GET_PARAM(param_id=0x0319)` (S20.3) | □ | `obdh.mmm_used` < 70 % ; `obdh.mem_errors` et `obdh.seu_count` relevés comme référence et stables entre deux lectures |
| 4 | OBDH : vérifier les compteurs de TC et de TM | `GET_PARAM(param_id=0x0304)`, `GET_PARAM(param_id=0x0306)`, `GET_PARAM(param_id=0x0307)` (S20.3) | □ | TC reçues conformes au journal sol ; TC rejetées = 0 ; TM générées en hausse |
| 5 | OBDH : vérifier la génération autonome de HK | `GET_PARAM(param_id=0x0307)` avant et après un intervalle | □ | `obdh.tm_pkt_count` a augmenté |
| 6 | OBDH : vérifier le chien de garde et la dernière cause de réinitialisation | `OBC_DIAGNOSTIC` (S8 func_id 61) ; `GET_PARAM(param_id=0x0316)` (S20.3) | □ | Réponse du diagnostic : chien de garde armé ; `obdh.last_reboot_cause` = 0 (aucune) |
| 7 | OBDH : excursion de mode NOMINAL → SAFE → NOMINAL | `OBC_SET_MODE(mode=1)`, puis `OBC_SET_MODE(mode=0)` (S8 func_id 50) | □ | `obdh.mode` = 1 en 15 s, puis 0 en 15 s. La fiche ne doit pas se terminer en SAFE |
| 8 | SPACON : consigner la référence de l'OBDH ; consigner ; GO COM-008 | (journal de mission) | □ | « COM-007 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] COM-008 — Configuration de la FDIR et fonctions de protection</div>

**Point d'entrée :** après le GO de COM-007 : OBC en NOMINAL (`obdh.mode` 0x0300 = 0), AOCS en NOMINAL commandé, liaison descendante en LOW, lignes charge utile et refroidisseur OFF, aucun verrouillage de délestage (`eps.load_shed_stage` 0x0134 = 0), SoC > 70 %, marge de liaison > 6 dB, accord du FD pour l'essai des fonctions de protection.

**Objectif :** confirmer que la pile de protection de bord est configurée et vivante avant que la charge utile vole : le service de surveillance S12 et ses définitions, la table événement-action S19, la télémesure de synthèse FDIR, et l'échelle de délestage commandée avec son verrouillage. La fiche se termine exactement dans l'état où elle a commencé.

**Issues défavorables possibles / écarts :**

- TM(12,13) ou TM(19,128) vide, ou définitions manquantes → recharger depuis la base de données d'exploitation (`MON_ADD_DEF` / `EA_ADD` selon l'enregistrement de la base) et redemander le rapport
- `eps.load_shed_stage` ne se verrouille pas à l'étape 4, ou l'étage 0 réalimente une ligne → régression du traitement du délestage ; la consigner, escalader, et ne pas passer à la recette de la charge utile
- `fdir.level` (0x0700) ≠ 0 à l'étape 3 ou 5 → lire le journal FDIR et supprimer la cause sous-jacente ; ne jamais désactiver la règle pour valider la fiche

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | SPACON : activer et inventorier le service de surveillance S12 | `MON_ENABLE` (S12.1) ; `MON_REPORT_DEFS` (S12.12) | □ | TM(12,13) en 10 s : `count`, puis un enregistrement par définition (`mon_id`, `param_id`, `check_type`, `enabled`, limites). Comparer à la base de données d'exploitation : toutes les définitions livrées présentes, aucune inattendue |
| 2 | SPACON : inventorier la table événement-action S19 | `EA_REPORT_DEFS` (S19.8) | □ | TM(19,128) en 10 s. La chaîne de gestion du moment cinétique (surveillance S12 sur `aocs.h_env_frac` 0x02BA → ea_id 2001 → fonction S8 1) et la chaîne de mise en sécurité en surchauffe du TCS (ea 3003) présentes et activées |
| 3 | SPACON : lire la télémesure de synthèse FDIR | `GET_PARAM(param_id=0x0700)`, `GET_PARAM(param_id=0x0701)` (S20.3) | □ | `fdir.level` = 0 et `fdir.active_alarms` = 0 : une référence propre pour l'essai fonctionnel |
| 4 | EPS : essai fonctionnel du verrouillage de délestage commandé | `EPS_EMERGENCY_LOAD_SHED(stage=1)`, puis `(stage=0)` (S8 func_id 25) | □ | Consigner d'abord les indicateurs de ligne. Étage 1 : `eps.load_shed_stage` = 1 en 5 s (il se VERROUILLE), événement `LOAD_SHED_STAGE_1` (0x0106), `eps.pl_payload` (0x0113) = 0. Étage 0 : verrouillage revenu à 0, et aucune ligne réalimentée. Ne jamais commander l'étage 2 ou 3 ici : l'étage 3 coupe `ttc_tx` et fait tomber cette liaison descendante |
| 5 | SPACON : confirmer l'absence d'état de protection résiduel ; consigner ; GO du FD pour COM-009 | `GET_PARAM(param_id=0x0700)` (S20.3) ; `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` (S3.27) | □ | `fdir.level` = 0 ; `eps.load_shed_stage` = 0 ; `obdh.mode` = 0 (NOMINAL) — cette fiche ne fait aucune excursion de mode de l'OBC. « COM-008 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[PE] COM-009 — Mise sous tension de la charge utile</div>

**Point d'entrée :** passage 3 de recette en orbite, après COM-008, avec le jeu FDIR nominal armé ; SoC > 75 %, production > 40 W.

**Objectif :** alimenter la ligne charge utile, amener l'imageur en STANDBY au courant attendu et confirmer qu'il s'y MAINTIENT.

**Issues défavorables possibles / écarts :**

- Surintensité sur la ligne charge utile dans les 2 s → CTG-012 Traitement d'une surintensité (ouverture autonome de la ligne) ; analyser la cause avant toute nouvelle tentative
- La charge utile n'atteint pas STANDBY, ou ne s'y maintient pas → CTG-006 Anomalie charge utile ; couper puis remettre la ligne après 30 s ; en cas de récidive, reporter COM-010
- La température de la charge utile monte plus vite que prévu → recouper avec le poste Thermique ; un défaut du refroidisseur peut suivre

**Arbre de décision :**

- SI mise sous tension propre ET `payload.mode` = 1 maintenu pendant 60 s ET hausse de consommation dans l'enveloppe → GO COM-010
- SI la FDIR ouvre la ligne → CTG-012 ; investigation avant toute nouvelle tentative
- SI le mode n'atteint pas STANDBY en 60 s → couper/remettre une fois, puis faire remonter l'anomalie

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | SPACON : GO du FD pour la mise sous tension de la charge utile | (annonce du FD) | □ | Double validation |
| 2 | Charge utile : confirmer que la charge utile est OFF | `HK_REQUEST(sid=5)` (S3.27) | □ | `payload.mode` (0x0600) = 0 |
| 3 | EPS : alimenter la ligne charge utile | `EPS_POWER_ON(line_index=3)` (S8 func_id 19) | □ | `eps.pl_payload` (0x0113) = 1 |
| 4 | Charge utile : commander STANDBY | `PAYLOAD_SET_MODE(mode=1)` (S8 func_id 26) | □ | `payload.mode` = 1 en 60 s, et TOUJOURS 1 après 60 s supplémentaires |
| 5 | EPS : vérifier la hausse de consommation | `GET_PARAM(param_id=0x0106)` (S20.3) — `eps.power_cons` | □ | +2–3 W ; bus (0x0105) > 27.0 V |
| 6 | Charge utile : vérifier la santé de l'imageur et le stockage | `payload.imager_status` (0x0611) ; `payload.store_used` (0x0604) ; `payload.product_count` (0x0648) | □ | Aucun bit de défaut ; stockage occupé à ~20 % (livré avec des données d'archive de démonstration) ; nombre de produits 0 |
| 7 | SPACON : attendre ≥ 30 s la stabilisation du transitoire ; consigner ; GO COM-010 | (journal de mission) | □ | « COM-009 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[SE] COM-010 — Activation du refroidisseur du FPA</div>

**Point d'entrée :** passage 3 de recette en orbite, immédiatement après le GO de COM-009 ; FPA à l'équilibre non refroidi (+8 à +14 °C), charge utile en STANDBY.

**Objectif :** amener le FPA de la température ambiante à la **consigne par défaut de −15 °C** et confirmer qu'il y est régulé, avec une marge positive du refroidisseur.

*(EOSAT-1 embarque un **cryoréfrigérateur miniature de type Stirling**, et
non un empilement thermoélectrique. Son autorité se dégrade avec l'écart
de température à franchir — `fpa_cooler_carnot_fraction` = 0.23 —, de sorte
que la température plancher atteignable dépend de la température du puits
thermique et de la charge de prise de vue. L'enveloppe de consigne commandable
va de **−20 °C à 0 °C** ; un véritable imageur multispectral descendrait
beaucoup plus bas, et cette fiche adopte l'enveloppe de vol.)*

**Issues défavorables possibles / écarts :**

- La mise en froid plafonne au-dessus de la consigne → lire `payload.cooler_margin_k` (0x064B) : une valeur ≤ 0 signifie que le refroidisseur ne peut physiquement pas atteindre la consigne commandée avec le puits et la charge actuels, et la réponse est une **consigne plus chaude, pas une attente plus longue** (`payload.cooler_floor_c`, 0x064A ; recopies TCS en 0x0424 / 0x0425)
- Anomalie de radiateur suspectée → se coordonner avec le poste Thermique ; vérifier les températures de la zone radiateur
- Le courant du refroidisseur augmente → CTG-012 si la FDIR de ligne se déclenche

**Arbre de décision :**

- SI `payload.fpa_ready` (0x0610) = 1 en ~15 min → GO COM-011
- SI marge ≤ 0 → le FD décide : (a) commander une consigne plus chaude et poursuivre avec un RSB dégradé, ou (b) abandonner et replanifier
- SI la FDIR de la ligne du refroidisseur ouvre la ligne → CTG-012 ; le FPA se réchauffe passivement ; la charge utile est en sécurité

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Thermique : consigner l'état avant activation | `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=5)` (S3.27) | □ | `payload.fpa_temp` (0x0601) +8…+14 °C ; `payload.mode` = 1 |
| 2 | Thermique : activer le refroidisseur du FPA | `FPA_COOLER(on=1)` (S8 func_id 43) | □ | `tcs.cooler_fpa` (0x040C) = 1 ET `eps.pl_fpa_cooler` (0x0114) = 1 — la fonction 43 garantit aussi l'alimentation de la ligne |
| 3 | EPS : vérifier la consommation du refroidisseur | `GET_PARAM(param_id=0x0106)` (S20.3) | □ | +14–16 W ; bus > 27.0 V |
| 4 | Thermique : surveiller la mise en froid | `GET_PARAM(param_id=0x0601)` (S20.3) à T+2 / T+5 min | □ | < +4 °C à T+2 (≈ 4 °C/min au début) ; < −8 °C à T+5 |
| 5 | Thermique : confirmer que la consigne est atteinte | `GET_PARAM(param_id=0x0601)` à T+10 / T+15 min | □ | −16.0…−14.0 °C ; `payload.fpa_setpoint` (0x0631) = −15.0 |
| 6 | Thermique : confirmer la disponibilité et la marge | `payload.fpa_ready` (0x0610) = 1 ; `payload.cooler_margin_k` (0x064B) > 0 | □ | La disponibilité suit la consigne ACTIVE, pas une valeur fixe |
| 7 | Thermique : attendre 30 min et contrôler la stabilité, y compris pendant l'éclipse | `GET_PARAM(param_id=0x0601)` (S20.3) | □ | −16.5…−14.5 °C, < 1.0 °C crête à crête |
| 8 | SPACON : consigner ; GO COM-011 | (journal de mission) | □ | « COM-010 complete » |

**Remarque.** Pour commander une autre consigne, utiliser `PAYLOAD_COOLER_SETPOINT(setpoint=-15)` (S8 func_id 36). L'argument est un uint16 en **centikelvins** — −15.00 °C se code 25815 = 0x64D7 — et une valeur hors de [−20, 0] °C est rejetée avec l'erreur S1.8 `0x0003`.

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[PE] COM-011 — Étalonnage de la charge utile</div>

**Point d'entrée :** passage 4 de recette en orbite, FPA régulé dans la plage −16.5…−14.5 °C avec `payload.fpa_ready` = 1, charge utile en STANDBY.

**Objectif :** acquérir une série d'images d'obscurité et une série de champs plats avec la lampe interne, puis capturer une série d'images d'un site d'étalonnage en FINE_POINT.

**Issues défavorables possibles / écarts :**

- `PAYLOAD_START_CALIBRATION` refusée → lire le code : `0x0024` refus car la charge utile est en IMAGING, `0x0025` FPA non prêt, `0x0026` obturateur dans la mauvaise position, `0x0027` lampe dans le mauvais état, `0x0028` capture avec l'obturateur fermé. L'étalonnage d'obscurité n'exige plus le mode IMAGING — la condition porte sur l'optique
- `cal_abort_reason` (0x0645) non nul → la séquence ne s'est pas achevée ; refaire l'acquisition après avoir vérifié la stabilité du FPA
- FINE_POINT refusé → lire `aocs.fine_ready` (0x02C5) ; reporter au passage suivant

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Charge utile : vérifier l'état avant étalonnage | `HK_REQUEST(sid=5)` (S3.27) | □ | Mode 1 ; `payload.fpa_ready` (0x0610) = 1 ; stockage libre > 1000 Mo (0x060A − 0x060B) |
| 2 | Charge utile : fermer l'obturateur, lampe éteinte | `PAYLOAD_SET_SHUTTER(position=0)` (func_id 119) ; `PAYLOAD_CAL_LAMP(on=0)` (func_id 95) | □ | `payload.shutter_pos` (0x063C) = 0 |
| 3 | Charge utile : exécuter la phase DARK | `PAYLOAD_START_CALIBRATION(mode=0)` (S8 func_id 37) | □ | `payload.mode` (0x0600) = 3 (CALIBRATION) ; `payload.calibration_active` (0x062A) 1 → 0 ; `cal_abort_reason` (0x0645) = 0 |
| 4 | Charge utile : ouvrir l'obturateur, allumer la lampe, exécuter la phase FLAT | `PAYLOAD_SET_SHUTTER(position=1)` ; `PAYLOAD_CAL_LAMP(on=1)` ; `PAYLOAD_START_CALIBRATION(mode=1)` | □ | `payload.cal_valid_mask` (0x0646) = 15 — les quatre bandes |
| 5 | Charge utile : revenir en STANDBY, lampe éteinte | `PAYLOAD_CAL_LAMP(on=0)` ; `PAYLOAD_SET_MODE(mode=1)` (func_id 26) | □ | Obturateur OPEN, mode 1 |
| 6 | AOCS : passer en FINE_POINT pour le survol du site | `AOCS_FINE_READY_CHECK` (func_id 89) ; `AOCS_SET_MODE(mode=5)` (func_id 0) | □ | `aocs.fine_ready` (0x02C5) = 0 ; erreur < 0.1° |
| 7 | Charge utile : capturer la série du site d'étalonnage | `PAYLOAD_SET_MODE(mode=2)` ; `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (func_id 28) | □ | `payload.last_scene_id` (0x060C) s'incrémente ; faire varier le temps d'intégration avec `PAYLOAD_SET_INTEGRATION_TIME` (func_id 34) — le RSB varie d'environ 3 dB par doublement |
| 8 | Charge utile / AOCS : rétablir la configuration standard | `PAYLOAD_SET_MODE(mode=1)` ; `AOCS_SET_MODE(mode=4)` | □ | Mode 1 ; `aocs.mode` = 4 |
| 9 | SPACON : consigner ; GO du FD pour COM-012 | (journal de mission) | □ | « COM-011 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[MULTI] COM-012 — Première lumière</div>

**Point d'entrée :** après COM-010 — COM-012 passe **avant** COM-011, car l'étalonnage exige une chaîne de prise de vue vérifiée. Charge utile en STANDBY, refroidisseur en marche avec `payload.fpa_ready` (0x0610) = 1 à −15 °C, AOCS en NOMINAL commandé, liaison descendante en LOW, SoC > 70 %, à l'approche d'une cible sol connue. La procédure phare.

**Objectif :** acquérir la première image scientifique, vérifier qu'elle est stockée, et la transmettre au sol par la vraie chaîne du service 13 pour une première évaluation de qualité.

**Issues défavorables possibles / écarts :**

- `payload.last_scene_quality` (0x060D) médiocre → CTG-015 Reprise d'une image corrompue ; nouvelle acquisition au passage suivant
- Erreur de pointage > 0.1° pendant l'intégration → image probablement floue ; la marquer et recommencer
- Cascade AOCS / charge utile (le senseur stellaire tombe en panne tardivement) → CTG-008 → CTG-002, reporter la première lumière, ne pas tenter de répétition pendant ce quart
- Le transfert démarre mais le sol signale des trames manquantes → CTG-014 Anomalie de TEB ; rouvrir le transfert

**Arbre de décision :**

- SI image acquise ET stockée ET transfert S13 terminé avec une somme de contrôle correcte → déclarer la **première lumière**
- SI le produit est corrompu une fois → CTG-015 ; réessayer au passage suivant (3 tentatives au maximum selon la règle du FD)
- SI anomalie en cascade AOCS / charge utile → report formel ; informer le responsable de mission

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : passer en FINE_POINT par sa condition d'entrée | `AOCS_FINE_READY_CHECK` (S8 func_id 89) ; `AOCS_SET_MODE(mode=5)` (S8 func_id 0) | □ | `aocs.mode` = 5 en 30 s ; `aocs.total_pointing_err_3sig` (0x02AA) < 0.05° en 300 s ; `aocs.att_error` (0x0217) < 0.1° |
| 2 | Charge utile : vérifier la température du FPA et la disponibilité | `GET_PARAM(param_id=0x0601)` (S20.3) ; `HK_REQUEST(sid=5)` (S3.27) | □ | `payload.fpa_temp` −16.5…−14.5 °C ; `payload.mode` (0x0600) = 1 ; consigner `payload.image_count` (0x0605) et `payload.mem_used_mb` (0x060B) comme références |
| 3 | Charge utile : commander IMAGING | `PAYLOAD_SET_MODE(mode=2)` (S8 func_id 26) | □ | `payload.mode` = 2 en 30 s |
| 4 | Charge utile : déclencher l'acquisition | `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8 func_id 28) | □ | `payload.last_scene_id` (0x060C) = 1 en 30 s ; `payload.image_count` incrémenté. La géolocalisation est horodatée à bord, ce n'est pas un argument |
| 5 | Charge utile : confirmer que le produit est stocké | `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x060B)` (S20.3) | □ | `payload.store_used` en hausse ; `payload.mem_used_mb` en hausse de 1.0–4.0 MB par rapport à la référence de l'étape 2 (4 MB brut, 1.0–2.7 MB compressé) |
| 6 | Charge utile : revenir en STANDBY | `PAYLOAD_SET_MODE(mode=1)` (S8 func_id 26) | □ | `payload.mode` = 1 en 15 s ; le refroidisseur continue de tourner |
| 7 | TT&C + charge utile : transmettre le produit par S13 | `TTC_SET_DOWNLINK_MODE(on=1)` ; `TTC_SET_DATA_RATE(rate=1)` ; `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)` ; `S13_END_TRANSFER(transfer_id=T)` ; puis `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)` | □ | `ttc.tm_data_rate` (0x0506) = 128000 bit/s ; `payload.transfer_active` (0x062D) = 1, `payload.transfer_progress` (0x062E) en hausse, puis 0x062D = 0 ; CRC-32 au sol ; retour à 16000 bit/s |
| 8 | AOCS : quitter FINE_POINT ; le FD déclare la première lumière | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | `aocs.mode` = 4 en 30 s ; charge utile en STANDBY, FPA toujours dans sa plage. « COM-012 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-commissioning" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] COM-013 — Clôture de la recette SCAO et déclaration NOMINAL</div>

**Point d'entrée :** après COM-011 — l'ordre de recette se termine par COM-010, COM-012 Première lumière, COM-011 Étalonnage de la charge utile, COM-013. Charge utile recettée ; AOCS en NOMINAL commandé avec roues activées et gyroscopes étalonnés ; liaison descendante revenue en LOW ; OBC en NOMINAL ; phase de mission 5 ; SoC > 60 %.

**Objectif :** clore la recette en orbite : relire l'état final consolidé par rapport à l'état de sortie de chaque fiche **sans rien réessayer**, faire le tour des postes et déclarer la phase de mission 6 (NOMINAL). L'amortissement, les transitions de modes, les contrôles des roues et des magnétocoupleurs et l'étalonnage des gyroscopes relèvent de LEOP-005, COM-003, COM-004 et COM-005, et ne sont pas répétés ici.

**Issues défavorables possibles / écarts :**

- Une relecture des étapes 1–3 échoue → NE PAS déclarer la phase 6 ; revenir à la section hors nominal de la fiche concernée et rétablir d'abord son état de sortie
- `SYS_SET_MISSION_PHASE` refusée → `0x0C03` : l'OBC est dans le chargeur d'amorçage (refaire l'étape 5 de LEOP-001 et LEOP-006) ; `0x0C04` : retour en arrière sans FORCE
- `sat.mode` ne passe pas à 1 après la déclaration → une contingence FDIR est verrouillée ; lire le journal FDIR et supprimer la cause — aucune TC ne règle `sat.mode`

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : relecture consolidée de l'état final de l'AOCS | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.mode` (0x020F) dans {4, 5, 8} ; `aocs.commanded_mode` (0x0297) = 4, `aocs.mode_demoted` (0x0298) = 0 ; `aocs.wheels_enabled` (0x0260) = 4 ; `aocs.gyro_units_mask` (0x02D1) = 7 ; `aocs.st1_status` (0x0240) = 2 avec ≥ 5 étoiles ; `aocs.mag_enabled` (0x025C) = 1 ; erreur < 1,0° sur le côté éclairé |
| 2 | SPACON : relecture consolidée de l'état final de la plateforme | `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)`, `HK_REQUEST(sid=6)` (S3.27) | □ | `obdh.mode` (0x0300) = 0 ; palier LOW ; `eps.load_shed_stage` (0x0134) = 0 ; bus 26,5–29,5 V ; `obdh.time_ref` (0x0A13) ≠ 0 |
| 3 | Charge utile : relecture consolidée de l'état final de la charge utile | `HK_REQUEST(sid=5)` (S3.27) | □ | `payload.mode` (0x0600) = 1 (STANDBY) ; `payload.fpa_ready` (0x0610) = 1 ; `payload.transfer_active` (0x062D) = 0 |
| 4 | FD : interroger tous les postes, puis déclarer les opérations NOMINAL | `SYS_SET_MISSION_PHASE(phase=6, flags=0)` (S8 func_id 120) | □ | COM-013 est la dernière fiche de recette en orbite. `eps.spacecraft_phase` (0x0129) = 6 en 5 s ; `sat.mode` (0x0001) = 1 en 10 s ; l'événement `MISSION_PHASE_CHANGED` (0x0055) indique 5 → 6 |
| 5 | FD : tenir NOMINAL pendant une orbite ; passer la main ; consigner | (journal de mission) | □ | « COM-013 complete » : recette close. Si la règle FDIR sur `aocs.att_error`, désormais armée, rétrograde l'AOCS, examiner l'excursion avant de redéclarer quoi que ce soit |

**Remarque — rien à bord ne fait avancer la phase à votre place.** En dessous de la phase 6, le mode satellite dérivé (`sat.mode` 0x0001, et l'en-tête de la console) est bloqué sur SAFE quel que soit l'état de santé du satellite, le modèle avancé de propagation de défaillance et les règles FDIR conditionnées par la phase restent désarmés, et le verrouillage de la propulsion (`min_phase: 6`) refuse d'armer toute poussée — **NOM-013 ne peut donc pas s'exécuter tant que cette étape n'a pas été envoyée**. Le retour en arrière est refusé avec `0x0C04` sauf si l'indicateur FORCE est positionné (`flags` bit 0 = 1) ; si une déclaration a été prématurée, la renvoyer avec l'indicateur et en consigner la raison.

</div>

<div style="page-break-before: always"></div>

## 14.3 Fiches de procédure nominales

> **Note de la rédaction — le jeu nominal.** Le simulateur est livré avec quatorze
> procédures nominales. Onze font l'objet d'une fiche ci-dessous ; **NOM-005 Configuration
> HK**, **NOM-008 Synchronisation de l'horloge** et **NOM-011
> Changement de débit** sont des fiches courtes, à poste unique, répertoriées
> au §14.7 pour consultation en console. Deux autres activités nominales —
> le **chargement du plan de passage** et la **revue des tendances à long terme** — font réellement partie
> du déroulement nominal mais ne sont livrées avec aucun fichier de procédure propre ; elles
> font l'objet d'une fiche ici, sans numéro NOM, et le déroulement y fait
> explicitement référence. Les fiches suivent l'ordre des identifiants livrés, à ceci près que NOM-013,
> NOM-014 et les deux fiches sol non numérotées se placent immédiatement avant la
> fiche de passation de consignes qui clôt la section.
>
> **NOM-008 en un paragraphe, parce que l'horloge est nouvelle.** (C'est l'une
> des huit fiches exécutables par la machine — `runnable: {kind: markdown}`
> —, et elle peut donc être pilotée depuis l'onglet Procédures du MCS.) L'OBC
> fait tourner une horloge indépendante qui démarre à CUC 0 = **J2000** et
> dérive librement d'environ **12 ppm** (≈ 1 s/jour). NOM-008 demande un SID 4 de HK
> récent *et* un `REQUEST_TIME` (S9.2) explicite au lieu de lire
> l'écran, corrige avec `SET_TIME(cuc_seconds=…)` (S9.1) jusqu'à un
> seuil plus serré de 0.1 s, contre 1.0 s pour LEOP-006, et consigne
> `obdh.time_ref` (0x0A13) et `obdh.time_since_sync_s` (0x0A14) avant et
> après. L'asservissement GPS (`OBC_GPS_TIME_SYNC`, S8 fonction 80) est
> l'autre solution et maintient exactement le temps vrai tant que le point GPS est bon —
> cette voie est CTG-027.

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FD] NOM-001 — Ouverture de passage</div>

**Point d'entrée :** AOS sur l'une des cinq stations du réseau (Iqaluit, Troll, Svalbard, Inuvik, O'Higgins) ; la liste de vérification complète « lire et faire » se déroule d'AOS à AOS+1 min.

**Objectif :** établir la liaison, vérifier l'ensemble des HK, faire le tour de santé entre postes et autoriser les activités planifiées du passage.

**Issues défavorables possibles / écarts :**

- Pas de verrouillage à l'AOS → CTG-003 Rétablissement après perte de liaison TTC
- Station qui ne poursuit pas → CTG-020 Panne d'antenne de station sol (fiche consultative — toutes ses actions sont menées au sol)
- Pas de HK après verrouillage → CTG-019 Absence de télémesure en début de passage
- Un sous-système hors plage lors du tour de santé → appliquer la CTG correspondante avant d'autoriser les activités planifiées

**Arbre de décision :**

- SI `ttc.link_status` = 2 ET test de liaison ET HK complètes ET tous les postes OK → GO activités planifiées
- SI verrouillé mais échec du test de liaison → CTG-019
- SI EPS OUT-OF-BAND → CTG-001 avant toute autre commande

**Liste de vérification complète « lire et faire » :** voir §9.3, tableau 9.2.

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : station en poursuite ? | (panneau MPS) | □ | TRACKING |
| 2 | TT&C : liaison verrouillée à l'AOS ? | `ttc.link_status` (0x0501) = 2 (LOCKED) | □ | RSSI (0x0502) > −100 dBm ; marge (0x0503) > 3.0 dB |
| 3 | SPACON : test de liaison | `CONNECTION_TEST` (S17.1) — première clé / GO du FD / envoi | □ | Réponse S17.2 < 4 s |
| 4 | SPACON : balayage complet des HK | `HK_REQUEST(sid=1…6)` (S3.27) | □ | 1 EPS, 2 AOCS, 3 TCS, 4 plateforme/OBDH, 5 charge utile, 6 TT&C — les six en 30 s |
| 5 | AOCS : mode et vitesses angulaires | `aocs.mode` (0x020F) = 4 (NOMINAL, nadir) | □ | Roulis/lacet < 0.05 °/s ; tangage −0.063 ± 0.02 °/s — le suivi du nadir est une vraie vitesse angulaire, pas une erreur |
| 6 | EPS : bus et SoC | `HK_REQUEST(sid=1)` (S3.27) | □ | SoC > 50 %, bus > 27.0 V, production > consommation |
| 7 | Thermique : zones | `HK_REQUEST(sid=3)` (S3.27) | □ | Toutes les zones au vert |
| 8 | FD : GO activités planifiées | (journal de mission) | □ | Voir le §9.3 pour le texte complet des annonces |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[PE] NOM-002 — Séance de prise de vue</div>

**Point d'entrée :** ouverture de la fenêtre de prise de vue programmée (selon le plan de passage) ; AOCS en FINE_POINT ou en transition vers ce mode. *(Exécutable depuis l'onglet Procédures du MCS — liée à l'activité `imaging_pass`.)*

**Objectif :** acquérir la ou les images prévues et vérifier qu'elles sont stockées dans la mémoire de la charge utile.

**Issues défavorables possibles / écarts :**

- FINE_POINT refusé ou rétrogradé → vérifier `aocs.fine_ready` (0x02C5) et `aocs.mode_demoted` (0x0298) ; HOLD jusqu'à 60 s pour la convergence
- Erreur de pointage ≥ 0.5° en cours de séance → mettre fin à la séance de façon anticipée et replanifier
- Stockage ≥ 95 % → arrêter la prise de vue ; donner la priorité au vidage NOM-003
- Moment cinétique en hausse → NOM-007, mais noter que les déchargements sont automatiquement inhibés tant que `payload.mode` = 2 (`aocs.desat_inhibit`, 0x029A)

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : passer en FINE_POINT et le vérifier | `AOCS_FINE_READY_CHECK` (func_id 89) ; `AOCS_SET_MODE(mode=5)` (func_id 0) | □ | `aocs.fine_ready` = 0 ; `aocs.mode` = 5 ; `aocs.mode_demoted` (0x0298) = 0 ; erreur < 0.1° |
| 2 | Thermique : vérifier le plan focal | `HK_REQUEST(sid=3)` (S3.27) | □ | `tcs.temp_fpa` (0x0408) < −10.0 °C ; `tcs.cooler_fpa` (0x040C) = 1 |
| 3 | Charge utile : vérifier le stockage | `HK_REQUEST(sid=5)` (S3.27) | □ | `payload.store_used` (0x0604) < 90 % |
| 4 | Charge utile : commander IMAGING | `PAYLOAD_SET_MODE(mode=2)` (S8 func_id 26) | □ | `payload.mode` (0x0600) = 2 en 15 s |
| 5 | Charge utile : déclencher chaque acquisition | `PAYLOAD_CAPTURE(scene_id=N, lines=2048)` (S8 func_id 28) | □ | Dater avec `SCHEDULE_TC` (S11.4) à chaque survol ; `payload.last_scene_id` (0x060C) = identifiant commandé |
| 6 | Charge utile : surveiller la séance | `HK_REQUEST(sid=5)` / `(sid=2)` / `(sid=3)` toutes les 30 s | □ | `payload.image_count` (0x0605) en progression ; erreur < 0.1° ; stockage < 95 % |
| 7 | Charge utile : mettre fin à la séance | `PAYLOAD_SET_MODE(mode=1)` (S8 func_id 26) | □ | Mode 1 ; la consommation baisse |
| 8 | SPACON : consigner ; mettre en file pour le vidage NOM-003 | (journal de mission) | □ | « NOM-002 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] NOM-003 — Transmission des données au sol</div>

**Point d'entrée :** AOS avec des produits en attente de vidage (en général immédiatement après NOM-001). *(Exécutable — liée à l'activité `data_dump`.)*

**Objectif :** passer la liaison en HIGH, descendre le produit segment par segment via S13 et confirmer sa livraison au sol, puis libérer le palier HIGH.

**Issues défavorables possibles / écarts :**

- HIGH refusé avec S1.8 `0x0007` → une condition n'est pas satisfaite : antenne déployée, mode DOWNLINK actif, élévation ≥ 10°, mode balise désactivé
- Le TEB augmente en cours de passage → CTG-014 ; redescendre en LOW ; remettre en file les segments concernés
- Panne de station en cours de passage → CTG-020 ; la file restante est reportée au passage suivant
- CRC discordant sur le produit réassemblé → redemander les segments en échec avant de clore le transfert

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | TT&C : confirmer la qualité de la liaison | `HK_REQUEST(sid=6)` (S3.27) | □ | `ttc.link_status` (0x0501) = 2 ; marge (0x0503) > 3.0 dB |
| 2 | Charge utile : lire le catalogue de bord | `PAYLOAD_GET_IMAGE_CATALOG` (S8 func_id 32) | □ | Sélectionner les identifiants de scène ; `payload.mode` (0x0600) = 1 |
| 3 | TT&C : passer la liaison en HIGH | `TTC_SET_DOWNLINK_MODE(on=1)` (func_id 79) ; `TTC_SET_DATA_RATE(rate=1)` (func_id 65) | □ | `ttc.tm_data_rate` (0x0506) = 128000 bit/s ; `ttc.tm_tier` (0x0539) = 2 |
| 4 | Charge utile : ouvrir le transfert | `S13_CREATE_TRANSFER(scene_id=N, size_mb=0)` (S13.1) | □ | `payload.transfer_active` (0x062D) = 1 ; nombre de blocs et CRC-32 consignés |
| 5 | Charge utile : parcourir les segments, surveiller la progression | `S13_DOWNLOAD_SEGMENT(transfer_id=T, segment_num=K)` (S13.3) ; `S13_REPORT_STATUS(transfer_id=T)` (S13.9) | □ | `payload.transfer_progress` (0x062E) en hausse ; verrouillage maintenu ; marge > 2.0 dB |
| 6 | Segment sol : vérifier la réception et le CRC-32 du produit | (outil sol) | □ | Taux d'erreur trame < 1e-6 ; CHECKSUM OK |
| 7 | TT&C : clore le transfert et libérer HIGH | `S13_END_TRANSFER(transfer_id=T)` (S13.5) ; `TTC_SET_DATA_RATE(rate=0)` ; `TTC_SET_DOWNLINK_MODE(on=0)` | □ | Retour à 16000 bit/s ; `ttc.downlink_mode` (0x053C) = 0 |
| 8 | SPACON : consigner ; clore le vidage du passage | (journal de mission) | □ | « NOM-003 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] NOM-004 — Planification d'une manœuvre de maintien d'orbite</div>

**Point d'entrée :** le FDS détecte une dérive d'altitude hors de l'enveloppe prévue, une conjonction avec un débris impose une manœuvre d'évitement de collision, ou une fenêtre programmée approche. *(Exécutable — liée à l'activité `orbit_manoeuvre`.)*

**Objectif :** concevoir et valider au sol la prochaine poussée, puis charger la séquence datée ; l'exécution relève de NOM-013.

**Issues défavorables possibles / écarts :**

- La dérive dépasse la tolérance avant la prochaine fenêtre prévue → avancer la manœuvre ; se coordonner avec le planning de la charge utile
- Défaut d'une vanne à verrouillage (`prop.latch_a_state` / `prop.latch_b_state`, 0x0B06 / 0x0B07 = 2) ou pression hors plage → reporter ; CTG-028 Anomalie de propulsion
- Plan rejeté en revue de sécurité → replanifier avec un delta-V plus faible

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FDS : concevoir la manœuvre | (outil FDS) | □ | Le bilan total de delta-V est de 66.9 m/s avec le monergol vert 1U — évitement de débris et maintien d'orbite limité ; à partir de la mi-mission, garder `prop.dv_remaining` (0x0B0C) ≥ 38 m/s pour le retrait de service NOM-014 |
| 2 | Propulsion : activer les données de servitude PROP et contrôler la santé | `HK_ENABLE(sid=9)` (S3.5) | □ | `prop.state` (0x0B00) = 0 (SAFED) ; `prop.tank_pressure` (0x0B01) dans la plage |
| 3 | FD : examiner et autoriser le vecteur et le passage d'exécution | (GO du FD) | □ | Consigné |
| 4 | SPACON : dater la séquence de poussée | `SCHEDULE_TC(exec_time_cuc=T, tc_data=TC)` (S11.4) ×3 | □ | `PROP_SET_BURN` à T−5 min, `PROP_ARM` à T−2 min, `PROP_EXECUTE` à T−0 |
| 5 | SPACON : relire le plan bord | `LIST_SCHEDULE` (S11.17) | □ | Trois commandes aux instants CUC prévus |
| 6 | FDS : présenter le décalage de passage prévu | (outil FDS) | □ | Une poussée oblige à réajuster les éléments orbitaux : 1 m/s donne Δa ≈ +1.800 km et −33.5 s à +24 h, si bien que les passages et les éclipses se déplacent réellement |
| 7 | SPACON : programmer le créneau de débriefing du résultat de NOM-013 | (journal de mission) | □ | « NOM-004 complete (plan only) » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] NOM-006 — Chargement de logiciel / mise à jour de paramètres</div>

**Point d'entrée :** créneau programmé de correctif ou de paramètres, approuvé hors ligne par les comités logiciel/FDIR ; SoC > 60 %, bus > 28.0 V, charge CPU < 50 %.

**Objectif :** envoyer l'image ou le jeu de paramètres via S6, vérifier par somme de contrôle, et activer lors d'un redémarrage maîtrisé.

**Issues défavorables possibles / écarts :**

- Somme de contrôle discordante → renvoyer le segment concerné
- Pas de retour du redémarrage en 90 s → CTG-021 Reprise par le chargeur d'amorçage de l'OBC
- Effets de bord sur le comportement de la FDIR → refaire l'essai aller-retour de COM-008 après activation

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | OBDH : bilan de santé avant envoi | `HK_REQUEST(sid=4)`, `HK_REQUEST(sid=1)` (S3.27) | □ | `obdh.mem_errors` (0x031E) = 0 ; `obdh.heap_usage` (0x031D) < 60 % |
| 2 | OBDH : suspendre la programmation bord et les charges non critiques | `DISABLE_SCHEDULE` (S11.9) ; `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | `payload.mode` (0x0600) = 0 |
| 3 | OBDH : envoyer les segments | `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (S6.2) | □ | Chaque segment acquitté en 10 s |
| 4 | OBDH : vérifier par somme de contrôle | `MEM_CHECK(memory_id=1, address=ADDR, length=LEN)` (S6.9) | □ | Concordance bit à bit |
| 5 | OBDH : configurer la source d'amorçage | `OBC_BOOT_APP` (S8 func_id 55) | □ | `obdh.sw_image` (0x0311) toujours à 1 — pas encore de redémarrage intempestif |
| 6 | OBDH : redémarrage maîtrisé et confirmation de la nouvelle image | `OBC_REBOOT` (S8 func_id 52) | □ | Répond en 90 s ; `obdh.sw_version` (0x030B) conforme à l'attendu ; `obdh.last_reboot_cause` (0x0316) = 4 (commandé) |
| 7 | SPACON : **resynchroniser l'horloge** avant de rétablir la programmation | `SET_TIME(cuc_seconds=T_corrected)` (S9.1) selon NOM-008 | □ | Le chargeur d'amorçage a ramené l'horloge à **J2000** : `obdh.time_ref` (0x0A13) = 0 (NONE), `obdh.time_since_sync_s` (0x0A14) = 4294967295, `obdh.obc_time` (0x0309) revenu près de 0. L'amorçage de l'application ne la restaure pas |
| 8 | SPACON : rétablir la programmation ; surveiller la première orbite | `ENABLE_SCHEDULE` (S11.13) | □ | Ne pas oublier que l'amorçage réapplique `default_enabled_sids: [1, 11]` — renvoyer `HK_ENABLE` pour les autres |
| 9 | SPACON : consigner | (journal de mission) | □ | « NOM-006 complete » |

**Remarque — le plan bord se déclenche sur le temps BORD.** Toute étiquette S11 envoyée avant le redémarrage a été calculée par rapport à l'horloge d'avant le redémarrage. Réactiver la programmation (étape 8) avant que l'horloge soit rétablie (étape 7) laisse l'OBC avec des étiquettes situées des décennies dans son propre futur, qui ne se déclenchent tout simplement jamais. Synchroniser d'abord, puis réarmer, puis relire avec `LIST_SCHEDULE` (S11.17).

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] NOM-007 — Gestion du moment cinétique (désaturation)</div>

**Point d'entrée :** moment cinétique stocké dans le satellite au-dessus du seuil de déchargement, ou créneau de désaturation programmé. AOCS en NOMINAL (mode 4), `aocs.desat_inhibit` (0x029A) = 0, aucune prise de vue en cours.

**Objectif :** évacuer le moment cinétique stocké à l'aide des magnétocoupleurs et laisser le satellite revenir automatiquement au mode antérieur à la désaturation.

**Issues défavorables possibles / écarts :**

- Commande refusée avec `DESAT_REFUSED_FINE` → le satellite est en FINE_POINT ; la désaturation n'y est pas permise
- Déchargement inefficace → s'il dépasse `desaturation.timeout_s` (3600 s), le satellite émet l'événement `0x020E AOCS_DESAT_INEFFECTIVE` ; suspecter un défaut de magnétocoupleur (CTG-007)
- L'erreur de pointage augmente pendant le déchargement → attendu jusqu'à la limite grossière de 5° ; si cela persiste, interrompre et revenir en arrière

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : évaluer l'état du moment cinétique | `GET_PARAM(param_id=0x029B)` (S20.3) — `aocs.h_body_nms` | □ | **C'est le moment cinétique du satellite, et non la vitesse des roues, qu'un déchargement magnétique évacue.** Recouper avec les roues (0x0207–0x020A) et l'enveloppe `aocs.h_env_frac` (0x02BA) |
| 2 | AOCS : relevé d'attitude avant désaturation | `HK_REQUEST(sid=2)` (S3.27) | □ | Erreur < 1.0° ; vitesses angulaires < 0.05 °/s |
| 3 | AOCS : planifier la fenêtre | (outil FDS / AOCS) | □ | Éviter les fenêtres de prise de vue — la prise de vue active automatiquement l'inhibition de désaturation |
| 4 | AOCS : commander le déchargement | `AOCS_DESATURATE` (S8 func_id 1) | □ | `aocs.mode` (0x020F) = 7 (DESAT) en 10 s |
| 5 | AOCS : surveiller la progression | `HK_REQUEST(sid=2)` toutes les 30 s | □ | **Un déchargement prend plusieurs dizaines de minutes, pas dix :** ~25 min jusqu'à 0.005 N·m·s et ~48 min jusqu'à 0.001 N·m·s à partir d'une charge de 0.020 N·m·s. Un `h_body` stable pendant quelques minutes est normal |
| 6 | AOCS : confirmer le retour automatique au mode antérieur | `aocs.mode_demoted` (0x0298) = 0 | □ | Le satellite revient de lui-même — aucune commande de mode n'est nécessaire |
| 7 | AOCS : vérification après désaturation | `HK_REQUEST(sid=2)` (S3.27) | □ | Erreur < 1.0° ; roues dans la plage nominale ; vitesses angulaires < 0.05 °/s |
| 8 | SPACON : consigner ; clore la fiche si le déchargement a été déclenché par une anomalie | (journal de mission) | □ | « NOM-007 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[MULTI] NOM-009 — Bilan de santé de routine</div>

**Point d'entrée :** à chaque ouverture de passage, dans le cadre de NOM-001 ; également commandé ponctuellement par le FD. *(Exécutable — liée à l'activité `housekeeping_collection` : une seule requête S3.27 par structure.)*

**Objectif :** chaque poste lit sa structure et annonce OK sur la boucle ; le SPACON confirme l'absence de déclenchement FDIR récent.

**Issues défavorables possibles / écarts :**

- Un poste renvoie une valeur hors plage → appliquer la CTG correspondante avant de poursuivre le passage
- Règle FDIR déclenchée dans l'heure écoulée mais déjà retombée → consigner et poursuivre ; ouvrir une fiche après le passage
- Dérive lente pas encore signalée → le FD autorise un point de surveillance, pas nécessairement une CTG

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | SPACON : demander les six structures | `HK_REQUEST(sid=1…6)` (S3.27) | □ | Les six en 30 s. `HK_REQUEST` est le S3 **sous-type 27** ; `HK_ENABLE` est S3.5 |
| 2 | EPS : SoC, bus, marge | SID 1 | □ | SoC (0x0101) > 40 % ; bus (0x0105) 27.0–29.5 V ; marge > −50 W |
| 3 | AOCS : mode, erreur, vitesses angulaires, roues | SID 2 | □ | `aocs.mode` (0x020F) = 4 (NOMINAL) ; erreur < 1.0° ; vitesses de roue < 5000 tr/min |
| 4 | Thermique : températures des zones et états des réchauffeurs | SID 3 | □ | OBC (0x0406) −10…+50 °C ; batterie (0x0407) +5…+35 °C ; `tcs.cooler_fpa` (0x040C) conforme à l'attendu |
| 5 | OBDH : mode, charge, temps de fonctionnement, **référence d'horloge** | SID 4 | □ | `obdh.mode` (0x0300) = 0 ; charge < 80 % ; aucun redémarrage inattendu. `obdh.time_ref` (0x0A13) = 1 (GROUND) ou 2 (GPS) — 0 (NONE) signifie que l'OBC a redémarré et que l'horloge est revenue à J2000 ; 3 correspond à HOLDOVER. `obdh.time_since_sync_s` (0x0A14) passe au jaune à 12 h, au rouge à 24 h ; à ~12 ppm nominaux, l'horloge avance d'environ 1 s/jour, si bien qu'une synchronisation par quart est la routine |
| 6 | TT&C : verrouillage, RSSI, marge | SID 6 | □ | `ttc.link_status` (0x0501) = 2 (LOCKED) ; marge > 2.0 dB |
| 7 | Charge utile : mode, FPA, stockage | SID 5 | □ | `payload.store_used` (0x0604) < 95 % |
| 8 | SPACON : consolider un PASS unique pour le FD | (boucle vocale) | □ | « NOM-009 PASS » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] NOM-010 — Transition d'éclipse</div>

**Point d'entrée :** approche de la limite d'éclipse (en général à chaque orbite) ; le FDS fournit l'horaire prévu.

**Objectif :** configurer le satellite pour la phase froide et obscure de l'éclipse, surveiller le creux de SoC et les marges thermiques, et confirmer le rétablissement après la sortie.

**Issues défavorables possibles / écarts :**

- Creux de SoC plus profond que prévu → plan de délestage CTG-001 ; envisager de reporter la prise de vue de l'éclipse suivante
- Une zone sort de sa plage → CTG-004 Dépassement thermique
- Pente de recharge plus faible que prévu après la sortie → signaler une possible sous-performance du régulateur de charge

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : consigner la référence avant éclipse | `HK_REQUEST(sid=1)` (S3.27) | □ | SoC (0x0101) > 60 % ; bus (0x0105) > 28.0 V ; courant batterie (0x0109) consigné |
| 2 | Thermique : régler les consignes de réchauffeur pour l'éclipse | `HEATER_SET_SETPOINT(circuit=0, on_temp=3.0, off_temp=8.0)` / `(circuit=1, on_temp=8.0, off_temp=13.0)` (S8 func_id 44) | □ | Batterie > 5 °C, OBC > 10 °C à l'entrée |
| 3 | Thermique : libérer le refroidisseur du FPA si aucune prise de vue n'est prévue | `FPA_COOLER(on=0)` (S8 func_id 43) | □ | `tcs.cooler_fpa` (0x040C) = 0 ; la consommation baisse d'environ 15 W |
| 4 | AOCS : commander le maintien d'éclipse | `AOCS_SET_MODE(mode=8)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 8 (ECLIPSE) en 15 s ; propagation sur gyroscopes seuls |
| 5 | EPS : surveiller pendant toute l'éclipse | `HK_REQUEST(sid=1)` toutes les 30 s | □ | `eps.eclipse_flag` (0x0108) = 1 ; production ≈ 0 W ; bus > 27.0 V ; courant batterie négatif |
| 6 | Thermique : surveiller les zones | `HK_REQUEST(sid=3)` toutes les 60 s | □ | Batterie > 0 °C, OBC > 5 °C ; réchauffeurs en cyclage |
| 7 | EPS : confirmer le rétablissement après la sortie | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.eclipse_flag` = 0 ; production > 25 W en 60 s |
| 8 | SPACON : déposer la note de passage d'éclipse | (journal de mission) | □ | « NOM-010 complete » |

</div>

<div style="page-break-before: always"></div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] NOM-013 — Exécution d'une manœuvre de maintien d'orbite</div>

**Point d'entrée :** exécution datée selon le plan de NOM-004, de préférence au-dessus d'une station pour une observation directe. *(Le livre numérotait auparavant cette fiche NOM-005 ; l'identifiant livré est NOM-013 — la NOM-005 du simulateur est la configuration HK.)*

**Objectif :** exécuter la poussée prévue et vérifier la réponse de l'orbite.

**Issues défavorables possibles / écarts :**

- Armement refusé → vérifier `prop.arm_inhibit_mask` (0x0B15), la température du lit catalytique, et **`eps.spacecraft_phase` (0x0129) = 6** : `prop.yaml` déclare `min_phase: 6`, si bien qu'avec une phase restée à 4 ou 5 aucune poussée ne peut jamais être armée. La phase est fixée par `SYS_SET_MISSION_PHASE(phase=6, flags=0)` (S8 func_id 120) à la fin de COM-013. `PROP_ARM` doit suivre `PROP_SET_BURN` dans les 300 s
- La poussée ne démarre pas à l'heure → vérifier la ligne de propulsion et l'état d'armement ; en l'absence de poussée, CTG-028 Anomalie de propulsion
- Poussée insuffisante → replanifier une manœuvre de correction dans le cadre de NOM-004
- L'attitude dérive hors axe pendant la poussée → l'autorité permanente d'interruption s'applique : `PROP_ABORT` d'abord, les questions ensuite

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Propulsion : alimenter la ligne de propulsion et préchauffer le lit catalytique (T−25 min) | `EPS_POWER_ON(line_index=8)` (func_id 19) ; `HEATER_THRUSTER(on=1)` (func_id 42) | □ | `eps.pl_prop` (0x014A) = 1 ; lit catalytique 12 W ; `tcs.temp_thruster` (0x0409) en hausse |
| 2 | AOCS : tenir l'attitude de poussée | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.mode` (0x020F) = 4, ou 9 (INERTIAL) avec le lacet de 180° pour une poussée rétrograde ; erreur < 0.5° |
| 3 | Propulsion : charger la manœuvre | `PROP_SET_BURN(dv_m_s=DV, direction=DIR, mode=MODE, t_start_cuc=0)` (S8 func_id 110) | □ | `prop.burn_dv_cmd` (0x0B0E) = dV prévu |
| 4 | Propulsion : armer | `PROP_ARM(arm_code=0xA5C3)` (S8 func_id 108) | □ | `tcs.temp_thruster` ≥ 180 °C ; `prop.state` (0x0B00) = 1 (ARMED) ; événement `0x0800` |
| 5 | Propulsion : exécuter et surveiller | `PROP_EXECUTE` (S8 func_id 111) — ou l'étiquette S11 la déclenche | □ | `prop.state` = 2 (FIRING) ; événement `0x0803`. La vitesse de simulation est limitée à ≤ 10× pendant une poussée |
| 6 | Propulsion : critères permanents d'interruption | `PROP_ABORT` (S8 func_id 112) | □ | Après toute interruption, `prop.burn_status` (0x0B0D) = 4 |
| 7 | FDS : restitution d'orbite après la poussée | `prop.sma_km` (0x0B1A) ; `prop.orbit_epoch_version` (0x0B19) | □ | Événement `0x0804` ; Δa comparé à la prédiction ; nouveaux éléments orbitaux, donc nouveaux horaires de passage |
| 8 | Propulsion : mise en sécurité et clôture | `PROP_DISARM` (func_id 109) ; `HEATER_THRUSTER(on=0)` (func_id 42) ; `EPS_POWER_OFF(line_index=8)` (func_id 20) | □ | `prop.state` = 0 ; `eps.pl_prop` = 0 ; `aocs.total_momentum` (0x025B) < 0.02 N·m·s — « NOM-013 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FD] NOM-014 — Retrait de service en fin de vie (abaissement du périgée et passivation)</div>

**Point d'entrée :** fin de mission déclarée par le FD ; prise de vue close et dernières données scientifiques transmises au sol. Phase de mission 6 (le verrouillage d'armement de la propulsion l'exige), `prop.dv_remaining` (0x0B0C) ≥ 38 m/s, propulsion saine (`prop.state` 0x0B00 = 0, aucune inhibition verrouillée, réservoir à 6,0–24,0 bar), SoC > 55 %, plan FDS de six poussées consécutives de jour.

**Objectif :** abaisser le périgée de 513 km à 390 km par une poussée rétrograde de 34,3 m/s, réalisée en six poussées de 5,72 m/s au même point de l'orbite (qui devient l'apogée), afin qu'EOSAT-1 rentre dans l'atmosphère en environ 1,5 an à activité solaire moyenne et 4,2 ans au minimum solaire ; puis passiver. La décroissance naturelle depuis 513 km prendrait 5,0 ans à activité moyenne et 14,2 ans au minimum solaire.

**Issues défavorables possibles / écarts :**

- Une poussée est interrompue → étape 5 de NOM-013 et CTG-028 ; le ΔV partiel est déjà dans l'orbite, et le FDS replanifie les poussées restantes depuis la nouvelle orbite
- `prop.dv_remaining` inférieur au plan → abaisser le périgée autant que l'ergol le permet (chaque 1 m/s rétrograde l'abaisse d'environ 3,6 km) et rendre compte de la durée de vie résiduelle obtenue
- Propulsion inutilisable en fin de vie → passiver (étapes 9–12) et signaler la non-conformité : la décroissance naturelle prend environ 5 ans à activité moyenne et 14 au minimum solaire
- Durée de vie au minimum solaire encore supérieure à 5 ans après l'étape 7 → poussée de correction (à nouveau l'étape 6, ΔV plus faible) avant la passivation
- Il n'existe pas de phase DISPOSAL : le satellite reste en phase 6 de bout en bout, car le verrouillage d'armement l'exige

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FDS : plan de retrait de service ; autorisation du FD | (outil FDS) | □ | Six instants de poussée de jour, ΔV par poussée, quaternion rétrograde ; périgée prévu 513 → ~492 → ~471 → ~451 → ~431 → ~410 → 390 km |
| 2 | Propulsion : contrôle de santé | `HK_ENABLE(sid=9)` (S3.5) | □ | `prop.state` = 0 ; `prop.tank_pressure` (0x0B01) 6,0–24,0 bar ; `prop.dv_remaining` ≥ 38 m/s ; consigner `prop.arm_inhibit_mask` (0x0B15). Sinon, CTG-028 d'abord |
| 3 | Propulsion : relever le chien de garde de poussée | `PROP_SET_LIMITS(att_err_max_deg=2.0, p_min_bar=4.0, catbed_max_c=350.0, t_burn_max_s=600.0)` (S8 func_id 115) | □ | Le chien de garde par défaut est de 300 s ; une poussée de 5,72 m/s en fin de vie dure jusqu'à ~480 s. Les autres limites d'interruption gardent leurs valeurs par défaut |
| 4 | Propulsion : alimentation, préchauffage et ouverture des vannes (T−25 min) | `EPS_POWER_ON(line_index=8)` (S8 func_id 19) ; `HEATER_THRUSTER(on=1)` (S8 func_id 42) ; `PROP_ISO_OPEN(branch=2)` (S8 func_id 113) | □ | `eps.pl_prop` (0x014A) = 1 ; `prop.latch_a_state` (0x0B06) = 1 ; `tcs.temp_thruster` (0x0409) ≥ 180 °C en 1500 s |
| 5 | AOCS : maintien inertiel rétrograde | `AOCS_SET_TARGET_QUAT(q_x=QX, q_y=QY, q_z=QZ, q_w=QW)` (S8 func_id 86) ; `AOCS_SET_MODE(mode=9)` (S8 func_id 0) | □ | Lacet de 180° pour que l'axe de poussée +X pointe à l'opposé de la vitesse. `aocs.mode` = 9 en 120 s ; `aocs.att_error` < 0,5° en 600 s |
| 6 | Propulsion : poussée de retrait de service — répéter les étapes 5 et 6 pour chacune des six poussées | `PROP_SET_BURN(dv_m_s=5.72, direction=1, mode=1, t_start_cuc=0)` (S8 func_id 110) ; `PROP_ARM(arm_code=0xA5C3)` (S8 func_id 108) ; `PROP_EXECUTE` (S8 func_id 111) ; `PROP_DISARM` (S8 func_id 109) | □ | `prop.burn_time_cmd` (0x0B10) à 10 % près de la prédiction FDS ; événement `PROP_BURN_COMPLETE` (0x0804) en 600 s ; `prop.burn_dv_achieved` (0x0B0F) à 2 % près de 5,72 ; `prop.state` revenu à 0. Revenir en NOMINAL pour l'éclipse entre deux poussées |
| 7 | FDS : confirmer l'orbite de retrait de service | `HK_REQUEST(sid=12)` (S3.27) sur une orbite complète | □ | `aocs.gps_alt` (0x0212) minimal entre 380 et 400 km ; demi-grand axe ~6830 km ; durée de vie résiduelle < 5 ans au minimum solaire |
| 8 | Propulsion : épuiser l'ergol | `PROP_SET_BURN(dv_m_s=DVREM, direction=1, mode=0, t_start_cuc=0)` (S8 func_id 110) ; `PROP_ARM(arm_code=0xA5C3)` ; `PROP_EXECUTE` | □ | Depuis le maintien rétrograde, de jour ; DVREM est la valeur courante de `prop.dv_remaining`. `prop.propellant_mass` (0x0B02) < 5 g en 900 s ; sous 5 g l'armement est refusé (`0x0B03`) et le résidu est consigné |
| 9 | Propulsion : mise en sécurité et inhibition | `PROP_DISARM` ; `HEATER_THRUSTER(on=0)` ; `PROP_INHIBIT_SET(on=1)` (S8 func_id 116) ; `EPS_POWER_OFF(line_index=8)` (S8 func_id 20) | □ | `prop.state` = 0 ; bit 9 de `prop.arm_inhibit_mask` positionné ; `eps.pl_prop` = 0. Il n'existe pas de commande de dégazage du réservoir : consigner la pression résiduelle (environ 9–10 bar) dans le rapport de retrait de service |
| 10 | Charge utile et AOCS : arrêt, arrêt des roues | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) ; `EPS_POWER_OFF(line_index=3)` ; `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0)` (S8 func_id 14) | □ | `payload.mode` (0x0600) = 0 ; `aocs.total_momentum` (0x025B) < 0,01 en 120 s. Il ne reste plus d'énergie cinétique dans les roues |
| 11 | EPS : passiver la batterie | `S2_EPS_CHARGE_REGULATOR(device_id=271, state=0)` (S2.1) | □ | Les générateurs ne peuvent plus charger la batterie ; `eps.bat_soc` (0x0101) en baisse au soleil. Envoyer les étapes 11 et 12 dans le même passage |
| 12 | TT&C : silence radio — les dernières commandes | `TTC_BEACON_TX_OFF` (S8 func_id 98) ; `TTC_PA_OFF` (S8 func_id 67) ; `EPS_TRANSPONDER_TX(on=0)` (S8 func_id 18) | □ | La perte du signal est la vérification ; confirmer l'absence de porteuse aux deux passages programmés suivants. Déposer le rapport de retrait de service. « NOM-014 complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FD] Chargement du plan de passage (déroulement nominal — aucun fichier de procédure livré)</div>

**Point d'entrée :** nouveau plan de passage sur 24 h prêt, fourni par le FDS ; créneau d'envoi programmé dans le passage en cours ou le suivant. Cette activité se situe entre NOM-001 (ouverture de passage) et les activités planifiées qu'elle programme — principalement la prise de vue NOM-002 et le vidage NOM-003.

**Objectif :** envoyer le plan daté et confirmer que le plan bord correspond à la copie sol.

**Issues défavorables possibles / écarts :**

- Envoi rejeté → vérifier le niveau d'autorisation et réessayer ; une `SCHEDULE_TC` rejetée laisse intact le plan précédent
- La relecture diffère de la copie sol → HOLD ; supprimer les entrées divergentes avec `DELETE_SCHEDULED` (S11.7) avant l'exécution de la prochaine activité programmée
- Le plan couvre une fenêtre pendant laquelle du matériel est désormais dégradé → replanifier hors ligne avant de réessayer

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FDS : produire le plan sur 24 h ; revue sol | (revue FDS / FD) | □ | Plan examiné au regard de la configuration actuelle du satellite |
| 2 | SPACON : envoyer les commandes datées | `SCHEDULE_TC(exec_time_cuc=T, tc_data=TC)` (S11.4), une par activité | □ | Toutes les TC acquittées |
| 3 | SPACON : relire le plan bord | `LIST_SCHEDULE` (S11.17) | □ | Comparaison entrée par entrée avec la copie sol |
| 4 | SPACON : supprimer les entrées périmées | `DELETE_SCHEDULED` (S11.7) / `DELETE_ALL_SCHEDULED` (S11.11) | □ | Uniquement avec le GO du FD |
| 5 | SPACON : consigner le nouveau plan actif | (journal de mission) | □ | « Pass plan upload complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] Revue des tendances à long terme (déroulement nominal — aucun fichier de procédure livré)</div>

**Point d'entrée :** fin de quart ou créneau hebdomadaire ; activité sol passive, menée depuis l'archive du MCS sans aucune commande. Ses résultats alimentent le briefing de passation de consignes de NOM-012.

**Objectif :** examiner les tendances à long terme (capacité et nombre de cycles de la batterie, marge du refroidisseur, enveloppe de moment cinétique, marge de liaison et TEB) pour détecter les dégradations lentes avant qu'elles ne deviennent des contingences.

**Issues défavorables possibles / écarts :**

- Une tendance dépasse le seuil jaune → ouvrir un point de surveillance ; briefer le responsable de mission
- Une tendance dépasse le seuil rouge → ouvrir une fiche d'anomalie formelle ; lancer la CTG correspondante

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Tous les postes : extraire les courbes de tendance hebdomadaires | (archive du MCS) | □ | Aucune télécommande — cette fiche ne commande rien |
| 2 | EPS : capacité et cycles de la batterie | `eps.bat_capacity_wh` (0x010A), `eps.bat_cycles` (0x0121), `eps.sa_age_factor` (0x0123) | □ | Comparer avec la référence de la recette en orbite |
| 3 | Charge utile / Thermique : autorité du refroidisseur | `payload.cooler_margin_k` (0x064B), `payload.cooler_floor_c` (0x064A) | □ | Une marge qui diminue est le signe avant-coureur d'un FPA trop chaud |
| 4 | AOCS : enveloppe de moment cinétique et santé des roulements | `aocs.h_env_frac` (0x02BA), `aocs.rw1_bearing_health` … (0x0284–0x0287) | □ | La tendance, c'est la fréquence croissante des déchargements, et non un déchargement isolé |
| 5 | TT&C : marge de liaison et TEB par station | `ttc.link_margin` (0x0503), `ttc.ber` (0x050C) | □ | Par station et par élévation |
| 6 | Chaque poste : signaler toute dégradation > 5 % par rapport à la référence de la recette en orbite | (revue) | □ | |
| 7 | FD : briefer le responsable de mission sur les points de surveillance | (briefing / journal de mission) | □ | « Trend review complete » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-nominal" markdown="1">

<div class="procedure-card-header" markdown="1">[FD] NOM-012 — Passation de consignes</div>

**Point d'entrée :** fin de quart ; le FD sortant briefe le FD entrant sur l'état, les points ouverts et le prochain passage.

**Objectif :** transférer proprement la responsabilité du satellite en ≤ 5 minutes, en veillant à ce qu'aucun point ne se perde en route.

**Issues défavorables possibles / écarts :**

- Procédure de contingence ouverte en cours d'exécution → la passation doit transférer explicitement l'autorité et l'état d'avancement des étapes
- Le FD entrant n'est pas d'accord avec la configuration actuelle → le FD sortant reste en poste jusqu'à obtenir un consensus
- Passage critique dans les 15 min suivant la passation → différer la passation après le passage

**Remarque.** Cette fiche n'est **pas** consultative : l'étape 1 est un véritable balayage des six structures de données de servitude et l'étape 4 une véritable requête de plan bord S11.

**Modèle complet :** voir §9.5.

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FD sortant : énoncer la configuration du satellite (mode, SoC, télémesure clé) | `HK_REQUEST(sid=1…6)` (S3.27), puis boucle vocale | □ | Une ligne |
| 2 | FD sortant : anomalies ouvertes / FDIR acquittées | (revue des fiches) | □ | Chaque point par son identifiant |
| 3 | FD sortant : travaux ouverts / procédures en cours | (journal de mission) | □ | P. ex. « NOM-007 desat scheduled next eclipse » |
| 4 | FD sortant : résumé du plan du prochain passage | `LIST_SCHEDULE` (S11.17) ; (FDS) | □ | Heure d'AOS, activités clés |
| 5 | FD entrant : collationnement de l'état, des anomalies, du plan | (boucle vocale) | □ | Mot pour mot |
| 6 | Les deux FD : transfert de l'autorité sur la boucle | (annonce formelle) | □ | « NOM-012 complete » |

</div>

<div style="page-break-before: always"></div>

## 14.4 Fiches de procédures de contingence

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-001 — Délestage sur sous-tension</div>

**Point d'entrée :** la règle FDIR `eps_bus_undervoltage_payload_off` (ea_id 1001) se déclenche, ou `eps.uv_flag` (0x010E) = 1, ou `eps.bus_voltage` (0x0105) est observée sous 27.0 V.

**Objectif :** sortir la batterie de la sous-tension en délestant d'abord les charges les moins critiques, puis en attendant la recharge en phase éclairée.

*(Un bus d'environ 28 V est inhabituel sur un CubeSat 6U — l'architecture 2S (8 V) est plus courante. EOSAT-1 embarque une batterie **8S-1P** de 100 Wh (26,4 V en nominal, 29,2 V à 100 % de SoC, 21,5 V à 0 %) sur un bus de 28 V ; considérez ces valeurs de tension comme propres au simulateur.)*

*(Il s'agit de l'une des huit fiches exécutables par la machine. Sa forme livrée est une échelle de branchements à quatre échelons sur un seul paramètre, `eps.bus_voltage` (0x0105) — exécutée sans ses branchements, elle délesterait la charge utile, le refroidisseur, l'émetteur **et** les roues d'un satellite que le premier délestage avait déjà sauvé.)*

**Issues défavorables possibles / écarts :**

- La tension continue de baisser après un échelon de délestage → passer à l'échelon suivant de l'échelle
- La tension ne remonte pas une fois tous les échelons franchis → `OBC_SET_MODE(mode=2)` (EMERGENCY), puis EMG-002 Perte totale d'alimentation
- `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104) tous deux proches de zéro après la sortie d'éclipse → cause liée au générateur solaire ; voir CTG-009
- Rétablissement obtenu mais cause première incertaine → ouvrir une fiche d'anomalie ; informer le responsable de mission

**Arbre de décision (l'échelle livrée — chaque échelon est une véritable étape de branchement) :**

- Délester la charge utile. SI V > 26.5 V → MAINTENIR (HOLD) cet échelon et surveiller
- SINON délester le refroidisseur FPA. SI V > 26.0 V → MAINTENIR et surveiller
- SINON délester le PA bande S. SI V > 25.5 V → MAINTENIR et surveiller
- SINON délester la ligne des roues de réaction (`line_index=7`). SI V > 25.0 V → MAINTENIR et surveiller
- SINON dernier recours → `OBC_SET_MODE(mode=2)` EMERGENCY ; informer le FD de l'état de préparation d'EMG-002

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FD : GO pour le délestage | (annonce du FD) | □ | Double validation |
| 2 | EPS : délester la priorité 1 — charge utile OFF | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | `payload.mode` (0x0600) = 0 ; branchement sur V > 26.5 V |
| 3 | EPS : délester la priorité 2 — refroidisseur FPA OFF | `FPA_COOLER(on=0)` (S8 func_id 43) | □ | `tcs.cooler_fpa` (0x040C) = 0 ; branchement sur V > 26.0 V |
| 4 | EPS : délester la priorité 3 — PA bande S OFF | `TTC_PA_OFF` (S8 func_id 67) | □ | La TM en bande S s'arrête ; la balise UHF (SID 11) continue d'émettre |
| 5 | EPS : délester la priorité 4 — ligne des roues de réaction OFF | `EPS_POWER_OFF(line_index=7)` (S8 func_id 20) | □ | `eps.pl_aocs_wheels` (0x0117) = 0 ; perte du contrôle d'attitude actif |
| 6 | EPS : maintenir le niveau de délestage et surveiller le rétablissement | (lire SID 1) | □ | Critère de sortie : V > 28.0 V **et** SoC > 40 % |
| 7 | EPS : rétablir dans l'ordre inverse des priorités, à 5 min d'intervalle | ligne des roues → `TTC_PA_ON` → `FPA_COOLER(on=1)` → `PAYLOAD_SET_MODE(mode=1)` | □ | Remettre sous tension dans l'ordre de LEOP-007 |
| 8 | SPACON : ouvrir une fiche ; informer le responsable de mission | (fiche) | □ | « CTG-001 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-002 — Reprise après anomalie SCAO</div>

**Point d'entrée :** l'un quelconque des trois déclencheurs de la fiche livrée — `aocs.att_error` (0x0217) > 5°, une température de roue (`aocs.rw1_temp`–`rw4_temp`, 0x0218–0x021B) > 60 °C, ou le senseur stellaire signalant BLIND.

**Objectif :** circonscrire l'anomalie, rétablir un pointage trois axes stable en NOMINAL (mode 4) et identifier la cause première afin de choisir la bonne sous-procédure. Il n'existe pas de mode « SAFE_POINT » : l'attente sûre est COARSE_SUN (mode 3), et le repli d'amortissement des vitesses angulaires est DETUMBLE (mode 2).

**Issues défavorables possibles / écarts :**

- COARSE_SUN impossible à atteindre → CTG-008 (senseur stellaire), CTG-007 (roue) ou EMG-005 Perte d'attitude
- Causes premières en cascade (p. ex. senseur stellaire puis gyro) → coordonner les CTG en cascade ; reporter les activités charge utile
- Le pointage revient dans le bilan après un transitoire → consigner ; ne pas revenir en NOMINAL au cours du même passage ; attendre la revue des tendances

**Arbre de décision :**

- SI le senseur stellaire est en défaut → CTG-008
- SI une roue est anormale → CTG-007 ; SI deux ou plus → DETUMBLE (mode 2) et EMG-005
- SI `aocs.att_error` dépasse 15° à une étape quelconque → DETUMBLE (mode 2) immédiatement
- SI `eps.bus_voltage` (0x0105) < 26.5 V pendant la reprise → CTG-001 d'abord
- SI le transitoire a disparu mais que la cause première n'est pas identifiée → rester en COARSE_SUN pendant une orbite ; analyser

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : lire le mode, l'erreur de pointage, les vitesses et les températures des roues | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.mode` 0x020F, `aocs.att_error` 0x0217 |
| 2 | AOCS : désactiver toute roue en surchauffe ou oscillante | `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8 func_id 2) | □ | La vitesse décroît en moins de 30 s |
| 3 | AOCS : décharger le moment cinétique accumulé | `AOCS_DESATURATE` (S8 func_id 1) | □ | Roues actives vers 0 tr/min ; vitesses < 0.5 °/s |
| 4 | AOCS : vérifier la stabilité des vitesses angulaires | (lire SID 2) | □ | `rate_roll/pitch/yaw` (0x0204–0x0206) chacune < 0.1 °/s |
| 5 | AOCS : rétablir le pointage nadir | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | `aocs.mode` = 4 (NOMINAL) ; erreur < 1.0° en 120 s |
| 6 | AOCS : en cas de panne de plusieurs roues, commander DETUMBLE à la place | `AOCS_SET_MODE(mode=2)` (S8 func_id 0) | □ | Vitesses < 2.0 °/s en 300 s, sinon EMG-001 |
| 7 | SPACON : ouvrir une fiche ; le FD décide entre reprise et attente | (journal de mission) | □ | « CTG-002 hand-off » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] CTG-003 — Reprise après perte de liaison TTC</div>

**Point d'entrée :** `ttc.link_status` (0x0501) = 0 (NO_LINK) persistant plus de 30 s après l'AOS prévue, ou une liaison établie qui tombe en cours de passage. LOCKED vaut **2**, et non 1.

**Objectif :** rétablir la liaison en parcourant les vérifications côté sol et le basculement de transpondeur — principal, redondant, puis de nouveau principal —, puis vérifier la qualité de la liaison et la santé des sous-systèmes avant d'escalader.

**Issues défavorables possibles / écarts :**

- Liaison non rétablie en fin de passage → un deuxième passage manqué consécutif déclenche EMG-004 Perte de communication
- Liaison revenue mais marge < 3 dB → la reprise n'est pas terminée ; la traiter comme marginale, replanifier le travail de liaison descendante et informer le FD
- Défaut de l'antenne sol découvert en cours de reprise → CTG-020 Panne d'antenne de station sol

**Arbre de décision (abrégé ; voir le §9.4 pour la version complète) :**

- SI la station sol ne poursuit pas → CTG-020
- SI la station poursuit mais sans porteuse → basculer de transpondeur (redondant, puis retour au principal)
- SI toujours pas de porteuse → voie de commande en aveugle CTG-019
- SI aucune reprise avant la LOS ET passage suivant également manqué → EMG-004

**Liste de vérification complète en mode « lire et faire » :** voir le §9.4, tableau 9.3.

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : vérifier la station de poursuite (et toute autre station en visibilité) | (panneau MPS) | □ | Poursuite de l'antenne, puissance montante, précompensation Doppler ; réseau de cinq stations ; en l'absence de poursuite, CTG-020 |
| 2 | TT&C : demande de HK en aveugle sur le transpondeur principal | `HK_REQUEST(sid=6)` (S3.27) | □ | `ttc.link_status` (0x0501) = 2 en 30 s → étape 5 |
| 3 | TT&C : basculer sur le transpondeur redondant (en aveugle) | `TTC_SWITCH_REDUNDANT` (S8 func_id 64) | □ | Attendre 45 s pour la mise sous tension et l'accrochage → étape 5 si accroché |
| 4 | TT&C : si toujours rien, réessayer le principal (en aveugle) | `TTC_SWITCH_PRIMARY` (S8 func_id 63) | □ | Attendre 45 s → étape 5 si accroché, étape 6 sinon |
| 5 | TT&C + tous : vérifier la qualité de la liaison et la santé des sous-systèmes | `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` (S3.27) | □ | RSSI (0x0502) > −90 dBm ; marge (0x0503) > 3.0 dB ; consigner l'unité active (`ttc.mode` 0x0500) ; bus > 27.0 V ; `obdh.mode` ni en sécurité ni en urgence |
| 6 | SPACON : en l'absence de reprise, consigner chaque commande en aveugle et escalader | (journal de mission) | □ | Prévenir le directeur de mission et le FDS ; réserver le passage suivant ; confirmer que la minuterie d'absence de contact de 24 h tourne ; deux passages manqués → EMG-004 |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[SE] CTG-004 — Dépassement thermique</div>

**Point d'entrée :** une zone surveillée franchit une limite jaune — `tcs.temp_obc` (0x0406) hors de −5 / +55 °C, `tcs.temp_battery` (0x0407) hors de +2 / +42 °C, `tcs.temp_fpa` (0x0408) hors de −45 / −15 °C.

**Objectif :** ramener les températures des zones dans leur plage en reconfigurant les thermostats des réchauffeurs ou en délestant les charges qui produisent de la chaleur.

**Issues défavorables possibles / écarts :**

- Dépassement chaud toujours en hausse après action → passer à EMG-006 Emballement thermique
- Dépassement froid sans rétablissement → vérifier l'état des réchauffeurs (CTG-012 si la ligne s'est ouverte) ; envisager un délestage pour réaffecter la puissance
- Zone charge utile concernée → mettre la charge utile en sécurité (`PAYLOAD_SET_MODE(mode=0)`) avant que la zone n'atteigne le seuil d'endommagement
- Batterie au-dessus de +45 °C ou OBC au-dessus de +60 °C → `OBC_SET_MODE(mode=2)` / `mode=1` et faire remonter l'anomalie immédiatement

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Thermique : identifier la zone concernée et le sens de l'écart (chaud/froid) | `HK_REQUEST(sid=3)` (S3.27) | □ | SID 3 correspond au TCS |
| 2 | Thermique (froid) : activer le réchauffeur de la zone | `HEATER_BATTERY(on=1)` (func_id 40) / `HEATER_OBC(on=1)` (func_id 41) | □ | `tcs.htr_battery` 0x040A / `tcs.htr_obc` 0x040B = 1 |
| 3 | Thermique (chaud) : supprimer la charge thermique | `PAYLOAD_SET_MODE(mode=0)` (func_id 26) ; réchauffeur batterie OFF | □ | `payload.mode` (0x0600) = 0 en moins de 10 s |
| 4 | Thermique : surveiller la tendance de la zone pendant 15 min | (lire SID 3) | □ | ≥ 0.2 °C/min de retour vers la plage |
| 5 | Thermique : en l'absence d'amélioration, régler à nouveau le thermostat | `HEATER_SET_SETPOINT(circuit=…, on_temp=…, off_temp=…)` (S8 func_id 44) | □ | Circuits 0 batterie, 1 OBC, 2 propulseur — il n'existe **pas** de paramètre `tcs.htr_<zone>_setpoint` |
| 6 | Thermique : cas chaud toujours en hausse — réorienter le satellite pour dissiper | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 3 (COARSE_SUN) |
| 7 | Thermique : après rétablissement, rendre le circuit au thermostat | `HEATER_AUTO_MODE(circuit=0)` (S8 func_id 45) | □ | Uniquement si les réchauffeurs ont été pilotés manuellement |
| 8 | SPACON : ouvrir une fiche ; si la zone chaude continue de monter, EMG-006 | (journal de mission) | □ | « CTG-004 status » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[PE] CTG-006 — Anomalie charge utile</div>

*(Note de la rédaction : il s'agit de la **CTG-006 Anomalie charge utile** du simulateur, `contingency/payload_anomaly.md`, sous forme condensée. La fiche livrée est centrée sur le cas thermique du FPA ; cette version couvre aussi les défauts de transition de mode de la charge utile.)*

**Point d'entrée :** le mode de la charge utile ne change pas comme commandé ; ou `payload.fpa_temp` (0x0601) au-dessus de −15 °C, ou en hausse de plus de 0.5 °C/min avec le refroidisseur actif.

**Objectif :** ramener la charge utile en STANDBY, rétablir l'état thermique et déterminer si l'anomalie est d'origine logicielle, liée au séquencement des commandes ou matérielle.

**Modes de la charge utile :** 0 OFF, 1 STANDBY, 2 IMAGING, **3 CALIBRATION**.

**Issues défavorables possibles / écarts :**

- Charge utile bloquée en IMAGING sans sortie possible → commander OFF, puis effectuer un cycle d'alimentation de la ligne charge utile (à la manière de CTG-012) après GO du FD
- FPA au-dessus de +10 °C à une étape quelconque → charge utile OFF immédiatement ; aucun redémarrage sans autorisation du sol
- Le refroidisseur ne s'active pas → laisser la charge utile OFF et exécuter CTG-004 pour évaluer la zone
- Écart de plus de 5 °C entre les capteurs FPA de la charge utile et du TCS → suspecter un capteur ; retenir la valeur la plus basse pour les décisions de sécurité

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Charge utile : lire le mode courant et la température du FPA | `HK_REQUEST(sid=5)` + `HK_REQUEST(sid=3)` (S3.27) | □ | `payload.mode` 0x0600 ; 0x0601 comparé à `tcs.temp_fpa` 0x0408 |
| 2 | Charge utile : commander OFF pour sortir de l'état bloqué | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | 0x0600 = 0 en moins de 10 s |
| 3 | Charge utile / Thermique : confirmer que le refroidisseur fonctionne | (lire SID 3) | □ | `tcs.cooler_fpa` (0x040C) = 1 ; cryoréfrigérateur miniature de type Stirling |
| 4 | Charge utile : surveiller le refroidissement pendant 20 min au plus | (lire les SID 3 et 5) | □ | ≥ 0.3 °C/min ; stabilisation sous −20 °C |
| 5 | Charge utile : redémarrer en STANDBY | `PAYLOAD_SET_MODE(mode=1)` (S8 func_id 26) | □ | 0x0600 = 1 ; le FPA reste sous −18 °C |
| 6 | Charge utile : si elle reste bloquée, effectuer un cycle d'alimentation de la ligne charge utile (GO du FD) | `EPS_POWER_OFF(line_index=3)` / `EPS_POWER_ON(line_index=3)` (func_id 20 / 19) | □ | 30 à 60 s hors tension ; la ligne 3 est celle de la charge utile |
| 7 | SPACON : ouvrir une fiche | (journal de mission) | □ | « CTG-006 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-007 — Anomalie de roue de réaction</div>

**Point d'entrée :** gigue de vitesse > ±500 tr/min sur 10 s, divergence de vitesse inattendue, vitesse > 6500 tr/min, ou température de palier de roue > 60 °C.

**Objectif :** isoler la roue défaillante, reconfigurer le contrôle sur trois roues et confirmer que le pointage nadir en NOMINAL (mode 4) reste atteignable. EOSAT-1 embarque quatre roues en pyramide ; **trois suffisent** — un ensemble de 3 roues sur 4 engendre toujours R³, et FINE_POINT fonctionne en mode dégradé sur cet ensemble (`aocs.fine_degraded`, 0x0299).

**Issues défavorables possibles / écarts :**

- Bilan de pointage inatteignable avec trois roues → COARSE_SUN (mode 3) et reporter les prises de vue
- Deux roues ou plus concernées → DETUMBLE (mode 2) et envisager EMG-005 Perte d'attitude
- Symptôme de roue bloquée dû en réalité à une panne de bus → CTG-017 à la place

**Arbre de décision :**

- SI exactement une roue est anormale → la désactiver, reconfigurer sur trois roues, maintenir NOMINAL avec un bilan assoupli à 1.5° ; ouvrir une fiche
- SI `aocs.att_error` (0x0217) dépasse 10° pendant la désactivation → DETUMBLE (mode 2) jusqu'à stabilisation des vitesses angulaires
- SI NON récupérable → COARSE_SUN (mode 3) ; reporter les prises de vue ; le FD évalue l'impact sur la mission

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : identifier la roue concernée à partir des vitesses et des températures | `HK_REQUEST(sid=2)` (S3.27) | □ | Vitesses 0x0207–0x020A (lecture seule) ; températures 0x0218–0x021B |
| 2 | AOCS : désactiver la roue concernée | `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8 func_id 2) | □ | La vitesse commence à décroître en moins de 10 s ; les vitesses angulaires restent < 1.0 °/s |
| 3 | AOCS : confirmer que la boucle s'est reconfigurée sur trois roues — aucune commande | (observation, 15 s) | □ | `aocs.att_error` (0x0217) qui converge sous 2,0° en 60 s. Il n'existe ni commande de mode à trois roues ni paramètre `aocs.wheel_config` : `AOCS_DISABLE_WHEEL` à l'étape 2 constitue toute la reconfiguration |
| 4 | AOCS : décharger le moment cinétique sur les trois roues restantes | `AOCS_DESATURATE` (S8 func_id 1) | □ | Prévoir **20 à 50 min**, et non quelques minutes — voir la remarque ci-dessous |
| 5 | AOCS : confirmer le pointage nadir en configuration trois roues | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 4 ; erreur < 1.5° |
| 6 | SPACON : ouvrir une fiche ; informer le responsable de mission de l'impact sur l'agilité | (journal de mission) | □ | « CTG-007 closed » |

**Planifier le déchargement avec réalisme.** DESAT (mode 7) est un déchargement magnétique par produit vectoriel, `m = k·(h_body × B)/|B|²`, limité par la géométrie : la durée réaliste du déchargement est de **20 à 50 minutes**, et non de cinq à quinze comme l'indiquait auparavant le livre. Il se termine désormais — il s'arrête sur une zone morte de 5e-4 N·m·s appliquée à `aocs.h_body_nms` (0x029B) — et il est borné par un **délai d'attente de 3600 s**, au terme duquel le satellite émet AOCS_DESAT_INEFFECTIVE (0x020E) et rend la main au lieu de rester indéfiniment en DESAT. **Prise de vue et désaturation s'excluent mutuellement :** `aocs.desat_inhibit` (0x029A) est activé automatiquement tant que `payload.mode` vaut 2 (IMAGING), et peut aussi être verrouillé par l'opérateur avec `AOCS_SET_DESAT_INHIBIT(inhibit=…)` (S8 func_id 96) — un déchargement demandé pendant un créneau de prise de vue est refusé, avec indication du motif. À la fin du déchargement, le satellite détermine son mode de retour d'après `aocs.commanded_mode` (0x0297) : il revient au dernier mode commandé par le sol, et non à un mode par défaut. Planifiez les déchargements sur cette fenêtre de 20 à 50 min ; ne programmez pas un passage de prise de vue en vous fondant sur une hypothèse de dix minutes.

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-008 — Panne du senseur stellaire</div>

**Point d'entrée :** `aocs.st1_status` (0x0240) = 4 (FAILED) avec `aocs.st1_num_stars` (0x0241) = 0 ; ou divergence de la détermination d'attitude. Le statut 3 correspond à BLIND (éblouissement par le Soleil, la Lune ou le limbe terrestre) — attendre jusqu'à 120 s avant de déclarer une panne.

**Objectif :** basculer sur le senseur stellaire redondant (ST2) et, en cas d'échec, se replier sur l'attente COARSE_SUN. EOSAT-1 embarque **deux** senseurs stellaires, ST1 et ST2.

*(Il s'agit de l'une des huit fiches exécutables par la machine ; la version livrée effectue un branchement sur `aocs.st2_status` (0x0243). Exécutée sans ses branchements, elle sélectionnerait un senseur qui ne poursuit pas, éteindrait le seul autre senseur et commanderait le repli dégradé — les trois, dans cet ordre.)*

**Issues défavorables possibles / écarts :**

- ST2 accroche → revenir au mode antérieur à la panne ; surveiller ; il ne reste plus aucune redondance de senseur stellaire
- ST2 n'atteint pas TRACKING en 120 s → COARSE_SUN (mode 3) ; le pointage fin est perdu ; la prise de vue charge utile est impossible
- CSS également invalides (éclipse) → DETUMBLE (mode 2) sur magnétocoupleurs et attendre la phase éclairée ; candidat à EMG-005

**Arbre de décision :**

- SI ST2 = 2 (TRACKING) après mise sous tension → `ST_SELECT(unit=2)`, puis isoler ST1 ; la fiche se termine
- SI ST2 n'atteint pas TRACKING → aller directement au repli COARSE_SUN ; ne **pas** sélectionner un senseur qui ne poursuit pas

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : confirmer la panne de ST1 et consigner les vitesses angulaires | `HK_REQUEST(sid=2)` (S3.27) | □ | 0x0240 = 4, 0x0241 = 0 |
| 2 | AOCS : mettre ST2 sous tension et attendre son démarrage | `ST2_POWER(on=1)` (S8 func_id 5) | □ | 0x0243 : 0 OFF → 1 BOOT → 2 TRACKING en moins de 120 s |
| 3 | AOCS : sélectionner ST2 comme senseur principal | `ST_SELECT(unit=2)` (S8 func_id 6) | □ | `aocs.att_error` (0x0217) commence à diminuer |
| 4 | AOCS : isoler ST1 défaillant | `ST1_POWER(on=0)` (S8 func_id 4) | □ | Confirmer via `aocs.st1_num_stars` = 0 — 0x0240 reste à 4 : une unité défaillante mise hors tension reste défaillante |
| 5 | AOCS : si ST2 n'a jamais accroché, passer en attente de repli | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 3 (COARSE_SUN) ; `aocs.css_valid` (0x0248) = 1 |
| 6 | AOCS : en mode dégradé, mettre la charge utile hors tension | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | La prise de vue est impossible en COARSE_SUN |
| 7 | SPACON : ouvrir une fiche ; informer le responsable de mission du report des prises de vue | (journal de mission) | □ | « CTG-008 closed » — consigner la branche suivie |

**Remarque sur COARSE_SUN :** il s'agit d'une **attente, et non d'une destination**. Ce mode ne fait pas partie de l'ensemble des modes opérationnels du modèle ; le commander n'écrase donc pas `aocs.commanded_mode` (0x0297) : le satellite revient de lui-même au mode commandé par le sol lorsqu'un senseur se rétablit. Surveillez `aocs.mode_demoted` (0x0298) plutôt que de renvoyer la commande manuellement.

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-009 — Dégradation du générateur solaire</div>

*(Note de la rédaction : il s'agit de la **CTG-009 Dégradation du générateur solaire** du simulateur, `contingency/solar_array_degradation.md`, sous forme condensée.)*

**Point d'entrée :** `eps.sa_a_current` (0x0103) ou `eps.sa_b_current` (0x0104) inférieur de plus de 20 % à la prévision pendant une phase éclairée confirmée, ou dégradation lente signalée par la revue des tendances.

**Objectif :** confirmer l'anomalie, écarter les causes transitoires (attitude, éclipse) et quantifier l'impact sur la mission.

**Issues défavorables possibles / écarts :**

- Une seule aile concernée → mission toujours viable avec une marge réduite ; le FDS replanifie
- Les deux générateurs sous 0.2 A en plein soleil → voie CTG-005 Mode survie EPS immédiatement
- Dégradation supérieure à 5 % par jour → avancer les priorités de liaison descendante ; prévoir un profil de puissance réduite
- SoC inférieur à 20 % pendant l'investigation → interrompre et basculer sur la voie de mise en sécurité EPS

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : quantifier le déficit par rapport à la prévision | `HK_REQUEST(sid=1)` (S3.27) | □ | 0x0103 / 0x0104 comparés à la prévision ; `eps.power_gen` 0x0107 |
| 2 | EPS : comparer le rapport A/B sur trois échantillons espacés de 30 s | (lire SID 1) | □ | Rapport nominal 0.9–1.1 ; écart d'un seul côté = défaillance locale |
| 3 | AOCS : écarter l'attitude comme cause | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.mode` (0x020F) = 4 (NOMINAL) ou 3 (COARSE_SUN) ; `att_error` < 2° |
| 4 | EPS : vérifier l'état de déploiement des ailes | `GET_PARAM(param_id=0x0144)` (S20.3) | □ | `eps.wing_status` : bit0 +Y, bit1 −Y — également transmis dans SID 1 |
| 5 | EPS : consigner le courant de chaque aile sur une orbite complète | (lire SID 8) | □ | `eps.sa_wing_py_current` 0x0146, `sa_wing_my_current` 0x0147 (SID 8, cadence de 8 s) |
| 6 | EPS : délester si nécessaire pour respecter le bilan dégradé | `PAYLOAD_SET_MODE(mode=1)` puis `(mode=0)` ; `HEATER_THRUSTER(on=0)` (func_id 42) | □ | Viser une réserve ≥ 3 W |
| 7 | EPS / FDS : refaire le bilan de puissance pour les prochaines 24 h | (outil FDS) | □ | Comparaison quotidienne des tendances pendant 7 jours |
| 8 | SPACON : ouvrir une fiche ; informer le responsable de mission | (journal de mission) | □ | « CTG-009 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-010 — Reprise après chien de garde OBDH</div>

**Point d'entrée :** événement de réinitialisation par le chien de garde dans le journal S5, redémarrage inattendu, ou acquittement de `OBC_BOOT_APP` sans fin d'exécution.

**Objectif :** rétablir l'état nominal de l'OBC après un redémarrage par le chien de garde et récupérer la configuration perdue.

**Issues défavorables possibles / écarts :**

- L'OBC redémarre de nouveau immédiatement → suspecter une corruption logicielle ; envisager la voie EMG-003 Redémarrage de l'OBC
- Table FDIR non restaurée après le redémarrage → recharger la table nominale (sous-étape de COM-008)
- Consignes des réchauffeurs perdues → les réappliquer selon le référentiel TCS
- Lignes d'alimentation verrouillées matériellement conservées mais état logiciel perdu → réarmer les programmes de commandes datées (NOM-008)

**Arbre de décision :**

- SI le redémarrage est propre et stable → la reprise se fait par CTG-010 ; ouvrir une fiche
- SI `obdh.reboot_count` (0x030A) augmente de plus de 3 en une heure → boucle d'amorçage ; `OBC_SET_MODE(mode=2)` et EMG-003
- SI la perte de table ou de consignes ne peut être réparée → reporter les engagements du prochain passage ; analyse par le FD

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | SPACON : rétablir la liaison si elle a été perdue | selon CTG-003 | □ | RSSI / marge |
| 2 | SPACON : confirmer le redémarrage et consigner le compteur | `HK_REQUEST(sid=4)` (S3.27) | □ | `obdh.reboot_count` (0x030A) incrémenté |
| 3 | SPACON : vérifier l'image OBC ; démarrer l'application si l'OBC est dans le chargeur d'amorçage | `obdh.sw_image` (0x0311) ; `OBC_BOOT_APP` (S8 func_id 55) | □ | S1.1 + S1.7 en moins de 15 s ; 0x0311 → 1 |
| 4 | SPACON : réactiver les structures de servitude | `HK_ENABLE(sid=2…6)` (S3.5) | □ | Le démarrage réapplique `default_enabled_sids` = [1, 11] — les SID 2 à 6 ne reviennent **pas** d'eux-mêmes |
| 5 | SPACON : confirmer l'identité de la table FDIR | (panneau FDIR) | □ | Nominale ou LEOP uniquement |
| 6 | SPACON : réappliquer les réglages perdus (consignes des réchauffeurs, forçages FDIR) et **resynchroniser l'horloge** | `SET_TIME(cuc_seconds=T_corrected)` (S9.1) | □ | Le chargeur d'amorçage a ramené l'horloge à **J2000** : s'attendre à `obdh.time_ref` (0x0A13) = 0 (NONE) et `obdh.time_since_sync_s` (0x0A14) = 4294967295. Exécuter la séquence LEOP-006 / NOM-008 ; un redémarrage implique toujours une resynchronisation |
| 7 | SPACON : réarmer les commandes datées — **après** avoir corrigé l'horloge | (S11) | □ | NOM-008 Synchronisation de l'horloge. Le planning bord se déclenche sur le temps bord : des commandes datées réarmées sur une horloge à J2000 ne s'exécutent jamais |
| 8 | SPACON : rétablir l'OBC en NOMINAL s'il est revenu en SAFE | `OBC_SET_MODE(mode=0)` (S8 func_id 50) | □ | `obdh.mode` (0x0300) = 0 ; charge CPU < 70 % |
| 9 | SPACON : ouvrir une fiche ; GO du FD pour la reprise | (journal de mission) | □ | « CTG-010 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-012 — Traitement d'une surintensité</div>

**Point d'entrée :** un déclenchement sur surintensité apparaît dans `eps.oc_trip_flags` (0x010D) ; la cascade FDIR correspondante (`eps_overcurrent_<bus>`, indexée sur le même masque de bits) ouvre la ligne de manière autonome.

**Objectif :** prendre acte de l'action autonome, identifier la ligne concernée, déterminer si le défaut est transitoire ou persistant, et ne réinitialiser/réactiver la ligne que lorsque le courant indique que c'est sans danger.

**Table des lignes (neuf lignes, indices 0 à 8) :** 0 obc, 1 ttc_rx, 2 ttc_tx, 3 payload, 4 fpa_cooler, 5 htr_bat, 6 htr_obc, 7 aocs_wheels, 8 prop. Les lignes 0 et 1 ne sont pas commutables ; un déclenchement sur l'une d'elles constitue une anomalie grave. Les indicateurs d'état des lignes occupent 0x0110–0x0117 pour les lignes 0 à 7, et les courants par ligne 0x0118–0x011F pour les lignes 0 à 7. **La ligne prop rompt cette arithmétique :** la ligne 8 correspond à `eps.pl_prop` en **0x014A** et à `eps.line_current_8` en **0x014B**, et non à 0x0118 et 0x0120. 0x0120 est `eps.bat_dod`. N'extrapolez pas le bloc au-delà de l'indice 7.

**Issues défavorables possibles / écarts :**

- Courant toujours élevé après le déclenchement → défaut persistant ; ne **pas** réinitialiser, isoler et faire remonter l'anomalie
- Nouveau déclenchement immédiatement après une réinitialisation → ne pas tenter de troisième réinitialisation ; `EPS_POWER_OFF` et faire remonter l'anomalie
- Plusieurs lignes concernées → suspecter le bus en amont ; CTG-017 Basculement sur panne de bus
- Ligne critique concernée (OBC, TT&C RX) → faire remonter l'anomalie ; candidat à EMG-001

**Arbre de décision :**

- SI la FDIR a déjà ouvert la ligne ET que le courant de la ligne est proche de 0 A → transitoire ; réinitialiser l'indicateur et réactiver
- SI le courant de la ligne reste élevé → persistant ; laisser la ligne ouverte, ouvrir une fiche, faire remonter l'anomalie
- SI le déclenchement a coïncidé avec une transition de mode ou une mise sous tension → le courant d'appel est la cause probable ; traiter comme transitoire

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : décoder le masque de déclenchement pour identifier la ligne | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.oc_trip_flags` (0x010D) ; SID 1 correspond à l'EPS |
| 2 | EPS : lire le courant de cette ligne | (lire SID 1) | □ | 0x0118 + N pour N = 0–7 ; **0x014B pour la ligne 8 (prop)**. Proche de 0 A = LCL ouvert comme prévu |
| 3 | EPS : se coordonner avec le poste responsable sur l'état du sous-système | (boucle vocale) | □ | Écarter tout dommage matériel avant toute réinitialisation |
| 4 | EPS : réinitialiser l'indicateur de surintensité (GO du FD) | `EPS_RESET_OC_FLAG(line_index=N)` (S8 func_id 21) | □ | L'indicateur s'efface et le reste pendant 5 s |
| 5 | EPS : réactiver la ligne | `EPS_POWER_ON(line_index=N)` (S8 func_id 19) | □ | État (0x0110 + N) = 1 pour N = 0–7 ; **0x014A pour la ligne 8**. Pas de nouveau déclenchement en 30 s |
| 6 | EPS : vérifier que le sous-système aval s'est rétabli | `HK_REQUEST` sur le SID de ce sous-système | □ | 2 AOCS, 3 TCS, 5 charge utile, 6 TT&C, 9 PROP (`HK_ENABLE(sid=9)` d'abord — SID 9 ne fait pas partie de l'ensemble par défaut) |
| 7 | SPACON : ouvrir une fiche d'anomalie avant la fin du passage | (fiche) | □ | Cause première à déterminer |
| 8 | SPACON : informer le quart entrant lors de la passation de consignes NOM-012 | (journal de mission) | □ | « CTG-012 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-013 — Défaillance d'un élément de batterie</div>

*(Note de la rédaction : il s'agit de la **CTG-013 Défaillance d'un élément de batterie** du simulateur, `contingency/battery_cell_failure.md`, sous forme condensée.)*

**Point d'entrée :** `eps.bat_voltage` (0x0100) inférieure de plus de 1.0 V à la valeur attendue pour la valeur `eps.bat_soc` (0x0101) rapportée, ou chute brutale de tension, ou dégradation signalée par la revue des tendances.

**Objectif :** caractériser l'anomalie, confirmer que la batterie est thermiquement sûre et décider si la capacité restante permet de survivre à l'éclipse avec la charge actuelle.

**Issues défavorables possibles / écarts :**

- La tension continue de baisser pendant la caractérisation → délestage CTG-001
- `eps.bat_temp` (0x0102) au-dessus de +40 °C → court-circuit interne possible ; désactiver le réchauffeur batterie et délester ; au-dessus de +50 °C, commander EMERGENCY et suivre EMG-002
- `eps.bat_voltage` sous 22.0 V → risque de décharge profonde ; tout délester sauf l'OBC et la réception TT&C (RX)
- Perte de capacité supérieure à la marge mission → informer le responsable de mission ; le FDS replanifie le rapport cyclique

**Remarque :** il n'existe aucune télécommande d'équilibrage des éléments dans `tc_catalog.yaml`, ni aucune télémesure au niveau des éléments. Les grandeurs observables sont la tension bus/batterie, le SoC, la température, le courant et `eps.bat_capacity_wh` (0x010A) ; l'opérateur déduit l'état des éléments de l'écart entre la tension et le SoC.

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : récupérer la télémesure batterie et calculer la tension attendue pour le SoC rapporté | `HK_REQUEST(sid=1)` (S3.27) | □ | SID 1 correspond à l'EPS ; SID 8 est la structure EPS étendue |
| 2 | EPS / Thermique : recouper la température de la batterie | `HK_REQUEST(sid=3)` (S3.27) | □ | `eps.bat_temp` 0x0102 comparée à `tcs.temp_battery` 0x0407 |
| 3 | EPS : si la batterie est chaude, désactiver son réchauffeur | `HEATER_BATTERY(on=0)` (S8 func_id 40) | □ | `tcs.htr_battery` (0x040A) = 0 |
| 4 | EPS : calculer la marge de survie en éclipse sur `eps.bat_capacity_wh` (0x010A) | (calcul opérateur) | □ | Réserve de 20 % de SoC ; éclipse ≈ 35 min |
| 5 | EPS : si la marge est négative, délester la charge utile, puis le refroidisseur, puis le PA | `PAYLOAD_SET_MODE(mode=0)` / `FPA_COOLER(on=0)` / `TTC_PA_OFF` | □ | Recalculer après chaque délestage |
| 6 | EPS / FDS : replanifier le rapport cyclique si la capacité est réduite | (outil FDS) | □ | Nouveau plan de passage |
| 7 | SPACON : ouvrir une fiche ; informer le responsable de mission | (journal de mission) | □ | « CTG-013 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] CTG-014 — Anomalie de TEB</div>

**Point d'entrée :** `ttc.ber` (0x050C) ≥ −5 — c'est-à-dire un TEB plus mauvais que 1e-5. Le paramètre contient l'exposant en base 10 ; une valeur « moins négative » est donc plus mauvaise.

**Objectif :** rétablir la qualité de la liaison descendante en refroidissant l'amplificateur, en descendant l'échelle des débits ou en ajustant la puissance d'émission ; replanifier les segments perdus.

**Échelle des débits :** BEACON / LOW / HIGH = **1 / 16 / 128 kbit/s**. Il n'existe pas d'échelon « medium ». Un passage de HIGH à LOW fait gagner 9,03 dB d'Eb/N0 grâce au terme `−10·log10(R)`, plus environ 1,5 dB de gain de codage (QPSK RS(255,223) → BPSK conv(7,1/2)+RS). BEACON est la liaison de secours du chargeur d'amorçage et ne peut pas être commandé ici.

**Issues défavorables possibles / écarts :**

- Le TEB persiste alors que le débit est déjà LOW → il n'existe pas d'échelon inférieur ; basculer sur la voie CTG-003 Perte de liaison
- TEB propre à une station sol → candidat à CTG-020
- Faible élévation (`ttc.contact_elevation`, 0x050A < 10°) → la dégradation est due à la géométrie attendue, il ne s'agit pas d'une anomalie
- Récurrence sur plusieurs passages → suspecter l'amplificateur du satellite ; ouvrir une fiche

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | TT&C : caractériser l'anomalie | `HK_REQUEST(sid=6)` (S3.27) | □ | 0x050C, `ttc.eb_n0` 0x0519, `link_margin` 0x0503, `rssi` 0x0502 |
| 2 | TT&C : vérifier l'amplificateur de puissance | (lire SID 6) | □ | `ttc.pa_temp` (0x050F) < 55 °C ; `ttc.tx_fwd_power` 0x050D |
| 3 | TT&C : si le PA est chaud, effectuer un cycle d'alimentation et réduire la puissance d'émission | `TTC_PA_OFF` (67) → 120 s → `TTC_PA_ON` (66) ; `TTC_SET_TX_POWER(level=0)` (68) | □ | La balise continue d'émettre pendant la coupure du PA |
| 4 | TT&C : descendre l'échelle des débits jusqu'à LOW | `TTC_SET_DATA_RATE(rate=0)` (S8 func_id 65) | □ | `ttc.tm_data_rate` (0x0506) = 16000 ; `ttc.tm_tier` (0x0539) = 1 |
| 5 | TT&C : si un vidage était en cours, lever la porte | `TTC_SET_DOWNLINK_MODE(on=0)` (S8 func_id 79) | □ | `ttc.downlink_mode` (0x053C) = 0 |
| 6 | Charge utile : replanifier les segments de liaison descendante concernés | (replanification selon NOM-003) | □ | |
| 7 | SPACON : ouvrir une fiche | (journal de mission) | □ | « CTG-014 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[PE] CTG-015 — Reprise après image corrompue</div>

**Point d'entrée :** `payload.checksum_errors` (0x0609) dépasse sa valeur de référence, ou `payload.last_scene_quality` (0x060D) signale la dernière scène.

**Objectif :** établir si la cause est la température du FPA, un segment mémoire défectueux ou une perturbation transitoire ; supprimer l'image défaillante, programmer une nouvelle acquisition et seulement ensuite reprendre.

**Issues défavorables possibles / écarts :**

- Corruption récurrente → surchauffe probable du FPA ; investigation thermique CTG-004
- Cas isolé → rayon cosmique probable ; remplacer l'image et continuer
- La nouvelle acquisition échoue aussi → reporter la scène à l'orbite suivante ; ouvrir une fiche

**Arbre de décision :**

- SI première occurrence → marquer, replanifier, continuer
- SI deuxième occurrence au cours du même passage → interrompre les prises de vue ; examiner la température du FPA / le bilan de pointage
- SI troisième occurrence → reporter au quart suivant ; informer le responsable de mission

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Charge utile : quantifier les erreurs de somme de contrôle et identifier la scène | `HK_REQUEST(sid=5)` (S3.27) | □ | Variation de 0x0609 ; `payload.last_scene_id` 0x060C |
| 2 | Charge utile / Thermique : vérifier la température du FPA | `HK_REQUEST(sid=3)` (S3.27) + SID 5 | □ | `payload.fpa_temp` 0x0601, `tcs.temp_fpa` 0x0408, `payload.fpa_ready` 0x0610 |
| 3 | Charge utile : si le FPA est chaud (> −20 °C), interrompre vers STANDBY et refroidir | `PAYLOAD_SET_MODE(mode=1)` (func_id 26) ; `FPA_COOLER(on=1)` (func_id 43) | □ | Attendre < −25 °C et `fpa_ready` = 1 |
| 4 | Charge utile : si un segment mémoire est en cause, passer la main à CTG-016 | `payload.mem_segments_bad` (0x0612) | □ | Marquer le segment avant de reprendre la vue |
| 5 | Charge utile : supprimer l'image corrompue (voie S8 canonique) | `PAYLOAD_DELETE_IMAGE(scene_id=X)` (S8 func_id 30) | □ | |
| 6 | Charge utile + AOCS : replanifier l'acquisition pour le prochain survol | (FDS) | □ | Selon l'arbre de décision |
| 7 | SPACON : ouvrir une fiche | (journal de mission) | □ | « CTG-015 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-016 — Défaillance d'un segment mémoire</div>

*(Note de la rédaction : il s'agit de la **CTG-016 Défaillance d'un segment mémoire** du simulateur, `contingency/memory_segment_failure.md`, sous forme condensée.)*

**Point d'entrée :** `payload.mem_segments_bad` (0x0612) dépasse sa dernière valeur connue, en général en même temps qu'une hausse de `payload.checksum_errors` (0x0609).

**Objectif :** identifier le segment mémoire concerné, le marquer comme inutilisable et replanifier les prises de vue en fonction de la capacité réduite.

**Issues défavorables possibles / écarts :**

- Nombre de segments défectueux en hausse rapide → suspecter un verrouillage (latch-up) radio-induit ; charge utile OFF, cycle d'alimentation après 60 s
- Données scientifiques dans le segment concerné → les images sont perdues ; consigner les identifiants de scène et coordonner une nouvelle acquisition
- Plus de 10 % de segments défectueux → faire remonter à la planification de mission pour une évaluation de la capacité à long terme

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Charge utile : lire le nombre de segments défectueux et les données de stockage | `HK_REQUEST(sid=5)` (S3.27) | □ | 0x0612, `payload.mem_total_mb` 0x060A, `mem_used_mb` 0x060B |
| 2 | Charge utile : demander le catalogue d'images pour localiser le segment | `PAYLOAD_GET_IMAGE_CATALOG` (S8 func_id 32) | □ | Les scènes corrompues désignent le segment défaillant |
| 3 | Charge utile : contrôler par CRC tout segment suspect | `MEM_CHECK(memory_id, address, length)` (S6.9) | □ | Une discordance confirme que le segment est défectueux |
| 4 | Charge utile : marquer le segment comme inutilisable | `PAYLOAD_MARK_BAD_SEGMENT(segment_id=N)` (S8 func_id 31) | □ | **N vaut de 0 à 7** — `num_memory_segments: 8` ; un indice ≥ 8 est rejeté |
| 5 | Charge utile : supprimer les images restées bloquées dans le segment défectueux | `PAYLOAD_DELETE_IMAGE(scene_id=X)` (S8 func_id 30) | □ | Pour chaque scène concernée |
| 6 | Charge utile : vérifier la capacité réduite au regard du plan de prise de vue | `HK_REQUEST(sid=5)` (S3.27) | □ | SID 5 correspond à la charge utile ; SID 4 à l'OBDH |
| 7 | SPACON : ouvrir une fiche | (journal de mission) | □ | « CTG-016 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-017 — Basculement sur panne de bus</div>

**Point d'entrée :** `obdh.bus_a_status` (0x030F) ou `obdh.bus_b_status` (0x0310) = 1 (ERROR), ou arrêt simultané du flux HK de plusieurs SID de sous-systèmes.

**Objectif :** basculer sur le bus redondant et rétablir la HK et la commande des sous-systèmes concernés.

**Issues défavorables possibles / écarts :**

- Le basculement ne rétablit pas la HK → suspecter une panne des deux bus ; candidat à EMG-003
- Le bus B tombe ensuite en panne → plus aucune redondance ; signaler la contrainte de mission au responsable de mission
- Le basculement provoque une réinitialisation momentanée d'un sous-système → attendu ; vérifier que chaque sous-système se rétablit

**Arbre de décision :**

- SI un seul sous-système est concerné → vérifier d'abord ce sous-système, et non le bus
- SI plusieurs sous-systèmes sont concernés via le bus A → basculement
- SI le bus B est déjà utilisé → escalade ; suspecter l'OBC

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | OBDH : établir quels SID manquent | `HK_REQUEST(sid=1…6)` (S3.27) | □ | Si seul SID 4 répond, le bus CAN est en cause |
| 2 | OBDH : confirmer les mots d'état des bus | `HK_REQUEST(sid=4)` (S3.27) | □ | 0x030F / 0x0310 = 1 (ERROR) ; `obdh.active_bus` 0x030E |
| 3 | FD : GO pour le basculement de bus (double validation) | (annonce du FD) | □ | |
| 4 | OBDH : commander le basculement | `OBC_SELECT_BUS(bus=0\|1)` (S8 func_id 54) | □ | La fonction 53 est `OBC_SWITCH_UNIT` — elle bascule l'**OBC**, et non le bus |
| 5 | OBDH : vérifier que le nouveau bus est actif et que la HK de tous les sous-systèmes reprend | (lire les SID 1, 2, 3, 4, 5, 6) | □ | En moins de 60 s |
| 6 | SPACON : ouvrir une fiche ; informer le responsable de mission (plus de redondance de bus) | (journal de mission) | □ | « CTG-017 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] CTG-019 — Absence de télémesure en début de passage</div>

**Point d'entrée :** AOS attendu, mais ni balise ni HK après l'instant prévu de la porteuse ; ou balise présente, mais la HK complète n'apparaît jamais après le démarrage de l'OBC.

**Objectif :** déterminer si le satellite répond (acquittements S1 présents) et, le cas échéant, poursuivre par commande en aveugle ; sinon, faire remonter l'anomalie.

**Issues défavorables possibles / écarts :**

- Le satellite acquitte les commandes mais aucune TM → posture de commande en aveugle ; désigner le passage suivant comme passage de rétablissement
- Ni acquittements ni TM → passage suivant également silencieux → EMG-004
- La géométrie était erronée depuis le début → revérifier les prévisions du FDS

**Arbre de décision :**

- SI des acquittements S1 sont reçus → poursuivre par commande en aveugle ; ne pas encore invoquer EMG-004
- SI aucun acquittement ET aucune TM → répéter le test de liaison ; si toujours rien au LOS, préparer EMG-004 pour le passage suivant
- SI balise seule, sans HK complète après `OBC_BOOT_APP` → il ne s'agit généralement **pas** d'une panne : le moteur réapplique `default_enabled_sids` = [1, 11] au démarrage de l'application ; les SID 2 à 6 doivent donc être réactivés avec `HK_ENABLE` (S3.5) avant d'être transmis. Envoyer d'abord ces commandes, puis commander en aveugle selon CTG-019 s'ils n'apparaissent toujours pas

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : vérifier la station de poursuite et la configuration bande de base | (panneau MPS) | □ | Réseau de cinq stations ; TRACKING |
| 2 | FDS : vérifier la prévision d'orbite / de passage | (FDS) | □ | Géométrie correcte |
| 3 | TT&C : test de connexion (en aveugle) | `CONNECTION_TEST` (S17.1) | □ | Guetter uniquement l'acquittement |
| 4 | TT&C : parcourir la chaîne RF en aveugle — ligne TX, PA, antenne | `eps.pl_ttc_tx` 0x0112 ; `ttc.pa_on` 0x0516 ; `ttc.antenna_deployed` 0x0520 | □ | `EPS_POWER_ON(line_index=2)`, `TTC_PA_ON` (66) selon les besoins |
| 5 | SPACON : si des acquittements sont présents, poursuivre les procédures par commande en aveugle | (journal de mission) | □ | Confirmations réduites |
| 6 | SPACON : si toujours silencieux au LOS, ouvrir une fiche haute priorité ; préparer EMG-004 pour le passage suivant | (journal de mission) | □ | « CTG-019 escalation » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[GS] CTG-020 — Panne d'antenne de station sol</div>

**Point d'entrée :** antenne principale (en général Iqaluit) perdue en cours de passage — perte soudaine et totale du signal, `ttc.carrier_lock` (0x0510) → 0, `ttc.link_status` (0x0501) → 0, alors que la télémesure TT&C du satellite était nominale dans la dernière trame reçue.

**Objectif :** reconnaître une panne côté sol, basculer sur une autre station du réseau de cinq stations pour le passage suivant et replanifier les activités concernées.

**Il s'agit de la seule fiche déclarée consultative.** Dans l'index livré, CTG-020 porte `advisory: true` avec le motif « segment sol pur : toutes les actions sont effectuées au sol et le satellite reste injoignable de bout en bout ». Sa liste `command_services` est vide et le MCS indique `runnable = false` pour cette fiche. Chaque étape ci-dessous est une action au sol — ne vous attendez **pas** à envoyer une télécommande pendant cette fiche ; c'est précisément sa raison d'être.

**Issues défavorables possibles / écarts :**

- Activité critique dans le temps perdue au cours du passage actuel → replanifier pour le prochain AOS (Troll, Svalbard, Inuvik ou O'Higgins)
- Station de secours également dégradée → candidat à EMG-004 sur les deux passages suivants
- Impact client → bulletin du responsable de mission

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : confirmer la panne d'antenne (et non une panne TT&C du satellite) | (TM bande de base / antenne) | □ | Dans la dernière trame, `ttc.rssi` 0x0502 et `link_margin` 0x0503 étaient nominaux |
| 2 | Segment sol : lire l'état des équipements de la station et la station active | (panneau MPS) | □ | `ttc.gs_equipment_status` 0x0524, `ttc.active_gs` 0x0523 |
| 3 | Segment sol : confier le passage suivant à une station de secours | (MPS) | □ | Mise à jour du planning — aucune télécommande n'est possible |
| 4 | FDS / planification de mission : replanifier les activités perdues dans le contact suivant | (outil de planification) | □ | L'envoi vers le bord se fait au passage suivant, pas pendant celui-ci |
| 5 | FD : informer le responsable de mission (bulletin client) | (point de situation) | □ | |
| 6 | SPACON : ouvrir une fiche | (journal de mission) | □ | « CTG-020 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-021 — Reprise par le chargeur d'amorçage de l'OBC</div>

**Point d'entrée :** toute la TM de l'APID applicatif cesse ; seule la balise SID 11 arrive sur l'APID du chargeur d'amorçage (0x002, distinct de l'APID applicatif 0x001). `obdh.sw_image` (0x0311) = 0.

**Objectif :** identifier la cause du redémarrage, tenter le démarrage de l'application et, en cas d'échec, passer à un rechargement de la mémoire ou un basculement d'unité.

**Issues défavorables possibles / écarts :**

- `OBC_BOOT_APP` envoyé mais aucun S1.7 en 30 s → positionner `OBC_BOOT_INHIBIT(inhibit=1)` (func 56), vérifier l'image applicative par `MEM_CHECK` (S6.9), puis réessayer
- CRC de l'image incorrect et durée de passage suffisante → recharger via `MEM_LOAD` (S6.2), revérifier, puis démarrer
- Rechargement impossible ou deux échecs de démarrage → basculer sur l'unité redondante via `OBC_SWITCH_UNIT` (S8 func_id 53), puis confirmer `obdh.active_obc` (0x030C)
- Erreurs ECC mémoire groupées → exécuter `OBC_MEMORY_SCRUB` (S8 func_id 51) avant la nouvelle tentative de démarrage

**Arbre de décision :**

- SI balise présente ET démarrage réussi → retour au nominal
- SI deux échecs de démarrage → basculer d'unité OBC (double validation)
- SI les deux unités redémarrent en boucle → passage en mode survie EMG-001

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | OBDH : confirmer l'état chargeur d'amorçage — `obdh.sw_image` (0x0311) = 0 | (lire SID 4, ou SID 11 si SID 4 ne répond pas) | □ | APID du chargeur d'amorçage uniquement |
| 2 | OBDH : consigner `obdh.last_reboot_cause` (0x0316) et `obdh.reboot_count` (0x030A) | (lire SID 4) | □ | 1=watchdog 2=memory 3=switchover 4=commanded |
| 3 | OBDH : commander le démarrage de l'application (double validation) | `OBC_BOOT_APP` (S8 func_id 55) | □ | S1.1 + S1.7 en moins de 30 s ; 0x0311 → 1 |
| 4 | TT&C : quitter le mode balise — le démarrage de l'application ne le fait **pas** | `TTC_SET_BEACON_MODE(on=0)` (S8 func_id 70) | □ | `ttc.beacon_mode` (0x0521) = 0 ; d'ici là, LOW est refusé (code d'échec 0x0007) |
| 5 | TT&C : sélectionner l'échelon des opérations de routine | `TTC_SET_DATA_RATE(rate=0)` (S8 func_id 65) | □ | LOW = 16 kbit/s ; le démodulateur de balise ne s'y verrouille pas |
| 6 | OBDH : réactiver les structures de servitude | `HK_ENABLE(sid=2…6)` (S3.5) | □ | Le démarrage réapplique `default_enabled_sids` = [1, 11] |
| 7 | OBDH : confirmer la transmission des SID 1 à 6 | (lire les SID) | □ | 1 EPS, 2 AOCS, 3 TCS, 4 OBDH, 5 charge utile, 6 TT&C |
| 8 | OBDH : resynchroniser l'horloge | `SET_TIME(cuc_seconds=T_corrected)` (S9.1) | □ | Le chargeur d'amorçage a ramené l'horloge à **J2000** et le démarrage de l'application ne l'a pas restaurée : `obdh.time_ref` (0x0A13) = 0 (NONE), `obdh.time_since_sync_s` (0x0A14) = 4294967295, et les paquets sont datés de l'an 2000 tant que cette étape n'est pas faite. Il s'agit d'un OBC non synchronisé, et non d'un bogue d'époque |
| 9 | SPACON : ouvrir une fiche ; informer le FD de la cause première | (journal de mission) | □ | « CTG-021 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-022 — Isolation d'une panne de bus CAN</div>

**Point d'entrée :** données de servitude d'un ou plusieurs sous-systèmes absentes depuis plus de 30 s ; `obdh.bus_a_status` (0x030F) ou `obdh.bus_b_status` (0x0310) = 1 (ERROR).

**Objectif :** identifier le bus CAN défaillant, basculer sur le bus redondant et vérifier que tous les sous-systèmes sont rétablis sur le nouveau bus.

**Issues défavorables possibles / écarts :**

- Le basculement ne rétablit pas les communications avec le sous-système perdu → la dérivation de bus de ce sous-système est rompue (panne d'une chaîne non redondée) ; poursuivre en mode dégradé
- Les deux états de bus signalent ERROR → plus aucun chemin de bus ; EMG-001 Mode survie d'urgence
- Le basculement rétablit la TM mais génère de nouvelles erreurs → invoquer CTG-021 si l'OBC se réinitialise

**Arbre de décision :**

- SI bus A en défaut ET bus B nominal → basculer sur le bus B
- SI les deux bus sont en défaut → passer à EMG-001
- SI le basculement réussit mais que le sous-système reste silencieux → ce sous-système n'est raccordé, sans redondance, qu'au bus défaillant

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | OBDH : identifier le bus défaillant et le bus actif | (lire SID 4) | □ | 0x030F / 0x0310 = 1 (ERROR) ; `obdh.active_bus` 0x030E |
| 2 | OBDH : informer le FD avec la liste des sous-systèmes concernés | (point de situation) | □ | Donnée d'entrée de la décision |
| 3 | OBDH : commander le basculement sur le bus redondant (double validation) | `OBC_SELECT_BUS(bus=0\|1)` (S8 func_id 54) | □ | Deuxième validation par le FD |
| 4 | OBDH : vérifier que la HK de tous les sous-systèmes est désormais transmise | (lire les SID 1, 2, 3, 5, 6) | □ | Les cinq rétablis |
| 5 | OBDH : consigner que l'exploitation se poursuit sur un bus non redondé | (journal de mission) | □ | « CTG-022 closed, on Bus X single-string » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-023 — Délestage progressif</div>

**Point d'entrée :** SoC de la batterie en baisse pendant une éclipse prolongée ; bilan de puissance négatif.

**Objectif :** délester les charges par ordre de priorité à des seuils de SoC définis ; rétablir dans l'ordre inverse dès que la recharge commence. Contrairement à CTG-001 (déclenchée par la tension), cette fiche est déclenchée par le SoC et ajoute un GO explicite du FD à chaque échelon.

**Issues défavorables possibles / écarts :**

- SoC toujours en baisse après chaque échelon → `OBC_SET_MODE(mode=2)` EMERGENCY, puis EMG-002 Perte totale d'alimentation
- SoC inférieur à 10 % → risque de décharge profonde ; EMERGENCY immédiatement, informer le responsable de mission de la perte de capacité probable
- Rétablissement en sortie d'éclipse plus lent que prévu → maintenir le niveau de délestage pendant une orbite ; réévaluer
- Puissance toujours pas rétablie après la sortie d'éclipse → vérifier les courants par panneau 0x012B–0x0130 ; s'ils sont tous proches de zéro, CTG-009

**Arbre de décision (les seuils livrés) :**

- SI SoC < 50 % → échelon 1, charge utile OFF
- SI SoC < 35 % → échelon 2, refroidisseur FPA OFF
- SI SoC < 25 % → échelon 3, PA bande S OFF (liaison descendante perdue ; la liaison montante et la balise UHF subsistent)
- SI SoC < 15 % → échelon 4, ligne des roues de réaction OFF (contrôle d'attitude actif perdu)
- SI la tension du bus reste inférieure à 25.0 V alors que tout est délesté → `OBC_SET_MODE(mode=2)`, puis EMG-002

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : consigner le SoC, la tension bus, la charge, et calculer le taux de décharge | `HK_REQUEST(sid=1)` (S3.27) | □ | Référence ; `eps.eclipse_flag` (0x0108) = 1 |
| 2 | FD : autoriser l'échelon 1 | (GO du FD) | □ | Double validation |
| 3 | EPS : échelon 1 à SoC < 50 % — charge utile OFF | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | −45 W en prise de vue / −8 W en attente |
| 4 | EPS : échelon 2 à SoC < 35 % — refroidisseur FPA OFF | `FPA_COOLER(on=0)` (S8 func_id 43) | □ | ≈ −15 W ; le FPA va se réchauffer |
| 5 | EPS : échelon 3 à SoC < 25 % — PA bande S OFF | `TTC_PA_OFF` (S8 func_id 67) | □ | ≈ −20 W ; la vérification repose désormais sur la balise et les acquittements S1 |
| 6 | EPS : échelon 4 à SoC < 15 % — ligne des roues OFF, amortissement sur magnétocoupleurs | `EPS_POWER_OFF(line_index=7)` (20) ; `AOCS_SET_MODE(mode=2)` (0) | □ | Le mode 2 est DETUMBLE ; le mode 1 (SAFE_BOOT) n'actionne rien |
| 7 | EPS : après la sortie d'éclipse, rétablir dans l'ordre inverse aux seuils de SoC croissants | roues + `AOCS_SET_MODE(mode=3)` > 25 % → `TTC_PA_ON` > 35 % → `FPA_COOLER(on=1)` > 45 % → `PAYLOAD_SET_MODE(mode=1)` > 60 % | □ | 5 min entre les étapes |
| 8 | SPACON : ouvrir une fiche ; documenter le délai de rétablissement | (journal de mission) | □ | « CTG-023 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] CTG-024 — Traitement de la perte d'un panneau solaire</div>

**Point d'entrée :** courant d'un panneau du générateur solaire tendant vers zéro ou nettement dégradé ; `eps.power_gen` total réduit. **Cinq faces de la structure portent des cellules, et non six :** −Z, la face nadir, accueille l'ouverture de l'imageur et le radiateur (`mz_area_m2: 0.000`) ; `eps.sa_mz_current` (0x0130) indique donc zéro en permanence et ne constitue jamais l'indice d'une panne de panneau. Les surfaces des panneaux sont de 0,060 m² pour +X/−X, 0,030 m² pour +Y/−Y, 0,018 m² pour +Z, plus 0,120 m² de cellules par aile déployable.

**Objectif :** identifier le panneau défaillant, recalculer le bilan de puissance pour la nouvelle configuration, décider si la mission se poursuit avec un cycle d'utilisation réduit ou passe dans un état sûr prolongé.

**Issues défavorables possibles / écarts :**

- Deux panneaux perdus ou plus → bilan de puissance probablement négatif même en phase éclairée ; invoquer CTG-023 par anticipation
- La « perte » du panneau est en réalité une ombre due à l'attitude → aucune correction nécessaire ; vérifier avec l'attitude
- Une perte asymétrique crée un couple perturbateur → le pointage SCAO peut se dégrader

**Arbre de décision :**

- SI un panneau est perdu et que l'attitude est nominale → réduire le cycle d'utilisation, continuer sous surveillance
- SI deux panneaux sont perdus sur le même axe → rester en COARSE_SUN (mode 3) jusqu'à l'analyse au sol
- SI la « perte » du panneau disparaît lorsque l'attitude change → pas de véritable panne, consigner et continuer

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | EPS : confirmer le déficit de production en plein soleil | `HK_REQUEST(sid=1)` (S3.27) | □ | `eps.power_gen` 0x0107 ; `eps.eclipse_flag` (0x0108) = 0 |
| 2 | EPS : lire les six courants par panneau, trois échantillons espacés de 30 s | (lire SID 1, paramètres 0x012B–0x0130) | □ | +X, −X, +Y, −Y, +Z, −Z ; les faces à l'ombre indiquent légitimement ~0 A, et **−Z (0x0130) indique toujours zéro — elle ne porte aucune cellule**. Les ailes déployables sont distinctes : 0x0146 (+Y) / 0x0147 (−Y) |
| 3 | AOCS : confirmer que l'attitude est nominale (écarter l'hypothèse d'une ombre) | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.att_error` (0x0217) < 2° ; vitesses < 0.1 °/s |
| 4 | EPS : recalculer le bilan moyenné sur l'orbite avec N−1 panneaux | (calcul opérateur) | □ | Projeter le SoC minimal à la prochaine sortie d'éclipse |
| 5 | EPS : si la projection est inférieure à 25 %, délester en conséquence | `PAYLOAD_SET_MODE(mode=1)` puis `(mode=0)` ; `FPA_COOLER(on=0)` | □ | Recalculer après chaque étape |
| 6 | FD : informer le responsable de mission du profil de mission dégradé | (point de situation) | □ | Notification au client |
| 7 | EPS : si le bilan reste négatif, passer la main à CTG-023 | (décision) | □ | Ou continuer avec un cycle d'utilisation réduit |
| 8 | SPACON : ouvrir une fiche ; marquer le panneau PERMANENT_FAULT dans le journal de mission | (journal de mission) | □ | « CTG-024 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-025 — Reprise après perte de capteur SCAO</div>

**Point d'entrée :** un senseur stellaire, une tête CSS ou un magnétomètre signale FAULT ou échoue à son contrôle de validité ; `aocs.att_error` (0x0217) augmente.

**Objectif :** identifier le capteur défaillant, basculer sur l'unité redondante lorsqu'elle existe (senseurs stellaires uniquement), évaluer si les capteurs restants permettent encore de satisfaire l'exigence de pointage de la mission, et dégrader le mode dans le cas contraire.

**Inventaire des redondances :** deux senseurs stellaires (ST1/ST2), six têtes CSS (+X, −X, +Y, −Y, +Z, −Z), **un magnétomètre sans rechange** et **trois gyros mono-axe sans rechange**. Le magnétomètre et les voies de gyro sont les capteurs SCAO sans unité redondante à sélectionner ; voir CTG-029 pour les gyros.

**Issues défavorables possibles / écarts :**

- La perte cumulée de capteurs fait passer la connaissance d'attitude sous l'exigence de la mission → repli sur COARSE_SUN (mode 3)
- Axe de visée du senseur stellaire masqué par le Soleil → statut 3 (BLIND) ; pas de panne, géométrie attendue, attendre la sortie de la zone d'exclusion solaire
- Perte d'une tête CSS → vecteur Soleil composite dégradé à environ 5–10° mais utilisable ; deux sur des faces opposées → cet axe est perdu ; trois ou plus → vérifier `aocs.css_valid` (0x0248)
- Perte du magnétomètre (non rétabli par un redémarrage) → DETUMBLE et la désaturation par magnétocoupleurs sont tous deux impossibles ; le moment cinétique va s'accumuler

**Arbre de décision :**

- SI ST1 en défaut → mettre ST2 sous tension et le sélectionner (`ST2_POWER(on=1)`, puis `ST_SELECT(unit=2)`)
- SI les deux ST sont en défaut → repli sur COARSE_SUN (mode 3) ; prises de vue suspendues
- SI magnétomètre en défaut → redémarrer l'unité unique (`S2_AOCS_MAGNETOMETER`, équipement 0x0209) ; il n'existe pas de second magnétomètre vers lequel basculer
- SI aucun ST et CSS invalides → DETUMBLE (mode 2)
- SI la perte cumulée dépasse le bilan de pointage → EMG-005

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : lire tous les indicateurs d'état des capteurs | `HK_REQUEST(sid=2)` (S3.27) | □ | 0x0240, 0x0243, `css_valid` 0x0248, `mag_enabled` 0x025C |
| 2 | AOCS : si ST1 est en défaut, mettre ST2 sous tension et le sélectionner | `ST2_POWER(on=1)` (func_id 5) ; `ST_SELECT(unit=2)` (func_id 6) | □ | Prévoir 60 à 120 s entre le démarrage et TRACKING |
| 3 | AOCS : isoler le senseur défaillant | `ST1_POWER(on=0)` (S8 func_id 4) | □ | Ne pas alimenter les deux si `eps.bat_soc` < 40 % |
| 4 | AOCS : si le magnétomètre est en défaut, le redémarrer | `S2_AOCS_MAGNETOMETER(device_id=521, state=0)`, attendre 10 s, puis `(state=1)` (S2.1, équipement 0x0209) | □ | `aocs.mag_enabled` (0x025C) = 1 et `aocs.mag_field_total` (0x0277) revenu dans 25 000–65 000 nT ; sinon, déclarer la configuration sans magnétomètre et escalader — il n'y a pas de `MAG_SELECT` |
| 5 | AOCS : évaluer la connaissance cumulée au regard de l'exigence de pointage | (calcul opérateur) | □ | NOMINAL exige un ST en poursuite + gyro + magnétomètre valide |
| 6 | AOCS : sélectionner le meilleur mode disponible | `AOCS_SET_MODE(mode=4\|3\|2)` (S8 func_id 0) | □ | 4 NOMINAL / 3 COARSE_SUN / 2 DETUMBLE |
| 7 | AOCS : en cas de dégradation sous NOMINAL, mettre la charge utile hors tension | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | Prises de vue suspendues |
| 8 | SPACON : informer le FD ; ouvrir une fiche | (journal de mission) | □ | « CTG-025 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-026 — Reprise après blocage d'un actionneur SCAO</div>

**Point d'entrée :** vitesse d'une roue de réaction inchangée malgré la commande de couple ; ou vitesse de roue figée à une valeur constante ; ou température de roue en hausse.

**Objectif :** identifier la roue bloquée, l'isoler de la boucle de contrôle, reconfigurer le contrôle sur trois roues et rétablir une attitude stable.

**Issues défavorables possibles / écarts :**

- Impossible de mettre hors service la roue bloquée → la roue reste dans la pyramide comme un moment cinétique fixe ; le décharger via les trois roues restantes
- Le contrôle sur trois roues ne permet pas de tenir le bilan de pointage → repli sur COARSE_SUN (mode 3)
- Le moment cinétique cumulé dépasse la capacité → désaturer ; si le magnétomètre est également invalide, le déchargement par magnétocoupleurs est impossible et le moment cinétique va s'accumuler jusqu'à saturation

**Arbre de décision :**

- SI une roue est bloquée ET trois sont opérationnelles → reconfigurer sur trois roues ; FINE_POINT fonctionne toujours, en mode dégradé (`aocs.fine_degraded`, 0x0299), avec un bilan assoupli à 1.5°
- SI deux roues sont bloquées → DETUMBLE (mode 2) ; deux roues ne permettent pas un pointage trois axes
- SI la température de la roue désactivée continue de monter au-delà de 70 °C → délester la ligne d'alimentation des roues, `EPS_POWER_OFF(line_index=7)` — attention, cela met hors tension **toutes** les roues

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : identifier la roue bloquée à partir de deux échantillons de vitesse espacés de 30 s | `HK_REQUEST(sid=2)` (S3.27) | □ | Vitesses 0x0207–0x020A figées ou à 0 tr/min |
| 2 | AOCS : vérifier la tendance de la température de la roue | (lire SID 2) | □ | Températures 0x0218–0x021B ; hausse = grippage du palier |
| 3 | AOCS : désactiver la roue bloquée (double validation) | `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8 func_id 2) | □ | Deuxième validation par le FD ; vitesses angulaires < 1.0 °/s |
| 4 | AOCS : confirmer que la boucle s'est reconfigurée sur trois roues — aucune commande | (observation, 15 s) | □ | Il n'existe ni télécommande `AOCS_3W_MODE` (la fonction S8 5 est `ST2_POWER`) ni paramètre `aocs.wheel_config` : `AOCS_DISABLE_WHEEL` à l'étape 3 constitue toute la reconfiguration. Rétablir plus tard avec `AOCS_ENABLE_WHEEL` (func_id 3) |
| 5 | AOCS : décharger le moment cinétique sur les trois roues restantes | `AOCS_DESATURATE` (S8 func_id 1) | □ | Rapports cycliques MTQ 0x0258–0x025A non nuls pendant le déchargement |
| 6 | AOCS : vérifier la stabilité de l'attitude dans la nouvelle configuration | `AOCS_SET_MODE(mode=4)` (S8 func_id 0) | □ | `aocs.att_error` (0x0217) < 1.5° — assoupli par rapport à 1.0° pour l'exploitation sur trois roues |
| 7 | SPACON : ouvrir une fiche ; marquer la roue PERMANENT_FAULT | (journal de mission) | □ | « CTG-026 closed » ; une désaturation est désormais nécessaire toutes les 3 à 4 orbites, et non toutes les 6 à 8 |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-027 — Synchronisation temporelle GPS et reprise SCAO</div>

**Point d'entrée :** saut de temps > 5 s détecté ; le SCAO est passé automatiquement en SAFE_BOOT (mode 1) par mesure de protection.

**Objectif :** vérifier le point GPS 3D, effectuer la synchronisation temporelle, puis remonter l'échelle des modes SCAO pour rétablir le mode opérationnel antérieur.

**Issues défavorables possibles / écarts :**

- Pas de point GPS 3D → synchronisation temporelle impossible ; attendre un point et réessayer
- La synchronisation temporelle réussit mais le SCAO ne sort pas de SAFE_BOOT → invoquer CTG-002 Reprise après anomalie SCAO
- PDOP > 5 → qualité du point marginale ; reporter la synchronisation temporelle

**Arbre de décision :**

- SI `aocs.gps_fix` = 3 ET `aocs.gps_pdop` < 5.0 ET ≥ 5 satellites → commander la synchronisation temporelle, puis l'échelle des modes
- SI le point est invalide → rester en SAFE_BOOT ; attendre une orbite ; réessayer
- SI la synchronisation temporelle échoue après une nouvelle tentative → invoquer CTG-021 Reprise par le chargeur d'amorçage de l'OBC (le sous-système d'horloge peut être en cause)

**Remarque :** les paramètres GPS appartiennent à l'**AOCS (SID 2)**, et non à l'OBDH. Il n'existe pas d'espace de noms `gps.*` dans `parameters.yaml`, et l'indicateur de qualité est le PDOP, et non le HDOP. L'horloge de bord elle-même se lit dans `obdh.obc_time` (0x0309) complété par `obdh.obc_time_fine` (0x0A12) dans SID 4, avec `obdh.time_ref` (0x0A13) à côté.

**Un réglage par le sol et une synchronisation GPS sont deux opérations différentes.** `SET_TIME` (S9.1) laisse `time_ref` = 1 (GROUND), et l'horloge continue de dériver à sa valeur tirée d'environ 12 ppm. `OBC_GPS_TIME_SYNC` verrouille le mode **asservi** : `time_ref` = 2 (GPS) et, tant que le point est maintenu, l'horloge est ramenée sur le temps vrai à chaque pas et n'accumule aucune dérive. La perte du point la fait passer à 3 (**HOLDOVER**) et émet `OBC_TIME_REF_LOST` (0x030E) — l'horloge n'est pas encore fausse, elle a simplement cessé d'être corrigée, et la dérive reprend à partir de sa valeur courante. Le retour du point rétablit l'asservissement de manière autonome et émet `OBC_TIME_SYNC` (0x030D), qui porte le saut. Aucune de ces deux commandes n'est disponible dans le chargeur d'amorçage.

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : confirmer le point GPS et sa qualité | `HK_REQUEST(sid=2)` (S3.27) | □ | `aocs.gps_fix` (0x0274) = 3, `gps_pdop` (0x0275) < 5.0, `gps_num_sats` (0x0276) ≥ 5. La condition propre à la commande est seulement `gps_fix` ≥ 2 ; un point 3D + vitesse est la préférence opérationnelle de cette fiche |
| 2 | AOCS : consigner le mode antérieur à l'événement, l'état de la référence et le décalage d'horloge | (lire les SID 2 et 4) | □ | `aocs.mode` 0x020F ; `obdh.time_ref` (0x0A13) — s'attendre à 3 (HOLDOVER) si le point vient d'être perdu, ou à 1 (GROUND) si l'horloge n'a jamais été asservie ; `obdh.obc_time` 0x0309 comparé à l'UTC sol |
| 3 | OBDH : commander la synchronisation temporelle GPS (attention — invalide brièvement la solution d'attitude du SCAO) | `OBC_GPS_TIME_SYNC` (S8 func_id 80) | □ | 0x0309 passe à la valeur issue du GPS en moins de 5 s ; `obdh.time_ref` (0x0A13) → 2 (GPS) ; `obdh.time_since_sync_s` (0x0A14) repart de zéro ; l'événement `OBC_TIME_SYNC` (0x030D) porte le saut |
| 4 | AOCS : vérifier que le SCAO est en SAFE_BOOT (mode 1) après la synchronisation | (lire SID 2) | □ | Transition automatique (événement 0x020F, que le catalogue des événements nomme actuellement `AOCS_MODE_RESTORED`) sur un saut > 5 s, car la solution d'attitude a été calculée avec une horloge qui vient de changer ; s'y attendre après un long maintien (holdover) ou un redémarrage. Si le mode est inchangé, l'étape 5 est sans objet |
| 5 | AOCS : remonter l'échelle — DETUMBLE → COARSE_SUN → NOMINAL → FINE_POINT | `AOCS_SET_MODE(mode=2)`, puis 3, 4, 5 (double validation) | □ | 30 s entre chaque ; vérifier que 0x020F est égal à chaque valeur commandée |
| 6 | AOCS : confirmer la convergence de l'attitude dans le mode visé | (lire SID 2) | □ | COARSE_SUN < 10°, NOMINAL < 5°, FINE_POINT < 1° |
| 7 | SPACON : ouvrir une fiche ; consigner la correction de l'écart de temps | (journal de mission) | □ | « CTG-027 closed, Δt = X s » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[PR] CTG-028 — Anomalie de propulsion</div>

*(Note de la rédaction : il s'agit de la **CTG-028 Anomalie de propulsion** du simulateur, `contingency/propulsion_anomaly.md`, sous forme condensée.)*

**Point d'entrée :** alarme S12 sur `prop.tank_pressure` (0x0B01) — plage absolue, ou surveillance de vitesse de variation/DELTA qui détecte une fuite lente ; ou événement PROP_VALVE_FAULT (0x080A), PROP_LEAK_DETECTED (0x080B), PROP_UNDERPERFORMANCE (0x080C), PROP_TANK_PRESSURE_HIGH (0x0807) ; ou restitution d'orbite (OD) après poussée montrant un ΔV obtenu inférieur à 90 % du plan (NOM-013, étape 6).

**Objectif :** isoler l'ergol, **borner** le ΔV utilisable restant et protéger la réserve d'évitement de collision. Le monoergol vert 1U d'EOSAT-1 (66,9 m/s au total) sert à l'évitement de débris, à un maintien d'orbite limité et à la poussée de retrait de service de 34,3 m/s en fin de vie (NOM-014) ; l'objectif n'est donc pas de « réparer le propulseur », mais de « savoir exactement quelle capacité de CAM subsiste et la préserver ».

**Issues défavorables possibles / écarts :**

- Une branche signalant 2 (défaut) ne s'est pas fermée — considérer comme perdu l'ergol situé en aval de la vanne bloquée
- Pression toujours en baisse après isolement → la fuite se situe en amont des vannes à verrouillage ; elle ne peut pas être isolée, seulement bornée
- Réserve bornée inférieure à ~1 m/s → la capacité d'évitement de débris est de fait perdue ; la posture vis-à-vis des conjonctions change
- Pression réservoir en hausse, insensible à la mise en sécurité des réchauffeurs → CTG-004, et préparer EMG-001 (le mode survie désarme la propulsion par la règle 8005)

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Propulsion : activer la structure PROP et capturer la TM complète | `HK_ENABLE(sid=9)` (S3.5) | □ | SID 9 correspond à PROP ; SID 5 à la charge utile |
| 2 | Propulsion : lire l'état, la tendance de pression, la masse, les températures, les vannes, le débit de fuite | (lire SID 9) | □ | 0x0B00, 0x0B01, 0x0B02, 0x0B04/0x0B05, 0x0B06–0x0B08, 0x0B16 |
| 3 | Propulsion : fermer les deux branches de vannes à verrouillage | `PROP_ISO_CLOSE(branch=2)` (S8 func_id 114) | □ | `prop.latch_a_state` 0x0B06 et `latch_b_state` 0x0B07 = 0 |
| 4 | Propulsion : borner le ΔV utilisable restant | lire `prop.dv_remaining` (0x0B0C), corriger selon le mode de défaillance | □ | Communiquer au FD la réserve CAM bornée |
| 5 | Propulsion : verrouiller l'inhibition sol tant que l'anomalie est ouverte | `PROP_INHIBIT_SET(on=1)` (S8 func_id 116) | □ | `prop.arm_inhibit_mask` (0x0B15) bit 9 positionné |
| 6 | SPACON : ouvrir une fiche ; le FD décide d'EMG-001 en cas de cascade | (journal de mission) | □ | La levée de l'inhibition (`PROP_INHIBIT_CLR`, func 117) exige une fiche close + l'autorité du FD |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] CTG-029 — Reprise après panne de gyroscope</div>

*(Fiche du simulateur `contingency/gyro_failure.md`. Elle remplace la fiche provisoire CTG-B01 « Anomalie IMU / gyro » du livre.)*

**Point d'entrée :** événement `GYRO_BIAS_HIGH` (0x020B) — le biais encore présent à la sortie du gyroscope dépasse 0,05 °/s (`aocs.gyro_bias_resid` 0x02D2) ; ou `aocs.gyro_units_mask` (0x02D1) ≠ 7, une unité est éteinte ; ou `aocs.gyro_saturated` (0x0295) = 1 ; ou l'estimation d'attitude qui dérive (`aocs.att_error` 0x0217 en hausse) alors que le senseur stellaire est hors de la boucle. Liaison établie avec ≥ 15 min de passage restantes, image applicative en service, SoC > 40 %, ni basculement, ni désaturation, ni poussée dans les 15 min.

**Objectif :** identifier la voie gyroscopique touchée, rétablir une référence de vitesse sans biais grâce à l'étalonnage bord du biais et, si la voie est irrécupérable, l'isoler et poursuivre la détermination d'attitude sur les capteurs restants.

**Ce que modélise le simulateur.** EOSAT-1 emporte trois gyroscopes mono-axe, un par axe du satellite, et **aucune unité redondante** : équipements S2 `S2_AOCS_GYROSCOPE_0/1/2` (identifiants 0x0206, 0x0207, 0x0208 = 518, 519, 520). Il n'y a ni ligne d'alimentation IMU ni unité vers laquelle basculer. Une panne `gyro_bias` injectée est un décalage **persistant** sur un axe ou sur les trois ; elle ne disparaît pas avec le temps, et l'étalonnage la compense dans la chaîne de mesure sans réparer l'unité. Une unité éteinte est une voie morte. Les trois valeurs de biais sont des grandeurs différentes : l'instabilité de biais d'une unité saine est d'environ 3e-5 °/s (0,1 °/h), l'événement 0x020B se déclenche à **0,05 °/s** de biais résiduel, et la limite S12 sur `aocs.gyro_bias_x/y/z` (0x0270–0x0272) est de ±0,5 °/s. Cette fiche agit sur l'événement à 0,05 °/s, le premier signal exploitable.

**Issues défavorables possibles / écarts :**

- Les trois unités éteintes ou en panne → aucune référence de vitesse ; le filtre se contente du senseur stellaire, des capteurs solaires et du magnétomètre. Tenir NOMINAL si le senseur est valide, sinon EMG-005 Perte d'attitude
- Saturation (`aocs.gyro_saturated` = 1) → le satellite tourne plus vite que la plage du gyroscope : c'est une anomalie d'attitude, pas une panne de gyroscope ; CTG-002 d'abord
- Refus avec `0x0A03` → aucun senseur stellaire dans la boucle ; le rétablir (CTG-008), attendre le bit 0 de `aocs.est_source` (0x02C1), réessayer. Refus avec `0x0A04` → satellite non au repos ; attendre la fin du basculement ou de la désaturation (`aocs.mode` ≠ 6 et ≠ 7)
- Le biais revient après un bon étalonnage → s'il suit `aocs.gyro_temp` (0x0273), relancer après le transitoire thermique ; à température constante, l'unité se dégrade — émettre un rapport d'anomalie
- L'instructeur retire un biais injecté après un étalonnage → la compensation mémorisée surcorrige désormais avec le signe opposé ; relancer l'étape 4

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | AOCS : recueillir la télémesure des gyroscopes et de détermination ; classer | `HK_REQUEST(sid=2)`, `HK_REQUEST(sid=7)` (S3.27) | □ | Consigner `aocs.gyro_units_on` (0x0294), `aocs.gyro_units_mask` (0x02D1), `aocs.gyro_saturated` (0x0295), `aocs.gyro_bias_x/y/z` (0x0270–0x0272), `aocs.gyro_bias_resid` (0x02D2), `aocs.gyro_temp` (0x0273). L'axe dont le biais se distingue est la voie touchée |
| 2 | AOCS : protéger l'estimation d'attitude | (lecture des SID 2 / SID 7) | □ | Bit 0 de `aocs.est_source` (0x02C1) positionné ; `aocs.st1_status` (0x0240) = 2 ; `aocs.att_error` (0x0217) < 1,0°. Sans senseur dans la boucle, un biais de 0,05 °/s fait dériver l'estimation de plusieurs dizaines de degrés en dix minutes : rétablir d'abord le senseur (CTG-008) |
| 3 | AOCS : rallumer toute unité éteinte (seulement si 0x02D1 ≠ 7) | `S2_AOCS_GYROSCOPE_0(device_id=518, state=1)`, `S2_AOCS_GYROSCOPE_1(device_id=519, state=1)`, `S2_AOCS_GYROSCOPE_2(device_id=520, state=1)` (S2.1) | □ | Idempotent. `aocs.gyro_units_mask` = 7 et `aocs.gyro_units_on` = 3 en 20 s ; un étalonnage avec une voie morte est refusé avec `0x0A02` |
| 4 | AOCS : lancer l'étalonnage bord du biais | `AOCS_GYRO_CALIBRATION(action=0, duration_s=300)` (S8 func_id 13) | □ | Tenir NOMINAL (mode 4, ou 8 en éclipse), vitesses à 0,10 °/s près. `aocs.gyro_cal_state` (0x02C9) = 1 en 20 s ; codes de refus `0x0A01`–`0x0A05` dans `aocs.gyro_cal_reject` (0x02D0) ; le S1.7 arrive à la fin de l'arc |
| 5 | AOCS : suivre l'arc d'étalonnage | `HK_REQUEST(sid=7)` (S3.27) toutes les 30 s | □ | `aocs.gyro_cal_progress` (0x02CA) ≥ 100 en 330 s. Un abandon (`AOCS_GYRO_CAL_ABORT`, 0x0212) n'applique rien : corriger la cause et relancer l'étape 4 |
| 6 | AOCS : vérifier le résultat et consigner le biais | `GET_PARAM(param_id=0x02CB)` … `(param_id=0x02CD)` (S20.3) | □ | `aocs.gyro_cal_state` = 2, `aocs.gyro_cal_result` (0x02CF) = 1 ; chaque axe à ±0,5 °/s. Au-delà, ne pas accepter le résultat : étape 7 |
| 7 | AOCS : isoler une voie irrécupérable (seulement si l'étape 6 a échoué) | `S2_AOCS_GYROSCOPE_0(device_id=518, state=0)` (X représenté ; 519 Y, 520 Z) ; `AOCS_EST_RESET(mode=1)` (S8 func_id 91) | □ | Seulement pour un biais supérieur à 0,5 °/s après un étalonnage de 900 s, ou deux abandons de suite avec `0x0A06`. Le bit fautif s'efface dans 0x02D1 ; bit 0 de `aocs.est_source` toujours positionné en 60 s. Cet axe ne dépend plus que du senseur stellaire jusqu'à la fin de la mission |
| 8 | AOCS : confirmer la reprise ; déposer le rapport d'anomalie | `HK_REQUEST(sid=2)`, `HK_REQUEST(sid=7)` (S3.27) | □ | `aocs.gyro_bias_resid` (0x02D2) < 0,005 °/s ; `aocs.gyro_cal_comp_mag` (0x02CE) consigné ; `aocs.knowledge_err_3sig` (0x02A7) < 120 arcsec et `aocs.control_err` (0x02A8) < 1,0° en 300 s. Si une voie a été isolée, vérifier `aocs.fine_ready` (0x02C5) avant la prochaine séance de prise de vue. « CTG-029 closed » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-contingency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] CTG-030 — Rejet de télécommande et échec de vérification</div>

*(Fiche du simulateur `contingency/tc_rejection.md`. Elle remplace la fiche provisoire CTG-B02 « Anomalie du taux de rejet des TC » du livre.)*

**Point d'entrée :** un échec d'acceptation S1.2 ou un échec d'exécution S1.8 sur une télécommande que le sol croit valide ; `obdh.tc_rej_count` (0x0306) qui augmente, ou l'événement `COMMAND_REJECTED` (0x030B) ; ou une télécommande sans **aucun** rapport S1 (délai de vérification dépassé dans le journal des commandes du MCS). Liaison attendue (dans un passage prédit) ; journal des commandes du MCS disponible.

**Objectif :** trouver pourquoi des télécommandes sont refusées ou non vérifiées, supprimer la cause et rétablir une commande propre. La fiche n'envoie que des demandes de HK et un essai de connexion.

**Ce que rapporte le simulateur.** Chaque refus porte un code d'échec sur 16 bits et un texte de motif. Le code est mémorisé dans `obdh.last_tc_error_code` (0x0315), et un refus à bord déclenche aussi `COMMAND_REJECTED` (0x030B), qui nomme la commande, l'étape et le code. À l'**acceptation** (S1.2) : 0x0001 service inconnu, 0x0002 sous-type inconnu, 0x0003 paramètre ou longueur invalide, 0x0004 sous-système cible non alimenté, 0x0005 liaison montante indisponible, 0x0006 hors du sous-ensemble du chargeur d'amorçage. À l'**exécution** (S1.8) : 0x0005 invalide dans le mode courant, 0x0007 non permise dans l'état courant, et les familles 0x0021–0x0028 charge utile, 0x0A01–0x0A08 étalonnage des gyroscopes, 0x0A20–0x0A22 entrée dans un mode AOCS, 0x0B01–0x0B13 propulsion, 0x0C01–0x0C04 phase de mission. Deux cas ne sont **pas** des rejets : 0x0005 à l'acceptation sans événement `COMMAND_REJECTED` (la liaison montante n'avait pas de verrouillage du canal de commande, le logiciel de bord n'a donc jamais vu la TC), et l'absence de tout rapport S1 (la TC n'est jamais arrivée, ou c'est une commande à achèvement différé — étalonnage des gyroscopes, amorçage de l'application, poussée — dont le S1.7 arrive à la fin de l'action). Déterminer lequel avant de renvoyer quoi que ce soit.

**Issues défavorables possibles / écarts :**

- La demande de l'étape 1 reste elle-même sans réponse → un problème de liaison, pas de commande : CTG-003 Reprise après perte de liaison TTC, ou CTG-019 s'il n'y a aucune télémesure
- `CONNECTION_TEST` reste sans réponse → la liaison montante ne fonctionne pas ; CTG-003
- Les rejets continuent avec un code que personne n'explique → arrêter de commander, consigner le code, le texte de motif et la commande, escalader au FD ; ne pas essayer d'autres commandes pour le contourner
- Rejets après un redémarrage de l'OBC → l'OBC redémarre dans le chargeur d'amorçage (`obdh.sw_image` 0x0311 = 0) : toute commande applicative est refusée `0x0006` jusqu'au réamorçage de l'application (EMG-003, CTG-021)
- Échecs liés à l'horloge → une commande horodatée calée sur une horloge de bord fausse s'exécute au mauvais moment au lieu d'être rejetée ; si `obdh.time_ref` (0x0A13) = 0 ou si `obdh.time_since_sync_s` (0x0A14) est grand, resynchroniser (NOM-008) avant de charger un nouveau programme

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FDIR / systèmes : lire les compteurs de commandes et l'état de bord | `HK_REQUEST(sid=4)` (S3.27) | □ | Consigner `obdh.tc_rx_count` (0x0304), `obdh.tc_acc_count` (0x0305), `obdh.tc_rej_count` (0x0306), `obdh.last_tc_error_code` (0x0315), `obdh.sw_image` (0x0311 : 0 chargeur d'amorçage, 1 application), `obdh.mode` (0x0300 : 0 nominal, 1 sécurité, 2 urgence), `eps.spacecraft_phase` (0x0129) |
| 2 | TT&C : vérifier la chaîne montante | `HK_REQUEST(sid=6)` (S3.27) | □ | `ttc.carrier_lock` (0x0510) = 1 ; `ttc.frame_sync` (0x0512) = 1 ; consigner `ttc.cmd_rx_count` (0x0513) et `ttc.beacon_mode` (0x0521). Ni rapport S1 ni variation de 0x0513 → la TC n'a jamais atteint le satellite |
| 3 | FDIR / systèmes : classer chaque rejet par code et par étape | (journal des commandes du MCS ; texte de l'événement 0x030B) | □ | 0x0006 avec `sw_image` = 0 → amorcer l'application (étape 5 de LEOP-001, CTG-021). 0x0004 → mettre d'abord la ligne sous tension. 0x0003 → reconstruire la TC dans le constructeur de commandes. 0x0001 / 0x0002 → non implémenté. 0x0005 / 0x0007 à l'exécution → valide mais pas permise maintenant (par exemple le mode balise : le quitter avec `TTC_SET_BEACON_MODE`). 0x0Axx → CTG-029 ; 0x0Bxx → lire `prop.arm_inhibit_mask` (0x0B15), NOM-013 ou CTG-028 ; 0x0Cxx → conditions de phase de mission |
| 4 | TT&C : vérifier une commande propre | `CONNECTION_TEST` (S17.1) ; `HK_REQUEST(sid=4)` (S3.27) | □ | S1.1 et S1.7 en 10 s ; `obdh.tc_acc_count` incrémenté, `obdh.tc_rej_count` inchangé |
| 5 | FD : renvoyer une seule fois la télécommande corrigée | (la TC corrigée) | □ | Seulement après suppression de sa cause ; ne jamais répéter à l'identique une TC refusée. S1.1 et S1.7 reçus ; `obdh.last_tc_error_code` inchangé. « CTG-030 closed » |

</div>

<div style="page-break-before: always"></div>

## 14.5 Fiches de procédures d'urgence

*Les procédures d'urgence doivent être lues une fois lors de la familiarisation des opérateurs, mais jamais invoquées sans autorisation explicite du FD. Toute approche d'un passage en mode survie commence par une annonce au FD sur la boucle vocale. Les fiches ci-dessous en donnent la structure canonique ; les fichiers de procédure du simulateur contiennent les listes d'étapes complètes.*

*Chaque fiche ci-dessous porte l'identifiant EMG du simulateur et correspond au fichier du même identifiant dans `configs/eosat1/procedures/emergency/`. La numérotation des tirages antérieurs figure dans la note historique à la fin du §14.6.*

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[FD] EMG-001 — Mode survie d'urgence</div>

**Point d'entrée :** au moins deux des conditions suivantes — `eps.bat_soc` (0x0101) < 15 % ; `aocs.att_error` (0x0217) > 30° ; une vitesse angulaire > 2 °/s ; `obdh.reboot_count` (0x030A) en hausse de ≥ 2 en une heure ; `tcs.temp_battery` (0x0407) hors de −10 / +45 °C ; `ttc.link_status` (0x0501) ≠ 2 pendant plus d'un passage ; `obdh.mode` (0x0300) déjà = 2 (EMERGENCY). Ou une déclaration d'urgence par le FD.

**Objectif :** placer le satellite dans la configuration durable la plus sûre — OBC en EMERGENCY, pointage solaire COARSE_SUN, charges minimales — et l'y maintenir pendant au moins trois orbites, le temps que l'analyse au sol décide de la voie de rétablissement. Il n'existe pas de « SAFE_POINT » : l'attente sûre au Soleil est COARSE_SUN, mode 3.

**Issues défavorables possibles / écarts :**

- Le passage en mode survie déclenche lui-même d'autres actions FDIR → attendu ; laisser converger la protection autonome
- Satellite en culbutage (vitesses > 2 °/s) → exécuter EMG-005 Perte d'attitude avant de poursuivre
- Bilan de puissance non positif après l'acquisition du Soleil → EMG-002 Perte totale d'alimentation
- La sortie du mode survie exige une analyse hors ligne ; ne pas quitter le mode survie au cours du même passage sans autorisation explicite du FD et du responsable de mission

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FD : déclarer l'urgence sur la boucle vocale | (annonce du FD) | □ | Acquittement de tous les postes |
| 2 | OBDH : commander l'OBC en EMERGENCY | `OBC_SET_MODE(mode=2)` (S8 func_id 50) | □ | `obdh.mode` (0x0300) = 2 en moins de 5 s ; le délestage autonome suit |
| 3 | Charge utile : confirmer le délestage autonome, commander OFF si elle est encore active | `PAYLOAD_SET_MODE(mode=0)` (S8 func_id 26) | □ | `payload.mode` (0x0600) = 0 ; `eps.power_cons` (0x0106) < 50 W |
| 4 | Thermique : réchauffeurs OBC et propulseur OFF | `HEATER_OBC(on=0)` (41) ; `HEATER_THRUSTER(on=0)` (42) | □ | Le réchauffeur batterie reste sous contrôle du thermostat |
| 5 | AOCS : commander l'attente sûre au Soleil | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 3 (COARSE_SUN) ; en cas de culbutage, mode 2 d'abord |
| 6 | EPS : confirmer un bilan de puissance positif à l'acquisition du Soleil | (lire SID 1) | □ | `eps.power_gen` (0x0107) > `power_cons` ; générateurs > 0.5 A |
| 7 | Tous : maintenir et évaluer pendant au moins trois orbites (~4,75 h) | (lire les SID 1 à 6) | □ | Critère de sortie : SoC > 25 %, aucune nouvelle anomalie |
| 8 | FD : informer le responsable de mission ; arrêter toute activité non indispensable à la survie | (point de situation) | □ | « EMG-001 active » ; rétablissement par paliers R+1 à R+5 sur les seuils de SoC 30/40/50/55/60 % |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[FE] EMG-002 — Perte totale d'alimentation</div>

**Point d'entrée :** `eps.bat_soc` (0x0101) < 10 % **ou** `eps.bus_voltage` (0x0105) < 26.0 V. La chaîne de sous-tension de l'arbre est la suivante : seuil de sous-tension FDIR à **26.5 V** (`simulation.yaml` `eps.uv_threshold_v`), délestage automatique dans le modèle à **25.0 V** (`eps.load_shed.bus_voltage_v`, rétablissement à 25.5 V, délestage dans l'ordre payload → fpa_cooler → ttc_tx → aocs_wheels → prop), événement `bus_critical_v` au même seuil de **25.0 V**, et cascade de propagation de défaillance à **23.0 V** — à ce stade, le satellite se met lui-même en sécurité. Il n'existe pas d'échelon à 24.5 V ; l'échelle FDIR fondée sur le SoC est distincte et fonctionne à 30 / 20 / 10 %.

**Objectif :** atteindre la configuration de survie minimale, orienter les générateurs vers le Soleil et attendre la recharge. **Aucune charge ne peut être réactivée avant que le SoC dépasse 30 %**, valeur confirmée sur trois échantillons consécutifs.

**Issues défavorables possibles / écarts :**

- La chute de tension atteint l'OBC → redémarrage autonome probable ; suites CTG-010 / EMG-003
- La batterie ne se rétablit pas même avec toutes les charges délestées → candidat à la perte de mission ; tentative de recharge sur plusieurs orbites
- Vitesses angulaires supérieures à 2 °/s → les générateurs ne peuvent pas être pointés ; exécuter d'abord l'étape 2 d'EMG-005
- Générateurs solaires partiellement ombrés du fait de l'attitude → recouper avec EMG-005

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FD : déclarer l'urgence puissance | (annonce du FD) | □ | |
| 2 | EPS : délestage immédiat, en moins de 60 s | `PAYLOAD_SET_MODE(mode=0)` (26) ; `HEATER_OBC(on=0)` (41) ; `HEATER_THRUSTER(on=0)` (42) | □ | `eps.power_cons` (0x0106) < 50 W en moins de 15 s |
| 3 | Thermique : laisser le réchauffeur batterie sous thermostat, ligne sous tension | `EPS_POWER_ON(line_index=5)` (19) ; `HEATER_BATTERY(on=1)` (40) | □ | `eps.pl_htr_bat` (0x0115) = 1 — le thermostat a besoin de la ligne |
| 4 | OBDH : commander l'OBC en EMERGENCY | `OBC_SET_MODE(mode=2)` (S8 func_id 50) | □ | `obdh.mode` (0x0300) = 2 ; la génération de HK tombe à 1/60 s |
| 5 | AOCS : acquisition du Soleil pour une production maximale | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | COARSE_SUN ; générateurs > 0.3 A chacun |
| 6 | EPS : surveiller le rétablissement pendant la phase éclairée et l'éclipse suivante | (lire SID 1) | □ | Le bus doit rester > 25.0 V pendant l'éclipse ; le rétablissement est lent |
| 7 | EPS : maintenir le seuil de rétablissement jusqu'à SoC > 30 % | (lire SID 1) | □ | Trois échantillons consécutifs ; puis le réchauffeur OBC en premier |
| 8 | FD : informer le responsable de mission ; posture de rétablissement sur plusieurs orbites | (point de situation) | □ | « EMG-002 active » ; viser un gain net de SoC ≥ 3 % par orbite |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[OB] EMG-003 — Redémarrage de l'OBC</div>

**Point d'entrée :** au moins deux indicateurs indépendants — `obdh.cpu_load` (0x0302) durablement au-dessus de 90 % ; `obdh.tc_rej_count` (0x0306) s'incrémentant sur des commandes valides ; `obdh.mem_errors` (0x031E) en hausse ; OBC ne répondant pas aux commandes de mode ; ou données de servitude périmées depuis plus de 30 s.

**Objectif :** forcer un redémarrage commandé propre, puis rétablir l'état minimal de la mission — en ne se repliant sur l'unité redondante que si le redémarrage ne rétablit pas l'OBC.

**Issues défavorables possibles / écarts :**

- Le redémarrage lance le chargeur d'amorçage mais l'application échoue de nouveau → CTG-021 Reprise par le chargeur d'amorçage de l'OBC ; suspecter une corruption logicielle
- Les deux unités OBC sont touchées → le mode survie autonome du satellite finira par se déclencher ; se coordonner avec le constructeur
- Le redémarrage provoque des transitoires d'alimentation → surveiller en parallèle l'EPS pour détecter un déclenchement de CTG-012 / CTG-001

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | FD : déclarer l'urgence ; coordonner l'autorisation en double validation | (annonce du FD) | □ | La séquence de démarrage exige un SoC > 30 % |
| 2 | OBDH : capturer l'état antérieur au redémarrage | `HK_REQUEST(sid=4)` (S3.27) | □ | 0x0300, 0x0302, 0x030A, 0x030B, 0x030C, 0x0311, 0x0316, 0x0319, 0x031E |
| 3 | Charge utile / Thermique : suspendre la charge utile et délester les charges non critiques | `PAYLOAD_SET_MODE(mode=0)` (26) ; `HEATER_OBC(on=0)` (41) | □ | Aucun chargement mémoire ni aucune séquence de commandes datées en cours |
| 4 | OBDH : commander le redémarrage | `OBC_REBOOT` (S8 func_id 52) | □ | La fonction 42 est `HEATER_THRUSTER` — commander 42 ici basculerait le réchauffeur du lit catalytique et laisserait l'OBC en fonctionnement |
| 5 | SPACON : démarrer l'image applicative | `OBC_BOOT_APP` (S8 func_id 55) | □ | `obdh.sw_image` (0x0311) = 1. Le démarrage de l'application ne restaure **pas** l'horloge |
| 6 | OBDH : si l'OBC ne se rétablit pas, basculer d'unité (double validation) | `OBC_SWITCH_UNIT` (S8 func_id 53) | □ | Confirmer que `obdh.active_obc` (0x030C) a changé |
| 7 | SPACON : après le rétablissement, exécuter la remise en ordre complète CTG-010 | selon CTG-010 | □ | Comprend `HK_ENABLE` pour les SID 2 à 6, la sortie du mode balise et une **resynchronisation de l'horloge** : le redémarrage a ramené l'OBC à J2000 avec `obdh.time_ref` (0x0A13) = 0 (NONE) ; ne réarmer donc aucune commande datée tant que `SET_TIME` (S9.1) n'a pas été accepté |
| 8 | FD : informer le responsable de mission | (point de situation) | □ | « EMG-003 closing » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[TT] EMG-004 — Perte de communication</div>

**Point d'entrée :** aucune télémesure pendant au moins deux fenêtres de passage consécutives (~3 h).

**Objectif :** monter en puissance par échelons successifs — segment sol, puis commande en aveugle sur chaque transpondeur, puis évaluation du rétablissement autonome — avec des jalons de décision à 6 h, 12 h, 24 h et 48 h depuis le dernier contact.

**Une bande S silencieuse ne signifie pas un satellite silencieux.** EOSAT-1 embarque deux émetteurs : l'émetteur principal en bande S et une balise UHF distincte à antenne fouet. La coupure du PA interrompt la télémesure en bande S, tandis que la balise continue d'émettre la HK SID 11 depuis la ligne non commutable `ttc_rx`. Recherchez la balise avant de conclure que le satellite est perdu.

**Issues défavorables possibles / écarts :**

- Le rétablissement autonome du satellite le ramène au passage suivant → poursuivre par la remise en ordre post-rétablissement CTG-010
- Silence persistant au-delà de 48 h → déclarer formellement la perte ; coordonner l'écoute radio avec les partenaires industriels
- Rétablissement partiel (porteuse seule, pas de démodulation) → voie CTG-014 + CTG-003

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Segment sol : confirmer chaque station, la configuration bande de base et celle des antennes | (vérification complète des stations) | □ | Réseau de cinq stations ; seuil du récepteur au minimum (−130 dBm) |
| 2 | TT&C : demander la HK en aveugle à chaque passage visible, élévation minimale 5° | `HK_REQUEST(sid=6)` (S3.27) | □ | Prioriser par élévation maximale |
| 3 | TT&C : basculer en aveugle sur le transpondeur principal, 3 fois à 10 s d'intervalle | `TTC_SWITCH_PRIMARY` (S8 func_id 63) | □ | De préférence sur un passage à plus de 20° d'élévation |
| 4 | TT&C : basculer en aveugle sur le transpondeur redondant, 3 fois à 10 s d'intervalle | `TTC_SWITCH_REDUNDANT` (S8 func_id 64) | □ | Toute exécution de fonction S8 utilise le sous-type 1 |
| 5 | TT&C : rechercher la balise UHF à chaque passage prévu | (recherche de porteuse) | □ | Échelon balise, HK SID 11 — indépendant du PA bande S |
| 6 | FD : étendre la recherche à l'écoute radio des partenaires industriels au-delà du jalon de 24 h | (communication externe) | □ | |
| 7 | FD : informer le responsable de mission de la stratégie de communication envers le client | (point de situation) | □ | « EMG-004 active » |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[AOCS] EMG-005 — Perte d'attitude</div>

**Point d'entrée :** l'une des valeurs `aocs.rate_roll` (0x0204), `rate_pitch` (0x0205) ou `rate_yaw` (0x0206) supérieure à 2.0 °/s — le satellite est en culbutage.

**Objectif :** amortir les vitesses angulaires avec les magnétocoupleurs, protéger le bilan de puissance tant que les générateurs ne sont pas orientés vers le Soleil, et réacquérir le Soleil.

**L'amortissement est lent, et c'est normal.** DETUMBLE (mode 2) est une véritable loi B-dot pilotée par le magnétomètre, `m = −k·dB/dt`, dont le dipôle sature à 1,6 A·m² par axe. Depuis une rotation de 14 °/s, la convergence demande de l'ordre de 3.5e3 s, avec un passage sous le seuil de sortie de 0.5 °/s vers 1166 s. Comptez environ une division par deux de la vitesse par orbite ; prévoyez deux orbites, et non deux minutes. Toute affirmation d'un amortissement rapide est fausse.

**Issues défavorables possibles / écarts :**

- Le bilan de puissance se dégrade pendant le rétablissement (générateurs hors Soleil) → CTG-001 / EMG-002 ; sous 10 % de SoC, commander `OBC_SET_MODE(mode=2)`
- Vitesses en hausse au lieu de baisser → suspecter une erreur de modèle magnétique ou de polarité des magnétocoupleurs ; commander le SCAO sur OFF, attendre une orbite, réessayer
- Magnétomètre invalide → la loi B-dot est impossible ; aucune voie d'amortissement tant que le magnétomètre n'est pas rétabli
- Apparition de dépassements thermiques pendant la rotation → CTG-004 / EMG-006

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Charge utile / Thermique : délester immédiatement pour prolonger l'autonomie de la batterie | `PAYLOAD_SET_MODE(mode=0)` (26) ; `HEATER_OBC(on=0)` (41) | □ | `eps.power_cons` (0x0106) < 60 W |
| 2 | AOCS : commander DETUMBLE (magnétocoupleurs uniquement) | `AOCS_SET_MODE(mode=2)` (S8 func_id 0) | □ | `aocs.mode` (0x020F) = 2 ; les roues ne sont pas nécessaires |
| 3 | AOCS : surveiller la réduction des vitesses au cours de l'orbite 1 | `HK_REQUEST(sid=2)` (S3.27) | □ | Tous les axes < 1.0 °/s à la fin de la première orbite |
| 4 | AOCS : surveiller au cours de l'orbite 2 | (lire SID 2) | □ | Tous les axes < 0.5 °/s et SoC > 15 % |
| 5 | AOCS : confirmer la fin de l'amortissement | (lire SID 2) | □ | Toutes les vitesses < 0.1 °/s pendant 10 min sans interruption |
| 6 | AOCS : commander l'acquisition du Soleil | `AOCS_SET_MODE(mode=3)` (S8 func_id 0) | □ | COARSE_SUN ; `aocs.att_error` (0x0217) < 5° en moins de 15 min |
| 7 | EPS : confirmer un bilan de puissance positif, puis maintenir pendant deux orbites | (lire SID 1) | □ | Les deux générateurs > 0.5 A ; SoC en hausse |
| 8 | FD : informer le responsable de mission ; coordonner si nécessaire un rétablissement sur plusieurs orbites | (point de situation) | □ | « EMG-005 active » ; passer la main à EMG-001 pour le rétablissement par paliers |

</div>

<div style="page-break-before: always"></div>

<div class="procedure-card procedure-card-emergency" markdown="1">

<div class="procedure-card-header" markdown="1">[SE] EMG-006 — Emballement thermique</div>

**Point d'entrée :** un circuit de réchauffeur bloqué sur ON, avec une température de zone en hausse incontrôlée malgré les actions de CTG-004.

**Objectif :** commander l'arrêt du réchauffeur, appliquer un forçage manuel en cas d'échec et, si le réchauffeur ne répond toujours pas, délester sa ligne d'alimentation au niveau de l'EPS — puis confirmer que la hausse est enrayée.

*(Il s'agit de l'une des huit fiches exécutables par la machine. Sa branche exécutable est celle du circuit **batterie** — circuit 0, ligne EPS 5 — car un élément lithium au-dessus de 50 °C constitue un danger chimique et non un simple désagrément. Les variantes OBC (circuit 1, ligne 6) et propulseur (circuit 2) ont la même structure de branchement avec des arguments substitués. Le branchement est essentiel : exécutée sans ses branchements, la fiche délesterait la ligne d'alimentation du réchauffeur même lorsque celui-ci a déjà obéi à la commande OFF.)*

**Issues défavorables possibles / écarts :**

- Emballement de la zone batterie → perte de capacité / endommagement des éléments ; peut conduire vers EMG-002
- Emballement de la zone charge utile → dommage permanent à la charge utile s'il n'est pas enrayé ; mettre immédiatement la charge utile en sécurité
- Emballement dû à l'attitude (panneau exposé en permanence au Soleil) → se coordonner avec l'AOCS pour une réorientation
- Emballement de plusieurs zones → candidat à EMG-001

| Étape | Action | TC / code | Confirmation | Remarques |
|:----:|:-------|:----------|:--------|:------|
| 1 | Thermique : identifier la zone concernée et confirmer la tendance à la hausse | `HK_REQUEST(sid=3)` (S3.27) | □ | `tcs.temp_battery` 0x0407 / `temp_obc` 0x0406 / `temp_thruster` 0x0409 |
| 2 | Thermique : commander l'arrêt (OFF) du réchauffeur en cause | `HEATER_BATTERY(on=0)` (40) / `HEATER_OBC(on=0)` (41) / `HEATER_THRUSTER(on=0)` (42) | □ | État 0x040A / 0x040B / 0x041B → 0 |
| 3 | Thermique : si l'état ne s'est pas annulé, forcer la plage du thermostat vers le froid | `HEATER_SET_SETPOINT(circuit=…, on_temp=…, off_temp=…)` (S8 func_id 44) | □ | Circuits 0 batterie, 1 OBC, 2 propulseur |
| 4 | EPS : si le réchauffeur ne répond toujours pas, délester sa ligne d'alimentation | `EPS_POWER_OFF(line_index=5)` (batterie) ou `6` (OBC) (S8 func_id 20) | □ | Uniquement sur la branche NO-GO ; `eps.pl_htr_bat` 0x0115 / `pl_htr_obc` 0x0116 → 0 |
| 5 | Tous les postes : délester toute autre charge contribuant à l'échauffement de la zone | (selon la carte des zones) | □ | Y compris la charge utile le cas échéant |
| 6 | Thermique : surveiller la tendance ; si elle continue de monter, passer à EMG-001 | (lire SID 3) | □ | Décision consignée |
| 7 | Thermique : après rétablissement, rétablir la ligne et rendre la main au thermostat | `EPS_POWER_ON(line_index=…)` (19) ; `HEATER_AUTO_MODE(circuit=…)` (45) | □ | Ne pas laisser la batterie sans protection contre le gel |
| 8 | FD : informer le responsable de mission des dommages matériels potentiels | (point de situation) | □ | « EMG-006 active » |

</div>

<div style="page-break-before: always"></div>

## 14.6 Index complet des procédures

Consultez le fichier du simulateur
`configs/eosat1/procedures/procedure_index.yaml`, qui fait foi, pour la
liste des **70** identifiants de procédure (69 actifs ; CTG-018 est retirée au profit de CTG-021) avec leurs chemins de fichier :
LEOP-001 à LEOP-007, COM-001 à COM-013, NOM-001 à **NOM-014**,
CTG-001 à **CTG-030** et EMG-001 à EMG-006. Les procédures
suivantes sont citées dans les plans de passage mais ne sont pas
développées en fiches d'une page dans ce catalogue, car leurs étapes
relèvent soit de la remise en ordre courante (journaux de clôture, tri des
fiches, export des tendances), soit de procédures provisoires en attente de contenu simulateur :

- Procédures mineures propres à la LEOP : aucune en suspens (LEOP-001 à
  LEOP-007 font toutes l'objet d'une fiche ci-dessus).
- Recette en orbite : les treize fiches COM existent dans l'arborescence et
  les treize figurent désormais ci-dessus. **COM-004 est la vérification des
  actionneurs SCAO, et non une procédure provisoire pour le magnétomètre** — l'étalonnage
  du magnétomètre fait partie de COM-003 Étalonnage des capteurs SCAO — et c'est
  la seule fiche de tout le catalogue qui envoie
  `AOCS_ENABLE_WHEEL`. Les tirages antérieurs écartaient COM-004 comme
  procédure provisoire et omettaient la fiche ; un satellite exploité ainsi
  atteint les opérations nominales avec ses quatre roues toujours désactivées.
- Opérations nominales : dans l'index livré, NOM-006 est Chargement logiciel et
  **NOM-008 est Synchronisation de l'horloge** (`nominal/clock_sync.md`)
  — les deux sont souvent intervertis, et toute référence à
  « NOM-006 (clock_sync.md) » est erronée. **NOM-013 Exécution d'une manœuvre
  de maintien d'orbite** et **NOM-014 Retrait de service en fin de
  vie** closent la série. Les deux fiches nominales
  supplémentaires du livre, **Chargement du plan de passage** et
  **Revue des tendances à long terme**, n'ont pas d'équivalent livré dans le
  simulateur et ne sont plus laissées isolées : le chargement du plan
  de passage s'insère dans le déroulement nominal juste avant le
  créneau de prise de vue (son produit est ce qu'exécute NOM-002), et la
  revue des tendances à long terme est une activité de fin de quart, menée lors de la
  passation de consignes et restituée dans le cadre de NOM-012.
- Les fiches de contingence peu fréquentes CTG-021 à CTG-027 sont
  entièrement développées ci-dessus au §14.4 ; les fichiers de procédure du simulateur
  correspondants sont `contingency/obc_bootloader_recovery.md`,
  `bus_failure_isolation.md`, `progressive_load_shed.md`,
  `solar_panel_loss_response.md`, `aocs_sensor_loss_recovery.md`,
  `aocs_actuator_stuck_recovery.md` et `gps_time_sync_recovery.md`.
  Les fiches de ce manuel sont condensées ; les fichiers du simulateur
  contiennent les listes d'étapes complètes.

Trois fiches du simulateur n'ont pas de fiche propre dans ce livre :
CTG-005 Mode survie EPS (son contenu est accessible par CTG-001),
CTG-011 Basculement sur l'OBC redondant (par CTG-017 / CTG-022) et
CTG-018 Reprise par le chargeur d'amorçage, retirée au profit de
CTG-021 Reprise de l'OBC par le chargeur d'amorçage. Les deux anciennes
consolidations du livre, CTG-B01 (Anomalie IMU / gyro) et CTG-B02 (Anomalie
du taux de rejet des TC), sont désormais les fiches du simulateur
**CTG-029** Reprise après panne de gyroscope et **CTG-030** Rejet de
télécommande et échec de vérification.

**Huit fiches sont exécutables par la machine** depuis l'onglet Procédures du MCS :
NOM-002, NOM-003, NOM-004, NOM-008, NOM-009, CTG-001, CTG-008 et
EMG-006 (Emballement thermique). NOM-002/003/004
et NOM-009 sont liées à des types d'activité du planificateur
(`imaging_pass`, `data_dump`, `orbit_manoeuvre`,
`housekeeping_collection`) ; NOM-008, CTG-001, CTG-008 et la fiche
d'emballement thermique portent `runnable: {kind: markdown}` et sont
exécutées à partir de leurs propres annotations **TC:**. L'exécuteur
ne signale plus de succès pour une procédure qui n'a rien fait, et
l'exécuteur du MCS traite les étapes `label` et `branch` et échoue
en position sûre sur tout type d'étape qu'il ne comprend pas. CTG-020 est la
seule fiche **déclarée consultative** : elle porte `advisory: true` avec
un motif explicite et aucun lien `runnable:`, car toutes ses actions
sont effectuées au sol.

Tout opérateur recourant à un identifiant de procédure provisoire doit consulter le FD et
le fichier de procédure du simulateur avant toute commande.

**Trois éléments de l'arborescence, plus récents que toutes les éditions imprimées de ce livre.**
(1) La phase de mission est désormais une **télécommande**,
`SYS_SET_MISSION_PHASE` (S8 func_id 120) : l'étape 7 de LEOP-003 déclare
COMMISSIONING (5) et l'étape 4 de COM-013 déclare NOMINAL (6). Toute
affirmation, ailleurs, selon laquelle la phase ne se règle qu'à la console, ou selon laquelle
`SET_PHASE` est un alias d'`OBC_BOOT_APP`, est caduque — cet
alias a été supprimé. (2) L'OBC dispose d'une **horloge indépendante**
partant de J2000, dérivant d'environ 12 ppm, asservissable au GPS, avec
`obdh.time_ref` (0x0A13) / `obdh.obc_time_fine` (0x0A12) /
`obdh.time_since_sync_s` (0x0A14) comme télémesure, et **une
réinitialisation du chargeur d'amorçage la ramène à J2000** — c'est pourquoi chaque fiche de redémarrage de
ce chapitre se termine par une resynchronisation. (3) Les **roues de réaction doivent être
explicitement activées** avec `AOCS_ENABLE_WHEEL` (S8 func_id 3) dans
COM-004 ; le chargeur d'amorçage les laisse désactivées et rien d'autre ne
les active.

<small>*Note historique — numérotation des tirages antérieurs.* Avant
octobre 2026, ce livre numérotait douze fiches de contingence et
d'urgence autrement que le simulateur. Ancien → actuel : EMG-002 →
EMG-005, EMG-003 → EMG-004, EMG-004 → EMG-003, EMG-005 → EMG-006,
EMG-006 → EMG-002 ; CTG-005 → CTG-013, CTG-006 → CTG-028, CTG-011 →
CTG-016, CTG-013 → CTG-009, CTG-016 → CTG-006 ; les fiches propres au
livre CTG-009 (IMU / gyro) et CTG-018 (taux de rejet des TC) sont
devenues CTG-B01 et CTG-B02, puis, en octobre 2026, les fiches du simulateur
CTG-029 et CTG-030. Tous les autres identifiants étaient
déjà ceux du simulateur.</small>

---

## 14.7 Références

- ECSS-E-ST-70-32C — *Test and operations procedures* — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/)
- FAA AC 120-71 — *Standard Operating Procedures* — [www.faa.gov](https://www.faa.gov/regulations_policies/advisory_circulars/)

# Chapitre 15 — Référence télémesure, FDIR et surveillance

Ce chapitre constitue la liste de surveillance. Imprimez les tableaux
de télémesure par poste et apportez-les à la console ; l'échelle
d'escalade FDIR s'affiche au mur.


![Automate d'états FDIR : NORMAL → MONITOR → DETECT → ISOLATE → RECOVER → EVALUATE, avec des exemples de noms de règles et les fenêtres temporelles de chaque transition.](../assets/figures/fig_fdir_state_machine.svg)

*Automate d'états FDIR : NORMAL → MONITOR → DETECT → ISOLATE → RECOVER → EVALUATE, avec des exemples de noms de règles et les fenêtres temporelles de chaque transition.*

## 15.1 Télémesure — référence condensée par sous-système

(Fichier complet des paramètres : `telemetry/parameters.yaml`. Fichier des limites :
`mcs/limits.yaml`, qui contient 51 plages jaune/rouge, chacune avec son
propre `check_interval_s`. Les limites sol et les moniteurs S12 de bord
sont désormais réellement actifs des deux côtés : un paramètre peut donc être jaune sur la
console sans qu'un moniteur de bord se soit déclenché, et inversement —
c'est un élément de diagnostic, pas un bogue.)

Les tableaux par poste figurent déjà au chapitre 6 (rubrique
*Télémesure à surveiller* de chaque poste). Faites-y référence plutôt
que de les dupliquer.

**Structures de servitude.** La télémesure périodique arrive dans
des structures de servitude définies dans `telemetry/hk_structures.yaml`.
Les SID qu'un opérateur rencontrera sont les suivants :

Tableau 15.1 — Identifiants des structures de servitude, contenu et cadence.

| SID | Contenu | Cadence |
|---|---|---|
| 1 | EPS | 1 s |
| 2 | AOCS | 4 s |
| 3 | TCS | 60 s |
| 4 | OBDH / plateforme | 8 s |
| 5 | Charge utile | 8 s |
| 6 | TT&C | 8 s |
| 7 | AOCS détermination et contrôle | 4 s |
| 8 | EPS gestion de puissance (étendue) | 8 s |
| 9 | Propulsion | 8 s |
| 11 | Balise (ligne de vie du chargeur d'amorçage, UHF) | 30 s |

`default_enabled_sids` vaut `[1, 11]`, et le moteur réapplique exactement
cette valeur à l'amorçage du logiciel applicatif. **Tout le reste doit être activé avec
`HK_ENABLE` — service 3, sous-type 5 — en précisant le SID.** Un rapport
ponctuel s'obtient avec `HK_REQUEST`, **service 3, sous-type 27**. Si une vue est
vide au début d'une séance, la première question n'est pas « avons-nous
perdu la liaison ? » mais « quelqu'un a-t-il activé ce SID ? ».

**La péremption dépend de la cadence, pas d'un seuil fixe.** Le MCS croise
`hk_structures.yaml` avec `mcs/staleness.yaml` et en déduit, pour chaque
paramètre : à jour tant que l'âge ≤ max(10 s, intervalle × 0,9), dégradé tant que
l'âge ≤ max(20 s, intervalle × 1,5), périmé au-delà. Un paramètre TCS du
SID 3 à 60 s peut donc avoir 54 s et être encore considéré comme
actuel ; un paramètre EPS du SID 1 à 1 s ne le peut pas. Les paramètres qui
n'appartiennent à aucune structure (lecture à la demande / S20) sont apériodiques et utilisent
300 s / 900 s. Il existe un quatrième état, NOT ENABLED, affiché lorsque toutes les
structures portant le paramètre sont désactivées — la bonne réponse
est alors `HK_ENABLE`, et non une enquête sur la liaison.

**Télémesure ajoutée depuis la dernière édition, à inscrire sur la
liste de surveillance :**

Tableau 15.2 — Paramètres ajoutés récemment.

| Paramètre | ID | Pourquoi c'est important |
|---|---|---|
| `aocs.gyro_units_on` | 0x0294 | Nombre de gyromètres alimentés (équipements S2 0x0206–0x0208). 0 = l'estimateur n'a aucune référence de vitesse et poursuit sur les senseurs solaires grossiers (CSS) et le magnétomètre |
| `aocs.gyro_saturated` | 0x0295 | Au moins une voie gyrométrique est en butée de sa plage de mesure — connaissance de la vitesse perdue sur cet axe |
| `aocs.gyro_bias_injected` | 0x0296 | Amplitude d'un défaut de biais gyrométrique injecté ; 0 sur un satellite sain |
| `aocs.commanded_mode` | 0x0297 | Le mode demandé par le sol, affiché à côté du mode réel 0x020F — une rétrogradation est désormais visible au lieu d'être déduite |
| `tcs.fpa_cooler_floor_c` | 0x0424 | Température FPA la plus froide que le refroidisseur peut maintenir avec le puits et la charge actuels (à la demande) |
| `tcs.fpa_cooler_margin_k` | 0x0425 | Consigne commandée moins plancher atteignable ; **≤ 0 signifie que la consigne est hors d'atteinte** (à la demande) |
| `prop.state` | 0x0B00 | 0 SAFED, 1 ARMED, 2 FIRING, 3 INHIBIT — tête du bloc propulsion, transmis dans le SID HK 9 |
| `prop.tank_pressure` | 0x0B01 | Fonctionnement en blowdown 22,00 → 9,33 bar ; le moniteur de variation sur ce paramètre détecte une fuite avant l'estimation du débit de fuite |
| `prop.dv_remaining` | 0x0B0C | Delta-V restant sur l'ergol disponible, sur un total de 66,9 m/s |
| `ttc.link_status` | 0x0501 | **LOCKED vaut 2, pas 1.** Une fiche ou une vue qui teste « = 1 » pour le verrouillage est erronée |

## 15.2 Règles de surveillance S12 (46 dans la configuration nominale)

(Fichier complet : `monitoring/s12_definitions.yaml`. Synthèse par
sous-système ci-dessous. Dans ce fichier, la gravité S12 est un *mot* — `WARNING` ou
`ALARM` — que le satellite convertit dans l'octet du rapport en
1 INFO / 2 WARNING / 3 ALARM / 4 HIGH avant de l'empaqueter. Ne lisez pas
ces nombres comme l'échelle FDIR du §15.4.)

Tableau 15.3 — Nombre de règles de surveillance S12 par sous-système, avec des exemples représentatifs.

| Sous-système | Règles | Exemples |
|---|---|---|
| EPS | 9 | `eps.bat_soc` 0x0101 < 20 % (WARNING) et < 10 % (ALARM) ; `eps.bus_voltage` 0x0105 < 27 V (WARNING) et < 25 V (ALARM) ; sur/sous-température batterie ; surintensité batterie ; courant faible du générateur solaire A/B |
| AOCS | 11 | quatre règles de survitesse des roues sur 0x0207–0x020A à ±5000 tr/min ; `aocs.h_env_frac` 0x02BA enveloppe de moment cinétique > 70 % ; `aocs.att_error` 0x0217 > 1° ; senseur stellaire 1 / 2 aveugle (0x0240 / 0x0243, ALARM) ; trois règles de biais gyrométrique sur 0x0270–0x0272 |
| TCS | 5 | `tcs.temp_fpa` 0x0408 hors de −22…+14 °C (WARNING) et de −25.5…+17.5 °C (ALARM) ; surchauffe OBC ; surchauffe batterie ; `tcs.htr_total_power` 0x0411 > 12.5 W |
| TT&C | 5 | `ttc.link_margin` 0x0503 < 3 dB (ALARM) ; RSSI faible ; Eb/N0 faible ; surchauffe de l'amplificateur de puissance ; `ttc.ber` 0x050C élevé (échelle log10, donc > −5 = pire que 1e-5) |
| OBDH / plateforme | 4 | `obdh.cpu_load` 0x0302 > 85 % ; occupation mémoire élevée ; `obdh.reboot_count` 0x030A > 3 (ALARM) ; erreurs mémoire |
| Charge utile | 4 | température FPA ; `payload.store_used` 0x0604 > 95 % ; `payload.checksum_errors` 0x0609 non nul ; RSB faible |
| PROP | 8 | `prop.tank_pressure` 0x0B01 : plage, hors plage et **taux de variation** (c'est le contrôle de variation qui détecte une fuite) ; `prop.catbed_temp` 0x0B05 : plage et surchauffe ; ergol bas ; poussée faible ; `prop.dv_remaining` 0x0B0C : enveloppe basse |

Remarquez la forme du jeu de règles de propulsion : c'est le seul sous-système dont
les moniteurs comportent un contrôle de *variation* (`check_type: 1`). Tout le reste sur
ce satellite est surveillé par rapport à une plage absolue.

## 15.3 Règles événement-action S19 (32 définies, 31 activées)

(Fichier complet : `monitoring/s19_rules.yaml`. Chaque règle est *déclenchée
par* un événement S5 ou par le moniteur S12 d'un paramètre, et *exécute*
une action autonome sans opérateur dans la boucle.)

Le discriminant `trigger.kind` est la première chose à lire. Les identifiants d'événement
et de paramètre partagent tous deux la plage 0x0000–0x0FFF : une règle n'est donc
sans ambiguïté qu'une fois que l'on sait si `kind` vaut `event` ou `param`. Une
règle avec `kind: param` se déclenche sur la violation de limite S12 de ce
paramètre — ce qui signifie que désactiver un moniteur S12 désactive silencieusement
l'autonomie qui en dépend.

Points saillants :

Tableau 15.4 — Règles événement-action S19 représentatives, avec déclencheur et action autonome.

| Règle | Déclencheur | Action autonome |
|---|---|---|
| `eps_bus_undervoltage_payload_off` | `kind: event`, événement S5 0x0102 BATTERY_SOC_CRITICAL | charge utile éteinte (délestage) |
| `aocs_momentum_saturation_desaturate` | `kind: param`, moniteur S12 sur `aocs.h_env_frac` 0x02BA (jaune 70 %, rouge 90 %) | lancer la désaturation des roues |
| `aocs_star_tracker_1_blind_switch` | `kind: param`, moniteur S12 sur `aocs.st1_status` 0x0240 | sélectionner l'autre senseur stellaire |
| `tcs_fpa_overtemp_payload_off` | `kind: param`, moniteur S12 sur `tcs.temp_fpa` 0x0408 | charge utile éteinte |
| `ttc_link_margin_critical_boost_tx` | `kind: param`, moniteur S12 sur `ttc.link_margin` 0x0503 (ALARM en dessous de 3 dB) | augmenter la puissance d'émission d'un cran |
| `obc_reboot_event` | `kind: event`, événement S5 0x0301 OBC_REBOOT | reprise après redémarrage |
| `payload_checksum_errors_verify` | `kind: param`, moniteur S12 sur `payload.checksum_errors` 0x0609 | vérifier le produit stocké |
| `prop_abort_on_low_tank_pressure` | `kind: param`, moniteur S12 sur `prop.tank_pressure` 0x0B01 | interrompre la poussée |
| `prop_disarm_on_safe_mode` | `kind: event`, passage en mode survie | désarmer la propulsion |

La règle `aocs_attitude_error_safe_mode` (ea_id 2004) est présente mais
`enabled: false` — la seule règle désactivée sur les trente-deux. Ne
planifiez pas un quart en supposant qu'une forte erreur d'attitude fera
passer le satellite en mode survie de lui-même.

## 15.4 Échelle d'escalade FDIR

Tableau 15.5 — Échelle d'escalade FDIR, avec l'action par défaut et la réponse attendue de l'opérateur pour chaque niveau de gravité.

| Niveau | Signification | Action par défaut | Réponse de l'opérateur |
|---|---|---|---|
| 0 | Information | Journalisation seule | Mention sur la boucle |
| 1 | Attention | Journalisation + alerte | À traiter au débriefing |
| 2 | Avertissement | Journalisation + alerte + mesure autonome si elle est définie | Exécuter la procédure de reprise |
| 3 | Grave | Action autonome + alerte sol + signalement pour le passage suivant | Exécuter la reprise + fiche d'anomalie |
| 4 | Critique | Candidat au mode survie (autonome si la règle le prévoit) | Confirmer le passage en mode survie, informer le responsable de mission |

**La gravité n'est pas le niveau d'autonomie.** Deux nombres distincts coexistent dans la
configuration FDIR, et les opérateurs les confondent constamment :

- **La gravité FDIR, de 0 à 4**, correspond au tableau ci-dessus : *à quel point est-ce grave*.
- **Le niveau d'escalade de la reprise, de 0 à 3**, dans
  `fdir/fault_propagation.yaml`, indique *avec quelle insistance le satellite a déjà
  essayé*. `initial_level` vaut 1, `max_attempts` vaut 3, et chaque domaine
  possède une reprise de niveau 1 / 2 / 3 : pour l'EPS, délestage étape 1 → 2 → 3 ;
  pour l'AOCS, reprise du mode survie → réinitialisation AOCS → mise hors tension d'urgence ;
  pour le TT&C, réduction de la puissance d'émission → commutation d'antenne → arrêt d'urgence.
  Les délais d'escalade sont de 30 s après le niveau 1 et de 60 s après le niveau 2 ;
  le niveau 3 est définitif et ne donne lieu à aucune escalade supplémentaire.

Un événement de gravité 4 peut rester au niveau d'escalade 1, et un événement de gravité 2
peut atteindre le niveau 3. Précisez toujours de quel nombre vous parlez sur la boucle.

Les étapes de délestage ont leurs propres seuils, également dans
`fdir/fault_propagation.yaml` : étape 1 « Power Conservation » à 30 %
de SoC, étape 2 « Payload Offline » à 20 %, étape 3 « Survival Mode » à
10 %. Les charges délestées par `EPS_SET_MODE` sont rétablies par l'opérateur, et non
automatiquement.

## 15.5 Référence des commandes — liste complète par sous-système

Voici l'ensemble complet des télécommandes qu'un opérateur peut envoyer au
satellite de référence, regroupées par sous-système et répertoriées par
mnémonique et par objet. Il complète les références de télémesure, de surveillance et
FDIR ci-dessus, de sorte que le chapitre 15 constitue l'unique aide-mémoire de l'opérateur.
La numérotation des *identifiants de fonction* PUS S8 sous-jacente (ainsi que les champs
de paramètres de chaque commande) est donnée au §7.7 ; les noms ci-dessous sont les
mêmes mnémoniques que ceux du panneau de commande et du catalogue
de procédures (chapitre 14).

**AOCS — contrôle d'attitude et d'orbite**

Tableau 15.6 — Commandes AOCS — contrôle d'attitude et d'orbite.

| Commande | Objet |
|---|---|
| `AOCS_SET_MODE` | Régler le mode AOCS (0=OFF, 1=SAFE_BOOT, 2=DETUMBLE, 3=COARSE_SUN, 4=NOMINAL, 5=FINE_POINT, 6=SLEW, 7=DESAT, 8=ECLIPSE, 9=INERTIAL). Le mode 5 est refusé avec TM(1,8) tant que le masque de bits de préconditions `aocs.fine_ready` 0x02C5 n'est pas à 0 |
| `AOCS_DESATURATE` | Lancer la désaturation des roues. Un déchargement dure de 20 à 50 min, inhibe la prise de vue pendant son déroulement, comporte un délai d'attente et revient au mode antérieur à la désaturation |
| `AOCS_DISABLE_WHEEL` | Désactiver une roue de réaction donnée (`wheel_idx` 0–3) |
| `AOCS_ENABLE_WHEEL` | Activer une roue de réaction donnée |
| `ST1_POWER` | Allumer / éteindre le senseur stellaire 1 |
| `ST2_POWER` | Allumer / éteindre le senseur stellaire 2 |
| `ST_SELECT` | Sélectionner le senseur stellaire principal (deux têtes embarquées, ST1 et ST2) |
| `RW_SET_SPEED_BIAS` | Régler le biais de vitesse d'une roue de réaction — le biais est **ajouté à** la vitesse actuelle de la roue. Les vitesses de roue 0x0207–0x020A sont en lecture seule ; c'est par cette commande qu'on les pilote |
| `MTQ_ENABLE` | Activer / désactiver les magnétocoupleurs (relecture `aocs.mtq_enabled` 0x025E) |
| `AOCS_SLEW_TO` | Exécuter un basculement vers un quaternion cible |
| `AOCS_CHECK_MOMENTUM` | Interroger l'état du moment cinétique des roues |
| `AOCS_BEGIN_ACQUISITION` | Lancer l'acquisition d'attitude automatique |
| `AOCS_GYRO_CALIBRATION` | Réinitialiser l'estimation de biais gyrométrique de bord. L'étalonnage du biais se fait à bord — il n'y a pas de chargement d'un biais calculé au sol |
| `AOCS_RW_RAMP_DOWN` | Ralentir progressivement une ou plusieurs roues (`wheel_idx` 255 = toutes les roues) |
| `AOCS_SET_DEADBAND` | Régler la bande morte de commande du pointage FINE |
| `AOCS_SET_POINTING_FRAME` | Sélectionner le repère de référence pour le pointage NOMINAL / FINE |
| `AOCS_SET_TARGET_QUAT` | Régler le quaternion cible du maintien inertiel (utilisé par INERTIAL, mode 9) |
| `AOCS_SET_TARGET_GEO` | Définir une cible au sol pour la poursuite de cible hors nadir |
| `AOCS_FINE_READY_CHECK` | Rapporter le masque de bits de préconditions d'entrée en FINE 0x02C5 ; 0 = prêt. Le bit 1 signifie « moins de **trois** roues » — le mode FINE fonctionne sur trois roues |
| `AOCS_SET_MOM_MGMT` | Configurer la gestion autonome du moment cinétique (seuils de désaturation automatique) |
| `AOCS_SET_DESAT_INHIBIT` | Inhiber / autoriser la désaturation — un déchargement fait perdre le pointage fin, il est donc inhibé pendant une fenêtre de prise de vue |
| `AOCS_EST_RESET` | Réinitialiser l'estimateur d'attitude (p. ex. après un saut de temps). La source de l'estimateur se lit dans `aocs.est_source` 0x02C1 |
| `AOCS_GPS_SET_START_MODE` | Sélectionner le mode de démarrage du récepteur GPS (à froid / tiède / à chaud) |

**EPS — alimentation électrique**

Tableau 15.7 — Commandes EPS — alimentation électrique.

| Commande | Objet |
|---|---|
| `EPS_PAYLOAD_MODE` | Régler le mode d'alimentation de la charge utile (0=off, 1=standby, 2=imaging) |
| `EPS_FPA_COOLER` | Activer / désactiver le refroidisseur du FPA |
| `EPS_TRANSPONDER_TX` | Activer / désactiver l'émission du transpondeur |
| `EPS_POWER_ON` | Mettre une ligne d'alimentation sur ON (`line_index` 0–8). Neuf lignes, indices 0–8 : obc, ttc_rx, ttc_tx, payload, fpa_cooler, htr_bat, htr_obc, aocs_wheels, prop. Toute ligne commutable est OFF par défaut |
| `EPS_POWER_OFF` | Mettre une ligne d'alimentation sur OFF (`line_index` 0–8) |
| `EPS_RESET_OC_FLAG` | Réarmer l'indicateur de déclenchement sur surintensité et réactiver la ligne (`line_index` 0–8) |
| `EPS_SET_MODE` | Régler le mode de fonctionnement de l'EPS. SAFE déleste les deux charges les moins essentielles, EMERGENCY les déleste toutes ; les charges sont rétablies par l'opérateur, et non automatiquement |
| `EPS_SWITCH_LOAD` | Allumer / éteindre une charge individuelle |
| `EPS_SET_CHARGE_RATE` | Forcer le courant de charge de la batterie |
| `EPS_SOLAR_ARRAY_DRIVE` | Orienter l'angle du générateur solaire |
| `EPS_EMERGENCY_LOAD_SHED` | Délestage immédiat (étape 0–3) |

**Charge utile — imageur et données**

Tableau 15.8 — Commandes charge utile — imageur et données.

| Commande | Objet |
|---|---|
| `PAYLOAD_SET_MODE` | 0=off, 1=standby, 2=imaging, **3=calibration**. Les modes 1, 2 et 3 sollicitent tous le refroidisseur du FPA ; le mode 0 le libère |
| `PAYLOAD_SET_SCENE` | *Obsolète* — prérégler l'identifiant de la scène suivante. Remplacée par l'argument propre de `PAYLOAD_CAPTURE` |
| `PAYLOAD_CAPTURE` | Déclencher une acquisition d'image. Le *où* est fixé par le *quand* : programmez la prise de vue au-dessus de la cible. Refusée si l'obturateur est fermé |
| `PAYLOAD_DOWNLOAD_IMAGE` | Rapporter un produit image stocké |
| `PAYLOAD_DELETE_IMAGE` | Supprimer une image donnée de la mémoire |
| `PAYLOAD_MARK_BAD_SEGMENT` | Marquer un segment mémoire comme inutilisable |
| `PAYLOAD_GET_IMAGE_CATALOG` | Demander le catalogue des images stockées |
| `PAYLOAD_SET_BAND_CONFIG` | Régler le masque d'activation des bandes spectrales |
| `PAYLOAD_SET_INTEGRATION_TIME` | Temps d'intégration du détecteur, par bande |
| `PAYLOAD_SET_GAIN` | Régler le gain du détecteur |
| `PAYLOAD_COOLER_SETPOINT` | Consigne de régulation du FPA. L'argument est un **uint16 en centikelvins** : brut = round((T °C + 273.15) × 100), donc −15.00 °C donne 25815 = 0x64D7. Enveloppe −20…0 °C ; en dehors, la TC est **rejetée** avec l'erreur S1.8 0x0003, jamais écrêtée |
| `PAYLOAD_START_CALIBRATION` | Lancer une séquence d'étalonnage radiométrique (image d'obscurité / champ plat / les deux). Exige le mode charge utile 1 STANDBY ou 3 CALIBRATION — jamais 0 OFF ni 2 IMAGING. L'étalonnage d'obscurité n'exige plus le mode IMAGING |
| `PAYLOAD_STOP_CALIBRATION` | Interrompre l'étalonnage |
| `PAYLOAD_SET_COMPRESSION` | Sélectionner l'algorithme de compression et forcer le taux |
| `PAYLOAD_SELECT_FILTER` | Faire tourner la roue à filtres jusqu'à une position (2 s par pas de 90°) |
| `PAYLOAD_CYCLE_SHUTTER` | Exécuter un exercice du mécanisme d'obturateur — un test de santé, pas un moyen d'atteindre une position connue |
| `PAYLOAD_SET_SHUTTER` | Amener l'obturateur à une position **absolue**. C'est ce dont ont besoin une image d'obscurité et la vérification préalable à une prise de vue |
| `PAYLOAD_CAL_LAMP` | Allumer / éteindre la lampe d'étalonnage |
| `PAYLOAD_INITIATE_TRANSFER` | Lancer le moteur de transfert d'images de bord pour une scène stockée |

Un étalonnage refusé vous dit *pourquoi* : cinq codes d'échec dédiés,
0x0024 (refusé car en IMAGING), 0x0025 (FPA non prêt), 0x0026
(obturateur dans la mauvaise position), 0x0027 (lampe dans le mauvais état) et
0x0028 (prise de vue avec l'obturateur fermé). Les codes 0x0021–0x0023 restent ceux du
pointage de prise de vue. Lisez le code avant de renvoyer la commande.

**TCS — contrôle thermique**

Tableau 15.9 — Commandes TCS — contrôle thermique.

| Commande | Objet |
|---|---|
| `HEATER_BATTERY` | Allumer / éteindre le réchauffeur de batterie |
| `HEATER_OBC` | Allumer / éteindre le réchauffeur de l'OBC |
| `HEATER_THRUSTER` | Allumer / éteindre le réchauffeur du propulseur |
| `FPA_COOLER` | Allumer / éteindre le refroidisseur du FPA (activation côté TCS). Le refroidisseur est un cryoréfrigérateur miniature de type Stirling : son efficacité se dégrade à mesure que l'écart de température augmente, vérifiez donc `tcs.fpa_cooler_margin_k` 0x0425 avant d'incriminer la machine |
| `HEATER_SET_SETPOINT` | Régler les températures de marche / arrêt du thermostat d'un circuit |
| `HEATER_AUTO_MODE` | Rendre le réchauffeur au thermostat autonome |
| `TCS_SET_HEATER_DUTY_LIMIT` | Limiter le rapport cyclique du réchauffeur |
| `TCS_DECONTAMINATION_START` | Lancer le chauffage de décontamination de la charge utile |
| `TCS_DECONTAMINATION_STOP` | Interrompre la décontamination |
| `TCS_GET_THERMAL_MAP` | Demander l'état thermique de toutes les zones |

**OBDH — gestion bord des données**

Tableau 15.10 — Commandes OBDH — gestion bord des données.

| Commande | Objet |
|---|---|
| `OBC_SET_MODE` | Régler le mode de l'OBC (0=nominal, 1=safe, 2=emergency) |
| `OBC_MEMORY_SCRUB` | Déclencher un nettoyage mémoire (scrubbing) manuel |
| `OBC_REBOOT` | Forcer le redémarrage de l'OBC (retombe dans le chargeur d'amorçage) — **critique** |
| `OBC_SWITCH_UNIT` | Basculer sur l'OBC redondant — **critique** |
| `OBC_SELECT_BUS` | Sélectionner le bus CAN actif — **attention** |
| `OBC_BOOT_APP` | Amorcer le logiciel applicatif depuis le chargeur d'amorçage — **attention** |
| `OBC_BOOT_INHIBIT` | Inhiber l'amorçage automatique (rester dans le chargeur d'amorçage) |
| `OBC_CLEAR_REBOOT_CNT` | Remettre à zéro le compteur de redémarrages |
| `OBC_SET_WATCHDOG_PERIOD` | Configurer le délai du chien de garde |
| `OBC_WATCHDOG_ENABLE` | Activer la surveillance par chien de garde |
| `OBC_WATCHDOG_DISABLE` | Désactiver la surveillance par chien de garde |
| `OBC_DIAGNOSTIC` | Demander un diagnostic de santé de l'OBC |
| `OBC_ERROR_LOG` | Demander les entrées récentes du journal d'erreurs |
| `OBC_GPS_TIME_SYNC` | Synchroniser l'horloge de bord sur le GPS — **attention** (peut invalider la solution d'attitude de l'AOCS) |

**TT&C — télémesure, poursuite et télécommande**

Tableau 15.11 — Commandes TT&C — télémesure, poursuite et télécommande.

| Commande | Objet |
|---|---|
| `TTC_SWITCH_PRIMARY` | Basculer sur le transpondeur principal |
| `TTC_SWITCH_REDUNDANT` | Basculer sur le transpondeur redondant |
| `TTC_SET_DATA_RATE` | Sélectionner un palier de l'échelle de débits TM. L'ancien codage est conservé : `rate=0` signifie toujours « le débit bas » et `rate=1` toujours « le débit haut » — mais ils sélectionnent désormais **LOW 16 kbit/s** et **HIGH 128 kbit/s**. Le troisième palier, BEACON 1 kbit/s, s'active avec `TTC_SET_BEACON_MODE`, pas ici. HIGH exige une antenne déployée, le mode DOWNLINK et une élévation ≥ 10°, faute de quoi la commande est **rejetée** avec S1.8, jamais écrêtée silencieusement |
| `TTC_SET_DOWNLINK_MODE` | Entrer dans le mode DOWNLINK / vidage charge utile ou en sortir — la condition d'accès au palier HIGH |
| `TTC_PA_ON` | Activer l'amplificateur de puissance |
| `TTC_PA_OFF` | Désactiver l'amplificateur de puissance. **La TM en bande S s'arrête, mais la balise UHF continue d'émettre** — voir ci-dessous |
| `TTC_SET_TX_POWER` | 0=LOW 1,0 W RF, 1=NOMINAL 2,0 W, 2=HIGH 5,0 W (le plafond). Les codes inconnus sont rejetés avec l'erreur S1.8 0x0003, jamais écrêtés |
| `TTC_DEPLOY_ANTENNA` | Déployer l'antenne du satellite (fil thermofusible) |
| `TTC_SET_BEACON_MODE` | Activer / désactiver la balise à bas débit |
| `TTC_CMD_CHANNEL_START` | Ouvrir un canal de commande dédié (15 min) |
| `TTC_SET_UL_FREQ` | Régler la fréquence de liaison montante |
| `TTC_SET_DL_FREQ` | Régler la fréquence de liaison descendante |
| `TTC_SET_MODULATION` | 0=BPSK, 1=QPSK, 2=8PSK, 3=OQPSK |
| `TTC_SET_RX_GAIN` | Régler la consigne de CAG du récepteur |
| `TTC_RANGING_START` | Lancer une séquence de mesure de distance (ranging) |
| `TTC_RANGING_STOP` | Arrêter la séquence de mesure de distance |
| `TTC_SET_COHERENT_MODE` | Activer / désactiver le mode cohérent du transpondeur |
| `TTC_BEACON_TX_ON` | Allumer l'**émetteur** de la balise UHF |
| `TTC_BEACON_TX_OFF` | Éteindre l'émetteur de la balise UHF — attention, cela supprime la ligne de vie |

EOSAT-1 embarque **deux émetteurs** : une chaîne principale en bande S et une
balise UHF séparée sur antenne fouet, à 437,5 MHz, 1 W dans un dipôle. La balise
émet le SID HK 11 et uniquement le SID 11, chaque fois que la chaîne en bande S
n'émet pas. C'est l'enseignement à tirer de `TTC_PA_OFF` : coupez
l'amplificateur, ou la ligne d'alimentation `ttc_tx`, et la télémesure en bande S s'arrête tandis que la
balise continue d'arriver toutes les 30 s. `ttc.pa_on` 0x0516 figure dans le SID 11
précisément pour que « aucune télémesure » devienne un diagnostic en une seule commande
plutôt qu'un mystère.

**PROP — propulsion**

EOSAT-1 emporte un module de monergol vert 1U offrant 66,9 m/s de
delta-V au total, utilisé pour l'évitement de débris, un maintien
d'orbite limité et la poussée de retrait de service en fin de vie (NOM-014). L'armement se fait volontairement en deux temps, et une poussée entraîne
un nouvel ajustement des éléments orbitaux : les passages et les éclipses se décalent donc réellement ensuite.

Tableau 15.12 — Commandes PROP — propulsion.

| Commande | Objet |
|---|---|
| `PROP_SET_BURN` | Charger une manœuvre : amplitude du delta-V, direction et mode de coupure |
| `PROP_ARM` | SAFED → ARMED. Exige un `PROP_SET_BURN` dans les 300 s précédentes |
| `PROP_DISARM` | ARMED → SAFED ; ferme la vanne de régulation de débit, laisse les vannes à verrouillage dans leur état |
| `PROP_EXECUTE` | ARMED → FIRING. Rejetée avec S1.8 hors de l'état ARMED |
| `PROP_ABORT` | FIRING → SAFED immédiatement ; ferme la FCV et verrouille un motif d'interruption |
| `PROP_ISO_OPEN` | Ouvrir une ou plusieurs branches de vannes à verrouillage |
| `PROP_ISO_CLOSE` | Fermer une ou plusieurs branches de vannes à verrouillage |
| `PROP_SET_LIMITS` | Reconfigurer les seuils d'interruption de poussée de bord |
| `PROP_INHIBIT_SET` | Inhibition propulsion verrouillée par le sol |
| `PROP_INHIBIT_CLR` | Lever l'inhibition sol et toute inhibition verrouillée par la FDIR |
| `PROP_GET_STATUS` | Rapport d'état de la propulsion à la demande |

**Mécanismes et éléments déployables**

Tableau 15.13 — Commandes des mécanismes et éléments déployables.

| Commande | Objet |
|---|---|
| `OBC_GPS_TIME_SYNC` | Synchronisation temporelle GPS (voir le tableau OBDH) |
| `EPS_DEPLOY_WING` | Déployer une aile solaire (+Y, −Y, les deux) par fil thermofusible |
| `EPS_WING_STATUS` | Interroger l'état de déploiement des ailes. La relecture se fait dans `eps.wing_status` 0x0144 (bit 0 = +Y déployée, bit 1 = −Y, bits 4/5 = déploiement en cours) ; les courants par aile sont 0x0146 (+Y) et 0x0147 (−Y) |
| `TTC_DEPLOY_ANTENNA` | Déploiement de l'antenne (voir le tableau TT&C) |

## 15.6 Références

- ECSS-E-ST-70-41C — *Telemetry and telecommand packet utilization* (PUS) — [ecss.nl](https://ecss.nl/standards/active-standards/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/)
- CCSDS 132.0-B-3 — *TM Space Data Link Protocol* — [public.ccsds.org](https://public.ccsds.org/)
- CCSDS 660.0-G-3 — *PUS green book* — [public.ccsds.org](https://public.ccsds.org/Pubs/660x0g3.pdf)

# Chapitre 16 — Fiches approfondies par poste (études de cas)

Ce chapitre développe chacun des neuf postes au moyen d'une
étude de cas sur plusieurs quarts — un récit réaliste de la manière dont le
poste se comporte au fil d'une série de quarts. À lire comme complément
avant les journées de simulation.

## 16.1 Étude de cas FD — gérer le rebond du troisième jour de LEOP

Le premier passage LEOP de l'équipe se passe mal. Il lui faut quatre minutes pour
amener l'OBC sur l'image applicative ; le décalage d'horloge mesuré dans
LEOP-006 ressort à 3,2 secondes, bien au-delà du seuil d'acceptation de 1,0 seconde
de la fiche ; et personne ne parvient à clore la vérification de la
synchronisation temporelle avant la LOS. Le SoC à la LOS est de 78 %. L'équipe est fragilisée. Sur
le réseau de cinq stations, le passage suivant est dans environ 35 minutes —
l'écart médian est de 33 minutes, 79 dans le pire des cas.

Un FD faible laisse l'équipe ruminer, mène un briefing d'avant-passage tendu,
et le deuxième passage se passe encore plus mal. Un FD solide procède ainsi :

1. **Il organise un débriefing à chaud de 10 minutes** immédiatement après la LOS. Il demande
   à chaque poste un point positif précis et un point
   d'amélioration précis.
2. **Il nomme ce qui s'est réellement bien passé.** `OBC_BOOT_APP` lui-même
   s'exécute en une dizaine de secondes — les quatre minutes correspondaient à
   l'attente, par l'équipe, de la confirmation au rythme de la balise
   toutes les 30 secondes, ce qui est le fonctionnement prévu du chargeur d'amorçage,
   et non un chargeur lent. Le décalage de 3,2 s est exactement ce que
   LEOP-006 sert à éliminer : `SET_TIME` a été envoyée, et le
   nombre qui compte est le résidu après synchronisation, pas celui
   d'avant. Et la liaison n'a jamais été près de poser
   problème — la marge sur le palier LOW se situe dans les quarante dB
   pour chacune des cinq stations.
3. **Il nomme une chose précise à changer au prochain passage.** « AOCS,
   nous n'avons jamais lancé l'étalonnage du biais gyrométrique. Au prochain passage, envoyez
   `AOCS_GYRO_CALIBRATION` en première action et relisez
   0x0270–0x0272. »
4. **Il ramène l'équipe à des besoins physiques.** « Prenez 20 minutes,
   mangez, hydratez-vous, sortez marcher si vous le pouvez. On se retrouve à
   AOS−10 min pour le briefing d'avant-passage. »

Le deuxième passage réussit. L'équipe apprend que la LEOP n'est pas
une affaire de perfection — c'est une affaire d'adaptation. Cette leçon la marque pour
le reste de sa carrière.

## 16.2 Étude de cas SPACON — trois procédures en parallèle

Nous sommes au milieu du jour 4. L'équipe déroule COM-009 (mise sous tension de la charge utile)
lorsque l'EPS annonce une surintensité. CTG-012 démarre. Alors que le SPACON est
au milieu de CTG-012, le panneau FDIR fait apparaître une *deuxième* règle — le
senseur stellaire se dégrade.

Un SPACON faible tente de tout faire à la fois — s'embrouille, saute une étape
de CTG-012 et passe complètement à côté de la dégradation du senseur stellaire.

Un SPACON solide procède ainsi :

1. **Il fixe les priorités.** « FD, SPACON — deux anomalies. CTG-012
   en cours. Senseur stellaire en dégradation, gravité FDIR 2, pas encore
   3, et toujours au niveau d'escalade 1. Je recommande de poursuivre
   CTG-012 ; AOCS prend la surveillance du senseur stellaire jusqu'à ce que
   la gravité 3 se déclenche. »
2. **Il confie explicitement la deuxième anomalie.** « AOCS, surveillez
   `aocs.st1_status` 0x0240. S'il passe à 3 — aveugle — c'est
   un moniteur ALARM et la règle S19 sélectionnera ST2 sans
   nous demander notre avis. Annoncez-le haut et fort quand cela arrive. »
3. **Il termine la première procédure.** Il rédige la fiche d'anomalie.
4. **Il revient à la deuxième.** « FD, SPACON — fiche CTG-012
   déposée. AOCS, état ? »

La discipline est la suivante : **une procédure à la fois par opérateur ;
des passations explicites ; le FD sait où en est chacun.**

## 16.3 Étude de cas AOCS — la discussion sur le bilan de pointage

Nous sommes en fin de jour 4. L'erreur de pointage totale
(`aocs.total_pointing_err_3sig`, 0x02AA) est de 0,042° pour
une référence de 0,021°. La charge utile veut faire une prise de vue maintenant. Le responsable de mission
veut le bulletin client.

Un ingénieur SCAO faible dit « le pointage est dégradé mais sans doute
suffisant pour la prise de vue » et laisse le FD décider sans aucune information
réelle.

Un ingénieur SCAO solide procède ainsi :

1. **Il décompose le bilan.** « FD, AOCS — 0x02AA est à 0.042 deg
   au total, et ce nombre est la somme quadratique (RSS) d'exactement deux termes :
   l'erreur de connaissance 0x02A7, actuellement 65 arcsec — 0.018 deg —
   et l'erreur de contrôle 0x02A8, actuellement 0.038 deg. La connaissance est
   nominale. Tout se joue sur le terme de contrôle, et
   `aocs.h_env_frac` 0x02BA est monté à 74 % de l'enveloppe de moment
   cinétique sur les trois dernières orbites. Nous avons dépassé le jaune
   à 70 %. »
2. **Il anticipe.** « Au rythme actuel, 0x02BA atteint le rouge à 90 %
   dans l'heure, l'erreur de contrôle passe à environ 0.048 et
   le total à 0.051 deg. À 513 km, cela donne une erreur de géolocalisation
   (0x02C7) d'environ 460 m, pour une distance d'échantillonnage au sol (GSD) de 33,4 m —
   plus d'une douzaine de pixels. Ce n'est pas un produit
   de qualité scientifique. »
3. **Il recommande.** « FD, AOCS — je recommande de commander la désaturation
   maintenant et de la laisser se dérouler pendant l'intervalle entre passages. Un déchargement dure de 20 à
   50 minutes et inhibe la prise de vue pendant ce temps : “désaturer
   à ce passage, imager au suivant” est donc la seule option
   qui tienne. Si vous imagez maintenant, vous obtiendrez une image exploitable,
   et ce sera la *dernière* image exploitable jusqu'au déchargement. »

Ce type d'opérateur est rare. C'est à lui que le FD fait confiance
pour trancher les cas limites.

## 16.4 Étude de cas EPS — le mystère de la charge parasite

Le jour 4 commence avec un SoC inférieur de 2 % aux prévisions à chaque
sortie d'éclipse. À mi-quart, le SoC est à 38 % — et se dirige vers le
seuil de délestage de l'étape 1, à 30 %.

Un ingénieur EPS faible l'ignore et espère qu'il s'agit d'un transitoire.

Un ingénieur EPS solide procède ainsi :

1. **Il mesure.** Il relève chacun des neuf courants de ligne
   (0x0118–0x011F et 0x014B ; le total du bus est en 0x0148) et en fait la somme.
   Elle atteint 29,3 W. La consommation nominale moyenne sur l'orbite prévue est de
   28,8 W. Différence : 0,5 W de consommation supplémentaire en régime permanent — peu
   de chose face à la marge nominale de +16,3 W, mais inexpliqué, et cela mérite
   d'être examiné.
2. **Il traque la ligne.** Il compare chaque courant de ligne à sa valeur nominale :
   la plupart sont à moins de 5 %, mais le rapport cyclique de `htr_bat` est à
   18 % alors que 8 % étaient prévus. Consommation supplémentaire : env. 0,4 W. L'essentiel
   de l'anomalie est expliqué.
3. **Il formule une hypothèse.** La zone batterie a perdu une partie de son isolation
   thermique, si bien que le réchauffeur travaille davantage. Il se coordonne avec
   le thermicien : « Thermal, EPS — le rapport cyclique de `htr_bat` a doublé et
   `tcs.htr_total_power` 0x0411 a augmenté lui aussi. L'hypothèse est une
   dégradation de l'isolation. Pouvez-vous vérifier ? »
4. **Il rend compte au FD.** « FD, EPS — charge parasite identifiée,
   environ 0.4 W supplémentaires sur la ligne `htr_bat`. Dérive nette du SoC
   de 2 % par orbite. Je recommande d'accepter la situation et de poursuivre
   la recette en orbite ; la charge n'est pas dangereuse, seulement pénalisante.
   Ouvrir une fiche d'anomalie pour investigation au prochain quart. »

La mission se poursuit. Le quart suivant trouve la cause première
(une feuille de MLI partiellement décollée lors des vibrations du lancement). Sans
le travail minutieux de cet opérateur, personne n'aurait su quelle
question poser.

## 16.5 Étude de cas thermique — le refroidisseur qui ne refroidit pas

COM-010 démarre bien. FPA à +5 °C, refroidisseur activé, consommant ses
15 W nominaux. Au bout des 20 premières minutes : FPA à −2 °C, conforme au profil.
Puis il plafonne. À 35 minutes, le FPA n'est qu'à −3 °C ; le
profil prévoyait −5 °C.

Un thermicien faible attend, en espérant que le refroidisseur rattrape
son retard. À 60 minutes, le FPA est à −4 °C ; prévu −9 °C. Il
alerte le FD trop tard ; la première lumière est compromise.

Un thermicien solide procède ainsi :

1. **Il repère l'écart tôt.** À 30 minutes, quand le
   profil indique −4 °C et que la réalité est à −2 °C, il l'annonce. « FD,
   Thermal — mise en froid du FPA en retard de 2 °C sur le profil au
   point de contrôle des 30 minutes. Je surveille. »
2. **Il diagnostique avec le bon paramètre.** « FD, Thermal —
   vérification en cours. La consommation du refroidisseur est toujours de 15 W conformément à la spécification, donc la
   machine fonctionne. Je demande la paire de paramètres à la demande :
   `tcs.fpa_cooler_floor_c` 0x0424 indique −6.5 °C et
   `tcs.fpa_cooler_margin_k` 0x0425 indique −3.5. La marge est
   négative. La consigne est hors d'atteinte avec la température actuelle du puits
   et la charge du détecteur — ce n'est pas un refroidisseur
   défaillant, c'est un refroidisseur à court d'efficacité. »
3. **Il explique pourquoi et se coordonne avec l'AOCS.** « C'est une
   machine de type Stirling, pas un empilement Peltier : son rendement
   n'est qu'une fraction de celui de Carnot, donc son efficacité s'effondre à mesure que l'écart
   de température augmente. Le levier, c'est le puits, pas le refroidisseur. AOCS, Thermal
   — pouvez-vous vérifier que le radiateur est à l'ombre ? Si nous pouvons
   abaisser le puits de quelques kelvins, le plancher baissera d'autant. »
4. **Il anticipe et recommande.** « FD, Thermal — avec le
   plancher actuel, nous n'atteindrons pas du tout −10 °C, et la mise en froid
   progresse à 0.05 °C/min contre 0.15 prévus. Je recommande
   soit de rapprocher la consigne du plancher atteignable —
   `PAYLOAD_COOLER_SETPOINT` a une enveloppe stricte de −20 à 0 °C,
   et hors de celle-ci la commande sera *rejetée*, pas écrêtée —, soit de
   reporter la première lumière à une orbite où la géométrie du radiateur est
   plus favorable. Ce que je ne ferai pas, c'est continuer d'attendre un refroidisseur
   qui nous dit déjà qu'il ne peut pas y arriver. »

Un diagnostic net transforme une panique du type « le refroidisseur est en panne » en une
décision opérationnelle du type « nous travaillons dans un coin de l'enveloppe que nous avons mal
modélisé — reporter et réessayer ».

## 16.6 Étude de cas TT&C — le TEB qui n'en était pas un

Au milieu du jour 4, pendant l'essai de liaison descendante au palier HIGH de COM-006
(vérification de la liaison TT&C) — antenne déployée, mode DOWNLINK activé,
élévation largement au-dessus du seuil de 10° fixé par les règles d'exploitation, 128 kbit/s. Le TT&C
voit le TEB (`ttc.ber` 0x050C) monter brièvement à 5e-6, puis redescendre
à 1e-7. Durée totale du pic de TEB : 8 secondes. Aucune des deux
valeurs ne déclenche le moniteur de bord, réglé à 1e-5.

Un ingénieur TT&C faible traite le pic comme du bruit et continue.
Deux passages plus tard, le même pic se reproduit, et l'équipe se rend compte
qu'elle est passée à côté d'un phénomène récurrent.

Un ingénieur TT&C solide procède ainsi :

1. **Il consigne le pic.** Heure, durée, TEB maximal, marge de liaison
   à cet instant. Même si le pic a disparu de lui-même.
2. **Il formule une hypothèse.** « FD, TT&C — vu un bref pic de TEB. La marge
   de liaison n'a pas bougé ; le bilan fourni boucle HIGH à Troll
   à 5 degrés avec 33.7 dB — nous ne le planifions qu'au-dessus de 10 degrés,
   par règle sol —, ce ne peut donc pas être une
   liaison limitée par la marge. Cela oriente vers des trajets multiples ou un
   effet du diagramme de rayonnement plutôt que vers la géométrie. Le satellite
   est à 33 degrés d'élévation et 117 d'azimut depuis
   Iqaluit en ce moment — c'est un coin du diagramme de rayonnement
   connu pour son faible gain. »
3. **Il recommande.** « FD, TT&C — je recommande de ne pas télécharger de
   données critiques lorsque le satellite passe entre 115 et 120 d'azimut
   depuis Iqaluit. Je le signale dans le panneau de planification
   pour le prochain quart. »

L'équipe évite ainsi des pertes de données récurrentes pendant le reste de la
mission.

## 16.7 Étude de cas charge utile — l'image qui n'était pas de la science

La première lumière réussit. L'évaluation de la qualité est concluante — DN moyen
nominal, contraste nominal, erreur de géoréférencement de 165 m, soit environ
cinq pixels pour la distance d'échantillonnage au sol (GSD) de 33,4 m de l'imageur, et
dans le bilan. La bande couvre toute la fauchée de 273 km. Le responsable
de mission rédige le bulletin.

Un opérateur charge utile faible se réjouit et passe à autre chose. Il ne voit pas
que le *contenu* réel de l'image — dès qu'un collègue scientifique
l'examine — ne montre aucun signal exploitable de courant océanique, parce que
la couverture nuageuse était de 60 % (la prévision annonçait 8 %).

Un opérateur charge utile solide procède ainsi :

1. **Il lit l'histogramme.** « FD, Payload — la qualité d'image est conforme,
   mais la couverture nuageuse semble importante d'après l'histogramme. Je propose
   d'afficher l'image de la bande 1 et de l'examiner. »
2. **Il identifie le contenu réel.** « FD, Payload — confirmé,
   environ 60 pour cent de couverture nuageuse. Nous avons une image de première lumière
   techniquement valide, mais aucun signal exploitable de courant océanique. »
3. **Il veille à l'honnêteté du bulletin.** « Mission Manager,
   Payload — je recommande que le bulletin indique : “Première lumière acquise,
   image techniquement nominale, exploitation scientifique reportée en raison
   d'une couverture nuageuse inhabituellement dense ; nouvelle acquisition prévue
   au prochain passage dégagé.” »
4. **Il planifie la nouvelle acquisition.** Il demande au FDS la prévision
   nuageuse sur la zone cible pour le prochain passage.

Cet opérateur transforme un moment « succès technique, client déçu »
en un moment « rapport honnête, reprise planifiée, client qui
respecte l'équipe ».

## 16.8 Étude de cas FDS — la manœuvre qui n'était pas nécessaire

Jour 4, le matin. Le propagateur d'orbite prévoit que le satellite
survolera la cible de prise de vue à 14,6 degrés hors nadir au TCA (instant de plus courte distance) —
dans la limite de roulis de 14,93 degrés du planificateur, mais de justesse.

Un ingénieur FDS faible planifie une petite manœuvre pour centrer la
cible. Il consomme inutilement de l'ergol sur un bilan total de
66,9 m/s, et décale au passage tous les passages
et toutes les éclipses du plan.

Un ingénieur FDS solide procède ainsi :

1. **Il vérifie le propagateur.** « FD, FDS — le propagateur indique
   14.6 degrés hors nadir au TCA, juste à la limite de
   roulis. Je fais une vérification croisée avec le dernier point GPS. »
2. **Il relance la restitution d'orbite.** Il récupère le vecteur d'état GPS le plus récent
   et repropage. Résultat : 4,2 degrés hors nadir.
3. **Il rend compte.** « FD, FDS — le propagateur utilisait des données de restitution d'orbite périmées.
   La nouvelle restitution donne 4.2 degrés hors nadir — largement
   dans la limite de roulis de 14.93 degrés. Aucune manœuvre nécessaire.
   Cela mérite d'être dit à voix haute : une poussée ici nous aurait coûté de
   l'ergol *et* aurait entraîné un nouvel ajustement des éléments orbitaux, si bien que tous les passages
   et toutes les éclipses du plan de demain se seraient décalés. Un
   mètre par seconde modifie le demi-grand axe de 1.8 km et
   décale la chronologie de 33 secondes à plus vingt-quatre heures. »

On économise une manœuvre, on économise de l'ergol, on préserve le plan, et l'on évite
un basculement qui aurait perturbé l'AOCS pendant la fenêtre de prise de vue.

## 16.9 Étude de cas segment sol — le basculement qui a fonctionné

Jour 3, pendant la LEOP. Au milieu d'un passage au-dessus d'Iqaluit, le G/T mesuré de la station
chute de 3 dB. La marge reste énorme — cette liaison boucle avec
des dizaines de dB partout — si bien que rien ne se plaint côté satellite. Un
ingénieur segment sol faible attend et espère que la situation se rétablisse.

Un ingénieur segment sol solide procède ainsi :

1. **Il identifie.** « FD, Ground Seg — le G/T d'Iqaluit a chuté de 3 dB.
   La marge est correcte, mais la *tendance* ne l'est pas. J'enquête. »
2. **Il formule une hypothèse.** « FD, Ground Seg — très probablement un problème
   de chaîne RF à la station. Je vérifie les journaux de bande de base… oui, la température
   du LNA a grimpé de 8 degrés au-dessus du nominal au cours de la dernière
   minute. Le LNA se dégrade. »
3. **Il recommande.** « FD, Ground Seg — je recommande de terminer ce
   passage sur le palier LOW, 16 kbit/s, au lieu de HIGH à 128 —
   c'est `TTC_SET_DATA_RATE` avec rate 0 — et de quitter le
   mode DOWNLINK, puis de planifier toutes les activités critiques
   pour le prochain passage à Troll pendant la maintenance de ce LNA. »
4. **Il coordonne la passation.** Avec le TT&C : changement de débit. Avec le FDS :
   reconfirmation de l'horaire du passage à Troll.

La mission se poursuit sans perte.

## 16.10 Étude de cas responsable de mission — le bulletin qui comptait

Le jour 4 se termine par une première lumière reportée. Le client suit la situation.

Un responsable de mission faible écrit : « Première lumière reportée en raison d'une
anomalie technique. Reprise prévue au prochain quart. »

Un responsable de mission solide écrit :

> « Point sur la recette en orbite d'EOSAT-1, jour 4.
>
> Aujourd'hui, l'équipe a amené EOSAT-1 de la fin de la LEOP au
> seuil de la première lumière. Au fil des passages sol du quart — le
> réseau de cinq stations nous en offre un toutes les 33 minutes environ —
> l'équipe
> a exécuté 11 des 12 procédures de recette en orbite prévues. La
> douzième procédure (première lumière, acquisition d'image) a été
> formellement reportée en raison d'une dégradation du senseur stellaire
> survenue pendant le quart, qui a rompu le bilan de pointage exigé pour
> une imagerie de qualité scientifique.
>
> La décision de l'équipe de reporter plutôt que d'imager avec un
> bilan de pointage dégradé illustre exactement la
> discipline opérationnelle que nous visons : aucune image ne vaut d'être acquise
> si elle n'est pas de qualité scientifique.
>
> Plan de reprise : le premier passage de demain matin servira à exécuter
> la procédure de réinitialisation du senseur stellaire. Si la réinitialisation réussit,
> la première lumière sera retentée au deuxième passage. Si
> la réinitialisation échoue, le satellite dispose d'un second senseur stellaire
> et l'équipe basculera sur celui-ci ; l'estimation d'attitude propagée par les
> gyromètres, dont nos analyses montrent qu'elle permet une imagerie exploitable
> (bien que non optimale), reste la solution de repli. Nous vous tiendrons informés.
>
> Cordialement,
> [Responsable de mission] »

Le bulletin dit la vérité, nomme la discipline en jeu
et donne au client une information réelle sur les 24 prochaines
heures. Le client apprend à faire confiance à cette équipe.

---

---

