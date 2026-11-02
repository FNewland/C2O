# LEOP-005 : Acquisition du Soleil
**Sous-système :** AOCS
**Phase :** LEOP
**Révision :** 2.0 --- refonte du déroulement 2026-08c. La transition DETUMBLE -> COARSE_SUN
est AUTOMATIQUE (vitesses < 0,5°/s maintenues pendant 30 s ---
`docs/plan_2026-08c/AOCS_MODE_TRANSITIONS.md` 1.2) : cette fiche l'OBSERVE et
vérifie le maintien solaire ; elle ne commande aucun changement de mode. Les contrôles des roues de réaction
sont supprimés --- les roues sont désactivées jusqu'à COM-004 et COARSE_SUN fonctionne sur
les magnétocoupleurs.
**Approuvé par :** Directeur des opérations de vol

**État d'entrée :** état de sortie de LEOP-007 --- AOCS en DETUMBLE sur magnétomètre + MTQ,
SID 2 transmis, roues DÉSACTIVÉES, récepteur GPS en acquisition, panneaux déployés.

## Objet
Surveiller la séquence automatique d'amortissement des vitesses et d'acquisition du Soleil : suivre la
réduction des vitesses angulaires sous le seuil par l'amortissement B-dot, observer le passage AUTOMATIQUE en
COARSE_SUN, et vérifier que le satellite se stabilise dans un maintien solaire à bilan de puissance positif.
COARSE_SUN est la position d'attente légitime de la LEOP : aucun senseur stellaire n'étant encore alimenté,
la promotion automatique hors de COARSE_SUN ne peut pas se déclencher (elle exige le suivi du ST) ;
le satellite conserve donc l'attitude de sécurité solaire jusqu'à ce que la recette en orbite
mette les senseurs en service (COM-003).

## Prérequis
- [ ] LEOP-007 terminée --- `aocs.mode` (0x020F) = 2 (DETUMBLE),
      `aocs.mag_enabled` (0x025C) = 1, `aocs.mtq_enabled` (0x025E) = 1
- [ ] LEOP-004 terminée --- panneaux déployés (énergie pour le maintien)
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] Données de servitude périodiques du SID 2 sur la liaison descendante (contact programmé ; cette
      fiche s'étend sur plus d'un passage si les vitesses de séparation sont élevées --- l'autonomie
      n'a pas besoin de la surveillance du sol pour progresser)

## Déroulement

### Étape 1 --- Consigner les vitesses angulaires initiales
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) = 2 (DETUMBLE) sous 10s
**Verify:** `aocs.rate_roll` (0x0204) rapportée sous 10s --- consigner la valeur
**Verify:** `aocs.rate_pitch` (0x0205) rapportée sous 10s --- consigner la valeur
**Verify:** `aocs.rate_yaw` (0x0206) rapportée sous 10s --- consigner la valeur
**Action:** Consigner les vitesses initiales comme référence. Vitesses attendues après séparation : typiquement 0,5 à 5,0°/s par axe.
**GO/NO-GO:** Télémesure de vitesse valide, DETUMBLE confirmé actif

### Étape 2 --- Surveiller l'amortissement des vitesses (observer --- ne rien commander)
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- renouveler à T+5 min
**Verify:** `aocs.rate_roll` (0x0204) en décroissance sous 10s
**Verify:** `aocs.rate_pitch` (0x0205) en décroissance sous 10s
**Verify:** `aocs.rate_yaw` (0x0206) en décroissance sous 10s
**Action:** Le B-dot devrait diviser les vitesses par deux environ toutes les 10-15 minutes. Vérifier l'activité des magnétocoupleurs via `aocs.mag_field_total` (0x0277) --- un champ à zéro signifie que le magnétomètre a décroché et que le B-dot est aveugle.
**GO/NO-GO:** Toutes les vitesses angulaires en décroissance

### Étape 3 --- Observer la transition AUTOMATIQUE vers COARSE_SUN
**Action:** Lorsque les vitesses angulaires sont restées sous 0,5°/s pendant 30 s consécutives,
l'AOCS passe de lui-même de DETUMBLE à COARSE_SUN.
**Note:** Il s'agit d'une transition AUTOMATIQUE --- NE PAS commander le mode 3 (S8.1
func 0). L'ancienne révision de cette fiche commandait le mode qu'elle allait obtenir
gratuitement, puis « vérifiait » une transition que le satellite avait déjà effectuée de
lui-même.
**Verify:** `aocs.mode` (0x020F) = 3 (COARSE_SUN) sous 1800s après le passage des vitesses
sous 0.5 deg/s
**Verify:** Événement `AOCS mode change` dans le journal des événements avec DETUMBLE -> COARSE_SUN
**GO/NO-GO:** Passage automatique observé et consigné

### Étape 4 --- Vérifier le maintien solaire
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- renouveler toutes les 60s pendant 5 minutes
**Verify:** `aocs.att_error` (0x0217) < 15.0 deg sous 600s --- convergence vers le vecteur Soleil
**TC:** `GET_PARAM(param_id=0x0215)` (Service 20, Subtype 3) — `aocs.css_sun_confidence` (à la demande : aucun SID HK ne le transporte)
**Verify:** `aocs.css_sun_confidence` (0x0215) > 0.5 sous 60s --- les CSS voient le Soleil
**Verify:** `aocs.rate_roll` (0x0204) < 0.5 deg/s sous 10s
**Verify:** `aocs.rate_pitch` (0x0205) < 0.5 deg/s sous 10s
**Verify:** `aocs.rate_yaw` (0x0206) < 0.5 deg/s sous 10s
**Note:** COARSE_SUN sans roues fonctionne sur les magnétocoupleurs : s'attendre à un maintien de l'ordre
du degré, oscillant lentement, et non à un maintien serré comme avec les roues. Des vitesses de quelques centièmes
à ~0,2°/s pendant ces oscillations sont normales ici.
**GO/NO-GO:** Pointage solaire obtenu à 15 degrés près et maintenu

### Étape 5 --- Vérifier la production électrique pendant le maintien
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.power_gen` (0x0107) > 40W sous 60s (pointage solaire, panneaux déployés) — au Soleil uniquement : si `eps.eclipse_flag` (0x0108) = 1, attendre la sortie d'éclipse (jusqu'à 35 min) et revérifier
**Verify:** `eps.bat_soc` (0x0101) stable ou en hausse sous 120s
**GO/NO-GO:** Bilan de puissance positif en COARSE_SUN

### Étape 6 --- Consigner l'état final de l'AOCS
**Action:** Consigner les vitesses angulaires finales, l'erreur d'attitude, la confiance CSS et la production
électrique. Noter explicitement que le satellite RESTE en COARSE_SUN : aucun
senseur stellaire n'étant alimenté, la promotion automatique hors du maintien ne peut pas se déclencher, et
c'est l'état d'attente prévu pour la LEOP. Émettre le rapport d'acquisition du Soleil.
**GO/NO-GO:** Maintien solaire stable confirmé --- LEOP-005 terminée

## Conduite à tenir hors nominal
- Si les vitesses angulaires ne diminuent pas après 15 min : vérifier `aocs.mtq_enabled` (0x025E) = 1 et `aocs.mag_enabled` (0x025C) = 1. Si l'un des deux est retombé, les rétablir selon LEOP-007, étape 4, et commander de nouveau DETUMBLE avec S8.1 func 0 mode 2 --- renvoyer la commande du mode dans lequel on se trouve déjà est sans effet néfaste. Faire remonter à l'ingénieur AOCS si les vitesses ne baissent toujours pas.
- Si le passage automatique en COARSE_SUN n'a pas lieu dans les 30 min suivant le passage des vitesses < 0.5 deg/s : la condition de maintien est peut-être rompue (un axe oscillant autour de 0.5). Surveiller les vitesses par axe ; si un axe ne se stabilise pas, suspecter une erreur de polarité d'un magnétocoupleur ou une panne d'axe du magnétomètre et faire remonter. Ne pas forcer le mode par commande --- un COARSE_SUN entré au-dessus du seuil de vitesse ne tiendra pas.
- Si l'erreur d'attitude ne converge pas en COARSE_SUN : vérifier `aocs.css_sun_confidence` (0x0215). Une faible confiance en éclipse est attendue --- les CSS ne peuvent pas voir le Soleil ; attendre l'arc éclairé et vérifier de nouveau.
- Si la production électrique est < 40W après le pointage solaire : contrôler l'état du générateur (LEOP-004) et l'attitude. Acceptable en LEOP si le SoC reste au-dessus de 40 %.

## État de sortie
- AOCS en COARSE_SUN (automatique, mode 3) --- le maintien d'attente de la LEOP ; roues
  toujours DÉSACTIVÉES ; senseurs stellaires et gyromètres toujours sur OFF
- Bilan de puissance positif : production > 40W, SoC stable ou en hausse
- Rien d'autre n'a été modifié par cette fiche

## Postconditions
- [ ] Profil d'amortissement des vitesses consigné (de la référence jusqu'à < 0.5 deg/s)
- [ ] Passage automatique DETUMBLE -> COARSE_SUN observé (non commandé)
- [ ] Maintien solaire vérifié : att_error < 15 deg, confiance CSS > 0.5
- [ ] Bilan de puissance positif confirmé
- [ ] Rapport d'acquisition du Soleil diffusé

**PROCÉDURE SUIVANTE :** LEOP-006 (Synchronisation temporelle --- voie sol immédiatement, voie GPS
dès que le récepteur alimenté dans LEOP-007 dispose d'un point)
