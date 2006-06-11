#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Discovery objects.

This module contains the discovery interface that gets implemented by various
concrete discovery objects themselves.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================


class Discovery:

    """Base class for discovery classes."""

    def __init__(self):
        pass

    def discover(self, opts):
        """Base method for discovery.

        @input: options
        @output: list of images.
        """

## TODO:
## subdirs
## samedir    
