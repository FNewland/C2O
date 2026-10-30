# Chapitre 15 — Gestion des risques, maîtrise des interfaces et AMDEC

> **Lectures préalables conseillées.** ECSS-M-ST-80C (*Risk management*) ; ECSS-Q-ST-30-02C (*Failure modes, effects and criticality analysis*) ; ECSS-Q-ST-30C (*Dependability*) ; ECSS-E-ST-10-24C (*Interface management*) ; NASA SEH Rev 2, §6.4 (gestion des risques techniques) ; NASA NPR 8000.4B (gestion des risques à l'échelle de l'agence). Ce chapitre suppose que les équipements ont été choisis (chapitre 13) et que les méthodes de vérification ont été attribuées (chapitre 14) ; il s'appuie sur l'analyse des interfaces par matrice N² du chapitre 8, §8.3, et alimente le traitement du risque de coût du chapitre 16 ainsi que la conception de la FDIR du chapitre 18.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. construire et alimenter un registre des risques à l'aide d'une matrice vraisemblance–conséquence 5 × 5 ;
2. traiter les interfaces identifiées dans une matrice N² comme une source de risque et reporter les conflits d'interface dans le registre des risques ;
3. réaliser une AMDE/AMDEC (FMEA/FMECA) simplifiée pour les sous-systèmes critiques ;
4. identifier les points de défaillance unique et calculer la fiabilité de montages en série, en parallèle et « $k$ parmi $n$ » ;
5. classer les risques et choisir les stratégies de traitement appropriées (accepter, réduire, transférer, éviter).

Les produits de fournisseurs cités dans ce chapitre sont des exemples représentatifs et non des recommandations.

---

## 15.1 Processus de gestion des risques

*[Source : ECSS-M-ST-80C (Risk Management) ; NASA SEH Rev 2, §6.4 (Process 13 : Technical Risk Management)]*

### 15.1.1 Le processus en quatre étapes

La gestion des risques se poursuit tout au long du cycle de vie du projet. Les quatre étapes sont les suivantes :

1. **Identifier** — Qu'est-ce qui peut mal tourner ? (Remue-méninges, listes de vérification, données historiques, avis d'experts)
2. **Évaluer** — Quelle en est la vraisemblance ? Quelle serait la gravité de la conséquence ? (Cotation)
3. **Réduire** — Que pouvons-nous faire pour réduire la vraisemblance ou la conséquence ? (Choix de la stratégie)
4. **Surveiller** — Le risque augmente-t-il, diminue-t-il ou reste-t-il stable ? (Suivi, seuils de déclenchement, escalade)

### 15.1.2 Sources de risques

| Source | Exemples de risques |
|--------|--------------|
| **Technique** | Défaillance d'un composant, incompatibilité d'interface, performances insuffisantes, défaut logiciel |
| **Délais** | Retard de livraison d'un composant, moyen d'essai indisponible, retard réglementaire |
| **Coût** | Hausse du prix d'un composant, dérive du périmètre, dépassement de la campagne d'essais |
| **Programmatique** | Réduction du financement, rotation du personnel, retrait d'un partenaire |
| **Externe** | Report ou échec du lancement, brouillage du spectre, refus d'autorisation d'exportation |

---

## 15.2 La matrice des risques 5 × 5

La matrice 5 × 5 est l'outil standard de cotation des risques utilisé à l'ESA, à la NASA et dans les programmes spatiaux commerciaux. La figure 15.1 la présente sous la forme de l'ECSS-M-ST-80C.

### 15.2.1 Échelle de vraisemblance

| Niveau | Vraisemblance | Description | Plage de probabilité |
|-------|-----------|-------------|-------------------|
| 1 | Très faible | Très improbable ; aucun précédent dans des missions similaires | < 5 % |
| 2 | Improbable | Pourrait se produire mais peu probable ; s'est rarement produit | 5–20 % |
| 3 | Possible | S'est produit sur des missions similaires ; scénario crédible | 20–50 % |
| 4 | Probable | Devrait se produire au moins une fois pendant la mission | 50–80 % |
| 5 | Quasi certain | Se produira presque certainement ; nombreux précédents | > 80 % |

### 15.2.2 Échelle de conséquence

| Niveau | Conséquence | Incidence technique | Incidence sur les coûts | Incidence sur les délais |
|-------|-----------|-----------------|-------------|----------------|
| 1 | Négligeable | Aucune incidence sur les performances | Dépassement < 1 % | Glissement < 1 semaine |
| 2 | Mineure | Légère dégradation des performances ; une solution de contournement existe | Dépassement de 1–5 % | Glissement de 1–4 semaines |
| 3 | Modérée | Perte de performances importante ; mission dégradée | Dépassement de 5–15 % | Glissement de 1–3 mois |
| 4 | Majeure | Capacités de la mission fortement dégradées ; perte partielle | Dépassement de 15–30 % | Glissement de 3–6 mois |
| 5 | Catastrophique | Échec de la mission ; perte totale | Dépassement > 30 % | Glissement > 6 mois ou annulation |

### 15.2.3 Indice de risque et classification

> **Indice de risque :**
>
> $$R = L \times C$$
>
> où $L$ = vraisemblance (1–5) et $C$ = conséquence (1–5).

| Vraisemblance ↓ / Conséquence → | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 5 (M) | 10 (H) | 15 (H) | 20 (C) | 25 (C) |
| **4** | 4 (L) | 8 (M) | 12 (H) | 16 (C) | 20 (C) |
| **3** | 3 (L) | 6 (M) | 9 (M) | 12 (H) | 15 (H) |
| **2** | 2 (L) | 4 (L) | 6 (M) | 8 (M) | 10 (H) |
| **1** | 1 (L) | 2 (L) | 3 (L) | 4 (L) | 5 (M) |

- **L = faible (Low, 1–4) :** accepter et surveiller ;
- **M = moyen (Medium, 5–9) :** réduire si le rapport coût-efficacité le justifie ;
- **H = élevé (High, 10–15) :** réduction active obligatoire ;
- **C = critique (Critical, 16–25) :** reconception ou réduction du périmètre obligatoire.

![Matrice des risques 5 × 5 (ECSS-M-ST-80C).](../assets/figures/fig_risk_matrix.png)

**Figure 15.1** — La matrice vraisemblance–conséquence 5 × 5, avec les quatre zones d'acceptation (faible, moyen, élevé, critique) et des risques représentatifs d'un CubeSat placés selon leur indice. Une mesure de réduction déplace un risque vers le bas (vraisemblance plus faible) ou vers la gauche (conséquence plus faible) ; le registre consigne la position avant et après réduction.

### 15.2.4 Exemples de risques propres aux CubeSats

| Risque | L | C | Indice | Catégorie | Mesure de réduction type |
|------|---|---|-------|----------|-------------------|
| Défaillance d'un mécanisme de déploiement (antenne, générateur solaire) | 3 | 4 | 12 | Élevé | Mécanismes redondants ; plus de 100 cycles d'essai au sol |
| Perte des communications après la séparation | 2 | 5 | 10 | Élevé | Mode balise ; déploiement de l'antenne sur minuterie ; plusieurs stations sol |
| Le SCAO n'atteint pas la spécification de pointage | 3 | 3 | 9 | Moyen | Marge dans le bilan de pointage ; plan d'étalonnage en orbite |
| Bilan de puissance négatif pendant l'éclipse | 2 | 4 | 8 | Moyen | Fonctionnement par intermittence prudent ; marge batterie de 20 % |
| Défaillance d'un composant COTS due aux radiations (SEU/SEL) | 2 | 4 | 8 | Moyen | Réinitialisations par chien de garde ; circuits de protection contre le verrouillage ; EDAC |
| Bogue logiciel provoquant un passage intempestif en mode survie | 4 | 2 | 8 | Moyen | Essais logiciels approfondis ; chargement par étapes ; le mode survie doit fonctionner de manière indépendante |
| Dépassement thermique (cas chaud) | 2 | 3 | 6 | Moyen | Surface de radiateur supplémentaire ; limitation du rapport cyclique |
| Report du lancement (défaillance du lanceur) | 3 | 2 | 6 | Moyen | Manifeste sur plusieurs lanceurs ; marge de calendrier |
| Retard d'attribution de licence de spectre | 3 | 2 | 6 | Moyen | Déposer la demande 12 mois ou plus avant le lancement prévu (chapitre 2, §2.7) |

### 15.2.5 Stratégies de traitement

| Stratégie | Description | Quand l'utiliser | Incidence sur les coûts |
|----------|-------------|-------------|-------------|
| **Accepter** | Le risque est dans les limites de tolérance ; simple surveillance | Indice 1–4 (faible) | Aucune |
| **Réduire** | Réduire $L$ ou $C$ par des modifications de conception, des essais ou des procédures | Indice 5–15 | Modérée — coût de la mesure de réduction |
| **Transférer** | Transférer le risque à un tiers (assurance, garantie fournisseur) | Risque financier ; risque opérationnel | Prime ou coût contractuel |
| **Éviter** | Modifier la conception pour éliminer complètement le risque | Indice 16–25 (critique) | Peut affecter les performances ou le coût |

---

## 15.3 Les interfaces comme source de risque

La matrice N² est construite au chapitre 8, §8.3 : le tableau 8.1 en donne l'exemple à six sous-systèmes, le tableau 8.2 définit les codes de type d'interface **M** (mécanique), **E** (électrique/puissance), **T** (thermique), **D** (données), **R** (RF), **O** (optique) et **S** (logiciel), et le §8.3.5 présente les contrôles de détection des conflits ainsi que l'exemple résolu I²C/RS-422. Rien de tout cela n'est repris ici. Ce que la présente section ajoute, c'est le lien entre le registre des interfaces et le registre des risques.

Chaque case hors diagonale de la matrice N² est un endroit où deux sous-systèmes — et généralement deux ingénieurs, et souvent deux fournisseurs — doivent s'accorder. Le constat de la NASA selon lequel la plupart des défaillances système remontent à des problèmes d'interface (chapitre 8, §8.3) est une affirmation sur la vraisemblance : une interface qui n'a pas été formalisée sous forme d'exigence a une forte probabilité d'être erronée à l'intégration. Les interfaces entrent donc dans le registre des risques de trois manières :

1. **Conflits non résolus.** Un conflit détecté par les contrôles du §8.3.5 (tension, protocole, bande, emplacement de montage) et non encore résolu est un risque avec $L$ = 4–5 et une valeur de $C$ fixée par la classe de gravité du §8.3.5 (critique → $C$ = 4–5, majeure → 3, mineure → 2). Il reste dans le registre jusqu'à ce que sa résolution soit devenue une exigence d'interface et ait été vérifiée (chapitre 14).
2. **Interfaces non documentées.** Une case que la matrice N² indique comme active, mais pour laquelle il n'existe ni exigence d'interface ni entrée d'ICD, constitue un risque à part entière, typiquement $L$ = 3, $C$ = 3 (« perte de performances importante ; mission dégradée ») ; le cas classique est le couplage de type R entre l'émetteur et le récepteur de la charge utile, qu'aucune fiche technique de fournisseur ne couvre.
3. **Modes de défaillance liés aux interfaces.** L'AMDEC du §15.4 pose, pour chaque élément, la question : « que se passe-t-il à la frontière ? » — un connecteur qui se désaccouple sous vibrations (M), un bus tiré au niveau bas par un équipement défaillant (D), une face de radiateur masquée par un panneau déployé (T). Chacun de ces modes est étiqueté avec son code littéral, de sorte que le responsable de l'interface, et pas seulement celui de l'élément, en ait connaissance.

La règle pratique consiste à étiqueter chaque risque d'interface avec la case N² à laquelle il appartient et son code littéral, afin que le registre puisse être trié par interface aussi bien que par indice. Dans un outil de conception concourante doté d'un moteur de contraintes, la première catégorie est générée automatiquement dès qu'une paire de composants incompatibles est retenue ; la deuxième et la troisième exigent le jugement d'ingénieur propre à l'AMDEC. Le chapitre 8, §8.3.6, donne le format de l'exigence d'interface qui permet de clore un risque d'interface.

---

## 15.4 AMDE/AMDEC (FMEA/FMECA)

*[Source : ECSS-Q-ST-30-02C (Failure Modes, Effects and Criticality Analysis) ; ECSS-Q-ST-30C (Dependability)]*

### 15.4.1 Définitions

- **AMDE** (FMEA, analyse des modes de défaillance et de leurs effets) : identifie les modes de défaillance, leurs causes et leurs effets sur le système ;
- **AMDEC** (FMECA, analyse des modes de défaillance, de leurs effets et de leur criticité) : AMDE complétée d'un classement par criticité.

### 15.4.2 Structure d'un tableau d'AMDE/AMDEC

| Élément | Fonction | Mode de défaillance | Cause | Effet local | Effet système | Gravité | Détection | Disposition compensatoire | Criticité |
|------|----------|-------------|-------|-------------|---------------|----------|-----------|----------------------|------------|
| OBC | Traiter les commandes, exécuter le logiciel de vol | Blocage du processeur | SEU, bogue du micrologiciel | Plus aucun traitement des commandes | Perte de la maîtrise de la mission | 5 | Expiration du délai d'attente de la télémesure de servitude | Réinitialisation par chien de garde ; OBC redondant (s'il est prévu) | 1 (SPF) |
| Batterie | Stocker l'énergie | Court-circuit d'un élément | Défaut de fabrication | Capacité réduite | Tenue en éclipse raccourcie | 3 | Surveillance de la tension | Équilibrage des éléments ; marge de capacité | 2 |
| Roue de réaction | Fournir du couple | Grippage du roulement | Défaut de lubrification | Perte du contrôle sur un axe | Pointage dégradé | 4 | Anomalie de courant | Configuration à 4 roues (redondance 3 + 1) | 3 (avec redondance) |
| Antenne | Rayonner le signal RF | Échec du déploiement | Blocage du mécanisme (interface M) | Aucune antenne déployée | Aucune communication | 5 | Absence de balise | Déploiement redondant ; fil thermofusible + ressort | 1 (SPF) |

### 15.4.3 Catégories de criticité

| Catégorie | Définition | Action requise |
|----------|-----------|----------------|
| **1 (catastrophique)** | Une défaillance unique entraîne la perte de la mission ; aucune compensation | Reconcevoir pour ajouter une redondance, ou accepter avec justification |
| **2 (critique)** | Une défaillance unique entraîne une dégradation importante | Réduire le risque (redondance, solution de contournement opérationnelle) |
| **3 (majeure)** | Une défaillance unique entraîne une dégradation modérée | Surveiller ; prévoir une solution de contournement opérationnelle |
| **4 (mineure)** | Une défaillance unique a une incidence négligeable sur la mission | Accepter |

Lorsqu'un classement numérique est souhaité — dans l'automobile et dans une partie du spatial commercial —, on utilise l'**indice de priorité de risque** (RPN, *risk priority number*) :

$$\text{RPN} = S \times O \times D$$

où la gravité $S$, l'occurrence $O$ et la détectabilité $D$ sont chacune cotées de 1 à 10, de sorte qu'un mode de défaillance grave, fréquent et difficile à détecter peut atteindre 1000. L'ECSS-Q-ST-30-02C utilise les catégories de gravité ci-dessus associées à une classe de probabilité plutôt qu'un RPN, mais les deux schémas classent les mêmes modes de défaillance dans le même ordre.

### 15.4.4 Analyse des points de défaillance unique (SPF)

Un **point de défaillance unique** est tout composant dont la seule défaillance entraîne la perte de la mission. L'identification des SPF est l'un des résultats essentiels de l'AMDEC.

**Points de défaillance unique types d'un CubeSat :**

| Composant | Pourquoi c'est un SPF | Mesure de réduction courante |
|-----------|-----------------|-------------------|
| OBC (processeur unique) | Aucun traitement des commandes → aucune mission | Minuterie de chien de garde + mode survie autonome + mémoire EDAC |
| Batterie (pack unique) | Aucune énergie stockée → aucune tenue en éclipse | Surveillance au niveau des éléments ; limite de DoD prudente (< 20 %) |
| Antenne (déploiement non redondant) | Aucune liaison RF → ni commande ni télémesure | Mécanismes de déploiement redondants (fil thermofusible + ressort) |
| Générateur solaire (déploiement) | Aucune production de puissance → perte de la mission en quelques heures | Déploiement redondant ; ressort de charnière + moteur de secours |
| Carte principale de l'EPS | Aucune distribution de puissance | Généralement aucune mesure (SPF accepté sur les CubeSats) |

### 15.4.5 Équations clés : fiabilité

> **Fiabilité en série (tous les composants doivent fonctionner) :**
>
> $$R_{\text{series}} = \prod_{i=1}^{n} R_i = R_1 \times R_2 \times \cdots \times R_n$$
>
> Exemple : 5 composants ayant chacun $R = 0.99$ : $R_{\text{series}} = 0.99^5 = 0.951$

> **Fiabilité en parallèle (au moins un doit fonctionner — redondance) :**
>
> $$R_{\text{parallel}} = 1 - \prod_{i=1}^{n} (1 - R_i)$$
>
> Pour $n$ unités redondantes identiques de fiabilité $R$ chacune : $R_{\text{parallel}} = 1 - (1 - R)^n$
>
> Exemple : 2 mécanismes de déploiement redondants ayant chacun $R = 0.95$ :
> $R_{\text{parallel}} = 1 - (1 - 0.95)^2 = 1 - 0.05^2 = 1 - 0.0025 = 0.9975$

> **Redondance « $k$ parmi $n$ » (au moins $k$ des $n$ unités identiques doivent fonctionner) :**
>
> $$R_{k\text{-of-}n} = \sum_{i=k}^{n} \binom{n}{i} R^i (1 - R)^{n-i}$$

> **Temps moyen entre défaillances (MTBF) :**
>
> $$\text{MTBF} = \frac{\text{durée totale de fonctionnement (h)}}{\text{nombre de défaillances}}$$
>
> Pour un composant de taux de défaillance constant $\lambda$ (défaillances par heure) : $\text{MTBF} = 1/\lambda$
>
> **Fiabilité en fonction du temps (modèle exponentiel) :**
> $$R(t) = e^{-t/\text{MTBF}} = e^{-\lambda t}$$
>
> Exemple : MTBF = 50 000 h, durée de la mission = 8760 h (1 an) :
> $R = e^{-8760/50000} = e^{-0.1752} = 0.839$

> **Disponibilité du système :**
>
> $$A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}}$$
>
> où MTTR = temps moyen de réparation (ou de rétablissement, pour un engin spatial).
>
> Pour un engin spatial avec MTBF = 50 000 h et MTTR = 2 h (rétablissement après passage en mode survie) : $A = 50000/(50000 + 2) = 0.99996$

### 15.4.6 Exemple résolu : redondance des roues de réaction

*Problème :* une mission à pointage fin exige un contrôle d'attitude sur 3 axes. Chaque roue de réaction a une fiabilité $R = 0.98$ sur la mission de 2 ans.

*Configuration A — 3 roues (sans redondance) :*
$$R_{\text{system}} = R^3 = 0.98^3 = 0.941$$

*Configuration B — 4 roues en redondance 3 parmi 4 (1 de rechange), à l'aide de la formule « $k$ parmi $n$ » :*
$$P(\geq 3 \text{ en fonctionnement}) = \binom{4}{4} R^4 + \binom{4}{3} R^3 (1 - R) = 0.98^4 + 4 \times 0.98^3 \times 0.02 = 0.9224 + 4 \times 0.9412 \times 0.02 = 0.9224 + 0.0753 = 0.9977$$

*L'ajout d'une roue de rechange fait passer la fiabilité de 0,941 à 0,998 — une amélioration notable pour une augmentation modeste de la masse et du coût. La géométrie pyramidale qui permet à trois quelconques des quatre roues de couvrir les trois axes est décrite au chapitre 10, §10.3.* La figure 15.2 représente les deux configurations sous forme de diagrammes de fiabilité.

![Diagrammes de fiabilité de trois roues en série et de quatre roues en vote 3 parmi 4](../assets/figures/fig_rbd_wheels.png)

**Figure 15.2** — Diagrammes de fiabilité de l'exemple des roues de réaction. À gauche : trois roues en série, chacune de fiabilité R = 0,98, donnent une fiabilité système de 0,98³ = 0,941, car toute défaillance unique met fin au contrôle sur trois axes. À droite : quatre roues alimentant un bloc de vote 3 parmi 4 donnent 0,98⁴ + 4 × 0,98³ × 0,02 = 0,9977 ≈ 0,998, puisque le système survit à toute défaillance unique.

### 15.4.7 Exemple de mission réelle : Hitomi (ASTRO-H)

L'observatoire en rayons X Hitomi de la JAXA a été perdu le 26 mars 2016, 37 jours seulement après son lancement, à la suite d'une défaillance en cascade du sous-système SCAO :
1. un paramètre erroné dans le senseur stellaire a conduit à une estimation d'attitude erronée ;
2. les roues de réaction ont appliqué des couples incorrects fondés sur cette mauvaise estimation ;
3. les propulseurs ont été allumés pour « corriger » l'erreur d'attitude (fictive), provoquant une rotation rapide ;
4. la vitesse de rotation du satellite a dépassé les limites structurales, et le banc optique extensible s'est détaché.

**Cause première :** erreur de paramètre logiciel (conversion d'unités) + logique de FDIR inadaptée + absence de contrôle croisé entre les capteurs d'attitude.

*Leçon : l'AMDEC doit prendre en compte les défaillances en cascade et les défaillances de cause commune, et pas seulement les défaillances d'un composant isolé. Les erreurs logicielles sont aussi des modes de défaillance — tout comme les interfaces : c'est à l'interface de type S entre le paramètre préparé au sol et l'estimateur de bord que cette défaillance a commencé.*

*[Source : JAXA, rapport d'enquête sur Hitomi, 2016]*

---

## 15.5 Retour sur UniSat-1 : registre des risques et points de défaillance unique

La conception d'UniSat-1 des chapitres 9 à 13 est assez simple pour que son registre des risques complet tienne sur une page. Voici les cinq risques techniques les mieux cotés, avec leurs responsables tirés de la liste des postes du tableau 1.4 du chapitre 1 :

| Id. | Risque | Case N² / code | L | C | Indice | Stratégie | Mesure de réduction | Responsable |
|----|------|----------------|---|---|-------|----------|------------|-------|
| R-01 | Le monopôle UHF ne se déploie pas depuis sa position repliée | Structure → TTC (M) | 3 | 5 | 15 (H) | Réduire | Libération par fil thermofusible avec ressort de secours ; 50 cycles de déploiement en essai ; balise sur une antenne fouet secondaire | Structures |
| R-02 | Le bilan de données ne boucle pas avec une seule station sol (chapitre 11, §11.8.2) | TTC → sol (R, D) | 4 | 3 | 12 (H) | Réduire | Inscription au réseau SatNOGS avant le lancement ; un mode de moyennage à bord divise le débit de données par deux | Communications |
| R-03 | L'OBC spécifique (TRL 5) tombe en panne dans l'environnement radiatif | OBC (SEU/SEL) | 2 | 5 | 10 (H) | Réduire | Processeur de mode survie MSP430 avec chien de garde indépendant ; limitation de courant contre le verrouillage ; EDAC sur la RAM externe | OBDH |
| R-04 | Données du magnétomètre corrompues par l'aimant permanent embarqué et par le bruit de découpage de l'EPS | AOCS → charge utile (M, E) | 3 | 3 | 9 (M) | Réduire | Implantation sans mât au coin opposé de l'empilement ; caractérisation en essai du champ de l'aimant pour le soustraire ; faisceau blindé | Charge utile |
| R-05 | La batterie descend sous 0 °C en éclipse et ne peut plus se charger | EPS ↔ thermique (T) | 2 | 4 | 8 (M) | Réduire | Réchauffeur de batterie avec thermostat (chapitre 9, §9.5) ; vérification du cas froid en TVAC (chapitre 14, §14.5) | Thermique |

**Points de défaillance unique.** UniSat-1 en compte quatre : la carte EPS, le pack batterie unique, l'émetteur-récepteur UHF et le déploiement de l'antenne. Les trois premiers sont acceptés avec justification (une EPS ou une radio redondante doublerait le coût des plus petits sous-systèmes et ne relève pas de la pratique CubeSat) ; le quatrième est traité par R-01. Une estimation de fiabilité en série de la chaîne acceptée — EPS 0,97, batterie 0,98, émetteur-récepteur 0,97 sur un an — donne $R = 0.97 \times 0.98 \times 0.97 = 0.92$, ce qui, combiné aux 0,9975 du déploiement redondant, situe la probabilité de succès de la mission à un an autour de 0,92. Pour une démonstration technologique à 85 k€, c'est acceptable ; pour la mission EOSat-3U, c'est ce même calcul qui justifie la quatrième roue de réaction.

> **Matière à réflexion.** R-02 est le seul risque du registre créé par un bilan et non par le matériel. Le calcul de quel chapitre faudrait-il modifier pour qu'il disparaisse, et que coûterait cette modification ?

---

## Synthèse

| Thème | Point clé à retenir |
|-------|-------------|
| Processus de gestion des risques | Identifier → évaluer → réduire → surveiller (en continu tout au long du cycle de vie) |
| Matrice 5 × 5 | $R = L \times C$ ; faible (1–4), moyen (5–9), élevé (10–15), critique (16–25) |
| Stratégies | Accepter (faible), réduire (moyen à élevé), transférer (financier), éviter (critique) |
| Les interfaces comme risque | Chaque case N² (chapitre 8, §8.3, tableau 8.1) est une source de risque ; étiqueter les risques d'interface avec le code M/E/T/D/R/O/S du tableau 8.2 |
| Conflits d'interface | Incompatibilité de protocole, de tension ou de bande — à détecter tôt ; les conflits non résolus entrent dans le registre |
| AMDEC | Mode de défaillance → cause → effet local → effet système → gravité → détection → réduction → criticité (ou $\text{RPN} = S \times O \times D$) |
| SPF | Les points de défaillance unique doivent être identifiés, évalués, puis acceptés ou réduits |
| Fiabilité | $R_{\text{series}} = \prod R_i$ ; $R_{\text{parallel}} = 1 - \prod(1 - R_i)$ ; $R_{k\text{-of-}n} = \sum_{i=k}^{n}\binom{n}{i}R^i(1-R)^{n-i}$ ; $R(t) = e^{-\lambda t}$ |

---

## Exercices

1. **Registre des risques.** Identifiez cinq risques techniques pour un CubeSat 3U d'observation de la Terre doté d'un générateur solaire déployable, d'un senseur stellaire et d'une liaison descendante en bande S. Cotez chacun sur la matrice 5 × 5, classez-le, définissez une mesure de réduction pour tout risque d'indice ≥ 10 et désignez un responsable dans la liste des postes du tableau 1.4 du chapitre 1. Recotez ensuite chaque risque après réduction et représentez les déplacements sur un croquis de la figure 15.1.

2. **Échelles de conséquence.** La livraison d'un composant glisse de 10 semaines et augmente de 8 % le coût du matériel. Cotez la conséquence sur chacune des trois échelles du §15.2.2 (technique, coût, délais), et expliquez comment choisir un niveau de conséquence unique lorsque les trois divergent.

3. **Risques d'interface.** À l'aide du tableau 8.1 du chapitre 8, identifiez les trois cases de la matrice N² d'EOSat-3U les plus susceptibles de produire un risque d'interface, étiquetez chacune avec son code littéral du tableau 8.2, cotez-la, et rédigez l'exigence d'interface (dans la forme en « doit » du chapitre 8, §8.3.6) dont la vérification permettrait de la clore.

4. **AMDEC.** Complétez un tableau d'AMDEC de quatre lignes, au format du §15.4.2, pour le mécanisme de déploiement du générateur solaire d'EOSat-3U, l'amplificateur de puissance de l'émetteur en bande S, la mémoire flash de l'OBC et le réchauffeur de batterie. Attribuez à chacun une gravité, un moyen de détection et une disposition compensatoire, et indiquez quelles lignes sont des points de défaillance unique.

5. **Fiabilité en série et en parallèle.** La chaîne critique d'EOSat-3U comporte sept éléments dont les fiabilités à un an sont 0,995, 0,99, 0,99, 0,98, 0,98, 0,97 et 0,96. Calculez la fiabilité en série. Si l'élément à 0,96 est doublé en parallèle, quelle est la nouvelle fiabilité de la chaîne, et quelle est l'amélioration équivalente si l'on porte plutôt chacun des éléments à 0,98 à 0,995 grâce à un meilleur tri ? Quelle solution est la moins coûteuse, et pourquoi ?

6. **« $k$ parmi $n$ ».** Un CubeSat 6U embarque six chaînes de cellules solaires et peut satisfaire son exigence de puissance avec quatre quelconques d'entre elles. Chaque chaîne a une fiabilité $R = 0.97$ sur trois ans. Calculez la probabilité que l'exigence de puissance soit satisfaite. Recommencez avec cinq chaînes dont quatre sont nécessaires, et commentez le coût en masse de la sixième chaîne.

7. **Fiabilité exponentielle.** Une roue de réaction COTS a un MTBF annoncé de 120 000 h. Calculez sa fiabilité sur 1, 2 et 5 ans, puis la fiabilité du système 3 parmi 4 pour chaque durée. À partir de quelle durée de mission un ensemble 3 parmi 4 descend-il sous les 0,95 qu'offre une roue unique à un an ?

8. **Disponibilité.** Un satellite passe en mode survie en moyenne toutes les 400 h et met 6 h à revenir aux opérations nominales. Calculez la disponibilité. Si la FDIR du chapitre 18 est améliorée de sorte que le rétablissement soit autonome et prenne 30 minutes, quelle est la nouvelle disponibilité, et combien de passages d'imagerie supplémentaires par an cela représente-t-il pour une mission à 4 passages par jour ?

9. **Défaillances en cascade.** Reconstituez la séquence Hitomi du §15.4.7 sous forme d'une chaîne de lignes d'AMDEC, une par étape, avec le code d'interface (tableau 8.2) auquel chaque étape a franchi une frontière entre sous-systèmes. Identifiez le contrôle croisé unique qui aurait rompu la chaîne le plus tôt et estimez son coût de mise en œuvre rapporté à celui de la mission.

10. **Accepter ou réduire.** La carte EPS d'UniSat-1 est un point de défaillance unique accepté. Estimez la masse, le coût et le délai nécessaires pour la rendre redondante (deux cartes, interconnectées, avec un interrupteur d'isolement), recotez le risque, et décidez si la mesure de réduction est justifiée pour (a) UniSat-1 et (b) une mission commerciale 3U embarquant une charge utile de 400 k€. Appuyez votre argumentation sur la colonne d'incidence sur les coûts du §15.2.2.

---

## Références

1. ECSS, *ECSS-M-ST-80C : Risk Management*, 2008. https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/
2. ECSS, *ECSS-Q-ST-30-02C : Failure Modes, Effects (and Criticality) Analysis (FMEA/FMECA)*, 2009. https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/
3. ECSS, *ECSS-Q-ST-30C Rev. 1 : Dependability*, 2017. https://ecss.nl/standard/ecss-q-st-30c-dependability/
4. ECSS, *ECSS-E-ST-10-24C : Interface Management*, 2015. https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/
5. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §6.4. https://www.nasa.gov/reference/systems-engineering-handbook/
6. NASA, *NPR 8000.4B : Agency Risk Management Procedural Requirements*, 2017. https://nodis3.gsfc.nasa.gov
7. JAXA, *Hitomi (ASTRO-H) Anomaly Investigation Report*, 2016. https://global.jaxa.jp/press/2016/05/20160531_hitomi.html
8. Département de la Défense des États-Unis, *MIL-HDBK-338B : Electronic Reliability Design Handbook*, 1998.
9. O'Connor, P. & Kleyner, A., *Practical Reliability Engineering*, 5e éd., Wiley, 2012.
