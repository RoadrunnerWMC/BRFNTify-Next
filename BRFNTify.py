#!/usr/bin/python
# -*- coding: latin-1 -*-

# BRFNTify - Editor for Nintendo BRFNT font files
# Version Next Beta 1
# Copyright (C) 2009-2014 Tempus, RoadrunnerWMC

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

import sip, struct, sys, os, traceback, TPL

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt



# Globals
version = 'Beta 1'
FontItems = []
Encoding = None
CharacterNames = {}
comicMode = False # easter egg




def module_path():
    """This will get us the program's directory, even if we are frozen using py2exe"""
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None


def GetIcon(name):
    """Helper function to grab a specific icon"""
    return QtGui.QIcon('data/icon_%s.png' % name)

def createHorzLine():
    """Helper to create a horizontal line widget"""
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Sunken)
    return f

def LoadCharacterNames():
    """Loads CharacterNames"""
    global CharacterNames

    f = open('data/CharNames.txt', 'r')
    d = f.read()
    f.close()
    del f

    for line in d.split('\n'):
        code = int(line.split(' ')[0], 16)
        name = ' '.join(line.split(' ')[1:])[1:-1]
        CharacterNames[code] = name


class Window(QtWidgets.QMainWindow):
    """Main Window"""
    
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, None)
        self.savename = ''
        
        centralWidget = QtWidgets.QWidget()

        self.view = ViewWidget()

        self.brfntScene = QtWidgets.QGraphicsScene()
        self.systemWidget = QtWidgets.QGraphicsScene()

        self.setCentralWidget(self.view)
        self.setWindowTitle('BRFNTify Next')
        ico = QtGui.QIcon()
        ico.addPixmap(QtGui.QPixmap('data/icon_logobig.png'))
        ico.addPixmap(QtGui.QPixmap('data/icon_logosmall.png'))
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
        """Helper function to create the menus"""
        # create the actions
        self.actions = {}
        self.CreateAction('open', self.HandleOpen, GetIcon('open'), '&Open...', 'Open a script file', QtGui.QKeySequence.Open)
        self.CreateAction('save', self.HandleSave, GetIcon('save'), '&Save', 'Save a script file', QtGui.QKeySequence.Save)
        self.CreateAction('saveas', self.HandleSaveAs, GetIcon('saveas'), 'Save &as...', 'Save a copy of the script file', QtGui.QKeySequence.SaveAs)
        self.CreateAction('generate', self.HandleGenerate, None, '&Generate', 'Generate a font table from an installed font', 'Ctrl+G')
        self.CreateAction('import', self.HandleImport, GetIcon('import'), '&Import', 'Import a txt to the current displayed script', 'Ctrl+I')
        # Dock show/hide actions are created later
        self.CreateAction('leading', self.HandleLeading, GetIcon('leading'), '&Leading', 'Show or hide leading lines (the height of each line of text)', 'Ctrl+1')
        self.CreateAction('ascent', self.HandleAscent, GetIcon('ascent'), '&Ascent', 'Show or hide ascent lines (the height of capital letters)', 'Ctrl+2')
        self.CreateAction('baseline', self.HandleBaseline, GetIcon('baseline'), '&Baseline', 'Show or hide baselines (the bottom)', 'Ctrl+3')
        self.CreateAction('widths', self.HandleWidths, GetIcon('widths'), '&Widths', 'Show or hide the widths of each character', 'Ctrl+4')
        self.actions['leading'].setCheckable(True)
        self.actions['ascent'].setCheckable(True)
        self.actions['baseline'].setCheckable(True)
        self.actions['widths'].setCheckable(True)
        self.CreateAction('about', self.HandleAbout, None, '&About', 'About BRFNTify Next', 'Ctrl+H')

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
        self.fileMenu.addAction(self.actions['import'])
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
        """Helper function to create an action"""
        
        if icon != None:
            act = QtWidgets.QAction(icon, text, self)
        else:
            act = QtWidgets.QAction(text, self)
        
        if shortcut != None: act.setShortcut(shortcut)
        if statustext != None: act.setStatusTip(statustext)
        if toggle:
            act.setCheckable(True)
        act.triggered.connect(function)
        
        self.actions[shortname] = act


    def sizeHint(self):
        """size hint"""
        return QtCore.QSize(786, 512)


    def HandleOpen(self):
        """Open a Binary Revolution Font (.brfnt) file for Editing"""

        # File Dialog        
        fn = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a Font', '', 'Binary Revolution Font (*.brfnt)')[0]
        if fn == '': return
        fn = str(fn)
        i = 0

        # Put the whole thing in a try-except clause
        try:

            with open(fn,'rb') as f:
                tmpf = f.read()
            f.close()
            
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
                    for glyph in range(Entry[0], Entry[1]+1):
                        CMAP.append((index, glyph))
                        index += 1
                
                elif Entry[2] == 1:
                    indexdat = tmpf[(position+12):(position+12+((Entry[1]-Entry[0]+1)*2))]
                    entries = struct.unpack('>' + str(int(len(indexdat)/2)) + 'H', indexdat)
                    i = 0
                    for glyph in range(Entry[0], Entry[1]+1):
                        index = entries[i]
                        if index == 0xFFFF:
                            pass
                        else:
                            CMAP.append((index, glyph))
                            
                        i += 1
                
                elif Entry[2] == 2:
                    entries = struct.unpack_from('>' + str(Entry[4]*2) + 'H', tmpf, position+0xE)
                    i = 0
                    for p in range(Entry[4]):
                        CMAP.append((entries[i+1],entries[i]))
                        i += 2
                                
                else:
                    raise ValueError('Unknown CMAP type!')
                    break
                
                position = Entry[3]
            

            self.rfnt = brfntHeader(RFNT[1], RFNT[2], RFNT[5])
            self.finf = FontInformation(FINF[2], FINF[3], FINF[4], FINF[5], FINF[6], FINF[7], FINF[8], FINF[12], FINF[13], FINF[14], FINF[15])
            self.tglp = TextureInformation(TGLP[2], TGLP[3], TGLP[4], TGLP[5], TGLP[6], TGLP[7], TGLP[8], TGLP[9], TGLP[10], TGLP[11], TGLP[12])
            
            global Encoding
            if self.finf.encoding == 1:
                Encoding = "UTF-16BE"
            elif self.finf.encoding == 2:
                Encoding = "SJIS"
            elif self.finf.encoding == 3:
                Encoding = "windows-1252"
            elif self.finf.encoding == 4:
                Encoding = "hex"
            else:
                Encoding = "UTF-8"
            
            
            TPLDat = tmpf[96:(TGLP[1] + 48)]
            w = self.tglp.width
            h = self.tglp.height


            self.fontDock.updateFields(self)

            SingleTex = []
            Images = []
            length = self.tglp.textureSize
            offset = 0
            charsPerTex = self.tglp.column * self.tglp.row
            
            for tex in range(self.tglp.amount):
                SingleTex.append(struct.unpack(">" + str(length) + "B", TPLDat[offset:length+offset]))
                offset += length

            prog = QtWidgets.QProgressDialog(self)
            prog.setRange(0, 100)
            prog.setValue(0)
            prog.setAutoClose(True)
            prog.setWindowTitle('Loading Font')
            file = fn.replace('\\', '/').split('/')[-1]
            strformat = ('I4', 'I8', 'IA4', 'IA8', 'RGB565', 'RGB4A3', 'RGBA8', '', 'CI4', 'CI8', 'CI14x2', '', '', '', 'CMPR')[self.tglp.type]
            prog.setLabelText('Loading %s (%s format)' % (file, strformat))
            prog.open()

            def handlePctUpdated(newpct):
                """Called when a Decoder object updates its percentage"""
                totalPct = (SingleTex.index(tex) / len(SingleTex)) + (newpct / len(SingleTex))
                totalPct *= 100
                prog.setValue(totalPct)
                prog.update()
            
            for tex in SingleTex:
                dest = QtGui.QImage(w,h,QtGui.QImage.Format_ARGB32)
                dest.fill(Qt.black)

                decoder = TPL.Decoder(dest, tex, w, h, self.tglp.type)
                decoder.percentUpdated.connect(handlePctUpdated)
                decoder.begin()
                
                y = 0
                for a in range(self.tglp.row):
                    x = 0
                    for b in range(self.tglp.column):
                        Images.append(QtGui.QPixmap.fromImage(dest.copy(x, y, self.tglp.cellWidth, self.tglp.cellHeight)))
                        x += self.tglp.cellWidth
                    y += self.tglp.cellHeight

            prog.setValue(100)

            self.brfntScene.clear()
            self.brfntScene.setSceneRect(0, 0, self.tglp.cellWidth * 30, self.tglp.cellHeight * (((self.tglp.row * self.tglp.column * self.tglp.amount) / 30) + 1))
                            
            


            CMAP.sort(key=lambda x: x[0])

            for i in range(len(CMAP), len(Images)):
                CMAP.append((0xFFFF,0xFFFF))

            for i in range(len(CWDH2), len(Images)):
                CWDH2.append((0xFF,0xFF,0xFF))
                

            global FontItems
            FontItems = []
            i = 0
            for tex in Images:
                if CMAP[i][1] == 0xFFFF: continue
                FontItems.append(Glyph(tex, CMAP[i][1], CWDH2[i][0], CWDH2[i][1], CWDH2[i][2]))
                i += 1
            x = 0
            y = 0
            i = 0
            for item in FontItems:
                if i >= 30:
                    x = 0
                    y = y + item.pixmap.height()
                    i = 0
                    
                item.setPos(x, y)
                self.brfntScene.addItem(item)
                x = x + item.pixmap.width()
                i += 1

            self.view.updateDisplay(self.rfnt, self.finf, self.tglp)
            self.view.setScene(self.brfntScene)
            self.prevDock.updatePreview()
            self.view.columns = 1
            self.view.updateLayout()
                
            self.savename = fn
            self.setWindowTitle('BRFNTify Next - %s' % fn.replace('\\', '/').split('/')[-1])

        except Exception as e:
            toplbl = QtWidgets.QLabel('An error occured while trying to load this file. Please refer to the information below for more details.')

            # This is a ridiculous way to do this, but it works...
            exc_type, exc_value, tb = sys.exc_info()
            class FileLike():
                def __init__(*args, **kwargs):
                    self = args[0]
                    self.s = ''
                def write(self, txt):
                    self.s += txt
            fl = FileLike()
            traceback.print_exception(exc_type, exc_value, tb, file=fl)
            btm = fl.s

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



    def HandleSave(self):
        """Save a level back to the archive"""
        if not self.savename:
            self.HandleSaveAs()
            return
        
        self.Save(self.savename)
   
        
    def HandleSaveAs(self):
        """Pack up the level files using the translations if available"""
        fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', 'Binary Revolution Font (*.brfnt);;All Files(*)')[0]
        if fn == '': return
        fn = str(fn)
        self.Save(fn)
        
        self.savename = fn


    def Save(self, fn):

        # Reconfigure the BRFNT
        reconfigureBrfnt()

        try:

            # Create a bytearray to store the data
            data = bytearray()

            # Make some dummy RFNT data, to fill in later
            for i in range(16):
                data.append(0)

            # Make the FINF data
            f = []
            for x in range(100): f.append(0)
            f[0] = 0x46494E46 # 'FINF'

            #FINF = struct.pack('>IIBbHbBbBIIIBBBB')

            # Make the TGLP data

            # Make the CWDH data

            # Make the real RFNT data
            r = []
            for x in range(6): r.append(0)
            r[0] = 0x52464E54 # 'RFNT'
            r[1] = self.rfnt.versionmajor
            r[2] = self.rfnt.versionminor
            r[3] = len(data)
            r[4] = 0x10
            r[5] = self.rfnt.chunkcount
            RFNT = struct.pack('>IHHIHH', *r)
            for i in range(len(RFNT)):
                data[i] = RFNT[i]


            # Save data
            with open(fn, 'wb') as f:
                f.write(bytes(data))
            f.close()














        except Exception as e:
            toplbl = QtWidgets.QLabel('An error occured while trying to save this file. Please refer to the information below for more details.')

            # This is a ridiculous way to do this, but it works...
            exc_type, exc_value, tb = sys.exc_info()
            class FileLike():
                def __init__(*args, **kwargs):
                    self = args[0]
                    self.s = ''
                def write(self, txt):
                    self.s += txt
            fl = FileLike()
            traceback.print_exception(exc_type, exc_value, tb, file=fl)
            btm = fl.s

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


    def HandleGenerate(self):
        """Generate a font"""
        
        dlg = GenerateDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            # Create a bunch of glyphs, I guess.

            charrange = dlg.charrange.text()
            
            global Encoding, FontItems
            Encoding = 'UTF-16BE'
            FontItems = []
                
                
            newFont = dlg.fontCombo.currentFont()
            newFont.setPointSize(int(dlg.sizeCombo.currentText()))
            if dlg.styleCombo.currentIndex() == 1:
                newFont.setBold(True)
            elif dlg.styleCombo.currentIndex() == 2:
                newFont.setStyle(1)
            elif dlg.styleCombo.currentIndex() == 3:            
                newFont.setStyle(1)
                newFont.setBold(True)

            fontMetrics = QtGui.QFontMetrics(newFont)

            for glyph in charrange:
                # make a pixmap
                rect = fontMetrics.boundingRect(glyph)
                tex = QtGui.QImage(fontMetrics.maxWidth(), fontMetrics.height(), QtGui.QImage.Format_ARGB32)
                tex.fill(dlg.bg)
                painter = QtGui.QPainter(tex)
                painter.setPen(dlg.fg)
                painter.setFont(newFont)
                painter.drawText(0-fontMetrics.leftBearing(glyph), fontMetrics.ascent(), glyph)
                                
                painter.end()
                
                newtex = QtGui.QPixmap.fromImage(tex)
                # append a glyph to FontItems
                FontItems.append(Glyph(newtex, ord(glyph), 0, fontMetrics.width(glyph), fontMetrics.width(glyph)))
               
            
            self.rfnt = brfntHeader(0xFFFE, 0x0104, 0)
            self.finf = FontInformation(1, fontMetrics.height() + fontMetrics.leading(), 0x20, fontMetrics.minLeftBearing(), fontMetrics.maxWidth(), fontMetrics.maxWidth(), Encoding, fontMetrics.height(), fontMetrics.maxWidth(), fontMetrics.ascent(), fontMetrics.descent())
            self.tglp = TextureInformation(fontMetrics.maxWidth(), fontMetrics.height(), fontMetrics.ascent() + 1, fontMetrics.maxWidth(), 0, 5, 3, 5, 5, 0, 0)
               
            x = 0
            y = 0
            i = 0
            self.brfntScene.clear()
            self.brfntScene.setSceneRect(0, 0, 5000, 5000)

            for item in FontItems:
                if i >= 30:
                    x = 0
                    y = y + item.pixmap.height()
                    i = 0
                item.setPos(x, y)
                self.brfntScene.addItem(item)
                x = x + item.pixmap.width()
                i += 1

            self.fontDock.updateFields(self)
            self.view.updateDisplay(self.rfnt, self.finf, self.tglp)
            self.view.setScene(self.brfntScene)
            self.prevDock.updatePreview()
            self.view.columns = 1
            self.view.updateLayout()

            self.setWindowTitle('BRFNTify Next - untitled')
    
        
        
    def HandleImport(self):
        """Import an image"""
         
        # File Dialog        
        fn = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a script file', '', 'Plain Text File (*.txt);;All Files(*)')[0]
        if fn == '': return
        fn = str(fn)

        file = open(fn, 'r')
        data = file.read()
        file.close()
        del file

        print(data)

        


    def HandleLeading(self, toggled):
        """Handles the user toggling Leading"""
        self.view.updateLeading(toggled)

    def HandleAscent(self, toggled):
        """Handles the user toggling Ascent"""
        self.view.updateAscent(toggled)

    def HandleBaseline(self, toggled):
        """Handles the user toggling Baseline"""
        self.view.updateBaseline(toggled)

    def HandleWidths(self, toggled):
        """Handles the user toggling Widths"""
        self.view.updateWidths(toggled)


    def HandleAbout(self):
        """Handles the user clicking About"""
        try: readme = open('readme.md', 'r').read()
        except: readme = 'BRFNTify %s by Tempus, RoadrunnerWMC\n(No readme.md found!)\nLicensed under GPL' % version

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


    zoomLevels = (20.0, 35.0, 50.0, 65.0, 80.0, 90.0, 100.0, 125.0, 150.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0)
    zoomidx = zoomLevels.index(100.0)
    def HandleZoom(self, btn):
        """Handles ANY of the zoom buttons being clicked"""
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
    """Allows the user to generate a glyph table from an installed font"""
    fg = Qt.black
    bg = Qt.white
    def __init__(self):
        """Creates and initialises the dialog"""
        QtWidgets.QDialog.__init__(self)
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
        """Adds font sizes to self.sizeCombo"""
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
        """User clicked the Choose... button for the foreground color"""
        dlg = QtWidgets.QColorDialog(self)
        dlg.setOption(dlg.ShowAlphaChannel, True)
        dlg.setCurrentColor(self.fg)
        dlg.open()
        dlg.finished.connect(lambda state: self.fgBtnClick2(state, dlg))

    def fgBtnClick2(self, state, dlg):
        """Called when the user closes the color dialog"""
        if state != dlg.Accepted: return

        self.fg = dlg.currentColor()

        fg = QtGui.QPixmap(48, 24)
        fg.fill(self.fg)
        self.fgLabel.setPixmap(fg)
        
    def bgBtnClick(self):
        """User clicked the Choose... button for the background color"""
        dlg = QtWidgets.QColorDialog(self)
        dlg.setOption(dlg.ShowAlphaChannel, True)
        dlg.setCurrentColor(self.bg)
        dlg.open()
        dlg.finished.connect(lambda state: self.bgBtnClick2(state, dlg))

    def bgBtnClick2(self, state, dlg):
        """Called when the user closes the color dialog"""
        if state != dlg.Accepted: return

        self.bg = dlg.currentColor()

        bg = QtGui.QPixmap(48, 24)
        bg.fill(self.bg)
        self.bgLabel.setPixmap(bg)


class Glyph(QtWidgets.QGraphicsItem):
    """Class for a character glyph"""
    
    def __init__(self, pixmap, glyph = None, leftmargin = 0, charwidth = 0, fullwidth = 0):
        """Generic constructor for glyphs"""
        QtWidgets.QGraphicsPixmapItem.__init__(self)
        
        self.glyph = glyph
        self.leftmargin = leftmargin
        self.charwidth = charwidth
        self.fullwidth = fullwidth
        self.pixmap = pixmap
        self.boundingRect = QtCore.QRectF(0,0,pixmap.width(),pixmap.height())
        self.selectionRect = QtCore.QRectF(0,0,pixmap.width()-1,pixmap.height()-1)

        buffer = struct.pack('>H', self.glyph)
        self.EncodeChar = (struct.unpack('>2s', buffer))[0].decode(Encoding, 'replace')
        
        if self.glyph != None:
            text = '<p>Character:</p><p><span style=\"font-size: 24pt;\">&#' + \
                    str(ord(self.EncodeChar)) + \
                    ';</span></p><p>Value: 0x' + \
                    '%X' % self.glyph
        else:
            text = '<p>Character: <span style=\"font-size: 24pt;\">Unknown Glyph'
        
        
        self.setToolTip(text)
        self.setFlag(self.ItemIsMovable, False)
        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemIsFocusable, True)
        

    def setGlyph(self, glyph):
        self.glyph = glyph
        
    def setWidths(self, a, b, c):
        self.leftmargin = a
        self.charwidth = b
        self.fullwidth = c
        
    def boundingRect(self):
        """Required for Qt"""
        return self.boundingRect

    def setPixmap(self, pict):
        self.pixmap = pict


    def contextMenuEvent(self, e):
        """Handles right-clicking the glyph"""
        QtWidgets.QGraphicsItem.contextMenuEvent(self, e)

        menu = QtWidgets.QMenu()
        menu.addAction('Import...', self.handleImport)
        menu.addAction('Export...', self.handleExport)
        menu.exec_(e.screenPos())

    def handleExport(self):
        """Handles the pixmap being exported"""

        # Get the name       
        fn = QtWidgets.QFileDialog.getSaveFileName(window, 'Choose a PNG file', '', 'PNG Image File (*.png);;All Files(*)')[0]
        if fn == '': return
        fn = str(fn)

        # Save it
        self.pixmap.save(fn)


    def handleImport(self):
        """Handles a new pixmap being imported"""

        # Get the name       
        fn = QtWidgets.QFileDialog.getOpenFileName(window, 'Choose a PNG file', '', 'PNG Image File (*.png);;All Files(*)')[0]
        if fn == '': return
        fn = str(fn)

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
        """Paints the object"""

        painter.drawPixmap(0, 0, self.pixmap)

        if self.isSelected():
            painter.setPen(QtGui.QPen(Qt.blue, 1, Qt.SolidLine))
            painter.drawRect(self.selectionRect)
            painter.fillRect(self.selectionRect, QtGui.QColor.fromRgb(255,255,255,64))



def FindGlyph(char):
    """Returns a Glyph object for the string character, or None if none exists"""
    default = None
    for glyph in FontItems:
        if glyph.EncodeChar == char:
            return glyph
        elif ord(glyph.EncodeChar) == window.finf.defaultchar:
            default = glyph
    return default

        

class FontMetricsDock(QtWidgets.QDockWidget):
    typeList = ('0', '1', '2') # TODO: check exactly what the valid values are
    encodingList = ('UTF-8LE', 'UTF-8BE', 'UTF-16LE', 'UTF-16BE', 'SJIS', 'CP1252', 'COUNT')
    formatList = ('I4', 'I8', 'IA4', 'IA8', 'RGB4A3', 'RGB565', 'RGBA8', 'Unknown', 'CI4', 'CI8', 'CI14x2', 'Unknown', 'Unknown', 'Unknown', 'CMPR/S3TC')
    parent = None
    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, parent)

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
        self.edits = (self.fonttypeEdit, self.encodingEdit, self.formatEdit, self.defaultcharEdit, self.leftmarginEdit, self.charwidthEdit, self.fullwidthEdit, self.leadingEdit, self.ascentEdit, self.baselineEdit, self.widthEdit, self.heightEdit)

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
        
        self.fonttypeEdit.setCurrentIndex(self.typeList.index(str(parent.finf.fonttype)))
        self.encodingEdit.setCurrentIndex(self.encodingList.index(Encoding))
        self.formatEdit.setCurrentIndex(parent.tglp.type)
        self.defaultcharEdit.setText(chr(parent.finf.defaultchar))
        self.leftmarginEdit.setValue(parent.finf.leftmargin)
        self.charwidthEdit.setValue(parent.finf.charwidth)
        self.fullwidthEdit.setValue(parent.finf.fullwidth)
        self.leadingEdit.setValue(parent.finf.leading)
        self.ascentEdit.setValue(parent.finf.ascent)
        self.baselineEdit.setValue(parent.tglp.baseLine)
        self.widthEdit.setValue(parent.finf.width)
        self.heightEdit.setValue(parent.finf.height)
        self.parent = parent

    def boxChanged(self, type, name):
        """A box was changed"""
        if self.parent == None: return
        if type == 'combo':
            if name == 'fonttype':
                self.parent.finf.fonttype = self.fonttypeEdit.currentText()
            elif name == 'encoding':
                global Encoding
                Encoding = self.encodingEdit.currentText()
            elif name == 'format':
                self.parent.tglp.type = self.formatEdit.currentIndex()
        elif type == 'line':
            if name == 'defaultchar':
                self.parent.finf.defaultchar = ord(self.defaultcharEdit.text())
        elif type == 'spin':
            if name in ('leftmargin', 'charwidth', 'fullwidth', 'leading', 'ascent', 'width', 'height'):
                newval = eval('self.%sEdit.value()' % name)
                setattr(self.parent.finf, name, newval)
            elif name == 'baseline':
                self.parent.tglp.baseLine = self.baselineEdit.value()
                
        window.brfntScene.update()
        window.prevDock.updatePreview()
        



class CharMetricsDock(QtWidgets.QDockWidget):
    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, parent)

        self.glyph = None
        self.leftmargin = 0
        self.charwidth = 0
        self.fullwidth = 0

        glyphFont = QtGui.QFont()
        glyphFont.setPointSize(22)
        glyphNameFont = QtGui.QFont()
        glyphNameFont.setPointSize(glyphNameFont.pointSize()*.95)

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
        """Updates the info for the currently selected character"""
        glyphs = window.brfntScene.selectedItems()
        if len(glyphs) != 1:
            self.glyph = None
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
            self.glyph = glyph
            self.glyphLabel.setText(glyph.EncodeChar)
            self.glyphNameLabel.setText(CharacterNames[ord(glyph.EncodeChar)])
            self.glyphValueEdit.setValue(ord(glyph.EncodeChar))
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
        """Handles changes to the glyph value line edit"""
        if self.glyph == None:
            self.glyphValueEdit.setValue(0)
            return
        self.glyph.EncodeChar = chr(self.glyphValueEdit.value())
        self.glyph.update()
        window.prevDock.updatePreview()
        self.glyphLabel.setText(self.glyph.EncodeChar)

        name = CharacterNames[ord(self.glyph.EncodeChar)]
        self.glyphNameLabel.setText(name)

    def handleLeftmarginEditChanged(self):
        """Handles changes to the left margin line edit"""
        if self.glyph == None:
            self.leftmarginEdit.setValue(0)
            return
        self.glyph.leftmargin = self.leftmarginEdit.value()
        self.glyph.update()
        window.prevDock.updatePreview()

    def handleCharwidthEditChanged(self):
        """Handles changes to the char width line edit"""
        if self.glyph == None:
            self.charwidthEdit.setValue(0)
            return
        self.glyph.charwidth = self.charwidthEdit.value()
        self.glyph.update()
        window.prevDock.updatePreview()

    def handleFullwidthEditChanged(self):
        """Handles changes to the full width line edit"""
        if self.glyph == None:
            self.fullwidthEdit.setValue(0)
            return
        self.glyph.fullwidth = self.fullwidthEdit.value()
        self.glyph.update()
        window.prevDock.updatePreview()

    def handleMove(self, dir):
        """Handles either of the Move buttons being clicked"""
        global FontItems
        current = FontItems.index(self.glyph)
        new = current + 1 if dir == 'R' else current - 1
        FontItems[current], FontItems[new] = FontItems[new], FontItems[current]

        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()

    def handleDelete(self):
        """Handles the Delete button being clicked"""
        global FontItems
        FontItems.remove(self.glyph)
        window.brfntScene.removeItem(self.glyph)

        del self.glyph
        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()

    def handleCopy(self):
        """Handles the Copy button being clicked"""
        global FontItems
        c = self.glyph # c: "current"
        new = Glyph(c.pixmap, c.glyph, c.leftmargin, c.charwidth, c.fullwidth)
        window.brfntScene.addItem(new)
        c.setSelected(False)
        new.setSelected(True)

        FontItems.insert(FontItems.index(c)+1, new)

        window.view.updateLayout(True)
        window.brfntScene.update()
        window.prevDock.updatePreview()



class TextPreviewDock(QtWidgets.QDockWidget):
    """Dock that lets you type in text and see a preview of it"""
    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, parent)

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
        """Redraws the preview image"""
        if Encoding == None:
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
                if glyph == None: continue
                w = charOffset + glyph.charwidth
                if w > linewidth: linewidth = w
                charOffset += glyph.fullwidth
                
            if linewidth > width: width = linewidth

        height = window.finf.height * (txt.count('\n') + 1)

        # Make the pixmap
        pix = QtGui.QPixmap(width+4, height+4)
        pix.fill(QtGui.QColor.fromRgb(0,0,0,0))
        paint = QtGui.QPainter(pix)

        # Draw the chars to the pixmap
        i = 0
        for line in txt.split('\n'):
            y = window.finf.leading * i
            x = 0
            for char in line:
                glyph = FindGlyph(char)
                if glyph == None: continue
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
            QtGui.QValidator.__init__(self)
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
        QtWidgets.QSpinBox.__init__(self, *args)
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

    characterSelected = QtCore.pyqtSignal(str)
    zoom = 100.0
    columns = 0

    def __init__(self, parent=None):
        super(ViewWidget, self).__init__(parent)

        self.Images = []
        self.drawLeading = False
        self.drawAscent = False
        self.drawBaseline = False
        self.drawWidths = False

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(119,136,153)))
        self.setMouseTracking(True)
        self.YScrollBar = QtWidgets.QScrollBar(Qt.Vertical, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)



    def updateDisplay(self, rfnt, finf, tglp):            
        self.rfnt = rfnt
        self.finf = finf
        self.tglp = tglp
        self.update()

    def updateLeading(self, checked):
        if checked:
            self.drawLeading = True
        else:
            self.drawLeading = False
        if self.scene() != None: self.scene().update()

    def updateAscent(self, checked):
        if checked:
            self.drawAscent = True
        else:
            self.drawAscent = False
        if self.scene() != None: self.scene().update()

    def updateBaseline(self, checked):
        if checked:
            self.drawBaseline = True
        else:
            self.drawBaseline = False
        if self.scene() != None: self.scene().update()

    def updateWidths(self, checked):
        if checked:
            self.drawWidths = True
        else:
            self.drawWidths = False
        if self.scene() != None: self.scene().update()


    def resizeEvent(self, e):
        QtWidgets.QGraphicsView.resizeEvent(self, e)
        self.updateLayout()

    def updateLayout(self, force=False):
        if not hasattr(self, 'tglp'): return
        if self.tglp == None: return

        cols = int((1 / (self.zoom / 100)) * self.viewport().width() / self.tglp.cellWidth)
        if cols < 1: cols = 1
        if cols == self.columns and not force: return
    
        self.columns = cols

        for i in range(len(FontItems)):
            itm = FontItems[i]
            x = self.tglp.cellWidth * (i % cols)
            y = self.tglp.cellHeight * int(i / cols)
            itm.setPos(x, y)

        self.scene().setSceneRect(0, 0, self.tglp.cellWidth * cols, self.tglp.cellHeight * (1+int(len(FontItems) / cols)))


    def drawForeground(self, painter, rect):

        # Calculate the # of rows, and round up
        rows = len(FontItems) / self.columns
        if float(int(rows)) == rows: rows = int(rows)
        else: rows = int(rows) + 1
        # Calculate columns
        cols = self.columns


        # Draw stuff
        
        drawLine = painter.drawLine
        
        # Leading
        if self.drawLeading:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255,0,0,255), 2))
            for i in range(rows):
                drawLine(0, (i* self.tglp.cellHeight) + self.finf.leading, self.tglp.cellWidth * cols, (i* self.tglp.cellHeight) + self.finf.leading)

        # Ascent
        if self.drawAscent:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(0,255,0,255), 2))
            for i in range(rows):
                drawLine(0, ((i+1)* self.tglp.cellHeight) - self.finf.ascent, self.tglp.cellWidth * cols, ((i+1)* self.tglp.cellHeight) - self.finf.ascent)

        # Baseline
        if self.drawBaseline:
            painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(0,0,255,255), 2))
            for i in range(rows):
                drawLine(0, (i* self.tglp.cellHeight) + self.tglp.baseLine, self.tglp.cellWidth * cols, (i* self.tglp.cellHeight) + self.tglp.baseLine)

        # Widths
        if self.drawWidths:
            for i in range(len(FontItems)):
                j = int(i%cols)
                x1 = j * self.tglp.cellWidth
                x2 = x1 + FontItems[i].charwidth + 2
                tooWide = x1 + self.tglp.cellWidth < x2

                painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255,255,0,255), 2))
                drawLine(x1, (int(i/cols)* self.tglp.cellHeight)+1, x1, (int(i/cols+1)* self.tglp.cellHeight)-1)
                if tooWide: continue
                painter.setPen(QtGui.QPen(QtGui.QColor.fromRgb(255,255,0,127), 2))
                drawLine(x2, (int(i/cols)* self.tglp.cellHeight)+1, x2, (int(i/cols+1)* self.tglp.cellHeight)-1)




def reconfigureBrfnt():
    """Restructures the file headers and sections and such before saving"""
    # Since editing the brfnt can change the
    # size and number of characters, this
    # function picks new values for texture
    # headers.

    # TGLP
    tglp = window.tglp
    tglp.row, tglp.column = 8, 8
    tglp.amount = int(len(FontItems) / 64)
    if float(int(len(FontItems) / 64)) != len(FontItems) / 64:
        tglp.amount = int(len(FontItems) / 64) + 1
    print(len(FontItems))
    print(tglp.amount)

    # RFNT
    print(window.rfnt.chunkcount)
    # Chunkcount is unrelated to the # of tex's?
    # It's used NOWHERE in the opening algorithm...
        
        


class brfntHeader():
    """Represents the brfnt header"""
    
    def __init__(self, vmajor, vminor, chunkcount):
        """Constructor"""
 
        self.versionmajor = vmajor      # Major Font Version (0xFFFE)
        self.versionminor = vminor      # Minor Font Version (0x0104)
        self.chunkcount = chunkcount    # Number of chunks in the file
        
        
class FontInformation():
    """Represents the finf section"""
    
    def __init__(self, fonttype, leading, defaultchar, leftmargin, charwidth, fullwidth, encoding, height, width, ascent, descent):
        """Constructor"""
        # '>BbHbBbBBBBB'
        # B = unsigned; len 1
        # b =   signed; len 1
        # H = unsigned; len 2
        self.fonttype = fonttype                #
        self.leading = leading +1               # http://en.wikipedia.org/wiki/Leading
        self.defaultchar = defaultchar          # Default char for exceptions
        self.leftmargin = leftmargin            # 
        self.charwidth = charwidth +1           # 
        self.fullwidth = fullwidth +1           # 
        self.encoding = encoding                # In order - UTF-8, UTF-16, SJIS, CP1252, COUNT
        self.height = height +1                 # 
        self.width = width +1                   # 
        self.ascent = ascent                    # 
        self.descent = descent                  # 
        
        
class TextureInformation():
    """Represents the Texture Pallete Group header"""
    
    def __init__(self, cellWidth, cellHeight, baseLine, maxCharWidth, texsize, texNum, texType, column, row, width, height):
        """Constructor"""
        self.cellWidth = cellWidth + 1          # Font Width (0 base)
        self.cellHeight = cellHeight + 1        # Font Height (0 base)
        self.baseLine = baseLine + 1            # Position of baseline from top (0 base)
        self.maxCharWidth = maxCharWidth + 1    # Maximum width of a single character (0 base)
        self.textureSize = texsize              # Length of texture in bytes
        self.amount = texNum                    # Number of textures in the TGLP
        self.type = texType                     # TPL format
        self.column = column                    # Number of characters per column
        self.row = row                          # Number of characters per row
        self.width = width                      # Width of a texture
        self.height = height                    # Height of a texture



if __name__ == '__main__':

    path = module_path()
    if path != None:
        os.chdir(module_path())

    global app, window
    app = QtWidgets.QApplication(sys.argv)
    
    if comicMode:
        currentFont = app.font()
        newFont = QtGui.QFont('Comic Sans MS')
        newFont.setPointSize(currentFont.pointSize())
        app.setFont(newFont)

    LoadCharacterNames()
        
    window = Window()
    window.show()
    sys.exit(app.exec_())
