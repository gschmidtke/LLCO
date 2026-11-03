"""Fetch reference data used by LLCO tools, at pinned commits, into tools/_ext/ (git-ignored).

AutoLispExt (Autodesk, Apache-2.0): extension/src/help/webHelpAbstraction.json, the index of
documented AutoLISP functions, used to tell built-in functions from estate code.
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "_ext", "AutoLispExt")
REPO, COMMIT, PATH = "https://github.com/Autodesk-AutoCAD/AutoLispExt", "74f59ee", "extension/src/help/webHelpAbstraction.json"

if not os.path.isdir(os.path.join(DEST, ".git")):
    subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", REPO, DEST], check=True)
subprocess.run(["git", "-C", DEST, "checkout", "--quiet", COMMIT, "--", PATH], check=True)
print(os.path.join(DEST, PATH))
