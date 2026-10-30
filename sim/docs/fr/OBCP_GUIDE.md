# Procédures de contrôle bord (OBCP) — service PUS 18

EOSAT-1 permet l'**exécution de scripts à bord** au moyen du service PUS 18. Une OBCP est une
liste ordonnée d'étapes ; chaque étape associe un *délai relatif* à une *TC PUS complète*
que le satellite s'applique à lui-même à l'expiration du délai. Comme les
étapes s'exécutent à bord, une procédure continue de se dérouler après la LOS — contrairement au
`ProcedureRunner` côté MCS, qui exige un contact actif pour chaque étape.

| Capacité | Lieu d'exécution | Survit à la LOS |
|---|---|---|
| Procédures MCS (`configs/eosat1/procedures/`) | au sol | non |
| TC datée S11 | à bord, exécution unique | oui |
| Événement-action S19 | à bord, fonction unique sans paramètre | oui |
| **OBCP S18** | **à bord, séquence multiétape** | **oui** |

---

## 1. Format des procédures

### 1.1 Sur disque (`configs/eosat1/obcp/*.yaml`)

Chaque fichier YAML de `configs/eosat1/obcp/` est préchargé à l'amorçage (comme les règles S19
de `configs/eosat1/monitoring/s19_rules.yaml`) : les étudiants peuvent donc activer
une procédure immédiatement, sans rien charger.

```yaml
procedure:
  id: 1                       # uint16, unique; used by TC(18,2/3/4)
  name: pass_preparation      # free text, shown in logs and events
  description: "..."          # optional, documentation only
  steps:
    - delay_s: 0              # seconds of SIM time, relative to previous step
      service: 8              # PUS service of the step TC
      subtype: 1              # PUS subtype
      func_id: 19             # optional; prepended to the data field (S8 calls)
      data_hex: "02"          # optional; appended as raw hex bytes
```

Le chargeur (`ObcpManager.load_from_dir`) transforme chaque étape en un véritable paquet TC CCSDS/PUS
au moyen de `build_tc_packet`, avec l'APID `0x1AC` pour le marquer comme
généré par le satellite. Un fichier mal formé est journalisé puis ignoré — il ne bloque jamais
l'amorçage.

Limites : **16 procédures**, **32 étapes chacune** (`obcp.py`, reprises dans
`configs/eosat1/mcs/pus_services.yaml` sous `s18`).

### 1.2 En liaison montante (données d'application de la TC(18,1))

```
proc_id      uint16
name_len     uint8
name         name_len bytes, UTF-8
n_steps      uint8
  per step:
    delay_s  float32 (big-endian), seconds relative to the previous step
    tc_len   uint16
    tc       tc_len bytes — a COMPLETE PUS TC packet (primary + secondary + CRC)
```

`ObcpManager.encode_load_blob(proc_id, name, steps)` construit ce bloc binaire
côté sol (utilisé par les tests) ; `parse_load_blob` le décode à bord.

---

## 2. Télécommandes

| TC | Nom | Données | Effet |
|---|---|---|---|
| **18,1** | `OBCP_LOAD` | bloc binaire sérialisé (§1.2) | Charger directement ou remplacer une procédure. Le remplacement d'une procédure en cours d'exécution interrompt d'abord celle-ci. |
| **18,2** | `OBCP_DELETE` | `proc_id(2)` | Supprimer une procédure (en l'interrompant si elle s'exécute). |
| **18,3** | `OBCP_START` | `proc_id(2)` `[+ param(1)]` | Activer. La première étape se déclenche une fois écoulé son propre `delay_s` (`delay_s: 0` → pas suivant). |
| **18,4** | `OBCP_STOP` | `proc_id(2)` | Interrompre une procédure en cours d'exécution. **`proc_id = 0` les arrête toutes.** |
| **18,6** | `OBCP_STATUS_REPORT` | — | Demander l'état → **TM(18,7)**. |

Structure de la **TM(18,7)** :

```
count       uint8
  per entry:
    proc_id       uint16
    status        uint8   0 = IDLE (loaded), 1 = RUNNING
    current_step  uint8   index of the step being waited on
    n_steps       uint8
```

Les échecs (`proc_id` inconnu, mémoire pleine, bloc binaire illisible, démarrage d'une
procédure déjà en cours) positionnent l'erreur du répartiteur : le moteur renvoie alors un
**échec d'exécution S1.8** — le chemin de vérification normal.

---

## 3. Sémantique d'exécution

* **Temps simulé.** `ObcpManager.tick(dt_sim)` est appelé depuis la boucle principale du moteur
  juste après le programmateur S11 (`engine._tick_once`). Les délais sont décomptés en
  secondes *simulées* : les procédures respectent donc automatiquement la vitesse de simulation
  choisie par l'enseignant — un pas à 10× consomme 10 s de délai, et plusieurs étapes peuvent se déclencher
  au cours d'un même pas.
* **Même chemin de répartition que le sol.** Les étapes sont exécutées par
  `engine._dispatch_tc`, exactement comme les TC reçues en liaison montante. Toutes les règles d'acceptation
  s'appliquent donc : la liste des TC autorisées en mode amorçage, le contrôle d'alimentation de l'EPS, le contrôle
  d'accessibilité sur le bus, la validation du sous-type et la vérification S1 complète (S1.1 / S1.3 /
  S1.7 ou S1.8). Une étape ne peut rien faire qu'un opérateur ne pourrait faire.
* **`source=OBCP`.** Les exécutions autogénérées sont étiquetées dans le journal
  (`OBCP <id> step <n>: dispatching S8.1 (source=OBCP)`) et la description de chaque événement OBCP
  nomme la procédure : une action autocommandée n'est jamais confondue
  avec une commande sol.
* **Arrêt sur échec.** Une étape mal formée ou rejetée à l'acceptation lève
  `OBCP_STEP_FAILED` et **interrompt le reste de la procédure** — elle ne
  saute pas silencieusement à la suite.

### Événements (S5, donc utilisables comme déclencheurs S19)

| ID | Nom | Gravité |
|---|---|---|
| `0x0700` | `OBCP_STARTED` | INFO |
| `0x0701` | `OBCP_COMPLETED` | INFO |
| `0x0702` | `OBCP_ABORTED` | MEDIUM |
| `0x0703` | `OBCP_STEP_FAILED` | MEDIUM |

Les quatre figurent dans `configs/eosat1/events/event_catalog.yaml`.

### Points de reprise

La mémoire des procédures *et* l'état de l'interpréteur (indice d'étape, délai restant,
paramètre d'activation) sont capturés par `BreakpointManager.save()` sous la clé `obcp`
et restaurés par `load()`, selon le même schéma `get_state`/`set_state`
que `OnboardTMStorage`. Une procédure en cours d'exécution au moment où l'enseignant
a enregistré un point de reprise reprend exactement à la même étape après un chargement.

---

## 4. Exemples fournis

Les trois n'utilisent que des fonctions S8 réellement routées par
`service_dispatch.py` (vérifié par `test_example_steps_use_only_implemented_funcs`).

| ID | Nom | Action |
|---|---|---|
| 1 | `pass_preparation` | Ligne EPS `ttc_tx` allumée → PA allumé → déploiement de l'antenne → balise éteinte → réglage du débit TM → émetteur du transpondeur allumé |
| 2 | `safe_mode_entry` | EPS en SAFE → mode charge utile éteint → ligne charge utile coupée → ligne du refroidisseur FPA coupée → AOCS en SAFE |
| 3 | `payload_checkout` | Ligne charge utile allumée → STANDBY → IMAGING → acquisition (lat./long.) → STANDBY |

Indices des lignes d'alimentation pour les fonctions S8 19/20 (`power_line_on` / `power_line_off`) :

```
0 obc   1 ttc_rx   2 ttc_tx   3 payload
4 fpa_cooler   5 htr_bat   6 htr_obc   7 aocs_wheels
```

---

## 5. Exécution depuis le MCS

`configs/eosat1/commands/tc_catalog.yaml` expose cinq commandes sous **S18** :
`OBCP_LOAD`, `OBCP_DELETE`, `OBCP_START`, `OBCP_STOP`, `OBCP_STATUS_REPORT`.

Déroulement type dans l'interface de commande du MCS :

1. **`OBCP_STATUS_REPORT`** (sans champ) — la réponse TM(18,7) liste chaque procédure
   chargée avec son état d'exécution, ce qui confirme la présence des procédures 1–3 chargées à l'amorçage.
2. **`OBCP_START`** avec `proc_id = 1`, `param = 0` — lance la préparation du passage.
   Attendre S1.1/S1.3/S1.7 pour la TC S18 elle-même, puis un événement `OBCP_STARTED`,
   puis un jeu de vérifications S1 par étape au fil du déroulement de la procédure.
3. **`OBCP_STATUS_REPORT`** de nouveau — la procédure 1 affiche désormais `status = 1` (RUNNING)
   et un `current_step` qui progresse.
4. **`OBCP_STOP`** avec `proc_id = 1` (ou `0` pour toutes) s'il faut
   abandonner l'exécution ; **`OBCP_DELETE`** la retire complètement de la mémoire.

**Charger une nouvelle procédure depuis le sol.** `OBCP_START/STOP/STATUS/DELETE`
agissent sur des procédures préchargées et sont pleinement utilisables depuis l'interface du MCS. Un chargement
multiétape *complet* (`OBCP_LOAD`) exige un bloc binaire sérialisé contenant des paquets TC
imbriqués, que le catalogue ne peut exprimer que sous la forme d'un champ hexadécimal brut `bytes` — la
même contrainte que pour la commande S11 `SCHEDULE_TC`. En pratique, les nouvelles procédures
sont ajoutées sous forme de fichier YAML dans `configs/eosat1/obcp/` (préchargé à l'amorçage), ou
construites par programme avec `ObcpManager.encode_load_blob` depuis un test ou un
script. L'entrée du catalogue est conservée pour un usage avancé ou brut.

---

## 6. Limitations connues

* Pas de logique conditionnelle, de boucles ni d'étapes `wait_for <condition>` — une procédure est
  une séquence linéaire minutée. L'autonomie conditionnelle relève de S19 (fonction unique) ou
  de la FDIR.
* L'octet `param` d'activation est stocké et rapporté, mais pas encore exploité par
  l'interpréteur d'étapes (pas de substitution de paramètres au niveau de l'étape).
* Les délais sont relatifs et monotones ; il n'existe pas d'étape en temps absolu (utiliser S11 pour
  dater la TC `OBCP_START` elle-même si une procédure doit commencer à un CUC fixé).
* Point *non* lié aux OBCP (l'ancien défaut de débit est corrigé) : la fonction de réglage
  du débit TM du TTC (fonction S8 65, `TTC_SET_DATA_RATE`) règle `data_rate_mode`, le palier commandé
  à partir duquel le pas de simulation du TTC détermine `tm_data_rate`. HIGH exige en outre
  le mode DOWNLINK (fonction S8 79) et une antenne déployée, qu'il soit commandé directement
  ou depuis une OBCP.
