"""LLCO step 1 (prototype): static inventory of AutoLISP sources.

Reads text only; executes nothing. Usage:
    python tools/llco_scan.py [sources_dir] [output.json]
Defaults: corpus/_sources and results/latest-static-inventory.json.
Counts are regex-based on comment-stripped text: a first triage, not a parser.
"""
import os, re, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'corpus', '_sources')
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'results', 'latest-static-inventory.json')
EXT = {'.lsp':'lisp','.dcl':'dcl','.fas':'compiled','.vlx':'compiled','.mnl':'menu-lisp','.cuix':'menu','.cui':'menu','.mnu':'menu',
       '.csv':'data','.xls':'data','.xlsx':'data','.txt':'text','.ini':'data','.dat':'data','.dwg':'drawing','.dwt':'template','.dxf':'drawing','.scr':'script'}
PAT = {
 'commands':      r'\(\s*defun\s+c:([\w\-\*\.]+)',
 'functions':     r'\(\s*defun\s+(?!c:)([\w\-\*\.:]+)',
 'com_vla':       r'\(\s*vlax?-[\w\-]+',
 'command_call':  r'\(\s*(?:vl-cmdf|command|command-s)\b',
 'dcl':           r'\(\s*(?:load_dialog|new_dialog)\b',
 'file_io':       r'\(\s*(?:open|read-line|write-line|findfile|getfiled)\b',
 'reactors':      r'\(\s*vlr-[\w\-]+',
 'load_chain':    r'\(\s*(?:load|autoload|vl-load-all)\b',
 'registry_env':  r'\(\s*(?:vl-registry-read|vl-registry-write|getenv|setenv)\b',
 'user_input':    r'\(\s*(?:getpoint|getdist|getstring|getkword|getreal|getint|getcorner|getangle|entsel|nentsel)\b',
 'selection':     r'\(\s*ssget\b',
 'entity_create': r'\(\s*(?:entmake|entmakex)\b',
 'entity_modify': r'\(\s*entmod\b',
 'sysvars':       r'\(\s*(?:setvar|getvar)\b',
}
rx = {k: re.compile(v, re.I) for k, v in PAT.items()}
repos = {}
for repo in sorted(os.listdir(root)):
    rp = os.path.join(root, repo)
    if not os.path.isdir(rp): continue
    files = collections.Counter(); lic = None; stats = collections.Counter(); cmds = []; lines = 0; per_file = []
    for dp, dn, fn in os.walk(rp):
        dn[:] = [d for d in dn if d != '.git']
        for f in fn:
            ext = os.path.splitext(f)[1].lower(); kind = EXT.get(ext)
            if f.upper().startswith(('LICENSE','LICENCE','COPYING')): lic = f
            if kind: files[kind] += 1
            if ext == '.lsp':
                t = open(os.path.join(dp, f), encoding='utf-8', errors='replace').read()
                t = re.sub(r';[^\n]*', '', t)  # strip comments
                n = t.count('\n') + 1; lines += n
                fstats = {k: len(r.findall(t)) for k, r in rx.items()}
                for k, v in fstats.items(): stats[k] += v
                cmds += rx['commands'].findall(t)
                per_file.append({'file': os.path.relpath(os.path.join(dp, f), rp), 'lines': n, **{k: v for k, v in fstats.items() if v}})
    repos[repo] = {'licence_file': lic, 'files': dict(files), 'lisp_lines': lines, 'commands': len(cmds), 'signals': dict(stats), 'per_file': per_file}
json.dump(repos, open(out_path, 'w'), indent=1)
hdr = ['repo','lic','.lsp','dcl','comp','lines','cmds','COM','command','DCL','fileIO','react','load','input','entmake']
print('\t'.join(hdr))
for r, d in repos.items():
    s = d['signals']; f = d['files']
    print('\t'.join(map(str, [r.split('__')[1][:22], (d['licence_file'] or '-')[:8], f.get('lisp',0), f.get('dcl',0), f.get('compiled',0), d['lisp_lines'], d['commands'],
        s.get('com_vla',0), s.get('command_call',0), s.get('dcl',0), s.get('file_io',0), s.get('reactors',0), s.get('load_chain',0), s.get('user_input',0), s.get('entity_create',0)])))
