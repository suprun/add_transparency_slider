# -*- coding: utf-8 -*-
"""
Add Transparency Slider - QGIS Plugin.
"""


def classFactory(iface):
    """Load AddTransparencySliderPlugin class.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .add_transparency_slider import AddTransparencySliderPlugin
    return AddTransparencySliderPlugin(iface)
