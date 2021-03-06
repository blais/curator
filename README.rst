=============================================
   curator: Static Image Gallery Generator
=============================================

.. contents:: Table of Contents

Description
===========

Curator/HS is a simple script that allows one to generate HTML image
galleries with the intent of displaying photographic images on the
Web, or for a CD-ROM presentation, or for archiving.

It generates static web pages only - no special configuration or
running of scripts are required on the server. The script supports
hierarchical directories, thumbnail generation, automatic resizing.
Its output leverages the `Highslide JS`__ library for a slick design.

It can be templated with a single file fo HTML with simple keywords in
them. Running this script only requires a recent Python interpreter
and the PIL (Python Imaging Library).

__ Highslide JS: http://highslide.com/

.. important::

   I've rewritten curator on 2011-01-16 to make it use Highslide JS,
   the result is much simpler and I made other improvements and
   simplifications along the way. Use `curator-hs` for an improved
   experience.


Motivation
----------

There are many gallery generator on the internet. It seems everyone
and their brother has been writing an image gallery generation script
these days. Why did I write my own? Most of the existing ones required
server customizations (PHP, cgi scripts) and will not work off of a
simple archive CDROM, or required some annoying installation of some
special image manipulation packages, or didn't support templating.
Problems problems problems. I just wanted something simple.

Another way to view the services that this script provides is this:

- it gathers the input files
- optionally, it generates scaled-down versions of the images
- it generates all the thumbnails
- it puts all those contents under a single directory 'gallery' with
  an HTML index
- all the links are relative, so you should be able archive and serve
  the files from anywhere


Features
--------

This script was written with the following requirements/goals/features:

- on the client side: nothing more should be required than a **web browser** to
  use it;

- on the server side: the web pages should be **statically** generated (no need
  for special server configuration, no cgi, no PHP, no Zope, no nonsense, just
  HTML);

- all links are **relative links** (i.e. it should work when burned on a CDROM
  or moved);

- the output HTML should be **templated/themeable** (i.e. the user can change
  the look of the output HTML);

- **thumbnails** should be generated automatically, the thumbnails reside
  alongside the photos themselves;

- it should be **simple to use** (it should be able to work with a simple
  hierarchy of image files, with a trivial invocation, try it now, if it don't
  work, I've failed);

- it should be **trivial to install and portable** (i.e. should not use more
  than what is available in base installs of most linux distributions).  In this
  respect, thus this script only depends on the availability of:

   - Python, version 2 or more;
   - Python Imaging Library (PIL);

There is no special library to install, no special tools, nothing.
Download and run. This runs on a default redhat install.


Documentation
=============

- `CHANGES <CHANGES>`_ (recent changes, history);
- `TODO <TODO>`_

Invocation
----------

Running the script with the default templates should be as easy as cd'ing in the
root of the image hierarchy and typing ``curator``.

Run ``curator --help`` for command line interface options, description of the
required inputs and of what the script generates.


Download
========

A Mercurial repository can be found at:

  http://github.com/blais/curator


Installation
============

Dependencies
------------

One of the most important "features" of curator is that it does not depend on
much to run or to view the pages.

- Python-2.3 or greater;
- PIL (Python Imaging Library);


Portability
-----------

curator will run under any platform that has a Python2 (or more)
interpreter and the ImageMagick tools. It has been tested under Linux
and IRIX. curator is known to have worked under Windows using the PIL
(tested on 2003-11).


Contributions
=============

Contributions from other people can be found in the source code.


External Links
==============

- `Sourceforge Project Page <http://sourceforge.net/projects/curator>`_

- `Freshmeat Appindex <http://www.freshmeat.net/projects/curator>`_

- Getting `Python <http://python.org>`_

- Getting `ImageMagick <http://www.imagemagick.org>`_


Copyright and License
=====================

Copyright (C) 2001-2011  Martin Blais.  All Rights Reserved.

This code is distributed under the `GNU General Public License <COPYING>`_;

Author
======

Martin Blais <blais@furius.ca>


.. official sourceforge logo code snippet

.. image:: http://sourceforge.net/sflogo.php?group_id=2198&type=1
   :width: 88
   :height: 31
   :alt: SourceForge Logo
