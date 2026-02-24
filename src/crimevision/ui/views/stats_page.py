from __future__ import annotations

import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QListWidget,
    QPushButton,
    QComboBox,
)

from crimevision.core.services.incident_service import IncidentService
from crimevision.core.db.database import get_db


def _card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    """Card UI: frame + title + content layout."""
    box = QFrame()
    box.setObjectName("card")

    layout = QVBoxLayout(box)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    t = QLabel(title)
    t.setObjectName("cardTitle")
    layout.addWidget(t)

    return box, layout, t


class StatsPage(QWidget):
    """
    StatsPage (analyse):
    - Graphique: incidents par jour (7/30/90 jours)
    - Listes: top categories, top PDQs (même période)
    - Pas de KPI (pour ne pas dupliquer Dashboard)
    """

    def __init__(self):
        super().__init__()

        self.incident_service = IncidentService()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Stats")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # -------------------------
        # Toolbar (période + refresh)
        # -------------------------
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        toolbar.addWidget(QLabel("Période:"))

        self.days_combo = QComboBox()
        self.days_combo.addItem("7 jours", 7)
        self.days_combo.addItem("30 jours", 30)
        self.days_combo.addItem("90 jours", 90)
        self.days_combo.setCurrentIndex(1)
        toolbar.addWidget(self.days_combo)

        toolbar.addStretch(1)

        self.btn_refresh = QPushButton("Refresh stats")
        toolbar.addWidget(self.btn_refresh)

        root.addLayout(toolbar)

        self.btn_refresh.clicked.connect(self.refresh)
        self.days_combo.currentIndexChanged.connect(self.refresh)

        # -------------------------
        # Main layout
        # -------------------------
        main = QHBoxLayout()
        main.setSpacing(10)
        root.addLayout(main, 1)

        # LEFT column
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        main.addLayout(left_col, 1)

        cat_card, cat_layout, _ = _card("Top categories")
        self.list_cat = QListWidget()
        cat_layout.addWidget(self.list_cat, 1)
        left_col.addWidget(cat_card, 2)

        pdq_card, pdq_layout, _ = _card("Top PDQs")
        self.list_pdq = QListWidget()
        pdq_layout.addWidget(self.list_pdq, 1)
        left_col.addWidget(pdq_card, 1)

        # RIGHT column (chart)
        chart_card, chart_layout, _ = _card("Incidents par jour")
        self._chart_container = QWidget()
        self._chart_container.setMinimumHeight(280)
        chart_layout.addWidget(self._chart_container, 1)
        main.addWidget(chart_card, 3)

        # Matplotlib state
        self._chart_ready = False
        self._chart_canvas = None
        self._chart_ax = None

        self._init_chart()
        self.refresh()

    # -------------------------
    # Matplotlib setup
    # -------------------------
    def _init_chart(self):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        except Exception:
            lay = QVBoxLayout(self._chart_container)
            msg = QLabel("Matplotlib not installed.\nChart disabled.")
            msg.setAlignment(Qt.AlignCenter)
            lay.addWidget(msg, 1)
            self._chart_ready = False
            return

        fig = Figure(figsize=(7, 3.2))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        lay = QVBoxLayout(self._chart_container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(canvas, 1)

        self._chart_canvas = canvas
        self._chart_ax = ax
        self._chart_ready = True

    def _style_dark_chart(self, fig, ax):
        panel = "#0b1220"
        fg = "#e2e8f0"
        grid = "#334155"

        fig.patch.set_facecolor(panel)
        ax.set_facecolor(panel)

        ax.tick_params(colors=fg)
        ax.title.set_color(fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)

        ax.grid(True, color=grid, alpha=0.35)
        for spine in ax.spines.values():
            spine.set_color(grid)

    # -------------------------
    # Refresh logic
    # -------------------------
    def refresh(self):
        days = int(self.days_combo.currentData() or 30)

        # Ensure Neon connection is alive
        try:
            get_db()
        except Exception as e:
            print("DB reconnect error:", e)
            traceback.print_exc()

        # ---------- Top Categories ----------
        try:
            top_cat = self.incident_service.top_categories(days=days, limit=10)
        except Exception as e:
            print("top_categories error:", e)
            traceback.print_exc()
            top_cat = []

        self.list_cat.clear()
        for x in top_cat:
            self.list_cat.addItem(f"{x['category']} — {x['count']}")

        # ---------- Top PDQs ----------
        try:
            top_pdq = self.incident_service.top_pdqs(days=days, limit=10)
        except Exception as e:
            print("top_pdqs error:", e)
            traceback.print_exc()
            top_pdq = []

        self.list_pdq.clear()
        for x in top_pdq:
            self.list_pdq.addItem(f"PDQ {x['pdqId']} — {x['count']}")

        # ---------- Chart ----------
        if not (self._chart_ready and self._chart_ax and self._chart_canvas):
            return

        try:
            series = self.incident_service.count_by_day(days=days)
        except Exception as e:
            print("count_by_day error:", e)
            traceback.print_exc()
            series = []

        ax = self._chart_ax
        fig = self._chart_canvas.figure

        ax.clear()
        self._style_dark_chart(fig, ax)

        if series:
            xs = [p["day"] for p in series]
            ys = [p["count"] for p in series]

            ax.plot(xs, ys, marker="o", linewidth=2)
            ax.set_title(f"Incidents par jour — {days} jours")
            ax.set_xlabel("Jour")
            ax.set_ylabel("Incidents")
            ax.tick_params(axis="x", labelrotation=30)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color="#e2e8f0")

        fig.tight_layout()
        self._chart_canvas.draw()