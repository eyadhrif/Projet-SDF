"""Environnement : dépendances déclarées, versions minimales et fichier de versions figées (§0.10)."""
import sys
from importlib.metadata import version, PackageNotFoundError

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from conftest import BACKEND


def _reqs(name):
    out = []
    for line in (BACKEND / name).read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-r"):
            out.append(Requirement(line))
    return out


REQS = _reqs("requirements.txt")


def test_python_au_moins_3_10():
    assert sys.version_info >= (3, 10)


def test_minimums_exiges_par_le_code_sont_declares():
    spec = {canonicalize_name(r.name): r.specifier for r in REQS}
    assert "2.0" in spec["numpy"] and "1.26" not in spec["numpy"]      # np.trapezoid
    assert "2.2" in spec["pandas"] and "2.1" not in spec["pandas"]     # include_groups


@pytest.mark.parametrize("req", REQS, ids=lambda r: r.name)
def test_version_installee_satisfait_requirements(req):
    try:
        v = version(req.name)
    except PackageNotFoundError:
        pytest.fail(f"{req.name} n'est pas installé")
    assert req.specifier.contains(v, prereleases=True), f"{req.name} {v} ne satisfait pas {req.specifier}"


def test_lock_fige_toutes_les_dependances():
    lock = {canonicalize_name(r.name): r for r in _reqs("requirements-lock.txt")}
    for r in REQS + _reqs("requirements-dev.txt"):
        name = canonicalize_name(r.name)
        assert name in lock, f"{r.name} absent de requirements-lock.txt"
        spec = str(lock[name].specifier)
        assert spec.startswith("=="), f"{r.name} n'est pas figé ({spec})"
        assert r.specifier.contains(spec[2:], prereleases=True), f"lock {r.name}{spec} contredit {r.specifier}"
