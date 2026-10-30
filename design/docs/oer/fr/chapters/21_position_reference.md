# Partie IV — Guide de référence des postes d'ingénierie

Cette partie présente une fiche de préparation pour chaque poste d'ingénierie d'une table de conception concourante — les seize postes du tableau 1.4 du chapitre 1, y compris le chef de projet qui les préside. Elle s'adresse aux personnes qui conçoivent un CubeSat pour la première fois. Pour chaque poste, elle couvre :

- **Décisions qui vous reviennent.** Ce que vous devez choisir, et dans quel ordre.
- **Ce qu'il faut savoir d'abord.** Les données d'entrée sans lesquelles vous ne pouvez pas décider.
- **Formules, abaques et règles empiriques.** Des renvois aux équations, tableaux et figures des parties I–III (et aux démonstrations de la partie V) plutôt que leur reformulation, ainsi que les règles empiriques qui ne sont écrites nulle part ailleurs.
- **Écueils fréquents.** Ce qu'il faut surveiller, surtout la première fois.
- **Références.** Normes et ouvrages pour le poste.

Chaque fiche fait deux à quatre pages et se suffit à elle-même. Lisez intégralement celle du poste que vous allez occuper, et parcourez une fiche voisine : la puissance devrait parcourir la thermique, l'AOCS les structures, les communications le segment sol, et tout le monde devrait parcourir celui de l'ingénieur système.

---

## Ingénieur système

Vous détenez les bilans, le jalon et l'autorité de trancher un compromis.

### Décisions qui vous reviennent

1. **Politique de marges de l'étude.** Vous fixez les marges cibles de chaque bilan pour la phase en cours. Le calendrier de marges de masse à deux niveaux (marge de maturité des équipements plus marge au niveau système, qui se resserre de la phase 0/A à la phase D) figure au tableau 8.3 du chapitre 8 ; le même resserrement phase par phase s'applique à la puissance, à la liaison et au Δv, typiquement d'environ 25 %, 6 dB et 25 % en phase A à 5 %, 3 dB et 5 % en phase D (valeurs typiques ; le calendrier de masse est celui du tableau 8.3).
2. **Décisions de bouclage des bilans.** Lorsque la puissance dépasse le bilan, vous décidez si l'équipe sacrifie un rapport cyclique de la charge utile, une capacité de batterie, une surface de générateur solaire ou une durée de vie en fin de vie.
3. **Arbitrage des conflits entre disciplines.** Lorsque l'AOCS veut plus de masse pour les roues de réaction et que la thermique veut la même surface pour un radiateur, vous réunissez les postes concernés et vous arbitrez.
4. **Préparation aux jalons de revue.** Vous jugez si l'équipe est prête à entrer dans la revue suivante (le tableau 1.3 du chapitre 1 liste les jalons et leurs critères d'entrée ; le chapitre 16, §16.5, les éléments de preuve que chacun exige), et vous validez la clôture des actions.

### Ce qu'il faut savoir d'abord

- **Objectifs de la mission** (processus SE 1, chapitre 4) — le *pourquoi* oriente les bilans que vous bouclez.
- **Le cycle en V** et la place de chaque poste sur celui-ci (figure 1.1 et tableau 1.1 du chapitre 1).
- **Les 17 processus du NASA SEH** (chapitre 1, §1.3) — vous en toucherez la plupart chaque jour.
- **La phase du cycle de vie en cours** (figure 1.4 et tableau 1.2 du chapitre 1) — elle fixe la politique de marges.

### Formules, abaques et règles empiriques

- **Définition de la marge et critère de bouclage des bilans** — chapitre 8, §8.4 ; le calendrier de marges est le tableau 8.3 et la répartition des masses est illustrée à la figure 8.4. Votre travail consiste à maintenir chaque bilan sous la colonne de la phase en cours.
- **Interfaces** — la matrice N² du chapitre 8, §8.3 (tableau 8.1, codes de type du tableau 8.2, figure 8.3). Vous êtes responsable de la matrice ; les postes sous-systèmes sont responsables des cases.
- **Traçabilité des exigences** — chapitre 5, §5.4. Chaque ligne de bilan devrait être tracée vers une exigence, et chaque exigence vers une méthode de vérification (chapitre 14).
- **Règle empirique.** Si un bilan se trouve à moins de 2 % de son allocation lors d'une revue, considérez-le comme *non bouclé* : la prochaine sélection d'équipement le fera varier de davantage.

### Écueils fréquents

> **Attention.** Résoudre un conflit en faisant la moyenne des demandes des deux disciplines *sans* mettre à jour le référentiel des exigences concernées est le mode de défaillance classique de l'ingénierie système. Mettez toujours l'exigence à jour avant d'accepter le compromis.

> **Attention.** La marge n'est pas du mou. La marge est une assurance contre l'incertitude. Si vous cédez de la marge à quelqu'un — à l'AOCS pour une roue supplémentaire, par exemple —, consignez-la comme une consommation de marge dans le journal des modifications, et non comme une nouvelle allocation.

> **Erreur fréquente.** Laisser chaque sous-système consommer sa propre marge, de sorte que rien ne reste détenu au niveau système. La marge au niveau système du tableau 8.3 existe précisément parce que les estimations des sous-systèmes sont corrélées.

### Références

- NASA SEH (SP-2016-6105 Rev 2) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- ECSS-M-ST-10C — *Space project management* — [https://ecss.nl/](https://ecss.nl/)
- ECSS-E-ST-10C — *System engineering general requirements* — [https://ecss.nl/](https://ecss.nl/)
- Wertz, Everett et Puschell, *Space Mission Engineering : The New SMAD* (2011), chap. 2.
- Larson et Wertz, *SMAD*, chap. 1, 22.

---

## Chef de projet

Vous êtes responsable du planning, du budget et de l'attention de l'équipe. L'ingénieur système décide de ce *qu'est* la conception ; vous décidez quand elle est arrêtée et par qui.

### Décisions qui vous reviennent

1. **Référentiel de planning et priorités.** Jalons, dépendances, chemin critique et emplacement de la marge de planning.
2. **Allocation des ressources.** Quel poste obtient le temps de qui cette semaine, et quand un poste est surchargé.
3. **Calendrier des revues.** Quand la conception est assez mûre pour passer le jalon suivant (tableau 1.3 du chapitre 1) — et quand elle ne l'est pas, quoi qu'en dise le calendrier.
4. **Acceptation des risques** (avec l'accord de l'ingénierie). Vous présidez la revue des risques et décidez quels risques sont acceptés, réduits ou remontés (chapitre 15, §15.1).
5. **Modifications du périmètre.** Toute demande de modification émanant d'une partie prenante passe par vous, avec son impact sur les coûts et le planning chiffré avant d'être acceptée.

### Ce qu'il faut savoir d'abord

- **Le référentiel de coûts et de planning** établi par l'ingénieur coûts (chapitre 16, §16.2 pour le WBS, §16.4 pour la courbe en S du risque de coût).
- **Le registre des risques** (chapitre 15, §15.2) — les cinq principaux risques et leurs responsables.
- **Les accords d'interface** entre postes (chapitre 8, §8.3) — les interfaces tardives sont la cause habituelle des retards de planning.
- **Les attentes des parties prenantes** telles que recueillies au chapitre 4, §4.2, afin de pouvoir juger une demande de modification par rapport à ce qui a réellement été convenu.

### Formules, abaques et règles empiriques

- **Valeur acquise.** Suivre le travail réalisé par rapport au temps passé et à l'argent dépensé ; un projet qui mesure son avancement au calendrier plutôt qu'aux produits terminés est déjà en retard.
- **Estimation à l'achèvement.** Le chapitre 16, §16.4, présente le traitement P50/P80 du risque de coût ; annoncez le P80 au commanditaire et pilotez sur le P50.
- **Conduite du comité de revue** — le chapitre 16, §16.6, donne les rôles du comité, la banque de questions des examinateurs et les issues GO / NO GO / GO WITH ACTIONS.
- **Règle empirique.** La marge de planning se place à la *fin* du planning, et c'est vous qui la détenez ; un jalon « dans les temps » alors que ses prédécesseurs ont consommé la marge libre n'est pas dans les temps.

### Écueils fréquents

> **Erreur fréquente.** Ne pas protéger la marge de planning — elle est consommée pendant les premières phases, où glisser semble peu coûteux, et elle manque pendant l'intégration et les essais, où ce n'est pas le cas.

> **Attention.** Accepter une dérive du périmètre sans évaluer son impact sur le planning et les coûts. Ce sont les « petits » ajouts à la liste de télémesures, au programme d'essais ou aux produits de données qui se cumulent.

> **Erreur fréquente.** Tenir une revue avant que les produits d'ingénierie soient mûrs, parce que la date a été fixée des mois auparavant. Une revue qui produit trente actions n'a pas fait gagner de temps.

### Références

- ECSS-M-ST-10C — *Space project management* — [https://ecss.nl/](https://ecss.nl/)
- NASA NPR 7120.5F — *Space flight program and project management requirements* — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- Project Management Institute, *A Guide to the Project Management Body of Knowledge* (PMBOK Guide).

---

## Analyste de mission

Vous êtes responsable de la relation de la mission avec la physique : l'orbite, la trace au sol, les conditions d'éclairement, les durées de contact.

### Décisions qui vous reviennent

1. **Type d'orbite et altitude.** LEO / SSO / MEO / GEO / HEO / lunaire. L'altitude doit équilibrer retour scientifique, durée de vie, traînée, rayonnement et coût de lancement (chapitre 7, §7.3).
2. **Inclinaison.** Elle détermine la couverture en latitude, la répétitivité de la trace au sol et (avec l'altitude) la condition d'héliosynchronisme.
3. **LTAN / LTDN** pour les missions SSO — elles déterminent l'enveloppe de l'angle β et la saison d'éclipses.
4. **Réseau de stations sol.** Où transmettre les données au sol, latence, trous de couverture (avec les communications et le segment sol).
5. **Plan de manœuvres.** Quand effectuer le phasage, comment assurer le maintien à poste, quand désorbiter (avec la propulsion).

### Ce qu'il faut savoir d'abord

- La **cible scientifique** de la mission — éviter le reflet spéculaire du Soleil ? couverture polaire ? observation de la Terre continue ?
- La **bande de latitudes** d'intérêt (la surveillance de l'Arctique polaire impose une orbite inclinée ou polaire).
- La **durée de vie visée** et le cadre réglementaire (FCC 5 ans / IADC 25 ans — chapitre 3, §3.6 ; chapitre 7, §7.3.2).
- La **disponibilité des lancements** — un lanceur cible contraint à la fois l'inclinaison et l'altitude.

### Formules, abaques et règles empiriques

- **Période et vitesse orbitales** — chapitre 7, §7.1.1 ; démonstration à la partie V, §V.2, et vérification sur des orbites connues à la figure D.1. Pour une orbite à 450 km, la période est de 93,6 min ; à 500 km, de 94,6 min.
- **Condition d'héliosynchronisme** — choisir $i$ de façon que la régression nodale due au J₂ égale le mouvement moyen de la Terre autour du Soleil (0,9856°/jour) : chapitre 7, §7.3.4, démonstration à la partie V, §V.4, avec les courbes d'inclinaison en fonction de l'altitude de la figure D.2. À 600 km, $i \approx 97.8°$ ; à 700 km, $\approx 98.2°$.
- **Fraction d'éclipse** — la formulation en angle β du chapitre 7, §7.1.2, avec l'enveloppe annuelle de β et les courbes de fraction d'éclipse de la figure 7.2 ; démonstration à la partie V, §V.5. Le cas le plus défavorable (éclipse la plus longue) correspond à β = 0 ; au-delà de $\beta^* = \arcsin(R_E/(R_E+h))$, l'orbite est entièrement éclairée.
- **Durée de vie orbitale** — l'estimation physique du chapitre 7, §7.3.3 (un 3U à 400 km : environ 9 mois, de 3 mois à 2 ans selon le cycle solaire ; à 500 km, environ 5 ans). La règle empirique et l'abaque de durée de vie du chapitre 3, §3.6.4 / figure 3.2, ne constituent qu'un premier tri ; le §7.3.3 explique pourquoi la règle surestime d'un facteur supérieur à dix en dessous d'environ 500 km.
- **Contact avec les stations sol** — la formule de géométrie des passages et le passage maximal de 7,4 min à 500 km / masque de 10° figurent au chapitre 7, §7.4.1 ; la trace au sol est à la figure 7.3 ; le profil de passage à la figure 17.2 du chapitre 17.
- **Transferts et désorbitation** — Hohmann au chapitre 7, §7.5, et à la figure 7.4 ; le Δv de désorbitation (112 m/s de 600 km vers un périgée à 200 km) alimente le chapitre 12, §12.2.

### Écueils fréquents

> **Erreur fréquente.** Choisir une altitude par habitude et supposer qu'elle est conforme aux règles sur les débris. À 500 km, un 3U retombe en environ cinq ans (de deux à douze selon le cycle solaire) ; à 650–700 km, le même satellite peut dépasser la limite de 25 ans, et une règle à 5 ans change complètement la donne. Confirmez toujours avec le chapitre 7, §7.3.3, et une propagation (GMAT ou équivalent).

> **Attention.** L'angle de reflet spéculaire pour l'imagerie de la couleur de l'océan varie à la fois avec la saison (β) et la longitude. Si votre mission est sensible au reflet solaire, construisez une carte β/azimut solaire sur un an avant de figer la LTAN.

> **Attention.** La fraction d'éclipse et β ne vous appartiennent pas en propre : la puissance dimensionne la batterie sur l'éclipse la plus longue (chapitre 9, §9.3) et la thermique y dimensionne le cas froid (chapitre 9, §9.4). Publiez tôt l'enveloppe de β et prévenez-les lorsqu'elle change.

### Références

- Curtis, *Orbital Mechanics for Engineering Students* (3e éd.).
- Vallado, *Fundamentals of Astrodynamics and Applications* (4e éd.).
- SMAD4, chap. 9 (choix de l'orbite).
- Wertz, *Mission Geometry : Orbit and Constellation Design and Management* (2001).
- NASA GMAT (logiciel libre) — [https://software.nasa.gov/software/GSC-17177-1](https://software.nasa.gov/software/GSC-17177-1).

---

## Responsable charge utile

Vous êtes responsable de la science. La mission existe pour faire ce que fait votre charge utile, et tous les autres sous-systèmes sont en définitive au service du vôtre.

### Décisions qui vous reviennent

1. **Concept de charge utile et type de capteur.** Optique / SAR / hyperspectral / radiomètre / récepteur RF / instrument in situ.
2. **Ouverture et bandes spectrales.** Elles déterminent la résolution, le RSB et la masse.
3. **Concept de fonctionnement.** Push-broom, whisk-broom ou matriciel ; acquisition continue ou déclenchée sur cible.
4. **Débit et volume de données par orbite.** Ils dimensionnent les communications et l'OBDH (chapitre 11, §11.9 ; chapitre 12, §12.3).
5. **Plan d'étalonnage.** Sources embarquées, références au sol, cadence.

### Ce qu'il faut savoir d'abord

- **L'objectif mesurable de la mission** (la MoP du chapitre 4, §4.3.3). Pour la couleur de l'océan, il faut certaines bandes à un certain RSB ; pour le SAR, une certaine résolution au sol et un certain temps de revisite ; pour l'AIS, une certaine probabilité de détection.
- **L'altitude de l'orbite**, fournie par l'analyste de mission — elle détermine la distance oblique, la GSD et la couverture.
- **La masse et la puissance disponibles** — typiquement 30–50 % de la plateforme.

### Formules, abaques et règles empiriques

- **Distance d'échantillonnage au sol (GSD).** La limite de diffraction $1.22\,\lambda h/D$ et la limite due au pixel $p\,h/f$ sont démontrées à la partie V, §V.9 ; la GSD atteignable est la plus grande des deux. La figure D.3 les trace toutes deux en fonction de l'ouverture pour des imageurs dans le visible.
- **Longueur d'antenne SAR.** La longueur d'antenne dans le sens de la trace doit dépasser environ deux fois la résolution en azimut souhaitée — une règle empirique qui dimensionne l'élément déployable avant toute conception détaillée.
- **Débit.** Pixels par ligne × bandes × profondeur de codage × cadence ligne, puis volume quotidien comparé à la capacité de liaison descendante du chapitre 11, §11.9, et de la figure 11.6. Le chapitre 11, §11.8, présente le cas d'EOSat-3U (capacité de 956 Mo/jour pour 720 Mo/jour produits) et celui d'UniSat-1, qui ne se boucle pas avec une seule station.
- **Masse de la charge utile.** Une relation tirée de l'héritage, de la forme $M \approx 20\,D^{1.5} + 2$ kg (D en mètres), constitue un premier tri pour les charges utiles optiques ; remplacez-la par une valeur fournisseur dès qu'il en existe une (chapitre 13).

### Écueils fréquents

> **Erreur fréquente.** Dimensionner l'ouverture de la charge utile sur la limite de diffraction alors que les pixels du détecteur sont trop grossiers pour en tirer parti. Accordez les deux : les GSD limitées par le pixel et par la diffraction doivent être comparables.

> **Attention.** Le volume de données par orbite croît avec l'ouverture de deux façons à la fois : plus de pixels et une cadence ligne plus rapide. Vérifiez la capacité de téléchargement quotidienne (figure 11.6) avant de vous engager.

> **Attention.** Votre exigence de pointage et de stabilité est la donnée d'entrée dont l'AOCS a le plus besoin de votre part (chapitre 10, §10.4), et c'est celle qui arrive le plus souvent en retard. Donnez un chiffre, avec un niveau de confiance, dès la première boucle de conception.

### Références

- SMAD4, chap. 9 (charge utile).
- Cracknell, *Introduction to Remote Sensing* (3e éd.).
- Rees, *Physical Principles of Remote Sensing* (3e éd.).
- Cumming et Wong, *Digital Processing of Synthetic Aperture Radar Data*.
- ECSS-E-ST-10-04C — *Space environment* — [https://ecss.nl/](https://ecss.nl/).

---

## Ingénieur puissance

Vous êtes responsable du bilan énergétique, orbite par orbite.

### Décisions qui vous reviennent

1. **Architecture du générateur solaire.** Fixé sur la structure ou déployable ; orientable ou fixe ; technologie (GaAs triple jonction ou Si).
2. **Surface du générateur solaire** — en fin de vie, compte tenu de la dégradation, de la plage d'angle β et de l'angle d'incidence solaire.
3. **Capacité de la batterie et DoD.** Durée de vie en cycles contre profondeur des éclipses.
4. **Tension du bus et architecture du PCDU.** Bus unique ou double ; régulé ou non régulé ; topologie MPPT (chapitre 9, §9.1, figure 9.1).
5. **Rapport cyclique des modes de puissance.** Il découle des modes du ConOps (tableau 18.1 du chapitre 18).

### Ce qu'il faut savoir d'abord

- **L'orbite** — elle détermine l'enveloppe de l'angle β et la fraction d'éclipse (figure 7.2 du chapitre 7).
- **La charge par mode** de chaque sous-système, et les rapports cycliques des modes, afin d'établir la charge moyenne sur l'orbite et la charge maximale en phase éclairée (tableau 8.4 du chapitre 8).
- **La durée de vie de la mission** — elle détermine le nombre de cycles et la dégradation en fin de vie.

### Formules, abaques et règles empiriques

- **Dimensionnement du générateur solaire** — la chaîne en cinq étapes du chapitre 9, §9.2 (puissance EOL à partir des charges en phase éclairée et en éclipse, puissance BOL via les facteurs de dégradation et de température, surface via le rendement des cellules, l'angle d'incidence solaire, le taux de remplissage et le facteur de verre de protection). La figure 9.2 montre ce que le bilan équilibre ; la figure 9.3 est l'abaque de dimensionnement. La partie V, §V.11, démontre cette chaîne et montre son équivalence avec la formulation en fraction d'éclipse que l'on trouve dans les références plus anciennes.
- **Dimensionnement de la batterie** — chapitre 9, §9.3, avec les courbes de durée de vie en cycles en fonction de la DoD de la figure 9.4. Un point de conception à 25–30 % de DoD fournit, avec marge, le nombre de cycles nécessaire à une mission LEO de plusieurs années ; la chimie LCO éprouvée exige un déclassement plus important, la LFP offre plus de latitude mais une densité massique moindre. Partie V, §V.12.
- **Valeurs de l'exemple** — EOSat-3U a besoin d'environ 14 W de puissance de générateur solaire en fin de vie et de 0,053 m² de panneau pour une charge maximale en phase éclairée de 10 W (chapitre 9, §9.2) ; celles d'UniSat-1 figurent au §9.5.
- **Règle empirique.** Le générateur solaire doit couvrir le *mode éclairé le plus défavorable*, et non la moyenne sur l'orbite ; la batterie doit couvrir *l'éclipse la plus longue à la charge d'éclipse la plus élevée*, et non l'éclipse typique.

### Écueils fréquents

> **Attention.** Dimensionner le générateur solaire en début de vie affame la batterie en fin de vie. Calculez toujours en EOL avec une dégradation réaliste (environ 2,5 % par an pour le GaAs triple jonction en LEO, plus le déclassement en température du chapitre 9, §9.2).

> **Erreur fréquente.** Oublier que le générateur ne produit que lorsque les cellules voient le Soleil — et que *les cellules* qui le voient changent au fil de l'année. β = 0° (Soleil dans le plan de l'orbite) est le cas d'éclipse maximale : un panneau fixé sur la face zénith voit le Soleil sous incidence normale au midi orbital, mais l'éclipse est la plus longue. Pour |β| élevé, l'éclipse raccourcit ou disparaît, mais un panneau dont la normale est dans le plan de l'orbite voit alors le Soleil sous incidence rasante. Dimensionnez sur toute la plage de β de la figure 7.2, et indiquez quel panneau et quelle saison fixent le point de conception.

> **Attention.** La thermique et vous vous disputez la même surface extérieure — radiateur ou cellules. Réglez l'allocation de chaque face dès la première boucle de conception, et non à la dernière.

### Références

- ECSS-E-ST-20C — *Electrical and electronic* — [https://ecss.nl/](https://ecss.nl/)
- SMAD4, chap. 11 (puissance).
- Patel, *Spacecraft Power Systems*.
- Brown, *Spacecraft Propulsion and Power Subsystems*.

---

## Ingénieur SCAO

Vous êtes responsable du pointage du satellite.

### Décisions qui vous reviennent

1. **Exigence de pointage** — connaissance, contrôle et stabilité, par axe (chapitre 10, §10.1).
2. **Jeu de capteurs** — senseur solaire / magnétomètre / senseur stellaire / récepteur GNSS / centrale inertielle (IMU).
3. **Jeu d'actionneurs** — magnétocoupleur / roue de réaction / propulseur.
4. **Modes et transitions** — amortissement (detumbling), acquisition solaire, pointage fin, survie (avec les opérations : chapitre 18, §18.2).
5. **Plan de gestion du moment cinétique** — à quelle fréquence, avec quels moyens (chapitre 10, §10.5).

### Ce qu'il faut savoir d'abord

- **L'exigence de pointage** fournie par le responsable charge utile (par exemple 0,05° à 1σ pour un imageur push-broom).
- **L'environnement perturbateur** sur l'orbite choisie (traînée à 400 km ou à 700 km ; champ magnétique pour une SSO) — chapitre 10, §10.2.
- **Le tenseur d'inertie du satellite** — fourni par les structures, il change à chaque modification de l'aménagement.

### Formules, abaques et règles empiriques

- **Bilan de pointage** — la somme quadratique des termes de connaissance, de contrôle et d'alignement, chapitre 10, §10.4, représentée en cascade à la figure 10.3. Dans le bilan d'EOSat-3U, c'est le terme d'alignement qui domine ; améliorez le terme dominant, pas le capteur.
- **Couples perturbateurs** — gradient de gravité, magnétique, pression solaire et traînée au chapitre 10, §10.2 ; la partie V, §V.14, donne l'ordre de grandeur de la traînée. Pour un 3U à 500 km, le terme magnétique domine.
- **Dimensionnement des roues** — capacité de moment cinétique à partir du couple perturbateur, de l'intervalle entre désaturations et d'un facteur de marge, chapitre 10, §10.3 et §10.5 ; la figure 10.4 montre l'accumulation pour un satellite plus grand. Notez le résultat du §10.3 sur le temps de basculement : une petite roue est limitée en moment cinétique et non en couple, si bien que la formule de basculement fondée sur le seul couple sous-estime le temps.
- **Règle empirique.** Planifiez la désaturation en même temps que la roue. Une roue dimensionnée pour le pointage fin mais pas pour le déchargement saturera en quelques orbites.

### Écueils fréquents

> **Attention.** Dérive de la normalisation du quaternion dans le logiciel de vol — même une dérive de 10⁻⁶ par seconde finit par compter. Renormalisez à chaque cycle.

> **Erreur fréquente.** Concevoir pour le pointage fin sans dimensionner les magnétocoupleurs pour la désaturation. Planifiez la stratégie de désaturation en même temps que la roue.

> **Attention.** Le choix d'antenne de l'ingénieur télécommunications dépend de votre pointage : une parabole exige une fraction de son ouverture de faisceau, une antenne patch tolère des dizaines de degrés (figure 11.2 du chapitre 11). Indiquez-lui ce que vous pouvez tenir dans *chaque* mode, y compris le mode survie.

### Références

- ECSS-E-ST-60-20C — *Star sensor terminology and performance specification* ; ECSS-E-ST-60-10C — *Control performance* — [https://ecss.nl/](https://ecss.nl/).
- Markley et Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*.
- Sidi, *Spacecraft Dynamics and Control*.
- SMAD4, chap. 10.

---

## Ingénieur thermique

Vous maintenez chaque composant dans sa plage de fonctionnement dans les cas chaud, froid et transitoires.

### Décisions qui vous reviennent

1. **Enveloppe cas chaud / cas froid** — à définir en fonction de l'angle β, de la saison, des éclipses et de la dissipation interne (chapitre 9, §9.4).
2. **Revêtements de surface (α, ε)** pour chaque panneau extérieur et chaque radiateur.
3. **MLI ou réchauffeurs** — isolation passive ou contrôle actif.
4. **Topologie de rejet thermique** — emplacement et surface des radiateurs.
5. **Interfaces thermiques** — chemins conductifs vers et depuis chaque composant.

### Ce qu'il faut savoir d'abord

- **Les plages de température de fonctionnement** de chaque composant (la batterie est la plus stricte, typiquement −5 à +25 °C en charge).
- **La fraction et la durée d'éclipse**, fournies par l'analyste de mission (figure 7.2 du chapitre 7).
- **La carte de dissipation interne** par mode, fournie par la puissance (tableau 8.4 du chapitre 8) : le cas froid est le mode survie dans l'éclipse la plus longue, le cas chaud est le mode le plus dissipatif au β le plus faible.

### Formules, abaques et règles empiriques

- **Bilan d'énergie et équilibre radiatif** — chapitre 9, §9.4 : apports solaire, d'albédo et d'infrarouge terrestre, dissipation interne, rayonnement émis ; la température d'équilibre en fonction de α/ε est donnée à la figure 9.6, avec les revêtements courants. La partie V, §V.10, démontre la formulation pour une plaque plane et traite l'exemple d'une peinture blanche.
- **Cas traités** — les cas chaud et froid d'EOSat-3U, la puissance de réchauffage en régime établi et la chute de température transitoire au cours d'une éclipse figurent au chapitre 9, §9.4.11 ; UniSat-1 au §9.5.
- **Règle empirique.** Le rapport α/ε est le principal levier de conception : la peinture blanche (α/ε ≈ 0,16) se situe bien en dessous de la plage de l'électronique, la peinture noire près de sa limite supérieure, l'aluminium poli nu très au-dessus.
- **Règle empirique.** Un MLI à dix couches a une émittance effective ε* ≈ 0,03 ; avec moins de couches, l'isolation est moins bonne — et un CubeSat a rarement la place pour dix.

### Écueils fréquents

> **Erreur fréquente.** Utiliser α et ε mesurés à température ambiante pour les calculs du cas froid — à −100 °C, l'émittance de nombreux matériaux change. Citez la température des données sources.

> **Attention.** Le MLI se caractérise par son émittance effective ε*, et non par le matériau de base.

> **Attention.** La puissance de réchauffage nécessaire dans le cas froid est aussi le problème de la puissance : elle s'ajoute à la charge en éclipse du chapitre 9, §9.3. Bouclez cette boucle avant que la batterie soit dimensionnée.

### Références

- ECSS-E-ST-31C — *Thermal control* — [https://ecss.nl/](https://ecss.nl/)
- Gilmore, *Spacecraft Thermal Control Handbook*, vol. I et II.
- SMAD4, chap. 12.

---

## Ingénieur télécommunications

Vous transportez les bits — dans les deux sens.

### Décisions qui vous reviennent

1. **Bande de fréquences** — UHF / S / X / Ka. Elle détermine les licences, la taille d'antenne et l'affaiblissement de propagation (chapitre 11, §11.5).
2. **Modulation et codage** (chapitre 11, §11.6).
3. **Diagramme de rayonnement de l'antenne** — parabole à grand gain, antenne patch ou antenne déployable (chapitre 11, §11.3).
4. **Réseau de stations sol** — station unique ou réseau (avec le segment sol, chapitre 17).
5. **Allocation de la marge de liaison** à chaque phase.

### Ce qu'il faut savoir d'abord

- **Le volume de données quotidien**, fourni par le responsable charge utile.
- **L'exigence de latence** — s'il y en a une —, fournie par le représentant des utilisateurs.
- **La capacité de pointage** de l'AOCS dans chaque mode, y compris le mode survie (elle conditionne le diagramme de rayonnement utilisable).
- **Les contraintes réglementaires** de la bande choisie (chapitre 2, §2.7 ; l'ingénieur conformité est responsable de la notification).

### Formules, abaques et règles empiriques

- **Le bilan de liaison** — l'équation canonique du chapitre 11, §11.2, $C/N_0 = \text{PIRE} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k$, avec $k = -228.6$ dBW/K/Hz, et sa démonstration à la partie V, §V.7. Conservez les pertes de polarisation et de ligne de réception sur des lignes distinctes, même lorsqu'elles sont faibles ; le bilan qui les omet est celui qui ne se boucle pas sur le pas de tir.
- **Affaiblissement en espace libre** — chapitre 11, §11.4, et figure 11.3 (démontré à la partie V, §V.6). Chaque doublement de la distance ou de la fréquence ajoute 6 dB. Avec $R_E = 6378.137$ km, la distance oblique à 10° d'élévation vaut 1440 km à 400 km d'altitude et 1695 km à 500 km ; passer du nadir à 10° d'élévation coûte 10,6 dB.
- **Modulation et codage** — les courbes de TEB de la figure 11.4 (partie V, §V.8) ; un code concaténé apporte environ 5 dB à un TEB de 10⁻⁵, le LDPC davantage.
- **Diagrammes d'antenne** — figure 11.2 : une parabole exige un pointage de l'AOCS à une fraction de son ouverture de faisceau, une antenne patch tolère des dizaines de degrés au prix de 25–30 dB de gain.
- **La cascade** — la figure 11.5 présente un bilan complet en bande S lu de gauche à droite : les gains s'ajoutent, les pertes se retranchent, l'écart au $C/N_0$ requis est la marge.
- **Valeurs de l'exemple** — chapitre 11, §11.8 : la liaison en bande S d'EOSat-3U se boucle avec 10,4 dB de marge à 5 Mbit/s et est limitée en bande passante plutôt qu'en puissance ; la liaison UHF d'UniSat-1 a besoin d'une correction d'erreurs directe pour satisfaire son exigence de 3 dB.

### Écueils fréquents

> **Attention.** La perte de dépointage n'est pas négligeable. Pour une ouverture à mi-puissance de 1°, une erreur de pointage de 0,3° coûte environ 1 dB ; à 0,5°, environ 3 dB.

> **Erreur fréquente.** Oublier l'effet Doppler. Une liaison en bande S à 2,2 GHz depuis un satellite LEO à 7,5 km/s subit un décalage Doppler d'environ ±55 kHz à l'horizon — la poursuite du récepteur doit le suivre.

> **Attention.** Une liaison qui se boucle n'est pas un bilan de données qui se boucle. Vérifiez le chapitre 11, §11.9 — passages par jour, minutes utilisables par passage et efficacité protocolaire — avant d'annoncer au responsable charge utile que le débit convient.

### Références

- ECSS-E-ST-50-05C — *Radio frequency and modulation* — [https://ecss.nl/](https://ecss.nl/).
- Pratt, Bostian et Allnutt, *Satellite Communications* (3e éd.).
- Recommandations UIT-R — [https://www.itu.int/en/ITU-R/](https://www.itu.int/en/ITU-R/).

---

## Ingénieur propulsion

Vous êtes responsable du Δv. (Même si votre CubeSat n'en a pas, c'est vous qui le décidez.)

### Décisions qui vous reviennent

1. **Besoin de propulsion** — compensation de la traînée ? désorbitation ? phasage ? vol en formation ? rendez-vous ? (Chapitre 12, §12.2.)
2. **Choix de l'ergol** — gaz froid / monergol / biergol / électrique (Hall, ionique, PPT, FEEP).
3. **Dimensionnement du propulseur** — poussée, Isp et puissance.
4. **Masse totale d'ergols** — l'équation de Tsiolkovski.
5. **Plan de gestion de l'impact du jet et de la contamination.**

### Ce qu'il faut savoir d'abord

- **Le bilan de Δv** — somme de toutes les manœuvres requises, avec marge, fournie par l'analyste de mission (chapitre 7, §7.5).
- **La durée de la mission** — elle détermine le Δv cumulé pour les orbites dominées par la traînée.
- **La puissance disponible** — elle conditionne la faisabilité de la propulsion électrique (un CubeSat de 20 W ne peut pas alimenter un propulseur à effet Hall de 200 W).

### Formules, abaques et règles empiriques

- **L'équation de Tsiolkovski** — chapitre 12, §12.2.2, et figure 12.2 (Δv en fonction du rapport de masse pour des Isp représentatives) ; démonstration à la partie V, §V.3. Pour les ~100 m/s d'une poussée de désorbitation de CubeSat, la courbe est presque linéaire ; pour un transfert d'orbite, l'exponentielle prend le dessus.
- **Valeurs de l'exemple** — le cas de désorbitation du chapitre 12, §12.2.5 : 112 m/s de 600 km vers un périgée à 200 km, avec la masse d'ergols pour les options gaz froid, monergol et électrique.
- **Conformité en matière de débris** — durée de vie naturelle du chapitre 7, §7.3.3, comparée aux règles du §7.3.2 ; si la durée de vie naturelle n'est pas conforme, le Δv de désorbitation est une exigence, pas une option.

### Écueils fréquents

> **Attention.** L'Isp dépend des conditions d'entrée et du rapport de détente de la tuyère. Donnez la valeur au point de fonctionnement réellement utilisé en vol.

> **Erreur fréquente.** Confondre la masse totale ($m_0$) et la masse sèche ($m_f$) en appliquant l'équation de Tsiolkovski — et oublier que la masse d'ergols modifie la masse de la structure et le tenseur d'inertie de l'ingénieur SCAO.

### Références

- Sutton et Biblarz, *Rocket Propulsion Elements* (9e éd.).
- ECSS-E-ST-35C — *Propulsion general requirements* — [https://ecss.nl/](https://ecss.nl/).
- Goebel et Katz, *Fundamentals of Electric Propulsion*.

---

## Ingénieur structures

Vous vous assurez que le satellite survit au lancement et à la vie en orbite, et que le matériel de tous les autres est correctement interfacé sur le plan mécanique.

### Décisions qui vous reviennent

1. **Topologie de la structure primaire** — monolithique, panneaux et nervures, ou fabrication additive.
2. **Choix des matériaux** — Al, Ti, CFRP, sandwich.
3. **Bouclage du bilan de masse avec marge** (avec l'ingénieur système : chapitre 8, §8.4, et tableau 8.3).
4. **Voie de vérification des charges de lancement** — analyse (FEA), essai, ou les deux (chapitre 14, §14.3).
5. **Interfaces mécaniques** — schéma de fixation, compatibilité avec le déployeur (chapitre 12, §12.1).

### Ce qu'il faut savoir d'abord

- **L'environnement du lanceur** — niveaux de qualification en sinus, vibrations aléatoires et chocs (chapitre 14, §14.3).
- **La masse et le centre de gravité des composants** — chaque sous-système les fournit, et le tenseur d'inertie est transmis à l'AOCS.
- **L'enveloppe de la CubeSat Design Specification** — rails, contact en bout de rail, interrupteurs de déploiement, limites du centre de gravité (chapitre 12, §12.1).

### Formules, abaques et règles empiriques

- **Marge de sécurité** — la définition canonique et l'exemple résolu figurent au chapitre 12, §12.1.6 (partie V, §V.13). Pour l'Al 7075-T6, la contrainte admissible à la limite élastique est de 503 MPa, avec un coefficient de sécurité à la limite élastique de 1,25.
- **Première fréquence propre** — supérieure à 100 Hz, c'est l'exigence habituelle pour un CubeSat ; l'estimation par poutre-caisson d'un 3U au chapitre 12, §12.1, donne environ 330 Hz.
- **Charges sur les rails** — la charge quasi statique de lancement sur les rails, avec $g_0 = 9.80665$ m/s², est traitée au chapitre 12, §12.1.
- **Règle empirique.** Les fixations, les adhésifs et le harnais ajoutent 5–10 % à la masse structurale ; portez-les comme une ligne du bilan de masse dès la première boucle.

### Écueils fréquents

> **Attention.** Oublier la masse des fixations et des adhésifs.

> **Erreur fréquente.** Dimensionner pour les charges statiques en oubliant l'amplification dynamique à la résonance sous vibrations aléatoires. Appliquez un facteur Q (typiquement 5–10) au premier mode.

> **Attention.** Tout élément déployable (antenne, panneau, mât) est un mécanisme, et un mécanisme est un point de défaillance unique tant que l'AMDEC du chapitre 15 ne dit pas le contraire.

### Références

- ECSS-E-ST-32C — *Structures* — [https://ecss.nl/](https://ecss.nl/).
- Sarafin, *Spacecraft Structures and Mechanisms*.
- CubeSat Design Specification (CDS) Rev 14 — [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement).
- NASA GSFC-STD-7000 (GEVS).

---

## Ingénieur coûts

Vous êtes le garde-fou de l'équipe face à la réalité.

### Décisions qui vous reviennent

1. **Structure du WBS** (chapitre 16, §16.2, d'après la NPR 7120.5).
2. **Méthode d'estimation des coûts** — paramétrique au début, par analogie, ascendante par la suite (chapitre 16, §16.1).
3. **Référentiel de planning** — jalons, chemin critique, marge libre (avec le chef de projet).
4. **Estimations ajustées au risque** — comment intégrer le risque à la fois dans le coût et dans le planning (chapitre 16, §16.4).

### Ce qu'il faut savoir d'abord

- **La nomenclature** du chapitre 13 — coûts des équipements, délais d'approvisionnement et TRL (§13.2 pour le facteur de risque lié au TRL).
- **Les coûts non récurrents** — le chapitre 13, §13.1.3, détaille la constitution des NRE ; ne les reprenez pas dans le modèle paramétrique.
- **Le nombre d'unités** — la courbe d'apprentissage du chapitre 16, §16.3 (avec l'exposant du chapitre 4, §4.6.4), change la réponse pour une constellation.
- **Le plafond programmatique** et ce que le commanditaire compte comme « coût » (lancement, opérations, segment sol inclus ou non).

### Formules, abaques et règles empiriques

- **Relations d'estimation de coût** et leur précision selon la phase — chapitre 16, §16.1.
- **Courbe d'apprentissage** — chapitre 16, §16.3 : sur une courbe à 90 %, la dixième unité coûte 70 % de la première, et vingt unités coûtent 14,6 fois la première, et non vingt fois.
- **Risque de coût** — la courbe en S P50/P80 du chapitre 16, §16.4 ; annoncez le P80, pilotez sur le P50.
- **Valeurs de l'exemple** — l'estimation d'EOSat-3U au chapitre 16, §16.1, et le cumul d'UniSat-1 (environ 85 k€, valeur indicative 2026) au chapitre 13, §13.6, et au chapitre 16, §16.4.3.

### Écueils fréquents

> **Erreur fréquente.** Prendre le résultat de l'outil paramétrique pour la réponse. Ce résultat est un point de départ ; adaptez-le à votre mission et au marché des lancements dans lequel vous travaillez.

> **Attention.** Les prix des COTS pour CubeSat se périment vite et sont annoncés hors intégration, essais et pièces de rechange. Indiquez pour chaque prix son année et ce qu'il comprend.

### Références

- NASA NPR 7120.5F — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/).
- Wertz et al., *Space Mission Engineering*, chap. 23 (coûts).
- SMAD4, chap. 20.
- NASA *Cost Estimating Handbook* — [https://www.nasa.gov/cost-estimating-handbook/](https://www.nasa.gov/cost-estimating-handbook/).

---

## Ingénieur conformité

Vous vous assurez que la mission a le droit de voler — au regard des normes qu'elle a adoptées, des autorités qui lui délivrent ses licences et des régimes de contrôle des exportations par lesquels ses composants sont passés.

### Décisions qui vous reviennent

1. **Applicabilité et adaptation des normes.** Quelles normes ECSS / NASA s'appliquent, et à quel niveau — la matrice d'adaptation (chapitre 3, §3.2, d'après l'ECSS-S-ST-00-02C).
2. **Stratégie de licences de fréquences.** Attribution amateur (IARU) ou commerciale ; la publication anticipée auprès de l'UIT, la notification nationale et leurs délais (chapitre 2, §2.7).
3. **Classification au titre du contrôle des exportations** de chaque composant (ITAR / EAR / marchandises contrôlées canadiennes), avec l'approvisionnement (chapitre 2, §2.8 ; chapitre 13, §13.4).
4. **Conformité en matière d'atténuation des débris** — 25 ans selon l'IADC, 5 ans selon la FCC lorsqu'elle s'applique, risque de victimes (chapitre 3, §3.6 ; chapitre 7, §7.3.2).
5. **Licence de télédétection** au titre de la LSTS si la mission observe la Terre (chapitre 2, §2.6), et immatriculation de l'objet après le lancement (chapitre 3, §3.7).

### Ce qu'il faut savoir d'abord

- **L'orbite et la durée de vie**, fournies par l'analyste de mission — le dossier débris en dépend entièrement.
- **La bande, la PIRE et les stations sol**, fournies par les communications — la notification ne peut pas commencer sans elles.
- **La nomenclature** du chapitre 13 — origine et classification de chaque composant.
- **La résolution de la charge utile et le plan de distribution des données**, fournis par le responsable charge utile et le représentant des utilisateurs — ils déterminent si la LSTS s'applique, et à quel niveau.

### Formules, abaques et règles empiriques

- **Le registre de conformité** — le format du tableau 3.1 du chapitre 3 : norme ou réglementation, paramètre dont elle dépend, phase à laquelle elle doit être soldée, éléments de preuve.
- **Calendrier des licences** — les délais du chapitre 2, §2.7.4 ; la coordination du spectre est couramment l'élément le plus long du planning d'un CubeSat, et elle commence avant que la conception soit figée.
- **Règle empirique.** Toute démarche réglementaire est une exigence assortie d'une méthode de vérification (chapitre 14) : inscrivez-la dans la matrice de vérification avec une date, pas dans une note.

### Écueils fréquents

> **Attention.** Commencer la notification de fréquences après le gel de la conception. La coordination prend un an ou plus ; un changement de bande tard en phase B réécrit le bilan de liaison, l'antenne et la licence.

> **Erreur fréquente.** Supposer qu'un composant COTS échappe au contrôle des exportations parce qu'il a été acheté sur catalogue. La classification dépend de l'origine du composant et de sa technologie, pas de son prix.

> **Attention.** La conformité en matière de débris s'évalue sur le satellite tel qu'il vole — surface déployée, masse finale, altitude réelle —, et non sur les chiffres de la phase A. Refaites l'analyse à chaque jalon.

### Références

- ECSS-S-ST-00-02C — *Tailoring* — [https://ecss.nl/](https://ecss.nl/).
- ISDE, *Circulaire des procédures concernant les clients CPC-2-6-02* (licences de stations spatiales) — [https://ised-isde.canada.ca/](https://ised-isde.canada.ca/).
- *Loi sur les systèmes de télédétection spatiale* (LSTS) et ses règlements — [https://laws-lois.justice.gc.ca/](https://laws-lois.justice.gc.ca/).
- Règlement des radiocommunications de l'UIT, article 9 (coordination) — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR).
- IADC *Space Debris Mitigation Guidelines* — [https://www.iadc-home.org/](https://www.iadc-home.org/).

---

## Représentant des utilisateurs

Vous parlez au nom des personnes qui utiliseront les données. La mission est un succès lorsqu'elles le disent, et non lorsque les bilans se bouclent.

### Décisions qui vous reviennent

1. **Exigences sur les produits de données** — format, résolution, précision, délai de mise à disposition (avec le responsable charge utile : chapitre 4, §4.3).
2. **Modes d'accès des utilisateurs** — API, portail, téléchargement direct (avec le segment sol : chapitre 17, §17.1).
3. **Niveaux de service** — disponibilité, temps de réponse, fraîcheur des données.
4. **Validation** que le système tel que conçu répond à ce que les parties prenantes ont demandé (chapitre 14, §14.1 — la validation est votre affaire, la vérification celle des ingénieurs).
5. **La voix de l'utilisateur dans les études de compromis** — vous siégez dans le comité d'étude de compromis du chapitre 4, §4.5, et notez les options du point de vue de l'utilisateur.

### Ce qu'il faut savoir d'abord

- **Qui sont les utilisateurs** — recherche, commercial, public, opérationnel — et en quoi ils diffèrent (chapitre 4, §4.2).
- **Ce qu'ils font aujourd'hui des données**, sans cette mission, afin de pouvoir énoncer le besoin plutôt que le souhait.
- **Le volume descendant et la latence que le système peut réellement fournir** (chapitre 11, §11.9 ; chapitre 17, §17.2), afin que le niveau de service promis soit tenable par la mission.

### Formules, abaques et règles empiriques

- **Besoin → objectif → MoE → MoP → TPM** — la hiérarchie du chapitre 4, §4.3.3, est votre instrument ; chaque exigence sur un produit de données devrait remonter à une mesure d'efficacité que l'utilisateur reconnaît.
- **Le test du QUOI et non du COMMENT** du chapitre 4, §4.1.4 : si votre exigence nomme une mise en œuvre, réécrivez-la.
- **Règle empirique.** Un « souhaitable » auquel on ne peut pas renoncer dans un compromis est une exigence ; une exigence dont personne ne regretterait l'absence est un souhaitable. Faites le tri avant la première étude de compromis, pas pendant.

### Écueils fréquents

> **Erreur fréquente.** Ne pas distinguer le « souhaitable » des véritables exigences — et laisser les ingénieurs deviner lequel est lequel.

> **Attention.** Spécifier des détails de mise en œuvre (une bande, un format de fichier, un satellite) au lieu de besoins des utilisateurs (une latence, une couverture, une précision).

> **Attention.** Supposer une bande passante illimitée pour la livraison des données. Le volume quotidien que le satellite peut transmettre en liaison descendante (figure 11.6) plafonne ce que tout utilisateur peut recevoir, aussi bon que soit le portail.

### Références

- NASA SEH §4.1 — *Stakeholder expectations definition* — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).
- ECSS-E-ST-10C §5.2 — *Requirements engineering* — [https://ecss.nl/](https://ecss.nl/).
- ISO 9241 — Ergonomie de l'interaction homme-système.

---

## Ingénieur opérations de mission

Vous piloterez le satellite une fois que l'équipe l'aura construit — et vous répéterez ce pilotage avant le lancement (chapitre 19).

### Décisions qui vous reviennent

1. **Concept d'opérations** — effectifs, niveau d'automatisation, organisation des quarts (chapitre 18, §18.1).
2. **Plan de passage** — quelles procédures, dans quel ordre, à chaque contact (chapitre 18, §18.4 ; chapitre 17, §17.4).
3. **Arbre de traitement des anomalies** — qui annonce quoi, et quand (chapitre 18, §18.5).
4. **Définition des télécommandes et de la télémesure** — en coordination avec l'ingénieur logiciel.
5. **Séquence LEOP** — premier contact, déploiements, chronologie de la recette en orbite (chapitre 19, §19.4).

### Ce qu'il faut savoir d'abord

- **Les modes opérationnels et leurs transitions**, issus du ConOps (chapitre 18, §18.2, et tableau 18.1).
- **La couverture des stations sol**, fournie par l'analyste de mission et le segment sol (chapitre 17, §17.2).
- **L'architecture FDIR** — ce que le satellite fera de lui-même avant que vous n'en entendiez parler (chapitre 18, §18.3).
- **L'inventaire des procédures** — LEOP, recette en orbite, nominales, de contingence, d'urgence.

### Formules, abaques et règles empiriques

- **Temps de contact par jour et données par passage** — chapitre 17, §17.2.3 ; une station de haute latitude voit un satellite en SSO à la plupart des orbites, une station de moyenne latitude à quatre à six d'entre elles.
- **La bibliothèque d'anomalies** — le chapitre 19, §19.5, recense les symptômes, diagnostics et reprises qui méritent d'être répétés (sous-tension, perte de contact, perte du pointage fin, passage inattendu en mode survie, dépassement thermique, mémoire de masse pleine, commande rejetée, et la panne sol qui ressemble à une panne du satellite).
- **Règle empirique.** Les huit premières heures après la séparation sont les plus critiques de la mission ; scénarisez-les à la minute près, et répétez le scénario.

### Écueils fréquents

> **Attention.** La discipline de boucle vocale est le tueur silencieux. Des interférences de parole qui semblent anodines en répétition deviennent rédhibitoires sous la pression du temps réel.

> **Erreur fréquente.** Ne pas prévoir d'opérations dégradées — une seule station sol, un déploiement partiel, des effectifs aux heures ouvrables alors que le plan supposait du 24/7.

> **Attention.** Lacunes saisonnières et géométriques de la visibilité des stations ; une station satisfaisante en simulation peut être inutilisable aux angles β de la saison de lancement.

### Références

- ECSS-E-ST-70C — *Ground systems and operations* — [https://ecss.nl/](https://ecss.nl/).
- ECSS-E-ST-70-32C — *Test and operations procedure language*.
- NASA-HDBK-1002 — *Fault management handbook* ; GSFC-STD-1000 — *Rules for the design, development, verification and operation of flight systems*.

---

## Ingénieur segment sol

Vous êtes responsable de l'architecture entre l'antenne et l'utilisateur.

### Décisions qui vous reviennent

1. **Réseau de stations sol** — en propre, en location ou commercial ; une seule station ou un réseau (chapitre 17, §17.1, §17.5).
2. **Logiciel de contrôle de mission** — libre ou commercial.
3. **Conception de l'archivage et du traitement** — L0 → L1 → L2 → distribution, et la latence de chaque étape.
4. **Outils de planification et de programmation des passages.**
5. **Architecture de cybersécurité** — authentification des commandes, chiffrement de la liaison, cloisonnement du réseau.

### Ce qu'il faut savoir d'abord

- **Le volume de données quotidien** — il dimensionne les contrats de bande passante et la croissance de l'archive.
- **L'exigence de latence**, fournie par le représentant des utilisateurs — elle détermine la densité du réseau de stations.
- **La classification de la mission** — les missions de défense et à double usage exigent des architectures différentes des missions civiles.
- **La pile de protocoles** que parlera le satellite (chapitre 17, §17.3).

### Formules, abaques et règles empiriques

- **Géométrie du contact** — chapitre 7, §7.4.1, et chapitre 17, §17.2 : le profil de passage de la figure 17.2, le passage maximal de 7,4 min à 500 km avec un masque de 10°, 9,2 min à 5°.
- **Capacité quotidienne** — les volumes station par station du chapitre 17, §17.2.3, et le bouclage par rapport à la production au §17.5 ; le déficit d'UniSat-1 avec une seule station est traité au §17.6.
- **Règle empirique.** La tarification commerciale des stations sol peut inverser l'économie entre bandes, et entre quelques longs passages et de nombreux passages courts ; faites le calcul au débit que vous utiliserez réellement en vol.

### Écueils fréquents

> **Attention.** Les modèles de tarification des stations sol en tant que service facturent à la minute ou au passage ; la bande la moins chère sur le papier n'est pas forcément la moins chère par mégaoctet.

> **Erreur fréquente.** Concevoir le segment sol après le gel du segment spatial. Le réseau de stations fait partie du bilan de liaison (chapitre 11, §11.7) et du bilan de données (§11.9) ; il a sa place dès la première boucle de conception.

### Références

- Normes CCSDS *Mission Operations* et de support croisé — [https://public.ccsds.org/Pubs/](https://public.ccsds.org/Pubs/).
- ECSS-E-ST-70C — *Ground systems and operations* — [https://ecss.nl/](https://ecss.nl/).
- SMAD4, chap. 14–15.

---

## Ingénieur logiciel (OBDH et logiciel de vol)

Vous êtes responsable du calculateur de bord, du logiciel de vol, de la liste de télémesure et de la moitié bord de la FDIR.

### Décisions qui vous reviennent

1. **Architecture de l'OBC** — carte unique ou paire redondante ; système sur puce ou composants discrets (chapitre 12, §12.3).
2. **Topologie des bus** — CAN / I²C / SPI / RS-422 / SpaceWire (les types d'interface du tableau 8.2 du chapitre 8).
3. **Architecture mémoire** — RAM, flash, mémoire de masse, schéma EDAC (chapitre 12, §12.3.3, pour le dimensionnement).
4. **Architecture du logiciel de vol** — gestionnaire de modes, boucle de commande du SCAO, gestionnaire TM/TC, règles FDIR (chapitre 18, §18.3).
5. **Ensemble de services** — quels services CCSDS/PUS mettre en œuvre ; les dictionnaires de télécommandes et de télémesure.

### Ce qu'il faut savoir d'abord

- **Le volume TM/TC** de chaque sous-système.
- **Les fréquences des boucles temps réel** exigées par l'AOCS.
- **Le plus long intervalle sans contact** — il dimensionne la mémoire de masse (chapitre 12, §12.3.3 ; EOSat-3U retient un cas d'interruption de trois jours).
- **Le logiciel sol** avec lequel il doit dialoguer (chapitre 17, §17.3).

### Formules, abaques et règles empiriques

- **Dimensionnement de la mémoire de masse** — plus long intervalle sans contact × débit maximal × une marge de 1,5–2 ; le chapitre 12, §12.3.3, traite le cas d'EOSat-3U.
- **Temporisateur chien de garde** — typiquement 30 s pour un OBC de CubeSat ; plus court pour les tâches à criticité élevée. Le chapitre 15, §15.5, porte le chien de garde de l'OBC comme risque R-03 pour UniSat-1.
- **Surcoût de l'EDAC** — un code de Hamming SECDED coûte environ 12,5 % pour des mots de 64 bits.
- **Règle empirique.** L'exemple d'interface I²C contre RS-422 du chapitre 8, §8.3, illustre la plupart des conflits d'interface de l'OBDH : le bus est choisi par commodité, et l'on découvre à l'intégration qu'il ne convient pas pour des raisons de bruit ou de distance.

### Écueils fréquents

> **Attention.** Les dépassements de la liste de télémesure constituent le principal défaut tardif de l'OBDH. Figez la liste à la SRR ; traitez tout ajout comme un élément soumis à la maîtrise des modifications.

> **Erreur fréquente.** Rédiger des règles FDIR qui ne sont pas testables au sol. Chaque règle du chapitre 18, §18.3, devrait avoir un cas d'essai dans la matrice de vérification (chapitre 14, §14.4).

### Références

- ECSS-E-ST-70-41C — *Telemetry and telecommand packet utilisation* (PUS) — [https://ecss.nl/](https://ecss.nl/).
- ECSS-E-ST-40C — *Software* ; ECSS-Q-ST-80C — *Software product assurance* — [https://ecss.nl/](https://ecss.nl/).
- CCSDS 133.0-B — *Space Packet Protocol* — [https://public.ccsds.org/Pubs/](https://public.ccsds.org/Pubs/).
