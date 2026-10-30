# Partie III — Intégration, vérification et opérations

# Chapitre 13 — Sélection des équipements et nomenclature

> **Lectures préalables conseillées.** SMAD4, chap. 14 (sous-systèmes et composants de l'engin spatial) et chap. 20 (modélisation des coûts) ; NASA NPR 7123.1D, annexe E (niveaux de maturité technologique) ; ECSS-E-HB-11A (*TRL guidelines*) ; ECSS-Q-ST-20C (*Quality assurance*) ; ECSS-E-ST-10-24C (*Interface management*) ; NASA SEH Rev 2, §6.8 (analyse de décision). Ce chapitre suppose que les sous-systèmes ont été dimensionnés (chapitres 9 à 12) et que des composants candidats ont été identifiés pour chacun d'eux ; il transforme ces candidats en une nomenclature approvisionnable et traçable. La méthode d'étude de compromis est celle du chapitre 4, §4.5, et les codes d'interface sont ceux du tableau 8.2 du chapitre 8.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. appliquer un cadre de décision structuré « faire, acheter ou réutiliser » au choix des composants ;
2. évaluer des composants COTS au regard des exigences à l'aide des critères de TRL et d'héritage ;
3. construire une nomenclature (BOM) avec une traçabilité complète vers les exigences ;
4. identifier les contraintes de contrôle des exportations (ITAR, EAR, marchandises contrôlées au Canada) applicables aux équipements retenus ;
5. vérifier la compatibilité des interfaces (RF, électriques, mécaniques) lors du choix des composants ;
6. suivre les bilans cumulés de masse, de puissance et de coût au fil des choix.

Les produits de fournisseurs cités dans ce chapitre sont des exemples représentatifs et non des recommandations ; les prix sont donnés à titre indicatif (2026).

---

## 13.1 La décision « faire, acheter ou réutiliser »

Avant de sélectionner le moindre matériel, le projet doit arrêter la stratégie d'approvisionnement de chaque sous-système. Il s'agit d'une décision fondamentale d'ingénierie système, qui a des répercussions sur le coût, les délais, le risque et les performances.

*[Source : NASA SEH Rev 2, §6.8 « Decision Analysis » ; ECSS-M-ST-10C Rev. 1, §5.4]*

### 13.1.1 Cadre de décision

```
Pour chaque sous-système ou composant :
  1. Existe-t-il un produit COTS conforme aux exigences ?
     → Oui : BUY (acheter ; risque le plus faible, délai le plus court)
     → Non : continuer
  2. Existe-t-il un matériel éprouvé en vol sur une mission antérieure ?
     → Oui : REUSE (réutiliser ; risque faible, delta-qualification parfois nécessaire)
     → Non : continuer
  3. L'exigence peut-elle être satisfaite en modifiant un matériel existant ?
     → Oui : MODIFY (modifier ; risque modéré, délai modéré)
     → Non : MAKE (développer ; risque le plus élevé, délai le plus long, coût le plus élevé)
```

### 13.1.2 Matrice de compromis « faire, acheter ou réutiliser »

| Critère | Acheter (COTS) | Réutiliser (héritage) | Modifier | Faire (spécifique) |
|--------|-----------|-------------------|--------|---------------|
| **Coût (NRE)** | Nul | Nul à faible | Modéré | Élevé |
| **Coût (récurrent)** | Prix du fournisseur | Coût de reproduction | Fournisseur + delta | Développement complet |
| **Délais** | 4–16 semaines de délai d'approvisionnement | 8–24 semaines | 12–36 semaines | 12–48 mois |
| **Risque** | Faible (si TRL ≥ 7) | Faible (éprouvé en vol) | Moyen | Élevé |
| **Performances** | Fixées par le fournisseur | Fixées par l'héritage | Ajustables | Entièrement personnalisables |
| **Propriété intellectuelle** | Conservée par le fournisseur | Partage possible | Négociée | Pleine propriété |
| **Qualification** | Données fournies par le fournisseur | Delta-qualification seulement | Requalification partielle | Qualification complète |

### 13.1.3 Coûts non récurrents

> **Équation clé — estimation des coûts non récurrents (NRE) :**
>
> $$C_{\text{NRE}} = N_{\text{hours}} \cdot r_{\text{hour}} + C_{\text{material}} + C_{\text{facility}} + C_{\text{test}}$$
>
> où $N_{\text{hours}}$ est la charge de travail d'ingénierie, $r_{\text{hour}}$ le taux horaire chargé, et les autres termes les coûts de matériaux, de moyens et d'essais du développement.
>
> Pour un COTS : les NRE sont quasi nuls (le fournisseur absorbe le coût de développement).
> Pour un développement spécifique : les NRE peuvent atteindre 3 à 10 fois le coût récurrent unitaire. Le chapitre 16 développe les relations d'estimation de coût qui permettent de replacer ce chiffre dans son contexte.

### 13.1.4 Exemple résolu

*Problème :* une mission CubeSat 6U a besoin d'un senseur solaire fin d'une précision de 0,1°. Trois options sont possibles :

| Option | Type | Précision | Masse | Coût (indicatif, 2026) | TRL | Délai d'approvisionnement |
|--------|------|----------|------|------|-----|-----------|
| Bradford SSOC-D60 (représentatif) | COTS | 0,1° | 35 g | 15 k€ | 9 | 8 semaines |
| Matrice de photodiodes développée en interne | Spécifique | 0,05° | 20 g | 8 k€ + 400 h de NRE | 4 | 12 mois |
| Senseur à héritage modifié | Réutilisation | 0,08° | 40 g | 6 k€ + 80 h de delta-qualification | 7 | 16 semaines |

*Décision :* l'option COTS satisfait l'exigence, présente un TRL 9 et le risque calendaire le plus faible, pour un coût total de 15 k€, contre 8 k€ + ~40 k€ de NRE (400 h à un taux chargé d'environ 100 €/h) pour l'option spécifique. **Acheter.**

---

## 13.2 Évaluation du niveau de maturité technologique (TRL)

Le TRL est l'indicateur de référence de la maturité d'une technologie. Développé par la NASA dans les années 1970, il est aujourd'hui utilisé universellement dans les programmes spatiaux. La figure 13.1 présente l'échelle en neuf niveaux.

*[Source : NASA NPR 7123.1D, annexe E ; ECSS-E-HB-11A « Technology Readiness Level (TRL) Guidelines »]*

![Échelle des niveaux de maturité technologique (TRL).](../assets/figures/fig_trl.png)

**Figure 13.1** — Les neuf niveaux de maturité technologique, des principes de base observés (TRL 1) au système éprouvé en vol (TRL 9), avec l'environnement dans lequel les éléments probants de chaque niveau doivent être obtenus. L'écart entre le TRL 6 et le TRL 7 — d'un environnement représentatif au sol à l'environnement opérationnel dans l'espace — est le plus coûteux à franchir.

### 13.2.1 Échelle des TRL et critères de décision

| TRL | Définition | Éléments probants exigés | Décision pour un CubeSat |
|-----|-----------|-------------------|-----------------|
| 1 | Principes de base observés | Travaux de recherche publiés | Ne pas retenir |
| 2 | Concept technologique formulé | Études analytiques | Ne pas retenir |
| 3 | Preuve de concept expérimentale | Mesures en laboratoire | Ne pas retenir |
| 4 | Composant validé en laboratoire | Maquette fonctionnelle testée | Risque élevé — à éviter sauf en l'absence d'alternative |
| 5 | Composant validé en environnement représentatif | Modèle d'ingénierie testé | Acceptable pour des missions de démonstration technologique |
| 6 | Modèle de système ou de sous-système démontré en environnement représentatif | Prototype en environnement représentatif | Acceptable avec des mesures de réduction du risque |
| 7 | Prototype du système démontré en environnement opérationnel | Prototype testé dans l'espace | Minimum souhaitable pour les CubeSats |
| 8 | Système réel achevé et qualifié | Matériel qualifié pour le vol | Fortement préférable |
| 9 | Système réel éprouvé en vol | Exploitation réussie en orbite | Risque le plus faible |

### 13.2.2 Relation entre TRL et risque

> **Facteur de réduction du risque (empirique) :**
>
> $$f_{\text{risk}} = 10^{-(\text{TRL} - 1)/3}$$
>
> | TRL | Facteur de risque | Interprétation |
> |-----|------------|----------------|
> | 3 | 0,22 | Forte probabilité de défaillance ou de reconception |
> | 5 | 0,046 | Risque modéré |
> | 7 | 0,010 | Risque faible |
> | 9 | 0,002 | Risque très faible |
>
> *Cette relation empirique (d'après le tableau 20-12 de SMAD4) montre pourquoi un TRL ≥ 6 constitue le seuil habituel pour les composants critiques pour la mission.*

### 13.2.3 Exemple de mission réelle : MarCO (Mars Cube One)

MarCO A et B, de la NASA (lancés en mai 2018), ont été les premiers CubeSats interplanétaires. Ils utilisaient :
- le transpondeur Iris (JPL, TRL 6 au moment de la sélection — première radio de CubeSat pour l'espace lointain) ;
- des roues de réaction COTS (Blue Canyon Technologies, TRL 9) ;
- une antenne *reflectarray* déployable spécifique (JPL, TRL 5 au moment de la sélection).

L'antenne spécifique était l'élément le plus risqué. Elle a exigé de nombreux essais de développement et a été le dernier composant à atteindre le TRL 6 pour la CDR. Elle a retardé le calendrier de 4 mois, mais a finalement été un succès.

*Leçon : si vous devez faire voler un composant de faible TRL, il dominera votre calendrier et votre registre des risques.*

*[Source : Klesh, A. et al., « MarCO : Early Operations of the First CubeSats to Mars », 32nd Annual Small Satellite Conference, 2018 ; « Mars Cube One (MarCO) — Lessons Learned », 33rd Annual Small Satellite Conference, 2019]*

---

## 13.3 Construction de la nomenclature (BOM)

La nomenclature est la liste de référence de tout le matériel, de tous les logiciels et de tous les consommables nécessaires à la construction du satellite. Elle fait le lien entre la conception et l'approvisionnement.

### 13.3.1 Structure de la nomenclature

Une nomenclature correctement structurée suit la hiérarchie de l'organigramme des tâches ; la figure 13.2 présente les cinq mêmes niveaux, avec les colonnes de cumul que porte chaque nœud parent :

```
BOM level 0: Spacecraft (S/C-001)
  BOM level 1: Subsystem (e.g. EPS-000)
    BOM level 2: Assembly (e.g. EPS-SA-000 Solar array assembly)
      BOM level 3: Component (e.g. EPS-SA-001 Solar cell string)
        BOM level 4: Part (e.g. EPS-SA-001-01 Azur 3G30C cell)
```

![Arborescence de la nomenclature avec colonnes de cumul](../assets/figures/fig_bom_tree.png)

**Figure 13.2** — La nomenclature sous forme d'arbre indenté, du satellite (niveau 0) à la pièce (niveau 4), illustrée pour la branche EPS d'un CubeSat 3U avec des valeurs représentatives. Chaque ligne parente cumule ses enfants : la masse, la puissance et le coût sont des sommes pondérées par les quantités, la colonne TRL porte le TRL le plus faible de la sous-arborescence et la colonne de délai d'approvisionnement le délai le plus long, de sorte que la ligne du satellite montre d'un coup d'œil quel article (ici la charge utile de TRL 6, à 26 semaines) pilote le risque et le calendrier.

### 13.3.2 Champs de la nomenclature

| Champ | Description | Exemple |
|-------|------------|---------|
| **Identifiant d'article** | Identifiant hiérarchique unique | EPS-BAT-001 |
| **Description** | Nom et modèle du composant | GomSpace NanoPower P31u |
| **Fabricant** | Nom du fournisseur | GomSpace A/S |
| **Référence** | Référence fabricant | P31U-9-30 |
| **Quantité** | Nombre requis | 1 |
| **Masse unitaire (g)** | Masse par article | 94 |
| **Puissance unitaire (W)** | Consommation de crête / moyenne | 0,5 / 0,2 |
| **Coût unitaire (EUR)** | Coût d'approvisionnement | 8500 (indicatif) |
| **TRL** | Niveau de maturité technologique | 9 |
| **Héritage** | Mission(s) précédente(s) ayant volé | GOMX-3, GOMX-4 |
| **Délai d'approvisionnement** | Délai d'obtention | 12 semaines |
| **ECCN/USML** | Classification à l'exportation | EAR99 |
| **État** | Retenu / commandé / reçu / testé | Retenu |

Dans un outil de conception concourante, la nomenclature est générée automatiquement à partir des choix d'équipements : chaque composant retenu devient une entrée de la nomenclature avec sa quantité, et l'export présente côte à côte l'estimation paramétrique et les données réelles du COTS, pour comparaison. Établi à la main, ce même tableau est la source unique à partir de laquelle on recalcule les bilans de masse, de puissance et de coût (chapitre 12, §12.5).

### 13.3.3 Masse totale de la nomenclature

> **Équation clé — masse totale de la nomenclature :**
>
> $$M_{\text{BOM}} = \sum_i m_i\, q_i + M_{\text{harness}} + M_{\text{fasteners}} + M_{\text{margin}}$$
>
> où :
> - $m_i$ = masse unitaire du composant $i$
> - $q_i$ = quantité du composant $i$
> - $M_{\text{harness}}$ = masse du faisceau de câbles (généralement 5–8 % de la masse sèche pour les CubeSats)
> - $M_{\text{fasteners}}$ = fixations mécaniques, entretoises, accessoires thermiques (~3–5 %)
> - $M_{\text{margin}}$ = marges d'équipement et de système selon le barème à deux niveaux du tableau 8.3 du chapitre 8 (marge système de 20 % en phase A)

### 13.3.4 Exemple résolu — synthèse de la nomenclature d'un CubeSat 6U

Le cumul par sous-système ci-dessous concerne un CubeSat 6U d'observation de la Terre (la ligne d'allocation correspond à la limite du déployeur 6U, chapitre 12, §12.1.1). Comparez-le avec la liste d'équipements du 3U du chapitre 12, §12.5.2.

| Sous-système | Composants | Masse totale (g) | Puissance totale (W) | Coût total (k€, indicatif) |
|-----------|-----------|----------------|-----------------|-------------------|
| Structure | Rails, panneaux, fixations | 350 | 0 | 8,0 |
| EPS | Générateur solaire + batterie + carte | 420 | 0,5 | 18,0 |
| OBC | Calculateur de vol + stockage | 80 | 1,2 | 10,0 |
| AOCS | Senseur stellaire + magnétocoupleurs + roues de réaction | 550 | 4,5 | 45,0 |
| TTC | Émetteur-récepteur en bande S + antenne patch | 180 | 8,0 (émission) | 22,0 |
| Thermique | MLI + réchauffeurs | 60 | 2,0 (crête) | 3,0 |
| Charge utile | Imageur multispectral | 800 | 12,0 | 65,0 |
| Faisceau | Câbles, connecteurs | 180 | 0 | 2,5 |
| **Total** | | **2620** | **28,2 (crête)** | **173,5** |
| Allocation (6U) | | 12 000 | 40,0 (générateur solaire EOL) | 250,0 |
| Marge | | 9380 (78 %) | 11,8 (30 %) | 76,5 (31 %) |

La marge de masse de 78 % est typique d'une conception 6U précoce embarquant une charge utile de classe 3U : le format a été choisi pour le volume et la puissance, pas pour la masse. Les deux marges qui comptent sont celle de puissance (30 % avec toutes les charges simultanément à leur crête, ce qui, comme le montrera le tableau des modes du chapitre 18, n'arrive jamais) et celle de coût (31 %, avant application des marges du chapitre 16).

---

## 13.4 Contrôle des exportations et approvisionnement

Le contrôle des exportations est l'un des aspects les plus souvent négligés des missions CubeSat, en particulier pour les équipes internationales. Les infractions sont lourdement sanctionnées (poursuites pénales, annulation du programme). Le chapitre 2, §2.8, décrit le régime canadien ; la présente section en donne la lecture de l'ingénieur, c'est-à-dire ses conséquences sur le choix des composants.

*[Source : ITAR — 22 CFR Parts 120–130 ; EAR — 15 CFR Parts 730–774 ; Programme des marchandises contrôlées du Canada — Loi sur la production de défense]*

### 13.4.1 Régimes de contrôle des exportations

| Régime | Texte de référence | Champ d'application | Enjeu principal pour les CubeSats |
|--------|-------------|-----------|-------------------------|
| **ITAR** | *Arms Export Control Act* (États-Unis) | Articles de défense (catégories IV, XI et XV de l'USML) | Senseurs stellaires, processeurs durcis, certains récepteurs GPS |
| **EAR** | *Export Administration Act* (États-Unis) | Biens à double usage (CCL) | La plupart des composants spatiaux COTS (ECCN 9A515) |
| **PMC (Canada)** | Loi sur la production de défense | Marchandises contrôlées au Canada | Manipulation d'articles ITAR d'origine américaine dans des installations canadiennes |
| **Wassenaar** | Arrangement de Wassenaar | Contrôles multilatéraux des exportations | Chiffrement, GNSS de haute précision, capteurs d'imagerie |

### 13.4.2 Décision de classification d'un composant

```
Le composant figure-t-il sur la US Munitions List (USML) ?
  → Oui : soumis à l'ITAR. Une licence DSP-5 est nécessaire pour l'exportation.
     Catégories : IV (lanceurs), XI (électronique militaire),
                  XV (systèmes spatiaux)
  → Non : consulter la Commerce Control List (CCL)
     Est-il classé sous l'ECCN 9A515 (engins spatiaux) ?
       → Oui : soumis aux EAR. Une licence du BIS peut être nécessaire.
       → Non : probablement EAR99 (aucune licence pour la plupart des destinations)
```

### 13.4.3 Composants de CubeSat couramment soumis à l'ITAR

| Type de composant | Motif du contrôle | Solution de remplacement |
|---------------|---------------|------------|
| Processeurs durcis aux radiations | Tenue aux radiations de niveau militaire | Processeurs COTS avec atténuation logicielle (chapitre 12, §12.3.2) |
| Senseurs stellaires de haute précision (< 1 seconde d'arc) | Utilisables pour le guidage de missiles | Modèles moins précis (> 5 secondes d'arc) |
| Certains récepteurs GPS/GNSS | Au-delà des limites COCOM (> 18 km d'altitude, > 515 m/s) | Récepteurs qualifiés spatial conformes aux limites COCOM |
| Systèmes de propulsion (certains) | Technologie des missiles | Systèmes à gaz froid ou à eau |
| Modules de chiffrement | Renseignement d'origine électromagnétique | Chiffrement libre (un examen au titre des EAR peut rester nécessaire) |

### 13.4.4 Processus d'approvisionnement

```
1. Exigences                → établir la spécification du composant
2. Étude de marché          → identifier les produits COTS candidats
3. Classification export    → demander l'ECCN au fournisseur
4. Étude de compromis       → noter et classer les candidats
5. Demande de prix          → obtenir prix et délais de livraison
6. Bon de commande          → engager l'approvisionnement
7. Contrôle à réception     → vérifier par rapport au bon de commande et à la fiche technique
8. Intégration              → installer et essayer fonctionnellement
```

### 13.4.5 Exemple de mission réelle : incidence du contrôle des exportations

BRITE-Constellation (Autriche/Canada/Pologne) était une série de nanosatellites consacrés à la photométrie stellaire. Les satellites BRITE canadiens (UniBRITE et BRITE-Austria, construits par l'UTIAS/SFL) ont exigé une gestion rigoureuse du contrôle des exportations :
- les composants ITAR d'origine américaine ont nécessité des accords d'assistance technique (TAA) ;
- l'équipe canadienne a dû s'inscrire au Programme des marchandises contrôlées ;
- des licences d'exportation ont été nécessaires pour les expéditions entre le Canada, l'Autriche et le site de lancement aux États-Unis ;
- effort total de mise en conformité réglementaire : ~6 personnes-mois et plus de 12 mois de délai.

*Leçon : lancez la classification à l'exportation dès que les composants sont identifiés. Un seul composant ITAR peut ajouter 6 à 12 mois au calendrier.*

*[Source : Sarda, K. et al., « BRITE-Constellation Mission and Spacecraft », AIAA/USU Small Satellite Conference, 2014]*

---

## 13.5 Vérification de la compatibilité des interfaces

À mesure que les composants sont retenus, la compatibilité de chaque interface doit être vérifiée. Les trois catégories d'interfaces qui posent le plus souvent problème au moment du choix sont les interfaces RF (R), électriques (E) et mécaniques (M), selon les codes littéraux du tableau 8.2 du chapitre 8.

### 13.5.1 Compatibilité de la chaîne RF

La chaîne RF (transpondeur, câble, antenne) doit être accordée en fréquence. C'est l'incompatibilité d'équipements la plus fréquente chez les débutants en CubeSat.

| Règle | Exemple correct | Exemple incorrect |
|------|----------------|-------------------|
| **Concordance de bande** | Transpondeur en bande S + antenne patch en bande S | Transpondeur en bande S + cornet en bande X |
| **Adaptation d'impédance** | Transpondeur 50 Ω + câble 50 Ω + antenne 50 Ω | Des impédances différentes provoquent des réflexions |
| **Concordance des connecteurs** | SMA sur le transpondeur + câble SMA–SMA + SMA sur l'antenne | Le passage de SMA à type N exige un adaptateur (pertes) |
| **Polarisation** | Antenne RHCP + station sol RHCP | RHCP vers LHCP provoque une perte de polarisation croisée > 20 dB (chapitre 11, §11.8.2) |

> **Équations clés — pertes par désadaptation d'impédance :**
>
> $$\Gamma = \frac{Z_{\text{load}} - Z_{\text{source}}}{Z_{\text{load}} + Z_{\text{source}}}$$
>
> $$\text{Affaiblissement de réflexion (dB)} = -20 \log_{10} |\Gamma|$$
>
> $$\text{Perte de désadaptation (dB)} = -10 \log_{10}\!\left(1 - |\Gamma|^2\right)$$
>
> Pour une source de 50 Ω débitant dans une charge de 75 Ω :
> $\Gamma = (75 - 50)/(75 + 50) = 0.2$ ; affaiblissement de réflexion $= -20 \log_{10}(0.2) = 14$ dB ; perte de désadaptation $= -10 \log_{10}(1 - 0.04) = 0.18$ dB.
>
> Une perte de désadaptation de cet ordre est absorbée par le terme de pertes de ligne $L_{TX}$ du bilan de liaison (chapitre 11, §11.2) ; l'affaiblissement de réflexion importe davantage, car la puissance réfléchie peut endommager l'étage de sortie d'un émetteur.

Un outil de conception concourante qui dispose des données de bande de chaque composant signale un transpondeur et une antenne de bandes différentes dès que le second est retenu ; à la main, la vérification tient en une colonne de la nomenclature.

### 13.5.2 Vérification des interfaces électriques

| Paramètre | CubeSat type | Points à vérifier |
|-----------|----------------|----------------|
| Tension du bus | 3,3 V, 5 V ou non régulée (6–8,4 V Li-ion) | La plage de tension d'entrée du composant couvre la tension du bus |
| Courant de crête | Limite par ligne commutée (généralement 1–3 A) | Le courant d'appel du composant ne dépasse pas la limite |
| Protocole de données | I²C, SPI, UART, CAN, RS-422 | Tous les équipements d'un même bus utilisent un protocole compatible (exemple résolu du chapitre 8, §8.3.5) |
| Connecteur | PC/104, Hirose, Harwin | Le type de connecteur physique correspond, ou un adaptateur est prévu |

### 13.5.3 Vérification des interfaces mécaniques

| Paramètre | Exigence de la CDS pour un 3U | Vérification |
|-----------|--------------------|----|
| Dimensions | 100,0 ± 0,1 mm × 100,0 ± 0,1 mm × 340,5 ± 0,5 mm | Mesure au pied à coulisse |
| Profil des rails | 8,5 × 8,5 mm ± 0,1 mm | Calibre de profil |
| Hauteur de l'empilement de composants | ≤ 83 mm de largeur interne par U | Contrôle sur la maquette 3D |
| Position du centre de gravité | À moins de 2 cm du centre géométrique | Mesure des propriétés de masse |

---

## 13.6 Retour sur UniSat-1 : nomenclature et coût

La nomenclature d'UniSat-1 est remarquablement courte : neuf lignes seulement (huit composants plus le faisceau). Cette simplicité est un atout majeur pour de petites équipes ayant peu d'expérience de l'approvisionnement. La liste d'équipements elle-même a été établie au chapitre 12, §12.6 ; elle est reprise ici sous forme de nomenclature, complétée des champs d'approvisionnement.

> **Nomenclature d'UniSat-1 (phase B — devis fournisseurs obtenus ; exemples représentatifs, coûts indicatifs 2026) :**
>
> | Identifiant | Composant | Fabricant | Référence | Qté | Masse unitaire (g) | Coût unitaire (k€) | TRL | ECCN | Délai (semaines) |
> |---------|-----------|-------------|-------------|-----|---------------|-----------------|-----|------|-----------|
> | STR-001 | Structure de CubeSat 1U | ISIS | ISIS-1U-STR | 1 | 200 | 4,0 | 9 | EAR99 | 8 |
> | EPS-001 | NanoPower P31us (EPS + batterie de 10 Wh) | GomSpace | P31US-10 | 1 | 200 | 12,0 | 9 | EAR99 | 12 |
> | EPS-SA-001 | Cellules solaires GaAs fixées sur la structure | AzurSpace | 3G30C | 5 | 10 | 1,5 | 9 | EAR99 | 10 |
> | OBC-001 | Calculateur de vol spécifique (Cortex-M) | Interne | UNISAT-OBC-01 | 1 | 30 | 3,0 | 5 | EAR99 | — |
> | COM-001 | Émetteur-récepteur UHF | GomSpace | NanoCom AX100 | 1 | 55 | 8,0 | 8 | EAR99 | 12 |
> | COM-ANT-001 | Antenne UHF déployable | Endurosat | UHF-ANT-S | 1 | 25 | 2,5 | 8 | EAR99 | 8 |
> | PL-001 | Carte magnétomètre MEMS | Interne | UNISAT-MAG-01 | 1 | 50 | 5,0 | 4 | EAR99 | — |
> | AOCS-001 | Kit magnétique passif (aimant + barreaux) | NewSpace | PMAG-1U | 1 | 30 | 1,0 | 9 | EAR99 | 6 |
> | HAR-001 | Faisceau interne | Spécifique | — | 1 | 50 | 1,0 | S. O. | EAR99 | — |
> | | **TOTAUX** | | | | **690 g** | **~44 k€** | | | |

**Synthèse des coûts (mission complète, matériel + services ; indicatif 2026) :**

| Élément du WBS | Coût (k€) | Remarques |
|-------------|------------|-------|
| Matériel (nomenclature) | 44 | Tout en COTS sauf l'OBC et la charge utile |
| Logiciel de l'OBC | 5 | Travail étudiant (valorisé au taux des bourses) |
| Étalonnage de la charge utile | 3 | Laboratoire universitaire de magnétométrie |
| Intégration et essais | 8 | Assemblage + essai de vibrations (moyen d'essai universitaire) |
| Station sol | 5 | SatNOGS (gratuit) + achat d'une antenne Yagi dédiée |
| Lancement (déploiement depuis l'ISS) | 15 | Frais de déploiement 1U de NanoRacks |
| Gestion de projet / IS / AQ | 5 | Encadrement par le corps enseignant |
| **TOTAL** | **~85 k€** | |

**Comparaison avec la mission d'observation de la Terre en 3U :**

| Indicateur | UniSat-1 (1U) | EOSat-3U |
|--------|--------------|---------------|
| Lignes de nomenclature | 9 | ~15–20 |
| Coût du matériel | ~44 k€ | ≈ 170 k€ avec un imageur COTS (chapitre 16, §16.1.6) ; ≈ 313 k€ avec le télescope spécifique du chapitre 12, §12.5.2 |
| Coût total de la mission | ~85 k€ | ~490 k€ |
| Durée de développement | 6–12 mois | 18–24 mois |
| Taille de l'équipe | 3–5 personnes | 8–15 personnes |

**Contrôle des exportations :** tous les composants d'UniSat-1 sont classés EAR99 (aucune licence requise). Aucun article n'est soumis à l'ITAR, car la mission n'utilise ni senseur stellaire, ni processeur durci aux radiations, ni propulsion faisant appel à une technologie restreinte par l'ITAR. C'est un avantage considérable pour les collaborations universitaires internationales.

**Décisions « faire, acheter ou réutiliser » :**

| Composant | Décision | Justification |
|-----------|----------|-----------|
| Structure | Acheter (COTS) | La structure 1U d'ISIS est éprouvée en vol, TRL 9, peu coûteuse |
| EPS | Acheter (COTS) | Le GomSpace P31us est la norme de fait, TRL 9 |
| OBC | Faire (spécifique) | Carte minimale réalisée au laboratoire universitaire ; moins coûteuse qu'un OBC COTS pour cette application simple |
| Communications | Acheter (COTS) | GomSpace AX100, TRL 8, bien documenté |
| Charge utile | Faire (spécifique) | Capteur MEMS innovant — c'est *précisément* la démonstration technologique |
| SCAO passif | Acheter (COTS) | Kit de stabilisation magnétique standard |

> **Matière à réflexion.** Les deux articles « faits » d'UniSat-1 sont aussi les deux articles de plus faible TRL (5 et 4). D'après la relation empirique du §13.2.2, leur facteur de risque est environ 10 et 20 fois celui des achats de TRL 9. À quel moment du calendrier le projet devrait-il placer le premier essai de bout en bout de ces deux cartes ?

---

## Synthèse

| Thème | Point clé à retenir |
|-------|-------------|
| Faire, acheter ou réutiliser | Acheter des COTS en premier ; réutiliser l'héritage en second ; ne faire du spécifique qu'en cas de nécessité |
| NRE | $C_{\text{NRE}} = N_{\text{hours}} r_{\text{hour}} + C_{\text{material}} + C_{\text{facility}} + C_{\text{test}}$ ; les NRE d'un développement spécifique valent 3 à 10 fois le coût unitaire |
| TRL | TRL 6 minimum pour les composants critiques pour la mission ; TRL 7+ préférable pour les CubeSats ; $f_{\text{risk}} = 10^{-(\text{TRL}-1)/3}$ |
| Nomenclature | Liste hiérarchique : sous-système → assemblage → composant → pièce, avec traçabilité complète |
| Contrôle des exportations | Classer chaque composant (EAR99 / ECCN / ITAR) ; commencer tôt — source de retards pour le programme |
| Compatibilité RF | Bande, impédance, connecteur et polarisation doivent tous concorder le long de la chaîne RF |
| Électrique | Tension du bus, protocole de données et type de connecteur vérifiés pour chaque composant |
| Suivi des bilans | Totaux courants pendant la sélection ; s'arrêter et résoudre le problème en cas de dépassement d'une allocation (chapitre 12, §12.5) |

---

## Exercices

1. **Faire, acheter ou réutiliser.** Un CubeSat 3U d'observation de la Terre a besoin d'une roue de réaction fournissant 10 mN m s. Options : une roue COTS (TRL 9, 8 k€, 10 semaines) ; une roue ayant volé lors d'une mission précédente de la même équipe, qui nécessite une nouvelle qualification de roulement (TRL 7, 4 k€ + 60 h de delta-qualification, 16 semaines) ; et une conception interne (TRL 3, 2 k€ + 600 h de NRE, 14 mois). Pour un taux chargé de 100 €/h, calculez le coût total de chaque option, appliquez le cadre de décision du §13.1.1 et énoncez la décision. Indiquez ensuite la seule circonstance dans laquelle l'option interne pourrait être la bonne réponse.

2. **TRL et risque.** À l'aide de $f_{\text{risk}} = 10^{-(\text{TRL}-1)/3}$, calculez le facteur de risque de chaque article de la nomenclature d'UniSat-1 (§13.6) et identifiez les deux composants qui représentent ensemble l'essentiel du risque cumulé. Proposez un plan d'essais de développement qui fait progresser chacun d'eux d'un niveau de TRL avant la CDR, et estimez la durée calendaire nécessaire.

3. **Cumul de la nomenclature.** Établissez le cumul de niveau 1 de la nomenclature pour la liste d'équipements d'EOSat-3U du chapitre 12, §12.5.2 : regroupez les composants par sous-système, totalisez la masse, la puissance de crête et le coût, ajoutez à la masse le faisceau (6 %) et les fixations (4 %), puis appliquez les marges de phase A du tableau 8.3 du chapitre 8. Comparez la MEV obtenue avec la limite de 6 kg de la CDS et avec les 5,17 kg du chapitre 12, §12.5.2, et expliquez l'écart.

4. **Le délai d'approvisionnement comme chemin critique.** À partir de la nomenclature d'UniSat-1, identifiez le délai d'approvisionnement le plus long, puis ajoutez 8 semaines d'inspection à réception et d'intégration et 6 semaines d'essais d'environnement. Si la date d'intégration sur le lanceur est dans 40 semaines, à quelle semaine au plus tard toutes les commandes doivent-elles être passées ? Quels sont les deux articles qui, avec quatre semaines de retard, feraient manquer le lancement ?

5. **Classification à l'exportation.** Classez chacun des éléments suivants pour une mission universitaire canadienne menée avec un partenaire polonais : (a) un senseur stellaire COTS de 5 secondes d'arc fabriqué aux États-Unis ; (b) un récepteur GNSS de fabrication européenne dont les limites COCOM n'ont pas été levées ; (c) un processeur LEON3 durci aux radiations ; (d) une bibliothèque de chiffrement AES libre ; (e) un magnétomètre de fabrication canadienne. Pour chacun, indiquez le régime probable (ITAR, EAR 9A515, EAR99 ou hors États-Unis), la démarche de licence et l'incidence sur le calendrier.

6. **Vérification de la chaîne RF.** Un CubeSat 3U retient un émetteur en bande S (50 Ω, SMA, 2 W) et, par erreur, un câble de 75 Ω. Calculez le coefficient de réflexion, l'affaiblissement de réflexion et la perte de désadaptation à l'entrée du câble. Puis, pour le bilan de liaison d'EOSat-3U du chapitre 11, §11.8.1, indiquez la marge que coûte cette désadaptation et si l'erreur aurait été détectée par le seul bilan de liaison.

7. **Interface électrique.** L'OBC retenu fournit un seul bus I²C à 3,3 V et des lignes commutées de 5 V limitées à 1,5 A. Le senseur stellaire candidat a besoin de 5 V avec un courant d'appel de 2,0 A et communique en RS-422. Dressez la liste de toutes les incompatibilités, proposez une correction pour chacune (changement de composant, adaptateur ou câblage) et indiquez quelles corrections ajoutent de la masse à la ligne « faisceau » de la nomenclature.

8. **Audit des interfaces à partir de la matrice N².** À l'aide du tableau 8.1 du chapitre 8 et des codes littéraux du tableau 8.2, dressez la liste de toutes les interfaces E, D et R du sous-système TTC dans la liste d'équipements d'EOSat-3U du chapitre 12, §12.5.2 et, pour chacune, indiquez le champ unique de la nomenclature (tension, protocole, connecteur, bande ou polarisation) qui doit concorder des deux côtés.

9. **Comparaison des coûts.** À partir de la synthèse des coûts d'UniSat-1 du §13.6 et du coût matériel d'EOSat-3U du chapitre 12, §12.5.2, estimez le coût total de la mission EOSat-3U en extrapolant chaque ligne hors matériel (logiciel, étalonnage, intégration et essais, station sol, lancement, gestion) à l'aide d'un facteur justifié, et comparez le résultat avec les ~490 k€ annoncés. Quelle ligne hors matériel est la plus sensible à vos hypothèses ?

10. **Concevoir pour l'approvisionnement.** Une opportunité de lancement partagé avance de six mois le lancement d'EOSat-3U. Quels choix du chapitre 12, §12.5.2 remplaceriez-vous par une solution à délai plus court ou à TRL plus élevé, à quelles performances renonceriez-vous, et comment le tableau de bouclage du chapitre 12, §12.5.3 évoluerait-il ?

---

## Références

1. NASA, *Technology Readiness Levels*, NPR 7123.1D, annexe E. https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/
2. ECSS, *ECSS-E-HB-11A : Technology Readiness Level (TRL) Guidelines*, 2017. https://ecss.nl
3. ECSS, *ECSS-Q-ST-20C Rev. 2 : Quality Assurance*, 2023. https://ecss.nl/standard/ecss-q-st-20c-rev-2-quality-assurance-1-march-2023/
4. ECSS, *ECSS-M-ST-10C Rev. 1 : Project Planning and Implementation*, 2009. https://ecss.nl
5. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §6.8. https://www.nasa.gov/reference/systems-engineering-handbook/
6. Département d'État des États-Unis, Directorate of Defense Trade Controls (ITAR, 22 CFR 120–130). https://www.pmddtc.state.gov/
7. Département du Commerce des États-Unis, Bureau of Industry and Security (EAR, 15 CFR 730–774). https://www.bis.doc.gov/
8. Services publics et Approvisionnement Canada, *Programme des marchandises contrôlées*. https://www.tpsgc-pwgsc.gc.ca/pmc-cgp/
9. Cal Poly, *CubeSat Design Specification Rev 14.1*, 2022. https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf
10. Wertz, J. R., Everett, D. F. & Puschell, J. J. (dir.), *Space Mission Engineering : The New SMAD*, Microcosm Press, 2011, chap. 14 et chap. 20.
11. Klesh, A. et al., « Mars Cube One (MarCO) — Lessons Learned », SSC19-WKII-07, 33rd Annual Small Satellite Conference, 2019.
12. Sarda, K. et al., « BRITE-Constellation Mission and Spacecraft », AIAA/USU Small Satellite Conference, 2014.
