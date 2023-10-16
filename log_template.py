import os
import sys
import inspect
import logging
from logging.handlers import TimedRotatingFileHandler

SYSTEM_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_LEVEL = os.getenv('DEFAULT_LOG_LEVEL', 'INFO').upper()

class CustomFormatter(logging.Formatter):
    format_str = '%(asctime)s - {name} - %(levelname)s - %(message)s'
    FORMATS = {
        logging.DEBUG: format_str,
        logging.INFO: format_str,
        logging.WARNING:  format_str,
        logging.ERROR: format_str,
        logging.CRITICAL: format_str
    }

    def __init__(self, *args, **kwargs):
        self.name_mode = kwargs.pop('namemode', 'file')
        logging.Formatter.__init__(self, *args, **kwargs)

    def _get_name(self, record):
        if self.name_mode == 'leaf':
            name = record.name.split('.')[-1]
        elif self.name_mode == 'full':
            name = record.name
        elif self.name_mode == 'short':
            names = record.name.split('.')
            n = [x[0] for x in names[0:-1]]
            n.append(names[-1])
            name = '.'.join(n)
        else:
            name = record.name
        return name

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)

        name = self._get_name(record)
        log_fmt = log_fmt.format(name=name)

        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class ColorFormatter(CustomFormatter):
    white = "\x1b[97m"
    grey = "\x1b[38m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[1;31m"
    white_on_red = "\x1b[41;97m"
    bold_blue = "\x1b[34;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: bold_blue + CustomFormatter.format_str + reset,
        logging.INFO: white + CustomFormatter.format_str + reset,
        logging.WARNING: yellow + CustomFormatter.format_str + reset,
        logging.ERROR: red + CustomFormatter.format_str + reset,
        logging.CRITICAL: white_on_red + CustomFormatter.format_str + reset
    }

def set_system_log_level(log):
    log.setLevel(SYSTEM_LOG_LEVEL)

def set_default_log_level(log):
    if DEFAULT_LOG_LEVEL in logging.getLevelNamesMapping().keys():
        lvl = logging.getLevelName(DEFAULT_LOG_LEVEL)
        log.setLevel(lvl)
    else:
        set_system_log_level(log)
        log.warning('Unknown log level "%s"' % DEFAULT_LOG_LEVEL)

def set_log_level(log, lvl_str):
    lvl = logging.getLevelName(lvl_str.upper())
    try:
        log.setLevel(lvl)
    except ValueError:
        set_default_log_level(log)
        log.warning('Unknown log level "%s"' % lvl_str.upper())

def get_console_handler(namemode):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(namemode=namemode))
    return handler

def get_file_handler(fname, namemode):
    handler = TimedRotatingFileHandler(fname, when='midnight', backupCount=30)
    handler.suffix = "%Y%m%d"
    handler.setFormatter(ColorFormatter(namemode=namemode))
    return handler

def init_root_logger(root_name, logpath='', namemode='leaf'):
    log = logging.getLogger(root_name)
    log.setLevel(logging.DEBUG)
    log.addHandler(get_console_handler(namemode))
    if logpath:
        log.addHandler(get_file_handler(logpath, namemode))

def get_logger(name, lvl_str='INFO', lvl_env=None, root_logger='', logpath='', namemode='leaf'):
    log = logging.getLogger(name)

    # Init root logger if it has no handlers set yet
    if not log.hasHandlers():
        init_root_logger(root_logger, logpath, namemode)
        log = logging.getLogger(name)

    if lvl_env:
        _lvl_str = os.getenv(lvl_env, DEFAULT_LOG_LEVEL)
    else:
        _lvl_str = lvl_str

    set_log_level(log, _lvl_str)

    return log

def _get_main_module_name(module, prefix):
    package = module.__package__
    if package is None:
        package = ''

    mfname = module.__file__
    if mfname is None:
        return package

    fname = os.path.basename(mfname)
    ext = ".py"
    if fname.endswith(ext):
        fname = fname[:-len(ext)]

    if fname == ("__init__", "__main__"):
        return package

    return os.path.join(prefix, package, fname).replace('/', '.').strip('/.')

def get_module_name(prefix=''): 
    stack = inspect.stack()
    module = inspect.getmodule(stack[1][0])
    if module is None:
        return prefix

    if module.__name__ != "__main__":
        return os.path.join(prefix, module.__name__).replace('/', '.').strip('/.')
    else:
        return _get_main_module_name(module, prefix)
