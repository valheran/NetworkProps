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

import locale

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import math
import os.path

def getVectorLayerNames():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerNames = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer:
            layerNames.append(unicode(layer.name()))
    return sorted(layerNames, cmp=locale.strcoll)


def getVectorLayerByName(layerName):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None

                
class NodeCounter:
    #class that does the grunt work of network analysis. Cleans the line layer, extracts nodes
    # and determines their type
    def __init__(self,layer, tolerance):
    
        self.layer = layer
        self.tolerance = float(tolerance)
        self.pr = layer.dataProvider()
        crsString = self.layer.crs().authid()
        uri = "LineString?&crs={}".format(crsString)
        self.seglayer = QgsVectorLayer(uri, "segments", "memory")
        self.segpr = self.seglayer.dataProvider()
        #if not layer.isValid():
          #print "Layer failed to load!"

    def prepareNetwork(self):
        #search for intersecting features, and ensure they both have nodes at that location

        featlist = []
        for feat in self.layer.getFeatures():
            #print feat
            featlist.append(feat)
        i =0    
        for testee in featlist:
            i =i+1
            for tester in featlist[i:]:
                #print "tester", tester
                #print "testee", testee
                if not testee == tester:
                    test = tester.geometry().intersects(testee.geometry())
                    #print test
                    if test:
                        #find the intersection
                        inter_point = tester.geometry().intersection(testee.geometry()).asPoint()
                        #determine how close to the nearest vertex on tester
                        sqrdist, atvert  = tester.geometry().closestVertexWithContext(inter_point)
                        closest = math.sqrt(sqrdist)
                        
                        #if the closest vertex is in tolerance, move on
                        if not closest < self.tolerance:
                            #test add new vertex at intersection
                            sqrdist,nearpoint, aftervert = tester.geometry().closestSegmentWithContext(inter_point)
                            geom = tester.geometry()
                            geom.insertVertex(inter_point.x(), inter_point.y(), aftervert)
                            self.pr.changeGeometryValues({tester.id(): geom})
                            
                         #determine how close to the nearest vertex on testee
                        sqrdist, atvert  = testee.geometry().closestVertexWithContext(inter_point)
                        closest = math.sqrt(sqrdist)
                        
                        #if the closest vertex is in tolerance, move on
                        if not closest < self.tolerance:
                            #test add new vertex at intersection
                            sqrdist,nearpoint, aftervert = testee.geometry().closestSegmentWithContext(inter_point)
                            geom = testee.geometry()
                            geom.insertVertex(inter_point.x(), inter_point.y(), aftervert)
                            self.pr.changeGeometryValues({testee.id(): geom})
                        


        #search for y nodes that dont have a corresponding node on the branch within a tolerance
        ytestList = []
        for elem in self.layer.getFeatures():
            for point in elem.geometry().asPolyline():
                ytestList.append(point)
                
                
        #test each feature against each node, if distance is within
        #tolerance, check if nearest vertex is in tolerence, 
        #if not, create one at nearest point
        for elem in self.layer.getFeatures():
            for point in ytestList:
               #check if a vertex exists within tolerance
                sqrdist, atvert  = elem.geometry().closestVertexWithContext(point)
                closest = math.sqrt(sqrdist)
                #print "closest", closest
                #if the closest vertex is in tolerance, do nothing
                if not closest < self.tolerance:
                #check if it should be a y node:
                    sqrdist,nearpoint, aftervert = elem.geometry().closestSegmentWithContext(point)
                    mindist = math.sqrt(sqrdist)
                    #print "mindist", mindist
               #if closest segment is in tolerance, is a y node, insert appropriate vertex
                    if mindist < self.tolerance:
                        geom = elem.geometry()
                       # print geom.asPolyline()
                        geom.insertVertex(nearpoint.x(), nearpoint.y(),aftervert)
                        #print geom.asPolyline()
                        #print geom
                        #print elem.id()
                        self.pr.changeGeometryValues({elem.id(): geom})
                        
                        self.layer.updateExtents()
                    
    def deconstructNetwork(self):
        #deconstruct into single segment lines

        for elem in self.layer.getFeatures():
            vertlist = elem.geometry().asPolyline()
            if len(vertlist) >2:
                #create individual segements
                i=0
                for vert in vertlist[:-1]:
                    seg= QgsGeometry().fromPolyline([vertlist[i], vertlist[i+1]])
                    segfeat = QgsFeature()
                    segfeat.setGeometry(seg)
                    self.segpr.addFeatures([segfeat])
                    i=i+1
            else:
                self.segpr.addFeatures([elem])
            self.seglayer.updateExtents()
        
    def extractNodes(self):
        #Extract nodes
        vertexList = []
        for elem in self.seglayer.getFeatures():
            #print elem.geometry().asPolyline()
            for point in elem.geometry().asPolyline():
                 #print point
                 vertexList.append(point)
                
        return vertexList

    def sortNodes(self, vertexList):
        k=0
        i_nodes = []
        x_nodes = []
        y_nodes_temp = []
        y_nodes=[]
        c_nodes = []
    #inspect every node for proximity within tolerance of another node,
    #and record how many are in the threshold.
        for node in vertexList:
            searchList = vertexList[:k] + vertexList[(k+1):]
            k=k+1
            matchcount = 0
            for othernode in searchList:
                if node.compare(othernode, self.tolerance):
                    matchcount = matchcount +1
                    
            if matchcount == 0:
                i_nodes.append(node)
            elif matchcount == 1:
                c_nodes.append(node)
            elif matchcount == 2:
                y_nodes_temp.append(node)
            elif matchcount >=3:
                x_nodes.append(node)
                #may want to check this definition
                
        #print "I nodes", i_nodes
        #print "Y nodes", y_nodes
        #print "X nodes", x_nodes
        #remove exact duplicates
        i_nodes = list(set(i_nodes))
        y_nodes_temp = list(set(y_nodes_temp))
        x_nodes = list(set(x_nodes))
        c_nodes = list(set(c_nodes))
        
        #remove duplicates within tolerance
        j=0
        for node in y_nodes_temp:
            searchList = y_nodes_temp[(j+1):]
            j=j+1
            single = True
            for othernode in searchList:
                if node.compare(othernode, self.tolerance):
                   single = False
            if single:
                y_nodes.append(node)
                
        
        return i_nodes,y_nodes,x_nodes, c_nodes
        
    def createNodelayer(self, i_nodes,y_nodes,x_nodes, c_nodes):
        
        #print layer.crs()
        crsString = self.layer.crs().authid()
        uri = "Point?field=NodeType:string&crs={}".format(crsString)
        reslayer = QgsVectorLayer(uri, "Nodes", "memory")
        respr = reslayer.dataProvider()
        resList = []
        tempList=[]
        
        for node in i_nodes:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(node))
            feat.setAttributes(["I"])
            tempList.append(feat)
            #respr.addFeatures([feat])
            
        for node in y_nodes:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(node))
            feat.setAttributes(["Y"])
            tempList.append(feat)
            #respr.addFeatures([feat])
            
        for node in x_nodes:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(node))
            feat.setAttributes(["X"])
            tempList.append(feat)
            #respr.addFeatures([feat])
            
        for node in c_nodes:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(node))
            feat.setAttributes(["C"])
            tempList.append(feat)

            #this is left over from original script- was commented out, keeping just in case
            """
            #clean out duplicate nodes in the reslayer
            #print "tempList", tempList, len(tempList)
            
            for j, ft in enumerate(tempList):
                
                searchList = tempList[:j] + tempList[(j+1):]
                #print "searchList", searchList, len(searchList)
                for otherfeat in searchList:
                    #print "j before if", j
                    if ft.geometry().isGeosEqual(otherfeat.geometry()):
                        print "j", j
                        del tempList[j]
                        print "templist length", len(tempList)

            resList = [tempList[0]]
            print "resList", len(resList), resList
            print "templist", len(tempList), tempList

            for ft in tempList:
                print ft
                for otherfeat in resList:
                    print otherfeat.geometry()
                    print ft.geometry()
                    if not ft.geometry().isGeosEqual(otherfeat.geometry()):
                     #   resList.append(ft)
                        print "would add entry here"    
                    else:
                        print "geometries equal"
            """
        
        respr.addFeatures(tempList)
        reslayer.updateExtents()

        return reslayer

    def segProps(self):
        #create a list of segment lengths
        lenList=[]
        aziList = []
        for elem in self.seglayer.getFeatures():
            geom = elem.geometry()
            len = geom.length()
            lenList.append(len)
            start = geom.vertexAt(0)
            end = geom.vertexAt(1)
            AziSign = start.azimuth(end)
            if AziSign <0:
                Azi= 360 + AziSign
            else:
                Azi=AziSign
            aziList.append(Azi)
            
        return lenList, aziList
    
    def createSeglayer(self):
        return self.seglayer

        
        
        

class FryAnalysis:

       
    def __init__(self):
        self.inputDict={};
        self.Xo = 0
        self.Yo = 0
    
        self.vecList=[]
        self.lenList=[]
        self.fryListX=[]
        self.fryListY=[]
    
    
    def listFromLayer(self, tarlayer):
        pointlist=[]
        self.tarlayer = tarlayer
        iter = self.tarlayer.getFeatures()
        for elem in iter:
            point = elem.geometry().asPoint()
            pointlist.append(point)
            
        return pointlist
         
    def makeFryplotlists(self, pointlist):
        #choose a point, and iterate over all other points to obtain fry coords and vectors
        for i in pointlist:
            Xp1 = i.x()
            Yp1 = i.y()
                
            for j in pointlist:
                Xp2 = j.x()
                Yp2 = j.y()
                if (Xp1 != Xp2 and Yp1 != Yp2):
                    Xf = (Xp2 - Xp1)
                    Yf = (Yp2 - Yp1)
                    FryPoint = [Xf, Yf]
                    
                    #output using seperate lists
                    self.fryListX.append(Xf)
                    self.fryListY.append(Yf)
                    
                    
                    #calculate fry vector length and azimuth            
                    sqLength = i.sqrDist(j)
                    vecLength = math.sqrt(sqLength)
                    vecAziSign = i.azimuth(j)
                    if vecAziSign <0:
                        vecAzi= 360 + vecAziSign
                    else:
                        vecAzi=vecAziSign
                        
                    #output vector lengths to output list
                    self.lenList.append(vecLength)
                    #output vector azis to output list
                    self.vecList.append(vecAzi)
        return self.fryListX, self.fryListY, self.lenList, self.vecList
            

