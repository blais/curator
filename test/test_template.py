#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""XXX [<options>] <file>

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys
from curator.generation.template import TemplateOutput
import unittest



#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

class Translator:

    def do_title(self, parent):
        """Setting simple text without a parent."""
        parent.text = 'I like this title.'

    def do_other(self, parent):
        """Setting as a node."""

        s = SPAN(P(text='blabla'))
        return s


class TestSequenceFunctions(unittest.TestCase):

    def test_basic(self):
        out = TemplateOutput()
        t = Translator()
        out.output(sys.stdout, t)


#===============================================================================
# MAIN
#===============================================================================

if __name__ == '__main__':
    unittest.main()
