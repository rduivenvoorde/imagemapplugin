"""
/***************************************************************************
ImageMapPlugin

This plugin generates a HTML-image map file+img from the active point 
or polygon layer

copyright            : (C) 2011 by Richard Duivenvoorde
email                : richard@duif.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
from imagemapplugin import ImageMapPlugin

def name():
    return "Html Image Map Plugin"

def description():
    return "This plugin generates a HTML-image map file+img from the active point or polygon layer"

def qgisMinimumVersion():
    return "1.0"

def version():
    return "0.6.1"

def author():
    return "Richard Duivenvoorde"

def email():
    return "richard@duif.net"

def category():
  return "Web"

def classFactory(iface):
    return ImageMapPlugin(iface)

