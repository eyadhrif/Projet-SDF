# Perspectives {#sec:perspectives}

## Introduction {-}

Ce chapitre présente les développements envisagés pour les Versions 2 et 3. **Aucun d'entre eux n'est réalisé à ce stade.** Pour chacun, les huit points suivants sont précisés : le développement envisagé, sa motivation, la limite actuelle qui le justifie, les données et ressources nécessaires, les méthodes envisageables, les expérimentations de validation, les bénéfices attendus et les difficultés prévisibles.

## Modèles de dégradation probabilistes plus avancés {#sec:p-degradation}

- **Développement :** remplacer la base polynomiale par un modèle exponentiel à coefficients aléatoires, puis par un processus de Wiener à dérive non linéaire [cite:gebraeel2005,si2012].
- **Motivation :** ces modèles décrivent mieux une dégradation qui s'accélère en fin de vie et intègrent naturellement le bruit de dégradation.
- **Limite actuelle :** le polynôme de degré {{deg_degre}} extrapole mal la fin de vie, ce qui contribue au biais de {{deg_biais}} cycles.
- **Données et ressources :** les mêmes données FD001 suffisent ; aucune ressource matérielle particulière.
- **Méthodes :** régression bayésienne sur le logarithme de l'indicateur, estimation par maximum de vraisemblance des paramètres du processus de Wiener, loi du premier temps de passage.
- **Validation :** comparaison du RMSE, du biais et du score NASA avec le modèle actuel, sur les mêmes moteurs de test.
- **Bénéfices attendus :** une réduction du biais et un modèle plus fidèle à la physique de l'usure.
- **Difficultés :** l'indicateur de santé peut devenir négatif, ce qui complique le passage au logarithme ; un recalage de l'indicateur sera nécessaire.

## Amélioration de l'estimation du RUL et de la quantification des incertitudes {#sec:p-incertitude}

- **Développement :** propager le bruit de mesure dans les trajectoires simulées et recalibrer les intervalles de prédiction.
- **Motivation :** un intervalle n'est utile pour planifier la maintenance que s'il couvre réellement le RUL dans la proportion annoncée.
- **Limite actuelle :** l'intervalle P10–P90 ne couvre le RUL réel que dans {{couverture_80}} % des cas.
- **Données et ressources :** les moteurs d'entraînement, dont une partie serait réservée à la calibration.
- **Méthodes :** simulation du bruit dans les trajectoires, recalibration par quantiles sur un jeu de validation, prédiction conforme.
- **Validation :** courbes de calibration à plusieurs niveaux, sur des moteurs jamais utilisés pour l'apprentissage ni pour la calibration.
- **Bénéfices attendus :** des intervalles fiables, utilisables pour un remplacement fondé sur un niveau de risque maîtrisé.
- **Difficultés :** des intervalles mieux calibrés seront aussi plus larges ; il faudra trouver un compromis entre couverture et utilité.

## Étude approfondie des indicateurs B10 et B50 {#sec:p-bp}

- **Développement :** calculer des intervalles de confiance des durées $B_{10}$ et $B_{50}$ et étudier leur sensibilité au choix de la loi.
- **Motivation :** ces durées servent à fixer des intervalles de maintenance ; leur incertitude doit être connue.
- **Limite actuelle :** les durées $B_p$ sont données sans intervalle de confiance, et deux lois équivalentes (Weibull 3P et log-normale) peuvent en donner des valeurs différentes.
- **Données et ressources :** les {{n_unites}} durées de vie, censures comprises.
- **Méthodes :** bootstrap non paramétrique [cite:efron1979], méthode delta, ajustement de la Weibull 3P avec censure.
- **Validation :** stabilité des intervalles selon le nombre de rééchantillonnages ; comparaison des valeurs selon la loi retenue.
- **Bénéfices attendus :** des recommandations de maintenance accompagnées de leur incertitude.
- **Difficultés :** l'estimation du paramètre de position par maximum de vraisemblance est délicate, en particulier sur des échantillons rééchantillonnés.

## Intégration de covariables externes {#sec:p-covariables}

- **Développement :** tenir compte des conditions de vol dans la fiabilité et dans le pronostic.
- **Motivation :** en exploitation réelle, la durée de vie dépend fortement des conditions d'utilisation.
- **Limite actuelle :** FD001 ne comporte qu'une seule condition opératoire ; cette perspective nécessite les sous-ensembles **FD002 et FD004**, qui en comportent six.
- **Données et ressources :** les sous-ensembles FD002 et FD004, plus volumineux, et un temps de calcul accru.
- **Méthodes :** modèle à risques proportionnels de Cox [cite:cox1972], normalisation des capteurs par condition opératoire.
- **Validation :** comparaison des performances avec et sans covariables, sur les jeux de test officiels.
- **Bénéfices attendus :** des modèles transposables à des conditions d'exploitation variées.
- **Difficultés :** la normalisation par condition opératoire et la présence de deux modes de défaillance dans FD004.

## Explicabilité des modèles d'apprentissage {#sec:p-xai}

- **Développement :** expliquer les prédictions du classifieur et du LSTM.
- **Motivation :** une décision de maintenance doit pouvoir être justifiée auprès des équipes techniques et des autorités.
- **Limite actuelle :** le LSTM et le gradient boosting sont des modèles opaques ; seuls les poids de l'indicateur de santé sont interprétables.
- **Données et ressources :** les modèles existants et les données de test.
- **Méthodes :** valeurs de Shapley, méthode SHAP [cite:lundberg2017], et attributions temporelles pour le LSTM.
- **Validation :** cohérence des capteurs les plus influents avec la physique de la dégradation du compresseur haute pression.
- **Bénéfices attendus :** une confiance accrue des utilisateurs et une vérification de l'absence de corrélations parasites.
- **Difficultés :** le coût de calcul des explications sur des séquences et l'interprétation d'attributions corrélées entre capteurs.

## Stratégies de pondération {#sec:p-ponderation}

- **Développement :** améliorer la fusion des capteurs dans l'indicateur de santé et la pondération des deux modèles de RUL.
- **Motivation :** une moyenne simple des deux modèles n'améliore pas le LSTM seul.
- **Limite actuelle :** l'indicateur de santé est une régression linéaire simple, et la combinaison des modèles est une moyenne non pondérée (RMSE {{ens_rmse}} contre {{lstm_rmse}} pour le LSTM seul).
- **Données et ressources :** les moteurs d'entraînement, avec un jeu de validation dédié à l'apprentissage des poids.
- **Méthodes :** sélection par monotonie et pronosticabilité [cite:coble2009], pondération selon l'incertitude, empilement de modèles.
- **Validation :** validation croisée par groupes de moteurs, comme pour la classification.
- **Bénéfices attendus :** un indicateur plus monotone et une combinaison au moins aussi précise que le meilleur modèle.
- **Difficultés :** le risque de sur-apprentissage des poids sur un nombre limité de moteurs.

## Analyses de sensibilité et de robustesse {#sec:p-sensibilite}

- **Développement :** mesurer l'effet des choix de paramètres sur les résultats.
- **Motivation :** plusieurs paramètres sont fixés par convention et non optimisés.
- **Limite actuelle :** le seuil de criticité ({{rul_critique}} cycles), la taille des fenêtres, le plafond du LSTM et les hypothèses de réparation et de coût sont fixés sans étude de sensibilité.
- **Données et ressources :** les données actuelles ; un temps de calcul proportionnel au nombre de configurations testées.
- **Méthodes :** plans d'expériences, variation d'un facteur à la fois, analyse de sensibilité globale.
- **Validation :** stabilité des conclusions (choix de la loi, âge optimal, classement des modèles) selon les paramètres.
- **Bénéfices attendus :** des conclusions dont la robustesse est démontrée.
- **Difficultés :** le nombre de combinaisons croît vite, en particulier si le LSTM doit être réentraîné.

## Benchmarks élargis, apprentissage profond et Transformers {#sec:p-benchmark}

- **Développement :** comparer davantage de familles de modèles : réseaux convolutifs, GRU, Transformers et forêts de survie aléatoires.
- **Motivation :** situer les deux modèles actuels par rapport à l'état de l'art [cite:babu2016,li2018,ramasso2014].
- **Limite actuelle :** seules deux approches sont comparées.
- **Données et ressources :** les quatre sous-ensembles C-MAPSS, et éventuellement un processeur graphique.
- **Méthodes :** réseaux convolutifs temporels, GRU, Transformers [cite:vaswani2017], forêts de survie aléatoires [cite:ishwaran2008], avec un protocole d'évaluation commun.
- **Validation :** mêmes métriques, mêmes moteurs de test et plusieurs graines pour les modèles stochastiques.
- **Bénéfices attendus :** un choix de modèle argumenté par une comparaison équitable.
- **Difficultés :** le coût de calcul, et le risque d'optimiser les modèles sur le jeu de test ; les Transformers ne seront retenus que si leur gain le justifie au regard de leur complexité.

## Passage à des données industrielles réelles {#sec:p-donnees}

- **Développement :** appliquer la chaîne à des données de capteurs réelles.
- **Motivation :** C-MAPSS est une simulation ; les données réelles sont plus bruitées, incomplètes et comportent des maintenances intermédiaires.
- **Limite actuelle :** toutes les données utilisées sont simulées, et les temps de réparation le sont aussi.
- **Données et ressources :** un partenariat industriel, des historiques de capteurs et de maintenance, et un cadre de confidentialité.
- **Méthodes :** nettoyage et synchronisation des données, traitement des valeurs manquantes, prise en compte des maintenances imparfaites.
- **Validation :** comparaison des prédictions avec les défaillances et les déposes réellement constatées.
- **Bénéfices attendus :** une validation de l'approche dans un contexte réel.
- **Difficultés :** l'accès aux données, leur qualité et le faible nombre de défaillances observées.

## Modèles hybrides et apprentissage informé par la physique {#sec:p-hybride}

- **Développement :** combiner un modèle physique de la dégradation et un modèle appris.
- **Motivation :** les modèles purement statistiques n'intègrent pas les lois physiques connues du moteur.
- **Limite actuelle :** les modèles actuels sont entièrement guidés par les données.
- **Données et ressources :** une connaissance des lois de dégradation du compresseur et, idéalement, un modèle thermodynamique simplifié du moteur.
- **Méthodes :** réseaux informés par la physique [cite:raissi2019], modèles hybrides où le réseau corrige un modèle physique.
- **Validation :** précision, mais aussi cohérence physique des prédictions, par exemple la monotonie de la dégradation.
- **Bénéfices attendus :** une meilleure extrapolation avec peu de données et des prédictions physiquement plausibles.
- **Difficultés :** la formulation des contraintes physiques et l'équilibre entre les termes de la fonction de coût.

## Optimisation avancée de la planification de la maintenance {#sec:p-planification}

- **Développement :** passer de la politique d'âge fixe à une planification dynamique fondée sur le RUL prédit.
- **Motivation :** la politique actuelle sacrifie en moyenne {{vie_sacrifiee}} cycles de vie utile par moteur.
- **Limite actuelle :** la politique optimisée est identique pour tous les moteurs et ignore leur état.
- **Données et ressources :** les distributions du RUL, des contraintes opérationnelles (disponibilité des équipes, des pièces et des créneaux).
- **Méthodes :** politiques de remplacement conditionnelles au risque, programmation linéaire en nombres entiers, optimisation sous incertitude.
- **Validation :** simulation de la flotte sur un horizon long, comparaison des coûts et du nombre de défaillances en service.
- **Bénéfices attendus :** une réduction du coût et de la vie sacrifiée par rapport à la politique d'âge fixe.
- **Difficultés :** la nécessité d'intervalles de RUL bien calibrés, d'où le lien avec la [@sec:p-incertitude].

## Jumeau numérique {#sec:p-jumeau}

- **Développement :** intégrer les modèles dans un jumeau numérique de la flotte, mis à jour en continu.
- **Motivation :** suivre l'état de chaque moteur en temps réel et simuler des scénarios de maintenance [cite:tao2019].
- **Limite actuelle :** les modèles sont appliqués hors ligne, sur des fichiers.
- **Données et ressources :** un flux de données en continu et une infrastructure logicielle de déploiement.
- **Méthodes :** mise à jour bayésienne en ligne (déjà compatible avec le modèle de dégradation), architecture orientée événements.
- **Validation :** latence de mise à jour et stabilité des prédictions dans le temps.
- **Bénéfices attendus :** une aide à la décision en temps réel.
- **Difficultés :** l'intégration aux systèmes existants et la maintenance du logiciel.

## Étude économique industrielle complète {#sec:p-economie}

- **Développement :** remplacer les coûts relatifs supposés par des coûts réels.
- **Motivation :** l'âge optimal et le gain dépendent directement du rapport des coûts.
- **Limite actuelle :** le rapport $C_c / C_p$ est une hypothèse d'illustration, et l'immobilisation n'est pas chiffrée.
- **Données et ressources :** des coûts de pièces, de main-d'œuvre et d'immobilisation, auprès d'un exploitant.
- **Méthodes :** modèle de coût complet incluant l'immobilisation, les stocks et les pénalités, analyse de sensibilité aux coûts.
- **Validation :** comparaison avec les coûts historiques d'un exploitant.
- **Bénéfices attendus :** une recommandation économiquement justifiée.
- **Difficultés :** la confidentialité et la variabilité des coûts.

## Déploiement et validation en environnement industriel {#sec:p-deploiement}

- **Développement :** déployer le tableau de bord et l'API auprès d'utilisateurs réels.
- **Motivation :** vérifier l'utilité de l'outil dans le processus de décision.
- **Limite actuelle :** l'application fonctionne en local, avec des données figées.
- **Données et ressources :** un serveur, une authentification des utilisateurs et une connexion aux données réelles.
- **Méthodes :** conteneurisation, intégration continue s'appuyant sur la suite de tests existante, surveillance de la dérive des données.
- **Validation :** retours des utilisateurs et indicateurs de maintenance avant et après le déploiement.
- **Bénéfices attendus :** un outil réellement utilisé pour la maintenance.
- **Difficultés :** la sécurité, la fiabilité du service et la conduite du changement.

## Conclusion {-}

Ces perspectives vont des plus directes, qui s'appuient sur les données actuelles, aux plus ambitieuses, qui demandent des données industrielles ou un déploiement réel. Les premières alimenteront la Version 2 du rapport, en fonction des remarques de l'encadrant.
