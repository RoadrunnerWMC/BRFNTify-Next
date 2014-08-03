# TPLLib
#### By Tempus and RoadrunnerWMC
1.0

A Python library for decoding and encoding Nintendo image formats.

The reason for moving this code into a Python extention is that many Python programs duplicate this code already. Programs that use such code include Reggie, BRFNTify, Puzzle, Koopatlas, Koopuzzle and Koopuzzle Tileset Generator. In addition, TPLLib is more powerful than any of the algorithms currently used in these programs. It contains an optional Cython backend for a further speedup.

## Installation Instructions
- Navigate to your Python installation
- Click on "Lib", then "site-packages"
- Make a new folder called "TPLLib"
- Paste all these files in there
- Restart Python, if you have it running already
- Test that it is installed properly by opening a Python shell and typing
`
import TPLLib
`
- If nothing happens, everything's fine. If you see  
`
Traceback (most recent call last):  
  File "<pyshell#0>", line 1, in <module>  
    import TPLLib  
ImportError: No module named 'TPLLib'  
`
  or another error, then you messed up somehow.

## Licensing

Licensed under GPLv3
