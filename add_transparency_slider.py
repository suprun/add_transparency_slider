# -*- coding: utf-8 -*-
"""
Add Transparency Slider - QGIS Plugin.

Adds an 'Add transparency slider' item to the layer tree context menu
to display the embedded transparency slider under layers.
"""

import os
from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QLocale, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.core import QgsLayerTreeLayer, QgsApplication
from qgis.gui import QgsLayerTreeViewMenuProvider


class TransparencySliderMenuProvider(QgsLayerTreeViewMenuProvider):
    """Context menu provider inserting 'Add transparency slider' at pos 6."""

    def __init__(self, view, prev_provider, plugin):
        super().__init__()
        self.view = view
        self.prev_provider = prev_provider
        self.plugin = plugin

    def createContextMenu(self):
        if self.prev_provider:
            menu = self.prev_provider.createContextMenu()
        else:
            menu = QMenu(self.view)

        if not menu:
            return None

        # Check if layer(s) are selected or right-clicked
        current_node = self.view.currentNode()
        selected_layers = self.view.selectedLayers()

        if isinstance(current_node, QgsLayerTreeLayer) or selected_layers:
            action = self.plugin.create_add_transparency_action(menu)
            if action:
                actions = menu.actions()
                # Insert at 6th position (0-based index 5)
                if len(actions) >= 5:
                    menu.insertAction(actions[5], action)
                else:
                    menu.addAction(action)

        return menu


class AddTransparencySliderPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.translator = None
        self.menu_provider = None
        self.original_provider = None
        self.view = None

    def tr(self, message):
        """Translate message using QCoreApplication."""
        return QCoreApplication.translate(
            "AddTransparencySliderPlugin", message
        )

    def initTranslator(self):
        """Initialize and install QTranslator for user locale."""
        settings = QSettings()
        locale = settings.value("locale/userLocale", "")
        if not locale:
            locale = QLocale.system().name()

        # Try exact locale (e.g. pt_BR), then short locale (e.g. uk, de)
        i18n_dir = os.path.join(self.plugin_dir, "i18n")
        qm_path = os.path.join(
            i18n_dir, f"add_transparency_slider_{locale}.qm"
        )
        if not os.path.exists(qm_path) and "_" in locale:
            short_locale = locale.split("_")[0]
            qm_path = os.path.join(
                i18n_dir, f"add_transparency_slider_{short_locale}.qm"
            )

        if os.path.exists(qm_path):
            self.translator = QTranslator()
            if self.translator.load(qm_path):
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """Initialize GUI and context menu provider."""
        self.initTranslator()

        if self.iface:
            self.view = self.iface.layerTreeView()
            if self.view:
                self.original_provider = self.view.menuProvider()
                self.menu_provider = TransparencySliderMenuProvider(
                    self.view, self.original_provider, self
                )
                self.view.setMenuProvider(self.menu_provider)

    def unload(self):
        """Restore original menu provider and remove translators."""
        if self.view and self.menu_provider:
            current_provider = self.view.menuProvider()
            if current_provider == self.menu_provider:
                self.view.setMenuProvider(self.original_provider)

        if self.translator:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None

    def get_transparency_icon(self):
        """Get standard transparency icon with safe fallbacks."""
        # 1. Standard QGIS theme resource icon
        icon = QIcon(":/images/themes/default/propertyicons/transparency.svg")
        if not icon.isNull():
            return icon

        # 2. QgsApplication theme icon lookup
        icon = QgsApplication.getThemeIcon("propertyicons/transparency.svg")
        if not icon.isNull():
            return icon

        # 3. Bundled SVG icon
        svg_path = os.path.join(self.plugin_dir, "transparency.svg")
        if os.path.exists(svg_path):
            return QIcon(svg_path)

        # 4. Bundled PNG icon
        png_path = os.path.join(self.plugin_dir, "icon.png")
        if os.path.exists(png_path):
            return QIcon(png_path)

        return QIcon()

    def create_add_transparency_action(self, parent=None):
        """Create QAction for adding transparency slider."""
        action = QAction(
            self.get_transparency_icon(),
            self.tr("Add transparency slider"),
            parent,
        )
        action.triggered.connect(self.add_transparency_slider)
        return action

    def add_transparency_slider_to_layer(self, layer):
        """Add transparency embedded widget to specified layer."""
        if not layer or not layer.isValid():
            return

        try:
            count = int(layer.customProperty("embeddedWidgets/count", 0))
        except (ValueError, TypeError):
            count = 0

        # Append transparency widget
        layer.setCustomProperty(f"embeddedWidgets/{count}/id", "transparency")
        layer.setCustomProperty("embeddedWidgets/count", count + 1)

        # Refresh layer tree legend and trigger repaint
        if self.iface and self.iface.layerTreeView():
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        layer.triggerRepaint()

    def add_transparency_slider(self):
        """Handler for 'Add transparency slider' action."""
        if not self.iface or not self.iface.layerTreeView():
            return

        selected_layers = self.iface.layerTreeView().selectedLayers()
        if not selected_layers:
            current_node = self.iface.layerTreeView().currentNode()
            if (
                isinstance(current_node, QgsLayerTreeLayer)
                and current_node.layer()
            ):
                selected_layers = [current_node.layer()]

        for layer in selected_layers:
            self.add_transparency_slider_to_layer(layer)
