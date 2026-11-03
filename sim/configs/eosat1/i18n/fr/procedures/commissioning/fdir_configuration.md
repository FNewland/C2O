# COM-008 : Configuration de la FDIR et fonctions de protection
**Sous-système :** OBDH / EPS / Tous
**Phase :** COMMISSIONING
**Révision :** 2.0 --- réécrite en 2026-08c. La révision 1.0 lisait et écrivait des paramètres
de « seuils FDIR » 0x0320-0x0331 qui sont en réalité la télémesure de rapport cyclique des réchauffeurs du TCS,
et son étape de rétablissement commandait `OBC_SET_MODE(mode=1)` en croyant que
1 = NOMINAL --- c'est SAFE ; la fiche se terminait donc avec l'OBC en mode SAFE et
toutes les fiches suivantes en héritaient. Les véritables interfaces de protection de bord sont
le service 12 (surveillance des paramètres), le service 19 (événements-actions), la table des règles
FDIR (`fdir.yaml`, configurée au sol) et l'échelle de délestage EPS commandée ;
cette révision les met en œuvre et se termine dans l'état où elle a commencé.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-007 --- OBC en NOMINAL (`obdh.mode` 0x0300 = 0),
AOCS en NOMINAL commandé, liaison descendante en LOW, lignes charge utile/refroidisseur sur OFF, aucun verrou
de délestage (`eps.load_shed_stage` 0x0134 = 0).

## Objet
Confirmer que la chaîne de protection autonome est configurée et manifestement opérationnelle
avant que la charge utile ne vole : le service de surveillance S12 et ses définitions, la
table événements-actions S19 qui associe les déclencheurs aux actions de rétablissement S8, la télémesure
de synthèse FDIR, et l'échelle de délestage commandée avec la sémantique de verrouillage 2026-08c
(les niveaux commandés se VERROUILLENT ; l'ordre de délestage depuis l'état nominal est 1 = charge utile,
2 = + fpa_cooler, 3 = + ttc_tx ; le niveau 0 lève le verrou SANS réalimenter
quoi que ce soit ; les événements 0x0106-0x0108 sont émis à chaque niveau).

## Prérequis
- [ ] COM-001 à COM-007 terminées
- [ ] OBC en mode NOMINAL (`obdh.mode` 0x0300 = 0)
- [ ] `eps.bat_soc` (0x0101) > 70 %
- [ ] Liaison bidirectionnelle en bande S active avec une marge de liaison > 6 dB
- [ ] Le directeur de vol a approuvé l'essai des fonctions de protection

## Déroulement

### Étape 1 --- Activer et inventorier le service de surveillance S12
**TC:** `MON_ENABLE` (Service 12, Subtype 1) --- activer la surveillance bord des paramètres
**TC:** `MON_REPORT_DEFS` (Service 12, Subtype 12) --- demander la table des définitions
**Verify:** Rapport de définitions TM(12,13) reçu sous 10s
**Action:** Comparer l'ensemble de surveillances rapporté à la base de données d'opérations
(`monitoring/s12_defs`) : toutes les définitions livrées présentes, aucune inattendue.
**GO/NO-GO:** Service de surveillance activé avec la table de définitions attendue

### Étape 2 --- Inventorier la table événements-actions S19
**TC:** `EA_REPORT_DEFS` (Service 19, Subtype 8) --- demander la table événements-actions
**Verify:** Rapport TM(19,128) reçu sous 10s
**Action:** Confirmer que les règles livrées sont présentes et ACTIVÉES --- en particulier
la chaîne de gestion du moment cinétique (surveillance S12 sur `aocs.h_env_frac` 0x02BA déclenchant
l'ea_id 2001, dont l'action est la S8 func 1, la fonction de désaturation) et la chaîne de mise
en sécurité sur surchauffe TCS (ea 3003, armée sur la limite HAUTE S12 seulement : un OBC froid
est signalé, pas mis en sécurité). Consigner la table dans le rapport de configuration
de la FDIR.
**GO/NO-GO:** Table événements-actions conforme à la base de données d'opérations

### Étape 3 --- Lire la télémesure de synthèse FDIR
**TC:** `GET_PARAM(param_id=0x0700)` (Service 20, Subtype 3) --- `fdir.level`
**TC:** `GET_PARAM(param_id=0x0701)` (Service 20, Subtype 3) --- `fdir.active_alarms`
**Verify:** `fdir.level` (0x0700) = 0 sous 10s --- aucune contingence verrouillée
**Verify:** `fdir.active_alarms` (0x0701) = 0 sous 10s
**Action:** Toute lecture non nulle signale ici une alarme verrouillée inexpliquée ---
la résoudre avant d'essayer l'échelle de délestage, faute de quoi le résultat de l'essai serait ininterprétable.
**GO/NO-GO:** FDIR au repos --- référence propre pour l'essai fonctionnel

### Étape 4 --- Essai fonctionnel : verrou de délestage commandé
**Action:** Consigner l'état d'entrée des lignes de l'ordre de délestage : `eps.pl_payload`
(0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112). À ce
stade de la recette en orbite, la charge utile et le refroidisseur sont sur OFF (leurs fiches n'ont pas été exécutées),
le niveau 1 ne modifie donc aucune ligne --- l'essai observe le VERROU et son événement, ce qui
est exactement le comportement 2026-08c dont on fait la recette.
**TC:** `EPS_EMERGENCY_LOAD_SHED(stage=1)` (Service 8, Subtype 1, func_id 25) --- commander le niveau 1
**Verify:** `eps.load_shed_stage` (0x0134) = 1 sous 5s --- le niveau COMMANDÉ
se VERROUILLE (il était auparavant remis à 0 au cycle suivant)
**Verify:** Événement `LOAD_SHED_STAGE_1` (0x0106) dans le journal des événements sous 10s
**Verify:** `eps.pl_payload` (0x0113) = 0 --- le échelon charge utile est délesté
**Note:** NE PAS commander ici le niveau 2 ou 3 : le niveau 3 déleste `ttc_tx` et coupe
cette liaison descendante même. La descente progressive des niveaux relève de CTG-001/CTG-023, lorsque le
satellite est réellement en difficulté ; la recette en orbite démontre le verrou et sa
levée.
**TC:** `EPS_EMERGENCY_LOAD_SHED(stage=0)` (Service 8, Subtype 1, func_id 25) --- lever le verrou
**Verify:** `eps.load_shed_stage` (0x0134) = 0 sous 5s
**Verify:** Chaque indicateur de ligne consigné ci-dessus est INCHANGÉ --- le niveau 0 lève le
verrou et ne réalimente RIEN ; le rétablissement est toujours un acte explicite de l'opérateur
**GO/NO-GO:** Verrou positionné, événement émis, verrou levé ; aucune ligne réalimentée par le niveau 0

### Étape 5 --- Confirmer l'absence d'état de protection résiduel
**TC:** `GET_PARAM(param_id=0x0700)` (Service 20, Subtype 3) --- `fdir.level`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `fdir.level` (0x0700) = 0 sous 10s
**Verify:** `eps.load_shed_stage` (0x0134) = 0 sous 10s
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) sous 10s --- cette fiche n'effectue AUCUNE
excursion de mode de l'OBC et ne doit pas se terminer avec un OBC en SAFE (le défaut de la rév. 1.0)
**GO/NO-GO:** Chaîne de protection armée, état du satellite exactement identique à l'entrée

## Conduite à tenir hors nominal
- Si TM(12,13) ou TM(19,128) est vide ou s'il manque des définitions : recharger la configuration de surveillance et d'événements-actions depuis la base de données d'opérations (`MON_ADD_DEF` / `EA_ADD` selon l'enregistrement de la base) et redemander le rapport.
- Si `eps.load_shed_stage` ne se verrouille pas à l'étape 4 : la correction 2026-08c du gestionnaire de délestage a régressé --- ouvrir un défaut simulateur/logiciel de vol ; ne pas engager la recette en orbite de la charge utile avec une échelle de délestage non éprouvée.
- Si le niveau 0 réalimente une ligne : idem --- c'est précisément le défaut que la correction 2026-08c a supprimé. Consigner et faire remonter.
- Si `fdir.level` != 0 à l'étape 3 ou 5 : lire le journal FDIR, identifier la règle verrouillée, supprimer la cause sous-jacente. Ne jamais la masquer en désactivant la règle pour valider la fiche.

## État de sortie
- IDENTIQUE à l'état d'entrée : OBC en NOMINAL, aucun verrou de délestage, aucune ligne modifiée,
  surveillance S12 activée (elle l'était déjà ; l'étape 1 est idempotente)
- Chaîne de protection inventoriée et démontrée fonctionnellement

## Postconditions
- [ ] Définitions S12 et événements-actions S19 vérifiés par rapport à la base de données
- [ ] Sémantique du verrou de délestage démontrée (verrouillage, événement, levée, aucune réalimentation)
- [ ] Télémesure de synthèse FDIR au repos
- [ ] OBC confirmé en NOMINAL à la sortie
- [ ] Rapport de configuration de la FDIR établi

**PROCÉDURE SUIVANTE :** COM-009 (Mise sous tension de la charge utile)
