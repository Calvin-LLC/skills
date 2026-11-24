#!/usr/bin/env python3
"""Read agent session history from every harness store on this machine.

Stores: OMP, Pi, Muse Code, Claude Code, Codex (JSONL files) and Hermes (SQLite).
Output is JSONL on stdout, one event per line, same shape for every harness:
  {"harness", "session", "parent", "cwd", "child", "kind", "tool", "id", "ts", "text", "error"}
kind is user | assistant | call | result. `id` is the harness's tool-call id (a call and
its result share it); `ts` is UTC ISO time; `parent` is the root session of a subagent.
Read-only; secrets are masked.

  sessions.py sources                          stores found, session counts
  sessions.py list   [filters]                 one row per session, newest first
  sessions.py prompts [filters]                what the user typed
  sessions.py calls  [filters]                 tool calls and clipped results
  sessions.py transcript --session ID          everything, in order

Filters: --harness NAME (repeatable)  --cwd PATH (prefix match, any slash style)
         --days N (default 7)  --limit N sessions (default 10; 0 = all)
         --session ID (substring; lifts --days and --limit)
         --children (include subagent sessions; with --session, that session's subagents)
         --clip N (max chars per text field; default 400, transcript 4000; 0 = no clip)
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time

HOME = os.path.expanduser('~')
SECRET = re.compile(r'(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{16,}'
                    r'|(?i:password|passwd|secret|token|api_key)\s*[=:]\s*\S+)')


def env_dir(var, *default):
    return os.environ.get(var) or os.path.join(HOME, *default)


def norm(path):
    return (path or '').replace('\\\\?\\', '').replace('\\', '/').rstrip('/').lower()


def text_of(content):
    """Flatten a string or a list of content blocks to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(b.get('text') or b.get('content') or '' if isinstance(b, dict) else str(b)
                         for b in content if not isinstance(b, dict) or isinstance(b.get('text') or b.get('content') or '', str))
    return '' if content is None else json.dumps(content, ensure_ascii=False)


def rows(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def head_match(path, pattern, size=262144):
    with open(path, encoding='utf-8', errors='replace') as fh:
        m = re.search(pattern, fh.read(size))
    return json.loads('"%s"' % m.group(1)) if m else ''


def iso(value):
    """Epoch seconds, milliseconds or microseconds, or an ISO string, as UTC ISO."""
    if isinstance(value, (int, float)) and value > 0:
        while value > 1e11:
            value /= 1000.0
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(value))
    return value if isinstance(value, str) else ''


# --- per-harness readers: each yields (kind, tool, text, error, call_id, ts) -----

def omp_events(path):  # OMP and Pi share this format
    for r in rows(path):
        ts = iso(r.get('timestamp'))
        if r.get('type') == 'custom_message' and r.get('customType') == 'skill-prompt':
            d = r.get('details') or {}
            yield 'user', '', '/skill:%s %s' % (d.get('name'), d.get('args') or ''), False, '', ts
        if r.get('type') != 'message':
            continue
        m = r.get('message') or {}
        role, content = m.get('role'), m.get('content')
        if role == 'user':
            yield 'user', '', text_of(content), False, '', ts
        elif role == 'toolResult':
            yield 'result', m.get('toolName') or '', text_of(content), bool(m.get('isError')), m.get('toolCallId') or '', ts
        elif role == 'assistant':
            for b in content if isinstance(content, list) else [{'type': 'text', 'text': content}]:
                if b.get('type') == 'text' and (b.get('text') or '').strip():
                    yield 'assistant', '', b['text'], False, '', ts
                elif b.get('type') == 'toolCall':
                    yield 'call', b.get('name') or '', json.dumps(b.get('arguments') or {}, ensure_ascii=False), False, b.get('id') or '', ts


def muse_events(path):
    for r in rows(path):
        p = r.get('payload')
        ev = p.get('event') if isinstance(p, dict) and p.get('kind') == 'run' else None
        if not isinstance(ev, dict):
            continue
        k, ts = ev.get('kind'), iso(r.get('recorded_at'))
        if k == 'started':
            yield 'user', '', ev.get('prompt') or '', False, '', ts
        elif k == 'inbox_item_drained':
            snap = ev.get('delivery_snapshot') or {}
            if (snap.get('source') or {}).get('source') == 'user_steer':
                yield 'user', '', snap.get('body') or '', False, '', ts
        elif k == 'assistant_message_committed' and (ev.get('text') or '').strip():
            yield 'assistant', '', ev['text'], False, '', ts
        elif k == 'assistant_tool_calls_committed':
            for c in ev.get('tool_calls') or []:
                yield 'call', c.get('name') or '', c.get('args') or '', False, c.get('call_id') or c.get('id') or '', ts
        elif k == 'tool_result_batch_committed':
            for res in ev.get('results') or []:
                yield 'result', '', res.get('text') or '', bool(res.get('is_error')), res.get('tool_call_id') or '', ts


def claude_events(path):
    for r in rows(path):
        m = r.get('message') or {}
        content, ts = m.get('content'), iso(r.get('timestamp'))
        if r.get('type') == 'user' and not r.get('isMeta'):
            if isinstance(content, str):
                yield 'user', '', content, False, '', ts
            for b in content if isinstance(content, list) else []:
                if b.get('type') == 'text':
                    yield 'user', '', b.get('text') or '', False, '', ts
                elif b.get('type') == 'tool_result':
                    yield 'result', '', text_of(b.get('content')), bool(b.get('is_error')), b.get('tool_use_id') or '', ts
        elif r.get('type') == 'assistant':
            for b in content if isinstance(content, list) else []:
                if b.get('type') == 'text' and (b.get('text') or '').strip():
                    yield 'assistant', '', b['text'], False, '', ts
                elif b.get('type') == 'tool_use':
                    yield 'call', b.get('name') or '', json.dumps(b.get('input') or {}, ensure_ascii=False), False, b.get('id') or '', ts


def codex_events(path):
    for r in rows(path):
        p = r.get('payload') if r.get('type') == 'response_item' else None
        if not isinstance(p, dict):
            continue
        t, ts, cid = p.get('type'), iso(r.get('timestamp')), p.get('call_id') or ''
        if t == 'message' and p.get('role') in ('user', 'assistant'):
            yield p['role'], '', text_of(p.get('content')), False, '', ts
        elif t in ('function_call', 'local_shell_call', 'custom_tool_call'):
            yield 'call', p.get('name') or t, p.get('arguments') or p.get('input') or json.dumps(p.get('action') or {}), False, cid, ts
        elif t in ('function_call_output', 'custom_tool_call_output'):
            yield 'result', '', text_of(p.get('output')), False, cid, ts


def hermes_events(db, sid):
    con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
    for role, content, calls, tool, call_id, stamp in con.execute(
            'select role, content, tool_calls, tool_name, tool_call_id, timestamp from messages where session_id=? order by id', (sid,)):
        ts = iso(stamp)
        if role == 'user':
            yield 'user', '', content or '', False, '', ts
        elif role == 'tool':
            failed = bool(re.search(r'"exit_code": [1-9]|"error": "', (content or '')[:2000]))
            yield 'result', tool or '', content or '', failed, call_id or '', ts
        elif role == 'assistant':
            if (content or '').strip():
                yield 'assistant', '', content, False, '', ts
            for c in json.loads(calls) if calls else []:
                fn = c.get('function') or {}
                yield 'call', fn.get('name') or '', fn.get('arguments') or '', False, c.get('id') or '', ts


# --- discovery: each yields a session dict ------------------------------------

def file_sessions(harness, root, pattern, reader, cwd_of, parent_of, sid_of):
    for path in glob.glob(os.path.join(root, pattern), recursive=True):
        rel = os.path.relpath(path, root).replace('\\', '/')
        parent = parent_of(rel)
        yield {'harness': harness, 'session': sid_of(rel), 'parent': parent, 'child': bool(parent), 'when': os.path.getmtime(path),
               'cwd': lambda path=path: cwd_of(path), 'events': lambda path=path: reader(path), 'path': path}


def hermes_sessions(db):
    con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
    for sid, parent, cwd, started in con.execute('select id, parent_session_id, cwd, started_at from sessions'):
        yield {'harness': 'hermes', 'session': sid, 'parent': parent or '', 'child': bool(parent) or sid.startswith('cron_'),
               'when': started or 0, 'cwd': lambda cwd=cwd: cwd or '', 'events': lambda sid=sid: hermes_events(db, sid), 'path': db}


def stores():
    """(harness, location, iterator factory) for every store that exists."""
    stem = lambda rel: os.path.splitext(os.path.basename(rel))[0].split('_')[-1]
    cwd_json = r'"cwd":\s*"((?:[^"\\]|\\.)*)"'
    # A subagent's log sits in a directory named after its root session.
    omp_parent = lambda rel: rel.split('/')[1].split('_')[-1] if rel.count('/') > 1 else ''
    muse_parent = lambda rel: rel.split('/subagent/')[0].split('/')[-1] if '/subagent/' in rel else ''
    claude_parent = lambda rel: rel.split('/subagents/')[0].split('/')[-1] if '/subagents/' in rel else ''
    found = []
    for harness, root in (('omp', env_dir('', '.omp', 'agent', 'sessions')), ('pi', env_dir('', '.pi', 'agent', 'sessions'))):
        if os.path.isdir(root):
            found.append((harness, root, lambda h=harness, r=root: file_sessions(
                h, r, '**/*.jsonl', omp_events, lambda p: head_match(p, cwd_json), omp_parent, stem)))
    root = os.path.join(env_dir('XDG_DATA_HOME', '.local', 'share'), 'muse', 'sessions')
    if os.path.isdir(root):
        found.append(('muse', root, lambda r=root: file_sessions(
            'muse', r, '**/session.jsonl', muse_events, lambda p: head_match(p, r'workspace_root\\?":\s*\\?"((?:[^"\\]|\\\\.)*?)\\?"').replace('\\\\', '\\'),
            muse_parent, lambda rel: rel.split('/')[-2])))
    root = os.path.join(env_dir('CLAUDE_CONFIG_DIR', '.claude'), 'projects')
    if os.path.isdir(root):
        found.append(('claude', root, lambda r=root: file_sessions(
            'claude', r, '**/*.jsonl', claude_events, lambda p: head_match(p, cwd_json), claude_parent, stem)))
    root = os.path.join(env_dir('CODEX_HOME', '.codex'), 'sessions')
    if os.path.isdir(root):
        found.append(('codex', root, lambda r=root: file_sessions(
            'codex', r, '**/rollout-*.jsonl', codex_events, lambda p: head_match(p, cwd_json), lambda rel: '', stem)))
    for db in (os.path.join(env_dir('HERMES_HOME', '.hermes'), 'state.db'),
               os.path.join(os.environ.get('LOCALAPPDATA') or HOME, 'hermes', 'state.db')):
        if os.path.isfile(db) and os.path.getsize(db) > 0:
            found.append(('hermes', db, lambda d=db: hermes_sessions(d)))
            break
    return found


def select(args):
    want_cwd = norm(os.path.abspath(args.cwd)) if args.cwd else ''
    since = time.time() - args.days * 86400 if args.days else 0
    picked = []
    for harness, _, factory in stores():
        if args.harness and harness not in args.harness:
            continue
        for s in factory():
            if s['when'] < since:
                continue
            if args.session:
                # the named session, plus its subagents when --children is set
                if args.session not in s['session'] and not (args.children and args.session in s['parent']):
                    continue
            elif s['child'] and not args.children:
                continue
            picked.append(s)
    picked.sort(key=lambda s: -s['when'])
    out = []
    for s in picked:
        s['cwd'] = s['cwd']()
        if want_cwd and not norm(s['cwd']).startswith(want_cwd):
            continue
        out.append(s)
        if args.limit and len(out) >= args.limit:
            break
    return out


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['sources', 'list', 'prompts', 'calls', 'transcript'])
    ap.add_argument('--harness', action='append')
    ap.add_argument('--cwd')
    ap.add_argument('--days', type=float, default=7)
    ap.add_argument('--limit', type=int, default=10)
    ap.add_argument('--session')
    ap.add_argument('--children', action='store_true')
    ap.add_argument('--clip', type=int)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if args.command == 'sources':
        for harness, where, factory in stores():
            emit({'harness': harness, 'store': where, 'sessions': sum(1 for _ in factory())})
        return
    if args.session:
        args.days = args.limit = 0
    chosen = select(args)
    if args.command == 'list':
        for s in chosen:
            emit({'harness': s['harness'], 'session': s['session'], 'parent': s['parent'], 'cwd': s['cwd'], 'child': s['child'],
                  'when': time.strftime('%Y-%m-%d %H:%M', time.localtime(s['when'])), 'path': s['path']})
        return
    kinds = {'prompts': ('user',), 'calls': ('call', 'result'), 'transcript': ('user', 'assistant', 'call', 'result')}[args.command]
    clip = (4000 if args.command == 'transcript' else 400) if args.clip is None else args.clip
    for s in chosen:
        for kind, tool, text, error, call_id, ts in s['events']():
            if kind not in kinds or not (text or '').strip():
                continue
            text = SECRET.sub('<redacted>', text)
            if clip and len(text) > clip:
                text = text[:clip] + ' …[+%d chars]' % (len(text) - clip)
            emit({'harness': s['harness'], 'session': s['session'], 'parent': s['parent'], 'cwd': s['cwd'], 'child': s['child'],
                  'kind': kind, 'tool': tool, 'id': call_id, 'ts': ts, 'text': text, 'error': error})


if __name__ == '__main__':
    try:
        main()
    except (BrokenPipeError, OSError):  # reader closed the pipe (e.g. `| head`)
        os._exit(0)
