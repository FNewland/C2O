# COM-005 : Transitions de modes SCAO
**Sous-système :** AOCS
**Phase :** COMMISSIONING
**Révision :** 2.0 --- réécrite en 2026-08c d'après la table définitive des transitions
(`docs/plan_2026-08c/AOCS_MODE_TRANSITIONS.md`). La révision 1.0 utilisait une
numérotation à cinq modes qui n'a jamais correspondu au logiciel de vol (elle appelait
le mode 2 COARSE_SUN et le mode 3 NOMINAL, essayait un « IDLE » qui est le mode 0 OFF,
et supposait que la fiche COMMENCE en COARSE_SUN --- ce n'est pas le cas : COARSE_SUN est un
maintien transitoire, et lorsque COM-005 arrive, l'AOCS est depuis longtemps en NOMINAL, commandé
par COM-004 depuis la décision Q16 du 2026-10-30).
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de COM-003 --- les quatre roues ACTIVÉES, senseur stellaire
en suivi, gyromètres étalonnés, AOCS dans la famille NOMINAL : mode (0x020F) = 4
NOMINAL ou 8 ECLIPSE (COM-004 a commandé NOMINAL pour sortir du maintien COARSE_SUN et
COM-003 l'y a maintenu ; 8 est le même état opérationnel côté ombre).

## Objet
Mettre en œuvre chaque transition COMMANDÉE utilisée par le concept d'opérations, et OBSERVER
(sans les commander) les transitions automatiques, afin que le comportement de gestion des modes soit
démontré de bout en bout avant que la charge utile ne s'appuie dessus. La règle constante,
issue de la table des transitions : **commander ce qui est commandé, attendre et vérifier ce qui
est automatique, et ne jamais vérifier le mode que l'on vient de quitter.**

Codes de mode canoniques (`configs/eosat1/aocs/aocs_mode_codes.yaml`) : 0 OFF,
1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW,
7 DESAT, 8 ECLIPSE, 9 INERTIAL. `aocs.commanded_mode` (0x0297) mémorise l'INTENTION
du sol (positionné uniquement lorsque 4, 5, 9 ou OFF est commandé) ; `aocs.mode_demoted`
(0x0298) = 1 chaque fois que le mode en vol diffère du mode commandé.

## Prérequis
- [ ] COM-003 (Étalonnage des capteurs) et COM-004 (Vérification des actionneurs) terminées
- [ ] `aocs.wheels_enabled` (0x0260) = 4 ; senseur stellaire suivant >= 5 étoiles
- [ ] `eps.bat_soc` (0x0101) > 65 %
- [ ] OBC en mode NOMINAL (`obdh.mode` 0x0300 = 0)
- [ ] Liaison bidirectionnelle en bande S active ; noter que les fenêtres d'observation de cette
      fiche dépassent la durée d'un passage --- les transitions automatiques se déroulent sans
      contact sol et sont vérifiées au contact suivant

## Déroulement

### Étape 1 --- Mémoriser le mode commandé (NOMINAL)
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- NOMINAL
**Note:** L'AOCS est normalement déjà en mode 4 --- COM-004 l'a
commandé. Cette commande est tout de même envoyée : elle MÉMORISE
`aocs.commanded_mode` (0x0297) = 4, valeur sur laquelle chaque transition automatique
fonde son chemin de retour. L'intention doit être explicite avant que cette fiche
ne commence à faire passer le véhicule par des transitoires.
**Verify:** `aocs.mode` (0x020F) dans {4, 8} sous 300s --- 8 (ECLIPSE) est le
passage automatique côté ombre du même état commandé
**Verify:** `aocs.commanded_mode` (0x0297) = 4 sous 10s
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg sous 600s (côté éclairé)
**GO/NO-GO:** NOMINAL commandé, mémorisé et convergé

### Étape 2 --- COMMANDÉE : NOMINAL -> FINE_POINT (soumise à verrou)
**TC:** `AOCS_FINE_READY_CHECK` (Service 8, Subtype 1, func_id 89) --- lire le masque des conditions préalables
**Verify:** `aocs.fine_ready` (0x02C5) = 0 sous 1800s --- les sept conditions au vert
(bit0 ST < 5 étoiles, bit1 < 3 roues, bit2 MEKF non convergé depuis 30 s, bit3 vitesse
>= 0.01 deg/s, bit4 moment cinétique >= 70 %, bit5 propagation seule/éclipse, bit6 basculement
non inactif depuis 60 s). En éclipse, le bit5 maintient le masque non nul --- attendre l'arc
éclairé plutôt que de lutter contre lui.
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1, func_id 0) --- FINE_POINT
**Verify:** `aocs.mode` (0x020F) = 5 sous 30s
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg sous 300s
**Note:** Un masque non nul fait refuser la commande avec 0x0A22, le masque figurant dans la
réponse --- c'est le verrou qui joue son rôle, pas une panne.
**GO/NO-GO:** FINE_POINT atteint par son verrou, pointage inférieur à 0.1°

### Étape 3 --- COMMANDÉE : FINE_POINT -> NOMINAL
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 sous 30s
**Verify:** `aocs.commanded_mode` (0x0297) = 4 sous 10s
**GO/NO-GO:** Retour propre en NOMINAL

### Étape 4 --- COMMANDÉE : NOMINAL -> INERTIAL et retour
**TC:** `AOCS_SET_MODE(mode=9)` (Service 8, Subtype 1, func_id 0) --- INERTIAL (maintien ECI)
**Verify:** `aocs.mode` (0x020F) = 9 sous 30s
**Note:** INERTIAL ne cède pas la place à l'éclipse (table des transitions 1.2) --- c'est
le seul mode opérationnel qui se maintient à travers le terminateur.
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- retour en NOMINAL
**Verify:** `aocs.mode` (0x020F) = 4 sous 30s
**GO/NO-GO:** Maintien INERTIAL entré et quitté par commande

### Étape 5 --- AUTOMATIQUE : COARSE_SUN est un maintien, pas une destination
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) --- maintien de sécurité COARSE_SUN
**Verify:** `aocs.mode` (0x020F) = 3 sous 30s
**Verify:** `aocs.mode_demoted` (0x0298) = 1 sous 30s --- le satellite sait
qu'il est en deçà de son mode commandé
**Action:** ATTENDRE maintenant. Avec des CSS valides, une erreur d'attitude < 15° maintenue pendant 60 s
et le senseur stellaire en suivi, l'AOCS se promeut de lui-même vers le mode
COMMANDÉ (0x0297 = 4) sans autre action du sol.
**Verify:** `aocs.mode` (0x020F) = 4 sous 1800s --- la promotion AUTOMATIQUE
(prévoir en sus un arc d'éclipse complet si le maintien chevauche le terminateur)
**Verify:** `aocs.mode_demoted` (0x0298) = 0 sous 30s après la promotion
**Note:** NE PAS vérifier mode = 3 « quelques minutes plus tard » --- une fiche qui stationne en
COARSE_SUN et s'attend à l'y retrouver est exactement le défaut que cette révision
supprime. La vérification après le maintien porte sur le mode PROMU.
**GO/NO-GO:** Maintien entré par commande, QUITTÉ automatiquement, indicateur de rétrogradation ayant basculé dans les deux sens

### Étape 6 --- AUTOMATIQUE : passage en éclipse (observé au passage)
**Action:** Au cours de la fiche, l'orbite franchit le terminateur. Confirmer
dans l'archive que NOMINAL est passé en ECLIPSE (mode 8) à l'entrée (anti-rebond de
5 s) et est revenu à la sortie, avec `aocs.commanded_mode` (0x0297) = 4 constant
tout du long. Aucune commande n'est associée à cette étape.
**Verify:** `aocs.mode` (0x020F) dans {4, 8} à chaque échantillon d'archive depuis l'étape 3
**GO/NO-GO:** Passage en éclipse automatique dans les deux sens, intention préservée

### Étape 7 --- COMMANDÉE avec sortie AUTOMATIQUE : désaturation
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1)
**Verify:** `aocs.mode` (0x020F) = 7 sous 30s --- DESAT
**Action:** DESAT sort D'ELLE-MÊME (moment cinétique dans la bande morte, enveloppe à la
cible de sortie, ou vitesses des roues redescendues --- maintenu 10 s ; ou temporisation de désaturation
inefficace, 0x029C/événement 0x020E). Ne pas commander la sortie.
**Verify:** `aocs.mode` (0x020F) = 4 sous 900s --- retour automatique au
mode commandé
**GO/NO-GO:** Désaturation effectuée, retour autonome

### Étape 8 --- Documenter la matrice des transitions
**Action:** Établir la matrice de vérification. Les entrées COMMANDÉES portent la TC
et sa vérification ; les entrées AUTOMATIQUES portent le déclencheur et l'instant observé.

| Transition | Type | Preuve |
|---|---|---|
| (entrée) COARSE_SUN -> NOMINAL | commandée (COM-004, étape 1b) | archive |
| NOMINAL -> FINE_POINT | commandée, soumise au verrou 0x02C5 | Étape 2 |
| FINE_POINT -> NOMINAL | commandée | Étape 3 |
| NOMINAL -> INERTIAL -> NOMINAL | commandée | Étape 4 |
| NOMINAL -> COARSE_SUN | commandée (maintien) | Étape 5 |
| COARSE_SUN -> NOMINAL | promotion AUTOMATIQUE | Étape 5 |
| NOMINAL <-> ECLIPSE | AUTOMATIQUE (terminateur) | Étape 6 |
| NOMINAL -> DESAT | commandée | Étape 7 |
| DESAT -> NOMINAL | sortie AUTOMATIQUE | Étape 7 |

**Note:** DETUMBLE et SAFE_BOOT ne sont délibérément PAS mis en œuvre ici : DETUMBLE
a été réellement exécuté en LEOP-007/LEOP-005, et y entrer de nouveau maintenant coûterait
une séquence complète de réacquisition sans information nouvelle. SLEW est mis en œuvre par les
fiches de prise de vue (`AOCS_SLEW_TO`).
**GO/NO-GO:** Toutes les lignes prouvées --- recette de la gestion des modes AOCS effectuée

## Conduite à tenir hors nominal
- Si `AOCS_SET_MODE(mode=5)` est refusée avec 0x0A22 : lire le masque dans la réponse S1.8 et corriger la condition nommée (senseur, roues, convergence, vitesses, moment cinétique, éclipse, basculement inactif). Un moment cinétique >= 70 % (bit4) est la raison d'être de l'étape 7 --- désaturer et réessayer.
- Si la promotion automatique de l'étape 5 n'a pas lieu dans la fenêtre : contrôler les trois conditions de promotion --- validité des CSS (l'éclipse la bloque), `aocs.att_error` < 15 deg, et senseur stellaire toujours en suivi. Une perte du senseur maintient le véhicule dans le maintien PAR CONCEPTION ; rétablir le senseur (CTG-008) plutôt que de forcer le mode.
- Si DESAT se termine avec `aocs.desat_ineffective` (0x029C) = 1 / événement 0x020E : l'autorité des magnétocoupleurs n'a pas permis de décharger à temps. Contrôler l'activation et l'état des MTQ ainsi que la position orbitale (les arcs équatoriaux déchargent lentement) ; relancer au-dessus d'un arc polaire.
- Si les vitesses angulaires divergent dans un mode quelconque : l'amortissement d'urgence est AUTOMATIQUE au-dessus du seuil de vitesse d'urgence --- ne pas chercher à le devancer. S'il se déclenche, exécuter de nouveau cette fiche depuis le début (étape 1) après le rétablissement.

## État de sortie
- AOCS en NOMINAL (ou ECLIPSE côté ombre) avec `aocs.commanded_mode`
  (0x0297) = 4 et `aocs.mode_demoted` (0x0298) = 0
- Roues activées, moment cinétique déchargé (étape 7), senseur stellaire dans la boucle
- Aucun état de ligne d'alimentation, de mode OBC, de charge utile ni de TTC touché par cette fiche

## Postconditions
- [ ] Chaque transition commandée démontrée avec le comportement de son verrou
- [ ] Chaque transition automatique OBSERVÉE, avec déclencheur et instant consignés
- [ ] Matrice des transitions archivée dans le rapport de transitions de modes
- [ ] AOCS laissé en NOMINAL commandé, moment cinétique déchargé

**PROCÉDURE SUIVANTE :** COM-006 (Vérification de la liaison TTC)
