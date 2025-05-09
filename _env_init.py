###############################################################################
# _env_init.py
# Author: Tom Kerr AB3GY
#
# Script to set the runtime environment for custom amateur radio applications.
# Designed for personal use by the author, but freely available to anyone.
###############################################################################

import os
import sys

### LOCAL CUSTOMIZATION ###
# Set these paths to point to the custom amateur radio packages on this computer.
# List them in order of search.
LOCAL_PACKAGE_PATH = '..'  # Root directory of local packages
path_base = os.path.abspath(LOCAL_PACKAGE_PATH)
local_package_paths = [
    path_base,
    os.path.join(path_base, 'ab3gy-pyutils'),
    os.path.join(path_base, 'ab3gy-adif'),
    os.path.join(path_base, 'ab3gy-wsjtx'),
]

n = len(local_package_paths)-1
if (n > 0):
    for i in range(n, -1, -1):
        path = local_package_paths[i]
        if os.path.isdir(path):
            if path not in sys.path:
                sys.path.insert(1, path)
