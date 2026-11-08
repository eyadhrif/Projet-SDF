# Discussion et perspectives {#sec:discussion}

## Introduction {-}

Ce chapitre interprète les résultats dans le contexte industriel, en présente les limites, puis propose les travaux futurs prioritaires.

## Interprétation industrielle {#sec:interpretation}

**Une flotte qui s'use.** Le paramètre de forme supérieur à un et le taux croissant signent des défaillances d'usure, conformes à la dégradation simulée du HPC : remplacer un moteur âgé réduit réellement le risque.

**Une période sans défaillance.** Le paramètre $\gamma$ permet d'alléger les inspections en début de vie et de concentrer la surveillance au-delà de cet âge.

**Le préventif et ses limites.** Le remplacement à $T^*$ réduit fortement le coût par cycle sous l'hypothèse de coûts retenue, mais il remplace aussi les moteurs robustes et sacrifie en moyenne {{vie_sacrifiee}} cycles de vie utile.

**L'apport du prédictif.** Le HI, la détection de l'état critique et la RUL permettent de décider moteur par moteur : le classifieur peut servir d'alarme et le modèle de RUL de planification, le LSTM apportant la précision et le modèle bayésien l'explication et l'incertitude.

## Limites {#sec:limites}

- **Hypothèses simulées.** Les temps de réparation, la conversion d'un cycle en {{h_par_cycle}} h et le rapport de coûts sont supposés : la maintenabilité, la disponibilité et le coût illustrent la démarche, sans valeur industrielle.
- **Un seul sous-ensemble.** FD001 n'a qu'une condition opératoire et un mode de défaillance ; les conclusions ne s'étendent pas telles quelles à FD002–FD004.
- **Weibull 3P ajustée sans censure.** L'aire sous la courbe KM ({{mttf_km}} cycles) dépasse le MTTF du modèle ({{mttf}} cycles) : le modèle sous-estime probablement un peu les durées de vie.
- **Biais et sous-couverture du modèle de dégradation.** La base polynomiale extrapole mal une dégradation qui s'accélère, le bruit n'est pas propagé et le seuil est estimé sur des valeurs ajustées ; ce modèle ne doit pas décider seul.
- **Seuil du classifieur.** Le rappel de test est faible au seuil par défaut ; ce seuil devrait refléter le coût relatif d'une défaillance manquée et d'une fausse alerte.
- **Évaluation ponctuelle de la RUL.** Seul le dernier cycle de chaque moteur de test est évalué ; le suivi au fil de la vie n'est illustré que sur un exemple.

## Travaux futurs {#sec:travaux-futurs}

Cinq travaux futurs sont prioritaires ; aucun n'est réalisé à ce stade.

- **Modèle de dégradation exponentiel ou de Wiener.** Remplacer la base polynomiale par un modèle exponentiel à coefficients aléatoires ou un processus de Wiener à dérive non linéaire [cite:gebraeel2005,si2012] devrait réduire le biais tardif, en comparant RMSE, biais et score NASA sur les mêmes moteurs.
- **Intervalles calibrés.** Propager le bruit de mesure dans les trajectoires puis recalibrer les intervalles sur des moteurs réservés, par exemple par prédiction conforme, viserait une couverture proche du niveau nominal.
- **Weibull 3P avec censure et incertitude des $B_p$.** Ajuster la loi retenue par MV avec censure et donner des IC de $B_{10}$ et $B_{50}$ par bootstrap [cite:efron1979] lèverait la limite principale de l'analyse de fiabilité.
- **Conditions opératoires multiples.** Étendre l'étude à FD002 et FD004, avec une normalisation par condition et un modèle de Cox [cite:cox1972], rendrait les modèles transposables à des usages variés.
- **Données et coûts réels.** Remplacer les hypothèses simulées par des temps de réparation et des coûts réels permettrait une véritable étude économique du préventif et du prédictif.

## Conclusion {-}

Les résultats confirment l'intérêt de combiner une vision de flotte, par les indices FMDS, et une décision moteur par moteur, par le pronostic. Les limites identifiées, surtout la calibration du modèle de dégradation et le caractère simulé de certaines hypothèses, fixent les travaux futurs.
