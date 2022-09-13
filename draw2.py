import math

from PyQt5.QtWidgets import QGraphicsView, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QGraphicsScene, \
    QInputDialog, QWidget, QGraphicsTextItem, QGraphicsRectItem, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QPointF, QLine
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QPixmap, QImage


class GraphicView(QGraphicsView):

    def __init__(self,parent=None):
        super().__init__(parent)

        self.gr_scene = GraphicScene()
        self.parent = parent


        self.edge_enable = False
        self.drag_edge = None

        self.real_x = 0  # 暂时没用上的东西
        self.real_y = 0

        self.x1 = 0  # 记录左上角点位置
        self.y1 = 0
        self.x2 = 0  # 记录右下角点位置
        self.y2 = 0
        self.x1_view = 0  # 记录view坐标系下左上角位置
        self.y1_view = 0
        self.x2_view = 0
        self.y2_view = 0
        self.mousePressItem = False  # 当前是否点击了某个item, 如果点了，把item本身附上去
        self.drawLabelFlag = -1  # 是否加了一个框，因为可以点取消而不画Bbox
        self.bboxPointList = []  # 用来存放bbox左上和右下坐标及label，每个元素以[x1,y1,x2,y2,text]的形式储存
        self.labelList = []  # 存放label，会展示在旁边的listview中。单独放为了保证不重名
        self.defaultLabelId = 0

        self.bboxList = []  # 存放图元对象和对应的label，方便删除管理, 每个对象都是[item1, item2, edge_item]

        self.init_ui()

    def init_ui(self):
        self.setScene(self.gr_scene)
        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.HighQualityAntialiasing |
                            QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform |
                            QPainter.LosslessImageRendering)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setDragMode(self.RubberBandDrag)

    def mousePressEvent(self, event):
        # 转换坐标系
        pt = self.mapToScene(event.pos())
        self.x1 = pt.x()
        self.y1 = pt.y()
        self.x1_view = event.x()
        self.y1_view = event.y()
        print('上层graphic： view-', event.pos(), '  scene-', pt)

        item = self.get_item_at_click(event)
        if item:
            self.mousePressItem = item

        if event.button() == Qt.RightButton:
            if isinstance(item, GraphicItem):
                self.gr_scene.remove_node(item)
        elif self.edge_enable:
            if isinstance(item, GraphicItem):
                # 确认起点是图元后，开始拖拽
                self.edge_drag_start(item)
        else:
            super().mousePressEvent(event)  # 如果写到最开头，则线条拖拽功能会不起作用
            print('原来如此')
        event.ignore()

    # def set_scene(self, my_scene):
    #     self.gr_scene = my_scene

    def get_item_at_click(self, event):
        """ Return the object that clicked on. """
        pos = event.pos()
        item = self.itemAt(pos)
        return item

    def get_items_at_rubber(self):
        """ Get group select items. """
        area = self.rubberBandRect()
        return self.items(area)

    def mouseMoveEvent(self, event):
        # 实时更新线条
        pos = event.pos()
        self.real_x = event.x()
        self.real_y = event.y()
        # if self.edge_enable and self.drag_edge is not None:
        #     sc_pos = self.mapToScene(pos)
        #     self.drag_edge.gr_edge.set_dst(sc_pos.x(), sc_pos.y())
        #     self.drag_edge.gr_edge.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.mousePressItem = False
        pt = self.mapToScene(event.pos())
        self.x2 = pt.x()
        self.y2 = pt.y()
        self.x2_view = event.x()
        self.y2_view = event.y()

        if self.edge_enable:
            # 拖拽结束后，关闭此功能
            self.edge_enable = False
            item = self.get_item_at_click(event)
            # 终点图元不能是起点图元，即无环图
            if isinstance(item, GraphicItem) and item is not self.drag_start_item:
                self.edge_drag_end(item)
            else:
                self.drag_edge.remove()
                self.drag_edge = None
        else:
            super().mouseReleaseEvent(event)
            item = self.get_item_at_click(event)  # 获得当前点击的item对象
            if not item:  # 如果不是点击item，则生成一个新的Bbox
                text, ok = QInputDialog().getText(QWidget(), '添加Label', '输入label:')
                if ok and text:
                    text = self.getSpecialLabel(text)
                    # 实际上存进去的是view坐标系下的坐标
                    self.savebbox(self.x1_view, self.y1_view, self.x2_view, self.y2_view, text)
                    self.labelList.append(text)
                    self.drawBbox(text)
                    self.drawLabelFlag *= -1  # 将标记变为正，表示画了
                elif ok:
                    self.defaultLabelId += 1
                    defaultLabel = 'label' + str(self.defaultLabelId)
                    self.savebbox(self.x1_view, self.y1_view, self.x2_view, self.y2_view, defaultLabel)
                    self.labelList.append(defaultLabel)
                    self.drawBbox(defaultLabel)
                    self.drawLabelFlag *= -1
            else:  # 如果点击了item，说明想拖动item
                print('点击item拖动，更新BboxPointList')
                print('更新前bboxPointList：', self.bboxPointList)
                index, position = self.findBboxItemIndexFromItem(item)
                label_text = self.bboxList[index][2].gr_edge.information['class']
                index_in_bboxPointList = self.findBboxFromLabel(label_text)
                if position == 1 :
                    self.bboxPointList[index_in_bboxPointList][0] = self.x2_view
                    self.bboxPointList[index_in_bboxPointList][1] = self.y2_view
                else:
                    self.bboxPointList[index_in_bboxPointList][2] = self.x2_view
                    self.bboxPointList[index_in_bboxPointList][3] = self.y2_view
                print('更新后bboxPointList：', self.bboxPointList)
            event.ignore()  # 将信号同时发给父部件

    def drawBbox(self, label_text):
        item1 = GraphicItem()
        item1.setPos(self.x1, self.y1)
        self.gr_scene.add_node(item1)

        item2 = GraphicItem()
        item2.setPos(self.x2, self.y2)
        self.gr_scene.add_node(item2)

        edge_item = Edge(self.gr_scene, item1, item2, label_text)  # 这里原来是self.drag_edge，我给删了

        self.bboxList.append([item1, item2, edge_item])

        print(self.bboxPointList)

    def savebbox(self, x1, y1, x2, y2, text):
        bbox = [x1, y1, x2, y2, text]  # 两个点的坐标以一个元组的形式储存，最后一个元素是label
        self.bboxPointList.append(bbox)

    def getSpecialLabel(self, text):
        # 获得不重名的label
        index = 0
        text_new = text
        for label in self.labelList:
            if text == label.split(' ')[0]:
                index += 1
                text_new = text + ' ' + str(index)
        return text_new

    def edge_drag_start(self, item):
        self.drag_start_item = item  # 拖拽开始时的图元，此属性可以不在__init__中声明
        # 开始拖拽线条，注意到拖拽终点为None
        self.drag_edge = Edge(self.gr_scene, self.drag_start_item, None)

    def edge_drag_end(self, item):
        new_edge = Edge(self.gr_scene, self.drag_start_item, item)
        self.drag_edge.remove()  # 删除拖拽时画的线
        self.drag_edge = None
        new_edge.store()  # 保存最终产生的连接线

    def findBboxFromLabel(self, label):
        '''
        根据label的内容找到self.bboxPointList的index
        '''
        for i,b in enumerate(self.bboxPointList):
            if b[4] == label:
                return i

    def findBboxItemIndexFromLabel(self, label_text):
        '''
        根据label的内容找到self.bboxList的index
        '''
        for i,b in enumerate(self.bboxList):
            edge_item = b[2]
            text = edge_item.labelText
            if text == label_text:
                return i

    def findBboxItemIndexFromItem(self, item):
        # 根据左上角或右下角的item找到此Bbox在数组中的位置
        for i,b in enumerate(self.bboxList):
            if b[0] == item:
                return i, 1  # 第二个参数1代表点击的是左上点
            elif b[1] == item:
                return i, 2  # 第二个参数2代表点击的是右下点
            else:
                return -1, -1  # 表示没找着

    def removeBbox(self, index):
        item1, item2, edge_item = self.bboxList[index]
        self.gr_scene.remove_node(item1)
        self.gr_scene.remove_node(item2)
        # self.gr_scene.remove_edge(edge_item)
        del self.bboxList[index]


class GraphicScene(QGraphicsScene):

    def __init__(self, parent=None):
        super().__init__(parent)

        # settings
        self.grid_size = 20
        self.grid_squares = 5

        # self._color_background = QColor('#393939')
        self._color_background = Qt.transparent
        self._color_light = QColor('#2f2f2f')
        self._color_dark = QColor('#292929')

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)
        self.setSceneRect(0, 0, 500, 500)

        #self.drawForeground()

        self.nodes = []  # 储存图元
        self.edges = []  # 储存连线

        self.real_x = 50

    def add_node(self, node):  # 这个函数可以改成传两个参数node1node2，弄成一组加进self.nodes里
        self.nodes.append(node)
        self.addItem(node)

    def remove_node(self, node):
        self.nodes.remove(node)
        for edge in self.edges:
            if edge.edge_wrap.start_item is node or edge.edge_wrap.end_item is node:
                self.remove_edge(edge)
        self.removeItem(node)

    def add_edge(self, edge):
        self.edges.append(edge)
        self.addItem(edge)

    def remove_edge(self, edge):
        self.edges.remove(edge)
        self.removeItem(edge)

    # def drawBackground(self, painter, rect):
    #
    #
    #
    #     img = QPixmap("F:\HOI\labeltoolv3.0\labeltoolv2.0beta\draw\0000001.jpg")
    #
    #     painter.drawPixmap(img)

class GraphicItem(QGraphicsEllipseItem):

    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen()
        pen.setColor(Qt.red)
        pen.setWidth(2.0)
        self.setPen(pen)
        self.pix = self.setRect(0, 0, 10, 10)
        self.width = 10
        self.height = 10
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # update selected node and its edge
        # 如果图元被选中，就更新连线，这里更新的是所有。可以优化，只更新连接在图元上的。
        if self.isSelected():
            for gr_edge in self.scene().edges:
                gr_edge.edge_wrap.update_positions()

class Edge:
    '''
    线条的包装类
    '''

    def __init__(self, scene, start_item, end_item, labelText=''):
        super().__init__()
        # 参数分别为场景、开始图元、结束图元
        self.scene = scene
        self.start_item = start_item
        self.end_item = end_item
        self.labelText = labelText

        # 线条图形在此创建
        self.gr_edge = GraphicEdge(self)
        # add edge on graphic scene  一旦创建就添加进scene
        self.scene.add_edge(self.gr_edge)

        if self.start_item is not None:
            self.update_positions()

    def store(self):
        self.scene.add_edge(self.gr_edge)

    def update_positions(self):
        patch = self.start_item.width / 2  # 想让线条从图元的中心位置开始，让他们都加上偏移
        src_pos = self.start_item.pos()
        self.gr_edge.set_src(src_pos.x()+patch, src_pos.y()+patch)
        if self.end_item is not None:
            end_pos = self.end_item.pos()
            self.gr_edge.set_dst(end_pos.x()+patch, end_pos.y()+patch)
        else:
            self.gr_edge.set_dst(src_pos.x()+patch, src_pos.y()+patch)
        self.gr_edge.update()

    def remove_from_current_items(self):
        self.end_item = None
        self.start_item = None

    def remove(self):
        self.remove_from_current_items()
        self.scene.remove_edge(self.gr_edge)
        self.gr_edge = None

class GraphicEdge(QGraphicsPathItem):

    def __init__(self, edge_wrap, parent=None):
        super().__init__(parent)
        self.edge_wrap = edge_wrap
        print(self.edge_wrap)
        self.width = 2.0
        self.pos_src = [0, 0]  # 线条起始坐标
        self.pos_dst = [0, 0]  # 线条结束坐标

        self._pen = QPen(QColor("#000"))  # 画线条的笔
        self._pen.setWidthF(self.width)

        self._pen_dragging = QPen(QColor("#000"))  # 画拖拽线条的笔
        self._pen_dragging.setStyle(Qt.DashDotLine)
        self._pen_dragging.setWidthF(self.width)

        self._mark_pen = QPen(Qt.green)
        self._mark_pen.setWidthF(self.width)
        self._mark_brush = QBrush()
        self._mark_brush.setColor(Qt.green)
        self._mark_brush.setStyle(Qt.SolidPattern)

        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)  # 让线条出现在所有图元的最下层

        # 标注信息
        self.information = {'coordinates':'', 'class':'', 'name':'', 'scale':'', 'owner':'', 'saliency':''}

    def set_src(self, x, y):
        self.pos_src = [x, y]

    def set_dst(self, x, y):
        self.pos_dst = [x, y]

    def calc_path(self):  # 计算线条的路径
        path = QPainterPath(QPointF(self.pos_src[0], self.pos_src[1]))  # 起点
        path.lineTo(self.pos_dst[0], self.pos_src[1])
        path.lineTo(self.pos_dst[0], self.pos_dst[1])
        path.moveTo(self.pos_src[0], self.pos_src[1])
        path.lineTo(self.pos_src[0], self.pos_dst[1])
        path.lineTo(self.pos_dst[0], self.pos_dst[1])

        font = QFont("Helvetica [Cronyx]", 12)
        path.addText(self.pos_src[0], self.pos_src[1], font, self.edge_wrap.labelText)
        self.information['coordinates'] = str([self.pos_src[0], self.pos_src[1], self.pos_dst[0], self.pos_dst[1]])
        self.information['class'] = self.edge_wrap.labelText
        return path

    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        return self.calc_path()

    def paint(self, painter, graphics_item, widget=None):
        self.setPath(self.calc_path())
        path = self.path()
        if self.edge_wrap.end_item is None:
            # 包装类中存储了线条开始和结束位置的图元
            # 刚开始拖拽线条时，并没有结束位置的图元，所以是None
            # 这个线条画的是拖拽路径，点线
            painter.setPen(self._pen_dragging)
            painter.drawPath(path)
        else:
            painter.setPen(self._pen)
            painter.drawPath(path)
