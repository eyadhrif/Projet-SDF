# Discussion {#sec:discussion}

## Introduction {-}

Ce chapitre interprète les résultats dans le contexte industriel, puis présente les limites actuelles de l'étude.

## Interprétation industrielle {#sec:interpretation}

**Une flotte qui s'use.** Le paramètre de forme supérieur à un et le taux de défaillance croissant indiquent que les défaillances de FD001 sont des défaillances d'**usure**, ce qui est conforme au mécanisme simulé (dégradation progressive du compresseur haute pression). Dans ce cas, la maintenance préventive a un sens : remplacer un moteur âgé réduit réellement le risque, ce qui ne serait pas vrai avec un taux constant.

**Une période sans défaillance.** Le paramètre de position $\gamma$ correspond à une durée pendant laquelle aucun moteur ne défaille. En exploitation, cette période peut servir à espacer les inspections lourdes en début de vie et à concentrer l'effort de surveillance au-delà de cet âge.

**L'intérêt et la limite du préventif à âge fixe.** La politique optimale remplace chaque moteur peu après la fin de la période sans défaillance, ce qui divise le coût par cycle d'un facteur important selon l'hypothèse de coûts retenue. Mais elle traite tous les moteurs de la même façon : elle remplace aussi les moteurs les plus robustes, et sacrifie en moyenne {{vie_sacrifiee}} cycles de vie utile par moteur.

**L'apport du prédictif.** C'est précisément ce que la maintenance prédictive peut améliorer : l'indicateur de santé, la détection de l'état critique et l'estimation du RUL permettent de décider moteur par moteur, de remplacer tôt les moteurs dégradés et d'exploiter plus longtemps les autres. Le LSTM fournit la prédiction la plus précise ; le modèle de dégradation fournit une explication et une incertitude, à condition d'en corriger la calibration. Dans une chaîne de décision, le classifieur peut jouer le rôle d'alarme et le modèle de RUL celui de planification.

## Limites actuelles {#sec:limites}

Les limites suivantes sont connues et assumées dans cette Version 1 :

1. **Temps de réparation simulés.** Les résultats de maintenabilité, de disponibilité et de coût reposent sur une loi de réparation, une conversion cycle–heure et un rapport de coûts **supposés**. Ils illustrent la démarche du cours mais ne doivent pas être lus comme des valeurs industrielles.
2. **Un seul sous-ensemble, FD001.** Une seule condition opératoire et un seul mode de défaillance : les conclusions ne s'étendent pas telles quelles aux sous-ensembles plus complexes (FD002 à FD004), où les conditions de vol modifient fortement les capteurs.
3. **Loi retenue ajustée sur les seules défaillances.** La comparaison des lois et l'ajustement de la Weibull 3P utilisent les {{n_defaillances}} durées de défaillance, sans les moteurs censurés. Kaplan-Meier, qui les inclut, donne une aire sous la courbe ({{mttf_km}} cycles) supérieure au MTTF du modèle ({{mttf}} cycles) : le modèle retenu sous-estime probablement un peu les durées de vie. Une estimation de la Weibull 3P par maximum de vraisemblance avec censure lèverait cette limite.
4. **Modèle markovien de disponibilité.** Il suppose des taux constants, alors que la loi retenue a un taux croissant : la courbe $A(t)$ est une approximation, seule sa limite est exacte.
5. **Biais et sous-couverture du modèle de dégradation.** Le modèle prédit en moyenne trop tard ({{deg_biais}} cycles) et ses intervalles sont trop étroits ({{couverture_80}} % de couverture pour l'intervalle P10–P90). Plusieurs causes sont identifiées : (*a*) la base polynomiale de degré {{deg_degre}} extrapole mal une dégradation qui s'accélère en fin de vie ; (*b*) le bruit de mesure n'est pas propagé dans les trajectoires simulées, seule l'incertitude des coefficients et du seuil l'est ; (*c*) le seuil est estimé sur les valeurs ajustées et non sur les mesures. Une prédiction tardive est la plus dangereuse en maintenance : ce modèle ne doit pas être utilisé seul pour décider.
6. **Seuil de décision du classifieur.** Le rappel de test est faible au seuil par défaut, sur un jeu très déséquilibré. Le seuil devrait être choisi selon le coût relatif d'une défaillance manquée et d'une fausse alerte.
7. **Plafond et reproductibilité du LSTM.** Le LSTM ne peut pas prédire au-delà de son plafond, et son réentraînement varie légèrement selon la machine ; les résultats publiés correspondent au modèle sauvegardé.
8. **Évaluation sur un seul instant par moteur.** Le RUL n'est évalué qu'au dernier cycle observé de chaque moteur de test, comme dans le challenge PHM ; la qualité des prédictions au fil de la vie n'est illustrée que sur un exemple.

## Conclusion {-}

Les résultats confirment l'intérêt d'une approche qui combine une vision de flotte, avec les indices FMDS, et une décision moteur par moteur, avec le pronostic. Les limites identifiées, en particulier la calibration du modèle de dégradation et le caractère simulé des données, orientent les perspectives présentées au chapitre suivant.
