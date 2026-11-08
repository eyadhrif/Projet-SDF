| Paramètre | Valeur | Module |
|---|---|---|
| Conversion temps | 1 cycle ≈ 2 h (1 vol) | fmds.py |
| Temps de réparation simulés | log-normale, médiane 16 h, σ = 0,6, graine 42 | fmds.py |
| Coûts relatifs | Cp = 1, Cc = 5 | fmds.py |
| Capteur constant | moins de 10 valeurs distinctes | features.py |
| Sélection des capteurs | \|tendance\| ≥ 0,5 | features.py |
| Fenêtre glissante (features, lissage du HI) | 10 cycles | features.py |
| Cible du HI | 1 sur les 10 % premiers cycles, 0 sur les 10 % derniers | features.py |
| Classe « critique » | RUL ≤ 30 cycles ; « surveillance » si P ≥ 0,2 | health.py |
| Modèle de dégradation | polynôme de degré 2, 1000 tirages, horizon 400 cycles | rul_degradation.py |
| LSTM | fenêtres de 30 cycles, cible plafonnée à 125, 2 couches de 64 | rul_lstm.py |
