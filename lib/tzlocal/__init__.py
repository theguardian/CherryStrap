import sys
if sys.platform == 'win32':
    from lib.tzlocal.win32 import get_localzone, reload_localzone
elif 'darwin' in sys.platform:
    from lib.tzlocal.darwin import get_localzone, reload_localzone
else:
    from lib.tzlocal.unix import get_localzone, reload_localzone
