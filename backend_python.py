#!/usr/bin/python
# -*- coding: latin-1 -*-

# TPLLib - A Python library for decoding and encoding Nintendo image formats
# Version 0.1
# Copyright (C) 2009-2014 Tempus, RoadrunnerWMC

# This file is part of TPLLib.

# TPLLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# TPLLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with TPLLib.  If not, see <http://www.gnu.org/licenses/>.



# backend_python.py
# Image encoding/decoding classes using pure-Python as a backend


################################################################
################################################################



class Decoder():
    """
    Object that decodes a texture
    """
    def __init__(self, tex, width, height, updater=None, updateInterval=0.1):
        """
        Initializes the decoder
        """
        self.tex = tex
        self.size = [width, height]
        self.updater = updater
        self.updateInterval = updateInterval
        self.progress = 0
        self.result = None

    def run(self):
        """
        Runs the algorithm
        """
        raise NotImplementedError('You cannot run an abstract decoder')


class Encoder():
    """
    Object that encodes a texture
    """
    def __init__(self, argb, width, height, updater=None, updateInterval=0.1):
        """
        Initializes the encoder
        """
        self.argb = argb
        self.size = [width, height]
        self.updater = updater
        self.updateInterval = updateInterval
        self.progress = 0
        self.result = None

    def run(self):
        """
        Runs the algorithm
        """
        raise NotImplementedError('You cannot run an abstract encoder')



class I4Decoder(Decoder):
    """
    Decodes an I4 texture
    """
    # Format:
    # IIII
    bytesPerPixel = .5

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]
        
        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 8):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 8):
                    for xpixel in range(xtile, xtile + 8, 2):

                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        newpixel = (tex[i] >> 4) * 255 / 15 # upper nybble
                        newpixel = int(newpixel)
                        
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 0] = 0xFF
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = newpixel
                        
                        newpixel = (tex[i] & 0x0F) * 255 / 15 # lower nybble
                        newpixel = int(newpixel)
                        
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 4] = 0xFF
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 5] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 6] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 7] = newpixel
                        
                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class I4Encoder(Encoder):
    """
    Encodes an I4 texture
    """
    # Format:
    # IIII
    bytesPerPixel = .5

    def run(self):
        """
        Runs the algorithm
        """
        argb, w, h = self.argb, self.size[0], self.size[1]
        
        texBuf = bytearray(int(w * h / 2))
        i = 0
        for ytile in range(0, h, 8):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 8):
                    for xpixel in range(xtile, xtile + 8, 2):

                        if xpixel >= w or ypixel >= h:
                            continue

                        newpixelB = argbBuf[(((ypixel * w) + xpixel) * 4) + 0]
                        newpixelG = argbBuf[(((ypixel * w) + xpixel) * 4) + 1]
                        newpixelR = argbBuf[(((ypixel * w) + xpixel) * 4) + 2]
                        newpixelA = argbBuf[(((ypixel * w) + xpixel) * 4) + 3]
                        newpixel = int((newpixelR + newpixelG + newpixelB) / 3)
                        newpixel = int(newpixel * (newpixelA / 255))

                        texBuf[i] = int(newpixel * 15 / 255) << 4 # upper nybble

                        newpixelB = argbBuf[(((ypixel * w) + xpixel) * 4) + 4]
                        newpixelG = argbBuf[(((ypixel * w) + xpixel) * 4) + 5]
                        newpixelR = argbBuf[(((ypixel * w) + xpixel) * 4) + 6]
                        newpixelA = argbBuf[(((ypixel * w) + xpixel) * 4) + 7]
                        newpixel = int((newpixelR + newpixelG + newpixelB) / 3)
                        newpixel = int(newpixel * (newpixelA / 255))

                        texBuf[i] |= int(newpixel * 15 / 255)
                        
                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(texBuf)
        return self.result


class I8Decoder(Decoder):
    """
    Decodes an I8 texture
    """
    # Format:
    # IIIIIIII
    bytesPerPixel = 1

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]
        
        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):
                        
                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        newpixel = tex[i]

                        argbBuf[(((ypixel * w) + xpixel) * 4) + 0] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = 0xFF
                        
                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class I8Encoder(Encoder):
    """
    Encodes an I8 texture
    """
    # Format:
    # IIIIIIII
    bytesPerPixel = 1

    def run(self):
        """
        Runs the algorithm
        """
        argb, w, h = self.argb, self.size[0], self.size[1]
        
        texBuf = bytearray(w * h)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):

                        if xpixel >= w or ypixel >= h:
                            continue

                        newpixelB = argb[(((ypixel * w) + xpixel) * 4) + 0]
                        newpixelG = argb[(((ypixel * w) + xpixel) * 4) + 1]
                        newpixelR = argb[(((ypixel * w) + xpixel) * 4) + 2]
                        newpixelA = argb[(((ypixel * w) + xpixel) * 4) + 3]
                        newpixel = int((newpixelR + newpixelG + newpixelB) / 3)
                        texBuf[i] = int(newpixel * (newpixelA / 255))

                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(texBuf)
        return self.result


class IA4Decoder(Decoder):
    """
    Decodes an IA4 texture
    """
    # Format:
    # IIIIAAAA
    bytesPerPixel = 1

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]

        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):
                        
                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        alpha = (tex[i] >> 4) * 255 / 15
                        newpixel = (tex[i] & 0x0F) * 255 / 15
                        alpha, newpixel = int(alpha), int(newpixel)

                        argbBuf[((ypixel * w) + xpixel) * 4] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = alpha

                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class IA4Encoder(Encoder):
    """
    Encodes an IA4 texture
    """
    # Format:
    # IIIIAAAA
    bytesPerPixel = 1

    def run(self):
        """
        Runs the algorithm
        """
        argb, w, h = self.argb, self.size[0], self.size[1]
        
        texBuf = bytearray(w * h)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 8):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 8):

                        if xpixel >= w or ypixel >= h:
                            continue

                        newpixelB = argb[(((ypixel * w) + xpixel) * 4) + 0]
                        newpixelG = argb[(((ypixel * w) + xpixel) * 4) + 1]
                        newpixelR = argb[(((ypixel * w) + xpixel) * 4) + 2]
                        newpixelA = argb[(((ypixel * w) + xpixel) * 4) + 3]
                        newpixel = int((newpixelR + newpixelG + newpixelB) / 3)
                        texBuf[i] = int(newpixel / 0xF) | int(newpixelA / 0xF)

                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(texBuf)
        return self.result


class IA8Decoder(Decoder):
    """
    Decodes an IA8 texture
    """
    # Format:
    # IIIIIIII AAAAAAAA
    bytesPerPixel = 2

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]

        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        newpixel = tex[i]
                        i += 1
                        
                        alpha = tex[i]
                        i += 1

                        argbBuf[((ypixel * w) + xpixel) * 4] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = newpixel
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = alpha

            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class IA8Encoder(Encoder):
    """
    Encodes an IA8 texture
    """
    # Format:
    # IIIIIIII AAAAAAAA
    bytesPerPixel = 2

    def run(self):
        """
        Runs the algorithm
        """
        argb, w, h = self.argb, self.size[0], self.size[1]
        
        texBuf = bytearray(w * h * 2)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):

                        if xpixel >= w or ypixel >= h:
                            continue

                        newpixelB = argb[(((ypixel * w) + xpixel) * 4) + 0]
                        newpixelG = argb[(((ypixel * w) + xpixel) * 4) + 1]
                        newpixelR = argb[(((ypixel * w) + xpixel) * 4) + 2]
                        newpixelA = argb[(((ypixel * w) + xpixel) * 4) + 3]
                        newpixel = int((newpixelR + newpixelG + newpixelB) / 3)
                        texBuf[i] = newpixel
                        i += 1
                        texBuf[i] = newpixelA
                        i += 1
                        
            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(texBuf)
        return self.result


class RGB565Decoder(Decoder):
    """
    Decodes an RGB565 texture
    """
    # Format:
    # RRRRRGGG GGGBBBBB
    bytesPerPixel = 2

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]

        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        blue = (tex[i] & 0x1F) * 255 // 0x1F
                        
                        green1 = (tex[i] >> 5)
                        green2 = (tex[i + 1] & 0x7)
                        
                        green = (green1 << 3) | (green2)
                        
                        red = (tex[i + 1] >> 3) * 255 // 0x1F

                        alpha = 0xFF

                        argbBuf[(((ypixel * w) + xpixel) * 4) + 0] = blue
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = green
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = red
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = alpha

                        i += 2

            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class RGB4A3Decoder(Decoder):
    """
    Decodes an RGB4A3 texture
    """
    # Formats:
    # 1BBBBBGG GGGRRRRR
    # 0RRRRGGG GBBBBAAA
    bytesPerPixel = 2

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]

        argbBuf = bytearray(w * h * 4)
        i = 0
        for ytile in range(0, h, 4):
            for xtile in range(0, w, 4):
                for ypixel in range(ytile, ytile + 4):
                    for xpixel in range(xtile, xtile + 4):
                        
                        if xpixel >= w or ypixel >= h:
                            continue
                        
                        newpixel = (tex[i] << 8) | tex[i+1]
                        newpixel = int(newpixel)
                        

                        if newpixel & 0x8000: # RGB555
                            blue = ((newpixel >> 10) & 0x1F) * 255 // 0x1F
                            green = ((newpixel >> 5) & 0x1F) * 255 // 0x1F
                            red = (newpixel & 0x1F) * 255 // 0x1F
                            alpha = 0xFF

                        else: # RGB4A3
                            alpha = ((newpixel & 0x7000) >> 12) * 255 // 0x7
                            blue = ((newpixel & 0xF00) >> 8) * 255 // 0xF
                            green = ((newpixel & 0xF0) >> 4) * 255 // 0xF
                            red = (newpixel & 0xF) * 255 // 0xF

                        argbBuf[(((ypixel * w) + xpixel) * 4) + 0] = red
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = green
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = blue
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = alpha

                        i += 2

            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result


class RGBA8Decoder(Decoder):
    """
    Decodes an RGBA8 texture
    """
    # Format:
    # RRRRRRRR GGGGGGGG BBBBBBBB AAAAAAAA
    bytesPerPixel = 4

    def run(self):
        """
        Runs the algorithm
        """
        tex, w, h = self.tex, self.size[0], self.size[1]

        argbBuf = bytearray(w * h * 4)
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
                        red, green, blue, alpha = R[j], G[j], B[j], A[j]
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 0] = blue
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 1] = green
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 2] = red
                        argbBuf[(((ypixel * w) + xpixel) * 4) + 3] = alpha
                        j += 1

            newProgress = (ytile / h) - self.progress
            if newProgress > self.updateInterval and self.updater:
                self.progress += self.updateInterval
                self.updater()

        self.result = bytes(argbBuf)
        return self.result
