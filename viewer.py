import json
import os
import sys

import yaml
from PyQt5 import QtWidgets, QtGui, QtCore
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

NO_DATA = object()


class Context(QtWidgets.QTextEdit):

    def __init__(self):
        super().__init__()
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

    def set_content(self, content):
        if content is NO_DATA:
            to_show = ""
        else:
            to_show = yaml.dump(content, allow_unicode=True, default_flow_style=False)
        self.setPlainText(to_show)


class Editor(QtWidgets.QTextEdit):

    def __init__(self, context_input, context_output):
        super().__init__()
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.context_input = context_input
        self.context_output = context_output

        self._trace_info = self._load_trace_info()
        self._trace_position = 0
        self._prev_filename = None
        self._line_limits = None

        self._show()

    def _load_trace_info(self):
        with open("my_trace.json", "rt", encoding="utf8") as fh:
            data = json.load(fh)

        # filter out invalid files
        data = [x for x in data if os.path.exists(x["filename"])]

        return data

    def _set_file(self, filename):
        print("======== set file!", filename)
        self._prev_filename = filename

        with open(filename, "rt", encoding="utf8") as fh:
            code = fh.read()

        self._line_limits = []
        prev = 0
        for line in code.split("\n"):
            len_line = len(line) + 1  # plus one because newline
            self._line_limits.append((prev, prev + len_line))
            prev += len_line
        print("====== limits todos", self._line_limits)

        formatter = HtmlFormatter(cssclass="source", full=True, noclasses=True)
        text_content = highlight(code, PythonLexer(), formatter)

        self.setHtml(text_content)

    def _show(self):
        info = self._trace_info[self._trace_position]
        if info["filename"] != self._prev_filename:
            self._set_file(info["filename"])

        limit_from, limit_to = self._line_limits[info["lineno"] - 1]
        print("========= limitS", limit_from, limit_to)
        cursor = self.textCursor()
        cursor.setPosition(limit_from)
        cursor.setPosition(limit_to, QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

        self.context_input.set_content(info.get("input", NO_DATA))
        self.context_output.set_content(info.get("output", NO_DATA))

    def next(self):
        self._trace_position += 1
        if self._trace_position >= len(self._trace_info):
            self._trace_position = len(self._trace_info) - 1
            return
        self._show()

    def previous(self):
        self._trace_position -= 1
        if self._trace_position < 0:
            self._trace_position = 0
            return
        self._show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            self.next()
        if event.key() == QtCore.Qt.Key_Left:
            self.previous()


class Viewer(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor Instrumentador")
        self.setGeometry(200, 200, 1200, 600)

        context_input = Context()
        context_output = Context()

        context_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        context_splitter.addWidget(context_input)
        context_splitter.addWidget(context_output)

        hbox = QtWidgets.QHBoxLayout(self)
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_splitter.addWidget(Editor(context_input, context_output))
        main_splitter.addWidget(context_splitter)
        main_splitter.setSizes([600, 350])
        hbox.addWidget(main_splitter)
        self.setLayout(hbox)

        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    viewer = Viewer()
    sys.exit(app.exec_())
