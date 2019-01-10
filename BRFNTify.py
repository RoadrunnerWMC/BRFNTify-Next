#!/usr/bin/python
# -*- coding: latin-1 -*-

# BRFNTify - Editor for Nintendo BRFNT font files
# Version Next Beta 1
# Copyright (C) 2009-2019 Tempus, RoadrunnerWMC

# This file is part of BRFNTify.

# BRFNTify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BRFNTify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BRFNTify.  If not, see <http://www.gnu.org/licenses/>.



# BRFNTify.py
# This is the main executable for BRFNTify



# Imports

import io
import os
import struct
import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

import TPLLib



# Globals
version = 'Beta 1'
Font = None
CharacterNames = {}




def module_path():
    """
    This will get us the program's directory, even if we are frozen using cx_Freeze
    """
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None


def GetIcon(name):
    """
    Helper function to grab a specific icon
    """
    return QtGui.QIcon('data/icon-%s.png' % name)


def createHorzLine():
    """
    Helper to create a horizontal line widget
    """
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Sunken)
    return f


def LoadCharacterNames():
    """
    Load character names
    """
    global CharacterNames
    if CharacterNames: return

    with open('data/CharNames.txt', 'r', encoding='utf-8') as f:
        d = f.read()

    for line in d.split('\n'):
        code = int(line.split(' ')[0], 16)
        name = ' '.join(line.split(' ')[1:])[1:-1]
        CharacterNames[code] = name


class Window(QtWidgets.QMainWindow):
    """
    Main window
    """

    def __init__(self):
        super().__init__(None)
        self.savename = ''

        centralWidget = QtWidgets.QWidget()

        self.view = ViewWidget()

        self.brfntScene = QtWidgets.QGraphicsScene()
        self.systemWidget = QtWidgets.QGraphicsScene()

        self.setCentralWidget(self.view)
        self.setWindowTitle('BRFNTify Next')
        ico = QtGui.QIcon()
        ico.addPixmap(QtGui.QPixmap('data/icon-logobig.png'))
        ico.addPixmap(QtGui.QPixmap('data/icon-logosmall.png'))
        self.setWindowIcon(ico)

        self.fontDock = FontMetricsDock(self)
        self.fontDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.charDock = CharMetricsDock(self)
        self.charDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.prevDock = TextPreviewDock(self)
        self.prevDock.setVisible(False)
        self.prevDock.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.prevDock.setFeatures(self.prevDock.features() | QtWidgets.QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.fontDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.charDock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.prevDock)
        self.brfntScene.selectionChanged.connect(self.charDock.updateGlyph)

        self.CreateMenus()


    def CreateMenus(self):
        """
        Helper function to create the menus
        """
        # create the actions
        self.actions = {}
        self.CreateAction('open', self.HandleOpen, GetIcon('open'), '&Open...', 'Open a font file', QtGui.QKeySequence.Open)
        self.CreateAction('save', self.HandleSave, GetIcon('save'), '&Save', 'Save the font file', QtGui.QKeySequence.Save)
        self.CreateAction('saveas', self.HandleSaveAs, GetIcon('saveas'), 'Save &as...', 'Save the font file to a new filename', QtGui.QKeySequence.SaveAs)
        self.CreateAction('generate', self.HandleGenerate, None, '&Generate', 'Generate a font from one installed on your computer', 'Ctrl+G')
        # Dock show/hide actions are created later
        self.CreateAction('leading', self.HandleLeading, GetIcon('leading'), '&Leading', 'Show or hide leading lines (the height of each line of text)', 'Ctrl+1')
        self.CreateAction('ascent', self.HandleAscent, GetIcon('ascent'), '&Ascent', 'Show or hide ascent lines (the height of capital letters)', 'Ctrl+2')
        self.CreateAction('baseline', self.HandleBaseline, GetIcon('baseline'), '&Baseline', 'Show or hide baselines (the bottom)', 'Ctrl+3')
        self.CreateAction('widths', self.HandleWidths, GetIcon('widths'), '&Widths', 'Show or hide the widths of each character', 'Ctrl+4')
        self.actions['leading'].setCheckable(True)
        self.actions['ascent'].setCheckable(True)
        self.actions['baseline'].setCheckable(True)
        self.actions['widths'].setCheckable(True)
        self.CreateAction('about', self.HandleAbout, GetIcon('about'), '&About', 'About BRFNTify Next', 'Ctrl+H')

        self.actions['fontmetrics'] = self.fontDock.toggleViewAction()
        self.actions['fontmetrics'].setText('&Font Metrics')
        self.actions['fontmetrics'].setStatusTip('Show or hide the Font Metrics window')
        self.actions['fontmetrics'].setShortcut('Ctrl+Q')
        self.actions['charmetrics'] = self.charDock.toggleViewAction()
        self.actions['charmetrics'].setText('&Character Metrics')
        self.actions['charmetrics'].setStatusTip('Show or hide the Character Metrics window')
        self.actions['charmetrics'].setShortcut('Ctrl+W')
        self.actions['textprev'] = self.prevDock.toggleViewAction()
        self.actions['textprev'].setText('&Text Preview')
        self.actions['textprev'].setStatusTip('Show or hide the Text Preview window')
        self.actions['textprev'].setShortcut('Ctrl+R')


        # create a menubar
        m = self.menuBar()
        self.fileMenu = QtWidgets.QMenu('&File', self)
        self.fileMenu.addAction(self.actions['open'])
        self.fileMenu.addAction(self.actions['save'])
        self.fileMenu.addAction(self.actions['saveas'])
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.actions['generate'])
        m.addMenu(self.fileMenu)
        self.viewMenu = QtWidgets.QMenu('&View', self)
        self.viewMenu.addAction(self.actions['fontmetrics'])
        self.viewMenu.addAction(self.actions['charmetrics'])
        self.viewMenu.addAction(self.actions['textprev'])
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.actions['leading'])
        self.viewMenu.addAction(self.actions['ascent'])
        self.viewMenu.addAction(self.actions['baseline'])
        self.viewMenu.addAction(self.actions['widths'])
        m.addMenu(self.viewMenu)
        self.helpMenu = QtWidgets.QMenu('&Help', self)
        self.helpMenu.addAction(self.actions['about'])
        m.addMenu(self.helpMenu)

        # create a statusbar
        self.status = self.statusBar()

        # add stuff to it
        self.zoomInBtn = QtWidgets.QToolButton()
        self.zoomInBtn.setText('Zoom In')
        self.zoomInBtn.setAutoRaise(True)
        self.zoomInBtn.clicked.connect(lambda: self.HandleZoom('+'))
        self.zoomInBtn.setShortcut('Ctrl++')
        self.zoomOutBtn = QtWidgets.QToolButton()
        self.zoomOutBtn.setText('Zoom Out')
        self.zoomOutBtn.setAutoRaise(True)
        self.zoomOutBtn.clicked.connect(lambda: self.HandleZoom('-'))
        self.zoomOutBtn.setShortcut('Ctrl+-')
        self.zoomBtn = QtWidgets.QToolButton()
        self.zoomBtn.setText('100%')
        self.zoomBtn.setAutoRaise(True)
        self.zoomBtn.clicked.connect(lambda: self.HandleZoom('%'))
        lyt = QtWidgets.QHBoxLayout()
        lyt.setContentsMargins(0,0,0,0)
        lyt.addWidget(self.zoomInBtn)
        lyt.addWidget(self.zoomOutBtn)
        lyt.addWidget(self.zoomBtn)
        w = QtWidgets.QWidget()
        w.setLayout(lyt)
        self.status.addPermanentWidget(w)


    def CreateAction(self, shortname, function, icon, text, statustext, shortcut, toggle=False):
        """
        Helper function to create an action
        """

        if icon is not None:
            act = QtWidgets.QAction(icon, text, self)
        else:
            act = QtWidgets.QAction(text, self)

        if shortcut is not None: act.setShortcut(shortcut)
        if statustext is not None: act.setStatusTip(statustext)
        if toggle:
            act.setCheckable(True)
        act.triggered.connect(function)

        self.actions[shortname] = act


    def sizeHint(self):
        """
        Size hint
        """
        return QtCore.QSize(786, 512)


    def ShowErrorBox(self, caption):
        """
        Show a nice error box for the current exception
        """
        toplbl = QtWidgets.QLabel(caption)

        exc_type, exc_value, tb = sys.exc_info()
        fl = io.StringIO()
        traceback.print_exception(exc_type, exc_value, tb, file=fl)
        fl.seek(0)
        btm = fl.read()

        txtedit = QtWidgets.QPlainTextEdit(btm)
        txtedit.setReadOnly(True)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toplbl)
        layout.addWidget(txtedit)
        layout.addWidget(buttonBox)

        dlg = QtWidgets.QDialog()
        dlg.setLayout(layout)
        dlg.setModal(True)
        dlg.setMinimumWidth(384)
        dlg.setWindowTitle('Error')
        buttonBox.accepted.connect(dlg.accept)
        dlg.exec_()


    def HandleOpen(self):
        """
        Open a Binary Revolution Font (.brfnt) file for editing
        """
        global Font

        # File Dialog
        fn = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a Font', '', 'Wii font files (*.brfnt);;All Files(*)')[0]
        if not fn: return

        # Put the whole thing in a try-except clause
        try:

            with open(fn, 'rb') as f:
                tmpf = f.read()

            Font = BRFNT(tmpf)

            self.fontDock.updateFields(self)
            self.brfntScene.clear()
            self.brfntScene.setSceneRect(
                0,
                0,
                Font.cellWidth * 30,
                Font.cellHeight * (((Font.charsPerRow * Font.charsPerColumn * Font.numTexs) / 30) + 1))

            x = 0
            y = 0
            i = 0
            for item in Font.glyphs:
                if i >= 30:
                    x = 0
                    y = y + item.pixmap.height()
                    i = 0

                item.setPos(x, y)
                self.brfntScene.addItem(item)
                x = x + item.pixmap.width()
                i += 1

            self.view.updateDisplay()
            self.view.setScene(self.brfntScene)
            self.prevDock.updatePreview()
            self.view.columns = 1
            self.view.updateLayout()

            self.savename = fn
            self.setWindowTitle('BRFNTify Next - %s' % fn.replace('\\', '/').split('/')[-1])

        except Exception as e:
            self.ShowErrorBox('An error occured while trying to load this file. Please refer to the information below for more details.')


    def HandleSave(self):
        """
        Save the font file back to the original file
        """
        if not self.savename:
            self.HandleSaveAs()
            return

        data = self.Save()
        if data:
            with open(self.savename, 'wb') as f:
                f.write(data)


    def HandleSaveAs(self):
        """
        Save the font file to a new file
        """
        fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', 'Wii font files (*.brfnt);;All Files(*)')[0]
        if not fn: return
        self.savename = fn

        self.HandleSave()


    def Save(self):
        """
        Save the font file and return its data
        """

        # Display a warning
        QtWidgets.QMessageBox.warning(self, 'Save', 'Saving is not yet completed. This save operation will be attempted but no guarantees.')

        try:
            return Font.save()

        except Exception as e:
            sel.ShowErrorBox('An error occured while trying to save this file. Please refer to the information below for more details.')


    def RenderGlyphsToTPL(self):
        """
        Render the glyphs to the correct Nintendo image encoding
        """
        prog = QtWidgets.QProgressDialog(self)
        prog.setRange(0, 100)
        prog.setValue(0)
        prog.setAutoClose(True)
        prog.setWindowTitle('Saving Font')
        strformat = ['I4', 'I8', 'IA4', 'IA8', 'RGB565', 'RGB4A3', 'RGBA8', '', 'CI4', 'CI8', 'CI14x2', '', '', '', 'CMPR'][Font.texFormat]
        prog.setLabelText('Saving the file (%s format)' % (strformat))
        prog.open()

        imagenum = len(Font.glyphs) // 64
        imagenum += 1 if len(Font.glyphs) % 64 else 0

        def handlePctUpdated():
            """
            Called when a Decoder object updates its percentage
            """
            newpct = encoder.progress
            totalPct = (texnum / imagenum) + (newpct / imagenum)
            totalPct *= 100
            prog.setValue(totalPct)
            prog.update()


        texs = []
        for texnum in range(imagenum):

            glyphs = Font.glyphs[texnum * 64: (texnum * 64) + 64]
            glyphW, glyphH = Font.cellWidth, Font.cellHeight

            # Put the glyphs together
            texImg = QtGui.QImage(glyphW * 8, glyphH * 8, QtGui.QImage.Format_ARGB32)
            texImg.fill(Qt.transparent)
            painter = QtGui.QPainter(texImg)
            i = 0
            for y in range(8):
                for x in range(8):
                    if i >= len(glyphs): continue
                    painter.drawPixmap(x * glyphW, y * glyphH, glyphs[i].pixmap)
                    i += 1
            del painter
            import random
            texImg.save(str(random.random()) + '.png')

            # The recommended method:
            # texImg.constBits().asstring(texImg.byteCount())
            # is giving me trouble. For future reference, the error is
            # SystemError: Bad call flags in PyCFunction_Call. METH_OLDARGS is no longer supported!
            # So I'll have to do this the slow way. :(
            tex = bytearray(texImg.width() * texImg.height() * 4)
            i = 0
            for y in range(texImg.height()):
                for x in range(texImg.width()):
                    px = texImg.pixel(x, y)
                    tex[i + 0] = QtGui.qAlpha(px)
                    tex[i + 1] = QtGui.qRed(px)
                    tex[i + 2] = QtGui.qGreen(px)
                    tex[i + 3] = QtGui.qBlue(px)

            # Encode into IA4 format
            encoder = TPLLib.encoder(TPLLib.IA4)
            encoder = encoder(tex, texImg.width(), texImg.height(), handlePctUpdated)
            texs.append(bytes(encoder.run()))

        prog.setValue(100)
        return texs


    def HandleGenerate(self):
        """
        Generate a font
        """

        dlg = GenerateDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            # Create a bunch of glyphs, I guess.

            chars = dlg.charrange.text()

            qfont = dlg.fontCombo.currentFont()
            qfont.setPointSize(int(dlg.sizeCombo.currentText()))
            if dlg.styleCombo.currentIndex() == 1:
                qfont.setBold(True)
            elif dlg.styleCombo.currentIndex() == 2:
                qfont.setStyle(1)
            elif dlg.styleCombo.currentIndex() == 3:
                qfont.setStyle(1)
                qfont.setBold(True)

            global Font
            Font = BRFNT.generate(qfont, chars, dlg.fg, dlg.bg)

            x = 0
            y = 0
            i = 0
            self.brfntScene.clear()
            self.brfntScene.setSceneRect(0, 0, 5000, 5000)

            for item in Font.glyphs:
                if i >= 30:
                    x = 0
                    y = y + item.pixmap.height()
                    i = 0
                item.setPos(x, y)
                self.brfntScene.addItem(item)
                x = x + item.pixmap.width()
                i += 1

            self.fontDock.updateFields(self)
            self.view.updateDisplay()
            self.view.setScene(self.brfntScene)
            self.prevDock.updatePreview()
            self.view.columns = 1
            self.view.updateLayout()

            self.setWindowTitle('BRFNTify Next - untitled')



    def HandleLeading(self, toggled):
        """
        Handle the user toggling Leading
        """
        self.view.updateLeading(toggled)

    def HandleAscent(self, toggled):
        """
        Handle the user toggling Ascent
        """
        self.view.updateAscent(toggled)

    def HandleBaseline(self, toggled):
        """
        Handle the user toggling Baseline
        """
        self.view.updateBaseline(toggled)

    def HandleWidths(self, toggled):
        """
        Handle the user toggling Widths
        """
        self.view.updateWidths(toggled)


    def HandleAbout(self):
        """
        Handle the user clicking About
        """
        try:
            with open('readme.md', 'r', encoding='utf-8') as f:
                readme = f.read()
        except:
            readme = 'BRFNTify %s by Tempus, RoadrunnerWMC\n(No readme.md found!)\nLicensed under GPL' % version

        txtedit = QtWidgets.QPlainTextEdit(readme)
        txtedit.setReadOnly(True)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(txtedit)
        layout.addWidget(buttonBox)

        dlg = QtWidgets.QDialog()
        dlg.setLayout(layout)
        dlg.setModal(True)
        dlg.setMinimumWidth(512)
        dlg.setWindowTitle('About')
        buttonBox.accepted.connect(dlg.accept)
        dlg.exec_()


    zoomLevels = [20.0, 35.0, 50.0, 65.0, 80.0, 90.0, 100.0, 125.0, 150.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0]
    zoomidx = zoomLevels.index(100.0)
    def HandleZoom(self, btn):
        """
        Handle ANY of the zoom buttons being clicked
        """
        oldz = self.zoomLevels[self.zoomidx]
        if btn == '+': self.zoomidx += 1
        elif btn == '-': self.zoomidx -= 1
        elif btn == '%': self.zoomidx = self.zoomLevels.index(100.0)
        if self.zoomidx < 0: self.zoomidx = 0
        if self.zoomidx > len(self.zoomLevels) - 1: self.zoomidx = len(self.zoomLevels) - 1

        z = self.zoomLevels[self.zoomidx]

        self.zoomBtn.setText('%d%%' % int(z))
        self.zoomInBtn.setEnabled(self.zoomidx < len(self.zoomLevels) - 1)
        self.zoomOutBtn.setEnabled(self.zoomidx > 0)

        self.view.scale(z/oldz, z/oldz)
        self.view.zoom = z
        self.view.updateLayout()



class GenerateDialog(QtWidgets.QDialog):
    """
    Allows the user to generate a glyph table from an installed font
    """
    fg = Qt.black
    bg = Qt.white

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Generate a Font')

        # Font Setting Groups
        self.fontGroupBox = QtWidgets.QGroupBox('Font Generation')

        self.fontCombo = QtWidgets.QFontComboBox()
        self.sizeCombo = QtWidgets.QComboBox()
        self.styleCombo = QtWidgets.QComboBox()
        self.charrange = QtWidgets.QLineEdit()
        self.fgLabel = QtWidgets.QLabel()
        self.bgLabel = QtWidgets.QLabel()
        fgBtn = QtWidgets.QPushButton('Choose...')
        bgBtn = QtWidgets.QPushButton('Choose...')

        fg = QtGui.QPixmap(48, 24)
        fg.fill(self.fg)
        bg = QtGui.QPixmap(48, 24)
        bg.fill(self.bg)
        self.fgLabel.setPixmap(fg)
        self.bgLabel.setPixmap(bg)

        colorlayout = QtWidgets.QGridLayout()
        colorlayout.addWidget(QtWidgets.QLabel('Foreground:'), 0, 0)
        colorlayout.addWidget(QtWidgets.QLabel('Background:'), 0, 1)
        colorlayout.addWidget(self.fgLabel, 1, 0)
        colorlayout.addWidget(self.bgLabel, 1, 1)
        colorlayout.addWidget(fgBtn, 2, 0)
        colorlayout.addWidget(bgBtn, 2, 1)

        fontlayout = QtWidgets.QGridLayout()
        fontlayout.addWidget(QtWidgets.QLabel('Font:'), 0, 0, 1, 1, Qt.AlignRight)
        fontlayout.addWidget(self.fontCombo, 0, 1, 1, 3)
        fontlayout.addWidget(QtWidgets.QLabel('Size:'), 1, 0, 1, 1, Qt.AlignRight)
        fontlayout.addWidget(self.sizeCombo, 1, 1, 1, 1)
        fontlayout.addWidget(QtWidgets.QLabel('Style:'), 1, 2, 1, 1, Qt.AlignRight)
        fontlayout.addWidget(self.styleCombo, 1, 3, 1, 1)
        fontlayout.addWidget(QtWidgets.QLabel('Character Range:'), 2, 0, 1, 1, Qt.AlignRight)
        fontlayout.addWidget(self.charrange, 2, 1, 1, 3)
        fontlayout.addWidget(QtWidgets.QLabel('Colors:'), 3, 0, 1, 1, Qt.AlignRight)
        fontlayout.addLayout(colorlayout, 3, 1, 1, 3)
        self.fontGroupBox.setLayout(fontlayout)

        self.styleCombo.addItems(['Normal', 'Bold', 'Italic', 'Bold Italic'])
        self.findSizes(self.fontCombo.currentFont())

        fgBtn.clicked.connect(self.fgBtnClick)
        bgBtn.clicked.connect(self.bgBtnClick)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        Layout = QtWidgets.QVBoxLayout()
        Layout.addWidget(self.fontGroupBox)
        Layout.addWidget(buttonBox)

        self.setLayout(Layout)


    def findSizes(self, font):
        """
        Add font sizes to self.sizeCombo
        """
        fontDatabase = QtGui.QFontDatabase()
        currentSize = self.sizeCombo.currentText()
        self.sizeCombo.blockSignals(True)
        self.sizeCombo.clear()

        if fontDatabase.isSmoothlyScalable(font.family(), fontDatabase.styleString(font)):
            for size in QtGui.QFontDatabase.standardSizes():
                self.sizeCombo.addItem(str(size))
                self.sizeCombo.setEditable(True)
        else:
            for size in fontDatabase.smoothSizes(font.family(), fontDatabase.styleString(font)):
                self.sizeCombo.addItem(str(size))
                self.sizeCombo.setEditable(False)

        self.sizeCombo.blockSignals(False)

        sizeIndex = self.sizeCombo.findText(currentSize)
        if sizeIndex == -1:
            self.sizeCombo.setCurrentIndex(max(0, self.sizeCombo.count() / 3))
        else:
            self.sizeCombo.setCurrentIndex(sizeIndex)


    def fgBtnClick(self):
        """
        User clicked the Choose... button for the foreground color
        """
        dlg = QtWidgets.QColorDialog(self)
        dlg.setOption(dlg.ShowAlphaChannel, True)
        dlg.setCurrentColor(self.fg)
        dlg.open()
        dlg.finished.connect(lambda state: self.fgBtnClick2(state, dlg))


    def fgBtnClick2(self, state, dlg):
        """
        Called when the user closes the color dialog
        """
        if state != dlg.Accepted: return

        self.fg = dlg.currentColor()

        fg = QtGui.QPixmap(48, 24)
        fg.fill(self.fg)
        self.fgLabel.setPixmap(fg)


    def bgBtnClick(self):
        """
        User clicked the Choose... button for the background color
        """
        dlg = QtWidgets.QColorDialog(self)
        dlg.setOption(dlg.ShowAlphaChannel, True)
        dlg.setCurrentColor(self.bg)
        dlg.open()
        dlg.finished.connect(lambda state: self.bgBtnClick2(state, dlg))


    def bgBtnClick2(self, state, dlg):
        """
        Called when the user closes the color dialog
        """
        if state != dlg.Accepted: return

        self.bg = dlg.currentColor()

        bg = QtGui.QPixmap(48, 24)
        bg.fill(self.bg)
        self.bgLabel.setPixmap(bg)



class Glyph(QtWidgets.QGraphicsItem):
    """
    Class for a character glyph
    """

    def __init__(self, pixmap, char, leftmargin=0, charwidth=0, fullwidth=0):
        super().__init__()

        self.char = char
        self.leftmargin = leftmargin
        self.charwidth = charwidth
        self.fullwidth = fullwidth
        self.pixmap = pixmap
        self.boundingRect = QtCore.QRectF(0,0,pixmap.width(),pixmap.height())
        self.selectionRect = QtCore.QRectF(0,0,pixmap.width()-1,pixmap.height()-1)

        self.setFlag(self.ItemIsMovable, False)
        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemIsFocusable, True)


    def value(self, encoding):
        """
        Get the glyph's value in the given encoding
        """
        b = self.char.encode(encoding, 'replace')
        if len(b) == 1: b = b'\0' + b
        return struct.unpack_from('>H', b)


    def updateToolTip(self, encoding):
        """
        Update the glyph's tooltip
        """
        if self.char is not None:
            text = '<p>Character:</p><p><span style="font-size: 24pt;">&#' + \
                    str(ord(self.char)) + \
                    ';</span></p><p>Value: 0x' + \
                    '%X' % self.value(encoding)
        else:
            text = '<p>Character: <span style="font-size: 24pt;">Unknown Glyph'


        self.setToolTip(text)


    def boundingRect(self):
        """
        Required for Qt
        """
        return self.boundingRect


    def contextMenuEvent(self, e):
        """
        Handle right-clicking the glyph
        """
        QtWidgets.QGraphicsItem.contextMenuEvent(self, e)

        menu = QtWidgets.QMenu()
        menu.addAction('Import...', self.handleImport)
        menu.addAction('Export...', self.handleExport)
        menu.exec_(e.screenPos())


    def handleExport(self):
        """
        Handle the pixmap being exported
        """

        # Get the name
        fn = QtWidgets.QFileDialog.getSaveFileName(window, 'Choose a PNG file', '', 'PNG image file (*.png);;All Files(*)')[0]
        if not fn: return

        # Save it
        self.pixmap.save(fn)


    def handleImport(self):
        """
        Handle a new pixmap being imported
        """

        # Get the name
        fn = QtWidgets.QFileDialog.getOpenFileName(window, 'Choose a PNG file', '', 'PNG image file (*.png);;All Files(*)')[0]
        if not fn: return

        # Open it
        try: pix = QtGui.QPixmap(fn)
        except: return

        if pix.height() > self.pixmap.height():
            pix = pix.scaledToHeight(self.pixmap.height())
        if pix.width() > self.pixmap.width():
            pix = pix.scaledToWidth(self.pixmap.width())

        self.pixmap = pix
        window.prevDock.updatePreview()


    def paint(self, painter, option, widget):
        """
        Paint the object
        """

        painter.drawPixmap(0, 0, self.pixmap)

        if self.isSelected():
            painter.setPen(QtGui.QPen(Qt.blue, 1, Qt.SolidLine))
            painter.drawRect(self.selectionRect)
            painter.fillRect(self.selectionRect, QtGui.QColor.fromRgb(255, 255, 255, 64))



def FindGlyph(char):
    """
    Return a Glyph object for the string character, or None if none exists
    """
    default = None
    for glyph in Font.glyphs:
        if glyph.char == char:
            return glyph
        elif ord(glyph.char) == Font.defaultchar:
            default = glyph
    return default



class FontMetricsDock(QtWidgets.QDockWidget):
    """
    A dock widget that displays font-wide metrics
    """
    typeList = ['0', '1', '2'] # TODO: check exactly what the valid values are
    encodingList = ['UTF-8LE', 'UTF-8BE', 'UTF-16LE', 'UTF-16BE', 'SJIS', 'CP1252', 'COUNT']
    formatList = ['I4', 'I8', 'IA4', 'IA8', 'RGB4A3', 'RGB565', 'RGBA8', 'Unknown', 'CI4', 'CI8', 'CI14x2', 'Unknown', 'Unknown', 'Unknown', 'CMPR/S3TC']
    parent = None

    def __init__(self, parent):
        super().__init__(parent)

        # Metrics Group
        self.defaultchar = QtWidgets.QLineEdit() # Default char for exceptions
        self.defaultchar.setMaxLength(1)
        self.defaultchar.setMaximumWidth(30)

        self.fonttype = 0
        self.encoding = 'None'
        self.format = 'None'
        # Default Char
        self.leftmargin = 0
        self.charwidth = 0
        self.fullwidth = 0
        self.leading = 0
        self.ascent = 0
        self.baseline = 0
        self.width = 0
        self.height = 0

        self.setupGui()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)
        sp = w.sizePolicy()
        w.setSizePolicy(sp)
        self.setWidget(w)

        self.setWindowTitle('Font Metrics')


    def setupGui(self):

        self.fonttypeEdit = QtWidgets.QComboBox()
        self.encodingEdit = QtWidgets.QComboBox()
        self.formatEdit = QtWidgets.QComboBox()
        self.defaultcharEdit = QtWidgets.QLineEdit()
        self.leftmarginEdit = QtWidgets.QSpinBox()
        self.charwidthEdit = QtWidgets.QSpinBox()
        self.fullwidthEdit = QtWidgets.QSpinBox()
        self.leadingEdit = QtWidgets.QSpinBox()
        self.ascentEdit = QtWidgets.QSpinBox()
        self.baselineEdit = QtWidgets.QSpinBox()
        self.widthEdit = QtWidgets.QSpinBox()
        self.heightEdit = QtWidgets.QSpinBox()
        self.edits = [self.fonttypeEdit, self.encodingEdit, self.formatEdit, self.defaultcharEdit, self.leftmarginEdit, self.charwidthEdit, self.fullwidthEdit, self.leadingEdit, self.ascentEdit, self.baselineEdit, self.widthEdit, self.heightEdit]

        self.fonttypeEdit.currentIndexChanged.connect(lambda: self.boxChanged('combo', 'fonttype'))
        self.encodingEdit.currentIndexChanged.connect(lambda: self.boxChanged('combo', 'encoding'))
        self.formatEdit.currentIndexChanged.connect(lambda: self.boxChanged('combo', 'format'))
        self.defaultcharEdit.textChanged.connect(lambda: self.boxChanged('line', 'defaultchar'))
        self.leftmarginEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'leftmargin'))
        self.charwidthEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'charwidth'))
        self.fullwidthEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'fullwidth'))
        self.leadingEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'leading'))
        self.ascentEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'ascent'))
        self.baselineEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'baseline'))
        self.widthEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'width'))
        self.heightEdit.valueChanged.connect(lambda: self.boxChanged('spin', 'height'))

        self.fonttypeEdit.addItems(self.typeList)
        self.encodingEdit.addItems(self.encodingList)
        self.formatEdit.addItems(self.formatList)
        self.defaultcharEdit.setMaxLength(1)
        self.defaultcharEdit.setMaximumWidth(30)

        for e in self.edits: e.setEnabled(False)

        lyt = QtWidgets.QFormLayout()
        lyt.addRow('Font Type:', self.fonttypeEdit)
        lyt.addRow('Encoding:', self.encodingEdit)
        lyt.addRow('Texture Format:', self.formatEdit)
        lyt.addRow('Default Char:', self.defaultcharEdit)
        lyt.addRow('Left Margin:', self.leftmarginEdit)
        lyt.addRow('Char Width:', self.charwidthEdit)
        lyt.addRow('Full Width:', self.fullwidthEdit)
        lyt.addRow('Leading:', self.leadingEdit)
        lyt.addRow('Ascent:', self.ascentEdit)
        lyt.addRow('Baseline:', self.baselineEdit)
        lyt.addRow('Width:', self.widthEdit)
        lyt.addRow('Height:', self.heightEdit)
        self.layout = lyt


    def updateFields(self, parent):

        for e in self.edits: e.setEnabled(True)

        self.fonttypeEdit.setCurrentIndex(self.typeList.index(str(Font.fonttype)))
        self.encodingEdit.setCurrentIndex(self.encodingList.index(Font.encoding))
        self.formatEdit.setCurrentIndex(Font.texFormat)
        self.defaultcharEdit.setText(chr(Font.defaultchar))
        self.leftmarginEdit.setValue(Font.leftmargin)
        self.charwidthEdit.setValue(Font.charwidth)
        self.fullwidthEdit.setValue(Font.fullwidth)
        self.leadingEdit.setValue(Font.leading)
        self.ascentEdit.setValue(Font.ascent)
        self.baselineEdit.setValue(Font.baseLine)
        self.widthEdit.setValue(Font.width)
        self.heightEdit.setValue(Font.height)
        self.parent = parent


    def boxChanged(self, type, name):
        """
        A box was changed
        """
        if self.parent is None: return
        if type == 'combo':
            if name == 'fonttype':
                Font.fonttype = self.fonttypeEdit.currentText()
            elif name == 'encoding':
                Font.encoding = self.encodingEdit.currentText()
                for g in Font.glyphs:
                    g.updateToolTip(Font.encoding)
            elif name == 'format':
                Font.type = self.formatEdit.currentIndex()
        elif type == 'line':
            if name == 'defaultchar':
                Font.defaultchar = ord(self.defaultcharEdit.text())
        elif type == 'spin':
            if name in ('leftmargin', 'charwidth', 'fullwidth', 'leading', 'ascent', 'width', 'height'):
                newval = eval('self.%sEdit.value()' % name)
                setattr(Font, name, newval)
            elif name == 'baseline':
                Font.baseLine = self.baselineEdit.value()

        window.brfntScene.update()
        window.prevDock.updatePreview()



class CharMetricsDock(QtWidgets.QDockWidget):
    """
    A dock widget that displays glyph metrics
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.value = None
        self.leftmargin = 0
        self.charwidth = 0
        self.fullwidth = 0

        glyphFont = QtGui.QFont()
        glyphFont.setPointSize(22)
        glyphNameFont = QtGui.QFont()
        glyphNameFont.setPointSize(glyphNameFont.pointSize() * .95)

        self.glyphLabel = QtWidgets.QLabel()
        self.glyphLabel.setFont(glyphFont)
        self.glyphNameLabel = QtWidgets.QLabel()
        self.glyphNameLabel.setFont(glyphNameFont)
        self.glyphNameLabel.setWordWrap(True)
        self.glyphValueLabel = QtWidgets.QLabel('0x')
        self.glyphValueEdit = HexSpinBox()
        self.glyphValueEdit.setMaximum(0xFFFF)
        self.glyphValueEdit.valueChanged.connect(self.handleGlyphvalueEditChanged)
        self.glyphValueEdit.setEnabled(False)
        L = QtWidgets.QGridLayout()
        L.setContentsMargins(0,0,0,0)
        L.setSpacing(0)
        L.setColumnStretch(1, 1)
        L.addWidget(self.glyphValueLabel, 0, 0)
        L.addWidget(self.glyphValueEdit, 0, 1)
        gv = QtWidgets.QWidget()
        gv.setLayout(L)
        self.leftmarginEdit = QtWidgets.QSpinBox()
        self.leftmarginEdit.setRange(-0x7F, 0x7F)
        self.leftmarginEdit.valueChanged.connect(self.handleLeftmarginEditChanged)
        self.leftmarginEdit.setEnabled(False)
        self.charwidthEdit = QtWidgets.QSpinBox()
        self.charwidthEdit.setMaximum(0xFF)
        self.charwidthEdit.valueChanged.connect(self.handleCharwidthEditChanged)
        self.charwidthEdit.setEnabled(False)
        self.fullwidthEdit = QtWidgets.QSpinBox()
        self.fullwidthEdit.setRange(-0x7F, 0x7F)
        self.fullwidthEdit.valueChanged.connect(self.handleFullwidthEditChanged)
        self.fullwidthEdit.setEnabled(False)
        horzA = createHorzLine()
        self.moveL = QtWidgets.QPushButton('Move Left')
        self.moveL.clicked.connect(lambda: self.handleMove('L'))
        self.moveL.setEnabled(False)
        self.moveR = QtWidgets.QPushButton('Move Right')
        self.moveR.clicked.connect(lambda: self.handleMove('R'))
        self.moveR.setEnabled(False)
        horzB = createHorzLine()
        self.delete = QtWidgets.QPushButton('Delete')
        self.delete.clicked.connect(self.handleDelete)
        self.delete.setEnabled(False)
        horzC = createHorzLine()
        self.copy = QtWidgets.QPushButton('Copy')
        self.copy.clicked.connect(self.handleCopy)
        self.copy.setEnabled(False)

        toplyt = QtWidgets.QFormLayout()
        toplyt.addRow('Character:', self.glyphLabel)
        toplyt.addRow('', self.glyphNameLabel)

        lyt = QtWidgets.QFormLayout()
        lyt.addRow('Character Value:', gv)
        lyt.addRow('Left Margin:', self.leftmarginEdit)
        lyt.addRow('Texture Width:', self.charwidthEdit)
        lyt.addRow('Effective Width:', self.fullwidthEdit)

        mainLyt = QtWidgets.QGridLayout()
        mainLyt.addLayout(toplyt, 0, 0)
        mainLyt.addLayout(lyt, 1, 0)
        mainLyt.addWidget(horzA, 2, 0)
        mainLyt.addWidget(self.moveL, 3, 0)
        mainLyt.addWidget(self.moveR, 4, 0)
        mainLyt.addWidget(horzB, 5, 0)
        mainLyt.addWidget(self.delete, 6, 0)
        mainLyt.addWidget(horzC, 7, 0)
        mainLyt.addWidget(self.copy, 8, 0)
        mainLyt.setRowStretch(9, 1)

        w = QtWidgets.QWidget()
        w.setLayout(mainLyt)
        self.setWidget(w)

        self.setWindowTitle('Character Metrics')


    def updateGlyph(self):
        """
        Update the info for the currently selected glyph
        """
        glyphs = window.brfntScene.selectedItems()
        if len(glyphs) != 1:
            self.value = None
            self.glyphLabel.setText('')
            self.glyphNameLabel.setText('')
            self.glyphValueEdit.setValue(0)
            self.leftmarginEdit.setValue(0)
            self.charwidthEdit.setValue(0)
            self.fullwidthEdit.setValue(0)
            self.glyphValueEdit.setEnabled(False)
            self.leftmarginEdit.setEnabled(False)
            self.charwidthEdit.setEnabled(False)
            self.fullwidthEdit.setEnabled(False)
            self.moveL.setEnabled(False)
            self.moveR.setEnabled(False)
            self.delete.setEnabled(False)
            self.copy.setEnabled(False)
        else:
            glyph = glyphs[0]
            self.value = glyph
            self.glyphLabel.setText(glyph.char)
            self.glyphNameLabel.setText(CharacterNames[ord(glyph.char)])
            self.glyphValueEdit.setValue(ord(glyph.char))
            self.leftmarginEdit.setValue(glyph.leftmargin)
            self.charwidthEdit.setValue(glyph.charwidth)
            self.fullwidthEdit.setValue(glyph.fullwidth)
            self.glyphValueEdit.setEnabled(True)
            self.leftmarginEdit.setEnabled(True)
            self.charwidthEdit.setEnabled(True)
            self.fullwidthEdit.setEnabled(True)
            self.moveL.setEnabled(True)
            self.moveR.setEnabled(True)
            self.delete.setEnabled(True)
            self.copy.setEnabled(True)

    def handleGlyphvalueEditChanged(self):
        """
        Handle changes to the glyph value line edit
        """
        if self.value is None: return
        self.value.char = chr(self.glyphValueEdit.value())
        self.value.update()
        window.prevDock.updatePreview()
        self.glyphLabel.setText(self.value.char)

        name = CharacterNames[ord(self.value.char)]
        self.glyphNameLabel.setText(name)

    def handleLeftmarginEditChanged(self):
        """
        Handle changes to the left margin line edit
        """
        if self.value is None: return
        self.value.leftmargin = self.leftmarginEdit.value()
        self.value.update()
        window.prevDock.updatePreview()

    def handleCharwidthEditChanged(self):
        """
        Handle changes to the char width line edit
        """
        if self.value is None: return
        self.value.charwidth = self.charwidthEdit.value()
        self.value.update()
        window.prevDock.updatePreview()

    def handleFullwidthEditChanged(self):
        """
        Handle changes to the full width line edit
        """
        if self.value is None: return
        self.value.fullwidth = self.fullwidthEdit.value()
        self.value.update()
        window.prevDock.updatePreview()

    def handleMove(self, dir):
        """
        Handle either of the Move buttons being clicked
        """
        current = Font.glyphs.index(self.value)
        new = current + 1 if dir == 'R' else current - 1
        Font.glyphs[current], Font.glyphs[new] = Font.glyphs[new], Font.glyphs[current]

        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()

    def handleDelete(self):
        """
        Handle the Delete button being clicked
        """
        Font.glyphs.remove(self.value)
        window.brfntScene.removeItem(self.value)

        del self.value
        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()

    def handleCopy(self):
        """
        Handle the Copy button being clicked
        """
        c = self.value # c: "current"
        new = Glyph(c.pixmap, c.value, c.leftmargin, c.charwidth, c.fullwidth)
        new.updateToolTip(Font.encoding)
        window.brfntScene.addItem(new)
        c.setSelected(False)
        new.setSelected(True)

        Font.glyphs.insert(Font.glyphs.index(c)+1, new)

        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()



class TextPreviewDock(QtWidgets.QDockWidget):
    """
    Dock that lets you type some text and see a preview of it in the font
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.textEdit = QtWidgets.QPlainTextEdit()
        self.textEdit.setEnabled(False)
        self.textEdit.textChanged.connect(self.updatePreview)
        self.textEdit.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.textEdit.setMinimumWidth(128)

        self.prevWidget = QtWidgets.QLabel()
        self.prevWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        scrl = QtWidgets.QScrollArea()
        scrl.setWidget(self.prevWidget)
        scrl.setWidgetResizable(True)

        lyt = QtWidgets.QGridLayout()
        lyt.addWidget(self.textEdit, 0, 0)
        lyt.addWidget(scrl, 0, 1)
        lyt.setColumnStretch(1, 1)
        lyt.setContentsMargins(0,0,0,0)
        lyt.setSpacing(0)

        w = QtWidgets.QWidget()
        w.setLayout(lyt)
        self.setWidget(w)
        self.setMinimumHeight(96)

        self.setWindowTitle('T. Preview')


    def updatePreview(self):
        """
        Redraw the preview image
        """
        if Font.encoding is None:
            self.textEdit.setEnabled(False)
            self.prevWidget.setText('')
            return
        self.textEdit.setEnabled(True)

        # Get the text
        txt = self.textEdit.toPlainText()

        # Pick a size for the pixmap
        width = 0
        for line in txt.split('\n'):
            charOffset = 0
            linewidth = 0

            for char in line:
                glyph = FindGlyph(char)
                if glyph is None: continue
                w = charOffset + glyph.charwidth
                if w > linewidth: linewidth = w
                charOffset += glyph.fullwidth

            if linewidth > width: width = linewidth

        height = Font.height * (txt.count('\n') + 1)

        # Make the pixmap
        pix = QtGui.QPixmap(width + 4, height + 4)
        pix.fill(QtGui.QColor.fromRgb(0,0,0,0))
        paint = QtGui.QPainter(pix)

        # Draw the chars to the pixmap
        i = 0
        for line in txt.split('\n'):
            y = Font.leading * i
            x = 0
            for char in line:
                glyph = FindGlyph(char)
                if glyph is None: continue
                # The glyph.pixmap.copy(...) part allows the image to be cropped to glyph.charwidth+1
                paint.drawPixmap(x + glyph.leftmargin, y, glyph.pixmap.copy(0,0, glyph.charwidth+1, glyph.pixmap.height()))
                x += glyph.fullwidth
            i += 1

        # Finish up
        del paint
        self.prevWidget.setPixmap(pix)



# This is copy-pasted from Reggie, mostly
class HexSpinBox(QtWidgets.QSpinBox):
    class HexValidator(QtGui.QValidator):
        def __init__(self, min, max):
            super().__init__()
            self.valid = set('0123456789abcdef')
            self.min = min
            self.max = max

        def validate(self, input, pos):

            try:
                value = int(input, 16)
            except ValueError:
                return (self.Invalid, input, pos)

            if value < self.min or value > self.max:
                return (self.Intermediate, self.format % value, pos)

            return (self.Acceptable, self.format % value, pos)


    def __init__(self, format='%04X', *args):
        super().__init__(*args)
        self.validator = self.HexValidator(self.minimum(), self.maximum())
        self.validator.format = format

    def setMinimum(self, value):
        self.validator.min = value
        QtWidgets.QSpinBox.setMinimum(self, value)

    def setMaximum(self, value):
        self.validator.max = value
        QtWidgets.QSpinBox.setMaximum(self, value)

    def setRange(self, min, max):
        self.validator.min = min
        self.validator.max = max
        QtWidgets.QSpinBox.setMinimum(self, min)
        QtWidgets.QSpinBox.setMaximum(self, max)

    def validate(self, text, pos):
        return self.validator.validate(text, pos)

    def textFromValue(self, value):
        return self.validator.format % value

    def valueFromText(self, value):
        return int(str(value), 16)




class ViewWidget(QtWidgets.QGraphicsView):
    """
    Widget that lets you see the font glyphs
    """

    characterSelected = QtCore.pyqtSignal(str)
    zoom = 100.0
    columns = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.Images = []
        self.drawLeading = False
        self.drawAscent = False
        self.drawBaseline = False
        self.drawWidths = False

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(119, 136, 153)))
        self.setMouseTracking(True)
        self.YScrollBar = QtWidgets.QScrollBar(Qt.Vertical, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


    def updateDisplay(self):
        self.update()


    def updateLeading(self, checked):
        self.drawLeading = checked
        if self.scene() is not None: self.scene().update()


    def updateAscent(self, checked):
        self.drawAscent = checked
        if self.scene() is not None: self.scene().update()


    def updateBaseline(self, checked):
        self.drawBaseline = checked
        if self.scene() is not None: self.scene().update()


    def updateWidths(self, checked):
        self.drawWidths = checked
        if self.scene() is not None: self.scene().update()


    def resizeEvent(self, e):
        QtWidgets.QGraphicsView.resizeEvent(self, e)
        self.updateLayout()


    def updateLayout(self, force=False):
        if Font is None: return

        cols = int((1 / (self.zoom / 100)) * self.viewport().width() / Font.cellWidth)
        if cols < 1: cols = 1
        if cols == self.columns and not force: return

        self.columns = cols

        for i in range(len(Font.glyphs)):
            itm = Font.glyphs[i]
            x = Font.cellWidth * (i % cols)
            y = Font.cellHeight * int(i / cols)
            itm.setPos(x, y)

        self.scene().setSceneRect(0, 0, Font.cellWidth * cols, Font.cellHeight * (1+int(len(Font.glyphs) / cols)))


    def drawForeground(self, painter, rect):

        # Calculate the # of rows, and round up
        rows = len(Font.glyphs) / self.columns
        if float(int(rows)) == rows: rows = int(rows)
        else: rows = int(rows) + 1
        # Calculate columns
        cols = self.columns


        # Draw stuff

        drawLine = painter.drawLine

        # Leading
        if self.drawLeading:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255, 0, 0, 255), 2))
            for i in range(rows):
                drawLine(0,
                         (i * Font.cellHeight) + Font.leading,
                         Font.cellWidth * cols, (i * Font.cellHeight) + Font.leading)

        # Ascent
        if self.drawAscent:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(0, 255, 0, 255), 2))
            for i in range(rows):
                drawLine(0,
                         ((i+1) * Font.cellHeight) - Font.ascent,
                         Font.cellWidth * cols, ((i+1) * Font.cellHeight) - Font.ascent)

        # Baseline
        if self.drawBaseline:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(0, 0, 255, 255), 2))
            for i in range(rows):
                drawLine(0,
                         (i * Font.cellHeight) + Font.baseLine,
                         Font.cellWidth * cols, (i * Font.cellHeight) + Font.baseLine)

        # Widths
        if self.drawWidths:
            for i, fi in enumerate(Font.glyphs):
                j = int(i % cols)
                x1 = j * Font.cellWidth
                x2 = x1 + fi.charwidth + 2
                tooWide = x1 + Font.cellWidth < x2

                painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255, 255, 0, 255), 2))
                drawLine(x1, (int(i/cols) * Font.cellHeight) + 1, x1, (int(i/cols + 1) * Font.cellHeight) - 1)
                if tooWide: continue
                painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255, 255, 0, 127), 2))
                drawLine(x2, (int(i/cols) * Font.cellHeight) + 1, x2, (int(i/cols + 1) * Font.cellHeight) - 1)



class BRFNT:
    """
    Class that represents a BRFNT file.
    """
    encoding = None

    def __init__(self, data=None):
        if data is not None:
            self._initFromData(data)


    def _initFromData(self, tmpf):
        """
        Load BRFNT data
        """

        RFNT = struct.unpack_from('>IHHIHH', tmpf[0:16])
        FINF = struct.unpack_from('>IIBbHbBbBIIIBBBB', tmpf[16:48])
        TGLP = struct.unpack_from('>IIBBbBIHHHHHHI', tmpf[48:96])
        CWDH = struct.unpack_from('>3Ixxxx', tmpf, FINF[10] - 8)
        CWDH2 = []
        CMAP = []


        position = FINF[10] + 8
        for i in range(CWDH[2]+1):
            Entry = struct.unpack_from('>bBb', tmpf, position)
            position += 3
            CWDH2.append((Entry[0], Entry[1], Entry[2]))

        position = FINF[11]
        while position != 0:
            Entry = struct.unpack_from('>HHHxxIH', tmpf, position) # 0: start range -- 1: end range -- 2: type -- 3: position -- 4: CharCode List
            if Entry[2] == 0:
                index = Entry[4]
                for glyph in range(Entry[0], Entry[1] + 1):
                    CMAP.append((index, glyph))
                    index += 1

            elif Entry[2] == 1:
                indexdat = tmpf[(position+12) : (position+12+((Entry[1]-Entry[0]+1)*2))]
                entries = struct.unpack('>' + str(int(len(indexdat)/2)) + 'H', indexdat)
                for i, glyph in enumerate(range(Entry[0], Entry[1]+1)):
                    index = entries[i]
                    if index == 0xFFFF:
                        pass
                    else:
                        CMAP.append((index, glyph))

            elif Entry[2] == 2:
                entries = struct.unpack_from('>' + str(Entry[4]*2) + 'H', tmpf, position+0xE)
                for i in range(Entry[4]):
                    CMAP.append((entries[i * 2 + 1], entries[i * 2]))

            else:
                raise ValueError('Unknown CMAP type!')
                break

            position = Entry[3]


        self.rfntVersionMajor = RFNT[1]      # Major Font Version (0xFFFE)
        self.rfntVersionMinor = RFNT[2]      # Minor Font Version (0x0104)

        self.fonttype = FINF[2]                 #
        self.leading = FINF[3] + 1              # http://en.wikipedia.org/wiki/Leading
        self.defaultchar = FINF[4]              # Default char for exceptions
        self.leftmargin = FINF[5]               #
        self.charwidth = FINF[6] + 1            #
        self.fullwidth = FINF[7] + 1            #
        self.encoding = {
            0: 'UTF-8',
            1: 'UTF-16BE',
            2: 'SJIS',
            3: 'windows-1252',
            4: 'hex', # COUNT
        }.get(FINF[8], 'UTF-8')
        self.height = FINF[12] + 1              #
        self.width = FINF[13] + 1               #
        self.ascent = FINF[14]                  #
        self.descent = FINF[15]                 #

        self.cellWidth = TGLP[2] + 1            # Font Width (0 base)
        self.cellHeight = TGLP[3] + 1           # Font Height (0 base)
        self.baseLine = TGLP[4] + 1             # Position of baseline from top (0 base)
        self.maxCharWidth = TGLP[5] + 1         # Maximum width of a single character (0 base)
        self.textureSize = TGLP[6]              # Length of texture in bytes
        self.numTexs = TGLP[7]                  # Number of textures in the TGLP
        self.texFormat = TGLP[8]                # TPL format
        self.charsPerColumn = TGLP[9]           # Number of characters per column
        self.charsPerRow = TGLP[10]             # Number of characters per row
        self.texWidth = TGLP[11]                # Width of a texture
        self.texHeight = TGLP[12]               # Height of a texture


        TPLDat = tmpf[96:(TGLP[1] + 48)]
        w = self.texWidth
        h = self.texHeight


        SingleTex = []
        Images = []
        length = self.textureSize
        offset = 0
        charsPerTex = self.charsPerColumn * self.charsPerRow

        for tex in range(self.numTexs):
            SingleTex.append(struct.unpack('>' + str(length) + 'B', TPLDat[offset:length+offset]))
            offset += length

        prog = QtWidgets.QProgressDialog(window)
        prog.setRange(0, 100)
        prog.setValue(0)
        prog.setAutoClose(True)
        prog.setWindowTitle('Loading Font')
        strformat = ['I4', 'I8', 'IA4', 'IA8', 'RGB565', 'RGB4A3', 'RGBA8', '', 'CI4', 'CI8', 'CI14x2', '', '', '', 'CMPR'][self.texFormat]
        prog.setLabelText('Loading font (%s format)' % (strformat,))
        prog.open()

        def handlePctUpdated():
            """
            Called when a Decoder object updates its percentage
            """
            newpct = decoder.progress
            totalPct = (SingleTex.index(tex) / len(SingleTex)) + (newpct / len(SingleTex))
            totalPct *= 100
            prog.setValue(totalPct)
            prog.update()

        for tex in SingleTex:

            decoder = TPLLib.decoder(self.texFormat)
            decoder = decoder(tex, w, h, handlePctUpdated)
            newdata = decoder.run()
            dest = QtGui.QImage(newdata, w, h, 4 * w, QtGui.QImage.Format_ARGB32)

            y = 0
            for a in range(self.charsPerRow):
                x = 0
                for b in range(self.charsPerColumn):
                    Images.append(QtGui.QPixmap.fromImage(dest.copy(x, y, self.cellWidth, self.cellHeight)))
                    x += self.cellWidth
                y += self.cellHeight

        prog.setValue(100)




        CMAP.sort(key=lambda x: x[0])

        for i in range(len(CMAP), len(Images)):
            CMAP.append((0xFFFF,0xFFFF))

        for i in range(len(CWDH2), len(Images)):
            CWDH2.append((0xFF,0xFF,0xFF))


        self.glyphs = []
        for i, tex in enumerate(Images):
            val = CMAP[i][1]
            if val == 0xFFFF: continue
            char = struct.pack('>H', val).decode(self.encoding, 'replace')
            g = Glyph(tex, char, CWDH2[i][0], CWDH2[i][1], CWDH2[i][2])
            g.updateToolTip(self.encoding)
            self.glyphs.append(g)


    @classmethod
    def generate(cls, qfont, chars, fgColor, bgColor):
        self = cls()

        self.encoding = 'UTF-16BE'
        self.glyphs = []

        fontMetrics = QtGui.QFontMetrics(qfont)

        for c in chars:
            # make a pixmap
            rect = fontMetrics.boundingRect(c)
            tex = QtGui.QImage(fontMetrics.maxWidth(), fontMetrics.height(), QtGui.QImage.Format_ARGB32)
            tex.fill(bgColor)
            painter = QtGui.QPainter(tex)
            painter.setPen(fgColor)
            painter.setFont(qfont)
            painter.drawText(-fontMetrics.leftBearing(c), fontMetrics.ascent(), c)

            painter.end()

            newtex = QtGui.QPixmap.fromImage(tex)
            self.glyphs.append(Glyph(newtex, c, 0, fontMetrics.width(c), fontMetrics.width(c)))


        self.rfntVersionMajor = 0xFFFE
        self.rfntVersionMinor = 0x0104

        self.fonttype = 1
        self.leading = fontMetrics.height() + fontMetrics.leading() + 1
        self.defaultchar = 0x20 # " "
        self.leftmargin = fontMetrics.minLeftBearing()
        self.charwidth = fontMetrics.maxWidth() + 1
        self.fullwidth = fontMetrics.maxWidth() + 1
        self.height = fontMetrics.height() + 1
        self.width = fontMetrics.maxWidth() + 1
        self.ascent = fontMetrics.ascent()
        self.descent = fontMetrics.descent()

        self.cellWidth = fontMetrics.maxWidth() + 1
        self.cellHeight = fontMetrics.height() + 1
        self.baseLine = fontMetrics.ascent() + 1
        self.maxCharWidth = fontMetrics.maxWidth() + 1
        self.textureSize = 0
        self.numTexs = 5
        self.texFormat = 3
        self.charsPerColumn = 5
        self.charsPerRow = 5
        self.texWidth = 0
        self.texHeight = 0

        return self


    def save(self):
        """
        Save the font and return its data
        """

        # Reconfigure the BRFNT


        # Since editing the brfnt can change the
        # size and number of characters, this
        # function picks new values for texture
        # headers.

        # TGLP
        self.charsPerRow, self.charsPerColumn = 8, 8
        self.numTexs = int(len(self.glyphs) / 64)
        if float(int(len(self.glyphs) / 64)) != len(self.glyphs) / 64:
            self.numTexs = int(len(Font.glyphs) / 64) + 1
        print(len(self.glyphs))
        print(self.numTexs)

        # RFNT
        # print(Font.rfnt.chunkcount)
        # Chunkcount is unrelated to the # of tex's?
        # It's used NOWHERE in the opening algorithm...


        # Skip RFNT until the end

        # Render the glyphs to TPL
        texs = self.RenderGlyphsToTPL()

        # Pack FINF
        # FINFbin = struct.pack('>IIBbHbBbBIIIBBBB', tmpf[16:48])

        # # Pack TGLP
        # TGLPbin = struct.pack('>IIBBbBIHHHHHHI', tmpf[48:96])

        # # Pack CWDH
        # CWDHbin = struct.pack('>3Ixxxx', tmpf, FINF[10] - 8)

        # # Pack CWDH2
        # CWDH2 = []

        # # Pack CMAP
        # CMAP = []

        # Pack RFNT
        RFNTdata = (
            0x52464E54, # b'RFNT'
            self.rfntVersionMajor,
            self.rfntVersionMinor,
            0, # length of entire font - figure out how to put this together later?
            0x10,
            0#self.rfnt.chunkcount,
            )
        RFNTbin = struct.pack('>IHHIHH', *RFNTdata)

        # Put everything together
        finaldata = bytes()

        # Save data
        return finaldata



if __name__ == '__main__':

    path = module_path()
    if path is not None:
        os.chdir(module_path())

    global app, window
    app = QtWidgets.QApplication(sys.argv)

    LoadCharacterNames()

    window = Window()
    window.show()
    sys.exit(app.exec_())
