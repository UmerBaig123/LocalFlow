"""QSS stylesheets for the popup window."""

POPUP_STYLE = """
QFrame#MainFrame {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 16px;
}

/* ---- Header ---- */
QLabel#TitleLabel {
    color: #cdd6f4;
    font-size: 16px;
    font-weight: 600;
    padding: 0;
}

QLabel#StatusLabel {
    color: #6c7086;
    font-size: 12px;
    padding: 0;
}

/* ---- Mode selector ---- */
QComboBox#ModeCombo {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    min-width: 80px;
}
QComboBox#ModeCombo:hover {
    border: 1px solid #89b4fa;
}
QComboBox#ModeCombo::drop-down {
    border: none;
    width: 20px;
}
QComboBox#ModeCombo::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6c7086;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
    outline: none;
}

/* ---- Record button ---- */
QPushButton#RecordButton {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
    border-radius: 26px;
    font-size: 26px;
    font-weight: 700;
    min-width: 52px;
    min-height: 52px;
    max-width: 52px;
    max-height: 52px;
    padding: 0px;
    text-align: center;
}
QPushButton#RecordButton:hover {
    background-color: #f5a0b8;
}
QPushButton#RecordButton:pressed {
    background-color: #d4687e;
}
QPushButton#RecordButton[recording="true"] {
    background-color: #eba0b3;
    border: 3px solid #f38ba8;
}
QPushButton#RecordButton[recording="true"]:hover {
    background-color: #f5a0b8;
}

/* ---- Preview text area ---- */
QTextEdit#PreviewText {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
    font-family: system-ui, sans-serif;
    selection-background-color: #45475a;
}

/* ---- Minimize button ---- */
QPushButton#MinimizeButton {
    background-color: transparent;
    color: #6c7086;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
    padding: 0px;
    text-align: center;
}
QPushButton#MinimizeButton:hover {
    background-color: #313244;
    color: #cdd6f4;
}

/* ---- Cancel button ---- */
QPushButton#CancelButton {
    background-color: #313244;
    color: #cdd6f4;
    border: none;
    border-radius: 26px;
    font-size: 22px;
    font-weight: 700;
    min-width: 52px;
    min-height: 52px;
    max-width: 52px;
    max-height: 52px;
    padding: 0px;
    text-align: center;
}
QPushButton#CancelButton:hover {
    background-color: #45475a;
    color: #f38ba8;
}
QPushButton#CancelButton:pressed {
    background-color: #585b70;
}

/* ---- Hint label ---- */
QLabel#HintLabel {
    color: #585b70;
    font-size: 11px;
    padding: 0;
}
"""
