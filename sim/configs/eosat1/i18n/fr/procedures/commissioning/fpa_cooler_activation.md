# COM-010 : Activation du refroidisseur du FPA
**Sous-système :** Charge utile / TCS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : c'est désormais CETTE fiche qui active le refroidisseur ---
LEOP-007 ne le démarre plus (constat du propriétaire : le refroidisseur du FPA était mis en marche bien trop
tôt et consommait de l'énergie pendant toute la LEOP). États d'entrée et de sortie déclarés.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-009 --- charge utile en STANDBY sur sa propre ligne,
SID 5 émis, FPA à l'équilibre non refroidi. La ligne EPS du refroidisseur
(`eps.pl_fpa_cooler` 0x0114), `tcs.cooler_fpa` et `payload.fpa_ready` valent tous 0 :
depuis le 2026-11-03, le mode STANDBY ne fait pas fonctionner le refroidisseur ; cette fiche
est donc la première à le mettre en marche.

## Objet
Activer le refroidisseur du plan focal (FPA) de l'imageur multispectral. Surveiller
la mise en froid depuis l'équilibre non refroidi jusqu'à la consigne commandée (par défaut
−15 °C). Vérifier la consommation du refroidisseur, la vitesse de mise en froid et la stabilité thermique. Le
FPA doit atteindre et tenir la consigne — `payload.fpa_ready` (0x0610) = 1 — avant que les
opérations de prise de vue puissent commencer.

> **Durées révisées (build 2026-08).** Toutes les températures et tous les intervalles de cette
> procédure sont mesurés sur le modèle de FPA à nœud unique corrigé. La révision
> précédente décrivait une mise en froid de 30 minutes passant par −20 °C avant d'atteindre
> −15 °C : elle avait été rédigée d'après le modèle antérieur à la phase B, dans lequel la consigne était
> appliquée comme un *décalage additif de l'environnement*, si bien que le nœud dérivait jusqu'à la température ambiante
> moins 35 K. La boucle réelle se stabilise en 10 minutes environ et ne dépasse jamais la
> consigne.

## Prérequis
- [ ] COM-009 (Mise sous tension de la charge utile) terminée — charge utile en STANDBY (mode 1)
- [ ] `payload.imager_status` (0x0611) sans bit de panne (COM-009, étape 5)
- [ ] `payload.fpa_temp` (0x0601) à l'équilibre non refroidi (environ -5C à +7C)
- [ ] `eps.bat_soc` (0x0101) > 70 % (le refroidisseur ajoute une charge continue de 15 W)
- [ ] `eps.power_gen` (0x0107) > 40W (phase éclairée, panneaux déployés)
- [ ] AOCS maintenant l'attitude dans la famille NOMINAL : `aocs.mode` (0x020F) = 4
      (ou 8 en éclipse) ; codes selon `configs/eosat1/aocs/aocs_mode_codes.yaml`.
- [ ] Liaison bidirectionnelle en bande S active
- [ ] Le passage station sol couvre au moins 15 minutes (ou plusieurs passages disponibles)
- [ ] Ingénieurs charge utile et thermique en console

## Déroulement

### Étape 1 — Consigner l'état thermique avant activation
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.fpa_temp` (0x0601) dans la plage [+8C, +14C] sous 10s
**Verify:** `tcs.temp_fpa` (0x0408) cohérente avec `payload.fpa_temp` sous 10s
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) sous 10s
**Action:** Consigner la température de référence du FPA et l'horodatage. Cet instant marque le T=0 de la mise en froid.
**GO/NO-GO:** FPA à température ambiante, charge utile en STANDBY

### Étape 2 — Activer le refroidisseur du FPA
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) — activation du refroidisseur du FPA, envoyée par l’EPS/TCS (la fonction 43 fait partie des commandes de ce poste ; la charge utile surveille le FPA)
**Octets émis :** `2B 01`
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa`
**TC:** `GET_PARAM(param_id=0x0114)` (Service 20, Subtype 3) — `eps.pl_fpa_cooler`
**Verify:** `tcs.cooler_fpa == 1` (0x040C, timeout 10 s) — le refroidisseur est commandé en marche
**Verify:** `eps.pl_fpa_cooler == 1` (0x0114, timeout 10 s) — et sa ligne EPS est SOUS TENSION
**Note:** Le contrôle de la ligne EPS est nouveau et c'est toute la raison d'être de cette fiche. La func 43 était
l'une des trois voies de commande du refroidisseur qui positionnaient l'indicateur du refroidisseur SANS alimenter la
ligne EPS 4 : `tcs.cooler_fpa` valait 1, l'opérateur croyait le refroidisseur en marche,
et le FPA ne refroidissait jamais — le symptôme « le FPA ne passe pas à YES ». Depuis la phase 4,
les quatre voies (funcs 16, 17, 26, 43 et l'équipement S2 0x0601) alimentent la ligne ;
0x040C et 0x0114 doivent donc désormais concorder. S'ils divergent de nouveau, c'est que le défaut
est revenu.
**Note:** S'attendre à une hausse de 15 W de la consommation de la charge utile
(`subsystems/payload.yaml: fpa_cooler_power_w`), rapportée dans
`payload.cooler_pwr` (0x0602). Le refroidisseur est une **machine miniature de type Stirling
fonctionnant à environ 23 % du rendement de Carnot**, et non un module Peltier : tenir −15 °C face au
puits interne de +12 °C représente un relèvement de 27 K avec UA = 0,833 W/K, soit 22,5 W de
chaleur parasite pompée pour 15 W en entrée — un COP de 1,50, alors qu'un module
au tellurure de bismuth à un étage plafonne vers 0,88 pour ce relèvement. Aucun transitoire de démarrage
n'est modélisé, ni aucune signature vibratoire.
**GO/NO-GO:** Refroidisseur du FPA activé, sa ligne EPS alimentée, et en fonctionnement

### Étape 3 — Vérifier la consommation du refroidisseur
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `GET_PARAM(param_id=0x0106)` (Service 20, Subtype 3) — `eps.power_cons`, charge totale
**Verify:** Hausse de la puissance totale de 14-16 W par rapport à la référence avant refroidissement
sous 30 s. (Cette ligne lisait 0x0108, `eps.eclipse_flag` — un booléen, et non une puissance.)
**Verify:** `eps.bus_voltage` (0x0105) > 30.9V (bus stable sous la charge supplémentaire) sous 10s
**GO/NO-GO:** Consommation du refroidisseur conforme à la spécification, bus stable

### Étape 4 — Surveiller la mise en froid (5 premières minutes)
**Action:** Échantillonner la température du FPA chaque minute pendant la rampe initiale.
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+2 min
**Verify:** `payload.fpa_temp` < +4C sous 10s (vitesse initiale d'environ 4C/min)
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+5 min
**Verify:** `payload.fpa_temp` < -8C sous 10s
**Action:** Consigner les points de la courbe de mise en froid. La rampe est exponentielle, et non
linéaire : la vitesse diminue à mesure que le nœud approche de la consigne ; une vitesse plus faible
à T+5 qu'à T+2 est donc attendue et ne constitue pas une panne.
**GO/NO-GO:** Température du FPA en baisse à la vitesse attendue

### Étape 5 — Surveiller la stabilisation (5-15 minutes)
**Action:** Poursuivre la surveillance toutes les 5 minutes pendant que la boucle se ferme.
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+10 min
**Verify:** `payload.fpa_temp` dans la plage [-16.0C, -14.0C] sous 10s
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+15 min
**Verify:** `payload.fpa_temp` dans la plage [-16.0C, -15.0C] sous 10s
**Note:** Le détecteur ne descend jamais *sous* la bande de consigne. Une lecture plus froide
que -16.5C est une panne de régulation, et non un refroidisseur trop performant ; le refroidisseur
régule sur la consigne, il ne fonctionne pas en boucle ouverte.
**GO/NO-GO:** FPA à la consigne commandée

### Étape 6 — Vérifier que la température opérationnelle est atteinte
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3)
**Verify:** `payload.fpa_temp` (0x0601) dans la plage [-16.5C, -14.5C] sous 10s
**TC:** `GET_PARAM(param_id=0x0610)` (Service 20, Subtype 3) — `payload.fpa_ready`
**Verify:** `payload.fpa_ready` (0x0610) = 1 sous 60s après l'entrée dans la bande
**Action:** C'est l'indicateur de disponibilité, et non une température mémorisée, qui conditionne
la prise de vue : il signifie que la boucle s'est stabilisée autour de la consigne **active** (−1 K /
+5 K) et que le détecteur est à −3,0 °C ou en dessous. Il comporte une hystérésis de 60 s ;
s'attendre donc à ce qu'il se positionne environ une minute après l'arrivée de la température.
**TC:** `GET_PARAM(param_id=0x0631)` (Service 20, Subtype 3) — relecture de la consigne du refroidisseur (0x0621 est le RSB de la bande VERTE, et non la consigne)
**Verify:** `payload.fpa_setpoint == -15.0` (0x0631, timeout 10 s)
**TC:** `GET_PARAM(param_id=0x064A)` (Service 20, Subtype 3) — `payload.cooler_floor_c`
**TC:** `GET_PARAM(param_id=0x064B)` (Service 20, Subtype 3) — `payload.cooler_margin_k`
**Verify:** `payload.cooler_margin_k > 0` (0x064B, timeout 10 s) — la consigne
commandée est atteignable à la température de puits et à la charge actuelles. S'attendre à environ
+5 K pour la consigne nominale de −15 °C avec un puits à +12 °C.
**Note:** `cooler_margin_k` <= 0 signifie que le refroidisseur NE PEUT physiquement PAS atteindre la
consigne commandée ici — la solution est une consigne plus chaude, et non une attente prolongée.
Le plancher atteignable en 0x064A est recalculé à chaque cycle à partir du bilan thermique
`UA*dT^2 + (Q_load + eta*P)*dT - eta*P*T_h = 0` ; il varie donc avec le puits et
avec la charge de prise de vue de 2 W : −20,35 °C au repos avec un puits à +12 °C, −19,24 °C en
prise de vue, et seulement −12,83 °C avec un puits à +20 °C, où même la consigne nominale de −15 °C
est hors d'atteinte.
**GO/NO-GO:** FPA à la consigne commandée, `fpa_ready` = 1, marge du refroidisseur positive

### Étape 7 — Vérifier la stabilité de la température
**Action:** Surveiller la température du FPA pendant 10 minutes pour confirmer une régulation stable à la consigne.
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+35 min
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+40 min
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — à T+45 min
**Verify:** `payload.fpa_temp` reste dans la plage [-16.5C, -14.5C] sur tous les échantillons
**Verify:** Variation de température < 1.0C crête à crête sur 10 minutes
**Action:** Consigner les données de stabilité. Le nœud régulé tient 3 sigma = 0,5 K
autour de sa consigne ; une variation crête à crête inférieure à 0,5 °C correspond donc à des performances de régulation normales,
et au-delà de 1,0 °C elle indique une boucle dégradée.
**GO/NO-GO:** Température du FPA stable à la consigne opérationnelle

### Étape 8 — Surveiller pendant l'éclipse (le cas échéant)
**Action:** Si le passage couvre une éclipse, vérifier que le refroidisseur maintient la température du FPA.
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — pendant l'éclipse
**Verify:** `payload.fpa_temp` reste dans la plage [-16.5C, -14.5C] sous 10s
**Verify:** `eps.bus_voltage` (0x0105) > 30.9V (le bus tient avec la charge du refroidisseur) sous 10s
**GO/NO-GO:** Le refroidisseur maintient la consigne pendant l'éclipse avec une alimentation suffisante

### Étape 9 — Établir le rapport d'activation du refroidisseur
**Action:** Rassembler la courbe complète de mise en froid (température en fonction du temps), la consommation du refroidisseur, les données de stabilité thermique et les performances en éclipse. Diffuser le rapport d'activation du refroidisseur du FPA. Le FPA est désormais prêt pour la prise de vue.
**GO/NO-GO:** Refroidisseur du FPA activé et stable — prêt pour COM-011 (Étalonnage de la charge utile)

## Conduite à tenir hors nominal
- Si la température du FPA ne baisse pas après 2 minutes : vérifier l'état du refroidisseur via `GET_PARAM(param_id=0x040C)`. Si `tcs.cooler_fpa` (0x040C) vaut 1 mais `eps.pl_fpa_cooler` (0x0114) vaut 0, la
  ligne du refroidisseur n'est pas alimentée et rien n'est pompé — c'est le défaut de la phase 4,
  qui ne devrait plus pouvoir se produire. Si les deux valent 1 et que
  `payload.cooler_pwr` (0x0602) est nul, la machine est défaillante. Si les deux valent 1,
  que la consommation est de 15 W et que la température ne baisse toujours pas, lire
  `payload.cooler_margin_k` (0x064B) : une valeur <= 0 signifie que la consigne est hors
  d'atteinte au puits actuel, ce qui est un problème de configuration, et non une panne. Éteindre le refroidisseur, éteindre la charge utile. Faire remonter à l'ingénieur thermique charge utile.
- Si la vitesse de mise en froid est inférieure à 2 °C/min sur les deux premières minutes : cela indique un rendement réduit du refroidisseur ou une charge thermique plus élevée que prévu. Laisser plus de temps. Si le FPA ne peut pas atteindre -14.5C en 20 minutes, consigner une anomalie. La prise de vue reste possible avec une consigne plus chaude, jusqu'à -3.0 C, au prix d'un RSB réduit —
  commander de nouveau la consigne avec `PAYLOAD_COOLER_SETPOINT` plutôt que d'attendre
  indéfiniment. L'enveloppe commandable va de -20 C à 0 C
  (`subsystems/tcs.yaml` `setpoint_min_c` / `setpoint_max_c`).
- Si la tension du bus descend sous 30.9V avec le refroidisseur en marche : désactiver le refroidisseur via `FPA_COOLER(on=0)` (func_id 43, octets `2B 00`). Contrôler le SOC de la batterie. Attendre un meilleur état de charge ou un meilleur éclairement. Réessayer lors du prochain passage éclairé avec une batterie pleine.
- Si la température du FPA oscille de plus de 1C crête à crête à la consigne : la boucle de régulation du refroidisseur doit peut-être être réglée. Contrôler la consigne via `GET_PARAM(param_id=0x0631)`. Si l'oscillation persiste, commander de nouveau la consigne avec `PAYLOAD_COOLER_SETPOINT(setpoint=-15.00 degC)` (func_id 36, octets `24 64 D7`) — il n'existe aucun paramètre de gain du refroidisseur commandable.
- Si le refroidisseur introduit des vibrations excessives (détectées par la gigue de l'accéléromètre) : comparer la gigue d'attitude de l'AOCS refroidisseur en marche et à l'arrêt. Si la gigue dépasse l'exigence de pointage, programmer le fonctionnement du refroidisseur en dehors des périodes de prise de vue. Consulter l'ingénieur AOCS pour le réglage des filtres.

## Postconditions
- [ ] Refroidisseur du FPA activé et en fonctionnement
- [ ] Température du FPA stable à la consigne commandée (-15C, bande de -16.5C à -14.5C)
- [ ] `payload.fpa_ready` (0x0610) = 1
- [ ] Stabilité de température < 1.0C crête à crête
- [ ] Consommation du refroidisseur de 14-16 W conforme à la spécification
- [ ] `eps.pl_fpa_cooler` (0x0114) = 1 — la ligne EPS du refroidisseur est alimentée
- [ ] `payload.cooler_margin_k` (0x064B) > 0 — la consigne est dans le domaine
      d'autorité du refroidisseur au puits actuel
- [ ] Tension du bus maintenue sous la charge du refroidisseur
- [ ] Courbe de mise en froid documentée
- [ ] Performances en éclipse vérifiées (si l'essai a été fait)
- [ ] Rapport d'activation du refroidisseur du FPA diffusé

## État de sortie
- Refroidisseur EN MARCHE (`tcs.cooler_fpa` 0x040C = 1, ligne 0x0114 = 1) et laissé
  en marche pour COM-012 (première lumière), qui prend une image aussitôt. Toute commande
  `PAYLOAD_SET_MODE(mode=1)` (STANDBY) ultérieure l'arrête de nouveau : en exploitation courante,
  le refroidisseur ne fonctionne que pour préparer une prise de vue et pendant la prise de vue
- `payload.fpa_ready` (0x0610) = 1 --- FPA à la consigne
- Aucun autre état touché

**PROCÉDURE SUIVANTE :** COM-012 (Première lumière --- le FPA refroidi est ce dont la première lumière a besoin ; l’étalonnage COM-011 suit)
