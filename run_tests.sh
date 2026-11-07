#!/usr/bin/env bash
# Lance toute la suite de tests puis génère tests/RAPPORT_TESTS.md
#   ./run_tests.sh          tests rapides (pytest sans les tests lents) + dashboard (Playwright)
#   ./run_tests.sh --slow   suite complète, y compris réentraînements et run_all.py (~10 min)
cd "$(dirname "$0")"

if [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
else PY=python3; fi

MODE=rapide
MARK=(-m "not slow")
if [ "$1" = "--slow" ]; then MODE=complet; MARK=(); fi

echo "=== pytest (mode $MODE) ==="
"$PY" -m pytest "${MARK[@]}" -p no:cacheprovider --cov=backend/pipeline --cov=backend/api \
  --cov-report=term --cov-report=json:tests/couverture.json --junitxml=tests/junit_pytest.xml
RC_PY=$?

echo "=== Playwright (dashboard) ==="
(cd frontend && npx playwright test)
RC_PW=$?

"$PY" tests/generer_rapport.py --mode "$MODE"

if [ $RC_PY -ne 0 ] || [ $RC_PW -ne 0 ]; then exit 1; fi
echo "Tous les tests sont verts."
