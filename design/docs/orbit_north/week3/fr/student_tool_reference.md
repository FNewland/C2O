---
title: "Référence MCS et MPS pour les étudiants"
subtitle: "ORBIT NORTH · aide-mémoire des outils d'exploitation, semaine 3"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants"
expected-reading: "Sections 1 – 4 avant la journée de formation 2 ; sections 5 – 7 avant la journée LEOP du mercredi"
---

# Référence MCS et MPS pour les étudiants

Ce document est la référence de l'opérateur pour les deux outils que vous
utiliserez pendant la semaine 3 d'ORBIT NORTH :

- **MCS** — le système de contrôle de mission (télémesure, commande,
  panneau de procédures, panneau FDIR) ;
- **MPS** — le système de planification de mission (cibles de prise de vue, planification
  des passages, détection des conflits).

Vous n'avez **pas** besoin de savoir comment fonctionne le simulateur sous-jacent.
Vous **devez** en revanche maîtriser les interfaces du MCS et du MPS.

---

## 1. La console en un coup d'œil

La console par défaut est le MCS *moderne* (`smo-mcs --ui modern` ;
`--ui classic` sert l'ancienne disposition que décrit le manuel du cours,
partie 2, §7.1). Elle comporte quatre zones :

- **Barre supérieure** — l'étiquette de mission (EO1 · EOSAT-1) ; trois
  horloges (UTC, MET et heure bord), avec une pastille TRAINING car l'horloge
  sol est l'heure du simulateur ; le sélecteur POSITION ; le bouton des
  alarmes avec le nombre d'alarmes non acquittées ; DELAYED TM et REPORTS ;
  les bascules GUIDED (annotations pédagogiques numérotées), GREY (contrôle en
  niveaux de gris) et THEME ; le sélecteur EN/FR, l'aide et le témoin de
  connexion. En dessous, le bandeau de situation répond à quatre questions :
  *Je le vois ?*, *Je lui parle ?*, *Va-t-il bien ?* et *Et ensuite ?*
- **Rail de navigation** (à gauche) — OVR, EPS, TCS, AOC, TTC, PLD, PRP, OBD,
  puis CMD, FDR, PRC, TRD, PUS et MAN. Votre poste détermine les boutons
  affichés (§1.1) ; le directeur de vol les voit tous.
- **Zone de travail** (au centre) — la page choisie sur le rail :
  synoptiques et mosaïques de télémesure, commande, procédures, FDIR,
  tendances.
- **Tiroir inférieur** — EVENTS (avec un filtre de gravité), TM PACKETS,
  CMD HISTORY, LOG (journal de console avec NOTE et MARK), HANDOVER et
  GO/NO-GO (le tour de table du FD).

> **À FAIRE (auteur) :** Réaliser une capture d'écran annotée de la vue par
> défaut du directeur de vol dans le MCS moderne et la placer ici, en
> identifiant les quatre zones ci-dessus.

### 1.1 Onglets propres à chaque poste

Chaque poste du MCS dispose d'un jeu d'onglets visibles différent, défini dans
`mcs/positions.yaml`. Référence rapide :

| Poste | Onglets visibles |
|----------|-------------|
| Directeur de vol | system_dashboard, power_monitor, fdir_panel, contact_schedule, procedure_panel, overview, eps, aocs, tcs, obdh, ttc, payload, prop, commanding, pus, procedures, trends, manual |
| Puissance et thermique | overview, eps, tcs, commanding, procedures, trends, manual |
| Dynamique du vol | overview, aocs, prop, commanding, procedures, trends, manual |
| TT&C | overview, ttc, commanding, procedures, trends, manual |
| Opérations charge utile | overview, payload, commanding, procedures, trends, manual |
| FDIR / systèmes | overview, obdh, commanding, pus, procedures, trends, manual |
| Propulsion | overview, prop, tcs, commanding, procedures, trends, manual |

L'onglet overview est toujours présent afin que chaque poste partage la même
conscience de la situation ; les onglets propres au poste sont ceux où vous faites
votre travail.

L'aide-mémoire imprimable est le tableau 7.2 du manuel du cours, partie 2,
§7.2. Voir un onglet n'est pas pouvoir commander depuis cet onglet :
`allowed_services` et `allowed_func_ids` dans `positions.yaml` déterminent
les boutons de commande actifs ; ainsi, la dynamique du vol voit l'onglet
PROP mais ne peut pas commander de poussée.

---

## 2. Lire la télémesure

La télémesure arrive dans des structures de housekeeping (SID) définies
dans `telemetry/hk_structures.yaml` ; chaque paramètre a un mnémonique et
un identifiant hexadécimal dans `telemetry/parameters.yaml` (par exemple
`eps.bat_soc`, 0x0101). Seuls les SID 1 (EPS) et 11 (balise) sont actifs à
l'amorçage de l'application ; les autres exigent `HK_ENABLE` (S3.5). Un
affichage *not enabled* n'est pas une panne de liaison.

La couleur provient de `mcs/limits.yaml` : vert dans la plage nominale,
jaune dans la plage de vigilance (l'annoncer sur la boucle), rouge dans la
plage d'alarme (une règle FDIR se déclenche en général au même moment).
L'obsolescence est un indicateur distinct, calculé pour chaque paramètre à
partir de la cadence du SID qui le porte (`mcs/staleness.yaml`) : valeur
fraîche tant que son âge reste inférieur à max(10 s, 0.9 × intervalle),
dégradée sous max(20 s, 1.5 × intervalle), obsolète au-delà. Une valeur du
SID 3 (TCS, 60 s) n'est donc pas obsolète au bout de 15 s. Obsolète signifie
*je ne connais pas la valeur*, et non *la valeur est mauvaise*.

La page TRD (Trends) trace les valeurs archivées d'un paramètre en fonction
du temps. Détails complets : manuel du cours, partie 2, §7.1 (mosaïque de
télémesure et indicateurs d'état) et §15.1 (référence condensée de la
télémesure par sous-système).

---

## 3. Envoyer une commande

Il existe deux voies. **Pilotée par procédure** (recommandée) : exécuter la
fiche depuis la page PRC (Procedures) ; chaque étape **TC** porte sa commande
et ses arguments, et le panneau remplit les champs de la commande.
**Directe** : construire la commande sur la page CMD — choisir le service ou
la fonction S8, remplir les champs d'arguments typés (Tab pour passer de l'un
à l'autre, Entrée pour envoyer). Le manuel du cours, partie 2, §7.8, indique
quand chaque voie convient.

Les sept services que vous verrez le plus (`mcs/pus_services.yaml`) :
**S1** vérification — acceptation (1.1), début (1.3), fin d'exécution (1.7)
ou échec (1.2, 1.8) de chaque TC ; **S3** housekeeping — activer (3.5) et
demander (3.27) un SID ; **S5** comptes rendus d'événements ; **S8** gestion
des fonctions — chaque fonction de sous-système est un S8.1 avec un func_id,
par ex. `OBC_BOOT_APP` (func 55) ; **S9** temps — `SET_TIME` (9.1) ; **S11** le
planning de bord à étiquette temporelle ; **S17** le test de connexion (17.1,
auquel répond 17.2). L'introduction complète se trouve au §7.6.

Les commandes critiques exigent deux clés : le poste responsable arme
(première clé) la commande, le FD donne le GO, et seulement ensuite la
commande part ; la page CMD n'envoie pas une commande critique qui n'a pas
été armée.

Refus fréquents : un argument hors plage ou manquant (refusé avec un motif,
et non tronqué en silence) ; une commande hors de la liste autorisée du
chargeur d'amorçage alors que `obdh.sw_image` = 0 ; une fonction que votre
poste n'a pas le droit d'utiliser (`allowed_func_ids`) ; et l'absence de
liaison — les commandes ne montent que pendant un contact.

---

## 4. Le panneau de procédures

Le manuel du cours, partie 2, §7.4, décrit le panneau en détail. En bref :

- **Charger** une fiche depuis la page PRC par son identifiant ou son titre ;
  elle devient la procédure active du quart.
- **Étapes** : elles suivent le fichier ; chaque étiquette **TC**, **Action**,
  **Verify** et **Note** devient une ligne du panneau. Le responsable est le
  poste figurant dans les `required_positions` de la fiche.
- **Exécuter** une étape à la fois : l'annoncer sur la boucle, obtenir le GO
  du FD, envoyer, relire la vérification, marquer l'étape comme vérifiée.
- **Sauter** (*skip*) n'est permis que si la télémesure montre déjà l'état final
  de l'étape, et le saut est consigné avec cette valeur. **Suspendre** (*hold*)
  est permis pendant que l'équipe évalue ; le FD autorise la reprise. Tout le
  reste est une violation de procédure.
- Chaque étape, saut et suspension est horodaté dans le journal de console
  (tiroir inférieur, LOG), qui est la trace utilisée au débriefing.

---

## 5. Le panneau FDIR

Le manuel du cours, partie 2, §7.5, décrit le panneau en détail. Les règles
proviennent de `monitoring/s12_definitions.yaml` (46 surveillances S12 : ce
qui est surveillé, seuil et persistance) et de `monitoring/s19_rules.yaml`
(32 règles événement-action S19 : ce que le satellite fait de lui-même). Le
panneau liste les déclenchements actifs avec leur couleur de gravité, leur
heure de déclenchement et leur sous-système ; les niveaux 3 et 4 affichent
le bandeau rouge.

- **Acquitter** indique que vous l'avez vu et coupe l'alerte ; le paramètre
  reste hors plage. Dans le MCS moderne, **A** ouvre le tiroir des alarmes et
  **K** acquitte la première alarme non acquittée de la liste.
- **Effacer** n'est possible qu'une fois le paramètre revenu dans sa plage,
  et toujours après une fiche d'anomalie.
- La **gravité** FDIR (0–4) et le **niveau d'autonomie** de bord (0–3) sont
  des échelles différentes ; ne pas les confondre.
- **Forçage manuel** (désactiver une règle) : exige l'autorisation du FD, par
  exemple pendant un étalonnage hors plage planifié ; la règle reste grisée
  jusqu'à sa réactivation.

Une fiche d'anomalie consigne l'heure du premier indice, le paramètre et sa
valeur, la règle déclenchée, la procédure exécutée et le résultat ; elle est
versée au journal de quart.

---

## 6. Le système de planification de mission (MPS)

Le MPS est une application web distincte à `http://localhost:9091/`
(disposition large à `/wide`) ; le manuel du cours, partie 2, §7.3, décrit
ses cinq panneaux, et le §8.5 est l'exercice du jour 1.

- **Sélecteur de cibles** — les cibles de courants océaniques de
  `planning/imaging_targets.yaml` (`OCM-001` Gulf Stream, `OCM-002`
  Kuroshio, …), chacune une boîte lat/lon avec une priorité, un intervalle de
  revisite et un seuil `min_solar_elevation_deg`. Les bandes se règlent par
  acquisition (`PAYLOAD_SET_BAND_CONFIG`), et non par cible.
- **Types d'activité** — les dix types de
  `planning/activity_types.yaml` (`imaging_pass`, `data_dump`,
  `calibration`, `housekeeping_collection`, `software_upload`,
  `momentum_desaturation`, `thermal_rebalance`, `load_shedding`,
  `fdir_recovery`, `orbit_manoeuvre`), chacun avec sa puissance, son profil
  thermique, son pointage et sa durée.
- **Planning des stations sol** — 24 h de passages sur les cinq stations :
  AOS, élévation maximale, LOS, durée. Un passage qui ne dépasse jamais 10°
  ne porte aucun vidage en palier HIGH.
- **Vérificateur de conflits** — temps de basculement, puissance, enveloppe
  thermique et pointage ; rouge pour les conflits, jaune pour les
  avertissements.
- **Export du plan** — le plan préparé devient des commandes S11 à étiquette
  temporelle (`SCHEDULE_TC`, S11.4) que l'OBC exécute ; les activités liées à
  des procédures (NOM-002, NOM-003, NOM-004, NOM-009) peuvent ensuite être
  exécutées depuis la page Procedures du MCS.

---

## 7. Boucle vocale et messagerie du MCS

Le manuel du cours, partie 2, chapitre 9, fait référence ; le §1 de la
journée de formation 2 en est l'entraînement.

- **Boucle vocale.** Un casque de téléphonie logicielle par poste sur un même
  canal de conférence. Nommer d'abord la station appelée, puis soi-même, puis
  le message : « FD, AOCS — … ». Alternat par défaut ; seul le FD peut passer
  en micro ouvert pour une séquence critique, et il l'annonce sur la boucle.
- **Messagerie et journal du MCS.** Les réserver aux notes de faible priorité,
  aux valeurs à recopier et aux points de passation. N'y mettre jamais une
  intention de commande ni un GO : un GO n'est valable que sur la boucle.
- **Traçabilité.** La boucle est enregistrée pour le débriefing, et chaque
  NOTE, MARK, tour de table GO/NO-GO et étape de procédure du journal de
  console est horodaté.

---

## 8. Raccourcis clavier rapides

Voici les raccourcis présents dans le code du MCS livré (console moderne ;
la console classique possède les cinq premiers). Les touches de lettre sont
sans effet pendant la saisie dans un champ.

| Raccourci | Action |
|----------|--------|
| `?` | Afficher ou masquer le panneau d'aide |
| `Esc` | Fermer l'aide, la vue en chaîne ou le tiroir des alarmes ; sinon, revenir à la page Overview |
| `F6` | Passer le focus à la zone suivante (barre supérieure → rail → zone de travail → tiroir inférieur) |
| `←` `→` (`↑` `↓`) sur le rail | Page précédente ou suivante |
| `Enter` dans un champ de commande | Envoyer la commande (une commande critique doit d'abord être armée) |
| `A` | Ouvrir le tiroir des alarmes |
| `K` | Acquitter la première alarme non acquittée de la liste |
| `Enter` dans la zone de passation | Ajouter la note de passation |
| `Enter` dans la zone du journal | Publier la note au journal |
| `Tab` dans le tiroir des alarmes ouvert | Parcourir ses commandes |

Il n'existe ni sélecteur global de commande rapide ni raccourci de focus par
touche de fonction en dehors de `F6`. Le manuel du cours, partie 2, §7.9,
précise que la carte de référence de l'installation prévaut là où elle
diffère.

---

## 9. Pour aller plus loin

| Sujet | Fichier source dans le simulateur |
|-------|--------------------------|
| Manuels des sous-systèmes (contexte) | `configs/eosat1/manual/0*.md` |
| Analyses des rôles par poste | `configs/eosat1/mcs/role_analysis/*.md` |
| Paramètres de télémesure | `configs/eosat1/telemetry/parameters.yaml` |
| Limites de télémesure | `configs/eosat1/mcs/limits.yaml` |
| Index des procédures | `configs/eosat1/procedures/procedure_index.yaml` |
| Règles FDIR | `configs/eosat1/monitoring/s19_rules.yaml` |

Références externes :

- ECSS-E-ST-70-11C — *Space segment operability* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- ECSS-E-ST-70-32C — *Test and operations procedures* —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/
- CCSDS *Packet Utilization Standard* (PUS) —
  https://public.ccsds.org/Pubs/660x0g3.pdf
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
