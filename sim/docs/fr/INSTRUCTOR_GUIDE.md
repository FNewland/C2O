# Guide de l'enseignant et de l'opérateur du simulateur SMO

## Vue d'ensemble

La console instructeur se trouve à l'adresse **`http://<server>:8080`**. C'est le
port de l'enseignant, et non celui des étudiants — les étudiants utilisent le MCS sur le port 9090. Ce
guide couvre :

- **Les scénarios** : exercices de formation prédéfinis, avec conditions initiales et événements minutés
- **Les points de reprise** : instantanés d'état permettant de reprendre une simulation à un moment clé
- **L'affichage des paramètres** : visibilité « omnisciente » sur chaque paramètre du satellite
- **L'injection de pannes** et les **commandes de simulation**
- **La reproductibilité** : comment faire en sorte qu'un exercice se comporte deux fois de la même manière
- **L'éditeur de configuration** (8080/config) : préparer un jeu de configuration par exercice
- **Les rapports** (8080/reports) : le support du débriefing
- **Ce que voient les étudiants**, qui a sensiblement changé dans cette version

Lancer la suite avec `./start.sh --public` pour une salle de cours (l'écoute sur l'interface de bouclage est le
comportement par défaut depuis la version 2026-08 — voir `docs/DEPLOYMENT.md`).

---

## CE QUI A CHANGÉ DANS LA VERSION 2026-08

Lisez cette section si vous avez enseigné avec une version antérieure. Tout ce qui suit
modifie le comportement d'un exercice ou ce que vous pouvez promettre à un étudiant.

**La simulation est désormais reproductible.** Même graine + même époque + même script de
commandes ⇒ une trace des paramètres identique à l'octet près. Rien n'était initialisé par une graine auparavant : aucun
exercice n'était donc répétable et aucun exemple résolu n'était vérifiable. L'accélération du temps
ne modifie plus non plus la physique jusqu'à ×60. Lisez
[`docs/DETERMINISM.md`](DETERMINISM.md) avant de préparer un exercice numérique —
en particulier l'avertissement concernant la notation de valeurs de pointage relevées au-delà de ×60.

**Les points de reprise capturent désormais tout.** Le plan bord S11, les pannes
injectées, les scénarios en cours, la phase du chargeur d'amorçage, les indicateurs d'activation des moniteurs, le
niveau de délestage et chaque détecteur de front étaient auparavant perdus au chargement. « Enregistrer →
injecter → restaurer → comparer » fonctionne désormais dans les deux sens. Voir
[`docs/THREADING_AND_STATE.md`](THREADING_AND_STATE.md) §4.

**Le bilan de puissance est bouclé.** Avec tous les systèmes nominaux en marche, la production moyenne sur l'orbite
dépasse la consommation d'un facteur **1,48 dans le pire cas (éclipse maximale)** et
**1,95 dans le meilleur cas**. L'ancienne configuration échouait dans le sens *opposé* —
une règle FDIR sur le bus se déclenchait à 58 % de SoC, à l'intérieur de la plage nominale, pendant des
opérations *correctes*, si bien que les étudiants ne pouvaient distinguer une bonne planification d'une mauvaise. La
tension pédagogique est préservée : laisser la charge utile allumée pendant une éclipse
coûte environ 46 % de profondeur de décharge, et vider la mémoire à chaque passage éligible érode
visiblement la marge en 6 à 8 orbites.

**L'attitude est réaliste.** Il n'y avait auparavant aucune dynamique d'attitude : pas de tenseur
d'inertie, pas d'intégration des couples, aucun capteur ne mesurait autre chose que la vérité, pas
d'estimateur. Il existe désormais une dynamique de corps rigide, quatre roues en pyramide, des magnétocoupleurs,
des modèles de senseur stellaire, de senseurs solaires, de magnétomètre et de gyromètre, un MEKF à 6 états, et
une réelle différence entre COARSE (environ 5°), NOMINAL (0,065°) et FINE (0,013°).
L'entrée en FINE est **refusée** tant que ses préconditions ne sont pas remplies, et la charge utile
**refuse toute acquisition** sans elle. Cette chaîne est tout l'enjeu.

**Le satellite dispose d'une propulsion** (fonctions 108–118). Un ΔV recale le TLE : les
passages, les éclipses, la puissance et les opportunités de prise de vue se déplacent tous. Le moteur limite
l'accélération du temps à ×10 pendant une poussée.

**La FDIR fonctionne réellement.** Le modèle de cascade de défaillances et les dix procédures
de reprise étaient enregistrés mais jamais lancés. Ils s'exécutent désormais, et la moitié
« que fait le satellite pour y remédier » de la fenêtre FDIR se remplit.

**La salle de contrôle s'est étoffée.** Le contrôle des limites au sol (51 plages) est actif et pilote
la coloration des alarmes ; il existe un *système* d'alarmes avec acquittement persistant et un
compteur d'alarmes non acquittées ; une page **Tendances** trace n'importe quel paramètre sur n'importe quelle fenêtre, avec
les plages de limites et l'ombrage des éclipses et des contacts ; l'historique des commandes est archivé pour le
débriefing ; et un bandeau de connaissance de la situation est disponible.

**Deux nouveaux outils pour l'enseignant :** l'éditeur de configuration (8080/config) et le
générateur de rapports (8080/reports, également sur le MCS).

**L'enveloppe thermique du FPA a été recalculée** à partir du modèle corrigé. Si vous
enseigniez « refroidir à −12 °C avant la prise de vue », cessez : la condition est l'indicateur
`fpa_ready` (0x0610), la consigne est commandable entre −20 et 0 °C, et la mise en froid
prend environ **10 minutes**, et non 30. Voir §FPA ci-dessous.

---

## SCÉNARIOS

### Qu'est-ce qu'un scénario ?

Les scénarios sont des exercices de formation définis en YAML qui initialisent le simulateur dans un état donné du satellite et peuvent déclencher des événements datés ou conditionnels. Chaque scénario comporte :
- **Nom** : identifiant unique (p. ex. « Post-Separation », « ACS Contingency »)
- **Difficulté** : niveau de formation (BASIC, INTERMEDIATE, ADVANCED)
- **Durée** : longueur du scénario en secondes
- **Briefing** : consignes pour les opérateurs et objectifs de la mission
- **État initial** : mode du satellite, état de l'alimentation, état thermique (fixés au démarrage du scénario)
- **Événements** : actions datées ou déclenchées sur condition (pannes injectées, commandes de télémesure, etc.)
- **Réponses attendues** : liste de vérification des actions que le stagiaire doit accomplir pour terminer le scénario

### Fichiers de scénario

Les scénarios sont stockés sous forme de fichiers YAML dans `configs/eosat1/scenarios/`. Exemple de schéma :

```yaml
name: "Post-Separation"
difficulty: BASIC
duration_s: 3600
briefing: |
  Post-separation scenario. Spacecraft has just separated from launch vehicle.
  All subsystems powered down except OBC bootloader. Battery at 95% SoC.
  AOCS in OFF mode with random tumble rates (~1-2 deg/s) from separation impulse.

  Your mission:
  1. Monitor separation timer (30 min countdown)
  2. Boot OBC and establish telecommand link
  3. Deploy antenna and verify uplink
  4. Initiate AOCS detumble sequence
  5. Enable thermal control and nominal power loads

events:
  - time_offset_s: 300
    action: "log_event"
    params:
      message: "Separation timer has 25 minutes remaining"
  - time_offset_s: 1800
    action: "inject_failure"
    params:
      subsystem: "ttc"
      failure: "antenna_mispoint"
      magnitude: 0.5
      onset: "immediate"

expected_responses:
  - { category: monitor, description: "Observe separation timer countdown" }
  - { category: action, description: "Boot OBC when separation timer expires" }
  - { category: action, description: "Deploy antenna via mechanical deployment" }
  - { category: action, description: "Establish command link and verify comms" }
  - { category: action, description: "Initiate AOCS detumble sequence" }
```

### Créer un scénario

1. Créer un nouveau fichier YAML dans `configs/eosat1/scenarios/` (p. ex. `my_scenario.yaml`)
2. Définir les cinq champs obligatoires : `name`, `difficulty`, `duration_s`, `briefing`, `events`
3. Redémarrer le serveur du simulateur (les scénarios sont chargés au démarrage)
4. Ouvrir l'interface web instructeur ; cliquer sur « ACTUALISER » (liste des scénarios) pour charger le nouveau scénario

### Utiliser un scénario

1. **Charger les scénarios** : cliquer sur le bouton **ACTUALISER** du panneau de gauche
2. **Sélectionner** : cliquer sur un scénario de la liste pour afficher son briefing
3. **Démarrer** : cliquer sur le bouton **DÉMARRER** pour lancer le scénario. Le simulateur revient à l'état initial du scénario et commence à exécuter les événements minutés.
4. **Suivre** : la barre de progression indique le temps écoulé et la durée du scénario
5. **Arrêter** : cliquer sur **ARRÊTER** pour terminer le scénario. Les pannes actives sont conservées sauf si elles sont effacées manuellement.

### Actions d'événement

Types d'actions d'événement courants :

| Action | Objet | Exemple |
|--------|---------|---------|
| `log_event` | Inscrire un message dans le journal des événements | Jalon de formation atteint |
| `inject_failure` | Injecter une panne de sous-système à T+décalage | Défaillance d'un élément de batterie, propulseur bloqué |
| `set_parameter` | Forcer la valeur d'un paramètre | Forcer le SoC à 10 % |
| `command_telecommand` | Envoyer une commande simulée | Changement de mode EPS, amortissement des vitesses angulaires AOCS |
| `conditional_event` | Déclencher si une condition est remplie (p. ex. `att_error_deg > 5`) | Uniquement si l'erreur d'attitude dépasse le seuil |

---

## POINTS DE REPRISE

### Qu'est-ce qu'un point de reprise ?

Les points de reprise capturent l'état mutable **complet** de la simulation à un instant
donné. « Complet » est désormais garanti : chaque composant à état figure dans un registre,
`BreakpointManager` le parcourt, et un composant incapable de se sérialiser **fait échouer
l'enregistrement tout entier** plutôt que d'écrire un instantané qui se chargerait sans erreur.

Éléments capturés :

- Le nombre de pas de simulation et le temps simulé
- Tous les paramètres du satellite
- L'état interne de chaque modèle de sous-système
- **L'état du générateur aléatoire (RNG) de chaque composant** — un chargement poursuit ainsi la même suite aléatoire
  au lieu d'en commencer une nouvelle
- **Le plan bord S11 de télécommandes datées** (il était auparavant détruit par un
  chargement, ce qui cassait précisément le scénario d'usage pour lequel il avait été conçu)
- Les pannes injectées et le scénario en cours
- L'automate de phase du satellite (chargeur d'amorçage ou logiciel applicatif), le niveau de
  délestage, les indicateurs d'activation des moniteurs S12 *et* leurs références de variation, les définitions S19,
  les transferts S13 en cours, les vidages S15 en cours et l'arriéré de régulation de débit
- Chaque détecteur de front `_prev_*` — le premier pas après un chargement ne
  redéclenche donc plus d'événements parasites d'AOS, d'entrée en éclipse ou de changement de mode

Délibérément **non** capturés : le temps réel (horloge murale), le journal des alarmes et le
journal de vérification du MCS (charger un point de reprise remet le satellite en arrière, pas la salle
de contrôle — ce qui est réaliste et mérite d'être signalé aux étudiants), ni les sockets
connectées.

Les points de reprise servent à :
- **Reprendre la formation** : mettre un scénario en pause, enregistrer, reprendre plus tard à partir de ce point
- **Déboguer des pannes** : capturer l'état avant et après une panne et comparer
- **Enseigner des points de référence** : montrer aux stagiaires l'état aux jalons clés de la mission
- **Construire un exercice** : enregistrer un état initial réputé sain et remettre à chaque équipe
  le même satellite

### Enregistrer un point de reprise

1. Dans le panneau de droite, saisir un nom dans le champ **Nom du point de reprise…** (p. ex. « Fin de la LEOP », « Avant l'anomalie AOCS »)
2. Cliquer sur **ENREG.** ou appuyer sur Entrée
3. Le point de reprise est enregistré avec :
   - le nom choisi ;
   - le temps de simulation courant ;
   - le nombre de pas courant ;
   - un instantané complet de l'état.

### Charger un point de reprise

Les points de reprise sont listés dans la section **Points de reprise**. Pour en charger un :
1. Cliquer sur le nom du point de reprise dans la liste (à venir : ajout d'un bouton de chargement dans l'interface)
2. Le simulateur revient exactement à cet état
3. La formation se poursuit à partir de ce point

L'enregistrement et le chargement passent par la file instructeur du fil d'exécution des pas : un
chargement ne peut donc plus intervenir au milieu d'un pas et produire un état du satellite sans
cause physique. Les deux opérations sont également disponibles en REST
(`POST /api/breakpoint/save`, `POST /api/breakpoint/load`) pour préparer un
exercice par script.

### Points de reprise enregistrés

Les métadonnées des points de reprise (nom, pas, temps) sont affichées dans l'interface instructeur. Les instantanés d'état complets sont accessibles via le point d'accès `/api/breakpoint/load`.

---

## AFFICHAGE DES PARAMÈTRES

### Vue d'ensemble

La vue instructeur/opérateur affiche **TOUS les paramètres du satellite** en temps réel à partir du point d'accès `/api/instructor/snapshot`. Elle offre une visibilité omnisciente sur :
- l'état orbital (position, vitesse, état d'éclipse et de contact) ;
- tous les paramètres des sous-systèmes (EPS, AOCS, TCS, OBDH, TT&C, charge utile) ;
- les modèles internes des sous-systèmes (thermique, puissance, attitude) ;
- l'état de la FDIR et les règles déclenchées ;
- l'état du stockage de la télémesure.

### Cartes de paramètres

Les paramètres sont regroupés par sous-système :

#### EPS (sous-système d'alimentation électrique)
- État de charge de la batterie (SoC, %)
- Tension du bus, tension de la batterie
- Température de la batterie
- Production de puissance, consommation
- Courants du générateur solaire (panneaux A et B)
- Mode, niveau de délestage

#### AOCS (contrôle d'attitude et d'orbite)
- Erreur d'attitude (deg)
- Vitesses angulaires (roulis, tangage, lacet en deg/s)
- Vitesses des roues de réaction (tr/min)
- État du senseur solaire et du senseur stellaire
- Mode de contrôle (OFF, SAFE_BOOT, DETUMBLE, COARSE_SUN, NOMINAL, FINE_POINT, SLEW, …)

#### TCS (contrôle thermique)
- Températures de l'OBC, de la batterie et du FPA
- État des réchauffeurs (ON/OFF) de la batterie et de l'OBC
- État du refroidisseur (refroidisseur du FPA)
- Taux d'utilisation de la surface des radiateurs
- Marges thermiques

#### OBDH (gestion bord des données)
- Charge CPU (%)
- Mémoire utilisée (%)
- Stockage utilisé (%)
- Nombre de redémarrages
- Mode (NOMINAL, SAFE, BOOTLOADER)

#### TT&C (télémesure, poursuite et télécommande)
- État de la liaison (UP/DOWN)
- RSSI (dBm)
- Marge de liaison (dB)
- Distance (km)
- Élévation (deg)
- Mode, débits TX/RX

#### Charge utile (système d'imagerie)
- Température du FPA
- Stockage utilisé (%)
- Nombre d'images
- Mode (OFF, STANDBY, IMAGING, PLAYBACK)
- État d'alimentation du refroidisseur
- RSB par bande spectrale

#### Informations orbitales
- Latitude, longitude, altitude
- Indicateurs d'éclipse et de contact
- Demi-grand axe, excentricité, inclinaison
- RAAN, argument du périgée, anomalie vraie

### Recherche de paramètre

Utiliser le champ **Recherche de paramètre** pour trouver rapidement un paramètre :
- Saisir un nom de paramètre (p. ex. « SoC », « Temperature », « Mode »)
- Saisir un identifiant de paramètre (hexadécimal, p. ex. « 0x0143 »)
- Les paramètres correspondants sont surlignés en vert
- Effacer la recherche pour revenir à l'affichage normal

### Vue de l'instantané brut

Pour le débogage, ou lorsqu'un paramètre n'est affiché dans aucune carte standard, déplier la section **Instantané brut (JSON)** en bas de la page. Elle affiche la réponse complète de `/api/instructor/snapshot`, avec tous les paramètres, les états des sous-systèmes et les métadonnées.

---

## INJECTION DE PANNES

### Injecter des pannes

Depuis le panneau de droite :
1. Sélectionner un **Sous-système** (EPS, AOCS, TCS, OBDH, TT&C, charge utile)
2. Sélectionner un **Type de panne** (p. ex. « solar_array_partial », « rw_bearing », « heater_stuck_on »)
3. Régler l'**Amplitude** (0.0 = aucune, 1.0 = panne totale)
4. Choisir le type d'**Apparition** :
   - **Échelon** : l'amplitude de la panne atteint instantanément la valeur cible
   - **Progressive** : l'amplitude croît en rampe pendant « Durée d'apparition » secondes
   - **Intermittente** : la panne apparaît et disparaît à intervalles aléatoires
5. Cliquer sur **INJECTER UNE PANNE**

### Effacer des pannes

- Cliquer sur le bouton **EFFACER** à côté d'une panne active pour la supprimer
- Cliquer sur **EFFACER TOUTES LES PANNES** pour supprimer d'un coup toutes les pannes injectées

### Types de panne par sous-système

| Sous-système | Pannes disponibles |
|-----------|-------------------|
| EPS | solar_array_partial, bat_cell (dégradation), bus_short |
| AOCS | rw_bearing, gyro_bias, stuck_thruster |
| TCS | heater_stuck_on, heater_stuck_off, sensor_bias |
| OBDH | cpu_spike, watchdog_reset, memory_error |
| TT&C | primary_failure, antenna_mispoint, frequency_drift |
| Charge utile | fpa_overheat, memory_full, calibration_error |

---

## COMMANDES DE SIMULATION

### Commandes de temps

- **Boutons de vitesse** : 0.1x, 0.5x, 1.0x, 2.0x, 5.0x, 10.0x (jusqu'à 1000x par l'API)
  - 1.0x = temps réel
  - >1.0x = accéléré (utile pour les scénarios longs)
  - <1.0x = ralenti (utile pour une observation détaillée)

**Accélération et fidélité.** Le pas est subdivisé : les modèles voient donc le
même pas de 1 seconde à ×60 qu'à ×1 — les réponses de la batterie, de la thermique, des réchauffeurs, des roues et
des variations S12 sont identiques. Deux exceptions, toutes deux délibérées et toutes deux
visibles :

| Au-delà de | Ce qui se passe | Comment le voir |
|---|---|---|
| **×60** | La boucle rapide de l'AOCS est court-circuitée. L'attitude est *échantillonnée* à partir de la distribution d'erreur en boucle fermée propre au mode ; le moment cinétique des roues, le biais des gyromètres et la covariance du MEKF restent intégrés exactement | Un événement S5, et `aocs.fidelity_mode` = 1 dans la télémesure |
| **pendant une poussée** | La vitesse est limitée à ×10 | Événement `PROP_SPEED_CLAMPED` |

Une exécution à ×1000 est donc une avance rapide déclarée, et non un mensonge silencieux. **Ne notez pas
une valeur de pointage issue d'une exécution au-delà de ×60.**

- **FIGER/REPRENDRE** : mettre complètement la simulation en pause ; tous les paramètres sont figés
  - Utile pour examiner en détail un état particulier
  - REPRENDRE pour continuer à partir de ce point

### Forçage de la liaison

- **FORCER LES PASSAGES** : force la visibilité GÉOMÉTRIQUE — le simulateur se comporte comme
  si une station sol était en permanence en visibilité (liaison montante forcée ; la condition de contact
  du contrôle de liaison descendante satisfaite). Il ne **ressuscite pas** un émetteur
  éteint : avec l'amplificateur (PA) bande S éteint ou la ligne `ttc_tx` coupée, il n'y a toujours
  pas de télémesure et la page radio indique la porteuse absente, avec ou sans forçage
  (2026-08c, point 6). Utiliser PA ON / ligne ON pour rétablir la liaison descendante.
  - Activé : télémesure et commande toujours disponibles
  - Désactivé : liaison disponible uniquement pendant les passages simulés au-dessus des stations sol
  - Utile pour une formation indépendante des passages au-dessus des stations sol

### Journal des événements

Le panneau inférieur présente un journal chronologique :
- des démarrages et arrêts de scénario ;
- des pannes injectées et effacées ;
- des modifications de paramètres ;
- des points de reprise enregistrés ;
- des messages système.

Cliquer sur **Effacer le journal** pour réinitialiser le journal des événements.

---

## REPRODUCTIBILITÉ — FAIRE QU'UN EXERCICE SE COMPORTE DEUX FOIS DE LA MÊME MANIÈRE

Trois entrées déterminent une exécution, et rien d'autre :

| Entrée | Emplacement | Valeur livrée |
|---|---|---|
| Graine | `configs/eosat1/simulation.yaml: seed` | `20260731` |
| Époque | `configs/eosat1/orbit.yaml: t0_epoch` (sélectionnée par `simulation.yaml: epoch: t0`) | fixe |
| Script de commandes | ce qu'envoie l'opérateur, et *à quel instant du temps simulé* | — |

Conséquences pratiques pour l'enseignement :

- **Donnez à chaque promotion sa propre graine** si vous voulez un univers différent mais tout aussi
  répétable. Changez un nombre dans `simulation.yaml` — l'éditeur de
  configuration (ci-dessous) est le moyen sûr de le faire, et il consigne qui
  l'a modifié et pourquoi.
- **Un exemple résolu est désormais vérifiable.** Publiez la graine avec l'exercice
  et un étudiant pourra reproduire exactement vos valeurs.
- **`epoch: wall`** démarre à partir de l'horloge murale. C'est la seule manière prise en charge
  de rendre une exécution non reproductible ; le journal l'indique au démarrage. N'en notez
  aucune.
- **Enregistrez un point de reprise pour créer une variante d'un exercice.** L'état du RNG figure dans l'instantané :
  un chargement poursuit donc la même suite — deux équipes qui chargent le même point de reprise
  et ne font rien obtiennent une télémesure identique.

L'énoncé complet de ce qui est reproductible et de ce qui ne l'est pas, y compris les deux axes
temporels (le CUC des paquets est en temps simulé ; les noms des fichiers de vidage sont en temps réel, et sous
accélération les deux sont sans rapport), figure dans
[`docs/DETERMINISM.md`](DETERMINISM.md).

---

## ÉDITEUR DE CONFIGURATION (8080/config)

**Lecture-écriture sur le port 8080 uniquement.** Le MCS et le planificateur montent les mêmes pages
en lecture seule — les routes de modification n'y existent pas, elles ne sont pas simplement
désactivées — si bien que les étudiants peuvent consulter la configuration et son historique, ce qui
mérite en soi d'être enseigné, sans pouvoir la modifier.

Ce qu'il vous apporte :

- **Une édition validée par schéma** de tout ce qui se trouve sous `configs/eosat1/`.
  La validation enchaîne schéma → plage et plausibilité physique → **cohérence
  entre fichiers** avant tout enregistrement.
- **Un aperçu des différences avant application.** Vous voyez exactement ce qui va changer.
- **Un véritable historique.** Les révisions sont conservées dans un dépôt git fantôme à
  `workspace/config-history/` dont l'arbre de travail est `configs/` : vous disposez ainsi
  des diffs, du blame et des étiquettes sans toucher au dépôt source. Si `git` est
  absent (l'installateur Windows des salles de TP ne le fournit pas), l'éditeur se rabat automatiquement sur
  des instantanés.
- **Les référentiels nommés** sont des étiquettes annotées. « Restaurer la dernière version saine » se fait en un clic.
- **Les variantes par exercice sont des branches.** C'est l'apport le plus utile de
  cette fonction : préparer *le jeu de configuration de l'exercice SCAO CERISE* avant
  le cours et passer de l'un à l'autre entre les séances.
- **Des métadonnées d'audit** sur chaque révision (`SMO-Actor`, `SMO-Role`,
  `SMO-Reason`, `SMO-CrossCheck`, `SMO-RestartScope`), afin que l'audit survive à un
  simple clonage.

**Règle de sécurité :** tant qu'un scénario de formation est en cours, l'application et l'annulation sont
refusées, sauf si vous les forcez en consignant une raison. Modifier le satellite
sous les pieds d'une équipe en plein exercice n'est presque jamais ce que vous vouliez.

**Portée du redémarrage.** Certaines clés prennent effet au pas suivant ; d'autres exigent le
redémarrage du service. L'éditeur l'indique, clé par clé.

---

## RAPPORTS ET DÉBRIEFING (8080/reports, 9090/reports)

Trois modèles : **revue quotidienne des opérations**, **rapport de passage**, **enquête
sur anomalie**. La sortie est un fichier HTML autonome — à remettre directement à un étudiant
ou à imprimer.

Deux aspects du générateur de rapports méritent d'être enseignés pour eux-mêmes :

1. **Archive moins direct est une vraie grandeur.** L'archive des vidages S15 est
   l'enregistrement *complet* de ce que le satellite a restitué. La vue en direct du MCS est
   incomplète : les paquets émis pendant que la liaison est coupée sont perdus. La
   différence entre les deux correspond exactement à « ce que la liaison vous a coûté », et elle fait l'objet d'une
   section du rapport plutôt que d'une note de bas de page.
2. **Toute sélection de période repose sur le CUC**, c.-à-d. sur le temps bord. Les *noms
   de fichiers* des vidages portent le temps réel, et sous accélération du temps les deux axes sont
   sans rapport — un outil qui filtrerait sur l'horodatage des fichiers renverrait la mauvaise
   heure de la mission.

L'historique des commandes est archivé : il est donc désormais possible de répondre après l'exercice à la question « qu'a envoyé cette équipe, quand,
et qu'est-il revenu » ; c'est le support dont un débriefing a réellement
besoin.

---

## CE QUE VOIENT LES ÉTUDIANTS (MCS, 9090)

Les changements de cette version justifient une visite guidée avant un cours.

| Fonction | Pourquoi c'est important pour vous |
|---|---|
| **Contrôle des limites au sol** | 51 plages issues de `mcs/limits.yaml` sont appliquées à chaque échantillon et colorent l'affichage. Auparavant, un paramètre ne passait au rouge que si la surveillance S12 *du satellite* le signalait, et 29 paramètres à limites n'ont pas d'équivalent S12 — le courant du bus, les courants par ligne, la température du gyromètre et le PDOP GPS ne donnaient donc aucun repère visuel |
| **Système d'alarmes** | Acquittement persistant, nombre d'alarmes non acquittées dans le bandeau, filtre de gravité qui survit à un rechargement, et lien alarme→procédure (« cette alarme ⇒ exécuter CTG-001 ») |
| **Page Tendances** | Choisir des paramètres, choisir une fenêtre, superposer les plages de limites, voir les arcs d'éclipse et de contact ombrés. « Montrez-moi ce paramètre sur les 12 dernières heures » est la fonction la plus utilisée d'une vraie salle de contrôle, et elle n'existait pas |
| **Fenêtre FDIR** | Se remplit désormais dans ses deux moitiés : ce que le satellite a détecté *et* ce qu'il fait pour y remédier |
| **Bandeau de connaissance de la situation** | Temps avant AOS/LOS avec le nom de la station, palier de débit actif ou commandé, remplissage de la mémoire bord, alarmes non acquittées, vitesse de simulation, et un indicateur EN DIRECT/PÉRIMÉ au niveau de la page |
| **Éditeur de commande** | Saisie typée des arguments en valeurs physiques, avec affichage en direct de l'hexadécimal brut pendant la frappe, et décodage inverse lorsqu'on colle de l'hexadécimal. La consigne du FPA sert d'exemple résolu : `-15.00 degC` → `0x64D7` |
| **TM différée** | `9090/dumps` liste chaque vidage archivé avec le nombre de paquets et un résumé décodé |

---

## THERMIQUE DU FPA — CE QU'IL FAUT ENSEIGNER DÉSORMAIS

Le FPA avait cinq réponses différentes selon les endroits de la configuration et une sixième dans le
manuel. Il n'en a plus qu'une, définie à un seul endroit,
`configs/eosat1/subsystems/tcs.yaml: fpa_envelope`, et dérivée partout ailleurs.

| Question | Réponse |
|---|---|
| Plage de consigne commandable | **−20.0 … 0.0 °C** (`PAYLOAD_COOLER_SETPOINT`, fonction 36, uint16 en centikelvins) |
| Consigne par défaut | **−15.0 °C** |
| Performance de régulation | 3σ = **0,5 K** autour de la consigne |
| État de repos non refroidi | **≈ +11,5 °C** (maximum +12,4). C'est *normal* — la charge utile est éteinte entre les passages |
| Plage de santé (0x0408) | jaune **−22.0 … +14.0 °C**, rouge **−25.5 … +17.5 °C** |
| Condition de prise de vue | **`fpa_ready` (0x0610)** — stabilisé autour de la consigne *active* (−1 K / +5 K) **et** à **−3.0 °C** ou moins |
| Mise en froid | **≈ 10 minutes** pour atteindre la plage de consigne, plus 60 s d'hystérésis de disponibilité |

**La leçon.** Une limite répond à la question « le matériel est-il sain ? ». Un indicateur de disponibilité
répond à « puis-je prendre la photo ? ». C'est la confusion des deux qui a produit cinq
réponses différentes — dont une « plage d'avertissement » `[-50, -5]` qui était en réalité une
plage de prise de vue, et une limite basse du détecteur qu'une commande *légale* faisait franchir d'emblée.
C'est une meilleure leçon d'ingénierie système que n'importe quelle valeur du
tableau.

La décontamination (`TCS_DECONTAMINATION_START`, fonction 47) étuve le FPA à
+50 °C et déclenche l'alarme rouge haute. C'est correct : vous avez
délibérément sorti le détecteur de son enveloppe de fonctionnement, et la console
doit le signaler.


---

## DÉPANNAGE

### Les scénarios ne se chargent pas
- Vérifier que tous les fichiers YAML de `configs/eosat1/scenarios/` sont des fichiers YAML valides
- Consulter les journaux du serveur : `tail -f logs/simulator.log`
- Cliquer sur le bouton **ACTUALISER** de l'interface

### Paramètres affichés « -- » (aucune donnée)
- Vérifier que le simulateur tourne et que la WebSocket est connectée (vérifier l'état « WS CONNECTÉ »)
- Vérifier que le point d'accès `/api/instructor/snapshot` répond : `curl http://localhost:8080/api/instructor/snapshot`
- Certains paramètres peuvent être sans objet dans certains modes du satellite (p. ex. le RSB de la charge utile lorsque celle-ci est sur OFF)

### Échec du chargement d'un point de reprise
- Vérifier que le point de reprise a été enregistré avec un état valide
- Si le point de reprise est corrompu, le supprimer et en enregistrer un nouveau
- Rechercher dans les journaux du serveur des erreurs de restauration d'état

### L'injection de pannes reste sans effet
- Vérifier que l'amplitude de la panne est > 0.0
- Vérifier que le sous-système est dans un mode où la panne est observable (p. ex. une panne TTC exige que la liaison soit active)
- Certaines pannes ont un délai d'apparition ; observer dans la durée

---

## EXEMPLE DE DÉMARRAGE RAPIDE

### Scénario de formation : « Post-Separation LEOP »

1. **Charger le scénario** :
   - Cliquer sur **ACTUALISER** → sélectionner « Post-Separation » → cliquer sur **DÉMARRER**

2. **Surveiller l'état initial** :
   - Observer SoC batterie = 95 %, mode OBC = BOOTLOADER, mode AOCS = OFF
   - Vitesses angulaires d'environ 1-2 deg/s dues à l'impulsion de séparation
   - Suivre la barre de progression ; le scénario dure 1 heure

3. **Actions du stagiaire** (attendues par le scénario) :
   - Commander : séquence d'amorçage de l'OBC à T+00:10:00
   - Observer : le mode AOCS passe en DETUMBLE
   - Commander : déploiement de l'antenne à T+00:15:00
   - Surveiller : la marge de liaison augmente à mesure que l'angle de l'antenne se stabilise
   - Commander : activation de la régulation nominale des réchauffeurs TCS
   - Vérifier : tous les sous-systèmes opérationnels, SoC batterie stable

4. **Enregistrer un point de reprise** :
   - À T+00:30:00 (fin de l'amortissement), saisir « End AOCS Detumble » comme nom du point de reprise et cliquer sur ENREG.
   - Les séances suivantes pourront recharger cet état pour s'entraîner à partir de ce point

5. **Injecter une panne** (pour éprouver la réaction du stagiaire) :
   - Pendant le déroulement du scénario, injecter « solar_array_partial » (panne EPS, amplitude 0.7)
   - Observer : la production de puissance chute, le SoC batterie commence à baisser
   - Le stagiaire doit réagir par des commandes de délestage

6. **Arrêter le scénario** :
   - Cliquer sur **ARRÊTER** lorsque la formation est terminée ou que le minuteur arrive à échéance

---

## AVANCÉ : POINTS D'ACCÈS DE L'API

Pour un accès par programme :

- `GET /api/scenarios` → liste des scénarios disponibles
- `POST /api/command` → envoi de commandes (démarrer/arrêter un scénario, injecter une panne, régler la vitesse, enregistrer/charger un point de reprise)
- `GET /api/instructor/snapshot` → instantané d'état complet (chaque paramètre, chaque sous-système, FDIR)
- `GET /api/state` → le résumé d'état filtré par la liaison RF (ce que le sol peut voir)
- `POST /api/breakpoint/save`, `POST /api/breakpoint/load` → préparation d'exercice par script
- `GET /api/scenario/debrief` → export du débriefing du scénario
- `POST /api/ground-time` → décalage du temps sol, pour la répétition de passage
- `GET|PUT /api/config/*` → l'API de l'éditeur de configuration (lecture-écriture sur le port 8080 uniquement)
- `GET|POST /api/reports/*` → l'API du générateur de rapports
- `GET /api/dumps`, `/api/dumps/file?name=…`, `/api/dumps/summary?name=…` → la mémoire de TM différée

Exemple : démarrer un scénario avec curl
```bash
curl -X POST http://localhost:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{"type": "start_scenario", "scenario": "Post-Separation"}'
```

Chaque route enregistrée est contrôlée pour vérifier qu'elle a un consommateur par
`tests/test_content/test_endpoint_reachability.py` : cette liste ne peut donc pas
devenir obsolète en silence.

---

## GLOSSAIRE

| Terme | Définition |
|------|-----------|
| **Scénario** | Exercice de formation défini en YAML, avec état initial, événements minutés et résultats attendus |
| **Point de reprise** | Instantané d'état permettant de reprendre la simulation à un moment clé |
| **Mode omniscient** | Visibilité de l'enseignant non limitée par l'état de la liaison RF simulée |
| **Événement** | Action datée ou déclenchée sur condition au sein d'un scénario |
| **FDIR** | Système de détection, d'isolation et de reprise des défaillances |
| **Apparition** | Mode de montée en puissance d'une panne (immédiate ou progressive) |
| **SoC** | État de charge (pourcentage de la batterie) |
| **TM** | Télémesure (données en liaison descendante) |
| **TC** | Télécommande (commandes en liaison montante) |
| **HK** | Données de servitude (paquets d'état périodiques) |

---

**Version :** 2.0
**Dernière mise à jour :** 2026-08-01
**Responsable :** équipe enseignants/opérateurs
