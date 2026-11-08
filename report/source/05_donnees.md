# Données {#sec:donnees}

## Introduction {-}

Ce chapitre décrit le jeu de données C-MAPSS FD001 : son origine, sa structure et ses tailles exactes, le traitement des moteurs encore en service par la censure à droite, et l'analyse exploratoire des capteurs.

## Origine et protocole de simulation {#sec:donnees-origine}

Les données proviennent du simulateur C-MAPSS (*Commercial Modular Aero-Propulsion System Simulation*) de la NASA [cite:saxena2008damage]. Chaque moteur démarre avec un niveau d'usure initial et une dispersion de fabrication inconnus, considérés comme normaux. Au cours des cycles de vol, une dégradation est injectée dans le compresseur haute pression (HPC) jusqu'à la défaillance, définie par le franchissement d'une marge de fonctionnement. Les mesures sont bruitées. Le sous-ensemble FD001 retenu ici est le plus simple : **une seule condition opératoire** (niveau de la mer) et **un seul mode de défaillance** (dégradation du HPC) [cite:saxena2008data].

## Structure et tailles exactes {#sec:donnees-structure}

Chaque ligne des fichiers correspond à un cycle de vol d'un moteur et contient le numéro du moteur, le numéro de cycle, {{n_reglages}} réglages opérationnels et {{n_capteurs}} capteurs (températures, pressions, vitesses de rotation, débits). Trois fichiers sont utilisés :

- `train_FD001.txt` : {{n_moteurs_train}} moteurs suivis jusqu'à la défaillance, soit {{n_lignes_train}} lignes ;
- `test_FD001.txt` : {{n_moteurs_test}} autres moteurs, dont la série s'arrête à un instant inconnu avant la défaillance, soit {{n_lignes_test}} lignes ;
- `RUL_FD001.txt` : la durée de vie résiduelle réelle de chaque moteur de test à son dernier cycle observé.

Le [@tab:donnees_tailles] résume les tailles et les statistiques principales. Les durées de vie d'entraînement vont de {{vie_min}} à {{vie_max}} cycles, avec une moyenne de {{vie_moy}} cycles. Les séries de test sont plus courtes, de {{test_len_min}} à {{test_len_max}} cycles (moyenne {{test_len_moy}}), et leur RUL réel va de {{rul_test_min}} à {{rul_test_max}} cycles (moyenne {{rul_test_moy}}).

!tableau[donnees_tailles]

La [@fig:donnees_durees_de_vie] montre la distribution des durées. Un fait est essentiel pour la suite : **aucun moteur ne défaille avant {{t_min_obs}} cycles**. Cette période sans défaillance orientera le choix d'une loi à seuil au [@sec:fiabilite].

!figure[donnees_durees_de_vie](Distribution des durées de vie des moteurs d'entraînement (gauche) et des durées observées des moteurs de test, censurées à droite (droite).)

## Censure à droite {#sec:donnees-censure}

Pour l'analyse de fiabilité, les {{n_unites}} moteurs forment une seule population. Les {{n_defaillances}} moteurs d'entraînement fournissent des **durées de défaillance observées** (statut $\delta = 1$). Les {{n_censures}} moteurs de test étaient encore en fonctionnement à leur dernier cycle observé : leur durée de vie est seulement connue pour être supérieure à ce cycle. Ce sont des **censures à droite** (statut $\delta = 0$). Le RUL réel des moteurs de test n'est pas utilisé dans l'analyse de fiabilité : il sert uniquement à évaluer les modèles de RUL, ce qui évite toute fuite d'information entre les deux parties de l'étude.

## Capteurs constants et analyse exploratoire {#sec:donnees-capteurs}

Le [@tab:donnees_capteurs] donne les statistiques des {{n_capteurs}} capteurs et des réglages sur le jeu d'entraînement. Avec une seule condition opératoire, plusieurs capteurs ne varient pas ou presque : {{n_constants}} capteurs présentent moins de {{min_valeurs_distinctes}} valeurs distinctes sur tout le jeu et sont écartés ({{capteurs_constants}}). Les réglages opérationnels ne portent pas d'information de dégradation. Les autres capteurs dérivent progressivement au cours de la vie du moteur, comme le montre la [@fig:donnees_signaux_moteur1] pour {{n_capteurs_illustres}} d'entre eux : certains croissent (températures, pression statique en sortie du HPC), d'autres décroissent (pression en sortie du HPC, débits de refroidissement). Le bruit de mesure est important à l'échelle d'un cycle, d'où l'intérêt des moyennes glissantes.

!tableau[donnees_capteurs]

!figure[donnees_signaux_moteur1](Signaux bruts de capteurs retenus pour le premier moteur d'entraînement et leur moyenne glissante : la dérive progressive vers la défaillance est visible malgré le bruit.)

## Conclusion {-}

Les données forment une population de {{n_unites}} unités pour l'analyse de fiabilité, dont {{n_censures}} durées censurées à droite. Aucune défaillance n'intervient avant {{t_min_obs}} cycles, et {{n_constants}} capteurs constants sont écartés. Le chapitre suivant présente les méthodes appliquées à ces données.
