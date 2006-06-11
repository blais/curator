#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Image and Directory classes.

These classes are used to pass information around.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys, os
import os.path

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
class Image:

    """Class that represents an image, including its thumbnails and all
    alternative represenations as well."""

    def __init__(self, fullfn):

        self.fullfn = fullfn
        self.dir, self.fn = os.path.splitpath(fullfn)

        self.thumb = None
        self.representations = {}
        self.representations['__ORIG__'] = self.fn


#-------------------------------------------------------------------------------
#
class Dir:

    """Class that represents a directory containing images."""


    def __init__(self, dirn):

        self.dirn = dirn
        self.subdirs = {}


#-------------------------------------------------------------------------------
#
class Metadata(dict):

    """Class that represents metadata for images. It is a map with key the image
    filename, mapping to an ElementTree object that can be observed for
    values. It is not necessarily guaranteed to have an entry for each image."""

    pass
