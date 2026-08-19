# -*- coding: utf-8 -*-
"""
Add Transparency Slider - QGIS Plugin.

Adds an 'Add / Remove transparency slider' item to the layer tree context menu
to manage embedded transparency sliders under layers.
"""

import os
from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QLocale, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsLayerTreeLayer, QgsApplication


class AddTransparencySliderPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.translator = None
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
        """Initialize GUI and connect context menu signal."""
        self.initTranslator()

        if self.iface:
            self.view = self.iface.layerTreeView()
            if self.view:
                # Disconnect first to avoid duplicate connections
                try:
                    self.view.contextMenuAboutToShow.disconnect(
                        self.populate_context_menu
                    )
                except (TypeError, RuntimeError):
                    pass
                self.view.contextMenuAboutToShow.connect(
                    self.populate_context_menu
                )

    def unload(self):
        """Disconnect signals and remove translators."""
        if self.view:
            try:
                self.view.contextMenuAboutToShow.disconnect(
                    self.populate_context_menu
                )
            except (TypeError, RuntimeError):
                pass

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

    def get_target_layers(self):
        """Get list of valid target layers from layer tree selection."""
        if not self.view:
            return []

        current_node = self.view.currentNode()
        # Only show action when a layer node is focused/selected
        if not isinstance(current_node, QgsLayerTreeLayer):
            return []

        selected_layers = self.view.selectedLayers()
        if not selected_layers and current_node.layer():
            selected_layers = [current_node.layer()]

        # Filter only existing and valid map layers
        return [
            layer
            for layer in selected_layers
            if layer is not None and layer.isValid()
        ]

    def get_embedded_widgets(self, layer):
        """Get list of embedded widget IDs configured on the layer."""
        if not layer or not layer.isValid():
            return []

        try:
            count = int(layer.customProperty("embeddedWidgets/count", 0))
        except (ValueError, TypeError):
            count = 0

        widgets = []
        for i in range(count):
            w_id = layer.customProperty(f"embeddedWidgets/{i}/id")
            if w_id is not None:
                widgets.append(str(w_id))
        return widgets

    def set_embedded_widgets(self, layer, widgets):
        """Set list of embedded widget IDs and refresh layer tree legend."""
        if not layer or not layer.isValid():
            return

        try:
            old_count = int(layer.customProperty("embeddedWidgets/count", 0))
        except (ValueError, TypeError):
            old_count = 0

        layer.setCustomProperty("embeddedWidgets/count", len(widgets))
        for i, w_id in enumerate(widgets):
            layer.setCustomProperty(f"embeddedWidgets/{i}/id", w_id)

        # Remove stale widget property keys
        for i in range(len(widgets), old_count):
            layer.removeCustomProperty(f"embeddedWidgets/{i}/id")

        if self.iface and self.iface.layerTreeView():
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        layer.triggerRepaint()

    def layer_has_transparency_slider(self, layer):
        """Check if layer already has at least one transparency slider."""
        return "transparency" in self.get_embedded_widgets(layer)

    def populate_context_menu(self, menu):
        """Inject conditional Add/Remove action at position 6."""
        if not menu or not self.view:
            return

        target_layers = self.get_target_layers()
        if not target_layers:
            return

        # Show 'Remove' only if ALL target layers already have a slider;
        # otherwise show 'Add' to add slider to layers missing it
        all_have_slider = all(
            self.layer_has_transparency_slider(layer)
            for layer in target_layers
        )

        if all_have_slider:
            action_text = self.tr("Remove transparency slider")
            handler = self.remove_transparency_slider
        else:
            action_text = self.tr("Add transparency slider")
            handler = self.add_transparency_slider

        action = QAction(self.get_transparency_icon(), action_text, menu)
        action.triggered.connect(handler)

        actions = menu.actions()
        # 6th position is 0-based index 5
        if len(actions) >= 5:
            menu.insertAction(actions[5], action)
        else:
            menu.addAction(action)

    def add_transparency_slider_to_layer(self, layer):
        """Add one transparency embedded widget to specified layer."""
        widgets = self.get_embedded_widgets(layer)
        widgets.append("transparency")
        self.set_embedded_widgets(layer, widgets)

    def remove_transparency_slider_from_layer(self, layer):
        """Remove one transparency slider from specified layer."""
        widgets = self.get_embedded_widgets(layer)
        if "transparency" in widgets:
            # Remove the last added transparency widget
            for i in range(len(widgets) - 1, -1, -1):
                if widgets[i] == "transparency":
                    widgets.pop(i)
                    break
            self.set_embedded_widgets(layer, widgets)

    def add_transparency_slider(self):
        """Add slider only to selected layers that do not already have one."""
        for layer in self.get_target_layers():
            if not self.layer_has_transparency_slider(layer):
                self.add_transparency_slider_to_layer(layer)

    def remove_transparency_slider(self):
        """Remove one slider from each selected layer."""
        for layer in self.get_target_layers():
            self.remove_transparency_slider_from_layer(layer)
