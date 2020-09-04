
import sys
import random
import threading
import circlify as circ
from pytrends.request import TrendReq
from pprint import pprint
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# https://pypi.org/project/circlify/
# https://www.geeksforgeeks.org/pyqt5-create-circular-push-button/

print("Initialize pytrend")

pytrend = TrendReq()

# Create payload and capture API tokens. Only needed for interest_over_time(), interest_by_region() & related_queries()
#kw = "python"
# pytrend.build_payload(kw_list=[kw])
# Related Queries, returns a dictionary of dataframes
#related_queries_dict = pytrend.related_queries()
#related_top = related_queries_dict[kw]["top"]
# related_rising = related_queries_dict["rising"]
#q = related_top["query"].to_list()
#q = list(map(lambda item: removeKw(kw, item), q))
#v = related_top["value"]
#size = related_top.size

# for i in range(0, size):
#    print(q[i], v[i])

# pprint(related_top)

# Get Google Keyword Suggestions
# suggestions_dict = pytrend.suggestions(keyword='pizza')
# print(suggestions_dict)


def removeKw(kw: str, item: str) -> str:
    if " " in kw:
        return item

    sp = item.split()
    if len(sp) < 2:
        return item

    start = 0
    end = len(sp)

    if sp[0] == kw:
        start = 1
    if sp[-1] == kw:
        end = end - 1

    if start == end:
        return sp[start]
    else:
        return " ".join(sp[start:end])


class SearchWorker(QRunnable):
    # kw : keyword, mode : top or rising, size : result panel size
    def __init__(self, kw, mode, size, fn, *args, **kwargs):
        super(SearchWorker, self).__init__()
        self.fn = fn
        self.kw = kw
        self.mode = mode
        self.size = size
        self.args = args
        self.kwargs = kwargs

    def search(self, kw: str):
        pytrend.build_payload([kw])
        datas = pytrend.related_queries()[kw][self.mode]
        if datas is None:
            return None

        print(datas)
        datas["query"] = datas["query"].apply(lambda item: removeKw(kw, item))

        result = datas.sort_values(by=['value'])
        return result

    def search_test(self, kw: str):
        return {
            "query": [
                "hi", "hello", "vsc", "foooooooo"
            ],
            "value": [
                30, 8, 5, 3
            ]
        }

    @pyqtSlot()
    def run(self):
        # search
        relatedData = self.search(self.kw)

        if relatedData is None:
            msg = QMessageBox()
            msg.setText("No results")
            msg.exec_()
            return

        queries = relatedData["query"]
        values = relatedData["value"]

        # test-case
        #values = [19, 17, 13, 11, 7, 5, 3, 2, 1]

        circles = circ.circlify(list(values), show_enclosure=True)
        circleData = map(lambda c: {
            'x': abs(c.x + 1) * self.size / 2,
            'y': abs(c.y - 1) * self.size / 2,
            'r': c.r * self.size / 2
        }, circles)

        circleData = sorted(circleData,
                            key=lambda item: item['r'],
                            reverse=True)

        self.fn(queries, circleData, *self.args, **self.kwargs)


def rndBrightColor():
    r = random.randint(200, 255)
    g = random.randint(200, 255)
    b = random.randint(200, 255)
    return (r, g, b)


def rndDarkColor():
    r = random.randint(0, 128)
    g = random.randint(0, 128)
    b = random.randint(0, 128)
    return (r, g, b)


def rgb2hex(rgb):
    return '#%02x%02x%02x' % rgb


class CirclePanelWidget(QWidget):
    def __init__(self, *args, **kwargs):
        # self.circles = circles
        super(CirclePanelWidget, self).__init__(*args, **kwargs)
        self.updateRequire = True
        self.circles = []
        self.names = []
        print("CirclePanelWidget Initialized")

    def drawCirclePen(self, painter, x: float, y: float, r: float):
        backgroundColor = QColor.fromRgb(*rndBrightColor())

        borderPen = QPen(Qt.black, 1, Qt.SolidLine)
        painter.setPen(borderPen)

        fillBrush = QBrush(backgroundColor, Qt.SolidPattern)
        painter.setBrush(fillBrush)

        painter.drawEllipse(QPointF(x, y), r, r)

    def drawTextInCircle(self, painter, x: int, y: int, r: int, n: str):
        fm = QFontMetrics(self.font())
        width = fm.width(n)
        height = fm.height()
        sx = x - int(width / 2)
        sy = y - int(height / 2)
        painter.drawText(
            QRect(sx, sy, width, height), Qt.AlignCenter, n)

    def updateCircles(self, circles):
        print("Update circle datas")
        self.circles = circles

    def updateNames(self, names):
        print("Update name datas")
        self.names = names

    def paintEvent(self, e):
        print("CirclePanelWidget updating")
        painter = QPainter(self)

        for i in range(0, len(self.circles)):
            c = self.circles[i]

            x = float(c['x'])
            y = float(c['y'])
            r = float(c['r'])

            self.drawCirclePen(painter, x, y, r)

        for i in range(0, len(self.names)):
            if i+1 >= len(self.circles):
                break
            c = self.circles[i + 1]

            x = int(c['x'])
            y = int(c['y'])
            r = int(c['r'])

            n = self.names[i]
            self.drawTextInCircle(painter, x, y, r, n)

        super(CirclePanelWidget, self).paintEvent(e)


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        self.displaySize = 500

        self.initUI()

    def initUI(self):
        self.threadpool = QThreadPool()

        wid = QWidget(self)
        self.setCentralWidget(wid)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.circlePanel = CirclePanelWidget()
        self.circlePanel.resize(self.displaySize, self.displaySize)
        layout.addWidget(self.circlePanel)

        self.txtSearch = QLineEdit("", self)
        layout.addWidget(self.txtSearch)

        self.txtMode = QLineEdit("top", self)
        layout.addWidget(self.txtMode)

        self.btnSearch = QPushButton("Search", self)
        self.btnSearch.clicked.connect(self.onBtnSearchClicked)
        layout.addWidget(self.btnSearch)

        self.setWindowTitle("STATS")
        self.setGeometry(100, 100, self.displaySize, self.displaySize + 100)
        self.setFixedSize(self.displaySize, self.displaySize + 100)

        wid.setLayout(layout)
        self.show()

    def drawCircleButton(self, x, y, r, name):
        backgroundColor = self.rgb2hex(self.rndBrightColor())

        btn = QPushButton(name, self)
        btn.setGeometry(x-r, y-r, r*2, r*2)
        btn.setStyleSheet(f"""
            border-radius:{r}px;
            border:1px solid black;
            background-color: {backgroundColor};
        """)
        btn.clicked.connect(self.onBtnCircleClicked)

    def onBtnCircleClicked(self):
        btn = self.sender()
        print(btn.text())

    def setUIEnabled(self, value):
        self.btnSearch.setEnabled(value)
        self.txtSearch.setEnabled(value)
        self.txtMode.setEnabled(value)

    def onBtnSearchClicked(self):
        self.setUIEnabled(False)

        kw = self.txtSearch.text()
        mode = self.txtMode.text()
        print(f"search {kw} in {mode}")

        worker = SearchWorker(kw, mode, self.displaySize, self.searchDone)
        self.threadpool.start(worker)

    def searchDone(self, queries, circles):
        self.circlePanel.updateNames(queries)
        self.circlePanel.updateCircles(circles)

        self.setUIEnabled(True)
        self.circlePanel.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = App()
    sys.exit(app.exec_())
