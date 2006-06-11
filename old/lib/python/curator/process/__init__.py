#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Process objects.

This module contains the an abstract interface that gets implemented by various
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

class Process:

    """Base class for process classes."""

    def __init__(self):
        pass

    def process(self, opts, images, metadata):
        """Base method for discovery.

        @input: options, list of images, metadata
        @output: processed image
        """

        # Noop for now.
        return images

## seproot
## subdirs
## samedir    
