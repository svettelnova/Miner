import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QLCDNumber, QPushButton, QAction, QMainWindow, QActionGroup
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath, QIcon, QMouseEvent, QImage, QFont
import random
from enum import Enum


class GameState(Enum):
    NOTSTARTED = 1
    RUNNING = 2
    WIN = 3
    LOSE = 4


class MinerCell:
    def __init__(self, index):
        self.__hasBomb = False
        self.__bombCount = 0
        self.__index = index
        self.__isOpen = False
        self.__hasMarkedBomb = False

    def hasBomb(self):
        return self.__hasBomb

    def setBomb(self):
        self.__hasBomb = True

    def bombCount(self):
        return self.__bombCount

    def setBombCount(self, value):
        self.__bombCount = value

    def index(self):
        return self.__index

    def isOpen(self):
        return self.__isOpen

    def hasMarkedBomb(self):
        return self.__hasMarkedBomb

    def open(self):
        self.__isOpen = True

    def markBomb(self):
        self.__hasMarkedBomb = True

    def unmarkBomb(self):
        self.__hasMarkedBomb = False


class MinerField(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.__gameState = GameState.NOTSTARTED
        self.__rows = 9
        self.__columns = 9
        self.__bombs = 10
        self.__buildCells()
        self.__cellWidth = 48
        self.__lineWidth = 1
        self.__cellColor = QColor("lightGray")
        self.__lineColor = QColor("darkGray")
        self.__openCellColor = QColor("gray")
        self.__digitColors = [None, QColor("blue"), QColor("green"), QColor("red"), QColor("red"), QColor("red"),
                              QColor("red"), QColor("red"), QColor("red")]
        image = QImage("bomb.png")
        self.__imgBomb = image.scaled(self.cellWidth(), self.cellWidth())
        image = QImage("flag.png")
        self.__imgFlag = image.scaled(self.cellWidth(), self.cellWidth())
        self.onGameOver = None
        self.onBombMarkedChanged = None
        self.__setControlSize()
        self.setMouseTracking(True)
        self.setFont(QFont(self.font().family(), 14))

    def __setControlSize(self):
        self.resize(self.columns() * self.cellSpace() + self.lineWidth(), self.rows() * self.cellSpace()
                    + self.lineWidth())

    def rows(self):
        return self.__rows

    def columns(self):
        return self.__columns

    def bombs(self):
        return self.__bombs

    def cellWidth(self):
        return self.__cellWidth

    def lineWidth(self):
        return self.__lineWidth

    def cellSpace(self):
        return self.cellWidth() + self.lineWidth()

    def gameState(self):
        return self.__gameState

    def getCell(self, rowIndex, columnIndex):
        if rowIndex < 0 or rowIndex >= self.rows() or columnIndex < 0 or columnIndex >= self.columns():
            return None
        index = rowIndex * self.columns() + columnIndex
        return self.__cells[index]

    def __buildCells(self):
        self.__cells = []
        for i in range(self.rows() * self.columns()):
            self.__cells.append(MinerCell(i))

    def setBombs(self, noBombIndex):
        curBombs = self.bombs()
        while curBombs > 0:
            bombIndex = random.randint(0, len(self.__cells) - 1)
            if not self.__cells[bombIndex].hasBomb() and bombIndex != noBombIndex:
                self.__cells[bombIndex].setBomb()
                curBombs -= 1
        for i in range(len(self.__cells)):
            self.__cells[i].setBombCount(self.__getBombCount(i))
        self.__gameState = GameState.RUNNING

    def __getBombCount(self, cellIndex, calcHasMarkedBombOnly=False):
        bombCount = 0
        rowIndex = cellIndex // self.columns()
        columnIndex = cellIndex % self.columns()
        for rIndex in range(rowIndex - 1, rowIndex + 2):
            for cIndex in range(columnIndex - 1, columnIndex + 2):
                if rIndex == rowIndex and cIndex == columnIndex:
                    continue
                cell = self.getCell(rIndex, cIndex)
                if cell != None and cell.hasBomb() and (not calcHasMarkedBombOnly or cell.hasMarkedBomb()):
                    bombCount += 1
        return bombCount

    def getCellByCoord(self, x, y):
        rowIndex = y // self.cellSpace()
        collIndex = x // self.cellSpace()
        return self.getCell(rowIndex, collIndex)

    def openCell(self, cell: MinerCell):
        if cell.isOpen():
            return
        cell.open()
        if cell.hasBomb():
            return
        if cell.bombCount() > 0:
            return
        self.__openCellsAround(cell)

    def __openCellsAround(self, cell):
        rowIndex = cell.index() // self.columns()
        columnIndex = cell.index() % self.columns()
        for rIndex in range(rowIndex - 1, rowIndex + 2):
            for cIndex in range(columnIndex - 1, columnIndex + 2):
                if rIndex == rowIndex and cIndex == columnIndex:
                    continue
                cell = self.getCell(rIndex, cIndex)
                if cell != None and not cell.hasBomb():
                    self.openCell(cell)

    def __openCellsAroundIfBombsMarked(self, cell: MinerCell):
        if self.__getBombCount(cell.index(), True) != cell.bombCount():
            return
        self.__openCellsAround(cell)

    def isWon(self):
        for i in range(len(self.__cells)):
            cell = self.__cells[i]
            if not cell.hasBomb() and not cell.isOpen():
                return False
        return True

    def __gameLost(self):
        self.__gameState = GameState.LOSE
        for i in range(len(self.__cells)):
            self.__cells[i].open()
        if self.onGameOver != None:
            self.onGameOver()

    def __gameWon(self):
        self.__gameState = GameState.WIN
        for i in range(len(self.__cells)):
            cell = self.__cells[i]
            if cell.hasBomb():
                cell.markBomb()
        if self.onGameOver != None:
            self.onGameOver()

    def restart(self, rows=None, cols=None, bombs=None):
        self.__gameState = GameState.NOTSTARTED
        if rows != None and rows > 0:
            self.__rows = rows
        if cols != None:
            self.__columns = cols
        if bombs != None:
            self.__bombs = bombs
        self.__buildCells()
        self.__setControlSize()
        self.update()

    def markedBombCount(self):
        counter = 0
        for i in range(len(self.__cells)):
            if self.__cells[i].hasMarkedBomb():
                counter += 1
        return counter

    def mousePressEvent(self, event: QMouseEvent):
        cell = self.getCellByCoord(event.x(), event.y())
        if cell == None:
            return
        if self.gameState() == GameState.NOTSTARTED and event.button() == Qt.LeftButton:
            self.setBombs(cell.index())
        if self.gameState() != GameState.RUNNING:
            return
        if event.button() == Qt.LeftButton:
            if not cell.hasMarkedBomb():
                if cell.hasBomb():
                    self.__gameLost()
                else:
                    if not cell.isOpen():
                        self.openCell(cell)
                    else:
                        self.__openCellsAroundIfBombsMarked(cell)
                    if self.isWon():
                        self.__gameWon()
                self.update()
        elif event.button() == Qt.RightButton:
            if not cell.isOpen():
                if cell.hasMarkedBomb():
                    cell.unmarkBomb()
                else:
                    cell.markBomb()
                self.update()
                if self.onBombMarkedChanged != None:
                    self.onBombMarkedChanged()

    def paintEvent(self, event):
        painter = QPainter(self)
        self.drawLines(painter)
        self.drawCells(painter)

    def drawLines(self, painter):
        painter.setPen(QPen(self.__lineColor, self.lineWidth(), Qt.SolidLine))
        path = QPainterPath()
        height = self.geometry().height()
        width = self.geometry().width()
        for i in range(self.columns() + 1):
            x = i * self.cellSpace()
            path.moveTo(x, 0)
            path.lineTo(x, height)
        for i in range(self.rows() + 1):
            y = i * self.cellSpace()
            path.moveTo(0, y)
            path.lineTo(width, y)
        painter.drawPath(path)

    def drawCells(self, painter):
        for rowIndex in range(self.rows()):
            for columnIndex in range(self.columns()):
                self.drawCell(painter, rowIndex, columnIndex)

    def drawCell(self, painter, rowIndex, columnIndex):
        cell = self.getCell(rowIndex, columnIndex)
        x = self.cellSpace() * columnIndex + self.lineWidth()
        y = self.cellSpace() * rowIndex + self.lineWidth()
        if not cell.isOpen():
            if cell.hasMarkedBomb():
                painter.drawImage(x, y, self.__imgFlag)
            return
        painter.fillRect(x, y, self.cellWidth(), self.cellWidth(), QBrush(self.__openCellColor))
        if cell.hasBomb():
            painter.drawImage(x, y, self.__imgBomb)
        else:
            if cell.bombCount() > 0:
                painter.setPen(self.__digitColors[cell.bombCount()])
                painter.drawText(x + 15, y + 30, str(cell.bombCount()))


class Miner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__iconHappy = QIcon("happy.png")
        self.__iconSad = QIcon("sad.png")
        self.__iconWon = QIcon("won.png")
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Сапёр')
        menuBar = self.menuBar()
        subMenu = menuBar.addMenu('Сложность')
        actionLight = subMenu.addAction('Легкий')
        actionLight.triggered.connect(self.changeToLightLevel)
        actionLight.setCheckable(True)
        actionMiddle = subMenu.addAction('Средний')
        actionMiddle.triggered.connect(self.changeToMiddleLevel)
        actionMiddle.setCheckable(True)
        actionHard = subMenu.addAction('Сложный')
        actionHard.triggered.connect(self.changeToHardLevel)
        actionHard.setCheckable(True)
        levelGroup = QActionGroup(self)
        levelGroup.addAction(actionLight)
        levelGroup.addAction(actionMiddle)
        levelGroup.addAction(actionHard)
        actionLight.setChecked(True)
        self.panelHeight = 50
        self.panelMargin = 10
        self.btnState = QPushButton(self)
        self.btnState.clicked.connect(self.restart)
        self.btnState.resize(self.panelHeight, self.panelHeight)
        self.btnState.setIconSize(QSize(self.panelHeight - 8, self.panelHeight - 8))
        self.btnState.setIcon(self.__iconHappy)
        self.lblBombs = QLCDNumber(self)
        self.lblBombs.resize(70, self.panelHeight)
        self.lblTimer = QLCDNumber(self)
        self.lblTimer.resize(70, self.panelHeight)
        self.minerField = MinerField(self)
        self.minerField.onGameOver = self.onGameOver
        self.minerField.onBombMarkedChanged = self.onBombMarkedChanged
        self.minerField.move(0, self.panelHeight + self.panelMargin * 2 + menuBar.height())
        self.move(100, 100)
        self.__setWidgetsGeometry()
        self.onBombMarkedChanged()
        self.gameTimeInSec = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.changeGameTime)
        self.timer.start(1000)
        self.changeGameTime()
        self.show()

    def __setWidgetsGeometry(self):
        self.setFixedSize(self.minerField.geometry().width(), self.minerField.geometry().height() +
                          self.minerField.y())
        panelTop = self.panelMargin + self.menuBar().height()
        self.btnState.move(self.width() // 2 - self.btnState.width() // 2, panelTop)
        self.lblBombs.move(self.btnState.x() - self.panelMargin - self.lblBombs.width(), panelTop)
        self.lblTimer.move(self.btnState.x() + self.btnState.width() + self.panelMargin, panelTop)

    def onGameOver(self):
        if self.minerField.gameState() == GameState.WIN:
            self.btnState.setIcon(self.__iconWon)
        else:
            self.btnState.setIcon(self.__iconSad)

    def onBombMarkedChanged(self):
        leftBombs = self.minerField.bombs() - self.minerField.markedBombCount()
        if leftBombs < 0:
            leftBombs = 0
        self.lblBombs.display(leftBombs)

    def changeGameTime(self):
        if self.minerField.gameState() != GameState.RUNNING and self.gameTimeInSec > 0:
            return
        self.lblTimer.display(self.gameTimeInSec)
        self.gameTimeInSec += 1

    def restart(self, rows=None, cols=None, bombs=None):
        self.minerField.restart(rows, cols, bombs)
        self.gameTimeInSec = 0
        self.onBombMarkedChanged()
        self.changeGameTime()
        self.__setWidgetsGeometry()
        self.btnState.setIcon(self.__iconHappy)

    def changeToLevel(self, rows, cols, bombs):
        self.restart(rows, cols, bombs)

    def changeToLightLevel(self):
        self.changeToLevel(9, 9, 10)

    def changeToMiddleLevel(self):
        self.changeToLevel(13, 16, 30)

    def changeToHardLevel(self):
        self.changeToLevel(12, 22, 52)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Miner()
    sys.exit(app.exec_())
