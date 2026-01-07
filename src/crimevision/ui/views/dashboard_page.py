import requests
from PySide6.QtCore import Signal, QObject, QThread
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame


class StatsWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url

    def run(self):
        try:
            r = requests.get(f"{self.base_url}/api/stats/dashboard", timeout=10)
            r.raise_for_status()
            self.finished.emit(r.json())
        except Exception as e:
            self.failed.emit(str(e))


class DashboardPage(QWidget):
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        super().__init__()
        self.api_base_url = api_base_url

        self.value_labels: dict[str, QLabel] = {}

        main_layout = QVBoxLayout(self)

        title = QLabel("CrimeVision Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self._stat_card("Total Incidents", "totalIncidents"))
        stats_layout.addWidget(self._stat_card("Incidents (7 days)", "incidents7d"))
        stats_layout.addWidget(self._stat_card("PDQs", "totalPdqs"))
        stats_layout.addWidget(self._stat_card("Users", "totalUsers"))
        main_layout.addLayout(stats_layout)

        main_layout.addWidget(QLabel("Recent Incidents (preview)"))
        main_layout.addWidget(QLabel("• Placeholder for table or list"))
        main_layout.addStretch()

        # load data once at startup
        self.refresh_stats()

    def _stat_card(self, title: str, key: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: gray;")

        value_label = QLabel("—")
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.value_labels[key] = value_label
        return frame

    def refresh_stats(self):
        # set placeholders while loading
        for lbl in self.value_labels.values():
            lbl.setText("…")

        self.thread = QThread(self)
        self.worker = StatsWorker(self.api_base_url)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_stats_loaded)
        self.worker.failed.connect(self._on_stats_failed)

        # cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_stats_loaded(self, data: dict):
        # Update labels from JSON keys
        self.value_labels["totalIncidents"].setText(str(data.get("totalIncidents", "—")))
        self.value_labels["incidents7d"].setText(str(data.get("incidents7d", "—")))
        self.value_labels["totalPdqs"].setText(str(data.get("totalPdqs", "—")))
        self.value_labels["totalUsers"].setText(str(data.get("totalUsers", "—")))

    def _on_stats_failed(self, err: str):
        for lbl in self.value_labels.values():
            lbl.setText("—")
        # optionally: show an error label / toast / status bar log
        print("Stats load failed:", err)
