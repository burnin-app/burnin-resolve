from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LabeledWidget(QWidget):
    def __init__(self, label_text: str, widget: QWidget):
        super().__init__()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #AAAAAA;")
        self.widget = widget

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.widget)

        # Optional: nicer proportions
        self.layout.setStretch(0, 1)  # label
        self.layout.setStretch(1, 2)  # field


class Label(LabeledWidget):
    def __init__(self, label_text: str, label_value: str):
        self.label = QLabel(label_value)
        super().__init__(label_text, self.label)

    def text(self):
        return self.label.text()


class LineEdit(LabeledWidget):
    def __init__(self, label_text: str):
        self.input = QLineEdit()
        super().__init__(label_text, self.input)

    def text(self):
        return self.input.text()


class ComboBox(LabeledWidget):
    def __init__(self, label_text: str, items=None):
        self.combo = QComboBox()

        if items:
            self.combo.addItems(items)

        super().__init__(label_text, self.combo)

        # expose signal
        self.currentTextChanged = self.combo.currentTextChanged

    def current_text(self):
        return self.combo.currentText()

    def set_items(self, items):
        self.combo.blockSignals(True)  # avoid unwanted triggers
        self.combo.clear()
        self.combo.addItems(items)
        self.combo.blockSignals(False)


class InputWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.input_field = QLineEdit()
        self.button = QPushButton("Print")

        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.on_click)

    def on_click(self):
        print(self.input_field.text())
