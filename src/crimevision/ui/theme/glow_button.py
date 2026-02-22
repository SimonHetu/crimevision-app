from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


class GlowButton(QPushButton):
    def __init__(
        self,
        *args,
        accent: str = "#3b82f6",
        blur_radius: int = 25,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(blur_radius)
        self._shadow.setOffset(0)
        self._shadow.setColor(QColor(accent))
        self._shadow.setEnabled(False)

        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._shadow.setEnabled(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setEnabled(False)
        super().leaveEvent(event)