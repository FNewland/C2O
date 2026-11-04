# CTG-005 : Mode survie EPS
**Sous-système :** EPS
**Phase :** CONTINGENCY
**Révision :** 1.1 --- 2026-11-02 (décision de Franz P3) : vérifier ce que la FDIR de bord a déjà
délesté avant de délester depuis le sol, et réalimenter les lignes avant les commandes de mode. Une
sous-tension EPS ne place pas à elle seule l'OBC en SAFE ; l'étape 1 consigne donc le mode de l'OBC
au lieu d'exiger SAFE.
**Approuvé par :** Directeur des opérations de vol

## Objet
Rétablir le sous-système d'alimentation électrique après un état de faible énergie déclenché par la chute de
l'état de charge de la batterie sous 20 % ou de la tension du bus principal sous 27.7 V. Cette procédure
déleste les charges non essentielles pour enrayer l'épuisement de l'énergie, surveille les performances du générateur solaire pendant
la phase éclairée de l'orbite et réactive progressivement les charges une fois la batterie remontée
au-dessus de 40 % de SoC.

## Prérequis
- [ ] Le satellite est passé en mode survie OBC, ou l'opérateur a confirmé l'anomalie EPS par la télémesure
- [ ] La liaison TT&C est active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Prévision d'orbite courante disponible — heures des prochaines transitions éclairé/éclipse connues
- [ ] Tableur du bilan de puissance (réf. : EOSAT1-PWR-BUD-001) accessible en console

## Déroulement

### Étape 1 — Vérifier l'entrée en mode survie et l'état de l'EPS
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Données de servitude plateforme/OBDH
**Verify:** `obdh.mode` (0x0300) — consigner (1 = SAFE si l'OBC a été mis en survie ; une sous-tension EPS seule le laisse en NOMINAL)
**Verify:** `eps.eps_mode` (0x0137) et `eps.load_shed_stage` (0x0134) — consigner ce que l'EPS a fait de lui-même
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) — consigner chacune : 0 = déjà délestée à bord
**Note:** VÉRIFIER D'ABORD LE SATELLITE. Une ligne que la FDIR de bord a ouverte ne peut pas être
délestée une seconde fois (la commande est refusée S1.8 « power line … is OFF »), et les données de
servitude de son unité s'arrêtent, si bien que son paramètre de mode reste figé à sa dernière valeur.
Ne délester depuis le sol que ce qui est encore alimenté.
**Verify:** `eps.bat_soc` (0x0101) — consigner la valeur courante (attendue < 20 %)
**Verify:** `eps.bus_voltage` (0x0105) — consigner la valeur courante (attendue < 27.7 V)
**Verify:** `eps.bat_voltage` (0x0100) — consigner la valeur courante
**GO/NO-GO:** La télémesure confirme l'état de faible énergie — engager le délestage

### Étape 2 — Délester les charges non essentielles : charge utile sur OFF
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-SHED` | NO-GO `STEP-3` (timeout 10 s)
**Note:** GO — la ligne de la charge utile est encore sur ON : la délester depuis le sol. NO-GO —
l'EPS l'a déjà ouverte : rien à envoyer, la charge utile est coupée.
**LABEL:** `STEP-2-SHED`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26)
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Données de servitude de la charge utile
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Données de servitude EPS
**Verify:** `payload.mode` (0x0600) = 0 (OFF) en moins de 10 s
**Verify:** `eps.power_cons` (0x0106) baisse d'au moins (>=) 15 W en moins de 15 s
**GO/NO-GO:** Charge utile confirmée sur OFF (par le sol ou déjà à bord) et consommation réduite — continuer

### Étape 3 — Vérifier que le SCAO est en configuration de puissance minimale
**LABEL:** `STEP-3`
**BRANCH:** `eps.pl_aocs_wheels == 1` -> GO `STEP-3-ATT` | NO-GO `STEP-3-OFF` (timeout 10 s)
**Note:** GO — la suite SCAO est alimentée : contrôler son pointage solaire. NO-GO — un délestage
profond a ouvert la ligne `aocs_wheels` : le SCAO est sur OFF (`aocs.mode` 0), le satellite dérive, et
`ttc_tx` l'a précédée dans l'ordre de délestage ; seule la balise UHF (SID 11) parvient donc au sol. Ne
pas commander le SCAO maintenant ; l'étape 7 le réalimente une fois la batterie rétablie.
**LABEL:** `STEP-3-OFF`
**Note:** SCAO non alimenté à la suite du délestage de bord — continuer à l'étape 4.
**GO/NO-GO:** Délestage profond confirmé — continuer avec le SCAO sur OFF -> GO `STEP-4` | NO-GO `STEP-4`
**LABEL:** `STEP-3-ATT`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) = 3 (COARSE_SUN) — pointage solaire pour un éclairement maximal du générateur
**Note:** Si le SCAO n'est pas en COARSE_SUN, commander `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) et vérifier la transition en moins de 30 s
**GO/NO-GO:** SCAO en COARSE_SUN, garantissant l'orientation optimale du générateur solaire — continuer

### Étape 4 — Évaluer les performances du générateur solaire
**LABEL:** `STEP-4`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.sa_a_current` (0x0103) — consigner la valeur (attendue > 0.5 A au Soleil)
**Verify:** `eps.sa_b_current` (0x0104) — consigner la valeur (attendue > 0.5 A au Soleil)
**Verify:** `eps.power_gen` (0x0107) — consigner la valeur (attendue > 25 W au Soleil, > 45 W en incidence optimale)
**GO/NO-GO:** Si les deux courants du générateur sont < 0.2 A pendant une phase éclairée confirmée, suspecter une panne du générateur — passer à CTG-009. Sinon, continuer.

### Étape 5 — Surveiller la recharge de la batterie pendant la phase éclairée
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — répéter toutes les 60 s
**Verify:** `eps.bat_soc` (0x0101) en hausse (au minimum +1 % par 10 minutes au Soleil)
**Verify:** `eps.bus_voltage` (0x0105) remontant au-dessus de 30.9 V
**Verify:** `eps.bat_temp` (0x0102) reste entre 0 et 40 °C pendant la charge
**GO/NO-GO:** SoC en hausse et température batterie nominale — poursuivre la surveillance jusqu'à un SoC > 40 %

### Étape 6 — Réactiver les charges : charge utile en veille
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `payload`, si `eps.pl_payload` (0x0113) = 0 (un délestage de bord l'ouvre ; la commande de mode est alors refusée par un S1.8 « power line 'payload' is OFF »)
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) en moins de 10 s
**Verify:** `eps.bat_soc` (0x0101) reste > 35 % après l'ajout de charge (laisser 60 s de stabilisation)
**Verify:** `eps.power_cons` (0x0106) augmente d'une valeur cohérente avec la consommation de la charge utile en veille (~8 W)
**GO/NO-GO:** SoC stable au-dessus de 35 % avec la charge utile en veille — continuer

### Étape 7 — Rétablir le mode SCAO nominal
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) — d'abord la ligne `aocs_wheels`, si `eps.pl_aocs_wheels` (0x0117) = 0 (un délestage profond l'ouvre et fait tomber `aocs.mode` à 0 ; la commande de mode est alors refusée par un S1.8 « power line 'aocs_wheels' is OFF »)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 en moins de 5 s
**BRANCH:** `aocs.mode == 0` -> GO `STEP-7-DET` | NO-GO `STEP-7-NOM` (timeout 10 s)
**Note:** GO — le SCAO est retombé sur OFF quand sa ligne s'est ouverte et ne redémarre pas seul :
d'abord DETUMBLE. NO-GO — il fonctionne déjà : passer en NOMINAL.
**LABEL:** `STEP-7-DET`
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE ; le SCAO passe de lui-même en COARSE_SUN une fois les vitesses faibles
**BRANCH:** `aocs.mode == 3` -> GO `STEP-7-NOM` | NO-GO `STEP-7-NOM` (timeout 1800 s)
**LABEL:** `STEP-7-NOM`
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) en moins de 30 s
**Verify:** `eps.bat_soc` (0x0101) reste > 30 % après la transition du SCAO
**GO/NO-GO:** Attitude nominale et SoC stable — engager le rétablissement du mode OBC

### Étape 8 — Ramener l'OBC en mode nominal
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) en moins de 10 s
**Verify:** `eps.bat_soc` (0x0101) > 40 %
**Verify:** `eps.bus_voltage` (0x0105) > 32.1 V
**GO/NO-GO:** Tous les sous-systèmes nominaux et bilan énergétique positif — reprise terminée

## Conduite à tenir hors nominal
- Si le SoC descend sous 10 % à n'importe quelle étape : commander `OBC_SET_MODE(mode=2)` (EMERGENCY), appliquer EMG-002
- Si la température de la batterie dépasse 45 °C pendant la charge : commander `HEATER_BATTERY(on=0)` et réduire le courant de charge par `SET_PARAM(param_id=eps.charge_limit, value=0.5)`
- Si la production du générateur solaire reste < 0.2 A pendant toute une phase éclairée : appliquer CTG-009 (Dégradation du générateur solaire)
- Si la tension du bus descend sous 28.4 V : appliquer immédiatement EMG-002

## Postconditions
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] `eps.bus_voltage` (0x0105) > 32.1 V
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] `payload.mode` (0x0600) >= 1 (STANDBY ou supérieur)
- [ ] Bilan de puissance positif avec une marge > 5 W, confirmé par la dynamique du vol

## Voie de reprise — réalimentation des charges délestées
Une fois le bus stabilisé par cette procédure et la cause racine comprise, **tout sous-système dont les lignes d'alimentation ont été coupées lors du délestage doit être remis sous tension dans l'ordre maîtrisé défini par LEOP-007 (Mise sous tension séquentielle)**. Ne **pas** se contenter de réactiver les lignes au cas par cas : LEOP-007 impose le bon enchaînement sous-système→ligne→mode, l'espacement des courants d'appel, le préconditionnement thermique par les réchauffeurs de l'OBC et de la batterie, ainsi que les exemptions set_mode SCAO/charge utile à la barrière d'alimentation à deux niveaux des TC. Référence croisée : `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
