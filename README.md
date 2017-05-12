# NetworkProps
## QGIS plugin for network analysis

This plugin takes a layer of multiple lines to represent a fracture network. It breaks this down into component straight line segments and characterises the nodes according to their connectivity. Other basic metrics are calculated and displayed including segment length and orientation characteristics, a ternary classification plot based on node type proportions.

This plugin requires matplotlib and numpy libraries. The ternary matplotlib library of Marc Harper et al. (2015). python-ternary: Ternary Plots in Python. Zenodo. 10.5281/zenodo.34938  is included

## Using the Plugin

select the layer containing the network of lines, and choose a tolerance in metres. Tolerence is a measure of how far nodes need to be apart in order to be considered distinct enitities (essentially accounts for digitisation error).

Check boxes to choose which layer outputs you want included on the QGIS map canvas, then press run. The various data will show in the series of tabs in the window, and any output layers will be loaded onto the canvas. These layers are memory layers only, and thus will need to be saved to be kept permanently

The reset button clears the tables and plots in preparation for a new  calculation.
