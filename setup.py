#!/usr/bin/env python
#
# Install script for curator.
#

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"

from distutils.core import setup

def read_version():
    try:
        return open('VERSION', 'r').readline().strip()
    except IOError, e:
        raise SystemExit(
            "Error: you must run setup from the root directory (%s)" % str(e))

# Include all files without having to create MANIFEST.in
def add_all_files(fun):
    import os, os.path
    from os.path import abspath, dirname, join
    def f(self):
        for root, dirs, files in os.walk('.'):
            if '.hg' in dirs: dirs.remove('.hg')
            self.filelist.extend(join(root[2:], fn) for fn in files
                                 if not fn.endswith('.pyc'))
        return fun(self)
    return f
from distutils.command.sdist import sdist
sdist.add_defaults = add_all_files(sdist.add_defaults)


setup(name="curator",
      version=read_version(),
      description="Templateable Image Gallery Generator.",
      long_description="""
Curator is a powerful script that allows one to generate Web page image
galleries with the intent of displaying photographic images on the Web, or for a
CD-ROM presentation and archiving.

It generates static Web pages only - no special configuration or running scripts
are required on the server. The script supports many file formats, hierarchical
directories, thumbnail generation and update, per-image description file with
any attributes, and 'tracks' of images spanning multiple directories. The
templates consist of HTML with embedded Python. Running this script only
requires a recent Python interpreter and the Python Imaging Library OR the
ImageMagick tools. If you've been looking for a simple yet very powerful script
to do this task you've come to the right place.""",
      license="GNU GPL",
      author="Martin Blais",
      author_email="blais@furius.ca",
      url="http://curator.sourceforge.net",
      download_url="http://github.com/blais/curator",
      scripts = ['bin/curator-hs', 'bin/curator']
     )
