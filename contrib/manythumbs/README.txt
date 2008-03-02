Date  	Sun, 2 Mar 2008 12:19 PM  ( 23 mins 14 secs ago ) 	Text view
Print view
Raw view
From  	"Tamás Gulácsi" <gt-dev@gthomas.homelinux.org> [Add]
To  	blais@furius.ca
Subject  	curator 	Show full header
Hi Martin,

I don't know whether you care about curator or not (it seems a little
bit "abandoned"). The attached version allows you to have any number of
thumbnails (I use it for a small (150) and a medium (800) size - because
my pictures are huge (6Mpixel), and I don't want to resize them).
The implemented template modification uses only this two "step" (the
image page includes the middle size thumbnail, and the image map's
centre points to the original image).

One other modification (not as throghout: a THUMBDIR global variable
(should be an opts attr)) makes the program store the thumbnails in a
separate (per-directory) directory (in the example .thumbnails).

Hope you can use this.

Tamás Gulácsi 
