#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Various utilities needed by curator.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys, os
from os.path import join
import string

#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
def parse_config( parser, opts ):
    
    """Parse a config using the optparse definition. We add appropriate data
    members to the opts object."""

    pass ## FIXME todo modify opts 


#-------------------------------------------------------------------------------
#
def letterbox( cur_size, new_side ):

    """Letterbox the cur_size square to fit within new_side.  Returns the
    letterboxed size."""

    m = apply(max, cur_size)
    f = float(new_side) / m
    return tuple( [int(x * f) for x in cur_size] )


#-------------------------------------------------------------------------------
#
def splitpath( path ):

    """Splits a path into a list of components.
    This function works around a quirk in string.split()."""

    # FIXME perhaps call os.path.split repetitively would be better.
    s = string.split( path, '/' ) # we work with fwd slash only inside.
    if len( s ) == 1 and s[0] == "":
        s = []
    return s

#-------------------------------------------------------------------------------
#
def rel( fn, curdir ):

    """Returns destination filename relative to curdir."""

    sc = splitpath( curdir )
    sd = splitpath( fn )

    while len( sc ) > 0 and len( sd ) > 0:
        if sc[0] != sd[0]:
            break
        sc = sc[1:]
        sd = sd[1:]

    if len( sc ) == 0 and len( sd ) == 0:
        out = ""
    elif len( sc ) == 0:
        out = apply( join, sd )
    elif len( sd ) == 0:
        out = apply( join, map( lambda x: os.pardir, sc ) )
    else:
        out = apply( join, map( lambda x: os.pardir, sc ) + list( sd ) )

    # make sure the path is suitable for html consumption
    return out

