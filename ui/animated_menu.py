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

def animate_switch(self, new_widget):
    current = self.stack.currentWidget()
    new_widget.setGeometry(self.stack.geometry())

    self.stack.addWidget(new_widget)
    anim = QPropertyAnimation(new_widget, b"geometry")
    anim.setDuration(250)
    anim.setStartValue(self.stack.geometry().adjusted(self.width(), 0, self.width(), 0))
    anim.setEndValue(self.stack.geometry())
    anim.setEasingCurve(QEasingCurve.OutCubic)
    self._anim = anim
    anim.start()

    self.stack.setCurrentWidget(new_widget)