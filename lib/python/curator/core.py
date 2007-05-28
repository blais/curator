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


import sys
import os
import optparse

from curator.utils import parse_config

# Import default components.
from curator.discovery import SepRootDiscovery as Discovery
from curator.imagedata import AttrFileImageData, EXIFImageData
from curator.process import ReduceProcess
from curator.process import ThumbnailProcess
from curator.globaldata import TracksData as GlobalData
from curator.generation import TemplateGeneration as Generation

from pprint import pprint



def add_global_options(parser):

    """Add global options to the given options parser."""

    group = optparse.OptionGroup(
        parser, "Common Options", "Common options for curator pipelines.")

    group.add_option(
        '-c', '--config', action='store',
        help="Specify location of config file.")

    group.add_option(
        '-r', '--root', '--root-dir', action='store',
        default=os.getcwd(),
        help="Root directory to process.")

    parser.add_option_group(group)


class Publisher:

    """Main class that sets up the default processing pipeline for curator.  You
    can customize using the constructor."""

    def __init__(self,
                 discovery=Discovery(),
                 imagedata=[ AttrFileImageData(), EXIFImageData() ],
                 processes=ReduceProcess(),
                 thumbproc=ThumbnailProcess(),
                 globaldata=GlobalData(),
                 generation=Generation()):

        self.discovery = discovery
        self.imagedata = imagedata
        self.processes = processes
        self.thumbproc = thumbproc
        self.globaldata = globaldata
        self.generation = generation

        if not thumbproc:
            raise SystemExit("Error: you must specify some thumbnail processing")
        

    def setup_options_parser(self, parser):

        # add the options common to all setups.
        add_global_options(parser)

        for c in [self.discovery, self.imagedata,
                  self.processes, self.thumbproc,
                  self.globaldata, self.generation]:

            if not type(c) is type([]):
                c = [c]
            for cc in c:
                if cc and hasattr(cc, 'add_options'):
                    cc.add_options(parser)

    def parse_args(self, parser):

        self.setup_options_parser(parser)
        opts, args = parser.parse_args()
        if opts.config:
            parse_config(parser, opts)

        return opts, args

    def run(self, opts):

        def print_phase(s, c='-'):
            print
            ss = 'Phase: %s' % s.__class__.__name__
            print ss
            print c * len(ss)
            print

        #
        # Processing pipeline.  Refer to dataflow diagram for more details.
        #

        # run discovery, passing in the (global and local) options
        # "images" is a tree of Dir and Images.
        print_phase(self.discovery)
        images = self.discovery.execute(opts)

        # fetch image-data associated with each image and directory.
        if type(self.imagedata) is type([]):
            imagedata = self.imagedata
        else:
            imagedata = [self.imagedata]
        metadata = {}
        for idata in imagedata:
            print_phase(idata)
            metadata = idata.execute(opts, images, metadata)

        # run the basic processing on each image.
        if type(self.processes) is type([]):
            processes = self.processes
        else:
            processes = [self.processes]
        for proc in processes:
            print_phase(proc, '~')
            images, metadata = proc.execute(
                opts, images, metadata, self.discovery)

        # run thumbnail processing.
        print_phase(self.thumbproc)
        images, metadata = self.thumbproc.execute(
                opts, images, metadata, self.discovery)

        # get global data.
        print_phase(self.globaldata)
        globdata = self.globaldata.execute(opts)

        # generation phase.
        print_phase(self.generation)
        self.generation.execute(opts, images, metadata, globdata, self.discovery)

