# Add Transparency Slider (QGIS Plugin)

[![QGIS Version](https://img.shields.io/badge/QGIS-3.16%20--%204+-green.svg)](https://qgis.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight and convenient QGIS plugin that adds a conditional **"Add / Remove transparency slider"** action directly into the Layer Tree context menu (as the 6th item), allowing you to quickly manage the embedded transparency (opacity) slider for layers in the Layers panel with a single click.

![Add Transparency Slider Screenshot](screenshot.PNG)

---

## Features

- **Context Menu Integration**: Adds the action as the 6th item in the layer context menu in the Layers panel.
- **Conditional Add / Remove**:
  - Automatically displays **"Add transparency slider"** when a layer does not have an opacity slider.
  - Automatically switches to **"Remove transparency slider"** when all selected layers already have a slider, allowing easy one-by-one removal.
- **Smart Multi-Layer Selection**: When multiple layers are selected, adding a slider applies only to layers that do not already have one.
- **Custom Context Menu Icons**: Uses dedicated `transparencyAdd.svg` and `transparencyRemove.svg` icons.
- **Single-Click Workflow**: Instantly displays the interactive transparency slider right beneath layer names in the legend.
- **Comprehensive Localization**: Fully translated into all major languages supported by the QGIS interface (over 50 languages).
- **QGIS 3.16 – QGIS 4+ Compatibility**: Compatible with both Qt5 and Qt6 interfaces.

---

## Installation

### Method 1: QGIS Plugin Manager (from custom repository)
1. Open QGIS.
2. Go to **Plugins** -> **Manage and Install Plugins...**.
3. Under **Settings**, add the repository URL containing `plugins.xml`.
4. Search for **Add Transparency Slider** and click **Install Plugin**.

### Method 2: Manual Installation from ZIP
1. Download `add_transparency_slider.zip`.
2. In QGIS, navigate to **Plugins** -> **Manage and Install Plugins...** -> **Install from ZIP**.
3. Select the `.zip` archive and click **Install Plugin**.

---

## Usage

1. Open your project in QGIS.
2. In the **Layers** panel, right-click on any map layer (raster, vector, mesh, etc.).
3. Click the 6th item in the context menu:
   - **"Add transparency slider"** — adds an interactive opacity slider directly under the layer in the Layers list.
   - **"Remove transparency slider"** — removes one opacity slider from the layer.
4. Adjust layer opacity in real time directly from the Layers panel without opening layer properties.

---

## Supported Languages

The plugin automatically detects your QGIS UI language and includes full translations for:
- Ukrainian (`uk`)
- English (`en`, `en_US`, `en_GB`)
- German (`de`)
- French (`fr`)
- Spanish (`es`)
- Italian (`it`)
- Portuguese (`pt_BR`, `pt_PT`)
- Polish (`pl`)
- Japanese (`ja`)
- Chinese (`zh_CN`, `zh_TW`, `zh_Hans`, `zh_Hant`)
- and 40+ other languages supported by QGIS.

---

## License

This plugin is released under the [MIT License](LICENSE).
