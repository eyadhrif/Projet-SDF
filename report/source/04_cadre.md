# Cadre du projet et état de l'art {#sec:etat-art}

## Introduction {-}

Ce chapitre pose le cadre du projet : le contexte industriel de la maintenance des turboréacteurs, la problématique et les objectifs, les contributions, puis un état de l'art ciblé sur les indices FMDS, l'estimation de la fiabilité, les stratégies de maintenance, les indicateurs de santé et l'estimation de la durée de vie résiduelle.

## Contexte industriel {#sec:contexte}

La maintenance des turboréacteurs représente une part importante du coût d'exploitation d'une flotte aérienne. Une défaillance en service entraîne l'immobilisation de l'appareil, des réparations plus lourdes, des pénalités opérationnelles et des risques pour la sécurité. À l'inverse, un remplacement trop précoce gaspille une partie de la vie utile des composants. La norme NF EN 13306 [cite:nf13306] distingue trois familles de stratégies : la maintenance **corrective**, réalisée après la défaillance ; la maintenance **préventive systématique**, réalisée à intervalles fixes ; et la maintenance **conditionnelle et prévisionnelle**, déclenchée par l'état mesuré du bien et par la prévision de son évolution [cite:jardine2006].

Choisir entre ces stratégies demande deux types de connaissances. Il faut d'abord connaître le comportement statistique de la flotte : la loi des durées de vie, le taux de défaillance, la maintenabilité et la disponibilité, c'est-à-dire les indices **FMDS** (fiabilité, maintenabilité, disponibilité, sécurité) [cite:benhmida]. Il faut ensuite savoir estimer, pour chaque moteur en service, son état de santé et sa **durée de vie résiduelle** (en anglais *remaining useful life*, RUL), à partir des mesures de ses capteurs [cite:lei2018,si2011].

## Problématique et objectifs {#sec:objectifs}

Ce projet s'appuie sur le jeu de données NASA C-MAPSS, sous-ensemble FD001 [cite:saxena2008data,saxena2008damage]. Il contient les séries de capteurs de turboréacteurs simulés : des moteurs suivis jusqu'à la défaillance (entraînement) et des moteurs dont la série s'arrête avant la défaillance (test). La problématique est la suivante : *à partir de ces seules données, comment quantifier la fiabilité de la flotte, en déduire une politique de maintenance préventive, puis aller au-delà avec une maintenance prédictive moteur par moteur ?*

Les objectifs sont :

- estimer les indices FMDS de la flotte en tenant compte de la censure des moteurs encore en service (tickets FMDS-01 et FMDS-02) ;
- construire un indicateur de santé à partir des capteurs et détecter les moteurs proches de la défaillance (PDM-01 et PDM-02) ;
- estimer la durée de vie résiduelle par deux approches de natures différentes, un modèle de dégradation probabiliste et un réseau de neurones récurrent, puis les comparer (RUL-01 à RUL-03) ;
- mettre ces résultats à disposition dans une API et un tableau de bord web (WEB-01 et WEB-02).

## Contributions {#sec:contributions}

Les travaux réalisés dans cette Version 1 sont les suivants :

1. une analyse de fiabilité complète avec censure à droite : estimateurs non paramétriques, quatre lois candidates, tests d'adéquation, choix argumenté d'une loi de Weibull à trois paramètres et indicateurs dérivés (MTTF, B1, B10, B50) ;
2. une étude de maintenabilité et de disponibilité fondée sur une hypothèse de temps de réparation explicitement signalée, et l'optimisation d'une politique de remplacement préventif à âge fixe ;
3. une chaîne de maintenance prédictive : sélection des capteurs, indicateur de santé, classification de l'état et deux modèles de RUL, dont un modèle bayésien qui fournit une distribution de la durée de vie résiduelle ;
4. un diagnostic honnête des limites, en particulier la calibration insuffisante des intervalles du modèle de dégradation ;
5. un système logiciel reproductible (pipeline, API, tableau de bord), dont chaque résultat est vérifié par une suite de tests automatiques.

## État de l'art ciblé {#sec:ea}

### Les indices FMDS {#sec:ea-fmds}

La sûreté de fonctionnement d'un bien se décrit par quatre grandeurs [cite:benhmida,nf13306]. La **fiabilité** $R(t)$ est la probabilité que le bien accomplisse sa fonction sur l'intervalle $[0, t]$. La **maintenabilité** $M(t)$ est la probabilité qu'une réparation soit achevée avant la durée $t$. La **disponibilité** $A(t)$ est la probabilité que le bien soit en état de fonctionner à l'instant $t$. La **sécurité** concerne l'absence d'événements critiques pour les personnes et l'environnement ; elle n'est pas quantifiée dans ce projet, faute de données sur la gravité des défaillances. Les indicateurs usuels en découlent : MTTF (durée moyenne de fonctionnement avant défaillance), MTTR (durée moyenne de réparation), MTBF, MUT et MDT, ainsi que les durées $B_p$, âges auxquels une proportion $p$ de la population a défailli.

### Estimation non paramétrique et paramétrique de la fiabilité {#sec:ea-estimation}

Lorsque certaines unités n'ont pas encore défailli à la fin de l'observation, leurs durées sont **censurées à droite** : on sait seulement qu'elles dépassent la durée observée. Les ignorer biaiserait l'estimation vers des durées trop courtes. L'estimateur de Kaplan-Meier [cite:kaplanmeier1958] traite la censure en ne retirant une unité censurée que de l'effectif à risque. Sa variance s'estime par la formule de Greenwood [cite:greenwood1926]. L'estimateur de Nelson-Aalen [cite:nelson1972,aalen1978] estime le taux de défaillance cumulé ; son lissage par noyau donne une estimation non paramétrique du taux de défaillance $\lambda(t)$.

L'approche paramétrique suppose une loi. La loi de Weibull [cite:weibull1951] est la référence en fiabilité mécanique : son paramètre de forme $\beta$ distingue les défaillances de jeunesse ($\beta < 1$), aléatoires ($\beta = 1$) et d'usure ($\beta > 1$). Ses paramètres s'estiment soit par moindres carrés sur le diagramme de Weibull, avec les rangs médians de Bernard [cite:bernard1953], soit par maximum de vraisemblance. L'adéquation se juge par le test de Kolmogorov-Smirnov [cite:massey1951] et les lois candidates se comparent par le critère d'information d'Akaike (AIC) [cite:akaike1974].

### Maintenance préventive et maintenance prédictive {#sec:ea-maintenance}

La politique de **remplacement à âge fixe** de Barlow et Proschan [cite:barlow1965] remplace préventivement un bien à l'âge $T$ s'il n'a pas défailli avant. L'âge optimal minimise le coût moyen par unité de temps ; il n'existe un optimum fini que si le taux de défaillance est croissant. Cette politique traite tous les moteurs de la même façon. La maintenance **prédictive**, ou PHM (*prognostics and health management*), décide au contraire moteur par moteur à partir de son état mesuré [cite:jardine2006,lei2018].

### Indicateurs de santé {#sec:ea-hi}

Un indicateur de santé (*health indicator*, HI) résume l'état d'un système en une grandeur scalaire, idéalement monotone au cours de la dégradation. Coble et Hines [cite:coble2009] proposent de sélectionner les capteurs selon leur monotonie, leur tendance et leur pronosticabilité. Wang et al. [cite:wang2008] construisent un HI par régression linéaire des capteurs vers une cible qui vaut un en début de vie et zéro à la défaillance : c'est l'approche suivie dans ce projet.

### Approches d'estimation de la durée de vie résiduelle {#sec:ea-rul}

Les méthodes d'estimation du RUL se répartissent en deux familles [cite:si2011,lei2018].

Les **modèles de dégradation statistiques** décrivent l'évolution d'un indicateur jusqu'à un seuil de défaillance. Gebraeel et al. [cite:gebraeel2005] proposent un modèle à coefficients aléatoires dont l'a priori est appris sur une flotte et mis à jour de façon bayésienne avec les mesures de chaque unité, ce qui donne une distribution du RUL. Les processus de diffusion, comme le processus de Wiener, en sont une généralisation [cite:si2012].

Les **méthodes d'apprentissage automatique** apprennent directement la relation entre les mesures et le RUL. Les réseaux récurrents [cite:heimes2008], en particulier les LSTM [cite:hochreiter1997,zheng2017], et les réseaux convolutifs [cite:babu2016,li2018] sont devenus la référence sur C-MAPSS. Ils sont plus précis, mais moins interprétables et ne fournissent pas nativement d'incertitude.

### Travaux sur C-MAPSS {#sec:ea-cmapss}

Le jeu C-MAPSS a été produit avec le simulateur de turboréacteur de la NASA [cite:saxena2008damage] et compte quatre sous-ensembles, de FD001 (une condition opératoire, un mode de défaillance) à FD004 (six conditions, deux modes). Ramasso et Saxena [cite:ramasso2014] recensent et comparent les nombreuses méthodes publiées. Deux conventions y sont devenues usuelles et sont reprises ici : la cible de RUL plafonnée pendant la phase saine [cite:heimes2008] et le score asymétrique du challenge PHM, qui pénalise davantage les prédictions tardives [cite:saxena2008damage].

## Conclusion {-}

Ce chapitre a présenté le contexte, les objectifs et les méthodes de référence sur lesquelles l'étude s'appuie. Le chapitre suivant décrit les données utilisées.
