#!/usr/bin/env python
#puddletag.py

#Copyright (C) 2008-2009 concentricpuddle

#This file is part of puddletag, a semi-good music tag editor.

#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys
from PyQt4.QtGui import QApplication, QPixmap, QSplashScreen

from puddlestuff import resource
from puddlestuff.puddletag import MainWin
__version__ = "0.5.9"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    filename = sys.argv[1:]
    app.setOrganizationName("Puddle Inc.")
    app.setApplicationName("puddletag")

    pixmap = QPixmap(':/puddlelogo.png')
    splash = QSplashScreen(pixmap)
    splash.show()
    QApplication.processEvents()

    qb = MainWin()
    qb.rowEmpty()
    splash.finish(qb)
    if filename:
        qb.openFolder(filename)
    qb.show()
    app.exec_()
