#
# Global code for templates.
#

import time

copyrightStyle = """

HR.copystyle { background-color: black; height: 1px; width: 90%; }

.copyright-text {
    text-align: center;
    font-style: italic;
    font-size: x-small;
}

.copyright-holder {
    font-size: normal;
    font-weight: bold
}

.copyright-email {
    font-weight: bold
}

"""

copyright = """
<hr class=\"copystyle\">
<div class=\"copyright-text\">
All images and material are
<span class=\"copyright-holder\">
Copyright &copy; %d Martin Blais, Montreal, Canada.
</span>
<br>
All Rights Reserved. Images may not be used without written permission.<BR>
If you would like to license or use an image, please contact 
<span class=\"copyright-email\">
<a href=\"mailto:blais@furius.ca\">blais@furius.ca</a>
</div>

""" % time.localtime()[0]

footer = copyright
footerStyle = copyrightStyle

