"""
Ovoz effektlari — macOS afplay, daemon thread-larda.
Grade 5: Hero fanfar + real qarsak MP3 (8 soniya), parallel.
"""
import subprocess, threading, os

_SYS = {
    "click":  "/System/Library/Sounds/Pop.aiff",
    "hero":   "/System/Library/Sounds/Hero.aiff",
    "glass":  "/System/Library/Sounds/Glass.aiff",
    "ping":   "/System/Library/Sounds/Ping.aiff",
    "basso":  "/System/Library/Sounds/Basso.aiff",
}

# Real qarsak ovozi fayli — exe ichida ham, oddiy Python-da ham ishlaydi
import sys as _sys

def _asset_path(rel: str) -> str:
    """PyInstaller _MEIPASS yoki oddiy fayl yo'li."""
    if getattr(_sys, "frozen", False):
        base = getattr(_sys, "_MEIPASS", "")
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

_APPLAUSE_MP3 = _asset_path(os.path.join("assets", "sounds", "applause.mp3"))


def _afplay(path: str, vol: float, duration: float = 0):
    """Sinxron ijro — faqat thread ichida."""
    try:
        if not (path and os.path.exists(path)):
            return
        cmd = ["afplay", "-v", f"{vol:.2f}"]
        if duration > 0:
            cmd += ["-t", str(duration)]
        cmd.append(path)
        subprocess.run(cmd, capture_output=True, timeout=duration + 5 if duration else 15)
    except Exception:
        pass


def play(name: str, volume: float = 0.75):
    """Bitta tizim ovozini background-da ijro etadi."""
    path = _SYS.get(name, "")
    threading.Thread(target=_afplay, args=(path, volume), daemon=True).start()


def prewarm():
    """(Endi kerak emas — MP3 to'g'ridan-to'g'ri ijro etiladi.)"""
    pass


def play_grade(grade: int):
    """
    Baho bo'yicha ovoz:
      5 — Hero fanfar (darhol) + qarsak MP3 8s (parallel)
      4 — Glass + Ping
      3 — Ping
      2 — Basso
    """
    if grade == 5:
        # ── Thread 1: Hero fanfar — DARHOL ───────────────────────────────────
        def _hero():
            _afplay(_SYS["hero"], 1.00)

        # ── Thread 2: Real qarsak MP3 — 0.4s kechikish bilan, 8 sekund ───────
        def _applause():
            import time
            time.sleep(0.4)                          # Hero boshlanib olsin
            _afplay(_APPLAUSE_MP3, 0.92, duration=8) # faqat 8 soniya

        threading.Thread(target=_hero,     daemon=True).start()
        threading.Thread(target=_applause, daemon=True).start()

    elif grade == 4:
        def _good():
            import time
            _afplay(_SYS["glass"], 0.90)
            time.sleep(0.35)
            _afplay(_SYS["ping"], 0.72)
        threading.Thread(target=_good, daemon=True).start()

    elif grade == 3:
        threading.Thread(
            target=_afplay, args=(_SYS["ping"], 0.80), daemon=True
        ).start()

    else:  # grade 2
        threading.Thread(
            target=_afplay, args=(_SYS["basso"], 0.65), daemon=True
        ).start()
