# Conclusion générale {-}

Ce projet a appliqué l'ensemble de la démarche de sûreté de fonctionnement à une flotte de turboréacteurs simulés, des données brutes jusqu'à un outil d'aide à la décision.

L'analyse de fiabilité, menée en tenant compte des {{n_censures}} moteurs censurés, montre une flotte soumise à l'usure, avec une période sans défaillance. La loi de Weibull à trois paramètres, acceptée par le test KS et équivalente à la log-normale selon l'AIC, donne un MTTF de {{mttf}} cycles et des durées $B_{10}$ et $B_{50}$ de {{b10}} et {{b50}} cycles. Sous des hypothèses de réparation et de coût explicitement signalées, la disponibilité intrinsèque atteint {{dispo}} % et un remplacement préventif à {{t_opt_arrondi}} cycles réduit le coût par cycle de {{gain_preventif}} %.

La chaîne de maintenance prédictive complète cette vision par une décision moteur par moteur. Un HI construit sur {{n_retenus}} capteurs décrit la dégradation, le classifieur détecte l'état critique avec une AUC de {{gb_auc}}, et deux modèles estiment la RUL. Le LSTM est le plus précis (RMSE de {{lstm_rmse}} cycles) ; le modèle de dégradation bayésien, moins précis (RMSE de {{deg_rmse}} cycles), est interprétable et probabiliste, et son biais comme la calibration insuffisante de ses intervalles sont mesurés et expliqués.

Les résultats sont restitués dans un tableau de bord et produits par un système reproductible. Les travaux futurs prioritaires portent sur un modèle de dégradation plus fidèle et mieux calibré, l'ajustement de la loi retenue avec censure et l'extension à plusieurs conditions opératoires.
