# -*- coding: utf-8 -*-
"""
mimotion 可视化页面

复用 main.py 的登录与提交逻辑（MiMotionRunner / zepp_helper）以及现有配置：
  - 配置来源优先级：环境变量 CONFIG(JSON)  >  USER/PWD  >  项目根目录 .env
  - 登录态复用 AES_KEY 加密的 encrypted_tokens.data

本地启动：
    pip install -r requirements.txt
    python web_app.py                 # 默认 http://127.0.0.1:5000
    PORT=8080 python web_app.py       # 自定义端口

公网部署建议设置访问口令：
    WEB_PASSWORD=你的口令 python web_app.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
import traceback
import uuid

from flask import Flask, jsonify, make_response, redirect, render_template, request


def resource_path(rel: str) -> str:
    """打包成单文件二进制后，资源会解压到 _MEIPASS，这里统一处理路径"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# 支持 DATA_DIR：指定 .env 与 encrypted_tokens.data 的存放目录（二进制/服务化部署时用）
DATA_DIR = os.environ.get("DATA_DIR", "").strip()
if DATA_DIR:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.chdir(DATA_DIR)

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

import main
import util.zepp_helper as zeppHelper  # noqa: F401  (确保 util 包被初始化，与 main.py 行为一致)

app = Flask(__name__, template_folder=resource_path("templates"))
try:
    app.json.ensure_ascii = False
except AttributeError:  # Flask < 2.3
    app.config["JSON_AS_ASCII"] = False

MAX_STEP_LIMIT = 200000

# region 配置与运行时状态
CONFIG: dict = {}
CONFIG_SOURCE = ""
CONFIG_ERROR = ""
AES_KEY: bytes | None = None
ENCRYPT_SUPPORT = False
USER_TOKENS: dict = {}
WEB_PASSWORD = os.environ.get("WEB_PASSWORD", "") or ""
SESSIONS: set[str] = set()
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def load_config() -> tuple[dict, str, str]:
    """按 main.py 的优先级加载配置，返回 (config, source, error)"""
    global CONFIG, CONFIG_SOURCE, CONFIG_ERROR
    raw = os.environ.get("CONFIG")
    if raw:
        try:
            cfg = dict(json.loads(raw))
            return cfg, "CONFIG 环境变量", ""
        except Exception:
            return {}, "CONFIG 环境变量", "CONFIG 不是合法 JSON，请检查配置"
    if os.environ.get("USER") and os.environ.get("PWD"):
        return {
            "USER": os.environ.get("USER"),
            "PWD": os.environ.get("PWD"),
            "MIN_STEP": os.environ.get("MIN_STEP", "18000"),
            "MAX_STEP": os.environ.get("MAX_STEP", "25000"),
            "PUSH_PLUS_TOKEN": os.environ.get("PUSH_PLUS_TOKEN", ""),
            "PUSH_PLUS_HOUR": os.environ.get("PUSH_PLUS_HOUR", ""),
            "PUSH_PLUS_MAX": os.environ.get("PUSH_PLUS_MAX", "30"),
            "PUSH_WECHAT_WEBHOOK_KEY": os.environ.get("PUSH_WECHAT_WEBHOOK_KEY", ""),
            "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID", ""),
            "SLEEP_GAP": os.environ.get("SLEEP_GAP", "5"),
            "USE_CONCURRENT": os.environ.get("USE_CONCURRENT", "False"),
        }, "USER/PWD 环境变量", ""
    return {}, "无", "未检测到 CONFIG 或 USER/PWD，请在环境变量或 .env 中配置"


def init_runtime():
    """初始化 main 模块所需的全局变量，使其中的逻辑可直接在 Web 环境复用"""
    global CONFIG, CONFIG_SOURCE, CONFIG_ERROR, AES_KEY, ENCRYPT_SUPPORT, USER_TOKENS
    CONFIG, CONFIG_SOURCE, CONFIG_ERROR = load_config()

    aes_key = os.environ.get("AES_KEY")
    if aes_key:
        key_bytes = aes_key.encode("utf-8")
        if len(key_bytes) == 16:
            AES_KEY = key_bytes
            ENCRYPT_SUPPORT = True
        else:
            print("AES_KEY 长度不是16位，已禁用登录态加密保存")

    main.aes_key = AES_KEY
    main.encrypt_support = ENCRYPT_SUPPORT
    if ENCRYPT_SUPPORT:
        USER_TOKENS = main.prepare_user_tokens()
    main.user_tokens = USER_TOKENS
    main.config = CONFIG
    main.time_bj = main.get_beijing_time()


def get_account_pairs() -> list[tuple[str, str]]:
    users = str(CONFIG.get("USER") or "").split("#")
    pwds = str(CONFIG.get("PWD") or "").split("#")
    pairs = []
    for i, u in enumerate(users):
        if not u.strip():
            continue
        pairs.append((u.strip(), pwds[i].strip() if i < len(pwds) else ""))
    return pairs


def get_sleep_gap() -> float:
    try:
        return max(float(str(CONFIG.get("SLEEP_GAP") or 5).strip()), 0)
    except ValueError:
        return 5.0


def get_time_range() -> tuple[int, int]:
    """当前北京时间对应的随机步数范围（与 main.py 逻辑一致）"""
    main.time_bj = main.get_beijing_time()
    return main.get_min_max_by_time()


# endregion


# region 任务执行
def job_log(job: dict, level: str, text: str):
    with JOBS_LOCK:
        job["logs"].append({"t": main.format_now(), "level": level, "text": text})


def cleanup_jobs():
    now = time.time()
    with JOBS_LOCK:
        for job_id in [k for k, v in JOBS.items() if now - v["created"] > 3600]:
            JOBS.pop(job_id, None)


def run_update_job(job_id: str, indices: list[int], mode: str, global_step: int, per_steps: dict):
    job = JOBS[job_id]
    pairs = get_account_pairs()
    sleep_gap = get_sleep_gap()
    success_count = 0
    total = 0
    try:
        job_log(job, "info", f"开始执行，选中账号 {len(indices)} 个，模式：{'按时间随机' if mode == 'auto' else '自定义步数'}")
        for n, idx in enumerate(indices):
            if idx < 0 or idx >= len(pairs):
                continue
            user, pwd = pairs[idx]
            name = main.desensitize_user_name(user)
            total += 1
            try:
                if mode == "auto":
                    min_step, max_step = get_time_range()
                    step = random.randint(min_step, max_step)
                else:
                    raw = per_steps.get(str(idx))
                    step = int(raw) if raw not in (None, "") else int(global_step)

                runner = main.MiMotionRunner(user, pwd)
                msg, ok = runner.login_and_post_step(step, step)
                for line in filter(None, str(runner.log_str).splitlines()):
                    job_log(job, "info", f"[{name}] {line}")
                if ok:
                    success_count += 1
                    job_log(job, "success", f"[{name}] {msg}")
                else:
                    job_log(job, "error", f"[{name}] {msg}")
                job["results"].append({"index": idx, "name": name, "step": step, "success": bool(ok), "msg": msg})
            except Exception:
                job_log(job, "error", f"[{name}] 执行异常：{traceback.format_exc()}")
                job["results"].append({"index": idx, "name": name, "step": None, "success": False, "msg": "执行异常"})

            if n < len(indices) - 1 and sleep_gap > 0:
                time.sleep(sleep_gap)

        if ENCRYPT_SUPPORT:
            try:
                main.persist_user_tokens()
                job_log(job, "info", "已加密保存登录态到 encrypted_tokens.data")
            except Exception:
                job_log(job, "error", f"保存登录态失败：{traceback.format_exc()}")

        job["summary"] = f"执行账号数 {total}，成功 {success_count}，失败 {total - success_count}"
        job_log(job, "info", job["summary"])
        job["status"] = "done"
    except Exception:
        job_log(job, "error", f"任务异常：{traceback.format_exc()}")
        job["status"] = "error"
        job["summary"] = "任务执行异常"


# endregion


# region 鉴权
@app.before_request
def check_auth():
    if not WEB_PASSWORD:
        return None
    if request.path in ("/login", "/healthz") or request.path.startswith("/api/login"):
        return None
    if request.cookies.get("mimotion_sid") in SESSIONS:
        return None
    if request.path.startswith("/api/"):
        return jsonify({"error": "未登录或登录已失效"}), 401
    return redirect("/login")


# endregion


# region 页面与接口
@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "time": main.format_now()})


@app.get("/login")
def login_page():
    return render_template("login.html", need_password=bool(WEB_PASSWORD))


@app.post("/api/login")
def api_login():
    password = (request.json or {}).get("password", "")
    if not WEB_PASSWORD:
        return jsonify({"ok": True})
    if password != WEB_PASSWORD:
        return jsonify({"ok": False, "error": "口令不正确"}), 401
    sid = uuid.uuid4().hex
    SESSIONS.add(sid)
    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie("mimotion_sid", sid, httponly=True, samesite="Lax", max_age=7 * 24 * 3600)
    return resp


@app.post("/api/logout")
def api_logout():
    sid = request.cookies.get("mimotion_sid")
    if sid:
        SESSIONS.discard(sid)
    resp = make_response(jsonify({"ok": True}))
    resp.delete_cookie("mimotion_sid")
    return resp


@app.get("/")
def index():
    return render_template("index.html", need_password=bool(WEB_PASSWORD))


@app.get("/api/status")
def api_status():
    pairs = get_account_pairs()
    accounts = [
        {"index": i, "name": main.desensitize_user_name(u), "valid": bool(p)}
        for i, (u, p) in enumerate(pairs)
    ]
    min_step, max_step = (0, 0)
    if pairs:
        try:
            min_step, max_step = get_time_range()
        except Exception:
            pass
    return jsonify({
        "ok": not CONFIG_ERROR,
        "error": CONFIG_ERROR,
        "config_source": CONFIG_SOURCE,
        "encrypt_support": ENCRYPT_SUPPORT,
        "accounts": accounts,
        "now": main.format_now(),
        "time_range": {"min": min_step, "max": max_step},
        "default_step": int(str(CONFIG.get("MIN_STEP") or 18000) or 18000),
        "sleep_gap": get_sleep_gap(),
        "use_concurrent": str(CONFIG.get("USE_CONCURRENT", "False")) == "True",
    })


@app.post("/api/update")
def api_update():
    if CONFIG_ERROR:
        return jsonify({"ok": False, "error": CONFIG_ERROR}), 400
    body = request.json or {}
    mode = "auto" if body.get("mode") == "auto" else "custom"
    indices = body.get("indices") or []
    try:
        indices = [int(i) for i in indices]
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "账号选择参数不正确"}), 400
    if not indices:
        return jsonify({"ok": False, "error": "请至少选择一个账号"}), 400

    per_steps = {}
    global_step = 0
    if mode == "custom":
        try:
            global_step = int(body.get("global_step"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "请填写有效的步数"}), 400
        for k, v in (body.get("steps") or {}).items():
            if v in (None, ""):
                continue
            try:
                per_steps[str(k)] = int(v)
            except (TypeError, ValueError):
                return jsonify({"ok": False, "error": f"账号步数[{v}]不是有效数字"}), 400

        candidates = [global_step] + list(per_steps.values())
        if any(s < 1 or s > MAX_STEP_LIMIT for s in candidates):
            return jsonify({"ok": False, "error": f"步数需在 1 ~ {MAX_STEP_LIMIT} 之间"}), 400

    if any(v["status"] == "running" for v in JOBS.values()):
        return jsonify({"ok": False, "error": "已有任务正在执行，请等待其结束后再提交"}), 409

    cleanup_jobs()
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "id": job_id,
        "status": "running",
        "logs": [],
        "results": [],
        "summary": "",
        "created": time.time(),
    }
    threading.Thread(
        target=run_update_job,
        args=(job_id, sorted(set(indices)), mode, global_step, per_steps),
        daemon=True,
    ).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/job/<job_id>")
def api_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"ok": False, "error": "任务不存在或已过期"}), 404
    with JOBS_LOCK:
        snapshot = {
            "ok": True,
            "id": job["id"],
            "status": job["status"],
            "logs": list(job["logs"]),
            "results": list(job["results"]),
            "summary": job["summary"],
        }
    return jsonify(snapshot)


# endregion


# 初始化配置与登录态（gunicorn 等 WSGI 方式启动时不会执行 __main__，因此在模块加载时初始化）
init_runtime()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8888"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"配置来源：{CONFIG_SOURCE}  账号数：{len(get_account_pairs())}  登录态加密保存：{ENCRYPT_SUPPORT}")
    if CONFIG_ERROR:
        print(f"配置异常：{CONFIG_ERROR}")
    print(f"可视化页面已启动： http://127.0.0.1:{port}")
    try:
        # 有 waitress 时用它，比 Flask 自带 server 更适合长期运行（二进制部署推荐）
        from waitress import serve

        print("使用 waitress 提供服务")
        serve(app, host=host, port=port, threads=8)
    except ImportError:
        app.run(host=host, port=port, debug=False, threaded=True)
