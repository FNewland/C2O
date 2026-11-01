# NOM-013 : Exécution d'une manœuvre de maintien d'orbite

**Sous-système :** Propulsion
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Exécuter une poussée de delta-V planifiée (évitement de débris ou compensation de la traînée, issue de
NOM-004) : préchauffage du lit catalytique, armement, poussée, surveillance en direct avec critères d'interruption,
et restitution d'orbite après la poussée. Généralement réalisée au-dessus d'une station sol pour
une observation directe ; la poussée elle-même dure de 8 à 260 s selon le dV et la pression
du réservoir (0,85 m/s ~ 32 s en début de vie).

> Remarque (concordance avec le livre) : le guide de l'animateur numérote cette fiche NOM-005.
> Dans le simulateur, NOM-005 est la procédure livrée de configuration HK ; la fiche
> d'exécution est donc ici NOM-013 ; le guide comporte une note de la rédaction.

## Prérequis
- [ ] NOM-004 achevée : paramètres de poussée autorisés, séquence S11 chargée (ou
      exécution manuelle autorisée pendant le passage)
- [ ] AOCS en NOMINAL (4), FINE_POINT (5) ou en attente INERTIAL (9) pour une poussée
      rétrograde : `aocs.mode` (0x020F)
- [ ] Erreur d'attitude < 2.0 deg : `aocs.att_error` (0x0217)
- [ ] SoC de la batterie > 45 % : `eps.bat_soc` (0x0101)
- [ ] Hors éclipse (verrouillage d'armement)
- [ ] Données de servitude PROP activées (SID 9)

## Déroulement

### Étape 1 --- Alimentation et préchauffage du lit catalytique (T-25 min)
**TC:** `EPS_POWER_ON(line_index=8)` (Service 8, Subtype 1) func_id = 19 --- alimenter la ligne de propulsion
**Verify:** `eps.pl_prop` (0x014A) = 1
**TC:** `HEATER_THRUSTER(on=1)` (Service 8, Subtype 1) func_id = 42 --- préchauffage du lit catalytique, 12 W
**Verify:** `tcs.htr_thruster` (0x041B) = 1 ; `tcs.temp_thruster` (0x0409)
en hausse (~10 °C/min au début)
**Note:** Le préchauffage jusqu'au verrouillage d'armement de 180 °C prend ~18-20 min (4 Wh). Une
manœuvre est une activité de PUISSANCE : préchauffage + poussée doivent tenir dans le bilan de puissance
de la période éclairée.

### Étape 2 --- Attitude de poussée
**Verify:** `aocs.mode` (0x020F) = 4 (prograde) ou 9 avec le quaternion cible de lacet à 180 deg
chargé (rétrograde)
**Verify:** `aocs.att_error` (0x0217) < 0.5 deg et stable
**Note:** L'axe de poussée est +X corps : l'attitude nadir nominale donne une poussée
prograde. Chaque degré d'erreur d'attitude coûte cos(theta) du dV le long de la trace et
fait fuir sin(theta) dans une composante latérale (normale à l'orbite).

### Étape 3 --- Charger et armer
**TC:** `PROP_SET_BURN(dv_m_s=DV, direction=DIR, mode=MODE, t_start_cuc=0)` (Service 8, Subtype 1, func_id 110) --- charger la manœuvre
**Verify:** `prop.burn_dv_cmd` (0x0B0E) = dV prévu ; `prop.burn_time_cmd`
(0x0B10) à 10 % près de la prévision du FDS — un désaccord signifie que le modèle sol
et le satellite divergent sur l'état du réservoir : ARRÊTER et résoudre.
**Verify:** `tcs.temp_thruster` (0x0409) >= 180 ; `prop.arm_inhibit_mask`
(0x0B15) = 0
**TC:** `PROP_ARM(arm_code=0xA5C3)` (Service 8, Subtype 1) func_id = 108 --- armer (dans les 300 s qui suivent SET_BURN)
**Verify:** `prop.state` (0x0B00) = 1 (ARMED) ; événement PROP_ARMED (0x0800)
**Note:** Un rejet renvoie un code distinct par verrouillage et positionne le
bit bloquant dans 0x0B15 — lire le masque avant de réessayer quoi que ce soit.

### Étape 4 --- Exécuter et surveiller
**TC:** `PROP_EXECUTE` (Service 8, Subtype 1) func_id = 111 --- lancer la poussée (ou S11 la déclenche)
**Verify:** `prop.state` (0x0B00) = 2 (FIRING) ; événement PROP_BURN_START (0x0803)
**Surveiller (en continu, pendant toute la poussée) :**
  - `prop.thrust_est` (0x0B09) ~ 330 mN en début de vie, suivant la pression du réservoir
  - `aocs.att_error` (0x0217) — la règle de bord interrompt au-delà de 1.0 deg
    (règle S19 8001) et le modèle interrompt à 2.0 deg
  - `prop.burn_time_elapsed` (0x0B11) par rapport à `prop.burn_time_cmd` (0x0B10)
**Attention :** L'accélération du temps est plafonnée à 10x pendant la poussée
(PROP_SPEED_CLAMPED 0x0811) — ne pas lutter contre ce plafond.

### Étape 5 --- Critères d'interruption (permanents, sans décision du FD)
**TC:** `PROP_ABORT` (Service 8, Subtype 1) func_id = 112 --- interruption manuelle immédiate
**Évaluer :** Interrompre IMMÉDIATEMENT si : erreur d'attitude > 1.0 deg et croissante ; poussée < 60 %
de la prévision ; pression du réservoir chutant plus vite qu'en régime de détente (blowdown) ; toute rétrogradation de mode AOCS.
**Vérifier (après toute interruption) :** `prop.burn_status` (0x0B0D) = 4 et
`prop.abort_reason` (0x0B14) identifie la cause. Le dV partiel déjà
délivré A modifié l'orbite — la restitution d'orbite après poussée (étape 6) reste obligatoire.
**Note:** L'interruption d'une poussée hors axe est d'abord une anomalie AOCS : exécuter CTG-002, puis
replanifier le reliquat selon NOM-004. Une seconde interruption verrouille INHIBIT (0x0810) ;
seul PROP_INHIBIT_CLR (func 117) l'efface, après analyse.

### Étape 6 --- Restitution d'orbite après poussée
**Verify:** événement PROP_BURN_COMPLETE (0x0804) ; `prop.burn_dv_achieved`
(0x0B0F) par rapport à `prop.burn_dv_cmd` (0x0B0E) — à 2 % près en nominal
**Verify:** la détermination d'orbite sol après la poussée : `prop.sma_km`
(0x0B1A, produit de détermination d'orbite sol) déplacé du da prévu (1.79 km par m/s
prograde). Une fois le nouveau jeu d'éléments publié par la dynamique du vol, le
planificateur et les prévisions de contact du MCS suivent la nouvelle orbite
**Évaluer :** Au passage suivant, comparer l'AOS observée à la prévision
d'avant poussée : une poussée de 1,0 m/s décale les heures de passage d'environ 34 s/jour. Un résultat inférieur au plan
de plus de 5 % signale un propulseur sous-performant : replanifier une poussée de correction selon NOM-004 et
ouvrir une fiche (dégradation possible du lit catalytique — voir CTG-028).

### Étape 7 --- Mise en sécurité et clôture
**TC:** `PROP_DISARM` (Service 8, Subtype 1) func_id = 109 --- ARMED -> SAFED
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1) func_id = 42 --- réchauffeur du lit catalytique coupé
**TC:** `EPS_POWER_OFF(line_index=8)` (Service 8, Subtype 1) func_id = 20 --- couper l'alimentation de la ligne de propulsion
**Verify:** `prop.state` (0x0B00) = 0 ; `eps.pl_prop` (0x014A) = 0
**Verify:** `aocs.total_momentum` (0x025B) < 0.02 N m s. Le couple dû au désalignement de la poussée
charge les roues pendant une poussée — si le moment cinétique s'est approché de l'enveloppe,
exécuter NOM-007 (gestion du moment cinétique).
**Consigner :** dV obtenu, ergol consommé (écart de 0x0B02), nombre de poussées
(0x0B12) et enveloppe restante (0x0B0C) dans le journal du bilan de dV.

## Écarts
- **La poussée ne démarre pas** -> vérifier `prop.arm_inhibit_mask` (0x0B15) et la
  ligne de propulsion EPS ; une ligne délestée désarme le système par conception.
- **La poussée est sous-performante** -> achever la restitution d'orbite après poussée, puis replanifier une poussée de correction
  (NOM-004). Ne pas prolonger la poussée de façon improvisée.
- **AOCS hors axe pendant la poussée** -> l'interruption automatique se déclenche ; exécuter CTG-002.
