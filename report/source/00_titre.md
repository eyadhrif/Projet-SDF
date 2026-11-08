<div class="page-titre">
<div class="haut">École Nationale Supérieure d'Ingénieurs de Tunis (ENSIT)<br>GMAM 3 — Module « Sûreté de fonctionnement et maintenance »<br>Projet pratique en binôme</div>
<div>
<h1 class="titre">Estimation des indices FMDS et maintenance prédictive d'une flotte de turboréacteurs</h1>
<div class="sous-titre">Fiabilité, maintenabilité, disponibilité, détection de l'état de santé et estimation de la durée de vie résiduelle sur le jeu NASA C-MAPSS FD001</div>
<p style="margin-top:18pt;text-align:center"><b>Rapport scientifique — Version 1</b></p>
</div>
<div class="auteurs"><b>Eya DHRIF</b> et <b>Salma MOUEDDEB</b><br>Encadrant : M. Fayçal Ben Hmida</div>
</div>
<div class="saut"></div>

## Résumé {-}

Ce rapport présente une étude de sûreté de fonctionnement et de maintenance prédictive menée sur le jeu de données public NASA C-MAPSS, sous-ensemble FD001, qui simule la dégradation jusqu'à la défaillance de turboréacteurs d'avion [cite:saxena2008data,saxena2008damage]. L'étude suit deux axes complémentaires.

Le premier axe estime les indices FMDS de la flotte. Les {{n_moteurs_train}} moteurs d'entraînement fournissent des durées de défaillance observées et les {{n_moteurs_test}} moteurs de test des durées censurées à droite. L'estimateur de Kaplan-Meier, l'estimateur de Nelson-Aalen et plusieurs lois paramétriques sont comparés. La loi de Weibull à trois paramètres est retenue (β = {{w3_beta}}, η = {{w3_eta}} cycles, γ = {{w3_gamma}} cycles, test de Kolmogorov-Smirnov accepté avec p = {{w3_ks_p}}). Elle donne un MTTF de {{mttf}} cycles et une durée B10 de {{b10}} cycles. À partir de temps de réparation simulés, hypothèse rendue nécessaire par l'absence de données de réparation, la disponibilité intrinsèque vaut {{dispo}} % et une politique de remplacement préventif à l'âge {{t_opt_arrondi}} cycles réduit le coût par cycle de {{gain_preventif}} %.

Le second axe construit une chaîne de maintenance prédictive : sélection de {{n_retenus}} capteurs pronostiques, indicateur de santé, détection de l'état critique (AUC de test {{gb_auc}}) et estimation de la durée de vie résiduelle (RUL) par deux modèles. Un modèle de dégradation bayésien interprétable atteint un RMSE de {{deg_rmse}} cycles ; un réseau LSTM atteint {{lstm_rmse}} cycles. Le modèle de dégradation fournit un intervalle de prédiction, mais celui-ci est trop étroit : l'intervalle nominal P10–P90 ne couvre le RUL réel que dans {{couverture_80}} % des cas. Les résultats sont servis par une API et un tableau de bord web, et chaque chiffre de ce rapport est produit par le code et vérifié par une suite de tests automatiques.

**Mots-clés :** fiabilité, censure à droite, Kaplan-Meier, Weibull à trois paramètres, disponibilité, remplacement préventif, indicateur de santé, durée de vie résiduelle, modèle bayésien, LSTM, C-MAPSS.

## Table des matières {-}

!table-des-matieres

## Liste des figures {-}

!liste-des-figures

## Liste des tableaux {-}

!liste-des-tableaux
