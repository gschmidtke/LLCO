"""Fetch the LLCO sample corpus at the pinned commits listed in corpus/MANIFEST.json.

Sources land in corpus/_sources/<owner>__<repo>/ (git-ignored). They are data: this script
clones them and checks out the pinned commit; it never runs anything from them.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
manifest = json.load(open(os.path.join(ROOT, "corpus", "MANIFEST.json"), encoding="utf-8"))
dest_root = os.path.join(ROOT, "corpus", "_sources")
os.makedirs(dest_root, exist_ok=True)

for src in manifest["sources"]:
    dest = os.path.join(dest_root, src["local_dir"])
    if not os.path.isdir(os.path.join(dest, ".git")):
        subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", src["repo"], dest], check=True)
    subprocess.run(["git", "-C", dest, "fetch", "--quiet", "--depth", "1", "origin", src["commit"]], check=False)
    subprocess.run(["git", "-C", dest, "checkout", "--quiet", src["commit"]], check=True)
    print(f'{src["local_dir"]:40} {src["commit"][:7]}  {src["licence"]}')
