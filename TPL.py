try:
    raise ImportError('')
    print('a')
    import pyximport
    print('b')
    pyximport.install()
    print('c')
    import TPLcy
    print('d')
except ImportError:
    print('Unable to load TPLcy; falling back to TPLpy')
    import TPLpy as TPLbackend

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
    """Returns the appropriate decoding algorithm based on the type specified"""
    if not isinstance(type, int):
        raise TypeError('Type is not an int')

    if type == I4:
    	return TPLbackend.I4Decoder
    elif type == I8:
    	return TPLbackend.I8Decoder
    elif type == IA4:
    	return TPLbackend.IA4Decoder
    elif type == IA8:
    	return TPLbackend.IA8Decoder
    elif type == RGB565:
    	return TPLbackend.RGB565Decoder
    elif type == RGB4A3:
    	return TPLbackend.RGB4A3Decoder
    elif type == RGBA8:
    	return TPLbackend.RGBA8Decoder
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
    """Returns the appropriate algorithm based on the type specified"""
    if not isinstance(type, int):
        raise TypeError('Type is not an int')

    if type == I4:
        return TPLbackend.I4Encoder
    elif type == I8:
        return TPLbackend.I8Encoder
    elif type == IA4:
        return TPLbackend.IA4Encoder
    elif type == IA8:
        return TPLbackend.IA8Encoder
    elif type == RGB565:
        return TPLbackend.RGB565Encoder
    elif type == RGB4A3:
        return TPLbackend.RGB4A3Encoder
    elif type == RGBA8:
        return TPLbackend.RGBA8Encoder
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
