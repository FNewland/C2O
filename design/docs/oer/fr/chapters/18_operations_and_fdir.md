# Chapitre 18 — Opérations de mission et FDIR

> **Lectures préalables conseillées.** ECSS-E-ST-70-11C (*Space segment operability*) ; ECSS-E-ST-70-32C (*Test and operations procedure language*) ; ECSS-E-ST-70-41C (*Packet utilisation standard*) ; NASA *Fault Management Handbook* (NASA-HDBK-1002). Ce chapitre s'appuie sur le *concept* de ConOps — phases de la mission, segments et notion de modes opérationnels — introduit au chapitre 4, §4.8, sur l'architecture du segment sol et la chronologie des opérations du chapitre 17, sur le bilan de puissance par mode du tableau 8.4 du chapitre 8 et du chapitre 9, ainsi que sur l'AMDEC (FMECA) et l'analyse des points de défaillance unique du chapitre 15. Il apporte le détail opérationnel : le tableau complet des modes, la logique de transition entre modes, l'architecture FDIR, les procédures et le traitement des anomalies.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. Structurer un document de concept d'opérations et spécifier les modes opérationnels avec leurs conditions d'entrée et de sortie
2. Tracer la machine à états des transitions de mode d'un satellite et vérifier que le mode survie est accessible depuis chaque état
3. Concevoir une architecture FDIR (détection, isolation et reprise des défaillances) dotée d'une hiérarchie de réponses autonomes
4. Rédiger des procédures opérationnelles pour les opérations de routine et de contingence selon la structure de l'ECSS-E-ST-70-32C
5. Décrire le processus de traitement des anomalies avec ses niveaux d'escalade et documenter une anomalie

Les produits de fournisseurs cités dans ce chapitre sont des exemples représentatifs et non des recommandations.

---

## 18.1 Le ConOps, document d'opérations

Le ConOps fait le pont entre la conception technique et la réalité opérationnelle. Il décrit *comment* le système sera utilisé, et pas seulement *ce qu'il* peut faire. Le chapitre 4 l'a présenté comme un livrable de définition de la mission — les phases de la mission, les trois segments et l'idée qu'un satellite possède des modes — parce que ces décisions façonnent l'architecture. Lorsque la conception atteint la PDR, le même document a acquis un second public : les personnes qui piloteront le satellite. Ce chapitre est écrit pour elles.

*[Source : ECSS-E-ST-70-11C (*Space Segment Operability*) ; IEEE 1362 (*Concept of Operations Document*)]*

### 18.1.1 Structure du ConOps

Un document ConOps complet couvre :

1. **Vue d'ensemble de la mission** — objectifs, parties prenantes, critères de succès (chapitre 4)
2. **Description du système** — segment spatial, segment sol, segment utilisateur (chapitre 8, §8.1 ; chapitre 17)
3. **Scénarios opérationnels** — opérations nominales, opérations de contingence
4. **Modes opérationnels** — définition, transitions, contraintes (§18.2)
5. **Gestion des ressources** — bilans de puissance, de données et d'ergols dans le temps (chapitres 9, 11, 12)
6. **Plan de communication** — planning des contacts, flux de données, exigences de latence (chapitre 17, §17.2)
7. **Plan d'effectifs** — personnel, quarts, besoins de formation (chapitre 17, §17.4)
8. **Maintenance et logistique** — mises à jour logicielles, maintenance des équipements sol

Les points 3, 4 et 8 sont ceux que seuls les gens des opérations rédigent bien, et ce sont aussi ceux qui manquent le plus souvent à la PDR.

### 18.1.2 Autonomie : où placer la limite

Tout ConOps incarne une décision sur ce que le satellite fait de lui-même. Cette décision dépend du temps de contact — un CubeSat en LEO est hors de visibilité d'une station unique environ 85 % du temps (chapitre 17, §17.2.3) — et du coût des effectifs. Les deux points de référence sont :

- **Pilotage par le sol :** le satellite exécute un plan de télécommandes datées envoyé chaque jour ; tout écart est traité par un passage en mode survie suivi d'une attente. Logiciel de vol simple, opérations coûteuses, reprise lente.
- **Autonomie bord :** le satellite planifie lui-même ses prises de vue à partir d'une liste de cibles envoyée depuis le sol, gère sa puissance et ses données, et se rétablit de la plupart des défauts sans le sol. Logiciel de vol complexe, opérations peu coûteuses, reprise rapide.

PROBA-2, de l'ESA (lancé en 2009 et toujours en service en 2026), est la démonstration de référence de ce à quoi conduit la seconde option pour un petit satellite : cinq modes opérationnels (*Standby*, *Science*, *Manoeuvre*, *Safe*, *Off*), environ 95 % des activités de routine automatisées par une chronologie bord, quatre à six passages par jour depuis une seule station, et seulement deux ou trois anomalies par an nécessitant une intervention du sol après la recette en orbite. L'enseignement est que l'investissement dans l'autonomie bord se rembourse directement en coût d'opérations. *[Source : ESA PROBA-2 Operations Team, « PROBA-2 : Over a Decade of Operations », SpaceOps 2020]*

---

## 18.2 Modes opérationnels

Tout satellite possède un ensemble défini de modes opérationnels. Chaque mode précise quels sous-systèmes sont actifs, la consommation électrique et les débits — et, surtout, les conditions dans lesquelles le satellite y entre et en sort.

### 18.2.1 Tableau des modes du CubeSat 3U d'observation de la Terre

Le tableau 18.1 est le tableau des modes de référence de l'exemple fil rouge 3U d'observation de la Terre, **EOSat-3U**. Les quatre valeurs de puissance des modes survie, nominal, prise de vue et liaison descendante sont celles utilisées au tableau 4.1 du chapitre 4 (la version illustrative à trois lignes), au tableau 8.4 du chapitre 8 (la répartition par sous-système) et dans le dimensionnement du générateur solaire et de la batterie du chapitre 9 ; la charge en éclipse est celle de 3,5 W du chapitre 8. Le chapitre 12, §12.5.3, relève que la charge du mode prise de vue *établie à partir des équipements* est plus proche de 10 W que de l'allocation paramétrique de 8 W — une tension sur le bilan que le concept d'opérations doit respecter en limitant le rapport cyclique de prise de vue jusqu'à ce que la conception de puissance soit refaite.

**Tableau 18.1 — Modes opérationnels d'EOSat-3U (CubeSat 3U d'observation de la Terre, SSO à 500 km)**

| Mode | Description | Puissance (W) | Débit | Durée typique | Condition d'entrée |
|------|------------|-----------|-----------|-----------------|----------------|
| **Survie** | Fonctionnalités minimales ; survie uniquement ; pointage solaire par contrôle magnétique ; charge utile et roues éteintes | 2,0 | Balise uniquement | Jusqu'à l'intervention du sol | Détection autonome d'un défaut (FDIR niveau 3) ou commande sol |
| **Amortissement (detumbling)** | Réduire la vitesse angulaire après le déploiement avec les seuls magnétocoupleurs | —, magnétocoupleurs uniquement | Servitude uniquement (100 bit/s) | Minutes à heures | Après la séparation ; vitesse angulaire au-dessus du seuil |
| **Nominal (attente)** | Pointage solaire ; tous les sous-systèmes alimentés et prêts ; la désaturation des roues s'effectue dans ce mode | 4,0 | Télémesure de servitude (1 kbit/s) | Entre les activités | Après l'amortissement ; périodes d'inactivité |
| **Prise de vue (science)** | Charge utile en fonctionnement ; pointage fin sur roues et senseur stellaire | 8,0 | Données scientifiques vers la mémoire de masse | Selon la cible (≈ 1 min par passage) | Programmé ; pointage fin atteint ; état de charge de la batterie au-dessus de la limite |
| **Liaison descendante** | Transfert à haut débit en bande S vers le sol | 10,0 | 1–5 Mbit/s (chapitre 11, §11.8.1) | Pendant le contact avec le sol (≈ 6 min) | Station en visibilité ; liaison établie |
| **Éclipse** | Opérations réduites dans l'ombre ; réchauffeurs selon les besoins | 3,5 | Servitude uniquement | ≈ 36 min par orbite (chapitre 7, §7.7) | Soleil hors du champ |

EOSat-3U n'a pas de propulsion, et donc pas de mode manœuvre ; la désaturation du moment cinétique par les magnétocoupleurs (chapitre 10, §10.5) est un sous-état du mode nominal. Une mission dotée de propulsion ajoute un mode **manœuvre** (servitude uniquement, contraintes d'attitude strictes, typiquement 15–25 W pour une plateforme plus grande) avec ses propres conditions d'entrée.

Deux vérifications s'appliquent à tout tableau des modes :

- **Le bilan de puissance du mode survie doit être positif dans le cas le plus défavorable.** Avec la charge de 2,0 W du mode survie, le générateur solaire d'EOSat-3U du chapitre 9, §9.2, charge la batterie même en attitude de culbutage ; le chapitre 9, §9.4.11, retient ces mêmes 2,0 W comme dissipation interne du cas froid.
- **L'éclipse doit pouvoir être supportée depuis n'importe quel mode.** Le dimensionnement de la batterie du chapitre 9, §9.3, utilise la charge en éclipse de 3,5 W ; si le satellite est encore en mode liaison descendante lorsqu'il entre dans l'ombre, la charge de 10 W doit être délestée dans la marge de la batterie.

### 18.2.2 Machine à états des transitions de mode

Le tableau des modes dit ce qu'est chaque mode ; la machine à états de la figure 18.1 dit comment le satellite passe de l'un à l'autre. Trois propriétés sont exigées : chaque état doit disposer d'un chemin vers le mode survie ; le mode survie doit disposer d'un chemin de retour vers le mode nominal qui *exige une commande sol* ; et aucune transition ne peut dépendre d'une ressource (puissance, connaissance d'attitude) que le mode de destination n'entretient pas lui-même.

![Machine à états des transitions de mode d'EOSat-3U](../assets/figures/fig_mode_state_machine.png)

**Figure 18.1** — Machine à états des transitions de mode d'EOSat-3U. Le mode amortissement est activé à la séparation et passe la main au mode nominal dès que la vitesse angulaire est sous le seuil ; les modes prise de vue et liaison descendante sont des excursions depuis le mode nominal, déclenchées par le planning ou par le contact avec une station, et y reviennent à leur achèvement ; le mode éclipse est activé depuis les modes nominal, prise de vue ou liaison descendante lorsque le Soleil quitte le champ de vue, et revient au mode nominal lorsqu'il réapparaît. Un défaut dans n'importe quel état conduit au mode survie, que l'on ne quitte que sur commande sol (ou, si la limite de vitesse angulaire est dépassée, en repassant en mode amortissement).

Lecture de la figure 18.1 : le mode amortissement est activé une fois à la séparation, puis de nouveau depuis le mode survie si la limite de vitesse angulaire est dépassée ; le mode nominal est le pivot ; les modes prise de vue et liaison descendante sont des excursions depuis le mode nominal, qui y reviennent à leur achèvement ou à la perte de leur condition d'entrée ; le mode survie est accessible depuis chaque état sur défaut et n'est quitté que sur commande sol. Un défaut pendant la liaison descendante ne ramène pas au mode nominal pour tomber ensuite en mode survie — il conduit directement au mode survie, car la transition intermédiaire pourrait être précisément ce qui est en panne.

---

## 18.3 Architecture FDIR

La FDIR — détection, isolation et reprise des défaillances — est la capacité autonome du satellite à détecter des défaillances, à déterminer quel composant est défaillant et à prendre des mesures correctives, le tout sans intervention du sol.

*[Source : NASA *Fault Management Handbook* (NASA-HDBK-1002) ; ECSS-E-ST-70-11C, §5.3]*
*[URL : https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002]*

### 18.3.1 Pourquoi la FDIR est essentielle pour les CubeSats

- **Contacts sol limités :** les CubeSats en LEO sont hors de visibilité ≈ 85 % du temps
- **Aucune intervention humaine à bord :** contrairement à l'ISS, personne à bord ne peut réparer quoi que ce soit
- **Contraintes thermiques :** un mode survie doit maintenir les limites thermiques en quelques minutes (chapitre 9, §9.4.11 : le cas froid d'EOSat-3U perd 7,8 °C en une seule éclipse de 36 minutes)
- **Contraintes de puissance :** sans délestage, la batterie peut se décharger complètement en une seule éclipse

### 18.3.2 Hiérarchie FDIR

La FDIR est organisée en couches (figure 18.2). Chaque niveau détecte une classe de défauts, répond avec une latence caractéristique et — si sa réponse n'élimine pas le défaut — transmet le problème au niveau supérieur. Le sol constitue le niveau le plus élevé ; c'est pourquoi toute action autonome doit être visible dans la télémesure et réversible par commande.

| Niveau | Détection | Réponse | Latence | Exemple |
|-------|-----------|----------|---------|---------|
| **0 — Matériel** | Chien de garde intégré | Réinitialisation du composant | Millisecondes | Temporisateur chien de garde du processeur |
| **1 — Équipement** | Surveillance au niveau de l'équipement | Reconfiguration de l'équipement | Secondes | Disjonction sur surintensité de l'EPS |
| **2 — Sous-système** | Bilan de santé du sous-système | Mode de repli du sous-système | Secondes à minutes | Basculement sur le senseur stellaire de secours |
| **3 — Système** | Détection d'anomalie au niveau système | Changement de mode (passage en survie) | Minutes | Transition en mode survie |
| **4 — Sol** | Diagnostic avec intervention humaine | Reprise par commande sol | Heures à jours | Investigation d'anomalie et correctif |

![Hiérarchie FDIR, du chien de garde matériel au sol](../assets/figures/fig_fdir_hierarchy.png)

**Figure 18.2** — La hiérarchie FDIR sous forme de pyramide en couches. Chaque couche, du chien de garde matériel de niveau 0 à la base jusqu'au sol de niveau 4 au sommet, a ses propres moyens de détection, sa réponse et sa latence caractéristique ; un défaut qu'une couche ne peut éliminer remonte vers le haut, et le sol peut forcer toute action autonome, car chacune est visible dans la télémesure et réversible par commande.

### 18.3.3 Logigramme de décision FDIR

```
                    NOMINAL OPERATIONS
                           |
           Panne détectée (niveaux 2–3)
                           |
                    +------v------+
                    |  FAULT      |
                    |  DETECTED   |
                    +------+------+
                           |
              +------------+------------+
              |                         |
        Panne isolée           Isolation impossible
              |                         |
        +-----v-----+           +-------v------+
        | ISOLATION  |           | SAFE MODE    |
        | SUCCESS    |           | (niveau 3)   |
        +-----+------+           +-------+------+
              |                          |
        Action de reprise          Attente du sol
              |                    (niveau 4)
        +-----v-----+                   |
        | RECOVERY   |           +------v-------+
        | ATTEMPT    |           | GROUND       |
        +-----+------+           | RECOVERY     |
              |                  +------+-------+
       Succès / échec                   |
              |                  Séquence de commandes
        +-----v-----+                   |
        | RETURN TO  |<----------------+
        | NOMINAL    |
        +------------+
```

La branche qui compte est « *cannot isolate* » (isolation impossible). Un satellite incapable de déterminer *quel* équipement est défaillant ne doit pas deviner ; il passe en mode survie et laisse le sol établir le diagnostic avec tout l'historique de télémesure. La perte d'Hitomi, au chapitre 15, §15.4.7, est l'exemple type d'un système autonome qui agit sur une isolation erronée.

### 18.3.4 Règles FDIR courantes sur les CubeSats

| Défaut | Méthode de détection | Seuil | Réponse |
|-------|-----------------|-----------|----------|
| Blocage du processeur | Temporisateur chien de garde | Aucun signal de vie pendant 60 s | Réinitialisation matérielle (niveau 0) |
| Sous-tension batterie | Surveillance de tension de l'EPS | $V_{\text{bat}} <$ 6,0 V | Délestage ; passage en mode survie |
| Surchauffe de la batterie | Capteur de température | $T_{\text{bat}} >$ 45 °C | Désactiver la charge ; réduire les charges électriques |
| Perte d'attitude | Aucune solution d'attitude pendant 5 min | Expiration de l'indicateur de santé du SCAO | Passage en mode amortissement |
| Perte de communication | Aucune liaison montante pendant 48 h | Sur temporisation | Réinitialiser le TT&C ; revenir en mode balise |
| Corruption mémoire | Compteur d'erreurs EDAC | > 10 erreurs non corrigibles/h | Nettoyage mémoire ; redémarrage sur l'image de secours |
| Anomalie de courant du générateur solaire | Capteur de courant | $I_{\text{SA}} <$ valeur attendue − 30 % | Vérifier l'attitude ; passage en mode nominal (attente) |
| Survitesse d'une roue de réaction | Surveillance de la vitesse des roues | $\omega >$ 6000 tr/min | Réduire le moment cinétique ; désaturer (chapitre 10, §10.5) |

Chaque règle devrait être tracée vers une ligne de l'AMDEC (chapitre 15, §15.4) : l'AMDEC dit ce qui peut tomber en panne et comment on le détecterait ; la règle FDIR dit ce que le satellite fait en conséquence. Le risque R-03 du registre d'UniSat-1 (OBC développé sur mesure dans l'environnement radiatif) est réduit précisément par la première et la sixième ligne de ce tableau.

### 18.3.5 Principes de conception essentiels

1. **Le mode survie doit toujours fonctionner.** C'est le dernier recours ; il doit être testé de manière exhaustive, y compris depuis chacun des autres modes et en éclipse.
2. **D'abord rester opérationnel, puis se mettre en sécurité.** Tenter de poursuivre la mission avant d'abandonner.
3. **Aucun défaut unique ne doit entraîner la perte de la mission.** Recouper avec la liste des points de défaillance unique du chapitre 15, §15.4.4.
4. **Forçage depuis le sol.** Toute action autonome doit pouvoir être commandée — et *inhibée* — depuis le sol.
5. **Journalisation.** Enregistrer chaque événement de défaut en mémoire non volatile pour analyse ultérieure ; une action FDIR qui ne laisse aucune trace ne peut pas être diagnostiquée.

---

## 18.4 Procédures opérationnelles

*[Source : ECSS-E-ST-70-32C (*Test and Operations Procedure Language*) ; ECSS-E-ST-70-01C (*On-board control procedures*)]*

### 18.4.1 Types de procédures

| Type | Objet | Exécution | Exemple |
|------|---------|-----------|---------|
| **Nominale** | Opérations programmées de routine | Automatisée (chronologie) ou manuelle | Séquence d'observation scientifique |
| **Contingence** | Réponse à des types d'anomalies connus | Semi-automatisée ; décision de l'opérateur | Reprise après passage en mode survie |
| **Urgence** | Réponse à des événements inattendus critiques | Manuelle ; décision en temps réel | Reprise après perte de communication |
| **Maintenance** | Étalonnage ou mises à jour périodiques | Manuelle programmée | Étalonnage du magnétomètre |

### 18.4.2 Structure d'une procédure (ECSS-E-ST-70-32C)

Chaque procédure comporte :

1. **Identifiant** — numéro de procédure unique (p. ex. NOM-SCI-001)
2. **Objet** — ce que la procédure accomplit
3. **Préconditions** — état du système requis avant le démarrage
4. **Étapes** — liste ordonnée d'actions, de vérifications et de décisions
5. **Résultats attendus** — ce qui doit se produire à chaque étape
6. **Actions de reprise** — que faire si les résultats attendus ne sont pas observés
7. **Postconditions** — état du système après un déroulement réussi

La discipline tient aux points 5 et 6 : chaque étape indique ce que l'on *devrait* observer et ce qu'il faut faire dans le cas contraire. Une procédure sans résultats attendus n'est qu'une liste de souhaits.

### 18.4.3 Exemple : procédure d'observation scientifique d'EOSat-3U

```
Procédure : NOM-SCI-001 « Acquisition d'une cible d'observation de la Terre »
Préconditions : mode = nominal, SoC batterie > 60 %, cible dans le champ de vue sous 10 min

Étape 1 : vérifier que le mode AOCS = pointage fin
  Attendu : état AOCS = FINE, erreur de pointage < 0.1°
  Sinon : attendre 60 s, réessayer. Toujours pas atteint → ABORT, rester en mode nominal

Étape 2 : commander la mise sous tension (ON) de la charge utile
  Attendu : la télémesure de servitude de la charge utile indique alimentation = ON sous 5 s
  Sinon : renvoyer la commande d'alimentation. Après 3 échecs → ABORT, consigner une anomalie

Étape 3 : attendre la stabilisation thermique de la charge utile (90 s)
  Attendu : température de la charge utile dans sa plage opérationnelle

Étape 4 : commander la charge utile en mode prise de vue
  Attendu : état charge utile = IMAGING, compteur de trames en progression

Étape 5 : attendre l'acquisition de la cible (heure de début prédite par le sol)
  Attendu : la prise de vue commence à l'heure prédite ± 5 s

Étape 6 : acquérir les images pendant la durée programmée

Étape 7 : commander la charge utile en attente
  Attendu : état charge utile = STANDBY

Étape 8 : commander la mise hors tension (OFF) de la charge utile (s'il n'y a plus de cible sur cette orbite)
  Attendu : la télémesure de servitude de la charge utile indique alimentation = OFF

Postconditions : mode = nominal, images stockées en mémoire de masse
```

Une procédure de contingence — la reprise après passage en mode survie, par exemple — a la même forme, mais ses préconditions sont le *diagnostic* : « journal FDIR relu et cause identifiée ; cause éliminée ou inhibée ; SoC de la batterie > 80 % ». Une reprise sans diagnostic est la manière la plus courante de passer deux fois en mode survie.

---

## 18.5 Processus de traitement des anomalies

*[Source : NASA-HDBK-1002 (*Fault Management Handbook*) ; procédures des commissions d'examen des anomalies (*Anomaly Review Board*) de l'ESA]*

### 18.5.1 Niveaux d'escalade des anomalies

| Niveau | Gravité | Délai de réponse | Autorité | Exemple |
|-------|----------|--------------|-----------|---------|
| **Vert** | Information | Jour ouvré suivant | Ingénieur d'opérations | Paramètre mineur hors de la plage attendue |
| **Jaune** | Avertissement | Sous 4 heures | Opérateur principal | Performances d'un sous-système dégradées |
| **Orange** | Grave | Sous 1 heure | Directeur de vol | Changement de mode nécessaire ; impact sur la mission |
| **Rouge** | Critique | Immédiat | Chef de projet + directeur de vol | Menace pour la mission ; passage en mode survie |

### 18.5.2 Déroulement du traitement des anomalies

```
1. DETECT (détecter) :   alarme de télémesure ou observation d'un opérateur
2. ASSESS (évaluer) :    s'agit-il d'un type d'anomalie connu ? Consulter la bibliothèque de procédures
                         → Connu :   exécuter la procédure de contingence
                         → Inconnu : continuer à l'étape 3
3. DIAGNOSE (diagnostiquer) : recueillir de la télémesure complémentaire, corréler les événements, formuler une hypothèse
4. PLAN (planifier) :    élaborer le plan de réponse (peut nécessiter un comité de revue d'anomalie)
5. EXECUTE (exécuter) :  appliquer les commandes de reprise (vérifier chaque étape)
6. VERIFY (vérifier) :   confirmer que le système est revenu dans l'état attendu
7. DOCUMENT (documenter) : consigner l'anomalie, la cause première, la réponse et le retour d'expérience
```

Deux règles empiriques issues de la pratique des agences : *éliminer d'abord l'hypothèse du sol* (un satellite silencieux est plus souvent dû à une antenne mal pointée ou à une mauvaise fréquence qu'à un émetteur hors service), et *ne pas envoyer de commande que l'on ne peut pas vérifier* (chaque envoi de l'étape 5 est suivi d'une vérification en télémesure avant le suivant).

### 18.5.3 Champs du rapport d'anomalie

| Champ | Description |
|-------|------------|
| **Identifiant de l'anomalie** | Identifiant unique (p. ex. ANO-2026-042) |
| **Date/heure (UTC)** | Moment de la détection de l'anomalie |
| **Gravité** | Vert / jaune / orange / rouge |
| **Sous-système concerné** | EPS, AOCS, TT&C, charge utile, … |
| **Observation** | Ce qui a été observé (valeurs de télémesure, tendances) |
| **Diagnostic** | Analyse des causes profondes |
| **Mesure prise** | Commandes envoyées, procédures exécutées |
| **Résultat** | État du système après la réponse |
| **Statut** | Ouverte / résolue / en cours d'investigation |
| **Retour d'expérience** | Mesures préventives pour l'avenir |

### 18.5.4 Exemple de mission réelle : défaillance des roues de réaction de Kepler

Le télescope spatial Kepler de la NASA a perdu sa roue de réaction 2 en juillet 2012, puis sa roue 4 en mai 2013. Le traitement de l'anomalie :

1. **Détection :** couple de frottement élevé dans la télémesure de servitude de la roue 2
2. **Évaluation :** signature de dégradation connue ; surveillance renforcée
3. **Défaillance :** la roue 2 a cessé de fonctionner ; la mission s'est poursuivie sur trois roues
4. **Seconde défaillance :** la roue 4 est tombée en panne dix mois plus tard ; il ne restait que deux roues — insuffisant pour le pointage fin
5. **Reprise :** l'équipe d'ingénierie a élaboré le concept de mission « K2 », qui utilise la pression de radiation solaire comme « troisième roue virtuelle »
6. **Résultat :** K2 a fonctionné plus de quatre années supplémentaires et découvert plus de 2700 exoplanètes candidates

*Enseignement : des solutions de contournement opérationnelles créatives peuvent sauver des missions. La FDIR doit être conçue pour une dégradation progressive, et non selon le principe « mode survie ou rien » — c'est la contrepartie opérationnelle de l'argument de fiabilité « 3 roues sur 4 » du chapitre 15, §15.4.6.*

*[Source : Howell et al., « The K2 Mission : Characterization and Early Results », PASP, 2014]*

---

## 18.6 Retour sur UniSat-1 : modes et FDIR d'un démonstrateur 1U

UniSat-1 dispose d'un contrôle d'attitude magnétique passif, sans roues ni senseur stellaire, d'une balise UHF et d'une charge utile unique — la majeure partie du tableau 18.1 ne s'applique donc pas. Son ensemble de modes se limite à trois états :

| Mode | Description | Puissance | Condition d'entrée |
|------|------------|-------|----------------|
| **Survie (balise)** | OBC et balise uniquement ; charge utile éteinte | Minimale, bilan positif dans toute attitude (chapitre 9, §9.5) | Tout déclenchement FDIR ; c'est aussi l'état après chaque réinitialisation |
| **Nominal** | Charge utile échantillonnant à la cadence scientifique ; données de servitude stockées | Charge nominale du chapitre 9, §9.5 | Commande sol, après confirmation de la santé par la balise |
| **Liaison descendante** | Émetteur UHF à plein débit pendant un passage | Charge en émission | Station en visibilité ; programmée par la liste de passages envoyée depuis le sol |

Il n'y a ni mode amortissement (l'aimant permanent et les barreaux d'hystérésis l'assurent passivement en quelques jours) ni mode prise de vue (le magnétomètre fonctionne en continu en mode nominal). Les règles FDIR se réduisent à quatre : la réinitialisation par chien de garde, le passage en mode survie sur sous-tension de la batterie, la temporisation de 48 heures sans liaison montante, et le nettoyage EDAC sur l'OBC développé sur mesure — les deux dernières étant les mesures de réduction consignées pour le risque R-03 au chapitre 15, §15.5. La procédure de reprise après passage en mode survie tient sur une page et, comme le mode survie a un bilan de puissance positif et un comportement thermique sans danger, le satellite peut y rester plusieurs semaines : UniSat-1 peut se permettre une équipe d'opérations étudiante précisément parce que sa FDIR n'a rien à faire dans l'urgence.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| ConOps | Définit *comment* le système est exploité : modes, transitions, plannings, effectifs ; le concept est au chapitre 4, le détail opérationnel ici |
| Modes opérationnels | EOSat-3U (tableau 18.1) : survie 2 W, nominal 4 W, prise de vue 8 W, liaison descendante 10 W, éclipse 3,5 W ; le bilan du mode survie doit être positif, l'éclipse supportable depuis n'importe quel mode |
| Transitions de mode | Définies par des conditions d'entrée et de sortie ; mode survie accessible depuis chaque mode et quitté uniquement sur commande sol |
| FDIR | Cinq niveaux : matériel → équipement → sous-système → système → sol ; le mode survie est le dernier recours ; « isolation impossible » mène au mode survie, jamais à une supposition |
| Procédures | Nominale, contingence, urgence, maintenance ; chaque étape a un résultat attendu et une action de reprise |
| Traitement des anomalies | Détecter → évaluer → diagnostiquer → planifier → exécuter → vérifier → documenter ; éliminer d'abord l'hypothèse du sol |
| Principes de conception | Le mode survie doit toujours fonctionner ; rester opérationnel avant de se mettre en sécurité ; forçage sol toujours possible ; tout journaliser |

---

## Exercices

1. **Tableau des modes.** Construisez le tableau des modes opérationnels d'un CubeSat 6U doté d'un système de propulsion à gaz froid et d'une liaison descendante en bande X : au moins six modes avec puissance, débit, durée typique et condition d'entrée. Identifiez le mode le plus gourmand en puissance et vérifiez, avec la méthode de dimensionnement de la batterie du chapitre 9, §9.3, si le satellite pourrait survivre à une entrée en éclipse dans ce mode.

2. **Machine à états.** Tracez la machine à états des transitions de mode du satellite de l'exercice 1. Vérifiez les trois propriétés du §18.2.2 — mode survie accessible depuis chaque état, sortie du mode survie uniquement sur commande sol, aucune transition dépendant d'une ressource que la destination n'entretient pas — et identifiez une transition de la figure 18.1 (§18.2.2) qui violerait la troisième propriété si le mode éclipse était implémenté comme un mode à part entière doté de son propre contrôle d'attitude.

3. **Bouclage du bilan de puissance en mode survie.** EOSat-3U passe en mode survie en attitude de culbutage. À partir de la surface du générateur solaire du chapitre 9, §9.2, et en supposant que la surface projetée moyenne sur l'orbite d'un 3U en culbutage vaut 40 % de son maximum, calculez la puissance produite moyenne sur l'orbite en fin de vie et comparez-la à la charge de 2,0 W du mode survie augmentée de la charge en éclipse de 3,5 W pendant 36 minutes par orbite. Le bilan du mode survie est-il positif ? Sinon, quelle charge du mode survie supprimeriez-vous en premier ?

4. **Jeu de règles FDIR.** Rédigez cinq règles FDIR pour la mission UniSat-1 (défaut, méthode de détection, seuil, réponse) au format du §18.3.4, en affectant chacune à un niveau de la hiérarchie du §18.3.2. Pour chaque règle, citez la ligne de l'AMDEC ou l'entrée du registre des risques du chapitre 15 à laquelle elle répond, et indiquez comment le sol peut l'inhiber.

5. **Isolation ou mode survie.** Un satellite 3U emporte deux magnétomètres redondants dont les mesures divergent de 30 %. Concevez la logique d'isolation de niveau 2 qui décide auquel se fier, indiquez de quelle troisième source d'information elle a besoin, et spécifiez la condition dans laquelle elle doit renoncer et passer en mode survie. Reliez votre réponse à la séquence d'Hitomi du chapitre 15, §15.4.7.

6. **Procédure de contingence.** Rédigez une procédure de reprise après passage en mode survie pour EOSat-3U selon la structure en sept parties du §18.4.2, avec au moins huit étapes, chacune avec un résultat attendu et une action de reprise. Les préconditions doivent inclure une étape de diagnostic ; les postconditions doivent laisser le satellite en mode nominal, le défaut étant inhibé ou éliminé.

7. **Rapport d'anomalie.** Le compteur de redémarrages de l'OBC d'EOSat-3U s'incrémente trois fois en dix minutes alors que le satellite survole l'Atlantique Sud, après quoi la FDIR passe en mode survie. Remplissez le rapport d'anomalie du §18.5.3 pour cet événement, attribuez-lui un niveau de gravité du §18.5.1 en le justifiant, et proposez les deux canaux de télémesure qui permettraient le plus rapidement de distinguer un aléa logique (SEU) d'un défaut logiciel.

8. **Compromis d'autonomie.** Estimez le coût des opérations sur trois ans pour la mission 3U dans les options de pilotage par le sol et d'autonomie bord du §18.1.2 (prenez 60 k€ par ETP-année et les profils d'effectifs du chapitre 17, §17.4.1), et estimez le surcoût de logiciel de vol de l'option autonome à l'aide de la ligne logiciel du chapitre 16, §16.2.1. À partir de quelle durée de mission l'autonomie est-elle rentabilisée ?

9. **Mode survie pendant le week-end.** Le satellite passe en mode survie un vendredi soir ; le prochain contact avec du personnel a lieu le lundi matin (≈ 60 heures, ≈ 38 orbites). À l'aide du tableau 18.1 et de la batterie du chapitre 9, §9.3, déterminez si EOSat-3U survit sans intervention, puis refaites l'analyse dans le cas où le mode survie ne parvient pas à délester le réchauffeur de la charge utile (1,5 W supplémentaires). Indiquez ce que la FDIR doit garantir pour qu'une mission sans personnel le week-end soit acceptable.

---

## Références

1. ECSS, *ECSS-E-ST-70-11C : Space Segment Operability*, 2008. https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/
2. ECSS, *ECSS-E-ST-70-32C : Test and Operations Procedure Language*, 2008. https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/
3. ECSS, *ECSS-E-ST-70-01C : Spacecraft On-board Control Procedures*, 2010. https://ecss.nl/standard/ecss-e-st-70-01c-spacecraft-on-board-control-procedures/
4. ECSS, *ECSS-E-ST-70-41C : Telemetry and Telecommand Packet Utilization*, 2016. https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/
5. NASA, *Fault Management Handbook*, NASA-HDBK-1002, 2012. https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002
6. IEEE, *IEEE Std 1362-1998 : Guide for Information Technology — System Definition — Concept of Operations (ConOps) Document*, 1998.
7. ESA PROBA-2 Operations Team, « PROBA-2 : Over a Decade of Operations », *SpaceOps 2020*. https://www.spaceops.org/
8. Howell, S. B. et al., « The K2 Mission : Characterization and Early Results », *Publications of the Astronomical Society of the Pacific*, 126(938), 2014. https://doi.org/10.1086/676406
