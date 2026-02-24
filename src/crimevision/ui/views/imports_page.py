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


# =========================================================
# UI HELPERS
# =========================================================

def _card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    """
    Construit une "carte" UI réutilisable:
    - QFrame stylé via QSS (objectName="card")
    - Titre en haut (objectName="cardTitle")
    """
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
# IMPORTS PAGE
# =========================================================
class ImportsPage(QWidget):
    """
    ImportsPage:
    - Permet de choisir le repo backend (root)
    - Lance des scripts Node (via npx + tsx) sans bloquer l'UI
    - Affiche les logs en direct dans une console
    - Permet d'arrêter un import (Stop)
    - Montre un "loading" pendant l'exécution (QProgressBar indéterminée)
    """

    def __init__(self, backend_dir: str | None = None):
        super().__init__()

        # --------------------
        # STATE / PROCESS
        # --------------------
        # Dossier backend = racine du repo (où se trouve package.json)
        self.backend_path = Path(backend_dir).resolve() if backend_dir else None

        # QProcess = exécute un processus externe de manière asynchrone
        # -> l'interface reste fluide pendant l'import
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)

        # ---------------------------------------------------------
        # UI ROOT
        # ---------------------------------------------------------
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("Imports")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # ---------------------------------------------------------
        # CONFIG BACKEND (path du repo backend)
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # ACTIONS (boutons d'import + max + stop)
        # ---------------------------------------------------------
        actions_card, actions_layout, _ = _card("Actions")
        root.addWidget(actions_card)

        # Ligne 1: Import incidents avec argument --max
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

        # ---------------------------------------------------------
        # LOGS (console)
        # ---------------------------------------------------------
        log_card, log_layout, _ = _card("Logs")
        root.addWidget(log_card, 2)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("console")
        log_layout.addWidget(self.log, 1)

        # Police monospace pour un rendu "terminal"
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.Monospace)
        self.log.setFont(mono)

        # ---------------------------------------------------------
        # LOADING INDICATOR
        # ---------------------------------------------------------
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 0,0 = infinite loading animation
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        # ---------------------------------------------------------
        # QPROCESS SIGNALS
        # ---------------------------------------------------------

        # Quand il y a du output à lire (stdout/stderr), on l'ajoute aux logs
        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.readyReadStandardError.connect(self._on_output)

        # started/finished -> verrouille/déverrouille l'UI et affiche/masque le loading
        self.proc.started.connect(lambda: self._set_running(True))
        self.proc.finished.connect(self._on_finished)

        # État initial: pas en exécution
        self._set_running(False)

    # =========================================================
    # UI HELPERS
    # =========================================================
    def _append(self, text: str):
        """
        Ajoute une ligne dans la console et garde l'auto-scroll.
        rstrip -> évite d'ajouter trop de lignes vides.
        """
        self.log.appendPlainText(text.rstrip("\n"))

    def _set_running(self, running: bool):
        """
        Active/désactive les boutons pendant un import:
        - On empêche de lancer un deuxième import en même temps
        - On permet "Stop" uniquement quand un process tourne
        - On affiche la progress bar pendant l'exécution
        """
        self.btn_incidents.setEnabled(not running)
        self.btn_latest.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.progress.setVisible(running)

    def _npx(self) -> str:
        """
        Sur Windows: npx.cmd (sinon 'npx' peut ne pas se résoudre correctement)
        Sur Linux/Mac: npx
        """
        return "npx.cmd" if os.name == "nt" else "npx"

    def _browse_backend(self):
        """Ouvre un file dialog pour choisir le dossier backend."""
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier backend (repo root)")
        if path:
            self.txt_backend.setText(path)

    def _save_backend_path(self):
        """
        Valide le chemin backend:
        - doit exister
        - doit être un dossier
        - doit contenir package.json (pour confirmer que c'est le repo root)
        """
        p = Path(self.txt_backend.text().strip())
        if not p.exists() or not p.is_dir():
            self._append("❌ Chemin backend invalide.")
            return

        if not (p / "package.json").exists():
            self._append("⚠️ Ce dossier ne semble pas être le root du backend (package.json introuvable).")
            self._append("   Choisis plutôt: .../crimevision-backend")
            return

        self.backend_path = p.resolve()
        self._append(f"✅ Backend repo défini: {self.backend_path}")

    def _ensure_backend(self) -> bool:
        """
        Vérifie que le backend est défini et accessible avant de lancer un script.
        """
        if not self.backend_path:
            self._append("❌ Backend repo non défini.")
            return False
        if not self.backend_path.exists():
            self._append("❌ Backend repo introuvable.")
            return False
        return True

    # =========================================================
    # CORE RUNNER (lancement de commande)
    # =========================================================
    def _run(self, program: str, args: list[str]):
        """
        Lance une commande non-bloquante dans le repo backend.
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

        # Lance le process
        self.proc.start(program, args)

        # timeout pour détecter un démarrage impossible (PATH, npx absent, etc.)
        if not self.proc.waitForStarted(1500):
            self._append("❌ Impossible de démarrer le process (Node/npx pas dans PATH?).")
            self._set_running(False)

    # =========================================================
    # ACTIONS (boutons)
    # =========================================================
    def _run_import_incidents_with_max(self):
        """
        Exécute:
          npx tsx src/scripts/importIncidents.ts --max=...
        - Normalise 'all' / 'tout' / '∞' / 'infinity'
        - Valide qu'un nombre est un int > 0
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

    # =========================================================
    # QPROCESS CALLBACKS
    # =========================================================
    def _on_output(self):
        """
        Lit le flux merged stdout/stderr et l'affiche dans la console.
        decode errors=replace -> évite crash si caractères invalides.
        """
        data = self.proc.readAllStandardOutput().data()
        if data:
            self._append(data.decode("utf-8", errors="replace"))

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        """
        Callback quand le process se termine:
        - success = code 0 + sortie normale
        - sinon on affiche une erreur
        - on réactive l'UI
        """
        ok = (exit_code == 0 and exit_status == QProcess.NormalExit)
        self._append("✅ Terminé." if ok else f"❌ Terminé avec erreur (code={exit_code}).")
        self._set_running(False)
