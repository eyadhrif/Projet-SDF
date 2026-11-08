# Résultats {#sec:resultats}

Tous les chiffres de ce chapitre proviennent des fichiers de résultats produits par `run_all.py` ; les figures et les tableaux sont générés à partir de ces fichiers.

## Fiabilité {#sec:res-fiabilite}

### Estimation non paramétrique

La courbe de Kaplan-Meier ([@fig:fiabilite_kaplan_meier]) vaut un jusqu'à la première défaillance, puis décroît rapidement. La médiane de survie est de {{mediane_km}} cycles et l'aire sous la courbe de {{mttf_km}} cycles. Les censures (moteurs de test) se concentrent aux faibles âges, où presque toute la population est encore à risque ; elles élargissent peu l'intervalle de confiance, qui ne s'ouvre vraiment qu'aux grands âges, quand peu de moteurs restent à risque.

!figure[fiabilite_kaplan_meier](Fonction de fiabilité : estimateur de Kaplan-Meier avec son intervalle de confiance et les censures, comparé à la loi de Weibull 3P retenue et à la loi de Weibull 2P (MV) rejetée.)

Le taux de défaillance estimé par Nelson-Aalen ([@fig:fiabilite_taux_defaillance]) est nul jusqu'à l'âge de la première défaillance, puis croît : c'est la signature d'une **usure**. Ses oscillations aux grands âges reflètent le faible nombre de moteurs encore à risque et non un phénomène physique.

!figure[fiabilite_taux_defaillance](Taux de défaillance : estimation non paramétrique de Nelson-Aalen lissée par noyau et taux de la loi de Weibull 3P.)

### Choix de la loi

Le [@tab:fiabilite_modeles] et le [@tab:fiabilite_adequation] résument les ajustements. Le diagramme de Weibull ([@fig:fiabilite_diagramme_weibull]) est nettement **courbé** : les points s'écartent de la droite aux deux extrémités et le coefficient de détermination ne vaut que {{mco_r2}}. La pente donne $\beta = {{mco_beta}}$ par MCO. L'estimation par MV de la loi de Weibull 2P sur les défaillances donne $\beta = {{mv_beta}}$, mais elle est **rejetée** par le test de Kolmogorov-Smirnov ($p = {{mv_ks_p}}$). Avec la censure, l'estimation sur les {{n_unites}} unités donne $\beta = {{mvc_beta}}$ (intervalle de confiance $[{{mvc_beta_lo}} ; {{mvc_beta_hi}}]$) et $\eta = {{mvc_eta}}$ cycles : l'échelle est plus grande, car les moteurs censurés apportent l'information qu'ils ont survécu au moins jusqu'à leur dernier cycle observé.

!figure[fiabilite_diagramme_weibull](Diagramme de Weibull (rangs médians de Bernard) et droite des moindres carrés : la courbure révèle un paramètre de position non nul.){largeur=55}

!tableau[fiabilite_modeles]

!tableau[fiabilite_adequation]

La loi exponentielle est rejetée sans ambiguïté ($p = {{exp_ks_p}}$, AIC {{aic_exp}}), ce qui exclut un taux de défaillance constant. Les lois de Weibull 3P (AIC {{aic_w3}}, $p = {{w3_ks_p}}$) et log-normale (AIC {{aic_ln}}, $p = {{ln_ks_p}}$) sont toutes deux acceptées, avec une différence d'AIC de {{delta_aic}} seulement : elles sont **statistiquement équivalentes**, et toutes deux bien meilleures que la loi de Weibull 2P (AIC {{aic_w2}}). La loi de **Weibull 3P est retenue** pour trois raisons :

1. son paramètre de position $\gamma = {{w3_gamma}}$ cycles a une interprétation physique directe, la durée de fonctionnement sans défaillance garantie, cohérente avec la première défaillance observée à {{t_min_obs}} cycles ;
2. son paramètre de forme $\beta = {{w3_beta}} > 1$ traduit un taux de défaillance croissant, conforme à l'estimation non paramétrique ;
3. elle est la loi de référence du cours et de la fiabilité mécanique [cite:benhmida,weibull1951].

### Indicateurs de fiabilité

Le [@tab:fiabilite_indicateurs] donne les indicateurs du modèle retenu : MTTF de {{mttf}} cycles, $B_1 = {{b1}}$, $B_{10} = {{b10}}$ et $B_{50} = {{b50}}$ cycles. La durée $B_{50}$ est proche de la médiane de Kaplan-Meier ({{mediane_km}} cycles), ce qui confirme l'accord entre les deux approches au centre de la distribution. La densité et la fonction de répartition ([@fig:fiabilite_densite_repartition]) montrent une distribution concentrée entre la fin de la période sans défaillance et les âges de l'ordre de trois cents cycles.

!tableau[fiabilite_indicateurs]

!figure[fiabilite_densite_repartition](Densité de défaillance et fonction de répartition de la loi de Weibull 3P, avec les durées B10 et B50.)

La fiabilité conditionnelle ([@fig:fiabilite_conditionnelle]) vaut un tant que l'âge augmenté de l'horizon reste dans la période sans défaillance, puis décroît : un moteur âgé a une probabilité de plus en plus faible de franchir les {{horizon_conditionnel}} cycles suivants. Ce résultat justifie directement une politique de remplacement liée à l'âge.

!figure[fiabilite_conditionnelle](Fiabilité conditionnelle : probabilité qu'un moteur ayant atteint l'âge t fonctionne encore pendant l'horizon suivant (ligne pointillée : niveau $0{,}9$).){largeur=55}

## Maintenabilité, disponibilité et politique préventive {#sec:res-fmds02}

Ces résultats reposent sur les temps de réparation simulés ([@sec:fmds02]). La loi log-normale ré-estimée sur l'échantillon a pour paramètres $\mu = {{ttr_mu}}$ et $\sigma = {{ttr_sigma}}$ ; le test de Kolmogorov-Smirnov l'accepte ($p = {{ttr_ks_p}}$). L'écart-type estimé est inférieur à la valeur utilisée pour la simulation ({{ttr_sigma_sim}}) : c'est l'effet de la fluctuation d'échantillonnage sur un échantillon de cette taille. Le MTTR vaut {{mttr_h}} h, soit {{mttr_cycles}} cycles, et $90\,\%$ des réparations sont terminées en {{t90_h}} h ([@fig:fmds_maintenabilite]).

!figure[fmds_maintenabilite](Temps de réparation simulés (gauche) et fonction de maintenabilité de la loi log-normale estimée, avec le MTTR et la durée t90 (droite).)

Le [@tab:fmds_maintenabilite_disponibilite] regroupe les indicateurs. La disponibilité intrinsèque vaut **{{dispo}} %**, soit environ {{indispo_h}} h d'indisponibilité pour mille heures. Selon le modèle markovien ([@fig:fmds_disponibilite]), la disponibilité instantanée part de un et converge vers cette valeur en quelques dizaines de cycles.

!tableau[fmds_maintenabilite_disponibilite]

!figure[fmds_disponibilite](Disponibilité instantanée A(t) selon le modèle markovien à deux états et sa limite asymptotique.){largeur=55}

La politique de remplacement préventif ([@fig:fmds_remplacement_preventif]) présente un optimum net à $T^* = {{t_opt}}$ cycles, juste après la fin de la période sans défaillance. À cet âge, la fiabilité vaut encore {{r_t_opt}} : presque aucun moteur ne défaille en service. Le coût par cycle passe de {{cout_rtf}} (maintenance corrective seule) à {{cout_opt}}, soit une **réduction de {{gain_preventif}} %**. Le prix de ce gain est élevé : chaque moteur est remplacé en moyenne {{vie_sacrifiee}} cycles avant son MTTF.

!figure[fmds_remplacement_preventif](Coût moyen par cycle de la politique de remplacement à âge fixe en fonction de l'âge T, comparé au coût de la maintenance corrective seule.)

## Indicateur de santé et détection de l'état critique {#sec:res-sante}

### Sélection des capteurs et indicateur de santé

Parmi les capteurs non constants, {{n_retenus}} présentent une tendance supérieure en valeur absolue au seuil de {{seuil_tendance}} et sont retenus : {{capteurs_retenus}} ([@fig:sante_selection_capteurs]). Les capteurs s9 et s14, des vitesses de rotation du corps du moteur, ont une tendance plus faible et sont écartés.

!figure[sante_selection_capteurs](Tendance des capteurs non constants : corrélation moyenne avec le numéro de cycle ; les capteurs retenus dépassent le seuil en valeur absolue.){largeur=55}

L'indicateur de santé ([@fig:sante_indicateur]) part d'environ un en début de vie et décroît jusqu'au voisinage de zéro à la défaillance, pour tous les moteurs, avec des durées de vie très différentes. Le seuil de défaillance appris par le modèle de dégradation vaut {{seuil_hi}}. Les poids de la combinaison linéaire ([@fig:sante_poids_hi]) sont de signes opposés selon le sens de dérive des capteurs ; les plus forts portent sur la pression statique en sortie du compresseur haute pression (s11) et sur la température en sortie de la turbine basse pression (s4).

!figure[sante_indicateur](Indicateur de santé lissé de dix moteurs d'entraînement et seuil de défaillance.)

!figure[sante_poids_hi](Poids des capteurs standardisés dans l'indicateur de santé.){largeur=55}

### Classification normal / critique

Le [@tab:sante_classifieurs] présente les performances. Les deux classifieurs séparent très bien les deux classes : en validation croisée par groupes de moteurs, l'AUC vaut {{gb_auc_cv}} pour le gradient boosting et {{svm_auc_cv}} pour le SVM ; sur le jeu de test, {{gb_auc}} et {{svm_auc}} ([@fig:sante_roc]). Le **gradient boosting** est retenu.

!tableau[sante_classifieurs]

!figure[sante_roc](Courbes ROC des deux classifieurs sur le jeu de test.){largeur=55}

Au seuil de décision par défaut, le rappel de test est cependant nettement plus faible qu'en validation croisée ({{gb_rappel}} contre {{gb_rappel_cv}}). La matrice de confusion ([@fig:sante_matrice_confusion]) montre que, sur les {{n_critiques_test}} cycles critiques du jeu de test, {{cm_tp}} sont détectés et {{cm_fn}} manqués, pour {{cm_fp}} fausses alertes parmi {{cm_tn}} cycles normaux correctement classés. Le jeu de test est très déséquilibré : la plupart des séries s'arrêtent bien avant la défaillance, et seuls les derniers cycles de quelques moteurs sont critiques. L'AUC élevée montre que le classement des probabilités reste bon ; c'est le **seuil** de décision qui est trop strict pour cet usage ([@sec:limites]).

!figure[sante_matrice_confusion](Matrice de confusion du gradient boosting sur le jeu de test, au seuil de décision par défaut.){largeur=50}

Au dernier cycle observé, la flotte de test se répartit en {{etat_normal}} moteurs normaux, {{etat_surveillance}} en surveillance et {{etat_critique}} critiques.

## Durée de vie résiduelle {#sec:res-rul}

### Performances des deux modèles

Le [@tab:rul_metriques] compare les modèles sur les {{n_moteurs_test}} moteurs de test. Le **LSTM est le plus précis** sur toutes les métriques : RMSE de {{lstm_rmse}} cycles contre {{deg_rmse}}, MAE de {{lstm_mae}} contre {{deg_mae}}, et score NASA de {{lstm_score}} contre {{deg_score}}. Son biais est faible ({{lstm_biais}} cycles), alors que le modèle de dégradation prédit en moyenne trop tard ({{deg_biais}} cycles, {{deg_tardif}} % de prédictions tardives). Le score NASA, qui pénalise fortement les retards, amplifie cet écart. La moyenne des deux prédictions (RMSE {{ens_rmse}}) n'améliore pas le LSTM seul : le biais du modèle de dégradation l'emporte sur le gain de la combinaison.

!tableau[rul_metriques]

La [@fig:rul_predit_vs_reel] montre les prédictions en fonction du RUL réel. Les prédictions du LSTM suivent la diagonale jusqu'au plafond de {{rul_cap}} cycles, au-delà duquel il ne peut pas prédire ; celles du modèle de dégradation sont plus dispersées et majoritairement au-dessus de la diagonale. La distribution des erreurs ([@fig:rul_erreurs]) confirme le décalage du modèle de dégradation vers les prédictions tardives.

!figure[rul_predit_vs_reel](RUL prédit en fonction du RUL réel pour les deux modèles ; la diagonale correspond à une prédiction parfaite.)

!figure[rul_erreurs](Distribution des erreurs de prédiction ; une erreur positive est une prédiction tardive.)

La [@fig:rul_flotte] présente les prédictions pour l'ensemble de la flotte, triée par RUL réel croissant. Pour les moteurs proches de la défaillance, les deux modèles sont précis et les intervalles du modèle de dégradation sont étroits ; pour les moteurs encore jeunes, l'incertitude augmente fortement.

!figure[rul_flotte](Prédictions des deux modèles pour les moteurs de test triés par RUL réel, avec l'intervalle P10–P90 du modèle de dégradation.)

### Calibration du modèle de dégradation

Le [@tab:rul_calibration] et la [@fig:rul_calibration] évaluent les intervalles de prédiction. À tous les niveaux, la couverture observée est inférieure au niveau nominal : {{couverture_50}} % pour l'intervalle P25–P75, {{couverture_80}} % pour P10–P90 et {{couverture_90}} % pour P05–P95. **Les intervalles sont trop étroits**, c'est-à-dire que le modèle sous-estime son incertitude.

!tableau[rul_calibration]

!figure[rul_calibration](Calibration des intervalles du modèle de dégradation : couverture observée en fonction du niveau nominal.){largeur=55}

Le [@tab:rul_biais_tranches] détaille le biais selon le RUL réel. Le biais est positif dans toutes les tranches, avec un maximum de {{biais_t2}} cycles dans la tranche intermédiaire. Pour les moteurs dont le RUL réel est le plus grand, le biais est plus faible ({{biais_t3}}) et la couverture meilleure ({{couv_t3}} %), car les intervalles y sont beaucoup plus larges. Le biais médian vaut {{biais_median}} cycles. À titre de diagnostic seulement, l'écart-type des erreurs vaut {{rmse_hors_biais}} cycles : c'est l'erreur qui resterait si le biais moyen était retiré. Ce n'est pas une performance atteignable, car le biais est mesuré sur le jeu de test lui-même.

!tableau[rul_biais_tranches]

### Apprentissage du LSTM et exemple d'un moteur

L'apprentissage du LSTM ([@fig:rul_apprentissage_lstm]) s'arrête au bout de {{lstm_epoques}} époques ; l'arrêt précoce conserve les poids de la meilleure époque (RMSE de validation {{lstm_val_rmse}} cycles, sur la cible plafonnée). Les erreurs d'entraînement et de validation restent proches, sans signe de sur-apprentissage marqué.

!figure[rul_apprentissage_lstm](Courbes d'apprentissage du LSTM : RMSE d'entraînement et de validation par époque.){largeur=55}

La [@fig:rul_exemple_moteur] illustre le fonctionnement des deux modèles sur le moteur de test n° {{moteur_exemple}}, observé pendant {{ex_cycles}} cycles et dont le RUL réel au dernier cycle est de {{ex_rul_reel}} cycles. Au fil des cycles, les deux prédictions se rapprochent du RUL réel. Au dernier cycle, le modèle de dégradation prédit {{ex_deg}} cycles (intervalle P10–P90 de {{ex_deg_p10}} à {{ex_deg_p90}}) et le LSTM {{ex_lstm}} cycles. La projection de l'indicateur de santé montre comment le modèle bayésien déduit le RUL du franchissement du seuil.

!figure[rul_exemple_moteur](Moteur de test pris en exemple : RUL prédit à chaque cycle par les deux modèles (gauche) et projection de l'indicateur de santé jusqu'au seuil de défaillance (droite).)

## Comparaison des méthodes {#sec:comparaison}

Les deux approches de RUL sont complémentaires :

- le **LSTM** est nettement plus précis et quasiment sans biais, ce qui est du même ordre que les réseaux récurrents publiés sur FD001 [cite:zheng2017,ramasso2014]. En revanche, il ne fournit pas d'incertitude, ne peut pas dépasser son plafond et reste peu interprétable ;
- le **modèle de dégradation** est moins précis et biaisé vers les prédictions tardives, mais chacune de ses étapes est interprétable (trajectoire de l'indicateur de santé, seuil, loi a priori de flotte), et il fournit une distribution du RUL, même mal calibrée à ce stade.

Du côté de la fiabilité, l'approche non paramétrique (Kaplan-Meier, Nelson-Aalen) et l'approche paramétrique (Weibull 3P) concordent sur la forme du taux de défaillance et sur la médiane, ce qui renforce la confiance dans le modèle retenu.
