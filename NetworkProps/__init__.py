# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkProps
                                 A QGIS plugin
 determines some properties of networks
                             -------------------
        begin                : 2016-08-30
        copyright            : (C) 2016 by Alex Brown
        email                : valheran@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NetworkProps class from file NetworkProps.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .network_properties import NetworkProps
    return NetworkProps(iface)
