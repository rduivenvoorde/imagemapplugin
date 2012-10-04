
# install directory
#INST_DIR = /home/richard/temp/plugin
INST_DIR = ~/.qgis/python/plugins/imagemap_plugin

# python qt4 binaries
PYRCC = /usr/bin/pyrcc4
PYUIC = /usr/bin/pyuic4

# qt-ui input and py-output file
# input (file is output of Qt-Designer)
UI_UI_FILE = src/imagemapplugingui.ui
# output
UI_PY_FILE = src/ui_imagemapplugingui.py

# resouce input and output file
# input
RC_QRC_FILE = src/imagemapplugin.qrc
# output
RC_PY_FILE = src/imagemapplugin_rc.py




# 'compile' all ui and resource files
all: $(RC_PY_FILE) $(UI_PY_FILE)
# compile resource to resource python file (depends on the qrc file)
$(RC_PY_FILE): $(RC_QRC_FILE)
	$(PYRCC) -o $(RC_PY_FILE) $(RC_QRC_FILE)
# compile the qt4-ui file to the ui python file
$(UI_PY_FILE): $(UI-UI_FILE)
	$(PYUIC) -o $(UI_PY_FILE) $(UI_UI_FILE)


dist: cleandist
	mkdir -p dist/imagemap_plugin/doc
	cp src/*.* dist/imagemap_plugin
	cp src/doc/*.* dist/imagemap_plugin/doc/
	rm -f bin/imagemap_plugin.zip
	cd dist; zip -9rv ../bin/imagemap_plugin.zip  imagemap_plugin

cleandist:
	rm -rf dist

# install (depends on 'all')
install: all
	mkdir -p $(INST_DIR)/doc
	cp src/*.py $(INST_DIR)/
	cp -r src/doc/* $(INST_DIR)/doc/
	#qgis /home/richard/dev/qgis/world.qgs &
	/home/richard/apps/qgis/trunk/bin/qgis /home/richard/geodata/nl/prov.qgs
	#/home/richard/apps/qgis/trunk/bin/qgis #/home/richard/geodata/prov.qgs &


clean:
	killall qgis
	rm -f $(RC_PY_FILE) $(UI_PY_FILE)
	rm -f src/*.pyc
	# clean up install directory
	rm -rf $(INST_DIR)

