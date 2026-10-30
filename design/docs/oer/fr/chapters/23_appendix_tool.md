# Annexe A — À propos de l'outil SpaceCDF

Les exemples numériques de ce manuel ont été calculés avec SpaceCDF, un outil libre de conception concourante pour petits engins spatiaux. Cette annexe le décrit brièvement et de façon neutre, afin que le lecteur puisse comprendre ce qui a produit les chiffres, et les reproduire ou les prolonger. L'outil est distribué sous licence MIT ; le code source, les descripteurs de mission utilisés pour les exemples de ce manuel et les scripts de génération des figures sont disponibles à l'adresse <https://github.com/FNewland/SpaceCDF>. Rien dans les parties I–III ne dépend de l'outil : toutes les méthodes du manuel peuvent être appliquées avec un tableur, et les exercices ne l'exigent jamais.

## A.1 Postes et agents de conception

Deux notions distinctes traversent une étude de conception concourante, et on les confond parfois. Il est indispensable de les distinguer avant la première boucle de conception.

Un **poste** est un *rôle humain* attribué à une personne installée à une console d'un centre de conception concourante — l'ingénieur puissance, l'ingénieur SCAO, l'analyste de mission, etc. L'outil définit les seize postes du tableau 1.4 du chapitre 1, chacun disposant de droits de modification limités à un sous-ensemble des paramètres de conception ; la partie IV présente une fiche pour chacun.

Un **agent de conception** est un *solveur de calcul* qui s'exécute en arrière-plan et fait converger un sous-système ou une analyse donnés. Les agents sont répartis en deux niveaux :

| Niveau | Rôle | Agents |
|---|---|---|
| Niveau 1 — Dimensionnement paramétrique | Calculer le point de conception d'un sous-système à partir des données d'entrée fournies par les autres | orbite · liaison · données · puissance · thermique · SCAO · propulsion · masse · structure |
| Niveau 2 — Analyse transverse | Noter, vérifier ou auditer la conception convergée | coût · risque · fiabilité · débris · rayonnement · durabilité · volume · systèmes · conflits · communauté · TRL |

Les agents de niveau 1 mettent en œuvre les chaînes de dimensionnement des chapitres 7–12 — l'agent orbite la période, l'éclipse et la géométrie des passages du chapitre 7, l'agent puissance la chaîne générateur solaire–batterie du chapitre 9, l'agent liaison le bilan du chapitre 11, et ainsi de suite —, avec les mêmes équations et les mêmes constantes que le texte. Les agents de niveau 2 mettent en œuvre les vérifications des chapitres 3, 8 et 13–16 : le calendrier de marges du tableau 8.3, les règles relatives aux débris, le cumul des TRL, l'estimation des coûts et le registre des risques.

Chaque agent publie trois éléments dans l'état de conception partagé lorsqu'il s'exécute : ses **paramètres** (des valeurs avec unités, marge et niveau de confiance), sa **justification** (un court paragraphe de raisonnement dans les termes du chapitre concerné) et un ensemble d'**hypothèses** que les agents en aval et les examinateurs peuvent interroger. Plusieurs agents produisent aussi des résultats intermédiaires structurés — l'agent orbite une décomposition du Δv, l'agent liaison une cascade complète, l'agent thermique les températures des nœuds en cas chaud et en cas froid, l'agent fiabilité une AMDEC —, et les exports présentent ces résultats sous forme de tableaux et de figures, à côté des valeurs brutes.

## A.2 La boucle de conception et le transfert entre humains et agents

Une boucle de conception exécute chaque agent une fois, dans l'ordre des dépendances, à partir de l'état de conception courant. Comme chaque agent lit les sorties des autres, plusieurs boucles sont nécessaires avant que l'état ne cesse d'évoluer ; c'est l'analogue calculatoire des itérations de conception décrites au chapitre 1, §1.1.

Lorsqu'un poste humain modifie une valeur, ce paramètre devient *verrouillé* dans l'état de conception et les agents ne l'écrasent plus lors des boucles suivantes. C'est le transfert formel entre l'opérateur humain et le solveur de calcul, et c'est la raison pour laquelle une étude de conception concourante converge rapidement : les agents se chargent de l'arithmétique itérative tandis que les postes exercent le jugement d'ingénieur. Une valeur verrouillée est aussi une décision consignée, avec un responsable, ce qu'un examinateur demandera.

## A.3 Revues et exports

Un jalon de revue n'est pas qu'une réunion. C'est un ensemble documentaire dont l'existence et le contenu sont convenus à l'avance, dont la production est traçable jusqu'à un état de conception convergé, et dont l'acceptation fait passer le projet d'une phase du cycle de vie à la suivante (tableau 1.3 du chapitre 1 ; chapitre 16, §16.5–§16.6). L'outil traite chaque jalon comme le point d'ancrage d'un lot d'exports : à chaque jalon, il exporte un dossier de revue de conception contenant les bilans avec leurs marges, les figures d'orbite et d'architecture, la matrice de conformité, la liste des équipements, le cumul des TRL, la matrice des risques, la courbe en S des coûts et l'organigramme des tâches, le contenu s'enrichissant de la revue de concept à la revue de définition critique comme le laissent attendre les chapitres des parties I–III — comptes rendus d'études de compromis et matrice de vérification à partir de la revue de définition préliminaire, plan d'essais et état de qualification à la revue de définition critique.

Outre les dossiers de revue, l'outil génère une famille de descriptions d'éléments de données sous forme modifiable : document d'exigences de mission, concept d'opérations, plan de vérification, plan de management de l'ingénierie système, plan de gestion des risques, document d'exigences d'interface, plan d'essais et nomenclature. Des rapports spécialisés couvrent l'analyse thermique, le plan de désorbitation en fin de vie, la demande de licence de télédétection et le programme d'essais de vérification. Les figures de ces exports sont tracées par les mêmes scripts, avec les mêmes conventions, que les figures de ce manuel, de sorte qu'un lecteur qui a rencontré une cascade de bilan de liaison au chapitre 11 reconnaîtra celle d'un dossier de revue exporté.

## A.4 Reproduire les exemples de ce manuel

Chaque exemple fil rouge (EOSat-3U et UniSat-1) est décrit par un fichier descripteur de mission distribué avec l'outil. Exécuter la boucle de conception sur un descripteur reproduit les bilans cités dans les chapitres correspondants ; les exemples résolus du texte montrent ensuite les mêmes chiffres obtenus à la main à partir des équations des parties I–III et de la partie V, ce qui constitue la vérification croisée que la partie V, §V.16, recommande pour toute revue de conception. Si un agent est mis à jour et qu'un résultat d'exemple résolu change, le texte peut être confronté à la sortie de l'outil et corrigé en un seul endroit.
