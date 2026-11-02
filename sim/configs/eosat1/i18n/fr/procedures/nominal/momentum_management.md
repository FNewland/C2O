# NOM-007 : Gestion du moment cinétique
**Sous-système :** AOCS
**Phase :** NOMINAL
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Gérer le moment cinétique accumulé dans l'ensemble des roues de réaction en
commandant une manœuvre de désaturation par magnétocoupleurs. Cette procédure est exécutée
lorsque la vitesse d'une roue de réaction approche de la limite opérationnelle, afin d'éviter la
saturation des roues et la perte consécutive du contrôle d'attitude fin. La désaturation est
réalisée en routine une fois par orbite ou selon les indications des données de tendance.

## Prérequis
- [ ] NOM-001 Ouverture de passage achevée (ou exécution autonome hors contact)
- [ ] AOCS en mode NOMINAL : `aocs.mode` (0x020F) = **4**. Le mode 0 est OFF ; la fiche
      l'appelait « NOMINAL ». Les codes de référence figurent dans
      `configs/eosat1/aocs/aocs_mode_codes.yaml`.
- [ ] Déchargement du moment cinétique non inhibé : `aocs.desat_inhibit` (0x029A) = 0. L'inhibition est
      activée AUTOMATIQUEMENT tant que `payload.mode` (0x0600) = 2 (IMAGING), et peut être
      verrouillée par l'opérateur avec `AOCS_SET_DESAT_INHIBIT` (func 96).
- [ ] L'AOCS n'est PAS en FINE_POINT. Depuis la phase 1, la commande de désaturation est REFUSÉE en
      FINE_POINT avec `code="DESAT_REFUSED_FINE"`, et l'entrée automatique en désaturation
      ne concerne que NOMINAL, INERTIAL et ECLIPSE — un déchargement ne peut plus interrompre
      une bande de lui-même.
- [ ] Aucune séance de prise de vue en cours : `payload.mode` (0x0600) != 2
- [ ] SoC de la batterie EPS > 40 % : `eps.bat_soc` (0x0101) > 40
- [ ] Bobines des magnétocoupleurs opérationnelles (aucune anomalie connue sur le sous-système MTQ)

## Déroulement

### Étape 1 --- Évaluer l'état du moment cinétique des roues de réaction
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- demander les données de servitude AOCS
**Verify:** Relever les vitesses actuelles des roues :
  - `aocs.rw1_speed` (0x0207) --- consigner la valeur RPM1
  - `aocs.rw2_speed` (0x0208) --- consigner la valeur RPM2
  - `aocs.rw3_speed` (0x0209) --- consigner la valeur RPM3
  - `aocs.rw4_speed` (0x020A) --- consigner la valeur RPM4
**TC:** `GET_PARAM(param_id=0x029B)` (Service 20, Subtype 3) --- `aocs.h_body_nms`
**Verify:** Consigner `aocs.h_body_nms` (0x029B) --- moment cinétique CORPS stocké |A.h_wheel|
**Note:** **C'est le moment cinétique du corps, et non la vitesse des roues, qu'un déchargement magnétique élimine.** Une
pyramide de quatre roues peut tourner à 5000 tr/min sur chaque roue avec un moment cinétique corps NUL (la
direction de l'espace nul), et elle peut tourner à 1200 tr/min avec un moment important. Les critères
de vitesse des roues ci-dessous sont conservés comme recoupement familier, mais 0x029B est la variable
de décision, avec le pourcentage d'enveloppe `aocs.momentum_envelope_pct`
(0x02BA) --- le bit 4 de `0x02C5` est positionné dès que celui-ci atteint 70 %, ce qui constitue l'avertissement fiable
« un déchargement approche » sur lequel un planificateur doit agir.
**Évaluer :** Si une |RPMn| > 4500 tr/min, la désaturation est REQUISE.
**Évaluer :** Si toutes les |RPMn| < 3000 tr/min, la désaturation est FACULTATIVE (peut être différée).
**GO/NO-GO:** Continuer si le moment cinétique corps dépasse le seuil de déchargement, si une roue
dépasse 4500 tr/min, ou au titre de la maintenance programmée.

### Étape 2 --- Instantané d'attitude avant désaturation
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg
**Verify:** `aocs.rate_roll` (0x0204) < 0.05 deg/s
**Verify:** `aocs.rate_pitch` (0x0205) dans la plage [0.043, 0.083] deg/s (le suivi du nadir impose la vitesse orbitale, +0.063 deg/s sur cette console ; une vitesse de tangage nulle signifierait que le satellite NE suit PAS le nadir)
**Verify:** `aocs.rate_yaw` (0x0206) < 0.05 deg/s
**Note:** Consigner l'erreur d'attitude et les vitesses comme référence avant désaturation.

### Étape 3 --- Commander la désaturation
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1) --- lancer un déchargement du moment cinétique
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- données de servitude AOCS
**Verify:** `aocs.mode == 7` (0x020F, timeout 10 s) --- DESAT
**Note:** Cette étape commandait `AOCS_SET_MODE mode=3` en l'appelant DESAT. **Le mode 3
est COARSE_SUN** ; DESAT est le mode **7**. Envoyer le mode 3 mettait le satellite en
attente pointée Soleil sans décharger le moindre moment cinétique, tandis que l'étape 4 de la fiche attendait
la baisse des vitesses des roues. `AOCS_DESATURATE` (func 1, à privilégier --- c'est
la voie unique sur laquelle aboutit tout appelant, de sorte que les refus ci-dessous s'y appliquent) ou
`AOCS_SET_MODE(mode=7)` conviennent l'un comme l'autre.
**Note:** La commande est REFUSÉE avec `code="DESAT_REFUSED_FINE"` en FINE_POINT et
avec `code="DESAT_INHIBITED"` tant que `aocs.desat_inhibit` (0x029A) est activé. Les deux sont
des comportements corrects, pas des anomalies.
**Note:** L'AOCS de bord active les dipôles des magnétocoupleurs pour évacuer le moment cinétique des
roues tout en maintenant un contrôle d'attitude grossier.
**Attention :** L'erreur d'attitude peut augmenter temporairement jusqu'à 2-3 deg pendant la désaturation.

### Étape 4 --- Suivre l'avancement de la désaturation
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- interroger toutes les 30 s
**Verify:** Toutes les vitesses de roue tendent vers le passage par zéro ou vers la polarisation nominale :
  - |`aocs.rw1_speed`| (0x0207) en baisse
  - |`aocs.rw2_speed`| (0x0208) en baisse
  - |`aocs.rw3_speed`| (0x0209) en baisse
  - |`aocs.rw4_speed`| (0x020A) en baisse
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg (limite grossière pendant la désaturation)
**Verify:** `aocs.rate_roll/pitch/yaw` (0x0204-6) < 0.5 deg/s
**Verify:** `aocs.h_body_nms` (0x029B) en baisse vers la bande morte de 5.0e-4 N.m.s
**Note:** **Un déchargement prend des dizaines de minutes, et non dix.** Mesuré sur le modèle corrigé :
environ **25 min pour atteindre 0,005 N·m·s et 48 min pour 0,001 N·m·s** à partir de la charge
de référence de 0,020 N·m·s. L'ancien chiffre de « 5-8 min » relevait d'un calcul à couple instantané
(0.020 / 4.8e-5) et ignorait que tau = m x B ne peut éliminer que la composante du
moment cinétique PERPENDICULAIRE au champ local ; le déchargement attend donc que le champ balaie
le corps à environ 2 fois la vitesse orbitale. Le délai maximal de bord est
`desaturation.timeout_s` = **3600 s**, et un déchargement qui l'atteint émet l'événement
**0x020E AOCS_DESAT_INEFFECTIVE** et positionne `aocs.desat_ineffective` (0x029C) au lieu
de rester indéfiniment en DESAT.
**Délai maximal :** Ne pas intervenir avant 3600 s, sauf si l'une des vérifications ci-dessus échoue. L'ancienne
échéance de 600 s interrompait tous les déchargements sains.

### Étape 5 --- Confirmer le retour automatique au mode antérieur à la désaturation
**Note:** **Ne pas commander de mode ici.** Depuis la phase 1, DESAT revient au mode
DEPUIS lequel il a été engagé, et non systématiquement à NOMINAL, et le satellite se repromeut
de lui-même en FINE_POINT dès que les conditions préalables `0x02C5` sont tenues pendant 30 s. Commander
NOMINAL ici ÉCRASERAIT le mode commandé par le sol et annulerait cette
repromotion --- c'est exactement le défaut de gestion des modes qui a laissé le satellite, lors de l'exécution réelle,
pointé vers le Soleil pendant six orbites.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- données de servitude AOCS
**Verify:** `aocs.mode_demoted == 0` (0x0298, timeout 300 s) --- le satellite est
revenu dans `aocs.commanded_mode` (0x0297). L'événement **0x020F AOCS_MODE_RESTORED** le signale.
**Verify:** `aocs.att_error` (0x0217) convergeant vers < 1.0 deg
**Note:** Prévoir jusqu'à 300 s pour la reconvergence de l'attitude. Si le retour ne se produit
PAS, `aocs.mode` (0x020F) et la description de l'événement 0x0200 indiquent où le
satellite est allé et pourquoi ; ce n'est qu'alors qu'il faut commander le mode à la main.

### Étape 6 --- Vérification après désaturation
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- HK AOCS finale
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg dans les 120 s qui suivent l'étape 5
**Verify:** Toutes les vitesses de roue dans la plage nominale :
  - |`aocs.rw1_speed`| (0x0207) < 3000 tr/min
  - |`aocs.rw2_speed`| (0x0208) < 3000 tr/min
  - |`aocs.rw3_speed`| (0x0209) < 3000 tr/min
  - |`aocs.rw4_speed`| (0x020A) < 3000 tr/min
**Verify:** `aocs.rate_roll/pitch/yaw` (0x0204-6) < 0.05 deg/s
**Consigner :** Inscrire dans le journal de passage les vitesses des roues avant et après ainsi que les performances d'attitude.

## Conduite à tenir hors nominal
- Si `aocs.mode` (0x020F) ne passe pas à 7 (DESAT) sous 10 s : vérifier le
  motif de refus dans l'avis d'échec S1.8. `DESAT_REFUSED_FINE` signifie que le
  satellite est en FINE_POINT --- commander d'abord NOMINAL (mode 4).
  `DESAT_INHIBITED` signifie que `aocs.desat_inhibit` (0x029A) est activé, soit
  automatiquement parce que la charge utile est en IMAGING, soit par un
  `AOCS_SET_DESAT_INHIBIT` (func 96) verrouillé ; traiter la cause, pas le symptôme.
- Si `aocs.h_body_nms` (0x029B) ne baisse pas au bout de 900 s : panne possible
  d'un magnétocoupleur. Noter qu'un h_body stable pendant quelques minutes est normal --- le
  déchargement n'agit que sur la composante perpendiculaire au champ local ; l'avancement
  n'est donc pas monotone sur de courtes fenêtres. Si le déchargement atteint
  `desaturation.timeout_s`, le satellite émet 0x020E AOCS_DESAT_INEFFECTIVE et
  positionne de lui-même `aocs.desat_ineffective` (0x029C) ; c'est ce drapeau, et non un chronomètre, qui
  déclenche l'analyse.
- Si `aocs.att_error` (0x0217) > 5.0 deg pendant la désaturation : interrompre le déchargement et rétablir
  le pointage avec `AOCS_SET_MODE(mode=3)` (COARSE_SUN, l'attente sûre au Soleil). Le mode 0 est
  OFF --- le commander couperait le contrôle d'attitude sur un satellite qui vient
  de perdre son pointage.
- Si une roue reste saturée après la désaturation : cela peut indiquer une anomalie de
  roulement. La signaler pour suivi de tendance et envisager des opérations à nombre de roues réduit.
- Si le SoC de l'EPS descend sous 35 % pendant la désaturation : interrompre et revenir à NOMINAL.
  La consommation des magnétocoupleurs peut être excessive dans la géométrie d'orbite actuelle.

## Postconditions
- [ ] AOCS revenu de lui-même dans son mode COMMANDÉ --- `aocs.mode_demoted`
      (0x0298) = 0, `aocs.mode` (0x020F) = `aocs.commanded_mode` (0x0297)
- [ ] `aocs.h_body_nms` (0x029B) sous la bande morte de 5.0e-4 N.m.s
- [ ] `aocs.desat_ineffective` (0x029C) = 0
- [ ] Vitesses de toutes les roues de réaction < 3000 tr/min
- [ ] Erreur d'attitude < 1.0 deg et vitesses < 0.05 deg/s
- [ ] Vitesses des roues avant et après désaturation consignées
- [ ] Satellite prêt pour la prise de vue ou d'autres activités nominales
