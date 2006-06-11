#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Process objects.

This module contains the an abstract interface that gets implemented by various
concrete discovery objects themselves.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import os
import optparse
from os.path import *

import curator.data
from curator.utils import letterbox
from curator.imagedata import EXIFImageData


#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
class Process:

    """Base class for process classes."""

    def execute(self, opts, images, metadata, discovery):
        """Base method for discovery.

        @input: options, list of images, metadata
        @output: processed image
        """

        # Noop for now.
        return images, metadata


#-------------------------------------------------------------------------------
#
class ReduceProcess(Process):

    """Rotate, reduce and apply a copyright to the given images, all using the
    PIL (Python Imaging Library)."""

    def add_options(self, parser):

        group = optparse.OptionGroup(
            parser, "Process Options", "Common processing options.")

        group.add_option(
            '-C', '--copyright-text', action='store', metavar='TEXT',
            help="Add specified copyright text.")

        group.add_option(
            '-s', '--browse-size', action='store', type='int', metavar='SIZE',
            default=768,
            help="Size of the largest side of the browseable images.")

        group.add_option(
            '--force-browse', action='store_true',
            help="Force re-generation of the browseable images.")

        parser.add_option_group(group)

    def execute(self, opts, images, metadata, discovery):

        class Visitor(curator.data.Visitor):

            def __init__(self, proc):
                self.proc = proc

            def visit_image(self, image):

                #
                # Set browseable image location
                #
                newfn = discovery.get_location(
                    'browse', image, opts.browse_size)

                self.proc.reduce_browse_image(
                    opts, image, image.fullfn, newfn, opts.browse_size)

        visitor = Visitor(self)
        images.visit(visitor)

        return images, metadata

    def reduce_browse_image(self, opts, image, origfn, newfn, size):

        """Reduce and rotate image to browseable size."""

        import Image

        print '  Reducing...'
        print '  Filename:', newfn

        # Open image, get current size.
        afn = join(opts.root, origfn)
        im = Image.open(afn)

        # Compute letterboxed size.
        let_size = letterbox(im.size, size)

        # Check if we need to rotate the image.  We first look at the
        # EXIF tags, then at the description file rotate field.
        fliph, flipv, nrot = False, False, 0
        if hasattr(image, 'exif'):
            if image.exif.has_key('Image Orientation'):
                exifori = image.exif['Image Orientation'].values[0]
                ##print exifori

                fliph, flipv, nrot = EXIFImageData.flip_rotate[exifori]
                ##print fliph, flipv, nrot
        elif hasattr(image, 'attrfile'):
            rot = image.attrfile.get('rotate', 0)
            if rot != 0:
                fliph, flipv, nrot = \
                       AttrFileImageData.flip_rotate[rot]

        # Compute what should become the final size of the image.
        if nrot % 2 == 1:
            final_size = [0, 0]
            final_size[0], final_size[1] = let_size[1], let_size[0]
        else:
            final_size = let_size
        final_size = tuple(final_size)
        print '  Final size is', final_size

        image.size = final_size

        # check if reduced image already exists.
        try:
            im_dst = Image.open(join(opts.root, newfn))
            print '  Checking sizes:', im_dst.size, final_size
            if im_dst.size == final_size:
                print '  Skipping image.'
                print
                if not opts.force_browse:
                    return
        except IOError:
            pass

        #
        # Image reduction.
        #
        print '  Scaling down from size %s to size %s.' % \
              (im.size, let_size)
        im = im.resize(let_size, Image.ANTIALIAS)


        #
        # Image rotation.
        #
        if fliph:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            print '  Flipping image left-to-right'
        if fliph:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
            print '  Flipping image top-to-bottom'
        if nrot == 3:
            im = im.transpose(Image.ROTATE_90)
            print '  Rotating image 90 degrees'
        elif nrot == 2:
            im = im.transpose(Image.ROTATE_180)
            print '  Rotating image 180 degrees'
        elif nrot == 1:
            im = im.transpose(Image.ROTATE_270)
            print '  Rotating image 270 degrees'
        # Note: we need to invert the angles because of the way
        # the PIL considers them.

        #
        # Apply copyright notice if required.
        #
        if opts.copyright_text:
            import ImageFont, ImageDraw
            font = ImageFont.load_default()

            b = 2
            b2 = 2*b
            trans = 128
            w, h = font.getsize(opts.copyright_text)
            x, y = b, im.size[1]-h-b
            box = (x, y, x+w, y+h)
            boxb = (x-b, y-b, x+w+b, y+h+b)

            maskim = Image.new('RGBA', (w + b2, h + b2), (0,0,0,trans))
            im.paste( (255, 255, 255), boxb, mask=maskim )

            draw = ImageDraw.Draw(im)
            draw.text( (x, y), opts.copyright_text, font=font)

        #
        # Writing out file.
        #
        print '  Writing file.'
        try:
            os.makedirs(join(opts.root, dirname(newfn)))
        except OSError:
            pass
        f = open(join(opts.root, newfn), 'wc')
        im.save(f, 'jpeg')
        f.close()

        print

#-------------------------------------------------------------------------------
#
class ThumbnailProcess(Process):

    """Compute a thumbnail of the given images."""

    def add_options(self, parser):

        group = optparse.OptionGroup(
            parser, "Process Options", "Common processing options.")

        group.add_option(
            '-t', '--thumb-size', action='store', type='int', metavar='SIZE',
            default=160,
            help="Size of the largest side of the thumbnail images.")

        parser.add_option_group(group)

    def execute(self, opts, images, metadata, discovery):

        class Visitor(curator.data.Visitor):

            def visit_image(self, image):

                try:
                    origfn = image.representations['browse']
                except KeyError:
                    origfn = image.fullfn
                    # use original if no reduced image avail.

                #
                # Set browseable image location
                #
                newfn = discovery.get_location(
                    'thumb', image, opts.thumb_size)

                import Image

                print '  Reducing...'
                print '  Filename:', newfn

                # Open image, get current size.
                afn = join(opts.root, origfn)
                im = Image.open(afn)

                # Compute letterboxed size.
                let_size = letterbox(im.size, opts.thumb_size)

                # check if reduced image already exists.
                try:
                    im_dst = Image.open(join(opts.root, newfn))
                    print '  Checking sizes:', im_dst.size, let_size
                    if im_dst.size == let_size:
                        print '  Skipping image.'
                        print
                        return
                except IOError:
                    pass

                #
                # Image reduction.
                #
                print '  Scaling down from size %s to size %s.' % \
                      (im.size, let_size)
                im = im.resize(let_size, Image.ANTIALIAS)

                #
                # Writing out file.
                #
                print '  Writing file.'
                try:
                    os.makedirs(join(opts.root, dirname(newfn)))
                except OSError:
                    pass
                f = open(join(opts.root, newfn), 'wc')
                im.save(f, 'jpeg')
                f.close()

                print

        visitor = Visitor()
        images.visit(visitor)

        return images, metadata
