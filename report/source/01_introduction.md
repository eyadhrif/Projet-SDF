# Introduction {#sec:introduction}

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

## Organisation du rapport {#sec:organisation}

Le [@sec:etat-art] présente un état de l'art ciblé. Le [@sec:donnees] décrit les données. Le [@sec:methodologie] détaille les méthodes, leurs fondements mathématiques et leurs hypothèses. Le [@sec:architecture] décrit l'architecture logicielle et le [@sec:protocole] le protocole expérimental. Les résultats sont présentés au [@sec:resultats] et discutés au [@sec:discussion]. Le [@sec:perspectives] expose les perspectives, avant la conclusion ([@sec:conclusion]).
