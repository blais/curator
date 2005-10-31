#!/usr/bin/env python

__revision__ = "$Id$"

from distutils.core import setup

setup (name = "curator",
       version = "0.1",
       description = "Generate HTML pages for displaying photographs",
       author = "Martin Blais",
       author_email = "blais@iro.umontreal.ca",
       maintainer = "Martin Blais",
       maintainer_email = "blais@iro.umontreal.ca",
       url = "http://www.iro.umontreal.ca/~blais/projects/curator/",
       licence = "GPL",
       long_description = """\
Curator is a script that allows one to generate web pages with the intent of
displaying photographic images on the web, or for a CD-ROM presentation and
archiving.
""",

       py_modules = ['quickopts'],
      )
