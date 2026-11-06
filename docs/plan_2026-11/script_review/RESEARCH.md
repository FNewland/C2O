# Research note: acronyms, animation and team vs role training for the ORBIT NORTH video scripts

2026-11-06. This note supports the script review (`BRIEF.md`). It builds on the earlier research note, which covered Mayer's segmenting, signalling, modality and coherence principles, Guo et al. on engagement, interpolated testing, and TTS versus a human voice. None of that is repeated here. Tags used below:

- **[read]**: I read the primary source, or its official abstract or summary page.
- **[secondary]**: I know the finding only through another source that cites it.
- **[unverified]**: I could not get to the source text. Treat it as a pointer, not as evidence.

---

## 1. Acronyms and jargon in spoken instruction

**Accessibility standard.** WCAG 2.2 success criterion 3.1.4, Abbreviations (level AAA), has this intent: "Users can identify and learn what abbreviations mean." One sufficient technique, when an abbreviation has one meaning on a page, is G97: give the expanded form immediately before or after the first use. Expanding every use through a glossary or links also counts. Words that have "become part of the language" are exempt, and the criterion treats a dictionary entry as reasonable evidence of that (its examples are *laser*, and possibly NASA or IBM). Otherwise "the criterion does not exempt abbreviations even if they are common or familiar." The criterion names who benefits: people who "have difficulty decoding words", "have limited memory", or "have difficulty using context". It also warns about acronyms that sound like other words (SMIL is said "smile"). [read]

For narration, that gives three points:
- One expansion at first use meets the standard. WCAG accepts either order, short form first or long form first.
- For a listener, long form first is the safer order. Unlike a reader, a listener cannot glance back.
- A spoken acronym said as a word ("nom", "lee-op") hides how it is spelled. Showing the written form on screen at the moment of expansion fills that gap.

**Government style guides agree.** The US 18F content guide says: "Acronyms often confuse readers. Avoid them whenever possible." If a term will come up again, spell it out on first reference with the acronym after it. Well-known acronyms are allowed. [read]

The Language Portal of Canada ("Alphabet soup") says that abbreviations "that may be misunderstood should be spelled out on the first reference." It adds that this "helps avoid translation mistakes" and asks writers to pick one form and stay consistent. [read]

On the French side, the Office québécois de la langue française (OQLF) advises giving "la forme longue de ce sigle la première fois qu'on l'emploie dans un texte". Either order is accepted. OQLF also separates two kinds of short form:
- a *sigle épelé*, spelled letter by letter (for example HLM);
- an *acronyme*, said as a word (for example ONU).

For English-origin short forms used in French (FAO, sonar), OQLF pairs the foreign long form with a French gloss. [read] That matches the house style, which keeps the identifier in English and gives the expansion in French prose: "le système de contrôle d'attitude et d'orbite, le SCAO".

**Evidence that acronyms cost comprehension.** The direct experimental evidence is thinner than the style guidance.
- Barnett & Doubleday (eLife 2020) counted 1.1 million distinct acronyms in PubMed titles and abstracts. 79% were used fewer than 10 times, and the same acronym often has several meanings ("UA" has 18 in medicine). They recommend dropping acronyms that save no syllables. [read] The study does not measure comprehension.
- Hales, Williams & Rector (2017) argue that abbreviations *exclude* readers who do not know them, and recommend assuming that readers may not. [read: press release only]
- Their experimental data on reading and comprehension: [unverified]

**Pretraining principle.** Mayer's statement: "People learn more deeply from a multimedia message when they know the names and characteristics of the main concepts." Pretraining before the lesson improved problem-solving transfer in 5 out of 5 tests, with a median d = 0.85. [read: Cambridge chapter abstract] The mechanism is that learning component names and behaviours *before* a fast causal explanation frees working memory during the explanation.

For this course, pretraining means learning the console vocabulary first: the subsystems, the modes, and the data products (SID, S9, S1). That vocabulary is part of the course content, so it should not be cut as "coherence" clutter. It should be taught before the procedure videos that depend on it.

**Fading support (expertise reversal).** Support that helps novices can hurt learners who have become competent. A longitudinal writing-to-learn study is a good example. Permanent prompts became "a redundant stimulus". Learners who kept getting them ended with substantially lower outcomes than learners whose prompts were faded adaptively. [read: abstract; the repository page's title metadata did not match its abstract, so the attribution is unverified]

Spanjers et al. (2011) report an expertise reversal effect for segmenting animated worked examples. [unverified: abstract not retrieved] The implication is that full expansions should get shorter as the series goes on. They should not be removed completely, and the written form should stay available, for example in a glossary.

**How operational communities teach jargon.** Operational communities do not avoid jargon. They teach it as a controlled code.
- **Aviation:** Alderson (2009) describes aviation English as "a code that is used in a very restricted context". Standard phraseology has been refined by studying miscommunication incidents. Second-language proficiency interacts with workload and affects readback accuracy, and accents add risk. Plain language takes over when phraseology runs out. [read]
- **NASA ISS flight controllers:** Initial training includes a lesson on the voice loop system (DVIS) covering protocol, standard phrases and the phonetic alphabet, plus a lesson on building team situational awareness. Both are woven into each discipline's technical lessons, not taught only as stand-alone classes (Baldwin 2008). [read]
- **DLR's GSOC:** The flight director programme includes "advanced voice-ops" practice (Schmidhuber 2024). [read]
- **DLR anomaly-handling board game** (SpaceOps 2023): it proposes in-game control-room speech rules and the NATO phonetic alphabet. [read]

The lesson is that learners must end up *speaking* the short forms. Narration should model them consistently, with the exact words on the procedure card, after first giving the meaning.

**Second-language learners.** I found no controlled study on acronyms in particular for listeners learning in a second language. Treat this as a gap. The nearest evidence:
- Lecture-vocabulary research ties L2 listening comprehension to vocabulary coverage: about 90% coverage needs roughly the 2,000 most frequent word families. It also notes that *scripted* lectures let the speaker choose words carefully (Dang 2022). [read]
- Dahm (2012) found that native and non-native speakers disagree about *what counts as* jargon, so "avoid or explain jargon" advice misfires when the author judges jargon by their own sense. [read: abstract]
- Alderson (2009): L2 load interacts with workload. [read]

Implications:
- In French narration, the English identifier (AOCS, LEOP, SID) is an *extra* unknown for francophones. Say the French expansion and show the identifier on screen.
- Do not assume that an English acronym is transparent to an anglophone who does not know the domain.

---

## 2. When animation helps

**Meta-analyses.**

*Höffler & Leutner (2007)*: 26 studies and 76 comparisons. Overall weighted d = 0.37 (95% CI 0.25–0.49) in favour of animation over static pictures. [read] The moderators:

| Moderator | Category | d |
|---|---|---|
| Role of the animation | Representational (the motion is the content) | 0.40 |
| | Decorational | −0.05 |
| Type of knowledge | Procedural-motor | 1.06 |
| | Declarative | 0.44 |
| | Problem solving | 0.24 |
| Format | Video | 0.76 |
| | Computer animation | 0.36 |

The authors caution that video was almost always representational, so the video advantage may come from that.

*Berney & Bétrancourt*: 61 experiments and 140 comparisons, N = 7,036. Hedges' g = 0.226 (95% CI 0.12–0.33), with high heterogeneity (I² = 78%). System-paced animations did significantly better (g = 0.31) than animations with learner control over pace. Iconic representations (realistic or schematic) gave g = 0.245. [read: EARLI 2016 conference paper. The fuller *Computers & Education* 2016 article was not read, and the conference text has some count inconsistencies.]

**Tversky, Morrison & Bétrancourt (2002)** set out two principles. [read]
- *Congruence*: the structure of the graphic should match the structure of the concept. Change over time therefore suits animation.
- *Apprehension*: the graphic must be "readily and accurately perceived and comprehended". Animations often fail here because they are too fast or too complex, and viewers break continuous motion into steps anyway.

Many apparent animation wins compared animations with static graphics that carried *less information*, or mixed animation up with interactivity or prediction. Animation may help most in three cases: the manner and timing of motion, continuous change, and real-time reorientation in space and time.

**Segmenting and pacing.** Segmenting works for two reasons (Spanjers et al. 2010 review). [read: abstract] It reduces the load caused by transience, and it marks the natural event boundaries. Tversky finds learner control can offset apprehension problems, yet Berney & Bétrancourt found system pacing better. One way to reconcile the two: use system pacing *within* a segment, and give the learner control *between* segments, through pauses, replay and scrubbing.

**Cueing in animations (de Koning et al. 2009).** [read]
- Cues serve three functions: *selection*, *organisation* and *integration*.
- Animated cues must guide attention "both spatially and temporally".
- Cues reliably direct attention but have not consistently improved deeper causal understanding.
- Colour cues that spread in sync with the causal chain helped (Lowe & Boucheix 2007). Changing playback speed guided attention better than arrows did.

So a cue alone is not enough: pair it with a question or a prediction prompt.

**Practical guidance for engineering and space explainers** (my synthesis):
- **Animate where motion carries the meaning.**
  - Energy flow across an orbit: sun to array to battery to loads, with eclipse entry and exit, and state of charge (SoC) rising and falling.
  - Attitude rates decaying under B-dot, and the momentum picture.
  - The path of a telecommand packet and its verification: S1 acceptance, start and completion, and light-time delay.
  - Ground-track and visibility geometry: why passes are short.
- **Do not animate** labels, static layouts or settings screens. A still image with a highlight is enough.
- **Prefer schematic over decorative.**
- **Segment at event boundaries** (eclipse entry, end of pass) and put an H5P question at each boundary.
- **Replay real simulator telemetry** with the `shared/ui-viz` modules so that what is shown matches the console. Use Manim or Motion Canvas only for the parts the console cannot show, such as equations and packet layouts.
- **Screen captures of a procedure** are already procedural video, where the effect is largest. A concept animation belongs in a *separate* short explainer that the procedure video links to. Do not put it inside the procedure walkthrough.

---

## 3. Team vs position training in mission operations

**NASA JSC (ISS).** A Flight Operations Directorate briefing (NTRS 20160012370) describes the flow. [read]
- **Boot camp** for all new hires: culture, basic ISS operations, and a first certification ("ISS Command").
- **Discipline technical training**, in two styles:
  - "spiral": a high-level view of every subsystem first;
  - "segmented": one subsystem in depth before the next.
- **Mini Sims**, focused on "practicing the soft skills".
- **Integrated Sims** with the full team, on complex cases.
- Controllers certify in a back-room (MPSR) position before moving to a front-room (FCR) role, typically about 18 months to the first certification.
- Each division has its own certification flow, with progression through positions of increasing responsibility.

Baldwin (2008) adds the following. [read]
- Space Flight Resource Management (SFRM), NASA's form of crew resource management, has eight team skills plus the STAR process (Stop, Think, Act, Review).
- SFRM is integrated into the technical lessons, because team skills "are best learned" in their operational context.
- Controllers used to complete "30 to 50 eight-hour integrated simulations" before certification. The redesign targeted 3–5 integrated sims plus 2–4-hour themed mini-sims.
- Mentoring continues at 1, 3 and 6 months after certification.
- Shuttle-era training rests on mission simulations: "train like you fly" (NTRS 20110003658). [read: abstract]
- The "generalist vs specialist" framing and JSC Flight Director certification details: [unverified, not found in the sources read]

**ESA/ESOC.** [read: ESA articles]
- Before a launch or critical operation, flight control teams run "dozens" of nominal and contingency simulations, sometimes 15 for a launch.
- Dedicated simulation officers run the sims and inject failures.
- In the Head of Mission Operations' words, "95% of what we exercise will never be applied."
- ATV sims were whole-team and multi-centre, with a briefing, unannounced faults and a debrief. Teams had to "prioritise and delegate".
- None of the articles describes individual certification.

ESA Academy trained the EIRSAT-1 student CubeSat team at ESOC in two ways. [read]
- The whole team learned together, alongside the OPS-SAT team.
- In the control-room simulation, each student held a role (operations manager, power, data handling) and the team solved one anomaly together.

**DLR GSOC.** The internal Ops Academy has three tiers. [read]
- **Basic**: open to everyone at the centre, built on a Spacecraft Operations Course that has run for more than 20 years and is also reused for universities.
- **Specialist**: for subsystem engineers, still being defined.
- **Key positions**: the LEOP Flight Director programme, with role-focused simulations and voice operations.

Training is in short units (lecture, hands-on exercise or case study) and uses e-learning and serious games. The 2023 SpaceOps paper notes two constraints on simulations: they need "the entire S/C operations team", and routine operations rarely give anomaly practice. [read]

**The common pattern** is a shared foundation for everyone, then position-specific depth and certification, then integrated team simulations, where team skills, voice protocol and shared situational awareness are practised.

**Team-cognition evidence.**
- *DeChurch & Mesmer-Magnus (2010)*: a meta-analysis of 65 studies. Team cognition, including shared mental models, relates strongly to team processes and performance, and adds predictive power beyond behavioural and motivational factors. [read: abstract]
- *Marks, Sabella, Burke & Zaccaro (2002)*: two experiments with 45 and 49 teams. Cross-training improved shared team-interaction mental models, and coordination carried the effect of those models on to performance. Results on *how deep* the cross-training had to be were mixed. [read: abstract] Which cross-training types they compared: [unverified]
- *Volpe et al. (1996)* and *Cannon-Bowers et al. (1998)*: cross-trained teams anticipate each other's needs better, and cross-training builds knowledge of the other positions. [secondary] The usual three-level typology:
  - positional clarification: being told about the other roles;
  - positional modelling: watching the other roles;
  - positional rotation: doing the other roles.
  The source of that typology: [secondary/unverified]
- *Salas et al. (2008)*: 93 effect sizes from 2,650 teams. Team training has moderate positive effects on cognitive, affective, process and performance outcomes. Training content, team stability and team size moderate the effect. [read: abstract] Salas summarises it as roughly 20% of team-performance variance. [read: interview] Exact effect sizes: [unverified]

**Implications for the videos.**
- **Common videos build the shared mental model.** That means the card mechanics, GO/NO-GO, the pass timeline, alarms and acknowledgements, logbook and voice conventions, the shape of LEOP, and *who owns what and what each seat needs from the others*. Every learner gets these.
- **Position videos build depth for one seat's certification.** Thresholds, commanding and diagnosis belong here.
- **Make other seats' videos available as low-cost cross-training.** This is positional clarification and modelling. They serve the flight director in particular, whose job is integration.
- **Interdependencies are the core content of cross-training,** so each position video should state them explicitly. That also makes it useful to the rest of the team.

---

## 4. Rules for the ORBIT NORTH video scripts

1. **Expand once per video, long form first.** On the first spoken use, say the full form, then the short form the team says: "the attitude and orbit control system, the AOCS"; "le système de contrôle d'attitude et d'orbite, le SCAO". After that, use only the short form. Take expansions from `video/lexicon/acronyms.yaml` and keep each concept to one word per language. (WCAG G97; 18F; Language Portal; OQLF)
2. **Show the written form at the moment of expansion.** Put the identifier as a short on-screen label, such as "AOCS", "SID 2" or "NOM-001", where it is spoken. This helps L2 listeners, catches acronyms said as words (nom, lee-op) and covers TTS mispronunciations. Keep every expansion in a glossary reachable from the H5P page as well. (WCAG 3.1.4 "programmatically determinable"; apprehension)
3. **Exempt names, but gloss what they do.** Mode names, on-screen values and dictionary words (GO, SAFE, DETUMBLE, GPS, EOSAT-1) need no expansion. A mode name gets a short gloss of its *function* the first time: "DETUMBLE, the mode that slows the tumble".
4. **Gloss jargon by function in one clause, and keep the term.** B-dot, light time and orbit-average margin stay in the script, because learners must use them on the loop. Add a short "what it does" clause at first use, and judge "opaque" from the viewpoint of a week-2 student working in their second language, not from the author's. (Phraseology practice; Dahm 2012)
5. **No more than about two new terms per step.** If a step brings in three or more acronyms, move the extra ones to an earlier step or to the pretraining video. Do not stack expansions in one sentence.
6. **Pretrain the console vocabulary.** Make one short team video per week, "Words on the console": the names and behaviour of the subsystems, modes and data products used that week, with H5P recall questions. Learners watch it before that week's procedure videos. (Pretraining, median d = 0.85)
7. **Fade expansions across the series, but never remove them.** Mark each acronym in the register by the week it is introduced.
   - Weeks before and including that week: full expansion.
   - Later weeks: a short gloss ("the AOCS, attitude control").
   - Core terms after about week 4: on-screen label plus glossary only.

   Each video still expands every term once, because learners watch out of order. Only the *length* of the expansion shrinks. (Expertise reversal)
8. **Add an animated explainer only when motion carries the meaning.** Animate continuous change that the learner must reason about and that the static console cannot show, such as energy flow over an orbit, rate decay under B-dot, a packet path with verification, or pass geometry. Use a schematic style and drive it from real simulator telemetry where possible (ui-viz replay). Do not animate layouts or settings. (Höffler & Leutner: representational d = 0.40, decorational ≈ 0; congruence)
9. **Put animations in separate explainer videos, segmented and system-paced.** Use 3–6 minute concept videos linked from the procedure video. Within each segment the animation runs at the system's pace. Each segment ends at a natural event boundary with an H5P question or prediction prompt, and scrubbing and replay stay available. (Berney & Bétrancourt; Spanjers et al. 2010; Tversky et al.)
10. **Cue in time and space, and follow every cue with a question.** Highlights or spreading colour should move with the causal chain and appear when the narration names the element. A cue on its own does not create understanding, so pair it with a question. (de Koning et al. 2009)
11. **Tag every video "team" or with position keys, and route by tag.**
    - **Team** videos are required for everyone and cover the shared mental model: card mechanics, GO/NO-GO, passes, alarms and acknowledgements, logbook and voice, the shape of LEOP, and who owns what.
    - **Position** videos are required only for the seat that commands or judges that content.
    - The flight director sees all of them.
    - Each learner also takes one other seat's videos as cross-training. Rotate that seat over the term.

    (NASA, ESOC and GSOC pattern; Marks et al. 2002; Salas et al. 2008)
12. **Open every position video with its interdependencies, and model the loop phrasing.** In about 15 seconds, say who depends on this seat and what it reports, and to whom. Use the card's exact phrases (GO/NO-GO, ACK, the card IDs) the same way every time, in both languages, so that narration doubles as phraseology training. (Cross-training content; voice-loop training in Baldwin 2008 and GSOC)

---

## Sources (read for this note)

- W3C, Understanding SC 3.1.4 Abbreviations (WCAG 2.2): https://www.w3.org/WAI/WCAG22/Understanding/abbreviations.html
- 18F Content Guide, Abbreviations and acronyms: https://guides.18f.gov/content-guide/our-style/abbreviations-and-acronyms
- Language Portal of Canada, "Alphabet soup": https://nos-langues.canada.ca/favourite-articles/alphabet-soup
- OQLF Vitrine linguistique, Généralités sur les sigles et acronymes: https://vitrinelinguistique.oqlf.gouv.qc.ca/21385/les-abreviations-et-les-symboles/les-sigles-et-les-acronymes/generalites-sur-les-sigles-et-acronymes
- Barnett & Doubleday (2020), The growth of acronyms in the scientific literature, eLife: https://elifesciences.org/articles/60080
- Purdue/Phys.org on Hales, Williams & Rector (2017), press release only: https://phys.org/news/2017-02-abbreviations-exclude-readers-scientific-experts.html
- Mayer, Pretraining principle (Cambridge Handbook / Multimedia Learning chapter abstract): https://www.cambridge.org/core/books/abs/multimedia-learning/pretraining-principle/01791D57F5D4164251269E6DF56A8BF1
- Fading prompts / expertise reversal abstract (repository title metadata mismatched): https://ro.uow.edu.au/edupapers/140
- Alderson (2009), Air safety, language assessment policy and policy implementation, ARAL: https://eprints.lancs.ac.uk/id/eprint/33530/1/download.pdf
- Dang (2022), vocabulary in academic lectures: https://eprints.whiterose.ac.uk/193067/3/Dang%20%282022%29_%20academic%20lecture_Manuscript_6th%20submission.pdf
- Dahm (2012), Coming to terms with medical terms: https://researchers.mq.edu.au/en/publications/coming-to-terms-with-medical-terms-exploring-insights-from-native
- Höffler & Leutner (2007), Instructional animation versus static pictures: a meta-analysis: https://wikicap.ulb.be/images/e/ef/Hoffler_Leutner_2007.pdf
- Berney & Bétrancourt (2016), EARLI conference paper: https://tecfa.unige.ch/perso/sandra/pdf/Earli2016_berney_betrancourt_FINAL.pdf
- Tversky, Morrison & Bétrancourt (2002), Animation: can it facilitate?: https://www.uky.edu/~gmswan3/575/Tversky_2002.pdf
- de Koning, Tabbers, Rikers & Paas (2009), Towards a framework for attention cueing in instructional animations: https://link.springer.com/content/pdf/10.1007/s10648-009-9098-7.pdf
- Spanjers, van Gog & van Merriënboer (2010), segmentation of dynamic visualizations (abstract): https://repub.eur.nl/pub/19682
- NASA JSC FOD, flight controller training flow briefing (NTRS 20160012370): https://ntrs.nasa.gov/api/citations/20160012370/downloads/20160012370.pdf
- NASA, thirty years of Shuttle flight controller training (NTRS 20110003658): https://ntrs.nasa.gov/api/citations/20110003658/downloads/20110003658.pdf
- Baldwin (2008), integrating SFRM into ISS flight controller training (NTRS 20080041534): https://ntrs.nasa.gov/api/citations/20080041534/downloads/20080041534.pdf
- ESA, "Is this the real launch or is this just fantasy?": https://www.esa.int/Enabling_Support/Operations/Is_this_the_real_launch_or_is_this_just_fantasy
- ESA, ATV operations: training the team: https://www.esa.int/Enabling_Support/Operations/ATV_operations_training_the_team
- ESA Education, EIRSAT-1 team at ESOC: https://www.esa.int/Education/Educational_Satellites/EIRSAT-1_team_discovers_what_it_takes_to_be_Spacecraft_Operators
- Schmidhuber (2024), GSOC training initiatives (DLRK): https://elib.dlr.de/210055/1/DLRK24_Trainings_inititativen_Schmidhuber.pdf
- DLR, "Operation Payload" board game, SpaceOps 2023: https://publications.spaceops.org/2023/download_by_id.php?id=0387
- Marks, Sabella, Burke & Zaccaro (2002), The impact of cross-training on team effectiveness (abstract): https://stars.library.ucf.edu/facultybib2000/3347
- DeChurch & Mesmer-Magnus (2010), The cognitive underpinnings of effective teamwork (abstract): https://stars.library.ucf.edu/facultybib2010/100
- Salas et al. (2008), Does team training improve team performance? (abstract): https://stars.library.ucf.edu/scopus2000/9425
- Salas interview, AHRQ PSNet: https://psnet.ahrq.gov/node/33720/psn-pdf
- Table citing Volpe et al. (1996) and Cannon-Bowers et al. (1998) (secondary): https://appliedvolc.biomedcentral.com/articles/10.1186/s13617-014-0020-8/tables/2

**Not verified:**
- Hales et al. (2017) experimental results.
- The *Computers & Education* version of Berney & Bétrancourt.
- Spanjers et al. (2011) expertise reversal findings.
- Salas (2008) numeric effect sizes.
- The cross-training types compared in Marks et al. (2002).
- The original source of the positional clarification / modelling / rotation typology.
- JSC Flight Director certification and "generalist vs specialist" details.
- Any direct study of acronyms with L2 listeners (none found).
