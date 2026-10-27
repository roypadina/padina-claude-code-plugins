#!/usr/bin/env python3
"""obsidian-vault-manager helper. Python 3 stdlib only (git and grep as external tools).

  vault.py <command> [--vault DIR] ...
  DIR defaults to the nearest ancestor of cwd holding .obsidian/ or _Vault/, else cwd.

Commands
  init                      create _Vault/ (config, Vault Structure.md, subjects.json) + Index.md; no review marker
  tree [--depth N]          folder tree with note counts (structure only, no bodies)
  changes [--all]           what changed since the last review marker: git diff + status, or snapshot diff
  index                     regenerate Index.md + _Vault/Index/… (subjects from _Vault/subjects.json; big folders split)
  subject set REL TEXT      one-line subject for a note (REL = path without .md) or folder (REL ends with /)
  subject missing           notes that have no subject from any source
  refs scan [--path REL]    references to vault paths in consumer roots + in-vault links; stale refs, broken links
  refs scan --bare OLD [--anywhere]        bare (vault-relative) mentions of OLD outside the vault, each with a verdict
  refs rewrite OLD NEW [--apply]           rewrite OLD -> NEW: consumers (full paths), in-vault links + path text, config, subjects
  refs rewrite OLD NEW --bare [--apply --only 1,3|all]   supervised rewrite of bare mentions, by hit id
  move OLD NEW              move a note/folder (git mv when tracked, case-only renames ok); fixes links, text, config, subjects
  check                     drift: folders missing from the Folder map or still "(describe: …)", writers whose
                            source/paths are gone, listed paths their Source never mentions
  mark                      write last_review_sha/date into Vault Structure.md (+ snapshot.json when not git)
  selfcheck                 scripted test in a temp vault

Config (_Vault/vault-manager.json): consumers.roots (rewritable), consumers.report_only (listed, never written),
consumers.exclude_dirs, consumers.needles (how the vault is named outside: default `<parent>/<name>` + `~/<name>`;
a copy of the vault with the same config scans for the original's name), index.collapse/depth/split_kb, ignore.

Never touches .git, .obsidian or any dot-folder; writes inside the vault only under _Vault/, Index.md and —
for moves/rewrites — the notes' links and path text; outside the vault only via `refs rewrite --apply`.
"""
import argparse, datetime, glob, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse

HOME = os.path.expanduser('~')
VDIR = '_Vault'
CONFIG = f'{VDIR}/vault-manager.json'
STRUCTURE = f'{VDIR}/Vault Structure.md'
SUBJECTS = f'{VDIR}/subjects.json'
SNAPSHOT = f'{VDIR}/snapshot.json'
INDEX = 'Index.md'
INDEX_DIR = f'{VDIR}/Index'
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'Vault Structure.md')
BEGIN, END = '<!-- vault:index:begin -->', '<!-- vault:index:end -->'
DEFAULT_CONFIG = {
    'ignore': [INDEX, INDEX_DIR, SNAPSHOT],
    'index': {'collapse': [], 'depth': 2, 'split_kb': 20},
    'consumers': {'roots': [], 'report_only': [], 'needles': [],
                  'exclude_dirs': ['.git', 'node_modules', '.venv', '__pycache__', '.build', 'DerivedData', 'dist', 'worktrees']},
}
WIKI = re.compile(r'\[\[([^\]|#]+)(#[^\]|]*)?(\|[^\]]*)?\]\]')
MDLINK = re.compile(r'\]\(([^)\s]+?\.md)(#[^)]*)?\)')
SCHEME = re.compile(r'[a-zA-Z][a-zA-Z0-9+.-]*:')  # http:, mailto:, obsidian: … — not vault paths
PATH_END = r'(?=$|[/`"\'\s)\]|,;:>*])'
TODAY = datetime.date.today().isoformat()


# ---------- basics ----------
def pj(*parts):
    return '/'.join(p for p in parts if p)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def find_vault(arg):
    if arg:
        d = os.path.abspath(os.path.expanduser(arg))
    else:
        d = p = os.getcwd()
        while True:
            if os.path.isdir(os.path.join(p, '.obsidian')) or os.path.isdir(os.path.join(p, VDIR)):
                d = p
                break
            if os.path.dirname(p) == p:
                break
            p = os.path.dirname(p)
    if not os.path.isdir(d):
        sys.exit(f'not a directory: {d}')
    return d.rstrip('/')


def load_config(v):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    p = os.path.join(v, CONFIG)
    if os.path.exists(p):
        for k, val in json.loads(read(p)).items():
            if isinstance(val, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(val)
            else:
                cfg[k] = val
    return cfg


def ignored(rel, cfg):
    if any(part.startswith('.') for part in rel.split('/')):
        return True
    return any(rel == i or rel.startswith(i.rstrip('/') + '/') for i in cfg['ignore'])


def collapsed(rel, cfg):
    return any(rel.startswith(c.rstrip('/') + '/') for c in cfg['index']['collapse'])


def walk(v, cfg):
    """All non-ignored files, vault-relative, sorted."""
    out = []
    for root, dirs, files in os.walk(v):
        rr = os.path.relpath(root, v)
        rr = '' if rr == '.' else rr
        dirs[:] = sorted(d for d in dirs if not ignored(pj(rr, d), cfg))
        out += [pj(rr, f) for f in sorted(files) if not ignored(pj(rr, f), cfg)]
    return out


def notes(v, cfg):
    return [r for r in walk(v, cfg) if r.endswith('.md')]


def head(v, rel, n=60):
    lines = []
    with open(os.path.join(v, rel), encoding='utf-8', errors='replace') as f:
        for i, l in enumerate(f):
            if i >= n:
                break
            lines.append(l.rstrip('\n'))
    return lines


def frontmatter(lines):
    """Minimal YAML: `key: value`, `key: [a, b]`, block lists. Returns (dict, body_lines)."""
    if not lines or lines[0].strip() != '---':
        return {}, lines
    end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == '---'), None)
    if end is None:
        return {}, lines
    fm, key = {}, None
    for l in lines[1:end]:
        m = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', l)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                fm[key] = [x.strip().strip('"\'') for x in val[1:-1].split(',') if x.strip()]
            else:
                fm[key] = [] if val == '' else val.strip('"\'')
        elif key and isinstance(fm.get(key), list) and re.match(r'^\s*-\s+', l):
            fm[key].append(re.sub(r'^\s*-\s+', '', l).strip().strip('"\''))
    return fm, lines[end + 1:]


def clean_line(s, n=110):
    s = re.sub(r'^#+\s*', '', s.strip())
    s = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = s.replace('**', '').replace('__', '').replace('|', '\\|')
    return s if len(s) <= n else s[:n - 1] + '…'


LINK = re.compile(r'\[\[[^\]]*\]\]|\[[^\]]*\]\([^)]*\)')


def auto_subject(fm, body, title=''):
    """frontmatter `description`, else the first prose line: not a heading repeating the title, not a link-only
    navigation line (`Up: [[hub]] · [[index]]`)."""
    if isinstance(fm.get('description'), str) and fm['description']:
        return clean_line(fm['description'])
    title = re.sub(r'^\d+[.\s-]*', '', title).casefold()  # `00 Hub` and `# Hub` are the same title
    for l in body:
        t = l.strip()
        if not t or t.startswith(('<!--', '|', '---', '![', '```', '%%')):
            continue
        if t.startswith('#') and re.sub(r'^\d+[.\s-]*', '', clean_line(t)).casefold() == title:
            continue
        if LINK.search(t) and len(re.findall(r'[^\W\d_]{2,}', LINK.sub('', t))) < 3:
            continue
        return clean_line(t)
    return ''


def load_subjects(v):
    p = os.path.join(v, SUBJECTS)
    return json.loads(read(p)) if os.path.exists(p) else {}


def save_subjects(v, s):
    write(os.path.join(v, SUBJECTS), json.dumps(dict(sorted(s.items())), indent=1, ensure_ascii=False) + '\n')


def git(v, *a):
    r = subprocess.run(['git', '-C', v, '-c', 'core.quotepath=false', *a], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def is_git(v):
    return (git(v, 'rev-parse', '--is-inside-work-tree') or '').strip() == 'true'


def set_frontmatter(path, updates):
    txt = read(path) if os.path.exists(path) else ''
    lines = txt.split('\n')
    if lines and lines[0].strip() == '---' and '---' in [l.strip() for l in lines[1:]]:
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == '---')
        for k, val in updates.items():
            i = next((i for i in range(1, end) if lines[i].startswith(k + ':')), None)
            if i is None:
                lines.insert(end, f'{k}: {val}')
                end += 1
            else:
                lines[i] = f'{k}: {val}'
    else:
        lines = ['---'] + [f'{k}: {val}' for k, val in updates.items()] + ['---'] + lines
    write(path, '\n'.join(lines))


def short(f):
    """Collapse plugin-cache version dirs so one plugin shows once."""
    return re.sub(r'(/plugins/cache/[^/]+/[^/]+/)[^/]+/', r'\1<ver>/', f)


# ---------- tree ----------
def folder_stats(v, cfg):
    """{folder_rel: [direct_notes, total_notes, other_files_total]} for every folder ('' = root)."""
    st = {'': [0, 0, 0]}
    for rel in walk(v, cfg):
        d = os.path.dirname(rel)
        st.setdefault(d, [0, 0, 0])
        if rel.endswith('.md'):
            st[d][0] += 1
        parts = d.split('/') if d else []
        for i in range(len(parts) + 1):
            anc = '/'.join(parts[:i])
            st.setdefault(anc, [0, 0, 0])
            st[anc][1 if rel.endswith('.md') else 2] += 1
    for d in list(st):  # make sure empty intermediate folders exist in the map
        parts = d.split('/') if d else []
        for i in range(len(parts)):
            st.setdefault('/'.join(parts[:i]), [0, 0, 0])
    return st


def cmd_tree(v, cfg, a):
    st = folder_stats(v, cfg)
    print(f'{os.path.basename(v)}/ — {st[""][1]} notes, {st[""][2]} other files')
    for d in sorted(k for k in st if k):
        depth = d.count('/') + 1
        if depth > a.depth:
            continue
        direct, total, other = st[d]
        extra = f', {other} files' if other else ''
        print(f'{"  " * depth}{d.split("/")[-1]}/  ({total} notes{"" if total == direct else f", {direct} direct"}{extra})')


# ---------- index ----------
def write_marked(path, generated, header):
    old = read(path) if os.path.exists(path) else None
    if old and BEGIN in old and END in old:
        pre, rest = old.split(BEGIN, 1)
        post = rest.split(END, 1)[1]
        new = f'{pre}{BEGIN}\n{generated}\n{END}{post}'
    else:
        new = f'{header}{BEGIN}\n{generated}\n{END}\n'
    if new != old:
        write(path, new)
        return True
    return False


def wl(rel, label=None):
    """Wikilink for a table cell (pipe escaped)."""
    return f'[[{rel}\\|{label or os.path.basename(rel)}]]'


def cmd_index(v, cfg, a):
    subj = load_subjects(v)
    collapse = [c.rstrip('/') for c in cfg['index']['collapse']]
    depth, limit = cfg['index']['depth'], cfg['index'].get('split_kb', 20) * 1024
    st = folder_stats(v, cfg)
    rows = {}  # note rel -> (tags, subject)
    for rel in notes(v, cfg):
        if collapsed(rel, cfg):
            continue
        fm, body = frontmatter(head(v, rel))
        tags = fm.get('tags', [])
        tags = ', '.join(tags) if isinstance(tags, list) else str(tags)
        rows[rel] = (tags.replace('|', '\\|'), subj.get(rel[:-3]) or auto_subject(fm, body, os.path.basename(rel)[:-3]))
    tops = sorted(d for d in st if d and '/' not in d and d != VDIR)
    stamp = f'Generated {TODAY} by `vault.py index`. Subjects: `{SUBJECTS}`. Structure and rules: [[{STRUCTURE[:-3]}]].'
    TH = ['| Note | Tags | Subject |', '|---|---|---|']
    files = {}  # folder -> lines of its own index file

    def render(folder):
        """Markdown for a folder's subtree; the largest children get their own file while the result is over split_kb."""
        direct = [r for r in rows if os.path.dirname(r) == folder]
        children = sorted(d for d in st if d and os.path.dirname(d) == folder)
        out = [f'### {folder}/' + (' (direct notes)' if children else ''), '', *TH] + \
              [f'| {wl(r[:-3])} | {rows[r][0]} | {rows[r][1]} |' for r in direct] + [''] if direct else []
        secs = []
        for c in children:
            if c in collapse:
                lines = [f'### {c}/', '', '| Folder | Notes | Subject |', '|---|---|---|',
                         f'| `{c}/` | {st[c][1]} | not listed (machine-written)' + (f'. {subj[c + "/"]}' if subj.get(c + '/') else '') + ' |', '']
            else:
                lines = render(c)
            secs.append([c, lines, len('\n'.join(lines).encode('utf-8'))])  # bytes: non-Latin names are multibyte
        total = len('\n'.join(out).encode('utf-8')) + sum(s[2] for s in secs)
        for s in sorted(secs, key=lambda s: -s[2]):
            if total <= limit:
                break
            if s[0] in collapse or not s[1]:
                continue
            files[s[0]] = s[1]
            s[1] = [f'### {s[0]}/', '', f'→ [[{pj(INDEX_DIR, s[0])}\\|{s[0]}/ index]] — {st[s[0]][1]} notes', '']
            total -= s[2] - len('\n'.join(s[1]).encode('utf-8'))
        return out + [l for s in secs for l in s[1]]

    for top in tops:
        files[top] = render(top)
    changed = []
    for folder, lines in files.items():
        hdr = f'---\ntype: vault-index\ntags: [vault-index]\n---\n\n# Index — {folder}\n\nDo not edit between the markers; set subjects with `vault.py subject set`.\n\n'
        if write_marked(os.path.join(v, INDEX_DIR, folder + '.md'), '\n'.join([stamp, ''] + lines).rstrip('\n'), hdr):
            changed.append(pj(INDEX_DIR, folder + '.md'))
    for stale in glob.glob(os.path.join(v, INDEX_DIR, '**', '*.md'), recursive=True):
        if os.path.relpath(stale, os.path.join(v, INDEX_DIR))[:-3] not in files:
            os.remove(stale)
            changed.append('removed ' + os.path.relpath(stale, v))
    for d, dirs, fs in os.walk(os.path.join(v, INDEX_DIR), topdown=False):
        if d != os.path.join(v, INDEX_DIR) and not os.listdir(d):
            os.rmdir(d)
    root = [f'Structure and rules: [[{STRUCTURE[:-3]}]] · {st[""][1]} notes · generated {TODAY} by `vault.py index`.', '',
            '## Folders', '', '| Folder | Notes | Subject |', '|---|---|---|']
    if os.path.exists(os.path.join(v, STRUCTURE)):
        root.append(f'| [[{STRUCTURE[:-3]}\\|{VDIR}/]] | {st.get(VDIR, [0, 0])[1]} | vault structure, rules, writers registry, generated indexes |')
    for top in tops:
        root.append(f'| [[{pj(INDEX_DIR, top)}\\|{top}/]] | {st[top][1]} | {subj.get(top + "/", "")} |')
        if top in collapse:
            continue
        for d in sorted(k for k in st if k.startswith(top + '/') and k.count('/') < depth):
            cell = f'[[{pj(INDEX_DIR, d)}\\|{d}/]]' if d in files else f'`{d}/`'
            root.append(f'| ↳ {cell} | {st[d][1]} | {subj.get(d + "/", "")} |')
    direct = [r for r in rows if '/' not in r]
    if direct:
        root += ['', '## Root notes', '', *TH] + [f'| {wl(r[:-3])} | {rows[r][0]} | {rows[r][1]} |' for r in direct]
    hdr = f'---\ntype: vault-index\ntags: [vault-index]\n---\n\n# Index\n\nFast search entry point for humans and agents: folders first, then each folder\'s own index. Do not edit between the markers.\n\n'
    if write_marked(os.path.join(v, INDEX), '\n'.join(root), hdr):
        changed.append(INDEX)
    print(f'index: {len(rows)} notes listed in {len(files)} index files (one per top-level folder; sub-folders split out over {limit // 1024} KB); changed: {", ".join(changed) or "nothing"}')


def cmd_subject(v, cfg, a):
    subj = load_subjects(v)
    if a.action == 'set':
        p = os.path.join(v, a.rel)
        if not (os.path.isdir(p) if a.rel.endswith('/') else os.path.isfile(p + '.md')):
            sys.exit(f'no such {"folder" if a.rel.endswith("/") else "note"}: {a.rel} (folder keys end with /, note keys drop .md)')
        subj[a.rel] = a.text
        save_subjects(v, subj)
        print(f'subject set: {a.rel}')
        return
    missing = []
    for rel in notes(v, cfg):
        if collapsed(rel, cfg):
            continue
        fm, body = frontmatter(head(v, rel))
        if not (subj.get(rel[:-3]) or auto_subject(fm, body, os.path.basename(rel)[:-3])):
            missing.append(rel)
    print(f'{len(missing)} notes without a subject')
    print('\n'.join(missing))


# ---------- links + path text ----------
def strip_code(txt):
    """Blank fenced blocks and inline code spans (quoted code is not a link), keeping line numbers."""
    txt = re.sub(r'^(`{3,}|~{3,}).*?^\1', lambda m: '\n' * m.group(0).count('\n'), txt, flags=re.S | re.M)
    return re.sub(r'`[^`\n]*`', '', txt)


def link_targets(v, cfg):
    """Yield (note_rel, lineno, kind, raw_target, resolved_rel_or_None, basename_candidates)."""
    base = {}
    for rel in notes(v, cfg):
        base.setdefault(os.path.basename(rel)[:-3], []).append(rel)
    allfiles = set(walk(v, cfg))
    for rel in notes(v, cfg):
        if collapsed(rel, cfg):  # machine-owned mirrors: their links are not ours to fix
            continue
        for ln, line in enumerate(strip_code(read(os.path.join(v, rel))).split('\n'), 1):
            for m in WIKI.finditer(line):
                t = m.group(1).strip().rstrip('\\')  # `\|` = escaped pipe inside tables
                c = base.get(t, []) if '/' not in t else []
                res = c[0] if c else next((x for x in (t + '.md', t) if x in allfiles or os.path.exists(os.path.join(v, x))), None)
                yield rel, ln, 'wiki', t, res, len(c) or 1
            for m in MDLINK.finditer(line):
                t = m.group(1)
                if SCHEME.match(t):
                    continue
                p = urllib.parse.unquote(t)
                res = os.path.normpath(pj(os.path.dirname(rel), p)) if not p.startswith('/') else p.lstrip('/')
                yield rel, ln, 'md', t, res if res in allfiles else None, 1


def map_path(rel, old, new):
    """Prefix-remap rel (file or folder path) for a move old -> new; None if unaffected."""
    if rel == old or rel == old + '.md':
        return new + rel[len(old):]
    if rel.startswith(old.rstrip('/') + '/'):
        return new.rstrip('/') + rel[len(old.rstrip('/')):]
    return None


def fix_links(v, cfg, old, new, apply):
    """Rewrite in-vault links for a move old -> new (run BEFORE the physical move). Returns [(note, n)]."""
    old, new = old.rstrip('/'), new.rstrip('/')
    old_base = os.path.basename(old)[:-3] if old.endswith('.md') else None
    new_base = os.path.basename(new)[:-3] if new.endswith('.md') else None
    base_count = sum(1 for r in notes(v, cfg) if os.path.basename(r)[:-3] == old_base) if old_base else 0
    out = []
    for rel in notes(v, cfg):
        txt = read(os.path.join(v, rel))
        rel_new = map_path(rel, old, new) or rel
        n = 0

        def wiki_sub(m):
            nonlocal n
            raw = m.group(1)
            bs = '\\' if raw.rstrip().endswith('\\') else ''
            t = raw.strip().rstrip('\\')
            nt = None
            if '/' in t:
                nt = map_path(t, old[:-3] if old.endswith('.md') else old, new[:-3] if new.endswith('.md') else new)
            elif old_base and t == old_base and new_base and new_base != old_base and base_count == 1:
                nt = new_base
            if nt is None or nt == t:
                return m.group(0)
            n += 1
            return f'[[{nt}{bs}{m.group(2) or ""}{m.group(3) or ""}]]'

        def md_sub(m):
            nonlocal n
            t = m.group(1)
            if SCHEME.match(t):
                return m.group(0)
            p = urllib.parse.unquote(t)
            res = os.path.normpath(pj(os.path.dirname(rel), p)) if not p.startswith('/') else p.lstrip('/')
            nres = map_path(res, old, new)
            if nres is None and rel_new == rel:
                return m.group(0)  # neither the target nor this note moved
            nl = os.path.relpath(nres or res, os.path.dirname(rel_new) or '.')
            if '%' in t:
                nl = urllib.parse.quote(nl)
            if nl == p:
                return m.group(0)
            n += 1
            return f']({nl}{m.group(2) or ""})'

        new_txt = MDLINK.sub(md_sub, WIKI.sub(wiki_sub, txt))
        if n:
            out.append((rel, n))
            if apply:
                write(os.path.join(v, rel), new_txt)
    return out


def continues_ok(v, old, new, tail):
    """A mention `old<tail>` is a path, not a product name, when the tail is empty or continues into something
    that exists under old (before a move) or new (after it). `Mac/PC` with no such folder → not a path."""
    if not tail.strip('/ '):
        return True
    base = old if os.path.exists(os.path.join(v, old)) else new
    return len(longest_existing(v, base + tail)) > len(base)


def fix_text(v, cfg, old, new, apply):
    """Rewrite path TEXT (not links) in notes for a move old -> new: backticked `old/…`, `<needle>/old…`,
    frontmatter `key: old…`. Skips collapsed folders and the Structure note's Review log (history).
    A folder mention must continue into a real sub-path (pairs like `Mac/PC` are left alone)."""
    old, new = old.rstrip('/'), new.rstrip('/')
    nd = needles(v, cfg)
    tail_rx = re.compile(r'/[^`"\'\]|>*]*')  # names contain spaces; longest_existing() finds where the path ends
    count = [0]

    def guarded(prefix):
        def rep(m):
            tail = tail_rx.match(m.string, m.end())
            if tail and not continues_ok(v, old, new, tail.group(0)):
                return m.group(0)
            count[0] += 1
            return prefix(m) + new
        return rep
    end = r'(?=`)' if old.endswith('.md') else r'(?=/)'
    pats = [(re.compile(r'`' + re.escape(old) + end), guarded(lambda m: '`')),
            (re.compile('(' + '|'.join(map(re.escape, nd)) + ')/' + re.escape(old) + PATH_END), guarded(lambda m: m.group(1) + '/'))]
    fmre = re.compile(r'^([A-Za-z0-9_-]+: )' + re.escape(old) + r'(?=/|$)', re.M)
    out = []
    for rel in notes(v, cfg):
        if collapsed(rel, cfg):
            continue
        txt = read(os.path.join(v, rel))
        body, sep, log = txt.partition('\n## Review log') if rel == STRUCTURE else (txt, '', '')
        count[0] = 0
        for rx, rep in pats:
            body = rx.sub(rep, body)
        if body.startswith('---\n'):
            end_ = body.find('\n---', 4)
            if end_ > 0:
                body = fmre.sub(guarded(lambda m: m.group(1)), body[:end_]) + body[end_:]
        n = count[0]
        if n:
            out.append((rel, n))
            if apply:
                write(os.path.join(v, rel), body + sep + log)
    return out


def remap_config(v, old, new, apply):
    """Remap index.collapse / ignore entries for a move. Returns count."""
    p = os.path.join(v, CONFIG)
    if not os.path.exists(p):
        return 0
    cfg = json.loads(read(p))
    n = 0
    for lst in (cfg.get('index', {}).get('collapse', []), cfg.get('ignore', [])):
        for i, c in enumerate(lst):
            m = map_path(c.rstrip('/'), old.rstrip('/'), new.rstrip('/'))
            if m:
                lst[i], n = m, n + 1
    if n and apply:
        write(p, json.dumps(cfg, indent=2, ensure_ascii=False) + '\n')
    return n


def remap_subjects(v, old, new, apply):
    subj = load_subjects(v)
    remap = {k: (map_path(k, old.rstrip('/'), new.rstrip('/')) or k) for k in subj}
    n = sum(1 for k in remap if remap[k] != k)
    if n and apply:
        save_subjects(v, {remap[k]: val for k, val in subj.items()})
    return n


# ---------- refs ----------
def needles(v, cfg):
    """Strings that identify this vault in files outside it: `<parent>/<name>` (+ `~/<name>` under HOME), or config override."""
    if cfg['consumers'].get('needles'):
        return list(cfg['consumers']['needles'])
    parent, name = os.path.split(v)
    n = [f'{os.path.basename(parent)}/{name}' if os.path.basename(parent) else name]
    if parent == HOME:
        n.append(f'~/{name}')
    return n


def grep_roots(v, cfg, patterns, key):
    paths = [p for r in cfg['consumers'][key] for p in sorted(glob.glob(os.path.expanduser(r)))]
    paths = [p for p in paths if os.path.abspath(p) != v]
    if not paths:
        return []
    cmd = ['grep', '-rInF', '--null'] + [f'--exclude-dir={d}' for d in cfg['consumers']['exclude_dirs']]
    cmd += [x for p in patterns for x in ('-e', p)] + ['--'] + paths
    r = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
    hits = []
    for line in r.stdout.split('\n'):
        if '\0' in line:
            f, rest = line.split('\0', 1)
            ln, _, txt = rest.partition(':')
            if not os.path.abspath(f).startswith(v + '/'):
                hits.append((f.replace(HOME, '~'), int(ln), txt))
    return hits


def longest_existing(v, cand):
    """Longest prefix of cand (cut at space, / or )) that exists in the vault as file, folder or note."""
    best = ''
    for i in range(1, len(cand) + 1):
        if i == len(cand) or cand[i] in ' /)':
            c = cand[:i].rstrip('/')
            if c and any(os.path.exists(os.path.join(v, x)) for x in (c, c + '.md')):
                best = c
    return best


def bare_rx(v, old):
    """`old` not inside a longer path; a leading `<vault name>/` (`Work/X`, `Obsidian Work/X`) is allowed and kept."""
    return re.compile(r'(?<![\w/.~\-])(' + re.escape(os.path.basename(v)) + '/)?' + re.escape(old) + PATH_END)


def bare_hits(v, cfg, old, new, anywhere, key='roots'):
    """Bare (vault-relative) mentions of `old` under consumers[key], path-shaped only (followed by `/`).
    Returns [(id, file, line, occurrence, text, verdict)]. ok = continues into something that exists under new/old
    (or is exactly the folder); ? = continuation does not exist — a product name, history, or a deeper move."""
    nd = needles(v, cfg)
    rx = bare_rx(v, old)
    hits, mentions = [], {}
    for f, ln, txt in grep_roots(v, cfg, [old], key):
        p = os.path.expanduser(f)
        if not anywhere:
            if f not in mentions:
                try:
                    mentions[f] = any(n in read(p) for n in nd)
                except (UnicodeDecodeError, OSError):
                    mentions[f] = False
            if not mentions[f]:
                continue
        if len(txt) > 2000:
            continue  # minified / generated line
        for k, m in enumerate(rx.finditer(txt)):
            tail = re.match(r'/[^`"\'\]|>*]*', txt[m.end():])
            if not tail:
                continue  # `Docs` as a word or "Docs" as a label is never a path reference; `Docs/…` is
            verdict = 'ok' if continues_ok(v, old, new.rstrip('/') or old, tail.group(0)) else '?'
            hits.append((len(hits) + 1, f, ln, k, txt, verdict))
    return hits


def apply_bare(v, hits, old, new, chosen):
    """Rewrite the chosen bare hits (by id) in place. Returns [(file, n)]."""
    rx = bare_rx(v, old)
    by_file = {}
    for hid, f, ln, k, txt, verdict in hits:
        if hid in chosen:
            by_file.setdefault(f, {}).setdefault(ln, set()).add(k)
    out = []
    for f, lines in by_file.items():
        p = os.path.expanduser(f)
        content = read(p).split('\n')
        n = 0
        for ln, ks in lines.items():
            cnt = [-1]

            def sub(m):
                cnt[0] += 1
                return (m.group(1) or '') + new if cnt[0] in ks else m.group(0)
            content[ln - 1] = rx.sub(sub, content[ln - 1])
            n += len(ks)
        write(p, '\n'.join(content))
        out.append((f, n))
    return out


def bare_report(v, cfg, old, new, anywhere):
    """Print bare hits in roots (with ids) and in report_only roots (listed only). Returns the roots hits."""
    hits = bare_hits(v, cfg, old, new, anywhere)
    print(f'## bare mentions of `{old}` in consumer roots ({"all files" if anywhere else "files that also mention the vault; --anywhere for all"}): {len(hits)}')
    for hid, f, ln, k, txt, verdict in hits:
        print(f'- [{hid} {verdict}] {f}:{ln}: {txt.strip()[:160]}')
    ro = sorted({(short(f), ln, verdict, txt.strip()[:160]) for _, f, ln, _, txt, verdict in bare_hits(v, cfg, old, new, anywhere, 'report_only')})
    if ro:
        print(f'## bare mentions in report_only roots: {len(ro)} — not written: fix at the source (PR), then update/reinstall')
        print('\n'.join(f'- [{verdict}] {f}:{ln}: {txt}' for f, ln, verdict, txt in ro))
    return hits


def cmd_refs(v, cfg, a):
    nd = needles(v, cfg)
    if a.action == 'scan' and a.bare:
        bare_report(v, cfg, a.bare, a.new or '', a.anywhere)
        print('Verdict ok = continues into a path that exists under NEW (pass NEW as the 2nd arg to verify); ? = check the meaning by hand (product names are not paths).')
        return
    if a.action == 'scan':
        alt = '|'.join(re.escape(n) for n in nd)
        pat = re.compile(f'(?:{alt})(/(?:(?!{alt})[^`"\'\\]|>*])*)?')  # stop at the next vault mention on the same line

        def classify(cand):
            cand = cand.strip('/ ').rstrip('.,:;)').rstrip('/')
            if not cand:
                return 'root', '(vault root)'
            best = longest_existing(v, cand)
            if not best:  # nothing of it exists: show the path-looking part only
                m = re.match(r'.*?\.md', cand)
                return 'STALE', (m.group(0) if m else cand.split(' ')[0])[:80]
            return ('partial', cand[:80]) if cand[len(best):].startswith('/') else ('ok', best)

        for key in ('roots', 'report_only'):
            hits = grep_roots(v, cfg, nd, key)
            refs = {}
            for f, ln, txt in hits:
                for m in pat.finditer(txt):
                    tag, rel = classify(m.group(1) or '')
                    if a.path and not rel.startswith(a.path.rstrip('/')):
                        continue
                    refs.setdefault((tag, rel), set()).add(f'{short(f)}:{ln}' if key == 'report_only' else f'{f}:{ln}')
            print(f'## consumers ({key}): {len(hits)} hits in {len({short(h[0]) for h in hits})} files, {len(refs)} distinct vault paths')
            for tag, rel in sorted(refs):
                locs = sorted(refs[(tag, rel)])
                print(f'- [{tag}] `{rel}` — {len(locs)} refs: ' + ', '.join(locs[:a.limit]) + (' …' if len(locs) > a.limit else ''))
        broken, amb = [], {}
        for rel, ln, kind, t, res, nbase in link_targets(v, cfg):
            if a.path and not ((res or t).startswith(a.path.rstrip('/'))):
                continue
            if res is None:
                broken.append(f'{rel}:{ln} [{kind}] {t}')
            elif nbase > 1:
                amb.setdefault(t, set()).add(rel)
        print(f'## in-vault links: {len(broken)} broken, {len(amb)} ambiguous basenames')
        print('\n'.join(broken if a.all else broken[:a.limit]) + (f'\n… {len(broken) - a.limit} more (--all)' if len(broken) > a.limit and not a.all else ''))
        for t in sorted(amb):
            print(f'- ambiguous `[[{t}]]` ({len(amb[t])} notes link it): prefer a path-style link')
        return
    old, new = a.old.rstrip('/'), a.new.rstrip('/')
    if a.bare:
        hits = bare_report(v, cfg, old, new, a.anywhere)
        if not a.apply:
            print('DRY RUN — review every hit for meaning (product names are not paths), then `--apply --only 1,3` or `--only all` (= every `ok` hit).')
            return
        if not a.only:
            sys.exit('--apply in bare mode needs --only 1,3 | all')
        chosen = {h[0] for h in hits if h[5] == 'ok'} if a.only == 'all' else {int(x) for x in a.only.split(',') if x.strip()}
        for f, n in apply_bare(v, hits, old, new, chosen):
            print(f'- rewrote {f}: {n}')
        print(f'APPLIED {len(chosen)} hit(s)')
        return
    total = 0
    for key in ('roots', 'report_only'):
        hits = grep_roots(v, cfg, [f'{n}/{old}' for n in nd], key)
        files = sorted({h[0] for h in hits})
        if key == 'report_only':
            print(f'## consumers (report_only): {len({short(f) for f in files})} installed copies reference `{old}` — not written: fix at the source, then update/reinstall')
            for f in sorted({short(f) for f in files}):
                print(f'- {f}')
            continue
        print(f'## consumers (roots): {len(files)} files reference `{old}`')
        for f in files:
            p = os.path.expanduser(f)
            txt = read(p)
            rx = re.compile('(' + '|'.join(re.escape(n) for n in nd) + ')/' + re.escape(old) + PATH_END)
            new_txt, n = rx.subn(lambda m: f'{m.group(1)}/{new}', txt)
            total += n
            print(f'- {f}: {n} replacement(s)' + ''.join(f'\n    L{ln}: {t.strip()[:160]}' for ff, ln, t in hits if ff == f))
            if a.apply and n:
                write(p, new_txt)
    links = fix_links(v, cfg, old, new, a.apply)
    print(f'## in-vault links: {sum(n for _, n in links)} link(s) in {len(links)} note(s)')
    print('\n'.join(f'- {r}: {n}' for r, n in links[:a.limit]))
    texts = fix_text(v, cfg, old, new, a.apply)
    print(f'## in-vault path text (backticks, full paths, frontmatter): {sum(n for _, n in texts)} in {len(texts)} note(s)')
    print('\n'.join(f'- {r}: {n}' for r, n in texts[:a.limit]))
    print(f'## config (collapse/ignore): {remap_config(v, old, new, a.apply)} entries; subjects: {remap_subjects(v, old, new, a.apply)} key(s)')
    print('APPLIED' if a.apply else 'DRY RUN — add --apply to write')


# ---------- move ----------
def cmd_move(v, cfg, a):
    old, new = a.old.rstrip('/'), a.new.rstrip('/')
    src, dst = os.path.join(v, old), os.path.join(v, new)
    if not os.path.exists(src):
        sys.exit(f'missing: {old}')
    same = os.path.exists(dst) and os.path.samefile(src, dst)  # case-only rename on a case-insensitive FS
    if os.path.exists(dst) and not same:
        sys.exit(f'exists: {new}')
    if ignored(old, cfg) or ignored(new, cfg) or old.startswith(VDIR) or new.startswith(VDIR):
        sys.exit('refusing to move ignored / _Vault paths')
    links = fix_links(v, cfg, old, new, True)
    texts = fix_text(v, cfg, old, new, True)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tracked = is_git(v) and git(v, 'ls-files', '--error-unmatch', '--', old) is not None
    how = 'git mv' if tracked else 'mv'
    for a_, b_ in ([(old, new + '.vm-tmp'), (new + '.vm-tmp', new)] if same else [(old, new)]):
        if tracked and git(v, 'mv', '-k', '--', a_, b_) is None:
            how = 'mv (git mv failed; stage by hand)'
        if not os.path.exists(os.path.join(v, b_)) or (same and os.path.exists(os.path.join(v, a_))):
            os.rename(os.path.join(v, a_), os.path.join(v, b_))
    removed = []
    d = os.path.dirname(old)
    while d:  # drop folders the move emptied
        full = os.path.join(v, d)
        if set(os.listdir(full)) - {'.DS_Store'}:
            break
        for junk in os.listdir(full):
            os.remove(os.path.join(full, junk))
        os.rmdir(full)
        removed.append(d)
        d = os.path.dirname(d)
    cfgn, subn = remap_config(v, old, new, True), remap_subjects(v, old, new, True)
    print(f'moved `{old}` -> `{new}` ({how}); links fixed in {len(links)} note(s); path text in {len(texts)} note(s); '
          f'config entries {cfgn}; subjects {subn}' + (f'; removed empty {", ".join(removed)}' if removed else '') +
          f'. Next: `refs rewrite "{old}" "{new}"` (dry run) for consumers outside the vault, `refs rewrite "{old}" "{new}" --bare` for bare mentions, then `index`.')


# ---------- changes ----------
def structure_fm(v):
    p = os.path.join(v, STRUCTURE)
    return frontmatter(head(v, STRUCTURE, 30))[0] if os.path.exists(p) else {}


def suffix(p1, p2):
    """Path components shared from the end."""
    a1, a2 = p1.split('/')[::-1], p2.split('/')[::-1]
    return next((i for i, (x, y) in enumerate(zip(a1, a2)) if x != y), min(len(a1), len(a2)))


def pair_moves(deleted, added):
    """Deleted + added paths with the same basename → likely (old, new) pairs (closest path wins)."""
    by = {}
    for p in added:
        by.setdefault(os.path.basename(p), []).append(p)
    return [(p, max(by[os.path.basename(p)], key=lambda q: suffix(p, q))) for p in deleted if os.path.basename(p) in by]


def collapse_moves(v, pairs):
    """File pairs → the folder moves that explain them: {(old, new): files}."""
    folders = {}
    for p1, p2 in pairs:
        k = min(suffix(p1, p2), p1.count('/'), p2.count('/'))
        key = ('/'.join(p1.split('/')[:-k]), '/'.join(p2.split('/')[:-k])) if k else (p1, p2)
        folders.setdefault(key, []).append((p1, p2))
    for key in list(folders):  # one file whose old folder still exists = a file move, not a folder move
        if len(folders[key]) == 1 and key != folders[key][0] and os.path.isdir(os.path.join(v, key[0])):
            ps = folders.pop(key)
            folders[ps[0]] = ps
    return {k: len(ps) for k, ps in folders.items()}


def print_moves(v, title, pairs, show_all):
    if not pairs:
        return
    folders = collapse_moves(v, pairs)
    print(f'### {title}: {len(folders)} move(s), {len(pairs)} files')
    print('\n'.join(f'- {k[0]} -> {k[1]} ({n} file{"s" if n > 1 else ""})' for k, n in sorted(folders.items())))
    if show_all:
        print('\n'.join(f'  - {p1} -> {p2}' for p1, p2 in pairs))


def snapshot(v, cfg):
    return {r: [int(os.stat(os.path.join(v, r)).st_mtime), os.stat(os.path.join(v, r)).st_size] for r in walk(v, cfg)}


def cmd_changes(v, cfg, a):
    fm = structure_fm(v)
    sha = fm.get('last_review_sha') or ''
    sha = sha if isinstance(sha, str) else ''
    lim = None if a.all else a.limit
    if is_git(v):
        if not sha or git(v, 'cat-file', '-e', sha) is None:
            print('no usable review marker (last_review_sha) — treat the whole vault as new; `mark` at the end of this review.')
            committed = []
        else:
            raw = git(v, 'diff', '--name-status', '-M', '-z', sha, 'HEAD', '--', '.') or ''
            parts = raw.split('\0')
            committed, i = [], 0
            while i < len(parts) - 1:
                code = parts[i]
                if code.startswith('R') or code.startswith('C'):
                    committed.append((code[0], parts[i + 1], parts[i + 2]))
                    i += 3
                else:
                    committed.append((code[0], parts[i + 1], None))
                    i += 2
        raw = git(v, 'status', '--porcelain=v1', '-z', '-uall', '--', '.') or ''
        parts, uncommitted, i = raw.split('\0'), [], 0
        while i < len(parts) - 1:
            xy, path = parts[i][:2], parts[i][3:]
            if 'R' in xy:
                uncommitted.append(('R', parts[i + 1], path))
                i += 2
            else:
                uncommitted.append(('A' if xy.strip() in ('??', 'A') else ('D' if 'D' in xy else 'M'), path, None))
                i += 1
        print(f'## since {sha[:9] or "(no marker)"} ({fm.get("last_review_date") or "?"}) → HEAD: {len(committed)} committed; uncommitted now: {len(uncommitted)}')
        for title, items in (('committed', committed), ('uncommitted', uncommitted)):
            by = {}
            for code, p1, p2 in items:
                if p2:
                    continue  # renames: collapsed to folder level below
                by.setdefault(p1.split('/')[0] if '/' in p1 else '(root)', []).append((code, p1))
            for top in sorted(by):
                counts = {c: sum(1 for x in by[top] if x[0] == c) for c in 'AMD'}
                print(f'### {title} · {top}: ' + ', '.join(f'{c}={n}' for c, n in counts.items() if n))
                print('\n'.join(f'- {code} {p1}' for code, p1 in by[top][:lim]))
                if lim and len(by[top]) > lim:
                    print(f'- … {len(by[top]) - lim} more (--all)')
            print_moves(v, f'{title} renames (git)', [(p1, p2) for _, p1, p2 in items if p2], a.all)
        pairs = pair_moves([p for c, p, _ in uncommitted if c == 'D'], [p for c, p, _ in uncommitted if c == 'A'])
        print_moves(v, 'likely human moves (deleted + added with the same name, uncommitted)', pairs, a.all)
        new_dirs = set()
        for c, p, _ in uncommitted:
            if c == 'A' and '/' in p:
                d = os.path.dirname(p)
                if (git(v, 'ls-files', '--', d) or '').strip():
                    continue
                while os.path.dirname(d) and not (git(v, 'ls-files', '--', os.path.dirname(d)) or '').strip():
                    d = os.path.dirname(d)
                new_dirs.add(d)
        if new_dirs:
            print(f'### folders with no tracked file (human-added, uncommitted): {", ".join(sorted(new_dirs))}')
        return
    snap_p = os.path.join(v, SNAPSHOT)
    snap = json.loads(read(snap_p)) if os.path.exists(snap_p) else {}
    now = snapshot(v, cfg)
    added = sorted(set(now) - set(snap))
    removed = sorted(set(snap) - set(now))
    modified = sorted(r for r in now if r in snap and now[r] != snap[r])
    pairs = pair_moves(removed, added)
    moved = {p for pr in pairs for p in pr}
    print(f'## not a git repo — snapshot diff since {fm.get("last_review_date") or "(none)"}: +{len(added)} -{len(removed)} ~{len(modified)}')
    print_moves(v, 'likely moves (removed + added with the same name)', pairs, a.all)
    for title, items in (('added', added), ('removed', removed), ('modified', modified)):
        items = [x for x in items if x not in moved]
        print(f'### {title}' + (' (moves excluded)' if pairs and title != 'modified' else ''))
        print('\n'.join('- ' + x for x in items[:lim]) + (f'\n- … {len(items) - lim} more (--all)' if lim and len(items) > lim else ''))


# ---------- check / mark / init ----------
def section(txt, title):
    m = re.search(r'^## ' + re.escape(title) + r'\s*$(.*?)(?=^## |\Z)', txt, re.S | re.M)
    return m.group(1) if m else ''


def source_paths(cell):
    """Existing `~/…` or `/…` paths in a registry Source cell (`~/a/SKILL.md; path in ~/b.json` → both; names may hold spaces)."""
    out = []
    for m in re.finditer(r'(?<![\w/.~\-])(?=~/|/)', cell):
        words = cell[m.start():].split(' ')
        for k in range(min(len(words), 6), 0, -1):
            c = ' '.join(words[:k]).rstrip(';,:)`\'"')
            if os.path.exists(os.path.expanduser(c)):
                out.append(os.path.expanduser(c))
                break
    return out


def mentions(src, p):
    """Does the source mention vault path p: the relative path, or for a note also its file name (sources often name
    the folder and the note separately)."""
    p = p.rstrip('/')
    needles_ = [p] if not p.endswith('.md') else [p[:-3], os.path.basename(p), os.path.basename(p)[:-3]]
    if os.path.isdir(src):
        return subprocess.run(['grep', '-rqF', '--exclude-dir=.git'] + [x for n in needles_ for x in ('-e', n)] + ['--', src],
                              capture_output=True).returncode == 0
    try:
        txt = read(src)
    except (UnicodeDecodeError, OSError):
        return False
    return any(n in txt for n in needles_)


def cmd_check(v, cfg, a):
    sp = os.path.join(v, STRUCTURE)
    if not os.path.exists(sp):
        sys.exit(f'{STRUCTURE} missing — run `init`')
    txt = read(sp)
    st = folder_stats(v, cfg)
    depth = cfg['index']['depth']
    listed = {m.group(1).rstrip('/') for m in re.finditer(r'^- `([^`]+)/?`(?!.*\(describe:)', section(txt, 'Folder map'), re.M)}
    actual = {d for d in st if d and d != VDIR and d.count('/') < depth and not collapsed(d, cfg)}
    missing, stale = sorted(actual - listed), sorted(listed - set(st))
    print(f'## folder map: {len(missing)} folders not described, {len(stale)} described but gone')
    print('\n'.join(f'- missing: `{d}/` ({st[d][1]} notes)' for d in missing) + ('\n' if missing else '') +
          '\n'.join(f'- gone: `{d}/`' for d in stale))
    if '(describe:' in txt:
        print(f'## placeholders: {txt.count("(describe:")} `(describe: …)` left from `init` — fill them')
    rows = [l for l in section(txt, 'Writers registry').split('\n') if l.startswith('|') and not l.startswith('|---') and not l.startswith('| Writer')]
    problems, unmentioned = [], []
    for r in rows:
        cells = [c.strip().strip('`') for c in r.strip('|').split('|')]
        if len(cells) < 5:
            problems.append(f'malformed row: {r[:80]}')
            continue
        name, src, paths = cells[0], cells[2], cells[3]
        srcs = source_paths(src)
        if src and not srcs:
            problems.append(f'{name}: source missing `{src[:100]}`')
        for p in [x.strip().strip('`') for x in paths.split(',') if x.strip()]:
            if not os.path.exists(os.path.join(v, p.rstrip('/'))) and not os.path.exists(os.path.join(v, p.rstrip('/') + '.md')):
                problems.append(f'{name}: vault path missing `{p}`')
            elif srcs and not any(mentions(s, p) for s in srcs):
                unmentioned.append(f'{name}: `{p}` not in its Source')
    print(f'## writers registry: {len(rows)} rows, {len(problems)} problems')
    print('\n'.join('- ' + p for p in problems))
    if unmentioned:  # a script given the vault dir as an argument holds only relative folders — this is where a stale one shows
        print(f'## writers vs sources: {len(unmentioned)} listed path(s) the Source never mentions — drift (old path in code) or expected (path passed as an argument; say so in Notes)')
        print('\n'.join('- ' + p for p in unmentioned))
    if not cfg['consumers']['roots']:
        print('## consumers: no `consumers.roots` configured — `refs` only covers in-vault links')


def cmd_mark(v, cfg, a):
    sp = os.path.join(v, STRUCTURE)
    if not os.path.exists(sp):
        sys.exit(f'{STRUCTURE} missing — run `init`')
    upd = {'last_review_date': TODAY}
    if is_git(v):
        upd['last_review_sha'] = (git(v, 'rev-parse', 'HEAD') or '').strip() or '(no commits)'
        dirty = bool((git(v, 'status', '--porcelain', '--', '.') or '').strip())
        upd['last_review_dirty'] = str(dirty).lower()
    else:
        upd['last_review_sha'] = '(not git — snapshot.json)'
    set_frontmatter(sp, upd)
    if not is_git(v):  # after the note is written, or the next `changes` reports it as modified
        write(os.path.join(v, SNAPSHOT), json.dumps(snapshot(v, cfg), indent=0, ensure_ascii=False))
    print('marked: ' + ', '.join(f'{k}={val}' for k, val in upd.items()))


def cmd_init(v, cfg, a):
    sp = os.path.join(v, STRUCTURE)
    if os.path.exists(sp):
        sys.exit(f'already initialised: {STRUCTURE}')
    cp = os.path.join(v, CONFIG)
    if not os.path.exists(cp):
        write(cp, json.dumps(DEFAULT_CONFIG, indent=2) + '\n')
    if not os.path.exists(os.path.join(v, SUBJECTS)):
        save_subjects(v, {})
    st = folder_stats(v, cfg)
    depth = cfg['index']['depth']
    fmap = '\n'.join(f'- `{d}/` — (describe: what this folder holds)' for d in sorted(st) if d and d != VDIR and d.count('/') < depth) or '- (no folders yet)'
    txt = read(TEMPLATE).replace('{{VAULT_NAME}}', os.path.basename(v)).replace('{{DATE}}', TODAY).replace('{{DEPTH}}', str(depth)).replace('{{FOLDER_MAP}}', fmap)
    write(sp, txt)
    cmd_index(v, cfg, a)
    print(f'initialised {VDIR}/ in {v}: fill Taxonomy + Folder map + Writers registry in {STRUCTURE}; set consumers.roots in {CONFIG}; run `mark` when the review is done (no marker yet).')


# ---------- selfcheck ----------
def selfcheck():
    import io, contextlib

    def run(fn, *args, **kw):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fn(*args, **kw)
        return buf.getvalue()

    tmp = tempfile.mkdtemp(prefix='vm-')
    v = os.path.join(tmp, 'vault')
    cons = os.path.join(tmp, 'consumers')
    tag = os.path.basename(tmp)
    os.makedirs(os.path.join(v, '.obsidian'))
    write(os.path.join(v, 'A/one.md'), '---\ntags: [x, y]\ndescription: first note\nbackup: B/two.md\n---\nSee [[B/two]], [[two]], [md](../B/two.md) and [[C/three#h|alias]]. Not ours: [u](https://example.com/a/README.md).\n'
          f'| [[B/two\\|two]] | text `B/two.md`, `B/deep/`, `B/sp ace.md` and more, the `B/Codex` product and ~/x/{tag}/vault/B/deep |\n'
          'quoted code `[[nope]]` is not a link:\n```\n[[also nope]]\n```\n')
    write(os.path.join(v, 'B/sp ace.md'), 'name with a space\n')
    write(os.path.join(v, 'A/Sp ace.md'), 'spaces in names\n')
    write(os.path.join(v, 'B/two.md'), '# Two\n\nBack to [[one]].\n')
    write(os.path.join(v, 'B/deep/four.md'), 'Sibling [s](../two.md) and [[B/two]].\n')
    write(os.path.join(v, 'B/deep/five.md'), 'x\n')
    write(os.path.join(v, 'Root note.md'), '**Root** — a note at the root.\n')
    write(os.path.join(cons, 'skill.md'), f'writes to ~/x/{tag}/vault/B/two.md and {tag}/vault/A/\n'
          f'see {tag}/vault/A/Sp ace.md for details; nested {tag}/vault/A/gone/x.md\n'
          'bare: notes in `B/deep/` and the B/Codex product; also B/deep/five.md — plain B word, "B" quoted\n'
          'prefixed with the vault name: vault/B/deep/five.md too\n')
    write(os.path.join(cons, 'other.md'), 'no vault mention here, but B/deep/ appears\n')
    ro = os.path.join(tmp, 'ro')
    write(os.path.join(ro, 'plug.md'), f'installed copy of a plugin naming {tag}/vault; bare: B/deep/five.md\n')
    subprocess.run(['git', '-C', v, 'init', '-q'], check=True)
    g = lambda *a: subprocess.run(['git', '-C', v, '-c', 'user.name=t', '-c', 'user.email=t@t', *a], check=True, capture_output=True)
    g('add', 'A', 'B', 'Root note.md')
    g('commit', '-q', '-m', 'init')
    write(os.path.join(v, 'C/three.md'), 'untracked\n')
    write(os.path.join(v, CONFIG), json.dumps({'consumers': {'roots': [cons], 'report_only': [ro]}, 'index': {'collapse': ['B/deep'], 'split_kb': 0}}))  # 0 = split every child
    cfg = load_config(v)
    ns = argparse.Namespace(depth=3, all=False, limit=50, apply=False, bare=None, anywhere=False, only=None, new=None, path=None)
    cmd_init(v, cfg, ns)
    assert os.path.exists(os.path.join(v, STRUCTURE)) and os.path.exists(os.path.join(v, INDEX))
    assert structure_fm(v).get('last_review_sha') in ([], ''), 'init must not mark'
    idx = read(os.path.join(v, INDEX))
    assert '[[_Vault/Index/A\\|A/]]' in idx and '| [[Root note\\|Root note]] |' in idx and 'Root — a note at the root.' in idx
    assert '| [[A/one\\|one]] | x, y | first note |' in read(os.path.join(v, INDEX_DIR, 'A.md'))
    assert '`B/deep/` | 2 | not listed' in read(os.path.join(v, INDEX_DIR, 'B.md'))
    # a heading repeating the title and a link-only line are not subjects
    assert '| [[B/two\\|two]] |  |  |' in read(os.path.join(v, INDEX_DIR, 'B.md')), read(os.path.join(v, INDEX_DIR, 'B.md'))
    assert 'B/two.md' in run(cmd_subject, v, cfg, argparse.Namespace(action='missing'))
    # init placeholders count as not described
    out = run(cmd_check, v, cfg, ns)
    assert '4 folders not described' in out and 'placeholders: 5' in out, out
    sp = os.path.join(v, STRUCTURE)
    write(sp, read(sp).replace('- `A/` — (describe: what this folder holds)', '- `A/` — area A notes'))
    assert '3 folders not described' in run(cmd_check, v, cfg, ns)
    cmd_subject(v, cfg, argparse.Namespace(action='set', rel='A/', text='area A'))
    try:
        cmd_subject(v, cfg, argparse.Namespace(action='set', rel='Nope/', text='x'))
        raise AssertionError('subject set must reject unknown paths')
    except SystemExit:
        pass
    cmd_index(v, cfg, ns)
    assert '| [[_Vault/Index/A\\|A/]] | 2 | area A |' in read(os.path.join(v, INDEX))
    # escaped-pipe wikilink and quoted code are not broken links
    out = run(cmd_refs, v, cfg, argparse.Namespace(action='scan', path=None, limit=50, all=True, bare=None, anywhere=False, new=None))
    assert 'two\\' not in out and '[wiki] B/two' not in out and 'nope' not in out, out
    # move a tracked folder: links + path text fixed before the move, git mv used, collapse remapped
    run(cmd_move, v, cfg, argparse.Namespace(old='B', new='Z/B'))
    out = run(cmd_changes, v, cfg, ns)
    assert 'uncommitted renames (git): 1 move(s), 4 files' in out and '- B -> Z/B (4 files)' in out and 'Z/B/two.md' not in out, out
    one = read(os.path.join(v, 'A/one.md'))
    assert '[[Z/B/two]]' in one and '(../Z/B/two.md)' in one and '[[two]]' in one and '[[Z/B/two\\|two]]' in one, one
    assert '`Z/B/two.md`' in one and f'{tag}/vault/Z/B/deep' in one and 'backup: Z/B/two.md' in one and '`B/Codex`' in one and '`Z/B/sp ace.md` and more' in one, one
    assert '[s](../two.md)' in read(os.path.join(v, 'Z/B/deep/four.md')) and '[[Z/B/two]]' in read(os.path.join(v, 'Z/B/deep/four.md'))
    assert 'R' in subprocess.run(['git', '-C', v, 'status', '--porcelain'], capture_output=True, text=True).stdout
    assert json.loads(read(os.path.join(v, CONFIG)))['index']['collapse'] == ['Z/B/deep']
    assert not os.path.exists(os.path.join(v, 'B')), 'emptied source folder must be removed'
    cfg = load_config(v)
    # move an untracked folder: plain mv
    run(cmd_move, v, cfg, argparse.Namespace(old='C', new='D/C'))
    assert os.path.exists(os.path.join(v, 'D/C/three.md')) and '[[D/C/three#h|alias]]' in read(os.path.join(v, 'A/one.md'))
    # rename a note: basename wikilinks follow when unique
    run(cmd_move, v, cfg, argparse.Namespace(old='Z/B/two.md', new='Z/B/second.md'))
    one = read(os.path.join(v, 'A/one.md'))
    assert '[[Z/B/second]]' in one and '[[second]]' in one and '(../Z/B/second.md)' in one and '[[Z/B/second\\|two]]' in one, one
    # case-only rename
    run(cmd_move, v, cfg, argparse.Namespace(old='Z/B', new='Z/b'))
    assert 'b' in os.listdir(os.path.join(v, 'Z')) and 'B' not in os.listdir(os.path.join(v, 'Z')) and '[[Z/b/second]]' in read(os.path.join(v, 'A/one.md'))
    run(cmd_move, v, cfg, argparse.Namespace(old='Z/b', new='Z/B'))
    # consumer refs: scan finds stale, rewrite fixes it
    out = run(cmd_refs, v, cfg, argparse.Namespace(action='scan', path=None, limit=50, all=False, bare=None, anywhere=False, new=None))
    assert '[STALE] `B/two.md`' in out and '[ok] `A`' in out and '[ok] `A/Sp ace.md`' in out and '[partial] `A/gone/x.md`' in out, out
    assert 'https://example.com/a/README.md' in read(os.path.join(v, 'A/one.md')) and 'README.md' not in out, out
    run(cmd_refs, v, cfg, argparse.Namespace(action='rewrite', old='B/two.md', new='Z/B/second.md', apply=False, limit=50, bare=None, anywhere=False, only=None))
    assert 'vault/B/two.md' in read(os.path.join(cons, 'skill.md'))
    run(cmd_refs, v, cfg, argparse.Namespace(action='rewrite', old='B/two.md', new='Z/B/second.md', apply=True, limit=50, bare=None, anywhere=False, only=None))
    assert 'vault/Z/B/second.md' in read(os.path.join(cons, 'skill.md'))
    # bare mode: verdicts, product-name guard, vault-name prefix, report_only listed but never written, supervised apply
    out = run(cmd_refs, v, cfg, argparse.Namespace(action='rewrite', old='B', new='Z/B', apply=False, limit=50, bare=True, anywhere=False, only=None))
    assert '[1 ok]' in out and '[2 ?]' in out and '[3 ok]' in out and '[4 ok]' in out and '[5' not in out and 'other.md' not in out, out
    assert 'report_only roots: 1' in out and 'plug.md:1' in out, out
    out = run(cmd_refs, v, cfg, argparse.Namespace(action='rewrite', old='B', new='Z/B', apply=False, limit=50, bare=True, anywhere=True, only=None))
    assert 'other.md' in out, out
    run(cmd_refs, v, cfg, argparse.Namespace(action='rewrite', old='B', new='Z/B', apply=True, limit=50, bare=True, anywhere=False, only='all'))
    sk = read(os.path.join(cons, 'skill.md'))
    assert '`Z/B/deep/`' in sk and 'the B/Codex product' in sk and 'also Z/B/deep/five.md' in sk and 'plain B word, "B" quoted' in sk, sk
    assert 'name: vault/Z/B/deep/five.md too' in sk and 'bare: B/deep/five.md' in read(os.path.join(ro, 'plug.md')), sk
    # index split: tiny threshold forces per-folder files + root links
    cmd_index(v, cfg, ns)
    assert os.path.exists(os.path.join(v, INDEX_DIR, 'Z/B.md')) and '[[_Vault/Index/Z/B\\|Z/B/]]' in read(os.path.join(v, INDEX)), read(os.path.join(v, INDEX))
    assert '→ [[_Vault/Index/Z/B\\|Z/B/ index]]' in read(os.path.join(v, INDEX_DIR, 'Z.md'))
    # structure drift + changes (folder-level human-move pairs); registry: `X; path in Y` sources, paths the source never mentions
    write(os.path.join(v, 'E/x/one.md'), 'moved by human\n')
    os.remove(os.path.join(v, 'A/one.md'))
    write(sp, read(sp).replace('|---|---|---|---|---|---|\n', '|---|---|---|---|---|---|\n'
                               f'| w1 | script | {cons}/skill.md; path in {cons}/other.md | `A/Sp ace.md`, `Z/B/deep/`, `Root note.md` | write | |\n'
                               '| w2 | skill | ~/definitely/missing/SKILL.md | `A/` | read | |\n', 1))
    out = run(cmd_check, v, cfg, ns) + run(cmd_changes, v, cfg, ns)
    assert 'missing: `Z/`' in out and 'missing: `D/`' in out and '0 described but gone' in out, out
    assert '- `Z/B/` —' in read(os.path.join(v, STRUCTURE)) and '- `D/C/` —' in read(os.path.join(v, STRUCTURE))
    assert '2 rows, 1 problems' in out and 'w2: source missing' in out and 'writers vs sources: 1' in out and 'w1: `Root note.md` not in its Source' in out, out
    assert '- A/one.md -> E/x/one.md (1 file)' in out and 'human-added, uncommitted): D, E, _Vault' in out, out
    # non-git fallback: mark then changes = clean; renames paired into moves
    shutil.rmtree(os.path.join(v, '.git'))
    run(cmd_mark, v, cfg, ns)
    out = run(cmd_changes, v, cfg, ns)
    assert 'not a git repo' in out and '+0 -0 ~0' in out, out
    write(os.path.join(v, 'A/new.md'), 'new\n')
    os.rename(os.path.join(v, 'E'), os.path.join(v, 'F'))
    out = run(cmd_changes, v, cfg, ns)
    assert '+2 -1 ~0' in out and '- A/new.md' in out and '- E -> F (1 file)' in out and '- E/x/one.md' not in out, out
    shutil.rmtree(tmp)
    print('selfcheck OK')


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--vault', help='vault directory (default: nearest ancestor of cwd with .obsidian/ or _Vault/)')
    subs = ap.add_subparsers(dest='cmd', required=True)
    sub = type('S', (), {'add_parser': staticmethod(lambda name: subs.add_parser(name, parents=[common]))})
    sub.add_parser('init')
    sub.add_parser('tree').add_argument('--depth', type=int, default=2)
    p = sub.add_parser('changes')
    p.add_argument('--all', action='store_true')
    p.add_argument('--limit', type=int, default=20)
    sub.add_parser('index')
    p = sub.add_parser('subject')
    p.add_argument('action', choices=['set', 'missing'])
    p.add_argument('rel', nargs='?')
    p.add_argument('text', nargs='?')
    p = sub.add_parser('refs')
    p.add_argument('action', choices=['scan', 'rewrite'])
    p.add_argument('old', nargs='?')
    p.add_argument('new', nargs='?')
    p.add_argument('--path')
    p.add_argument('--bare', nargs='?', const=True, help='scan: --bare OLD; rewrite: flag')
    p.add_argument('--anywhere', action='store_true', help='bare mode: all files under roots, not only those mentioning the vault')
    p.add_argument('--only', help='bare mode apply: hit ids 1,3 or all (= every ok hit)')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--all', action='store_true')
    p.add_argument('--limit', type=int, default=20)
    p = sub.add_parser('move')
    p.add_argument('old')
    p.add_argument('new')
    sub.add_parser('check')
    sub.add_parser('mark')
    sub.add_parser('selfcheck')
    a = ap.parse_args()
    if a.cmd == 'selfcheck':
        return selfcheck()
    if a.cmd == 'subject' and (a.action == 'set' and not (a.rel and a.text)):
        ap.error('subject set REL TEXT')
    if a.cmd == 'refs' and a.action == 'rewrite' and not (a.old and a.new):
        ap.error('refs rewrite OLD NEW')
    if a.cmd == 'refs' and a.action == 'scan' and a.bare:
        if a.bare is True:  # `refs scan --bare OLD [NEW]`: argparse put OLD/NEW in old/new
            a.bare, a.new = a.old, a.new
        elif a.old and not a.new:
            a.new = a.old
    v = find_vault(a.vault)
    cfg = load_config(v)
    {'init': cmd_init, 'tree': cmd_tree, 'changes': cmd_changes, 'index': cmd_index, 'subject': cmd_subject,
     'refs': cmd_refs, 'move': cmd_move, 'check': cmd_check, 'mark': cmd_mark}[a.cmd](v, cfg, a)


if __name__ == '__main__':
    main()
