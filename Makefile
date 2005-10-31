#
# Makefile for curator
#
# This doesn't need anything except installation tasks as the package
# currently consists of only a python script and manpage.
#
# We may later include some themes within the same package, at which
# time we'll add to the Makefile to handle it.
#
#
# Makefile created on 2001-12-31 by Dave Baker <dsb3@debian.org> as part
# of the Debian packaging.
#

# DESTDIR allows package building in non-root location 
DESTDIR=	/
prefix=		${DESTDIR}/usr
install=	/usr/bin/install -c


all: curator


clean:
	rm -f *~ curator.1

install:	install-man
	$(install) -d ${prefix}/bin
	$(install) -m 755 curator ${prefix}/bin

install-man:
	$(install) -d ${prefix}/share/man/man1
	$(install) -m 644 curator.1 ${prefix}/share/man/man1

