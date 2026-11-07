@echo off
rem Lance toute la suite de tests puis génère tests\RAPPORT_TESTS.md
rem   run_tests.bat          tests rapides (pytest sans les tests lents) + dashboard (Playwright)
rem   run_tests.bat --slow   suite complète, y compris réentraînements et run_all.py (~10 min)
setlocal
chcp 65001 > nul
cd /d "%~dp0"

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

set "MODE=rapide"
if /I "%~1"=="--slow" set "MODE=complet"

echo === pytest (mode %MODE%) ===
if "%MODE%"=="complet" (
  "%PY%" -m pytest -p no:cacheprovider --cov=backend/pipeline --cov=backend/api --cov-report=term --cov-report=json:tests/couverture.json --junitxml=tests/junit_pytest.xml
) else (
  "%PY%" -m pytest -m "not slow" -p no:cacheprovider --cov=backend/pipeline --cov=backend/api --cov-report=term --cov-report=json:tests/couverture.json --junitxml=tests/junit_pytest.xml
)
set "RC_PY=%ERRORLEVEL%"

echo === Playwright (dashboard) ===
pushd frontend
call npx playwright test
set "RC_PW=%ERRORLEVEL%"
popd

"%PY%" tests\generer_rapport.py --mode %MODE%

if not "%RC_PY%"=="0" exit /b 1
if not "%RC_PW%"=="0" exit /b 1
echo Tous les tests sont verts.
exit /b 0
