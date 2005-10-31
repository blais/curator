#
# Global code for templates.
#

import time

copyright = """
<HR NOSHADE SIZE=2 WIDTH=90%%>
<CENTER><I><FONT SIZE=-2>
All images and material are
</FONT><FONT SIZE=-1>
<B>Copyright &copy; %d Martin Blais, Montreal, Canada.<BR></B>
</FONT><FONT SIZE=-2>
All Rights Reserved. Images may not be used without written permission.<BR>
If you would like to license or use an image, please contact 
<B><A HREF=\"mailto:blais@iro.umontreal.ca\">blais@iro.umontreal.ca</A></B>
</FONT></I></CENTER>
""" % time.localtime()[0]

# curator_plug = """
# <CENTER><I><FONT SIZE=-2>
# This page was generated using
# <A HREF="http://curator.sourceforge.net">Curator</A>.
# </FONT></I></CENTER>
# """

# footer = copyright + "\n<P>\n\n" + curator_plug
footer = copyright

