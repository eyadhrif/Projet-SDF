# Évaluation et visualisation {#sec:evaluation}

## Introduction {-}

Ce chapitre évalue d'abord la solution : protocole et métriques, puis résultats de fiabilité, de disponibilité, de détection de l'état critique et de RUL, et comparaison des méthodes. Il montre ensuite comment ces résultats sont restitués dans le tableau de bord et comment leur reproductibilité est assurée.

## Protocole et métriques {#sec:protocole}

Le découpage officiel de FD001 est respecté : les modèles sont appris sur les {{n_moteurs_train}} moteurs d'entraînement et évalués sur les {{n_moteurs_test}} moteurs de test. La fiabilité porte sur les {{n_unites}} unités avec censure ; la classification est validée par GroupKFold puis évaluée sur tous les cycles de test ; la RUL est évaluée au dernier cycle observé de chaque moteur, comme dans le challenge PHM [cite:saxena2008damage].

Pour la classification, la classe positive est l'état critique. Le **rappel** est la métrique prioritaire, car une défaillance manquée coûte bien plus qu'une inspection inutile ; l'AUC [cite:hanley1982] mesure la qualité du classement indépendamment du seuil. Pour la RUL, l'erreur d'un moteur est $e_i = \widehat{\mathrm{RUL}}_i - \mathrm{RUL}_i$ ; une erreur positive est une prédiction **tardive**, la plus dangereuse. Sur $N$ moteurs :

$$\mathrm{RMSE} = \sqrt{\frac1N \sum_i e_i^2}, \qquad \mathrm{MAE} = \frac1N \sum_i |e_i|, \qquad S = \sum_i \begin{cases} e^{-e_i/13} - 1 & e_i < 0 \\ e^{e_i/10} - 1 & e_i \ge 0 \end{cases}, $$ {#eq:rmse}

où $S$ est le score NASA [cite:saxena2008damage]. La **couverture** d'un intervalle de prédiction est la proportion de moteurs dont la RUL réelle y tombe ; elle doit être proche du niveau nominal.

## Fiabilité {#sec:res-fiabilite}

La [@fig:fiabilite_kaplan_meier] compare l'estimateur KM aux lois ajustées ; la médiane de survie vaut {{mediane_km}} cycles. Les censures, concentrées aux faibles âges, élargissent peu l'IC. Le taux de Nelson-Aalen, nul avant la première défaillance puis croissant, confirme une **usure**.

!figure[fiabilite_kaplan_meier](Fonction de fiabilité : estimateur KM avec son IC et les censures, loi de Weibull 3P retenue et loi de Weibull 2P (MV) rejetée.)

Le diagramme de Weibull ([@fig:fiabilite_diagramme_weibull]) est nettement courbé ($R^2 = {{mco_r2}}$, $\beta = {{mco_beta}}$ par MCO), ce qui révèle un paramètre de position non nul.

!figure[fiabilite_diagramme_weibull](Diagramme de Weibull (rangs de Bernard) et droite des MCO : la courbure révèle un paramètre de position non nul.){largeur=55}

Le [@tab:fiabilite_adequation] compare les quatre lois candidates.

!tableau[fiabilite_adequation]

La loi exponentielle et la Weibull 2P (MV, $\beta = {{mv_beta}}$, $p = {{mv_ks_p}}$) sont rejetées. La Weibull 3P et la log-normale sont acceptées et équivalentes ($\Delta\mathrm{AIC} = {{delta_aic}}$). La **Weibull 3P est retenue** : $\gamma = {{w3_gamma}}$ cycles traduit une période sans défaillance cohérente avec la première défaillance à {{t_min_obs}} cycles, $\beta = {{w3_beta}} > 1$ un taux croissant, et c'est la loi de référence du cours [cite:benhmida]. L'ajustement 2P avec censure donne une échelle plus grande ($\eta = {{mvc_eta}}$ cycles), car les moteurs censurés ont survécu au moins jusqu'à leur dernier cycle. Le [@tab:fiabilite_indicateurs] donne les indicateurs du modèle retenu.

!tableau[fiabilite_indicateurs]

$B_{50}$ est proche de la médiane KM, ce qui confirme l'accord des deux approches au centre de la distribution. La [@fig:fiabilite_densite_repartition] situe $B_{10}$ et $B_{50}$ sur la densité et la fonction de répartition.

!figure[fiabilite_densite_repartition](Densité de défaillance et fonction de répartition de la loi de Weibull 3P, avec les durées B10 et B50.)

## Disponibilité et remplacement préventif {#sec:res-fmds02}

Le [@tab:fmds_maintenabilite_disponibilite] regroupe les indicateurs obtenus avec les temps de réparation simulés.

!tableau[fmds_maintenabilite_disponibilite]

La loi log-normale ré-estimée est acceptée par le test KS ($p = {{ttr_ks_p}}$). La disponibilité intrinsèque atteint **{{dispo}} %**, soit environ {{indispo_h}} h d'indisponibilité pour mille heures. La [@fig:fmds_remplacement_preventif] montre le coût du remplacement préventif en fonction de l'âge.

!figure[fmds_remplacement_preventif](Coût moyen par cycle du remplacement à âge fixe en fonction de l'âge T, comparé à la maintenance corrective seule.)

L'optimum, net, se situe à $T^* = {{t_opt}}$ cycles, juste après la période sans défaillance : le coût par cycle baisse de **{{gain_preventif}} %**, au prix d'un remplacement en moyenne {{vie_sacrifiee}} cycles avant le MTTF.

## Détection de l'état critique {#sec:res-sante}

Parmi les capteurs non constants, {{n_retenus}} dépassent le seuil de tendance et sont retenus : {{capteurs_retenus}}. La [@fig:sante_indicateur] montre le HI obtenu.

!figure[sante_indicateur](HI lissé de dix moteurs d'entraînement et seuil de défaillance.)

Le HI part d'environ un et décroît jusqu'au voisinage de zéro pour tous les moteurs, quelle que soit leur durée de vie. Le [@tab:sante_classifieurs] compare les deux classifieurs.

!tableau[sante_classifieurs]

Les deux modèles séparent très bien les classes ; le **gradient boosting**, de meilleure AUC sur le test ({{gb_auc}}), est retenu. Son rappel de test ({{gb_rappel}}) est pourtant inférieur à celui de la validation croisée ({{gb_rappel_cv}}), comme le détaille la [@fig:sante_matrice_confusion].

!figure[sante_matrice_confusion](Matrice de confusion du gradient boosting sur le jeu de test, au seuil de décision par défaut.){largeur=50}

Le jeu de test est très déséquilibré : la plupart des séries s'arrêtent bien avant la défaillance. L'AUC reste élevée, c'est donc le seuil de décision qui est trop strict. Au dernier cycle, la flotte compte {{etat_normal}} moteurs normaux, {{etat_surveillance}} en surveillance et {{etat_critique}} critiques.

## Durée de vie résiduelle {#sec:res-rul}

Le [@tab:rul_metriques] compare les deux modèles sur les {{n_moteurs_test}} moteurs de test.

!tableau[rul_metriques]

Le **LSTM est le plus précis** sur toutes les métriques et presque sans biais. Le modèle de dégradation prédit en moyenne trop tard ({{deg_biais}} cycles), ce que le score NASA amplifie. La moyenne des deux n'améliore pas le LSTM seul. La [@fig:rul_predit_vs_reel] montre les prédictions en fonction de la RUL réelle.

!figure[rul_predit_vs_reel](RUL prédite en fonction de la RUL réelle pour les deux modèles ; la diagonale correspond à une prédiction parfaite.)

Le LSTM suit la diagonale jusqu'à son plafond de {{rul_cap}} cycles ; le modèle de dégradation est plus dispersé et majoritairement au-dessus. La [@fig:rul_calibration] évalue ses intervalles de prédiction.

!figure[rul_calibration](Calibration des intervalles du modèle de dégradation : couverture observée en fonction du niveau nominal.){largeur=55}

Les couvertures observées, {{couverture_50}} %, {{couverture_80}} % et {{couverture_90}} % pour des niveaux nominaux de 50, 80 et 90 %, sont toutes trop faibles : **les intervalles sont trop étroits** et le modèle sous-estime son incertitude. La [@fig:rul_exemple_moteur] illustre les deux modèles sur le moteur de test n° {{moteur_exemple}}.

!figure[rul_exemple_moteur](Moteur de test pris en exemple : RUL prédite à chaque cycle par les deux modèles (gauche) et projection du HI jusqu'au seuil de défaillance (droite).)

Au fil des cycles, les deux prédictions se rapprochent de la RUL réelle ({{ex_rul_reel}} cycles) ; la projection du HI montre comment le modèle bayésien déduit la RUL du franchissement du seuil.

## Comparaison des méthodes {#sec:comparaison}

Les deux approches de RUL sont complémentaires. Le **LSTM** est précis et quasi sans biais, du même ordre que les réseaux récurrents publiés sur FD001 [cite:zheng2017,ramasso2014], mais il ne fournit pas d'incertitude et reste peu interprétable. Le **modèle de dégradation** est moins précis et biaisé, mais chaque étape est interprétable et il fournit une distribution de la RUL, encore mal calibrée. En fiabilité, les approches non paramétrique et paramétrique concordent sur la forme du taux et sur la médiane.

## Visualisation : le tableau de bord {#sec:dashboard}

Les résultats évalués sont restitués dans un tableau de bord web React, alimenté par une API qui sert les fichiers de résultats ; une version autonome en un seul fichier HTML s'ouvre sans serveur. La page de vue d'ensemble ([@fig:dashboard_overview]) réunit les indicateurs clés et l'état de la flotte.

!figure[dashboard_overview](Page de vue d'ensemble : indicateurs clés, distribution des durées de vie, état de la flotte et priorités d'intervention.)

La page consacrée à la RUL ([@fig:dashboard_rul]) compare les deux modèles et détaille les prédictions pour chaque moteur.

!figure[dashboard_rul](Page de la durée de vie résiduelle : métriques des deux modèles, prédictions et erreurs.)

## Reproductibilité {#sec:reproductibilite}

Toutes les étapes aléatoires utilisent des graines fixées, et chaque exécution enregistre les versions des bibliothèques (Python {{python}}, scikit-learn {{v_sklearn}}, PyTorch {{v_torch}}). Le réentraînement du LSTM variant légèrement d'une machine à l'autre, les résultats publiés correspondent au modèle sauvegardé. Une suite de tests automatiques vérifie les méthodes, l'absence de fuite entre moteurs et la concordance de chaque nombre du rapport avec sa source.

## Conclusion {-}

La Weibull 3P décrit la fiabilité de la flotte avec un MTTF de {{mttf}} cycles, le classifieur atteint une AUC de {{gb_auc}}, et le LSTM est le plus précis pour la RUL (RMSE de {{lstm_rmse}} cycles), tandis que le modèle de dégradation fournit des intervalles encore trop étroits. Le chapitre suivant discute ces résultats.
