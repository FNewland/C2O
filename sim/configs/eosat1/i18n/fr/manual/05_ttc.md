# Télémesure, poursuite et télécommande (TTC) d'EOSAT-1 {#eosat-1-telemetry-tracking-and-command-ttc}

**Référence du document :** EOSAT1-UM-TTC-006
**Édition :** 2.0
**Date :** 2026-03-13
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble {#1-overview}

Le sous-système de télémesure, poursuite et télécommande (TTC) assure la liaison de communication
radiofréquence entre EOSAT-1 et le segment sol. Il prend en charge la réception des télécommandes,
l'émission de la télémesure et la mesure de distance (ranging) pour la restitution d'orbite. Le sous-système
comprend une paire de transpondeurs bande S en redondance froide (plus un émetteur de balise UHF distinct), avec un canal de commande PDM dédié
pour le récepteur, des antennes déployées par fil thermofusible et des modes de données à bas débit et à haut débit.

## 2. Architecture {#2-architecture}

### 2.1 Configuration des transpondeurs {#21-transponder-configuration}

| Paramètre           | Principal        | Redondant        |
|---------------------|------------------|------------------|
| Fréquence montante  | 2025,0 MHz (bande S) | 2025,0 MHz (bande S) |
| Fréquence descendante | 2200,0 MHz (bande S) | 2200,0 MHz (bande S) |
| Débit montant       | 4 kbit/s (fixe)  | 4 kbit/s (fixe)  |
| Liaison descendante (SAFE) | 1 kbit/s  | 1 kbit/s         |
| Liaison descendante (LOW) | 16 kbit/s  | 16 kbit/s        |
| Liaison descendante (HIGH) | 128 kbit/s | 128 kbit/s      |
| Modulation          | BPSK (TC) / BPSK ou QPSK (TM, selon le palier) | identique |
| Puissance RF de sortie | 2 W           | 2 W              |
| Redondance          | Redondance froide | —               |

Les trois débits descendants sont les échelons de l'**échelle de débits TM**
(§2.4). La liaison montante de télécommande est fixe à 4 kbit/s et ne fait *pas* partie de l'échelle :
augmenter le débit descendant n'augmente jamais le débit montant.

Un seul transpondeur est actif à la fois. L'équipement redondant est hors tension (redondance froide)
et peut être activé par commande sol au moyen de `TTC_SWITCH_REDUNDANT`. Si aucune télécommande
n'est acceptée pendant 24 h, la minuterie de perte de commande de bord bascule d'elle-même sur
l'autre équipement, puis de nouveau toutes les 24 h jusqu'à ce qu'une télécommande soit
acceptée (FDIR TTC-01, §8).

### 2.2 Canal de commande PDM dédié {#22-dedicated-pdm-command-channel}

Le récepteur du transpondeur est alimenté par un canal de commande PDM dédié, indépendant de
la ligne PDM commutable principale qui alimente l'émetteur et l'amplificateur de puissance. Cette caractéristique
de conception essentielle garantit que le satellite est toujours commandable :

| Composant          | Source d'alimentation       | Toujours sous tension ? |
|--------------------|-----------------------------|------------|
| Récepteur (RX)     | Non commutable `ttc_rx` (ligne 1) | Oui  |
| Émetteur (TX)      | Commutable `ttc_tx` (ligne 2) | Non      |
| Amplificateur de puissance | Commutable `ttc_tx` (ligne 2) | Non |

Après le dernier décodage d'une commande valide, une minuterie d'extinction automatique de 15 minutes démarre pour la ligne
commutable du TX et du PA. Si aucune autre commande n'est reçue dans les 15 minutes, l'émetteur
et l'amplificateur de puissance sont automatiquement mis hors tension pour économiser l'énergie. Le récepteur reste
alimenté indéfiniment par la ligne PDM non commutable.

Ce mécanisme de minuterie est particulièrement important pendant la période d'attente de 30 minutes après la séparation,
pendant laquelle le TX doit rester éteint, alors que le RX est prêt à recevoir les commandes sol dès
le déploiement de l'antenne.

### 2.3 Système d'antennes — déploiement par fil thermofusible {#23-antenna-system--burn-wire-deployment}

| Antenne              | Type          | Couverture      | Gain     |
|----------------------|---------------|-----------------|----------|
| Patch zénith (+Z)    | Réseau patch  | Hémisphérique   | 3 dBi    |
| Patch nadir (-Z)     | Réseau patch  | Hémisphérique   | 3 dBi    |

Les antennes sont repliées pendant le lancement et déployées à l'échéance de la minuterie de séparation de 30 minutes,
au moyen d'un mécanisme à fil thermofusible :

1. **Avant le déploiement** : les antennes sont maintenues en position repliée par un fil de retenue.
2. **Commande de fusion** : à l'échéance de la minuterie de séparation, l'OBC commande le circuit du
   fil thermofusible, qui fait passer un courant dans un fil résistif qui fait fondre la retenue.
3. **Déploiement** : des charnières à ressort déploient les éléments d'antenne dans leur configuration
   opérationnelle.
4. **Vérification** : le déploiement est confirmé par l'amélioration du RSSI et par la télémesure
   des microcontacts de déploiement.

Le déploiement par fil thermofusible est une opération unique et irréversible. Si le fil thermofusible principal
échoue, un circuit de fil thermofusible redondant est disponible.

### 2.4 L'échelle de débits TM {#24-the-tm-data-rate-ladder}

EOSAT-1 n'a pas « un débit descendant ». Il dispose d'une **échelle** à trois échelons, définie une seule fois dans
`configs/eosat1/subsystems/ttc.yaml` sous `tm_rate_tiers` et lue à cet endroit par le
satellite, la chaîne RF, le planificateur de mission et la console. Chaque échelon a sa propre
modulation, son propre codage et ses propres conditions d'autorisation.

| Palier | Débit | Modulation / codage | Débit symbole | Bande occupée | Usage |
|------|------|---------------------|-------------|-------------|---------|
| SAFE | 1 kbit/s | BPSK, conv(7,1/2)+RS | 1 kBd | 3,1 kHz | Lien de survie pour le chargeur d'amorçage et les contingences (anciennement BEACON, renommé en 2026-08c) |
| LOW | 16 kbit/s | BPSK, conv(7,1/2)+RS | 16 kBd | 49,8 kHz | **Opérations de routine** et repli en mode survie / FDIR |
| HIGH | 128 kbit/s | QPSK, RS(255,223) | 64 kBd | 99,5 kHz | Relecture de la télémesure différée et vidages d'images uniquement |

**LOW (16 kbit/s) est le palier où le satellite se trouve normalement.** C'est le point le plus
important à comprendre au sujet de l'échelle. L'ensemble périodique de données de servitude (SID 1-6)
génère 1378,5 bit/s de paquets PUS, soit 1588 bit/s sur le canal après RS(255,223) et
mise en trames de transfert TM. LOW écoule ce flux avec un taux d'occupation inférieur à 10 % *et* relit environ
0,82 orbite de données de servitude enregistrées en un seul bon passage : un satellite au palier LOW ne
prend donc jamais de retard. Les opérations de routine ne sont en rien dégradées au palier LOW ; l'antenne peut même
être repliée.

**SAFE (1 kbit/s) est un lien de survie, et non un débit d'exploitation.** (Ce échelon s'appelait
BEACON avant 2026-08c : « balise » désigne désormais toujours l'émetteur UHF à antenne fouet, la seconde
radio.) 1000 bit/s est *inférieur* au
débit de génération des données de servitude de 1588 bit/s : un satellite maintenu au échelon SAFE accumule donc un
retard en temps réel qui ne peut jamais se résorber. Ce échelon sert à transmettre le SID 11 (28 octets toutes les 30 s =
7,5 bit/s) depuis le chargeur d'amorçage, avec une réserve de plus de 100x et la bande occupée
la plus étroite possible. On y entre par `TTC_SET_BEACON_MODE` (fonction 70) ou par le
chargeur d'amorçage — jamais par `TTC_SET_DATA_RATE`.

**HIGH (128 kbit/s) se mérite, il ne se sélectionne pas.** À bord, il est refusé sauf si LES DEUX
conditions que le satellite peut lui-même connaître sont satisfaites :

1. l'antenne est déployée (`ttc.antenna_deployed`, 0x0520 = 1) ;
2. le mode DOWNLINK / vidage de la charge utile est actif (`TTC_SET_DOWNLINK_MODE`, fonction 79 ;
   `ttc.downlink_mode`, 0x053C = 1).

Un palier dont les conditions sont ouvertes est **rejeté** avec un échec d'exécution S1.8
(erreur 0x0007), jamais plafonné silencieusement — le texte de l'échec nomme la condition ouverte.
(Tant que le MODE balise est verrouillé — fonction 70 —, tous les paliers sauf SAFE sont refusés
avec le même code 0x0007.)

**La règle d'élévation de 10° est une politique SOL, et non une condition bord**
(2026-08c) : un satellite réel ne connaît pas son élévation vue depuis une
station ; le logiciel de vol ne refuse donc pas HIGH et ne le rétrograde pas en fonction de l'élévation.
La valeur de cette politique se trouve dans `subsystems/ttc.yaml`
`tm_rate_tiers[HIGH].min_elevation_deg` (10°) et elle est appliquée par le
segment SOL : le planificateur de mission programme les vidages en HIGH au-dessus de ce seuil, et la
page de commande du MCS place la commande en attente, à lever par armement explicite, lorsque HIGH est commandé en dessous,
calculée à partir de la géométrie de contact propre au sol. Sous 10°, la physique
continue de s'appliquer honnêtement — l'affaiblissement atmosphérique proportionnel à la cosécante et la dégradation du G/T consomment
une marge réelle et augmentent le TEB observé au sol.

**Commande.** `TTC_SET_DATA_RATE` (service 8, sous-type 1, **fonction 65**) prend un seul code de palier
uint8. L'ancien codage binaire est conservé tel quel : `rate=0` correspond au « bas débit »
et sélectionne LOW, `rate=1` correspond au « haut débit » et sélectionne HIGH. Les procédures existantes et
l'action FDIR `ttc_reduce_power` conservent donc leur sens et aboutissent simplement sur des débits
utilisables.

**Actif ou commandé.** Les conditions agissent sur le palier ACTIF, jamais sur le palier COMMANDÉ.
`ttc.tm_tier_cmd` (0x053A) est ce que le sol a demandé ; `ttc.tm_tier` (0x0539) est ce qui
est réellement émis. Les deux divergent lorsqu'une condition se ferme — le plus souvent lorsqu'un passage descend sous
10° — et convergent de nouveau lorsqu'elle se rouvre, sans nouvelle commande (les fermetures de conditions concernent
l'antenne, le mode DOWNLINK ou le verrou du mode balise — jamais l'élévation). Une console qui n'affiche
que l'un des deux transforme une situation diagnosticable en mystère.

**Débit et marge.** Chaque échelon coûte `10*log10(R2/R1)` d'Eb/N0 : de SAFE à LOW, cela représente
12,04 dB ; de LOW à HIGH, 9,03 dB. Le codage s'y ajoute — conv(7,1/2)+RS apporte 7,5 dB
contre 6,0 dB pour RS(255,223) — de sorte que redescendre de HIGH à LOW fait regagner 9,03 + 1,5 =
10,5 dB au total. Voir `docs/LINK_BUDGET_AND_RATES.md` pour la démonstration et le
tableau par station, ou exécuter `python tools/link_budget_ladder.py`.

### 2.5 Mode paquet de balise {#25-beacon-packet-mode}

Pendant la LEOP et les opérations dans le chargeur d'amorçage, la TTC émet les paquets de balise sur le échelon SAFE
de l'échelle :

| Paramètre          | Valeur                                     |
|--------------------|--------------------------------------------|
| Cadence de la balise | 1 paquet toutes les 30 secondes          |
| Débit              | 1 kbit/s (palier SAFE)                     |
| Débit symbole      | 1 kBd, BPSK, conv(7,1/2)+RS, ~3,1 kHz de bande occupée |
| Contenu            | SID 11 — télémesure minimale de santé de l'OBC |
| Modulation         | BPSK                                       |

Le paquet de balise permet aux stations sol d'acquérir et d'identifier le signal du satellite
lors du premier contact. La balise contient suffisamment d'informations pour évaluer la santé de base du satellite
et engager les commandes de reprise.

## 3. Synthèse du bilan de liaison {#3-link-budget-summary}

### 3.1 Liaison montante (du sol vers le satellite) {#31-uplink-ground-to-spacecraft}

| Paramètre            | Valeur             |
|----------------------|--------------------|
| PIRE de la station sol | 53 dBW           |
| Affaiblissement en espace libre | -164,0 dB (orbite à 513 km, élévation de 10°) |
| Gain d'antenne du satellite | 3 dBi       |
| Température de bruit du système | 800 K   |
| Eb/N0 requis         | 9,6 dB             |
| Marge de liaison (min.) | > 6 dB à 5°     |

### 3.2 Liaison descendante (du satellite vers le sol) {#32-downlink-spacecraft-to-ground}

Calculé par l'outil de bilan de liaison sol à partir des constantes RF de
`subsystems/ttc.yaml`, de sorte que le bilan publié ne peut pas s'écarter des valeurs selon lesquelles
le satellite a été construit.

| Paramètre            | SAFE (1 kbit/s) | LOW (16 kbit/s) | HIGH (128 kbit/s) |
|----------------------|-----------------|---------------|-----------------|
| PIRE (10 dBW + 3 dBi)| 13 dBW          | 13 dBW        | 13 dBW          |
| Affaiblissement en espace libre à 5° | -165,8 dB (2111,7 km) | -165,8 dB | -165,8 dB |
| G/T de la station sol (Iqaluit) | 20 dB/K | 20 dB/K   | 20 dB/K         |
| Codage               | conv(7,1/2)+RS, 7,5 dB | conv(7,1/2)+RS, 7,5 dB | RS(255,223), 6,0 dB |
| Eb/N0 requis (9,6 dB non codé, moins le gain de codage) | 2,1 dB | 2,1 dB | 3,6 dB |
| **Marge de liaison à 5°, Iqaluit** | **57,0 dB** | **45,0 dB** | **34,5 dB** |
| **Marge de liaison à 5°, Troll (station la plus défavorable)** | **55,5 dB** | **43,5 dB** | **33,0 dB** |
| **Marge de liaison au zénith, Iqaluit** | 73,2 dB | 61,2 dB | 50,6 dB |

Deux conséquences en découlent, et toutes deux figurent au programme :

* **Chaque barreau se boucle avec des dizaines de dB de réserve.** À ~513 km d'une parabole polaire professionnelle,
  cette liaison n'est pas limitée en puissance. Ce qui différencie les paliers, c'est la bande occupée,
  la puissance et le coût thermique du PA, la configuration du modem sol et la politique de modes — et non un seuil
  de puissance. La règle des 10° pour HIGH est une politique SOL (programmation par le planificateur + attente
  de commande du MCS), et non le point où la liaison tombe — ni une condition bord.
* **La marge suit néanmoins le débit exactement comme le prévoit le bilan.** LOW est 12,04 dB
  en dessous de SAFE et HIGH est 10,5 dB en dessous de LOW (9,03 dB dus au débit plus 1,5 dB dus au codage).
  Lisez l'échelle sur le terme `-10*log10(R)` : le résultat est correct.

La marge de liaison diminue lorsque l'élévation baisse : l'affaiblissement de propagation augmente, l'affaiblissement atmosphérique est
multiplié par cosec(élévation) en dessous de 30°, et le G/T de la station sol est dégradé par la
captation du bruit du sol et du ciel (-1,5 dB sous 10°, -0,5 dB sous 30°).

## 4. Paramètres de télémesure {#4-telemetry-parameters}

| ID param. | Nom              | Unité  | Description                          |
|----------|-------------------|--------|--------------------------------------|
| 0x0500   | ttc_mode          | enum   | Mode TTC (transpondeur actif)        |
| 0x0501   | link_status       | enum   | État de la liaison (0=pas de liaison, 1=verrouillée) |
| 0x0502   | rssi              | dBm    | Indicateur de puissance du signal reçu |
| 0x0503   | link_margin       | dB     | Marge de liaison actuelle            |
| 0x0506   | tm_data_rate      | kbit/s | Débit descendant TM actuel           |
| 0x0507   | xpdr_temp         | °C     | Température du transpondeur actif    |
| 0x0509   | range_km          | km     | Distance oblique jusqu'à la station sol active |
| 0x050A   | contact_elevation | deg    | Élévation de la station sol active   |

## 5. Contacts avec les stations sol {#5-ground-station-contacts}

| Station    | Latitude   | Longitude  | Élév. min. | Durée type d'un passage |
|------------|------------|------------|-----------|----------------------|
| Iqaluit    | 63,747 N   | 68,518 O   | 5°        | 5–10 min             |
| Troll      | 72,012 S   | 2,535 E    | 5°        | 5–10 min             |
| Svalbard   | 78,230 N   | 15,398 E   | 5°        | 5–10 min             |
| Inuvik     | 68,320 N   | 133,550 O  | 5°        | 5–10 min             |
| O'Higgins  | 63,321 S   | 57,901 O   | 5°        | 5–10 min             |

EOSAT-1 utilise un réseau de cinq stations en bande S, trois dans l'Arctique et deux en
Antarctique. La liste et sa géométrie font foi dans `orbit.yaml` ; les données RF (antenne,
G/T) se trouvent dans `planning/ground_stations.yaml`.

### 5.1 Réseau de stations {#51-station-network}

| Station   | Site                                         | Antenne | G/T     | Contacts par jour | Passage moyen | Priorité du planificateur |
|-----------|----------------------------------------------|---------|---------|--------------|-----------|------------------|
| Svalbard  | KSAT SvalSat, Longyearbyen (Norvège)         | 11,3 m  | 21,5 dB/K | ~13        | 7,8 min   | 100              |
| Troll     | TrollSat, Terre de la Reine-Maud (Antarctique) | 7,3 m | 18,5 dB/K | ~11        | 7,8 min   | 90               |
| Inuvik    | Inuvik Satellite Station Facility (T. N.-O., Canada) | 13,0 m | 22,0 dB/K | ~10,5 | 7,4 min | 80             |
| O'Higgins | DLR GARS O'Higgins, péninsule Antarctique    | 9,0 m   | 20,0 dB/K | ~8         | 7,5 min   | 60               |
| Iqaluit   | Iqaluit Satellite Station Facility (Nunavut, Canada) | 9,0 m | 20,0 dB/K | ~9      | 6,7 min   | 50               |

Les contacts par jour et la durée moyenne des passages sont mesurés sur 48 h à partir de l'époque du TLE
(`tools/pass_gap_analysis.py`) ; un contact dure au plus 10 minutes environ avec le masque de 5°.

### 5.2 Rôle des stations {#52-station-roles}

Toutes les stations ont le même rôle : TT&C en bande S (liaison montante 2025 MHz / liaison descendante 2200 MHz) et
vidage des données. Aucune station n'est spécialisée ; lorsque deux contacts sont en concurrence, le planificateur les classe
selon la colonne de priorité ci-dessus :

- **Svalbard** (78,230° N) voit le plus de passages et les élévations les plus hautes (élévation maximale
  médiane ~39°) : c'est la station polaire principale de transmission au sol.
- **Troll** (72,012° S) en est le pendant dans l'hémisphère Sud.
- **Inuvik** (68,320° N) et **Iqaluit** (63,747° N) couvrent les passages Nord aux longitudes ouest
  et est de l'Arctique canadien.
- **O'Higgins** (63,321° S) complète les passages Sud à l'ouest de Troll.

Avec les cinq stations, l'intervalle le plus long entre deux contacts est d'environ 80 minutes, contre environ
2,5 heures avec Iqaluit et Troll seules.

### 5.3 Bilan de liaison par station {#53-per-station-link-budget}

La marge de liaison varie d'une station à l'autre par le G/T ; la géométrie de distance oblique est la même pour toutes
(`tools/link_budget_ladder.py`) :

| Paramètre             | Iqaluit | Troll   | Svalbard | Inuvik  | O'Higgins |
|-----------------------|---------|---------|----------|---------|-----------|
| Marge à 5°, palier HIGH  | 34,5 dB | 33,0 dB | 36,0 dB | 36,5 dB | 34,5 dB |
| Marge à 10°, palier HIGH | 38,6 dB | 37,1 dB | 40,1 dB | 40,6 dB | 38,6 dB |
| Affaiblissement en espace libre (513 km, élévation de 10°) | -164,0 dB | -164,0 dB | -164,0 dB | -164,0 dB | -164,0 dB |

Troll est la station la plus défavorable. EOSAT-1 bénéficie typiquement d'environ 51 contacts sol par jour sur l'ensemble
des cinq stations, soit environ 385 minutes de contact pour la liaison montante des télécommandes et la liaison descendante
de la télémesure et des données, avec un intervalle médian d'environ 33 minutes entre deux contacts
(`tools/pass_gap_analysis.py`, 48 h à partir de l'époque du TLE).

## 6. Commandes {#6-commands}

| Commande              | Service  | Paramètres | Description                          |
|-----------------------|----------|------------|--------------------------------------|
| TTC_SWITCH_PRIMARY    | S8,S1    | —          | Activer le transpondeur principal    |
| TTC_SWITCH_REDUNDANT  | S8,S1    | —          | Activer le transpondeur redondant    |
| TTC_SWITCH_OTHER      | S8,S1    | —          | Activer l'équipement non sélectionné (à l'aveugle ; action de FDIR TTC-01) |
| HK_REQUEST            | S3,S27   | sid=5      | Demander le paquet de servitude TTC  |
| GET_PARAM             | S20,S3   | param_id   | Lire un paramètre TTC individuel     |
| SET_PARAM             | S20,S1   | param_id, value | Modifier un paramètre de configuration TTC |

### 6.1 Procédure de basculement de transpondeur {#61-transponder-switchover-procedure}

1. Vérifier la santé du transpondeur actuel par `HK_REQUEST` (sid=5).
2. Envoyer la commande `TTC_SWITCH_REDUNDANT` (ou `TTC_SWITCH_PRIMARY`).
3. Attendre la mise en température du transpondeur (environ 30 secondes).
4. Confirmer la réacquisition de la liaison par `link_status` (0x0501) = 1.
5. Vérifier que `rssi` et `link_margin` restent dans des bornes acceptables.

**Remarque :** un basculement de transpondeur provoque une interruption temporaire de la liaison de 20 à 40 secondes.
Programmer les commandes de basculement en conservant un temps de contact restant suffisant.

## 7. Remarques d'exploitation {#7-operational-notes}

1. Le sous-système TTC ne passe pas en réception seule pendant le mode survie du satellite.
   L'émission de la télémesure se poursuit sur le palier LOW (16 kbit/s) — le `safe_tier`
   configuré. Le mode survie ne vous prive pas des données de servitude ; il vous prive de la possibilité
   d'effectuer des vidages.
2. Le récepteur GPS de bord fournit les données de position et de vitesse pour la restitution d'orbite,
   complétées par des mesures de distance (0x0509) pendant les contacts sol.
3. Des valeurs de RSSI inférieures à -100 dBm indiquent des conditions de liaison marginales. Les opérations devraient être
   limitées aux commandes de haute priorité lorsque le RSSI est faible. Descendre l'échelle jusqu'à LOW
   (`TTC_SET_DATA_RATE(rate=0)`), ce qui fait regagner 10,5 dB.
4. La température du transpondeur (0x0507) devrait rester entre 0 et 50 °C en fonctionnement.
   La protection thermique est assurée par des moyens passifs (radiateur TCS et MLI).
5. La télémesure enregistrée et les données de la charge utile sont transmises au sol pendant les contacts sur le palier HIGH
   (128 kbit/s), dans lequel il faut entrer délibérément : d'abord le mode DOWNLINK, puis le débit.
   La télémesure HK en temps réel est entrelacée avec les données enregistrées. Une image de 4 Mio représente 262 s de
   canal au palier HIGH — 328 s avec la provision protocolaire de 20 % du planificateur de mission, soit environ
   les trois quarts d'un passage moyen : un vidage est donc une activité programmée, et non une
   opération improvisée.
6. Le canal de commande PDM dédié garantit que le récepteur reste alimenté même lorsque la
   minuterie d'extinction automatique de l'émetteur arrive à échéance. C'est voulu — le satellite est toujours
   commandable.
7. Après le déploiement de l'antenne (fil thermofusible), vérifier l'amélioration du RSSI par rapport aux niveaux
   antérieurs au déploiement. Une amélioration marginale peut indiquer un déploiement incomplet.
8. Lors du premier contact en LEOP, s'attendre à des paquets de balise sur le palier SAFE (1 kbit/s, 1 kBd,
   BPSK conv(7,1/2)+RS). Configurer le démodulateur sol pour 1 kBd avant l'AOS, puis le
   reconfigurer pour 16 kBd immédiatement après le démarrage de l'application, lorsque le palier
   `default_tier` (LOW) de l'échelle devient actif — le démodulateur de balise ne se verrouillera pas sur 16 kbit/s.

## 8. Modes de défaillance {#8-failure-modes}

| Défaillance                 | Détection                   | Réaction                        |
|-----------------------------|-----------------------------|---------------------------------|
| Défaillance du transpondeur sélectionné (principal ou redondant) | Aucune télécommande valide depuis > 24 h (`cmd_loss_switch_timeout_s`) | Basculement sur l'autre équipement, puis de nouveau toutes les 24 h jusqu'à l'acceptation d'une TC (FDIR TTC-01, voir `08_fdir.md` §4.5) |
| Dégradation du RSSI         | rssi < -105 dBm (`cmd_loss_rssi_threshold_dbm`) | Passage au bas débit, analyse   |
| Échec du déploiement de l'antenne | Aucun RSSI après la fusion du fil | Essayer le circuit de fil thermofusible redondant |
| Extinction automatique du TX (minuterie de 15 min) | Aucune liaison descendante, RX toujours actif | Comportement attendu ; envoyer une commande pour réactiver le TX |
| Aucune TM d'aucune station | Deux stations ou plus, l'une après l'autre, ne signalent aucun signal | Analyser l'attitude ; vérifier la santé du transpondeur |

---

*Fin du document — EOSAT1-UM-TTC-006*
