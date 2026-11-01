# Interface de visualisation VR — ICD `smo-vr/1`

**État :** édition 1, 2026-09-27 · **Responsable :** suite SMO (smo-simulator `vr_bridge.py`)
**Utilisateurs :** équipes de première année travaillant sur casque VR (GNG) et toute personne qui construit un visualiseur 3D externe.

## 1. Objet

Le simulateur diffuse ce dont aurait besoin une caméra flottant à côté d'EOSAT-1 pour dessiner
la scène : la position du satellite, son orientation, la position du Soleil et de la Terre,
et l'état de déploiement des ailes solaires et de l'antenne. Un casque peut
(facultativement) renvoyer une courte ligne d'état, afin que la console instructeur indique
si chaque casque reçoit les données et fonctionne correctement.

Il s'agit de la **vérité de simulation destinée à la visualisation**. Ce n'est pas de la télémesure du satellite :
elle ne transite ni par le MCS ni par la liaison radio, et rien de ce qu'envoie un casque ne peut
modifier la simulation.

```
 smo-simulator (pas du moteur, 1 Hz à x1)
   └─ vr_bridge ── TCP 8100 (NDJSON) ──►  Unity / Unreal / application native du casque
                └─ WS  8101 /vr     ──►  page WebXR / three.js / A-Frame
                ◄─ lignes « status » (option) ┘
   └─ en-tête de la console instructeur : badge « VR n OK », GET /api/vr
```

Le bouchon autonome `tools/vr_stub/vr_stub.py` parle exactement le même protocole :
les équipes peuvent donc développer sans le simulateur.

## 2. Transports

| | TCP | WebSocket |
|---|---|---|
| Port par défaut | **8100** | **8101**, chemin `/vr` (ou `/`) |
| Tramage | un objet JSON par ligne, UTF-8, terminé par `\n` | un objet JSON par message texte |
| Adapté à | Unity (`TcpClient`), Unreal, Python, C++ | navigateurs (WebXR, three.js) — les navigateurs ne peuvent pas ouvrir de connexion TCP brute |
| Limite en entrée | 4096 octets par ligne | 4096 octets par message |

* Le simulateur est le **serveur** ; les casques s'y connectent en tant que clients. Le nombre de
  clients n'est pas limité ; chacun reçoit le même flux.
* Configuration : `configs/eosat1/mission.yaml` → `network.vr_*` ; surcharges
  `smo-simulator --vr-port / --vr-ws-port / --no-vr`, variables d'environnement `SMO_VR_PORT`,
  `SMO_VR_WS_PORT`, `SMO_VR=0`.
* **Casques en Wi-Fi :** lancer la suite avec `./start.sh --public` (écoute sur le réseau local).
  Le mode local par défaut n'écoute que sur l'interface de bouclage, inaccessible à un casque.
  Le pare-feu de la machine doit autoriser les connexions entrantes sur 8100/8101.
* Un client qui ne suit pas le rythme (écriture bloquée plus de 2 s) est déconnecté. Il doit se reconnecter.

## 3. Enchaînement des messages

1. À la connexion, le serveur envoie un **`hello`**, puis immédiatement le dernier
   **`state`** (s'il en existe un).
2. Ensuite, un `state` par nouveau pas du simulateur (1 Hz à la vitesse ×1), plus une répétition de
   la dernière trame au moins une fois par seconde tant que la simulation est figée.
   Jamais plus vite que `max_rate_hz` (10 par défaut).
3. Le client peut envoyer des lignes **`status`** à tout moment ; environ 1 Hz est idéal.

Les positions varient d'environ 7,5 km par seconde de temps simulé : il faut donc **interpoler** entre
les trames pour obtenir un mouvement fluide (slerp sur le quaternion, lerp sur la position, ou propagation
avec `vel_eci_km_s`). Aux fortes accélérations du temps (`speed` ≫ 10), les trames sont très
espacées sur l'orbite : sauter directement à la nouvelle valeur au lieu d'interpoler.

## 4. `hello` (serveur → client, une fois)

Description statique ; le texte complet figure dans le message. Champs principaux :

| Champ | Signification |
|---|---|
| `type` | `"hello"` |
| `schema` | `"smo-vr/1"` — refuser de fonctionner si la version majeure diffère |
| `source` | `"smo-simulator"` ou `"vr-stub"` |
| `max_rate_hz` | borne supérieure de la cadence des trames |
| `frames` | définitions textuelles des repères (§6) |
| `status_bits`, `healthy_mask` | la définition du mot d'état (§7) |
| `spacecraft` | signification des axes satellite, dimensions de la plateforme `[0.100, 0.226, 0.366]` m (X, Y, Z), dimensions des ailes, convention du SADA, modèle d'antenne suggéré |

## 5. `state` (serveur → client, environ 1 Hz)

Exemple (une seule ligne sur le réseau, mise en forme ici pour la lisibilité) :

```json
{"type":"state","schema":"smo-vr/1","seq":1812,
 "sim_time":"2026-08-20T12:30:12.000Z","met_s":1812.0,"tick":1812,"speed":1.0,
 "orbit":{"pos_eci_km":[-4702.3,2515.9,4406.8],"vel_eci_km_s":[-3.09,4.07,-5.62],
          "lat_deg":39.8,"lon_deg":-77.1,"alt_km":505.2},
 "attitude":{"q_body_to_eci":[0.123,-0.702,0.281,0.643],"rate_body_deg_s":[0.0,-0.0635,0.0],
             "aocs_mode":"NOMINAL","pointing":"NADIR"},
 "sun":{"dir_eci":[-0.843,0.493,0.214],"dir_body":[0.41,0.47,-0.78],"in_eclipse":false,"sun_fraction":1.0},
 "earth":{"dir_body":[0.0,0.0,1.0],"gmst_deg":156.4,"radius_km":6371.0},
 "deploy":{"wing_py":{"state":"DEPLOYED","fraction":1.0},
           "wing_my":{"state":"DEPLOYING","fraction":0.43},
           "sada_angle_deg":-48.2,
           "antenna":{"state":"DEPLOYED","deployed":true,"sensor":"DEPLOYED"}},
 "mission":{"sc_mode":"SAFE","phase":"LEOP","in_contact":true,"ground_station":"Iqaluit"}}
```

| Champ | Type / unité | Signification |
|---|---|---|
| `seq` | int | s'incrémente de 1 à chaque message **émis par le serveur de cette connexion** ; un saut = des trames manquées, une répétition = maintien de connexion |
| `sim_time` | ISO-8601 UTC | temps simulé. **Peut sauter** (l'enseignant charge un point de reprise, le scénario du bouchon reboucle) |
| `met_s` | s | temps écoulé depuis le lancement |
| `tick` | int | pas du simulateur ; inchangé lors des répétitions de maintien de connexion |
| `speed` | × | accélération du temps |
| `orbit.pos_eci_km` | km, ECI | position du satellite (centre de la Terre à l'origine) |
| `orbit.vel_eci_km_s` | km/s, ECI | vitesse (pour l'interpolation) |
| `orbit.lat_deg/lon_deg/alt_km` | deg, deg, km | point subsatellite et altitude |
| `attitude.q_body_to_eci` | `[x,y,z,w]` | **l'**attitude de référence, voir §6 |
| `attitude.rate_body_deg_s` | deg/s, repère satellite | vitesse angulaire en axes satellite (pour faire tourner le modèle entre deux trames) |
| `attitude.aocs_mode` | énumération | `OFF SAFE_BOOT DETUMBLE COARSE_SUN NOMINAL FINE_POINT SLEW DESAT ECLIPSE INERTIAL` |
| `attitude.pointing` | énumération | `NADIR INERTIAL TARGET_TRACK SUN` (la référence vers laquelle l'AOCS asservit l'attitude) |
| `sun.dir_eci` | vecteur unitaire | direction **vers** le Soleil, en ECI |
| `sun.dir_body` | vecteur unitaire | direction du Soleil en axes satellite (prête à l'emploi pour une caméra liée au satellite) |
| `sun.in_eclipse` | booléen | ombre : pas d'éclairement solaire direct — atténuer la lumière du Soleil |
| `sun.sun_fraction` | 0–1 | fraction visible du disque solaire (fondu dans la pénombre) |
| `earth.dir_body` | vecteur unitaire | direction du centre de la Terre en axes satellite (≈ `[0,0,1]` en pointage nadir) |
| `earth.gmst_deg` | deg | angle de rotation de la Terre : ECEF = ECI tourné de −gmst autour de Z. Faire tourner le modèle de Terre de **+gmst** autour de l'axe des pôles pour que les continents soient bien placés |
| `earth.radius_km` | km | rayon terrestre utilisé par le simulateur |
| `deploy.wing_py`, `wing_my` | `{state, fraction}` | `STOWED` 0.0 → `DEPLOYING` 0–1 (balayage d'environ 30 s) → `DEPLOYED` 1.0 |
| `deploy.sada_angle_deg` | deg | angle du mécanisme d'entraînement du générateur solaire ; normale aux cellules de l'aile en axes satellite = `(cos a, 0, sin a)` |
| `deploy.antenna.state` | énumération | `STOWED`, `DEPLOYED`, `JAMMED` (échec de déploiement partiel) |
| `deploy.antenna.deployed` | booléen | vérité : l'antenne est-elle sortie |
| `deploy.antenna.sensor` | énumération | ce que rapporte le microcontact de déploiement (`UNKNOWN STOWED DEPLOYED JAMMED`) — peut contredire la vérité en cas d'injection de pannes |
| `mission.sc_mode` | énumération | `SAFE NOMINAL SCIENCE EMERGENCY` |
| `mission.phase` | énumération | `PRE_SEPARATION SEPARATION_TIMER INITIAL_POWER_ON BOOTLOADER_OPS LEOP COMMISSIONING NOMINAL` |
| `mission.in_contact`, `ground_station` | booléen, chaîne | une station sol voit le satellite (dessiner un faisceau de liaison ?) |

## 6. Repères et conventions

* **ECI** — repère inertiel géocentrique, direct, en km. +X vers le point
  vernal, +Z passant par le pôle Nord. (Il s'agit strictement du repère TEME du SGP4 ; la
  différence avec J2000 est invisible à l'échelle de la VR.)
* **Satellite** — repère direct, lié au satellite :
  +X le long de la trace (vitesse) en pointage nominal · +Y perpendiculaire à la trace, axe de l'aile +Y et
  du mécanisme d'entraînement du générateur solaire · **+Z nadir** (imageur, tourné vers la Terre) · −Z zénith.
  Plateforme 6U de 0,100 × 0,226 × 0,366 m selon X, Y, Z.
  Ces axes sont ceux de l'interface smo-vr/1 ; ce ne sont pas ceux du repère
  satellite du simulateur. Depuis la décision de l'auteur Q4 (2026-10-30), le simulateur et le
  manuel d'exploitation utilisent +Z = zénith et −Z = nadir (imageur et radiateur sur
  −Z), avec +Y = +normale à l'orbite. Le pont VR convertit toutes les grandeurs
  exprimées en axes satellite, `v_vr = diag(1, −1, −1) · v_sim` (rotation de 180° autour de X) : les
  clients smo-vr/1 voient donc exactement les axes ci-dessus. Faire passer l'ICD elle-même à
  la nouvelle convention serait une rupture de compatibilité (smo-vr/2).
* **Quaternion** `q_body_to_eci = [x, y, z, w]` — partie scalaire **en dernier**, convention de
  Hamilton, norme unitaire. En tant que rotation active, il transforme un vecteur exprimé en
  axes satellite en vecteur ECI : `v_eci = q ⊗ v_body ⊗ q*`. Dans une scène dont les axes du monde sont
  ceux de l'ECI, c'est simplement la rotation de l'objet satellite.
  *Vérification :* en pointage nadir nominal, la rotation du vecteur satellite `[0,0,1]` par `q` donne
  `-pos_eci/|pos_eci|` (verticale descendante).

### Conversion vers les repères des moteurs de jeu

| Moteur | Axes | Vecteur `(x,y,z)` → | Quaternion `(x,y,z,w)` → |
|---|---|---|---|
| **Unity** (indirect, Y vers le haut) | permuter Y et Z | `(x, z, y)` | `(-x, -z, -y, w)` |
| **three.js / WebXR** (direct, Y vers le haut) | rotation de −90° autour de X | `(x, z, -y)` | `(x, z, -y, w)` |
| **Unreal** (indirect, Z vers le haut, cm) | inverser Y | `(x, -y, z)`·1e5 | `(-x, y, -z, w)` |

Code C# prêt à l'emploi pour Unity : `tools/vr_stub/unity/VRLinkClient.cs`.

### Conseils pour construire la scène (non obligatoires)
* Une scène centrée sur le satellite est la plus simple : garder le satellite à l'origine, placer
  le centre de la Terre en `-pos_eci_km` (mis à l'échelle), orienter la lumière directionnelle selon
  `-sun.dir_eci`.
* L'échelle réelle est impitoyable : un satellite de 0,37 m à 513 km au-dessus d'une Terre de 6371 km. Utiliser
  des échelles séparées (satellite à l'échelle réelle, distance à la Terre comprimée), ou une
  Terre en skybox rendue à partir de `earth.dir_body`.
* En éclipse, le Soleil est derrière la Terre — une scène physiquement exacte devient
  noire. Envisager une faible lumière ambiante de « clair de Terre ».

## 7. `status` (client → serveur, facultatif)

```json
{"type":"status","team":"T07","status_word":15,"state":"OK","seq_ack":1812,"fps":72,"text":"all good"}
```

| Champ | Obligatoire | Signification |
|---|---|---|
| `type` | oui | `"status"` |
| `status_word` | oui | entier de 0 à 65535, **logique positive** (un bit positionné = l'élément correspondant fonctionne ; 0 = rien ne fonctionne) |
| `state` | non | `OK`, `WARN` ou `ERROR` — le verdict de l'équipe elle-même |
| `team` | non | 32 caractères au plus, affiché sur la console instructeur |
| `seq_ack` | non | `seq` de la dernière trame appliquée — le serveur indique de combien de trames vous êtes en retard |
| `fps` | non | cadence d'images du casque |
| `text` | non | 200 caractères au plus, texte libre |

Bits du mot d'état :

| Bit | Masque | Nom | Positionné lorsque |
|---|---|---|---|
| 0 | 0x0001 | `RX_OK` | les trames arrivent |
| 1 | 0x0002 | `PARSE_OK` | la dernière trame a été analysée |
| 2 | 0x0004 | `RENDERING` | la scène est en cours de rendu |
| 3 | 0x0008 | `DATA_FRESH` | la trame la plus récente a moins de 2 s (temps réel) |
| 4 | 0x0010 | `DEPLOY_SHOWN` | facultatif : le déploiement est visualisé |
| 5 | 0x0020 | `FRAMERATE_OK` | facultatif : la cadence d'images cible est tenue |
| 6–7 | | réservés | envoyer 0 |
| 8–15 | 0xFF00 | définis par l'équipe | tout ce que votre équipe souhaite signaler |

Bits 0 à 3 tous positionnés (`status_word & 0x000F == 0x000F`) = **en bonne santé**.

Comment le simulateur classe chaque client (badge instructeur `VR n <worst>`, `GET /api/vr`) :

| Santé | Signification |
|---|---|
| `NO_REPLY` | connecté, n'a jamais envoyé de ligne d'état — normal, la voie retour est facultative |
| `OK` | bits 0 à 3 positionnés et `state` absent ou `OK` |
| `DEGRADED` | répond, mais un bit obligatoire n'est pas positionné ou `state` = `WARN` (badge orange) |
| `SILENT` | a déjà répondu, mais plus rien depuis 5 s (badge orange) |
| `ERROR` | `state` = `ERROR` (badge rouge) |

Les lignes d'état mal formées sont comptées (`rx_errors`, `last_error`) et ignorées ; la
connexion est maintenue.

## 8. Règles pour un client robuste

1. **Ignorer les champs et les types de message inconnus.** De nouveaux champs facultatifs peuvent
   apparaître dans `smo-vr/1` ; une modification incompatible deviendra `smo-vr/2`.
2. **Ignorer une ligne illisible** et continuer — ne jamais planter sur une entrée.
3. Les sauts et répétitions de `seq` sont normaux. `sim_time` peut sauter en arrière ou en avant.
4. Se reconnecter automatiquement (toutes les 2 s) lorsque la socket tombe.
5. Effectuer les entrées-sorties réseau hors du fil de rendu ; ne lui transmettre que la trame la plus récente.
6. Tester avec `vr_stub.py --chaos` avant le jour de la démonstration.

## 9. Fichiers à plat

`tools/vr_stub/sample_vr_frames.ndjson` — les messages exacts tels qu'ils circulent (`hello` puis
1134 lignes `state`, soit 1135 lignes au total), une orbite par pas de 5 s. `sample_vr_frames.csv` — les mêmes
trames mises à plat : noms imbriqués joints par `_`, vecteurs sous la forme `_x/_y/_z`, le
quaternion sous la forme `_x/_y/_z/_w`, booléens en 0/1. Le scénario (LEOP compressée) :

| t (s) | Événement |
|---|---|
| 0 | séparé, culbutage à environ 2,7 °/s, tout est replié |
| 300 | début de l'amortissement des vitesses angulaires (detumble) |
| 600 | déploiement de l'antenne |
| 900–1200 | acquisition du pointage nadir |
| 1300–1330 | déploiement de l'aile +Y |
| 1400–1430 | déploiement de l'aile −Y |
| 1440–1620 | le mécanisme d'entraînement du générateur solaire commence à suivre le Soleil |
| 1980–4000 | éclipse |
| 4300–4800 | basculement de 25° en roulis pour la prise de vue, maintien, basculement retour |
| 5670 | une orbite |

Enregistrer une séance réelle du simulateur avec
`tools/vr_stub/vr_client_example.py --record run.ndjson --csv run.csv` et
la rejouer avec `vr_stub.py --replay run.ndjson`.

## 10. Limitations connues (édition 1)

* Pendant les phases du chargeur d'amorçage (démarrage à froid, avant la LEOP), le simulateur ne
  propage pas l'attitude : le quaternion reste donc à sa valeur initiale jusqu'à ce que
  l'AOCS fonctionne. Le scénario du bouchon montre à la place un culbutage.
* Le bouchon utilise une orbite circulaire et une ombre cylindrique ; le simulateur utilise
  le SGP4 et une ombre conique avec pénombre. Les positions concordent à environ 50 km
  près sur la première orbite, et les heures d'éclipse à quelques secondes près pour l'époque de référence.
