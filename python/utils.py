import os
import sd
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from sd.api import *
from sd.api.sdapplication import SDApplicationPath
from sd.api.sdpackage import SDPackage
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdbasetypes import float2
from sd.ui.graphgrid import GraphGrid


powerSDRootDir = os.path.dirname(__file__)


class PowerSDUtils:
    @staticmethod
    def getPowerSDRootDir():
        return powerSDRootDir


class PowerSDPackageUtils:
    __packageMgr = None

    @staticmethod
    def getDefaultResourcePath():
        return sd.getContext().getSDApplication().getPath(SDApplicationPath.DefaultResourcesDir)

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
        resourcePath = PowerSDPackageUtils.getDefaultResourcePath()
        return packageMgr.loadUserPackage(os.path.join(resourcePath, "packages", "{}.{}".format(packageName, "sbs")))

    @staticmethod
    def findResource(package: SDPackage, identifier: str):
        for resource in package.getChildrenResources(True):
            if resource.getIdentifier() == identifier:
                return resource
        return None

    @staticmethod
    def getGraphResource(graph: SDSBSCompGraph):
        package = graph.getPackage()
        for resource in package.getChildrenResources(True):
            if resource.getIdentifier() == graph.getIdentifier():
                return resource
        return None


class PowerSDFunctionGraphUtils:

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


class PowerSDPropertyUtils:

    @staticmethod
    def exposeInputProperty(node: SDNode, graph: SDGraph, property: SDProperty):
        propertyId = property.getId()
        nodeProperty = node.getPropertyFromId(propertyId, SDPropertyCategory.Input)
        if graph.getPropertyFromId(propertyId, SDPropertyCategory.Input) is None:
            graph.newProperty(propertyId, property.getType(), SDPropertyCategory.Input)
        functionGraph = node.getPropertyGraph(nodeProperty)
        if functionGraph is None:
            functionGraph = node.newPropertyGraph(nodeProperty, "SDSBSFunctionGraph")
        getValueNode = PowerSDFunctionGraphUtils.newGetValueNode(functionGraph, property.getType(), property.getId())
        functionGraph.setOutputNode(getValueNode, True)

    @staticmethod
    def createPropertyFromTemplate(templateProperty: SDProperty, srcGraph: SDGraph, dstGraph: SDGraph):
        property = dstGraph.newProperty(templateProperty.getId(), templateProperty.getType(), SDPropertyCategory.Input)
        annotations = srcGraph.getPropertyAnnotations(templateProperty)
        for annotation in annotations:
            value = srcGraph.getPropertyAnnotationValueFromId(templateProperty, annotation.getId())
            if value is not None and value.get() != "dropdownlist":
                dstGraph.setPropertyAnnotationValueFromId(property, annotation.getId(), value)
        dstGraph.setPropertyValue(property, srcGraph.getPropertyValue(templateProperty))
        return property


class PowerSDNodeUtils:

    @staticmethod
    def setPositionByGridSize(node: SDNode, pos: float2):
        cGridSize = GraphGrid.sGetFirstLevelSize()
        node.setPosition(float2(pos.x * cGridSize, pos.y * cGridSize))


class PowerSDGraphUtils:

    @staticmethod
    def getInputNodes(graph: SDSBSCompGraph):
        inputNodes = []
        for node in graph.getNodes():
            identifier = node.getDefinition().getId()
            if identifier == "sbs::compositing::input_grayscale":
                inputNodes.append((node, True))
            elif identifier == "sbs::compositing::input_color":
                inputNodes.append((node, False))
            else:
                continue
        return inputNodes

    @staticmethod
    def newProperty(
            graph: SDSBSCompGraph,
            srcProperty: SDProperty,
            annotations,  #: dict[SDProperty, SDValue],
            category: SDPropertyCategory):
        propertyTypeMapping = {
            "SDTypeInt": SDTypeInt.sNew(),
            "SDTypeInt2": SDTypeInt2.sNew(),
            "SDTypeInt3": SDTypeInt3.sNew(),
            "SDTypeInt4": SDTypeInt4.sNew(),
            "SDTypeFloat": SDTypeFloat.sNew(),
            "SDTypeFloat2": SDTypeFloat2.sNew(),
            "SDTypeFloat3": SDTypeFloat3.sNew(),
            "SDTypeFloat4": SDTypeFloat4.sNew(),
            "SDTypeBool": SDTypeBool.sNew(),
            "SDTypeString": SDTypeString.sNew(),
            "SDTypeEnum": SDTypeInt.sNew(),
            "SDTypeColorRGB": SDTypeFloat3.sNew(),
            "SDTypeColorRGBA": SDTypeFloat4.sNew(),
        }
        propertyType = propertyTypeMapping[srcProperty.getType().getClassName()]
        property = graph.newProperty(srcProperty.getId(), propertyType, category)
        srcAnnotations = graph.getPropertyAnnotations(srcProperty)
        for annotation, val in annotations.items():
            graph.setPropertyAnnotationValueFromId(property, annotation.getId(), val)


class PowerSDUIUtils:
    __uiMgr = None
    __pathToMenu = {}

    @staticmethod
    def getUIMgr():
        if PowerSDUIUtils.__uiMgr is None:
            PowerSDUIUtils.__uiMgr = sd.getContext().getSDApplication().getQtForPythonUIMgr()
        return PowerSDUIUtils.__uiMgr

    @staticmethod
    def getMenu(menuPath: str, create=False):
        uiMgr = PowerSDUIUtils.getUIMgr()
        menu = PowerSDUIUtils.__pathToMenu.get(menuPath)
        if menu is None and create:
            (parentPath, title) = os.path.split(menuPath)
            if parentPath == "":
                menu = uiMgr.newMenu(menuTitle=title, objectName=title)
            else:
                parent = PowerSDUIUtils.getMenu(parentPath, True)
                menu = parent.addMenu(title)
            PowerSDUIUtils.__pathToMenu[menuPath] = menu
        return menu

    @staticmethod
    def registerMenuItem(menuPath: str, triggered):
        (menu, title) = os.path.split(menuPath)
        menu = PowerSDUIUtils.getMenu(menu, True)
        for action in menu.actions():
            if action.text() == title:
                menu.removeAction(action)
                break
        action = QtWidgets.QAction(title, menu)
        action.triggered.connect(triggered)
        menu.addAction(action)

    @staticmethod
    def loadUIFile(filename: str, parent):
        loader = QtUiTools.QUiLoader()
        uiFile = QtCore.QFile(filename)
        uiFile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uiFile, parent)
        uiFile.close()
        return ui


def initializeSDPlugin():
    print()
