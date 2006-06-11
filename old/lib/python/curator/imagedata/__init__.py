#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""ImageData objects.

This module contains the image data interface that is used to get metadata for
each image.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

class ImageData:

    """Base class for image-data classes."""

    def __init__(self):
        pass

    def getdata(self, opts, images):
        """Base method for discovery.

        @input: options, list of images
        @output: list of images with associated images metadata.
        """

        # Noop.
        metadata = {}
        return metadata
