# -*- coding: utf-8 -*-
import os
from cc3d import CompuCellSetup
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cc3d.player5.Configuration as Configuration
from cc3d.player5.styles import tab_bar_style
from .ConfigurationPageBase import ConfigurationPageBase
from . import ui_configurationdlg  # the file generated by 'pyuic4' using the .ui Designer file
from cc3d.player5.Utilities.utils import assign_cell_type_colors

import subprocess
import tempfile

MAC = "qt_mac_set_native_menubar" in dir()

MODULENAME = '------- ConfigurationDialog.py: '


class ConfigurationDialog(QDialog, ui_configurationdlg.Ui_CC3DPrefs, ConfigurationPageBase):

    def __init__(self, parent=None, name=None, modal=False):
        QDialog.__init__(self, parent)
        self.setModal(modal)

        # dict for ALL parameters on CC3D Preferences dialog
        self.paramCC3D = {}

        # read params from QSession file
        self.initParams()

        # in ui_configurationdlg.Ui_CC3DPrefs
        self.setupUi(self)

        # for now, let's disable these guys until we want to handle them.
        # But can still do: compucell3d.sh --prefs=myprefs
        # self.prefsFileLineEdit.setEnabled(False)
        # self.prefsFileButton.setEnabled(False)

        #        if not MAC:
        #            self.cancelButton.setFocusPolicy(Qt.NoFocus)

        self.tabWidget.currentChanged.connect(self.currentTabChanged)
        comma_separated_list_validator = QRegExpValidator(QRegExp('(\d+)(,\d+)*'))


        # Output tab
        self.outputImagesCheckBox.clicked.connect(self.outputImagesClicked)
        self.outputLatticeDataCheckBox.clicked.connect(self.outputLatticeDataClicked)
        self.outputToProjectCheckBox.clicked.connect(self.outputToProjectClicked)
        self.pause_at_LE.setValidator(comma_separated_list_validator)

        # Movie tab
        self.createMovieButton.clicked.connect(self.createMovieButtonClicked)

        # Cell Type/Colors tab
        self.typeColorTable.clicked.connect(self.typeColorTableClicked)

        self.cellBorderColorButton.clicked.connect(self.cellBorderColorClicked)
        self.clusterBorderColorButton.clicked.connect(self.clusterBorderColorClicked)
        self.contourColorButton.clicked.connect(self.contourColorClicked)
        self.windowColorButton.clicked.connect(self.windowColorClicked)
        self.windowColorButton.clicked.connect(self.windowColorClicked)
        self.fppColorButton.clicked.connect(self.fppColorButtonClicked)

        cell_glyph_scale_valid = QDoubleValidator(self.cellGlyphScale)
        self.cellGlyphScale.setValidator(cell_glyph_scale_valid)

        # The following will constrain the input to be valid (double) numeric values
        self.fieldComboBox.currentIndexChanged.connect(self.fieldComboBoxClicked)
        self.lastSelectedField = -1

        field_min_valid = QDoubleValidator(self.fieldMinRange)
        self.fieldMinRange.setValidator(field_min_valid)
        field_max_valid = QDoubleValidator(self.fieldMaxRange)
        self.fieldMaxRange.setValidator(field_max_valid)

        self.fieldMinRangeFixedCheckBox.clicked.connect(self.fieldMinRangeClicked)
        self.fieldMaxRangeFixedCheckBox.clicked.connect(self.fieldMaxRangeClicked)

        self.cellTypesInvisibleList.setValidator(comma_separated_list_validator)

        self.vectorsArrowColorCheckBox.clicked.connect(self.vectorsArrowColorClicked)
        self.vectorsArrowColorButton.clicked.connect(self.vectorsArrowColorButtonClicked)

        self.isovalList.textEdited.connect(self.isovalListChanged)
        self.numberOfContoursLinesSpinBox.valueChanged.connect(self.numContoursInRangeChanged)

        self.windowColorSameAsMediumCB.toggled.connect(self.windowColorSameAsMediumToggled)

        # 3D tab
        self.boundingBoxColorButton.clicked.connect(self.boundingBoxColorClicked)

        # self.axes3DBoxColorButton.clicked.connect(self.axes3DBoxColorClicked)

        self.axesColorButton.clicked.connect(self.axesColorClicked)

        self.buttonBox.clicked.connect(self.buttonBoxClicked)

        self.updateUI()

    # ----------- following methods are callbacks from the above "connect"s  ------------
    def currentTabChanged(self):

        Configuration.setSetting("TabIndex", self.tabWidget.currentIndex())
        if self.tabWidget.currentIndex() == 2:

            if self.lastSelectedField >= 0:
                self.fieldComboBox.setCurrentIndex(self.lastSelectedField)

    # -------- Output widgets CBs
    def outputImagesClicked(self):
        if self.outputImagesCheckBox.isChecked():
            self.saveImageSpinBox.setEnabled(True)

        else:
            self.saveImageSpinBox.setEnabled(False)

    def outputLatticeDataClicked(self):
        if self.outputLatticeDataCheckBox.isChecked():
            self.saveLatticeSpinBox.setEnabled(True)

        else:
            self.saveLatticeSpinBox.setEnabled(False)

    def windowColorSameAsMediumToggled(self, _flag):
        if _flag:
            # this means windowColorSameAsMedium has been checked
            medium_color = self.paramCC3D["TypeColorMap"][0]
            self.changeButtonColor(self.windowColorButton, medium_color, "WindowColor")

    def outputToProjectClicked(self):
        if self.outputToProjectCheckBox.isChecked():
            self.outputLocationLineEdit.setEnabled(False)
            self.outputLocationButton.setEnabled(False)
        else:
            self.outputLocationLineEdit.setEnabled(True)
            self.outputLocationButton.setEnabled(True)

    # -------- Movie widgets CBs

    def createMovieButtonClicked(self):

        #TODO
        inputPath = 'C:/Users/Pete/CC3DWorkspace/cellsort_2D_cc3d_11_04_2023_19_53_54/Cell_Field_CellField_2D_XY_25'

        temp_file_path = None
        with tempfile.NamedTemporaryFile(delete=False, mode='+a', dir=inputPath) as temp_file:
            # 'delete=True' removes the temporary file when it is closed.
            # So, setting 'delete=True' ensures that the tempfile stays active long enough for FFMPEG to read it.

            for fileName in os.listdir(inputPath):
                if fileName.lower().endswith(".png"):
                    temp_file.write(f"file '{fileName}'\n")
            temp_file.close()

            frameRate = min(self.frameRateSpinBox.value(), 1);
            quality = 30

            #Number the file name so that it does not overwrite another movie
            fileNumber = 0
            outputPath = 'C:/Users/Pete/CC3DWorkspace/cellsort_2D_cc3d_11_04_2023_19_53_54/movies/'
            while os.path.exists(os.path.join(outputPath, f"movie{fileNumber}.mp4")):
                fileNumber += 1
            outputPath = os.path.join(outputPath, f"movie{fileNumber}.mp4")

            # TODO test if inputPath can contain spaces

            subprocess.run([
                "ffmpeg",
                "-n", #never overwrite a file
                "-r", str(frameRate), # output frame rate
                "-f", "concat",
                "-safe", "0",
                "-i", temp_file.name,
                "-crf", str(quality), # set quality (constant rate factor, crf): 51=worst, 0=best
                "-c:v", "libx264", # video codec: H.264
                "-pix_fmt", "yuv420p",
                outputPath
            ], cwd=inputPath)

            os.remove(temp_file.name)


    # -------- Cell Type (colors) widgets CBs
    def typeColorTableClicked(self):
        '''handles cell type color table modifications'''

        row = self.typeColorTable.currentRow()
        col = self.typeColorTable.currentColumn()

        # highlight the left column cell (cell #), not cell w/ the color
        self.typeColorTable.setCurrentCell(row, 0)
        # col 2 contains color
        item = self.typeColorTable.item(row, 2)

        keys = list(self.paramCC3D["TypeColorMap"].keys())

        cell_color = self.paramCC3D["TypeColorMap"][keys[row]]
        color = QColorDialog.getColor(cell_color)
        if color.isValid():
            self.paramCC3D["TypeColorMap"][keys[row]] = color

            item.setBackground(QBrush(color))

        if self.windowColorSameAsMediumCB.isChecked():
            # get medium color
            medium_color = self.paramCC3D["TypeColorMap"][0]
            self.changeButtonColor(self.windowColorButton, medium_color, "WindowColor")

    def changeButtonColor(self, _btn, _color, _settingName):
        """
        assigns color (_color)  to button (_btn) and changes corresponding color
        setting (setting_name). Does not shows Choose color dialog
        """

        if _color.isValid():
            size = _btn.iconSize()
            pm = QPixmap(size.width(), size.height())
            pm.fill(_color)
            _btn.setIcon(QIcon(pm))
            Configuration.setSetting(_settingName, _color)

    def updateColorButton(self, btn, name):
        """
            updates button (btn) and changes corresponding color setting (name).Shows Choose color dialog
        """
        color = self.selectColor(btn, Configuration.getSetting(name))

        # which of the following is necessary at this point?
        Configuration.setSetting(name, color)
        self.paramCC3D[name] = color

    def cellBorderColorClicked(self):

        self.updateColorButton(self.cellBorderColorButton, "BorderColor")

    def clusterBorderColorClicked(self):

        self.updateColorButton(self.clusterBorderColorButton, "ClusterBorderColor")

    def contourColorClicked(self):

        self.updateColorButton(self.contourColorButton, "ContourColor")

    def windowColorClicked(self):
        self.updateColorButton(self.windowColorButton, "WindowColor")

    def fppColorButtonClicked(self):
        self.updateColorButton(self.fppColorButton, "FPPLinksColor")

    def boundingBoxColorClicked(self):
        self.updateColorButton(self.boundingBoxColorButton, "BoundingBoxColor")

    def axesColorClicked(self):
        self.updateColorButton(self.axesColorButton, "AxesColor")

    # -------- Field widgets CBs  (was both Colormap and Vector tabs, now combined in Field tab)
    def fieldComboBoxClicked(self):
        fname = self.fieldComboBox.currentText()

        field_index = self.fieldComboBox.currentIndex()
        Configuration.setSetting("FieldIndex", field_index)
        self.lastSelectedField = field_index

        # allFieldsDict = Configuration.getSimFieldsParams()
        all_fields_dict = Configuration.getSetting('FieldParams')

        key1 = list(all_fields_dict.keys())[0]

        if isinstance(key1, str):
            field_params = all_fields_dict[str(fname)]
        else:
            field_params = all_fields_dict[fname]

        if not isinstance(field_params, dict):

            field_params_dict = field_params.toMap()
        else:

            field_params_dict = field_params

        try:  # in case ShowPlotAxes is not defined in a dictinary for this plot
            val = field_params_dict["ShowPlotAxes"]
        except KeyError:
            val = Configuration.getSetting('ShowPlotAxes')

        self.showPlotAxesCB.setChecked(val)

        val = field_params_dict["MinRange"]

        self.fieldMinRange.setText(str(val))
        val = field_params_dict["MinRangeFixed"]

        self.fieldMinRangeFixedCheckBox.setChecked(val)
        # enable/disable
        self.fieldMinRangeClicked()

        val = field_params_dict["MaxRange"]

        self.fieldMaxRange.setText(str(val))
        val = field_params_dict["MaxRangeFixed"]
        self.fieldMaxRangeFixedCheckBox.setChecked(val)
        # enable/disable
        self.fieldMaxRangeClicked()

        val = field_params_dict["NumberOfLegendBoxes"]

        self.fieldLegendNumLabels.setValue(val)

        val = field_params_dict["NumberAccuracy"]
        self.fieldLegendAccuracy.setValue(val)

        val = field_params_dict["LegendEnable"]
        self.fieldShowLegendCheckBox.setChecked(val)

        try:
            val = field_params_dict["OverlayVectorsOn"]
            self.vectorsOverlayCheckBox.setChecked(val)

        except KeyError:
            print(MODULENAME, '  WARNING fieldParamsDict key "OverlayVectorsOn" not defined')
            print(MODULENAME, '  fieldParamsDict=', field_params_dict)
            print('\n')

        try:
            val = field_params_dict["ScalarIsoValues"]

            if type(val) == QVariant:
                self.isovalList.setText(val.toString())
            elif type(val) == str:
                self.isovalList.setText(val)
            else:
                self.isovalList.setText(str(val))

            print('ScalarIsoValues=', val)
        except KeyError:
            print('-----------------\n')
            print(MODULENAME, '  WARNING fieldParamsDict key "ScalarIsoValues" not defined')
            print(MODULENAME, '  fieldParamsDict=', field_params_dict)
            print('\n')

        val = field_params_dict["NumberOfContourLines"]

        self.numberOfContoursLinesSpinBox.setValue(val)

        val = field_params_dict["ArrowLength"]
        self.vectorsArrowLength.setValue(int(val))
        val = field_params_dict["ScaleArrowsOn"]
        self.vectorsScaleArrowCheckBox.setChecked(val)
        val = field_params_dict["FixedArrowColorOn"]
        self.vectorsArrowColorCheckBox.setChecked(val)
        self.vectorsArrowColorClicked()  # enable/disable

        contours_on = field_params_dict["ContoursOn"]
        self.contoursShowCB.setChecked(contours_on)
        # self.isovalList.setEnabled(contoursOn)
        # self.numberOfContoursLinesSpinBox.setEnabled(contoursOn)

    def fieldMinRangeClicked(self):
        if self.fieldMinRangeFixedCheckBox.isChecked():
            self.fieldMinRange.setEnabled(True)
            self.fieldMinLabel.setEnabled(True)
        else:
            self.fieldMinRange.setEnabled(False)
            self.fieldMinLabel.setEnabled(False)

    def fieldMaxRangeClicked(self):
        if self.fieldMaxRangeFixedCheckBox.isChecked():
            self.fieldMaxRange.setEnabled(True)
            self.fieldMaxLabel.setEnabled(True)
        else:
            self.fieldMaxRange.setEnabled(False)
            self.fieldMaxLabel.setEnabled(False)

    # -------- Vectors widgets CBs
    def vectorsMinMagClicked(self):
        if self.vectorsMinMagFixedCheckBox.isChecked():
            self.vectorsMinMag.setEnabled(True)
            self.vectorsMinMagLabel.setEnabled(True)
        else:
            self.vectorsMinMag.setEnabled(False)
            self.vectorsMinMagLabel.setEnabled(False)

    def vectorsMaxMagClicked(self):
        if self.vectorsMaxMagFixedCheckBox.isChecked():
            self.vectorsMaxMag.setEnabled(True)
            self.vectorsMaxMagLabel.setEnabled(True)
        else:
            self.vectorsMaxMag.setEnabled(False)
            self.vectorsMaxMagLabel.setEnabled(False)

    def vectorsArrowColorClicked(self):
        if self.vectorsArrowColorCheckBox.isChecked():
            self.vectorsArrowColorButton.setEnabled(True)
        else:
            self.vectorsArrowColorButton.setEnabled(False)

    def vectorsArrowColorButtonClicked(self):
        self.updateColorButton(self.vectorsArrowColorButton, "ArrowColor")

    def isovalListChanged(self):
        pass

    def numContoursInRangeChanged(self):
        pass

    def buttonBoxClicked(self, btn):
        """
        handling of primary buttons (Apply/Cancel/OK) at the bottom of the Preferences dialog
        """

        if str(btn.text()) == 'Apply':
            if self.outputImagesCheckBox.isChecked() and (
                    self.saveImageSpinBox.value() < self.updateScreenSpinBox.value()):
                save_img_str = str(self.saveImageSpinBox.value())
                QMessageBox.warning(None, "WARN",
                                    "If saving images, you need to Update screen at least "
                                    "as frequently as Save image (e.g. Update screen = " + save_img_str + ')',
                                    QMessageBox.Ok)
                return
        self.updatePreferences()

    def accept(self):
        """
        Handling OK click
        """
        #        Configuration.setSetting()
        if self.outputImagesCheckBox.isChecked() and (self.saveImageSpinBox.value() < self.updateScreenSpinBox.value()):
            save_img_str = str(self.saveImageSpinBox.value())
            QMessageBox.warning(None, "WARN",
                                "If saving images, you need to Update screen at least as frequently "
                                "as Save image (e.g. Update screen = " + save_img_str + ')',
                                QMessageBox.Ok)
            return

        self.updatePreferences()
        QDialog.accept(self)

    def enableLatticeOutput(self, boolFlag):
        self.outputLatticeDataCheckBox.setEnabled(boolFlag)

    # The following "on_blah_clicked" methods magically happen when a UI button (whose name *matches* "blah") is clicked
    # @pyqtSignature("") # signature of the signal emitted by the button
    @pyqtSlot()  # signature of the signal emitted by the button
    def on_projectLocationButton_clicked(self):
        current_project_dir = Configuration.getSetting('ProjectLocation')
        dir_name = QFileDialog.getExistingDirectory(self, "Specify CC3D Project Directory", current_project_dir,
                                                   QFileDialog.ShowDirsOnly)
        dir_name = str(dir_name)
        dir_name.rstrip()
        if dir_name == "":
            return

        dir_name = os.path.abspath(dir_name)
        self.projectLocationLineEdit.setText(dir_name)
        Configuration.setSetting('ProjectLocation', dir_name)

    # signature of the signal emitted by the button
    @pyqtSlot()
    def on_outputLocationButton_clicked(self):
        current_output_dir = Configuration.getSetting('OutputLocation')
        dir_name = QFileDialog.getExistingDirectory(self, "Specify CC3D Output Directory", current_output_dir,
                                                   QFileDialog.ShowDirsOnly)
        dir_name = str(dir_name)
        dir_name.rstrip()
        print("dirName=", dir_name)
        if dir_name == "":
            return
        dir_name = os.path.abspath(dir_name)
        self.outputLocationLineEdit.setText(dir_name)
        Configuration.setSetting('OutputLocation', dir_name)

    @pyqtSlot()
    def on_addCellTypeButton_clicked(self):
        last_row_idx = self.typeColorTable.rowCount() - 1

        type_item = self.typeColorTable.item(last_row_idx, 0)
        flag = True
        try:
            last_type_number = int(type_item.text())
        except ValueError:
            flag = False
            last_type_number = 257

        if not flag:
            # conversion to integer unsuccessful
            return

        if last_type_number >= 256:
            # cc3d supports only up to 256 cell types
            return

        color_item = self.typeColorTable.item(last_row_idx, 2)  # col 2 contains color

        self.typeColorTable.insertRow(last_row_idx + 1)

        # fill new row
        self.typeColorTable.setItem(last_row_idx + 1, 0, QTableWidgetItem(str(last_type_number + 1)))
        self.typeColorTable.setItem(last_row_idx + 1, 1, QTableWidgetItem())
        self.typeColorTable.setItem(last_row_idx + 1, 2, QTableWidgetItem())
        # init setting dictionary

        self.paramCC3D["TypeColorMap"][last_row_idx + 1] = QColor(Qt.white)

    def populateCellColors(self):

        cw = self.typeColorTable.columnWidth(1)

        self.typeColorTable.setColumnWidth(1, cw * 2)

        type_id_type_name_dict = CompuCellSetup.simulation_utils.extract_type_names_and_ids()
        # type_id_to_type_name_color_map = self.assign_cell_type_colors(type_id_type_name_dict=type_id_type_name_dict)
        type_id_to_type_name_color_map = assign_cell_type_colors(type_id_type_name_dict=type_id_type_name_dict,
                                                                 setting_type_color_map=self.paramCC3D["TypeColorMap"])

        row_count = len(type_id_to_type_name_color_map)
        self.typeColorTable.setRowCount(row_count)

        for i, (type_id, type_name_color_tuple) in enumerate(type_id_to_type_name_color_map.items()):
            item = QTableWidgetItem(str(type_id))
            self.typeColorTable.setItem(i, 0, item)

            item = QTableWidgetItem()
            item.setBackground(QBrush(type_name_color_tuple.color))
            self.typeColorTable.setItem(i, 2, item)

            item = QTableWidgetItem(str(type_name_color_tuple.type_name))
            self.typeColorTable.setItem(i, 1, item)

    def updateFieldParams(self, fieldName):
        # we do not allow fields with empty name
        if str(fieldName) == '':
            return

        field_dict = {}

        key = "ShowPlotAxes"
        val = self.showPlotAxesCB.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "MinRange"
        val = self.fieldMinRange.text()

        field_dict[key] = float(val)

        Configuration.setSetting(key, val)
        key = "MinRangeFixed"
        val = self.fieldMinRangeFixedCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)
        key = "MaxRange"
        val = self.fieldMaxRange.text()

        field_dict[key] = float(val)
        Configuration.setSetting(key, val)
        key = "MaxRangeFixed"
        val = self.fieldMaxRangeFixedCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "NumberOfLegendBoxes"
        val = self.fieldLegendNumLabels.value()  # spinbox
        field_dict[key] = val
        Configuration.setSetting(key, val)
        key = "NumberAccuracy"
        val = self.fieldLegendAccuracy.value()  # spinbox
        field_dict[key] = val
        Configuration.setSetting(key, val)
        key = "LegendEnable"
        val = self.fieldShowLegendCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "OverlayVectorsOn"
        val = self.vectorsOverlayCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "ContoursOn"
        val = self.contoursShowCB.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "ScalarIsoValues"
        val = self.isovalList.text()
        field_dict[key] = val

        Configuration.setSetting(key, val)
        key = "NumberOfContourLines"
        val = self.numberOfContoursLinesSpinBox.value()
        field_dict[key] = val
        Configuration.setSetting(key, val)

        key = "ArrowLength"
        val = self.vectorsArrowLength.value()
        field_dict[key] = val
        Configuration.setSetting(key, val)
        key = "ScaleArrowsOn"
        val = self.vectorsScaleArrowCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)
        key = "FixedArrowColorOn"
        val = self.vectorsArrowColorCheckBox.isChecked()
        field_dict[key] = val
        Configuration.setSetting(key, val)
        color = Configuration.getSetting("ArrowColor")

        field_dict["ArrowColor"] = color

        Configuration.updateFieldsParams(fieldName, field_dict)

    def updatePreferences(self):
        """called when user presses Apply or OK button on the Prefs dialog"""

        # update flags in menus:  CC3DOutputOn, etc. (rf. ViewManager/SimpleViewManager)

        # Output
        Configuration.setSetting("ScreenUpdateFrequency", self.updateScreenSpinBox.value())
        Configuration.setSetting("ImageOutputOn", self.outputImagesCheckBox.isChecked())
        Configuration.setSetting("SaveImageFrequency", self.saveImageSpinBox.value())
        Configuration.setSetting("Screenshot_X", self.screenshot_X_SB.value())
        Configuration.setSetting("Screenshot_Y", self.screenshot_Y_SB.value())
        Configuration.setSetting("LatticeOutputOn", self.outputLatticeDataCheckBox.isChecked())
        Configuration.setSetting("SaveLatticeFrequency", self.saveLatticeSpinBox.value())
        Configuration.setSetting("DebugOutputPlayer", self.debugOutputPlayerCB.isChecked())
        Configuration.setSetting("UseInternalConsole", self.useInternalConsoleCheckBox.isChecked())
        Configuration.setSetting("ClosePlayerAfterSimulationDone", self.closePlayerCheckBox.isChecked())
        Configuration.setSetting("ProjectLocation", self.projectLocationLineEdit.text())
        Configuration.setSetting("OutputLocation", self.outputLocationLineEdit.text())
        Configuration.setSetting("PauseAt", self.pause_at_LE.text())
        Configuration.setSetting("LogLevel", "LOG_"+self.log_level_combo.currentText())
        Configuration.setSetting("LogToFile", self.write_log_CB.isChecked())

        #Movie settings
        Configuration.setSetting("FrameRate", self.frameRateSpinBox.value())

        if str(self.outputLocationLineEdit.text()).rstrip() == '':
            Configuration.setSetting("OutputLocation", os.path.join(os.path.expanduser('~'), 'CC3DWorkspace'))

        Configuration.setSetting("OutputToProjectOn", self.outputToProjectCheckBox.isChecked())
        Configuration.setSetting("NumberOfRecentSimulations", self.numberOfRecentSimulationsSB.value())
        Configuration.setSetting("NumberOfStepOutputs", self.numberOfStepOutputsSB.value())
        Configuration.setSetting("FloatingWindows", self.floatingWindowsCB.isChecked())

        Configuration.setSetting("WindowColorSameAsMedium", self.windowColorSameAsMediumCB.isChecked())

        # Cell Type/Colors
        Configuration.setSetting("TypeColorMap", self.paramCC3D["TypeColorMap"])  # rwh

        Configuration.setSetting("CellGlyphScaleByVolumeOn", self.cellGlyphScaleByVolumeCheckBox.isChecked())
        Configuration.setSetting("CellGlyphScale", float(self.cellGlyphScale.text()))
        # spinbox
        Configuration.setSetting("CellGlyphThetaRes", self.cellGlyphThetaRes.value())
        # spinbox
        Configuration.setSetting("CellGlyphPhiRes", self.cellGlyphPhiRes.value())

        fp = Configuration.getSetting("FieldParams")

        # get Field name from combobox in the Field tab and save the current settings for that field
        fname = self.fieldComboBox.currentText()

        # TODO change
        self.updateFieldParams(fname)

        Configuration.setSetting("PixelizedCartesianFields", self.pixelizedScalarFieldCB.isChecked())

        Configuration.setSetting("MinRange", float(self.fieldMinRange.text()))
        Configuration.setSetting("MinRangeFixed", self.fieldMinRangeFixedCheckBox.isChecked())
        Configuration.setSetting("MaxRange", float(self.fieldMaxRange.text()))
        Configuration.setSetting("MaxRangeFixed", self.fieldMaxRangeFixedCheckBox.isChecked())

        Configuration.setSetting("NumberOfLegendBoxes", self.fieldLegendNumLabels.value())  # spinbox
        Configuration.setSetting("NumberAccuracy", self.fieldLegendAccuracy.value())  # spinbox
        Configuration.setSetting("LegendEnable", self.fieldShowLegendCheckBox.isChecked())

        Configuration.setSetting("ScalarIsoValues", self.isovalList.text())
        Configuration.setSetting("NumberOfContourLines", self.numberOfContoursLinesSpinBox.value())
        Configuration.setSetting("ShowPlotAxes", self.showPlotAxesCB.isChecked())

        Configuration.setSetting("DisplayMinMaxInfo", self.min_max_display_CB.isChecked())

        # Vectors
        Configuration.setSetting("ArrowLength", self.vectorsArrowLength.value())
        Configuration.setSetting("ScaleArrowsOn", self.vectorsScaleArrowCheckBox.isChecked())
        Configuration.setSetting("FixedArrowColorOn", self.vectorsArrowColorCheckBox.isChecked())

        # 3D section
        Configuration.setSetting("Types3DInvisible", self.cellTypesInvisibleList.text())
        Configuration.setSetting("BoundingBoxOn", self.boundingBoxCheckBox.isChecked())
        Configuration.setSetting("ShowAxes", self.showAxesCB.isChecked())
        Configuration.setSetting("ShowHorizontalAxesLabels", self.showHorizontalAxesLabelsCB.isChecked())
        Configuration.setSetting("ShowVerticalAxesLabels", self.showVerticalAxesLabelsCB.isChecked())

        # restart section
        Configuration.setSetting("RestartOutputEnable", self.restart_CB.isChecked())
        Configuration.setSetting("RestartOutputFrequency", self.restart_freq_SB.value())
        Configuration.setSetting("RestartAllowMultipleSnapshots", self.multiple_restart_snapshots_CB.isChecked())

    def updateUI(self):
        """called whenever Prefs dialog is open"""

        self.tabWidget.tabBar().setStyleSheet(tab_bar_style)

        self.tabWidget.setCurrentIndex(Configuration.getSetting("TabIndex"))

        fieldIndex = Configuration.getSetting("FieldIndex")
        self.lastSelectedField = fieldIndex
        self.fieldComboBox.setCurrentIndex(self.lastSelectedField)

        # Output
        self.updateScreenSpinBox.setValue(Configuration.getSetting("ScreenUpdateFrequency"))
        #        self.updateScreenSpinBox.setMinimum(1)
        self.outputImagesCheckBox.setChecked(Configuration.getSetting("ImageOutputOn"))
        self.saveImageSpinBox.setValue(Configuration.getSetting("SaveImageFrequency"))
        self.screenshot_X_SB.setValue(Configuration.getSetting("Screenshot_X"))
        self.screenshot_Y_SB.setValue(Configuration.getSetting("Screenshot_Y"))
        self.outputImagesClicked()  # enable/disable
        #        self.saveImageSpinBox.setMinimum(1)
        self.outputLatticeDataCheckBox.setChecked(Configuration.getSetting("LatticeOutputOn"))
        self.saveLatticeSpinBox.setValue(Configuration.getSetting("SaveLatticeFrequency"))
        self.outputLatticeDataClicked()  # enable/disable

        self.debugOutputPlayerCB.setChecked(Configuration.getSetting("DebugOutputPlayer"))
        self.useInternalConsoleCheckBox.setChecked(Configuration.getSetting("UseInternalConsole"))
        self.closePlayerCheckBox.setChecked(Configuration.getSetting("ClosePlayerAfterSimulationDone"))

        self.projectLocationLineEdit.setText(str(Configuration.getSetting("ProjectLocation")))
        self.outputLocationLineEdit.setText(str(Configuration.getSetting("OutputLocation")))
        self.outputToProjectCheckBox.setChecked(Configuration.getSetting("OutputToProjectOn"))

        self.log_level_combo.setCurrentText(str(Configuration.getSetting("LogLevel"))[len("LOG_"):])
        self.write_log_CB.setChecked(Configuration.getSetting("LogToFile"))

        self.numberOfRecentSimulationsSB.setValue(Configuration.getSetting("NumberOfRecentSimulations"))
        self.numberOfStepOutputsSB.setValue(Configuration.getSetting("NumberOfStepOutputs"))
        self.floatingWindowsCB.setChecked(Configuration.getSetting("FloatingWindows"))

        self.min_max_display_CB.setChecked(Configuration.getSetting("DisplayMinMaxInfo"))
        self.pause_at_LE.setText(Configuration.getSetting("PauseAt"))

        # Movie settings
        self.frameRateSpinBox.setValue(Configuration.getSetting("FrameRate"))

        # Cell Type/Colors
        self.populateCellColors()

        color = Configuration.getSetting("BorderColor")
        size = self.cellBorderColorButton.size()

        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.cellBorderColorButton.setIconSize(pm.size())
        self.cellBorderColorButton.setIcon(QIcon(pm))

        color = Configuration.getSetting("ClusterBorderColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.clusterBorderColorButton.setIconSize(pm.size())
        self.clusterBorderColorButton.setIcon(QIcon(pm))

        color = Configuration.getSetting("ContourColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.contourColorButton.setIconSize(pm.size())
        self.contourColorButton.setIcon(QIcon(pm))

        color = Configuration.getSetting("WindowColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.windowColorButton.setIconSize(pm.size())
        self.windowColorButton.setIcon(QIcon(pm))

        color = Configuration.getSetting("FPPLinksColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.fppColorButton.setIconSize(pm.size())
        self.fppColorButton.setIcon(QIcon(pm))

        self.windowColorSameAsMediumCB.setChecked(Configuration.getSetting("WindowColorSameAsMedium"))

        self.cellGlyphScaleByVolumeCheckBox.setChecked(Configuration.getSetting("CellGlyphScaleByVolumeOn"))
        self.cellGlyphScale.setText(str(Configuration.getSetting("CellGlyphScale")))
        self.cellGlyphThetaRes.setValue(self.paramCC3D["CellGlyphThetaRes"])
        self.cellGlyphPhiRes.setValue(self.paramCC3D["CellGlyphPhiRes"])

        fp = Configuration.getSetting("FieldParams")

        self.showPlotAxesCB.setChecked(Configuration.getSetting("ShowPlotAxes"))
        self.pixelizedScalarFieldCB.setChecked(Configuration.getSetting("PixelizedCartesianFields"))

        self.fieldMinRange.setText(str(Configuration.getSetting("MinRange")))
        self.fieldMinRangeFixedCheckBox.setChecked(Configuration.getSetting("MinRangeFixed"))
        self.fieldMinRangeClicked()  # enable/disable
        self.fieldMaxRange.setText(str(Configuration.getSetting("MaxRange")))
        self.fieldMaxRangeFixedCheckBox.setChecked(Configuration.getSetting("MaxRangeFixed"))
        self.fieldMaxRangeClicked()  # enable/disable

        self.fieldLegendNumLabels.setValue(self.paramCC3D["NumberOfLegendBoxes"])
        self.fieldLegendAccuracy.setValue(self.paramCC3D["NumberAccuracy"])
        self.fieldShowLegendCheckBox.setChecked(self.paramCC3D["LegendEnable"])

        self.isovalList.setText(Configuration.getSetting("ScalarIsoValues"))
        self.numberOfContoursLinesSpinBox.setValue(self.paramCC3D["NumberOfContourLines"])

        contours_on = Configuration.getSetting("ContoursOn")
        self.contoursShowCB.setChecked(contours_on)
        self.isovalList.setEnabled(contours_on)
        self.numberOfContoursLinesSpinBox.setEnabled(contours_on)

        # Vectors
        self.vectorsArrowLength.setValue(int(self.paramCC3D["ArrowLength"]))
        self.vectorsScaleArrowCheckBox.setChecked(self.paramCC3D["ScaleArrowsOn"])
        self.vectorsArrowColorCheckBox.setChecked(self.paramCC3D["FixedArrowColorOn"])
        self.vectorsArrowColorClicked()  # enable/disable

        self.vectorsOverlayCheckBox.setChecked(self.paramCC3D["OverlayVectorsOn"])

        color = Configuration.getSetting("ArrowColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.vectorsArrowColorButton.setIconSize(pm.size())
        self.vectorsArrowColorButton.setIcon(QIcon(pm))

        # 3D
        self.cellTypesInvisibleList.setText(Configuration.getSetting("Types3DInvisible"))
        self.boundingBoxCheckBox.setChecked(self.paramCC3D["BoundingBoxOn"])

        self.showAxesCB.setChecked(Configuration.getSetting("ShowAxes"))
        self.showHorizontalAxesLabelsCB.setChecked(Configuration.getSetting("ShowHorizontalAxesLabels"))
        self.showVerticalAxesLabelsCB.setChecked(Configuration.getSetting("ShowVerticalAxesLabels"))

        color = Configuration.getSetting("BoundingBoxColor")
        pm = QPixmap(size.width(), size.height())
        pm.fill(color)
        self.boundingBoxColorButton.setIconSize(pm.size())
        self.boundingBoxColorButton.setIcon(QIcon(pm))

        color_axes = Configuration.getSetting("Axes3DColor")
        pm_axes = QPixmap(size.width(), size.height())
        pm_axes.fill(color_axes)

        # self.axes3DBoxColorButton.setIconSize(pm_axes.size())
        # self.axes3DBoxColorButton.setIcon(QIcon(pm_axes))

        color_axes = Configuration.getSetting("AxesColor")
        pm_axes = QPixmap(size.width(), size.height())
        pm_axes.fill(color_axes)

        self.axesColorButton.setIconSize(pm_axes.size())
        self.axesColorButton.setIcon(QIcon(pm_axes))

        # restart section
        enable_restart = Configuration.getSetting("RestartOutputEnable")
        restart_output_frequency = Configuration.getSetting("RestartOutputFrequency")
        allow_multiple_snapshots = Configuration.getSetting("RestartAllowMultipleSnapshots")

        self.restart_CB.setChecked(enable_restart)
        self.restart_freq_SB.setValue(restart_output_frequency)
        self.multiple_restart_snapshots_CB.setChecked(allow_multiple_snapshots)

    def initParams(self):
        """
            this fcn stores current settings for all the keys of Configuration.Configuration.
            defaultConfigs as a self.paramCC3D dictionary
        """

        for key in Configuration.getSettingNameList():
            self.paramCC3D[key] = Configuration.getSetting(key)
