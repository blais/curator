#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Core routines for curator.

This module contains code that is used to put together the different processing
actions of the dataflow. The creator of a script only has to setup a processing
pipeline with the publisher objects in this module.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import optparse

from curator.utils import parse_config

# Import default components.
from curator.discovery.seproot import Discovery
#from curator.imagedata.xml import ImageData
from curator.imagedata import ImageData
from curator.process.reduce import Process as ReduceProcess
from curator.process.thumb import Process as ThumbProcess
from curator.globaldata.tracks import GlobalData
from curator.generation.template import Generation


#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
def add_global_options(parser):

    """Add global options to the given options parser."""

    group = optparse.OptionGroup(
        parser, "Common Options", "Common options for curator pipelines.")

    group.add_option(
        '-c', '--config', action='store',
        help="Specify location of config file.")

    parser.add_option(
        '-r', '--root', '--root-dir', action='store',
        help="Root directory to process.")


#-------------------------------------------------------------------------------
#
class Publisher:

    """Main class that contains the processing pipeline for curator."""

    def __init__(self,
                 discovery=Discovery(),
                 imagedata=ImageData(),
                 process=ReduceProcess(),
                 thumbproc=ThumbProcess(),
                 globaldata=GlobalData(),
                 generation=Generation()):

        self.discovery = discovery
        self.imagedata = imagedata
        self.process = process
        self.thumbproc = thumbproc
        self.globaldata = globaldata
        self.generation = generation

    def setup_options_parser(self, parser):
        
        add_global_options(parser)
        for c in [self.discovery, self.imagedata,
                  self.process, self.thumbproc,
                  self.globaldata, self.generation]:

            if c and hasattr(c, 'add_options'):
                c.add_options(parser)
        
    def parse_options(self, parser):

        setup_options_parser(parser)
        opts, args = parser.parse_args()
        if opts.config:
            parse_config(parser, opts)

        return opts, args

    def run(self):

        pass
