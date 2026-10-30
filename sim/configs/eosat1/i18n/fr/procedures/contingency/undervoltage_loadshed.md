# CTG-001 : Délestage sur sous-tension

**Catégorie :** Contingence
**Poste responsable :** Puissance et thermique (EPS/TCS)
**Postes associés :** directeur de vol, tous les postes
**Difficulté :** Avancé

## Objectif
Traiter une sous-tension sur le bus d'alimentation principal en effectuant un délestage manuel
dans un ordre de priorité maîtrisé. Les charges sont délestées en commençant par la plus basse
priorité (charge utile), puis le refroidisseur du FPA, l'émetteur TX et les roues
de réaction, afin d'enrayer la baisse de la tension du bus et de protéger les fonctions critiques du satellite. Le rétablissement
est surveillé jusqu'au retour de l'état de charge de la batterie et de la tension du bus à des niveaux sûrs.

## Prérequis
- [ ] Indicateur de sous-tension détecté — `eps.uv_flag` (0x010E) = 1 ou tension du bus observée < 27.0 V
- [ ] Liaison TT&C active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Directeur de vol informé, autorisant le délestage manuel
- [ ] Prévision d'orbite à jour disponible (heures d'entrée et de sortie d'éclipse)

## Télémesure requise
| Paramètre | ID | Valeur attendue |
|---|---|---|
| eps.uv_flag | 0x010E | 1 (sous-tension détectée) |
| eps.bus_voltage | 0x0105 | Surveillance — < 27.0 V attendu à la détection |
| eps.bat_soc | 0x0101 | Surveillance — consigner la tendance |
| eps.bat_voltage | 0x0100 | Surveillance — consigner la valeur |
| eps.bat_current | 0x0109 | Négatif (décharge) |
| eps.power_cons | 0x0106 | Surveillance — consigner avant/après chaque délestage |
| eps.power_gen | 0x0107 | Consigner — peut valoir 0 en éclipse |
| eps.eclipse_flag | 0x0108 | État courant Soleil/éclipse |
| payload.mode | 0x0600 | Mode courant de la charge utile |
| tcs.cooler_fpa | 0x040C | État courant du refroidisseur |
| ttc.pa_on | 0x0516 | État courant de l'amplificateur de puissance |
| aocs.mode | 0x020F | Mode courant du SCAO |

## Télécommandes requises
| Commande | Service | Sous-type | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Demander un rapport HK ponctuel |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Mettre la charge utile en mode OFF |
| FPA_COOLER | 8 | 1 | 43 | Désactiver le refroidisseur du FPA |
| TTC_PA_OFF | 8 | 1 | 67 | Désactiver l'amplificateur de puissance (TX) |
| EPS_POWER_OFF | 8 | 1 | 20 | Mettre une ligne d'alimentation sur OFF |
| OBC_SET_MODE | 8 | 1 | 50 | Régler le mode de l'OBC (safe/emergency) |

## Déroulement

### Étape 1 : Détecter et confirmer la sous-tension
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Demander la télémesure de servitude EPS
**Verify:** `eps.uv_flag == 1` (0x010E, timeout 10 s)
**Verify:** `eps.bus_voltage` (0x0105) — consigner la valeur courante (< 27.0 V attendu)
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante
**Verify:** `eps.bat_voltage` (0x0100) — consigner la valeur courante
**Verify:** `eps.power_cons` (0x0106) — consigner la consommation totale
**Verify:** `eps.power_gen` (0x0107) — consigner la production de puissance
**Verify:** `eps.eclipse_flag` (0x0108) — déterminer si le satellite est en éclipse
**Action:** Annoncer « UNDERVOLTAGE — initiating manual load shed » sur la boucle opérations.
**GO/NO-GO:** Sous-tension confirmée. Le directeur de vol autorise le délestage — continuer.

### Étape 2 : Délester la charge de priorité 1 — charge utile sur OFF
**LABEL:** `STEP-2`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — Mettre la charge utile sur OFF
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en 10 s
**Verify:** `eps.power_cons` (0x0106) diminue (-45 W attendus en prise de vue, -8 W en STANDBY)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Télémesure de servitude charge utile
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 26.5` -> GO `STEP-6` | NO-GO `STEP-3` (timeout 60 s)
**Note:** GO — le délestage a suffi ; MAINTENIR (HOLD) ce niveau, la suite est directement la surveillance.
NO-GO — la tension baisse encore ; le niveau de délestage suivant s'applique. La temporisation de 60 s
de la branche correspond à ce que la prose appelait « attendre 30 s et contrôler de nouveau » : elle laisse au bus deux
échantillons SID 1 à 1 Hz pour se stabiliser avant l'évaluation du prédicat.

### Étape 3 : Délester la charge de priorité 2 — refroidisseur du FPA sur OFF
**LABEL:** `STEP-3`
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43) — Désactiver le refroidisseur du FPA
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (OFF) en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 15 W
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — Télémesure de servitude TCS
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 26.0` -> GO `STEP-6` | NO-GO `STEP-4` (timeout 60 s)

### Étape 4 : Délester la charge de priorité 3 — émetteur TX sur OFF
**LABEL:** `STEP-4`
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — Désactiver l'amplificateur de puissance
**Verify:** `ttc.pa_on` (0x0516) = 0 en 5 s
**Verify:** `eps.power_cons` (0x0106) diminue d'environ 20 W
**Note:** AVERTISSEMENT — Cette action supprime la capacité de liaison descendante. La liaison montante (RX) reste active.
Le satellite peut encore recevoir des commandes mais ne peut plus émettre de télémesure.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau la tension du bus
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Télémesure de servitude TT&C
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 25.5` -> GO `STEP-6` | NO-GO `STEP-5` (timeout 60 s)
**Note:** Après cette étape, la liaison descendante en bande S est INHIBÉE — `ttc.tx_active`
(0x0525) passe à 0 et la télémesure s'arrête. La balise UHF est une radio distincte, sur la
ligne non commutable `ttc_rx`, et continue d'émettre la HK SID 11 : le sol peut donc encore
voir l'état du satellite ; le prédicat de la branche est évalué à partir du dernier
échantillon SID 1 reçu avant la coupure de l'amplificateur, ou à partir de la balise.

### Étape 5 : Délester la charge de priorité 4 — roues de réaction sur OFF
**LABEL:** `STEP-5`
**TC:** `EPS_POWER_OFF(line_index=7)` (Service 8, Subtype 1, func_id 20) — Mettre hors tension les roues AOCS
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 0 (OFF) en 5 s
**Note:** AVERTISSEMENT — Le satellite va perdre le contrôle d'attitude actif. Le moment cinétique résiduel
provoquera une lente dérive. L'amortissement magnétique (s'il existe) ou le gradient de gravité
n'assureront qu'une stabilisation passive.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Attendre 30 s et contrôler de nouveau
**Verify:** `eps.bus_voltage` (0x0105) — consigner la nouvelle valeur
**BRANCH:** `eps.bus_voltage > 25.0` -> GO `STEP-6` | NO-GO `STEP-5B` (timeout 60 s)

### Étape 5B : Dernier recours — mode EMERGENCY de l'OBC
**LABEL:** `STEP-5B`
**Note:** Atteinte uniquement lorsque tous les niveaux de délestage ont été appliqués et que le bus reste
sous 25.0 V.
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) — EMERGENCY
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Télémesure de servitude plateforme/OBDH
**Verify:** `obdh.mode == 2` (0x0300, timeout 15 s) — EMERGENCY
**Note:** Cette étape n'existait que sous forme de prose dans la ligne GO/NO-GO de l'étape 5. Exécutée à plat,
l'ancienne fiche l'aurait envoyée à CHAQUE exécution — y compris dans le cas courant
où le délestage de la seule charge utile suffisait à rétablir le bus.

### Étape 6 : Surveiller le rétablissement
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Surveiller la télémesure EPS toutes les 60 s
**Verify:** `eps.bus_voltage` (0x0105) — en hausse
**Verify:** `eps.bat_soc` (0x0101) — en hausse (surtout en phase éclairée)
**Verify:** `eps.power_gen` (0x0107) > 0 W au Soleil
**Verify:** `eps.bat_current` (0x0109) — positif (charge) au Soleil
**Action:** Poursuivre la surveillance jusqu'à ce que :
- `eps.bus_voltage` > 28.0 V ;
- `eps.bat_soc` > 40 %.
**Note:** Le rétablissement peut prendre plusieurs orbites selon la profondeur de décharge et
la puissance disponible du générateur solaire.
**GO/NO-GO:** Tension du bus > 28.0 V et SoC > 40 % — passer au rétablissement des charges.

### Étape 7 : Rétablir les charges dans l'ordre de priorité inverse
**Note:** Réactiver les charges une par une, en attendant 5 min entre chacune pour vérifier la stabilité :
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) — 1. Roues AOCS : vérifier que `aocs.mode` (0x020F)
   revient dans un mode commandable. Il peut être nécessaire de passer d'abord par `AOCS_SET_MODE(mode=3)` (COARSE_SUN).
**GO/NO-GO:** Bus stable pendant 5 min avec les roues AOCS rétablies — rétablir la charge suivante
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — 2. Émetteur TX : vérifier `ttc.pa_on` (0x0516) = 1
**GO/NO-GO:** Bus stable pendant 5 min avec l'émetteur rétabli — rétablir la charge suivante
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) — 3. Refroidisseur du FPA : vérifier `tcs.cooler_fpa` (0x040C) = 1
**GO/NO-GO:** Bus stable pendant 5 min avec le refroidisseur du FPA rétabli — rétablir la charge suivante
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — 4. Charge utile en STANDBY : vérifier `payload.mode` = 1
**Verify:** Après chaque ajout de charge, confirmer que `eps.bus_voltage` (0x0105) reste > 27.5 V
et que `eps.bat_soc` (0x0101) reste > 35 %.
**GO/NO-GO:** Toutes les charges rétablies et bilan de puissance positif — procédure terminée.

## Critères de vérification
- [ ] `eps.uv_flag` (0x010E) = 0 (retombé)
- [ ] `eps.bus_voltage` (0x0105) > 28.0 V
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] Tous les sous-systèmes revenus dans leurs modes de fonctionnement nominaux
- [ ] Bilan de puissance positif (production > consommation) avec marge
- [ ] Aucune nouvelle sous-tension pendant au moins 2 orbites

## Cas de contingence
- Si la tension du bus descend sous 25.0 V après le délestage de toutes les charges : commander
  `OBC_SET_MODE(mode=2)` pour passer en mode EMERGENCY. Le satellite devrait passer de lui-même en configuration
  de puissance minimale.
- Si la tension du bus ne remonte pas après la sortie d'éclipse : suspecter une défaillance du générateur solaire.
  Contrôler `eps.sa_a_current` (0x0103) et `eps.sa_b_current` (0x0104). S'ils sont tous deux proches de
  zéro, passer à la procédure de dégradation du générateur solaire.
- Si le SoC de la batterie descend sous 10 % : risque de décharge profonde de la batterie et de dommages permanents.
  Commander immédiatement le mode EMERGENCY. Toutes les fonctions non essentielles seront désactivées
  par la FDIR de bord.
- Si les charges ne peuvent pas être rétablies sans déclencher de nouveau une sous-tension : réduire le
  bilan de puissance opérationnel. Fonctionner avec un rapport cyclique de charge utile réduit ou sans le refroidisseur
  du FPA. Consulter l'équipe de planification de mission.
- Si la sous-tension se reproduit dans les 2 orbites suivant le rétablissement : suspecter un déficit de puissance
  persistant. Réévaluer le bilan de puissance avec la dynamique du vol (dégradation du générateur,
  durée d'éclipse, biais d'attitude).

## Chemin de reprise — remise sous tension des charges délestées
Une fois le bus stabilisé par cette procédure et la cause première comprise, **tout sous-système dont les lignes d'alimentation ont été mises hors tension lors du délestage doit être remis en service dans l'ordre maîtrisé défini par LEOP-007 (mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au coup par coup : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique des réchauffeurs OBC/batterie et les exemptions set_mode AOCS/charge utile au verrou d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
