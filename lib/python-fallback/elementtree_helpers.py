#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2001, Martin Blais <blais@furius.ca>
#*
#*****************************************************************************/

"""ElementTree XML helper functions.

Augment ElementTree with missing functionality.

"""

__version__ = "$Revision$"
__author__ = "Martin Blais <blais@furius.ca>"


import os, sys
import textwrap

from elementtree import ElementTree, ElementPath



def element_getiteratorp(self, tag=None, index=0, parent=None):
    """A version of Element.getiterator that also gives the parent. This is
    useful when you want to replace a node."""

    nodes = []
    if tag == "*":
        tag = None
    if tag is None or self.tag == tag:
        nodes.append( (self, index, parent) )
    i = 0
    for node in self._children:
        nodes.extend(node.getiteratorp(tag, i, self))
        i += 1
    return nodes

ElementTree._Element.getiteratorp = element_getiteratorp


def tree_findallp(self, path):
    assert self._root is not None
    if path[:1] == "/":
        path = "." + path
    return self._root.findallp(path)

ElementTree.ElementTree.findallp = tree_findallp


def element_findallp(self, path):
    return ElementPath.findallp(self, path)

ElementTree._Element.findallp = element_findallp



# FIXME: not sure about this code, my modifications are hacked quickly without
# full understanding of this code, always review changes.

from elementtree.ElementPath import xpath_descendant_or_self

def path_findallp(self, element):
    nodeset = [(element, 0, None)]
    index = 0
    while 1:
        try:
            path = self.path[index]
            index = index + 1
        except IndexError:
            return nodeset
        set = []
        if isinstance(path, xpath_descendant_or_self):
            try:
                tag = self.path[index]
                if not isinstance(tag, type("")):
                    tag = None
                else:
                    index = index + 1
            except IndexError:
                tag = None # invalid path
            for node, idx, parent in nodeset:
                new = list(node.getiteratorp(tag))
                if new and new[0] is node:
                    set.extend(new[1:])
                else:
                    set.extend(new)
        else:
            for node, idx, parent in nodeset:
                i = 0
                for nodec in node:
                    if path == "*" or nodec.tag == path:
                        set.append( (nodec, i, node) )
                    i += 1
        if not set:
            return []
        nodeset = set

ElementPath.Path.findallp = path_findallp


def path_findallp_mod(element, path):
    return ElementPath._compile(path).findallp(element)

ElementPath.findallp = path_findallp_mod



# Formatted output.
wrapper = textwrap.TextWrapper()

if True:

    from elementtree.ElementTree import \
         Comment, ProcessingInstruction, QName, _escape_cdata, _escape_attrib
    def write_fmt(self, file, encoding="us-ascii", indent='   '):
        assert self._root is not None
        if not hasattr(file, "write"):
            file = open(file, "wb")
        if not encoding:
            encoding = "us-ascii"
        elif encoding != "utf-8" and encoding != "us-ascii":
            file.write("<?xml version='1.0' encoding='%s'?>\n" % encoding)
        self._write_fmt(file, self._root, encoding, {}, 0, indent)

    def _write_fmt(self, file, node, encoding, namespaces, level, indent):
        indstr = '\n' + indent * level

        # write XML to file
        tag = node.tag
        if tag is Comment:
            file.write(indstr) # indent
            file.write("<!-- %s -->" % _escape_cdata(node.text, encoding))
        elif tag is ProcessingInstruction:
            file.write(indstr) # indent
            file.write("<?%s?>" % _escape_cdata(node.text, encoding))
        else:
            items = node.items()
            xmlns_items = [] # new namespaces in this scope
            try:
                if isinstance(tag, QName) or tag[:1] == "{":
                    tag, xmlns = fixtag(tag, namespaces)
                    if xmlns: xmlns_items.append(xmlns)
            except TypeError:
                _raise_serialization_error(tag)
            file.write(indstr) # indent
            file.write("<" + tag)
            if items or xmlns_items:
                items.sort() # lexical order
                for k, v in items:
                    try:
                        if isinstance(k, QName) or k[:1] == "{":
                            k, xmlns = fixtag(k, namespaces)
                            if xmlns: xmlns_items.append(xmlns)
                    except TypeError:
                        _raise_serialization_error(k)
                    try:
                        if isinstance(v, QName):
                            v, xmlns = fixtag(v, namespaces)
                            if xmlns: xmlns_items.append(xmlns)
                    except TypeError:
                        _raise_serialization_error(v)
                    file.write(" %s=\"%s\"" % (k, _escape_attrib(v, encoding)))
                for k, v in xmlns_items:
                    file.write(" %s=\"%s\"" % (k, _escape_attrib(v, encoding)))
            if node.text or node:
                file.write(">")
                filled = False
                if node.text:
                    if '\n' in node.text:
##                         wrapper.initial_indent = indstr[1:] + indent
##                         wrapper.subsequent_indent = indstr[1:] + indent
##                         file.write('\n')
##                         file.write(
##                             _escape_cdata(wrapper.fill(node.text), encoding))
                        file.write(_escape_cdata(node.text, encoding))
##                         if node.text.endswith(os.linesep):
                        filled = True
                    else:
                        file.write(_escape_cdata(node.text, encoding))
                for n in node:
                    self._write_fmt(file, n, encoding, namespaces,
                                    level + 1, indent)
                if node:
                    file.write(indstr) # indent
                elif filled:
                    pass # file.write(indstr[1:]) # indent
                file.write("</" + tag + ">")
            else:
                file.write(" />")
            for k, v in xmlns_items:
                del namespaces[v]
        if node.tail:
            file.write(_escape_cdata(node.tail, encoding))

    ElementTree.ElementTree.write_fmt = write_fmt
    ElementTree.ElementTree._write_fmt = _write_fmt
