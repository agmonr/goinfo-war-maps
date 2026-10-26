#!/usr/bin/env python3
"""Every war page the generator writes is measured (the owner 10-25, rule 13): build the war stage, every .html must carry gtag + ga-guard + eventlog; a page without them is refused."""
import subprocess, sys, tempfile
from pathlib import Path

T = Path(__file__).resolve().parent
sys.path.insert(0, str(T))
import ga_inject  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    r = subprocess.run([sys.executable, str(T / "war_build.py"), "--stage", d], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    ok = subprocess.run([sys.executable, str(T / "war_measure_check.py"), d], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    pages = sorted((Path(d) / "war").rglob("*.html"))
    assert len(pages) >= 5, len(pages)
    victim = pages[0]
    victim.write_text(victim.read_text(encoding="utf-8").replace("googletagmanager.com/gtag", "example.invalid/x"), encoding="utf-8")
    bad = subprocess.run([sys.executable, str(T / "war_measure_check.py"), d], capture_output=True, text=True)
    assert bad.returncode == 1 and "UNMEASURED" in bad.stderr, bad
# the inline host-fallback sits between the shared guard and the gtag loader and decides like ga-guard: LAN twin / preview host and an insider are disabled, goinfo.co.il is not
import re, shutil
with tempfile.TemporaryDirectory() as d:
    subprocess.run([sys.executable, str(T / "war_build.py"), "--stage", d], check=True, capture_output=True)
    for pg in sorted((Path(d) / "war").rglob("*.html")):
        h = pg.read_text(encoding="utf-8")
        a, b, c = h.find("/src/ga-guard.js"), h.find("host-fallback"), h.find("googletagmanager.com/gtag/js")
        assert 0 < a < b < c, (pg, a, b, c)
    snippet = re.search(r"<script>/\* host-fallback.*?</script>", h, re.S).group(0)[len("<script>"):-len("</script>")]
    node = shutil.which("node")
    if node:
        def run(host, insider):
            js = "var window={};var location={hostname:%r};var localStorage={getItem:function(k){return k==='gi-insider'&&%s?'1':null}};%s;console.log(!!window['ga-disable-G-HMYNE9NT2K'])" % (host, "true" if insider else "false", snippet)
            return subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout.strip()
        assert run("localhost", False) == "true" and run("localhost", False) == "true" and run("x.workers.dev", False) == "true"
        assert run("goinfo.co.il", True) == "true" and run("goinfo.co.il", False) == "false" and run("trees.goinfo.co.il", False) == "false"
        assert run("evilgoinfo.co.il", False) == "true"
    # a stage without the fallback is refused
    h2 = h.replace("host-fallback", "x")
    (Path(d) / "war" / "x_nofallback.html").write_text(re.sub(r"!/\(\^\|\\\.\)goinfo[^;]*?hostname\)", "false", h2, count=1), encoding="utf-8")
    bad = subprocess.run([sys.executable, str(T / "war_measure_check.py"), d], capture_output=True, text=True)
    assert bad.returncode == 1 and "x_nofallback" in bad.stderr, bad.stderr
assert not ga_inject.measured("<html><head></head></html>") and ga_inject.measured(ga_inject.ensure("<html><head></head></html>"))
print("ok: all war pages measured; an unmeasured one is refused")
