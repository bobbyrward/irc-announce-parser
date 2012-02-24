import platform
import os


APP_NAME = 'irc_announce_parser'


def get_version():
    return '0.0.1'


def is_windows():
    return platform.system() in ('Windows', 'Microsoft')


def get_config_dir(filename=None):
    base_path = ''

    if is_windows():
        base_path = os.path.join(os.environ.get('APPDATA'), APP_NAME)
    else:
        import xdg.BaseDirectory
        base_path = xdg.BaseDirectory.save_config_path(APP_NAME)

    if filename:
        base_path = os.path.join(base_path, filename)

    return base_path
