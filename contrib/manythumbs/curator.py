#!/usr/bin/python
#******************************************************************************\
#* $Source: /u/blais/cvsroot/curator/bin/curator,v $
#* $Id: curator,v 1.34 2003/09/20 21:28:52 blais Exp $
#*
#* Copyright (C) 2001, Martin Blais <blais@iro.umontreal.ca>
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 2 of the License, or
#* (at your option) any later version.
#*
#* This program is distributed in the hope that it will be useful,
#* but WITHOUT ANY WARRANTY; without even the implied warranty of
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#* GNU General Public License for more details.
#*
#* You should have received a copy of the GNU General Public License
#* along with this program; if not, write to the Free Software
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#*
#*****************************************************************************/

"""Generate HTML image gallery pages.

Curator is a powerful script that allows one to generate Web page image
galleries with the intent of displaying photographic images on the Web, or for a
CD-ROM presentation and archiving. It generates static Web pages only - no
special configuration or running scripts are required on the server. The script
supports many file formats, hierarchical directories, thumbnail generation and
update, per-image description file with any attributes, and 'tracks' of images
spanning multiple directories. The templates consist of HTML with embedded
Python. Running this script only requires a recent Python interpreter (version 2
or more) and the ImageMagick tools.

All links it generates are relative links, so that the pages can be moved or
copied to different media. Each image page and directory can be associated any
set of attributes which become available from the template (this way you can
implement descriptions, conversion code, camera settings, and more).

You can find the latest version at http://curator.sourceforge.net


Input
------------------------------

The image files need to be organized in a directory structure.

For each image, the following is required:

 - <image>.<ext>: the main image file to be displayed in the html page, where
   <ext> is an image extension (e.g. jpg, gif, etc.)

The following is optional, and will be used if present:

 - <image>.desc: a per-image description file containing user-provided
   attributes about the photograph.  The format is, e.g.:

      <attribute-name>: <text>
      <text>
      <text>

      <attribute-name>: <text>
      ...

   Each attribute text is ended with a blank line.  You can inclue all the
   attribute fields you want, it is up to the template file to access them or
   not. There are, however, some special predefined attributes:

    - title: A descriptive title for the image (a short one liner).

    - tracks: <trackname1> <trackname2> ...
      specifies the tracks that the image is part of

    - ignore: yes
      specifies that the image should be ignored

 - <image>--<string>.<ext>: alternative representations of the image. Could be
   the original scan plate, or alternative resolutions, or anything else related
   to this image.  The image html page can add links to these alternative
   representations. We assume that we only need to generate an HTML page for the
   main resolution (i.e. smaller resolutions won't have associated web pages)

To configure the generated HTML files, use --save-templates and modify the code
that will appear in the output directory.

The following files can be put in the root:

 - template-image.html: template for image HTML file
 - template-allindex.html: template for global index HTML file
 - template-dirindex.html: template for directory index HTML file
 - template-trackindex.html: template for track index HTML file
 - template-sortindex.html: template for sorted index HTML file

The template is a normal HTML file, the way you like it, except that it contains
certain special tags that get evaluated by the script in a special environment
nwhich contains useful variables and functions.  You can use the following two
tags:

<!--tagcode:
print 'some python code',
for i in images:
    print 'bla'
-->

<!--tag:title-->

The second tag is implemented as 'print <tag contents>,'. You can put
definitions, function calls, whatever you like.  Variable bindings and
definitions will remain between tags.

The templates are looked up in the following order:
 - user-specified path (-templates option)
 - the root of the hierarchy
 - the dir specified in the env var CURATOR_TEMPLATE

If not found, simple fallback templates are used. Remember that under unix,
processing python code with carriage returns will fail the python interpreter
with a Syntax Error.

For a complete description of the environment, look at the code.


Output
------------------------------

Note by default nothing that already exists is overwritten. Use the --no* or
--force* options to disable or force thumbnails, indexes and image pages.
Directories which do not contain images (and whose subdirectories do not contain
images) will be ignored.

For each image:

 - <image>--thumb.<ext>: associated image thumbnail.

 - <image>.html
   (for each image, an associated web page which features it)

Thus you will end up with the following files for each image:

 - <image>.<ext>
 - <image>.desc
 - <image>--<string>.<ext>
 - <image>--<string>.<ext>
 - ...
 - <image>--thumb.<ext>
 - <image>.html

In each subdirectory of the root:

 - dirindex.html: an HTML index of the directory, with thumbnails and
   titles.

In the root:

 - trackindex-<track>.html: for each track, an HTML index of the track, with
   thumbnails and titles.

 - allindex.cidx: a text index of all the pictures, with image filenames and
   titles, each on a single line.

 - allindex.html: an HTML index of all the pictures, with thumbnails and titles,
   and list of tracks.

 - sortindex.html: an HTML index of all the pictures, with some form of sorting
   This output can be used as a global index for sorting images by
   name/date/whatever.  The images in the author's photo gallery are named
   by date so sorting by name is sorting by date, which the default template
   implements.


Usage:
------------------------------
  curator <options> [<root>]

If <root> is not specified, we assume cwd is the root.
"""

# Developer's manual (ahahah):
#
# Rules for filenames:
#
# All filenames are relative to the root. It is up to the template implementor
# to call the rel method to generate relative links. This simplifies
# handling of paths a lot.

__version__ = "$Revision: 1.34 $"
__version_pr__ = '2.0'

THUMBDIR = '.thumbnails'

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

import sys
if int(sys.version[0]) < 2:
    sys.stderr.write( \
        "Error: you need Python version 2 or more to run this friggin' script.")
    sys.exit(1)

from distutils.fancy_getopt \
     import FancyGetopt, OptionDummy, translate_longopt, wrap_text

import os, os.path, dircache
from os.path import join as joinpath, dirname, basename, normpath, splitext
from os.path import isfile, islink, isdir, exists

import re, string
import StringIO
from pprint import pprint, pformat, PrettyPrinter
from urllib import quote as urlquote, unquote as urlunquote

import imghdr
import stat

from traceback import print_exception

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

#===============================================================================
# fcache module
#===============================================================================

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

class Entry:
    def __init__( self, fn, mtime, size, info ):
        self.fn = fn
        self.mtime = mtime
        self.size = size
        self.info = info

class FCache:
    mre = re.compile('^"([^"]*)" (\d+) (\d+): (.*)$')

    def __init__( self, filename ):
        "Initialize the fcache, reading the given file."
        self.cachefn = filename
        self.entries = {}
        if exists(self.cachefn):
            f = open(self.cachefn, 'r')
            lines = f.readlines()
            for line in lines:
                mo = FCache.mre.match(line)
                if mo:
                    (fn, mtime, size, info) = mo.groups()
                    self.entries[fn] = Entry(fn, int(mtime), int(size), info)
            f.close()

    def store( self, fn, info ):
        s = os.stat(fn)
        self.entries[fn] = Entry(fn, s[stat.ST_MTIME], s[stat.ST_SIZE], info)

        # write out cache
        try:
            f = open(self.cachefn, 'w')
            for e in self.entries.values():
                print >> f, '"%s" %d %d: %s' % (e.fn, e.mtime, e.size, e.info)
            f.close()
        except IOError:
            print >> sys.stderr, "Error writing out cache"

    def lookup( self, fn ):
        try:
            e = self.entries[fn]
        except KeyError:
            return None

        s = os.stat(fn)
        if e.mtime != s[stat.ST_MTIME] or e.size != s[stat.ST_SIZE]:
            return None

        return e.info

    def dump( self ):
        print "Cache filename:", self.cachefn
        print
        for e in self.entries.values():
            print "filename:", e.fn
            print "mtime:", e.mtime
            print "size:", e.size
            print "info:", e.info
            print


#===============================================================================
# DIRECTORY NAMES
#===============================================================================

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
def rel( dest, curdir ):

    """Returns dest filename relative to curdir."""

    sc = splitpath( curdir )
    sd = splitpath( dest )

    while len( sc ) > 0 and len( sd ) > 0:
        if sc[0] != sd[0]:
            break
        sc = sc[1:]
        sd = sd[1:]

    if len( sc ) == 0 and len( sd ) == 0:
        out = ""
    elif len( sc ) == 0:
        out = apply( joinpath, sd )
    elif len( sd ) == 0:
        out = apply( joinpath, map( lambda x: os.pardir, sc ) )
    else:
        out = apply( joinpath, map( lambda x: os.pardir, sc ) + list( sd ) )

    # make sure the path is suitable for html consumption
    return out

# #-----------------------------------------------------------------------------
# #
# def html_join(a, *p):
#
#     """Version of os.path.join() that uses strickly '/', for legal HTML
#     output."""
#
#     # Hopefully, all paths will at some time have gone through this, it should
#     # work under Windows.
#     print 'a', a
#     print 'p', p
#
#     p = apply( joinpath, ( a, ) + p )
#     p = p.replace( os.sep, '/' )
#     return p
#
# if os.sep != '/':
#     joinpath = html_join

from posixpath import join as joinpath


#-------------------------------------------------------------------------------
#
def splitFn( fn ):
    """Returns a tuplet ( dir, base, repn, ext ).  Repn is '' if not present."""

    ( dir, bn ) = os.path.split( fn )

    fidx = bn.find( opts.separator )
    if fidx != -1:
        # found separator, add as an alt repn
        base = bn[ :fidx ]
        ( repn, ext ) = splitext( bn[ fidx + len(opts.separator): ] )

    else:
        # didn't find separator, split using extension
        ( base, ext ) = splitext( bn )
        repn = ''
    return ( dir, base, repn, ext )


#===============================================================================
# UTILITIES
#===============================================================================

#-------------------------------------------------------------------------------
#
def test_jpeg_exif(h, f):
    """imghdr test for JPEG data in EXIF format"""
    if h[6:10].lower() == 'exif':
        return 'jpeg'

imghdr.tests.append(test_jpeg_exif)

#-------------------------------------------------------------------------------
#
fast_imgexts = [ 'jpeg', 'jpg', 'gif', 'png', 'rgb', 'pbm', 'pgm', 'ppm', \
                 'tiff', 'tif', 'rast', 'xbm', 'bmp' ]

def imgwhat( fn, fast = None ):

    """Faster, sloppier, imgwhat, that doesn't require opening the file if we
    specified that it should be fast."""

    if fast == 1:
        ( base, ext ) = splitext( fn )
        if ext[1:].lower() in fast_imgexts:
            return ext.lower()
        else:
            return None
    else:
        # slow method, requires opening the file
        try:
            return imghdr.what( fn )
        except IOError:
            return None

#-------------------------------------------------------------------------------
#
magick_path_cache = {}

def getMagickProg( progname ):

    """Returns the program name to execute for an ImageMagick command."""

    if magick_path_cache.has_key( progname ):
        p = magick_path_cache[ progname ]
    else:
        if opts.magick_path:
            prg = joinpath( opts.magick_path, progname )
        else:
            prg = progname
        magick_path_cache[ progname ] = prg

        prg = normpath( prg )

        # Issue a warning if we can't find the program where specified.
        if opts.magick_path:
            if not exists( prg ) and not exists( prg + '.exe' ):
                print >> sys.stderr,\
                      "Warning: can't stat ImageMagick program %s" % prg
                print >> sys.stderr, \
                      "Perhaps try specifying it using --magick-path."

        p = prg

    o = p
    return o



#===============================================================================
# CLASS AttrFile
#===============================================================================

class AttrFile:

    """Attributes file representation and trivial parser."""

    #---------------------------------------------------------------------------
    #
    def __init__( self, path ):

        """Constructor."""

        self._path = path
        self._attrmap = {}
        self._dirty = 0

    #---------------------------------------------------------------------------
    #
    def read( self ):

        """Read the file and parse it."""

        try:
            f = open( self._path, "r" )
            self._lines = f.read()
            f.close()
        except IOError, e:
            print >> sys.stderr, \
                  "Error: cannot open attributes file", self._path
            self._lines = ''

        self.parse( self._lines )
        self._dirty = 0

    #---------------------------------------------------------------------------
    #
    def resetDirty( self ):

        """Resets the dirty flag. Why would you want to do this?"""

        self._dirty = 0

    #---------------------------------------------------------------------------
    #
    def write( self ):

        """Write the file to disk, if dirty."""

        # If not dirty, don't write anything.
        if self._dirty == 0:
            return

        try:
            # if there are no field, delete the file.
            if len( self._attrmap ) == 0:
                os.unlink( self._path )
                return

            f = open( self._path, "w" )
            for k in self._attrmap.keys():
                f.write( k )
                f.write( ": " )
                f.write( self._attrmap[k] )
                f.write( "\n\n" )
            f.close()
        except IOError, e:
            print >> sys.stderr, "Error: cannot open attributes file", \
                  self._path
            self._lines = ''

    #---------------------------------------------------------------------------
    #
    def parse( self, lines ):

        """Parse attributes file lines into a map."""

        mre1 = re.compile( "^([^:\n]+)\s*:", re.M )
        mre2 = re.compile( "^\s*$", re.M )

        pos = 0
        while 1:
            mo1 = mre1.search( lines, pos )

            if not mo1:
                break

            txt = None
            mo2 = mre2.search( lines, mo1.end() )
            if mo2:
                txt = string.strip( lines[ mo1.end() : mo2.start() ] )
            else:
                txt = string.strip( lines[ mo1.end() : ] )

            self._attrmap[ mo1.group( 1 ) ] = txt

            if mo2:
                pos = mo2.end()
            else:
                break

    #---------------------------------------------------------------------------
    #
    def get( self, field ):

        """Returns an attribute field content extracted from this attributes
        file."""

        if self._attrmap.has_key( field ):
            return self._attrmap[ field ]
        else:
            raise KeyError()

    #---------------------------------------------------------------------------
    #
    def get_def( self, field, default=None ):

        """Returns an attribute field content extracted from this attributes
        file."""

        if self._attrmap.has_key( field ):
            return self._attrmap[ field ]
        else:
            return default

    #---------------------------------------------------------------------------
    #
    def set( self, field, value ):

        """Sets a field of the description file. Returns true if the value has
        changed.  Set a field value to None to remove the field."""

        if value == None:
            if self._attrmap.has_key( field ):
                del self._attrmap[ field ]
                self._dirty = 1
                return 1
            else:
                return 0

        # remove stupid dos chars (\r) added by a web browser
        value = value.replace( '\r', '' )
        value = string.strip( value )

        # remove blank lines from the field value
        mre2 = re.compile( "^\s*$", re.M )
        while 1:
            mo = mre2.search( value )
            if mo and mo.end() != len(value):
                outval = value[:mo.start()]
                id = mo.end()
                while value[id] != '\n': id += 1
                outval += value[id+1:]
                value = outval
            else:
                break

        if '\n' in value:
            value = '\n' + value

        if self._attrmap.has_key( field ):
            if self._attrmap[ field ] == value:
                return 0

        self._attrmap[ field ] = value
        self._dirty = 1
        return 1

    #---------------------------------------------------------------------------
    #
    def __getitem__(self, key):
        return self.get( key )

    #---------------------------------------------------------------------------
    #
    def keys(self):
        return self._attrmap.keys()

    #---------------------------------------------------------------------------
    #
    def has_key(self, key):
        return self._attrmap.has_key(key)

    #---------------------------------------------------------------------------
    #
    def __len__(self):
        return len( self._attrmap )

    #---------------------------------------------------------------------------
    #
    def __repr__( self ):

        """Returns contents to a string for debugging purposes."""

        txt = (a + ":\n" + v + "\n\n" 
            for a, v in self._attrmap.iteritems())
        return ''.join(txt)




#===============================================================================
# BASIC CLASSES (for internal representation)
#===============================================================================

#===============================================================================
# CLASS Dir
#===============================================================================

class Dir:

    """Directory class."""

    #---------------------------------------------------------------------------
    #
    def __init__( self, path, parent, root ):

        """This ctor is called recursively to implement the recursive find.

        This returns a directory object. It expects the absolute path to the
        root and a relative directory name."""

        self._path = path
        self._basename = basename(path)
        self._parent = parent
        self._subdirs = []
        self._images = []
        self._tracks = []
        self._attrfile = None

        self._pagefn = None # to be computed outside according to policies

        files = dircache.listdir( joinpath( root, path ) )

        pattr = joinpath( root, self._path, dirattr_fn )
        if exists( pattr ) and isfile( pattr ):
            self._attrfile = AttrFile( pattr )
            self._attrfile.read()
            if self._attrfile.keys():
                print "  read attributes", self._attrfile.keys()

        imgmap = {}
        for f in files:
            af = joinpath( path, f )
            paf = joinpath( root, af )

            # add subdir
            bn = os.path.basename(paf)
            if not bn.startswith('.') and bn != THUMBDIR and isdir( paf ):
                subdir = Dir( af, self, root )
                # ignore directories which do not have images under them.
                if subdir.hasImages():
                    self._subdirs.append( subdir )

            # check other files in map
            else:

                # perhaps ignore file
                if opts.ignore_pattern and opts.ignore_re.search( af ):
                    print "ignoring file", af
                    continue

                # check for separator
                ( dir, base, repn, ext ) = splitFn( f )
                # dir should be nothing here.

                # ignore html file
                if not repn and ext == opts.htmlext:
                    continue

                # don't put index bases
                if base in [ 'dirindex', 'allindex', 'sortindex' ]:
                    continue
                if base.startswith( 'trackindex-' ):
                    continue

                try:
                    img = imgmap[ base ]
                except KeyError:
                    img = Image( self, base )
                    imgmap[ base ] = img

                if repn:
                    img._calts.append( repn + ext )
                else:
                    img._salts.append( ext )

        # Detect thumbnails, imagepages, attributes files.
        for i in imgmap.keys():
            e = imgmap[i]
            print "looking for images with base '%s'" % \
                  joinpath(e._dir._path, e._base)
            e.cleanAlts()
            if not e.selectName( joinpath( root, path ) ):
                del imgmap[i]
            print

        for f in imgmap.keys():
            img = imgmap[f]
            img.init( self._attrfile )
            if img._ignore:
                print "ignoring", img._base, "from desc file ignore tag."
                continue
            self._images.append( img )

        def cmp_img( a, b ):
            return cmp( a._base, b._base )
        self._images.sort( cmp_img )

        # compute directory files' trackmap (incomplete tracks, just to get
        # the list of keys)
        mmap = computeTrackmap( self._images )
        self._tracks = mmap.keys().sort()

    #---------------------------------------------------------------------------
    #
    def visit( self, functor ):
        for sd in self._subdirs:
            sd.visit(functor)
        functor(self)

    #---------------------------------------------------------------------------
    #
    def getAllImages( self ):

        """Gathers and returns all images in this directory and in its
        subdirectories."""

        images = list( self._images )
        for s in self._subdirs:
            print 'DIR', s
            if s != THUMBDIR:
                images += s.getAllImages()
        return images

    #---------------------------------------------------------------------------
    #
    def getAllDirs( self ):

        """Gathers and returns all dirnames and subdirnames from this
        directory."""

        dirs = [ self ]
        for d in self._subdirs:
            print 'getAllDirs', d
            if d != THUMBDIR and d.hasImages():
                dirs += d.getAllDirs()
        return dirs

    #---------------------------------------------------------------------------
    #
    def hasImages( self ):

        """Returns true if this directory has images, or if any of it
        subdirectories has images."""

        if len( self._images ) > 0:
            return 1
        for s in self._subdirs:
            if s.hasImages():
                return 1
        return 0

class SortedDict(dict):
    def __init__(self, mapping=None, key=lambda z: z, reverse=False, 
        *args, **kwds):
        dict.__init__(self, mapping, **kwds)
        self._key = key
        self._reverse = reverse

    def __iter__(self): 
        return iter(sorted(dict.__iter__(self), key=self._key, 
            reverse=self._reverse))

    def iterkeys(self): return iter(self)

    def iteritems(self): 
        for k in self.iterkeys(): 
            yield (k, self[k])

    def first(self):
        return iter(self).next()

    def nth(self, n):
        #print n, len(self)
        it = iter(self)
        for i in xrange(n-1): it.next() 
        return it.next()

#===============================================================================
# CLASS Image
#===============================================================================

class Image:

    """Image specific processing and storage."""

    #---------------------------------------------------------------------------
    #
    def __init__( self, dir, base ):

        """Constructor. Initialize to accumulation information."""

        self._dir = dir # directory object
        self._base = base # base (e.g. dscn0111)
        self._repn = None # suffix, if present (e.g. --800x800)
        self._ext = None # file extension (e.g. .jpg)

        self._salts = [] # simple alt.repns. (i.e. base.ext)
        self._calts = [] # complex alt.repns (i.e. base--repn.ext)
        self._size = None
        self._thumbs = SortedDict({})
        #self._thumbfn = None # thumbnail filename (i.e. base--thumb.gif)
        #self._thumbsize = None
        self._attr = None # attributes filename boolean
        self._title = '' # to be computed upon init()

        self._pagefn = None # to be computed outside according to policies

    #---------------------------------------------------------------------------
    #
    def init( self, dirattrfile = None ):

        """Performs proper initialization."""

        self._filename = joinpath( self._dir._path, self._base )
        if self._repn: self._filename += opts.separator + self._repn
        if self._ext: self._filename += self._ext

        # Create attrfile object.
        if self._attr:
            pattr = joinpath(opts.root, self._dir._path, \
                             self._base + self._attr)
            if exists( pattr ) and isfile( pattr ):
                attr = AttrFile( pattr )
                attr.read()
                if attr.keys():
                    print "  read attributes", attr.keys()

                self._attr = attr

        # Special pre-defined attributes.
        # FIXME these up in ctor?
        self._tracks = []
        self._ignore = 0

        self._dirattr = dirattrfile

        for a in [ self._dirattr, self._attr ]:
            if a:
                try:
                    self.handleDescription( a )
                except:
                    print >> sys.stderr, \
                          "Error: in attributes file %s" % a._path

        # no title, so use something unique to the image, it's path
        if not self._title:
            self._title = joinpath(self._dir._path, self._base)

        # make up map of altrepns
        self._altrepns = {}
        for k in self._salts:
            self._altrepns[ k[1:] ] = self._base + k
        for k in self._calts:
            self._altrepns[ k ] = self._base + opts.separator + k

    #---------------------------------------------------------------------------
    #
    def __repr__( self ):
        t = "Image( %s, %s, %s, %s,\n" % \
            ( self._dir, self._base, self._repn, self._ext )
        t += "       %s, %s, %s,\n" % \
             ( self._salts, self._calts, self._thumbs )
        t += "       %s )\n" % self._attr
        return t


    #---------------------------------------------------------------------------
    #
    def cleanAlts( self ):

        """Clean up found alt.repns, thumbnails, attributes files, etc."""

        # Detect html files, remove them in the altrepn
        try:
            idx = self._salts.index( opts.htmlext )
            print "  detected existing imagepage '%s'" % opts.htmlext
            del self._salts[idx]
        except ValueError:
            pass

        # Detect attributes files, remove them in the altrepn
        try:
            idx = self._salts.index( opts.attrext )
            print "  detected attributes file '%s'" % opts.attrext
            self._attr = self._salts[idx]
            del self._salts[idx]
        except ValueError:
            pass

        # Detect thumb file, separate them from altrepns
        for k in self._calts:
            if k.startswith( opts.thumb_sfx ):
                print "  detected thumb file '%s'" % k
                _, s, _ = k.split(opts.separator)
                self._thumbs[(int(s), int(s))] = k
                self._calts.remove( k )
                break

    #---------------------------------------------------------------------------
    #
    def selectName( self, absdirname ):

        """Select base file (image file) for image page generation. Returns true
        if it could find a suitable one."""

        print "  ", self._salts + self._calts

        #
        # choose one representation for the imagepage
        #

        # 1) the first of the affinity repn which is an image file
        found = 0
        for ref in opts.repn_affinity:
            for f in self._salts + self._calts:
                if ref.search( f ):
                    ff = self._base + opts.separator + f
                    paf = joinpath( absdirname, ff )
                    if imgwhat( paf, opts.fast ):
                        if f in self._salts:
                            self._salts.remove( f )
                            self._ext = f
                        else:
                            self._calts.remove( f )
                            ( self._repn, self._ext ) = splitext( f )

                        print "  choosing affinity '%s'" % f
                        return 1
                    else:
                        print "  ignoring non-image '%s'" % f

        # 2) the first of the base files which is an image file
        if opts.use_repn:
            # 3) with the first of the alternate representations which
            #    is an image file.
            eee = self._salts + self._calts
        else:
            eee = self._salts

        for f in eee:
            if not f.startswith('.'): f = opts.separator + f
            ff = self._base + f
            paf = joinpath( absdirname, ff )
            if imgwhat( paf, opts.fast ):
                if f in self._salts:
                    self._salts.remove( f )
                    self._ext = f
                else:
                    self._calts.remove( f )
                    ( self._repn, self._ext ) = splitext( f )
                print "  choosing imagefile '%s'" % f
                return 1
            else:
                print "  ignoring non-image '%s'" % f

        print "  no imagepage for base '%s'" % self._base
        return 0

    #---------------------------------------------------------------------------
    #
    def handleDescription( self, attrfile ):

        """Two description files, with precedence for the first."""

        tracks = attrfile.get_def( 'tracks' )
        if tracks:
            intracks = string.split( tracks )
            self._tracks = []
            for i in intracks:
                if i not in self._tracks:
                    self._tracks.append( i )

        ignore = attrfile.get_def( 'ignore' )
        if ignore:
            self._ignore = 1

        title = attrfile.get_def( 'title' )
        if title:
            self._title = title

    #---------------------------------------------------------------------------
    #
    def generateThumbnail( img ):

        """Generates a thumbnail for an image.

        Make it so that the longest dimension is the specified dimension."""

        if not img._thumbs:
            return

        for thumbsize, thumbfn in img._thumbs.iteritems():
            img.generateOneThumbnail(thumbsize, thumbfn)

    def generateOneThumbnail( img, thumbsize, thumbfn ):
        '''generates a thumbnail'''

        aimgfn = joinpath( opts.root, img._filename )
        if not opts.fast:
            img._size = imageSize(aimgfn)

        athumbfn = joinpath( opts.root, thumbfn )

        #print 'DIR ', os.path.dirname(athumbfn)
        if not os.path.exists(os.path.dirname(athumbfn)):
          os.mkdir(os.path.dirname(athumbfn))

        if opts.thumb_force:
            print "forced regeneration of '%s'" % thumbfn
        elif not exists(athumbfn):
            print "thumbnail absent '%s'" % thumbfn
        else:
            # Check if thumbsize has changed
            if not opts.fast:
                ts = imageSize(athumbfn)
                if not checkThumbSize( img._size,\
                                       ts, \
                                       thumbsize[0] ):
                    print "thumbnail '%s size has changed" % thumbfn
                    try:
                        # Clear cache for thumbnail size.
                        del imageSizeCache[ athumbfn ]
                    except:
                        pass
                else:
                    print "thumbnail '%s' already generated (size ok)" \
                          % thumbfn
                    return
            else:
                print "thumbnail '%s' already generated" % thumbfn
                return

        if opts.no_magick:
            print "ImageMagick tools disabled, can't create thumbnail"
            return

        # create necessary directories
        d = dirname(athumbfn)
        if not exists(d):
            os.makedirs(d)
            
        if opts.pil:

            try:
                im = PilImage.open(aimgfn)
                im.thumbnail( thumbsize )
                im.save(athumbfn)

                #ts = im.size
                del img._thumbs[thumbsize]
                img._thumbs[tuple(im.size)] = thumbfn
            except IOError, e:
                print >> sys.stderr, \
                    "Error: identifying file '%s'" % aimgfn + str(e)
                #raise SystemExit(\
                    #"Error: identifying file '%s'" % aimgfn + str(e))

        else:
    
            cmd = getMagickProg('convert') + ' -border 2x2 '
            # FIXME check if this is a problem if not specified
            #cmd += '-interlace NONE '
    
            cmd += '-geometry %dx%d ' % thumbsize
    
            if opts.thumb_quality:
                cmd += '-quality %d ' % opts.thumb_quality
    
            # This doesn't add text into the picture itself, just the comment in
            # the header.
            if opts.copyright:
                cmd += '-comment \"%s\" ' % opts.copyright
    
            # We use [1] to extract the thumbnail when there is one.
            # It is harmless otherwise.
            subimg = ""
            if img._ext.lower() in [ ".jpg", ".tif", ".tiff" ]:
                subimg = "[1]"
    
            cmd += '"%s%s" "%s"' % ( aimgfn, subimg, athumbfn )
    
            print "generating thumbnail '%s'" % thumbfn
    
            (chin, chout, cherr) = os.popen3( cmd )
            errs = cherr.readlines()
            chout.close()
            cherr.close()
            if errs:
                print >> sys.stderr, \
                      "Error: running convert program on %s:" % aimgfn
                errs = string.join(errs, '\n')
                print errs
    
                if subimg and \
                       re.compile('Unable to read subimage').search(errs):
                    print "retrying without subimage"
                    cmd = string.replace(cmd,subimg,"")
    
                    (chin, chout, cherr) = os.popen3( cmd )
                    errs = cherr.readlines()
                    chout.close()
                    cherr.close()
                    if errs:
                        print >> sys.stderr, \
                              "Error: running convert program on %s:" % aimgfn
                        print string.join(errs, '\n')
    
            else:
                del img._thumbs[thumbsize] 
                img._thumbs[tuple(imageSize(athumbfn))] = thumbfn


#===============================================================================
# IMAGE SIZE CACHE
#===============================================================================

#-------------------------------------------------------------------------------
#
def checkThumbSize( isz, tsz, desired ):

    """Returns true if the sizepair fits the size."""

    # tolerate 2% error
    try:
        if abs( float(isz[0])/isz[1] - float(tsz[0])/tsz[1] ) > 0.02:
            return 0 # aspect has changed, or isz rotated
    except:
        return 0
    return abs( desired - tsz[0] ) <= 1 or abs( desired - tsz[1] ) <= 1


#-------------------------------------------------------------------------------
#
def imageSizeNoCache( filename ):

    """Non-caching finding out the size of an image file."""

    if opts.no_magick:
        return ( 0, 0 )

    fn = filename
    if opts.pil:

        try:
            im = PilImage.open(fn)
            s = im.size
        except IOError, e:
            raise SystemExit("Error: identifying file '%s'" % fn + str(e))

        return s

    elif not opts.old_magick:

        cmd = getMagickProg('identify') + ' -format "%w %h" ' + \
              '"%s"' % fn
        po = os.popen( cmd )
        output = po.read()
        try:
            ( width, height ) = map( lambda x: int(x), string.split( output ) )
        except ValueError:
            print >> sys.stderr, \
                  "Error: parsing identify output on %s" % fn
            return ( 0, 0  )
        err = po.close()
        if err:
            print >> sys.stderr, \
                  "Error: running identify program on %s" % fn
            return ( 0, 0 )
        return ( width, height )

    else:
        # Old imagemagick doesn't have format tags
        cmd = getMagickProg('identify') + ' "%s"' % fn

        po = os.popen( cmd )
        output = po.read()
        err = po.close()
        if err:
            print >> sys.stderr, \
                  "Error: running identify program on %s" % fn
            return ( 0, 0 )

        mre = re.compile( "([0-9]+)x([0-9]+)" )
        mo = mre.match( string.split( output )[1] )
        if not mo:
            mo = mre.match( string.split( output )[2] )
        if mo:
            ( width, height ) = map( lambda x: int(x), mo.groups() )
            return ( width, height )
        print >> sys.stderr, \
              "Warning: could not identify size for image '%s'" % filename
        return ( 0, 0 )


#-------------------------------------------------------------------------------
#
fcachesizes = None
szre = re.compile('(\d+)x(\d+)')

imageSizeCache = {}

def imageSize( path ):

    """Returns the ( width, height ) image size pair.  Filename must be
    absolute. This method uses a cache to avoid having to reopen an image file
    multiple times."""

    global fcachesizes
    if not fcachesizes:
        fcachesizes = FCache( joinpath(opts.root, '.fcache') )

    sizestr = fcachesizes.lookup(path)
    if sizestr != None:
        mo = szre.match(sizestr)
        if mo:
            return ( int(mo.group(1)), int(mo.group(2)) )
    # else: go on...

    try:
        size = imageSizeCache[path]
        fcachesizes.store(path, "%dx%d" % size)
        return size
    except KeyError:
        size = imageSizeNoCache( path )
        imageSizeCache[path] = size
        fcachesizes.store(path, "%dx%d" % size)
        return size

    # We assume that the images don't change for the
    # duration that we build this cache.


#===============================================================================
# PAGE GENERATION
#===============================================================================

#-------------------------------------------------------------------------------
#
def generatePage( fn, ttype, envir ):

    """Generates an index page, replacing the tags as needed."""

    # create necessary directories
    d = dirname(joinpath(opts.root,fn))
    if not exists(d):
        os.makedirs(d)

    envir['cd'] = dirname(fn)

    # Write out modified file.
    try:
        afn = joinpath(opts.root, fn)
        tfile = open( afn, "w" )
        execTemplate( tfile, templates[ttype], envir )
        tfile.close()

    except IOError, e:
        print >> sys.stderr, "Error: can't open file: %s" % fn

#-------------------------------------------------------------------------------
#
def generateSummary( fn, allimages ):

    """Generates the text index that could be used by other processing tools."""

    # create necessary directories
    d = dirname(joinpath(opts.root,fn))
    if not exists(d):
        os.makedirs(d)

    otext = ""

    for i in allimages:
        l = i._filename
        l += ','
        if i._title:
            l += i._title
        # Make sure it's on a single line
        l = string.replace( l, '\n', ' ' )
        otext += l + '\n'

    # Write out file.
    try:
        afn = joinpath(opts.root, fn)
        tfile = open( afn, "w" )
        tfile.write( otext )
        tfile.close()

    except IOError, e:
        print >> sys.stderr, "Error: can't open file: %s" % fn

#===============================================================================
# TEMPLATE PARSING AND EXECUTION
#===============================================================================

#===============================================================================
# CLASS StringStream
#===============================================================================

class StringStream:

    """Simple string stream with a write() method, for replacing stdout when
    running in script environment. We can't use StringIO because we need the
    pop() hack."""

    #---------------------------------------------------------------------------
    #
    def __init__( self ):
        self._string = ""
        self._ignoreNext = 0

    #---------------------------------------------------------------------------
    #
    def write( self, s ):
        if self._ignoreNext:
            s = s[1:]
            self._ignoreNext = 0

        self._string += ( s )

    #---------------------------------------------------------------------------
    #
    def ignoreNextChar( self ):
        self._ignoreNext = 1

    #---------------------------------------------------------------------------
    #
    def getvalue( self ):
        return self._string


#-------------------------------------------------------------------------------
#
def readTemplates():

    """Reads the template files."""

    # Compile HTML templates.
    templates = {}
    for tt in [ 'image', 'dirindex', 'allindex', 'trackindex', 'sortindex' ]:
        fn = 'template-%s' % tt + opts.htmlext
        ttext = readTemplate( fn )
        templates[ tt ] = compileTemplate( ttext, fn )

    fn = 'template-css.css'
    ttext = readTemplate( fn )
    templates[ 'css' ] = compileTemplate( ttext, fn )

    # Compile user-specified rc file.
    rcsfx = 'rc'
    templates[ rcsfx ] = []
    if opts.rc:
        try:
            tfile = open( opts.rc, "r" )
            orc = tfile.read()
            tfile.close()
        except IOError, e:
            print >> sys.stderr, "Error: can't open user rc file:", opts.rc
            sys.exit(1)

        o = compileCode( '', orc, opts.rc )
        templates[ rcsfx ] += [ o ]

    # Compile user-specified code.
    if opts.rccode:
        o = compileCode( '', opts.rccode, "rccode option" )
        templates[ rcsfx ] += [ o ]

    # Compile global rc file without HTML tags, just python code.
    code = readTemplate( 'template-%s' % rcsfx + '.py' )
    o = compileCode( '', code, tt )
    templates[ rcsfx ] += [ o ]

    return templates


#-------------------------------------------------------------------------------
#
def readTemplate( tfn ):

    """Reads a template file.
    This method expects an simple filename."""

    if opts.verbose: print "fetching template", tfn

    found = 0
    foundInRoot = 0

    # check in user-specified template root.
    if opts.templates:
        fn = joinpath( opts.templates, tfn )
        if opts.verbose: print "  looking in %s" % fn
        if exists( fn ):
            found = 1

    # check in hierarchy root
    if not found:
        fn = joinpath( opts.root, tfn )
        if opts.verbose: print "  looking in %s" % fn
        if exists( fn ):
            foundInRoot = 1
            found = 1

    # look for it in the environment var path
    if not found:
        try:
            curatorPath = os.environ[ 'CURATOR_TEMPLATE' ]
            pathlist = string.split( curatorPath, os.pathsep )
            for p in pathlist:
                fn = joinpath( p, tfn )
                if opts.verbose: print "  looking in %s" % fn
                if exists( fn ):
                    found = 1
                    break
        except KeyError:
            pass

    if found == 1:
        # read the file
        try:
            tfile = open( fn, "r" )
            t = tfile.read()
            tfile.close()
        except IOError, e:
            print >> sys.stderr, "Error: can't open image template file:", fn
            sys.exit(1)
        if opts.verbose: print "  succesfully loaded template", tfn

    else:
        # bah... can't load it, use fallback templates
        if opts.verbose:
            print "  falling back on simplistic default templates."
        global fallbackTemplates
        try:
            t = fallbackTemplates[ splitext( tfn )[0] ]
        except KeyError:
            t = ''

    # Save templates in root, if it was requested.
    if opts.save_templates and foundInRoot == 0:
        rootfn = joinpath( opts.root, tfn )
        if opts.verbose: print "  saving template in %s" % rootfn

        # saving the file template
        if exists( rootfn ):
            bakfn = joinpath( opts.root, tfn + '.bak' )
            if opts.verbose: print "  making backup in %s" % bakfn
            import shutil
            try:
                shutil.copy( rootfn, bakfn )
            except:
                print >> sys.stderr, \
                      "Error: can't copy backup template %s", bakfn

        try:
            ofile = open( rootfn, "w" )
            ofile.write(t)
            ofile.close()
        except IOError, e:
            print >> sys.stderr, "Error: can't save template file to", rootfn

    return t

#-------------------------------------------------------------------------------
#
def compileCode( pretext, codetext, filename ):

    """Compile a chunk of code."""

    try:
        if codetext:
            co = compile( codetext, filename, "exec" )
            o = [ pretext, co, codetext ]
        else:
            o = [ pretext, None, codetext ]
    except:
        o = [ pretext, None, codetext ]

        print >> sys.stderr, \
              "Error compiling template in the following code:"
        print >> sys.stderr, codetext

        try:
            etype, value, tb = sys.exc_info()
            print_exception( etype, value, tb, None, sys.stderr )
        finally:
            etype = value = tb = None
        if not opts.ignore_errors:
            errors = 1

        print >> sys.stderr
    return o


#-------------------------------------------------------------------------------
#
def compileTemplate( ttext, filename ):

    """Compiles template text."""

    mre1 = re.compile( "<!--tag(?P<code>code)?:\s*" )
    mre2 = re.compile( "-->" )
    pos = 0
    olist = []
    errors = 0
    while pos < len(ttext):
        mo1 = mre1.search( ttext, pos )
        if not mo1:
            break
        mo2 = mre2.search( ttext, mo1.end() )
        if not mo2:
            print >> sys.stderr, "Error: unfinished tag."
            sys.exit(1)

        pretext = ttext[ pos : mo1.start() ]
        code = ttext[ mo1.end() : mo2.start() ]
        if not mo1.group( 'code' ):
            code = "print " + code + ","

        o = compileCode( pretext, code, filename )

        olist.append( o )
        pos = mo2.end()
    if pos < len(ttext):
        olist.append( [ ttext[ pos: ], None ] )

    if errors == 1 and not opts.ignore_errors:
        sys.exit(1)

    return olist

#-------------------------------------------------------------------------------
#
def execTemplate( outfile, olist, envir ):

    """Executes template text.  Output is written to outfile."""

    ss = outfile
    saved_stdout = sys.stdout
    sys.stdout = ss
    errors = 0
    for o in olist:
        ss.write( o[0] )

        if o[1]:
            try:
                eval( o[1], envir )

                # Note: this is a TERRIBLE hack to flush the comma cache of the
                # python interpreter's print statement between tags when outfile
                # is a string stream.
                #
                # Note: we don't need this anymore, since we're outputting to a
                # real file object.  However, keep this around in case we change
                # it back to output to a string.
                #if hack:
                #    ss.ignoreNextChar()

            except:
                print >> sys.stderr, \
                      "Error executing template in the following code:"
                print >> sys.stderr, o[2]

                try:
                    etype, value, tb = sys.exc_info()
                    print_exception( etype, value, tb, None, sys.stderr )
                finally:
                    etype = value = tb = None
                if not opts.ignore_errors:
                    errors = 1

                print >> sys.stderr


    if errors == 1 and not opts.ignore_errors:
        sys.exit(1)

    sys.stdout = saved_stdout

#===============================================================================
# MISC
#===============================================================================

#-------------------------------------------------------------------------------
#
def computeTrackmap( imagelist ):

    """Computes a map of files in each track. The key is the track name."""

    tracks = {}
    for i in imagelist:
        for t in i._tracks:
            if not tracks.has_key( t ):
                tracks[ t ] = []
            tracks[ t ].append( i )
    return tracks


#-------------------------------------------------------------------------------
#
def clean( allimages, alldirs ):

    """Removes the files generated by curator in the current directory and
    below."""

    for img in allimages:
        # Delete HTML files
        htmlfn = joinpath( opts.root, img._dir._path, img._pagefn )
        if exists( htmlfn ):
            if opts.verbose:
                print "Deleting", htmlfn
            try:
                os.unlink( htmlfn )
            except:
                print >> sys.stderr, "Error: deleting", htmlfn

        # Delete thumbnails
        if img._thumbfn:
            thumbfn = joinpath(opts.root, img._thumbfn)
            if exists( thumbfn ):
                if opts.verbose:
                    print "Deleting", thumbfn
                try:
                    os.unlink( thumbfn )
                    img._thumbfn = None
                except:
                    print >> sys.stderr, "Error: deleting", thumbfn

    for d in alldirs:
        files = dircache.listdir( joinpath(opts.root, d._path) )

        # Delete HTML files in directories
        for f in files:
            fn = joinpath( opts.root, d._path, f )
            if f in [ dirindex_fn, allindex_fn, allcidx_fn,
                      sortindex_fn, css_fn ] or \
               f.startswith( 'trackindex-' ):
                if opts.verbose:
                    print "Deleting", fn
                try:
                    os.unlink( fn )
                    pass
                except:
                    print >> sys.stderr, "Error: deleting", fn

            if f == index_fn and islink(fn):
                os.unlink(fn)



#===============================================================================
# DEFAULT TEMPLATES
#===============================================================================

# These are the very bare minimum and are provided here so that we just NEVER
# abort because we can't find the templates.

# Note: we really want this at the end of the file, because it screws up emacs
# python-mode highlighting.

#---------------------------------------------------------------------------
#
def imageSrc( cd, image, xtra='' ):

    assert(image._filename)
    if image._size:
        (w, h) = image._size
        iss = '<img src="%s" width="%d" height="%d" alt="%s" %s>' % \
              (urlquote(rel(image._filename, cd)), w, h, image._base, xtra)
    else:
        iss = '<img src="%s" alt="%s" %s>' % \
              (urlquote(rel(image._filename, cd)), image._base, xtra)

    return iss

#---------------------------------------------------------------------------
#
def thumbImage( cd, image, xtra='', nth=1 ):

    assert(image._thumbs)
    if image._thumbs:
        (w, h) = image._thumbs.nth(nth)
        iss = '<img src="%s" width="%d" height="%d" alt="%s" %s>' % \
              (urlquote(rel(image._thumbs[(w,h)], cd)), w, h, image._base, xtra)
    else:
        iss = '<img src="%s" alt="%s" %s>' % \
              (urlquote(rel(image._thumbs, cd)), image._base, xtra)

    return '<a href="%s">\n%s</a>' % (urlquote(rel(image._pagefn, cd)), iss)


#---------------------------------------------------------------------------
#
def table( dstdir, images, textfun=None, cols=4 ):

    """(images: seq of Image, textfun: function, cols: int)

    Utility function that generates a table with thumbnails for the given
    images. Specify textfun a callback if you want to include some text
    under each image. cols is the number of columns.  Of course, you're free
    to define your own table making function within the template itself if
    you don't like this one."""

    if len(images) == 0:
        return ""

    os = StringIO.StringIO()
    idx = 0
    while idx < len(images):

        if len(images) - idx >= cols:
            isubset = images[idx:idx + cols]
            idx += cols
        else:
            isubset = images[idx:]
            idx += len(isubset)

        # Separate tables provide for tighter fitting of thumbnails.
        print >> os, '<center><table width="100%">'
        print >> os, '<tr align=center>'
        for i in isubset:
            print >> os, '<td>'
            altname = 'alt="%s"' % i._title

            print >> os, thumbImage(dstdir, i)
            if textfun:
                print >> os, textfun(i)

            print >> os, "</td>"

        for i in range( 0, cols - len( isubset ) ):
            print >> os, "<td></td>"

        print >> os, "</tr>"

        print >> os, "</table></center>"

    return os.getvalue()

#-------------------------------------------------------------------------------
#
def twoColumns( dstdir, images ):

    os = StringIO.StringIO()
    print >> os, '<table cols=2 width=\"100%\"><tr><td>'
    print >> os, '<ul><font size=-2>'
    for i in images[ :len(images)/2 ]:
	 print >> os, '<li><a href=\"%s\">%s</a></li>' % \
	     ( rel(i._pagefn, dstdir), i._title )
    print >> os, '</font></ul>'

    print >> os, '</td><td>'

    print >> os, '<ul><font size=-2>'
    for i in images[ len(images)/2: ]:
	 print >> os, '<li><a href=\"%s\">%s</a></li>' % \
	     ( rel(i._pagefn, dstdir), i._title )
    print >> os, '</font></ul>'
    print >> os, '</td></tr></table>'

    return os.getvalue()

#---------------------------------------------------------------------------
#
def imagePile( dstdir, images ):

    if len(images) == 0:
        return ""

    os = StringIO.StringIO()
    print >> os, '<center>'
    for i in images:
        print >> os, thumbImage(dstdir, i)
    print >> os, "</center>"

    return os.getvalue()


#---------------------------------------------------------------------------
#
dirnavsep = ' / '
def dirnav( cd, dir, rootname="(root)", dirsep=dirnavsep ):

    """(rootname: string, dirsep: string, dir: Dir, ignoreCurrent: bool)

    Utility that generates an anchored HTML representation for a
    directory within the image hierarchy. You can click on the directory
    names."""

    d = dir
    dirs = []
    while d:
        dirs.append(d)
        d = d._parent
    dirs.reverse()

    comps = []
    for d in dirs:
        f = urlquote(joinpath(rel(d._pagefn, cd)))
        if d._parent == None:
            name = rootname
        else:
            name = d._basename
        comps.append('<a href="%s">%s</a>' % (f, name))

    return string.join(comps, '\n%s\n' % dirsep)

#---------------------------------------------------------------------------
#
def next( image, imglist ):
    idx = imglist.index(image)
    if idx+1 < len( imglist ):
        return imglist[idx+1]
    return None

#---------------------------------------------------------------------------
#
def prev( image, imglist ):
    idx = imglist.index(image)
    if idx-1 >= 0:
        return imglist[idx-1]
    return None

#---------------------------------------------------------------------------
#
def cycnext( image, imglist ):
    idxnext = (imglist.index(image)+1) % len(imglist)
    return imglist[idxnext]

#---------------------------------------------------------------------------
#
def cycprev( image, imglist ):
    idxprev = (imglist.index(image)-1) % len(imglist)
    return imglist[idxprev]

#---------------------------------------------------------------------------
#
def textnav(dstdir, image, imglist, midtext="", middest=None, pcycling=0 ):

    """(imglist: seq of Image, midtext: string, middest: string,
    pcycling: bool)

    Returns an HTML snippet for a text track navigation widget. Set
    pcycling to 1 if you want it cycling."""

    if pcycling == 1:
        prevfunc = cycprev
        nextfunc = cycnext
    else:
        prevfunc = prev
        nextfunc = next

    os = StringIO.StringIO()

    pi = prevfunc(image, imglist)
    if pi:
        print >> os, "<a href=\"%s\">" % rel(pi._pagefn, dstdir),
        print >> os, "<font size=\"-2\">prev</font></a>"

    if midtext != "":
        print >> os, "[",
        if middest:
            print >> os, "<a href=\"%s\"><font size=\"-2\">%s</font></a>" % \
                 ( urlquote(middest), midtext ),
        else:
            print >> os, "<font size=\"-2\">" + midtext + "</font>",
        print >> os, "]"
    else:
        if pi:
            print >> os, "&nbsp;"

    ni = nextfunc(image, imglist)
    if ni:
        print >> os, "<a href=\"%s\">" % rel(ni._pagefn, dstdir),
        print >> os, "<font size=\"-2\">next</font></a>"

    return os.getvalue()

#===============================================================================
# DEFAULT TEMPLATES
#===============================================================================

# Important Note: you can always save these with --save-templates and then edit
# them, and they will be used, without modifying this script. You can also put
# new common code in template-rc.py and use it from your templates.

html_preamble = \
"""<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">
<html>
<head>
   <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
   <link rel=stylesheet type=\"text/css\" href=\"<!--tag:rel(css_fn, cd)-->\">
   <title>%s</title>
</head>
<body>
"""

html_postamble = """
<!--tagcode:
if 'footer' in globals():
    print footer
-->
</body>
</html>
"""

fallbackTemplates = {}

fallbackTemplates[ 'template-css' ] = """

BODY {
    background-color: white;
    font-family: Arial,Geneva,sans-serif;
}

A:link { text-decoration: none }
A:visited { text-decoration: none }

.arrownav { width: 100%; border: none; margin: 0; padding: 0; }
.arrow { font-weight: bold; text-decoration: none; }

.image { border: solid 7px black; }

.desctable { width: 100%; border: none; margin: 0; padding: 0; }

.titlecell { vertical-align: top; }
.title { font-size: 32px; }

.location { font-weight: bold; }

.description { font-family: Arial,Geneva,sans-serif; }

HR.sephr { background-color: black; height: 1px; width: 90%; }

.navtable { width: 100%; border: none }

.settingscell {
    width: 1%;
    vertical-align: top;
    text-align: right;
    white-space: nowrap;
}
.settingstitle {
    font-size: xx-small;
    font-weight: bold;
}
.settings {
    font-size: xx-small;
}

.tracksind { font-weight: bold; }

.toptable { width: 100%; background-color: #EEEEFF; }

.dirtop { background-color: #EEEEFF; }
.globaltop { background-color: #FFEEEE; }
.tracktop { background-color: #EEFFEE; }
.sortedtop { background-color: #EEFFFF; }

.toptitle { font-size: x-large; }
.topsubtitle { font-weight: bold; }

.mininav { text-align: right; font-size: smaller; }

<!--tagcode:
if 'footerStyle' in globals():
    print footerStyle
-->

"""

fallbackTemplates[ 'template-image' ] = \
(html_preamble % 'Image: <!--tag:image._title-->') + \
"""

<!-- quick navigator at the top -->
<table class=\"arrownav\">
<tr><td width=50% align=\"left\">
<!--tagcode:
pi = prev(image, allimages)
if pi:
    print '<a class=\"arrow\" href=\"%s\">&lt;&lt;&lt;</a>' % \
        rel(pi._pagefn, cd)
-->

</td><td width=\"50%\" align=\"right\">
<!--tagcode:
ni = next(image, allimages)
if ni:
    print '<a class=\"arrow\" href=\"%s\">&gt;&gt;&gt;</a>' % \
        rel(ni._pagefn, cd)
-->
</td></tr></table>

<center>
<!--tagcode:

if image._pagefn:

    if image._size:
        (w,h)=image._size
        use_map = 1
        # smart image map
        w4 = w / 4
        ht = h / 10

        print '<map name=\"navmap\">'
        s = 0
        e = w

        print '<area shape=\"circle\" coords=\"%d,%d,%d\" href=\"%s\" />' % (w/2, h/2, w4, image._filename)

        pi = prev(image, allimages)
        if pi:
            print '<area shape=\"rect\" coords=\"%d,%d,%d,%d\" href=\"%s\" />' % \
                  (0, 0, w4, h, rel(pi._pagefn, cd))
            s = w4

        ni = next(image, allimages)
        if ni:
            print '<area shape=\"rect\" coords=\"%d,%d,%d,%d\" href=\"%s\" />' % \
                  (3*w4, 0, w, h, rel(ni._pagefn, cd))
            e = 3*w4

        print '<area shape=\"rect\" coords=\"%d,%d,%d,%d\" href=\"%s\" />' % \
              (s, 0, e, ht, rel(image._dir._pagefn, cd))

        print '</map>'

    else:
        use_map = 0

    xtra = 'class=\"image\"'
    if use_map:
        xtra += '  usemap=\"#%s\"' % 'navmap'
    # GT1
    #print imageSrc(cd, image, xtra)
    print thumbImage(cd, image, xtra, 2)
-->
</center>

<p>

<!--description and camera settings, in a table-->
<!--tagcode:
if image._attr:
    description = image._attr.get_def('description')
    settings = image._attr.get_def('settings')
    if not settings:
        settings = image._attr.get_def('info')

    print '<table class=\"desctable\">'
    print '<tr>'
    print '<td class=\"titlecell\">'

-->

<!--title and location in big, if available, to the left-->
<div class=\"title\">
<a href=\"<!--tag:image._filename-->\"><!--tag:image._base--></a><br>
</div>
<!--tagcode:
if image._attr:
    location = image._attr.get_def('location')
    if location:
        print '<span class=\"location\">%s</span><br>' % location
-->
<p>

<!--tagcode:

if image._attr:
    description = image._attr.get_def('description')
    if description:
        print '<p class=\"description\">'
        # FIXME don't we have to convert accents?
        print description
        print '</p>'

-->

<!--previous and next thumbnails, with text in between-->
<br>
<center>
<hr class=\"sephr\">
<table class=\"navtable\">
<tr>

<!--tagcode:
pi = prev(image, allimages)

if pi and pi._thumbs:
    pw = pi._thumbs.first()[0]
else:
    pw = opts.thumb_sizes[0]
#if pi and pi._thumbsize:
#    pw = pi._thumbsize[0]
#else:
#    pw = opts.thumb_size

print '<td width=\"%d\">' % pw
if pi:
    print thumbImage(cd, pi, 'align=\"left\"')
-->

</td><td align=\"center\" bgcolor=\"#F4F4F4\" CELLPADDING=\"5\">

<!--dirnav, alternative representations and navigation,
    between the floating thumbs-->

<b>
<!--tag:dirnav(cd, image._dir)-->
<!--tag:dirnavsep-->
<a href=\"<!--tag:rel(image._filename, cd)-->\">
<!--tag:basename(image._filename)--></a>
</b><br>

<!--tagcode:
if len(image._altrepns) > 0:
    print \"Alternative representations:\"
    for rep in image._altrepns.keys():
        print '<a href=\"%s\">%s</a>&nbsp;' % \
            (urlquote(rel(joinpath(image._dir._path, \
                                   image._altrepns[ rep ]), cd)), rep)
    print '<p>'
-->

<br>
<!--tagcode:
print textnav(cd, image, image._dir._images,
              \"dir\", rel(image._dir._pagefn, cd) )
if len(image._tracks) > 0:
    print '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;',
    print '<span class=\"tracksind\">tracks:</span>'
    for t in image._tracks:
        print '&nbsp;&nbsp;&nbsp;&nbsp;'
        print textnav(cd, image, trackmap[t], t, rel(trackindex_fns[t], cd) )
--><p>

</td>

<!--tagcode:
ni = next(image, allimages)

if ni and ni._thumbs:
    nw = ni._thumbs.first()[0]
else:
    nw = opts.thumb_sizes[0]
#if ni and ni._thumbsize:
#    nw = ni._thumbsize[0]
#else:
#    nw = opts.thumb_size

print '<td width=\"%d\">' % nw
if ni:
    print thumbImage(cd, ni, 'align=\"right\"')
-->

</td></tr></table>
</center>

</td>
<!--tagcode:

if image._attr:
    settings = image._attr.get_def('settings')
    if settings:
        print '<td class=\"settingscell\" >'
        print '<span class=\"settingstitle\">CAMERA SETTINGS:</span><br>'
        print '<span class=\"settings\">'
        for s in settings.splitlines():
            print \"%s<br>\" % s
        print '</span>'
        print '</td>'
-->

</tr>
</table>
""" + html_postamble

fallbackTemplates[ 'template-dirindex' ] = \
(html_preamble % 'Directory Index: <!--tag:dir._path-->') + \
"""
<table class=\"toptable dirtop\"><tr><td>
<p class=\"toptitle\"><!--tag:dirnav(cd, dir)--></p>
<p class=\"topsubtitle\">Directory Index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len( dir._subdirs ) > 0:
    print '<h3>Sub-directories:</h3>'
    print '<ul>'
    for d in dir._subdirs:
        print '<li><a href=\"%s\">%s</a></li>' % \
            ( rel(d._pagefn,cd), d._basename )
    print '</ul><p>'
-->

<!--tagcode:
if len( dir._images ) > 0:
    print '<h3>Images:</h3>'
    print imagePile( cd, dir._images )

    print '<h3>Images By Name:</h3>'
    print '<ul>'
    for i in dir._images:
        print '<li><a href=\"%s\">%s</a></li>' % \
            ( rel(i._pagefn, cd), i._base )
    print '</ul>'
-->
""" + html_postamble

fallbackTemplates[ 'template-trackindex' ] = \
(html_preamble % 'Track Index: <!--tag:track-->') + \
"""

<table class=\"toptable tracktop\"><tr><td>
<p class=\"toptitle\">Track index: <!--tag:track--></p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
images = trackmap[track]

if len(images) > 0:
    print '<h3>Images:</h3>'
    print imagePile( cd, images )

    print '<h3>Images by name:</h3>'
    print twoColumns(cd, images)
-->
""" + html_postamble

fallbackTemplates[ 'template-allindex' ] = \
(html_preamble % 'Global Index') + \
"""

<table class=\"toptable globaltop\"><tr><td>
<p class=\"toptitle\">Global Index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(alldirs) > 0:
    print '<H3>Directories:</H3>'
    print '<UL>'
    for d in alldirs:
        if d._parent:
            pname = d._path
        else:
            pname = '(root)'
        print '<li><a href=\"%s\">%s</a></li>' % \
            ( rel(d._pagefn, cd), pname )
    print '</ul><p>'
-->

<!--tagcode:
if len(tracks) > 0:
    print '<h3>Tracks:</h3>'
    print '<ul>'
    for t in tracks:
        print '<li><a href=\"%s\">%s</a></li>' % (trackindex_fns[t], t)
    print '</ul>'
-->

<!--tagcode:
if len(allimages) > 0:
    print '<h3>Images:</h3>'
    print imagePile( cd, allimages )

    print '<h3>Images by name:</h3>'
    print twoColumns(cd, allimages)
-->
""" + html_postamble

fallbackTemplates[ 'template-sortindex' ] = \
(html_preamble % '\"Sorted index\"') + \
"""
<table class=\"toptable sortedtop\"><tr><td>
<p class=\"toptitle\">Sorted index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(allimages) > 0:
    import os
    print '<h3>Images sorted by name:</h3>'
    ilist = list(allimages)
    ilist.sort( lambda x,y: cmp( x._base, y._base ) )

    for i in ilist:
        print '<p>'
	print thumbImage( cd, i, 'align=\"middle\"' )
        print '<a href=\"%s\">%s</a>' % \
            ( rel(i._pagefn, cd), i._base )
	print
-->
""" + html_postamble

#===============================================================================
# MAIN
#===============================================================================

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip(), version=__version_pr__)
    parser.add_option('--help-script', action='store_true',
                      help="show scripting environment documentation.")
    parser.add_option('-v', '--verbose', action='store_true', dest="verbose",
                      help="run verbosely (default)")
    parser.add_option('-q', '--quiet', action='store_false', dest="verbose",
                      help="run quietly (turns verbosity off)")
    parser.add_option('--no-links', action='store_true',
                      help="don't make links to HTML directory indexes")

    parser.add_option('--use-repn', action='store', help="""Don't
                      generate an image page if there is no base file (i.e. a
                      file without an alternate repn suffix. The default
                      selection algorithm is to choose 1) the first of the
                      affinity repn which is an image file (see repn-affinity
                      option), 2) the first of the base files which is an image
                      file, 3) (optional) the first of the alternate
                      representations which is an image file.  This option adds
                      step (3).""")

    parser.add_option('--repn-affinity', action='store', help="""Specifies
                      a comma separated list of regular expressions to match for
                      alt.repn files and file extensions to prefer when
                      searching for a main image file to generate a page for
                      (e.g. \"\.jpg,--768\..*,\.gif\".""")

    parser.add_option('-t', '--templates', action='store', help="""specifies the
                      directory where to take templates from (default:
                      root). This takes precedence over the CURATOR_TEMPLATE
                      environment variable AND over the root""")

    parser.add_option('--rc', action='store', help="""specifies an
                      additional global file to include and run in the page
                      environment before expanding the templates.  This can be
                      used to perform global initialization and customization of
                      template variables.  The file template-rc.py is searched
                      in the same order as for templates and is executed in that
                      order as well.  Note that output when executing this goes
                      to stdout.""")

    parser.add_option('--rccode', action='store', help="""specifies
                      additional global init code to run in the global
                      environment.  This can be used to parameterize the
                      templates from the command line (see option --rc).""")


    parser.add_option('--save-templates', action='store', help="""saves
                      the template files in the root of the hierarchy.  Previous
                      copies, if existing and different from the current
                      template, are moved into backup files.  This can be useful
                      for keeping template files around for future regeneration,
                      or for saving a copy before editing.""")

    parser.add_option('-k', '--ignore-errors', action='store_true',
                      help="ignore errors in templates")

    parser.add_option('-I', '--ignore-pattern', action='store',
                      help="regexp to specify image files to ignore")

    parser.add_option('--htmlext', action='store',
                      help="specifies html files extension (default: '.html')")

    parser.add_option('--attrext', action='store', help="""specifies
                      attributes files extension (default: '.desc')""")

    parser.add_option('--thumb-sfx', action='store', help="""specifies the
                      thumbnail alt.repn. suffix (default: 'thumb.jpg')""")

    parser.add_option('-p', '--separator', action='store', help="""specify the
                      image basename separator from the suffix and extension
                      (default: --)""")

    parser.add_option('-C', '--copyright', action='store',
                      help="""specifies a copyright notice to include in image
                      conversions""")

    group = optparse.OptionGroup(\
        parser, "Conversion tools",
        "Selects options related to conversion tools.")

    group.add_option('--magick-path', action='store', metavar="PATH",
                     help="specify imagemagick path to use")

    group.add_option('--old-magick', action='store_true',
                     help="use old imagemagick features (default)")

    group.add_option('--new-magick', action='store_false',
                     dest="old_magick", help="use new imagemagick features")

    group.add_option('--no-magick', action='store_true',
                     help="disable using imagemagick (disable conversions)")
    # FIXME remove this option at some point

    group.add_option('--pil', action='store_true', help="""use the Python
                      Imaging Library (PIL) instead of the Imagemagick
                      tools.""")
    parser.add_option_group(group)

    parser.add_option('-s', '--thumb-sizes', action='store', 
                      help="specifies size in pixels of thumbnail largest side")

    parser.add_option('-F', '--thumb-force', action='store_true',
                      help="regenerate and xoverwrite existing thumbnails")

    parser.add_option('-Q', '--thumb-quality', action='store', help="""specify
                      quality for thumbnail conversion (see convert(1))""")

    parser.add_option('-X', '--fast', action='store_true', help="""disables some
                      miscalleneous slow checks, even if the consistency can be
                      shaken up. Don't use this, this is a debugging tool""")

    parser.add_option('--clean', action='store_true', help="""remove all
                      files generated by curator.  Curator exits after clean
                      up.""")

    group = optparse.OptionGroup(\
        parser, "Output method",
        "Selects where the output files will be located .")

    group.add_option('-D', '--out-along', action='store_true',
                     help="Put outputs along with files (default).")

    group.add_option('-S', '--out-subdirs', action='store_true',
                     help="Put outputs in subdirectories of the directories.")

    group.add_option('-O', '--out-onedir', action='store_true',
                     help="Put all outputs in a single output subdirectory.")
    parser.add_option_group(group)

    # FIXME eventually make it use the full power of optparse
    # type conversions
    # aliases

    global opts
    opts, args = parser.parse_args()

    if len(args) == 0:
        opts.root = os.getcwd()
    elif len(args) == 1:
        opts.root = args[0]
    elif len(args) > 1:
        print >> sys.stderr, "Error: can only specify one root."
        sys.exit(1)

    #
    # end options parsing.
    #

    # Debugging this script
    opts.debug = 0

    #
    # set defaults
    #

    if not opts.thumb_sizes:
        opts.thumb_sizes = (150,800)
        # this is the best default IMHO, that doesn't detract the attention too
        # much from 1024x768 images (makes the clicker curious) yet gives enough
        # detail you can find the image in the index.
    else:
        #print opts.thumb_sizes
        #print tuple(map(int, opts.thumb_sizes.split(',')))
        try:
            opts.thumb_sizes = tuple(map(int, opts.thumb_sizes.split(',')))
            if len([x for x in opts.thumb_sizes if x <= 0]) > 0:
                raise ValueError()
        except ValueError:
            print >> sys.stderr, "Error: Illegal thumbnail size."
            sys.exit(1)

    if not opts.separator:
        opts.separator = "--"

    if not opts.htmlext:
        opts.htmlext = ".html"

    if not opts.attrext:
        opts.attrext = ".desc"

    if not opts.thumb_sfx:
        opts.thumb_sfx = "thumb.jpg" # will create jpg thumbnails by default


    #
    # Validate options.
    #
    print "====> validating options"

    if opts.help_script:
        print generateScriptHelp()
        sys.exit(1)

    if opts.pil:
        global PilImage
        try:
            import Image as PilImage
        except ImportError, e:
            try:
                import PIL.Image as PilImage
            except ImportError, e:
                raise SystemExit(\
                "Error: you said to use PIL but PIL seems not to be installed.")

    if opts.templates:
        opts.templates = os.path.expanduser( opts.templates )

    if ( opts.magick_path or opts.old_magick != None ) and opts.no_magick:
        print >> sys.stderr, "Error: Ambiguous options, use Magick or not?"
        sys.exit(1)

    if opts.old_magick == None:
        opts.old_magick = 1

    if opts.thumb_quality:
        try:
            opts.thumb_quality = int( opts.thumb_quality )
        except ValueError:
            print >> sys.stderr, "Error: Illegal thumbnail quality."
            sys.exit(1)

    if opts.ignore_pattern:
        # pre-compile ignore re for efficiency
        opts.ignore_re = re.compile( opts.ignore_pattern )

    if opts.repn_affinity:
        res = []
        for r in string.split( opts.repn_affinity, ',' ):
            res.append( re.compile( r ) )
        opts.repn_affinity = res
    else:
        opts.repn_affinity = []

    if len(filter(None, [opts.out_along, opts.out_subdirs,
                         opts.out_onedir])) > 1:
        print >> sys.stderr, "Error: Make up your mind, which outputs?"
        sys.exit(1)

    #
    # initialize global constants
    #
    cidxext = ".cidx"

    global index_fn, dirindex_fn, dirattr_fn
    global allindex_fn, allcidx_fn, trackindex_fn, sortindex_fn, css_fn
    index_fn = "index" + opts.htmlext
    dirindex_fn = "dirindex" + opts.htmlext
    dirattr_fn = "dir" + opts.attrext
    allindex_fn = "allindex" + opts.htmlext
    allcidx_fn = "allindex" + cidxext
    trackindex_fn = "trackindex-%s" + opts.htmlext
    sortindex_fn = "sortindex" + opts.htmlext
    css_fn = 'core-style.css'

    global hor_sep, ver_sep
    hor_sep = "&nbsp;&nbsp;\n"
    ver_sep = "<BR>\n"

    opts.root = normpath( opts.root )
    if not exists( opts.root ) or not isdir( opts.root ):
        print >> sys.stderr, "Error: root %s doesn't exist." % opts.root
        sys.exit(1)

    if opts.magick_path:
        opts.magick_path = normpath( opts.magick_path )
        if not exists( opts.magick_path ) or \
           not isdir( opts.magick_path ):
            print >> sys.stderr, \
                  "Error: magick-path %s is invalid." % opts.magick_path
            sys.exit(1)

    #
    # Find and process list of images, reading necessary information for each
    # image.
    #
    print "====> gathering image list and attributes files"

    rootdir = Dir( "", None, opts.root )

    #
    # compute pathnames and some global variables
    #
    def prepend(path, pfx):
        (d, f) = os.path.split(path)
        return joinpath(d, pfx, f)

    allimages = rootdir.getAllImages()
    alldirs = rootdir.getAllDirs()
    trackmap = computeTrackmap( allimages )
    tracks = trackmap.keys()
    tracks.sort()
    trackindex_fns = {}
    for t in tracks:
        trackindex_fns[t] = trackindex_fn % t

    def compDirName(dir):
        dir._pagefn = joinpath(dir._path, dirindex_fn)
    rootdir.visit(compDirName)

    #print opts.thumb_sizes
    for i in allimages:
        i._pagefn = joinpath(i._dir._path, i._base + opts.htmlext)
        i._thumbs = SortedDict(
          ((x, x), joinpath(i._dir._path, THUMBDIR,
                       (i._base + opts.separator + ('%03d' % x)
                        + opts.separator + opts.thumb_sfx)) )
          for x in opts.thumb_sizes)
        #i._thumbfn = joinpath(i._dir._path, THUMBDIR,
        #                      i._base + opts.separator + opts.thumb_sfx)

    if opts.out_subdirs:

        htmldir = 'html'
        thumbdir = 'html'

        allindex_fn = prepend(allindex_fn, htmldir)
        allcidx_fn = prepend(allcidx_fn, htmldir)
        sortindex_fn = prepend(sortindex_fn, htmldir)
        css_fn = prepend(css_fn, htmldir)
        for t in tracks:
            trackindex_fns[t] = prepend(trackindex_fns[t], htmldir)

        def prependDirVisitor(dir):
            dir._pagefn = prepend(dir._pagefn, htmldir)
        rootdir.visit(prependDirVisitor)

        for i in allimages:
            i._pagefn = prepend(i._pagefn, htmldir)
            #i._thumbfn = prepend(i._thumbfn, thumbdir, THUMBDIR)

    elif opts.out_onedir:
        od = 'html'

        allindex_fn = joinpath(od, allindex_fn)
        allcidx_fn = joinpath(od, allcidx_fn)
        sortindex_fn = joinpath(od, sortindex_fn)
        css_fn = joinpath(od, css_fn)
        for t in tracks:
            trackindex_fns[t] = joinpath(od, trackindex_fns[t])

        def prependDirVisitor(dir):
            dir._pagefn = joinpath(od, dir._pagefn)
        rootdir.visit(prependDirVisitor)

        for i in allimages:
            i._pagefn = joinpath(od, i._pagefn)
            #i._thumbfn = joinpath(od, THUMBFN, i._thumbfn)

    #
    # If asked to clean, clean and exit.
    #
    if opts.clean:
        print "====> cleaning up generated files"

        clean( allimages, alldirs )
        print "====> done."
        sys.exit(0)

    #
    # Read template files.
    #
    print "====> templates input and compilation"

    global templates
    templates = readTemplates()

    #
    # Thumbnail generation.
    #
    print "====> thumbnail generation and sizes computation"

    for img in allimages:
        img.generateThumbnail()

    #
    # Execute global rc file.
    #
    print "====> executing global rc file"
    envir = {}
    envir.update( globals() )
    envir.update( locals() )
    execTemplate( sys.stdout, templates['rc'], envir )

    #
    # Output directory indexes
    #
    print "==> directory index generation"

    def walkDirsForIndex( dir ):
        # this does not do make the link for existing dirindex
        if dir.hasImages() == 1:
            envir['dir'] = dir
            print "generating dirindex", dir._pagefn
            generatePage( dir._pagefn, 'dirindex', envir )

            lnfn = joinpath(opts.root, dir._path, index_fn)
            if not ( opts.no_links or opts.out_onedir ) and \
                   not exists(lnfn) and not islink(lnfn):
                if hasattr(os, 'symlink'):
                    os.symlink(rel(dir._pagefn, dir._path), lnfn)
    rootdir.visit(walkDirsForIndex)

    #
    # Output track indexes HTML
    #
    print "==> track index generation"

    for track in trackmap.keys():
        fn = trackindex_fns[track]
        envir['dir'] = rootdir
        envir['track'] = track
        print "generating trackindex", fn
        generatePage( fn, 'trackindex', envir )

    #
    # Output global index HTML file and summary text file.
    #
    print "==> global index generation"

    envir['dir'] = rootdir
    print "generating allindex", allindex_fn
    generatePage( allindex_fn, 'allindex', envir )
    print "generating sortindex", sortindex_fn
    generatePage( sortindex_fn, 'sortindex', envir )
    print "generating summary", allcidx_fn
    generateSummary( allcidx_fn, allimages )
    print "generating css file", css_fn
    generatePage( css_fn, 'css', envir )

    #
    # Output image HTML files
    #
    print "====> image page generation"

    global walkDirsForImages
    def walkDirsForImages( dir ):
        for d in dir._subdirs:
            walkDirsForImages( d )
        for img in dir._images:
            envir['dir'] = dir
            envir['image'] = img
            print "generating image page", img._pagefn
            generatePage( img._pagefn, 'image', envir )

    walkDirsForImages( rootdir )

    # signal the end
    print "====> done."


# Run main if loaded as a script
if __name__ == "__main__":
    main()

#===============================================================================
# END
#===============================================================================

# change 'name' to 'file-or-title'

# split stuff that could totally be in the includes.py file

# remove table b.s. when it all works

# make it work with CSS
