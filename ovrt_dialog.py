from .run_guard import single_run
from .output_safety import ensure_new_output
from .qt_compat import FIELD_STRING, FIELD_LONG, FIELD_DOUBLE
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import re
import traceback
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout
)
from qgis.PyQt.QtGui import QPixmap, QDesktopServices
from qgis.core import (
    QgsCoordinateTransform, QgsDistanceArea, QgsFeature, QgsField, QgsFields,
    QgsGeometry, QgsMapLayerType, QgsProject, QgsSpatialIndex, QgsUnitTypes,
    QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes
)
from .licensehub_ovrt_qgis import (
    FIXED_CODE,
    LicenseManager,
    PRODUCT_CODE,
    PRODUCT_NAME,
    TRIAL_LIMIT,
)

HELP_URL = 'https://aktivasi.ruangspasial.my.id/help/overlap-report-qgis'


class ActivationDialog(QDialog):
    def __init__(self, lm, parent=None):
        super(ActivationDialog, self).__init__(parent)
        self.lm = lm
        self.setWindowTitle('License Activation')
        window_flags = (
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(window_flags)
        self.setSizeGripEnabled(True)
        self.resize(700, 190)
        self._build_ui()
        self.refresh_status(True)

    def _build_ui(self):
        main = QVBoxLayout(self)
        grid = QGridLayout()
        self.lbl_status = QLabel('-')
        self.txt_device_id = QLineEdit()
        self.txt_device_id.setReadOnly(True)
        self.btn_copy = QPushButton('Copy Device ID')
        self.btn_copy.clicked.connect(self.copy_device_id)
        self.lbl_trial = QLabel('-')
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText(
            'Enter the activation code from License Hub')
        grid.addWidget(QLabel('Activation Status'), 0, 0)
        grid.addWidget(self.lbl_status, 0, 1, 1, 2)
        grid.addWidget(QLabel('Device ID'), 1, 0)
        grid.addWidget(self.txt_device_id, 1, 1)
        grid.addWidget(self.btn_copy, 1, 2)
        grid.addWidget(QLabel('Trial Usage'), 2, 0)
        grid.addWidget(self.lbl_trial, 2, 1, 1, 2)
        grid.addWidget(QLabel('Activation Code'), 3, 0)
        grid.addWidget(self.txt_code, 3, 1, 1, 2)
        main.addLayout(grid)
        row = QHBoxLayout()
        self.btn_request = QPushButton('Submit Request')
        self.btn_request.clicked.connect(self.open_request_page)
        self.btn_activate = QPushButton('Activate')
        self.btn_activate.clicked.connect(self.activate_license)
        self.btn_refresh = QPushButton('Refresh Status')
        self.btn_refresh.clicked.connect(lambda: self.refresh_status(False))
        self.btn_close = QPushButton('Close')
        self.btn_close.clicked.connect(self.accept)
        row.addStretch(1)
        row.addWidget(self.btn_request)
        row.addWidget(self.btn_activate)
        row.addWidget(self.btn_refresh)
        row.addWidget(self.btn_close)
        main.addLayout(row)

    def refresh_status(self, quiet=True):
        self.txt_device_id.setText(self.lm.get_device_id())
        self._display_local_status()
        if not quiet:
            ok, msg = self.lm.refresh_activation_from_server()
            self.txt_device_id.setText(self.lm.get_device_id())
            self._display_local_status()
            if ok is True:
                QMessageBox.information(
                    self,
                    PRODUCT_NAME,
                    'License status was refreshed from the website.')
            elif ok is False:
                QMessageBox.warning(
                    self, PRODUCT_NAME, msg or 'License is not active.')
            else:
                QMessageBox.warning(
                    self,
                    PRODUCT_NAME,
                    msg or (
                        'License status could not be confirmed from the '
                        'website.'
                    ))

    def _display_local_status(self):
        status = self.lm.status_text()
        self.lbl_status.setText(status)
        remaining = self.lm.trial_remaining()
        self.lbl_trial.setText(
            '%s/%s used, %s remaining' %
            (TRIAL_LIMIT - remaining, TRIAL_LIMIT, remaining))
        if status.startswith('Active'):
            self.lbl_status.setStyleSheet('font-weight:bold;color:#0B7A2A;')
        elif status.startswith('Trial'):
            self.lbl_status.setStyleSheet('font-weight:bold;color:#B35C00;')
        elif status.startswith('Expired'):
            self.lbl_status.setStyleSheet('font-weight:bold;color:#B00020;')
        else:
            self.lbl_status.setStyleSheet('font-weight:bold;color:#7A003C;')

    def copy_device_id(self):
        QApplication.clipboard().setText(self.txt_device_id.text().strip())
        QMessageBox.information(
            self, PRODUCT_NAME, 'Device ID copied successfully.')

    def open_request_page(self):
        try:
            self.lm.open_request_url()
            message = (
                'The activation request page has been opened. Please submit '
                'the request with Product Code %s and Fixed Code %s.'
            ) % (PRODUCT_CODE, FIXED_CODE)
            QMessageBox.information(
                self,
                PRODUCT_NAME,
                message)
        except Exception as e:
            QMessageBox.warning(
                self,
                PRODUCT_NAME,
                'Failed to open request page: %s' %
                e)

    def activate_license(self):
        ok, msg = self.lm.activate(self.txt_code.text().strip())
        self.refresh_status(True)
        if ok:
            QMessageBox.information(self, PRODUCT_NAME, msg)
            self.accept()
        else:
            QMessageBox.warning(self, PRODUCT_NAME, msg)


class OverlapReportDialog(QDialog):
    def __init__(self, iface, parent=None):
        super(OverlapReportDialog, self).__init__(parent)
        self.iface = iface
        self.lm = LicenseManager()
        self.setWindowTitle('Overlap Report')
        window_flags = (
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(window_flags)
        self.setSizeGripEnabled(True)
        self.resize(860, 620)
        self._build_ui()
        self.load_layers()
        self.refresh_license_status()

    def _build_ui(self):
        main = QVBoxLayout(self)
        hero = QGroupBox()
        hero_layout = QHBoxLayout(hero)
        self.lbl_logo = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            self.lbl_logo.setPixmap(
                pix.scaled(
                    160,
                    160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
        self.lbl_logo.setMinimumWidth(180)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.lbl_logo)
        center = QVBoxLayout()
        self.lbl_title = QLabel(
            "<span style='font-size:24px; font-weight:700;'>"
            "Overlap Report</span>")
        self.lbl_title.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_desc = QLabel(
            'Overlap Report helps identify overlaps and intersections between '
            'polygon layers quickly and accurately, improving the efficiency '
            'of spatial data validation.')
        self.lbl_desc.setWordWrap(True)
        center.addWidget(self.lbl_title)
        center.addWidget(self.lbl_desc)
        center.addStretch(1)
        hero_layout.addLayout(center, 1)
        right = QVBoxLayout()
        self.lbl_activation = QLabel()
        self.lbl_activation.setTextFormat(Qt.TextFormat.RichText)
        self.btn_manage = QPushButton('Manage Activation')
        self.btn_manage.clicked.connect(self.show_activation_dialog)
        self.btn_help_main = QPushButton('User Guide and Activation')
        self.btn_help_main.clicked.connect(self.open_help_page)
        right.addWidget(self.lbl_activation, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.btn_manage, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.btn_help_main, 0, Qt.AlignmentFlag.AlignRight)
        right.addStretch(1)
        hero_layout.addLayout(right)
        main.addWidget(hero)

        tool_box = QGroupBox('Analysis Workspace')
        layout = QVBoxLayout(tool_box)
        grid = QGridLayout()
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(['Self Overlap', 'Pair Overlap'])
        self.cmb_method.currentIndexChanged.connect(self.on_method_changed)
        self.txt_input1_file = QLineEdit()
        self.txt_input1_file.setPlaceholderText(
            'Optional: browse primary polygon data directly from a folder')
        self.btn_input1_file = QPushButton('Browse Primary...')
        self.btn_input1_file.clicked.connect(self.choose_input1_file)
        self.cmb_layer1 = QComboBox()
        self.cmb_layer1.currentIndexChanged.connect(self.on_layer_changed)
        self.cmb_target1 = QComboBox()
        self.txt_input2_file = QLineEdit()
        self.txt_input2_file.setPlaceholderText(
            'Optional: browse secondary polygon data directly from a folder')
        self.btn_input2_file = QPushButton('Browse Secondary...')
        self.btn_input2_file.clicked.connect(self.choose_input2_file)
        self.cmb_layer2 = QComboBox()
        self.cmb_layer2.currentIndexChanged.connect(self.on_layer2_changed)
        self.cmb_target2 = QComboBox()
        self.lst_select_fields = QListWidget()
        self.lst_select_fields.setMinimumHeight(120)
        self.btn_select_all = QPushButton('Select All')
        self.btn_select_all.clicked.connect(self.select_all_fields)
        self.btn_unselect_all = QPushButton('Unselect All')
        self.btn_unselect_all.clicked.connect(self.unselect_all_fields)
        self.txt_output = QLineEdit()
        self.btn_output = QPushButton('Browse Output...')
        self.btn_output.clicked.connect(self.choose_output)
        grid.addWidget(QLabel('Overlap Analysis Mode'), 0, 0)
        grid.addWidget(self.cmb_method, 0, 1, 1, 2)
        grid.addWidget(QLabel('Primary Data From Folder'), 1, 0)
        grid.addWidget(self.txt_input1_file, 1, 1)
        grid.addWidget(self.btn_input1_file, 1, 2)
        grid.addWidget(QLabel('Primary Layer From Project'), 2, 0)
        grid.addWidget(self.cmb_layer1, 2, 1, 1, 2)
        grid.addWidget(QLabel('Primary Identifier Field (Optional)'), 3, 0)
        grid.addWidget(self.cmb_target1, 3, 1, 1, 2)
        grid.addWidget(QLabel('Secondary Data From Folder (Optional)'), 4, 0)
        grid.addWidget(self.txt_input2_file, 4, 1)
        grid.addWidget(self.btn_input2_file, 4, 2)
        grid.addWidget(QLabel('Secondary Layer From Project (Optional)'), 5, 0)
        grid.addWidget(self.cmb_layer2, 5, 1, 1, 2)
        grid.addWidget(QLabel('Secondary Identifier Field (Optional)'), 6, 0)
        grid.addWidget(self.cmb_target2, 6, 1, 1, 2)
        layout.addLayout(grid)

        fields_box = QGroupBox('Additional Attributes to Include (Optional)')
        fields_layout = QVBoxLayout(fields_box)
        row_fields = QHBoxLayout()
        row_fields.addStretch(1)
        row_fields.addWidget(self.btn_select_all)
        row_fields.addWidget(self.btn_unselect_all)
        fields_layout.addLayout(row_fields)
        fields_layout.addWidget(self.lst_select_fields)
        layout.addWidget(fields_box)

        output_grid = QGridLayout()
        output_grid.addWidget(QLabel('Output Report Shapefile (.shp)'), 0, 0)
        output_grid.addWidget(self.txt_output, 0, 1)
        output_grid.addWidget(self.btn_output, 0, 2)
        layout.addLayout(output_grid)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        layout.addWidget(self.log)
        main.addWidget(tool_box)

        bottom = QHBoxLayout()
        self.btn_run = QPushButton('Run')
        self.btn_run.clicked.connect(self.run_tool)
        self.btn_cancel = QPushButton('Cancel')
        self.btn_cancel.clicked.connect(self.close)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_run)
        bottom.addWidget(self.btn_cancel)
        main.addLayout(bottom)

    def open_help_page(self):
        try:
            QDesktopServices.openUrl(QUrl(HELP_URL))
        except Exception as e:
            QMessageBox.warning(
                self,
                PRODUCT_NAME,
                "Failed to open help page: %s" %
                e)

    def show_activation_dialog(self):
        dlg = ActivationDialog(self.lm, self)
        dlg.exec()
        self.refresh_license_status()

    def refresh_license_status(self):
        status = self.lm.status_text()
        if status.startswith('Active'):
            txt = (
                "<b><span style='color:#0B7A2A;'>"
                "Activation : Active</span></b>")
        elif status.startswith('Trial'):
            txt = (
                "<b><span style='color:#B35C00;'>"
                "Activation : Trial</span></b>")
        elif status.startswith('Expired'):
            txt = (
                "<b><span style='color:#B00020;'>"
                "Activation : Expired</span></b>")
        else:
            txt = (
                "<b><span style='color:#7A003C;'>"
                "Activation : Deactivated</span></b>")
        self.lbl_activation.setText(txt)

    def log_msg(self, msg):
        self.log.append(str(msg))

    def load_layers(self):
        self.cmb_layer1.clear()
        self.cmb_layer2.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            is_polygon = (
                lyr.type() == QgsMapLayerType.VectorLayer
                and lyr.geometryType() == QgsWkbTypes.PolygonGeometry
            )
            if is_polygon:
                self.cmb_layer1.addItem(lyr.name(), lyr.id())
                self.cmb_layer2.addItem(lyr.name(), lyr.id())
        self.on_layer_changed()
        self.on_layer2_changed()
        self.on_method_changed()

    def _open_vector_from_path(self, path):
        if not path:
            return None
        if not os.path.exists(path):
            return None
        layer = QgsVectorLayer(path, os.path.basename(path), 'ogr')
        if (
                layer.isValid()
                and layer.geometryType() == QgsWkbTypes.PolygonGeometry):
            return layer
        return None

    def current_layer1(self):
        input_path = ''
        if hasattr(self, 'txt_input1_file'):
            input_path = self.txt_input1_file.text().strip()
        if input_path:
            return self._open_vector_from_path(input_path)
        lid = self.cmb_layer1.currentData()
        if not lid:
            return None
        return QgsProject.instance().mapLayer(lid)

    def current_layer2(self):
        input_path = ''
        if hasattr(self, 'txt_input2_file'):
            input_path = self.txt_input2_file.text().strip()
        if input_path:
            return self._open_vector_from_path(input_path)
        lid = self.cmb_layer2.currentData()
        if not lid:
            return None
        return QgsProject.instance().mapLayer(lid)

    def choose_input1_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Select primary polygon data from folder',
            '',
            'Vector Polygon Data '
            '(*.shp *.gpkg *.geojson *.json *.kml *.tab);;All Files (*.*)'
        )
        if path:
            layer = self._open_vector_from_path(path)
            if layer is None:
                QMessageBox.warning(
                    self,
                    PRODUCT_NAME,
                    'The selected primary input cannot be opened as a valid '
                    'polygon layer.')
                return
            self.txt_input1_file.setText(path)
            self.on_layer_changed()
            self.log_msg('Primary input selected from folder: %s' % path)

    def choose_input2_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Select secondary polygon data from folder',
            '',
            'Vector Polygon Data '
            '(*.shp *.gpkg *.geojson *.json *.kml *.tab);;All Files (*.*)'
        )
        if path:
            layer = self._open_vector_from_path(path)
            if layer is None:
                QMessageBox.warning(
                    self,
                    PRODUCT_NAME,
                    'The selected secondary input cannot be opened as a valid '
                    'polygon layer.')
                return
            self.txt_input2_file.setText(path)
            self.on_layer2_changed()
            self.log_msg('Secondary input selected from folder: %s' % path)

    def on_layer_changed(self):
        self.cmb_target1.clear()
        self.lst_select_fields.clear()
        lyr = self.current_layer1()
        if lyr is None:
            return
        self.cmb_target1.addItem('')
        for f in lyr.fields():
            name = f.name()
            self.cmb_target1.addItem(name)
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.lst_select_fields.addItem(item)

    def on_layer2_changed(self):
        self.cmb_target2.clear()
        lyr = self.current_layer2()
        self.cmb_target2.addItem('')
        if lyr is None:
            return
        for f in lyr.fields():
            self.cmb_target2.addItem(f.name())

    def on_method_changed(self):
        is_pair = self.cmb_method.currentText() == 'Pair Overlap'
        self.txt_input2_file.setEnabled(is_pair)
        self.btn_input2_file.setEnabled(is_pair)
        self.cmb_layer2.setEnabled(is_pair)
        self.cmb_target2.setEnabled(is_pair)

    def select_all_fields(self):
        for i in range(self.lst_select_fields.count()):
            self.lst_select_fields.item(i).setCheckState(Qt.CheckState.Checked)

    def unselect_all_fields(self):
        for i in range(self.lst_select_fields.count()):
            self.lst_select_fields.item(i).setCheckState(Qt.CheckState.Unchecked)

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save output report', '', 'Shapefile (*.shp)')
        if path:
            if not path.lower().endswith('.shp'):
                path += '.shp'
            self.txt_output.setText(path)

    @single_run
    def run_tool(self):
        can_run, msg = self.lm.can_run()
        if not can_run:
            self.refresh_license_status()
            QMessageBox.warning(self, PRODUCT_NAME, msg)
            return
        using_trial = not self.lm.is_activated_local()
        try:
            out_main, out_overlap = self._process()
            if using_trial:
                self.lm.consume_trial_for_run()
                self.log_msg(
                    'Trial run completed. Remaining trial: %s of %s.' %
                    (self.lm.trial_remaining(), TRIAL_LIMIT))
            self.log_msg('Process completed. Report output: %s' % out_main)
            self.log_msg('Overlap detail output: %s' % out_overlap)
            QMessageBox.information(
                self,
                PRODUCT_NAME,
                'Process completed.\n\nReport output: %s\n'
                'Overlap detail output: %s' %
                (out_main,
                 out_overlap))
            self.refresh_license_status()
        except Exception as e:
            self.log_msg('ERROR: %s\n%s' % (e, traceback.format_exc()))
            QMessageBox.critical(
                self,
                PRODUCT_NAME,
                'Failed to run tool:\n%s' %
                e)

    def _field_names_from_checks(self):
        names = []
        for i in range(self.lst_select_fields.count()):
            item = self.lst_select_fields.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                names.append(item.text())
        return names

    def _process(self):
        method = self.cmb_method.currentText()
        layer1 = self.current_layer1()
        layer2 = self.current_layer2() if method == 'Pair Overlap' else None
        if layer1 is None:
            raise RuntimeError(
                'Please select a primary polygon layer from the project or '
                'browse one from a folder.')
        if method == 'Pair Overlap' and layer2 is None:
            raise RuntimeError(
                'Please select a secondary polygon layer from the project or '
                'browse one from a folder for Pair Overlap mode.')
        if not layer1.crs().isValid():
            raise RuntimeError(
                'The primary layer needs a valid CRS so areas can be reported '
                'in square metres.')
        if method == 'Pair Overlap' and not layer2.crs().isValid():
            raise RuntimeError(
                'The secondary layer needs a valid CRS for Pair Overlap '
                'analysis.')
        out_main = self.txt_output.text().strip()
        if not out_main:
            raise RuntimeError('Please choose an output report shapefile.')
        if not out_main.lower().endswith('.shp'):
            out_main += '.shp'
        out_overlap = out_main[:-4] + '_Overlap.shp'
        output_paths = {
            os.path.normcase(
                os.path.abspath(out_main)), os.path.normcase(
                os.path.abspath(out_overlap))}
        input_paths = set()
        for layer in (layer1, layer2):
            if layer is None:
                continue
            source_path = str(layer.source()).split('|', 1)[0]
            if source_path and os.path.isfile(source_path):
                input_paths.add(os.path.normcase(os.path.abspath(source_path)))
        if output_paths.intersection(input_paths):
            raise RuntimeError(
                'The output path must be different from every input dataset.')
        target1 = self.cmb_target1.currentText().strip()
        target2 = self.cmb_target2.currentText().strip()
        selected_fields = self._field_names_from_checks()

        ensure_new_output(out_main)
        ensure_new_output(out_overlap)
        self._delete_shapefile(out_main)
        self._delete_shapefile(out_overlap)

        report_fields = self._write_main_output(layer1, out_main)
        self._write_overlap_output(
            method,
            layer1,
            layer2,
            out_overlap,
            target1,
            target2,
            selected_fields)
        self._update_main_report(method, out_main, out_overlap, report_fields)

        out_layer = QgsVectorLayer(out_main, os.path.basename(out_main), 'ogr')
        if out_layer.isValid():
            QgsProject.instance().addMapLayer(out_layer)
        ov_layer = QgsVectorLayer(
            out_overlap, os.path.basename(out_overlap), 'ogr')
        if ov_layer.isValid():
            QgsProject.instance().addMapLayer(ov_layer)
        return out_main, out_overlap

    @staticmethod
    def _unique_field_name(fields, preferred):
        used = set()
        for field in fields:
            name = field.name().upper()
            used.add(name)
            used.add(name[:10])
        base = re.sub(r'[^A-Za-z0-9_]', '_', preferred).strip('_') or 'FIELD'
        base = base[:10]
        candidate = base
        counter = 1
        while candidate.upper() in used:
            suffix = str(counter)
            candidate = base[:10 - len(suffix)] + suffix
            counter += 1
        return candidate

    @staticmethod
    def _prepared_geometry(geometry):
        if geometry is None or geometry.isEmpty():
            return None
        prepared = QgsGeometry(geometry)
        if not prepared.isGeosValid():
            prepared = prepared.makeValid()
        if prepared is None or prepared.isEmpty() or not prepared.isGeosValid():
            raise RuntimeError("A source geometry could not be repaired. Fix it before analysis.")
        return prepared

    @staticmethod
    def _area_m2(geometry, crs):
        calculator = QgsDistanceArea()
        calculator.setSourceCrs(crs, QgsProject.instance().transformContext())
        ellipsoid = QgsProject.instance().ellipsoid()
        if not ellipsoid or str(ellipsoid).upper() == 'NONE':
            ellipsoid = 'WGS84'
        calculator.setEllipsoid(ellipsoid)
        measured = calculator.measureArea(geometry)
        return float(calculator.convertAreaMeasurement(
            measured, QgsUnitTypes.AreaSquareMeters))

    def _write_main_output(self, layer1, out_main):
        fields = QgsFields()
        for source_field in layer1.fields():
            fields.append(QgsField(source_field))

        report_fields = {
            'source_id': self._unique_field_name(fields, 'OVRT_ID'),
        }
        fields.append(QgsField(report_fields['source_id'], FIELD_LONG))
        report_fields['text'] = self._unique_field_name(fields, 'OVERLAP')
        fields.append(
            QgsField(
                report_fields['text'],
                FIELD_STRING,
                len=254))
        report_fields['area'] = self._unique_field_name(fields, 'AREA_M2')
        fields.append(
            QgsField(
                report_fields['area'],
                FIELD_DOUBLE,
                len=20,
                prec=3))
        report_fields['percentage'] = self._unique_field_name(
            fields, 'PERCENTAGE')
        fields.append(
            QgsField(
                report_fields['percentage'],
                FIELD_DOUBLE,
                len=20,
                prec=6))

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'ESRI Shapefile'
        options.fileEncoding = 'UTF-8'
        writer = QgsVectorFileWriter.create(
            out_main, fields, layer1.wkbType(), layer1.crs(),
            QgsProject.instance().transformContext(), options)
        if writer.hasError() != QgsVectorFileWriter.WriterError.NoError:
            raise RuntimeError(
                'Failed to create the output report shapefile: %s' %
                writer.errorMessage())

        failed = 0
        for source_feature in layer1.getFeatures():
            output_feature = QgsFeature(fields)
            output_feature.setGeometry(QgsGeometry(source_feature.geometry()))
            output_feature.setAttributes(
                list(source_feature.attributes())
                + [int(source_feature.id()), '', 0.0, 0.0]
            )
            if not writer.addFeature(output_feature):
                failed += 1
        del writer
        if failed:
            raise RuntimeError(
                '%s feature(s) could not be written to the report output.' %
                failed)

        out_layer = QgsVectorLayer(out_main, os.path.basename(out_main), 'ogr')
        if not out_layer.isValid():
            raise RuntimeError(
                'The output report shapefile could not be opened.')
        return report_fields

    def _write_overlap_output(
            self,
            method,
            layer1,
            layer2,
            out_overlap,
            target1,
            target2,
            selected_fields):
        fields = QgsFields()
        fields.append(QgsField('SRC_ID_A', FIELD_LONG))
        fields.append(QgsField('SRC_ID_B', FIELD_LONG))
        fields.append(QgsField('AREA_M2', FIELD_DOUBLE, len=20, prec=3))
        fields.append(QgsField('OVERLAP', FIELD_STRING, len=254))
        attribute_fields = []
        for name in selected_fields:
            source_index = layer1.fields().indexOf(name)
            if source_index == -1:
                continue
            source_field = layer1.fields().field(source_index)
            output_name = self._unique_field_name(fields, name)
            output_field = QgsField(source_field)
            output_field.setName(output_name)
            fields.append(output_field)
            attribute_fields.append(name)

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'ESRI Shapefile'
        options.fileEncoding = 'UTF-8'
        writer = QgsVectorFileWriter.create(
            out_overlap, fields, QgsWkbTypes.MultiPolygon, layer1.crs(),
            QgsProject.instance().transformContext(), options)
        if writer.hasError() != QgsVectorFileWriter.WriterError.NoError:
            raise RuntimeError(
                'Failed to create the overlap-detail shapefile: %s' %
                writer.errorMessage())

        primary_features = list(layer1.getFeatures())
        if method == 'Pair Overlap':
            secondary_features = list(layer2.getFeatures())
        else:
            secondary_features = primary_features
        coordinate_transform = None
        if method == 'Pair Overlap' and layer2.crs() != layer1.crs():
            coordinate_transform = QgsCoordinateTransform(
                layer2.crs(),
                layer1.crs(),
                QgsProject.instance()
            )

        spatial_index = QgsSpatialIndex()
        secondary = {}
        secondary_order = {}
        for order, feature in enumerate(secondary_features):
            geometry = self._prepared_geometry(feature.geometry())
            if geometry is None:
                continue
            if coordinate_transform is not None:
                geometry.transform(coordinate_transform)
            index_feature = QgsFeature()
            index_feature.setId(feature.id())
            index_feature.setGeometry(geometry)
            spatial_index.addFeature(index_feature)
            secondary[int(feature.id())] = (feature, geometry)
            secondary_order[int(feature.id())] = order

        failed = 0
        for primary_order, fa in enumerate(primary_features):
            ga = self._prepared_geometry(fa.geometry())
            if ga is None:
                continue
            for candidate_id in spatial_index.intersects(ga.boundingBox()):
                candidate_id = int(candidate_id)
                if method == 'Self Overlap' and secondary_order.get(
                        candidate_id, -1) <= primary_order:
                    continue
                record = secondary.get(candidate_id)
                if record is None:
                    continue
                fb, gb = record
                if not ga.intersects(gb):
                    continue
                inter = ga.intersection(gb)
                if inter is None or inter.isEmpty():
                    continue
                if QgsWkbTypes.geometryType(
                        inter.wkbType()) != QgsWkbTypes.PolygonGeometry:
                    continue
                if QgsWkbTypes.isSingleType(inter.wkbType()):
                    inter.convertToMultiType()
                area_m2 = self._area_m2(inter, layer1.crs())
                if area_m2 <= 0:
                    continue
                has_target1 = (
                    target1 and layer1.fields().indexOf(target1) != -1
                )
                val_a = str(fa[target1]) if has_target1 else str(fa.id())
                if method == 'Pair Overlap':
                    has_target2 = (
                        target2
                        and layer2
                        and layer2.fields().indexOf(target2) != -1
                    )
                    val_b = (
                        str(fb[target2]) if has_target2 else str(fb.id())
                    )
                    txt = '%s %s overlaps with %s %s' % (
                        target1 or 'Feature',
                        val_a,
                        target2 or 'Feature',
                        val_b)
                else:
                    val_b = (
                        str(fb[target1]) if has_target1 else str(fb.id())
                    )
                    txt = '%s %s overlaps with %s %s' % (
                        target1 or 'Feature',
                        val_a,
                        target1 or 'Feature',
                        val_b)
                newf = QgsFeature(fields)
                newf.setGeometry(inter)
                attrs = [int(fa.id()), int(fb.id()), area_m2, txt]
                for name in attribute_fields:
                    attrs.append(fa[name])
                newf.setAttributes(attrs)
                if not writer.addFeature(newf):
                    failed += 1
        del writer
        if failed:
            raise RuntimeError(
                '%s overlap feature(s) could not be written.' %
                failed)

    def _update_main_report(
            self,
            method,
            out_main,
            out_overlap,
            report_fields):
        overlap_layer = QgsVectorLayer(
            out_overlap, os.path.basename(out_overlap), 'ogr')
        main_layer = QgsVectorLayer(
            out_main, os.path.basename(out_main), 'ogr')
        if not overlap_layer.isValid() or not main_layer.isValid():
            raise RuntimeError(
                'Failed to open the generated shapefiles for updating.')
        totals = {}
        coverage = {}
        texts = {}
        idx_a = overlap_layer.fields().indexOf('SRC_ID_A')
        idx_b = overlap_layer.fields().indexOf('SRC_ID_B')
        idx_text = overlap_layer.fields().indexOf('OVERLAP')
        for f in overlap_layer.getFeatures():
            aid = int(f[idx_a])
            txt = str(f[idx_text] or '')
            coverage.setdefault(aid, []).append(QgsGeometry(f.geometry()))
            texts.setdefault(aid, []).append(txt)
            if method == 'Self Overlap':
                bid = int(f[idx_b])
                coverage.setdefault(bid, []).append(QgsGeometry(f.geometry()))
                texts.setdefault(bid, []).append(txt)
        for source_id, geometries in coverage.items():
            merged = QgsGeometry.unaryUnion(geometries)
            if merged.isNull() or merged.isEmpty():
                raise RuntimeError("Could not compute unique overlap coverage.")
            totals[source_id] = self._area_m2(merged, main_layer.crs())
        idx_id = main_layer.fields().indexOf(report_fields['source_id'])
        idx_ov = main_layer.fields().indexOf(report_fields['text'])
        idx_ar = main_layer.fields().indexOf(report_fields['area'])
        idx_pc = main_layer.fields().indexOf(report_fields['percentage'])
        if min(idx_id, idx_ov, idx_ar, idx_pc) < 0:
            raise RuntimeError(
                'Required report fields are missing from the output '
                'shapefile.')
        prov = main_layer.dataProvider()
        changes = {}
        for feat in main_layer.getFeatures():
            geometry = self._prepared_geometry(feat.geometry())
            area_feat = self._area_m2(
                geometry, main_layer.crs()) if geometry is not None else 0.0
            source_id = int(feat[idx_id])
            total = float(totals.get(source_id, 0.0))
            pct = (total / area_feat * 100.0) if area_feat > 0 else 0.0
            txt = '; '.join(texts.get(source_id, []))
            changes[feat.id()] = {idx_ov: txt[:254],
                                  idx_ar: total, idx_pc: pct}
        if changes and not prov.changeAttributeValues(changes):
            raise RuntimeError('Failed to update the report attributes.')
        main_layer.updateFields()

    def _delete_shapefile(self, path):
        base, ext = os.path.splitext(path)
        if ext.lower() == '.shp':
            for e in (
                '.shp',
                '.shx',
                '.dbf',
                '.prj',
                '.cpg',
                '.qpj',
                '.qix',
                '.sbn',
                '.sbx',
                '.fix',
                    '.shp.xml'):
                p = base + e
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError as exc:
                        raise RuntimeError(
                            'Unable to replace existing output file %s: %s' %
                            (p, exc))
