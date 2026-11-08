# Cadre du projet, état de l'art et jeu de données {#sec:cadre}

## Introduction {-}

Ce chapitre présente le contexte industriel, la problématique et les objectifs du projet, puis un état de l'art ciblé sur les méthodes utilisées. Il décrit enfin le jeu de données C-MAPSS FD001.

## Contexte industriel et problématique {#sec:contexte}

La norme NF EN 13306 [cite:nf13306] distingue trois familles de maintenance : **corrective**, après la défaillance ; **préventive systématique**, à intervalles fixes ; **conditionnelle et prévisionnelle**, déclenchée par l'état mesuré du bien et par la prévision de son évolution [cite:jardine2006]. Choisir entre elles demande deux connaissances : le comportement statistique de la flotte, décrit par les indices FMDS [cite:benhmida], et l'état de santé de chaque moteur en service, avec sa RUL [cite:lei2018,si2011].

La problématique est donc la suivante : à partir des seules données de capteurs de C-MAPSS FD001, comment quantifier la fiabilité de la flotte, en déduire une politique préventive, puis passer à une maintenance prédictive moteur par moteur ?

## Objectifs et contributions {#sec:objectifs}

Le projet poursuit quatre objectifs : (**1**) estimer les indices FMDS en tenant compte de la censure des moteurs encore en service ; (**2**) construire un HI et détecter les moteurs proches de la défaillance ; (**3**) estimer la RUL par un modèle de dégradation probabiliste et par un réseau récurrent, puis les comparer ; (**4**) restituer ces résultats dans un tableau de bord web.

Les contributions qui en découlent sont :

- une analyse de fiabilité avec censure à droite, quatre lois candidates, des tests d'adéquation et le choix argumenté d'une loi de Weibull à trois paramètres ;
- une étude de maintenabilité et de disponibilité, fondée sur des temps de réparation simulés et signalés comme tels, avec l'optimisation d'un remplacement préventif à âge fixe ;
- une chaîne prédictive complète : sélection des capteurs, HI, classification de l'état et deux modèles de RUL, dont un modèle bayésien qui fournit une distribution de la RUL ;
- un diagnostic explicite des limites, en particulier la calibration insuffisante du modèle de dégradation ;
- un système reproductible dont chaque résultat est vérifié par des tests automatiques.

## État de l'art ciblé {#sec:ea}

### Indices FMDS {#sec:ea-fmds}

La fiabilité $R(t)$ est la probabilité qu'un bien fonctionne sur $[0, t]$, la maintenabilité $M(t)$ celle qu'une réparation soit achevée avant $t$, et la disponibilité $A(t)$ celle que le bien soit en état de fonctionner à l'instant $t$ [cite:benhmida,nf13306]. La sécurité n'est pas quantifiée ici, faute de données sur la gravité des défaillances. En découlent le MTTF, le MTTR, le MTBF et les durées $B_p$, âges auxquels une proportion $p$ de la population a défailli.

### Estimation de la fiabilité {#sec:ea-estimation}

Les durées des unités encore en service sont censurées à droite ; l'estimateur KM [cite:kaplanmeier1958], avec la variance de Greenwood [cite:greenwood1926], et l'estimateur de Nelson-Aalen [cite:nelson1972,aalen1978] en tiennent compte. En paramétrique, la loi de Weibull [cite:weibull1951] est la référence en fiabilité mécanique : $\beta > 1$ signe une usure. Ses paramètres s'estiment par MCO sur le diagramme de Weibull avec les rangs de Bernard [cite:bernard1953] ou par MV, et les lois se comparent par le test KS [cite:massey1951] et l'AIC [cite:akaike1974].

### Maintenance préventive et prédictive {#sec:ea-maintenance}

La politique de remplacement à âge fixe de Barlow et Proschan [cite:barlow1965] remplace un bien à l'âge $T$ s'il n'a pas défailli ; un optimum fini n'existe que si le taux de défaillance croît. Elle traite tous les moteurs de la même façon, alors que la maintenance prédictive (PHM) décide moteur par moteur à partir de l'état mesuré [cite:jardine2006,lei2018].

### Indicateurs de santé {#sec:ea-hi}

Un HI résume l'état d'un système en une grandeur scalaire, idéalement monotone. Coble et Hines [cite:coble2009] sélectionnent les capteurs selon leur monotonie et leur tendance ; Wang et al. [cite:wang2008] construisent le HI par régression linéaire vers une cible qui vaut un en début de vie et zéro à la défaillance, approche suivie ici.

### Estimation de la RUL {#sec:ea-rul}

Les modèles de dégradation statistiques décrivent l'évolution d'un indicateur jusqu'à un seuil : Gebraeel et al. [cite:gebraeel2005] apprennent un a priori sur la flotte et le mettent à jour de façon bayésienne pour chaque unité, ce que généralisent les processus de Wiener [cite:si2012]. Les réseaux récurrents [cite:heimes2008], en particulier les LSTM [cite:hochreiter1997,zheng2017], et les réseaux convolutifs [cite:babu2016,li2018] sont plus précis sur C-MAPSS, mais moins interprétables et sans incertitude native.

### Travaux sur C-MAPSS {#sec:ea-cmapss}

Ramasso et Saxena [cite:ramasso2014] recensent les nombreuses méthodes publiées sur C-MAPSS, dont les quatre sous-ensembles vont de FD001 (une condition, un mode de défaillance) à FD004 (six conditions, deux modes). Deux conventions y sont reprises : la cible de RUL plafonnée en phase saine [cite:heimes2008] et le score asymétrique du challenge PHM, qui pénalise davantage les prédictions tardives [cite:saxena2008damage].

## Jeu de données {#sec:donnees}

### Origine et protocole de simulation {#sec:donnees-origine}

Les données proviennent du simulateur C-MAPSS de la NASA [cite:saxena2008damage]. Chaque moteur démarre avec une usure initiale inconnue ; une dégradation du HPC est injectée jusqu'à la défaillance, et les mesures sont bruitées. FD001 comporte **une seule condition opératoire** et **un seul mode de défaillance** [cite:saxena2008data].

### Structure et tailles {#sec:donnees-structure}

Chaque ligne correspond à un cycle de vol d'un moteur et contient {{n_reglages}} réglages opérationnels et {{n_capteurs}} capteurs. Le fichier d'entraînement suit {{n_moteurs_train}} moteurs jusqu'à la défaillance ; le fichier de test contient {{n_moteurs_test}} autres moteurs arrêtés avant la défaillance, dont la RUL réelle au dernier cycle est fournie à part. Le [@tab:donnees_tailles] donne les tailles exactes.

!tableau[donnees_tailles]

### Censure à droite {#sec:donnees-censure}

Pour la fiabilité, les {{n_unites}} moteurs forment une seule population : {{n_defaillances}} durées de défaillance observées (statut $\delta = 1$) et {{n_censures}} durées censurées à droite, les moteurs de test étant encore en service à leur dernier cycle ($\delta = 0$). La RUL réelle des moteurs de test sert uniquement à évaluer les modèles de RUL, ce qui évite toute fuite d'information. La [@fig:donnees_durees_de_vie] montre les deux distributions ; **aucun moteur ne défaille avant {{t_min_obs}} cycles**, ce qui orientera le choix d'une loi à seuil.

!figure[donnees_durees_de_vie](Durées de vie des moteurs d'entraînement (gauche) et durées observées, censurées à droite, des moteurs de test (droite).)

### Capteurs constants {#sec:donnees-capteurs}

Avec une seule condition opératoire, {{n_constants}} capteurs prennent moins de {{min_valeurs_distinctes}} valeurs distinctes et sont écartés ({{capteurs_constants}}), de même que les réglages opérationnels. Les autres capteurs dérivent progressivement au cours de la vie, avec un bruit important d'un cycle à l'autre, d'où l'usage de moyennes glissantes.

## Conclusion {-}

Ce chapitre a fixé le cadre et les méthodes de référence de l'étude. Le jeu FD001 fournit {{n_unites}} unités pour la fiabilité, dont {{n_censures}} censurées, sans défaillance avant {{t_min_obs}} cycles. Le chapitre suivant présente les méthodes appliquées à ces données.
