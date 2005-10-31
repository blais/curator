#!/usr/bin/env python

__revision__ = "$Id$"

from distutils.core import setup

setup (name = "curator",
       version = "1.0",
       description = "Generate static HTML pages for displaying photographs",
       author = "Martin Blais",
       author_email = "blais@iro.umontreal.ca",
       maintainer = "Martin Blais",
       maintainer_email = "blais@iro.umontreal.ca",
       url = "http://www.iro.umontreal.ca/~blais/projects/curator/",
       licence = "GPL",

       long_description = """\ Curator is a script that allows one to generate
static web pages with the intent of displaying photographic images on the web,
or for a CD-ROM presentation and archiving. The pages are fully templateable,
with embedded python code within the HTML.  """,

       scripts = ['curator'],

      )
