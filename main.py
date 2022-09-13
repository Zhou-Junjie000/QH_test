import sys
import cgitb

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow



from draw2 import GraphicScene, GraphicView

cgitb.enable(format("text"))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.scene = GraphicScene(self)
        #img = QPixmap("./0000001.jpg")
        #self.scene.drawBackground(img)
        # self.imgLabel = QtWidgets.QLabel(self)
        self.view = GraphicView(self.scene)


        # self.view.setScene(self.scene)

        self.setMinimumHeight(500)
        self.setMinimumWidth(500)
        self.setCentralWidget(self.view)
        self.setWindowTitle("Graphics Demo")
        #self.set_image()

    # def set_image(self):
    #     img_path = "./0000001.jpg"
    #     img = cv.imread(img_path)
    #     img = cv.cvtColor(img, cv.COLOR_BGR2RGB) # 转换颜色通道
    #     x = img.shape[1] # 获取图像大小
    #     y = img.shape[0]
    #     print(x, y)
    #     self.zoomscale = 1
    #     frame = QImage(img, x, y, QImage.Format_RGB888)
    #     pix = QPixmap.fromImage(frame)
    #     self.item = QGraphicsPixmapItem(pix)
    #     self.scene = GraphicScene(self)
    #     self.scene.addItem(self.item)
    #     self.view.setScene(self.scene)
    #     self.view.show()



def demo_run():
    app = QApplication(sys.argv)
    demo = MainWindow()
    # compatible with Mac Retina screen.
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # show up
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    demo_run()