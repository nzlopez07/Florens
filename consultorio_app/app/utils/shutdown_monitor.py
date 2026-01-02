import os
import threading

_clients = 0
_lock = threading.Lock()
_timer = None
_DELAY_SECONDS = 5.0
_last_seen_zero = None
_WATCHDOG_SECONDS = 15.0


def _watchdog():
    """Kills the process if we've been at 0 clients for too long (fallback)."""
    global _last_seen_zero
    while True:
        with _lock:
            if _clients == 0 and _last_seen_zero is not None:
                idle = time.monotonic() - _last_seen_zero
                if idle >= _WATCHDOG_SECONDS:
                    try:
                        print("[EXIT] Watchdog: no browser tabs active. Shutting down.")
                    except Exception:
                        pass
                    os._exit(0)
        time.sleep(2)


def on_connect():
    global _clients, _timer
    with _lock:
        _clients += 1
        _last_seen_zero = None
        # Cancel any pending shutdown
        if _timer is not None:
            try:
                _timer.cancel()
            except Exception:
                pass
            _timer = None


def on_disconnect():
    global _clients, _timer, _last_seen_zero
    with _lock:
        _clients = max(0, _clients - 1)
        if _clients == 0 and _timer is None:
            _timer = threading.Timer(_DELAY_SECONDS, _shutdown_if_still_idle)
            _timer.daemon = True
            _timer.start()
            _last_seen_zero = time.monotonic()


def _shutdown_if_still_idle():
    global _clients, _timer
    with _lock:
        _timer = None
        if _clients == 0:
            # Forcefully exit process; reliable even outside request context
            try:
                # Print to aid troubleshooting
                print("[EXIT] No browser tabs connected. Shutting down.")
            except Exception:
                pass
            os._exit(0)


# Start watchdog thread once on import
_wd_thread = threading.Thread(target=_watchdog, daemon=True)
_wd_thread.start()
