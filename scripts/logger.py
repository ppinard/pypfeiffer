#!/usr/bin/env python
"""
================================================================================
:mod:`logger` -- Logger of vacuum pressure
================================================================================

.. module:: logger
   :synopsis: Logger of vacuum pressure

.. inheritance-diagram:: pypfeiffer.logger

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2013 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import time

# Third party modules.

# Local modules.
from pypfeiffer.interface import PfeifferSingleGaugeInterface

# Globals and constants variables.

with PfeifferSingleGaugeInterface() as p:
    p.pressure_unit = 'pa'

    while True:
        currenttime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        pressure_Pa = p.pressure(1)

        with open('log.csv', 'a') as fp:
            fp.write('%s,%e\n' % (currenttime, pressure_Pa))

        print currenttime, pressure_Pa

        time.sleep(10)
