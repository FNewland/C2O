# Chapitre 16 — Estimation des coûts et revues de conception

> **Lectures préalables conseillées.** NASA *Cost Estimating Handbook* v4.0 (annexe C, relations d'estimation de coût) ; SMAD4, chapitre 20 (coût) ; NPR 7120.5F (organigrammes des tâches) ; ECSS-M-ST-60C (*Cost and schedule management*) ; ECSS-M-ST-10C Rev. 1, §6, et NPR 7123.1D, annexe G (revues). Ce chapitre s'appuie sur la nomenclature et les coûts non récurrents du chapitre 13, sur la matrice de vérification du chapitre 14 et sur le registre des risques du chapitre 15 ; les jalons de revue eux-mêmes sont définis dans le tableau 1.3 du chapitre 1.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. estimer le coût d'une mission par les méthodes paramétrique (CER), analogique et ascendante, et indiquer la précision de chacune ;
2. établir l'organigramme des tâches (WBS) d'un projet CubeSat et répartir les coûts entre les phases du cycle de vie ;
3. appliquer les effets de la courbe d'apprentissage à l'estimation des coûts d'une constellation ;
4. exprimer le risque de coût sous forme de distribution et annoncer des niveaux de confiance P50/P70/P80 ;
5. préparer une revue de conception (SRR/PDR/CDR) au regard de critères de jalon explicites ;
6. présenter clairement les éléments probants de la conception, répondre aux questions du comité de revue et siéger vous-même dans un comité de revue.

Les produits de fournisseurs cités dans ce chapitre sont des exemples représentatifs et non des recommandations ; les prix sont donnés à titre indicatif (2026), sauf mention d'un exercice budgétaire.

---

## 16.1 Méthodes d'estimation des coûts

*[Source : NASA CEH v4.0, annexe C ; SMAD4, chapitre 20 ; Aerospace Corp SSCM]*
*[URL : https://www.nasa.gov/offices/ocfo/references-and-tools/ (NASA CEH)]*

Le coût est un bilan d'ingénierie au même titre que la masse ou la puissance : il a une meilleure estimation courante, une marge et une allocation, et il doit être bouclé. La différence est que le coût ne se mesure pas sur un banc : il est *estimé*, et la qualité de l'estimation dépend de la part de la conception qui existe au moment où l'estimation est faite.

### 16.1.1 Trois méthodes principales

| Méthode | Description | Précision (1σ) | Quand l'utiliser | Données nécessaires |
|--------|-------------|---------------|-------------|---------------|
| **Paramétrique** | Relations d'estimation de coût (CER) ajustées sur une base de données historique | ± 30–50 % | Phase 0/A (peu de détails connus) | Masse, puissance, type de mission |
| **Analogique** | Comparaison avec une mission passée similaire, ajustée des différences | ± 20–40 % | Phase A/B (mission de référence disponible) | Connaissance détaillée de la référence |
| **Ascendante** | Somme des devis fournisseurs + estimations de main-d'œuvre + installations | ± 10–20 % | Phase B/C (conception détaillée) | Nomenclature, devis fournisseurs, taux horaires |

Les trois méthodes ne sont pas des solutions concurrentes mais une séquence : l'estimation se resserre à mesure que le cycle de vie progresse, d'une fourchette paramétrique à la revue du concept de mission jusqu'à un chiffre ascendant à la CDR. La figure 16.1 montre cet entonnoir : la bande d'incertitude se resserre de ± 50 % à ± 10 % à mesure que la méthode d'estimation évolue avec la maturité de la conception.

![Bande de précision de l'estimation des coûts se resserrant de la méthode paramétrique à la méthode ascendante](../assets/figures/fig_cost_funnel.png)

**Figure 16.1** — Précision de l'estimation des coûts en fonction de la phase du cycle de vie. La bande ± 1σ autour de l'estimation ponctuelle se resserre d'environ ± 50 % à la revue du concept de mission à environ ± 10 % à la CDR, à mesure que la méthode d'estimation passe de la méthode paramétrique (phase 0/A) à la méthode analogique (A/B), puis à la méthode ascendante (B/C/D) ; les jalons de revue du tableau 1.3 du chapitre 1 sont repérés sur l'axe des phases.

### 16.1.2 Relations d'estimation de coût paramétriques (CER)

Les CER expriment le coût en fonction de paramètres techniques ; elles sont obtenues par analyse de régression de données historiques. Leur forme générale est

$$C = a \, M^{\,b} \, f_{\text{complexity}}$$

où $a$ est le coefficient de régression, $M$ le paramètre déterminant (généralement la masse sèche en kg, parfois la puissance en W ou le débit de données), $b$ l'exposant (généralement 0,5–1,0, de sorte que le coût croît moins vite que la masse) et $f_{\text{complexity}}$ un ajustement tenant compte de la difficulté de la mission. Une CER ne vaut que ce que vaut la base de données qui la sous-tend : elle ne doit pas être utilisée en dehors de la plage de masses et de technologies des missions sur lesquelles elle a été ajustée.

### 16.1.3 CER de l'USCM (Unmanned Space Vehicle Cost Model)

*[Source : SMAD4, tableau 20-8 ; base de données USCM de l'US Air Force]*

| Sous-système | CER (FY2010 \$K) | Paramètre | $b$ type |
|-----------|-----------------|-----------|-------------|
| Structure | $157\,M_{\text{struct}}^{0.83}$ | Masse sèche (kg) | 0,83 |
| Thermique | $394\,M_{\text{therm}}^{0.635}$ | Masse sèche (kg) | 0,635 |
| EPS | $62.7\,M_{\text{EPS}}^{1.00}$ | Masse sèche (kg) | 1,00 |
| TT&C | $545\,M_{\text{TTC}}^{0.761}$ | Masse sèche (kg) | 0,761 |
| AOCS | $464\,M_{\text{AOCS}}^{0.867}$ | Masse sèche (kg) | 0,867 |
| Propulsion | $17.8\,M_{\text{prop}}^{0.75}$ | Masse sèche (kg) | 0,75 |
| Intégration et essais | $10.4\,M_{\text{dry}}^{0.907}$ | Masse sèche totale (kg) | 0,907 |
| Gestion de programme | 12,3 % du coût du matériel | — | — |
| Ingénierie système | 14,2 % du coût du matériel | — | — |

### 16.1.4 SSCM (Small Satellite Cost Model)

Le SSCM de l'Aerospace Corporation a été spécifiquement calibré pour les satellites de moins de 500 kg. Il fournit des estimations plus précises que l'USCM pour les CubeSats.

*[Source : Aerospace Corp, « Small Satellite Cost Model (SSCM) », disponible par l'intermédiaire d'Aerospace TOR]*

**Principaux ajustements du SSCM pour les CubeSats :**
- les coûts du matériel COTS sont des prix catalogue, et non des CER fondées sur la masse ;
- les coûts de main-d'œuvre dominent pour les projets universitaires ou de petites équipes ;
- les NRE dépendent fortement du caractère unique de la mission (le chapitre 13, §13.1.3, donne l'équation des NRE) ;
- les CER standard (conçues pour plus de 100 kg) surestiment d'un facteur 2 à 6 pour la classe nano/micro.

### 16.1.5 Prix adaptés aux CubeSats : prix forfaitaires des COTS ou CER

Une approche hybride pragmatique utilise les prix forfaitaires des COTS pour la classe nano/micro et les CER pour les engins spatiaux plus gros. La comparaison ci-dessous montre pourquoi : pour des sous-systèmes de la masse d'un CubeSat, la CER est évaluée bien en dessous de la plage de masses sur laquelle elle a été ajustée, et l'ajustement n'est plus valable.

| Sous-système | Coût COTS CubeSat (k€) | CER USCM (k€, pour la masse d'un CubeSat) | Rapport |
|-----------|--------------------------|-----------------------------------|-------|
| EPS | 15 | 60 | CER 4 fois plus élevée |
| AOCS (fin) | 40 | 66 | CER 1,6 fois plus élevée |
| TT&C (bande S) | 20 | 25 | Comparable |
| OBC | 10 | 12 | Comparable |
| Structure | 8 | 3 | CER plus basse (effet de commande minimale) |
| Charge utile | 50 (variable) | 300 | CER 6 fois plus élevée pour les charges utiles COTS |

*Cela confirme que, pour les CubeSats, les prix des COTS sont plus fiables que les CER paramétriques pour le coût du matériel.*

### 16.1.6 Exemple résolu : estimation paramétrique ou ascendante pour le CubeSat 3U d'observation de la Terre

*EOSat-3U, mission 3U d'observation de la Terre (fournisseurs représentatifs, prix indicatifs 2026) :*

| Élément du WBS | Paramétrique (k€) | Ascendante (k€) | Remarques |
|-------------|-------------------|-------------------|-------|
| Structure | 8 | 8,5 | Structure 3U d'ISIS |
| EPS | 18 | 16,2 | GomSpace P31u + générateur solaire |
| OBC | 12 | 10,0 | NanoAvionics SatBus |
| AOCS | 45 | 42,0 | BCT XACT-15 |
| TT&C | 22 | 20,5 | Endurosat bande S |
| Thermique | 5 | 3,0 | Passif uniquement |
| Charge utile | 65 | 58,0 | Simera Sense xScape |
| Faisceau | 3 | 2,5 | Câbles spécifiques |
| **Sous-total matériel** | **178** | **160,7** | |
| Intégration et essais (12 %) | 21 | 19,3 | |
| Logiciel (8 %) | 14 | 12,9 | |
| Gestion de projet / IS / AM (13 %) | 23 | 20,9 | |
| Lancement | 200 | 195,0 | Lancement partagé |
| Sol (5 %) | 9 | 8,0 | Réseau bénévole + station dédiée |
| Opérations (3 ans) | 45 | 40,0 | 0,5 ETP |
| **TOTAL** | **490** | **456,8** | |

*L'estimation paramétrique est supérieure d'environ 7 % à l'estimation ascendante. C'est attendu : l'estimation paramétrique intègre une incertitude et une provision pour aléas inhérentes.* Le total d'environ 490 k€ est le chiffre repris au chapitre 13, §13.6, pour la comparaison entre 1U et 3U.

---

## 16.2 Structure de ventilation des coûts (WBS)

L'organigramme des tâches (WBS) est la décomposition hiérarchique de l'ensemble des travaux nécessaires à la réalisation de la mission. C'est le socle de l'estimation des coûts, de la planification et de la gestion : chaque euro et chaque heure sont imputés à un seul élément du WBS, de sorte que rien n'est compté deux fois et que rien n'est oublié.

*[Source : NPR 7120.5F, annexe G ; ECSS-M-ST-60C ; NASA CEH v4.0, annexe B]*

### 16.2.1 WBS type d'un CubeSat

```
WBS niveau 1 : total mission
  1.0  Management de programme              5 %   (pilotage, revues, comptes rendus)
  2.0  Ingénierie système                   5 %   (bilans, interfaces, études de compromis)
  3.0  Assurance mission                    3 %   (qualité, fiabilité, composants)
  4.0  Charge utile                        20 %   (instrument + étalonnage)
    4.1  Matériel de l'instrument charge utile
    4.2  Logiciel charge utile
    4.3  Étalonnage et caractérisation de la charge utile
  5.0  Matériel de la plateforme           30 %   (tous les sous-systèmes)
    5.1  Structure et mécanismes
    5.2  EPS (générateur solaire + batterie + carte)
    5.3  AOCS (capteurs + actionneurs)
    5.4  TT&C (transpondeur + antenne)
    5.5  OBC et traitement des données
    5.6  Contrôle thermique
    5.7  Propulsion (le cas échéant)
    5.8  Harnais et câblage
  6.0  Intégration et essais               12 %   (assemblage, essais d'environnement)
    6.1  Assemblage et intégration
    6.2  Campagne d'essais d'environnement
    6.3  Location des moyens d'essai
  7.0  Logiciel (bord + sol)                8 %   (FSW, GSW, planification de mission)
    7.1  Logiciel de vol
    7.2  Logiciel du segment sol
    7.3  Outils de planification de mission
  8.0  Services de lancement               10 %   (lanceur, déployeur, intégration)
  9.0  Segment sol                          5 %   (antennes, MCS, réseaux)
  10.0 Opérations (durée de vie mission)    5 %   (personnel, consommables, maintenance)
```

![Arborescence type du WBS d'un CubeSat](../assets/figures/fig_wbs_tree.png)

**Figure 16.2** — L'organigramme des tâches type d'un CubeSat sous forme d'arbre : le total de la mission se ramifie en dix éléments de niveau 1, chacun avec sa part type du coût total, et l'élément 5.0 (matériel de la plateforme) est développé en ses huit éléments de niveau 2. Les couleurs regroupent les éléments en gestion (1–3), segment spatial (4–6), logiciel (7), lancement (8), et sol et opérations (9–10).

Les pourcentages (figure 16.2) sont typiques d'un CubeSat universitaire ou de petite entreprise et constituent une allocation de départ, non une loi : une mission dotée d'une charge utile spécifique poussera l'élément 4.0 vers 35 %, et une mission dont la plateforme est achetée clés en main fusionnera 5.0 et 6.0 en une seule ligne d'approvisionnement.

### 16.2.2 Coûts par phase

La répartition des coûts entre les phases du cycle de vie importe pour l'établissement du budget et pour la trésorerie :

| Phase | % du total | Activités | Niveau maximal d'effectifs |
|-------|-----------|-----------|---------------|
| 0/A (concept) | 5–10 % | Études, études de compromis, exigences | Faible |
| B (définition préliminaire) | 15–20 % | PDR, analyses détaillées, approvisionnements à long délai | En hausse |
| C (définition détaillée) | 30–40 % | CDR, fabrication, développement logiciel | Maximal |
| D (intégration et essais) | 20–25 % | Assemblage, essais d'environnement, recette en orbite | Élevé |
| E (exploitation) | 10–20 % | Opérations de routine, gestion des anomalies | Faible et stable |
| F (retrait de service) | 1–3 % | Mise hors service, désorbitation | Minimal |

---

## 16.3 Courbe d'apprentissage pour les constellations

*[Source : SMAD4, §20.3 ; théorie de la courbe d'apprentissage de Wright (1936)]*

Lorsque l'on construit plusieurs unités identiques, le coût unitaire diminue grâce à une fabrication plus efficace, à des essais plus courts, aux achats en volume et à l'apprentissage de la main-d'œuvre. Le chapitre 4, §4.6.4, a utilisé la forme cumulée de cet effet pour dimensionner le budget d'une constellation ; nous développons ici la forme unitaire sur laquelle elle repose.

### 16.3.1 Courbe d'apprentissage de Wright

Le coût (ou le temps de main-d'œuvre) de la $n$-ième unité est

$$T_n = T_1 \, n^{\log_2 L}$$

où $T_1$ est le coût de la première unité, $L$ le *taux d'apprentissage* (0,90 pour une « courbe à 90 % ») et l'exposant $b = \log_2 L = \ln L / \ln 2$ est négatif. En écrivant explicitement le coût, $C_n = C_1\, n^{b}$ :

| Taux d'apprentissage $L$ | $b = \log_2 L$ | Coût de la 10e unité (% de la 1re) |
|--------------|-----|-----|
| 95 % | −0,074 | 84 % |
| 90 % | −0,152 | 70 % |
| 85 % | −0,234 | 58 % |

Le coût total de $N$ unités est la somme cumulée, qui est la forme utilisée au chapitre 4 :

$$C_{\text{total}} = C_1 \sum_{i=1}^{N} i^{\log_2 L}
\;\approx\; C_1\,\frac{N^{\,1+b}}{1+b} \quad\text{(approximation continue)}$$

L'approximation continue surestime la somme de quelques pour cent pour de petites valeurs de $N$ ; utilisez la somme exacte lorsque $N < 10$.

### 16.3.2 Règle empirique simplifiée

> Avec un **taux d'apprentissage de 90 %**, chaque fois que vous **doublez** le nombre d'unités, le coût unitaire baisse de **10 %** :
>
> Unité 1 : 800 k€ · unité 2 : 720 k€ · unité 4 : 648 k€ · unité 8 : 583 k€ · unité 16 : 525 k€

### 16.3.3 Exemple résolu : constellation de 20 satellites

*Coût de la première unité (plateforme + charge utile + intégration et essais) : 800 k€. Taux d'apprentissage : 90 % ($b = -0.152$). Les totaux utilisent la somme cumulée exacte.*

| Unités $N$ | $\sum_{i=1}^{N} i^{b}$ | Coût unitaire moyen | Matériel total | Calcul |
|-------|---|--------------|----------------|------|
| 1 | 1,000 | 800 k€ | 800 k€ | Première unité |
| 5 | 4,34 | 694 k€ | 3470 k€ | $800 \times 4.34$ |
| 10 | 8,00 | 640 k€ | 6400 k€ | $800 \times 8.00$ |
| 20 | 14,61 | 584 k€ | 11 690 k€ | $800 \times 14.61$ (l'approximation continue donne 11 960 k) |

Estimation totale pour la constellation :
- matériel des 20 satellites : 11,7 M€ ;
- 2 unités de rechange (construites comme unités 21–22 à ≈ 0,63 × 800 k chacune) : 1,0 M€ ;
- lancement (20 satellites × 200 k€ en lancement partagé) : 4,0 M€ ;
- segment sol : 1,0 M€ ;
- opérations (3 ans) : 0,9 M€ ;
- gestion de projet / IS / AM (10 % de ce qui précède) : 1,9 M€ ;
- **total : ≈ 20,5 M€.**

Sans la courbe d'apprentissage, les 22 unités coûteraient à elles seules 17,6 M€ ; la courbe permet d'économiser environ 4,9 M€, ce qui constitue l'argument économique en faveur d'une constellation plutôt que d'une série d'exemplaires uniques.

---

## 16.4 Risque sur les coûts et niveaux de confiance

Les estimations ponctuelles sont trompeuses. Toute estimation de coût comporte une incertitude, et la pratique courante consiste à exprimer le coût sous forme de distribution de probabilité plutôt que par un chiffre unique.

*[Source : NASA CEH v4.0, §2.3 ; pratique d'estimation paramétrique du JPL]*

### 16.4.1 Incertitude par élément de coût

| Élément de coût | Distribution | Incertitude (1σ) | Justification |
|-------------|-------------|----------------------|-----------|
| Matériel COTS | Normale | ± 10 % | Prix connus d'après les devis fournisseurs |
| Matériel spécifique | Log-normale | ± 30 % | L'incertitude de développement tire vers le haut |
| Logiciel | Triangulaire | ± 40 % | Le plus difficile à estimer ; dépassements fréquents |
| Lancement | Normale | ± 15 % | Prix publiés ; négociation contractuelle |
| Opérations | Uniforme | ± 25 % | Incertitude sur le niveau d'effectifs |
| Intégration et essais | Log-normale | ± 25 % | Les anomalies d'essai entraînent des dérives de délais et de coûts |

Une distribution est attribuée à chaque élément du WBS ; une simulation de Monte-Carlo effectue des tirages dans chacune d'elles et en fait la somme, ce qui produit une distribution du coût total. Sa forme cumulée est la **courbe en S** de la figure 16.3 — la probabilité que la mission ne coûte pas plus qu'un montant donné —, sur laquelle on lit les niveaux de confiance. Les éléments log-normaux et triangulaires étant asymétriques à droite, l'estimation ponctuelle (meilleure estimation courante) se situe à *gauche* de P50 : une estimation à chiffre unique a plus de chances d'être dépassée que tenue.

![Courbe en S des coûts avec P50, P70 et P80 repérés](../assets/figures/fig_cost_scurve.png)

**Figure 16.3** — Courbe en S des coûts et niveaux de confiance pour l'estimation ascendante d'EOSat-3U du §16.1.6 (456,8 k€), issue d'une simulation de Monte-Carlo de 200 000 tirages dans laquelle chaque élément de coût suit la distribution du tableau ci-dessus et les éléments sont indépendants. On obtient P50 ≈ 459 k€, P70 ≈ 479 k€ et P80 ≈ 491 k€ ; l'estimation ponctuelle se situe vers P47, légèrement à gauche de P50, parce que les éléments « charge utile spécifique » et « intégration » sont asymétriques à droite, et la réserve entre P50 et P80 est d'environ 31 k€ (7 %).

Pour cette mission majoritairement en COTS, dont l'élément le plus important est un lancement à prix ferme, le tableau par élément donne P80 ≈ 1,07 × P50 — bien en dessous de la règle empirique de 1,3 du §16.4.2. L'écart est voulu : la règle empirique couvre aussi la croissance corrélée, au niveau du programme, que les distributions par élément ne saisissent pas (modifications d'exigences, glissement de calendrier qui se répercute sur chaque ligne de main-d'œuvre, charge utile qui s'avère nécessiter une seconde itération). C'est pourquoi le *NASA Cost Estimating Handbook* exige que la corrélation entre éléments soit modélisée dans une analyse de confiance conjointe coûts-délais, et pourquoi la règle empirique reste le meilleur chiffre de planification en phase A.

### 16.4.2 Niveaux de confiance

| Percentile | Signification | Utilisation |
|-----------|---------|-----|
| **P50** | Probabilité de 50 % que le coût soit inférieur ou égal à cette valeur | Référentiel du projet ; coût « attendu » |
| **P70** | Probabilité de 70 % | Niveau d'engagement standard de la NASA (NPR 7120.5F) |
| **P80** | Probabilité de 80 % | Planification prudente ; habituel pour les propositions |

> **Règle empirique pour les missions CubeSat :**
>
> $$P_{70} \approx 1.2\,P_{50}, \qquad P_{80} \approx 1.3\,P_{50}$$
>
> Exemple : si $P_{50} =$ 500 k€, alors $P_{80} \approx$ 650 k€.
>
> *Cette approximation suppose une complexité modérée et un matériel COTS bien maîtrisé. Pour les missions comportant des charges utiles spécifiques ou des technologies nouvelles, utilisez $P_{80} \approx 1.5\,P_{50}$.*

L'écart entre P50 et le niveau d'engagement constitue la **réserve pour coûts**. Elle appartient au chef de projet, et non aux responsables de sous-système, et elle est débloquée au regard du registre des risques du chapitre 15 : un risque qui se concrétise puise dans la réserve ; un risque levé lui restitue sa part.

### 16.4.3 Retour sur UniSat-1 : structure des coûts

**Un WBS simple, majoritairement en COTS.** La structure des coûts d'UniSat-1 diffère fondamentalement de celle des missions plus importantes, car (a) la quasi-totalité du matériel est en COTS, de sorte que les NRE sont quasi nuls, et (b) l'équipe est petite et universitaire, de sorte que les coûts de main-d'œuvre sont faibles. Le chapitre 13, §13.6, a donné la synthèse des coûts fondée sur la nomenclature (≈ 85 k€, sans les opérations et avec une seule ligne de gestion de programme ; l'estimation par WBS ci-dessous ajoute ces deux postes et atteint ≈ 91 k€) ; la même mission est ici estimée par les deux méthodes selon le WBS du §16.2.1, puis portée à un chiffre P80.

> **Estimation des coûts d'UniSat-1 par élément du WBS (paramétrique ou ascendante ; indicatif 2026) :**
>
> | Élément du WBS | Paramétrique (k€) | Ascendante (k€) | Remarques |
> |-------------|-------------------|-------------------|-------|
> | 1.0 Gestion de programme | 4 | 5 | Encadrement par le corps enseignant, 0,1 ETP × 12 mois |
> | 2.0 Ingénierie système | 3 | 3 | Chef d'équipe |
> | 3.0 Assurance mission | 1 | 1 | AQ minimale pour une mission universitaire |
> | 4.0 Charge utile | 8 | 8 | Circuit imprimé du capteur MEMS + étalonnage |
> | 5.0 Matériel de la plateforme | 39 | 38 | Nomenclature du chapitre 13, §13.6 |
> |   5.1 Structure | 4 | 4 | Structure 1U |
> |   5.2 EPS + générateur solaire | 20 | 19,5 | Carte EPS + cellules fixées sur la structure |
> |   5.3 AOCS (passif) | 1 | 1 | Aimant + barreaux d'hystérésis |
> |   5.4 Communications (UHF) | 11 | 10,5 | Émetteur-récepteur + antenne |
> |   5.5 OBC | 3 | 3 | Carte Cortex-M spécifique |
> | 6.0 Intégration et essais | 8 | 8 | Salle blanche universitaire + moyen d'essai de vibrations |
> | 7.0 Logiciel | 5 | 5 | Logiciel de vol (RTOS) + logiciel sol |
> | 8.0 Lancement | 15 | 15 | Déploiement 1U depuis l'ISS |
> | 9.0 Segment sol | 5 | 5 | Antenne Yagi + réseau bénévole |
> | 10.0 Opérations (6 mois) | 3 | 3 | Opérateurs étudiants, 0,2 ETP |
> | **TOTAL (P50)** | **≈ 91** | **≈ 91** | |
> | **P80 (× 1,3)** | **≈ 118** | **≈ 118** | Estimation prudente |

**Principaux constats sur les coûts des missions 1U :**

1. **Le matériel est bon marché.** Le coût total du matériel COTS est de ≈ 36–44 k€, soit moins qu'un seul senseur stellaire pour une mission 3U.
2. **Les NRE sont minimes.** Seuls l'OBC et la charge utile nécessitent un développement spécifique. Les NRE sont estimés à ≈ 8 k€ (étalonnage de la charge utile + routage de la carte OBC), contre ≈ 50–150 k€ pour des charges utiles spécifiques sur des missions plus importantes.
3. **Le coût du lancement est proportionnellement élevé.** À 15 k€, le lancement représente ≈ 18 % du coût total. Pour une mission 3U dont le lancement coûte ≈ 200 k€, il représente ≈ 40 % du total. Le coût de lancement d'un 1U est faible en valeur absolue, mais reste une fraction importante.
4. **La main-d'œuvre domine.** Pour une équipe universitaire, la main-d'œuvre étudiante « gratuite » est le coût caché. Si les étudiants étaient rémunérés au tarif professionnel (≈ 50 €/h), le coût total de la main-d'œuvre serait de ≈ 100–200 k€, bien au-delà du coût du matériel. C'est typique des missions pédagogiques.
5. **Aucun facteur de coût lié à la complexité.** Pas de développement de logiciel SCAO, pas de qualification de mécanisme déployable, pas d'intégration de propulsion, pas d'essai en vide thermique des réchauffeurs — autant de postes qui ajoutent chacun 10–50 k€ sur une mission 3U.

**Applicabilité de la courbe d'apprentissage.** Si une université construit une série de démonstrateurs 1U (UniSat-1, UniSat-2, UniSat-3…), un taux d'apprentissage de 90 % s'applique au matériel et à la main-d'œuvre récurrente (logiciel, étalonnage, intégration et essais, gestion ≈ 21 k€), tandis que le lancement (15 k€) et le segment sol (5 k€) sont fixes :

| Unité | Coût du matériel (k€) | Coût total (k€) |
|------|---------------------|-------------------|
| UniSat-1 | 44 | 85 |
| UniSat-2 | 40 | 79 |
| UniSat-4 | 36 | 73 |
| UniSat-8 | 32 | 67 |

Le plancher asymptotique est dominé par le coût du lancement (15 k€) et par les coûts incompressibles du segment sol et des opérations (≈ 8 k€), ce qui donne un coût de mission minimal de ≈ 40–50 k€ pour des constructions répétées.

---

## 16.5 Revues de conception : critères de jalon et présentation

Les revues de conception sont des jalons de décision formels au cours desquels le projet démontre qu'il est prêt à passer à la phase suivante du cycle de vie. La séquence des jalons — MCR, SDR, SRR, PDR, CDR, TRR, QR, FRR — et la question clé à laquelle répond chacun d'eux sont données dans le tableau 1.3 du chapitre 1 et ne sont pas reprises ici. La présente section traite de ce qu'une revue *contrôle* et de la manière d'y présenter.

*[Source : NPR 7123.1D, annexe G ; ECSS-M-ST-10C Rev. 1, §6 ; NASA SEH Rev 2, §3.7]*
*[URL : https://www.nasa.gov/reference/systems-engineering-handbook/]*

### 16.5.1 Critères de jalon de la SRR (phase A → B)

| N° | Critère | Priorité | Éléments probants |
|---|-----------|----------|----------|
| 1 | Toutes les exigences de niveau 0/1 figées dans le référentiel | Obligatoire | Document d'exigences signé (chapitre 5) |
| 2 | ConOps défini (toutes les phases de la mission) | Obligatoire | Document de ConOps (chapitre 4, chapitre 18) |
| 3 | Études de compromis d'architecture de mission achevées | Obligatoire | Rapports d'études de compromis avec justification (chapitre 4, §4.6) |
| 4 | Faisabilité confirmée (tous les bilans positifs) | Obligatoire | Bilans de masse, de puissance et de liaison avec marges (chapitre 8) |
| 5 | Registre des risques établi, avec mesures de réduction | Obligatoire | Registre des risques avec indices et plans (chapitre 15) |
| 6 | Approche préliminaire de V&V définie | Souhaitable | Matrice de vérification avec méthodes ATIR(D) attribuées (chapitre 14) |
| 7 | Calendrier et estimation des coûts (P50/P80) | Obligatoire | Estimation des coûts avec WBS (§16.2, §16.4) |
| 8 | Exigences d'interface identifiées | Souhaitable | Matrice N² ou ébauche d'ICD (chapitre 8, §8.3) |

### 16.5.2 Critères de jalon de la PDR (phase B → C)

| N° | Critère | Priorité | Éléments probants |
|---|-----------|----------|----------|
| 1 | Toutes les exigences allouées aux sous-systèmes | Obligatoire | Matrice d'allocation des exigences (chapitre 6) |
| 2 | Définition préliminaire achevée pour tous les sous-systèmes | Obligatoire | Documents de conception, schémas fonctionnels (chapitres 9 à 12) |
| 3 | Tous les bilans bouclent avec une marge ≥ 20 % | Obligatoire | Bilans de masse, de puissance, de liaison, de données et de pointage (tableau 8.3 du chapitre 8 pour le barème des marges) |
| 4 | Équipements sélectionnés (nomenclature) | Obligatoire | Nomenclature avec TRL, héritage, coût et délai d'approvisionnement (chapitre 13) |
| 5 | Toutes les interfaces définies (matrice N²) | Obligatoire | Documents de contrôle d'interface (chapitre 8, §8.3) |
| 6 | Matrice de vérification complète avec méthodes attribuées | Obligatoire | Matrice de vérification (chapitre 14, §14.4) |
| 7 | Registre des risques mis à jour ; aucun risque critique sans mesure de réduction | Obligatoire | Registre des risques (chapitre 15) |
| 8 | Ébauche du plan d'essais approuvée | Souhaitable | Plan d'essais d'environnement (chapitre 14, §14.3) |
| 9 | Architecture logicielle définie | Souhaitable | Document de conception logicielle |
| 10 | Estimation des coûts mise à jour (ascendante) | Obligatoire | Estimation des coûts avec devis fournisseurs (§16.1.6) |

Un critère *obligatoire* non satisfait conduit à un NO GO ou à un GO WITH ACTIONS ; un critère *souhaitable* non satisfait donne lieu à une action assortie d'un responsable et d'une échéance.

### 16.5.3 Présenter lors d'une revue

**À faire :**
- Commencer par la conclusion (« Le bilan de masse boucle avec une marge de 22 % »).
- Montrer des éléments probants, et pas seulement des affirmations (« L'analyse du bilan de liaison montre une marge de 4,2 dB dans le cas le plus défavorable »).
- Reconnaître honnêtement les risques (« Le déploiement de l'antenne est notre risque le plus élevé, à L3 × C4 = 12 »).
- Énoncer les hypothèses avant les résultats.
- Répondre directement aux questions ; si nécessaire, dire « Je ne sais pas — nous prenons une action ».

**À éviter :**
- Lire les diapositives à voix haute.
- Cacher les problèmes (les comités de revue finissent toujours par les trouver).
- Présenter une analyse sans en énoncer les hypothèses.
- Faire l'impasse sur les diapositives de réserve : ayez les données détaillées sous la main pour la séance de questions-réponses.
- Consacrer le temps à la description de la mission et expédier les résultats techniques.

---

## 16.6 Conduire un comité de revue

Un comité indépendant — composé de personnes qui n'ont pas réalisé la conception — évalue le projet au regard des critères de jalon. L'indépendance est essentielle : le comité existe pour trouver ce que l'équipe ne voit plus. Siéger dans un comité est une compétence au même titre que s'y présenter.

### 16.6.1 Rôles au sein du comité de revue

| Rôle | Responsabilité | Question clé à poser |
|------|---------------|---------------------|
| **Président** | Conduit la revue ; s'assure que tous les critères sont couverts | « Contrôlons systématiquement chaque critère de jalon. » |
| **Évaluateur système** | Évalue l'architecture d'ensemble et les bilans | « Tous les bilans bouclent-ils ? Quelle est la marge minimale ? » |
| **Évaluateur technique** | Évalue les décisions de conception des sous-systèmes | « Pourquoi avez-vous choisi ce composant plutôt que les autres solutions ? » |
| **Évaluateur risques** | Évalue la gestion des risques et la vérification | « Quel est votre risque le plus élevé ? La mesure de réduction est-elle adéquate ? » |
| **Évaluateur opérations** | Évalue le ConOps, le segment sol et la situation réglementaire | « Que se passe-t-il si vous perdez le contact pendant 48 heures ? » |

Dans un petit comité, le président peut aussi assumer l'un des rôles de relecteur, mais le relecteur risques et le relecteur technique devraient être deux personnes différentes : le premier cherche ce qui pourrait mal tourner, le second vérifie que la conception est juste, et une même personne mène rarement bien les deux à la fois.

### 16.6.2 Banque de questions pour les relecteurs

Questions types que le comité peut poser, chacune renvoyant à un chapitre de cet ouvrage :

- « Pourquoi l'espace est-il la bonne réponse ? Quelles autres solutions ont été envisagées ? » (chapitre 4)
- « Quelle est votre marge de masse ? Qu'est-ce qui la dimensionne ? Et si la charge utile était 20 % plus lourde que prévu ? » (chapitre 8)
- « Détaillez-moi votre bilan de liaison dans le cas le plus défavorable. Quelle est la marge minimale ? » (chapitre 11)
- « Quels sont vos trois principaux risques ? Quel est le risque résiduel après réduction ? » (chapitre 15)
- « Montrez-moi votre bilan de données. Boucle-t-il avec une seule station sol ? » (chapitre 11, §11.9, chapitre 17)
- « Que se passe-t-il lors d'un passage en mode survie pendant une éclipse ? Le bilan thermique tient-il ? » (chapitres 9 et 18)
- « Quel composant a le TRL le plus faible ? Quel est votre plan de qualification ? » (chapitres 13 et 14)
- « Avez-vous lancé les démarches de licence de spectre ? Qu'y a-t-il sur le chemin critique ? » (chapitre 2)
- « Quelle est votre liste de points de défaillance unique ? Lesquels avez-vous acceptés ? » (chapitre 15, §15.4.4)
- « Si vous disposiez de six mois et de 20 % de budget supplémentaires, que changeriez-vous ? »

### 16.6.3 Issue de la revue

Le comité conclut par l'une de trois recommandations — **GO**, **NO GO** ou **GO WITH ACTIONS** (accord sous réserve d'actions) —, annoncée par le président, accompagnée d'une liste d'actions comportant chacune un responsable et une échéance. Les actions sont suivies jusqu'à leur clôture avant le jalon suivant ; une action encore ouverte à la revue suivante constitue en soi une constatation.

---

## Synthèse

| Thème | Point clé à retenir |
|-------|-------------|
| Méthodes d'estimation des coûts | Paramétrique (en amont, CER), analogique (mission de référence), ascendante (devis fournisseurs) ; la précision se resserre de ± 50 % à ± 10 % au fil du cycle de vie |
| Coûts des CubeSats | Prix des COTS souvent inférieurs aux prévisions des CER ; adopter une approche hybride |
| WBS | Structure standard en dix éléments : gestion de programme, IS, AM, charge utile, plateforme, intégration et essais, logiciel, lancement, sol, opérations |
| CER | $C = a\,M^{b}\,f_{\text{complexity}}$ ; bases de données USCM/SSCM ; les CubeSats exigent des CER calibrées |
| Courbe d'apprentissage | $T_n = T_1\,n^{\log_2 L}$ ; avec un taux de 90 %, chaque doublement de la quantité réduit le coût unitaire de 10 % |
| Risque sur les coûts | P50 (référentiel), P70 (engagement NASA), P80 (prudent) ; $P_{80} \approx 1.3\,P_{50}$ ; l'écart constitue la réserve |
| Revues | Jalons selon le tableau 1.3 du chapitre 1 ; les critères de SRR et de PDR sont des listes explicites « obligatoire/souhaitable » avec des éléments probants désignés |
| Présentation | Commencer par les conclusions, montrer les éléments probants, reconnaître les risques, répondre directement |
| Comité de revue | Président + relecteurs système, technique, risques et opérations ; GO / NO GO / GO WITH ACTIONS, avec suivi des actions |

---

## Exercices

1. **Estimation paramétrique.** Un CubeSat 6U a une structure de 1,2 kg, une EPS de 1,5 kg, un sous-système TT&C de 0,4 kg et un SCAO de 1,1 kg. Évaluez les CER de l'USCM du §16.1.3 pour chaque sous-système (FY2010 $K), ajoutez la gestion de programme et l'ingénierie système, puis comparez le résultat avec une estimation ascendante COTS établie à partir des prix catalogue du §16.1.5. De quel facteur la CER surestime-t-elle le coût, et quel sous-système est responsable de l'essentiel de l'écart ?

2. **Répartition du WBS.** Un CubeSat 3U d'observation de la Terre a un plafond de coût de 320 k€. Répartissez-le entre les dix éléments de niveau 1 du WBS du §16.2.1 selon les pourcentages par défaut, puis refaites la répartition pour une mission dont la charge utile est un imageur hyperspectral spécifique avec 60 k€ de NRE (chapitre 13, §13.1.3). Quels éléments se réduisent pour absorber la croissance de la charge utile, et qu'est-ce que cela implique pour la campagne d'essais ?

3. **Coûts par phase.** À l'aide des pourcentages par phase du §16.2.2 et d'un total de 490 k€, tracez la courbe des dépenses cumulées de la mission 3U sur un calendrier de développement de 26 mois (phase 0/A 4 mois, B 6, C 8, D 8, puis E 36). Au cours de quel mois le projet a-t-il besoin de son apport de trésorerie le plus important, et qu'advient-il de la courbe si le lancement (WBS 8.0) est payé à 50 % à la signature du contrat en phase B ?

4. **Courbe d'apprentissage — calcul exact ou approché.** Pour un coût de première unité $C_1 =$ 800 k€ et des taux d'apprentissage de 95 %, 90 % et 85 %, calculez le coût total de 8, 16 et 32 unités à l'aide (a) de la somme exacte $C_1\sum i^{\log_2 L}$ et (b) de l'approximation continue du §16.3.1. Présentez dans un tableau l'erreur relative de (b) et indiquez la plus petite valeur de $N$ pour laquelle elle est inférieure à 3 %.

5. **Argument économique d'une constellation.** Reprenez l'exemple résolu du §16.3.3 pour une constellation de 12 satellites avec un taux d'apprentissage de 85 %, deux unités de rechange, un lancement à 250 k€ par satellite et un coût d'exploitation sur 3 ans de 1,2 M€. Comparez le coût par satellite avec le coût total d'un satellite unique du §16.1.6 et expliquez quels éléments du WBS ne bénéficient *pas* de la courbe d'apprentissage.

6. **P50/P80 par Monte-Carlo.** Modélisez la colonne ascendante du §16.1.6 avec les distributions et les valeurs de 1σ du §16.4.1 (considérez une distribution triangulaire comme symétrique autour de l'estimation, et une distribution log-normale comme ayant sa médiane à l'estimation). À l'aide d'un tableur et de 1000 tirages, estimez P50, P70 et P80 pour le total, et comparez le rapport P80/P50 à la règle empirique de 1,3. Quel élément contribue le plus à la dispersion ?

7. **Réduction des coûts.** Identifiez les trois principaux facteurs de coût de l'estimation ascendante du §16.1.6 et proposez un ensemble de modifications qui réduit le total de 20 % sans changer les objectifs de la mission. Pour chaque modification, indiquez quel bilan d'ingénierie (masse, puissance, liaison, données) ou quel indice de risque évolue, et dans quel sens.

8. **Préparation à la SRR.** Pour la conception d'UniSat-1 développée aux chapitres 5, 8, 9, 11, 13, 14 et 15, évaluez chaque critère de SRR du §16.5.1 comme satisfait, partiellement satisfait ou non satisfait, désignez les éléments probants (numéro de section et de tableau), et rédigez l'action — responsable, livrable, échéance — pour chaque critère qui n'est pas clairement satisfait.

9. **Comité de revue.** Constituez un comité de cinq personnes selon les rôles du §16.6.1 pour examiner le tableau de bouclage d'EOSat-3U du chapitre 12, §12.5.3, qui signale une ligne rouge (puissance en mode imagerie). Rédigez les cinq questions que poserait le comité, les éléments probants qu'il exigerait pour chacune, et la recommandation (GO / NO GO / GO WITH ACTIONS) à laquelle vous vous attendriez, avec les actions associées.

10. **Présentation.** Rédigez le plan en six diapositives d'une présentation de PDR pour la mission 3U d'observation de la Terre — besoin de la mission, pourquoi l'espace, conception du système et bilans, équipements et vérification, risques et coûts, opérations — et, pour chaque diapositive, rédigez la conclusion en une phrase qui l'ouvre, selon le principe « commencer par la conclusion » du §16.5.3, en indiquant la figure ou le tableau de cet ouvrage qui lui servirait d'élément probant.

---

## Références

1. NASA, *Cost Estimating Handbook*, version 4.0, 2015. https://www.nasa.gov/offices/ocfo/references-and-tools/
2. Wertz, J. R., Everett, D. F. & Puschell, J. J. (dir.), *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011, chapitre 20 (coût).
3. The Aerospace Corporation, *Small Satellite Cost Model (SSCM)*. https://www.aerospace.org/capabilities/small-satellite-cost-model
4. NASA, *NPR 7120.5F : NASA Space Flight Program and Project Management Requirements*, 2021 (organigrammes des tâches). https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7120&s=5F
5. ECSS, *ECSS-M-ST-60C : Cost and Schedule Management*, 2008. https://ecss.nl/standard/ecss-m-st-60c-cost-and-schedule-management/
6. NASA, *NPR 7123.1D : NASA Systems Engineering Processes and Requirements*, annexe G (*Technical Review Process*), 2023. https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D
7. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §3.7 (*Technical Reviews*). https://www.nasa.gov/reference/systems-engineering-handbook/
8. ECSS, *ECSS-M-ST-10C Rev. 1 : Project Planning and Implementation*, 2009, §6 (*Reviews*). https://ecss.nl/standard/ecss-m-st-10c-rev-1-project-planning-and-implementation/
9. Wright, T. P., « Factors Affecting the Cost of Airplanes », *Journal of the Aeronautical Sciences*, 3(4), 1936, p. 122–128.
