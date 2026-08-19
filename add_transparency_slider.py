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

    def get_transparency_icon(self, is_remove=False):
        """Get transparency icon (Add or Remove) with safe fallbacks."""
        # 1. Custom Add / Remove SVG icon
        svg_name = (
            "transparencyRemove.svg" if is_remove else "transparencyAdd.svg"
        )
        svg_path = os.path.join(self.plugin_dir, svg_name)
        if os.path.exists(svg_path):
            icon = QIcon(svg_path)
            if not icon.isNull():
                return icon

        # 2. Standard QGIS theme resource icon
        icon = QIcon(":/images/themes/default/propertyicons/transparency.svg")
        if not icon.isNull():
            return icon

        # 3. QgsApplication theme icon lookup
        icon = QgsApplication.getThemeIcon("propertyicons/transparency.svg")
        if not icon.isNull():
            return icon

        # 4. Bundled fallback SVG icon
        fallback_svg = os.path.join(self.plugin_dir, "transparency.svg")
        if os.path.exists(fallback_svg):
            return QIcon(fallback_svg)

        # 5. Bundled PNG icon
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

    def is_show_labels_action(self, action):
        """Check if action is the standard 'Show Labels' layer action."""
        if not action or action.isSeparator():
            return False

        clean_text = action.text().replace("&", "").strip().lower()
        if clean_text in ("show labels", "show label"):
            return True

        # Check translations across standard QGIS contexts
        contexts = (
            "QgsAppLayerTreeViewMenuProvider",
            "QgisApp",
            "QgsLayerTreeViewDefaultActions",
        )
        for ctx in contexts:
            translated = (
                QCoreApplication.translate(ctx, "Show Labels")
                .replace("&", "")
                .strip()
                .lower()
            )
            if translated and clean_text == translated:
                return True

        return False

    def find_insertion_index(self, actions):
        """Find the optimal position in context menu for transparency slider.

        Places action immediately after 'Show Labels' (vector layers),
        or before the first separator (raster/mesh layers).
        """
        # 1. Insert immediately after 'Show Labels' if present
        for idx, action in enumerate(actions):
            if self.is_show_labels_action(action):
                return idx + 1

        # 2. Otherwise insert at the end of View block (before 1st separator)
        for idx, action in enumerate(actions):
            if action.isSeparator():
                return idx

        # 3. Fallback: before Rename Layer if found
        contexts = (
            "QgsAppLayerTreeViewMenuProvider",
            "QgisApp",
            "QgsLayerTreeViewDefaultActions",
        )
        for idx, action in enumerate(actions):
            clean_text = action.text().replace("&", "").strip().lower()
            if "rename" in clean_text:
                return idx
            for ctx in contexts:
                translated = (
                    QCoreApplication.translate(ctx, "Rename Layer")
                    .replace("&", "")
                    .strip()
                    .lower()
                )
                if translated and clean_text == translated:
                    return idx

        # 4. Final fallback: position 5 or end of menu
        return min(5, len(actions))

    def populate_context_menu(self, menu):
        """Inject conditional Add/Remove action at optimal position."""
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
            action_icon = self.get_transparency_icon(is_remove=True)
            handler = self.remove_transparency_slider
        else:
            action_text = self.tr("Add transparency slider")
            action_icon = self.get_transparency_icon(is_remove=False)
            handler = self.add_transparency_slider

        action = QAction(action_icon, action_text, menu)
        action.triggered.connect(handler)

        actions = menu.actions()
        insert_idx = self.find_insertion_index(actions)

        if insert_idx < len(actions):
            menu.insertAction(actions[insert_idx], action)
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
