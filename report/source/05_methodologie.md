# Méthodologie {#sec:methodologie}

## Introduction {-}

Ce chapitre présente les méthodes de l'étude : la fiabilité, la maintenabilité et la disponibilité, l'indicateur de santé, la classification de l'état et les deux modèles de RUL. Les valeurs des paramètres sont regroupées au [@tab:hypotheses_parametres] (annexe A).

## Fiabilité {#sec:fiabilite}

### Estimation non paramétrique

Soient $t_1 < t_2 < \dots$ les instants de défaillance, $d_i$ le nombre de défaillances en $t_i$ et $n_i$ le nombre d'unités encore à risque juste avant $t_i$. L'estimateur KM [cite:kaplanmeier1958] est

$$\hat R(t) = \prod_{t_i \le t} \left(1 - \frac{d_i}{n_i}\right). $$ {#eq:km}

Une unité censurée sort de l'effectif à risque sans être comptée comme défaillance. L'IC à $95\,\%$ utilise la variance de Greenwood [cite:greenwood1926] sur l'échelle $\log(-\log \hat R)$. La censure est supposée non informative, ce que justifie le tirage indépendant des instants de troncature dans C-MAPSS [cite:saxena2008damage]. Le taux cumulé de Nelson-Aalen, lissé par un noyau d'Epanechnikov de {{na_largeur_noyau}} cycles, donne la forme de $\lambda(t)$ sans supposer de loi.

### Lois paramétriques

La loi de Weibull à trois paramètres [cite:weibull1951] s'écrit

$$R(t) = \exp\!\left[-\left(\frac{t-\gamma}{\eta}\right)^{\beta}\right] \text{ pour } t > \gamma, \qquad R(t) = 1 \text{ sinon}, $$ {#eq:weibull3}

avec $\beta$ la forme, $\eta$ l'échelle et $\gamma$ la position, durée sans défaillance garantie ; la loi 2P correspond à $\gamma = 0$. Par **MCO**, la méthode graphique du cours [cite:benhmida], les durées triées reçoivent les rangs de Bernard [cite:bernard1953] et la loi 2P se linéarise :

$$\hat F_i = \frac{i - 0{,}3}{n + 0{,}4}, \qquad \ln\!\big(-\ln(1-\hat F_i)\big) = \beta \ln t_i - \beta \ln \eta . $$ {#eq:bernard}

Une courbure du diagramme signale un $\gamma$ non nul. Par **MV**, la log-vraisemblance $\ell = \sum_i [\delta_i \ln f(t_i) + (1-\delta_i) \ln R(t_i)]$ est maximisée. La loi 2P est ajustée avec censure sur les {{n_unites}} unités (bibliothèque lifelines [cite:davidsonpilon2019]). Les quatre lois candidates, exponentielle, Weibull 2P, log-normale et Weibull 3P, sont comparées sur les {{n_defaillances}} durées de défaillance complètes : **la Weibull 3P retenue est donc ajustée sans les censures**, limite discutée au [@sec:limites]. L'adéquation est jugée par le test KS au seuil de $5\,\%$, et les lois sont comparées par $\mathrm{AIC} = 2k - 2\ell$ ; un écart inférieur à deux unités les rend équivalentes.

### Indicateurs dérivés

Pour la Weibull 3P, le MTTF et la durée $B_p$ valent

$$\mathrm{MTTF} = \gamma + \eta\, \Gamma\!\left(1 + \frac{1}{\beta}\right), \qquad B_p = \gamma + \eta \big(-\ln(1-p)\big)^{1/\beta}. $$ {#eq:mttf}

## Maintenabilité, disponibilité et remplacement préventif {#sec:fmds02}

C-MAPSS ne contient aucun temps de réparation : ils sont donc **simulés**, selon une loi log-normale de médiane {{ttr_mediane}} h et d'écart-type logarithmique {{ttr_sigma_sim}}, avec un cycle d'environ {{h_par_cycle}} h. Les résultats qui en dépendent illustrent la démarche du cours et ne décrivent pas une flotte réelle.

La loi log-normale est ré-estimée par MV sur l'échantillon simulé, ce qui donne $\mathrm{MTTR} = e^{\mu + \sigma^2/2}$. La disponibilité intrinsèque d'un moteur réparé après chaque défaillance est

$$A_\infty = \frac{\mathrm{MUT}}{\mathrm{MUT} + \mathrm{MDT}}, \qquad \mathrm{MUT} = \mathrm{MTTF}, \quad \mathrm{MDT} = \mathrm{MTTR}. $$ {#eq:dispo}

Selon la politique de Barlow et Proschan [cite:barlow1965], un moteur est remplacé à l'âge $T$ pour un coût $C_p$, alors qu'une défaillance en service coûte $C_c > C_p$. Le coût moyen par cycle est

$$C(T) = \frac{C_p\, R(T) + C_c\, \big(1 - R(T)\big)}{\displaystyle\int_0^T R(t)\, \mathrm{d}t}, \qquad C_\infty = \frac{C_c}{\mathrm{MTTF}} , $$ {#eq:cout}

où $C_\infty$ est le coût de la maintenance corrective seule. L'âge optimal $T^*$ minimise $C(T)$. Les coûts relatifs $C_p = {{cp}}$ et $C_c = {{cc}}$ sont une hypothèse d'illustration.

## Sélection des capteurs et indicateur de santé {#sec:hi}

Pour chaque capteur non constant, deux scores inspirés de Coble et Hines [cite:coble2009] sont calculés : la **tendance** $\rho$, corrélation moyenne avec le numéro de cycle, et la **monotonie** de la série lissée,

$$\mathrm{Mon} = \frac{|N^{+} - N^{-}|}{n-1}, $$ {#eq:monotonie}

où $N^{+}$ et $N^{-}$ sont les nombres de variations positives et négatives et $n$ la longueur de la série. Un capteur est retenu si $|\rho| \ge {{seuil_tendance}}$. Pour chaque capteur retenu, la moyenne, l'écart-type et la pente sont calculés sur une fenêtre glissante de {{fenetre}} cycles, moteur par moteur ; avec le HI et le numéro de cycle, chaque cycle est décrit par {{n_features}} variables.

Suivant Wang et al. [cite:wang2008], le HI est une combinaison linéaire des capteurs standardisés $z_j$ :

$$\mathrm{HI}(t) = a_0 + \sum_j a_j\, z_j(t), $$ {#eq:hi}

ajustée par moindres carrés vers une cible égale à un sur les {{hi_frac_sain}} % premiers cycles de chaque moteur et à zéro sur les {{hi_frac_defaillant}} % derniers, puis lissée sur {{fenetre}} cycles.

## Classification de l'état de santé {#sec:classification}

Un cycle est **critique** si sa RUL réelle est d'au plus {{rul_critique}} cycles. Deux classifieurs de scikit-learn [cite:pedregosa2011] sont comparés : un gradient boosting à histogrammes [cite:friedman2001,ke2017] et un SVM à noyau gaussien [cite:cortes1995] calibré par la méthode de Platt [cite:platt1999]. Les cycles d'un même moteur étant corrélés, la validation croisée se fait **par groupes de moteurs** (GroupKFold, {{k_plis}} plis), sans fuite entre apprentissage et validation. Au dernier cycle observé, chaque moteur est classé *critique* si sa probabilité dépasse $0{,}5$, *surveillance* si elle dépasse {{prob_surveillance}}, *normal* sinon.

## RUL par modèle de dégradation bayésien {#sec:degradation}

Le HI d'un moteur est modélisé par un polynôme de degré {{deg_degre}} du temps réduit $\tau = t/100$, à coefficients propres au moteur :

$$\mathrm{HI}(t) = \boldsymbol\phi(t)^\top \mathbf w + \varepsilon, \qquad \boldsymbol\phi(t) = (1, \tau, \tau^2)^\top, \qquad \varepsilon \sim \mathcal N(0, \sigma^2). $$ {#eq:degradation}

Les ajustements sur les moteurs d'entraînement donnent l'a priori de flotte $\mathbf w \sim \mathcal N(\mathbf m_0, \mathbf S_0)$ [cite:gebraeel2005], la variance $\sigma^2$ des résidus et un seuil de défaillance $\mathcal N(\bar s, \sigma_s^2)$. Pour un moteur observé, de matrice de régression $\boldsymbol\Phi$ et de mesures $\mathbf h$, la loi a posteriori est gaussienne :

$$\mathbf S_n^{-1} = \mathbf S_0^{-1} + \frac{\boldsymbol\Phi^\top \boldsymbol\Phi}{\sigma^2}, \qquad \mathbf m_n = \mathbf S_n \left(\mathbf S_0^{-1} \mathbf m_0 + \frac{\boldsymbol\Phi^\top \mathbf h}{\sigma^2}\right). $$ {#eq:posterior}

On tire {{n_tirages}} couples de coefficients et de seuils ; le premier passage de chaque trajectoire sous le seuil donne une RUL. La médiane est la prédiction, et les quantiles donnent les intervalles P25–P75, P10–P90 et P05–P95. Le bruit $\varepsilon$ n'est pas propagé dans les trajectoires.

## RUL par réseau LSTM {#sec:lstm}

Les {{n_retenus}} capteurs retenus sont normalisés entre zéro et un, et chaque exemple est une fenêtre de {{seq}} cycles d'un même moteur. Suivant Heimes [cite:heimes2008], la cible est plafonnée, $y = \min(\mathrm{RUL}, {{rul_cap}})$, car la dégradation n'est pas observable en début de vie. Le réseau [cite:hochreiter1997,zheng2017] comprend {{lstm_couches}} couches LSTM de {{lstm_unites}} unités, une couche dense et une sortie linéaire ; il est entraîné avec Adam [cite:kingma2015] sous PyTorch [cite:paszke2019], avec un arrêt précoce sur {{lstm_val_moteurs}} moteurs de validation.

## Conclusion {-}

Ce chapitre a présenté les méthodes et leurs hypothèses, en particulier la censure non informative et les temps de réparation simulés. Le chapitre suivant les évalue sur les données de test et présente leur restitution.
