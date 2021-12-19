import os
import sd
from sd.api import *
from PySide2 import QtWidgets
from sd.api.sdpackage import SDPackage
from sd.api.sdproperty import SDPropertyCategory


class PowerSDUIUtils:
    __uiMgr = None

    @staticmethod
    def getUIMgr():
        if PowerSDUIUtils.__uiMgr is None:
            PowerSDUIUtils.__uiMgr = sd.getContext().getSDApplication().getQtForPythonUIMgr()
        return PowerSDUIUtils.__uiMgr

    @staticmethod
    def getPowerSDMenu():
        uiMgr = PowerSDUIUtils.getUIMgr()
        menu = uiMgr.findMenuFromObjectName("PowerSD")
        if menu is None:
            menu = uiMgr.newMenu(menuTitle="PowerSD", objectName="PowerSD")
        return menu

    @staticmethod
    def registerMenuItem(menuTitle: str, triggered):
        menu = PowerSDUIUtils.getPowerSDMenu()
        for action in menu.actions():
            if action.text() == menuTitle:
                menu.removeAction(action)
                break
        action = QtWidgets.QAction(menuTitle, menu)
        action.triggered.connect(triggered)
        menu.addAction(action)


class PowerSDPackageUtils:
    __packageMgr = None

    @staticmethod
    def getPackageMgr():
        if PowerSDPackageUtils.__packageMgr is None:
            PowerSDPackageUtils.__packageMgr = sd.getContext().getSDApplication().getPackageMgr()
        return PowerSDPackageUtils.__packageMgr

    @staticmethod
    def findPackage(packageName: str):
        packageMgr = PowerSDPackageUtils.getPackageMgr()
        packages = packageMgr.getPackages()
        for package in packages:
            url = package.getFilePath()
            (path, filename) = os.path.split(url)
            (name, ext) = os.path.splitext(filename)
            if name == packageName:
                return package
        return None

    @staticmethod
    def findResource(package: SDPackage, identifier: str):
        for resource in package.getChildrenResources(True):
            if resource.getIdentifier() == identifier:
                return resource
        return None


class PowerSDFunctionGraphUtils:

    @staticmethod
    def newGetValueNode(functionGraph: SDSBSFunctionGraph, property: SDProperty):
        return PowerSDFunctionGraphUtils.newGetValueNode(functionGraph, property.getType(), property.getId())

    @staticmethod
    def newGetValueNode(functionGraph: SDSBSFunctionGraph, valueType: SDType, identifier: str):
        typeToGetValueNode = {
            "float": "sbs::function::get_float1",
            "float2": "sbs::function::get_float2",
            "float3": "sbs::function::get_float3",
            "float4": "sbs::function::get_float4",
            "int": "sbs::function::get_integer1",
            "int2": "sbs::function::get_integer2",
            "int3": "sbs::function::get_integer3",
            "int4": "sbs::function::get_integer4",
            "bool": "sbs::function::get_bool",
            "str": "sbs::function::get_string",
        }
        getValueNode = functionGraph.newNode(typeToGetValueNode.get(valueType.getId()))
        getValueNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew(identifier))
        return getValueNode


class PowerSDNodeUtils:

    @staticmethod
    def exposeInputProperty(node: SDNode, graph: SDGraph, property: SDProperty):
        propertyId = property.getId()
        print(propertyId)
        nodeProperty = node.getPropertyFromId(propertyId, SDPropertyCategory.Input)
        if graph.getPropertyFromId(propertyId, SDPropertyCategory.Input) is None:
            graph.newProperty(propertyId, property.getType(), SDPropertyCategory.Input)
        functionGraph = node.getPropertyGraph(nodeProperty)
        if functionGraph is None:
            functionGraph = node.newPropertyGraph(nodeProperty, "SDSBSFunctionGraph")
        getValueNode = PowerSDFunctionGraphUtils.newGetValueNode(functionGraph, property)
        functionGraph.setOutputNode(getValueNode, True)


def initializeSDPlugin():
    print()
