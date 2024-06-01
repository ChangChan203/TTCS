from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QGraphicsView


class MouseDetector(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if isinstance(obj, QGraphicsView):
                self.getPos(event)
                scene_position = obj.mapToScene(int(event.position().x()),
                                                int(event.position().y()))

                if self.app.select_x_spinbox is not None:
                    self.app.select_x_spinbox.setValue(scene_position.x())
                    self.app.select_x_spinbox = None
                if self.app.select_y_spinbox is not None:
                    self.app.select_y_spinbox.setValue(scene_position.y())
                    self.app.select_y_spinbox = None
        return super(MouseDetector, self).eventFilter(obj, event)

    def getPos(self, event):
        x = event.position.x()
        y = event.position.y()
