---
title: "Conception concourante d'engins spatiaux — Un manuel ouvert sur la conception de missions et l'ingénierie concourante"
subtitle: "Du besoin de mission aux opérations, avec des exemples résolus de CubeSats"
authors: "Franz Newland et collaborateurs"
version: "Édition REL 1.0 — 2026"
licence: "CC BY 4.0"
language: fr
toc: true
---

# Comment utiliser ce manuel

Ce manuel ouvert traite de la conception de petits engins spatiaux selon la méthode de l'ingénierie concourante — la manière dont un centre de conception concourante (CDF) conduit une mission d'un besoin exprimé jusqu'à un référentiel validé en revue, chaque sous-système étant dimensionné dans la même salle, à partir du même état de conception partagé, au même moment. Il s'adresse aux étudiantes et étudiants de dernière année de premier cycle et des cycles supérieurs ainsi qu'aux jeunes ingénieures et ingénieurs qui possèdent une formation d'ingénieur mais n'ont encore jamais conçu d'engin spatial, et à toute personne qui souhaite comprendre comment les composantes d'une mission — orbite, puissance, attitude, communications, structure, opérations, coût, réglementation — se contraignent mutuellement.

Le manuel est organisé en cinq parties, une annexe et de courtes pages de fin d'ouvrage. Les parties I à III constituent le texte principal : dix-neuf chapitres qui suivent une mission du besoin jusqu'aux opérations ; les parties IV et V sont des documents de référence à consulter au besoin.

**Partie I — Fondements et conception (chapitres 1 à 8)** pose les fondements : la méthode de conception concourante et le cadre d'ingénierie système dans lequel elle s'inscrit (chapitre 1), l'environnement réglementaire et industriel d'une mission canadienne (chapitre 2), les normes internationales qu'un projet doit appliquer (chapitre 3), les besoins de la mission, les parties prenantes, les études de compromis et le concept d'opérations (chapitre 4), les exigences (chapitre 5), la décomposition fonctionnelle (chapitre 6), le choix de l'orbite et l'environnement spatial (chapitre 7), ainsi que l'architecture de mission avec ses segments, ses interfaces et ses bilans techniques (chapitre 8).

**Partie II — Conception des sous-systèmes (chapitres 9 à 12)** dimensionne les sous-systèmes — puissance et thermique (chapitre 9), contrôle d'attitude et d'orbite (chapitre 10), communications et bilans de liaison (chapitre 11), et structures, propulsion et gestion bord des données (chapitre 12).

**Partie III — Intégration, vérification et opérations (chapitres 13 à 19)** conduit la conception à travers le choix des équipements et la nomenclature (chapitre 13), la vérification et la validation (chapitre 14), les risques, la maîtrise des interfaces et l'AMDEC (chapitre 15), l'estimation des coûts et les revues de conception (chapitre 16), le segment sol (chapitre 17), les opérations de mission et la FDIR (chapitre 18), et enfin la répétition d'une mission avant le lancement (chapitre 19).

Chaque chapitre des parties I à III suit le même schéma : une courte liste de lectures préalables conseillées, des objectifs d'apprentissage, des sections numérotées, une synthèse, une série d'exercices et une liste de références. Les exercices combinent questions conceptuelles, calculs et petites tâches de conception ; la plupart peuvent être réalisés avec une calculatrice ou un tableur, et quelques-uns vous invitent à utiliser l'outil de conception concourante de votre choix.

**Partie IV — Guide de référence des postes d'ingénierie** présente une fiche pour chacun des seize postes d'ingénierie réunis autour d'une table de CDF : les décisions qui reviennent à ce poste, ce qu'il doit savoir des autres avant de pouvoir décider, les équations et règles empiriques qu'il utilise (avec renvoi aux parties I à III plutôt que reprises), les écueils qui piègent les concepteurs débutants, et les lectures complémentaires. Lisez la fiche du poste que vous vous apprêtez à occuper, et parcourez celle d'un poste voisin.

**Partie V — Démonstrations à partir des premiers principes** établit, à partir des premiers principes, les équations que les chapitres appliquent — troisième loi de Kepler, équation de Tsiolkovski, régression nodale due au J₂, fraction d'éclipse, affaiblissement en espace libre et algèbre du bilan de liaison, courbes de taux d'erreur binaire, distance d'échantillonnage au sol, équilibre radiatif, dimensionnement du générateur solaire et de la batterie, marge de sécurité, couples perturbateurs et bouclage du volume de données quotidien —, chacune assortie d'un contrôle de vraisemblance résolu par comparaison avec une valeur publiée. Utilisez-la lorsque vous voulez savoir *pourquoi* une formule a la forme qu'elle a, ou lorsqu'un examinateur vous demande de justifier vos calculs.

**L'annexe A** décrit l'outil libre de conception concourante SpaceCDF, avec lequel les exemples numériques de ce manuel ont été calculés. **Les pages de fin d'ouvrage** contiennent une note sur la façon dont le manuel a été produit, sa licence, une mention de l'assistance par IA générative utilisée pour sa préparation, et un colophon.

### Les deux exemples fil rouge

Deux engins spatiaux reviennent tout au long du manuel, de sorte que les chapitres puissent s'appuyer sur les chiffres les uns des autres.

- **EOSat-3U** est un CubeSat 3U d'observation de la Terre en orbite héliosynchrone à 500 km, qui emporte un imageur multispectral et une liaison descendante en bande S, avec un contrôle d'attitude trois axes. C'est le principal exemple résolu des chapitres consacrés aux sous-systèmes (puissance, attitude, communications, structure) et des chapitres suivants sur les bilans, la vérification, les risques, les coûts et les opérations. Lorsqu'un chapitre parle du « CubeSat 3U d'OT », c'est de cet engin qu'il s'agit.
- **UniSat-1** est un démonstrateur technologique 1U qui emporte un magnétomètre MEMS, avec une stabilisation magnétique passive, une liaison UHF et aucune propulsion. Il est présenté au chapitre 1, §1.7, comme second exemple volontairement plus simple ; chaque chapitre suivant se termine par une courte section « Retour sur UniSat-1 » qui lui applique la méthode du chapitre. Comme UniSat-1 est assez petit pour être gardé entièrement en tête, il se prête bien aux exercices de fin de chapitre.

Les deux ne sont jamais interchangeables : les chiffres donnés pour le CubeSat 3U d'OT ne sont pas ceux d'UniSat-1, et inversement.

### Lectures préalables conseillées

Le manuel suppose une formation d'ingénieur — mécanique, électromagnétisme de base, thermodynamique élémentaire et le calcul différentiel et intégral qui les accompagne —, mais aucune expérience préalable de la conception d'engins spatiaux. Les références suivantes sont citées tout au long de l'ouvrage et méritent d'être gardées à portée de main :

- NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), §1–§3 pour le cadre d'ingénierie système. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, §3. [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- NASA, *CubeSat 101 : Basic Concepts and Processes for First-Time CubeSat Developers*. [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- Wertz, Everett et Puschell (dir.), *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011 — cité « SMAD4 » dans tout l'ouvrage.
- ECSS, les normes de la Coopération européenne pour la normalisation spatiale (*European Cooperation for Space Standardization*), en particulier ECSS-E-ST-10C (ingénierie système), ECSS-M-ST-10C (planification de projet) et ECSS-E-ST-10-02C (vérification). [https://ecss.nl/](https://ecss.nl/)
- Vallado, *Fundamentals of Astrodynamics and Applications*, 4e édition, pour la mécanique spatiale du chapitre 7 et de la partie V.

Chaque chapitre s'ouvre sur une liste plus courte, propre à son sujet.

### Comment les exemples numériques ont été produits

Chaque exemple numérique résolu de ce manuel — les bilans d'EOSat-3U et d'UniSat-1, les durées orbitales, les bouclages de bilans de liaison, les cas thermiques, les consolidations de coûts — a été calculé avec l'outil libre SpaceCDF décrit à l'annexe A, à partir de descripteurs de mission publiés avec l'outil, puis vérifié à la main à l'aide des équations données dans le texte et démontrées dans la partie V. Les figures sont générées de manière procédurale par des scripts conservés avec les sources du manuel, de sorte qu'une figure puisse être régénérée lorsqu'une valeur change. Lorsque les éditeurs de la présente édition ont trouvé et corrigé une erreur de calcul dans une version antérieure, la valeur corrigée est utilisée de manière cohérente dans chaque chapitre qui la cite. Les lecteurs qui souhaitent reproduire ou prolonger un exemple trouveront les détails dans les pages de fin d'ouvrage.

### Conventions

Le manuel utilise les unités SI, l'orthographe française traditionnelle et, dans tout l'ouvrage, les constantes $R_E = 6378.137$ km, $\mu = 398\,600.44$ km³/s², $J_2 = 1.0826 \times 10^{-3}$, $g_0 = 9.80665$ m/s² et $k = -228.6$ dBW/K/Hz (la partie V, V.1, en donne la liste complète avec leurs sources). Les méthodes de vérification sont abrégées ATIR(D) — analyse (*Analysis*), essai (*Test*), inspection (*Inspection*), revue de conception (*Review of design*) et, lorsqu'elle est employée, démonstration (*Demonstration*). Les produits commerciaux cités dans les exemples résolus sont des exemples représentatifs et non des recommandations, et les prix indiqués sont donnés à titre indicatif pour 2026. Les intitulés de postes désignent des fonctions et s'appliquent indifféremment à toutes et à tous.
