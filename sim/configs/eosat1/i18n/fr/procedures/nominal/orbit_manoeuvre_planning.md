# NOM-004 : Planification d'une manœuvre de maintien d'orbite

**Sous-système :** Propulsion / Flight Dynamics
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Planifier une manœuvre de delta-V — une **manœuvre d'évitement de débris (CAM)** ou une
**poussée de routine de compensation de la traînée / de maintien du demi-grand axe** — et la charger à
bord sous forme de séquence de télécommandes datées S11. La dynamique du vol (FDS)
produit le vecteur de manœuvre ; l'ingénieur propulsion vérifie la santé du système ;
le directeur de vol autorise l'exécution.

La propulsion d'EO-Sat-1 est un module minimal 1U à monergol vert, dimensionné uniquement pour
l'évitement de débris et un maintien d'orbite limité (66,9 m/s au total). Il n'y a
pas de désorbitation propulsée : le retrait de service en fin de vie se fait par décroissance naturelle, ce qui respecte
la règle des 5 ans de la FCC depuis cette orbite. Chaque poussée entame la réserve
d'évitement de collision — le bilan de dV est un bilan de sécurité, pas une jauge de carburant.

## Prérequis
- [ ] Satellite en phase NOMINAL ; aucune mise en sécurité FDIR active
- [ ] Santé de la propulsion vérifiée : `prop.state` (0x0B00) = 0 (SAFED),
      `prop.arm_inhibit_mask` (0x0B15) n'indique aucune inhibition verrouillée (bit 9 à zéro)
- [ ] Pression du réservoir dans la plage : `prop.tank_pressure` (0x0B01) 6.0-24.0 bar
- [ ] Enveloppe restante : `prop.dv_remaining` (0x0B0C) > dV prévu + 1.0 m/s
      de marge de réserve CAM
- [ ] Si l'indicateur de santé de la propulsion n'est PAS nominal : différer la manœuvre et
      exécuter d'abord CTG-028 (anomalie de propulsion)
- [ ] SoC de la batterie > 55 % : `eps.bat_soc` (0x0101) — le préchauffage du lit catalytique coûte
      4 Wh et le verrouillage d'armement exige > 45 %

## Déroulement

### Étape 1 --- Conception de la manœuvre par le FDS
**Évaluer :** Pour une alerte de conjonction : distance d'évitement le long de la trace requise au
TCA, délai d'anticipation et dV qui en résulte (un écart de 500 m le long de la trace avec >= 3 orbites
d'anticipation demande ~15 mm/s ; 0,05 m/s apporte une marge de 3x). Pour la compensation de la traînée : décroissance du demi-grand axe (SMA)
depuis la dernière poussée (tendance de `prop.sma_km` 0x0B1A) et dV nécessaire pour rétablir le
SMA de référence (da = 2a*dv/v : 1,79 km pour 1,0 m/s).
**Note:** Les poussées rétrogrades (annulation d'une manœuvre d'évitement, correction d'un excès de relèvement) exigent un
lacet de 180 degrés vers une attente INERTIAL — à coordonner avec l'ingénieur AOCS.
**Consigner :** dv (m/s), direction (prograde/rétrograde), date de la poussée (CUC),
durée de poussée prévue et décalage d'AOS prévu au passage suivant.

### Étape 2 --- Contrôle de santé de la propulsion
**TC:** `HK_ENABLE(sid=9)` (Service 3, Subtype 5) --- activer la structure de servitude PROP
**Verify:** `prop.state` (0x0B00) = 0, `prop.tank_pressure` (0x0B01) dans la plage,
`prop.propellant_mass` (0x0B02) cohérente avec la masse tenue à jour au sol,
`prop.dv_remaining` (0x0B0C) couvre le plan, `prop.arm_inhibit_mask` (0x0B15)
conforme au motif attendu (lit catalytique froid + aucune poussée chargée est normal à ce stade).
**GO/NO-GO:** Toute panne de vanne à verrouillage (0x0B06/0x0B07 = 2) ou pression
hors plage -> NO-GO, exécuter CTG-028.

### Étape 3 --- Autorisation du directeur de vol
**Évaluer :** Conflits de poussée : prises de vue, vidages et désaturations sont inhibés
autour de la manœuvre (l'activité de planification `orbit_manoeuvre` déclare les
conflits). Confirmer la puissance : préchauffage + poussée en période éclairée.
**GO/NO-GO:** Le FD autorise le vecteur de manœuvre et le passage d'exécution.

### Étape 4 --- Envoi des télécommandes datées S11
**TC:** `SCHEDULE_TC(exec_time_cuc=T-300, tc_data=TC)` (Service 11, Subtype 4) --- dater `PROP_SET_BURN` à T-5 min
**Note:** `tc_data` est le paquet de télécommande interne COMPLET, et non un mnémonique : construire d'abord `PROP_SET_BURN` et en incorporer les octets.
**TC:** `SCHEDULE_TC(exec_time_cuc=T-120, tc_data=TC)` (Service 11, Subtype 4) --- dater `PROP_ARM` à T-2 min
**Note:** `tc_data` est le paquet de télécommande interne COMPLET, et non un mnémonique : construire d'abord `PROP_ARM` et en incorporer les octets.
**TC:** `SCHEDULE_TC(exec_time_cuc=T, tc_data=TC)` (Service 11, Subtype 4) --- dater `PROP_EXECUTE` à T-0
**Note:** `tc_data` est le paquet de télécommande interne COMPLET, et non un mnémonique : construire d'abord `PROP_EXECUTE` et en incorporer les octets.
**Note:** PROP_ARM doit intervenir dans les 300 s qui suivent PROP_SET_BURN (la fenêtre d'armement)
et après la fin du préchauffage du lit catalytique — programmer HEATER_THRUSTER ON à
T-25 min dans la même séquence S11, ou exécuter NOM-013 manuellement pendant le passage.
**TC:** `LIST_SCHEDULE` (Service 11, Subtype 17) --- demander la synthèse du plan bord
**Verify:** la synthèse liste les trois commandes aux dates CUC prévues.

### Étape 5 --- Passage de relais à l'exécution
**Note:** L'exécution, la surveillance en direct, les critères d'interruption et la restitution d'orbite
après poussée relèvent de NOM-013 (exécution d'une manœuvre de maintien d'orbite).

## Écarts
- **Indicateur de santé de la propulsion non nominal** -> différer, exécuter CTG-028.
- **Délai d'anticipation de la conjonction < 1 orbite** -> une CAM n'est plus efficace ;
  se coordonner avec l'autorité de surveillance pour obtenir une solution de TCA révisée plutôt que de
  tenter une poussée tardive.
- **dv_remaining inférieur au plan + réserve** -> décision du FD : n'accepter d'entamer la réserve
  que face à une menace de conjonction réelle, jamais pour une compensation de traînée
  de routine.
