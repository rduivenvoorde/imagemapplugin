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
"""
import os
import platform

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from imagemapplugingui import ImageMapPluginGui

# initialize Qt resources from file
import imagemapplugin_rc


class ImageMapPlugin:

  MSG_BOX_TITLE = "QGis Html Image Map Plugin "

  def __init__(self, iface):
    # save reference to the QGIS interface
    self.iface = iface
    self.filesPath = "/tmp/foo"

  def initGui(self):
    # create action that will start plugin configuration
    self.action = QAction(QIcon(":/imagemapicon.xpm"), "Image Map", self.iface.mainWindow())
    self.action.setWhatsThis("Configuration for Image Map plugin")
    QObject.connect(self.action, SIGNAL("triggered()"), self.run)
    # add toolbar button and menu item
    self.iface.addToolBarIcon(self.action)
    if hasattr ( self.iface, "addPluginToWebMenu" ):
        self.iface.addPluginToWebMenu("&Html Image Map Plugin", self.action)
    else:
        self.iface.addPluginToMenu("&Html Image Map Plugin", self.action)

    #self.iface.pluginMenu().insertAction(self.action)
    # connect to signal renderComplete which is emitted when canvas rendering is done
    QObject.connect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), self.renderTest)

  def unload(self):
    # remove the plugin menu item and icon
    if hasattr ( self.iface, "addPluginToWebMenu" ):
        self.iface.removePluginWebMenu("&Html Image Map Plugin",self.action)
    else:
        self.iface.removePluginMenu("&Html Image Map Plugin",self.action)
    self.iface.removeToolBarIcon(self.action)
    # disconnect form signal of the canvas
    QObject.disconnect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), self.renderTest)

  def run(self):
    # check if current active layer is a polygon layer:
    layer =  self.iface.activeLayer()
    if layer == None:
        QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("No active layer found\n" "Please make one (multi)polygon or point layer active\n" "by choosing a layer in the legend"), QMessageBox.Ok, QMessageBox.Ok)
        return
    # don't know if this is possible / needed
    if not layer.isValid():
        QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("No VALID layer found\n" "Please make one (multi)polygon or point layer active\n" "by choosing a layer in the legend"), QMessageBox.Ok, QMessageBox.Ok)
        return
    if (layer.type()>0): # 0 = vector, 1 = raster
        QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("Wrong layer type, only vector layers can be used..\n" "Please make one vector layer active\n" "by choosing a vector layer in the legend"), QMessageBox.Ok, QMessageBox.Ok)
        return
    self.provider = layer.dataProvider()
    if not(self.provider.geometryType() == QGis.WKBPolygon or self.provider.geometryType() == QGis.WKBMultiPolygon or self.provider.geometryType() == QGis.WKBPoint):
        QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("Wrong geometrytype, only (multi)polygons and points can be used.\n" "Please make one (multi)polygon or point layer active\n" "by choosing a layer in the legend"), QMessageBox.Ok, QMessageBox.Ok)
        return

    # we need the fields of the active layer to show in the attribute combobox in the gui:
    attrFields = []

    fields = self.provider.fields()
    if hasattr(fields, 'iteritems'):
      for (i, field) in fields.iteritems():
        attrFields.append(field.name().trimmed())
    else:
        for field in self.provider.fields():
          attrFields.append(field.name().trimmed())

    # construct gui (using these fields)
    flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMaximizeButtonHint  # QgisGui.ModalDialogFlags
    # construct gui: if available reuse this one
    if hasattr(self, 'imageMapPlugin') == False:
        self.imageMapPluginGui = ImageMapPluginGui(self.iface.mainWindow(), flags)
    self.imageMapPluginGui.setAttributeFields(attrFields)
    self.imageMapPluginGui.setMapCanvasSize(self.iface.mapCanvas().width(), self.iface.mapCanvas().height())
    self.layerAttr = attrFields
    self.selectedFeaturesOnly = False # default all features in current Extent
    # catch SIGNAL's
    QObject.connect(self.imageMapPluginGui, SIGNAL("getFilesPath(QString)"), self.setFilesPath)
    QObject.connect(self.imageMapPluginGui, SIGNAL("onHrefAttributeSet(QString)"), self.onHrefAttributeFieldSet)
    QObject.connect(self.imageMapPluginGui, SIGNAL("onClickAttributeSet(QString)"), self.onClickAttributeFieldSet)
    QObject.connect(self.imageMapPluginGui, SIGNAL("onMouseOverAttributeSet(QString)"), self.onMouseOverAttributeFieldSet)
    QObject.connect(self.imageMapPluginGui, SIGNAL("onMouseOutAttributeSet(QString)"), self.onMouseOutAttributeFieldSet)
    QObject.connect(self.imageMapPluginGui, SIGNAL("getCbkBoxSelectedOnly(bool)"), self.setSelectedOnly)
    QObject.connect(self.imageMapPluginGui, SIGNAL("go(QString)"), self.go)
    QObject.connect(self.imageMapPluginGui, SIGNAL("setMapCanvasSize(int, int)"), self.setMapCanvasSize)
    # remember old path's in this session:
    self.imageMapPluginGui.setFilesPath(self.filesPath)
    self.imageMapPluginGui.show()


  def writeHtml(self):
    # create a holder for retrieving features from the provider
    feature = QgsFeature();
    temp = unicode(self.filesPath+".png")
    imgfilename = os.path.basename(temp)
    html = [u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html>']
    # some rudimentary javascript to show off the mouse click and mouse over
    html.append(u'<head><title>QGIS</title><script type="text/javascript">\n')
    html.append(u'function mapOnMouseOver(str){document.getElementById("mousemovemessage").innerHTML=str; }\n')
    html.append(u'function mapOnMouseOut(str){document.getElementById("mousemovemessage").innerHTML="out of "+str; }\n')
    html.append(u'function mapOnClick(str){alert(str);}\n')
    html.append(u'</script> </head> <body>')
    html.append(u'<div id="mousemovemessage"></div><br>')
    html.append(u'<img src="' + imgfilename + '" border="0" ismap="ismap" usemap="#mapmap" alt="html imagemap created with QGIS" >\n')
    html.append(u'<map name="mapmap">\n')

    mapCanvasExtent = self.iface.mapCanvas().extent()
    doCrsTransform = False

    # in case of 'on the fly projection' 
    # AND 
    # different srs's for mapCanvas/project and layer we have to reproject stuff
    if hasattr(self.iface.mapCanvas().mapRenderer(), 'destinationSrs'):
      # QGIS < 2.0
      destinationCrs = self.iface.mapCanvas().mapRenderer().destinationSrs()
      layerCrs = self.iface.activeLayer().srs()
    else:
      destinationCrs = self.iface.mapCanvas().mapRenderer().destinationCrs()
      layerCrs = self.iface.activeLayer().crs()
    #print 'destination crs: %s:' % destinationCrs.toProj4()
    #print 'layer crs:       %s:' % layerCrs.toProj4()
    if not destinationCrs == layerCrs:
      # we have to transform the mapCanvasExtent to the data/layer Crs to be able
      # to retrieve the features from the data provider
      # but ONLY if we are working with on the fly projection
      # (because in that case we just 'fly' to the raw coordinates from data)
      if self.iface.mapCanvas().hasCrsTransformEnabled():
        crsTranform = QgsCoordinateTransform(destinationCrs, layerCrs)
        mapCanvasExtent = crsTranform.transformBoundingBox(mapCanvasExtent)
        # we have to have a transformer to do the transformation of the geometries
        # to the mapcanvas srs ourselves:
        crsTranform = QgsCoordinateTransform(layerCrs, destinationCrs)
        doCrsTransform = True
    # now iterate through each feature
    # select features within current extent,
    # set max progress bar to number of features (not very accurate with a lot of huge multipolygons)
    #self.imageMapPluginGui.setProgressBarMax(self.iface.activeLayer().featureCount())
    # or run over all features in current selection, just to determine the number of... (should be simpler ...)
    count = 0
    #   with  ALL attributes, WITHIN extent, WITH geom, AND using Intersect instead of bbox
    if hasattr(self.provider, 'select'):
        self.provider.select(self.provider.attributeIndexes(), mapCanvasExtent, True, True)
        while self.provider.nextFeature(feature):
            count = count + 1
    else:
        request = QgsFeatureRequest().setFilterRect(mapCanvasExtent)
        for feature in self.iface.activeLayer().getFeatures(request):
            count = count + 1
    self.imageMapPluginGui.setProgressBarMax(count)
    progressValue = 0
    # in case of points / lines we need to buffer geometries, calculate bufferdistance here
    bufferDistance = self.iface.mapCanvas().mapUnitsPerPixel()*10 #(plusminus 20pixel areas)

    # get a list of all selected features ids
    selectedFeaturesIds = self.iface.activeLayer().selectedFeaturesIds()
    # it seems that a postgres provider is on the end of file now
    # we do the select again to set the pointer/cursor to 0 again ?
    if hasattr(self.provider, 'select'):
        self.provider.select(self.provider.attributeIndexes(), mapCanvasExtent, True, True)
        while self.provider.nextFeature(feature):
            html.extend( self.handleGeom(feature, selectedFeaturesIds, doCrsTransform, bufferDistance) )
            progressValue = progressValue+1
            self.imageMapPluginGui.setProgressBarValue(progressValue)
    else:   # QGIS >= 2.0
        for feature in self.iface.activeLayer().getFeatures(request):
            html.extend( self.handleGeom(feature, selectedFeaturesIds, doCrsTransform, bufferDistance) )
            progressValue = progressValue+1
            self.imageMapPluginGui.setProgressBarValue(progressValue)
    html.append(u'</map></body></html>')
    return html

  def handleGeom(self, feature, selectedFeaturesIds, doCrsTransform, bufferDistance):
    html = []
    # if checkbox 'selectedFeaturesOnly' is checked: check if this feature is selected
    if self.selectedFeaturesOnly and feature.id() not in selectedFeaturesIds:
        # print "skipping %s " % feature.id()
        None
    else:
        geom = feature.geometry()
        if hasattr(self.iface.activeLayer(), "srs"):
            # QGIS < 2.0
            layerCrs = self.iface.activeLayer().srs()
        else:
            layerCrs = self.iface.activeLayer().crs()
        if doCrsTransform:
            if hasattr(geom, "transform"):
                geom.transform(crsTranform)
            else:
                QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("Cannot crs-transform geometry in your QGIS version ...\n" "Only QGIS version 1.5 and above can transform geometries on the fly\n" "As a workaround, you can try to save the layer in the destination crs (eg as shapefile) and reload that layer...\n"), QMessageBox.Ok, QMessageBox.Ok)
                #break
                raise Exception("Cannot crs-transform geometry in your QGIS version ...\n" "Only QGIS version 1.5 and above can transform geometries on the fly\n" "As a workaround, you can try to save the layer in the destination crs (eg as shapefile) and reload that layer...\n")
        projectExtent = self.iface.mapCanvas().extent()
        projectExtentAsPolygon = QgsGeometry()
        projectExtentAsPolygon = QgsGeometry.fromRect(projectExtent)
        #print "GeomType: %s" % geom.wkbType()
        if geom.wkbType() == QGis.WKBPoint: # 1 = WKBPoint
            # we make a copy of the geom, because apparently buffering the orignal will
            # only buffer the source-coordinates 
            geomCopy = QgsGeometry.fromPoint(geom.asPoint())
            polygon = geomCopy.buffer(bufferDistance, 0).asPolygon()
            #print "BufferedPoint: %s" % polygon
            for ring in polygon:
                h = self.ring2area(feature, ring, projectExtent, projectExtentAsPolygon)
                html.append(h)
        if geom.wkbType() == QGis.WKBPolygon: # 3 = WKBTYPE.WKBPolygon:
            polygon = geom.asPolygon()  # returns a list
            for ring in polygon:
                h = self.ring2area(feature, ring, projectExtent, projectExtentAsPolygon)
                html.append(h)
        if geom.wkbType() == QGis.WKBMultiPolygon: # 6 = WKBTYPE.WKBMultiPolygon:
            multipolygon = geom.asMultiPolygon() # returns a list
            for polygon in multipolygon:
                for ring in polygon:
                    h = self.ring2area(feature, ring, projectExtent, projectExtentAsPolygon)
                    html.append(h)
    return html

  def renderTest(self, painter):
    # Get canvas dimensions
    self.canvaswidth = painter.device().width()
    self.canvasheight = painter.device().height()

  def setFilesPath(self, filesPathQString):
    self.filesPath = filesPathQString

  def onHrefAttributeFieldSet(self, attributeFieldQstring):
    self.hrefAttributeField = attributeFieldQstring
    self.hrefAttributeIndex = self.provider.fieldNameIndex(attributeFieldQstring)

  def onClickAttributeFieldSet(self, attributeFieldQstring):
    self.onClickAttributeField = attributeFieldQstring
    self.onClickAttributeIndex = self.provider.fieldNameIndex(attributeFieldQstring)

  def onMouseOverAttributeFieldSet(self, attributeFieldQstring):
    self.onMouseOverAttributeField = attributeFieldQstring
    self.onMouseOverAttributeIndex = self.provider.fieldNameIndex(attributeFieldQstring)

  def onMouseOutAttributeFieldSet(self, attributeFieldQstring):
    self.onMouseOutAttributeField = attributeFieldQstring
    self.onMouseOutAttributeIndex = self.provider.fieldNameIndex(attributeFieldQstring)

  def setSelectedOnly(self, selectedOnlyBool):
    #print "selectedFeaturesOnly: %s" % selectedOnlyBool
    self.selectedFeaturesOnly = selectedOnlyBool

  def setMapCanvasSize(self, newWidth, newHeight):
    mapCanvas=self.iface.mapCanvas()
    parent=mapCanvas.parentWidget()
    # some QT magic for me, coming from maximized force a minimal layout change first
    if(parent.isMaximized()):
      QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("Maximized QGIS window..\n" "QGIS window is maximized, plugin will try to de-maximize the window.\n" "If image size is still not exact what you asked for,\ntry starting plugin with non maximized window."), QMessageBox.Ok, QMessageBox.Ok)
      parent.showNormal()
    # on diffent OS's there seems to be different offsets to be taken into account
    magic=0
    if platform.system() == "Linux":
      magic=2
    elif platform.system() == "Windows":
      magic=4
    newWidth=newWidth+magic
    newHeight=newHeight+magic
    diffWidth=mapCanvas.size().width()-newWidth
    diffHeight=mapCanvas.size().height()-newHeight
    mapCanvas.resize(newWidth, newHeight)
    parent.resize(parent.size().width()-diffWidth, parent.size().height()-diffHeight)
    # HACK: there are cases where after maximising and here demaximizing the size of the parent is not
    # in sync with the actual size, giving a small error in the size setting
    # we do the resizing again, this fixes this small error then ....
    if newWidth <> mapCanvas.size().width() or newHeight <> mapCanvas.size().height():
      diffWidth=mapCanvas.size().width()-newWidth
      diffHeight=mapCanvas.size().height()-newHeight
      mapCanvas.resize(newWidth, newHeight)
      parent.resize(parent.size().width()-diffWidth, parent.size().height()-diffHeight)

  def go(self, foo):
    htmlfilename = unicode(self.filesPath + ".html")
    imgfilename = unicode(self.filesPath + ".png")
    # check if path is writable: ?? TODO
    #if not os.access(htmlfilename, os._OK):
    #  QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("Unable to write file with this name.\n" "Please choose a valid filename and a writable directory."))
    #  return
    # check if file(s) excist:
    if os.path.isfile(htmlfilename) or os.path.isfile(imgfilename):
        if QMessageBox.question(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("There is already a filename with this name.\n" "Continue?"), QMessageBox.Cancel, QMessageBox.Ok) <> QMessageBox.Ok:
            return
    # else: everthing ok: start writing img and html
    try:
        if len(self.filesPath)==0:
            raise IOError
        file = open(htmlfilename, "w")
        html = self.writeHtml()
        for line in html:
          file.write(line.encode('utf-8'))
        file.close()
        self.iface.mapCanvas().saveAsImage(imgfilename)
        msg = "Files successfully saved to:\n" + self.filesPath
        QMessageBox.information(self.iface.mainWindow(), self.MSG_BOX_TITLE, ( msg ), QMessageBox.Ok)
        self.imageMapPluginGui.hide()
    except IOError:
        QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, ("No valid path or filename.\n" "Please give or browse a valid filename."), QMessageBox.Ok, QMessageBox.Ok)


  # NOT WORKING ????
  # pixpoint = m2p.transform(point.x(), point.y())
  # print m2p.transform(point.x(), point.y())
  # so for now: a custom 'world2pixel' method
  def w2p(self, x, y, mupp, minx, maxy):
    pixX = (x - minx)/mupp
    pixY = (y - maxy)/mupp
    return [int(pixX), int(-pixY)]

  # for given ring in feature, IF al least on point on ring is in mapCanvasExtent
  # generate a string like:
  # <area shape=polygon href='xxx' onClick="mapOnClick('yyy')" onMouseOver="mapOnMouseOver('zzz')  coords=519,-52,519,..,-52,519,-52>
  def ring2area(self, feature, ring, extent, extentAsPoly):
    param = u''
    htm = u'<area shape="poly" '
    if hasattr(feature, 'attributeMap'):
        attrs = feature.attributeMap()
    else:
        # QGIS > 2.0
        attrs = feature
    # escape ' and " because they will collapse as javascript parameter
    if self.imageMapPluginGui.isHrefChecked():
        htm = htm + 'href="' + attrs[self.hrefAttributeIndex].toString() + '" '
    if self.imageMapPluginGui.isOnClickChecked():
        param = attrs[self.onClickAttributeIndex].toString()
        htm = htm + 'onClick="mapOnClick(\'' + self.jsEscapeString(param) + '\')" '
    if self.imageMapPluginGui.isOnMouseOverChecked():
        param = attrs[self.onMouseOverAttributeIndex].toString()
        htm = htm + 'onMouseOver="mapOnMouseOver(\'' + self.jsEscapeString(param) + '\')" '
    if self.imageMapPluginGui.isOnMouseOutChecked():
        param = attrs[self.onMouseOutAttributeIndex].toString()
        htm = htm + 'onMouseOut="mapOnMouseOut(\'' + self.jsEscapeString(param) + '\')" '
    htm = htm + ' coords="'
    lastPixel=[0,0]
    insideExtent = False
    coordCount = 0
    extentAsPoly = QgsGeometry()
    extentAsPoly = QgsGeometry.fromRect(extent)
    for point in ring:
        if extentAsPoly.contains(point):
            insideExtent = True
        pixpoint =  self.w2p(point.x(), point.y(), 
                self.iface.mapCanvas().mapUnitsPerPixel(),
                extent.xMinimum(), extent.yMaximum())
        if lastPixel<>pixpoint:
            coordCount = coordCount +1
            htm += (str(pixpoint[0]) + ',' + str(pixpoint[1]) + ',')
            lastPixel = pixpoint
    htm = htm[0:-1]
    # check if there are more then 2 coords: very small polygons on current map can have coordinates
    # which if rounded to pixels all come to the same pixel, resulting in just ONE x,y coordinate
    # we skip these
    if coordCount < 2:
        #print "Ring contains just one pixel coordinate pair: skipping"
        return ''
    # if at least ONE pixel of this ring is in current view extent, return the area-string, otherwise return an empty string
    if not insideExtent:
        #print "RING FULLY OUTSIDE EXTENT: %s " % ring
        return ''
    else:
        # using last param as alt parameter (to be W3 compliant we need one)
        htm += '" alt="' + param + '">\n'
        return unicode(htm)


  # escape ' and " so string can be safely used as string javascript argument
  def jsEscapeString(self, str):
    return unicode(str.replace("'", "\\'").replace('"', '\"'))
