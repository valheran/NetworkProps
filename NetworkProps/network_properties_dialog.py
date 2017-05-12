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
 *   (at your option) any later version.  
 *  Utilises the matplotlib ternary library by Marc Harper, and license therein
 *  Marc Harper et al. (2015). python-ternary: Ternary Plots in Python. Zenodo. 10.5281/zenodo.34938      
    
 *
 ***************************************************************************/
"""
from __future__ import division
import os

from PyQt4 import QtGui, uic, QtCore

import network_properties_utils as utils
import ternary
from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
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
        ##initialise buttons
        self.btn_run.clicked.connect(lambda:self.runAnalysis(utils.getVectorLayerByName(self.cbx_inputLayer.currentText()),self.led_tolerance.text()))
        self.btn_reset.clicked.connect(self.resetData)
        
    def setupFigures(self):
        ##initialise matplot figures/canvas
        self.segLengthFigure = InitHist(self.lyt_segmentLength, self.wdg_toolLength)
        self.segOriFigure = InitRose(self.lyt_segmentOri, self.wdg_toolOri)
        self.ternaryFigure = InitTernary(self.lyt_classification, self.wdg_toolClass)
        #initialise Fry plot figures
        self.fryXnode = InitScatter(self.lyt_fryplot, self.wdg_toolfry, col=0, row=0)
        self.fryYnode = InitScatter(self.lyt_fryplot, self.wdg_toolfry, col=1, row=0)
        self.fryInode = InitScatter(self.lyt_fryplot, self.wdg_toolfry, col = 0, row=2)
        self.fryCnode = InitScatter(self.lyt_fryplot, self.wdg_toolfry, col=1, row=2)
        #initialise Fty Length plot figures
        self.frylenXnode = InitHist(self.lyt_frylen, self.wdg_toolfrylen, col=0, row=0)
        self.frylenYnode = InitHist(self.lyt_frylen, self.wdg_toolfrylen, col=1, row=0)
        self.frylenInode = InitHist(self.lyt_frylen, self.wdg_toolfrylen, col=0, row=2)
        self.frylenCnode = InitHist(self.lyt_frylen, self.wdg_toolfrylen, col=1, row=2)
        #initialise Fry vector orientation figures
        self.fryvecXnode = InitRose(self.lyt_fryvec, self.wdg_toolfryvec, col=0, row=0)
        self.fryvecYnode = InitRose(self.lyt_fryvec, self.wdg_toolfryvec, col=1, row=0)
        self.fryvecInode = InitRose(self.lyt_fryvec, self.wdg_toolfryvec, col=0, row=2)
        self.fryvecCnode = InitRose(self.lyt_fryvec, self.wdg_toolfryvec, col=1, row=2)
        
        
    def manageGui(self):
        
        #populate the combobox
        self.cbx_inputLayer.clear()
        self.cbx_inputLayer.addItems(utils.getVectorLayerNames())
    
    def resetData(self):
        self.segLengthFigure.resetFigure()
        self.segOriFigure.resetFigure()
        self.ternaryFigure.resetFigure()
        self.tbl_Summary.clearContents()
        self.tbl_ratios.clearContents()
        self.led_tolerance.clear()
        self.fryXnode.resetFigure() 
        self.fryYnode.resetFigure() 
        self.fryInode.resetFigure()
        self.fryCnode.resetFigure() 
       
        self.frylenXnode.resetFigure() 
        self.frylenYnode.resetFigure()
        self.frylenInode.resetFigure()
        self.frylenCnode.resetFigure()
       
        self.fryvecXnode.resetFigure() 
        self.fryvecYnode.resetFigure()
        self.fryvecInode.resetFigure()
        self.fryvecCnode.resetFigure()
        
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
        self.tbl_Summary.setItem(6,0, QtGui.QTableWidgetItem("{0:.2f}".format(sum(lenList))))
       
        #populate ratio table
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
                    #print "n, j, ratio", n, j, ratio
                    self.tbl_ratios.setItem(row, col, QtGui.QTableWidgetItem("{0:.2f}".format(ratio)))
                row += 1
            col += 1
            k +=1
        #populate segment length summary table
        self.tbl_segments.setItem(0,0, QtGui.QTableWidgetItem("{0:.2f}".format(sum(lenList))))
        self.tbl_segments.setItem(1,0, QtGui.QTableWidgetItem(str(len(lenList))))
        self.tbl_segments.setItem(2,0, QtGui.QTableWidgetItem("{0:.2f}".format(np.mean(lenList))))
        self.tbl_segments.setItem(3,0, QtGui.QTableWidgetItem("{0:.2f}".format(np.std(lenList))))
        
        #populate segment plots with data
        self.segLengthFigure.histPlotter(lenList, "Segment Lengths")
        self.segOriFigure.rosePlotter(aziList, "Segment Orientation")
        
        #populate the Classification Plots
        point = (len(xnodes)/totalnodes, len(inodes)/totalnodes, len(ynodes)/totalnodes)
        self.ternaryFigure.ternaryPlotter(point)
        
        #perform and plot Fry Analysis
        if self.chk_fry.isChecked():
            if len(inodes)>10:
                iFry = utils.FryAnalysis()
                ifryX,ifryY,ifryLen, ifryVec = iFry.makeFryplotlists(inodes)
                self.fryInode.scatterPlotter(ifryX,ifryY, "I Node Fry Plot")
                self.frylenInode.histPlotter(ifryLen,"I Node Fry Length")
                self.fryvecInode.rosePlotter(ifryVec, "I Node Fry Vector Orientation")
            
            if len(xnodes)>10:
                xFry = utils.FryAnalysis()
                xfryX,xfryY,xfryLen, xfryVec = xFry.makeFryplotlists(xnodes)
                self.fryXnode.scatterPlotter(xfryX,xfryY, "X Node Fry Plot")
                self.frylenXnode.histPlotter(xfryLen,"X Node Fry Length")
                self.fryvecXnode.rosePlotter(xfryVec, "X Node Fry Vector Orientation")
            
            if len(ynodes)>10:
                yFry = utils.FryAnalysis()
                yfryX,yfryY,yfryLen, yfryVec = yFry.makeFryplotlists(ynodes)
                self.fryYnode.scatterPlotter(yfryX,yfryY, "Y Node Fry Plot")
                self.frylenYnode.histPlotter(yfryLen,"Y Node Fry Length")
                self.fryvecYnode.rosePlotter(yfryVec, "Y Node Fry Vector Orientation")
            
            if len(cnodes)>10:
                cFry = utils.FryAnalysis()
                cfryX,cfryY,cfryLen, cfryVec = cFry.makeFryplotlists(cnodes)
                self.fryCnode.scatterPlotter(cfryX,cfryY, "C Node Fry Plot")
                self.frylenCnode.histPlotter(cfryLen,"C Node Fry Length")
                self.fryvecCnode.rosePlotter(cfryVec, "I Node Fry Vector Orientation")
        
        #create output layers
        if self.chk_node.isChecked():
            resultnodelayer = nodecounter.createNodelayer(inodes, ynodes, xnodes, cnodes)
            QgsMapLayerRegistry.instance().addMapLayer(resultnodelayer)
        if self.chk_seg.isChecked():
            resultseglayer = nodecounter.createSeglayer()
            QgsMapLayerRegistry.instance().addMapLayer(resultseglayer)
        
class InitHist:
    #this is the fryplot init - will this work for the histogram?
    def __init__(self, plotTarget, barTarget, col=0, row=0):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        self.col=col
        self.row=row
        self.setupFigure()
        
    def setupFigure(self):   
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas, self.row, self.col)
        self.plotTarget.addWidget(self.mpltoolbar)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"
        
    def histPlotter(self, lenList, title):

        self.axes.clear()
        self.axes.set_title(title)
        x = lenList
        
        count, bin, self.bar = self.axes.hist(x)
        self.figure.canvas.draw()

    def resetFigure(self):
        #plt.close(self.figure)
        #self.setupFigure()
        try:
            t = [b.remove() for b in self.bar]
        except:
            pass
        self.figure.canvas.draw()
        
class InitScatter:
    #this is the fryplot init - will this work for the histogram?
    def __init__(self, plotTarget, barTarget, col=0, row=0):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        self.col=col
        self.row=row
        self.setupFigure()
        
    def setupFigure(self):   
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas, self.row, self.col)
        self.plotTarget.addWidget(self.mpltoolbar, self.row +1, self.col)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"
        
            
    def scatterPlotter(self, listX, listY, title):

        self.axes.clear()
        self.axes.set_title(title, size=9)

        self.scatter = self.axes.scatter(listX,listY,2)
        self.axes.axis('equal')
        self.axes.grid(b=True)
        self.axes.tick_params(labelsize=4)
        self.canvas.draw()   
        
    def resetFigure(self):
        #plt.close(self.figure)
        #self.setupFigure()
        try:
            self.scatter.remove()
            self.setupFigure()
        except:
            pass
        self.figure.canvas.draw()       

class InitTernary:
    #initialise the Ternary classification plot
    def __init__(self, plotTarget, barTarget, col=0, row=0):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        self.col=col
        self.row=row
        self.figure, self.tax = ternary.figure(scale=1)
        self.canvas = FigureCanvas(self.figure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas, self.row, self.col)
        self.plotTarget.addWidget(self.mpltoolbar)
        
         # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"
        self.setupFigure()
        
    def setupFigure(self):
        #self.figure, self.tax = ternary.figure(scale=1)
        #self.canvas = FigureCanvas(self.figure)
        #self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        #lstActions = self.mpltoolbar.actions()
        #self.mpltoolbar.removeAction(lstActions[7])
        #self.plotTarget.addWidget(self.canvas)
        #self.plotTarget.addWidget(self.mpltoolbar)
        self.tax.set_title("Network Classification")
        self.figure.text(0.33,0.85, "I Nodes")
        self.figure.text(0.86,0.05, "X Nodes")
        self.figure.text(0.05,0.05, "Y Nodes")
        self.tax.clear_matplotlib_ticks()
        self.tax.boundary(linewidth=2.0)
        self.tax.gridlines(color="black", multiple=0.1)
        self.tax.left_axis_label("Y", offset=0.5)
        self.tax.right_axis_label("I Nodes", fontsize=12)
        self.tax.bottom_axis_label("X Nodes", fontsize=12)
        self.tax.ticks(axis='lbr', linewidth=1, multiple=0.1)
        
        self.figure.canvas.draw()

     
        
    def ternaryPlotter(self, point):
        #self.tax.clear()
        pt = point
        self.scatter = self.tax.scatter([pt], marker='s', color='red', label="Network Ratio")
        self.figure.canvas.draw()
    def resetFigure(self):
        #plt.close(self.figure)
        self.scatter.clear()
        self.setupFigure()
        self.figure.canvas.draw()
        
   
class InitRose:
    #Create a rose diagram
    def __init__(self, plotTarget, barTarget, col=0, row=0):
         # add matplotlib figure to dialog
        self.plotTarget = plotTarget  
        self.barTarget = barTarget
        self.col=col
        self.row=row
        self.setupFigure()
        
    def setupFigure(self):
        self.rosefigure = Figure()
        self.axes = self.rosefigure.add_subplot(111, polar = True) #set up a plot with polar co-ordinates
        self.axes.set_theta_direction(-1)  #change the direction of increasing angle to match compass
        self.axes.set_theta_zero_location("N") #change the O theta position to North
        self.canvas = FigureCanvas(self.rosefigure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.barTarget)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.plotTarget.addWidget(self.canvas, self.row, self.col)
        self.plotTarget.addWidget(self.mpltoolbar)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono" 
  
    def rosePlotter(self, aziList, title):
    
        self.axes.set_title(title)
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
        
        self.bar = self.axes.bar(direction, frequency, width=awidth, bottom=0.0)
        self.rosefigure.canvas.draw()  
        
    def resetFigure(self):
        #plt.close(self.rosefigure)
        #self.setupFigure()
        try:
            self.bar.remove()
        except:
            pass
    