"""Custom color picker using floats and alpha."""

# Modified code from
# https://orthallelous.wordpress.com/2018/12/19/custom-color-dialog/

import math
import random
from typing import Union

from PySide2 import QtCore, QtGui, QtWidgets

from PropertyEditor.widgets.widgets import DoubleSlider


class PickScreen:
    def __init__(self, screen: QtGui.QScreen):

        geo = screen.availableGeometry()
        self.img = screen.grabWindow(0)
        self.x = geo.x()
        self.y = geo.y()
        self.width = geo.width()
        self.height = geo.height()

    @property
    def rect(self):
        return self.x, self.y, self.width, self.height

    def over_screen(self, geo: QtCore.QRect):

        if (
            self.x <= geo.x() <= self.x + self.width
            and self.y <= geo.y() <= self.y + self.height
        ):
            return True
        return False


class ColorPicker(QtWidgets.QDialog):
    """Custom colorDialog based on Orthallelous custom widget."""

    currentColorChanged = QtCore.Signal(QtGui.QColor)
    colorSelected = QtCore.Signal(QtGui.QColor)

    def __init__(self, initial=None, use_alpha=False, parent=None):
        super(ColorPicker, self).__init__(parent)
        self._color = initial
        self.use_alpha = use_alpha
        self._create_ui()
        self.set_color(initial)
        self._mag = None

    def current_color(self):
        return self._color

    def set_color(self, qcolor=None):
        if qcolor is None:
            self._color = QtGui.QColor("#ffffff")
        else:
            self._color = QtGui.QColor(qcolor)

        self._color_edited()

    def set_alpha(self, alpha):
        self._color_edited()

    @staticmethod
    def get_color(initial=None, parent=None, title=None):
        dialog = ColorPicker(initial, parent)
        if title:
            dialog.setWindowTitle(title)
        dialog.exec_()
        color = dialog._color
        return color

    def close_valid(self):
        """Emits colorSelected signal with valid color on OK."""
        self.currentColorChanged.emit(self._color)
        self.colorSelected.emit(self._color)
        self.close()

    def close_invalid(self):
        """Emits colorSelected signal with invalid color on Cancel."""
        self._color = QtGui.QColor()
        self.colorSelected.emit(QtGui.QColor())
        self.close()

    def set_options(self):
        self.setFixedSize(self.sizeHint())

    def _color_edited(self):
        """Internal color editing."""
        sender, color = self.sender(), self._color
        for i in self.inputs:
            i.blockSignals(True)

        if sender in self.rgbInputs:
            color.setRgb(*[int(i.value() * 255) for i in self.rgbInputs])
        elif sender is self.colorWheel:
            color = self._color = self.colorWheel.get_color()
        elif sender is self.colorNamesCB:
            dat = self.colorNamesCB.itemData(self.colorNamesCB.currentIndex())
            color = self._color = QtGui.QColor(str(dat))
            self.colorNamesCB.setToolTip(self.colorNamesCB.currentText())
        else:
            pass

        if sender not in self.rgbInputs:
            for i, j in zip(color.getRgb()[:-1], self.rgbInputs):
                j.setValue(i / 255)
        if sender is not self.colorWheel:
            self.colorWheel.set_color(color)
        if sender is not self.colorNamesCB:
            idx = self.colorNamesCB.findData(color.name())
            self.colorNamesCB.setCurrentIndex(idx)
        if self.use_alpha is not None:
            color.setAlphaF(self.alpha.slider.value())

        for i in self.inputs:
            i.blockSignals(False)
        self.currentColorChanged.emit(color)

    def pick_color(self):
        """Pick a color on the screen, part 1.

        Create a screenshot of all screens
        and only display some part of it in a grid magnifier.
        """
        # Screenshot desktops
        self._view = QtWidgets.QGraphicsView(self)
        scene = QtWidgets.QGraphicsScene(self)

        self._view.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self._view.setWindowFlags(QtCore.Qt.WindowType_Mask)
        self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Create one pixmap from all screens and get full screens size
        # This only works for side by side screens not top down ones
        pm_x = pm_y = 0
        images = []
        for screen in QtWidgets.QApplication.screens():
            screen = PickScreen(screen)
            pm_x += screen.width
            pm_y = screen.height + 40
            images.append(screen.img)

        self._img = QtGui.QPixmap(pm_x, pm_y)
        painter = QtGui.QPainter(self._img)
        for i, img in enumerate(images):
            x = (pm_x / len(images)) * i
            rect = QtCore.QRectF(x, 0, pm_x / len(images), 1080)
            painter.drawPixmap(rect, img, QtCore.QRectF(img.rect()))
        scene.addPixmap(self._img)
        scene.setSceneRect(QtCore.QRectF(0, 0, pm_x, pm_y))

        self._mag = Magnifier()
        self._mag.set_brackground(self._img)
        self._mag.set_size(11, 11)
        scene.addItem(self._mag)
        self._view.setScene(scene)

        self._appview = QtWidgets.QApplication
        self._appview.setOverrideCursor(QtCore.Qt.CrossCursor)

        self._view.showFullScreen()

        # Force view geometry,
        # needed for multi screens to set the QGraphicsView to 0,
        # otherwise the QGraphicsView x() and y() are set from the current screen
        # and the whole tool fails to work correctly
        self._view.setGeometry(0, 0, int(scene.width()), int(scene.height()))

        self._view.mousePressEvent = self._picked_color
        self._view.mouseMoveEvent = self._mag.mouse_moved

    def _picked_color(self, event):
        """Pick a color on the screen, part 2."""

        if event.button() == QtCore.Qt.LeftButton:

            x = event.globalPos().x()
            y = event.globalPos().y()

            # if x > self.current_screen.x:
            #     x = x - self.current_screen.x

            color = QtGui.QColor(self._img.toImage().pixel(QtCore.QPoint(x, y)))
            self._color = color
            self._color_edited()

        self._reset_picker()

    def _reset_picker(self):
        self._view.hide()
        self._appview.restoreOverrideCursor()
        self._mag = self._appview = self._view = self._img = None

    def use_random(self, state=True):
        """Toggles show colors button and random color button."""
        if state:
            self.rndButton.blockSignals(False)
            self.rndButton.show()
        else:
            self.rndButton.blockSignals(True)
            self.rndButton.hide()

    def random_color(self):
        """Select a random color."""
        rand = random.randint
        col = QtGui.QColor()
        col.setHsv(rand(0, 359), rand(0, 255), rand(0, 255))
        self.set_color(col)
        return col

    def get_named_colors(self):
        """Returns a list [(name, #html)] from the named colors combobox."""
        lst = []
        for i in range(self.colorNamesCB.count()):
            name = str(self.colorNamesCB.itemText(i))
            html = str(self.colorNamesCB.itemData(i))
            lst.append((name, html))
        return lst

    def add_named_colors(self, lst):
        """Add a list [('name', '#html'), ] of named colors (repeats removed)."""
        col = self.get_named_colors() + lst
        lst = [(i[0], QtGui.QColor(i[1])) for i in col]
        sen = set()
        add = sen.add
        uni = [x for x in lst if not (x[1].name() in sen or add(x[1].name()))]

        self.colorNamesCB.clear()
        for i, j in sorted(uni, key=lambda q: q[1].getHsv()):
            icon = QtGui.QPixmap(16, 16)
            icon.fill(j)
            self.colorNamesCB.addItem(QtGui.QIcon(icon), i, j.name())
        self.colorWheel.set_named_colors([(i, j.name()) for i, j in uni])

    def _create_ui(self):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        rightCenter = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

        self.inputGrid = QtWidgets.QGridLayout()
        self.inputGrid.setSpacing(5)
        h_spc = self.inputGrid.horizontalSpacing()

        self.redInput = QtWidgets.QDoubleSpinBox()
        self.grnInput = QtWidgets.QDoubleSpinBox()
        self.bluInput = QtWidgets.QDoubleSpinBox()
        self.rgbInputs = [self.redInput, self.grnInput, self.bluInput]

        self.redLabel = QtWidgets.QLabel("&R:")
        self.redLabel.setToolTip("Red")
        self.grnLabel = QtWidgets.QLabel("&G:")
        self.grnLabel.setToolTip("Green")
        self.bluLabel = QtWidgets.QLabel("&B:")
        self.bluLabel.setToolTip("Blue")
        self.rgbLabels = [self.redLabel, self.grnLabel, self.bluLabel]

        self.redLabel.setBuddy(self.redInput)
        self.grnLabel.setBuddy(self.grnInput)
        self.bluLabel.setBuddy(self.bluInput)

        for i in self.rgbInputs:
            i.setRange(0, 1)
            i.setFixedSize(50, 22)
            i.setSingleStep(0.01)
            i.setDecimals(3)
            i.setAlignment(QtCore.Qt.AlignCenter)

        self.alphaLabel = QtWidgets.QLabel("    A:")
        self.alpha = AlphaSlider()
        if self.use_alpha is not None:
            self.alpha.slider.setValue(self.use_alpha)
        self.alpha.currentColorChanged.connect(self.set_alpha)

        self.htmlInput = QtWidgets.QLineEdit()
        self.htmlInput.setFixedSize(35 + 22 + h_spc, 22)
        self.htmlInput.setPlaceholderText("html")
        self.htmlInput.setAlignment(QtCore.Qt.AlignCenter)
        regex = QtCore.QRegExp("[0-9A-Fa-f]{1,6}")
        valid = QtGui.QRegExpValidator(regex)
        self.htmlInput.setValidator(valid)

        self.inputLabels = self.rgbLabels
        for i in self.inputLabels:
            i.setFixedSize(22, 22)
            i.setAlignment(rightCenter)

        self.inputs = self.rgbInputs.copy()
        for i in self.inputs:
            i.valueChanged.connect(self._color_edited)

        self.pickButton = QtWidgets.QPushButton("&Pick")
        self.pickButton.setToolTip("Pick a color from the screen")
        self.pickButton.clicked.connect(self.pick_color)

        self.rndButton = QtWidgets.QPushButton("&Random")
        self.rndButton.setToolTip("Select a random color")
        self.rndButton.clicked.connect(self.random_color)

        self.colorWheel = ColorWheel()
        self.colorWheel.setFixedSize(256, 256)
        self.colorWheel.currentColorChanged.connect(self.set_color)

        self.colorNamesCB = QtWidgets.QComboBox()
        self.colorNamesCB.setFixedSize(70 + 66 + 4 * h_spc, 22)  # spans 5 cols

        lst = [i for i in QtGui.QColor.colorNames() if str(i) != "transparent"]
        lst = [(i, QtGui.QColor(i)) for i in lst]
        self.add_named_colors(lst)
        self.colorNamesCB.currentIndexChanged.connect(self._color_edited)

        self.inputs += [self.colorWheel, self.colorNamesCB]

        self.validate = QtWidgets.QPushButton("OK")
        self.validate.clicked.connect(self.close_valid)
        self.validate.setDefault(True)

        self.inputGrid.addWidget(self.colorWheel, 0, 0, 1, 7)

        start_row = 2
        if self.use_alpha is not None:
            self.inputGrid.addWidget(self.alphaLabel, start_row, 0, 1, 1)
            self.inputGrid.addWidget(self.alpha, start_row, 1, 1, -1)
            self.alpha.slider.setValue(self.use_alpha)
            self.alpha.line_edit.setText(str(self.use_alpha)[:5])

            start_row += 1

        row = start_row
        for label, spinbox in zip(self.rgbLabels, self.rgbInputs):
            self.inputGrid.addWidget(label, row, 0, 1, 1)
            self.inputGrid.addWidget(spinbox, row, 1, 1, 1)
            row += 1

        self.inputGrid.addWidget(self.colorNamesCB, start_row, 4, 1, 1)
        start_row += 1

        self.inputGrid.addWidget(self.pickButton, start_row, 4, 1, 1)
        start_row += 1

        self.inputGrid.addWidget(self.rndButton, start_row, 4, 1, 1)
        start_row += 1

        self.inputGrid.addWidget(self.validate, start_row + 1, 0, 1, -1)

        self.setWindowTitle("Select color")
        ico = self.style().standardIcon(QtWidgets.QStyle.SP_DialogResetButton)
        self.setWindowIcon(ico)
        self.setLayout(self.inputGrid)
        self.setFixedSize(self.sizeHint())
        self.use_random()


class ColorWheel(QtWidgets.QWidget):
    currentColorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self, parent=None):
        super(ColorWheel, self).__init__(parent)
        self.setFixedSize(256, 256)

        self.s_ang, self.e_ang = 135, 225

        self.o_ang, self.rot_d = 45, -1

        self.pos = QtCore.QPointF(-100, -100)
        self.wheel_center = QtCore.QPointF(-100, -100)
        self.wheel_angle = math.radians(self.s_ang)
        self.choose_point = self.pos
        self.hue = self.sat = self.value = 255

        self.setup()
        self.pos = self.color_wheel_box.center()

        self._namedColorList = []
        self._namedColorPts = []
        self._showNames = False

        self.setMouseTracking(True)
        self.installEventFilter(self)

        self._startedTimer = False
        self.in_wheel = False
        self.in_arc = False

    def resizeEvent(self, event):
        self.setup()
        self.set_named_colors(self._namedColorList)

    def get_color(self):
        col = QtGui.QColor()
        col.setHsv(self.hue, self.sat, self.value)
        return col

    def get_color_point(self, color: QtGui.QColor) -> QtCore.QPoint:
        h, s, v, a = color.getHsv()
        self.hue, self.sat, self.value = h, s, v
        t = math.radians(h + self.o_ang * -self.rot_d) * -self.rot_d
        r = s / 255.0 * self.cW_rad
        x, y = r * math.cos(t) + self.center.x(), r * -math.sin(t) + self.center.y()
        return QtCore.QPoint(x, y)

    def set_named_colors(self, colorList):
        """Sets list [(name, #html)] of named colors."""
        self._namedColorList = colorList
        lst = []
        for i in self._namedColorList:
            lst.append(self.get_color_point(QtGui.QColor(i[1])))

        self._namedColorPts = lst

    def show_named_colors(self, flag=False):
        """Show/hide location of named colors on color wheel."""
        self._showNames = flag
        self.update()

    def set_color(self, color):
        self.choose_point = self.get_color_point(color)

        self.wheel_angle = t2 = (self.value / 255.0) * self.ang_w + math.radians(
            self.e_ang
        )
        self.wheel_angle = t2 = t2 if t2 > 0 else t2 + 2 * math.pi
        r2 = self.arc_outer_value.width() / 2.0

        x, y = r2 * math.cos(t2) + self.center.x(), r2 * -math.sin(t2) + self.center.y()
        self.wheel_center, self.wheel_angle = QtCore.QPointF(x, y), t2
        self.indicator_box.moveCenter(self.wheel_center)
        self.update()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonPress or (
            event.type() == QtCore.QEvent.MouseMove
            and event.buttons() == QtCore.Qt.LeftButton
        ):
            self.pos = pos = event.pos()

            t = math.atan2(self.center.y() - pos.y(), pos.x() - self.center.x())
            if self.colWhlPath.contains(pos) and not self.in_arc:
                self.in_wheel = True
                self.choose_point = pos

                h = (int(math.degrees(t)) - self.o_ang) * -self.rot_d
                self.hue = (h if h > 0 else h + 360) % 360

                m_rad = math.sqrt(
                    (self.pos.x() - self.center.x()) ** 2
                    + (self.pos.y() - self.center.y()) ** 2
                )
                self.sat = int(255 * min(m_rad / self.cW_rad, 1))

            if self.vInArcPath.contains(pos) and not self.in_wheel:
                self.in_arc = True
                self.wheel_angle = t if t > 0 else t + 2 * math.pi
                r2 = self.arc_outer_value.width() / 2.0

                x, y = (
                    r2 * math.cos(t) + self.center.x(),
                    r2 * -math.sin(t) + self.center.y(),
                )
                self.wheel_center = QtCore.QPointF(x, y)
                self.indicator_box.moveCenter(self.wheel_center)
                self.value = (
                    int(255 * (t - math.radians(self.e_ang)) / self.ang_w) % 256
                )

            self.update()
            col = QtGui.QColor()
            col.setHsv(self.hue, self.sat, self.value)
            self.currentColorChanged.emit(col)

        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            self.in_wheel = self.in_arc = False

        return QtWidgets.QWidget.eventFilter(self, source, event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(painter.Antialiasing)

        painter.setBrush(QtGui.QBrush(QtCore.Qt.black, QtCore.Qt.SolidPattern))
        painter.drawPie(
            self.indicator_box, 16 * (math.degrees(self.wheel_angle) - 22.5), 720
        )

        painter.setClipPath(self.vArcPath)
        painter.setPen(QtCore.Qt.NoPen)

        arc = QtGui.QConicalGradient(self.center, self.e_ang)
        color = QtGui.QColor()
        color.setHsv(self.hue, self.sat, 255)
        arc.setColorAt(1 - (self.e_ang - self.s_ang) / 360.0, color)
        arc.setColorAt(1, QtCore.Qt.black)
        arc.setColorAt(0, QtCore.Qt.black)

        painter.setBrush(arc)
        painter.drawPath(self.vArcPath)
        painter.setClipPath(self.vArcPath, QtCore.Qt.NoClip)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.color_wheel_brush_1)
        painter.drawEllipse(self.color_wheel_box)
        painter.setBrush(self.color_wheel_brush_2)
        painter.drawEllipse(self.color_wheel_box)

        painter.setClipPath(self.colWhlPath)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.black, QtCore.Qt.SolidPattern))
        chVert = QtCore.QRectF(0, 0, 2, 20)
        chHort = QtCore.QRectF(0, 0, 20, 2)
        chVert.moveCenter(self.choose_point)
        chHort.moveCenter(self.choose_point)
        painter.drawRect(chVert)
        painter.drawRect(chHort)

        if self._showNames:
            painter.setClipPath(self.vArcPath, QtCore.Qt.NoClip)
            painter.setPen(QtCore.Qt.SolidLine)
            painter.drawPoints(self._namedColorPts)

    def setup(self):
        """Sets bounds on value arc and color wheel."""

        self.window_box = QtCore.QRectF(self.rect())
        self.arc_outer_box = QtCore.QRectF()
        self.indicator_box = QtCore.QRectF()
        self.arc_outer_value = QtCore.QRectF()
        self.arc_inner_value = QtCore.QRectF()
        self.color_wheel_box = QtCore.QRectF()

        self.indicator_box.setSize(QtCore.QSizeF(15, 15))
        self.arc_outer_box.setSize(self.window_box.size())
        self.arc_outer_value.setSize(
            self.window_box.size() - self.indicator_box.size() / 2.0
        )
        self.arc_inner_value.setSize(
            self.arc_outer_value.size() - QtCore.QSizeF(20, 20)
        )
        self.color_wheel_box.setSize(
            self.arc_inner_value.size() - QtCore.QSizeF(20, 20)
        )

        x = (
            self.window_box.width()
            - (self.indicator_box.width() + self.arc_inner_value.width()) / 2.0
        )
        self.center = QtCore.QPointF(x, self.window_box.height() / 2.0)

        self.arc_outer_value.moveCenter(self.center)
        self.arc_inner_value.moveCenter(self.center)
        self.color_wheel_box.moveCenter(self.center)
        self.indicator_box.moveCenter(self.wheel_center)

        self.cW_rad = self.color_wheel_box.width() / 2.0
        self.ang_w = math.radians(self.s_ang) - math.radians(self.e_ang)

        rad = self.arc_outer_value.width() / 2.0
        x, y = rad * math.cos(math.radians(self.s_ang)), -rad * math.sin(
            math.radians(self.s_ang)
        )
        x += self.center.x()
        y += self.center.y()

        self.vArcPath = QtGui.QPainterPath(QtCore.QPointF(x, y))
        self.vArcPath.arcTo(self.arc_outer_value, self.s_ang, self.e_ang - self.s_ang)
        self.vArcPath.arcTo(self.arc_inner_value, self.e_ang, self.s_ang - self.e_ang)
        self.vArcPath.closeSubpath()

        self.vInArcPath = QtGui.QPainterPath(QtCore.QPointF(x, y))
        self.vInArcPath.arcTo(self.arc_outer_box, self.s_ang, self.e_ang - self.s_ang)
        self.vInArcPath.arcTo(self.arc_inner_value, self.e_ang, self.s_ang - self.e_ang)
        self.vInArcPath.closeSubpath()

        self.colWhlPath = QtGui.QPainterPath()
        self.colWhlPath.addEllipse(self.color_wheel_box)

    @property
    def color_wheel_brush_1(self):
        return QtGui.QBrush(self.get_color_wheel())

    @property
    def color_wheel_brush_2(self):
        return QtGui.QBrush(self.get_color_wheel_fade())

    def get_color_wheel(self):
        colWhl = QtGui.QConicalGradient(self.center, self.o_ang)

        red = QtGui.QColor(QtCore.Qt.red)
        red.setHsv(red.hue(), red.saturation(), self.value)
        magenta = QtGui.QColor(QtCore.Qt.magenta)
        magenta.setHsv(magenta.hue(), magenta.saturation(), self.value)
        blue = QtGui.QColor(QtCore.Qt.blue)
        blue.setHsv(blue.hue(), blue.saturation(), self.value)
        cyan = QtGui.QColor(QtCore.Qt.cyan)
        cyan.setHsv(cyan.hue(), cyan.saturation(), self.value)
        green = QtGui.QColor(QtCore.Qt.green)
        green.setHsv(green.hue(), green.saturation(), self.value)
        yellow = QtGui.QColor(QtCore.Qt.yellow)
        yellow.setHsv(yellow.hue(), yellow.saturation(), self.value)

        whl_cols = [
            red,
            magenta,
            blue,
            cyan,
            green,
            yellow,
            red,
        ]
        for i, c in enumerate(whl_cols[:: self.rot_d]):
            colWhl.setColorAt(i / 6.0, c)

        return colWhl

    def get_color_wheel_fade(self):
        rad = min(
            self.color_wheel_box.width() / 2.0, self.color_wheel_box.height() / 2.0
        )
        cWhlFade = QtGui.QRadialGradient(self.center, rad, self.center)
        color = QtGui.QColor(QtCore.Qt.white)
        color.setHsv(color.hue(), color.saturation(), self.value)
        cWhlFade.setColorAt(0, color)
        cWhlFade.setColorAt(1, QtGui.QColor(255, 255, 255, 0))

        return cWhlFade


class Magnifier(QtWidgets.QGraphicsPixmapItem):
    """Zoomed in view around mouse.

    Could use QtWidgets.QGraphicsPixmapItem's built-in scale function
    but then wouldn't be able to have the fancy grid
    and that's what matters!
    """

    def __init__(self, parent=None):
        super(Magnifier, self).__init__(parent)

        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        self.zoom = self.width = self.height = 10
        self.size = QtCore.QSize(self.width, self.height)

        zw = 0 if self.width % 2 else self.zoom
        zh = 0 if self.height % 2 else self.zoom
        self.offset = QtCore.QPoint(
            (self.width * self.zoom + zw) // 2, (self.height * self.zoom + zh) // 2
        )

        self.background = None
        self.setPos(QtGui.QCursor().pos() - self.offset)

    def draw_grid(self, image: QtGui.QPixmap):
        """Draws a grid on image."""
        img = QtGui.QPixmap(image.width() + 1, image.height() + 1)
        p = QtGui.QPainter(img)
        p.drawPixmap(1, 1, image)

        w, h, z = img.width(), img.height(), self.zoom
        for i in range(max(self.width, self.height) + 1):
            p.drawLine(QtCore.QPoint(0, i * z), QtCore.QPoint(w, i * z))
            p.drawLine(QtCore.QPoint(i * z, 0), QtCore.QPoint(i * z, h))

        return img

    def set_brackground(self, img):
        self.background = img
        self._adjust()

    def set_size(self, w, h):
        self.width = w
        self.height = h
        self._adjust()

    def set_zoom(self, z):
        self.zoom = z
        self._adjust()

    def _adjust(self):
        """Re-set some things."""
        w, h, z = self.width, self.height, self.zoom
        zw = 0 if w % 2 else z
        zh = 0 if h % 2 else z

        self.size = QtCore.QSize(w, h)
        self.offset = QtCore.QPoint((w * z + zw) // 2, (h * z + zh) // 2)

        pos = QtGui.QCursor().pos() - self.offset
        self.setPos(pos)
        self._set_view(pos)

    def _set_view(self, pos: Union[QtCore.QPoint, QtCore.QPointF]):
        """Grab viewpoint around pos, set as image."""
        if self.background is None:
            return

        topLeft = pos - QtCore.QPoint(self.width // 2, self.height // 2)
        if not isinstance(topLeft, QtCore.QPoint):
            topLeft = topLeft.toPoint()

        rect = QtCore.QRect(topLeft, self.size)

        img = self.background.copy(rect)

        w, h, z = img.width(), img.height(), self.zoom
        img = img.scaled(w * z, h * z, QtCore.Qt.KeepAspectRatio)
        self.setPixmap(self.draw_grid(img))

    def mouse_moved(self, event: QtCore.QEvent):
        pos = QtGui.QCursor.pos()
        self.setPos(pos - self.offset)
        self._set_view(pos)


class AlphaDoubleSlider(DoubleSlider):
    """Double slider for float."""

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Key pressed event."""
        if event.key() == QtCore.Qt.Key_Control:
            self.setTickInterval(0.01)
            return
        super().keyPressEvent(event)


class AlphaSlider(QtWidgets.QWidget):
    """Editor slider for floats."""

    currentColorChanged = QtCore.Signal(float)

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__(parent=parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setMargin(0)
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setFixedWidth(55)
        self.slider = AlphaDoubleSlider()
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.slider)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 5, 0)

        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1)

        self.slider.valueChanged.connect(self.emitDoubleValueChanged)
        self.line_edit.textChanged.connect(self.emitDoubleTextChanged)

    def emitDoubleValueChanged(self):
        """Emit double value changed."""
        value = self.slider.emitDoubleValueChanged()
        if str(value) != self.line_edit.text():
            self.line_edit.setText(str(value))
            self.currentColorChanged.emit(value)

    def emitDoubleTextChanged(self):
        """Emit double text changed."""
        value = self.line_edit.text()
        if float(value) != self.slider.value():
            self.slider.setValue(float(value))
