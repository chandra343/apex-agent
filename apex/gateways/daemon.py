"""24/7 Multi-Platform Messaging Gateway Daemon Controller."""
from __future__ import annotations

import os
import signal
import sys
import time
import threading
from pathlib import Path
from apex.config import DATA_DIR, config
from apex.gateways.adapters.telegram import telegram_adapter
from apex.gateways.adapters.webhook import start_webhook_server
from apex.scheduler.scheduler import task_scheduler

PID_FILE = DATA_DIR / "gateway.pid"


class GatewayDaemon:
    """Orchestrates background messaging services, schedulers, and webhooks."""

    def __init__(self) -> None:
        pass

    def run_foreground(self) -> None:
        """Run all enabled gateways synchronously in foreground."""
        print("🚀 Starting Project Apex Gateway Daemon (Foreground)...")
        self._write_pid()

        # Start Scheduler Loop
        task_scheduler.start_loop()
        print("✔ In-App Task Scheduler started.")

        # Start Webhook Server
        ws_host = config.get("gateways.websocket.host", "127.0.0.1")
        ws_port = config.get("gateways.websocket.port", 20129)
        start_webhook_server(ws_host, ws_port)
        print(f"✔ Authenticated Webhook Server listening on {ws_host}:{ws_port}")

        # Start Telegram Adapter in main or worker thread
        tg_thread = threading.Thread(target=telegram_adapter.start_polling, daemon=True)
        tg_thread.start()

        print("✔ Gateway services active. Press Ctrl+C to terminate.")
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nShutting down gateway daemon...")
            self.stop()

    def start(self, foreground: bool = False) -> None:
        if self.is_running():
            print("Gateway daemon is already running.")
            return

        if foreground:
            self.run_foreground()
        else:
            # Fork into background on POSIX
            if sys.platform != "win32":
                pid = os.fork()
                if pid > 0:
                    print(f"✔ Project Apex Gateway started in background (PID: {pid})")
                    return
                os.setsid()
                self.run_foreground()
            else:
                print("Background daemon mode: running in foreground on Windows.")
                self.run_foreground()

    def stop(self) -> None:
        telegram_adapter.stop()
        task_scheduler.stop()

        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            PID_FILE.unlink(missing_ok=True)
        print("✔ Gateway daemon stopped.")

    def is_running(self) -> bool:
        if not PID_FILE.exists():
            return False
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return True
        except Exception:
            PID_FILE.unlink(missing_ok=True)
            return False

    def status(self) -> None:
        if self.is_running():
            pid = PID_FILE.read_text().strip()
            print(f"🟢 Project Apex Gateway Daemon is RUNNING (PID: {pid})")
        else:
            print("⚪ Project Apex Gateway Daemon is STOPPED.")

    def _write_pid(self) -> None:
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))


# Global daemon controller
gateway_daemon = GatewayDaemon()
