#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Discovery that places all generated files under a separate root.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

from curator import discovery

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

class Discovery(discovery.Discovery):

    def discover(self, opts):

        for root, dirs, files in os.walk(opts.root_dir, topdown=True):
            print files

