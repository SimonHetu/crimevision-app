from __future__ import annotations
import os
from PySide6.QtGui import QFont
from pathlib import Path
from PySide6.QtCore import Qt, QProcess
from PySide6.QtWidgets import QProgressBar
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QPlainTextEdit, QLineEdit, QFileDialog
)

def _card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    """Carte UI réutilisable (bloc stylé + titre)."""
    box = QFrame()
    box.setObjectName("card")

    layout = QVBoxLayout(box)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    t = QLabel(title)
    t.setObjectName("cardTitle")
    layout.addWidget(t)

    return box, layout, t


class ImportsPage(QWidget):
    """
    ImportsPage:
    - Choisir le repo backend (cwd = repo root)
    - Bouton Import Incidents (avec --max)
    - Bouton Import Latest Incidents
    - Logs live, Stop
    """

    def __init__(self, backend_dir: str | None = None):
        super().__init__()

        # Dossier backend = racine du repo (où est package.json)
        self.backend_path = Path(backend_dir).resolve() if backend_dir else None

        # Process non-bloquant (UI reste fluide)
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)

        # -------- UI root --------
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Imports / Scripts (DEV)")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # -------- Config backend --------
        cfg_card, cfg_layout, _ = _card("Configuration")
        root.addWidget(cfg_card)

        row = QHBoxLayout()
        cfg_layout.addLayout(row)

        self.txt_backend = QLineEdit()
        self.txt_backend.setPlaceholderText("Chemin du repo backend (ex: D:/.../crimevision-backend)")
        if self.backend_path:
            self.txt_backend.setText(str(self.backend_path))

        btn_browse = QPushButton("Parcourir…")
        btn_browse.clicked.connect(self._browse_backend)

        btn_save = QPushButton("Sauver")
        btn_save.clicked.connect(self._save_backend_path)

        row.addWidget(QLabel("Backend repo:"))
        row.addWidget(self.txt_backend, 1)
        row.addWidget(btn_browse)
        row.addWidget(btn_save)

        # -------- Actions --------
        actions_card, actions_layout, _ = _card("Actions")
        root.addWidget(actions_card)

        # Ligne 1: Incidents + max
        line1 = QHBoxLayout()
        actions_layout.addLayout(line1)

        self.txt_max = QLineEdit()
        self.txt_max.setPlaceholderText("max (ex: 1000, 5000, all)")
        self.txt_max.setText("1000")

        self.btn_incidents = QPushButton("Importer Incidents")
        self.btn_incidents.clicked.connect(self._run_import_incidents_with_max)

        line1.addWidget(QLabel("--max="))
        line1.addWidget(self.txt_max)
        line1.addWidget(self.btn_incidents)
        line1.addStretch(1)

        # Ligne 2: Latest + Stop
        line2 = QHBoxLayout()
        actions_layout.addLayout(line2)

        self.btn_latest = QPushButton("Importer Latest Incidents")
        self.btn_latest.clicked.connect(self._run_import_latest_incidents)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self._stop)

        line2.addWidget(self.btn_latest)
        line2.addStretch(1)
        line2.addWidget(self.btn_stop)

        # Logs
        log_card, log_layout, _ = _card("Logs")
        root.addWidget(log_card, 2)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("console")
        log_layout.addWidget(self.log, 1)

        
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.Monospace)
        self.log.setFont(mono)

        # Loading indicator
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 0,0 = infinite loading animation
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        # QProcess signals
        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.readyReadStandardError.connect(self._on_output)
        self.proc.started.connect(lambda: self._set_running(True))
        self.proc.finished.connect(self._on_finished)

        self._set_running(False)

    # -------------------------
    # UI helpers
    # -------------------------
    def _append(self, text: str):
        """Append log + auto-scroll."""
        self.log.appendPlainText(text.rstrip("\n"))

    def _set_running(self, running: bool):
        """Disable actions when running + show loading bar."""
        self.btn_incidents.setEnabled(not running)
        self.btn_latest.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.progress.setVisible(running)

    def _npx(self) -> str:
        return "npx.cmd" if os.name == "nt" else "npx"

    def _browse_backend(self):
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier backend (repo root)")
        if path:
            self.txt_backend.setText(path)

    def _save_backend_path(self):
        p = Path(self.txt_backend.text().strip())
        if not p.exists() or not p.is_dir():
            self._append("❌ Chemin backend invalide.")
            return

        # validation: package.json devrait exister au root
        if not (p / "package.json").exists():
            self._append("⚠️ Ce dossier ne semble pas être le root du backend (package.json introuvable).")
            self._append("   Choisis plutôt: .../crimevision-backend")
            return

        self.backend_path = p.resolve()
        self._append(f"✅ Backend repo défini: {self.backend_path}")

    def _ensure_backend(self) -> bool:
        if not self.backend_path:
            self._append("❌ Backend repo non défini.")
            return False
        if not self.backend_path.exists():
            self._append("❌ Backend repo introuvable.")
            return False
        return True

    # -------------------------
    # Core runner
    # -------------------------
    def _run(self, program: str, args: list[str]):
        """
        Lance une commande non-bloquante dans le repo backend.
        program: "npx"
        args: ["tsx", "src/scripts/importIncidents.ts", "--max=1000"]
        """
        if self.proc.state() != QProcess.NotRunning:
            self._append("⚠️ Un import est déjà en cours.")
            return
        if not self._ensure_backend():
            return

        self._append("")
        self._append("────────────────────────────────────────")
        self._append(f"▶ {program} {' '.join(args)}")
        self._append(f"(cwd: {self.backend_path})")

        self.proc.setWorkingDirectory(str(self.backend_path))

        # Windows: parfois il faut "npx.cmd" si "npx" n'est pas résolu
        # Essaye d'abord "npx", si ça fail souvent chez toi: remplace par "npx.cmd"
        self.proc.start(program, args)

        if not self.proc.waitForStarted(1500):
            self._append("❌ Impossible de démarrer le process (Node/npx pas dans PATH?).")
            self._append("   Astuce: essaie program='npx.cmd' sur Windows.")
            self._set_running(False)

    # -------------------------
    # Actions
    # -------------------------
    def _run_import_incidents_with_max(self):
        """
        Exécute:
          npx tsx src/scripts/importIncidents.ts --max=...
        """
        raw = self.txt_max.text().strip().lower()

        # Normalise
        if raw in ("", "all", "tout", "∞", "infinity"):
            max_arg = "--max=all"
        else:
            # valide que c'est un entier > 0
            try:
                n = int(raw)
                if n <= 0:
                    raise ValueError()
                max_arg = f"--max={n}"
            except Exception:
                self._append("❌ Valeur invalide pour max. Exemples: 1000, 5000, all")
                return

        self._run(self._npx(), ["tsx", "src/scripts/importIncidents.ts", max_arg])

    def _run_import_latest_incidents(self):
        """
        Exécute:
          npx tsx src/scripts/importLatestIncidents.ts
        (adapte le nom si ton fichier s'appelle autrement)
        """
        self._run(self._npx(), ["tsx", "src/scripts/importLatestIncidents.ts"])

    def _stop(self):
        if self.proc.state() == QProcess.NotRunning:
            return
        self._append("⏹️ Stop demandé…")
        self.proc.kill()

    # -------------------------
    # QProcess callbacks
    # -------------------------
    def _on_output(self):
        data = self.proc.readAllStandardOutput().data()
        if data:
            self._append(data.decode("utf-8", errors="replace"))

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        ok = (exit_code == 0 and exit_status == QProcess.NormalExit)
        self._append("✅ Terminé." if ok else f"❌ Terminé avec erreur (code={exit_code}).")
        self._set_running(False)
