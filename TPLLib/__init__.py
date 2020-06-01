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



# __init__.py
# Sets up TPLLib


################################################################
################################################################


using_cython = True

try:
    import pyximport
    pyximport.install()
    from .backend_cython import *
except ImportError:
    from .backend_python import *
    using_cython = False


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



def decoder(type):
    """
    Returns the appropriate decoding algorithm based on the type specified
    """
    if not isinstance(type, int):
        raise TypeError('Type is not an int')

    if type == I4:
    	return I4Decoder
    elif type == I8:
    	return I8Decoder
    elif type == IA4:
    	return IA4Decoder
    elif type == IA8:
    	return IA8Decoder
    elif type == RGB565:
    	return RGB565Decoder
    elif type == RGB4A3:
    	return RGB4A3Decoder
    elif type == RGBA8:
    	return RGBA8Decoder
    elif type == CI4:
        raise ValueError('CI4 is not supported')
    elif type == CI8:
        raise ValueError('CI8 is not supported')
    elif type == CI14x2:
        raise ValueError('CI14x2 is not supported')
    elif type == CMPR:
        raise ValueError('CMPR is not supported')
    else:
        raise ValueError('Unrecognized type')


def encoder(type):
    """
    Returns the appropriate encoding algorithm based on the type specified
    """
    if not isinstance(type, int):
        raise TypeError('Type is not an int')

    if type == I4:
        return I4Encoder
    elif type == I8:
        return I8Encoder
    elif type == IA4:
        return IA4Encoder
    elif type == IA8:
        return IA8Encoder
    elif type == RGB565:
        return RGB565Encoder
    elif type == RGB4A3:
        return RGB4A3Encoder
    elif type == RGBA8:
        return RGBA8Encoder
    elif type == CI4:
        raise ValueError('CI4 is not supported')
    elif type == CI8:
        raise ValueError('CI8 is not supported')
    elif type == CI14x2:
        raise ValueError('CI14x2 is not supported')
    elif type == CMPR:
        raise ValueError('CMPR is not supported')
    else:
        raise ValueError('Unrecognized type')
