from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, \
    QGraphicsPixmapItem
from MainWindow import Ui_MainWindow
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap
import pybboxes as pbx


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        self.setupUi(self)
        # self.yoloToCOCO()
        self.graphicsView = GraphicView(self)
        self.graphicsView.scene = GraphicScene(self)
        self.graphicsView.setScene(self.graphicsView.scene)


class GraphicView(QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicView, self).__init__(parent)
        self.setGeometry(QtCore.QRect(0, 0, 1030, 770))

    def mousePressEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            print(event.pos())
            scene = GraphicScene()
            rect = QGraphicsRectItem(0, 0, 155, 155)
            rect.setAcceptDrops(True)
            rect.setPos(0, 0)
            pen = QPen(Qt.black, 5, Qt.SolidLine)
            pen.setWidth(3)
            rect.setPen(pen)
            scene.addItem(rect)
            self.setScene(scene)


class GraphicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(GraphicScene, self).__init__(parent)
        self.yoloToCOCO()

    def imageIntoItem(self) -> ():
        image = QImage("0000020.jpg")
        pix = QPixmap.fromImage(image)
        item = QGraphicsPixmapItem(pix)
        self.addItem(item)
        graphicsWidth = image.width()
        graphicsHeight = image.height()
        return graphicsWidth, graphicsHeight

    def yoloToCOCO(self):
        txtFile = open(file=f"0000020.txt", mode="r")
        lines = txtFile.readlines()
        graphicsWidth = self.imageIntoItem()[0]
        graphicsHeight = self.imageIntoItem()[1]

        for line in lines:
            _, x, y, w, h = map(float, line.split(' '))
            # convertedCorordinate = pbx.convert_bbox((x, y, w, h), from_type="yolo", to_type="coco",
            #                                         image_size=(self.imageIntoItem()[0], self.imageIntoItem()[1]))
            convertedCorordinate = pbx.convert_bbox((x, y, w, h), from_type="yolo", to_type="coco",
                                                    image_size=(graphicsWidth, graphicsHeight))
            # print(convertedCorordinate)
            self.drawBBox(convertedCorordinate)
        txtFile.close()

    def drawBBox(self, convertedCorordinate):
        rect = QGraphicsRectItem(convertedCorordinate[0], convertedCorordinate[1], convertedCorordinate[2],
                                 convertedCorordinate[3])
        rect.setAcceptDrops(True)
        rect.setPos(0, 0)
        pen = QPen(Qt.blue, 5, Qt.SolidLine)
        pen.setWidth(3)
        rect.setPen(pen)
        # scene.addItem(rect)
        self.addItem(rect)


if __name__ == "__main__":
    app = QApplication([])
    mainWindow = MyWindow()
    mainWindow.show()
    app.exec_()
