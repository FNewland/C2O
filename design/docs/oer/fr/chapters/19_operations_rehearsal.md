# Chapitre 19 — Répéter la mission : simulation des opérations

> **Lectures préalables conseillées.** ECSS-E-ST-70C (*Ground systems and operations*, §5, validation des opérations) ; ECSS-E-ST-70-11C (*Space segment operability*) ; ECSS-E-ST-70-32C (procédures) ; les chapitres consacrés aux opérations de mission du *SMAD*. Ce chapitre suppose que le segment sol du chapitre 17 ainsi que les modes, les règles FDIR et les procédures du chapitre 18 existent sur le papier ; son but est de vérifier qu'ils fonctionnent avant que le satellite ne quitte le sol.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. Expliquer pourquoi les agences spatiales répètent les opérations avant le lancement, et ce qu'une répétition révèle que l'analyse ne peut pas révéler
2. Structurer une répétition des opérations couvrant la LEOP, la recette en orbite, les opérations nominales et l'injection d'anomalies, avec un niveau de fidélité adapté au projet
3. Répartir les rôles d'opérations pour une équipe de toute taille, y compris le contrôleur de simulation
4. Choisir, scénariser et injecter des scénarios d'anomalie tirés d'une bibliothèque réutilisable, chacun avec ses symptômes, son diagnostic attendu et sa reprise
5. Conduire un débriefing structuré et en reporter les constats dans le ConOps, les règles FDIR, les procédures et les exigences

---

## 19.1 Pourquoi les agences répètent

Un satellite est exploité par des personnes qui suivent des procédures au moyen d'un segment sol, et aucun de ces trois éléments n'a volé avant le lancement. L'analyse peut montrer que le bilan de puissance se boucle et que les règles FDIR sont cohérentes ; elle ne peut pas montrer qu'un opérateur en fin de quart de nuit lira la bonne page de télémesure, que la procédure de reprise après passage en mode survie comporte une étape dont le résultat attendu est inobservable, ni que deux rôles croient chacun que c'est l'autre qui décide de commander une réinitialisation. Ces problèmes, on les découvre en répétant.

### 19.1.1 Pratique des agences

- L'**ESA** mène une *campagne de simulations* à l'ESOC pour chaque mission dans les mois qui précèdent le lancement : l'équipe de contrôle du vol pilote un simulateur logiciel du satellite pendant la LEOP et les premières opérations, tandis qu'un officier de simulation injecte sans prévenir des pannes dans le simulateur et dans le segment sol. Les campagnes comptent des dizaines de séances de simulation, et le lancement n'est pas autorisé tant que l'équipe ne s'est pas rétablie des contingences injectées avec les procédures réelles et le système de contrôle réel. L'ECSS-E-ST-70C exige que le segment sol et la préparation des opérations soient validés avant le lancement ; c'est par la campagne de simulations qu'est satisfaite la partie de cette exigence qui concerne les opérations.
- La **NASA** et ses centres mènent des *essais d'aptitude opérationnelle* (ORT, *operational readiness tests*) et des essais d'aptitude de la mission, dans lesquels l'équipe de vol, le réseau sol et le satellite (ou son simulateur) sont éprouvés de bout en bout par rapport à la chronologie du lancement, avec des anomalies scénarisées par un directeur d'essai. Les règles de vol et les jeux de procédures ne sont figés qu'une fois les ORT terminés.
- **Les deux** continuent de répéter après le lancement : avant chaque événement critique — insertion en orbite, atterrissage, sortie du mode survie après une longue interruption —, l'équipe exécute d'abord la séquence sur le simulateur. Le principe directeur est *train like you fly, fly like you train* (s'entraîner comme on vole, voler comme on s'est entraîné) : la répétition utilise les vraies consoles, les vraies procédures et les vraies boucles vocales, de sorte que le jour J, seul le satellite diffère.

### 19.1.2 Ce que révèle une répétition

L'expérience des missions d'agences et des missions universitaires donne une liste constante :

| Constat | Exemple typique | Où il aurait dû être détecté |
|---------|-----------------|------------------------------|
| Lacunes des procédures | Une étape dont le « résultat attendu » est un point de télémesure absent du paquet de servitude | Revue des procédures (chapitre 18, §18.4) |
| Lacunes de la FDIR | Un défaut que les règles détectent, mais dont la réponse laisse le satellite dans un mode sans chemin vers le mode survie | Vérification de la machine à états (chapitre 18, §18.2.2) |
| Ambiguïté des rôles | Deux personnes attendent chacune que l'autre autorise une commande ; ou les deux l'envoient | Plan d'effectifs du ConOps (chapitre 18, §18.1.1) |
| Optimisme de la chronologie | Le plan LEOP prévoit trois activités sur un passage de cinq minutes | Chronologie des opérations (chapitre 17, §17.4) |
| Défauts du segment sol | Mauvais signe du Doppler dans le logiciel de poursuite ; passage prédit à partir d'éléments orbitaux périmés | Validation du segment sol |
| Faiblesses de conception | Le bilan de puissance du mode survie n'est pas positif dans l'attitude de culbutage imposée par la répétition | Bilan de puissance (chapitre 9) |

La dernière ligne est la plus importante pour un manuel de conception : la répétition est une *activité de vérification de la conception*, tardive en phase D, et ses constats se traduisent par des modifications d'exigences. Les opérations révèlent ce que l'analyse ne peut pas révéler.

### 19.1.3 Niveaux de fidélité

Une répétition n'a pas besoin d'un simulateur du logiciel de vol pour être utile. Quatre niveaux, par coût croissant :

| Niveau | Représentation du satellite | Source de télémesure | Adapté à |
|-------|---------------------------|------------------|-----------|
| **Sur table** | Aucune ; le contrôleur de simulation raconte l'état et lit les valeurs de télémesure | Tableaux préparés | Début de phase C ; ConOps au niveau du concept ; toute équipe |
| **Modèle tableur** | Puissance, données et état des modes suivis dans un tableur que le contrôleur met à jour à chaque orbite | Tableur | Phases C/D ; vérification des bilans en conditions d'opérations |
| **Simulateur logiciel** | Modèle du logiciel de vol doté d'une interface télémesure/télécommande avec le système de contrôle réel | Simulateur | Phase D ; validation des procédures ; norme des agences |
| **Matériel dans la boucle** | Modèle d'ingénierie sur banc, alimenté par des capteurs simulés | Représentative du vol | Phase D ; validation de bout en bout ; procédures critiques pour la mission |

Ce chapitre est rédigé de façon à pouvoir être mis en œuvre aux deux premiers niveaux par n'importe quelle équipe, et étendu aux deux niveaux supérieurs lorsque le projet en dispose. Tout le contenu des §19.3–§19.6 est indépendant du niveau de fidélité.

---

## 19.2 Structurer une répétition

### 19.2.1 Les éléments

Toute répétition des opérations, de l'exercice sur table de deux heures à la campagne d'agence de trois mois, comporte les cinq mêmes éléments :

1. **Un satellite simulé** — à l'un des niveaux de fidélité du §19.1.3 —, dont l'état évolue selon le tableau des modes, le bilan de puissance et le bilan de données de la mission elle-même.
2. **Un contrôleur de simulation** (« l'Univers »), qui détient le scénario, fait avancer le temps simulé, lit la télémesure, décide de ce que fait le satellite en réponse à chaque commande et injecte les anomalies. Le contrôleur ne fait pas partie de l'équipe des opérations et ne l'aide pas.
3. **Un temps compressé.** Le temps simulé saute d'un événement à l'autre ; une LEOP de 72 heures se répète en une ou deux heures en ne jouant que les passages et les décisions. Le contrôleur annonce chaque saut (« il est maintenant T+24 h ; huit passages ont eu lieu avec des données de servitude nominales »).
4. **Un scénario** — la séquence des événements, la télémesure que le contrôleur lira à chacun d'eux et les réponses attendues (§19.4).
5. **Un journal**, tenu en temps réel par un rôle désigné, de chaque événement, lecture de télémesure, commande et décision, avec horodatage simulé et réel. Le journal est la donnée d'entrée du débriefing, et la tenue du journal en temps réel est elle-même une compétence qui se répète : sous pression, la mémoire n'est pas fiable.

### 19.2.2 Phases

Une répétition complète parcourt dans l'ordre la chronologie des opérations du chapitre 17, §17.4.1, car chaque phase suppose que la précédente a réussi :

| Temps simulé | Phase | Ce qui est répété |
|----------|-------|--------|
| T+0 à T+1 h | LEOP | Séparation, minuterie d'inhibition RF, déploiement de l'antenne, acquisition de la balise, premières données de servitude, première liaison montante |
| T+1 h à T+24 h | Début de LEOP | Déploiement du générateur solaire, initialisation du SCAO, validation de la chaîne de communication |
| T+1 à T+7 jours | Recette en orbite | Vérification des sous-systèmes, étalonnage du SCAO, première lumière de la charge utile, premier téléchargement de données |
| T+7 à T+30 jours | Premières opérations | Science ou service nominal, affinement des procédures |
| *(toute phase)* | Injection d'anomalies | Deux ou trois scénarios tirés de la bibliothèque du §19.5, choisis pour la mission |
| T+30 jours à T+1 an | Opérations nominales | Revue des indicateurs par rapport au plan |
| — | Débriefing | §19.6 |

Une répétition plus courte n'en retient qu'une partie : la LEOP seule (la phase la plus contrainte en temps, et celle que l'équipe ne vivra qu'une fois) ; ou les opérations nominales avec injection d'anomalies (la phase que l'équipe vivra pendant des années). Les injections d'anomalies sont placées dans la phase où elles sont les plus difficiles — une sous-tension de la batterie ne pose pas le même problème pendant la recette en orbite, alors que l'équipe n'a pas encore vu d'éclipse normale, qu'au sixième mois.

### 19.2.3 Rythme

La LEOP doit être vécue sous pression temporelle : les passages sont courts, et les décisions doivent être prises avant la perte du signal, faute de quoi il faut attendre quatre-vingt-dix minutes. La recette en orbite peut être plus lente. L'injection d'anomalies doit être exigeante mais soluble avec les propres procédures de l'équipe — le but est d'éprouver les procédures, pas de mettre l'équipe en échec. Il faut accorder au débriefing plus de temps qu'il ne semble nécessaire : c'est là que les constats se transforment en modifications.

---

## 19.3 Répartition des rôles pour toute taille d'équipe

### 19.3.1 Rôles d'opérations

Les rôles reproduisent ceux d'une véritable équipe de contrôle du vol, à échelle réduite. Chacun dispose d'une autorité définie et d'un ensemble défini de télémesures qu'il surveille.

| Rôle | Responsabilité | Autorité | Surveille |
|------|---------------|-----------|---------|
| **Directeur de vol (FD)** | Autorité de décision globale ; coordonne l'équipe ; déclare la gravité des anomalies (chapitre 18, §18.5.1) | GO/NO GO sur toute commande non routinière | La situation d'ensemble ; l'horloge |
| **Contrôleur satellite (SC)** | Envoie les commandes ; surveille la télémesure de servitude ; exécute les procédures étape par étape | Commandes de routine dans le cadre d'une procédure approuvée | Servitude de la plateforme ; mode ; indicateurs FDIR |
| **Opérateur station sol (GSO)** | Programmation de l'antenne ; acquisition de la liaison ; qualité du signal | Configuration du segment sol | Porteuse, Doppler, niveau du signal, verrouillage trame |
| **Opérateur charge utile (PO)** | Planifie et exécute les observations ; suit le bilan de données | Commandes charge utile dans le cadre d'une procédure approuvée | Servitude de la charge utile ; remplissage de la mémoire de masse |
| **Dynamique du vol (FDyn)** | Connaissance de l'orbite ; prévisions de passages ; planification des manœuvres s'il y a une propulsion ; alertes de conjonction | Mises à jour des éléments orbitaux | Orbite, heures d'éclipse, géométrie des passages |
| **Responsable du journal** | Consigne chaque événement, lecture, commande et décision avec horodatage ; tient à jour le rapport d'anomalie (chapitre 18, §18.5.3) | Aucune — délibérément | Tout |
| **Contrôleur de simulation** | Déroule le scénario ; fait avancer le temps ; injecte les anomalies ; joue le satellite et le monde extérieur | Absolue, sur l'univers simulé | L'équipe |

### 19.3.2 Adapter l'équipe à l'effectif

Pour les petites équipes, combinez des rôles ; SC+GSO et PO+FDyn sont des associations naturelles, car chaque paire surveille des télémesures apparentées. Le directeur de vol et le contrôleur de simulation ne doivent jamais être la même personne, et le responsable du journal ne devrait pas être aussi le directeur de vol.

| Personnes disponibles | Répartition |
|------------------|-----------|
| 2 | Contrôleur de simulation ; un opérateur qui est à la fois FD, SC, GSO, PO et responsable du journal (utile pour dérouler seul une procédure, pas pour une répétition d'équipe) |
| 3 | Contrôleur de simulation ; FD + responsable du journal ; SC + GSO + PO + FDyn |
| 4 | Contrôleur de simulation ; FD ; SC + GSO ; PO + FDyn + responsable du journal |
| 5 | Contrôleur de simulation ; FD ; SC + GSO ; PO + FDyn ; responsable du journal |
| 6–7 | Contrôleur de simulation ; FD ; SC ; GSO ; PO + FDyn ; responsable du journal (+ un second contrôleur pour jouer la station sol) |
| 8+ | Les sept rôles, plus un second quart — ce qui permet l'injection la plus instructive de toutes : une passation de consignes au milieu d'une anomalie |

### 19.3.3 Discipline de communication

Trois règles empruntées aux vraies salles de contrôle, que la répétition mettra chacune à l'épreuve :

- **Toute commande est annoncée avant d'être envoyée** (« SC to FD : request GO for payload power ON, step 2 of NOM-SCI-001 ») et acquittée (« FD : GO »).
- **Toute lecture de télémesure est énoncée avec sa plage attendue** (« bus voltage 7.8, expected 7.0 to 8.4, nominal »), afin que le responsable du journal et le directeur de vol entendent la comparaison, et pas seulement le chiffre.
- **Personne n'agit hors procédure sans l'accord du directeur de vol.** Improviser est parfois la bonne décision ; improviser en silence ne l'est jamais.

---

## 19.4 Scénariser les phases

Les scénarios ci-dessous sont écrits pour le CubeSat 3U d'observation de la Terre EOSat-3U, avec les modes du tableau 18.1 du chapitre 18 ; le contrôleur de simulation adapte les valeurs de télémesure à la mission répétée. Chaque entrée donne la narration du contrôleur, ce que l'équipe est censée faire et ce à quoi ressemble une bonne réponse.

### 19.4.1 LEOP

**[T+0 — Séparation]** *« Le satellite s'est séparé du déployeur. Les interrupteurs de déploiement sont libérés. La minuterie de 30 minutes a démarré. Vous êtes en silence radio — aucune émission RF n'est autorisée avant l'expiration de la minuterie. Que fait le satellite en ce moment ? »*

Attendu : la minuterie décompte ; la batterie alimente l'OBC et rien d'autre ; le satellite culbute à la vitesse de séparation ; aucun déploiement n'a eu lieu. Une bonne équipe indique aussi ce qu'elle *ne peut pas* savoir — l'attitude, l'état de la batterie — et à quel moment elle le saura pour la première fois.

**[T+30 min — Expiration de la minuterie]** *« La minuterie a expiré. L'OBC a commandé le déploiement de l'antenne. Qu'attendez-vous de voir, et d'où ? »*

Attendu : la commande de déploiement de l'antenne a été émise par la séquence bord ; la balise devrait commencer à émettre ; rien ne peut être confirmé tant qu'aucune station n'est en visibilité. L'équipe devrait déjà savoir quand a lieu le premier passage (dynamique du vol) et s'il tombe avant ou après T+30 min (chapitre 17, §17.4.3).

**[T+35 min — Premier passage]** *« Votre station sol est en visibilité directe. L'opérateur d'antenne signale : porteuse détectée à la fréquence attendue, avec un décalage Doppler cohérent avec un satellite qui se rapproche. Le niveau du signal est de −110 dBm. Est-ce ce que vous attendiez ? »*

L'équipe doit vérifier que la fréquence de la porteuse correspond à la prévision (compte tenu du Doppler), que le niveau du signal est cohérent avec le bilan de liaison à la distance oblique du moment (chapitre 11, §11.8.1) et que le débit de la balise est conforme à la conception. Une équipe qui se contente de répondre « oui » n'a rien vérifié.

**[T+40 min — Première télémesure]** *« Verrouillage sur la balise obtenu. Vous recevez les données de servitude. Voici la première trame : »*

| Paramètre | Valeur | Plage attendue | État |
|-----------|-------|---------------|--------|
| Tension du bus | 7.8 V | 7.0–8.4 V | Nominal |
| État de charge de la batterie | 72 % | > 50 % | Nominal |
| Courant du générateur solaire | 0.45 A | 0.3–0.6 A | Nominal |
| Température de l'OBC | 22 °C | −10 à +50 °C | Nominal |
| Température de la batterie | 19 °C | 0 à 45 °C | Nominal |
| Mode du SCAO | Detumble | Attendu | Nominal |
| Vitesse angulaire | 3.2 °/s | En diminution | Nominal |
| État de l'antenne | Déployée | Attendu | Nominal |
| Mode balise | Actif | Attendu | Nominal |
| État de la liaison montante | Pas encore tentée | — | — |

Attendu : le contrôleur satellite lit à voix haute chaque valeur par rapport à sa plage ; le directeur de vol déclare terminée l'étape LEOP « première télémesure » ; le responsable du journal consigne la trame. Un contrôleur de simulation qui veut corser l'exercice modifie une valeur — une température de batterie de −2 °C, par exemple — et observe si quelqu'un le remarque.

**[T+1 h — Validation de la liaison montante]** *« Envoyez une commande sans effet (no-operation) pour vérifier la chaîne de liaison montante. »*

Attendu : le contrôleur satellite compose la commande, vérifie son codage, l'annonce au directeur de vol, l'émet et attend que le compteur d'acquittement s'incrémente dans la trame de télémesure suivante. La liaison montante n'est pas validée tant que ce compteur n'a pas été observé.

### 19.4.2 Recette en orbite

**[Saut temporel : T+24 h]** *« L'amortissement des vitesses angulaires est terminé. Le SCAO est en mode de pointage solaire. Tous les paramètres de servitude ont été nominaux sur huit passages. Vous êtes prêts à commencer la recette en orbite. Quelle est votre première activité ? »*

Attendu : l'étalonnage du SCAO — estimation du biais du magnétomètre, vérification de l'alignement des senseurs solaires — avant toute activité qui dépend de l'attitude. Une équipe qui passe directement à la charge utile a sauté l'étape sur laquelle reposera le pointage de la charge utile.

**[T+3 jours — Première lumière de la charge utile]** *« Le SCAO est étalonné et atteint un pointage de 0,3°. Vous êtes prêts pour la première lumière de la charge utile. Déroulez-moi votre procédure. »*

L'équipe exécute sa procédure d'observation scientifique (chapitre 18, §18.4.3) étape par étape, en annonçant chaque résultat attendu. Le contrôleur joue le satellite : à chaque étape, le résultat attendu est signalé ou ne l'est pas, et l'équipe doit appliquer l'action de reprise que spécifie la procédure. Une procédure dépourvue d'action de reprise pour une étape constitue un constat.

**[T+5 jours — Premier téléchargement de données]** *« La charge utile a acquis 150 Mo d'images. Votre prochain passage dure 8 minutes au-dessus du masque. Pouvez-vous tout télécharger en un seul passage ? »*

Calcul attendu (chapitre 17, §17.2.2) : à 2 Mbit/s, sur 8 min et avec $\eta = 0.9$, la capacité vaut $2 \times 10^6 \times 480 \times 0.9 / 8 = 108$ Mo — donc non ; deux passages sont nécessaires, et l'opérateur charge utile planifie la séquence et indique quelles données passent en premier. Une équipe qui répond sans calculer n'a pas compris pourquoi le bilan de données existe.

### 19.4.3 Opérations nominales

**[Saut temporel : T+30 jours à T+1 an]** *« La mission est opérationnelle depuis un mois. La recette en orbite est terminée. Passez en revue vos indicateurs opérationnels. »*

L'équipe présente :
- le volume total de données transmises au sol en 30 jours par rapport au plan ;
- le nombre d'observations réalisées par rapport au plan ;
- les anomalies rencontrées (lors de l'exercice d'injection) et leur statut ;
- l'état actuel des bilans : marge de puissance, marge de données, ergols restants le cas échéant ;
- l'état de l'orbite : alertes de conjonction, suivi de la conformité en matière de débris (chapitre 3, §3.6).

C'est le moment où la répétition vérifie si la mission, exploitée comme le décrit le ConOps, fournit réellement ce que promettaient les exigences. Un retour de données de 60 % du plan est un résultat courant et instructif.

---

## 19.5 Une bibliothèque de scénarios d'anomalie

Chaque scénario ci-dessous est rédigé tel que le contrôleur de simulation l'injecte, suivi des symptômes que l'équipe peut observer, du diagnostic auquel une équipe bien préparée devrait aboutir, de la reprise qu'elle devrait exécuter, et de la règle FDIR ou de la caractéristique de conception que le scénario met à l'épreuve. Choisissez-en deux ou trois par répétition, adaptés à la mission — n'injectez pas d'anomalie de propulsion dans une mission sans propulsion —, et gardez-en un en réserve pour une équipe qui résout rapidement le premier.

### 19.5.1 Sous-tension de la batterie

**Injection.** *« Pendant l'éclipse, vous recevez une alerte : la tension de la batterie est tombée à 6,2 V, sous le seuil d'avertissement de 6,5 V. La température de la batterie est de 5 °C. L'état de charge est estimé à 18 %. »*

**Symptômes.** Tension sous le seuil d'avertissement, état de charge très inférieur à la valeur de fin d'éclipse que prévoit le bilan de puissance ; température de batterie basse qui réduit la capacité disponible ; éventuellement un changement de mode déjà exécuté par la FDIR.

**Diagnostic attendu.** La consommation a dépassé la production sur plusieurs orbites. Causes possibles : dégradation du générateur solaire ou défaillance d'une chaîne de cellules ; charge inattendue (réchauffeur bloqué en marche, charge utile restée alimentée) ; dégradation de la batterie ; attitude qui éclaire insuffisamment le générateur solaire ; éclipse plus longue que prévu (saison d'angle β, chapitre 7, §7.1.2). La télémesure discriminante est la tendance du courant du générateur solaire sur les dernières 24 heures, rapprochée de l'historique d'attitude.

**Reprise.** Vérifier que la FDIR a délesté les charges (charge utile éteinte, réchauffeurs non essentiels éteints) ; sinon, commander manuellement le mode survie. Examiner ensuite la tendance de puissance et la comparer au bilan ; ne pas quitter le mode survie tant que la production ne dépasse pas la consommation avec marge et que la cause n'est pas connue.

**Ce qui est éprouvé.** La règle de sous-tension du chapitre 18, §18.3.4 ; le caractère positif du bilan de puissance en mode survie (chapitre 9, §9.2) ; la capacité de l'équipe à lire une tendance, et pas seulement une valeur.

### 19.5.2 Perte de communication

**Injection.** *« Vous n'avez reçu aucune télémesure lors des trois derniers passages programmés (18 heures). La station sol signale un pointage et une fréquence corrects, mais aucune porteuse détectée. »*

**Symptômes.** Le silence. Rien d'autre — et c'est bien là le problème.

**Diagnostic attendu.** Éliminer d'abord l'hypothèse du sol : antenne, LNA, modem, éléments orbitaux, signe du Doppler. Rechercher ensuite des éléments indépendants — demander à un réseau bénévole ou à une autre station si quelqu'un a reçu la balise. Envisager enfin le satellite : panne de l'émetteur, antenne non déployée, perte d'attitude (antenne pointée dans la mauvaise direction), défaut d'alimentation ayant coupé l'émetteur, blocage de l'OBC. Si la mission dispose d'une temporisation sans liaison montante (48 h au chapitre 18, §18.3.4), le satellite réinitialisera de lui-même son TT&C et reviendra en mode balise.

**Reprise.** Réparer ou mettre hors de cause le sol ; configurer une antenne à large faisceau pour rechercher la balise ; attendre la réinitialisation sur temporisation ; planifier la liaison montante qui la suivra. Le directeur de vol doit décider combien de temps attendre avant de passer au niveau rouge (chapitre 18, §18.5.1).

**Ce qui est éprouvé.** La règle FDIR de perte de communication ; l'arbre de défaillances du segment sol ; la discipline de l'équipe, qui ne commande pas en aveugle.

### 19.5.3 Perte du pointage fin

**Injection.** *« L'erreur de pointage est passée de 0,1° à 5°. Le senseur stellaire signale « no solution ». Les roues de réaction sont à 80 % de leur capacité. »*

**Symptômes.** Pointage dégradé ; source de détermination d'attitude perdue ; moment cinétique proche de la saturation.

**Diagnostic attendu.** Panne du senseur stellaire, contamination optique, Soleil ou Terre dans son champ de vue, ou roue proche de la saturation ayant écarté l'attitude du domaine d'acquisition du senseur. Vérifier l'attitude grossière donnée par le magnétomètre et les senseurs solaires — est-elle cohérente avec la dernière solution valide du senseur stellaire ? Vérifier l'historique des vitesses de roue — le moment cinétique s'accumulait-il avant que le senseur ne décroche ?

**Reprise.** Commander d'abord la désaturation par les magnétocoupleurs (chapitre 10, §10.5) ; passer ensuite en pointage grossier (senseurs solaires + magnétomètre) ; tenter enfin la réacquisition par le senseur stellaire. Évaluer l'impact : la prise de vue peut-elle se poursuivre en pointage grossier, et à quel coût pour la qualité d'image (chapitre 10, §10.4) ?

**Ce qui est éprouvé.** La règle de survitesse des roues ; le repli au niveau sous-système (niveau 2) du chapitre 18, §18.3.2 ; la dégradation progressive opposée au mode survie.

### 19.5.4 Passage inattendu en mode survie

**Injection.** *« Le satellite est passé de lui-même en mode survie. La dernière télémesure avant ce passage montrait le compteur de redémarrages de l'OBC s'incrémenter trois fois en dix minutes. Tous les autres paramètres étaient nominaux. »*

**Symptômes.** Mode survie sans cause matérielle évidente ; une rafale de redémarrages.

**Diagnostic attendu.** Des redémarrages répétés évoquent un aléa logique (SEU) ou un défaut du micrologiciel. Le satellite se trouvait-il dans l'anomalie de l'Atlantique Sud (chapitre 7, §7.6) ? Lire le journal FDIR en mémoire non volatile pour connaître les déclencheurs du défaut. Le rapprocher de la position orbitale et de toute commande envoyée juste avant.

**Reprise.** Ne commander la sortie du mode survie qu'une fois le journal lu et la cause attribuée ; surveiller une éventuelle récurrence sur plusieurs passages dans la SAA ; en cas de récurrence, envoyer un correctif logiciel (ou modifier la fréquence de nettoyage EDAC) pour améliorer la robustesse aux aléas.

**Ce qui est éprouvé.** Les règles du chien de garde et de corruption mémoire ; la précondition « pas de reprise sans diagnostic » du chapitre 18, §18.4.3 ; la conception vis-à-vis des radiations du chapitre 7, §7.6, et le risque R-03 du chapitre 15, §15.5.

### 19.5.5 Dépassement thermique

**Injection.** *« La température de la charge utile a atteint 58 °C pendant une observation, au-dessus de la limite opérationnelle de 55 °C. La température de la batterie est de 38 °C et approche de la limite de 45 °C. »*

**Symptômes.** Charge utile au-delà de sa limite opérationnelle ; batterie qui se réchauffe vers sa limite ; les deux pendant une observation en phase éclairée.

**Diagnostic attendu.** Le cas chaud a été dépassé. La face radiateur est-elle tournée vers le Soleil dans l'attitude de prise de vue ? L'orbite est-elle dans une saison à β élevé que le modèle thermique (chapitre 9, §9.4) ne couvrait pas ? Le rapport cyclique de prise de vue a-t-il dérivé au-delà de la valeur supposée par le cas thermique ?

**Reprise.** Désactiver immédiatement la charge utile ; vérifier l'attitude et la modifier si nécessaire ; confronter le modèle thermique à la géométrie orbitale réelle ; réduire le rapport cyclique et programmer les observations pendant des phases plus froides de l'orbite ; si le modèle est faux, le mettre à jour, et avec lui les contraintes opérationnelles.

**Ce qui est éprouvé.** La règle de surchauffe de la batterie ; la prise en compte des contraintes thermiques comme limites opérationnelles dans le ConOps ; le retour des opérations vers la conception thermique.

### 19.5.6 Panne sol se faisant passer pour une panne du satellite

**Injection.** *« Pendant le passage, vous recevez la porteuse et des trames, mais chaque trame échoue au contrôle de somme. Le niveau du signal est inférieur de 6 dB à celui du passage précédent. »*

**Symptômes.** Liaison présente mais inutilisable ; signal affaibli.

**Diagnostic attendu.** Une perte de 6 dB alors que le verrouillage est encore obtenu désigne le sol — antenne mal pointée, mauvaise polarisation, défaut d'un câble ou du LNA, pluie — avant le satellite. Une panne de l'émetteur du satellite se traduirait plus souvent par une absence totale de porteuse. Comparer avec une autre station si l'on en dispose.

**Reprise.** Vérifications du segment sol entre les passages ; seconde station si possible ; si la perte persiste d'une station à l'autre, réexaminer l'antenne et l'attitude du satellite.

**Ce qui est éprouvé.** La discipline consistant à éliminer d'abord l'hypothèse du sol ; le rôle de l'opérateur station sol ; la marge de liaison du chapitre 11, §11.8.1 (6 dB sont-ils dans la marge ou non ?).

### 19.5.7 Mémoire de masse pleine

**Injection.** *« L'opérateur charge utile signale que la mémoire de masse est remplie à 97 % et que les trois prochains passages se font au-dessus de la station à basse élévation. »*

**Symptômes.** Stockage presque épuisé ; capacité de liaison descendante du jour suivant inférieure à la production.

**Diagnostic attendu.** Le bilan de données (chapitre 11, §11.9 ; chapitre 17, §17.2.4) ne se boucle pas avec le rapport cyclique et le planning des stations actuels — peut-être parce qu'une indisponibilité de station, un passage manqué ou une cadence de prise de vue supérieure au plan a consommé la marge.

**Reprise.** Établir des priorités : quelles données descendre en premier, lesquelles peuvent être écrasées ? Réduire le rapport cyclique de prise de vue jusqu'à résorption du retard ; acheter ou emprunter des passages si la mission le peut ; confronter le dimensionnement du stockage bord du chapitre 12, §12.3.3, à l'hypothèse d'indisponibilité sur laquelle il repose.

**Ce qui est éprouvé.** La gestion du bilan de données en opérations ; le jugement de l'opérateur charge utile ; le cas d'indisponibilité dans le dimensionnement du stockage.

### 19.5.8 Commande rejetée

**Injection.** *« La commande de sortie du mode survie a été envoyée trois fois. La télémesure montre que le compteur de commandes s'incrémente mais que le mode reste inchangé, et un indicateur « command rejected » est positionné. »*

**Symptômes.** La liaison montante fonctionne ; le satellite refuse la commande.

**Diagnostic attendu.** Une précondition bord n'est pas satisfaite — verrouillage sur l'état de charge de la batterie, indicateur de connaissance d'attitude, inhibition FDIR encore active —, ou la commande est envoyée avec un paramètre erroné ou dans un mauvais mode. Lire le motif du rejet si la télémesure le fournit ; si elle ne le fournit pas, c'est un constat.

**Reprise.** Satisfaire la précondition (attendre la charge ; lever l'inhibition par sa propre commande) plutôt que la forcer ; ne forcer que sur autorisation du directeur de vol, en consignant le motif.

**Ce qui est éprouvé.** Les préconditions des procédures ; le principe de forçage depuis le sol du chapitre 18, §18.3.5, et ses limites ; la capacité de la télémesure à dire à l'opérateur *pourquoi*.

### 19.5.9 Passation de consignes pendant une anomalie

**Injection** (équipes disposant d'un second quart). *« C'est la fin du quart. La sous-tension de la batterie du §19.5.1 est toujours en cours d'investigation. Passez les consignes. »*

**Symptômes.** Aucun côté satellite ; le danger se trouve dans l'équipe.

**Réponse attendue.** Une passation de consignes structurée : mode actuel, anomalies ouvertes et leur gravité, actions en cours et leurs responsables, heure du prochain passage et ce qui y est prévu, décisions en attente pour le directeur de vol. Le quart entrant la collationne.

**Ce qui est éprouvé.** Le plan d'effectifs du chapitre 18, §18.1.1 ; le journal comme document de passation ; l'existence d'informations connues seulement dans la tête de quelqu'un.

### 19.5.10 Consigner la réponse

Pour chaque scénario injecté, le responsable du journal remplit la fiche de réponse, qui est la forme la plus courte du rapport du chapitre 18, §18.5.3 :

| Champ | Ce qu'il faut consigner |
|-------|---------------|
| Heure (simulée) | Moment de la détection de l'anomalie |
| Observation | Valeurs exactes de télémesure et symptômes |
| Évaluation initiale | Niveau de gravité (vert / jaune / orange / rouge) et qui l'a déclaré |
| Diagnostic | Cause profonde soupçonnée et télémesure qui l'étaye |
| Mesure prise | Commandes envoyées, procédures exécutées, par qui, autorisées par qui |
| Résultat | État du système après la réponse |
| Suite à donner | Investigation complémentaire ; mises à jour des procédures, de la FDIR ou des exigences |

---

## 19.6 Le débriefing

C'est au débriefing que la répétition se rentabilise. Il est conduit par une personne autre que le directeur de vol, s'appuie sur le journal et les fiches de réponse plutôt que sur la mémoire, et s'organise autour de trois questions.

### 19.6.1 Trois questions

1. **Qu'est-ce qui a bien fonctionné ?** Quelles procédures ont fonctionné telles qu'écrites ? Quelles règles FDIR se sont déclenchées correctement ? Où l'équipe a-t-elle communiqué efficacement ?
2. **Qu'est-ce qui pourrait être amélioré ?** Quelles procédures ont dû être modifiées en temps réel ? La conception FDIR présentait-elle des lacunes ? Où la prise de décision a-t-elle ralenti, et pourquoi — information manquante, autorité floue ou résultat attendu inobservable ?
3. **Enseignements pour la conception.** La répétition a-t-elle révélé une faiblesse de conception ? Une exigence doit-elle changer au vu de l'expérience opérationnelle ? Quelle autonomie supplémentaire aurait aidé, et que coûterait-elle ?

### 19.6.2 Observations à consigner

Un débriefing utile recherche des comportements précis plutôt que des impressions générales :

- L'équipe a-t-elle suivi ses procédures ou improvisé — et, lorsqu'elle a improvisé, avait-elle raison, et l'a-t-elle annoncé ?
- Le directeur de vol a-t-il coordonné, ou a-t-il opéré lui-même ? (Un directeur de vol qui lit la télémesure ne dirige pas.)
- Le traitement des anomalies a-t-il été méthodique — détecter, évaluer, diagnostiquer, planifier, exécuter, vérifier, documenter — ou est-il passé directement du symptôme à la commande ?
- Le journal était-il assez complet pour reconstituer l'anomalie après coup ?
- Quelqu'un a-t-il identifié un défaut de conception pendant les opérations, et a-t-il été consigné ?

### 19.6.3 Boucler la boucle

Chaque constat devient l'un de quatre types de modification, chacune avec un responsable et une échéance :

| Constat | Devient | Destinataire |
|---------|---------|---------|
| Lacune ou erreur de procédure | Révision de la procédure | Opérations (chapitre 18, §18.4) |
| Lacune FDIR ou seuil erroné | Modification d'une règle FDIR | Logiciel de vol et AMDEC (chapitre 15 ; chapitre 18, §18.3) |
| Ambiguïté de rôle ou d'autorité | Révision du plan d'effectifs du ConOps | ConOps (chapitre 18, §18.1) |
| Faiblesse de conception | Modification d'exigence ou dérogation | Exigences et registre des risques (chapitres 5, 15) ; prochain jalon de revue (chapitre 16) |

Une répétition dont les constats ne sont pas suivis jusqu'à leur clôture a répété la mauvaise chose.

---

## 19.7 Retour sur UniSat-1 : une répétition pour une équipe de trois personnes

L'équipe d'opérations d'UniSat-1 compte trois étudiants, que le §19.3.2 répartit ainsi : contrôleur de simulation ; directeur de vol + responsable du journal ; et un opérateur couvrant le satellite, la station sol, la charge utile et la dynamique du vol. La répétition se fait sur table (§19.1.3), car le satellite a trois modes (chapitre 18, §18.6) et son état tient sur une page.

Le scénario du §19.4 se raccourcit en conséquence : il n'y a ni déploiement de générateur solaire ni étalonnage du SCAO, si bien que la recette en orbite est terminée dès que le magnétomètre renvoie des valeurs de champ plausibles, le deuxième jour ; le calcul du premier téléchargement de données utilise les passages UHF de 5 minutes et les 153 ko par passage du chapitre 11, §11.8.2, ce qui fait du déficit du bilan de données (risque R-02 du chapitre 15, §15.5) le sujet naturel de la revue des indicateurs des opérations nominales. Dans la bibliothèque de scénarios, les §19.5.1, §19.5.2, §19.5.4 et §19.5.6 s'appliquent directement ; le §19.5.3 ne s'applique pas (ni roues ni senseur stellaire) ; et le §19.5.8 mérite d'être injecté, car les verrouillages de l'OBC développé sur mesure sont la partie la moins testée du logiciel de vol. La question de débriefing qui compte le plus pour une mission exploitée par des étudiants est la première du §19.6.2 : avec un seul opérateur tenant quatre rôles, les procédures doivent être assez bonnes pour être suivies à la lettre, car personne n'est là pour rattraper une improvisation.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Pourquoi répéter | Procédures, FDIR, rôles et segment sol n'ont jamais volé ; la répétition révèle ce que l'analyse ne peut pas révéler ; les campagnes de simulations de l'ESA et les essais d'aptitude de la NASA sont les modèles |
| Fidélité | Sur table → tableur → simulateur logiciel → matériel dans la boucle ; la structure est la même à chaque niveau |
| Éléments | Satellite simulé, contrôleur de simulation, temps compressé, scénario, journal en temps réel |
| Phases | LEOP (contrainte en temps, vécue une seule fois) → recette en orbite → premières opérations et opérations nominales, avec injection d'anomalies là où elle est la plus difficile |
| Rôles | FD, SC, GSO, PO, FDyn, responsable du journal, contrôleur de simulation ; combiner SC+GSO et PO+FDyn dans les petites équipes ; FD et contrôleur jamais la même personne |
| Bibliothèque d'anomalies | Neuf scénarios, chacun avec symptômes → diagnostic → reprise → ce qu'il éprouve ; choisir selon la mission, en garder un en réserve |
| Réponse | Détecter, évaluer, diagnostiquer, planifier, exécuter, vérifier, documenter ; éliminer d'abord l'hypothèse du sol ; ne jamais commander en aveugle |
| Débriefing | Ce qui a bien fonctionné, ce qui est à améliorer, enseignements pour la conception ; chaque constat devient une modification suivie de procédure, de FDIR, de ConOps ou d'exigence |

---

## Exercices

1. **Concevoir une répétition de la LEOP.** Pour un CubeSat 3U d'observation de la Terre déployé sur une orbite héliosynchrone à 500 km avec une station en bande S à 45° N, rédigez le scénario du contrôleur de simulation pour les 24 premières heures : chaque passage (utilisez le chapitre 17, §17.2.3, pour leur nombre et leur durée), la télémesure lue à chacun, l'activité du chapitre 17, §17.4.3, tentée à chacun, et la décision que l'équipe doit prendre avant la perte du signal. Repérez le passage où vous injecteriez une valeur de télémesure modifiée, et précisez laquelle.

2. **Adapter l'équipe.** Répartissez les rôles du §19.3.1 pour des équipes de 3, 5 et 8 personnes pour la mission de l'exercice 1 et, pour chaque répartition, identifiez la défaillance de communication la plus probable (qui attend qui) et la règle du §19.3.3 qui la prévient.

3. **Rédiger un scénario.** Ajoutez un dixième scénario à la bibliothèque du §19.5 pour une mission à propulsion à gaz froid — un propulseur qui ne fournit pas le ΔV commandé pendant une manœuvre d'évitement de collision —, au même format : injection, symptômes, diagnostic attendu, reprise et ce qui est éprouvé. Citez la fonction de dynamique du vol du chapitre 17, §17.1.4, et le niveau FDIR du chapitre 18, §18.3.2, qu'il met à l'épreuve.

4. **Modèle de fidélité tableur.** Spécifiez le modèle tableur minimal qui permet à un contrôleur de simulation de jouer de façon crédible le satellite EOSat-3U au travers des §19.5.1 et §19.5.7 : les variables d'état (mode, état de charge de la batterie, remplissage de la mémoire de masse, moment cinétique des roues), les règles de mise à jour à chaque orbite tirées du tableau 18.1 du chapitre 18 et du chapitre 9, et les valeurs de télémesure qui en découlent. Indiquez quelles injections d'anomalie se réduisent à de simples modifications de paramètres dans ce modèle.

5. **Fiche de réponse à une anomalie.** Déroulez sur papier le §19.5.4 pour la conception d'UniSat-1 (chapitre 18, §18.6), en jouant à la fois le contrôleur et l'équipe, et remplissez la fiche de réponse du §19.5.10. Indiquez ensuite quelle règle FDIR, quelle précondition de procédure et quelle entrée du registre des risques l'exercice a touchées, et ce que vous modifieriez dans chacune.

6. **Répétition de survie en mode survie.** Scénarisez une répétition dont le seul but est de vérifier si une mission peut survivre à un passage en mode survie au début d'un week-end sans personnel (60 heures). Énumérez la télémesure que le contrôleur doit générer à chaque orbite, les décisions que l'équipe doit prendre au premier passage avec personnel, et le critère de réussite ou d'échec. Utilisez les valeurs d'EOSat-3U du tableau 18.1 du chapitre 18 et la batterie du chapitre 9, §9.3.

7. **Du débriefing à la conception.** Une répétition de la mission 3U produit les constats suivants : (a) l'étape 4 de la procédure de reprise après passage en mode survie attend un point de télémesure qui ne figure que dans le paquet de servitude étendu ; (b) le directeur de vol et le contrôleur satellite croyaient chacun que l'autre déciderait de la commande de désaturation ; (c) dans l'attitude de culbutage imposée par le contrôleur, la puissance moyenne du générateur solaire sur l'orbite est ressortie inférieure à la charge de 2 W du mode survie. Classez chaque constat selon le §19.6.3, rédigez la modification qui en découle avec son responsable, et identifiez le jalon de revue du tableau 1.3 du chapitre 1 auquel chacun devrait être réexaminé.

8. **Compromis de fidélité.** Pour une mission universitaire 3U à 18 mois du lancement, avec une équipe logiciel de vol de deux personnes, estimez l'effort (en semaines-personnes) nécessaire pour atteindre chaque niveau de fidélité du §19.1.3, ainsi que les classes de constats du §19.1.2 que chaque niveau peut ou ne peut pas produire. Recommandez un niveau, et indiquez quelle classe de constats unique vous accepteriez de ne pas détecter avant le lancement.

---

## Références

1. ECSS, *ECSS-E-ST-70C : Ground Systems and Operations*, 2008. https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/
2. ECSS, *ECSS-E-ST-70-11C : Space Segment Operability*, 2008. https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/
3. ECSS, *ECSS-E-ST-70-32C : Test and Operations Procedure Language*, 2008. https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/
4. NASA, *Fault Management Handbook*, NASA-HDBK-1002, 2012. https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002
5. NASA Goddard Space Flight Center, *Rules for the Design, Development, Verification, and Operation of Flight Systems*, GSFC-STD-1000 (les « Gold Rules »), révision en vigueur. https://standards.nasa.gov/standard/GSFC/GSFC-STD-1000
6. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §5.5 (*Transition to operations*) et §6.4. https://www.nasa.gov/reference/systems-engineering-handbook/
7. ESA, *Operations : Mission Control*, European Space Operations Centre. https://www.esa.int/Enabling_Support/Operations
8. Wertz, J. R. et Larson, W. J. (dir.), *Space Mission Analysis and Design*, 3e éd., Microcosm/Kluwer, 1999, chapitre 14 (*Mission Operations*).
9. Squibb, G. F., Boden, D. G. et Larson, W. J. (dir.), *Cost-Effective Space Mission Operations*, 2e éd., McGraw-Hill, 2006.
10. Wertz, J. R., Everett, D. F. et Puschell, J. J. (dir.), *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011, chapitre 29 (*Mission Operations*).
