# État de l'art ciblé {#sec:etat-art}

## Les indices FMDS {#sec:ea-fmds}

La sûreté de fonctionnement d'un bien se décrit par quatre grandeurs [cite:benhmida,nf13306]. La **fiabilité** $R(t)$ est la probabilité que le bien accomplisse sa fonction sur l'intervalle $[0, t]$. La **maintenabilité** $M(t)$ est la probabilité qu'une réparation soit achevée avant la durée $t$. La **disponibilité** $A(t)$ est la probabilité que le bien soit en état de fonctionner à l'instant $t$. La **sécurité** concerne l'absence d'événements critiques pour les personnes et l'environnement ; elle n'est pas quantifiée dans ce projet, faute de données sur la gravité des défaillances. Les indicateurs usuels en découlent : MTTF (durée moyenne de fonctionnement avant défaillance), MTTR (durée moyenne de réparation), MTBF, MUT et MDT, ainsi que les durées $B_p$, âges auxquels une proportion $p$ de la population a défailli.

## Estimation non paramétrique et paramétrique de la fiabilité {#sec:ea-estimation}

Lorsque certaines unités n'ont pas encore défailli à la fin de l'observation, leurs durées sont **censurées à droite** : on sait seulement qu'elles dépassent la durée observée. Les ignorer biaiserait l'estimation vers des durées trop courtes. L'estimateur de Kaplan-Meier [cite:kaplanmeier1958] traite la censure en ne retirant une unité censurée que de l'effectif à risque. Sa variance s'estime par la formule de Greenwood [cite:greenwood1926]. L'estimateur de Nelson-Aalen [cite:nelson1972,aalen1978] estime le taux de défaillance cumulé ; son lissage par noyau donne une estimation non paramétrique du taux de défaillance $\lambda(t)$.

L'approche paramétrique suppose une loi. La loi de Weibull [cite:weibull1951] est la référence en fiabilité mécanique : son paramètre de forme $\beta$ distingue les défaillances de jeunesse ($\beta < 1$), aléatoires ($\beta = 1$) et d'usure ($\beta > 1$). Ses paramètres s'estiment soit par moindres carrés sur le diagramme de Weibull, avec les rangs médians de Bernard [cite:bernard1953], soit par maximum de vraisemblance. L'adéquation se juge par le test de Kolmogorov-Smirnov [cite:massey1951] et les lois candidates se comparent par le critère d'information d'Akaike (AIC) [cite:akaike1974].

## Maintenance préventive et maintenance prédictive {#sec:ea-maintenance}

La politique de **remplacement à âge fixe** de Barlow et Proschan [cite:barlow1965] remplace préventivement un bien à l'âge $T$ s'il n'a pas défailli avant. L'âge optimal minimise le coût moyen par unité de temps ; il n'existe un optimum fini que si le taux de défaillance est croissant. Cette politique traite tous les moteurs de la même façon. La maintenance **prédictive**, ou PHM (*prognostics and health management*), décide au contraire moteur par moteur à partir de son état mesuré [cite:jardine2006,lei2018].

## Indicateurs de santé {#sec:ea-hi}

Un indicateur de santé (*health indicator*, HI) résume l'état d'un système en une grandeur scalaire, idéalement monotone au cours de la dégradation. Coble et Hines [cite:coble2009] proposent de sélectionner les capteurs selon leur monotonie, leur tendance et leur pronosticabilité. Wang et al. [cite:wang2008] construisent un HI par régression linéaire des capteurs vers une cible qui vaut un en début de vie et zéro à la défaillance : c'est l'approche suivie dans ce projet.

## Approches d'estimation de la durée de vie résiduelle {#sec:ea-rul}

Les méthodes d'estimation du RUL se répartissent en deux familles [cite:si2011,lei2018].

Les **modèles de dégradation statistiques** décrivent l'évolution d'un indicateur jusqu'à un seuil de défaillance. Gebraeel et al. [cite:gebraeel2005] proposent un modèle à coefficients aléatoires dont l'a priori est appris sur une flotte et mis à jour de façon bayésienne avec les mesures de chaque unité, ce qui donne une distribution du RUL. Les processus de diffusion, comme le processus de Wiener, en sont une généralisation [cite:si2012].

Les **méthodes d'apprentissage automatique** apprennent directement la relation entre les mesures et le RUL. Les réseaux récurrents [cite:heimes2008], en particulier les LSTM [cite:hochreiter1997,zheng2017], et les réseaux convolutifs [cite:babu2016,li2018] sont devenus la référence sur C-MAPSS. Ils sont plus précis, mais moins interprétables et ne fournissent pas nativement d'incertitude.

## Travaux sur C-MAPSS {#sec:ea-cmapss}

Le jeu C-MAPSS a été produit avec le simulateur de turboréacteur de la NASA [cite:saxena2008damage] et compte quatre sous-ensembles, de FD001 (une condition opératoire, un mode de défaillance) à FD004 (six conditions, deux modes). Ramasso et Saxena [cite:ramasso2014] recensent et comparent les nombreuses méthodes publiées. Deux conventions y sont devenues usuelles et sont reprises ici : la cible de RUL plafonnée pendant la phase saine [cite:heimes2008] et le score asymétrique du challenge PHM, qui pénalise davantage les prédictions tardives [cite:saxena2008damage].
