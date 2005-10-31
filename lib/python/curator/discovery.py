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

    def __init__( self ):
        pass

    def discover( self, opts ):
        """Base method for discovery.

        @input: options
        @output: list of images.
        """

## TODO:
## subdirs
## samedir    
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

    def discover( self, opts ):

        for root, dirs, files in os.walk(opts.root_dir, topdown=True):
            print files

