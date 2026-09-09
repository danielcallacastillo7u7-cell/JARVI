"""Local startup video; never delays startup permanently if playback fails."""
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


class StartupIntro(QWidget):
    finished = pyqtSignal()

    def __init__(self, video_path: Path, name: str = "JARVIS"):
        super().__init__()
        self._done = False
        self.setWindowTitle(f"{name} — Iniciando")
        self.setStyleSheet("background: #00060a; color: #8ffcff;")
        self.resize(980, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        self.video = QVideoWidget(self)
        self.video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        layout.addWidget(self.video, 1)
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 0, 20, 0)
        footer.addWidget(QLabel(f"{name.upper()}  /  INICIANDO SISTEMA"))
        footer.addStretch()
        skip = QPushButton("Omitir intro · Esc")
        skip.setStyleSheet("padding: 8px 16px; border: 1px solid #1a5c7a; border-radius: 5px;")
        skip.clicked.connect(self.finish)
        footer.addWidget(skip)
        layout.addLayout(footer)
        self._escape = QShortcut(QKeySequence("Escape"), self)
        self._escape.activated.connect(self.finish)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.55)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self._status_changed)
        self.player.errorOccurred.connect(self._error)
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self.finish)
        self.player.setSource(QUrl.fromLocalFile(str(video_path.resolve())))

    def start(self):
        if not self._done:
            self.show()
            self._timeout.start(12000)
            self.player.play()

    def _status_changed(self, status):
        if status in (QMediaPlayer.MediaStatus.EndOfMedia,
                      QMediaPlayer.MediaStatus.InvalidMedia):
            self.finish()

    def _error(self, *_):
        self.finish()

    def finish(self):
        if self._done:
            return
        self._done = True
        self._timeout.stop()
        self.player.stop()
        # Show the main window via the callback before hiding this last window.
        self.finished.emit()
        self.hide()

    def closeEvent(self, event):
        self.finish()
        event.accept()
