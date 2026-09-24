# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction
from .ovrt_dialog import OverlapReportDialog


HELP_URL = 'https://aktivasi.ruangspasial.my.id/help/overlap-report-qgis'


class OverlapReportPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.help_action = None
        self.menu = 'RUANG SPASIAL'
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(
            QIcon(icon_path),
            'Overlap Report',
            self.iface.mainWindow())
        self.action.setObjectName('OverlapReportAction')
        self.action.setStatusTip(
            'Create self-overlap and pair-overlap reports for polygon layers')
        self.action.triggered.connect(self.run)
        self.iface.addPluginToVectorMenu(self.menu, self.action)
        self.iface.addToolBarIcon(self.action)

        self.help_action = QAction(
            QIcon(icon_path),
            'Overlap Report Help',
            self.iface.mainWindow()
        )
        self.help_action.setObjectName('OverlapReportHelpAction')
        self.help_action.triggered.connect(self.open_help)
        self.iface.pluginHelpMenu().addAction(self.help_action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu(self.menu, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.help_action:
            self.iface.pluginHelpMenu().removeAction(self.help_action)
            self.help_action = None
        if self.dialog:
            dialog = self.dialog
            self.dialog = None
            dialog.close()
            dialog.deleteLater()

    def run(self):
        if self.dialog:
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.dialog = OverlapReportDialog(self.iface)
        self.dialog.finished.connect(self._dialog_closed)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _dialog_closed(self, _result=None):
        if self.dialog:
            self.dialog.deleteLater()
            self.dialog = None

    @staticmethod
    def open_help():
        QDesktopServices.openUrl(QUrl(HELP_URL))
