
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import os.path

from qgis.core import QgsContextHelp

from ui_imagemapplugingui import Ui_ImageMapPluginGui

import imagemapplugin_rc


class ImageMapPluginGui(QDialog, Ui_ImageMapPluginGui):

  PATH_STRING = "Path and file name (without extension)"
  MSG_BOX_TITLE = "QGis Html Image Map Plugin"

  def __init__(self, parent, fl):
    QDialog.__init__(self, parent, fl)
    self.setupUi(self)


  def on_buttonBox_accepted(self):
    # check to see if at least one of the attr checkboxes are checked
    if (not self.chkBoxHref.isChecked()) and (not self.chkBoxOnClick.isChecked()) and (not self.chkBoxOnMouseOver.isChecked()):
      QMessageBox.warning(self, self.MSG_BOX_TITLE, ("Not one attr checkbox checked?\n" "Please choose at least one attribute to use in AREA tags."), QMessageBox.Ok)
      return
    self.emit(SIGNAL("getFilesPath(QString)"), self.txtFileName.text() )
    self.emit(SIGNAL("onHrefAttributeSet(QString)"), self.cmbAttributesHref.currentText() )
    self.emit(SIGNAL("onClickAttributeSet(QString)"), self.cmbAttributesOnClick.currentText() )
    self.emit(SIGNAL("onMouseOverAttributeSet(QString)"), self.cmbAttributesOnMouseOver.currentText() )
    self.emit(SIGNAL("onMouseOutAttributeSet(QString)"), self.cmbAttributesOnMouseOut.currentText() )
    # and GO
    self.emit(SIGNAL("go(QString)"), "ok" )
    #self.done(1)   

  def on_buttonBox_rejected(self):
    self.done(0)

  def on_buttonBox_helpRequested(self):
    # TODO make help resources ?
    # QgsContextHelp.run(32338213)
    docFile = os.path.join(os.path.dirname(__file__), "doc","index.html")
    QDesktopServices.openUrl( QUrl("file:" + docFile) )


  def on_chkBoxSelectedOnly_stateChanged(self):
    self.emit(SIGNAL("getCbkBoxSelectedOnly(bool)"), self.chkBoxSelectedOnly.isChecked() )

  def on_chkBoxHref_stateChanged(self):
    self.cmbAttributesHref.setEnabled(self.chkBoxHref.isChecked())

  def on_chkBoxOnClick_stateChanged(self):
    self.cmbAttributesOnClick.setEnabled(self.chkBoxOnClick.isChecked())

  def on_chkBoxOnMouseOver_stateChanged(self):
    self.cmbAttributesOnMouseOver.setEnabled(self.chkBoxOnMouseOver.isChecked())

  def on_chkBoxOnMouseOut_stateChanged(self):
    self.cmbAttributesOnMouseOut.setEnabled(self.chkBoxOnMouseOut.isChecked())

  # if the text in this field is stil beginning with: 'full path and name'
  def on_txtFileName_cursorPositionChanged(self, old, new):
    if self.txtFileName.text().startswith(self.PATH_STRING):  # text() returns QString => startsWith instead startswith
        self.txtFileName.setText('')

  # see http://www.riverbankcomputing.com/Docs/PyQt4/pyqt4ref.html#connecting-signals-and-slots
  # without this magic, the on_btnOk_clicked will be called two times: one clicked() and one clicked(bool checked)
  @pyqtSignature("on_btnBrowse_clicked()")
  def on_btnBrowse_clicked(self):
    fileName = QFileDialog.getSaveFileName(self, self.PATH_STRING, "/", "")
    # TODO do some checks to be sure there is no extension
    self.txtFileName.setText(fileName)

  @pyqtSignature("on_btnSetImageSize_clicked()")
  def on_btnSetImageSize_clicked(self):
    self.emit(SIGNAL("setMapCanvasSize(int, int)"), self.spinBoxImageWidth.value(), self.spinBoxImageHeight.value() )

  def setFilesPath(self, path):
    self.txtFileName.setText(path)

  def setAttributeFields(self, layerAttr):
    # populate comboboxes with attribute field names of active layer
    self.cmbAttributesHref.addItems(layerAttr)
    self.cmbAttributesOnClick.addItems(layerAttr)
    self.cmbAttributesOnMouseOver.addItems(layerAttr)
    self.cmbAttributesOnMouseOut.addItems(layerAttr)

  def setProgressBarMax(self, maxInt):
    # minimum default to zero
    self.progressBar.setMinimum(0)
    self.progressBar.setMaximum(maxInt)

  def setMapCanvasSize(self, width, height):
    self.spinBoxImageWidth.setValue(width)
    self.spinBoxImageHeight.setValue(height)

  def setProgressBarValue(self, valInt):
    self.progressBar.setValue(valInt)

  def isHrefChecked(self):
    return self.chkBoxHref.isChecked()

  def isOnClickChecked(self):
    return self.chkBoxOnClick.isChecked()

  def isOnMouseOverChecked(self):
    return self.chkBoxOnMouseOver.isChecked()
  
  def isOnMouseOutChecked(self):
    return self.chkBoxOnMouseOut.isChecked()
