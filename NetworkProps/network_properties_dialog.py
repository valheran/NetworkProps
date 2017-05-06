# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkPropsDialog
                                 A QGIS plugin
 determines some properties of networks
                             -------------------
        begin                : 2016-08-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Alex Brown
        email                : valheran@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import division
import os

from PyQt4 import QtGui, uic, QtCore

import network_properties_utils as utils
from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
from matplotlib import pyplot as plt

import numpy as np


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'network_properties_dialog_base.ui'))


class NetworkPropsDialog(QtGui.QDialog, FORM_CLASS):

    
    def __init__(self, parent=None):
        """Constructor."""
        super(NetworkPropsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        
        
        self.manageGui()
        ##initialise matplot figures/canvas
        self.segLengthFigure = InitFigure(self.lyt_segmentLength, self.wdg_toolLength)
        self.segOriFigure = InitRose(self.lyt_segmentOri, self.wdg_toolOri)
        
        ##initialise buttons
        self.btn_run.clicked.connect(lambda:self.runAnalysis(utils.getVectorLayerByName(self.cbx_inputLayer.currentText()),self.led_tolerance.text()))
        
    def manageGui(self):
        
        #populate the combobox
        self.cbx_inputLayer.clear()
        self.cbx_inputLayer.addItems(utils.getVectorLayerNames())
    
    
    def showFileBrowser(self, target):
        self.target.setText(QtGui.QFileDialog.getSaveFileName(self, 'Save As', '/',"*.shp"))
        
        
    def runAnalysis(self, layer, tolerance):
        #run the analysis of the network and produce node lists
        nodecounter = utils.NodeCounter(layer, tolerance)
        nodecounter.prepareNetwork()
        nodecounter.deconstructNetwork()
        vertexList = nodecounter.extractNodes()
        inodes, ynodes, xnodes, cnodes = nodecounter.sortNodes(vertexList) 
        totalnodes = len(inodes)+ len(ynodes)+ len(xnodes)+ len(cnodes)
        lenList, aziList = nodecounter.segProps()
        
        #populate summary table
        self.tbl_Summary.setItem(0,0, QtGui.QTableWidgetItem(str(len(inodes))))
        self.tbl_Summary.setItem(1,0, QtGui.QTableWidgetItem(str(len(ynodes))))
        self.tbl_Summary.setItem(2,0, QtGui.QTableWidgetItem(str(len(xnodes))))
        self.tbl_Summary.setItem(3,0, QtGui.QTableWidgetItem(str(len(cnodes))))
        self.tbl_Summary.setItem(4,0, QtGui.QTableWidgetItem(str(totalnodes)))
        self.tbl_Summary.setItem(5,0, QtGui.QTableWidgetItem(str(len(lenList))))
        #populate ratio table
        
        #populate segment plots with data
        statList = [len(inodes), len(ynodes), len(xnodes), len(cnodes), totalnodes, len(lenList)]
        print statList
        k=0
        col =0
        for n in statList:
            
            searchList = statList[:k] + statList[(k+1):]
            print searchList
            row = 0
            for j in searchList:
                if row == k:
                    row+=1
                if j > 0:
                    ratio = float(n/j)
                    print "n, j, ratio", n, j, ratio
                    self.tbl_ratios.setItem(row, col, QtGui.QTableWidgetItem(str(ratio)))
                row += 1
            col += 1
            k +=1
        
        self.segLengthFigure.histPlotter(lenList)
        self.segOriFigure.rosePlotter(aziList)
        #create output layers
        resultnodelayer = nodecounter.createNodelayer(inodes, ynodes, xnodes, cnodes)
        QgsMapLayerRegistry.instance().addMapLayer(resultnodelayer)
        
        
class InitFigure:
    #this is the fryplot init - will this work for the histogram?
    def __init__(self, plotTarget, barTarget):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas)
        self.plotTarget.addWidget(self.mpltoolbar)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"
        
    def histPlotter(self, lenList):
    
     
        self.axes.clear()
        self.axes.set_title("Segment Length Distribution")
        
        x = lenList
        
        self.axes.hist(x)
        self.figure.canvas.draw()
        
class InitRose:
    #Create a rose diagram
    def __init__(self, plotTarget, barTarget):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        
        
        self.rosefigure = Figure()
        self.axes = self.rosefigure.add_subplot(111, polar = True) #set up a plot with polar co-ordinates
        self.axes.set_theta_direction(-1)  #change the direction of increasing angle to match compass
        self.axes.set_theta_zero_location("N") #change the O theta position to North
        self.canvas = FigureCanvas(self.rosefigure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas)
        self.plotTarget.addWidget(self.mpltoolbar)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono" 
  
    def rosePlotter(self, aziList):
    
        self.axes.set_title("Segment Orientation")
        angle = 15 #the width of the divisions of the rose diagram. later stage this could be set by value in dialog box
                 ##get data list
        data = aziList
         #set up bin parameters
        nsection = 360 // angle
        direction = np.linspace(0, 360, nsection, False) / 180 * np.pi
        #print direction
        ##set up list for counting frequency
        frequency = [0] * (nsection)
        ##count up how many in each bin
      
        for i in data:
            
            tmp = int((i - (i % angle)) / angle) ##figure out which bin data belongs
            frequency[tmp] = frequency[tmp] + 1
             
        awidth = angle / 180.0 * np.pi * np.ones(nsection) ## makes an array with nection entries all with the same number representing the angular width
        
        self.axes.bar(direction, frequency, width=awidth, bottom=0.0)
        self.rosefigure.canvas.draw()   