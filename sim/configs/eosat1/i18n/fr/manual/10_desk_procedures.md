# 10. Affectation des procédures par poste

Cette section affecte chaque procédure de recette en orbite et de contingence à un
poste opérateur précis et définit, pour chacune, les annonces GO/NO-GO requises.

## Postes opérateurs

| ID du poste      | Nom de la console  | Sous-systèmes           | ID de fonction S8 |
|------------------|--------------------|-------------------------|-------------------|
| flight_director  | Direction de vol   | Tous (supervision)      | Toutes            |
| eps_tcs          | Puissance et thermique | EPS, TCS            | 16-25, 40-49, 81-82 |
| aocs             | Dynamique du vol   | AOCS                    | 0-15              |
| ttc              | TT&C               | TTC                     | 63-78             |
| payload_ops      | Opérations charge utile | Charge utile       | 26-39             |
| fdir_systems     | FDIR / Systèmes    | OBDH, FDIR, inter-systèmes | 50-62, 80      |

---

## Procédures de recette en orbite par poste

### Direction de vol (coordination d'ensemble)

Le directeur de vol est maître de la chronologie de recette en orbite et autorise chaque
jalon GO/NO-GO. Il n'exécute pas lui-même d'étapes, sauf mention contraire ci-dessous.

### eps_tcs — Puissance et thermique

| ID proc.  | Titre                        | Pilote | Appui     | GO/NO-GO FD |
|-----------|------------------------------|------|-------------|-------------|
| COM-001   | Vérification de l'EPS | eps_tcs | fdir_systems | OUI — avant l'essai d'éclipse, après le calcul du bilan de puissance |
| COM-002   | Vérification du TCS          | eps_tcs | payload_ops | OUI — avant les essais d'activation des réchauffeurs |
| COM-010   | Activation du refroidisseur du FPA | eps_tcs | payload_ops | OUI — avant l'activation du refroidisseur (impact sur la puissance) |

**COM-001 — Vérification de l'EPS**
- **Pilote :** eps_tcs (ingénieur EPS)
- **Appui :** fdir_systems surveille l'état de l'OBC pendant les transitoires de charge
- **GO/NO-GO FD requis :**
  1. Avant l'essai de charge transitoire de la charge utile (étape 7)
  2. Après le calcul du bilan de puissance moyenne sur l'orbite — le FD confirme une marge positive
- **Télémesure clé :** bus_voltage (0x0105), bat_soc (0x0101), power_gen (0x0107), power_cons (0x0106)
- **Annoncer sur la boucle opérations :** tension du bus, SoC, marge de puissance à chaque jalon GO/NO-GO

**COM-002 — Vérification du TCS**
- **Pilote :** eps_tcs (ingénieur TCS)
- **Appui :** payload_ops pour le contrôle de la température de référence du FPA
- **GO/NO-GO FD requis :**
  1. Avant l'essai d'activation du réchauffeur de batterie
  2. Avant l'essai d'activation du réchauffeur de l'OBC
  3. Après l'évaluation du profil thermique sur l'orbite
- **Télémesure clé :** temp_obc (0x0406), temp_battery (0x0407), temp_fpa (0x0408), états des réchauffeurs (0x040A-0x040C)

**COM-010 — Activation du refroidisseur du FPA**
- **Pilote :** eps_tcs (ingénieur TCS)
- **Appui :** payload_ops surveille la convergence de la température du FPA
- **GO/NO-GO FD requis :**
  1. Avant l'activation du refroidisseur — confirmer que le bilan de puissance absorbe une charge supplémentaire de +15 W
  2. Après la courbe de mise en froid — confirmer que la consigne de −15 °C est atteinte et stable
- **Télémesure clé :** fpa_temp (0x0601), bus_voltage (0x0105), bat_soc (0x0101)
- **Durée :** 45 minutes ou plus pour une mise en froid complète — peut s'étendre sur plusieurs passages

---

### aocs — Dynamique du vol

| ID proc.  | Titre                        | Pilote | Appui     | GO/NO-GO FD |
|-----------|------------------------------|------|-------------|-------------|
| COM-003   | Étalonnage des capteurs SCAO | aocs | fdir_systems | OUI — avant la fermeture de la boucle sur le senseur stellaire |
| COM-004   | Vérification des actionneurs SCAO | aocs | eps_tcs     | OUI — avant chaque mise en rotation de roue |
| COM-005   | Transitions de modes SCAO     | aocs | tous les postes | OUI — avant le mode OFF (perte de contrôle), avant le maintien en FINE_POINT |

**COM-003 — Étalonnage des capteurs SCAO**
- **Pilote :** aocs (ingénieur SCAO)
- **Appui :** fdir_systems pour la référence de temps OBDH
- **GO/NO-GO FD requis :**
  1. Avant la fermeture de la boucle sur le senseur stellaire — l'attitude peut faire un saut
  2. Après l'étalonnage du biais des gyromètres — confirmer que les valeurs de biais sont acceptables
- **Télémesure clé :** rates (0x0204-0x0206), att_error (0x0217), st_status (0x0240), css_valid (0x0248)
- **Durée :** gyromètres 5 min + magnétomètre 10 min + acquisition du senseur stellaire 2 min

**COM-004 — Vérification des actionneurs SCAO (roues de réaction + magnétocoupleurs)**
- **Pilote :** aocs (ingénieur SCAO)
- **Appui :** eps_tcs surveille la tension du bus pendant les transitoires de mise en rotation
- **GO/NO-GO FD requis :**
  1. Avant chaque essai de roue — confirmer que l'attitude est stable
  2. Après l'essai des 4 roues — confirmer que la désaturation fonctionne
- **Télémesure clé :** rw_speed (0x0207-0x020A), rw_temp (0x0218-0x021B), att_error (0x0217)

**COM-005 — Transitions de modes SCAO**
- **Pilote :** aocs (ingénieur SCAO)
- **Appui :** tous les postes observent pendant l'essai du mode OFF (le satellite va dériver)
- **GO/NO-GO FD requis :**
  1. Avant de commander le mode 0 (OFF) — critique : satellite non contrôlé pendant 30 s.
     Il n'existe pas de mode IDLE ; les codes sont 0 OFF, 1 SAFE_BOOT, 2 DETUMBLE,
     3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL
  2. Avant le mode FINE_POINT — vérifier que l'attitude est prête pour les opérations de prise de vue
  3. Après la matrice complète des modes — confirmer que toutes les transitions sont nominales
- **Annoncer sur la boucle opérations :** transition de mode + erreur d'attitude à chaque étape

---

### ttc — TT&C

| ID proc.  | Titre                        | Pilote | Appui     | GO/NO-GO FD |
|-----------|------------------------------|------|-------------|-------------|
| COM-006   | Vérification de la liaison TTC | ttc  | fdir_systems | OUI — avant l'essai du transpondeur redondant |

**COM-006 — Vérification de la liaison TTC**
- **Pilote :** ttc (ingénieur TT&C)
- **Appui :** fdir_systems pour la vérification du compteur de TC de l'OBC
- **GO/NO-GO FD requis :**
  1. Avant le basculement sur le transpondeur redondant — brève interruption de la télémesure
  2. Après la comparaison avec le bilan de liaison — confirmer que les deux transpondeurs sont sains
- **Télémesure clé :** link_status (0x0501, LOCKED = **2**), rssi (0x0502),
  link_margin (0x0503), ber (0x050C), carrier_lock (0x0510),
  tx_fwd_power (0x050D), tx_active (0x0525), tx_gate_status (0x052B),
  antenna_deployed (0x0520), beacon_mode (0x0521)

---

### fdir_systems — FDIR / Systèmes

| ID proc.  | Titre                        | Pilote | Appui     | GO/NO-GO FD |
|-----------|------------------------------|------|-------------|-------------|
| COM-007   | Vérification de l'OBDH       | fdir_systems | eps_tcs | OUI — avant la transition en mode NOMINAL |
| COM-008   | Configuration et essai de la FDIR | fdir_systems | TOUS les postes | OUI — avant l'injection de panne contrôlée (TOUS les postes en console) |

**COM-007 — Vérification de l'OBDH**
- **Pilote :** fdir_systems (ingénieur OBDH)
- **Appui :** eps_tcs surveille la puissance pendant les transitions de mode
- **GO/NO-GO FD requis :**
  1. Avant la transition de mode SAFE→NOMINAL
  2. Après la vérification des compteurs de TC/TM
- **Télémesure clé :** mode (0x0300), cpu_load (0x0302), reboot_count (0x030A), sw_image (0x0311)

**COM-008 — Configuration et essai de la FDIR**
- **Pilote :** fdir_systems (ingénieur FDIR)
- **Appui :** TOUS les postes doivent être en console — le mode survie affecte tous les sous-systèmes
- **GO/NO-GO FD requis :**
  1. Avant l'abaissement contrôlé des seuils — TOUS les postes confirment être prêts
  2. Avant la reprise après le mode survie — confirmer que tous les sous-systèmes ont réagi comme prévu
  3. Après la reprise — confirmer l'absence d'effet résiduel sur tous les sous-systèmes
- **Critique :** c'est la seule procédure de recette en orbite qui mobilise TOUS les postes simultanément.
  Chaque poste confirme que son sous-système est correctement passé en mode survie et en est revenu.

---

### payload_ops — Opérations charge utile

| ID proc.  | Titre                        | Pilote | Appui     | GO/NO-GO FD |
|-----------|------------------------------|------|-------------|-------------|
| COM-009   | Mise sous tension de la charge utile | payload_ops | eps_tcs | OUI — avant la mise sous tension (impact sur le bilan de puissance) |
| COM-012   | Acquisition de la première lumière | payload_ops | aocs | OUI — avant la prise d'image (FINE_POINT confirmé) |
| COM-011   | Étalonnage radiométrique de la charge utile | payload_ops | aocs | OUI — avant la prise de vue au survol du site d'étalonnage |

**COM-009 — Mise sous tension de la charge utile**
- **Pilote :** payload_ops (ingénieur charge utile)
- **Appui :** eps_tcs confirme le bilan de puissance et surveille le bus pendant l'amorçage
- **GO/NO-GO FD requis :**
  1. Avant la mise sous tension de la charge utile — eps_tcs confirme une marge suffisante
  2. Après l'autotest — payload_ops confirme que le micrologiciel et les interfaces sont nominaux
- **Télémesure clé :** payload_mode (0x0600), fpa_temp (0x0601), bus_voltage (0x0105)

**COM-012 — Acquisition de la première lumière**
- **Pilote :** payload_ops (ingénieur charge utile)
- **Appui :** aocs confirme la stabilité en FINE_POINT
- **GO/NO-GO FD requis :**
  1. Avant la transition en FINE_POINT — aocs confirme que l'attitude est prête
  2. Avant la prise d'image — confirmer la température du FPA, le pointage, la capacité de stockage
  3. Après la descente de l'aperçu — payload_ops évalue la qualité de l'image
- **Annoncer sur la boucle opérations :** « First light capture complete » avec l'évaluation de la qualité

**COM-011 — Étalonnage radiométrique de la charge utile**
- **Pilote :** payload_ops (ingénieur étalonnage)
- **Appui :** aocs pour le pointage nadir en FINE_POINT sur le site d'étalonnage
- **GO/NO-GO FD requis :**
  1. Avant l'acquisition des images d'obscurité — charge utile dans l'état correct
  2. Avant la prise de vue du site d'étalonnage — pointage AOCS confirmé, site d'étalonnage en visibilité
- **Durée :** procédure sur plusieurs passages — images d'obscurité + survol du site d'étalonnage + descente

---

## Procédures de contingence par poste

### eps_tcs — Contingences puissance et thermique

| ID proc.      | Titre                            | Pilote   | Appui        | GO/NO-GO FD | Critique en temps |
|---------------|----------------------------------|----------|--------------|-------------|---------------|
| CTG-005       | Reprise après mode survie EPS    | eps_tcs  | tous les postes | OUI — à chaque étape de rétablissement de charge | Non (reprise à rythme maîtrisé) |
| CTG-009       | Dégradation du générateur solaire | eps_tcs  | aocs         | OUI — si une réduction du rapport cyclique de la charge utile est nécessaire | Non |
| CTG-023       | Délestage progressif             | eps_tcs  | tous les postes | OUI — à chaque niveau de délestage | OUI — compte à rebours d'éclipse |
| CTG-024       | Conduite à tenir sur perte de panneau solaire | eps_tcs  | aocs         | OUI — si une optimisation de l'attitude est nécessaire | Non |
| CTG-012 | Traitement d'une surintensité | eps_tcs  | poste concerné | OUI — avant la remise à zéro de l'indicateur OC | OUI — contrôle de stabilité de 30 s |
| CTG-001 | Délestage sur sous-tension    | eps_tcs  | tous les postes | OUI — à chaque étape de délestage/rétablissement | OUI — tension du bus en baisse |
| CTG-013 | Défaillance d'un élément de batterie | eps_tcs  | fdir_systems | OUI — avant l'entrée en éclipse si la marge est négative | OUI — calage sur l'éclipse |
| CTG-004       | Dépassement de limite thermique  | eps_tcs  | poste concerné | OUI — avant activation d'un réchauffeur ou arrêt de la charge utile | Non (surveillance de 15 min) |
| CTG-006       | Anomalie thermique charge utile/FPA | eps_tcs  | payload_ops  | OUI — avant le redémarrage de la charge utile | Non (minuterie de mise en froid) |

**Schéma de coordination clé :** eps_tcs pilote toutes les contingences puissance/thermique. Pendant
un délestage (CTG-023, CTG-001), chaque poste concerné doit acquitter
avant que ses équipements ne soient délestés, et le FD autorise chaque niveau.

**Annonces du délestage progressif (CTG-023) :**
1. SoC < 50 % : eps_tcs → payload_ops : « Payload OFF. » GO du FD.
2. SoC < 35 % : eps_tcs → payload_ops : « FPA Cooler OFF. » GO du FD.
3. SoC < 25 % : eps_tcs → ttc : « TX OFF — loss of downlink. » GO du FD.
4. SoC < 15 % : eps_tcs → aocs : « Wheels OFF — loss of pointing. » GO du FD.
5. Sortie d'éclipse : rétablir dans l'ordre inverse, à 5 min d'intervalle, avec un GO du FD à chaque étape.

---

### aocs — Contingences dynamique du vol

| ID proc.      | Titre                            | Pilote | Appui        | GO/NO-GO FD | Critique en temps |
|---------------|----------------------------------|------|--------------|-------------|---------------|
| CTG-002       | Reprise après anomalie SCAO      | aocs | eps_tcs      | OUI — si 2 roues ou plus sont défaillantes | OUI — attitude en dégradation |
| CTG-007       | Anomalie de palier/vitesse de roue de réaction | aocs | eps_tcs      | OUI — avant la désactivation de la roue | OUI — risque sur l'attitude |
| CTG-025       | Défaillance en cascade des capteurs SCAO | aocs | payload_ops  | OUI — décision sur le mode de repli | OUI — commutation de capteurs |
| CTG-026       | Reprise d'une roue de réaction bloquée | aocs | fdir_systems | OUI — avant la tentative de reprise | Non (évaluation sur 2 orbites) |
| CTG-008 | Panne du senseur stellaire   | aocs | payload_ops  | OUI — si passage en COARSE_SUN | OUI — amorçage de ST2 en 60 s |

**Schéma de coordination clé :** aocs pilote toutes les contingences d'attitude. Si le pointage
se dégrade au-delà du seuil de prise de vue, payload_ops est prévenu pour suspendre les opérations.
eps_tcs est consulté sur la marge de puissance avant l'activation de capteurs redondants.

**Annonces de panne du senseur stellaire (CTG-008) :**
1. aocs : « ST1 failure confirmed. Powering ST2. » — annoncer sur la boucle opérations
2. aocs : « ST2 booting, 60s to acquisition. » — le FD acquitte
3. Si ST2 tombe en panne : aocs → FD : « Dual ST failure. Requesting COARSE_SUN fallback. » GO du FD requis.
4. aocs → payload_ops : « Imaging suspended — insufficient pointing accuracy. »

---

### ttc — Contingences TT&C

| ID proc.      | Titre                            | Pilote | Appui        | GO/NO-GO FD | Critique en temps |
|---------------|----------------------------------|------|--------------|-------------|---------------|
| CTG-003       | Rétablissement après perte de liaison TTC | ttc  | fdir_systems | OUI — avant toute commande en aveugle | OUI — fenêtre de passage |
| CTG-014 | Analyse d'une anomalie de TEB | ttc  | eps_tcs      | OUI — avant le basculement de transpondeur | Non |
| CTG-019 | Absence de TM en début de passage | ttc  | fdir_systems | OUI — à chaque étape de commande en aveugle | OUI — fenêtre de passage |
| CTG-020 | Panne d'antenne de station sol | ttc  | FD directement | OUI — coordination avec une station de secours | OUI — planning des contacts |

**Schéma de coordination clé :** ttc pilote toutes les contingences RF/liaison. Les séquences de
commande en aveugle exigent une autorisation du FD à chaque étape. Escalade de la perte de liaison vers EMG-004
après 2 passages consécutifs en échec.

**Séquence d'annonces en cas d'absence de TM à l'AOS (CTG-019) :**
1. ttc : « No TM received at AOS+60s. GS confirms nominal. »
2. ttc → FD : « Request GO for blind HK. » GO du FD.
3. ttc : « Blind HK sent. Waiting 30s. »
4. En l'absence de réponse : ttc → FD : « Request GO for blind xpdr switch. » GO du FD.
5. Toujours sans réponse : ttc → FD : « Request GO for blind PA cycle. » GO du FD.
6. Toujours sans réponse : ttc → FD : « Request GO for antenna deploy (IRREVERSIBLE). » GO du FD requis (décision critique).
7. Après 2 passages en échec : ttc → FD : « Escalating to EMG-004 Loss of Communication. »

---

### payload_ops — Contingences charge utile

| ID proc.      | Titre                            | Pilote | Appui        | GO/NO-GO FD | Critique en temps |
|---------------|----------------------------------|------|--------------|-------------|---------------|
| CTG-006       | Anomalie thermique charge utile/FPA | payload_ops | eps_tcs | OUI — avant le redémarrage de la charge utile | Non (mise en froid) |
| CTG-015 | Traitement d'une image corrompue | payload_ops | fdir_systems | NON — routine (compte rendu au FD ensuite) | Non |
| CTG-016 | Défaillance d'un segment mémoire | payload_ops | fdir_systems | OUI — si capacité < 50 % | Non |

**Schéma de coordination clé :** payload_ops traite les anomalies propres à la charge utile.
Les problèmes thermiques du FPA exigent qu'eps_tcs vérifie l'alimentation du refroidisseur et l'état thermique du TCS.
Les défaillances mémoire peuvent imposer une replanification de la mission si la capacité est sensiblement réduite.

---

### fdir_systems — Contingences OBDH / systèmes

| ID proc.      | Titre                            | Pilote | Appui        | GO/NO-GO FD | Critique en temps |
|---------------|----------------------------------|------|--------------|-------------|---------------|
| CTG-010       | Reprise après réinitialisation par chien de garde de l'OBC | fdir_systems | eps_tcs | OUI — en cas de réinitialisations répétées | OUI — risque de boucle de redémarrage |
| CTG-018 | Reprise par le chargeur d'amorçage | fdir_systems | tous les postes | OUI — à chaque étape de reprise | OUI — calage de l'inhibition d'amorçage |
| CTG-017 | Basculement sur panne du bus CAN | fdir_systems | tous les postes | OUI — avant le basculement de bus | OUI — lacune HK de 10 s |
| CTG-011 | Basculement sur l'OBC redondant | fdir_systems | tous les postes | OUI — CRITIQUE : plus aucune redondance ensuite | OUI — lacune TM de 60 s |
| CTG-021 | Reprise par le chargeur d'amorçage de l'OBC | fdir_systems | eps_tcs | OUI — avant le rechargement de l'image | OUI — sur plusieurs contacts |
| CTG-022 | Isolation du bus CAN         | fdir_systems | tous les postes | OUI — avant le basculement de bus | OUI — lacune HK de 10 s |
| CTG-027  | Synchronisation temporelle GPS et reprise SCAO | fdir_systems | aocs | OUI — si saut de temps > 5 s | OUI — l'AOCS peut se réinitialiser |

**Schéma de coordination clé :** fdir_systems pilote toutes les contingences OBDH. Les pannes de l'OBC et
du bus CAN affectent TOUS les sous-systèmes : chaque poste doit donc être en console et
confirmer l'état de son sous-système après la reprise. Le basculement d'OBC est l'opération la plus critique
— il ne laisse aucune redondance d'OBC.

**Annonces du basculement sur l'OBC redondant (CTG-011) :**
1. fdir_systems → FD : « Requesting OBC switchover to Unit B. This eliminates OBC redundancy. » GO du FD requis.
2. fdir_systems : « Switchover commanded. Expect 30-60s TM gap. »
3. TOUS les postes : « Subsystem status check. » Chaque poste confirme que son sous-système est nominal sur OBC-B.
4. fdir_systems → FD : « All subsystems nominal on OBC-B. Zero OBC redundancy remaining. »

---

## Lacunes de l'interface MCS pour le soutien aux contingences

Les fonctions MCS suivantes sont **absentes ou insuffisantes** pour une exécution correcte
des procédures de contingence :

### Lacunes critiques

| N° | Lacune | Impact | Procédures concernées |
|---|-----|--------|---------------------|
| 1 | **Pas de compte à rebours d'éclipse** | Les procédures de délestage exigent que les opérateurs connaissent le temps restant avant la sortie/l'entrée d'éclipse | CTG-023, CTG-001, CTG-013 |
| 2 | **Pas d'indicateur de niveau de délestage** | Le délestage progressif comporte 4 niveaux — sans aucun état visuel | CTG-023, CTG-001 |
| 3 | **Pas d'alerte d'impact inter-sous-systèmes** | Quand un sous-système tombe en panne, les opérateurs des sous-systèmes dépendants ne sont pas alertés | Toutes les contingences OBC/CAN, délestage |
| 4 | **Pas de compte à rebours par étape de procédure** | Les étapes d'attente (30 s, 60 s, 120 s) n'affichent pas le temps restant | Toutes les procédures comportant des étapes wait_s |
| 5 | **Pas d'affichage de l'état de déploiement des ailes** | L'état des ailes (0x0144) n'apparaît dans aucun onglet | CTG-009, CTG-024 |
| 6 | **Pas de journal d'audit persistant des commandes** | La piste d'audit est perdue au redémarrage du serveur | Toutes les contingences (analyse après incident) |
| 7 | **Pas de filtre des alarmes par gravité/date** | Impossible de filtrer le journal des alarmes par gravité ou par plage horaire | Toutes les contingences nécessitant un tri des alarmes |
| 8 | **Pas de restriction des procédures par poste** | N'importe quel poste peut exécuter n'importe quelle procédure | Toutes — risque qu'un mauvais poste exécute une mauvaise procédure |
| 9 | **Pas de bandeau « contingence active »** | Aucune indication visuelle signalant à tous les opérateurs qu'une contingence est en cours | Toutes les contingences |
| 10 | **Pas de suivi des commandes en aveugle** | Pas de mode spécial pour les commandes envoyées sans confirmation par la TM | CTG-003, CTG-019 |

### Priorités recommandées

**P1 (à implémenter maintenant) :** n° 1 (compte à rebours d'éclipse), n° 2 (indicateur de délestage), n° 9 (bandeau de contingence)
**P2 (à implémenter prochainement) :** n° 3 (alertes inter-sous-systèmes), n° 5 (état des ailes), n° 7 (filtres d'alarmes)
**P3 (à implémenter plus tard) :** n° 4 (compte à rebours par étape), n° 6 (audit persistant), n° 8 (RBAC des procédures), n° 10 (mode commande en aveugle)

---

## Matrice des annonces GO/NO-GO

> **Remarque (G7) :** ce tableau est un MIROIR de la matrice lisible par machine de
> `configs/eosat1/mcs/gonogo_matrix.yaml`, que le MCS sert à l'adresse
> `GET /api/gonogo-matrix` pour le panneau GO/NO-GO. Modifier d'abord le YAML,
> puis maintenir ce tableau en cohérence.

| Situation | Qui annonce | Qui doit répondre | Décision du FD |
|-----------|-----------|------------------|-------------|
| Passage au niveau de délestage supérieur | eps_tcs | postes concernés | Le FD autorise chaque niveau |
| Changement de mode d'un sous-système | poste pilote | FD | Le FD autorise |
| Envoi d'une commande en aveugle | ttc | FD | Le FD autorise chaque TC en aveugle |
| Basculement d'OBC | fdir_systems | TOUS les postes | Le FD autorise (CRITIQUE) |
| Mode de repli AOCS | aocs | payload_ops, FD | Le FD autorise le changement de mode |
| Suspension/reprise de la charge utile | payload_ops ou eps_tcs | FD | Le FD autorise |
| Basculement de transpondeur | ttc | FD | Le FD autorise (interruption de la TM) |
| Modification d'un seuil FDIR | fdir_systems | TOUS les postes | Le FD autorise (essai uniquement) |
| Déploiement de l'antenne | ttc | FD | Le FD autorise (IRRÉVERSIBLE) |
| Reprise après le mode survie | fdir_systems | TOUS les postes | Le FD autorise chaque étape de rétablissement |
| Jalon de phase de recette en orbite | poste pilote | FD | Le FD prononce le GO pour la phase suivante |

---

## Chemins d'escalade vers les urgences

| Contingence d'origine | Déclencheur d'escalade | Procédure d'urgence |
|------------------|--------------------|---------------------|
| CTG-023 (délestage) | SoC < 10 % ou bus < 25 V | EMG-002 Perte totale d'alimentation |
| CTG-003 (perte de liaison) | 2 passages consécutifs en échec | EMG-004 Perte de communication |
| CTG-002 (anomalie AOCS) | défaillance de 3 roues ou plus, ou vitesse angulaire > 5°/s | EMG-005 Perte d'attitude |
| CTG-004 (thermique) | Dépassement d'une limite rouge (toute zone) | EMG-006 Emballement thermique |
| CTG-010 (chien de garde OBC) | 3 réinitialisations ou plus en 1 orbite | EMG-003 Redémarrage de l'OBC (évaluer le basculement) |
| CTG-011 (basculement) | OBC-B également en panne | EMG-003 Redémarrage de l'OBC |
