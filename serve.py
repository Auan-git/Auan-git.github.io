"""
本地预览服务器
用法: python serve.py

自动打开浏览器访问网站。
"""

import http.server
import socketserver
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PORT = 8080
BASE_DIR = Path(__file__).parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = args[1] if len(args) > 1 else "---"
        path = args[0] if args else "---"
        parts = path.split()
        if len(parts) >= 2:
            path = parts[1]
        print(f"  [{timestamp}] {status}  {path}", flush=True)

    def log_error(self, format, *args):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{timestamp}] [错误] {args[0]}", flush=True)


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════╗
║     Edge's Web - 本地预览           ║
║     按 Ctrl+C 停止                  ║
╚══════════════════════════════════════╝
""", flush=True)

    try:
        server = socketserver.ThreadingTCPServer(("", PORT), Handler)
    except OSError:
        print(f"[错误] 端口 {PORT} 已被占用，请先关闭占用程序后重试", flush=True)
        print(f"       可以运行: netstat -ano | findstr :{PORT}", flush=True)
        sys.exit(1)

    server.allow_reuse_address = True
    server.daemon_threads = True  # 确保 Ctrl+C 能立即停止，不会卡在线程上
    url = f"http://localhost:{PORT}"
    print(f"[启动] {url}", flush=True)

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[停止] 服务已关闭", flush=True)
        server.shutdown()
