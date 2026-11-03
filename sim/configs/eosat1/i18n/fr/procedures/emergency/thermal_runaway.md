# EMG-006 : Emballement thermique

**Catégorie :** Urgence
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** directeur de vol
**Difficulté :** Avancé

## Objectif
Réagir à un emballement thermique, c'est-à-dire un circuit de réchauffeur bloqué sur ON et une
zone thermique associée dont la température monte de façon incontrôlée. Cette procédure tente
de couper le réchauffeur par les commandes normales, applique un forçage manuel et, si le
réchauffeur ne répond pas, déleste sa ligne d'alimentation via l'EPS pour arrêter le chauffage. La
température est ensuite surveillée pour confirmer que l'emballement a été enrayé.

## Prérequis
- [ ] Hausse de température détectée sur une zone thermique dont le réchauffeur indique ON en permanence
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol prévenu — il s'agit d'une procédure d'URGENCE
- [ ] Opérateur EPS disponible pour délester des lignes d'alimentation si nécessaire

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| tcs.temp_battery | 0x0407 | À surveiller si le réchauffeur batterie est en cause |
| tcs.temp_obc | 0x0406 | À surveiller si le réchauffeur OBC est en cause |
| tcs.temp_thruster | 0x0409 | À surveiller si le réchauffeur du propulseur est en cause |
| tcs.htr_battery | 0x040A | État du réchauffeur (0=off, 1=on) |
| tcs.htr_obc | 0x040B | État du réchauffeur |
| tcs.htr_thruster | 0x041B | État du réchauffeur |
| tcs.temp_panel_px | 0x0400 | Températures des panneaux, pour le contexte |
| tcs.temp_panel_mx | 0x0401 | Températures des panneaux, pour le contexte |
| eps.pl_htr_bat | 0x0115 | État de la ligne d'alimentation — réchauffeur batterie |
| eps.pl_htr_obc | 0x0116 | État de la ligne d'alimentation — réchauffeur OBC |
| eps.line_current_5 | 0x011D | Courant de la ligne du réchauffeur batterie |
| eps.line_current_6 | 0x011E | Courant de la ligne du réchauffeur OBC |
| eps.bus_voltage | 0x0105 | Surveiller la tension du bus |
| eps.power_cons | 0x0106 | Surveiller la consommation |

## Commandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| HEATER_BATTERY | 8 | 1 | 40 | Réchauffeur batterie marche/arrêt |
| HEATER_OBC | 8 | 1 | 41 | Réchauffeur OBC marche/arrêt |
| HEATER_THRUSTER | 8 | 1 | 42 | Réchauffeur du propulseur marche/arrêt |
| HEATER_SET_SETPOINT | 8 | 1 | 44 | Modifier les consignes de thermostat du réchauffeur |
| HEATER_AUTO_MODE | 8 | 1 | 45 | Revenir au thermostat autonome |
| EPS_POWER_ON | 8 | 1 | 19 | Rétablir la ligne d'alimentation du réchauffeur |
| EPS_POWER_OFF | 8 | 1 | 20 | Délester la ligne d'alimentation du réchauffeur |

## Déroulement

**Remarque sur l'exécutabilité.** Cette fiche est `runnable: {kind: markdown}` et sa
branche lisible par la machine est le réchauffeur **batterie** (ligne EPS 5, circuit 0) — la
zone où un emballement est réellement dangereux, car un élément au lithium au-delà de
50 °C est un danger chimique et non un simple désagrément. Les variantes OBC (ligne 6,
circuit 1) et propulseur (circuit 2) sont données en remarques à côté de chaque
étape ; pour les exécuter, substituer les arguments de commande indiqués et suivre la même
structure de branchement. Rendre une seule zone exécutable et nommer les substitutions est
honnête ; paramétrer une ligne `**TC:**` sur « la zone concernée » produirait une
fiche qui paraît exécutable et n'envoie rien.

### Étape 1 : Détecter la hausse de température et identifier la zone concernée
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — données de servitude TCS
**Verify:** Identifier la température qui monte anormalement :
- `tcs.temp_battery` (0x0407) — si elle dépasse 40 °C avec `tcs.htr_battery` (0x040A) = 1
- `tcs.temp_obc` (0x0406) — si elle dépasse 55 °C avec `tcs.htr_obc` (0x040B) = 1
- `tcs.temp_thruster` (0x0409) — si elle monte avec `tcs.htr_thruster` (0x041B) = 1
**Verify:** `tcs.htr_battery == 1` (0x040A, timeout 70 s) — la signature de
l'emballement : le réchauffeur indique ON. La structure HK SID 3 est à 60 s ; le
délai maximal doit donc dépasser un intervalle de collecte, faute de quoi le contrôle entre en concurrence avec la liaison descendante.
**Verify:** Consigner la température et confirmer qu'elle est au-dessus de la consigne d'arrêt du réchauffeur
(le réchauffeur aurait déjà dû se couper).
**Note:** Consignes issues de `subsystems/tcs.yaml` : batterie ON +5 °C / OFF +10 °C
(8 W), OBC ON -10 °C / OFF -5 °C (4 W), lit catalytique du propulseur ON +190 °C / OFF +230 °C
(12 W). Si la température est nettement au-dessus de ces valeurs
et que le réchauffeur est toujours ON, le thermostat est défaillant.
**GO/NO-GO:** Emballement thermique confirmé — commander l'arrêt du réchauffeur

### Étape 2 : Commander l'arrêt du réchauffeur par la commande normale
**LABEL:** `STEP-2`
**Note:** Le thermostat du réchauffeur batterie ne fonctionne que si la ligne d'alimentation EPS 5
(`eps.pl_htr_bat`, 0x0115) est alimentée. Un réchauffeur sur une ligne hors tension ne peut pas répondre
à une commande d'arrêt, puisqu'il ne fonctionne pas du tout — la ligne 5 est donc alimentée
EN PREMIER, sans condition. `EPS_POWER_ON` sur une ligne déjà sous tension est sans effet,
ce qui explique que ce soit une étape linéaire et non un branchement supplémentaire.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) — ligne du réchauffeur batterie
**TC:** `HEATER_BATTERY(on=0)` (Service 8, Subtype 1, func_id 40) — commander l'arrêt du réchauffeur
**Note:** Réchauffeur OBC : `HEATER_OBC(on=0)` (func_id 41) avec `EPS_POWER_ON(line_index=6)`.
Réchauffeur du propulseur : `HEATER_THRUSTER(on=0)` (func_id 42).
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — relire l'état du réchauffeur
**BRANCH:** `tcs.htr_battery == 0` -> GO `STEP-5` | NO-GO `STEP-3` (timeout 70 s)
**Note:** GO — le réchauffeur a obéi ; il n'y a rien à forcer ni à
délester, et les étapes 3 et 4 ne sont donc PAS exécutées. NO-GO — le réchauffeur n'a pas répondu ; on enchaîne
sur le forçage des consignes. C'est cet embranchement qui rend la fiche sûre à
exécuter : exécutée à plat, l'étape 4 délesterait la ligne d'alimentation du réchauffeur sur un satellite
dont le réchauffeur s'était déjà coupé de lui-même.

### Étape 3 : Commander un forçage manuel par modification des consignes
**LABEL:** `STEP-3`
**Note:** Forcer le thermostat dans un état où il ne peut jamais demander de chauffe,
en plaçant les deux consignes bien au-dessus de toute température que la zone peut atteindre.
**TC:** `HEATER_SET_SETPOINT(circuit=0, on_temp=100.0, off_temp=100.0)` (Service 8, Subtype 1, func_id 44) — circuit 0 = batterie
**Note:** OBC = circuit 1, propulseur = circuit 2.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**BRANCH:** `tcs.htr_battery == 0` -> GO `STEP-5` | NO-GO `STEP-4` (timeout 70 s)
**Note:** Ici, NO-GO signifie que la commande logicielle est inopérante : le relais ou l'interrupteur
est bloqué fermé, et il ne reste plus qu'à couper l'alimentation.

### Étape 4 : Délester la ligne d'alimentation du réchauffeur via l'EPS
**LABEL:** `STEP-4`
**Note:** Dernier recours. Couper l'alimentation du réchauffeur en mettant hors tension sa ligne EPS.
**TC:** `EPS_POWER_OFF(line_index=5)` (Service 8, Subtype 1, func_id 20) — ligne du réchauffeur batterie
**Note:** Le réchauffeur OBC est sur la ligne 6. Le réchauffeur du propulseur n'a pas de ligne commutable
dédiée ; si c'est la zone du propulseur qui est concernée, cette étape n'est pas disponible et
l'escalade s'arrête à l'étape 3 — le consigner et se reporter à la section Contingence.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS pour l'état de la ligne
**Verify:** `eps.pl_htr_bat == 0` (0x0115, timeout 10 s) — la ligne est délestée
**Verify:** `eps.line_current_5 == 0` (0x011D, timeout 10 s) — et ne consomme rien
**Verify:** `eps.power_cons` (0x0106) diminue de la puissance du réchauffeur :
- réchauffeur batterie : 8 W
- réchauffeur OBC : 4 W
**Note:** ATTENTION — délester la ligne d'alimentation du réchauffeur signifie que celui-ci ne peut plus
assurer la protection thermique si la zone se refroidit ensuite (p. ex. pendant une éclipse).
Surveiller étroitement la température.
**Note:** Une panne `htr_battery_stuck_on` laisse `tcs.htr_battery` (0x040A)
à 1 même après le délestage de la ligne, car le modèle de panne force
l'indicateur d'état en aval de la condition d'alimentation. C'est pourquoi cette étape vérifie la ligne EPS
et son courant plutôt que le mot d'état du réchauffeur : 0x0115 et 0x011D sont les
mesures qui ne peuvent pas mentir sur la circulation effective du courant.

### Étape 5 : Surveiller la baisse de température
**LABEL:** `STEP-5`
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — surveiller toutes les 60 s
**Verify:** La température de la zone concernée ne monte plus.
**Verify:** La température commence à baisser ou se stabilise :
- température de la batterie : doit se stabiliser puis baisser vers l'ambiante
- température de l'OBC : doit se stabiliser puis baisser
- température du propulseur : doit se stabiliser puis baisser
**Verify:** Consigner la température toutes les 60 s pendant au moins 10 minutes pour confirmer la tendance.
**Note:** Si la température continue de monter alors que le réchauffeur est OFF ou que sa
ligne d'alimentation est délestée, la source de chaleur n'est PAS le réchauffeur. Rechercher d'autres causes
(équipement voisin, échauffement solaire, dissipation interne) et faire remonter à l'équipe d'ingénierie — voir la section Contingence.
**GO/NO-GO:** Température en baisse — emballement enrayé, poursuivre la surveillance

### Étape 6 : Bilan après l'événement
**LABEL:** `STEP-6`
**Note:** Une fois la température revenue dans une plage sûre — batterie < 35 °C,
OBC < 50 °C, propulseur dans les limites —, évaluer si le réchauffeur peut être rétabli.
**Note:** Si le réchauffeur a répondu à l'étape 2, le rendre au contrôle autonome
avec `HEATER_AUTO_MODE(circuit=0)` (func_id 45) et surveiller toute récurrence.
Ce n'est délibérément PAS une étape `**TC:**` : rétablir un thermostat qui vient de
dysfonctionner est une décision du directeur de vol, et une fiche exécutable ne doit pas la prendre
automatiquement. L'envoyer à la main une fois la décision prise.
**Note:** Si le réchauffeur a nécessité le délestage d'une ligne d'alimentation, NE PAS réactiver la ligne
sans évaluation par l'ingénierie. Le relais ou l'interrupteur est soupçonné d'être bloqué.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — contrôle final de la puissance
**Verify:** `eps.bus_voltage > 28.0` (0x0105, timeout 10 s) — le bilan de puissance est stable
**Note:** Consigner l'événement d'emballement thermique : zone concernée, température maximale
atteinte, intervention nécessaire (commande d'arrêt / forçage des consignes /
délestage), durée de l'emballement et configuration thermique actuelle.
**Note:** Si la ligne d'alimentation du réchauffeur a été délestée, prévoir la gestion thermique pendant
la prochaine éclipse sans ce réchauffeur (il faudra peut-être délester d'autres charges pour maintenir la
température, ou accepter un refroidissement prolongé de cette zone).

## Critères de vérification
- [ ] Réchauffeur confirmé OFF (commande, forçage ou délestage)
- [ ] Température de la zone concernée en baisse
- [ ] La température maximale n'a pas dépassé le seuil d'endommagement du matériel
- [ ] Aucun effet secondaire sur les autres sous-systèmes
- [ ] `eps.bus_voltage` (0x0105) et `eps.power_cons` (0x0106) nominaux
- [ ] Rapport d'anomalie établi avec la chronologie complète des températures

## Contingence
- Si la température atteint le seuil d'endommagement du matériel avant que le réchauffeur puisse être coupé :
  - Batterie : > 50 °C — risque d'emballement thermique de la batterie (chimique). Commander
    `OBC_SET_MODE(mode=2)` pour passer en EMERGENCY. Délester TOUTES les charges pour arrêter la chaleur produite
    par la décharge de la batterie.
  - OBC : > 70 °C — risque d'endommagement du processeur. Envisager un basculement de l'OBC sur l'unité redondante
    selon CTG-011.
  - Propulseur : > limite de conception — risque de problèmes d'ergol s'il y en a.
- Si le délestage de la ligne d'alimentation n'arrête pas la hausse de température : la source de chaleur n'est pas le
  réchauffeur. Vérifier si la zone fait face au Soleil (échauffement solaire). Vérifier si un équipement voisin
  dissipe une chaleur inattendue. Envisager une manœuvre d'attitude pour modifier l'exposition thermique.
- Si le réchauffeur est nécessaire à la survie en éclipse mais que sa ligne d'alimentation a été délestée : évaluer si
  la zone peut survivre à l'éclipse sans chauffage actif. Sinon, envisager une brève
  réactivation de la ligne d'alimentation pendant l'éclipse uniquement, sous surveillance continue.
  Cela exige l'approbation du directeur de vol et l'attention continue d'un opérateur.
