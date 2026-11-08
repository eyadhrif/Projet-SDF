# Résumé {-}

:::resumes
## Résumé {-}

Ce rapport présente une étude de sûreté de fonctionnement et de maintenance prédictive menée sur le jeu de données public NASA C-MAPSS FD001, qui simule la dégradation de turboréacteurs jusqu'à la défaillance. L'analyse de fiabilité traite {{n_moteurs_test}} moteurs encore en service comme des durées censurées à droite et retient une loi de Weibull à trois paramètres (β = {{w3_beta}}, η = {{w3_eta}} cycles, γ = {{w3_gamma}} cycles), validée par le test de Kolmogorov-Smirnov : le MTTF vaut {{mttf}} cycles. Sous des hypothèses de réparation explicitement signalées, la disponibilité intrinsèque atteint {{dispo}} % et un remplacement préventif à {{t_opt_arrondi}} cycles réduit le coût par cycle de {{gain_preventif}} %. Une chaîne de maintenance prédictive construit un indicateur de santé à partir de {{n_retenus}} capteurs, détecte l'état critique avec une AUC de {{gb_auc}} et estime la durée de vie résiduelle avec un modèle de dégradation bayésien (RMSE {{deg_rmse}} cycles) et un réseau LSTM (RMSE {{lstm_rmse}} cycles). Les résultats sont restitués dans un tableau de bord web.

**Mots-clés :** fiabilité, censure à droite, loi de Weibull, disponibilité, maintenance prédictive, durée de vie résiduelle, LSTM.

## Abstract {-}

This report presents a dependability and predictive maintenance study of the public NASA C-MAPSS FD001 dataset, which simulates the run-to-failure degradation of turbofan engines. The reliability analysis treats {{n_moteurs_test}} engines still in service as right-censored lifetimes and retains a three-parameter Weibull distribution (β = {{w3_beta}}, η = {{w3_eta}} cycles, γ = {{w3_gamma}} cycles), accepted by the Kolmogorov-Smirnov test, with a mean time to failure of {{mttf}} cycles. Under explicitly stated repair assumptions, the inherent availability reaches {{dispo}} %, and an age replacement policy at {{t_opt_arrondi}} cycles cuts the cost per cycle by {{gain_preventif}} %. A predictive maintenance pipeline builds a health indicator from {{n_retenus}} sensors, detects the critical state with an AUC of {{gb_auc}}, and estimates the remaining useful life with a Bayesian degradation model (RMSE {{deg_rmse}} cycles) and an LSTM network (RMSE {{lstm_rmse}} cycles). The results are presented in a web dashboard.

**Keywords:** reliability, right censoring, Weibull distribution, availability, predictive maintenance, remaining useful life, LSTM.
:::

:::arabe
## ملخص {-}

يقدّم هذا التقرير دراسة في سلامة التشغيل والصيانة التنبّؤية أُجريت على مجموعة البيانات العمومية NASA C-MAPSS FD001، التي تحاكي تدهور المحرّكات التوربينية النفّاثة حتى العطل. يعالج تحليل الموثوقية {{n_moteurs_test}} محرّكًا ما زالت في الخدمة باعتبارها مُدَدًا مبتورة من اليمين، ويعتمد قانون فايبل ذا المعاملات الثلاثة الذي قَبِله اختبار كولموغوروف-سميرنوف، ويبلغ متوسّط مدّة التشغيل قبل العطل {{mttf}} دورة. ووفق فرضيات إصلاح مُصرَّح بها، تبلغ الإتاحة الذاتية {{dispo}} %، ويُخفّض الاستبدال الوقائي عند عمر {{t_opt_arrondi}} دورة كلفة الدورة بنسبة {{gain_preventif}} %. وتبني سلسلة الصيانة التنبّؤية مؤشّرًا للحالة الصحّية انطلاقًا من {{n_retenus}} حسّاسًا، وتكشف الحالة الحرجة بمساحة تحت المنحنى قدرها {{gb_auc}}، وتقدّر العمر المتبقّي بنموذج تدهور بايزي (جذر متوسّط مربّع الخطأ {{deg_rmse}} دورة) وبشبكة LSTM (جذر متوسّط مربّع الخطأ {{lstm_rmse}} دورة).

**الكلمات المفاتيح:** الموثوقية، البتر من اليمين، قانون فايبل، الإتاحة، الصيانة التنبّؤية، العمر المتبقّي.
:::
