# Chapitre 14 — Vérification et validation

> **Lectures préalables conseillées.** ECSS-E-ST-10-02C Rev. 1 (*Verification*) ; ECSS-E-ST-10-03C (*Testing*) ; NASA SEH Rev 2, §5.3–5.4 (vérification et validation des produits) ; MIL-STD-1540E (*Test requirements for launch, upper-stage and space vehicles*) ; MIL-STD-461G (EMI/CEM). Ce chapitre referme la branche droite du cycle en V présenté au chapitre 1 (figure 1.1) : les exigences du chapitre 5, chacune associée à une méthode de vérification, rencontrent désormais le matériel des chapitres 12 et 13. L'environnement de charges de lancement que reproduit le programme d'essais est décrit au chapitre 12, §12.1.5.

## Objectifs d'apprentissage

À la fin de ce chapitre, vous serez capable de :

1. distinguer la vérification de la validation à l'aide des définitions de l'ECSS et de la NASA ;
2. attribuer à chaque exigence, selon une logique de décision, une méthode de vérification appropriée — analyse, essai, inspection, revue de conception ou démonstration, ATIR(D) ;
3. définir les niveaux d'essais d'environnement à partir des spécifications d'interface du lanceur ;
4. construire une matrice de vérification de conformité reliant chaque exigence à sa méthode, à son niveau et à sa phase ;
5. déterminer quand une dérogation est appropriée et en documenter la justification.

---

## 14.1 Vérification ou validation : définitions précises

*[Source : ECSS-E-ST-10-02C Rev. 1, §4 et §5.2.2 ; NASA SEH Rev 2, §5.3 (Process 7 : Product Verification) et §5.4 (Process 8 : Product Validation)]*

| | **Vérification** | **Validation** |
|--|-----------------|----------------|
| **Question** | « Avons-nous construit le système correctement ? » | « Avons-nous construit le bon système ? » |
| **Contrôle par rapport à** | Les exigences (énoncés en « doit ») | Les besoins des parties prenantes et les attentes opérationnelles |
| **Norme** | ECSS-E-ST-10-02C | ECSS-E-ST-10-06C |
| **Réalisée par** | L'équipe d'ingénierie | Les utilisateurs, les opérateurs, les parties prenantes |
| **Moment** | Tout au long du développement (phases B–D) | Fin du développement + début de l'exploitation (phases D–E) |
| **Méthodes** | ATIR(D) : analyse, essai, inspection, revue de conception, démonstration | Démonstration opérationnelle, essais de recette par les utilisateurs |
| **Résultat** | Document de contrôle de la vérification (VCD) | Rapport de validation |

### 14.1.1 La distinction essentielle

Un système peut être **vérifié** (chaque exigence notée « conforme ») et pourtant **échouer à la validation** si les exigences ont été mal rédigées. Cela se produit lorsque :
- les exigences ont été dérivées de besoins des parties prenantes mal compris ;
- l'environnement opérationnel diffère des hypothèses ;
- des cas limites n'ont pas été pris en compte dans les exigences.

### 14.1.2 Exemple

- **Exigence :** « Le système doit atteindre une GSD ≤ 10 m depuis une altitude de 500 km. »
- **Vérification (essai) :** imagerie d'une cible d'étalonnage à 500 km → GSD mesurée = 9,2 m → **vérifiée**
- **Validation :** les utilisateurs tentent une évaluation des cultures avec des images à 9,2 m → « Nous voyons les limites des parcelles mais ne pouvons pas distinguer les types de cultures ; il nous fallait une GSD ≤ 5 m » → **non validée**

*L'exigence a été satisfaite, mais le besoin des parties prenantes ne l'a pas été, car l'exigence n'était pas assez stricte. C'est pourquoi l'analyse des parties prenantes et la hiérarchie MoE/MoP/TPM du chapitre 4 sont importantes : la validation ne vaut que ce que valent les besoins recueillis au départ.*

---

## 14.2 Les méthodes de vérification ATIR(D) en détail

La norme ECSS-E-ST-10-02C Rev. 1, §5.2.2.1, définit quatre méthodes de vérification — **essai, analyse, revue de conception et inspection** — et la pratique de la NASA y ajoute la **démonstration** comme cinquième méthode. Cet ouvrage abrège l'ensemble en **ATIR(D)**, le D étant entre parenthèses parce que l'ECSS compte la démonstration dans l'essai (« test (including demonstration) ») tandis que la NASA la présente à part. L'ordre des lettres varie d'un document à l'autre ; les méthodes sont les mêmes. Le chapitre 5, §5.5, a présenté le tableau à cinq lignes ; la présente section explique quand chaque méthode s'applique et quels éléments probants elle produit.

*[Source : ECSS-E-ST-10-02C Rev. 1, §5.2.2 ; NASA SEH Rev 2, §5.3.2]*

### 14.2.1 Analyse (A)

**Définition :** des modèles mathématiques, des simulations, des analyses statistiques ou une comparaison avec l'héritage démontrent la conformité avec un niveau de confiance acceptable. L'ECSS range la *vérification par similarité* (héritage) dans l'analyse.

**Quand l'utiliser :**
- lorsqu'un essai physique est impossible ou peu praticable (durée de vie orbitale, dose ionisante totale) ;
- au début du développement (phase B), avant que le matériel n'existe ;
- pour démontrer une marge (bilan de liaison, modèle thermique, analyse structurale par éléments finis) ;
- pour les paramètres statistiques (prévision de fiabilité, risque de victimes dû aux débris) ;
- pour les exigences relevant de la mécanique spatiale ou des performances au niveau de la mission.

**Éléments produits :** rapport d'analyse comprenant la description du modèle, les hypothèses, les données d'entrée, les résultats, l'évaluation des incertitudes et une analyse de sensibilité.

**Exemples pour les CubeSats :**
- analyse de mécanique spatiale → vérifie l'exigence de temps de revisite (chapitre 7) ;
- modèle thermique (différences finies ou éléments finis) → vérifie que les températures restent dans les limites (chapitre 9, §9.4) ;
- calcul du bilan de liaison → vérifie une marge ≥ 3 dB dans le cas le plus défavorable (chapitre 11) ;
- analyse structurale par éléments finis → vérifie une marge de sécurité positive sous les charges de lancement (chapitre 12, §12.1.6).

> **Marge de sécurité (structurale)** — la forme canonique est celle du chapitre 12, §12.1.6 :
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\text{FoS} \times \sigma_{\text{applied}}} - 1 \geq 0 \quad \text{pour tous les cas de charge}$$
> avec FoS = 1,25 (limite élastique) et 1,5 (rupture) pour une structure métallique selon l'ECSS-E-ST-32-10C. Un rapport d'analyse qui vérifie une exigence structurale donne la MoS pour chaque cas de charge, et pas seulement pour le plus défavorable.

### 14.2.2 Essai (T)

**Définition :** le matériel physique est soumis à des conditions maîtrisées ; les performances mesurées sont comparées quantitativement aux seuils exigés.

**Quand l'utiliser :**
- des propriétés physiques doivent être prouvées par une mesure quantitative ;
- la tenue à l'environnement doit être démontrée (vibrations, vide thermique, CEM) ;
- des chaînes fonctionnelles de bout en bout doivent être prouvées dans des conditions représentatives ;
- les performances doivent être mesurées, et pas seulement observées.

**Types d'essais selon leur finalité :**

| Type d'essai | Finalité | Niveau | Phase | Charges/conditions |
|-----------|---------|-------|-------|-----------------|
| **Développement** | Explorer l'espace de conception, détecter les problèmes tôt | Unité/maquette | B | Selon les besoins |
| **Qualification** | Prouver que la conception résiste au cas le plus défavorable + marge | Unité/système | C | Niveaux de qualification (MPE + marge) |
| **Recette** | Prouver que le matériel de vol est exempt de défauts | Système | D | Niveaux de recette (MPE) |
| **Protovol** | Qualification + recette combinées (unité unique) | Système | C/D | Niveaux de qualification, durées de recette |

*MPE = environnement maximal prévu (maximum predicted environment).*

**L'approche protovol.** Pour les CubeSats, l'approche **protovol** est la norme, car construire une unité de qualification distincte serait d'un coût prohibitif. Le modèle de vol est soumis aux **niveaux de qualification**, mais pendant les **durées de recette**.

*[Source : ECSS-E-ST-10-03C, §4.5.4 ; MIL-STD-1540E, §6.2.4]*

**Justification :** les durées de qualification sont plus longues et plus contraignantes — ce qui est acceptable pour un modèle de qualification dédié qui ne volera pas. En protovol, la durée plus courte limite la consommation de la durée de vie en fatigue tout en permettant de détecter les défauts de fabrication.

| Paramètre | Qualification | Recette | Protovol |
|-----------|-------------|-----------|-------------|
| Niveau de vibrations | MPE + 3 dB | MPE | MPE + 3 dB |
| Durée de vibrations | 2 min/axe | 1 min/axe | 1 min/axe |
| Plage de température en TVAC | Prévue ± 15 °C | Prévue ± 10 °C | Prévue ± 10 °C |
| Cycles de TVAC | 8 | 4 | 4 |
| Vitesse de balayage sinusoïdal | 2 oct/min | 4 oct/min | 4 oct/min |

Les niveaux de protovol suivent les normes. Le GSFC-STD-7000B §2.6 essaie une unité de protovol aux températures maximale et minimale prédites ± 10 °C, avec au moins 4 cycles ; l'ECSS-E-ST-10-03C atteint les mêmes 10 °C avec sa marge de recette de 5 °C et sa marge de qualification de 5 °C sur la plage prédite. L'ECSS-E-ST-10-03C balaie en sinus à 2 oct/min en qualification (tableau 5-2) et à 4 oct/min en recette (tableau 5-4), et le protovol reprend les durées de recette, d'où 4 oct/min. Les colonnes de température de qualification et de recette sont celles du chapitre 9, §9.4.11.

### 14.2.3 Inspection (I)

**Définition :** examen visuel ou physique du produit, sans fonctionnement ni stimulation, pour vérifier sa conformité aux exigences.

**Quand l'utiliser :**
- caractéristiques physiques (dimensions, masse, état de surface, étiquetage) ;
- qualité de fabrication (joints de brasure, cheminement des câbles, pose du MLI) ;
- marquages, identification et étiquettes de sécurité ;
- ajustement mécanique (conformité des rails au déployeur).

**Éléments produits :** rapport d'inspection avec photographies, mesures et liste de vérification conforme/non conforme.

**Exemples pour les CubeSats :**
- mesure de masse sur une balance étalonnée → vérifie « $M_{\text{dry}} \leq 4.0$ kg » ;
- mesure du profil des rails au pied à coulisse → vérifie la conformité dimensionnelle à la CDS (chapitre 12, §12.1.3) ;
- inspection visuelle du repliement de l'antenne → vérifie l'absence de protubérance au-delà de l'enveloppe du déployeur ;
- inspection de la qualité de fabrication des joints de brasure des circuits imprimés → vérifie la conformité à l'IPC-A-610 classe 3.

### 14.2.4 Revue de conception (R)

**Définition :** vérification par examen de la documentation de conception — plans, schémas, conception logicielle, analyses déjà réalisées, enregistrements de procédés — afin de confirmer que la conception telle que documentée satisfait l'exigence. Dans l'ECSS-E-ST-10-02C, il s'agit d'une méthode formelle à part entière, distincte de l'analyse : aucun nouveau modèle n'est construit ; l'élément probant est la conception documentée.

**Quand l'utiliser :**
- exigences portant sur l'existence ou le contenu d'un document, d'un processus ou d'un plan (« un plan de vérification doit être produit », « le logiciel doit être développé selon l'ECSS-E-ST-40C ») ;
- caractéristiques de conception évidentes à la lecture des plans (nombre d'interrupteurs de déploiement, présence d'une goupille RBF, brochage des connecteurs) ;
- exigences déjà couvertes par une conception héritée approuvée.

**Éléments produits :** procès-verbal de revue de conception citant les documents examinés, signé par le relecteur ; généralement clos lors d'une revue de conception (chapitre 16).

**Exemples pour les CubeSats :**
- examen du schéma de l'empilement → vérifie « deux interrupteurs de déploiement indépendants doivent inhiber toute alimentation » ;
- examen du document d'architecture logicielle → vérifie « le chien de garde doit être réalisé en matériel, indépendamment du processeur principal ».

### 14.2.5 Démonstration (D)

**Définition :** le système est mis en fonctionnement dans des conditions maîtrisées pour montrer qu'il fonctionne comme exigé, sans qu'il soit nécessaire de mesurer précisément ses paramètres de performance.

**Quand l'utiliser :**
- exigences fonctionnelles (« le système doit déployer l'antenne dans les 30 minutes suivant la séparation ») ;
- procédures opérationnelles (« le système doit répondre à une commande de changement de mode en moins de 5 secondes ») ;
- exigences fonctionnelles du logiciel (« la FDIR doit basculer de manière autonome en mode survie en cas de perte d'attitude »).

**Éléments produits :** rapport de démonstration avec procédure, observations, photographies ou vidéo et verdict conforme/non conforme.

**Exemples pour les CubeSats :**
- essai de déploiement de l'antenne → démontre le déploiement dans le délai imparti ;
- essai de passage en mode survie → démontre la réponse autonome de la FDIR (chapitre 18) ;
- essai de commande depuis la station sol → démontre la chaîne de commande complète (chapitre 17).

---

## 14.3 Programme d'essais d'environnement

*[Source : ECSS-E-ST-10-03C (Testing) ; manuels utilisateurs des lanceurs (payload user's guides) ; MIL-STD-1540E]*

### 14.3.1 Séquence type d'essais d'environnement

La séquence d'essais est conçue de sorte que chaque essai sollicite le matériel d'une manière spécifique, et les essais fonctionnels intercalés entre les essais d'environnement détectent tout dommage. La figure 14.1 présente la séquence habituelle pour un CubeSat protovol. Les niveaux des §14.3.2 à 14.3.4 sont des valeurs représentatives à des fins d'enseignement : les niveaux qui font foi pour un vol donné sont fixés par le manuel utilisateur du déployeur ou du lanceur.

![Enchaînement des essais d'environnement d'un CubeSat protovol](../assets/figures/fig_test_flow.png)

**Figure 14.1** — Séquence type d'essais d'environnement d'un CubeSat protovol. Des essais fonctionnels encadrent chaque essai d'environnement, de sorte que tout dommage soit imputé à l'essai qui l'a causé ; une anomalie constatée après les vibrations est analysée et résolue avant que le matériel n'entre dans l'enceinte de vide thermique. Les niveaux de qualification, de recette et de protovol du §14.2.2 sont indiqués en regard des étapes de vibrations et de vide thermique.

### 14.3.2 Niveaux des essais de vibrations sinusoïdales

*[Source : enveloppe représentative d'un lancement partagé de CubeSats ; le manuel utilisateur du déployeur ou du lanceur fixe les niveaux qui font foi]*

Les vibrations sinusoïdales simulent les modes structuraux basse fréquence du lanceur (généralement 5–100 Hz). Il s'agit de charges quasi statiques.

| Gamme de fréquences (Hz) | Niveau | Remarques |
|----------------------|-------|-------|
| 5–100 | 1,25 g (0-crête) | Pilotage en accélération sur toute la bande ; pas de bande en déplacement |
| Vitesse de balayage | 4 octaves/minute (protovol) | 2 oct/min est la vitesse de qualification |
| Axes | 3 (X, Y, Z) | Successivement, un axe à la fois |

> **Pourquoi il n'y a pas de bande en déplacement — la fréquence de transition :**
>
> Pour une sinusoïde, $a = (2\pi f)^2\, d$ ; la fréquence à laquelle une accélération donnée correspond à un déplacement donné est donc
>
> $$f_c = \frac{1}{2\pi}\sqrt{\frac{a}{d}}$$
>
> Pour $a = 1.25\,g_0 = 12.26$ m/s$^2$ et une limite de course de pot vibrant typique $d = 12.5$ mm $= 0.0125$ m :
> $f_c = \sqrt{12.26/0.0125}\,/\,2\pi = 31.3/6.283 = 4.98$ Hz $\approx 5$ Hz
>
> *En dessous d'environ 5 Hz, maintenir 1,25 g exigerait plus de 12,5 mm de déplacement ; un profil qui descend plus bas en fréquence a donc besoin d'une bande pilotée en déplacement. Ce profil commence à 5 Hz : il est piloté en accélération sur toute sa bande.*

### 14.3.3 Niveaux des essais de vibrations aléatoires

Les vibrations aléatoires simulent l'environnement acoustique et mécanique à large bande pendant le lancement. Les niveaux sont spécifiés sous forme de densité spectrale de puissance (DSP) en g$^2$/Hz. Le profil ci-dessous est le niveau minimal de qualité de fabrication des équipements du GSFC-STD-7000B (GEVS, tableau 2.4-4) ; le tableau 2.4-1 du GEVS fixe le niveau protovol à +3 dB pendant 1 minute par axe.

| Fréquence (Hz) | Niveau de DSP (g$^2$/Hz) | Remarques |
|----------------|---------------------|-------|
| 20 | 0,01 | Début du profil |
| 20–80 | Rampe à +3 dB/octave | Montée |
| 80–500 | 0,04 (palier) | Palier de niveau maximal |
| 500–2000 | Rampe à −3 dB/octave | Descente |
| 2000 | 0,01 | Fin du profil |
| **g$_{\text{rms}}$ global** | **6,8 g$_{\text{rms}}$** | Niveau de qualité de fabrication (recette) |
| **Protovol** | **+3 dB : 9,6 g$_{\text{rms}}$** | DSP doublée à toutes les fréquences ; 1 min par axe, 3 axes |

> **Calcul du g$_{\text{rms}}$ global à partir d'un profil de DSP :**
>
> $$g_{\text{rms}} = \sqrt{\int_{f_1}^{f_2} \text{PSD}(f)\, df}$$
>
> Pour une zone de DSP constante : $g_{\text{rms,flat}} = \sqrt{\text{PSD}_{\text{flat}} \times (f_2 - f_1)}$
>
> Exemple : DSP = 0,04 g$^2$/Hz de 80 à 500 Hz :
> $g_{\text{rms,flat}} = \sqrt{0.04 \times 420} = \sqrt{16.8} = 4.10$ g$_{\text{rms}}$
>
> Les contributions des rampes et du palier se combinent en somme quadratique :
> $$g_{\text{rms,total}} = \sqrt{g_{\text{rms,ramp1}}^2 + g_{\text{rms,flat}}^2 + g_{\text{rms,ramp2}}^2}$$
> Un segment en pente est une droite en coordonnées log–log, $\text{PSD}(f) = P_1 (f/f_1)^n$ avec $n = (\text{dB/oct})/3.01$, et s'intègre exactement en $\frac{P_1 f_1}{n+1}\left[(f_2/f_1)^{n+1} - 1\right]$ (ou $P_1 f_1 \ln(f_2/f_1)$ lorsque $n = -1$). La rampe montante ($n = +1$) donne $\frac{0.01 \times 20}{2}(4^2 - 1) = 1.50$ g$^2$, soit 1,22 g$_{\text{rms}}$, et la rampe descendante ($n = -1$) donne $0.04 \times 500 \times \ln 4 = 27.73$ g$^2$, soit 5,27 g$_{\text{rms}}$ ; d'où $g_{\text{rms,total}} = \sqrt{1.50 + 16.80 + 27.73} = \sqrt{46.03} = 6.78 \approx 6.8$ g$_{\text{rms}}$. En protovol (+3 dB, DSP × 2), $\sqrt{92.06} = 9.59 \approx 9.6$ g$_{\text{rms}}$.

### 14.3.4 Profil de l'essai de vide thermique

| Paramètre | Niveau protovol | Remarques |
|-----------|-------------------|-------|
| Température du cas chaud | Maximum prévu + 10 °C | P. ex. si le modèle thermique prévoit +55 °C → essai à +65 °C |
| Température du cas froid | Minimum prévu − 10 °C | P. ex. si le modèle thermique prévoit −20 °C → essai à −30 °C |
| Nombre de cycles | 4 (protovol) | Début et fin en chaud ; essai fonctionnel à chaque extrême |
| Niveau de vide | < 10$^{-5}$ mbar | Vide représentatif de l'espace |
| Durée de palier à l'extrême | ≥ 1 heure | Permettre la stabilisation thermique (gradient < 1 °C/h) |
| Vitesse de variation de température | 1–3 °C/min | Limitée par les capacités de l'enceinte |
| Essai fonctionnel | Performances complètes aux extrêmes chaud et froid | Fonctions partielles lors des transitions intermédiaires |

La bande de ± 10 °C du protovol est la marge de protovol du GSFC-STD-7000B §2.6 (§14.2.2) ; les extrêmes prévus proviennent des cas chaud et froid de l'analyse thermique.

> **Estimation de la durée d'un cycle de TVAC :**
>
> $$t_{\text{cycle}} = 2\,\frac{\Delta T}{\dot{T}_{\text{ramp}}} + 2\, t_{\text{dwell}} + 2\, t_{\text{functional}}$$
>
> Exemple : $\Delta T = 95$ °C (de −30 à +65 °C), rampe = 2 °C/min, palier = 1 h, essai fonctionnel = 2 h :
> $t_{\text{cycle}} = 2 \times (95/2) + 2 \times 60 + 2 \times 120 = 95 + 120 + 240 = 455$ min $\approx 7.6$ h
>
> Campagne de TVAC complète (4 cycles + mise en place) : $\approx 4 \times 7.6 + 8 = 38.4$ h $\approx$ 5 jours ouvrés de fonctionnement continu de l'enceinte.

### 14.3.5 Essais de CEM

*[Source : MIL-STD-461G ; ECSS-E-ST-20-07C]*

| Essai | Norme | Finalité |
|------|----------|---------|
| CE102 émissions conduites | MIL-STD-461G | Mesurer les émissions conduites parasites sur les lignes d'alimentation |
| RE102 émissions rayonnées | MIL-STD-461G | Mesurer le rayonnement RF non intentionnel du satellite |
| CS101 susceptibilité conduite | MIL-STD-461G | Vérifier l'immunité aux transitoires des lignes d'alimentation |
| RS103 susceptibilité rayonnée | MIL-STD-461G | Vérifier l'immunité aux champs RF extérieurs |

*Remarque : les essais de CEM ne sont pas toujours exigés pour les CubeSats. Cela dépend du fournisseur de lancement et des charges utiles embarquées sur le même vol. Consultez le document de contrôle d'interface du lancement partagé. Le couplage entre l'émetteur et la charge utile, identifié comme un point d'attention d'interface de type R au chapitre 8, §8.3.4, est le cas de CEM interne que traite un essai d'autocompatibilité.*

---

## 14.4 Construction de la matrice de vérification de conformité

La matrice de vérification (aussi appelée matrice de conformité ou matrice de références croisées de vérification, VCRM) est le document central qui relie chaque exigence aux éléments probants de sa vérification. Elle complète la matrice de vérification des exigences du chapitre 5, §5.5, par les colonnes de phase, de niveau, de responsable, de moyen et d'état nécessaires pour planifier et suivre la campagne.

*[Source : ECSS-E-ST-10-02C Rev. 1, §6 ; DRD en annexe A]*

### 14.4.1 Structure de la matrice

| Id. exigence | Texte de l'exigence | Méthode | Phase | Niveau | Responsable | Moyen | État | Éléments probants |
|--------|-----------------|--------|-------|-------|-------------|----------|--------|----------|
| SYS-001 | $M_{\text{dry}} \leq 4.0$ kg | I | D | Système | Structures | Salle blanche | Prévu | Rapport de mesure de masse |
| SYS-002 | Résister à 9,6 g$_{\text{rms}}$ en vibrations aléatoires (protovol) | T | C/D | Système | Structures | Laboratoire de vibrations | Prévu | Rapport d'essai de vibrations |
| SYS-003 | GSD ≤ 10 m à 500 km | A | B | Système | Charge utile | S. O. | Prévu | Rapport d'analyse optique |
| SYS-004 | Marge de liaison ≥ 3 dB | A | B | Système | Communications | S. O. | Prévu | Analyse du bilan de liaison |
| SYS-005 | Déploiement de l'antenne < 30 min | D | D | Système | Mécanismes | Salle blanche | Prévu | Démonstration de déploiement |
| SYS-006 | Deux interrupteurs de déploiement indépendants inhibent toute alimentation | R | B | Système | EPS | S. O. | Prévu | Revue du schéma de l'empilement |

### 14.4.2 Logique d'attribution des méthodes ATIR(D)

```
S'agit-il d'une propriété physique (masse, dimensions, état de surface) ?
  → Inspection (I), phase D, niveau système

Ne peut-elle être prouvée que par une mesure quantitative en conditions maîtrisées ?
  → Essai (T), phase C/D, niveau équipement ou système

Peut-elle être démontrée en faisant fonctionner le système (fonctionnel, pas de précision) ?
  → Démonstration (D), phase D, niveau système
    (l'ECSS la consigne comme un essai sans mesure quantitative)

Peut-elle être établie avec une confiance suffisante par modélisation ou similarité ?
  → Analyse (A), phase B/C, niveau système

S'agit-il d'un document, d'un processus, d'un plan ou d'une caractéristique visible sur les plans ?
  → Revue de conception (R), phase B
```

### 14.4.3 Méthodes multiples

Certaines exigences nécessitent **à la fois** une analyse (confiance précoce) et un essai (preuve finale) :

| Exigence | Analyse (phase B) | Essai (phase C/D) |
|------------|-------------------|------------------|
| Tenue structurale sous les charges de lancement | Analyse par éléments finis avec MoS positive | Essai de vibrations — aucun dommage |
| Précision de pointage ≤ 0,1° | Analyse du bilan d'erreurs (chapitre 10, §10.4) | Mesure d'étalonnage en orbite |
| Températures dans les limites (−20 à +55 °C) | Simulation par modèle thermique | Essai fonctionnel en TVAC aux extrêmes |
| Marge de liaison RF ≥ 3 dB | Calcul du bilan de liaison | Essai de compatibilité RF (si réalisable) |

Dans la matrice, indiquez la méthode **principale** et ajoutez la mention « confirmé par [méthode secondaire] en phase [X] ».

### 14.4.4 Processus de dérogation

Lorsqu'une exigence ne peut pas être vérifiée par la méthode prescrite, ou ne peut pas être satisfaite, une **dérogation** est nécessaire :

| Type de dérogation | Cas d'utilisation | Niveau d'approbation |
|-------------|-----------|---------------|
| **Non-conformité** | L'exigence ne peut pas être satisfaite ; l'écart est accepté | Chef de projet + client |
| **Écart de méthode** | Une autre méthode de vérification est employée (p. ex. analyse au lieu d'essai) | Ingénieur système + qualité |
| **Adaptation** | Exigence normative non applicable à cette mission | Ingénieur système |

**La documentation d'une dérogation doit comprendre :** l'identifiant de l'exigence, la description de l'écart, la justification technique, l'évaluation du risque (dans les termes du chapitre 15) et les mesures compensatoires.

---

## 14.5 Retour sur UniSat-1 : une matrice de vérification

Les exigences ci-dessous sont tirées des exemples UniSat-1 des chapitres 5, 9, 11 et 12. Une méthode est attribuée à chacune selon la logique du §14.4.2.

| Id. exigence | Exigence | Méthode | Phase | Niveau | Éléments probants |
|--------|-------------|--------|-------|-------|----------|
| US-SYS-001 | Masse humide ≤ 1,33 kg (limite du déployeur) | I | D | Système | Mesure sur balance étalonnée |
| US-SYS-002 | Conformité à l'enveloppe 1U et au profil de rails de la CDS Rev 14 | I | D | Système | Rapport de mesure au pied à coulisse et au calibre de profil ; essai d'ajustement dans le déployeur |
| US-STR-001 | Premier mode structural > 90 Hz | A, confirmé par T | B / C | Système | Analyse modale ; balayage sinusoïdal bas niveau avant les vibrations aléatoires |
| US-STR-002 | Résister sans dégradation à 9,6 g$_{\text{rms}}$ (protovol) en vibrations aléatoires | T | C/D | Système | Comparaison fonctionnelle avant/après, rapport d'essai de vibrations |
| US-EPS-001 | Deux interrupteurs de déploiement et une goupille RBF inhibent toute alimentation | R, confirmé par D | B / D | Système | Revue du schéma ; démonstration d'inhibition avec interrupteurs enfoncés |
| US-COM-001 | Marge de liaison descendante ≥ 3 dB à 10° d'élévation | A | B | Système | Bilan de liaison (chapitre 11, §11.8.2) |
| US-COM-002 | Déploiement de l'antenne dans les 30 min suivant le relâchement de l'interrupteur de séparation | D | D | Système | Démonstration chronométrée du déploiement (3 répétitions) |
| US-THM-001 | Température de la batterie dans les limites de charge de 0–45 °C dans tous les modes | A, confirmé par T | B / C | Système | Analyse thermique (chapitre 9, §9.5) ; TVAC avec surveillance de la température de la batterie |
| US-PL-001 | Bruit du magnétomètre < 10 nT/√Hz à 1 Hz | T | C | Unité | Mesure en laboratoire dans une enceinte blindée |
| US-OPS-001 | Passage autonome en mode survie en cas de sous-tension du bus | D | D | Système | Démonstration par injection de pannes avec le logiciel de vol |

Deux caractéristiques de ce tableau méritent d'être soulignées. D'abord, les seules exigences qui nécessitent les moyens d'essais d'environnement du §14.3 sont US-STR-002 et US-THM-001 : une seule campagne de vibrations et de TVAC d'environ deux semaines vérifie les deux, et c'est pourquoi ces essais dominent le calendrier et le coût de la vérification d'une petite mission. Ensuite, les deux articles « faits » du chapitre 13, §13.6 (l'OBC et la carte magnétomètre) portent l'essai au niveau unité et la démonstration par injection de pannes ; le risque lié au TRL identifié là-bas est levé ici par des éléments probants.

---

## Synthèse

| Thème | Point clé à retenir |
|-------|-------------|
| Vérification ou validation | Vérification = satisfait les exigences (ATIR(D)) ; validation = répond aux besoins des parties prenantes |
| ATIR(D) | Analyse (modèles et similarité), essai (quantitatif), inspection (physique), revue de conception (documents et plans), démonstration (fonctionnelle) |
| Protovol | CubeSats : un modèle de vol unique soumis aux niveaux de qualification, avec les durées de recette |
| Vibrations sinusoïdales | 5–100 Hz, 1,25 g, 4 oct/min en protovol (2 oct/min en qualification), 3 axes, pas de bande en déplacement (transition $f_c = \sqrt{a/d}/2\pi \approx 5$ Hz à 12,5 mm) ; charges de lancement quasi statiques |
| Vibrations aléatoires | 20–2000 Hz, 6,8 g$_{\text{rms}}$ (qualité de fabrication du GEVS, $g_{\text{rms}} = \sqrt{\int \text{PSD}\, df}$) ; protovol à +3 dB, environ 9,6 g$_{\text{rms}}$, 1 min par axe |
| TVAC | Protovol à la prévision ± 10 °C (GSFC-STD-7000B / ECSS-E-ST-10-03C), 4 cycles, essai fonctionnel à chaque extrême ; ~7,6 h par cycle |
| Matrice de conformité | Pour chaque exigence : méthode + phase + niveau + responsable + moyen + état + éléments probants |
| Dérogations | Documenter l'écart, la justification, le risque et les mesures compensatoires |

---

## Exercices

1. **Vérification ou validation ?** Pour chacune des activités suivantes, indiquez s'il s'agit d'une activité de vérification ou de validation et justifiez votre choix en une phrase : (a) la mesure de la masse sèche du modèle de vol ; (b) l'évaluation d'une image d'échantillon par un utilisateur agricole ; (c) l'exécution du modèle thermique pour le cas chaud ; (d) une répétition des opérations de 30 jours avec des anomalies simulées (chapitre 19) ; (e) la confirmation que la GSD des images acquises en orbite est de 9,2 m.

2. **Attribution des méthodes.** Attribuez une méthode ATIR(D) principale, une phase et un niveau à chacune des exigences suivantes d'EOSat-3U, selon la logique du §14.4.2, et indiquez les éléments probants produits : (a) le satellite doit offrir une marge de liaison ≥ 3 dB à 10° d'élévation ; (b) les générateurs solaires doivent se déployer dans les 10 minutes suivant la séparation ; (c) l'axe de visée du senseur stellaire doit être aligné sur la charge utile à 1 minute d'arc près ; (d) le logiciel de vol doit être développé selon l'ECSS-E-ST-40C ; (e) le satellite doit être désorbité dans les 5 ans suivant la fin de mission ; (f) toutes les surfaces extérieures doivent être anodisées ou revêtues d'une finition à faible dégazage.

3. **Analyse et essai.** Choisissez trois exigences d'EOSat-3U qui nécessitent à la fois une analyse en phase B et un essai en phase C/D et, pour chacune, expliquez ce que l'analyse peut et ne peut pas établir, ce que l'essai apporte, et ce qu'il advient de la matrice si l'essai est supprimé pour raisons de coût.

4. **Profil sinusoïdal.** Un fournisseur de lancement spécifie un déplacement de 10 mm (0-crête) à partir de 4 Hz et 2,0 g (0-crête) jusqu'à 100 Hz. Calculez la fréquence de transition à laquelle les deux limites coïncident, ainsi que l'accélération que subirait le spécimen d'essai à 4 Hz si la limite en déplacement y était appliquée. Expliquez pourquoi le pilote doit passer du pilotage en déplacement au pilotage en accélération.

5. **g$_{\text{rms}}$ en vibrations aléatoires.** Un déployeur spécifie un profil aléatoire de 0,02 g$^2$/Hz constant de 20 à 1000 Hz, décroissant à −6 dB/octave jusqu'à 2000 Hz. Calculez le g$_{\text{rms}}$ du palier puis, en assimilant la rampe descendante à une droite en DSP linéaire, estimez sa contribution et le g$_{\text{rms}}$ global. Ce niveau est-il supérieur ou inférieur au profil de qualité de fabrication de 6,8 g$_{\text{rms}}$ du §14.3.3 ?

6. **Planification de la TVAC.** L'analyse thermique d'EOSat-3U (chapitre 9, §9.4) prévoit de −15 °C à +50 °C au niveau de la batterie. Indiquez les températures d'essai protovol, puis calculez la durée d'un cycle pour une enceinte à 1,5 °C/min, des paliers de 1 h et des essais fonctionnels de 90 minutes, ainsi que la durée totale de la campagne pour six cycles plus 8 h de mise en place. Si l'enceinte coûte 2 k€ par jour (indicatif), quel est le coût de la campagne, et comment se compare-t-il au budget d'intégration et d'essais d'UniSat-1 du chapitre 13, §13.6 ?

7. **Séquence d'essais.** Expliquez pourquoi l'essai de vibrations aléatoires précède la TVAC au §14.3.1 et pourquoi un essai fonctionnel s'intercale entre les deux. Que perdrait-on si l'ordre était inversé ? Citez un défaut que les vibrations révèlent mais pas la TVAC, et un défaut que la TVAC révèle mais pas les vibrations.

8. **Protovol ou modèle de qualification.** Deux options s'offrent à une mission : construire un modèle de qualification et le soumettre aux niveaux et durées de qualification complets (ce qui ajoute 60 k€ et 4 mois), ou soumettre le modèle de vol unique à des essais protovol. Énumérez les risques associés à chaque option, et tranchez pour (a) UniSat-1 et (b) une mission commerciale 12U embarquant une charge utile de 2 M€. Justifiez chaque décision au regard de l'échelle de conséquence du chapitre 15.

9. **Dérogation.** L'essai de CEM d'EOSat-3U (RE102) ne peut pas être réalisé, faute d'enceinte disponible avant l'expédition. Rédigez la dérogation : identifiant de l'exigence, écart, justification technique fondée sur le chapitre 8, §8.3.4 et sur le chapitre 11, évaluation du risque sur la matrice 5×5 du chapitre 15, et deux mesures compensatoires.

10. **Audit d'une matrice de conformité.** La matrice de vérification d'un CubeSat 6U comporte 142 exigences : 61 vérifiées par analyse, 48 par essai, 20 par inspection, 9 par revue de conception et 4 par démonstration. Douze exigences n'ont aucune méthode, et six entrées « essai » n'indiquent aucun moyen. Dressez la liste des questions qu'un relecteur devrait poser à la CDR (chapitre 16), et estimez combien d'exigences peuvent être closes avant le début de la campagne d'essais d'environnement.

---

## Références

1. ECSS, *ECSS-E-ST-10-02C Rev. 1 : Verification*, 2018. https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification/
2. ECSS, *ECSS-E-ST-10-03C : Testing*, 2012. https://ecss.nl/standard/ecss-e-st-10-03c-testing/
3. ECSS, *ECSS-E-ST-10-06C : Technical Requirements Specification*, 2009. https://ecss.nl
4. ECSS, *ECSS-E-ST-32-10C Rev. 2 : Structural Factors of Safety for Spaceflight Hardware*, 2019. https://ecss.nl
5. ECSS, *ECSS-E-ST-20-07C Rev. 2 : Electromagnetic Compatibility*, 2022. https://ecss.nl
6. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §5.3–5.4. https://www.nasa.gov/reference/systems-engineering-handbook/
7. Département de la Défense des États-Unis, *MIL-STD-1540E : Test Requirements for Launch, Upper-Stage and Space Vehicles*. https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36197
8. Département de la Défense des États-Unis, *MIL-STD-461G : Requirements for the Control of Electromagnetic Interference Characteristics of Subsystems and Equipment*. https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35789
9. NASA, *General Environmental Verification Standard (GEVS)*, GSFC-STD-7000B, 2021.
10. Cal Poly, *CubeSat Design Specification Rev 14.1*, 2022. https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf
11. SpaceX, *Rideshare Payload User's Guide*, 2024 (spécification d'interface représentative d'un lanceur). https://www.spacex.com/rideshare/
