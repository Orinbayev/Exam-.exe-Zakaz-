"""
O'qituvchi paneli — ishga tushirish nuqtasi.
"""
import sys
import os

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

# ── PyInstaller MUHIM: barcha modullarni oldindan import qilish ───────────────
#
# PyInstaller statik tahlili funksiya ichidagi RELATIVE importlarni
# (masalan `from .windows.teacher.dashboard import TeacherDashboard`)
# ko'pincha o'tkazib yuboradi. Shu sababli barcha kerakli modullarni
# shu yerda ABSOLUTE import sifatida yozamiz.
#
import app.windows.teacher.dashboard        # noqa: F401
import app.windows.teacher.fan_widget       # noqa: F401
import app.windows.teacher.students_widget  # noqa: F401
import app.windows.teacher.questions_widget # noqa: F401
import app.windows.teacher.results_widget   # noqa: F401
import app.windows.teacher.stats_widget     # noqa: F401
import app.windows.teacher.tests_widget     # noqa: F401
import app.windows.superadmin.dashboard     # noqa: F401
import app.windows.student.info_window      # noqa: F401
import app.windows.student.exam_window      # noqa: F401
import app.windows.student.result_window    # noqa: F401
# ─────────────────────────────────────────────────────────────────────────────

from app.main import run

if __name__ == "__main__":
    run()
