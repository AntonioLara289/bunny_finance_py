from PySide6.QtWidgets import QMenu
from PySide6.QtCore import QPropertyAnimation, QRect, QEasingCurve

class AnimatedMenu(QMenu):
    def showEvent(self, event):
        """Animate the dropdown when shown"""
        pos = self.pos()
        start_rect = QRect(pos.x(), pos.y() - 10, self.width(), 0)
        end_rect = QRect(pos.x(), pos.y(), self.sizeHint().width(), self.sizeHint().height())

        self.setGeometry(start_rect)

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(130)
        self._anim.setStartValue(start_rect)
        self._anim.setEndValue(end_rect)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

        super().showEvent(event)
