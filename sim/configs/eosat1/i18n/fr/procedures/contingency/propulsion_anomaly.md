# CTG-028 : Anomalie de propulsion

**Sous-système :** Propulsion
**Phase :** CONTINGENCY
**Révision :** 1.0
**Approuvé par :** directeur des opérations de vol

## Objet
Traiter un déclenchement de la FDIR propulsion — poussée faible, défaut de vanne, fuite ou pression
de réservoir hors plage — en isolant les ergols, en bornant le delta-V utilisable
restant et en protégeant la réserve d'évitement des débris. Sur EOSAT-1, le
système de propulsion existe POUR l'évitement de collision : l'objectif de la reprise n'est
pas de « réparer le propulseur », mais de « savoir exactement quelle capacité de CAM subsiste
et la préserver ».

> Remarque (rapprochement avec le livre) : le guide de l'animateur numérote cette fiche CTG-006
> et son étape 1 indique « SID 5 / propulsion ». Dans le simulateur, CTG-006 est l'anomalie charge utile
> et le SID 5 est la charge utile ; la fiche propulsion est CTG-028 et la structure de servitude
> de la propulsion est le SID 9.

## Critères d'entrée
L'un quelconque des cas suivants :
- alarme S12 sur `prop.tank_pressure` (0x0B01) — plage absolue ou surveillance DELTA
  (vitesse de variation), qui est celle qui détecte une fuite lente ;
- événement PROP_LEAK_DETECTED (0x080B), PROP_VALVE_FAULT (0x080A),
  PROP_UNDERPERFORMANCE (0x080C), PROP_TANK_PRESSURE_HIGH (0x0807) ;
- la restitution d'orbite après poussée montre un dV obtenu < 90 % du plan (d'après l'étape 6 de NOM-013).

## Déroulement

### Étape 1 --- Lire l'ensemble de la télémesure de propulsion
**TC:** `HK_ENABLE(sid=9)` (Service 3, Subtype 5) --- s'assurer que la structure PROP est active
**Verify:** Relever et consigner TOUS les paramètres suivants : `prop.state` (0x0B00),
`prop.tank_pressure` (0x0B01) + tendance, `prop.propellant_mass` (0x0B02),
`prop.tank_temp` (0x0B04), `prop.catbed_temp` (0x0B05), états des vannes
(0x0B06/0x0B07/0x0B08), `prop.abort_reason` (0x0B14). Il n'y a pas de capteur
de débit de fuite à bord : une fuite se voit comme une tendance de la pression
réservoir, donc comparer 0x0B01 aux valeurs consignées lors des passages précédents,
corrigées de la température avec 0x0B04.
**Évaluer :** Pression en baisse avec masse d'ergols constante = fuite du gaz
de pressurisation ; pression et masse en baisse ensemble = fuite d'ergols ; pression en hausse
= cause thermique (contrôler 0x0B04 et l'état des réchauffeurs).

### Étape 2 --- Isoler
**TC:** `PROP_ISO_CLOSE(branch=2)` (Service 8, Subtype 1) func_id = 114 --- fermer LES DEUX branches de vannes à verrouillage
**Verify:** `prop.latch_a_state` (0x0B06) = 0 et `prop.latch_b_state`
(0x0B07) = 0. Une branche qui indique 2 (défaut) ne s'est PAS fermée — elle est bloquée :
fermer l'autre branche, noter que l'isolation est partielle et considérer les
ergols situés en aval de la vanne bloquée comme perdus.
**Verify:** la tendance de la pression réservoir 0x0B01 sur ce passage et les suivants
après isolation, à température réservoir comparable (0x0B04) —
une baisse qui continue signifie que la fuite se situe en amont des vannes à verrouillage (côté réservoir) :
elle ne peut pas être isolée, seulement bornée.
**Note:** La règle bord 8004 isole automatiquement sur un événement de fuite ; cette étape
vérifie et achève ce que l'autonomie a commencé.

### Étape 3 --- Borner le delta-V utilisable restant
**Verify:** `prop.dv_remaining` (0x0B0C) — valeur de Tsiolkovski calculée à bord sur
les ergols restants.
**Évaluer :** La corriger selon le mode de défaillance : soustraire les ergols situés derrière une
branche bloquée ouverte ; pour une fuite de réservoir non isolable, extrapoler la masse au taux de fuite
courant jusqu'à l'époque de la prochaine conjonction crédible. **Consigner la réserve CAM bornée
et la communiquer au directeur de vol** — en dessous de ~1 m/s, le satellite
a de fait perdu sa capacité d'évitement des débris et la posture vis-à-vis des conjonctions
change (seuils de criblage, décisions plus précoces).

### Étape 4 --- Inhiber et ouvrir une fiche
**TC:** `PROP_INHIBIT_SET(on=1)` (Service 8, Subtype 1) func_id = 116 --- verrouiller l'inhibition sol tant que l'anomalie est ouverte
**Verify:** `prop.arm_inhibit_mask` (0x0B15) bit 9 positionné.
**Consigner :** Fiche d'anomalie : déclencheur, relevé de télémesure, état d'isolation,
dV borné. Une sous-performance (0x080C) avec une pression nominale indique une dégradation du lit catalytique
— les poussées futures sont replanifiées avec le facteur de performance mesuré.

### Étape 5 --- Escalade
**Évaluer :** Une pression de réservoir EN HAUSSE (0x0807) qui ne réagit pas à la mise en sécurité
des réchauffeurs menace le disque de rupture : GO pour CTG-004 (Dépassement thermique) et
préparer EMG-001 (mode survie) — le mode survie désarme la propulsion par la règle 8005.

## Critères de sortie
- Ergols isolés (ou fuite explicitement bornée comme non isolable)
- dV restant borné consigné et communiqué au FD
- Inhibition sol verrouillée ; sa levée (PROP_INHIBIT_CLR, func 117) exige une
  fiche d'anomalie close et l'autorisation du FD
