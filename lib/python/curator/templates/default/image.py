from curator.utils import rel
###from htmlout import *
import pprint

image, dir, css = None, None, None

#
# template code for image.
#
def title( el ):
    el.text = image.fullfn

def link_css( el ):
    print css, cwd
    el.attrib['href'] = rel(css, cwd)

def left_url( el ):
    el.attrib['href'] = 'left_url_replaced.html'

def right_url( el ):
    el.attrib['href'] = 'right_url_replaced.html'
    
def navmap( el ):
    w, h = image.size
    w4, h4 = w/4, h/4
    mapp = MAP(id="navmap")
    if image.prev:
        mapp.append(
            AREA(shape="rect", coords=','.join(map(str, [0,0,w4,h])),
                 href=rel(image.prev.html, cwd), alt="previous")
            )
    if image.next:
        mapp.append(
            AREA(shape="rect", coords=','.join(map(str, [3*w4,0,w,h])),
                 href=rel(image.next.html, cwd), alt="next")
            )
    return mapp

##   <map id="navmap" r:id="navmap">
##     <area shape="rect" coords="0,0,192,576" 
## 	  href="previous.html" alt="previous"/>
##     <area shape="rect" coords="576,0,768,576" 
## 	  href="next.html" alt="next"/>
##     <area shape="rect" coords="192,0,576,57" 
## 	  href="dirindex.html" alt=""/>
##   </map>
