# EOSAT-1 — Temps et horloges

**Référence du document :** EOSAT1-UM-TIME-012
**Édition :** 2.0
**Date :** 2026-08-17
**Classification :** NON CLASSIFIÉ — Opérations de mission

---

## 1. Vue d'ensemble

Les opérations d'EOSAT-1 font intervenir **deux horloges qui peuvent être en désaccord**, plus un
compteur dérivé :

* **GROUND TIME** (temps sol) — l'UTC tel que le détient la référence de temps du segment sol. Chaque
  affichage, journal, plan et entrée d'archive au sol est horodaté dans ce temps.
* **ONBOARD TIME** (temps bord) — l'horloge propre de l'OBC. Le satellite horodate avec elle chaque paquet
  qu'il émet.
* **MET** — temps écoulé depuis le lancement (*Mission Elapsed Time*), compté à partir de l'époque de la mission.

L'écart entre GROUND TIME et ONBOARD TIME est le sujet de ce chapitre. L'oscillateur de bord dérive, l'horloge repart
de l'époque après chaque redémarrage, et rien ne la corrige tant que le GPS ne
l'asservit pas. Résorber cet écart est une tâche de l'opérateur — voir **NOM-008 Synchronisation
d'horloge** et **LEOP-006 Synchronisation temporelle**.

Une troisième horloge, l'**horloge locale** de la console devant laquelle vous êtes assis, n'est pas du tout
une horloge de mission. Elle n'est légitime que pour trois usages exactement : cadencer le rafraîchissement
de l'affichage, les délais d'attente réseau, et les noms des journaux et fichiers de séance. Si un affichage du temps
mission suit l'horloge de votre poste au lieu du temps sol, c'est une anomalie — signalez-la.

## 2. Les horloges

| Horloge | Détenteur | Définition | Comportement |
|---|---|---|---|
| **GROUND TIME** | référence de temps du segment sol | UTC absolu. Ancré sur l'époque de la mission définie dans `orbit.yaml` `t0_epoch`. | Asservi à une référence externe (GPS/NTP). La source de vérité unique sur *le moment où les choses se produisent* au sol. |
| **ONBOARD TIME** | OBDH du satellite | l'horloge de l'OBC, en secondes CUC depuis l'époque de la mission. Démarre à **CUC 0 = 2000-01-01T12:00:00 UTC (J2000)** à la première mise en route et après chaque réinitialisation du chargeur d'amorçage. | Fonctionne librement avec la dérive de l'oscillateur ; peut être recalée par commande sol (S9,1) ou asservie au GPS (S8, fonction 80). |
| **MET** | dérivé, au sol | `ground_time - t0_epoch`, en secondes. | Calculé **une seule fois** et diffusé ; le MCS et le planificateur lisent cette valeur au lieu de la recalculer chacun à partir de sa propre idée de l'époque. |

Règles qui en découlent :

1. Le satellite horodate **chaque** paquet qu'il émet avec l'ONBOARD TIME — vérification
   S1, servitude S3, événements S5, rapports S11, TM stockée S15, transferts
   S13. Sans exception.
2. Le segment sol (MCS et planificateur) travaille en **GROUND TIME** — affichages,
   péremption, heures des alarmes, archive, historique des commandes, prédictions de passages et
   heures des activités du plan.
3. **Une seule époque sur la liaison : J2000.** Elle est déclarée une seule fois, dans
   `configs/eosat1/mission.yaml` :

   ```yaml
   time_epoch: "2000-01-01T12:00:00"   # live config, not decoration
   ```

   Elle est lue au chargement de la configuration et transmise à la couche paquets ; le littéral
   Python n'est qu'une valeur de repli pour fonctionner sans arborescence de configuration.

## 3. Le format de temps CUC

Le temps bord circule sous la forme d'un CUC ECSS (*CCSDS Unsegmented Time Code*) :

```
coarse : uint32 big-endian   secondes entières depuis l'époque de la mission (J2000)
fine   : uint16 big-endian   fraction de seconde, en unités de 1/65536 s  (~15.26 µs)
```

Il se trouve dans l'**en-tête secondaire TM PUS**, qui fait **9 octets** :

```
offset  size  field
 0       1    0x10 | pus_version
 1       1    service
 2       1    subtype
 3       4    CUC coarse (uint32 BE)
 7       2    CUC fine   (uint16 BE)
              ── 9 octets total ──
```

Conséquences utiles à connaître en console :

* l'en-tête primaire occupe les octets 0-5, l'en-tête secondaire les octets 6-14, et le
  **champ de données TM commence à l'octet 15** (il commençait à l'octet 13 avant le passage au CUC) ;
* les paquets TC ne sont pas concernés — l'en-tête secondaire TC fait toujours 3 octets
  `[0x20, service, subtype]` et ne porte aucun temps ;
* le corps des événements S5 porte toujours son propre CUC de 4 octets en secondes entières. Il s'agit
  de la valeur *grossière* du temps de l'en-tête, conservée pour compatibilité ; l'en-tête
  fait foi et fournit l'horodatage en pleine précision ;
* les fichiers de vidage écrits avant ce changement ne peuvent pas être décodés par les outils actuels —
  le champ de données est décalé de deux octets et le CRC échoue. Supprimer
  les vidages antérieurs à la migration plutôt que d'essayer de les lire.

## 4. `time_ref` — comment l'OBC croit connaître l'heure

`obdh.time_ref` (**0x0A13**, SID HK 4) est la déclaration propre de l'OBC sur sa
référence de temps. Lisez-la avant de lire l'horloge.

| Valeur | Nom | Signification | Dérive ? |
|---|---|---|---|
| 0 | `NONE` | jamais réglée depuis la dernière réinitialisation du chargeur d'amorçage. Fonctionne librement depuis CUC 0 — l'OBC se croit le 1er janvier 2000. | oui |
| 1 | `GROUND` | réglée en dernier par commande sol (S9,1 `SET_TIME`). | oui |
| 2 | `GPS` | asservie au GPS avec un point GPS valide. Maintenue sur le temps vrai à chaque pas. | **non** |
| 3 | `HOLDOVER` | était asservie au GPS, le point GPS a été perdu. Fonctionne librement à partir de sa dernière valeur. | oui |

Paramètres associés, tous dans le **SID HK 4 (plateforme/OBDH, période de 8 s)** :

| Paramètre | ID | Type | Remarques |
|---|---|---|---|
| `obdh.obc_time` | `0x0309` | uint32 | secondes CUC grossières |
| `obdh.obc_time_fine` | `0x0A12` | uint16 | fraction de seconde, 1/65536 s |
| `obdh.time_ref` | `0x0A13` | uint8 | tableau ci-dessus |
| `obdh.time_since_sync_s` | `0x0A14` | uint32 | secondes bord depuis la dernière synchronisation réussie. Sature au lieu de repasser à zéro ; `4294967295` (0xFFFFFFFF) signifie **jamais synchronisé**. Limite sol : jaune à 12 h, rouge à 24 h |

`obdh.uptime` (`0x0308`) compte les secondes depuis l'**amorçage**, et non depuis l'époque. Il
sert à repérer un redémarrage et à contrôler une marche ; ce n'est jamais un horodatage.

## 5. Le modèle de dérive

L'oscillateur est un TCXO réaliste. Sa dérive effective est tirée **une seule fois par exécution**
dans le générateur aléatoire (RNG) initialisé de chaque modèle, de sorte qu'une graine donnée produit toujours la même horloge :

```
clock_drift_ppm = clock_drift_ppm_nominal + N(0, clock_drift_sigma_ppm)
```

`configs/eosat1/subsystems/obdh.yaml` :

```yaml
clock_drift_ppm_nominal: 12.0     # ~1 s/day
clock_drift_sigma_ppm: 4.0        # per-unit spread
clock_gps_discipline: true        # a GPS sync latches into disciplined mode
clock_jump_event_threshold_s: 1.0 # |jump| that raises an S5 clock event
clock_drift_failure_ppm: 500.0    # ppm forced by the `clock_drift` injection
```

À la valeur nominale de 12 ppm, l'horloge avance d'environ **1 seconde par jour** — de quoi justifier une
synchronisation par quart, un écart visible mais pas spectaculaire au bout d'une semaine. À chaque pas, hors
asservissement GPS :

```
obc_time_s += dt_sim * (1 + clock_drift_ppm * 1e-6)
```

Un oscillateur dégradé fait mordre la dérive bien plus vite que la valeur nominale —
de l'ordre de **500 ppm (~43 s/jour)**, ce qui se voit au cours d'un seul quart.

La dérive étant une *vitesse*, l'erreur mesurée croît avec
`time_since_sync_s`. Un décalage de 3 secondes avec `time_since_sync_s` = 3 jours correspond à une
horloge saine d'environ 12 ppm. Les mêmes 3 secondes dix minutes après une synchronisation, non.

## 6. Asservissement GPS et maintien (holdover)

* **`OBC_GPS_TIME_SYNC`** (S8, fonction 80) exige un point GPS 3D ou mieux —
  `aocs.gps_fix` (`0x0274`) >= 2. Sinon, la commande est refusée.
* En cas de succès, l'horloge est réglée sur le temps vrai, `time_ref` passe à **GPS** et
  `time_since_sync_s` repart de zéro. Tant que `time_ref = GPS` et que le point GPS tient, l'horloge
  est maintenue sur le temps vrai à chaque pas et **n'accumule aucune dérive**.
* **La perte du point GPS** fait passer `time_ref` à **HOLDOVER**, lève
  `OBC_TIME_REF_LOST` (`0x030E`), et la dérive reprend là où se trouvait l'horloge.
* **Le retour du point GPS** rétablit automatiquement l'asservissement, lève `OBC_TIME_SYNC`
  (`0x030D`) avec le saut qu'il a fallu effectuer, et ramène `time_ref` à GPS.
* Avec `clock_gps_discipline: false`, une synchronisation GPS serait un réglage ponctuel
  (`time_ref = GROUND`) et la dérive se poursuivrait. La valeur livrée est `true`.

Un réglage sol et une synchronisation GPS ne sont **pas** la même opération :

| | `SET_TIME` sol (S9,1) | `OBC_GPS_TIME_SYNC` (S8, fonction 80) |
|---|---|---|
| source de vérité | votre horloge sol, corrigée du temps de propagation et du délai de traitement | le récepteur GPS propre au satellite |
| `time_ref` obtenu | `GROUND` | `GPS` (puis `HOLDOVER` si le point GPS est perdu) |
| dérive ensuite | se poursuit au taux tiré (ppm) | aucune tant que le point GPS est valide |
| précision | aussi bonne que votre calcul de correction | suit exactement le temps vrai |
| nécessite un passage | oui — c'est une commande envoyée vers le bord | oui pour la commander, mais la réacquisition ultérieure est autonome |
| disponible en mode chargeur d'amorçage | **non** — rejetée avant l'amorçage | non |

## 7. Événements d'horloge

Chaque recalage de l'horloge lève un événement S5 portant le **saut signé en secondes** —
un simple « heure réglée » ne dirait pas de combien l'horloge était décalée, ce qui est tout
l'intérêt de l'exercice. Les sauts inférieurs à `clock_jump_event_threshold_s`
(1.0 s) sont supprimés, de sorte qu'une resynchronisation de routine d'une horloge saine n'encombre pas
le journal des événements.

| Événement | ID | Levé par |
|---|---|---|
| `OBC_TIME_SET` | `0x030C` | réglage sol S9,1. Texte de la forme `OBC clock set by ground (S9,1): jump +12.345s, time_ref=GROUND` |
| `OBC_TIME_SYNC` | `0x030D` | synchronisation GPS — commandée, ou automatique à la réacquisition après un maintien |
| `OBC_TIME_REF_LOST` | `0x030E` | point GPS perdu pendant l'asservissement ; `time_ref` -> HOLDOVER, la dérive reprend |

Autre conséquence : une synchronisation GPS dont le saut dépasse **5 s** force l'AOCS en
SAFE_BOOT (événement `0x020F`), car la solution d'attitude a été calculée avec
une horloge qui vient de bouger. Il faut s'y attendre après un long maintien ou un redémarrage ; c'est
un effet réel, pas un artefact.

## 8. Comportement au redémarrage

**Le chargeur d'amorçage réinitialise l'horloge.** Sur `OBC_REBOOT`, ou en coupant puis en rétablissant
la ligne EPS `obc` :

* `obc_time_s = 0` — l'OBC est revenu à J2000 ;
* `time_ref = NONE` ;
* `time_since_sync_s` indique « jamais synchronisé » (`0xFFFFFFFF`) ;
* `uptime` = 0 et `reboot_count` s'incrémente.

L'amorçage de l'image applicative (`OBC_BOOT_APP`) ne restaure **pas** le temps.
L'horloge est toujours à J2000 et doit être resynchronisée — c'est exactement l'enchaînement LEOP :
amorcer l'application, puis effectuer la synchronisation temporelle. `SET_TIME` ne figure pas dans la liste
d'autorisation des commandes du chargeur d'amorçage : elle ne peut être envoyée qu'une fois l'image applicative en marche.

Une horloge qui indique une date de l'an 2000 ne trahit donc pas un bogue d'époque ; c'est un
OBC non synchronisé. Vérifier `obdh.uptime` et `obdh.reboot_count` avant de conclure
quoi que ce soit sur la dérive.

## 9. Lire la corrélation en console

La console MCS affiche côte à côte :

* **GROUND UTC** — l'horloge sur laquelle fonctionne tout ce qui est au sol ;
* **ONBOARD** — `obdh.obc_time` + `obdh.obc_time_fine` décodés par rapport à l'époque
  de la mission ;
* **`time_ref`** — NONE / GROUND / GPS / HOLDOVER ;
* **temps depuis la synchronisation** — `obdh.time_since_sync_s`, ou « never ».

Le nombre qui compte est le **décalage**, `ONBOARD - GROUND UTC` ; la console
le signale dès qu'il dépasse le seuil d'affichage. Les deux lectures vieillissent : la valeur bord
n'est pas plus fraîche que le dernier paquet SID 4 ; avec une cadence de 8 s, il faut donc s'attendre à
jusqu'à ~8 s de péremption, plus le temps de propagation. C'est pourquoi NOM-008 vous fait demander un
SID HK 4 frais et un rapport de temps TM(9,2) explicite au lieu de lire ce qui
se trouve à l'écran à ce moment-là.

Deux voies indépendantes transportent la même horloge — le rapport de temps TM(9,2) et
`0x0309` dans le SID HK 4. Les recouper : un désaccord supérieur à la période
d'échantillonnage du SID 4 signifie que le service de temps et l'échantillonneur de servitude
ne s'accordent pas sur l'horloge, ce qui est une panne différente d'une horloge fausse.

Le satellite ne peut pas connaître son propre décalage par rapport au temps vrai : celui-ci n'est donc pas
transmis au sol, puisque le satellite ne peut pas mesurer l'erreur de sa propre horloge. Le sol
la déduit de la corrélation temporelle, et cette déduction est
la réponse de l'exercice, pas un affichage opérationnel.

## 10. Télécommandes datées (S11) et planificateur

Le plan bord se déclenche sur l'**ONBOARD TIME**. C'est le plan propre au satellite,
et il n'a rien d'autre sur quoi s'appuyer.

Le planificateur travaille en temps sol : les heures de début des activités sont des instants absolus en temps simulé,
UTC ISO-8601. Lors de l'envoi, le planificateur transmet cet instant en temps simulé au MCS,
et c'est le **MCS** qui effectue l'unique conversion en étiquette temporelle CUC au moyen de sa
corrélation temporelle (ancrée sur `0x0309`), si bien que l'étiquette tombe sur l'horloge propre
de l'OBC.

Rien dans la chaîne ne masque une erreur d'horloge, et c'est voulu :

* avec une corrélation à jour, l'étiquette est exprimée sur l'horloge de l'OBC et
  l'activité s'exécute à l'heure sol prévue même si l'horloge est décalée ;
* si l'horloge a bougé depuis la prise de la corrélation — le cas habituel d'un
  plan envoyé lors d'un passage et exécuté au suivant, avec de la dérive entre les deux —
  l'activité se déclenche **en avance de l'avance de l'horloge** et en retard de son
  retard. Une horloge qui avance de 40 s exécute votre plan 40 s trop tôt.

Le planificateur ne précompense pas. Plier le plan à une horloge fausse
laisse l'horloge fausse et masque la raison de la corriger. Le remède est une
synchronisation d'horloge avant que le plan n'entre en jeu ; après la synchronisation, le même plan, inchangé, se déclenche
au moment annoncé.

Si l'horloge n'a jamais été réglée (`time_ref = NONE`, encore proche de J2000), être
particulièrement prudent avec les étiquettes temporelles calculées directement à partir de l'époque : une telle étiquette
peut se situer des décennies dans le futur de l'OBC, et la commande ne se déclenche tout simplement jamais.

## 11. Le MET et son origine

`MET = ground_time - t0_epoch`. Il est calculé une seule fois et diffusé ; le MCS et le
planificateur lisent tous deux cette valeur au lieu de la recalculer à partir de leur propre idée d'une
époque de départ — une définition, un nombre, partout.

Le MET n'est pas une grandeur bord et n'est pas transmis au sol. Ne pas le confondre avec
`obdh.uptime`, qui compte depuis le dernier amorçage de l'OBC, ni avec l'accumulateur
interne de temps écoulé du module FDIR.

## 12. Mises en garde

* **Mise en garde sur le redémarrage.** La source de temps sol est déterminée au démarrage du MCS ou du
  planificateur. La changer impose de redémarrer le service concerné.
* La configuration sol ne modifie jamais le temps du satellite : le temps bord n'est modifié que
  par télécommande (S9,1) ou par l'asservissement GPS.
* Rien d'autre que l'OBDH du satellite n'écrit le temps bord, et seule la
  référence de temps sol détient le temps sol.

## 13. Diagnostic rapide

| Symptôme | Que regarder | Cause probable |
|---|---|---|
| Le temps bord indique l'an 2000 | `time_ref` = NONE, `uptime` faible, `reboot_count` incrémenté | L'OBC a redémarré ; le chargeur d'amorçage a réinitialisé l'horloge. Resynchroniser (LEOP-006, ou NOM-008 étapes 3-5) |
| Le décalage croît régulièrement d'environ 1 s/jour | `time_ref` = GROUND ou HOLDOVER, `time_since_sync_s` | Dérive normale de l'oscillateur, d'environ 12 ppm |
| Le décalage croît environ 40 fois plus vite | un oscillateur dégradé (~500 ppm) | panne de l'oscillateur — émettre un rapport d'anomalie |
| Décalage figé à zéro | `time_ref` = GPS | Asservi au GPS ; comportement correct |
| `time_ref` passé à HOLDOVER | événement `0x030E`, `aocs.gps_fix` < 2 | Point GPS perdu ; la dérive a repris |
| Synchronisation GPS refusée | `aocs.gps_fix` (`0x0274`) | Nécessite un point GPS 3D (>= 2) |
| `SET_TIME` rejetée | `obdh.sw_image` (`0x0311`) | Toujours en mode chargeur d'amorçage ; amorcer d'abord l'image applicative |
| L'AOCS est tombé en SAFE_BOOT juste après une synchronisation | événement `0x020F`, saut dans `0x030D` | Le saut de synchronisation a dépassé 5 s |
| Une activité programmée s'est déclenchée en avance ou en retard | le décalage et `time_since_sync_s` au moment de l'envoi | Une erreur d'horloge, pas une erreur de planification. Synchroniser, puis revérifier |


---

## Annexe A — Source de temps du système de formation

**Manual-Scope:** system — cette annexe ne s'applique que lorsque le segment sol
est connecté au simulateur de formation au lieu d'un satellite. Elle n'a pas
d'équivalent en opérations de vol, où le temps sol provient de la propre référence
de la station.

Un réglage unique détermine si le **MCS** et le **planificateur** suivent le temps
simulé ou l'UTC réel. Il n'affecte **pas** le temps du satellite : le temps bord provient toujours
de la télémesure et n'est jamais synthétisé au sol.

### A.1 Ordre de priorité

Pour chaque service (le premier l'emporte) :

1. **Option de ligne de commande** — `--time-source sim|real`
2. **Variable d'environnement** — `SMO_TIME_SOURCE` (`sim` | `real`)
3. **Champ de la configuration de mission** — `time_source:` dans `configs/eosat1/mission.yaml`
4. **Valeur par défaut intégrée** — `"sim"`

Le paramètre associé `sim_state_url` (le point d'accès du simulateur interrogé pour `sim_time`,
`speed` et `met_s`) se résout de la même façon :

1. `--sim-state-url <url>`
2. `SMO_SIM_STATE_URL`
3. `sim_state_url:` dans `mission.yaml`
4. Par défaut `http://<connect_host>:8080/api/state`

### A.2 Configuration de mission

```yaml
time_epoch: "2000-01-01T12:00:00"   # the CUC epoch — live config
time_source: sim                    # "sim" | "real"
# sim_state_url: http://localhost:8080/api/state   # optional override
```

### A.3 start.sh

```bash
SMO_TIME_SOURCE="${SMO_TIME_SOURCE:-sim}"          # --real sets this to real
export SMO_SIM_STATE_URL="${SMO_SIM_STATE_URL:-http://localhost:8080/api/state}"
```

- `./start.sh` -> source de temps **sim** (par défaut).
- `./start.sh --real` -> **real** (horloge murale).
- `SMO_TIME_SOURCE=real ./start.sh` -> real, via la variable d'environnement.

La source de temps active est rappelée dans la bannière de démarrage.

### A.4 Synchronisation en boucle fermée sur la simulation

En mode sim, l'horloge sol est synchronisée en boucle fermée sur le simulateur au lieu d'être
reconstruite localement :

* le **MCS** interroge `sim_state_url` toutes les 1,5 s environ, lit `sim_time` et `speed`
  et réancre son horloge ; entre deux interrogations, il extrapole selon `speed`, si bien que
  la dérive dans le pire cas est bornée par l'intervalle d'interrogation. Les pauses, changements
  de vitesse et chargements de points de reprise sont ainsi suivis correctement ;
* le **planificateur** conserve le même type d'ancrage (`_sim_anchor_time` /
  `_sim_anchor_wall` / `_sim_anchor_speed`), rafraîchi au plus ~1 fois/s, et renvoie
  `anchor_sim_time + (now - anchor_wall) x speed`. Une discontinuité supérieure à
  la tolérance configurée est traitée comme un saut : les caches de contacts et de traces au sol
  sont immédiatement vidés.

**Replis :** en cas d'échec d'une interrogation, les deux services conservent le dernier ancrage. Si le
simulateur n'a jamais été joignable, ils se rabattent sur l'UTC de l'horloge murale et l'indiquent — le
planificateur signale `wall_clock_fallback` sur `/api/time-source` et journalise un avertissement,
car un badge SIM affiché sur des données d'horloge murale est le moyen le plus sûr pour des opérateurs de planifier
sur le mauvais jour.

Les âges au sol se mesurent en secondes **sim** : mettre le simulateur en pause fige
la péremption au lieu de rendre tout périmé, et une exécution à 60x vieillit
la télémesure 60 fois plus vite. C'est voulu.
