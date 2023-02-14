import os.path

# Everything highly specific to BRFNTify is in this section, to make it
# simpler to copypaste this script across all of the NSMBW-related
# projects that use the same technologies (Reggie, Puzzle, BRFNTify,
# etc)

PROJECT_NAME = 'BRFNTify'
FULL_PROJECT_NAME = 'BRFNTify Font Editor'
PROJECT_VERSION = '1.0'

WIN_ICON = None
MAC_ICON = None
MAC_BUNDLE_IDENTIFIER = 'ca.chronometry.brfntify'

SCRIPT_FILE = 'BRFNTify.py'
DATA_FOLDERS = ['data']
DATA_FILES = ['readme.md', 'license.txt', 'format.txt']
EXTRA_IMPORT_PATHS = []

USE_PYQT = True
USE_NSMBLIB = False

EXCLUDE_HASHLIB = True

# macOS only
AUTO_APP_BUNDLE_NAME = SCRIPT_FILE.split('.')[0] + '.app'
FINAL_APP_BUNDLE_NAME = FULL_PROJECT_NAME + '.app'
