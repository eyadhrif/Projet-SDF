# PROMPT MAÎTRE — Projet SdF binôme : FMDS & Maintenance prédictive (C-MAPSS FD001)

À donner à Claude Code, ouvert à la racine du projet. Lis d'abord `CLAUDE.md` (contexte, structure, décisions) et `README.md` (méthode et résultats), puis applique ce prompt.

---

## 0. Rôle et contexte

Tu es l'assistant de recherche et d'ingénierie d'Eya DHRIF et de Salma MOUEDDEB.

- **Formation :** GMAM 3, ENSIT
- **Module :** Sûreté de fonctionnement et maintenance
- **Encadrant :** M. Fayçal Ben Hmida

**Le projet existe déjà et fonctionne :**
- Pipeline Python : `backend/pipeline/`, lancé par `run_all.py`
- API FastAPI : `backend/api/main.py`
- Dashboard React : `frontend/`
- Résultats dans `backend/results/*.json`

**Ta mission, en trois phases :**
0. **Phase 0 — Tests exhaustifs.** Tester chaque détail du projet existant avant toute modification (section 1 bis)
1. **Phase A — Consolidation du code pour la Version 1.** Des modifications limitées et justifiées, pour que chaque chiffre du rapport soit produit par le code et reproductible
2. **Phase B — Rédaction du rapport scientifique, Version 1**, selon la stratégie progressive décrite ci-dessous

**Règles de travail :**
- Langue : **français** pour le code commenté, le rapport et les messages de commit
- Respecter la répartition des tickets (Eya / Salma) indiquée dans les en-têtes de fichiers
- Avant toute modification importante, présenter le plan et attendre la validation d'Eya

---

## 1. Données de référence (vérifiées, à ne pas modifier sans relancer le code)

### Jeu de données

| Élément | Valeur |
|---|---|
| Source | NASA C-MAPSS FD001 (Saxena et al., 2008) : 1 condition opératoire, 1 mode de défaillance (dégradation HPC) |
| Entraînement | 100 moteurs suivis jusqu'à la défaillance, 20 631 lignes |
| Test | 100 moteurs tronqués, 13 096 lignes |
| Longueur des séries de test | 31 à 303 cycles, moyenne 131 |
| RUL réel de test | 7 à 145 cycles, moyenne 75,5 |
| Variables | 21 capteurs + 3 réglages opérationnels |
| Unités pour la fiabilité | 200 : 100 défaillances observées et 100 censures à droite (moteurs de test au dernier cycle observé) |

### Fiabilité

| Modèle | Paramètres | Validation |
|---|---|---|
| Weibull 2P par MCO (rangs de Bernard) | β = 5,52, η = 223,4 | R² = 0,894 |
| Weibull 2P par MV | β = 4,41, η = 225,0 | KS p = 0,013, **rejeté** |
| Weibull 2P par MV avec censure | β = 4,82 [4,22 ; 5,42], η = 236,6 | — |
| **Weibull 3P (retenue)** | **β = 1,83, η = 91,3, γ = 125,2** | **KS p = 0,32** |
| Log-normale | — | Équivalente (ΔAIC < 1) |

**Indicateurs du modèle retenu :**
- MTTF = 206,3 cycles
- B1 = 132,6 cycles
- B10 = 151,9 cycles
- B50 ≈ 199,9 cycles (calculé à la main, **à intégrer au code** en phase A)
- Médiane Kaplan-Meier = 202 cycles

### Maintenabilité et disponibilité (hypothèse : temps de réparation simulés)

- Temps de réparation simulés selon une loi log-normale : médiane 16 h, σ = 0,6, graine 42, avec 1 cycle ≈ 2 h
- MTTR = 17,3 h
- A = 95,98 %
- Remplacement préventif avec Cc = 5·Cp : T* ≈ 131 cycles, gain de 68 % sur le coût

### Détection de l'état de santé

- 7 capteurs constants écartés, 12 retenus (|tendance| ≥ 0,5)
- Classe « critique » : RUL ≤ 30 cycles
- Validation GroupKFold par moteur

| Classifieur | AUC test | Rappel |
|---|---|---|
| Gradient Boosting | 0,991 | 0,657 |
| SVM | 0,974 | — |

### Durée de vie résiduelle (RUL)

| Modèle | RMSE | MAE | Biais | Score NASA |
|---|---|---|---|---|
| Dégradation bayésienne (Eya) | 24,47 | 18,98 | +13,5 | 3743 |
| LSTM (Salma) | 15,35 | 11,22 | +2,2 | 485 |

L'intervalle 10–90 % du modèle de dégradation ne couvre le RUL réel que dans **54 %** des cas.

**Si un chiffre change après une modification du code, mettre à jour le rapport, le README, `CLAUDE.md` et le dashboard, et signaler le changement.**

---

## 1 bis. PHASE 0 — Tests exhaustifs (obligatoire, avant toute modification)

**Règle absolue : rien n'est considéré comme terminé tant qu'il n'est pas testé.** Chaque détail du projet (chiffre, fonction, endpoint, page, figure, phrase chiffrée du rapport) doit être couvert par un test automatique ou par une vérification documentée.

Les tests sont écrits **avant** la phase A. Ils figent l'état actuel, ce qui permet de détecter toute régression lors des modifications.

### 0.1 Organisation

- Dossier `tests/` avec **pytest** ; un fichier par module : `test_data.py`, `test_fmds.py`, `test_features.py`, `test_health.py`, `test_rul_degradation.py`, `test_rul_lstm.py`, `test_api.py`, `test_results.py`, `test_report.py`
- Tests front dans `frontend/tests/` avec **Playwright**
- Un script unique **`run_tests.sh`** (et `run_tests.bat` pour Windows) qui lance tout, puis produit `tests/RAPPORT_TESTS.md` : nombre de tests, réussites, échecs, durée, couverture
- Couverture du code Python mesurée avec `pytest-cov` ; objectif **≥ 90 %** sur `backend/pipeline/` et `backend/api/`
- Les tests rapides (< 1 min) et les tests lents (réentraînement complet) sont séparés par un marqueur `@pytest.mark.slow`

### 0.2 Tests des données (`test_data.py`)

- Les 3 fichiers FD001 existent ; nombre de lignes exact (20 631 et 13 096) et 26 colonnes
- 100 moteurs en entraînement, 100 en test ; aucun moteur manquant ; cycles consécutifs à partir de 1, sans trou ni doublon
- Aucune valeur manquante ni infinie
- RUL d'entraînement = 0 au dernier cycle de chaque moteur, strictement décroissant de 1 par cycle
- RUL de test au dernier cycle = valeur de `RUL_FD001.txt` pour chaque moteur
- Table de durées de vie : 200 lignes, 100 statuts 1 et 100 statuts 0 ; durée minimale des défaillances = 128

### 0.3 Tests de fiabilité et FMDS (`test_fmds.py`)

**Validation sur cas connus** (données simulées dont on connaît la vraie loi) :
- Un échantillon Weibull simulé (β = 2, η = 100, n = 5000) : les estimations MCO et MV retrouvent β et η à 5 % près
- Un échantillon Weibull 3P simulé : γ est retrouvé
- Kaplan-Meier sans censure = fonction de répartition empirique
- Kaplan-Meier sur un petit exemple calculé à la main (exemple du cours) : valeurs exactes
- Nelson-Aalen : exp(−H) proche de KM
- Log-normale simulée : μ et σ retrouvés ; MTTR = exp(μ + σ²/2)

**Propriétés mathématiques :**
- R(t) décroissante, entre 0 et 1, R(0) = 1
- R(t) = 1 pour t ≤ γ ; λ(t) = 0 pour t ≤ γ
- F + R = 1
- L'intégrale de f vaut 1 (à 10⁻³ près)
- B1 < B10 < B50
- MTTF = γ + η·Γ(1 + 1/β), comparé à l'intégrale numérique de R
- Disponibilité A(t) : A(0) = 1, converge vers A∞ = MUT / (MUT + MDT)
- Coût de remplacement préventif : T* est bien un minimum (coût plus élevé à T* ± 5) ; coût à T* < coût sans préventif

**Non-régression des chiffres** : toutes les valeurs de la section 1 sont vérifiées avec une tolérance explicite (par exemple β à ±0,01, RMSE à ±0,5 pour le LSTM, qui dépend du matériel).

### 0.4 Tests de l'indicateur de santé et de la détection (`test_features.py`, `test_health.py`)

- Capteurs écartés = exactement {s1, s5, s6, s10, s16, s18, s19} ; capteurs retenus = les 12 attendus
- Features fenêtrées : aucune valeur manquante, y compris aux premiers cycles de chaque moteur ; aucune fuite entre moteurs (la fenêtre ne déborde jamais sur le moteur précédent)
- HI : moyenne ≈ 0,94 en début de vie et ≈ 0 en fin de vie (tolérances fixées) ; corrélation HI / cycle négative pour chaque moteur d'entraînement
- GroupKFold : aucun moteur présent à la fois dans un pli d'entraînement et de validation
- Étiquettes : critique ⇔ RUL ≤ 30
- Métriques recalculées indépendamment avec scikit-learn et comparées aux JSON : AUC, précision, rappel, F1, matrice de confusion (somme = nombre de lignes de test)

### 0.5 Tests des modèles de RUL (`test_rul_degradation.py`, `test_rul_lstm.py`)

**Modèle de dégradation :**
- Sur une trajectoire synthétique sans bruit qui atteint le seuil à une date connue : le RUL prédit est exact à ±2 cycles
- L'a posteriori se resserre quand le nombre d'observations augmente (trace de la covariance décroissante)
- P10 ≤ médiane ≤ P90 ; RUL ≥ 0 ; résultats identiques avec la même graine
- Couverture empirique recalculée = valeur du JSON

**LSTM :**
- Formes des tenseurs (lots, 30, 12) ; sortie ≥ 0
- Série plus courte que 30 cycles : remplissage correct
- Le modèle sauvegardé `lstm_rul.pt` se recharge et redonne exactement les mêmes prédictions
- Test lent : un réentraînement complet donne un RMSE de test dans [13 ; 18]

**Métriques :**
- RMSE, MAE, biais et score NASA recalculés indépendamment sur des cas simples calculés à la main (une prédiction en avance, une en retard)
- Asymétrie du score NASA : un retard de d coûte plus qu'une avance de d

### 0.6 Tests de l'API (`test_api.py`, avec `TestClient` de FastAPI)

- Chaque endpoint (`/api/fmds`, `/api/health`, `/api/rul`, `/api/fleet`, `/api/engines/{id}`) répond 200 et respecte un schéma attendu : clés présentes, types, longueurs
- `/api/engines/0` et `/api/engines/101` répondent 404 ; un identifiant non numérique répond 422
- Résultats absents : réponse 503 avec message clair
- La racine `/` sert le dashboard ; `/docs` fonctionne
- Les données servies par l'API sont identiques aux fichiers JSON

### 0.7 Tests des résultats exportés (`test_results.py`)

- Tous les fichiers JSON existent, sont valides et sans NaN ni valeur infinie
- Cohérence croisée : les 100 moteurs de `engines.json` correspondent aux lignes de `rul.json` ; dernier cycle et RUL réel identiques
- Chaque figure et chaque tableau générés en phase A existent et ne sont pas vides

### 0.8 Tests du dashboard (Playwright)

- Les 4 pages se chargent, **sans erreur dans la console** ; capture d'écran de chaque page en largeur 1440 px et 390 px (mobile)
- Chaque graphique est rendu (présence de l'élément SVG non vide) ; chaque KPI affiche une valeur et non « — »
- Les KPI affichés correspondent aux valeurs des JSON (MTTF, A, β, RMSE)
- Interactions : changement de moteur dans les sélecteurs, tri du tableau de flotte, clic sur une ligne, navigation entre pages
- La version autonome `dashboard_autonome.html` s'ouvre sans serveur (`file://`) et réussit les mêmes tests
- `npm run build` et `npm run build:static` réussissent sans erreur

### 0.9 Tests du rapport (`test_report.py`), à partir de la phase B

- **Chaque nombre** cité dans le rapport est extrait automatiquement et confronté à sa source JSON. Les chiffres du rapport sont générés depuis les JSON par des macros ou variables, et non tapés à la main
- Chaque figure et chaque tableau sont référencés dans le texte ; aucune référence cassée ; toutes les citations bibliographiques existent dans la bibliographie
- Le document compile sans erreur ni avertissement bloquant
- Aucune perspective n'est formulée au passé ou comme un résultat : relecture ciblée du chapitre Perspectives, avec une liste de contrôle

### 0.10 Installation propre et reproductibilité

- Test d'installation à partir de zéro, dans un environnement virtuel neuf (`requirements.txt` seul), sous **Windows** (machine d'Eya) et sous Linux
- Deux exécutions de `run_all.py` donnent des résultats identiques, hors entraînement du LSTM (tolérance documentée)
- Les versions exactes des bibliothèques sont figées dans `requirements-lock.txt`

### 0.11 Définition de « terminé »

Un ticket est terminé seulement si :
1. Tous les tests (anciens et nouveaux) passent
2. Un nouveau test couvre la modification
3. La couverture ne baisse pas
4. Le dashboard et la version autonome sont reconstruits et retestés
5. La documentation est à jour
6. `tests/RAPPORT_TESTS.md` est régénéré et commité avec le ticket

**En cas d'échec d'un test :** ne jamais modifier le test pour le faire passer sans justification écrite. Trouver la cause, corriger le code, et signaler à Eya tout écart sur un chiffre de la section 1.

---

## 2. PHASE A — Modifications du code pour la Version 1

Objectif : rendre le rapport **traçable**. Tout chiffre ou figure du rapport doit provenir d'un script. Pas de nouvelle méthode lourde à ce stade.

| # | Modification | Fichier(s) | Responsable |
|---|---|---|---|
| A1 | Ajouter **B50** (et garder B1, B10) dans les sorties de fiabilité ; l'afficher sur le dashboard | `fmds.py`, `Fiabilite.jsx`, `Overview.jsx` | Eya |
| A2 | Exporter un **tableau de description des données** : tailles, longueurs de séries, statistiques des capteurs, capteurs constants | `run_all.py` → `results/dataset.json` + `.csv` | Salma |
| A3 | Script **`backend/report_figures.py`** qui génère toutes les figures du rapport en PNG 300 dpi et en PDF (matplotlib, style sobre, libellés en français) dans `report/figures/`, à partir des fichiers `results/*.json` | nouveau fichier | Eya + Salma |
| A4 | Script qui génère les **tableaux du rapport** (LaTeX et/ou Markdown) dans `report/tables/` à partir des JSON | `report_figures.py` ou `report_tables.py` | Eya + Salma |
| A5 | **Reproductibilité** : fixer et documenter toutes les graines ; écrire dans `results/run_info.json` les versions des bibliothèques, la date et la durée d'exécution | `run_all.py` | Salma |
| A6 | Ajouter la **couverture empirique** des intervalles et la **calibration du biais** dans les métriques du modèle de dégradation, sans changer le modèle | `run_all.py` | Eya |
| A7 | Mettre à jour `README.md` et `CLAUDE.md` ; relancer `run_all.py` ; reconstruire `frontend/dist` et la version autonome | — | — |
| A8 | Versionner : un commit par modification, puis le tag `v1.0-rapport` quand la Version 1 est validée | git | — |

**Hors périmètre de la phase A** (renvoyé aux perspectives ou à la Version 2) : nouveaux modèles, autres sous-ensembles C-MAPSS, XAI, optimisation d'hyperparamètres à grande échelle.

---

## 3. STRATÉGIE DE RÉDACTION PROGRESSIVE ET GESTION DES VERSIONS DU RAPPORT

### 3.1 Principe général

Le rapport est développé progressivement, en plusieurs versions successives.

La première version est une étude scientifique structurée, fondée uniquement sur :
- les travaux réellement réalisés
- les modèles effectivement implémentés
- les données disponibles
- les résultats déjà obtenus

Il n'est pas nécessaire de réaliser immédiatement toutes les analyses avancées, les expérimentations supplémentaires ou les développements industriels envisageables. L'objectif est une première version cohérente, rigoureuse et défendable, qui identifie clairement les améliorations prévues pour les versions suivantes.

### 3.2 Version 1 : travaux actuels — « Comprendre et démontrer »

La priorité est de présenter et de valoriser correctement le travail déjà réalisé. La Version 1 doit contenir :

- Une présentation claire du problème industriel et des objectifs
- Un état de l'art ciblé et pertinent
- Une description détaillée des données : origine, nature, structure et **taille exacte de l'échantillon**
- Une explication approfondie des modèles réellement utilisés
- Les fondements mathématiques et les hypothèses de chaque méthode
- La justification des choix méthodologiques et des paramètres
- Le workflow et l'architecture du système (pipeline, API, dashboard)
- Le protocole expérimental effectivement appliqué
- Les métriques utilisées et leur interprétation
- Les résultats réellement obtenus
- Une comparaison des méthodes, lorsque les expérimentations disponibles le permettent
- Une première interprétation des résultats dans le contexte industriel
- Une discussion des limites actuelles

Chaque élément doit être assez expliqué pour garantir la compréhension et la crédibilité scientifique. Privilégier la profondeur et la cohérence plutôt que la multiplication des méthodes.

### 3.3 Perspectives : développements les plus avancés

Les développements les plus complexes, les plus coûteux en temps, ou qui demandent des données ou expérimentations supplémentaires, sont présentés dans le chapitre **Perspectives**. Notamment :

- Des modèles probabilistes plus avancés (par exemple un modèle de dégradation exponentiel ou à processus de Wiener, à la place de la base polynomiale actuelle)
- L'amélioration de l'estimation du RUL et de la quantification des incertitudes (la couverture actuelle de 54 % justifie ce point)
- L'étude approfondie des indicateurs B10 et B50 : intervalles de confiance par bootstrap, sensibilité au modèle retenu
- L'intégration de covariables externes : FD001 n'a qu'une condition opératoire, ce point nécessite **FD002 et FD004**
- Des méthodes avancées d'Explainable AI (SHAP sur le classifieur et le LSTM)
- L'amélioration des stratégies de pondération (fusion des capteurs dans le HI, pondération des modèles dans l'ensemble)
- Des analyses de sensibilité et de robustesse plus approfondies (seuil de criticité, taille de fenêtre, hypothèses de réparation)
- Des benchmarks élargis entre plusieurs familles de modèles (CNN, GRU, Transformers, forêts de survie)
- Le passage de données simulées à des données industrielles réelles
- Des modèles hybrides et le Physics-Informed Machine Learning
- Le Deep Learning et les Transformers, lorsque c'est justifié
- Un système d'optimisation avancé pour la planification de la maintenance (au-delà de la politique d'âge fixe)
- L'intégration éventuelle d'un Digital Twin
- Une étude économique industrielle plus complète (coûts réels Cp et Cc, immobilisation)
- Le déploiement et la validation dans un environnement industriel réel

**Pour chaque perspective, préciser :**
1. Le développement envisagé
2. La motivation scientifique et industrielle
3. Les limites de l'approche actuelle qui le justifient
4. Les données et ressources nécessaires
5. Les méthodes et outils envisageables
6. Les expérimentations nécessaires pour le valider
7. Les bénéfices attendus
8. Les difficultés potentielles de mise en œuvre

Ne jamais présenter ces développements comme des travaux déjà réalisés.

### 3.4 Versions 2 et 3 : enrichissement progressif

- **Version 2 — Approfondir et améliorer :** nouvelles expérimentations, benchmarking avancé, covariables, XAI, analyses de sensibilité, de robustesse et de fiabilité
- **Version 3 — Consolider et industrialiser :** optimisation avancée, validation industrielle, étude économique, généralisation et perspectives technologiques

Ces évolutions sont guidées par :
- les remarques et recommandations de l'encadrement académique
- les lacunes identifiées dans la version précédente
- les résultats des nouvelles expérimentations
- la disponibilité de données supplémentaires
- la faisabilité scientifique et technique
- la pertinence pour le contexte industriel

Chaque nouvelle version améliore la précédente sans introduire de contradictions entre la théorie, la méthodologie, les résultats et les conclusions.

**Gestion des versions :**
- Le rapport est versionné dans `report/`
- Chaque version a un tag git (`v1.0-rapport`, `v2.0-rapport`, `v3.0-rapport`)
- Le fichier `report/CHANGELOG.md` liste ce qui a été ajouté ou modifié et pourquoi

### 3.5 Règles de rédaction et de cohérence scientifique

- Ne pas chercher à intégrer toutes les méthodes avancées dans la première version
- Ne pas multiplier les modèles sans justification scientifique
- Ne pas présenter une perspective future comme un résultat expérimental
- **Ne jamais inventer de données, de résultats ou de validations.** Tout chiffre vient de `backend/results/` ou d'un script du dépôt
- Distinguer systématiquement les travaux réalisés, les analyses en cours et les améliorations envisagées
- **Signaler explicitement les hypothèses**, en particulier les temps de réparation simulés et la conversion cycle → heures
- Maintenir une méthodologie logique et progressive
- Adapter le niveau de détail à l'état réel d'avancement

---

## 4. PHASE B — Plan du rapport, Version 1

Ce plan est à proposer et à faire valider avant la rédaction ; il peut être adapté. Les numéros de tickets renvoient au plan de sprints.

1. **Introduction**
   - Contexte industriel : maintenance des turboréacteurs, coût des défaillances en service
   - Problématique et objectifs
   - Contributions
   - Organisation du rapport
2. **État de l'art ciblé**
   - Indices FMDS
   - Estimation non paramétrique (KM, Nelson-Aalen) et paramétrique (Weibull 2P/3P, MCO, MV)
   - Maintenance préventive vs prédictive
   - Indicateurs de santé
   - Approches de RUL : modèles de dégradation et apprentissage profond
   - Travaux sur C-MAPSS
3. **Données**
   - Origine et protocole de simulation
   - Structure, tailles exactes (tableau A2)
   - Censure à droite
   - Capteurs constants et analyse exploratoire
4. **Méthodologie** (pour chaque méthode : fondements mathématiques, hypothèses, justification des paramètres)
   - 4.1 Fiabilité (FMDS-01, Eya) : KM avec IC de Greenwood (log-log), Nelson-Aalen et lissage par noyau, Weibull 2P par MCO et MV, Weibull 3P, tests KS et AIC, MTTF, B1, B10, B50, fiabilité conditionnelle
   - 4.2 Maintenabilité et disponibilité (FMDS-02, Salma) : hypothèse log-normale, MTTR, disponibilité intrinsèque, modèle markovien A(t), politique de remplacement à âge fixe (Barlow-Proschan)
   - 4.3 Feature engineering et indicateur de santé (PDM-01, Salma)
   - 4.4 Classification de l'état (PDM-02, Eya) : GroupKFold, métriques
   - 4.5 RUL par modèle de dégradation bayésien (RUL-01, Eya) : a priori de flotte, a posteriori conjugué, tirages, seuil incertain
   - 4.6 RUL par LSTM (RUL-02, Salma) : fenêtres, cible plafonnée, architecture, arrêt précoce
5. **Architecture et workflow du système**
   - Pipeline, API et endpoints
   - Dashboard (captures des 4 pages)
   - Reproductibilité
6. **Protocole expérimental et métriques**
   - Découpages, validation
   - KS, AIC, AUC, précision, rappel, F1, RMSE, MAE, biais, score NASA, couverture des intervalles
7. **Résultats**
   - Tableaux et figures générés en phase A
   - Comparaison des méthodes
8. **Discussion**
   - Interprétation industrielle : usure, période sans défaillance, intérêt du préventif à T*, apport du prédictif
   - Limites actuelles : réparations simulées, sous-ensemble FD001 unique, biais et sous-couverture du modèle de dégradation, faible précision sur un test déséquilibré
9. **Perspectives** (format en 8 points de la section 3.3)
10. **Conclusion**

**Annexes :** paramètres complets, structure du dépôt, guide de lancement, répartition du travail Eya / Salma.

**Format de sortie :** à confirmer avec Eya avant la rédaction (LaTeX avec PDF compilé, Word, ou document Claude). Les figures et tableaux viennent de `report/figures/` et `report/tables/`. Bibliographie complète, avec citations dans le texte.

---

## 5. Ordre d'exécution

1. Lire `CLAUDE.md`, `README.md` et le code ; confirmer que `python run_all.py` reproduit les chiffres de la section 1
2. **Phase 0** : écrire toute la suite de tests (section 1 bis), la faire passer sur le code actuel, et livrer le premier `tests/RAPPORT_TESTS.md`. Tout défaut découvert est signalé à Eya avant d'être corrigé
3. Proposer le plan détaillé de la phase A, puis l'exécuter après validation : un commit par ticket, chaque ticket respectant la définition de « terminé » (section 0.11)
4. Relancer le pipeline et **toute** la suite de tests, y compris les tests lents ; mettre à jour toute la documentation et le dashboard ; signaler tout écart de chiffres
5. Faire valider le format et le plan du rapport
6. Rédiger la Version 1 chapitre par chapitre, en faisant relire chaque chapitre ; lancer `test_report.py` après chaque chapitre
7. Vérification finale : suite de tests complète au vert, installation propre sous Windows, chaque chiffre du texte confronté aux JSON, chaque figure référencée, chaque hypothèse signalée
8. Poser le tag `v1.0-rapport` et remplir `report/CHANGELOG.md`, avec le rapport de tests joint

**Objectif final :** une Version 1 moins ambitieuse mais parfaitement justifiée, présentable devant l'encadrement, avec une marge d'amélioration claire pour les Versions 2 et 3.
