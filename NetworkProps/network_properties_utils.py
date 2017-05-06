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
        uri = "Point?&crs={}".format(crsString)
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
                        pr.changeGeometryValues({elem.id(): geom})
                        
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
        y_nodes = []
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
                y_nodes.append(node)
            elif matchcount >=3:
                x_nodes.append(node)
                #may want to check this definition
                
        #print "I nodes", i_nodes
        #print "Y nodes", y_nodes
        #print "X nodes", x_nodes
        i_nodes = list(set(i_nodes))
        y_nodes = list(set(y_nodes))
        x_nodes = list(set(x_nodes))
        c_nodes = list(set(c_nodes))
        
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
        

        
        
        
"""
class FryAnalysis:

    layer = 0
    outLayer = 0
    inputDict={};
    Xo = 0
    Yo = 0
    
    vecList=[]
    lenList=[]
    fryListX=[]
    fryListY=[]
    #fryDict={};

    #some variables to help debugging
    getDataFlag = "no"
    makePseudoFryplotFlag = "no"
    makeFryplotListsFlag = "no"
    
    def __init__(self, layerName, outLayer):
        self.layerName = layerName
        self.outLayer = outLayer
        
        FryAnalysis.layer = getVectorLayerByName(layerName)
        FryAnalysis.outLayer = outLayer
    
    
    
    
    def getData(self):
        #collects up all the coordinate information in the target layer for use in calculations
        
        
        #FryAnalysis.layer = QgsVectorLayer(self.layerName)  from original 
        iter = FryAnalysis.layer.getFeatures()
        spatialIndex = QgsSpatialIndex()
        ID = 0
        maxCox = 0
        maxCoy = 0
        minCox = 99999999999999999999999.999
        minCoy = 99999999999999999999999.999
    
        for elem in iter:
            point = elem.geometry().asPoint()
            xcoord = point.x()
            ycoord = point.y()
            coords = (xcoord, ycoord)
            
            #print coords
            #print elem.id()
            #keep track of the data extents
            if maxCox < xcoord:
                maxCox = xcoord
            if maxCoy < ycoord:
                maxCoy = ycoord
            if minCox > xcoord:
                minCox = xcoord
            if minCoy > ycoord:
                minCoy = ycoord
                
            spatialIndex.insertFeature(elem)
            FryAnalysis.inputDict[ID] = coords;
            ID = ID + 1
            
        #find the approximate centre of the data extent
        XCentre = maxCox - ((maxCox-minCox)/2)
        YCentre = maxCoy - ((maxCoy-minCoy)/2)
        #find nearest actual point to approximate centre
        nearest = spatialIndex.nearestNeighbor(QgsPoint(XCentre, YCentre),1)
        #print for debugging
        #print nearest
        #print XCentre
        #print YCentre
        #set up request for Fid of nearest point
        orifeat = QgsFeatureRequest().setFilterFid(nearest[0])
        #go get the actual feature
        ori = FryAnalysis.layer.getFeatures(orifeat)
        #extract the point as an object
        for ele in ori:
            origin = ele.geometry().asPoint()
            #print origin

        #set variables for origin using extracted nearest point
        FryAnalysis.Xo = origin.x()
        FryAnalysis.Yo = origin.y()
        #QMessageBox.about(None, 'message', 'Get Data was run')
        FryAnalysis.getDatFlag = "yes"
        
    def makePseudoFryplot(self):
        ### need to link with an output layer input
        #self.outLayer = outputLayerName
        tempLayer = QgsVectorLayer("Fry_Points?field=FryVecLen:double&field=FryVecAzi:double", "Fry Points", "memory")
        tempLayer.setCrs(FryAnalysis.layer.crs())
        prov = tempLayer.dataProvider()
        tempLayer.updateFields()
        #get layer name from dialog box input
        QgsVectorFileWriter(FryAnalysis.outLayer, "CP1250", prov.fields(),QGis.WKBPoint , tempLayer.crs(), "ESRI Shapefile", )
        #pathstring = FryAnalysis.outLayer
        #name = pathstring[(pathstring.rfind("\\")+1):pathstring.rfind('.')]
        name = os.path.basename(FryAnalysis.outLayer)
        outputLayer = QgsVectorLayer(FryAnalysis.outLayer, name,"ogr")
        outprov = outputLayer.dataProvider()



        ID=0
        fkey = 0
        resdict= {}
        for i in FryAnalysis.inputDict:
            coord= FryAnalysis.inputDict[ID];
            Xp1 = coord[0]
            Yp1 = coord[1]
            ID2 = 0
            
            for j in FryAnalysis.inputDict:
                coord = FryAnalysis.inputDict[ID2];
                Xp2 = coord[0]
                Yp2 = coord[1]
                if (Xp1 != Xp2 and Yp1 != Yp2):  #skip when central point and target point are the same
                   #co ordinate calculation
                    Xf = FryAnalysis.Xo + (Xp2 - Xp1)
                    Yf = FryAnalysis.Yo + (Yp2 - Yp1)
                    FryPoint = [Xf, Yf]
                    resdict[fkey] = FryPoint;
                    #create Qpoints for length and azimuth calc
                    centfet = QgsPoint(Xp1, Yp1)
                    tarfet = QgsPoint(Xp2, Yp2)
                    #calculate fry vector length and azimuth            
                    sqLength = centfet.sqrDist(tarfet)
                    vecLength = math.sqrt(sqLength)
                    vecAziSign = centfet.azimuth(tarfet)
                    if vecAziSign <0:
                        vecAzi= 360 + vecAziSign
                    else:
                        vecAzi=vecAziSign
                        
                    #output vector lengths to output list
                    #lenList[fkey] = vecLength
                    #output vector azis to output list
                    #vecList[fkey]= vecAzi
                    #create feature and write to output file
                    fryfet= QgsFeature()
                    #set attributes
                    fryfet.setAttributes([vecLength, vecAzi])
                    fryfet.setGeometry(QgsGeometry.fromPoint(QgsPoint(Xf,Yf)))
                   
                    outprov.addFeatures([fryfet])
                    ID2 = ID2 +1
                    fkey= fkey + 1
                else:
                   ID2 = ID2 + 1
                
            ID = ID +1
        #debug output contents of results dictionary
        #for keys in resdict:
        #    print(resdict[keys]) 
        #load into canvas
        QgsMapLayerRegistry.instance().addMapLayer(outputLayer)
 
 
 
    def makeFryplotlists(self):
       #generate fryspace co-ordinates for plotting on graph, as well as vector length and vector azimuth data
        #Iterator for fryspace Co-ordinates
        ID=0
        fkey = 0
        
        Xo = 0
        Yo = 0
        
        for i in FryAnalysis.inputDict:
            coord= FryAnalysis.inputDict[ID];
            Xp1 = coord[0]
            Yp1 = coord[1]
            ID2 = 0
            
            for j in FryAnalysis.inputDict:
                coord = FryAnalysis.inputDict[ID2];
                Xp2 = coord[0]
                Yp2 = coord[1]
                if (Xp1 != Xp2 and Yp1 != Yp2):
                    Xf = Xo + (Xp2 - Xp1)
                    Yf = Yo + (Yp2 - Yp1)
                    FryPoint = [Xf, Yf]
                    
                    #output using seperate lists
                    FryAnalysis.fryListX.append(Xf)
                    FryAnalysis.fryListY.append(Yf)
                    
                    #output frypoint to output dict this was the original idea
                    #FryAnalysis.fryDict[fkey] = FryPoint;
                    #create Qpoints for length and azimuth calc
                    centfet = QgsPoint(Xp1, Yp1)
                    tarfet = QgsPoint(Xp2, Yp2)
                    #calculate fry vector length and azimuth            
                    sqLength = centfet.sqrDist(tarfet)
                    vecLength = math.sqrt(sqLength)
                    vecAziSign = centfet.azimuth(tarfet)
                    if vecAziSign <0:
                        vecAzi= 360 + vecAziSign
                    else:
                        vecAzi=vecAziSign
                        
                    #output vector lengths to output list
                    FryAnalysis.lenList.append(vecLength)
                    #output vector azis to output list
                    FryAnalysis.vecList.append(vecAzi)
                    ID2 = ID2 +1
                    fkey= fkey + 1
                else:
                   ID2 = ID2 + 1
                
            ID = ID +1
            
            #print FryAnalysis.fryListX
"""