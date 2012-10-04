
# for initing the ImageMapPlug as plugin in Qgis

from imagemapplugin import ImageMapPlugin

def name():
    return "Html Image Map Plugin"

def description():
    return "This plugin generates a HTML-image map file+img from the active point or polygon layer"


def qgisMinimumVersion():
    return "1.0"

def version():
    return "0.5.1"

def authorName():
    return "Richard Duivenvoorde"

def classFactory(iface):
    return ImageMapPlugin(iface)

