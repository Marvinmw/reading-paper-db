"""
论文浏览器 Web 服务
启动：python web_app.py
访问：http://127.0.0.1:7860
"""
import os
import json
import glob
import pty
import threading
import select
import struct
import fcntl
import termios
import signal
from pathlib import Path

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "output"
PAPERS_DIR  = OUTPUT_DIR / "papers"
REPORTS_DIR = OUTPUT_DIR / "reports"

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "papers-2025"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# (sid, term_id) -> {"master": fd, "proc": Popen, "alive": bool}
_terminals: dict = {}


# ── HTTP 路由 ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
def list_files():
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(PAPERS_DIR / "papers_*.json")), reverse=True)
    result = []
    for f in files:
        stem = Path(f).stem
        parts = stem.split("_")
        if len(parts) >= 3:
            d, t = parts[1], parts[2]
            result.append({
                "filename": Path(f).name,
                "label": f"{d[:4]}-{d[4:6]}-{d[6:8]} {t[:2]}:{t[2:]}",
            })
    return jsonify(result)


@app.route("/api/papers/<path:filename>")
def get_papers(filename):
    path = PAPERS_DIR / Path(filename).name
    if not path.exists() or not path.name.startswith("papers_"):
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.route("/api/reports")
def list_reports():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(REPORTS_DIR / "report_*.json")), key=os.path.getmtime, reverse=True)
    result = []
    def _fmt_dt(d, t=None):
        """YYYYMMDD[_HHMM] -> 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'."""
        s = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        if t and len(t) >= 4:
            s += f" {t[:2]}:{t[2:4]}"
        return s

    for f in files:
        stem = Path(f).stem
        parts = stem.split("_")
        if stem.startswith("report_pi_code_") and len(parts) >= 4:
            d = parts[3]
            t = parts[4] if len(parts) >= 5 else None
            label = f"💉×Code {_fmt_dt(d, t)}"
        elif stem.startswith("report_sec_se_") and len(parts) >= 4:
            d = parts[3]
            t = parts[4] if len(parts) >= 5 else None
            label = f"🔒×SE {_fmt_dt(d, t)}"
        elif stem.startswith("report_sec_") and len(parts) >= 3:
            d = parts[2]
            t = parts[3] if len(parts) >= 4 else None
            label = f"🔒 安全顶会 {_fmt_dt(d, t)}"
        elif len(parts) >= 3:
            d, t = parts[1], parts[2]
            label = _fmt_dt(d, t)
        else:
            label = stem
        result.append({"filename": Path(f).name, "label": label})
    return jsonify(result)


@app.route("/api/reports/<path:filename>")
def get_report(filename):
    path = REPORTS_DIR / Path(filename).name
    if not path.exists() or not path.name.startswith("report_"):
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


# ── File Browser / Editor ──────────────────────────────────────────────────────

_BASE_RESOLVED = BASE_DIR.resolve()
_SKIP_NAMES = {".git", "__pycache__", ".DS_Store", "node_modules"}
_WEB_EXTRA_CFG = BASE_DIR / ".claude" / "web-extra-roots.json"


def _load_all_roots() -> list[Path]:
    """Return [project_root] + additionalDirectories from Claude Code settings + web-extra-roots."""
    seen: set[Path] = {_BASE_RESOLVED}
    result: list[Path] = [_BASE_RESOLVED]

    # Read additionalDirectories from Claude Code settings (project first, then global)
    for cfg_file in [
        BASE_DIR / ".claude" / "settings.json",
        Path.home() / ".claude" / "settings.json",
    ]:
        if not cfg_file.exists():
            continue
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            for d in (cfg.get("permissions") or {}).get("additionalDirectories") or []:
                p = Path(d).expanduser().resolve()
                if p.is_dir() and p not in seen:
                    seen.add(p)
                    result.append(p)
        except Exception:
            pass

    # Web app's own persisted extra roots
    if _WEB_EXTRA_CFG.exists():
        try:
            for d in json.loads(_WEB_EXTRA_CFG.read_text(encoding="utf-8")):
                p = Path(d).expanduser().resolve()
                if p.is_dir() and p not in seen:
                    seen.add(p)
                    result.append(p)
        except Exception:
            pass

    return result


_ALL_ROOTS: list[Path] = _load_all_roots()


def _reload_roots() -> None:
    global _ALL_ROOTS
    _ALL_ROOTS = _load_all_roots()


def _safe_path(rel: str, root_idx: int = 0) -> "Path | None":
    """Resolve rel relative to the given root; return None on path-traversal attempt."""
    try:
        if root_idx < 0 or root_idx >= len(_ALL_ROOTS):
            return None
        root = _ALL_ROOTS[root_idx]
        p = (root / rel).resolve() if rel else root
        p.relative_to(root)
        return p
    except Exception:
        return None


@app.route("/api/roots")
def list_roots():
    _reload_roots()
    return jsonify([
        {
            "id": i,
            "path": str(r),
            "name": "项目目录" if i == 0 else r.name,
            "is_project": i == 0,
        }
        for i, r in enumerate(_ALL_ROOTS)
    ])


@app.route("/api/roots/add", methods=["POST"])
def add_root():
    data = request.get_json(force=True) or {}
    raw = data.get("path", "").strip()
    if not raw:
        return jsonify({"error": "路径为空"}), 400
    try:
        p = Path(raw).expanduser().resolve()
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if not p.is_dir():
        return jsonify({"error": f"目录不存在: {p}"}), 400
    if p in _ALL_ROOTS:
        return jsonify({"error": "该目录已在列表中"}), 400

    existing: list[str] = (
        json.loads(_WEB_EXTRA_CFG.read_text(encoding="utf-8"))
        if _WEB_EXTRA_CFG.exists() else []
    )
    existing.append(str(p))
    _WEB_EXTRA_CFG.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _reload_roots()
    return jsonify({"ok": True, "id": _ALL_ROOTS.index(p)})


@app.route("/api/roots/remove", methods=["POST"])
def remove_root():
    data = request.get_json(force=True) or {}
    root_id = int(data.get("id", -1))
    if root_id <= 0 or root_id >= len(_ALL_ROOTS):
        return jsonify({"error": "无效 id（项目目录不可移除）"}), 400

    target = _ALL_ROOTS[root_id]
    existing: list[str] = (
        json.loads(_WEB_EXTRA_CFG.read_text(encoding="utf-8"))
        if _WEB_EXTRA_CFG.exists() else []
    )
    existing = [d for d in existing if Path(d).expanduser().resolve() != target]
    _WEB_EXTRA_CFG.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _reload_roots()
    return jsonify({"ok": True})


@app.route("/api/fs/list")
def fs_list():
    rel = request.args.get("path", "")
    root_idx = int(request.args.get("root", 0))
    target = _safe_path(rel, root_idx)
    if target is None or not target.is_dir():
        return jsonify({"error": "invalid path"}), 400
    root = _ALL_ROOTS[root_idx]
    items = []
    for child in sorted(target.iterdir(),
                        key=lambda x: (x.is_file(), x.name.lower())):
        if child.name in _SKIP_NAMES or child.suffix == ".pyc":
            continue
        rel_child = str(child.relative_to(root))
        st = child.stat()
        items.append({
            "name": child.name,
            "path": rel_child,
            "is_dir": child.is_dir(),
            "size": st.st_size if child.is_file() else 0,
            "ext": child.suffix.lower(),
            "mtime": st.st_mtime,
        })
    return jsonify(items)


@app.route("/api/fs/read")
def fs_read():
    rel = request.args.get("path", "")
    root_idx = int(request.args.get("root", 0))
    p = _safe_path(rel, root_idx)
    if p is None or not p.is_file():
        return jsonify({"error": "not found"}), 404
    if p.stat().st_size > 2 * 1024 * 1024:
        return jsonify({"error": "file too large (>2 MB)"}), 400
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    root = _ALL_ROOTS[root_idx]
    return jsonify({
        "content": content,
        "path": str(p.relative_to(root)),
        "name": p.name,
    })


@app.route("/api/fs/write", methods=["POST"])
def fs_write():
    data = request.get_json(force=True) or {}
    rel  = data.get("path", "")
    root_idx = int(data.get("root", 0))
    content = data.get("content", "")
    p = _safe_path(rel, root_idx)
    if p is None or not p.is_file():
        return jsonify({"error": "file not found"}), 404
    try:
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.get_json() or {}
    api_key = data.get("api_key", "").strip()
    title    = data.get("title", "")
    abstract = data.get("abstract", "")

    if not api_key:
        return jsonify({"error": "请先填写 Claude API Key"}), 400
    if not abstract:
        return jsonify({"error": "该论文无摘要内容"}), 400

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    "请用中文总结这篇学术论文，包含：①核心问题 ②方法亮点 ③主要结论，100字以内。\n\n"
                    f"标题：{title}\n\n摘要：{abstract[:1500]}"
                ),
            }],
        )
        return jsonify({"summary": msg.content[0].text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Terminal WebSocket ────────────────────────────────────────────────────────

@socketio.on("term_start")
def term_start(data):
    sid = request.sid
    term_id = str(data.get("term_id", "1"))
    key = (sid, term_id)
    _close_terminal(key)

    cols = int(data.get("cols", 120))
    rows = int(data.get("rows", 30))

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ,
                struct.pack("HHHH", rows, cols, 0, 0))

    import subprocess
    proc = subprocess.Popen(
        ["/bin/zsh"],
        stdin=slave, stdout=slave, stderr=slave,
        close_fds=True,
        cwd=str(BASE_DIR),
        env={**os.environ,
             "TERM": "xterm-256color",
             "HOME": str(Path.home()),
             "LANG": "en_US.UTF-8"},
        preexec_fn=os.setsid,
    )
    os.close(slave)
    _terminals[key] = {"master": master, "proc": proc, "alive": True}

    def _reader():
        while _terminals.get(key, {}).get("alive"):
            try:
                r, _, _ = select.select([master], [], [], 0.02)
                if r:
                    chunk = os.read(master, 1024)
                    socketio.emit("term_output",
                                  {"term_id": term_id,
                                   "data": chunk.decode("utf-8", errors="replace")},
                                  to=sid)
            except (OSError, IOError):
                break

    threading.Thread(target=_reader, daemon=True).start()


@socketio.on("term_input")
def term_input(data):
    term_id = str(data.get("term_id", "1"))
    sess = _terminals.get((request.sid, term_id))
    if sess:
        try:
            os.write(sess["master"], data["data"].encode("utf-8"))
        except OSError:
            pass


@socketio.on("term_resize")
def term_resize(data):
    term_id = str(data.get("term_id", "1"))
    sess = _terminals.get((request.sid, term_id))
    if sess:
        try:
            fcntl.ioctl(sess["master"], termios.TIOCSWINSZ,
                        struct.pack("HHHH", data["rows"], data["cols"], 0, 0))
        except OSError:
            pass


@socketio.on("term_close")
def term_close(data):
    term_id = str(data.get("term_id", "1"))
    _close_terminal((request.sid, term_id))


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    keys = [k for k in list(_terminals) if k[0] == sid]
    for key in keys:
        _close_terminal(key)


def _close_terminal(key):
    sess = _terminals.pop(key, None)
    if not sess:
        return
    sess["alive"] = False
    try:
        os.killpg(os.getpgid(sess["proc"].pid), signal.SIGTERM)
    except Exception:
        pass
    try:
        os.close(sess["master"])
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 7860
    print(f"\n论文浏览器已启动 → http://127.0.0.1:{port}\n")
    socketio.run(app, host="127.0.0.1", port=port, debug=False, allow_unsafe_werkzeug=True)
