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



# TPL.py
# Provides classes for decoding and encoding TPL images



from PyQt5 import QtCore


class Decoder(QtCore.QObject):
    """Object that decodes a texture"""
    percentUpdated = QtCore.pyqtSignal(float)

    # Enums
    I4 = 0
    I8 = 1
    IA4 = 2
    IA8 = 3
    RGB565 = 4
    RGB4A3 = 5
    RGBA8 = 6
    CI4 = 8
    CI8 = 9
    CI14x2 = 10
    CMPR = 14
    
    def __init__(self, dest, tex, w, h, type):
        """Initializes the decoder"""
        QtCore.QObject.__init__(self)
        
        self.dest = dest
        self.tex = tex
        self.w = w
        self.h = h
        self.type = type

        # Check for unsupported stuff
        if not isinstance(type, int):
            raise TypeError('Type is not an int')

        if type == self.CI4:
            raise ValueError('CI4 is not supported')
        elif type == self.CI8:
            raise ValueError('CI8 is not supported')
        elif type == self.CI14x2:
            raise ValueError('CI14x2 is not supported')
        elif type == self.CMPR:
            raise ValueError('CMPR is not supported')
        elif type < 0 or type in (7, 11, 12, 13) or type > 14:
            raise ValueError('Unrecognized type')

    def begin(self):
        """Begins the decoding"""
        if self.type == self.I4:
            self.DecodeI4()
        elif self.type == self.I8:
            self.DecodeI8()
        elif self.type == self.IA4:
            self.DecodeIA4()
        elif self.type == self.IA8:
            self.DecodeIA8()
        elif self.type == self.RGB565:
            self.DecodeRGB565()
        elif self.type == self.RGB4A3:
            self.DecodeRGB4A3()
        elif self.type == self.RGBA8:
            self.DecodeRGBA8()


    def DecodeI4(self):
        """Decodes I4 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 8):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 8):
                    for xpixel in range(xtile, xtile + 8, 2):

                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        newpixel = (tex[i] >> 4) * 255 / 15 # upper nybble
                        newpixel = int(newpixel)
                        
                        argb = (newpixel) | (newpixel << 8) | (newpixel << 16) | (0xFF << 24)
                        dest.setPixel(xpixel, ypixel, argb)
                        
                        newpixel = (tex[i] & 0x0F) * 255 / 15 # lower nybble
                        newpixel = int(newpixel)
                        
                        argb = (newpixel) | (newpixel << 8) | (newpixel << 16) | (0xFF << 24)
                        dest.setPixel(xpixel+1, ypixel, argb)
                        
                        i += 1
                        
            newPct = ytile / h
            self.percentUpdated.emit(newPct)
        
    def DecodeI8(self):
        """Decodes I8 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):
                        
                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        newpixel = tex[i]

                        argb = (newpixel) | (newpixel << 8) | (newpixel << 16) | (0xFF << 24)
                        dest.setPixel(xpixel, ypixel, argb)
                        
                        i += 1
                        
            newPct = ytile / h
            self.percentUpdated.emit(newPct)

    def DecodeIA4(self):
        """Decodes IA4 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):
                        
                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        alpha = (tex[i] >> 4) * 255 / 15
                        newpixel = (tex[i] & 0x0F) * 255 / 15
                        alpha, newpixel = int(alpha), int(newpixel)

                        argb = (newpixel) | (newpixel << 8) | (newpixel << 16) | (alpha << 24)
                        dest.setPixel(xpixel, ypixel, argb)

                        i += 1
                        
            newPct = ytile / h
            self.percentUpdated.emit(newPct)
        
    def DecodeIA8(self):
        """Decodes IA8 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        newpixel = tex[i]
                        i += 1
                        
                        alpha = tex[i]
                        i += 1

                        argb = (newpixel) | (newpixel << 8) | (newpixel << 16) | (alpha << 24)
                        dest.setPixel(xpixel, ypixel, argb)

            newPct = ytile / h
            self.percentUpdated.emit(newPct)

    def DecodeRGB565(self):
        """Decodes RGB565 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        
                        blue = (tex[i] & 0x1F) * 255 / 0x1F
                        
                        
                        green1 = (tex[i] >> 5)
                        green2 = (tex[i+1] & 0x7)
                        
                        green = (green1 << 3) | (green2)
                        
                        red = (tex[i+1] >> 3) * 255 / 0x1F

                        red, green, blue - int(red), int(green), int(blue)

                        argb = (blue) | (green << 8) | (red << 16) | (0xFF << 24)
                        dest.setPixel(xpixel, ypixel, argb)

                        i += 2

            newPct = ytile / h
            self.percentUpdated.emit(newPct)
        
    def DecodeRGB4A3(self):
        """Decodes RGB4A3 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h
        
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if(xpixel >= w or ypixel >= h):
                            continue
                        
                        newpixel = (tex[i] << 8) | tex[i+1]
                        newpixel = int(newpixel)
                        

                        if(newpixel >= 0x8000): # Check if it's RGB555
                            red = ((newpixel >> 10) & 0x1F) * 255 / 0x1F
                            green = ((newpixel >> 5) & 0x1F) * 255 / 0x1F
                            blue = (newpixel & 0x1F) * 255 / 0x1F
                            alpha = 0xFF

                        else: # If not, it's RGB4A3
                            alpha = ((newpixel & 0x7000) >> 12) * 255 / 0x7
                            blue = ((newpixel & 0xF00) >> 8) * 255 / 0xF
                            green = ((newpixel & 0xF0) >> 4) * 255 / 0xF
                            red = (newpixel & 0xF) * 255 / 0xF

                        red, green, blue, alpha = int(red), int(green), int(blue), int(alpha)

                        argb = (blue) | (green << 8) | (red << 16) | (alpha << 24)
                        dest.setPixel(xpixel, ypixel, argb)
                        i += 2

            newPct = ytile / h
            self.percentUpdated.emit(newPct)

    def DecodeRGBA8(self):
        """Decodes RGBA8 data"""
        dest, tex, w, h = self.dest, self.tex, self.w, self.h

        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                A = []
                R = []
                G = []
                B = []
                try:
                    for AR in range(16):
                        A.append(tex[i])
                        R.append(tex[i+1])
                        i += 2
                    for GB in range(16):
                        G.append(tex[i])
                        B.append(tex[i+1])
                        i += 2
                except IndexError: continue

                j = 0
                for ypixel in range(ytile, ytile+4):
                    for xpixel in range(xtile, xtile+4):
                        argb = B[j] | (G[j] << 8) | (R[j] << 16) | (A[j] << 24)
                        dest.setPixel(xpixel, ypixel, argb)
                        j += 1

            newPct = ytile / h
            self.percentUpdated.emit(newPct)
        


def Encode(dest, tex, w, h, type):
    """Pass it on!"""

    if type == 0:
        return I4Encode(dest, tex, w, h)
    elif type == 1:
        return I8Encode(dest, tex, w, h)
    elif type == 2:
        return IA4Encode(dest, tex, w, h)
    elif type == 3:
        return IA8Encode(dest, tex, w, h)
    elif type == 4:
        return RGB565Encode(dest, tex, w, h)
    elif type == 5:
        return RGB4A3Encode(dest, tex, w, h)
    elif type == 6:
        return RGBA8Encode(dest, tex, w, h)
    elif type == 8:
        print("CI4 Not supported.")
        return
    elif type == 9:
        print("CI8 Not supported.")
        return
    elif type == 10:
        print("CI14x2 Not supported.")
        return
    elif type == 14:
        print("I love the CMPR format. But not supported.")
        return

