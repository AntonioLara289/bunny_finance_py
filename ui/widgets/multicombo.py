from PySide6 import QtWidgets, QtCore, QtGui

class MultiComboBox(QtWidgets.QComboBox):
    def __init__(self):
        super().__init__()
        # 1. Usar un View para controlar el comportamiento de la lista
        self.setView(QtWidgets.QListView(self))
        self.view().viewport().installEventFilter(self)
        
        # 2. Usar un modelo estándar para manejar los checks
        self.model = QtGui.QStandardItemModel(self)
        self.setModel(self.model)
        
        # Conectar cambio de estado
        self.model.dataChanged.connect(self.on_selection_changed)

    def addItem(self, text, data=None):
        item = QtGui.QStandardItem(text)
        item.setData(data, QtCore.Qt.UserRole)
        item.setCheckable(True)  # <-- Aquí ocurre la magia
        item.setCheckState(QtCore.Qt.Unchecked)
        self.model.appendRow(item)

    def eventFilter(self, widget, event):
        # Evita que el combo se cierre al hacer clic en un item
        if event.type() == QtCore.QEvent.MouseButtonRelease and widget is self.view().viewport():
            index = self.view().indexAt(event.pos())
            item = self.model.itemFromIndex(index)
            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
            return True
        return super().eventFilter(widget, event)

    def on_selection_changed(self):
        # Actualiza el texto visible del combo con lo seleccionado
        seleccionados = self.get_selected_data()
        texto = ", ".join([self.model.item(i).text() for i in range(self.model.rowCount()) 
                          if self.model.item(i).checkState() == QtCore.Qt.Checked])
        self.setEditText(texto) # Requiere que el combo sea editable o manejar el paint

    def get_selected_data(self):
        """Retorna una lista con los 'index' (ID) de las cámaras marcadas"""
        return [self.model.item(i).data(QtCore.Qt.UserRole) 
                for i in range(self.model.rowCount()) 
                if self.model.item(i).checkState() == QtCore.Qt.Checked]