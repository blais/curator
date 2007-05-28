#
# $Source$
# $Id$
#

"""Image and Directory classes.

These classes are used to pass information around.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"


import sys, os
from os.path import *



class Image:

    """Class that represents an image, including its thumbnails and all
    alternative represenations as well."""
    
    def __init__(self, fullfn):

        self.fullfn = fullfn # this is the filename relative to the root dir.
        self.dir, self.fn = split(fullfn)
        self.bn, self.ext = splitext(self.fn)

        self.thumb = None
        self.representations = {}
        self.representations['__ORIG__'] = self.fn



class Dir:

    """Class that represents a directory containing images."""

    def __init__(self, dirn):

        self.dirn = dirn
        self.subdirs = []

        self.images = []

    def dump(self, oss, indent='  '):
        print >> oss, indent, 'D', self.dirn
        indent += '  '
        for img in self.images:
            print >> oss, indent, 'I', img.fullfn
        for dn in self.subdirs:
            dn.dump(oss, indent)

    def visit(self, visitor):

        """Simple visitor interface (inorder), expects visitor with the
        following interface:

            visit_image( self, image )
            visit_dir( self, dir )
        """

        visitor.visit_dir(self)

        for img in self.images:
            visitor.visit_image(img)

        for dir in self.subdirs:
            dir.visit(visitor)



class Visitor:

    def visit_image(self, image):
        pass

    def visit_dir(self, dir):
        pass



class Metadata(dict):

    """Simple generic interface that represents metadata for images. It is a map
    with key the image filename, mapping to an ElementTree object that can be
    observed for values. It is not necessarily guaranteed to have an entry for
    each image."""

    pass

