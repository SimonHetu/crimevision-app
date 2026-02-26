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
    QListWidgetItem,
    QPushButton,
    QComboBox,
)

from crimevision.core.services.incident_service import IncidentService
from crimevision.core.db.database import get_db


# =========================================================
# UI HELPER — CARD
# ---------------------------------------------------------
# Helper pour créer une "carte" (QFrame) uniforme :
# - un titre
# - un layout vertical interne
# Utilisé pour les sections: Top categories, Top PDQs, Graphique
# =========================================================

def _card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    """Carte UI : frame + titre + layout de contenu."""
    box = QFrame()
    box.setObjectName("card")

    layout = QVBoxLayout(box)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    t = QLabel(title)
    t.setObjectName("cardTitle")
    layout.addWidget(t)

    return box, layout, t

# =========================================================
# STATS PAGE 
# ---------------------------------------------------------
# Rôle:
# - Afficher des statistiques d’incidents sur une période (7/30/90 jours)
# - Deux listes à gauche:
#     1) Top catégories
#     2) Top PDQs
# - Un graphique à droite:
#     - Incidents par jour
# - Interaction:
#     - Clic sur une catégorie => filtre le graphique (toggle)
#       (re-clic sur la même catégorie => reset du filtre)
# =========================================================
class StatsPage(QWidget):
    """
    StatsPage (analyse):
    - Graphique: incidents par jour (7/30/90 jours)
    - Listes: top categories, top PDQs (même période)
    - Click sur une catégorie => filtre le graphique (toggle)
    """

    def __init__(self):
        super().__init__()

        # Service qui encapsule les requêtes Peewee / SQL
        self.incident_service = IncidentService()

        # Catégorie sélectionnée pour filtrer le graphique
        # None => aucun filtre (graph = toutes catégories)
        self._selected_category: str | None = None

        # =========================================================
        # LAYOUT RACINE
        # =========================================================
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Stats")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # =========================================================
        # TOOLBAR — choix de période + bouton refresh
        # =========================================================
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        toolbar.addWidget(QLabel("Période:"))

        # Combo période (valeurs stockées dans currentData)
        self.days_combo = QComboBox()
        self.days_combo.addItem("7 jours", 7)
        self.days_combo.addItem("30 jours", 30)
        self.days_combo.addItem("90 jours", 90)
        self.days_combo.setCurrentIndex(1)  # 30 jours
        toolbar.addWidget(self.days_combo)

        # Push le bouton refresh à droite
        toolbar.addStretch(1)

        # Événements UI => refresh des données
        self.btn_refresh = QPushButton("Refresh stats")
        toolbar.addWidget(self.btn_refresh)

        root.addLayout(toolbar)

        self.btn_refresh.clicked.connect(self.refresh)
        self.days_combo.currentIndexChanged.connect(self.refresh)

         # =========================================================
        # MAIN — colonne gauche (listes) + colonne droite (graph)
        # =========================================================
        main = QHBoxLayout()
        main.setSpacing(10)
        root.addLayout(main, 1)

        # LEFT column
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        main.addLayout(left_col, 1)

        # Carte Top categories
        cat_card, cat_layout, _ = _card("Top categories")
        self.list_cat = QListWidget()

        # Interaction: clic sur une catégorie => toggle du filtre graphique
        self.list_cat.itemClicked.connect(self._on_category_clicked)
        self.list_cat.setToolTip("Clique une catégorie pour filtrer le graphique (re-clique pour reset).")
        cat_layout.addWidget(self.list_cat, 1)
        left_col.addWidget(cat_card, 2)

        # Carte Top PDQs
        pdq_card, pdq_layout, _ = _card("Top PDQs")
        self.list_pdq = QListWidget()
        pdq_layout.addWidget(self.list_pdq, 1)
        left_col.addWidget(pdq_card, 1)

        # RIGHT COLUMN — Graphique
        chart_card, chart_layout, _ = _card("Incidents par jour")
        self._chart_container = QWidget()
        self._chart_container.setMinimumHeight(280)
        chart_layout.addWidget(self._chart_container, 1)
        main.addWidget(chart_card, 3)

        # État matplotlib (initialisé dans _init_chart)
        self._chart_ready = False
        self._chart_canvas = None
        self._chart_ax = None

        # Init du graphique + 1er chargement
        self._init_chart()
        self.refresh()

    # =========================================================
    # EVENT — clic sur une catégorie (toggle filtre)
    # =========================================================
    def _on_category_clicked(self, item: QListWidgetItem):
        """
        Toggle:
        - si on clique la même catégorie => reset (None)
        - sinon => on applique cette catégorie comme filtre
        """
        cat = item.data(Qt.UserRole)

        # toggle: click same category again => reset
        if self._selected_category == cat:
            self._selected_category = None
            self.list_cat.clearSelection()
        else:
            self._selected_category = cat

        # Refresh pour recharger le graphique avec le nouveau filtre
        self.refresh()

    # =========================================================
    # MATPLOTLIB SETUP
    # ---------------------------------------------------------
    # Crée un canvas matplotlib intégré à Qt.
    # Si matplotlib n’est pas installé => on affiche un message.
    # =========================================================
    def _init_chart(self):
        """Init matplotlib canvas (optional dep)."""
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        except Exception:
            lay = QVBoxLayout(self._chart_container)
            msg = QLabel("Matplotlib not installed.\nChart disabled (lists still work).")
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

    # =========================================================
    # STYLE DARK — matplotlib
    # ---------------------------------------------------------
    # Harmonise le graphique avec le thème sombre (QSS).
    # =========================================================
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

    # =========================================================
    # REFRESH — charge données + met à jour UI
    # ---------------------------------------------------------
    # 1) Assure que la DB est vivante
    # 2) Charge top catégories + remplit list_cat
    # 3) Charge top PDQs + remplit list_pdq
    # 4) Charge série incidents/jour (filtrée ou non) + redessine le chart
    # =========================================================
    def refresh(self):

        # Valeur choisie dans la combo (7/30/90)
        days = int(self.days_combo.currentData() or 30)

        # (Neon) Ping/reconnect DB
        try:
            get_db()
        except Exception as e:
            print("DB reconnect error:", e)
            traceback.print_exc()

        # TOP CATÉGORIES
        try:
            top_cat = self.incident_service.top_categories(days=days, limit=10)
        except Exception as e:
            print("top_categories error:", e)
            traceback.print_exc()
            top_cat = []

        # On évite de relancer l’événement itemClicked pendant qu’on reconstruit la liste
        self.list_cat.blockSignals(True)
        self.list_cat.clear()

        for x in top_cat:
            cat = x.get("category") or ""
            cnt = x.get("count") or 0

            item = QListWidgetItem(f"{cat} — {cnt}")

            # On stocke la vraie valeur dans Qt.UserRole pour éviter de parser
            item.setData(Qt.UserRole, cat)
            self.list_cat.addItem(item)

            # Restaure la sélection visuelle si c’est le filtre actif
            if self._selected_category and cat == self._selected_category:
                item.setSelected(True)

        self.list_cat.blockSignals(False)

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

        # GRAPHIQUE — Incidents par jour
        if not (self._chart_ready and self._chart_ax and self._chart_canvas):
            return

        try:
            # On passe category=self._selected_category
            series = self.incident_service.count_by_day(days=days, category=self._selected_category)
        except Exception as e:
            print("count_by_day error:", e)
            traceback.print_exc()
            series = []

        ax = self._chart_ax
        fig = self._chart_canvas.figure

        ax.clear()
        self._style_dark_chart(fig, ax)

        if series:
            xs = [p["day"] for p in series]   # strings "YYYY-MM-DD"
            ys = [p["count"] for p in series]

            n = len(xs)
            x_idx = list(range(n))            # X = indices 

            ax.plot(x_idx, ys, marker="o", linewidth=2)

            # Titre dynamique
            if self._selected_category:
                ax.set_title(f"{self._selected_category} — incidents/jour — {days} jours")
            else:
                ax.set_title(f"Incidents par jour — {days} jours")

            ax.set_xlabel("Jour")
            ax.set_ylabel("Incidents")

            if days >= 90:
                step = 7 
                labelsize = 7
                rotation = 30
            elif days >= 30:
                step = 2
                labelsize = 8
                rotation = 30
            else:
                step = 1
                labelsize = 9
                rotation = 20

            tick_idx = list(range(0, n, step))
            ax.set_xticks(tick_idx)

            ax.set_xticklabels([xs[i] for i in tick_idx], rotation=rotation, ha="right")
            ax.set_xlabel("Jour", labelpad=12)
            ax.set_ylabel("Incidents", labelpad=10)
            ax.tick_params(axis="x", labelsize=labelsize)

        else:
            ax.set_title("Incidents par jour")
            ax.set_xlabel("Jour")
            ax.set_ylabel("Incidents")
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color="#e2e8f0")

        fig.tight_layout()
        self._chart_canvas.draw()