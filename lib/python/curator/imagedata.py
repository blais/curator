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

from os.path import *

from curator.attrfile import AttrFile
import curator.data

import curator.ext.EXIF as EXIF


#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
class ImageData:

    """Base class for image-data classes."""

    def execute(self, opts, images, metadata):
        """Base method for discovery.

        @input: options, list of images, metadata until now
        @output: list of images with associated images metadata.
        """

        # Noop.
        metadata = {}
        return metadata


#-------------------------------------------------------------------------------
#
class AttrFileImageData(ImageData):

    """Backwards-compatibility image data gatherer that uses the same format as
    the old curator."""

    ext = 'desc'

    # translation table from attrfile rotation spec to exif orientation spec.
    attr_fliprot = {}
    attr_fliprot[0] = (False, False, 0)
    attr_fliprot[1] = (False, False, 2)
    attr_fliprot[2] = (False, False, 1)
    attr_fliprot[3] = (False, False, 3)

    def execute(self, opts, images, metadata):

        class Visitor(curator.data.Visitor):

            def __init__(self):
                self.metadata = {}

            def visit_image(self, image):
                afn = join(opts.root, image.fullfn)
                bn, ext = splitext(afn)
                descfn = join(opts.root, '%s.%s' % (bn, AttrFileImageData.ext))
                if exists(descfn):
                    print "  found '%s'" % descfn
                    image.attrfile = AttrFile(descfn)
                    image.attrfile.read() # read file in memory now.
                    self.metadata[afn] = image.attrfile

        visitor = Visitor()
        images.visit(visitor)

        return visitor.metadata


#-------------------------------------------------------------------------------
#
class EXIFImageData(ImageData):

    """EXIF tags data gatherer.  This uses Gene Cash's EXIF.py library."""

    # flip + rotate definitions (flip-H, flip-V, rotate *90 degrees).
    flip_rotate = {}
    flip_rotate[1] = (False, False, 0)
    flip_rotate[2] = (True, False, 0)
    flip_rotate[3] = (True, True, 0) # or (False, False, 2)
    flip_rotate[4] = (False, True, 0)
    flip_rotate[5] = (True, False, 1)
    flip_rotate[6] = (False, False, 1)
    flip_rotate[7] = (False, True, 1)
    flip_rotate[8] = (False, False, 3)
    
    def execute(self, opts, images, metadata):

        class Visitor(curator.data.Visitor):

            def __init__(self):
                self.metadata = {}

            def visit_image(self, image):
                print "  reading exif tags from '%s'" % image.fullfn
                afn = join(opts.root, image.fullfn)
                f = open(afn, 'r')
                image.exif = EXIF.process_file(f)

        visitor = Visitor()
        images.visit(visitor)

        return visitor.metadata

# EXIF Orientation
# The image orientation viewed in terms of rows and columns.
# Tag = 274 (112.H)
# Type = SHORT
# Count = 1 Default = 1
# 
# 0001 = The 0th row is at the visual top of the image,
#        the 0th column is the visual left-hand side.
#  
# 0010 = The 0th row is at the visual top of the image,
#        the 0th column is the visual right-hand side.
#    
# 0011 = The 0th row is at the visual bottom of the image,
#        the 0th column is the visual right-hand side.
#    
# 0100 = The 0th row is at the visual bottom of the image,
#        the 0th column is the visual left-hand side.
#    
# 0101 = The 0th row is the visual left-hand side of the image,
#        the 0th column is the visual top.
#    
# 0110 = The 0th row is the visual right-hand side of the image,
#        the 0th column is the visual top.
#    
# 0111 = The 0th row is the visual right-hand side of the image,
#        the 0th column is the visual bottom.
#    
# 1000 = The 0th row is the visual left-hand side of the image,
#        the 0th column is the visual bottom.
#    
# Other = reserved


#-------------------------------------------------------------------------------
#
class XMLImageData(ImageData):

    """Image data gatherer that loads an associated XML file using ElementTree
    and provides subelements of the top node in the map."""

    pass # FIXME todo









##     exif_orientation_map = {}
##     exif_orientation_map['1'] = None
##     exif_orientation_map['3'] = '2'
##     exif_orientation_map['6'] = '3'
##     exif_orientation_map['8'] = '1'

