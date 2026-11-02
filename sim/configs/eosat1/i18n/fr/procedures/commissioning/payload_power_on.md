# COM-009 : Mise sous tension de la charge utile
**Sous-système :** Charge utile / EPS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- 2026-08c : c'est désormais CETTE fiche qui alimente la ligne EPS de la charge utile
--- LEOP-007 n'y touche plus (constat du propriétaire : la LEOP alimentait
tout, y compris la charge utile). États d'entrée et de sortie déclarés.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-008 --- recette de la plateforme terminée, OBC
en NOMINAL, AOCS en NOMINAL commandé, ligne charge utile sur OFF (`eps.pl_payload` 0x0113 =
0, intacte depuis la séparation), ligne du refroidisseur du FPA sur OFF, liaison descendante en LOW.

## Objet
Mettre sous tension l'imageur multispectral pour la première fois en orbite. Faire passer
la charge utile du mode OFF au mode STANDBY. Vérifier l'initialisation de l'électronique de la charge utile
et la génération de télémesure, et confirmer que la consommation reste dans le bilan EPS. Établir
l'état de référence de la charge utile requis pour l'activation ultérieure du refroidisseur et la prise de vue.

## Prérequis
- [ ] COM-001 à COM-008 terminées — recette de la plateforme terminée
- [ ] AOCS maintenant l'attitude dans la famille NOMINAL : `aocs.mode` (0x020F) = 4
      (ou 8 en éclipse). Codes selon `configs/eosat1/aocs/aocs_mode_codes.yaml`.
- [ ] `eps.bat_soc` (0x0101) > 75 % (le mode STANDBY de la charge utile ajoute ~2,4 W ; le refroidisseur du FPA de 15 W suit en COM-010)
- [ ] `eps.power_gen` (0x0107) > 40W (phase éclairée, panneaux déployés)
- [ ] OBC en mode NOMINAL
- [ ] `tcs.temp_fpa` (0x0408) dans la plage [+5C, +25C] (ambiante, avant refroidissement)
- [ ] Liaison bidirectionnelle en bande S active avec une marge de liaison > 6 dB
- [ ] Équipe charge utile en console

## Déroulement

### Étape 1 — Référence EPS avant mise sous tension
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.bus_voltage` (0x0105) dans la plage [27.0V, 29.0V] sous 10s (la bande jaune de la console)
**Verify:** `eps.bat_soc` (0x0101) > 75 % sous 10s
**Verify:** `eps.power_gen` (0x0107) > 40W sous 10s
**Action:** Consigner comme référence la tension du bus, le SOC de la batterie et la production électrique avant mise sous tension.
**GO/NO-GO:** L'EPS peut supporter la charge supplémentaire de la charge utile

### Étape 2 — Vérifier que la charge utile est actuellement sur OFF
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27)
**Verify:** `payload.mode` (0x0600) = 0 (OFF) sous 10s
**GO/NO-GO:** Charge utile confirmée sur OFF — mise sous tension sans risque

### Étape 3 — Alimenter la ligne de la charge utile, puis commander STANDBY
**Note:** La ligne EPS de la charge utile doit être alimentée AVANT la commande de mode. Cette
fiche envoyait `PAYLOAD_SET_MODE(1)` sans `EPS_POWER_ON`, et le modèle de charge utile
remet le mode à OFF au cycle suivant lorsque sa ligne n'est pas alimentée — le mode
semblait donc pris, puis revenait silencieusement en arrière, et toutes les étapes suivantes de cette fiche
étaient exécutées sur une charge utile éteinte.
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — la ligne `payload`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — données de servitude EPS
**Verify:** `eps.pl_payload == 1` (0x0113, timeout 10 s) — ligne charge utile alimentée
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — STANDBY
**Note:** Alimentation de la charge utile activée ; la séquence de démarrage de l'électronique s'engage.
Le démarrage dure environ 45 secondes.
**TC:** `HK_ENABLE(sid=5)` (Service 3, Subtype 5) — données de servitude périodiques de la charge utile activées. Aucune fiche antérieure n'active le SID 5 (LEOP-007 n'active que le SID 2), et COM-010 puis toutes les fiches nominales supposent que le SID 5 est émis
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `payload.mode == 1` (0x0600, timeout 60 s) — STANDBY
**Verify:** Redemander le SID 5 après 60 s supplémentaires et confirmer que `payload.mode` vaut
TOUJOURS 1. Un mode qui revient à 0 au cycle suivant est la signature d'une
ligne charge utile non alimentée.
**GO/NO-GO:** Charge utile passée en STANDBY et MAINTENUE dans ce mode

### Étape 4 — Vérifier la consommation de la charge utile
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Action:** Comparer la tension du bus et la consommation électrique à la référence avant mise sous tension.
**Verify:** `eps.bus_voltage` (0x0105) > 27.0V sous 10s (bus maintenu sous la nouvelle charge)
**TC:** `GET_PARAM(param_id=0x0106)` (Service 20, Subtype 3) — `eps.power_cons`, charge totale
**Verify:** Augmentation de la charge totale par rapport à la référence de **2-3 W** sous 10 s.
(Cette ligne lisait 0x0108, c'est-à-dire `eps.eclipse_flag` — un booléen 0/1, et non une puissance.
L'augmentation attendue est la consommation de la charge utile en STANDBY selon `eps.yaml`, ~2,4 W ;
l'ancienne valeur « 10-20 W » correspondait à la consommation en STANDBY plus les 15 W du refroidisseur du FPA, qui
n'est mis en marche qu'à COM-010.)
**GO/NO-GO:** Consommation de la charge utile dans la plage attendue

### Étape 5 — Vérifier l'état de santé de l'électronique de la charge utile
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**TC:** `GET_PARAM(param_id=0x0611)` (Service 20, Subtype 3) — `payload.imager_status`
**TC:** `GET_PARAM(param_id=0x0603)` (Service 20, Subtype 3) — `payload.imager_temp`
**Verify:** `payload.imager_status` (0x0611) — mot d'état de l'imageur, aucun bit de panne positionné
**Verify:** `payload.imager_temp` (0x0603) dans sa plage de fonctionnement
**Note:** Cette étape lisait autrefois 0x0602 comme « version du micrologiciel » et 0x0603 comme
« résultat de l'autotest ». 0x0602 est `payload.cooler_pwr` (watts) et 0x0603 est
`payload.imager_temp` (degrés C). Il n'existe aucun paramètre de version de micrologiciel ni d'autotest
dans `telemetry/parameters.yaml` ; le mot d'état de l'imageur est l'indicateur de santé
que la charge utile publie réellement.
**GO/NO-GO:** Électronique de la charge utile saine — état et température de l'imageur nominaux

### Étape 6 — Contrôler la température du FPA (avant refroidissement)
**TC:** `GET_PARAM(param_id=0x0601)` (Service 20, Subtype 3) — `payload.fpa_temp`
**Verify:** `payload.fpa_temp` (0x0601) dans la plage [+5C, +30C] sous 10s
**Action:** Consigner la température ambiante du FPA avant l'activation du refroidisseur (COM-010).
**GO/NO-GO:** Température du FPA au niveau ambiant attendu

### Étape 7 — Vérifier l'interface de données de la charge utile
**TC:** `GET_PARAM(param_id=0x0604)` (Service 20, Subtype 3) — `payload.store_used` (%)
**TC:** `GET_PARAM(param_id=0x0648)` (Service 20, Subtype 3) — `payload.product_count`
**TC:** `GET_PARAM(param_id=0x0647)` (Service 20, Subtype 3) — `payload.product_mb`
**Verify:** `payload.store_used` (0x0604) autour de 20 % — la mémoire est livrée avec un
remplissage préexistant hors produits ; 20 % constitue donc la référence « vide », et non une panne
**Verify:** `payload.product_count` (0x0648) = 0 et `payload.product_mb` (0x0647)
= 0 — aucun produit catalogué avant la première lumière
**Note:** 0x0604 est `payload.store_used` exprimé en POURCENTAGE et 0x0605 est
`payload.image_count`. Cette étape les lisait comme « état de l'interface de données » et
« espace de stockage libre à bord (Mo) » ; il n'existe aucun paramètre d'état de l'interface de données.
`product_count` / `product_mb` sont les ajouts de la phase 4 qui distinguent l'imagerie réelle
du remplissage de référence de la mémoire.
**Action:** Confirmer que la charge utile peut écrire des données d'image dans la mémoire de masse.
**GO/NO-GO:** Interface de données opérationnelle, stockage disponible

### Étape 8 — Maintenir STANDBY pour la stabilisation thermique
**Action:** Maintenir la charge utile en STANDBY pendant 10 minutes pour permettre la stabilisation thermique de l'électronique. Surveiller les températures de la charge utile et de la plateforme.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — à T+5 min
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — à T+10 min
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — données de servitude de la charge utile
**Verify:** `tcs.temp_obc` (0x0406) stable (non affectée par la chaleur de la charge utile) sous 10s
**Verify:** `payload.fpa_temp` (0x0601) stable sous 10s
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) maintenu sous 10s
**GO/NO-GO:** Charge utile thermiquement stable en STANDBY

### Étape 9 — Consigner le rapport de mise sous tension de la charge utile
**Action:** Consigner toute la télémesure de mise sous tension, y compris la chronologie, la consommation, le mot d'état de l'imageur, la température de l'imageur, la température du FPA et le remplissage de référence de la mémoire. Diffuser le rapport de mise sous tension de la charge utile.
**GO/NO-GO:** Charge utile mise sous tension avec succès en STANDBY — prête pour COM-010

## Conduite à tenir hors nominal
- Si `payload.mode` ne passe pas en STANDBY sous 90s : renvoyer `PAYLOAD_SET_MODE(mode=1)` une fois. Toujours sans transition : contrôler la ligne d'alimentation de la charge utile via `GET_PARAM(param_id=0x0113)` — `eps.pl_payload`.
  (0x0610 est `payload.fpa_ready`, et non un indicateur de bus d'alimentation.) Si `eps.pl_payload` (0x0113) vaut 0, la ligne charge utile n'est pas alimentée — c'est
  le `EPS_POWER_ON(line_index=3)` de l'étape 3, et une commande de mode sans lui revient en arrière au
  cycle suivant. Si l'alimentation est présente mais que la charge utile ne répond pas, l'éteindre via `PAYLOAD_SET_MODE(mode=0)` et faire remonter.
- Si la tension du bus descend sous 27.0V lors de la mise sous tension de la charge utile : éteindre immédiatement la charge utile via `PAYLOAD_SET_MODE(mode=0)`. Contrôler le SOC de la batterie. Si le SOC < 60 %, attendre un état de charge plus élevé. En cas de problème de régulation du bus, examiner l'EPS avant de réessayer.
- Si le mot d'état de l'imageur indique une panne : le consigner via `GET_PARAM(param_id=0x0611)`. Éteindre la charge utile via `PAYLOAD_SET_MODE(mode=0)`. Ne pas engager l'activation du refroidisseur. Faire remonter à l'ingénieur charge utile avec le mot d'état de l'imageur.
- Si la consommation de la charge utile dépasse 5 W en STANDBY (pour un bilan de ~2,4 W) : une consommation inattendue peut indiquer une panne de l'électronique. Surveiller pendant 5 minutes. Si elle augmente, éteindre la charge utile. Si elle se stabilise à un niveau supérieur à l'attendu, consulter les spécifications du fabricant de la charge utile.
- Si la lecture de température du FPA est anormale : la recouper avec le nœud TCS
  `tcs.temp_fpa` (0x0408), qui est le même nœud physique publié par le modèle
  TCS. Un désaccord entre 0x0601 et 0x0408 est un problème de chaîne de télémesure ;
  une concordance sur une valeur étrange traduit un état thermique réel. En cas de panne de thermistance, noter la limitation pour COM-010 (l'activation du refroidisseur reposera sur une surveillance alternative).

## Postconditions
- [ ] Charge utile en mode STANDBY (mode 1)
- [ ] Ligne charge utile alimentée — `eps.pl_payload` (0x0113) = 1
- [ ] Consommation de la charge utile dans la plage attendue (2-3 W en STANDBY)
- [ ] `payload.imager_status` (0x0611) sans bit de panne
- [ ] Température ambiante de référence du FPA consignée
- [ ] Interface de données opérationnelle, stockage disponible
- [ ] Tension du bus stable sous la charge de la charge utile
- [ ] Rapport de mise sous tension de la charge utile diffusé

## État de sortie
- Ligne charge utile sur ON, charge utile en STANDBY (`payload.mode` 0x0600 = 1), SID 5
  lisible sur demande (`HK_REQUEST(sid=5)`) ; le SID 5 périodique est activé par NOM-005 lorsqu'une prise de vue est prévue
- REMARQUE : depuis la phase 4, TOUTE voie de commande du refroidisseur --- y compris le
  `PAYLOAD_SET_MODE` utilisé ici (funcs 16/17/26/43 et équipement S2 0x0601) ---
  alimente la ligne EPS 4 ; `eps.pl_fpa_cooler` (0x0114) peut donc déjà valoir 1 à la
  sortie. Le REFROIDISSEUR lui-même est commandé (et ses performances vérifiées) dans
  COM-010 ; cette fiche ne revendique que l'effet de bord sur la ligne.
- Aucun état AOCS, OBC, TTC ou réchauffeur touché

**PROCÉDURE SUIVANTE :** COM-010 (Activation du refroidisseur du FPA)
