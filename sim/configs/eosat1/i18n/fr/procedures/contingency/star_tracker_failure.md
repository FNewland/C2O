# CTG-008 : Panne du senseur stellaire

**Catégorie :** Contingence
**Poste responsable :** Dynamique du vol (AOCS)
**Postes associés :** directeur de vol
**Difficulté :** Avancé

## Objectif
Traiter une panne du senseur stellaire 1 (ST1) en basculant sur le senseur stellaire redondant 2
(ST2). Si ST2 est lui aussi indisponible, se replier sur le mode de pointage par senseurs solaires grossiers (CSS)
(COARSE_SUN) pour maintenir une attitude sûre du satellite. Cette procédure garantit la continuité
de la capacité de détermination d'attitude et réduit au minimum l'impact sur les opérations de mission.

## Prérequis
- [ ] Panne du senseur stellaire 1 détectée — `aocs.st1_status` (0x0240) = 4 (FAILED)
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé de l'anomalie du capteur d'attitude
- [ ] Alimentation du bus du satellite nominale — `eps.bus_voltage` (0x0105) > 27.0 V

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| aocs.st1_status | 0x0240 | 4 (FAILED) — condition de déclenchement |
| aocs.st1_num_stars | 0x0241 | 0 (aucune étoile suivie en cas de panne) |
| aocs.st2_status | 0x0243 | 0 (OFF) au départ, puis 1 (BOOT), puis 2 (TRACKING) |
| aocs.mode | 0x020F | Mode courant du SCAO |
| aocs.att_error | 0x0217 | Surveiller — peut augmenter sans données ST |
| aocs.rate_roll | 0x0204 | Surveiller les vitesses angulaires |
| aocs.rate_pitch | 0x0205 | Surveiller les vitesses angulaires |
| aocs.rate_yaw | 0x0206 | Surveiller les vitesses angulaires |
| aocs.css_valid | 0x0248 | Validité du vecteur Soleil CSS |
| aocs.css_sun_x | 0x0245 | Vecteur Soleil CSS, X |
| aocs.css_sun_y | 0x0246 | Vecteur Soleil CSS, Y |
| aocs.css_sun_z | 0x0247 | Vecteur Soleil CSS, Z |
| eps.bus_voltage | 0x0105 | > 27.0 V |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| ST2_POWER | 8 | 1 | 5 | Mise sous tension du senseur stellaire 2 |
| ST_SELECT | 8 | 1 | 6 | Sélectionner le senseur stellaire principal (codage : 1=ST1, 2=ST2, 0 refusé) |
| ST1_POWER | 8 | 1 | 4 | Mise hors tension du senseur stellaire 1 (isolation) |
| AOCS_SET_MODE | 8 | 1 | 0 | Régler le mode SCAO (repli en COARSE_SUN) |

## Déroulement

### Étape 1 : Confirmer la panne du senseur stellaire 1
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander la télémesure de servitude AOCS
**Verify:** `aocs.st1_status == 4` (0x0240, timeout 15 s) — FAILED
**Verify:** `aocs.st1_num_stars` (0x0241) = 0
**Verify:** `aocs.mode` (0x020F) — consigner le mode courant
**Verify:** `aocs.att_error` (0x0217) — consigner la valeur courante (peut être en hausse)
**Verify:** `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206)
— consigner les vitesses angulaires
**Note:** Si `aocs.st1_status` = 3 (BLIND) plutôt que 4 (FAILED), le senseur stellaire est peut-être
temporairement ébloui par le Soleil, la Lune ou le limbe terrestre. Attendre jusqu'à 120 s son rétablissement
avant de continuer.
**GO/NO-GO:** ST1 confirmé FAILED (état = 4) — procéder au basculement sur la redondance.

### Étape 2 : Mettre sous tension le senseur stellaire 2
**LABEL:** `STEP-2`
**TC:** `ST2_POWER(on=1)` (Service 8, Subtype 1, func_id 5) — Commander la mise sous tension de ST2
**Verify:** Attendre 60 s la fin de la séquence d'amorçage de ST2.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Demander la télémesure de servitude AOCS
**Verify:** `aocs.st2_status` (0x0243) évolue ainsi :
- 0 (OFF) -> 1 (BOOT) dans les 5 s suivant la mise sous tension ;
- 1 (BOOT) -> 2 (TRACKING) dans les 60 s suivant la mise sous tension.
**Verify:** Si `aocs.st2_status` reste à 1 (BOOT) après 60 s, attendre jusqu'à
60 s de plus (120 s au total). L'initialisation du senseur stellaire peut être plus longue si l'attitude est
incertaine.
**BRANCH:** `aocs.st2_status == 2` -> GO `STEP-3` | NO-GO `STEP-5` (timeout 120 s)
**Note:** GO — ST2 est en TRACKING ; le sélectionner comme principal et isoler ST1. NO-GO — ST2
n'a pas acquis en 120 s ; il ne reste aucun autre senseur stellaire, le NO-GO mène donc
DIRECTEMENT au repli COARSE_SUN. Exécutée à plat, l'ancienne fiche aurait sélectionné un
senseur stellaire qui ne suit rien (étape 3), éteint le seul autre senseur
(étape 4), ET commandé le repli dégradé (étape 5) — les trois branches, dans cet
ordre, sur un satellite qui venait de perdre sa référence d'attitude.

### Étape 3 : Sélectionner le senseur stellaire 2 comme principal
**LABEL:** `STEP-3`
**TC:** `ST_SELECT(unit=2)` (Service 8, Subtype 1, func_id 6) — Sélectionner ST2 comme
capteur d'attitude principal. LE CODAGE EST 1=ST1, 2=ST2 (0 est refusé) : l'ancien
`unit=1` à cet endroit RESÉLECTIONNAIT SILENCIEUSEMENT le ST1 en panne alors que la fiche croyait
avoir basculé sur ST2 (décision 2026-08c)
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — télémesure de servitude AOCS, 10 s après la sélection
**Verify:** `aocs.att_error` (0x0217) commence à diminuer (la solution d'attitude s'améliore)
**Verify:** `aocs.st2_status == 2` (0x0243, timeout 15 s) — TRACKING, confirmé stable
**Verify:** `aocs.mode` (0x020F) — le SCAO devrait rester dans le mode antérieur à la panne ou y revenir
**GO/NO-GO:** ST2 sélectionné et fournissant une solution d'attitude valide — passer à l'isolation.

### Étape 4 : Isoler le senseur stellaire 1 en panne
**LABEL:** `STEP-4`
**TC:** `ST1_POWER(on=0)` (Service 8, Subtype 1, func_id 4) — Mettre ST1 hors tension pour éviter toute interférence
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Télémesure de servitude AOCS
**Verify:** `aocs.st1_num_stars == 0` (0x0241, timeout 15 s) — ST1 ne produit plus rien
**Note:** NE PAS vérifier ici `aocs.st1_status` (0x0240) = 0 (OFF). Constaté sur un
moteur en fonctionnement : lorsque `st1_failed` est activé, le modèle applique le verdict FAILED
APRÈS le verrou d'alimentation, si bien que 0x0240 reste à 4 (FAILED) même une fois l'unité
hors tension. C'est défendable — une unité en panne que l'on a éteinte reste
une unité en panne —, mais cela signifie que le contrôle OFF ne peut jamais réussir sur la panne
même que traite cette fiche. Le nombre d'étoiles est la confirmation fiable
que ST1 est sorti de la boucle.
**Verify:** `aocs.att_error` (0x0217) < 0.1° (pointage fin rétabli)
**Verify:** `aocs.rate_roll` (0x0204) < 0.01°/s
**Verify:** `aocs.rate_pitch` (0x0205) < 0.01°/s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.01°/s
**Action:** Consigner la panne de ST1 et l'activation de ST2 dans le rapport d'anomalie.
**Note:** Le satellite fonctionne désormais sur le seul senseur stellaire restant. Toute
panne de ST2 imposera le repli en mode COARSE_SUN (étape 5).
**BRANCH:** `aocs.st2_status == 2` -> GO `STEP-END` | NO-GO `STEP-5` (timeout 30 s)
**Note:** GO — le basculement est terminé et la fiche s'achève ici. NO-GO — ST2 est
lui aussi en panne et la seule option restante est le repli COARSE_SUN.

### Étape 5 : Repli — les deux senseurs stellaires en panne, entrer en mode COARSE_SUN
**LABEL:** `STEP-5`
**Note:** Si ST2 n'a pas atteint l'état TRACKING ou est lui aussi en panne (état = 4) :
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN, le maintien sûr au Soleil
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — Télémesure de servitude AOCS
**Verify:** `aocs.mode == 3` (0x020F, timeout 20 s) — COARSE_SUN
**Note:** COARSE_SUN est un mode d'attente (HOLD), pas une destination : depuis la phase 1, il ne fait pas partie de
l'ensemble des modes opérationnels du modèle ; le commander n'écrase donc PAS
`aocs.commanded_mode` (0x0297), et le satellite revient de lui-même au mode commandé
par le sol si un senseur stellaire se rétablit. Surveiller `aocs.mode_demoted`
(0x0298) plutôt que de renvoyer la commande de mode à la main.
**Verify:** `aocs.css_valid` (0x0248) = 1 (vecteur Soleil valide)
**Verify:** `aocs.css_sun_x` (0x0245), `aocs.css_sun_y` (0x0246), `aocs.css_sun_z` (0x0247)
— le vecteur Soleil est mesuré
**Verify:** `aocs.att_error` (0x0217) — sera plus grande dans ce mode (< 5° acceptable)
**Action:** Informer le directeur de vol : « Both star trackers failed. Operating in COARSE_SUN
mode. Fine pointing capability is LOST. Payload imaging is NOT possible. »
**Note:** Uniquement si la charge utile est encore sous tension.
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — charge utile sur OFF
**Note:** Le mode COARSE_SUN assure un pointage solaire pour la sécurité énergétique mais ne permet ni le
pointage nadir ni les opérations de charge utile. Il s'agit d'une configuration dégradant la mission.
**GO/NO-GO:** Mode COARSE_SUN actif, satellite en sécurité. Faire remonter à l'équipe d'ingénierie
pour planifier la reprise des senseurs stellaires.

### Étape 6 : Fin de la procédure
**LABEL:** `STEP-END`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — télémesure de servitude AOCS finale
**Note:** Atteinte soit après un basculement réussi sur ST2 (GO de l'étape 4), soit après le
repli COARSE_SUN (fin de l'étape 5). Consigner dans le rapport d'anomalie la branche suivie
— elles laissent le satellite dans des configurations sensiblement différentes.

## Critères de vérification
- [ ] `aocs.st2_status` (0x0243) = 2 (TRACKING) — si le basculement sur ST2 a réussi
- [ ] `aocs.att_error` (0x0217) < 0.1° — pointage fin rétabli (cas ST2)
- [ ] `aocs.st_selected` (0x0244) = 2 et ST1 isolé (`aocs.st1_num_stars` (0x0241) = 0 ; `aocs.st1_status` peut encore indiquer 4 = FAILED, voir l'étape 4)
- [ ] OU `aocs.mode` (0x020F) = 3 (COARSE_SUN) — si les deux ST sont en panne
- [ ] Vitesses angulaires dans les limites (< 0.01°/s pour le pointage fin, < 1.0°/s en COARSE_SUN)
- [ ] Aucun déclenchement du mode survie par la FDIR pendant le basculement

## Cas de contingence
- Si ST2 tombe en panne pendant l'amorçage (état bloqué à 1) : effectuer un cycle d'alimentation de ST2 — `ST2_POWER(on=0)`,
  attendre 10 s, `ST2_POWER(on=1)`. En cas d'échec après la deuxième tentative, passer à l'étape 5.
- Si ST2 passe en BLIND (état = 3) plutôt qu'en TRACKING : le champ de vue est peut-être
  obstrué. Attendre jusqu'à 120 s. En éclipse, le senseur stellaire peut avoir besoin de la phase éclairée pour
  acquérir des étoiles. S'il reste BLIND après deux tentatives, passer à l'étape 5.
- Si l'erreur d'attitude dépasse 5° pendant le basculement : la FDIR peut déclencher le mode survie
  automatiquement. Si la FDIR se déclenche, laisser le passage autonome en mode survie se faire. Suivre ensuite
  CTG-002 (reprise après anomalie SCAO) pour le retour au nominal une fois ST2 opérationnel.
  Remarque : contrôler `aocs.mode` (0x020F) avant d'agir --- le simulateur a peut-être
  déjà repris de lui-même le mode 4 (NOMINAL). Dès que COARSE_SUN a tenu un bon verrouillage
  solaire (CSS valide, erreur < 15 deg) pendant 60 s avec un senseur stellaire disponible,
  l'AOCS rend la main au mode commandé sans aucune télécommande.
- Si les deux senseurs stellaires sont en panne et que les CSS sont également invalides (éclipse) : le SCAO n'a aucune
  référence d'attitude. Commander `AOCS_SET_MODE(mode=2)` pour passer en DETUMBLE au moyen des magnétocoupleurs.
  Attendre la phase éclairée pour l'acquisition CSS. Il s'agit d'une anomalie critique pour la mission —
  faire remonter l'anomalie immédiatement.
- Si le bilan de puissance ne permet pas d'alimenter les deux senseurs stellaires simultanément : ne garder que ST2
  sous tension. Ne pas tenter d'alimenter les deux unités si `eps.bat_soc` < 40 %.
