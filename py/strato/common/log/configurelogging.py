from strato.common.log import config
from strato.common.log import machinereadableformatter
from strato.common.log import coloringformatter
import logging
import logging.config
import os
import sys
import atexit
import json
import subprocess


def logFilename(name):
    return '%s/%s%s' % (config.LOGS_DIRECTORY, name, config.LOGS_SUFFIX)


def configureLogging(name):
    _configureOutputToScreen(logging.getLogger())
    _configureOutputToFile(logging.getLogger(), name)
    _configureLogLevels()
    hostname = subprocess.check_output('/usr/bin/hostname').strip()
    logging.info("Logging started for '%(name)s' on '%(hostname)s'", dict(
        name=name, hostname=hostname))


def addFileHandler(name, path):
    fileHandler = logging.FileHandler(filename=path)
    formatter = logging.Formatter(
        '%(created).03f(%(process)d%(threadName)s):%(levelname)s:%(message)s (%(pathname)s:%(lineno)d)')
    fileHandler.setFormatter(formatter)
    fileHandler.set_name(name)
    fileHandler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(fileHandler)
    logging.info("Logging started for %s" % name)


def _findCaller():
    f = sys._getframe(3)
    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if 'logging/__init__.py' in filename or 'common/log/morelevels.py' in filename:
            f = f.f_back
            continue
        return (filename, f.f_lineno, co.co_name)
    return ("(unknown file)", 0, "(unknown function)")


def _useColorsForScreenOutput():
    if 'STRATO_LOGS_NO_COLORS' in os.environ:
        return False
    if 'STRATO_FORCE_COLORS' in os.environ:
        return True
    if os.system("stty > /dev/null 2>&1") != 0:
        return False
    return True


def _configureOutputToScreen(logger):
    if logger.handlers == []:
        streamHandler = logging.StreamHandler()
        if _useColorsForScreenOutput():
            streamHandler.setFormatter(coloringformatter.ColoringFormatter(
                '%(created).03f(%(process)d%(threadName)s):%(startColor)s%(levelname)s'
                ':%(message)s%(endColor)s (%(pathname)s:%(lineno)d)'))
        else:
            streamHandler.setFormatter(logging.Formatter(
                '%(created).03f(%(process)d%(threadName)s):%(levelname)s:%(message)s '
                '(%(pathname)s:%(lineno)d)'))
        streamHandler.set_name("console")
        streamHandler.setLevel(logging.DEBUG)
        logger.addHandler(streamHandler)


def _configureOutputToFile(logger, logName):
    if not os.path.isdir(config.LOGS_DIRECTORY):
        os.makedirs(config.LOGS_DIRECTORY, mode=0777)
    handler = logging.FileHandler(filename=logFilename(logName))
    atexit.register(handler.close)
    handler.setFormatter(machinereadableformatter.MachineReadableFormatter())
    handler.set_name("file")
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.findCaller = _findCaller


def _configureLogLevels():
    if config.LOG_CONFIGURATION is not None:
        with open(config.LOG_CONFIGURATION, 'rt') as f:
            dictConfig = json.load(f)
    else:
        dictConfig = config.DEFAULT_LOG_CONFIGURATION
    logging.config.dictConfig(dictConfig)