# Chapitre 2 — L'écosystème spatial canadien et son cadre réglementaire

> **Lectures préalables conseillées.** NASA *Systems Engineering Handbook* §4.1 (attentes des parties prenantes) ; SMAD4, chap. 1 (objectifs de mission) ; les lois canadiennes citées dans les références, en particulier la Loi sur les systèmes de télédétection spatiale et la Loi sur la radiocommunication. Ce chapitre s'appuie sur les phases du cycle de vie et les jalons de revue du chapitre 1.

## Objectifs d'apprentissage

À l'issue de ce chapitre, vous serez capable de :

1. Décrire le mandat et la structure organisationnelle de l'Agence spatiale canadienne
2. Cartographier l'écosystème de l'industrie spatiale canadienne — maîtres d'œuvre, PME, universités et programmes de financement
3. Identifier les organismes de réglementation qui encadrent les activités spatiales au Canada (ASC, ISDE, AMC, MDN)
4. Expliquer la procédure de licence de la LSTS pour les satellites de télédétection
5. Décrire la procédure de licence de spectre auprès d'ISDE et la coordination avec l'UIT
6. Identifier les obligations canadiennes en matière de contrôle des exportations au titre de la LLEI, de l'ITAR et de l'EAR

---

## 2.1 L'Agence spatiale canadienne

### 2.1.1 Mandat et historique

L'Agence spatiale canadienne (ASC) a été créée par la *Loi sur l'Agence spatiale canadienne* (L.C. 1990, ch. 13) avec pour mission de « promouvoir l'exploitation et l'usage pacifiques de l'espace, de faire progresser la connaissance de l'espace au moyen de la science et de faire en sorte que les Canadiens tirent profit des sciences et techniques spatiales sur les plans tant social qu'économique ».

| Jalon | Année | Portée |
|-----------|------|-------------|
| Alouette 1 | 1962 | Le Canada devient la 3e nation à concevoir et construire un satellite |
| Hermes (CTS) | 1976 | Premier satellite de radiodiffusion directe de forte puissance au monde (ASC/NASA) |
| Canadarm | 1981 | Bras robotique de la navette spatiale ; assoit la domination du Canada en robotique spatiale |
| Création de l'ASC | 1990 | La Loi sur l'Agence spatiale canadienne crée l'agence |
| RADARSAT-1 | 1995 | Premier satellite canadien d'observation de la Terre ; radar à synthèse d'ouverture en bande C |
| Canadarm2 | 2001 | Bras robotique de l'ISS ; prolonge l'héritage en robotique |
| RADARSAT-2 | 2007 | Satellite radar commercial (MDA) ; la LSTS s'applique |
| Mission de la Constellation RADARSAT (RCM) | 2019 | Trois satellites radar en bande C ; surveillance maritime, gestion des catastrophes |
| Participation au Lunar Gateway | 2019–2026 | Le Canada s'est engagé comme partenaire ; en mars 2026, la NASA a suspendu le Gateway « dans sa forme actuelle » (suspension largement présentée comme une annulation) au profit d'une base à la surface lunaire |
| Canadarm3 | En développement | Robotique autonome de nouvelle génération entreprise pour le Lunar Gateway ; fin 2026, l'ASC la réoriente vers les opérations à la surface lunaire dans le cadre d'Artemis |

[Source : ASC, « Jalons spatiaux du Canada », www.asc-csa.gc.ca ; situation du Gateway et de Canadarm3 fin 2026 d'après les références 12–13]

### 2.1.2 Axes d'action de l'ASC

L'ASC a son siège à Saint-Hubert (Québec) et organise ses activités autour de trois priorités stratégiques :

| Priorité | Activités | Programmes clés |
|----------|-----------|-------------|
| **Exploration spatiale** | Exploitation de l'ISS, exploration lunaire Artemis (technologies Canadarm3 réorientées vers les opérations à la surface lunaire), programme des astronautes | Programme d'accélération de l'exploration lunaire (LEAP) |
| **Utilisation de l'espace** | Observation de la Terre, télécommunications par satellite, renforcement des GNSS | RADARSAT, SmartEarth, télésanté |
| **Sciences et technologies spatiales** | Astronomie, planétologie, développement technologique | CASTOR, JWST/NIRISS, santé dans l'espace |

### 2.1.3 Stratégie spatiale canadienne (2019)

La stratégie *Exploration, imagination, innovation : une nouvelle stratégie spatiale pour le Canada* (2019) a engagé 2,05 G$ sur 24 ans et fixé cinq priorités :

1. Garantir la santé et le bien-être des astronautes dans l'espace lointain
2. Développer et utiliser l'IA et la robotique avancées dans l'espace
3. Relier les Canadiens des régions rurales et éloignées grâce aux télécommunications par satellite de nouvelle génération
4. Utiliser les données et les technologies spatiales pour gérer durablement les ressources naturelles
5. Préparer l'avenir du secteur spatial canadien

> **Pratique industrielle.** Le Programme d'accélération de l'exploration lunaire (LEAP), doté de 150 M$, cible spécifiquement les PME et les universités canadiennes pour développer des technologies destinées aux sciences de la surface lunaire, à la santé, à l'IA et à la robotique. Ce modèle d'« entraînement » — dans lequel un investissement public stratégique crée des débouchés pour l'industrie — est une caractéristique de l'écosystème spatial canadien.

---

## 2.2 Cartographie de l'industrie spatiale canadienne

### 2.2.1 Structure de l'industrie

L'industrie spatiale canadienne a généré un chiffre d'affaires d'environ 2,7 G$ (2022) et emploie env. 12 000 personnes. Elle est structurée en niveaux ; une carte représentative des organisations avec lesquelles une mission canadienne est en relation est présentée à la figure 2.1.

![Carte représentative des parties prenantes des missions spatiales canadiennes : agence, maîtres d'œuvre, fournisseurs de sous-systèmes, PME, milieu universitaire et organismes de réglementation.](../assets/figures/fig_canadian_sector.png)

**Figure 2.1** — Carte représentative des parties prenantes des missions canadiennes : l'agence et les organismes de financement, les niveaux de l'industrie, le milieu universitaire et les organismes de réglementation auxquels une mission doit s'adresser.

| Niveau | Rôle | Principaux acteurs | Part du chiffre d'affaires |
|------|------|-------------|--------------|
| **Niveau 1 : maîtres d'œuvre** | Intégration de systèmes, grandes plateformes, exploitation de constellations | MDA Space, Telesat, SFL (U of T) | env. 60 % |
| **Niveau 2 : sous-systèmes et composants** | Conception de sous-systèmes, composants spécialisés, systèmes sol | Honeywell Canada, ABB, Magellan Aerospace, NGC Aerospace | env. 25 % |
| **Niveau 3 : PME et jeunes pousses** | Technologies de niche, applications, analyse de données | GHGSat, NorthStar, Kepler Communications, Wyvern | env. 10 % |
| **Niveau 4 : milieu universitaire** | R-D, formation, incubation technologique | U of T (SFL), York U, UBC, U of Calgary, Western | env. 5 % |

Les noms d'entreprises cités dans ce chapitre sont des exemples représentatifs et non des recommandations.

### 2.2.2 Principales capacités spatiales canadiennes

Le Canada dispose de capacités de premier plan mondial dans plusieurs domaines :

| Capacité | Acteur(s) principal(aux) | Missions marquantes | Position mondiale |
|-----------|--------------|-----------------|----------------|
| **Robotique spatiale** | MDA Space | Canadarm, Canadarm2, Dextre, Canadarm3 | Leader mondial |
| **Observation de la Terre par radar à synthèse d'ouverture** | MDA Space, ASC | RADARSAT-1/2/RCM | Parmi les 3 premiers mondiaux |
| **Télécommunications par satellite** | Telesat | Flotte Anik, Telesat Lightspeed (constellation LEO) | Pionnier de la radiodiffusion directe (DBS) en GEO |
| **Systèmes de petits satellites** | SFL (U of T) | MOST, NEOSSat, GHGSat-D, BRITE | Premier laboratoire universitaire au monde |
| **Surveillance des GES** | GHGSat | Constellation GHGSat (méthane) | Seule constellation commerciale de surveillance des GES au monde |
| **Instruments optiques** | ABB, Honeywell | JWST/FGS-NIRISS, altimètre laser d'OSIRIS-REx | Fabricant d'instruments de rang 1 |
| **Senseurs stellaires/SCAO** | NGC Aerospace/Honeywell | Nombreuses missions | Capteurs largement utilisés |

### 2.2.3 Programmes de financement

Les activités spatiales canadiennes sont financées par plusieurs mécanismes (montants indicatifs, 2026) :

| Programme | Géré par | Périmètre | Montant type |
|---------|----------------|-------|--------------|
| **Programme de développement des technologies spatiales (PDTS)** | ASC | Progression en TRL vers l'héritage en vol | 100 k$ à 3 M$ par projet |
| **Subventions et contributions par catégorie** | ASC | Sciences spatiales, sensibilisation, STIM | Variable |
| **LEAP** | ASC | Développement de technologies lunaires | Jusqu'à 3 M$ par projet |
| **PARI** | CNRC | Soutien à l'innovation des PME | 50 k$ à 1 M$ |
| **FSI** | ISDE | Projets d'innovation stratégiques | 10 M$ à 100 M$ et plus |
| **Contrats de RDDC** | MDN | Technologies à double usage | Classifié à 10 M$ |
| **CRSNG / FCI** | Fédéral | Infrastructures de recherche universitaire | 50 k$ à 5 M$ |

> **Pratique industrielle.** GHGSat (Montréal) est passée d'un démonstrateur technologique financé par l'ASC (GHGSat-D « Claire », lancé en 2016) à une constellation commerciale de plus de 12 satellites qui surveillent les émissions de méthane d'installations industrielles individuelles. Cette trajectoire — un financement public d'amorçage qui permet une montée en échelle commerciale — est le modèle de croissance canonique de l'industrie spatiale canadienne.

---

## 2.3 Comparaison avec d'autres modèles nationaux

Pour comprendre l'écosystème spatial canadien, il faut le comparer à celui des agences partenaires :

| Paramètre | Canada (ASC) | États-Unis (NASA) | Europe (ESA) | Japon (JAXA) |
|-----------|-------------|-----------|-------------|-------------|
| Budget annuel (approx.) | env. 300 M$ CA | env. 25 G$ US | env. 7,5 G€ | env. 1,5 G$ US |
| Effectifs | env. 670 | env. 18 000 | env. 2300 | env. 1500 |
| Capacité de lancement | Aucune (recours aux partenaires) | SLS, lanceurs commerciaux (SpaceX, ULA) | Ariane 6, Vega-C | H3, Epsilon |
| Point fort | Robotique, radar à synthèse d'ouverture, instruments | Spectre complet | Sciences, observation de la Terre, navigation | Fusées, sciences, ISS (Kibo) |
| Modèle industriel | Amorçage public + montée en échelle commerciale | Maîtrise d'œuvre publique + commercial | *Juste retour* (retour géographique) | Pilotage public + commercial |

L'absence de capacité de lancement nationale signifie que tous les satellites canadiens sont lancés par des lanceurs étrangers, ce qui a des conséquences en matière de contrôle des exportations (§2.8).

---

## 2.4 Le spatial canadien dans le contexte international

### 2.4.1 Partenariats internationaux

Le Canada participe aux activités spatiales dans le cadre d'accords multilatéraux et bilatéraux :

| Partenariat | Contribution canadienne | Retombées pour le Canada |
|------------|----------------------|-----------------|
| **ISS** | Canadarm2, Dextre, SPDM | Accès des astronautes, temps de recherche, démonstrations technologiques |
| **Artemis** (Lunar Gateway jusqu'à sa suspension en mars 2026) | Canadarm3, réorienté vers les opérations à la surface lunaire (2026) | Vols d'astronautes, accès aux sciences lunaires |
| **Copernicus (ESA)** | Accord d'accès aux données | Accès gratuit aux données Sentinel pour les utilisateurs canadiens |
| **COSPAS-SARSAT** | Stations sol canadiennes, charges utiles MEOSAR | Capacité de recherche et sauvetage sur le territoire canadien |
| **Groupe des cinq (Five Eyes)** | Partage du renseignement, technologies à double usage | Accès aux capacités de renseignement spatial alliées |

### 2.4.2 La stratégie canadienne de niche

Le Canada a historiquement suivi une stratégie d'« excellence de niche » : plutôt que de viser une capacité spatiale complète, il développe une expertise de classe mondiale dans des domaines précis (robotique, radar à synthèse d'ouverture, instruments) et échange l'accès à ces capacités contre une participation à des programmes plus vastes.

> **Équation clé.** Le « ratio de levier des partenariats » — informel mais utile — décrit la manière dont le Canada échange des capacités contre un accès :
>
> $$L = \frac{V_{\text{access}}}{C_{\text{contribution}}}$$
>
> où $V_{\text{access}}$ est la valeur de l'accès au programme obtenu et $C_{\text{contribution}}$ le coût de la contribution canadienne. Pour l'ISS, la contribution canadienne Canadarm2/Dextre (env. 2 G\$ CA sur 30 ans) donne accès à un programme de plus de 150 G\$, d'où $L \approx 75$. C'est le ratio de levier le plus élevé de tous les partenaires de l'ISS.

---

## 2.5 Vue d'ensemble du cadre réglementaire

Les activités spatiales au Canada relèvent de plusieurs organismes fédéraux. Il n'existe pas de « loi sur l'espace » unique — la réglementation est au contraire répartie entre plusieurs lois. La figure 2.2 présente les organismes auxquels une même activité spatiale doit satisfaire et la loi que chacun applique ; le tableau ci-dessous en donne le détail.

![Cadre réglementaire spatial canadien : un nœud central « activité spatiale » relié aux cinq organismes fédéraux de réglementation et à trois instances internationales.](../assets/figures/fig_regulatory_framework.png)

**Figure 2.2** — Le cadre réglementaire spatial canadien. Une même activité spatiale est encadrée par cinq organismes fédéraux au titre de lois distinctes (ASC, ISDE, AMC, MDN/RDDC et, pour le lancement, Transports Canada à l'avenir), tandis que les instruments internationaux de l'UIT, du CUPEEA de l'ONU et du MTCR s'appliquent à la mission par l'intermédiaire d'ISDE, des obligations conventionnelles et de la Liste des marchandises et technologies d'exportation contrôlée gérée par AMC.

| Organisme de réglementation | Loi | Objet de la réglementation | Pertinence pour la conception de mission |
|----------------|---------|-------------------|---------------------------|
| **ASC** | Loi sur l'Agence spatiale canadienne | Coordination du programme spatial, politique | Approbation des missions, financement |
| **ISDE** | Loi sur la radiocommunication | Attribution du spectre radioélectrique, licences | Licences de fréquences pour toutes les émissions RF |
| **ISDE** | Loi sur les systèmes de télédétection spatiale (LSTS) | Exploitation des satellites de télédétection | Licence pour tout satellite qui prend des images de la Terre |
| **AMC** | Loi sur les licences d'exportation et d'importation (LLEI) | Contrôle des exportations de marchandises stratégiques | Licences d'exportation pour les technologies satellitaires |
| **AMC** | Programme des marchandises contrôlées | Accès aux marchandises contrôlées (ITAR/MC) | Habilitations de sécurité du personnel |
| **MDN/RDDC** | Loi sur la défense nationale | Technologies à double usage, spatial militaire | Classification, exigences de sécurité |
| **Transports Canada** | (Aucune loi actuellement) | Opérations de lancement (à venir) | Le Canada n'a pas encore de réglementation nationale des lancements |

---

## 2.6 Loi sur les systèmes de télédétection spatiale (LSTS)

### 2.6.1 Objet et champ d'application

La LSTS (L.C. 2005, ch. 45) encadre l'exploitation de satellites de télédétection depuis le Canada. Elle a été adoptée principalement en réponse à la commercialisation de RADARSAT-2 (le premier satellite commercial canadien d'observation de la Terre) et répond à des préoccupations de sécurité nationale et de politique étrangère liées à l'imagerie de la Terre.

[Source : Gouvernement du Canada, LSTS, https://laws-lois.justice.gc.ca/eng/acts/r-5.4/]

### 2.6.2 Qui doit obtenir une licence ?

Une licence au titre de la LSTS est exigée de toute personne ou entité qui :

- **exploite** un système de télédétection spatiale depuis le Canada, ou
- **contrôle** la collecte ou la diffusion de données de télédétection issues d'un système canadien.

Cela s'applique quel que soit le lieu de fabrication ou de lancement du satellite. S'il est exploité depuis le territoire canadien, la LSTS s'applique.

### 2.6.3 Catégories de licences et conditions

| Type de licence | Périmètre | Conditions habituelles |
|-------------|-------|-------------------|
| **Licence d'exploitation de système** | Exploiter un système satellitaire de télédétection | Plan de gestion des données, accès prioritaire du gouvernement canadien, dispositions d'interruption de service (*shutter control*) |
| **Accords d'interopérabilité** | Partager des données avec des entités étrangères | Approbation pour chaque gouvernement ou partenaire commercial étranger |

Principales conditions habituellement imposées :

| Condition | Description | Justification |
|-----------|-------------|-----------|
| **Accès prioritaire** | Le gouvernement du Canada peut demander l'imagerie prioritaire de n'importe quelle zone | Sécurité nationale |
| **Interruption de service** | Le gouvernement peut restreindre l'imagerie de zones déterminées | Sécurité nationale, relations diplomatiques |
| **Sort des données** | Plan approuvé de stockage, de diffusion et de destruction des données | Empêcher tout accès non autorisé |
| **Retrait du système** | Plan de mise hors service en fin de vie | Atténuation des débris spatiaux |
| **Protection des données brutes** | Restrictions sur la diffusion des données non traitées | Empêcher le contournement des contrôles |

### 2.6.4 Conséquences pour les missions CubeSat et universitaires

Même les petites missions CubeSat équipées de caméras doivent se conformer à la LSTS si elles produisent des images de la Terre. Points clés à considérer :

| Paramètre | Seuil | Conséquence |
|-----------|-----------|------------|
| GSD | Aucun seuil formel dans la Loi | Toutes les résolutions exigent une licence |
| Type d'orbite | Toute orbite permettant d'imager la Terre | LEO, MEO, GEO sont toutes concernées |
| Diffusion des données | Toute diffusion d'images | Un plan de gestion des données approuvé est obligatoire |
| Participation étrangère | Tout accès étranger aux données | Exige un accord d'interopérabilité |

> **Pratique industrielle.** RADARSAT-2, de MDA, est exploité sous une licence LSTS qui comporte des dispositions d'interruption de service. Lors des secours après le séisme de 2010 en Haïti, le gouvernement du Canada a exercé son accès prioritaire pour faire imager la zone sinistrée par RADARSAT-2 en quelques heures. Cet exemple illustre à la fois l'utilité opérationnelle et le mécanisme réglementaire de la LSTS.

---

## 2.7 Gestion du spectre et licences

### 2.7.1 Pourquoi les licences de spectre sont importantes

Tout satellite qui émet ou reçoit des signaux radioélectriques doit disposer d'une autorisation d'utilisation du spectre. Ce n'est pas facultatif — une émission RF non autorisée est illégale dans tous les États membres de l'UIT et peut causer des brouillages préjudiciables à d'autres systèmes.

La procédure comporte deux niveaux :

1. **National :** ISDE (Innovation, Sciences et Développement économique Canada) délivre la licence radio
2. **International :** l'UIT (Union internationale des télécommunications) coordonne la notification des fréquences afin d'éviter les brouillages avec les autres administrations nationales

### 2.7.2 Le cadre de l'UIT

L'Union internationale des télécommunications attribue le spectre à l'échelle mondiale au moyen du Règlement des radiocommunications (RR), mis à jour lors des Conférences mondiales des radiocommunications (CMR) tous les 3–4 ans.

| Notion UIT | Description | Pertinence |
|-------------|-------------|-----------|
| **Attribution de fréquences** | Spectre réparti entre services de radiocommunication (fixe par satellite, mobile, exploration de la Terre par satellite, etc.) | Détermine quelles bandes sont disponibles pour un type de mission donné |
| **Régions UIT** | Région 1 (Europe/Afrique), Région 2 (Amériques), Région 3 (Asie/Pacifique) | Le Canada se trouve en Région 2 ; les attributions peuvent différer d'une région à l'autre |
| **Coordination** | Accords bilatéraux ou multilatéraux destinés à éviter les brouillages | Exigée avant qu'un nouveau système à satellites puisse être exploité |
| **Notification** | Dépôt formel auprès du Bureau des radiocommunications (BR) de l'UIT | Inscrit le système à satellites dans le Fichier de référence international des fréquences (MIFR) |

### 2.7.3 Bandes de fréquences courantes des satellites

| Bande | Gamme de fréquences | Usage type | Caractéristiques principales |
|------|----------------|-------------|-------------------|
| **UHF** | 400–450 MHz | TT&C de CubeSats, AIS, ADS-B | Antennes simples, faible débit (1–9,6 kbit/s), bande encombrée |
| **Bande L** | 1,5–1,6 GHz | GNSS, service mobile par satellite | Navigation, balises de recherche et sauvetage |
| **Bande S** | 2,0–2,3 GHz | TT&C (liaisons montante et descendante) | Standard pour les données de servitude ; gain d'antenne modéré requis |
| **Bande C** | 3,7–4,2 / 5,9–6,4 GHz | Télécommunications GEO historiques (DBS), radar à synthèse d'ouverture (RADARSAT) | En cours de réaffectation à la 5G dans certains pays |
| **Bande X** | 8,025–8,4 GHz | Liaison descendante des données de charge utile d'OT | Débits plus élevés (10–150 Mbit/s) ; antenne de poursuite requise au sol |
| **Bande Ka** | 26,5–40 GHz | Liaison descendante de données à haut débit, liaisons intersatellites | Débits très élevés (100+ Mbit/s) ; affaiblissement dû à la pluie important |

Savoir si une attribution donnée offre des performances suffisantes est une question de bilan de liaison ; l'équation du bilan de liaison et ses critères de marge sont développés au chapitre 11.

### 2.7.4 La procédure de licence (Canada)

La procédure de licence de spectre d'ISDE pour un système à satellites suit les étapes du tableau 2.1. Le délai est long au regard du calendrier de développement d'un CubeSat, et c'est pourquoi le travail sur le spectre doit commencer dès la phase A. La figure 2.3 superpose les délais réglementaires à un calendrier de 30 mois couvrant les phases A à D : la barre de la coordination UIT est à elle seule aussi longue que l'ensemble du programme de développement.

![Diagramme de Gantt des étapes réglementaires d'un CubeSat canadien, superposé à un calendrier de 30 mois couvrant les phases A à D.](../assets/figures/fig_licensing_timeline.png)

**Figure 2.3** — Calendrier indicatif des licences pour un CubeSat canadien (PDR au mois 9, CDR au mois 18, lancement au mois 30, comme dans l'exercice 4). La consultation préalable et l'examen technique d'ISDE ainsi que le dépôt de l'API auprès de l'UIT suivent le tableau 2.1 ; la coordination UIT, de deux à sept ans, constitue le chemin critique et peut se prolonger au-delà du lancement (hachures) ; la licence d'exploitation LSTS ne concerne que les missions d'imagerie de la Terre ; les licences d'exportation (LLEI, et un TAA au titre de l'ITAR si des pièces d'origine américaine sont utilisées) doivent être obtenues avant l'expédition de l'engin spatial vers le site de lancement.

**Tableau 2.1** — Étapes de la procédure de licence de spectre ISDE/UIT et durées indicatives.

| Étape | Activité | Durée | Documents |
|------|----------|----------|-----------|
| 1 | Consultation préalable avec ISDE | 2–4 semaines | Description technique préliminaire |
| 2 | Dépôt de la demande formelle | — | Formulaire de demande d'ISDE, annexe technique |
| 3 | Examen technique par ISDE | 3–6 mois | Analyse de brouillage, exigences de coordination |
| 4 | Dépôt auprès de l'UIT (renseignements pour la publication anticipée — API) | — | Fiche API auprès de l'UIT (déposée par ISDE au nom du Canada) |
| 5 | Coordination UIT avec les administrations concernées | 2–7 ans | Accords de coordination |
| 6 | Notification à l'UIT et inscription au MIFR | — | Inscription au MIFR |
| 7 | Délivrance de la licence par ISDE | — | Licence radio |

### 2.7.5 Points propres aux CubeSats

De nombreux exploitants de CubeSats utilisent les fréquences radioamateurs (VHF/UHF) pendant le développement, mais doivent passer à des bandes commerciales pour les missions opérationnelles, en particulier en cas de diffusion commerciale de données.

| Approche | Voie de licence | Limites |
|----------|---------------|-------------|
| **Radioamateur (VHF/UHF)** | Coordination IARU ; licence radioamateur nationale | Aucun usage commercial ; données obligatoirement en libre accès ; puissance et largeur de bande limitées |
| **UHF commerciale** | Licence commerciale d'ISDE ; coordination UIT | Faible débit ; bande encombrée ; délai de licence plus long |
| **TT&C en bande S** | Licence d'ISDE ; coordination SFCG | Voie standard ; délai modéré (6–12 mois) |
| **Charge utile en bande X** | Licence d'ISDE ; coordination UIT | Débit plus élevé ; station sol de poursuite requise |

> **Pratique industrielle.** Kepler Communications (Toronto) a d'abord exploité ses premiers satellites précurseurs en bande Ku pour le relais de données IoT en mode différé (*store-and-forward*). L'obtention des droits sur le spectre en bande Ku a exigé une coordination avec les exploitants GEO en place, procédure qui a pris plus de 2 ans. La leçon : engager la procédure de licence de spectre dès la phase A.

---

## 2.8 Contrôle des exportations

### 2.8.1 Le paysage du contrôle des exportations

Les technologies satellitaires sont des marchandises contrôlées dans la plupart des pays en raison de leurs applications à double usage (civil/militaire). Les entreprises spatiales et les universités canadiennes doivent maîtriser trois régimes qui se chevauchent :

| Régime | Géré par | Périmètre | Liste principale |
|--------|----------------|-------|----------|
| **LLEI** (Canada) | Affaires mondiales Canada (AMC) | Marchandises et technologies d'origine canadienne | Liste des marchandises et technologies d'exportation contrôlée (LEC), groupes 1–7 |
| **ITAR** (États-Unis) | Département d'État américain (DDTC) | Articles et services de défense d'origine américaine | US Munitions List (USML), catégorie XV (engins spatiaux) |
| **EAR** (États-Unis) | Département du Commerce américain (BIS) | Marchandises et technologies à double usage d'origine américaine | Commerce Control List (CCL), ECCN 9Axx |

### 2.8.2 Contrôles canadiens des exportations (LLEI)

La Loi sur les licences d'exportation et d'importation exige une licence d'exportation pour les marchandises inscrites sur la Liste des marchandises et technologies d'exportation contrôlée (LEC) du Canada. Groupes de la LEC pertinents pour le spatial :

| Groupe de la LEC | Description | Exemples |
|-----------|-------------|---------|
| Groupe 1 | Marchandises à double usage (Arrangement de Wassenaar) | Électronique durcie aux rayonnements, composants qualifiés pour l'espace |
| Groupe 2 | Munitions (marchandises de défense) | Systèmes satellitaires militaires, télécommunications chiffrées |
| Groupe 4 | Nucléaire (NSG) | Générateurs thermoélectriques à radio-isotope (RTG), composants de propulsion nucléaire |
| Groupe 6 | Technologies des missiles (MTCR) | Systèmes de fusée complets, systèmes de guidage, propulsion |
| Groupe 7 | Armes chimiques et biologiques | Généralement sans rapport avec le spatial |

### 2.8.3 Contrôles américains des exportations (ITAR et EAR)

Toute mission qui utilise des composants d'origine américaine (ce qui inclut la quasi-totalité de l'électronique spatiale commerciale) doit se conformer aux contrôles américains des exportations :

**ITAR (International Traffic in Arms Regulations) :**

- La catégorie XV de l'USML couvre les engins spatiaux et les articles connexes
- Exige un accord d'assistance technique (TAA) ou un accord de licence de fabrication (MLA)
- S'applique aux articles de défense d'origine américaine, où qu'ils se trouvent
- Sanctions en cas d'infraction : jusqu'à 1 M$ par infraction et 20 ans d'emprisonnement

**EAR (Export Administration Regulations) :**

- Contrôle les articles à double usage (composants spatiaux commerciaux, logiciels, technologies)
- Utilise les numéros de classification du contrôle des exportations (ECCN)
- Exige une licence pour l'exportation vers la plupart des pays (sauf le Canada pour de nombreux articles, en vertu d'accords bilatéraux)
- L'Accord canado-américain sur le partage de la production de défense prévoit certaines exemptions

### 2.8.4 Conséquences pratiques pour la conception de mission

| Décision de conception | Conséquence en matière de contrôle des exportations |
|----------------|--------------------------|
| Utiliser des roues de réaction d'origine américaine | Une licence EAR peut être exigée ; ITAR s'il s'agit de matériel de qualité militaire |
| Collaborer avec une université hors du Groupe des cinq (Five Eyes) | TAA exigé pour les données techniques soumises à l'ITAR |
| Lancer sur une fusée non américaine | Technology Transfer Agreement ITAR pour les composants américains embarqués sur un lanceur étranger |
| Publier le logiciel du satellite en source ouverte | Vérifier l'absence d'algorithmes contrôlés (p. ex. chiffrement au-delà des seuils de l'EAR) |
| Embarquer une charge utile étrangère | Peut exiger une licence d'exportation au titre de la LLEI et/ou une autorisation ITAR |
| Publier la conception détaillée dans un article | Examen des données techniques exigé si des composants soumis à l'ITAR sont abordés |

> **Pratique industrielle.** L'exportation par MDA de technologies du segment sol de RADARSAT-2 vers des partenaires internationaux a exigé de nombreuses licences au titre de la LLEI et un examen de conformité à l'ITAR (des composants d'origine américaine étant intégrés au système). La procédure a pris plus de 18 mois et mobilisé du personnel dédié à la conformité. Même les projets universitaires de CubeSat utilisant des composants COTS d'origine américaine doivent suivre la classification ECCN de ces composants.

---

## Synthèse

| Thème | Point clé |
|-------|-------------|
| Mandat de l'ASC | Promouvoir l'usage pacifique de l'espace ; stratégie d'excellence de niche (robotique, radar à synthèse d'ouverture, instruments) |
| Structure de l'industrie | Écosystème à 4 niveaux ; le financement public d'amorçage permet la montée en échelle commerciale |
| LSTS | Tout satellite de télédétection exploité depuis le Canada exige une licence, assortie de dispositions d'interruption de service |
| Licences de spectre | Procédure à deux niveaux (national par ISDE + international par l'UIT) ; à engager dès la phase A ; délai de plus de 2 ans |
| Contrôle des exportations | Trois régimes qui se chevauchent (LLEI, ITAR, EAR) ; presque toutes les missions sont soumises aux contrôles américains |
| Leçon clé | La conformité réglementaire n'est pas facultative — elle oriente les décisions de conception dès les toutes premières phases |

---

## Exercices

1. **S'insérer dans l'écosystème.** Une équipe universitaire développe un CubeSat 3U d'observation de la Terre doté d'un imageur multispectral pour le suivi des cultures. En vous appuyant sur le §2.2, identifiez le ou les niveaux de l'industrie que l'équipe solliciterait pour (a) l'imageur, (b) les capteurs du contrôle d'attitude, (c) le courtage du lancement et (d) la diffusion des données. Quels programmes de financement de l'ASC ou fédéraux du §2.2.3 pourraient s'appliquer à chaque phase du cycle de vie, et quelles capacités devraient le plus probablement être obtenues à l'étranger ?

2. **Applicabilité de la LSTS.** Déterminez, en justifiant, si une licence au titre de la LSTS est exigée dans chacun des cas suivants, et énumérez les conditions de licence du §2.6.3 qui influeraient le plus sur la conception : (a) le CubeSat 3U d'OT ci-dessus, exploité depuis une station sol universitaire canadienne ; (b) UniSat-1, le démonstrateur 1U de magnétomètre du chapitre 1, §1.7, qui n'emporte aucune caméra ; (c) un satellite d'imagerie construit au Canada et exploité entièrement depuis la station sol d'un partenaire en Allemagne ; (d) une jeune pousse canadienne qui achète des images brutes à un satellite étranger et revend des produits traités.

3. **Choix des bandes.** En vous appuyant sur les §2.7.3 et §2.7.5, choisissez une bande de fréquences (ou plusieurs) pour la TT&C et pour la liaison descendante de la charge utile (a) d'UniSat-1, qui doit descendre environ 1 Mo par jour, et (b) du CubeSat 3U d'OT, qui doit descendre au moins 2 Go par jour. Pour chaque choix, indiquez la voie de licence, le délai de licence prévisible et une conséquence de conception pour le segment sol.

4. **Les licences sur le chemin critique.** Un projet de CubeSat prévoit la PDR au mois 9, la CDR au mois 18 et le lancement au mois 30 après le lancement du projet. À l'aide des durées du tableau 2.1, construisez un calendrier indiquant à quel moment doivent intervenir la consultation préalable d'ISDE, la demande formelle et le dépôt de l'API auprès de l'UIT pour que la licence radio soit obtenue avant le lancement, en supposant la période de coordination UIT la plus courte plausible. Quelle étape réglementaire se trouve sur le chemin critique, et qu'advient-il du calendrier si la coordination prend la durée la plus longue du tableau ?

5. **Scénario de contrôle des exportations.** Le CubeSat 3U d'OT utilise un ensemble de roues de réaction d'origine américaine et un récepteur GNSS d'origine américaine, sera lancé par un PSLV indien et compte dans l'équipe de conception un chercheur invité originaire d'un pays hors du Groupe des cinq. Identifiez toutes les obligations de contrôle des exportations du §2.8 qui s'appliquent, nommez pour chacune le régime et l'instrument (licence, TAA, classification ECCN, etc.), et proposez deux modifications de conception ou de programme qui allégeraient la charge de conformité.

6. **Levier des partenariats.** À l'aide du ratio de levier du §2.4.2, estimez $L$ pour la contribution canadienne Canadarm3 à Artemis (engagée pour le Lunar Gateway en 2019, puis réorientée vers les opérations à la surface lunaire après la suspension du Gateway par la NASA en mars 2026), en précisant vos hypothèses sur $C_{\text{contribution}}$ et $V_{\text{access}}$. Discutez deux limites de ce ratio en tant qu'indicateur de décision, notamment ce que devient $V_{\text{access}}$ lorsque le partenaire restructure le programme, et proposez une amélioration.

7. **Comparer les modèles nationaux.** À partir de la comparaison du §2.3, identifiez deux conséquences, pour une équipe canadienne de conception de mission, (a) de l'absence de capacité de lancement nationale et (b) de la modestie du budget de l'agence par rapport à celui de la NASA ou de l'ESA. En quoi le modèle du *juste retour* de l'ESA modifie-t-il la manière dont une équipe européenne aborderait le choix des fournisseurs par rapport à une équipe canadienne ?

8. **La réglementation comme facteur dimensionnant.** Pour chacun des trois régimes réglementaires de ce chapitre (LSTS, spectre, contrôle des exportations), rédigez une exigence — sous la forme en « doit » du chapitre 5 — que le CubeSat 3U d'OT doit satisfaire, et indiquez la phase du cycle de vie (chapitre 1, §1.4) à laquelle les preuves correspondantes doivent exister.

---

## Références

1. Gouvernement du Canada, *Canadian Space Agency Act* (S.C. 1990, c. 13). [https://laws-lois.justice.gc.ca/eng/acts/c-11.2/](https://laws-lois.justice.gc.ca/eng/acts/c-11.2/)
2. Gouvernement du Canada, *Remote Sensing Space Systems Act* (S.C. 2005, c. 45). [https://laws-lois.justice.gc.ca/eng/acts/r-5.4/](https://laws-lois.justice.gc.ca/eng/acts/r-5.4/)
3. Gouvernement du Canada, *Radiocommunication Act* (R.S.C., 1985, c. R-2). [https://laws-lois.justice.gc.ca/eng/acts/r-2/](https://laws-lois.justice.gc.ca/eng/acts/r-2/)
4. Gouvernement du Canada, *Export and Import Permits Act* (R.S.C., 1985, c. E-19). [https://laws-lois.justice.gc.ca/eng/acts/e-19/](https://laws-lois.justice.gc.ca/eng/acts/e-19/)
5. ISDE Canada, *Spectrum Management and Telecommunications*. [https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home](https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home)
6. UIT, *Radio Regulations*, édition 2020. [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
7. ASC, *Exploration, Imagination, Innovation : A New Space Strategy for Canada*, 2019. [https://www.asc-csa.gc.ca/eng/publications/space-strategy-for-canada.asp](https://www.asc-csa.gc.ca/eng/publications/space-strategy-for-canada.asp)
8. ASC, *State of the Canadian Space Sector Report*, 2022. [https://www.asc-csa.gc.ca/eng/publications/state.asp](https://www.asc-csa.gc.ca/eng/publications/state.asp)
9. US Department of State, *International Traffic in Arms Regulations* (22 CFR 120–130). [https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M](https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M)
10. US Department of Commerce, *Export Administration Regulations* (15 CFR 730–774). [https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C)
11. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
12. NASA, « NASA Unveils Initiatives to Achieve America's National Space Policy » (suspension du Gateway « dans sa forme actuelle »), communiqué, 24 mars 2026. [https://www.nasa.gov/news-release/nasa-unveils-initiatives-to-achieve-americas-national-space-policy/](https://www.nasa.gov/news-release/nasa-unveils-initiatives-to-achieve-americas-national-space-policy/)
13. MDA Space, « MDA Space responds to Canadian Space Agency announcement on Canadarm3 » (réorientation de Canadarm3 par l'ASC vers les opérations à la surface lunaire), 6 août 2026. [https://mda.space/article/mda-space-responds-to-canadian-space-agency-announcement-on-canadarm3](https://mda.space/article/mda-space-responds-to-canadian-space-agency-announcement-on-canadarm3)
