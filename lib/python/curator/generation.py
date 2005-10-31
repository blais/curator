#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""template output module.

This is an output module that does template replacement.

FIXME add docos

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys, os
from os.path import *

import elementtree
from elementtree.ElementTree import Element, SubElement
import elementtree_helpers

#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
def find_elements_with_attrib( el, attr_name, parent=None ):

    """Go thru all the tree and extract all the elements with the given
    attribute."""

    found = []
    if el.attrib.has_key(attr_name):
        found.append( (el, parent) )
    for c in el:
        found.extend( find_elements_with_attrib(c, attr_name, el) )
    return found


#-------------------------------------------------------------------------------
#
class TemplateOutput:

    """Output module that uses XHTML file templates to customize the HTML
    output."""

    id = 'r:id'

    def __init__( self, fn=None ):

        if not fn:
            fn = join(dirname(__file__), 'default-template.html')
        self.fn = fn

        self.read_templates()

    def read_templates( self ):
        try:
            self.tree = elementtree.ElementTree.parse(open(self.fn, 'r'))
            self.root = self.tree.getroot()
        except IOError, e:
            raise SystemExit("Error: reading template (%s)" % e)

    def output( self, f, obj ):
        els = find_elements_with_attrib(self.root, TemplateOutput.id)
        for el, parent in els:
            attr_value = el.attrib[TemplateOutput.id]
            meth_name = 'do_%s' % attr_value
            if hasattr(obj, meth_name):
                newel = getattr(obj, meth_name)(parent)

                if newel == None:
                    parent.remove(el)
                    continue
                else:
                    idx = parent.getchildren().index(el)
                    parent[idx] = newel

        self.tree.write(f, encoding='UTF-8')
