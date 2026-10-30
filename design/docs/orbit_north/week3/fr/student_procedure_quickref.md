---
title: "Aide-mémoire des procédures"
subtitle: "ORBIT NORTH · guide de poche de l'opérateur, semaine 3"
course-codes: "GNG 3100 · SYS 5186"
term: "Été 2026"
version: "v1 — 2026-05-05"
language: fr
brand: uottawa-horizon
publisher: "Faculté de génie · École de conception et d'innovation pédagogique en génie (ECIPG)"
audience: "étudiantes et étudiants en console"
expected-reading: "Parcourez-le avant chaque journée de simulation. Lisez en entier toute procédure que votre équipe a le plus de chances d'exécuter."
---

# Aide-mémoire des procédures

Les vingt-cinq procédures que vous utiliserez le plus probablement pendant la semaine 3, au
format d'une carte chacune. Les fichiers de procédure complets font foi —
ces cartes sont des repères, pas des substituts.

Format des cartes : **ID · Titre · Postes responsables · Déclencheur · 3 étapes principales ·
Critère de sortie · Fichier**.

Référence faisant foi pour les procédures :
`~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
ainsi que les fichiers de chaque procédure dans les sous-dossiers.

---

## Procédures LEOP

[Claude Code : produire une carte d'une page par procédure. Utiliser ce modèle :]

> **LEOP-001 · Première acquisition du signal et amorçage de l'OBC**
> *Postes responsables :* directeur de vol · TT&C · FDIR/Systèmes
> *Déclencheur :* premier passage au-dessus d'Iqaluit après expiration de la minuterie de séparation.
> *3 étapes principales :* (1) configurer la station sol, surveiller l'acquisition RF ;
> (2) vérifier la balise du chargeur d'amorçage (SID 11) ; (3) envoyer la commande OBC_BOOT_APP
> (S8 func_id 55).
> *Sortie :* logiciel applicatif en cours d'exécution, HK complète émise.
> *Fichier :* `procedures/leop/first_acquisition.md`

Cartes requises pour cette section :
- LEOP-001 Première acquisition du signal et amorçage de l'OBC
- LEOP-002 Bilan de santé initial
- LEOP-006 Synchronisation temporelle
- LEOP-007 Mise sous tension séquentielle

[Claude Code : inclure aussi LEOP-003 (Restitution d'orbite initiale)
et LEOP-005 (Acquisition du Soleil) pour les étudiants avancés qui les
atteignent pendant la simulation.]

---

## Procédures de recette en orbite

[Claude Code : une carte par procédure listée ci-dessous, même format que
les cartes LEOP.]

- COM-001 Vérification de l'EPS
- COM-002 Vérification du TCS
- COM-005 Transitions de modes SCAO
- COM-006 Vérification de la liaison TTC
- COM-007 Vérification de l'OBDH
- COM-008 Configuration de la FDIR
- COM-009 Mise sous tension de la charge utile
- COM-010 Activation du refroidisseur du FPA
- COM-011 Étalonnage de la charge utile
- COM-012 Première lumière

---

## Procédures nominales

[Claude Code : une carte par procédure.]

- NOM-001 Ouverture de passage
- NOM-002 Séance de prise de vue
- NOM-003 Transmission des données au sol
- NOM-009 Bilan de santé de routine
- NOM-012 Passation de consignes

---

## Procédures de contingence (les plus probables pendant la semaine 3)

[Claude Code : une carte par procédure.]

- CTG-001 Délestage sur sous-tension
- CTG-002 Reprise après anomalie SCAO
- CTG-003 Rétablissement après perte de liaison TTC
- CTG-007 Anomalie de roue de réaction
- CTG-012 Traitement d'une surintensité
- CTG-019 Absence de télémesure en début de passage

---

## Procédures d'urgence (à lire une fois, en principe jamais déclenchées)

Simple mention — vous devez savoir qu'elles existent :

- EMG Mode survie d'urgence (`procedures/emergency/emergency_safe_mode.md`)
- EMG Perte d'attitude
- EMG Perte de communication
- EMG Redémarrage de l'OBC
- EMG Emballement thermique

Si vous êtes sur le point de recourir à l'une d'elles, **appelez d'abord le
FD**. Ces procédures comportent le passage en mode survie parmi leurs étapes, et vous
ne déclenchez pas le mode survie sans autorisation du FD.

---

## Comment lire un fichier de procédure

[Claude Code : 200 mots. Les fichiers de procédure du simulateur suivent une
structure constante. La présenter à partir de l'exemple
`procedures/leop/first_acquisition.md` : en-tête,
préconditions, étapes avec colonne des responsables, vérifications, critères de
sortie, dépannage.]

---

## Correspondance entre procédures et commandes MCS

Chaque étape de procédure qui comporte une commande indique le service PUS
à utiliser (d'après `mcs/pus_services.yaml`) :

| Service | Usage |
|---------|-----|
| S1 | Vérification des télécommandes (succès / échec de la dernière commande) |
| S3 | Configuration des données de servitude (quels SID sont émis et quand) |
| S5 | Rapports d'événements (événements d'anomalie émis par le satellite) |
| S8 | Gestion des fonctions (appel de fonctions du satellite, p. ex. OBC_BOOT_APP) |
| S9 | Gestion du temps (réglage de l'heure, corrélation temporelle) |
| S11 | Plan bord (télécommandes datées) |
| S15 | Stockage et restitution à bord (transmission au sol de la mémoire de masse) |
| S17 | Test de connexion (contrôle de la liaison montante-descendante) |
| S19 | Service événement-action (déclencher une action de l'OBC sur un événement) |
| S20 | Gestion des paramètres (lecture / écriture de paramètres de l'OBC) |

Vous commandez via l'interface du MCS ; vous n'avez pas à écrire vous-même
les trames PUS.

---

## Quand vous êtes bloqué

1. Faites une pause. Utilisez une annonce : « [Poste], standby. »
2. N'envoyez aucune commande. Relisez le critère de sortie de la procédure.
3. Demandez au FD un « Hold » de 60 secondes.
4. Si le FD accepte, consignez l'attente et consultez la section du manuel
   relative au sous-système concerné
   (`configs/eosat1/manual/0*.md`).
5. Si vous ne parvenez pas à résoudre le problème, le FD annonce *no-go* et l'équipe revient
   au dernier état vérifié.

---

## Références

- Index des procédures du simulateur :
  `~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
- ECSS-E-ST-70-32C — *Test and operations procedures*
- CCSDS *Mission Operations Services Concept* (CCSDS 520.0-G) —
  https://public.ccsds.org/Pubs/520x0g4.pdf
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F)
