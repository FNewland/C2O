# Guide de la propulsion d'EOSAT-1 (phase D)

**Périmètre :** la propulsion sert aux **manœuvres d'évitement de débris**, à un **maintien
d'orbite limité** (compensation de la traînée / décalage volontaire du demi-grand axe) et à la
**poussée de retrait de service en fin de vie**. Elle est délibérément minimale.

> **Décision de l'auteur Q3 (modifiée le 2026-10-30) :** le retrait de service se fait par une poussée
> d'abaissement du périgée en fin de vie avec le propulseur existant, dimensionnée pour une rentrée en moins de
> 5 ans même au minimum solaire. L'ancien « 1,7–4,8 ans, aucune capacité de désorbitation »
> avait été établi à 450 km.

**Déclin naturel depuis 513 km** (B = 77,9 kg/m², décroissance due à la traînée intégrée jusqu'à 120 km
avec l'atmosphère exponentielle CIRA-72 pour l'activité moyenne et 0,35 fois celle-ci pour le
minimum solaire, la méthode et le facteur d'échelle du dimensionnement initial) : environ
**5,0 ans à activité solaire moyenne et 14 ans au minimum solaire** — hors de
la règle des 5 ans. Orienter les ailes face à la vitesse (B ≈ 8,3 kg/m²) le ramènerait
à environ 0,5 / 1,5 an, mais cela exige une attitude maîtrisée et n'est pas
modélisé ; c'est une solution de secours, pas le plan.

**Poussée de retrait de service (NOM-014) :** abaisser le périgée de 513 km à **390 km** avec
**34,3 m/s** de ΔV rétrograde, en six poussées de 5,72 m/s au même point de l'orbite
(chacune de 320–480 s à la poussée de fin de vie, avec le chien de garde de poussée relevé
à 600 s). Durée de vie résiduelle **~1,5 an (moyenne), ~4,2 ans (minimum
solaire)**. Ensuite, épuiser le propergol, verrouiller l'inhibition de la propulsion,
arrêter les roues, couper le régulateur de charge de la batterie et faire taire les
émetteurs.

## Matériel

Module à monergol vert (classe LMP-103S/ADN) de 1U en mode blowdown (pressurisation non régulée), avec un
propulseur unique sur la face −X poussant selon **+X satellite** — dans le sens du mouvement en
attitude nominale nadir ; une poussée rétrograde exige un basculement délibéré de 180° en lacet
(maintien INERTIAL). Ce couplage avec l'AOCS est voulu : c'est le point pédagogique.

| Paramètre | Valeur |
|---|---|
| Poussée | 0,33 N (22 bar en BOL) → 0,14 N (9,33 bar en EOL), F ∝ P |
| Isp | 220 s en BOL → 196 s en EOL (208 s en moyenne) |
| Ergol | 0,400 kg, ρ = 1240 kg/m³, réservoir de 560 cm³, blowdown N₂ 2,36:1 |
| Lit catalytique | préchauffage ≥ 180 °C, 12 W × ~20 min (4 Wh) via `HEATER_THRUSTER` (fonction S8 42) |
| Système humide | 1,55 kg (12,9 % de la plateforme de 12 kg) |
| **ΔV total** | **66,9 m/s** |

**Bilan de ΔV (phase active de 2 ans + retrait de service, recalculé à 513 km) :**
compensation de traînée 15,1 (activité solaire de dimensionnement à 513 km ; elle était de 42,6 à 450 km) +
décalage SMA/LTAN 3,0 + manœuvres d'évitement de collision, CAM (6 événements × 0,1) 0,6 + recette en orbite/étalonnage 1,0 +
contrôle de l'excentricité 1,5 + **retrait de service 34,3** = 55,5, plus des marges de 5 % (2,8) et
10 % (5,8) = **64,1 m/s nécessaires** pour une capacité de 66,9 (**+4,4 %** ; +2,6 %
par rapport aux 65,8 m/s obtenus en intégrant la courbe d'Isp en blowdown). Le
propergol et le réservoir suffisent sans modification : le retrait de service consomme ~0,21 kg des
0,400 kg chargés. L'enveloppe restante (`prop.dv_remaining`, 0x0B0C) est une
**réserve d'évitement de collision et de retrait de service** : conserver au moins 38 m/s pour la
poussée de retrait de service ; à moins d'environ 1 m/s au-dessus de cette réserve, le satellite a de fait
perdu sa capacité de CAM et la conduite à tenir face aux conjonctions change.

Poussées types : CAM de 0,20 m/s ≈ 7,5 s ; compensation de traînée bimensuelle de 0,85 m/s ≈
32 s (BOL) ; toutes tiennent dans un passage. Une poussée prograde de 1,0 m/s relève le SMA de
1,79 km et décale les heures de passage d'environ 34 s/jour (mesuré dans le simulateur : −33,5 s/jour,
valeur analytique −33,9).

## Automate d'états et verrouillages

`SAFED(0) → ARMED(1) → FIRING(2)`, plus l'état verrouillé `INHIBIT(3)` après une deuxième
interruption (levé uniquement par `PROP_INHIBIT_CLR`). Armement en deux temps : `PROP_SET_BURN`
doit précéder `PROP_ARM` (code 0xA5C3) de 300 s au plus. Les huit verrouillages d'armement
(lit catalytique ≥ 180 °C, réservoir 6–24 bar, ergol > 5 g, mode AOCS ∈ {4,5,9},
att_error < 2°, SoC > 45 %, phase NOMINAL, hors éclipse, une branche de vanne à verrouillage
ouverte, aucune inhibition) renvoient des **codes S1(8) distincts** et positionnent leur bit dans
`prop.arm_inhibit_mask` (0x0B15) — le paramètre le plus utile de tous pour les stagiaires.

Interruptions de poussée à bord (att_error > 2°, alimentation < 4 bar, lit catalytique > 350 °C,
chien de garde, perte de vanne, délestage de la ligne EPS `prop`), plus l'autonomie S19 : règles
8001–8006 (interruption sur violation S12 de 0x0217, pression réservoir, surchauffe du lit catalytique,
isolation sur fuite, désarmement sur passage en mode survie, interruption sur SoC critique). Le **ΔV partiel
d'une poussée interrompue perturbe tout de même l'orbite** — la restitution d'orbite après poussée est obligatoire.

## Intégration orbitale (ce qui la rend réaliste)

Une poussée finie est intégrée par sous-pas de 1 s au plus ; le ΔV résultant
(composante le long de la trace × cos θ + composante latérale × sin θ, θ = att_error) est appliqué au SGP4 sous la forme
d'**une impulsion unique au milieu de la poussée**, au moyen d'une correction différentielle du TLE à 6 paramètres
(paramétrisation équinoxiale ; 3 à 6 itérations, résidu inférieur au millimètre ;
divergence → événement 0x0812, orbite inchangée). Chaque poussée appliquée incrémente
`epoch_version` (0x0B19, `/api/state`) : le planificateur et le MCS la traitent comme un saut
de temps, purgent leurs caches de contacts et de trace au sol et adoptent le nouveau TLE. Les points de reprise
sérialisent le jeu d'éléments (`orbit_elset`) — « le SGP4 est sans état pour un temps
UTC donné » a cessé d'être vrai le jour où la propulsion est arrivée.

En état FIRING, le moteur **limite l'accélération du temps à 10× au plus** (événement
0x0811 `PROP_SPEED_CLAMPED`) afin que les poussées et les interruptions restent observables.

## Puissance et thermique

Ligne EPS 8 `prop` (OFF par défaut, **dernière** dans l'ordre de délestage — la délester
en cours de poussée déclenche l'interruption). La consommation suit l'état des actionneurs, et non celui de
l'interrupteur de ligne : 0 W au repos, 2 W pour les circuits de commande des vannes en ARMED/FIRING, +12 W lorsque le
réchauffeur du lit catalytique fonctionne. Le lit catalytique correspond au circuit TCS `thruster`
(`tcs.temp_thruster` 0x0409, état du réchauffeur 0x041B) : commande manuelle via la fonction 42,
régulation thermostatique 190/230 °C via `HEATER_AUTO_MODE circuit=2`. Une manœuvre est
une **activité de puissance** : les 4 Wh de préchauffage plus la poussée doivent tenir dans le bilan
de la phase éclairée.

## Interfaces

- **Commandes :** fonctions S8 **108–118** (`PROP_ARM` 108, `PROP_DISARM` 109,
  `PROP_SET_BURN` 110, `PROP_EXECUTE` 111, `PROP_ABORT` 112,
  `PROP_ISO_OPEN/CLOSE` 113/114, `PROP_SET_LIMITS` 115,
  `PROP_INHIBIT_SET/CLR` 116/117, `PROP_GET_STATUS` 118) + fonction 42 pour le réchauffeur.
  *(Le brief 03 prévoyait 85–95 ; le bloc de pointage AOCS de la phase C a pris 85–91, si bien que
  108–118 est le bloc attribué.)*
- **Télémesure :** bloc **0x0B00–0x0B1B** ; **SID HK 9** à 8 s (désactivé à la
  mise sous tension, `HK_ENABLE sid=9`). *(Le brief prévoyait le SID 7 ; la phase C l'a pris pour
  l'AOCS.)* Paramètres de ligne EPS 0x014A/0x014B ; TCS 0x0409/0x041B.
- **Événements :** **0x0800–0x0812**. **S12 :** plage de pression réservoir + **moniteur de variation
  et de taux** (le détecteur de fuite), lit catalytique, ergol, poussée faible, enveloppe de
  ΔV. **S19 :** ea_id 8001–8006.
- **Procédures :** **NOM-004** (planification, occupe l'indice laissé libre),
  **NOM-013** (exécution ; la NOM-005 du manuel — la NOM-005 du simulateur était déjà la Configuration
  HK), **NOM-014** (retrait de service en fin de vie : abaissement du périgée et
  passivation), **CTG-028** (anomalie ; la CTG-006 du manuel — la CTG-006 du simulateur était
  déjà l'Anomalie charge utile ; et « SID 5/propulsion » correspond ici au SID 9). L'OBCP 4
  (`obcp/04_orbit_manoeuvre.yaml`) constitue la séquence minutée à bord. Activité du planificateur :
  `orbit_manoeuvre`.
- **Scénarios de formation :** `prop_valve_stuck_open`, `prop_slow_leak`,
  `prop_underperformance`, `prop_burn_eclipse_power`,
  `prop_attitude_loss_mid_burn`.

## Limites du modèle (enseignées, non simulées)

Un propulseur, un axe — pas d'orientation de la poussée (TVC), pas de désaturation par propulseurs (NOM-007 reste
réalisée uniquement aux magnétocoupleurs). La poussée de retrait de service est réalisée comme des poussées rétrogrades ordinaires ;
le déclin et la rentrée qui suivent ne sont pas simulés, et il n'y a pas de mise à l'air du
pressurisant à la passivation. Pas de changement de plan, de relèvement d'orbite,
de phasage, de rendez-vous, de contrôle d'orbite en boucle fermée ni de véritable criblage des
conjonctions (la CAM est une entrée de scénario scriptée). Pas de transitoires de combustion ou d'alimentation,
de blowdown non isotherme, de ballottement ou de migration du centre de gravité, ni de couplage avec le tenseur d'inertie
(la masse n'est qu'une télémesure). Deux *branches* de vannes à verrou, un propulseur. Le déclin dû
à la traînée est celui que donne le B* du SGP4 — le bilan de ΔV ci-dessus est un calcul de dimensionnement
hors ligne, non une boucle de rétroaction en temps réel.
