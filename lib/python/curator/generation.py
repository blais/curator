#!/usr/bin/env python
#
# $Source$
# $Id$
#

"""Generation algorithms.

In particular, the template generation.  This is an output module that does
template replacement.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys, os
import optparse
from os.path import *
import copy

import curator.data

import elementtree
from elementtree.ElementTree import Element, SubElement
import elementtree_helpers

#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
class Generation:

    """Base interface for generation classes."""

    def execute(self, opts, images, metadata, globdata, discovery):
        raise NotImplementedError()


#-------------------------------------------------------------------------------
#
def find_elements_with_attrib(el, attr_name, parent=None):

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
class TemplateGeneration(Generation):

    """Output generation module that uses some simple XHTML file templates to
    customize the HTML output."""

    id = 'r:id'
    
    def add_options(self, parser):

        group = optparse.OptionGroup(
            parser, "Process Options", "Common processing options.")

        group.add_option(
            '-T', '--templates', action='store', metavar='FILENAME',
            default=join(dirname(__file__), 'templates', 'default'),
            help="Directory where templates should be fetched from.")

        parser.add_option_group(group)

    def replace(self, tree, code, css, image, dir, cwd):
        code.cwd = cwd

        code.image = image
        code.dir = dir
        code.css = css
        
        els = find_elements_with_attrib(tree.getroot(), self.id)
        for el, parent in els:
            attr_value = el.attrib[self.id]
            del el.attrib[self.id]
            meth_name = '%s' % attr_value # do_ ? nah, KISS.
            if hasattr(code, meth_name):
                newel = getattr(code, meth_name)(el)
                if newel == False: # False means remove.
                    parent.remove(el)
                    continue
                elif not newel is None:
                    idx = parent.getchildren().index(el)
                    parent[idx] = newel

    #---------------------------------------------------------------------------
    #
    def read_templates(self, opts):
        #
        # Read templates in.
        #

        class Dummy(object): pass

        templates = Dummy()

        def read_template(base):

            # load HTML template.
            tmpl = Dummy()
            try:
                f = open(join(opts.templates, '%s.html' % base), 'r')
                tmpl.tree = elementtree.ElementTree.parse(f)
                tmpl.root = tmpl.tree.getroot()
            except IOError, e:
                raise SystemExit("Error: reading template (%s)" % e)

            # load code template.
            import imp
            try:
                f = open(join(opts.templates, '%s.py' % base), 'r')
                tmpl.code = imp.load_source(
                    base, join(opts.templates, '%s.py' % base), f)
            except IOError, e:
                raise SystemExit("Error: reading template (%s)" % e)

            return tmpl

        templates.index = read_template('index')
        templates.image = read_template('image')
        templates.css = open(join(opts.templates, 'style.css'), 'r').read()

        return templates

    #---------------------------------------------------------------------------
    #
    def execute(self, opts, images, metadata, globdata, discovery):

        templates = self.read_templates(opts)


        #
        # Output global track of images.
        #

        # 1. set prev/next and other fields on each image.
        #    also set HTML filename for global track.
        class SetVisitor(curator.data.Visitor):

            html_fmt = '%s.html'

            def __init__(self, html_root):
                self.prev, self.next = None, None
                self.html_root = html_root

                self.curdir = None

            def visit_image(self, image):
                if self.prev:
                    self.prev.next = image
                image.prev, image.next = self.prev, None
                self.prev = image

                # an image may belong to multiple tracks
                image.html = join(self.html_root, image.dir,
                                  self.html_fmt % image.bn)

                image.dirobj = self.curdir
                # note this assumes dir is visited first

                #print image.dirobj.html, image.html
                
            def visit_dir(self, dir):

                dir.html = join(self.html_root, dir.dirn,
                                self.html_fmt % 'index')
                self.curdir = dir
                #print dir.html

        html_all = join(discovery.root_subdir, 'html', 'all')
        html_all_css = join(html_all, 'style.css')
        visitor = SetVisitor(html_all)
        images.visit(visitor)


        # 2. generate directory indexes
        class GenVisitor(curator.data.Visitor):

            def __init__(self, generation, templates, opts):
                self.generation = generation
                self.templates = templates
                self.opts = opts

            def visit_image(self, image):

                print '  Generating Image', image

                treecopy = copy.deepcopy(self.templates.image.tree)
                self.generation.replace(
                    treecopy, self.templates.image.code, html_all_css,
                    image, image.dirobj, dirname(image.html))

                adn = dirname(join(self.opts.root, image.html))
                if not exists(adn):
                    os.makedirs(adn)
                outf = open(join(self.opts.root, image.html), 'w')
                treecopy.write(outf, encoding='UTF-8')

            def visit_dir(self, dir):
                print '  Generating Index', dir
                # FIXME todo
                
        visitor = GenVisitor(self, templates, opts)
        images.visit(visitor)

        #
        # Output style.css
        #
        adn = join(opts.root, html_all)
        if not exists(adn):
            os.makedirs(adn)
        open(join(opts.root, html_all_css), 'w').write(templates.css)

        return images, metadata

