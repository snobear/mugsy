# must pass version number on command line to setup.py
from distutils.core import setup, Command
from cx_Freeze import setup,Executable
import os

# grab version from environment var
version = os.environ['MUGSY_VER']

# module dependencies to package up
packages = ['watchdog','elasticsearch','yaml','daemon','fcntl']

# other files to include
includefiles = ['pid.py']

setup(
    name = 'mugsy',
    version = version,
    description = 'Mugsy File Monitor.',
    author = 'ashbyj',
    author_email = 'ashbyj@imsweb.com',
    options = {
        'build_exe': {'packages': packages,
                     },
    },
    executables = [Executable('mugsy.py')],
)
