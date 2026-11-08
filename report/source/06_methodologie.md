# Méthodologie {#sec:methodologie}

## Introduction {-}

Ce chapitre présente les méthodes mises en œuvre, dans l'ordre du plan de sprints : l'estimation de la fiabilité, la maintenabilité et la disponibilité, la construction de l'indicateur de santé, la classification de l'état et les deux modèles d'estimation de la durée de vie résiduelle. Pour chacune sont donnés les fondements mathématiques, les hypothèses et le choix des paramètres.

Les valeurs numériques des paramètres sont lues directement dans le code ; elles sont regroupées au [@tab:hypotheses_parametres] (annexe). Chaque section indique le ticket du plan de sprints et la personne responsable.

## Fiabilité (FMDS-01, Eya) {#sec:fiabilite}

### Estimateur de Kaplan-Meier

Soient $t_1 < t_2 < \dots$ les instants distincts de défaillance, $d_i$ le nombre de défaillances en $t_i$ et $n_i$ le nombre d'unités encore à risque juste avant $t_i$ (ni défaillies, ni censurées). L'estimateur de Kaplan-Meier [cite:kaplanmeier1958] est

$$\hat R(t) = \prod_{t_i \le t} \left(1 - \frac{d_i}{n_i}\right). $$ {#eq:km}

Une unité censurée en $c$ contribue à l'effectif à risque jusqu'à $c$, puis en sort sans être comptée comme défaillance. La variance est estimée par la formule de Greenwood [cite:greenwood1926] :

$$\widehat{\mathrm{Var}}\big[\hat R(t)\big] = \hat R(t)^2 \sum_{t_i \le t} \frac{d_i}{n_i (n_i - d_i)}. $$ {#eq:greenwood}

L'intervalle de confiance à $95\,\%$ est construit sur la transformation $\log(-\log \hat R)$, qui garantit des bornes dans $[0, 1]$. La durée médiane de survie est le plus petit $t$ tel que $\hat R(t) \le 0{,}5$, et l'aire sous la courbe de Kaplan-Meier donne une estimation non paramétrique de la durée moyenne.

**Hypothèse :** la censure est non informative, c'est-à-dire que l'arrêt de l'observation d'un moteur de test ne dépend pas de son état. Dans C-MAPSS, l'instant de troncature des séries de test est tiré indépendamment de la dégradation [cite:saxena2008damage], ce qui justifie cette hypothèse.

### Estimateur de Nelson-Aalen et taux de défaillance

Le taux de défaillance cumulé est estimé par [cite:nelson1972,aalen1978]

$$\hat H(t) = \sum_{t_i \le t} \frac{d_i}{n_i}, \qquad \hat R_{NA}(t) = e^{-\hat H(t)} . $$ {#eq:na}

Le taux de défaillance instantané $\lambda(t)$ est obtenu en lissant les incréments $d_i / n_i$ par un noyau d'Epanechnikov de largeur $b = {{na_largeur_noyau}}$ cycles. Ce lissage est non paramétrique : il permet de vérifier la forme de $\lambda(t)$ sans supposer de loi.

### Lois paramétriques et estimation

La loi de Weibull à trois paramètres [cite:weibull1951] a pour fonction de fiabilité et taux de défaillance

$$R(t) = \begin{cases} 1 & t \le \gamma \\ \exp\!\left[-\left(\dfrac{t-\gamma}{\eta}\right)^{\beta}\right] & t > \gamma \end{cases}, \qquad \lambda(t) = \frac{\beta}{\eta}\left(\frac{t-\gamma}{\eta}\right)^{\beta-1} \text{ pour } t > \gamma, $$ {#eq:weibull3}

avec $\beta$ le paramètre de forme, $\eta$ le paramètre d'échelle et $\gamma$ le paramètre de position, ou durée sans défaillance garantie. La loi à deux paramètres correspond à $\gamma = 0$.

**Moindres carrés ordinaires (MCO)**, la méthode graphique du cours [cite:benhmida]. Les $n$ durées de défaillance triées reçoivent la fonction de répartition empirique de Bernard [cite:bernard1953], et la loi de Weibull 2P se linéarise :

$$\hat F_i = \frac{i - 0{,}3}{n + 0{,}4}, \qquad \ln\!\big(-\ln(1-\hat F_i)\big) = \beta \ln t_i - \beta \ln \eta . $$ {#eq:bernard}

La droite de régression donne $\beta$ (pente) et $\eta$, et le coefficient $R^2$ mesure la linéarité du diagramme. Une courbure du diagramme signale un paramètre de position non nul.

**Maximum de vraisemblance (MV).** Pour des durées $t_i$ de statut $\delta_i$ ($\delta_i = 1$ : défaillance, $\delta_i = 0$ : censure), la log-vraisemblance est

$$\ell(\theta) = \sum_i \Big[\delta_i \ln f(t_i; \theta) + (1 - \delta_i) \ln R(t_i; \theta)\Big]. $$ {#eq:vraisemblance}

Deux estimations sont réalisées. La première, avec censure, porte sur les {{n_unites}} unités et la loi de Weibull 2P (bibliothèque lifelines [cite:davidsonpilon2019]) ; elle donne un intervalle de confiance sur $\beta$. La seconde porte sur les {{n_defaillances}} **durées de défaillance complètes** ($\delta_i = 1$) et sert à comparer quatre lois candidates : exponentielle, Weibull 2P, log-normale et Weibull 3P (bibliothèque SciPy). **La loi retenue, Weibull 3P, est donc ajustée sur les seules défaillances observées** : ce choix et ses conséquences sont discutés au [@sec:limites].

### Validation et choix du modèle

L'adéquation de chaque loi est testée par le test de Kolmogorov-Smirnov [cite:massey1951], de statistique $D = \sup_t |F_n(t) - F(t)|$, au seuil $\alpha = 5\,\%$. Les lois sont comparées par le critère d'Akaike [cite:akaike1974], $\mathrm{AIC} = 2k - 2\ell$, où $k$ est le nombre de paramètres : il pénalise la complexité. Une différence d'AIC inférieure à deux unités indique deux modèles équivalents.

### Indicateurs dérivés

Pour la loi de Weibull 3P, la durée moyenne de fonctionnement avant défaillance et la durée $B_p$ (âge auquel une proportion $p$ a défailli) valent

$$\mathrm{MTTF} = \gamma + \eta\, \Gamma\!\left(1 + \frac{1}{\beta}\right), \qquad B_p = \gamma + \eta \big(-\ln(1-p)\big)^{1/\beta}. $$ {#eq:mttf}

Le rapport utilise $B_1$, $B_{10}$ et $B_{50}$ (durée médiane). La **fiabilité conditionnelle** donne la probabilité qu'un moteur ayant atteint l'âge $t$ fonctionne encore $\Delta$ cycles plus tard, avec $\Delta = {{horizon_conditionnel}}$ cycles :

$$R(t + \Delta \mid t) = \frac{R(t + \Delta)}{R(t)} . $$ {#eq:conditionnelle}

## Maintenabilité et disponibilité (FMDS-02, Salma) {#sec:fmds02}

### Hypothèse sur les temps de réparation

> **Hypothèse forte.** C-MAPSS ne contient aucun temps de réparation. Pour illustrer la démarche du cours, des temps de réparation sont **simulés** : un temps par défaillance observée, tiré selon une loi log-normale de médiane {{ttr_mediane}} h et d'écart-type logarithmique {{ttr_sigma_sim}}, avec une graine fixe ({{graine_ttr}}). La conversion entre unités suppose qu'un cycle correspond à un vol d'environ {{h_par_cycle}} h. Les résultats de cette section illustrent la méthode ; ils ne décrivent pas une flotte réelle.

La loi log-normale est le modèle usuel des durées de réparation, car celles-ci sont positives et asymétriques. Ses paramètres sont ré-estimés par maximum de vraisemblance sur l'échantillon simulé, et l'ajustement est vérifié par le test de Kolmogorov-Smirnov. La maintenabilité, le MTTR et la durée $t_{90}$ ($90\,\%$ des réparations terminées) valent

$$M(t) = \Phi\!\left(\frac{\ln t - \mu}{\sigma}\right), \qquad \mathrm{MTTR} = e^{\mu + \sigma^2/2}, \qquad t_{90} = e^{\mu + z_{0,9}\,\sigma}, $$ {#eq:lognormale}

où $\Phi$ est la fonction de répartition de la loi normale centrée réduite et $z_{0,9}$ son quantile d'ordre $0{,}9$.

### Disponibilité

La disponibilité intrinsèque (asymptotique) d'un moteur réparé après chaque défaillance est

$$A_\infty = \frac{\mathrm{MUT}}{\mathrm{MUT} + \mathrm{MDT}}, $$ {#eq:dispo}

avec $\mathrm{MUT} = \mathrm{MTTF}$ et $\mathrm{MDT} = \mathrm{MTTR}$ exprimés en cycles ; le MTBF vaut $\mathrm{MUT} + \mathrm{MDT}$. L'évolution de la disponibilité instantanée est décrite par le modèle markovien à deux états (marche, panne), de taux $\lambda = 1/\mathrm{MTTF}$ et $\mu = 1/\mathrm{MTTR}$ :

$$A(t) = \frac{\mu}{\lambda + \mu} + \frac{\lambda}{\lambda + \mu}\, e^{-(\lambda + \mu) t}. $$ {#eq:markov}

Ce modèle suppose des taux constants. Il s'agit d'une **approximation** : la loi retenue a un taux de défaillance croissant. Elle donne cependant la bonne limite $A_\infty$ et illustre la convergence.

### Politique de remplacement préventif à âge fixe

Selon la politique de Barlow et Proschan [cite:barlow1965], un moteur est remplacé préventivement à l'âge $T$ s'il n'a pas défailli avant, pour un coût $C_p$ ; une défaillance en service coûte $C_c > C_p$. Par le théorème du renouvellement, le coût moyen par cycle vaut

$$C(T) = \frac{C_p\, R(T) + C_c\, \big(1 - R(T)\big)}{\displaystyle\int_0^T R(t)\, \mathrm{d}t}, \qquad C_\infty = \frac{C_c}{\mathrm{MTTF}} , $$ {#eq:cout}

où $C_\infty$ est le coût de la maintenance corrective seule. L'âge optimal $T^*$ minimise $C(T)$ ; il est recherché numériquement au-delà de $\gamma$. Les coûts relatifs sont $C_p = {{cp}}$ et $C_c = {{cc}}$ : une défaillance en service coûte autant que cinq remplacements préventifs. Ce rapport est une hypothèse d'illustration.

## Sélection des capteurs et indicateur de santé (PDM-01, Salma) {#sec:hi}

### Sélection des capteurs

Après le retrait des capteurs constants ([@sec:donnees-capteurs]), deux scores sont calculés pour chaque capteur, en s'inspirant de Coble et Hines [cite:coble2009]. La **tendance** est la corrélation moyenne, sur les moteurs d'entraînement, entre le capteur et le numéro de cycle ; son signe indique le sens de la dérive. La **monotonie**, calculée sur la série lissée de chaque moteur, vaut

$$\mathrm{Mon} = \frac{\big|\#\{\Delta x > 0\} - \#\{\Delta x < 0\}\big|}{n - 1}. $$ {#eq:monotonie}

Un capteur est retenu si sa tendance vérifie $|\rho| \ge {{seuil_tendance}}$. La monotonie est calculée et affichée, mais n'entre pas dans la règle de sélection.

### Features fenêtrées

Pour chaque capteur retenu et chaque cycle, trois features sont calculées sur une fenêtre glissante de $w = {{fenetre}}$ cycles, **moteur par moteur** pour qu'aucune fenêtre ne déborde sur le moteur précédent : la moyenne, l'écart-type et la pente locale des moindres carrés. Aux premiers cycles, la moyenne et l'écart-type utilisent les cycles disponibles et la pente vaut zéro tant que la fenêtre n'est pas complète. Avec l'indicateur de santé et le numéro de cycle, chaque cycle est décrit par {{n_features}} features.

### Indicateur de santé

Suivant Wang et al. [cite:wang2008], l'indicateur de santé est une combinaison linéaire des capteurs retenus standardisés $z_j$ :

$$\mathrm{HI}(t) = a_0 + \sum_j a_j\, z_j(t). $$ {#eq:hi}

Les coefficients sont estimés par moindres carrés avec une cible égale à un sur les {{hi_frac_sain}} % premiers cycles de chaque moteur d'entraînement (état sain) et à zéro sur les {{hi_frac_defaillant}} % derniers (état défaillant) ; les cycles intermédiaires ne servent pas à l'ajustement. L'indicateur brut est ensuite lissé par une moyenne glissante de {{fenetre}} cycles, moteur par moteur.

## Classification de l'état de santé (PDM-02, Eya) {#sec:classification}

Un cycle est étiqueté **critique** si le RUL réel est inférieur ou égal à {{rul_critique}} cycles, durée choisie comme fenêtre d'intervention pour planifier un remplacement. Deux classifieurs de la bibliothèque scikit-learn [cite:pedregosa2011] sont comparés sur les features du [@sec:hi] :

- un **gradient boosting** à histogrammes [cite:friedman2001,ke2017] ({{gb_iterations}} itérations, pas d'apprentissage {{gb_lr}}, {{gb_feuilles}} feuilles au plus par arbre), qui gère bien des features hétérogènes ;
- une **machine à vecteurs de support** à noyau gaussien [cite:cortes1995] ($C = {{svm_c}}$), dont les sorties sont calibrées en probabilités par la méthode de Platt [cite:platt1999]. Le coût d'apprentissage du SVM étant quadratique en nombre d'exemples, il est entraîné sur un sous-échantillon aléatoire de {{svm_echantillon}} cycles.

**Validation sans fuite.** Les cycles d'un même moteur sont fortement corrélés. Une validation croisée aléatoire placerait des cycles d'un même moteur à la fois dans l'apprentissage et dans la validation, ce qui surestimerait les performances. La validation croisée est donc faite **par groupes de moteurs** (GroupKFold, {{k_plis}} plis) : chaque moteur est entièrement dans l'apprentissage ou entièrement dans la validation. Le modèle de meilleure AUC sur le jeu de test sert ensuite à classer chaque moteur en service, selon la probabilité $p$ d'état critique à son dernier cycle : *critique* si $p \ge 0{,}5$, *surveillance* si $p \ge {{prob_surveillance}}$, *normal* sinon.

## Estimation du RUL par modèle de dégradation bayésien (RUL-01, Eya) {#sec:degradation}

### Modèle

L'indicateur de santé brut d'un moteur est modélisé par un polynôme de degré {{deg_degre}} du temps réduit $\tau = t/100$, à coefficients propres au moteur :

$$\mathrm{HI}(t) = \boldsymbol\phi(t)^\top \mathbf w + \varepsilon, \qquad \boldsymbol\phi(t) = (1, \tau, \tau^2)^\top, \qquad \varepsilon \sim \mathcal N(0, \sigma^2). $$ {#eq:degradation}

### Apprentissage sur la flotte : loi a priori

Le polynôme est ajusté par moindres carrés sur chaque moteur d'entraînement. La moyenne $\mathbf m_0$ et la covariance $\mathbf S_0$ des coefficients obtenus définissent la loi a priori $\mathbf w \sim \mathcal N(\mathbf m_0, \mathbf S_0)$, qui représente la variabilité de la flotte [cite:gebraeel2005]. La variance du bruit $\sigma^2$ est celle des résidus. Le **seuil de défaillance** est la valeur moyenne du HI ajusté au cycle de défaillance, et son écart-type sur la flotte mesure l'incertitude du seuil.

### Mise à jour bayésienne pour un moteur en service

Pour un moteur observé aux instants $t_1, \dots, t_n$, de matrice de régression $\boldsymbol\Phi$ et de mesures $\mathbf h$, le modèle étant gaussien et linéaire en $\mathbf w$, la loi a posteriori est gaussienne (conjugaison) :

$$\mathbf S_n^{-1} = \mathbf S_0^{-1} + \frac{\boldsymbol\Phi^\top \boldsymbol\Phi}{\sigma^2}, \qquad \mathbf m_n = \mathbf S_n \left(\mathbf S_0^{-1} \mathbf m_0 + \frac{\boldsymbol\Phi^\top \mathbf h}{\sigma^2}\right). $$ {#eq:posterior}

Au début de la vie, l'a priori de flotte domine ; quand les mesures s'accumulent, la trajectoire propre du moteur prend le dessus.

### Distribution du RUL

On tire {{n_tirages}} vecteurs de coefficients dans la loi a posteriori et, pour chacun, un seuil dans $\mathcal N(\bar s, \sigma_s^2)$. Chaque trajectoire moyenne est prolongée cycle par cycle sur un horizon de {{horizon}} cycles, et l'instant de premier passage sous le seuil donne un RUL. La médiane de ces RUL est la prédiction ; leurs quantiles donnent les intervalles de prédiction (P10–P90, et pour la calibration P25–P75 et P05–P95). Le bruit $\varepsilon$ n'est pas ajouté aux trajectoires : l'incertitude représentée est celle des coefficients et du seuil. Ce choix a une conséquence sur la largeur des intervalles, discutée au [@sec:limites].

## Estimation du RUL par réseau LSTM (RUL-02, Salma) {#sec:lstm}

### Données d'entrée et cible

Les {{n_retenus}} capteurs retenus sont normalisés entre zéro et un avec les minimums et maximums du jeu d'entraînement. Chaque exemple est une fenêtre de {{seq}} cycles consécutifs d'un même moteur ; la cible est le RUL au dernier cycle de la fenêtre. Une série plus courte que la fenêtre est complétée au début en répétant sa première ligne. Suivant une convention établie sur C-MAPSS [cite:heimes2008], la cible est **plafonnée** :

$$y = \min(\mathrm{RUL}, {{rul_cap}}), $$ {#eq:plafond}

car en début de vie la dégradation n'est pas observable et le RUL exact ne peut pas être appris.

### Architecture et apprentissage

Le réseau [cite:hochreiter1997,zheng2017] comprend {{lstm_couches}} couches LSTM de {{lstm_unites}} unités avec un dropout de {{lstm_dropout}}, puis une petite couche dense ReLU et une sortie linéaire. L'apprentissage minimise l'erreur quadratique moyenne avec l'optimiseur Adam [cite:kingma2015] (pas initial {{lstm_lr}}, lots de {{lstm_lot}} fenêtres, écrêtage de la norme du gradient), et le pas est réduit en cas de plateau. {{lstm_val_moteurs}} moteurs d'entraînement tirés au hasard sont réservés à la validation. L'**arrêt précoce** interrompt l'apprentissage après {{lstm_patience}} époques sans amélioration de l'erreur de validation (au plus {{lstm_epoques_max}} époques), et les poids de la meilleure époque sont conservés. La prédiction pour un moteur de test est la sortie au dernier cycle observé, bornée à zéro. Le réseau est implémenté avec PyTorch [cite:paszke2019].

**Reproductibilité.** L'entraînement du LSTM n'est pas exactement reproductible d'une machine à l'autre (calcul flottant sur processeur). Les résultats publiés correspondent au modèle sauvegardé, rechargé par défaut ; le réentraînement reste possible et sa variabilité est quantifiée au [@sec:reproductibilite].

## Conclusion {-}

Ce chapitre a détaillé les six méthodes de l'étude, leurs hypothèses, en particulier la censure non informative et les temps de réparation simulés, et leurs paramètres. Le chapitre suivant décrit le système logiciel qui les met en œuvre.
