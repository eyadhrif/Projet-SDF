# Protocole expérimental et métriques {#sec:protocole}

## Découpages des données et validation {#sec:decoupages}

Le découpage officiel de FD001 est respecté : les modèles sont appris sur les {{n_moteurs_train}} moteurs d'entraînement et évalués sur les {{n_moteurs_test}} moteurs de test, jamais vus pendant l'apprentissage. Les choix propres à chaque partie sont les suivants :

- **fiabilité** : population de {{n_unites}} unités, avec {{n_defaillances}} défaillances et {{n_censures}} censures à droite ([@sec:donnees-censure]) ; le RUL réel des moteurs de test n'est pas utilisé ;
- **classification** : validation croisée par groupes de moteurs ({{k_plis}} plis) sur l'entraînement, puis évaluation sur **tous les cycles** des moteurs de test ;
- **RUL** : évaluation au **dernier cycle observé** de chaque moteur de test, comme dans le challenge PHM [cite:saxena2008damage] ; le LSTM réserve {{lstm_val_moteurs}} moteurs d'entraînement à l'arrêt précoce.

## Métriques {#sec:metriques}

### Fiabilité

Le test de Kolmogorov-Smirnov accepte une loi si sa *p*-valeur dépasse $\alpha = 5\,\%$. L'AIC compare les lois entre elles, et le coefficient $R^2$ mesure la linéarité du diagramme de Weibull ([@sec:fiabilite]).

### Classification

Avec $VP$, $FP$, $VN$ et $FN$ les vrais et faux positifs et négatifs (la classe positive étant l'état critique), on utilise :

$$\text{précision} = \frac{VP}{VP + FP}, \qquad \text{rappel} = \frac{VP}{VP + FN}, \qquad F_1 = \frac{2\,\text{précision} \cdot \text{rappel}}{\text{précision} + \text{rappel}}. $$ {#eq:classif}

En maintenance, le **rappel** est la métrique la plus importante, car une défaillance manquée coûte bien plus cher qu'une inspection inutile. L'aire sous la courbe ROC (AUC) [cite:hanley1982] mesure la capacité à classer un cycle critique au-dessus d'un cycle normal, indépendamment du seuil de décision.

### Durée de vie résiduelle

L'erreur d'un moteur est $e_i = \widehat{\mathrm{RUL}}_i - \mathrm{RUL}_i$ : une erreur **positive** est une prédiction **tardive**, la plus dangereuse puisqu'elle annonce plus de vie qu'il n'en reste. Sur les $N$ moteurs de test :

$$\mathrm{RMSE} = \sqrt{\frac1N \sum_i e_i^2}, \qquad \mathrm{MAE} = \frac1N \sum_i |e_i|, \qquad \text{biais} = \frac1N \sum_i e_i . $$ {#eq:rmse}

Le **score NASA** [cite:saxena2008damage] pénalise exponentiellement les erreurs, et davantage les prédictions tardives :

$$S = \sum_i s_i, \qquad s_i = \begin{cases} e^{-e_i/13} - 1 & e_i < 0 \\ e^{e_i/10} - 1 & e_i \ge 0 \end{cases}. $$ {#eq:score}

Pour le modèle de dégradation, la qualité de l'incertitude est mesurée par la **couverture empirique** : la proportion de moteurs dont le RUL réel tombe dans l'intervalle de prédiction. Un intervalle bien calibré de niveau nominal $q$ couvre le RUL réel dans une proportion proche de $q$ ; une couverture inférieure signale une incertitude sous-estimée. Trois niveaux sont évalués : P25–P75, P10–P90 et P05–P95.
