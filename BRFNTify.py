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

import contextlib
import functools
import io
import os
import struct
import sys
import traceback
import unicodedata

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

import TPLLib



# Globals
version = 'Beta 1'
Font = None




def module_path():
    """
    This will get us the program's directory, even if we are frozen using cx_Freeze
    """
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None


@contextlib.contextmanager
def blockSignalsFrom(qobject):
    orig = qobject.blockSignals(True)
    try:
        yield
    finally:
        qobject.blockSignals(orig)


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


@functools.lru_cache(1024)
def getCharacterName(c):
    """
    Return the Unicode character name for c (a string of length 1)
    """
    # ASCII control characters don't have officially defined Unicode
    # names (just Unicode aliases), so unicodedata.name() refuses to
    # name them. That's annoying. So we provide names for them manually.
    OVERRIDES = {
        '\x00': 'Null',
        '\x01': 'Start Of Heading',
        '\x02': 'Start Of Text',
        '\x03': 'End Of Text',
        '\x04': 'End Of Transmission',
        '\x05': 'Enquiry',
        '\x06': 'Acknowledge',
        '\x07': 'Bell',
        '\x08': 'Backspace',
        '\x09': 'Character Tabulation',
        '\x0A': 'Line Feed',
        '\x0B': 'Line Tabulation',
        '\x0C': 'Form Feed (FF)',
        '\x0D': 'Carriage Return (CR)',
        '\x0E': 'Shift Out',
        '\x0F': 'Shift In',
        '\x10': 'Data Link Escape',
        '\x11': 'Device Control One',
        '\x12': 'Device Control Two',
        '\x13': 'Device Control Three',
        '\x14': 'Device Control Four',
        '\x15': 'Negative Acknowledge',
        '\x16': 'Synchronous Idle',
        '\x17': 'End Of Transmission Block',
        '\x18': 'Cancel',
        '\x19': 'End Of Medium',
        '\x1A': 'Substitute',
        '\x1B': 'Escape',
        '\x1C': 'Information Separator Four',
        '\x1D': 'Information Separator Three',
        '\x1E': 'Information Separator Two',
        '\x1F': 'Information Separator One',
    }

    name = OVERRIDES.get(c)
    if name is not None:
        return name

    name = unicodedata.name(c, None)
    if name is None:
        return '(Unknown)'
    else:
        return name.title()


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
        self.CreateAction('baseLine', self.HandleBaseline, GetIcon('baseLine'), '&Baseline', 'Show or hide baseLines (the bottom)', 'Ctrl+3')
        self.CreateAction('widths', self.HandleWidths, GetIcon('widths'), '&Widths', 'Show or hide the widths of each character', 'Ctrl+4')
        self.actions['leading'].setCheckable(True)
        self.actions['ascent'].setCheckable(True)
        self.actions['baseLine'].setCheckable(True)
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
        self.viewMenu.addAction(self.actions['baseLine'])
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
        return QtCore.QSize(1280, 512)


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

            self.fontDock.updateFields()
            self.brfntScene.clear()
            self.brfntScene.setSceneRect(
                0,
                0,
                Font.cellWidth * 30,
                Font.cellHeight * (len(Font.glyphs) / 30) + 1)

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
        try:
            return Font.save()

        except Exception as e:
            self.ShowErrorBox('An error occured while trying to save this file. Please refer to the information below for more details.')


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

            chars = dlg.chars.text()

            global Font
            Font = BRFNT.generate(dlg.selectedFont(), chars, dlg.fg, dlg.bg)

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

            self.fontDock.updateFields()
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
    bg = Qt.transparent

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Generate a Font')

        # Font and style group box
        fontGroupBox = QtWidgets.QGroupBox('Font and Style')

        self.fontCombo = QtWidgets.QFontComboBox()
        self.sizeCombo = QtWidgets.QComboBox()
        self.weightValue = QtWidgets.QSpinBox()
        self.italicCheckbox = QtWidgets.QCheckBox('Italic')

        self.findSizes(self.fontCombo.currentFont())

        self.weightValue.setMaximum(99)
        self.weightValue.setValue(50)

        self.fontCombo.currentFontChanged.connect(self.findSizes)

        fontLayout = QtWidgets.QFormLayout(fontGroupBox)
        fontLayout.addRow('Font:', self.fontCombo)
        fontLayout.addRow('Size:', self.sizeCombo)
        fontLayout.addRow('Weight:', self.weightValue)
        fontLayout.addRow('', QtWidgets.QLabel('<small>Default is 50. Bold is 75. <a href="https://doc.qt.io/qt-5/qfont.html#Weight-enum">More information.</a></small>'))
        fontLayout.addRow(self.italicCheckbox)

        # Colors group box
        colorsGroupBox = QtWidgets.QGroupBox('Colors')

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

        fgBtn.clicked.connect(self.fgBtnClick)
        bgBtn.clicked.connect(self.bgBtnClick)

        fgLayout = QtWidgets.QHBoxLayout()
        fgLayout.addWidget(self.fgLabel)
        fgLayout.addWidget(fgBtn)
        bgLayout = QtWidgets.QHBoxLayout()
        bgLayout.addWidget(self.bgLabel)
        bgLayout.addWidget(bgBtn)

        colorsLayout = QtWidgets.QFormLayout(colorsGroupBox)
        colorsLayout.addRow('Foreground:', fgLayout)
        colorsLayout.addRow('Background:', bgLayout)

        # Characters group box
        charsGroupBox = QtWidgets.QGroupBox('Characters')

        self.chars = QtWidgets.QLineEdit()
        self.chars.setText(''.join([chr(x) for x in range(0x20, 0x7F)]))

        charsLayout = QtWidgets.QVBoxLayout(charsGroupBox)
        charsLayout.addWidget(self.chars)

        # Button box and overall layout
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        L = QtWidgets.QGridLayout(self)
        L.addWidget(fontGroupBox, 0, 0)
        L.addWidget(colorsGroupBox, 0, 1)
        L.addWidget(charsGroupBox, 1, 0, 1, 2)
        L.addWidget(buttonBox, 2, 0, 1, 2)


    def findSizes(self, font):
        """
        Add font sizes to self.sizeCombo
        """
        fontDatabase = QtGui.QFontDatabase()
        currentSize = self.sizeCombo.currentText()

        with blockSignalsFrom(self.sizeCombo):
            self.sizeCombo.clear()

            if fontDatabase.isSmoothlyScalable(font.family(), fontDatabase.styleString(font)):
                self.sizeCombo.setEditable(True)

                for size in QtGui.QFontDatabase.standardSizes():
                    self.sizeCombo.addItem(str(size))

            else:
                self.sizeCombo.setEditable(False)

                addedAny = False
                for size in fontDatabase.smoothSizes(font.family(), fontDatabase.styleString(font)):
                    self.sizeCombo.addItem(str(size))
                    addedAny = True

                if not addedAny:
                    for size in QtGui.QFontDatabase.standardSizes():
                        self.sizeCombo.addItem(str(size))

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


    def selectedFont(self):
        """
        Return a QFont representing the font the user selected, with
        appropriate point size and styling options.
        """
        font = self.fontCombo.currentFont()
        font.setPointSize(int(self.sizeCombo.currentText()))
        font.setWeight(self.weightValue.value())
        font.setItalic(self.italicCheckbox.isChecked())
        return font



class Glyph(QtWidgets.QGraphicsItem):
    """
    Class for a character glyph
    """

    def __init__(self, pixmap, char, leftMargin=0, charWidth=0, fullWidth=0):
        super().__init__()

        self.char = char
        self.leftMargin = leftMargin
        self.charWidth = charWidth
        self.fullWidth = fullWidth
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
        while len(b) < 4: b = b'\0' + b
        return struct.unpack_from('>I', b)[0]


    def updateToolTip(self, encoding):
        """
        Update the glyph's tooltip
        """
        if self.char is None:
            name = '<p>Unknown glyph</p>'
        else:
            name = (
                ('<p style="font-size: 24pt;">&#%d;</p>' % ord(self.char))
                + ('<p>Value: 0x%X</p>' % self.value(encoding))
            )

        text = '<p>Character:</p>' + name

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

        # Resize it if needed
        tooWide = pix.width() > self.pixmap.width()
        tooTall = pix.height() > self.pixmap.height()
        if tooWide and tooTall:
            pix = pix.scaled(self.pixmap.width(), self.pixmap.height())
        elif tooWide:
            pix = pix.scaledToWidth(self.pixmap.width())
        elif tooTall:
            pix = pix.scaledToHeight(self.pixmap.height())

        # Set it
        self.pixmap = pix
        self.update()
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
        elif ord(glyph.char) == Font.defaultChar:
            default = glyph
    return default



class FontMetricsDock(QtWidgets.QDockWidget):
    """
    A dock widget that displays font-wide metrics
    """
    typeList = ['0', '1', '2'] # TODO: check exactly what the valid values are
    encodingList = ['UTF-8LE', 'UTF-8BE', 'UTF-16LE', 'UTF-16BE', 'SJIS', 'CP1252', 'COUNT']
    formatList = ['I4', 'I8', 'IA4', 'IA8', 'RGB565', 'RGB4A3', 'RGBA8', 'Unknown', 'CI4', 'CI8', 'CI14x2', 'Unknown', 'Unknown', 'Unknown', 'CMPR/S3TC']
    updating = False

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Font Metrics')

        self.setupGui()


    def setupGui(self):

        self.edits = {
            'fontType': QtWidgets.QComboBox(self),
            'encoding': QtWidgets.QComboBox(self),
            'format': QtWidgets.QComboBox(self),
            'charsPerRow': QtWidgets.QSpinBox(self),
            'charsPerColumn': QtWidgets.QSpinBox(self),
            'defaultChar': QtWidgets.QLineEdit(self),
            'leftMargin': QtWidgets.QSpinBox(self),
            'charWidth': QtWidgets.QSpinBox(self),
            'fullWidth': QtWidgets.QSpinBox(self),
            'leading': QtWidgets.QSpinBox(self),
            'ascent': QtWidgets.QSpinBox(self),
            'descent': QtWidgets.QSpinBox(self),
            'baseLine': QtWidgets.QSpinBox(self),
            'width': QtWidgets.QSpinBox(self),
            'height': QtWidgets.QSpinBox(self),
        }

        self.edits['fontType'].addItems(self.typeList)
        self.edits['encoding'].addItems(self.encodingList)
        self.edits['format'].addItems(self.formatList)
        self.edits['charsPerRow'].setMaximum(0xFFFF)
        self.edits['charsPerColumn'].setMaximum(0xFFFF)
        self.edits['defaultChar'].setMaxLength(1)
        self.edits['defaultChar'].setMaximumWidth(30)
        self.edits['leftMargin'].setRange(-0x80, 0x7F)
        self.edits['charWidth'].setRange(1, 0x100)
        self.edits['fullWidth'].setRange(-0x7F, 0x80)
        self.edits['leading'].setRange(-0x7F, 0x80)
        self.edits['ascent'].setMaximum(0xFF)
        self.edits['descent'].setMaximum(0xFF)
        self.edits['baseLine'].setRange(-0x7F, 0x80)
        self.edits['width'].setRange(1, 0x100)
        self.edits['height'].setRange(1, 0x100)

        for name, e in self.edits.items():
            if isinstance(e, QtWidgets.QComboBox):
                e.currentIndexChanged.connect(lambda: self.boxChanged(name))
            elif isinstance(e, QtWidgets.QSpinBox):
                e.valueChanged.connect(lambda: self.boxChanged(name))
            elif isinstance(e, QtWidgets.QLineEdit):
                e.textChanged.connect(lambda: self.boxChanged(name))

        for e in self.edits.values(): e.setEnabled(False)

        textPropsBox = QtWidgets.QGroupBox('Text Properties')
        textPropsLyt = QtWidgets.QFormLayout(textPropsBox)
        textPropsLyt.addRow('Font Type:', self.edits['fontType'])
        textPropsLyt.addRow('Encoding:', self.edits['encoding'])
        textPropsLyt.addRow('Default Char:', self.edits['defaultChar'])

        texturesBox = QtWidgets.QGroupBox('Textures')
        texturesLyt = QtWidgets.QFormLayout(texturesBox)
        texturesLyt.addRow('Texture Format:', self.edits['format'])
        texturesLyt.addRow('Chars Per Row:', self.edits['charsPerRow'])
        texturesLyt.addRow('Chars Per Column:', self.edits['charsPerColumn'])
        texturesLyt.addRow('Width:', self.edits['width'])
        texturesLyt.addRow('Height:', self.edits['height'])
        # cell width / height

        metricsBox = QtWidgets.QGroupBox('Metrics')
        metricsLyt = QtWidgets.QFormLayout(metricsBox)
        metricsLyt.addRow('Left Margin:', self.edits['leftMargin'])
        metricsLyt.addRow('Char Width:', self.edits['charWidth'])
        metricsLyt.addRow('Full Width:', self.edits['fullWidth'])
        metricsLyt.addRow('Leading:', self.edits['leading'])
        metricsLyt.addRow('Ascent:', self.edits['ascent'])
        metricsLyt.addRow('Descent:', self.edits['descent'])
        metricsLyt.addRow('Baseline:', self.edits['baseLine'])

        baseWidget = QtWidgets.QWidget()
        lyt = QtWidgets.QVBoxLayout(baseWidget)
        lyt.addWidget(textPropsBox)
        lyt.addWidget(texturesBox)
        lyt.addWidget(metricsBox)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(baseWidget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(scrollArea)


    def updateFields(self):

        for e in self.edits.values(): e.setEnabled(True)

        self.updating = True
        self.edits['fontType'].setCurrentIndex(self.typeList.index(str(Font.fontType)))
        self.edits['encoding'].setCurrentIndex(self.encodingList.index(Font.encoding))
        self.edits['format'].setCurrentIndex(Font.texFormat)
        self.edits['charsPerRow'].setValue(Font.charsPerRow)
        self.edits['charsPerColumn'].setValue(Font.charsPerColumn)
        self.edits['defaultChar'].setText(chr(Font.defaultChar))
        self.edits['leftMargin'].setValue(Font.leftMargin)
        self.edits['charWidth'].setValue(Font.charWidth)
        self.edits['fullWidth'].setValue(Font.fullWidth)
        self.edits['leading'].setValue(Font.leading)
        self.edits['ascent'].setValue(Font.ascent)
        self.edits['descent'].setValue(Font.descent)
        self.edits['baseLine'].setValue(Font.baseLine)
        self.edits['width'].setValue(Font.width)
        self.edits['height'].setValue(Font.height)
        self.updating = False


    def boxChanged(self, name):
        """
        A box was changed
        """
        if Font is None or self.updating: return

        w = self.edits[name]
        if isinstance(w, QtWidgets.QComboBox):
            value = w.currentIndex()
        elif isinstance(w, QtWidgets.QSpinBox):
            value = w.value()
        elif isinstance(w, QtWidgets.QLineEdit):
            value = ord(w.text())
        setattr(Font, name, value)

        window.brfntScene.update()
        window.prevDock.updatePreview()



class CharMetricsDock(QtWidgets.QDockWidget):
    """
    A dock widget that displays glyph metrics
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.value = None
        self.leftMargin = 0
        self.charWidth = 0
        self.fullWidth = 0

        glyphFont = QtGui.QFont()
        glyphFont.setPointSize(22)
        glyphNameFont = QtGui.QFont()
        glyphNameFont.setPointSize(int(glyphNameFont.pointSize() * .95))

        self.glyphLabel = QtWidgets.QLabel()
        self.glyphLabel.setFont(glyphFont)
        self.glyphNameLabel = QtWidgets.QLabel()
        self.glyphNameLabel.setFont(glyphNameFont)
        self.glyphNameLabel.setWordWrap(True)
        self.glyphValueEdit = HexSpinBox()
        self.glyphValueEdit.setMaximum(0xFFFF)
        self.glyphValueEdit.valueChanged.connect(self.handleGlyphvalueEditChanged)
        self.glyphValueEdit.setEnabled(False)
        self.leftMarginEdit = QtWidgets.QSpinBox()
        self.leftMarginEdit.setRange(-0x7F, 0x7F)
        self.leftMarginEdit.valueChanged.connect(self.handleLeftmarginEditChanged)
        self.leftMarginEdit.setEnabled(False)
        self.charWidthEdit = QtWidgets.QSpinBox()
        self.charWidthEdit.setMaximum(0xFF)
        self.charWidthEdit.valueChanged.connect(self.handleCharwidthEditChanged)
        self.charWidthEdit.setEnabled(False)
        self.fullWidthEdit = QtWidgets.QSpinBox()
        self.fullWidthEdit.setRange(-0x7F, 0x7F)
        self.fullWidthEdit.valueChanged.connect(self.handleFullwidthEditChanged)
        self.fullWidthEdit.setEnabled(False)
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
        lyt.addRow('Character Value:', self.glyphValueEdit)
        lyt.addRow('Left Margin:', self.leftMarginEdit)
        lyt.addRow('Texture Width:', self.charWidthEdit)
        lyt.addRow('Effective Width:', self.fullWidthEdit)

        w = QtWidgets.QWidget()
        self.setWidget(w)

        L = QtWidgets.QVBoxLayout(w)
        L.addLayout(toplyt)
        L.addLayout(lyt)
        L.addWidget(horzA)
        L.addWidget(self.moveL)
        L.addWidget(self.moveR)
        L.addWidget(horzB)
        L.addWidget(self.delete)
        L.addWidget(horzC)
        L.addWidget(self.copy)
        L.addStretch()

        self.setWindowTitle('Character Metrics')


    def updateGlyph(self):
        """
        Update the info for the currently selected glyph
        """

        try:
            glyphs = window.brfntScene.selectedItems()
        except RuntimeError:
            # must catch this error: if you close the app while something is selected,
            # you get a RuntimeError about the "underlying C++ object being deleted"
            return

        if len(glyphs) != 1:
            self.value = None
            self.glyphLabel.setText('')
            self.glyphNameLabel.setText('')
            self.glyphValueEdit.setValue(0)
            self.leftMarginEdit.setValue(0)
            self.charWidthEdit.setValue(0)
            self.fullWidthEdit.setValue(0)
            self.glyphValueEdit.setEnabled(False)
            self.leftMarginEdit.setEnabled(False)
            self.charWidthEdit.setEnabled(False)
            self.fullWidthEdit.setEnabled(False)
            self.moveL.setEnabled(False)
            self.moveR.setEnabled(False)
            self.delete.setEnabled(False)
            self.copy.setEnabled(False)
        else:
            glyph = glyphs[0]
            self.value = glyph
            self.glyphLabel.setText(glyph.char)
            self.glyphNameLabel.setText(getCharacterName(glyph.char))
            self.glyphValueEdit.setValue(ord(glyph.char))
            self.leftMarginEdit.setValue(glyph.leftMargin)
            self.charWidthEdit.setValue(glyph.charWidth)
            self.fullWidthEdit.setValue(glyph.fullWidth)
            self.glyphValueEdit.setEnabled(True)
            self.leftMarginEdit.setEnabled(True)
            self.charWidthEdit.setEnabled(True)
            self.fullWidthEdit.setEnabled(True)
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
        self.value.updateToolTip(Font.encoding)
        window.prevDock.updatePreview()
        self.glyphLabel.setText(self.value.char)

        self.glyphNameLabel.setText(getCharacterName(self.value.char))

    def handleLeftmarginEditChanged(self):
        """
        Handle changes to the left margin line edit
        """
        if self.value is None: return
        self.value.leftMargin = self.leftMarginEdit.value()
        self.value.update()
        window.prevDock.updatePreview()

    def handleCharwidthEditChanged(self):
        """
        Handle changes to the char width line edit
        """
        if self.value is None: return
        self.value.charWidth = self.charWidthEdit.value()
        self.value.update()
        window.prevDock.updatePreview()

    def handleFullwidthEditChanged(self):
        """
        Handle changes to the full width line edit
        """
        if self.value is None: return
        self.value.fullWidth = self.fullWidthEdit.value()
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
        new = Glyph(c.pixmap, c.char, c.leftMargin, c.charWidth, c.fullWidth)
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

        w = QtWidgets.QWidget()
        self.setWidget(w)

        lyt = QtWidgets.QHBoxLayout(w)
        lyt.addWidget(self.textEdit)
        lyt.addWidget(scrl)
        lyt.setStretchFactor(scrl, 1)
        lyt.setContentsMargins(0,0,0,0)
        lyt.setSpacing(0)

        self.setMinimumHeight(124)

        self.setWindowTitle('T. Preview')


    def updatePreview(self):
        """
        Redraw the preview image
        """
        if Font is None:
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
                w = charOffset + glyph.charWidth
                if w > linewidth: linewidth = w
                charOffset += glyph.fullWidth

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
                # The glyph.pixmap.copy(...) part allows the image to be cropped to glyph.charWidth+1
                paint.drawPixmap(x + glyph.leftMargin, y, glyph.pixmap.copy(0,0, glyph.charWidth+1, glyph.pixmap.height()))
                x += glyph.fullWidth
            i += 1

        # Finish up
        del paint
        self.prevWidget.setPixmap(pix)


class HexSpinBox(QtWidgets.QSpinBox):
    def __init__(self, format='%04X', *args):
        self.format = format

        super().__init__(*args)
        self.setPrefix('0x')
        self.setDisplayIntegerBase(16)

    def textFromValue(self, v):
        return self.format % v


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
                x2 = x1 + fi.charWidth + 2
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

        RFNT = struct.unpack_from('>4sHHIHH', tmpf[0:16])
        FINF = struct.unpack_from('>4sIBbHbBbB3I4B', tmpf[16:48])
        TGLP = struct.unpack_from('>4sIBBbBI6HI', tmpf[48:96])
        CWDH = struct.unpack_from('>4sII4x', tmpf, FINF[10] - 8)
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

        self.fontType = FINF[2]                 #
        self.leading = FINF[3] + 1              # http://en.wikipedia.org/wiki/Leading
        self.defaultChar = FINF[4]              # Default char for exceptions
        self.leftMargin = FINF[5]               #
        self.charWidth = FINF[6] + 1            #
        self.fullWidth = FINF[7] + 1            #
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
        self.baseLine = TGLP[4] + 1             # Position of baseLine from top (0 base)
        self.maxCharWidth = TGLP[5] + 1         # Maximum width of a single character (0 base)
        textureSize = TGLP[6]                   # Length of texture in bytes
        numTexs = TGLP[7]                       # Number of textures in the TGLP
        self.texFormat = TGLP[8]                # TPL format
        self.charsPerRow = TGLP[9]              # Number of characters per column
        self.charsPerColumn = TGLP[10]          # Number of characters per row
        texWidth = TGLP[11]                     # Width of a texture
        texHeight = TGLP[12]                    # Height of a texture


        TPLDat = tmpf[96:(TGLP[1] + 48)]


        SingleTex = []
        Images = []
        offset = 0
        charsPerTex = self.charsPerRow * self.charsPerColumn

        for tex in range(numTexs):
            SingleTex.append(struct.unpack('>' + str(textureSize) + 'B', TPLDat[offset:textureSize+offset]))
            offset += textureSize

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
            prog.setValue(int(totalPct))
            prog.update()

        for tex in SingleTex:

            decoder = TPLLib.decoder(self.texFormat)
            decoder = decoder(tex, texWidth, texHeight, handlePctUpdated)
            newdata = decoder.run()
            dest = QtGui.QImage(newdata, texWidth, texHeight, 4 * texWidth, QtGui.QImage.Format_ARGB32)

            y = 0
            for a in range(self.charsPerColumn):
                x = 0
                for b in range(self.charsPerRow):
                    Images.append(QtGui.QPixmap.fromImage(dest.copy(x, y, self.cellWidth, self.cellHeight)))
                    x += self.cellWidth
                y += self.cellHeight

        prog.setValue(100)


        CMAP.sort(key=lambda x: x[0])

        for i in range(len(CMAP), len(Images)):
            CMAP.append((0xFFFF, 0xFFFF))

        for i in range(len(CWDH2), len(Images)):
            CWDH2.append((0xFF, 0xFF, 0xFF))


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

        self.fontType = 1
        self.leading = fontMetrics.height() + fontMetrics.leading() + 1
        self.defaultChar = 0x20 # " "
        self.leftMargin = fontMetrics.minLeftBearing()
        self.charWidth = fontMetrics.maxWidth() + 1
        self.fullWidth = fontMetrics.maxWidth() + 1
        self.height = fontMetrics.height() + 1
        self.width = fontMetrics.maxWidth() + 1
        self.ascent = fontMetrics.ascent()
        self.descent = fontMetrics.descent()

        self.cellWidth = fontMetrics.maxWidth() + 1
        self.cellHeight = fontMetrics.height() + 1
        self.baseLine = fontMetrics.ascent() + 1
        self.maxCharWidth = fontMetrics.maxWidth() + 1
        self.texFormat = 3
        self.charsPerRow = 5
        self.charsPerColumn = 5

        return self


    def save(self):
        """
        Save the font and return its data
        """

        data = bytearray()

        # Leave space for the RFNT header
        data.extend(b'\0' * 16)
        numChunks = 0

        # Leave space for the FINF header
        data.extend(b'\0' * 32)
        numChunks += 1

        # TGLP

        # Get the smallest power-of-two texture size that will fit
        texWidth = texHeight = 1
        while texWidth < self.cellWidth * self.charsPerRow:
            texWidth <<= 1
        while texHeight < self.cellHeight * self.charsPerColumn:
            texHeight <<= 1

        texImages = []
        currentTexP = None
        x = y = 0
        for g in self.glyphs:
            if currentTexP is None:
                # make new tex
                tex = QtGui.QImage(texWidth, texHeight, QtGui.QImage.Format_ARGB32_Premultiplied)
                tex.fill(QtCore.Qt.transparent)
                currentTexP = QtGui.QPainter(tex)
                texImages.append(tex)

            currentTexP.drawPixmap(x * self.cellWidth, y * self.cellHeight, g.pixmap)

            x += 1
            if x >= self.charsPerRow:
                x = 0
                y += 1

                if y >= self.charsPerColumn:
                    y = 0
                    currentTexP = None

        texDatas = []
        for ti in texImages:
            encoder = TPLLib.encoder(self.texFormat)
            encoder = encoder(ti.bits().asstring(texWidth * texHeight * 4), texWidth, texHeight)
            texDatas.append(encoder.run())


        data.extend(struct.pack('>4sIBBbBI6HI16x',
            b'TGLP',
            sum(len(t) for t in texDatas) + 0x30,
            self.cellWidth - 1,
            self.cellHeight - 1,
            self.baseLine - 1,
            self.maxCharWidth - 1,
            len(texDatas[0]) if texDatas else 0,
            len(texDatas),
            self.texFormat,
            self.charsPerRow,
            self.charsPerColumn,
            texWidth,
            texHeight,
            0x60))
        numChunks += 1
        for t in texDatas:
            data.extend(t)

        # CWDH
        cwdhOffset = len(data)
        # Leave space for the CWDH header
        data.extend(b'\0' * 16)
        numChunks += 1

        for g in self.glyphs:
            data.extend(struct.pack('>bBb', g.leftMargin, g.charWidth, g.fullWidth))
        while len(data) % 4: data.append(0)

        # Fill in the CWDH header
        struct.pack_into('>4sII', data, cwdhOffset,
            b'CWDH',
            len(data) - cwdhOffset,
            len(self.glyphs) - 1)

        # CMAP
        firstCMAPOffset = len(data)
        prevCMAPOffset = None

        for type, firstChar, lastChar, extra in self._createCmapBlocks():

            if prevCMAPOffset is not None:
                struct.pack_into('>I', data, prevCMAPOffset + 16, len(data) + 8)
            prevCMAPOffset = len(data)

            extraData = bytearray()

            if type == 0:
                firstIndex = extra
                extraData.extend(struct.pack('>Hxx', firstIndex))

            elif type == 1:
                indices = extra
                extraData.extend(struct.pack('>' + str(len(indices)) + 'H', *indices))

            else: # type == 2
                entries = extra
                extraData.extend(struct.pack('>H', len(entries)))
                for e in entries:
                    extraData.extend(struct.pack('>HH', e[0], e[1]))

            while len(extraData) % 4: extraData.append(0)
            data.extend(struct.pack('>4sIHHHxxI',
                b'CMAP',
                0x14 + len(extraData),
                firstChar,
                lastChar,
                type,
                0, # filled in at the beginning of the next iteration
                ))
            data.extend(extraData)
            numChunks += 1


        # Fill in the FINF header
        struct.pack_into('>4sIBbHbBbB3I4B', data, 0x10,
            b'FINF',
            0x20,
            self.fontType,
            self.leading - 1,
            self.defaultChar,
            self.leftMargin,
            self.charWidth - 1,
            self.fullWidth - 1,
            {
                'utf-8': 0,
                'utf-16be': 1,
                'sjis': 2,
                'windows-1252': 3,
                'hex': 4,
                }.get(self.encoding.lower(), 0),
            0x38,
            cwdhOffset + 8,
            firstCMAPOffset + 8,
            self.height - 1,
            self.width - 1,
            self.ascent,
            self.descent)

        # Fill in the RFNT header
        struct.pack_into('>4sHHIHH', data, 0,
            b'RFNT',
            self.rfntVersionMajor,
            self.rfntVersionMinor,
            len(data),
            0x10,
            numChunks)

        return data


    def _createCmapBlocks(self):
        """
        Figure out how glyphs should be defined among CMAP blocks, and
        then yield the type value, the first character code, the last
        character code, and an extra value for each one.
        For type 0, the extra value is the first glyph index.
        For type 1, the extra value is a list of glyph indices.
        For type 2, the extra value is a list of (code, index) pairs.
        """

        charCodes = [g.value(self.encoding) for g in self.glyphs]
        yieldedChars = [False] * len(charCodes)

        def findRuns(L, minLen=1):
            """
            Find runs of numbers counting up by 1 in the given list.
            Yield (startIndex, runLength) pairs.
            Only runs at least minLen long will count.
            """
            if not L: return
            runStartI = 0
            lastValue = L[0]
            for i, v in enumerate(L):
                if i == 0: continue
                if v != lastValue + 1:
                    if i - runStartI >= minLen:
                        yield runStartI, i - runStartI
                    runStartI = i
                lastValue = v
            if len(L) - runStartI >= minLen:
                yield runStartI, len(L) - runStartI


        # Type-0 CMAPs (runs of glyphs and indices together)
        for runStart, runLen in findRuns(charCodes, 5):
            firstChar = charCodes[runStart]
            lastChar = charCodes[runStart + runLen - 1]
            yield 0, firstChar, lastChar, runStart

            for i in range(runStart, runStart + runLen):
                yieldedChars[i] = True

        # Type-1 CMAPs (runs of increasing character codes with explicit indices)
        remainingCodes = {}
        for i, c in enumerate(charCodes):
            if yieldedChars[i]: continue
            remainingCodes[c] = i

        sortedRemainingCodes = sorted(remainingCodes)
        for runStart, runLen in findRuns(sortedRemainingCodes, 5):
            firstChar = sortedRemainingCodes[runStart]
            lastChar = sortedRemainingCodes[runStart + runLen - 1]
            indices = []
            for c in range(firstChar, lastChar + 1):
                indices.append(remainingCodes[c])
            yield 1, firstChar, lastChar, indices

            for i in indices:
                yieldedChars[i] = True

        # And put whatever's left into a final type-2 CMAP (explicit mapping)
        entries = []
        for i, c in enumerate(charCodes):
            if yieldedChars[i]: continue
            entries.append((c, i))
        if entries:
            entries.sort(key=lambda e: e[0]) # sort by char code
            yield 2, 0, 0xFFFF, entries




if __name__ == '__main__':

    path = module_path()
    if path is not None:
        os.chdir(module_path())

    global app, window
    app = QtWidgets.QApplication(sys.argv)

    window = Window()
    window.show()
    sys.exit(app.exec_())
