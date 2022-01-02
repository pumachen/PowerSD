import PySide2.QtWidgets
from utils import *
from sd.ui.graphgrid import *
from sd.api.sbs.sdsbscompgraph import *
from sd.api.sbs.sdsbscompnode import *
from sd.api.sdnode import *
from sd.api.sdvalueint import *
from sd.api.sdvaluebool import *
from sd.api.sdtypeint import *
from sd.api.sdtypefloat import *
from sd.api.sdvaluestring import *
from sd.api.sdproperty import *


def setIterationProperty(itrNode: SDSBSCompNode):
    # value Function
    itrValueFunction = itrNode.newPropertyGraph(
        itrNode.getPropertyFromId("value", SDPropertyCategory.Input),
        "SDSBSFunctionGraph")

    getIterationNode = itrValueFunction.newNode("sbs::function::get_integer1")
    getIterationNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("iteration"))
    PowerSDNodeUtils.setPositionByGridSize(getIterationNode, float2(0, 0))

    toFloatNode = itrValueFunction.newNode("sbs::function::tofloat")
    PowerSDNodeUtils.setPositionByGridSize(toFloatNode, float2(1.5, 0))

    getIncrementNode = itrValueFunction.newNode("sbs::function::get_float1")
    getIncrementNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("increment"))
    PowerSDNodeUtils.setPositionByGridSize(getIncrementNode, float2(1.5, -1.5))

    getStartValueNode = itrValueFunction.newNode("sbs::function::get_float1")
    getStartValueNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("startvalue"))
    PowerSDNodeUtils.setPositionByGridSize(getStartValueNode, float2(3, 0.75))

    mulNode = itrValueFunction.newNode("sbs::function::mul")
    PowerSDNodeUtils.setPositionByGridSize(mulNode, float2(3, -0.75))

    addNode = itrValueFunction.newNode("sbs::function::add")
    PowerSDNodeUtils.setPositionByGridSize(addNode, float2(4.5, 0))

    getIterationNode.newPropertyConnectionFromId("unique_filter_output", toFloatNode, "value")
    getIncrementNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "a")
    toFloatNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "b")
    mulNode.newPropertyConnectionFromId("unique_filter_output", addNode, "a")
    getStartValueNode.newPropertyConnectionFromId("unique_filter_output", addNode, "b")
    itrValueFunction.setOutputNode(addNode, True)

    # ivalue Function
    itrIValueFunction = itrNode.newPropertyGraph(
        itrNode.getPropertyFromId("ivalue", SDPropertyCategory.Input),
        "SDSBSFunctionGraph")

    getIterationNode = itrIValueFunction.newNode("sbs::function::get_integer1")
    getIterationNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("iteration"))
    PowerSDNodeUtils.setPositionByGridSize(getIterationNode, float2(0, 0))

    toFloatNode = itrIValueFunction.newNode("sbs::function::tofloat")
    PowerSDNodeUtils.setPositionByGridSize(toFloatNode, float2(1.5, 0))

    getIncrementNode = itrIValueFunction.newNode("sbs::function::get_float1")
    getIncrementNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("increment"))
    PowerSDNodeUtils.setPositionByGridSize(getIncrementNode, float2(1.5, -1.5))

    mulNode = itrIValueFunction.newNode("sbs::function::mul")
    PowerSDNodeUtils.setPositionByGridSize(mulNode, float2(3, -0.75))

    getStartValueNode = itrIValueFunction.newNode("sbs::function::get_float1")
    getStartValueNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("startvalue"))
    PowerSDNodeUtils.setPositionByGridSize(getStartValueNode, float2(3, 0.75))

    addNode = itrIValueFunction.newNode("sbs::function::add")
    PowerSDNodeUtils.setPositionByGridSize(addNode, float2(4.5, 0))

    toIntNode = itrIValueFunction.newNode("sbs::function::toint1")
    PowerSDNodeUtils.setPositionByGridSize(toIntNode, float2(6, 0))

    getIterationNode.newPropertyConnectionFromId("unique_filter_output", toFloatNode, "value")
    getIncrementNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "a")
    toFloatNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "b")
    mulNode.newPropertyConnectionFromId("unique_filter_output", addNode, "a")
    getStartValueNode.newPropertyConnectionFromId("unique_filter_output", addNode, "b")
    addNode.newPropertyConnectionFromId("unique_filter_output", toIntNode, "value")
    itrIValueFunction.setOutputNode(toIntNode, True)


def createLoopGraph(compGraph: SDSBSCompGraph, maxIteration=16):
    with SDHistoryUtils.UndoGroup("Create Loop Graph"):
        package = compGraph.getPackage()
        srcResource = PowerSDPackageUtils.getGraphResource(compGraph)

        loopGraph = SDSBSCompGraph.sNew(package)

        loopGraph.setIdentifier("{}_{}".format(compGraph.getIdentifier(), "Loop"))
        cGridSize = GraphGrid.sGetFirstLevelSize()

        inputProperties = [
            PowerSDPropertyUtils.createPropertyFromTemplate(property, compGraph, loopGraph)
            for property in compGraph.getProperties(SDPropertyCategory.Input)
            if not property.getId().startswith("$")
            and not property.getId() == "numiterations"
            and not property.getId() == "iteration"
            and not property.getId() == "value"
            and not property.getId() == "ivalue"
            and not property.isConnectable()]
        srcInputNodes = PowerSDGraphUtils.getInputNodes(compGraph)
        srcInputFeedbackNodes = [
            (node, isGrayscale) for (node, isGrayscale) in srcInputNodes
            if node.getAnnotationPropertyValueFromId("identifier").get().startswith("Feedback_")]
        srcInputNodes = [
            (node, isGrayscale) for (node, isGrayscale) in srcInputNodes
            if not node.getAnnotationPropertyValueFromId("identifier").get().startswith("Feedback_")]

        outputFeedbackProperties = [
            property for property in compGraph.getProperties(SDPropertyCategory.Output)
            if property.getId().startswith("Feedback_")]
        numIterationProperty = loopGraph.newProperty("numiterations", SDTypeInt.sNew(), SDPropertyCategory.Input)
        startValueProperty = loopGraph.newProperty("startvalue", SDTypeFloat.sNew(), SDPropertyCategory.Input)
        incrementProperty = loopGraph.newProperty("increment", SDTypeFloat.sNew(), SDPropertyCategory.Input)
        loopGraph.setPropertyAnnotationValueFromId(numIterationProperty, "min", SDValueInt.sNew(0))
        loopGraph.setPropertyAnnotationValueFromId(numIterationProperty, "max", SDValueInt.sNew(maxIteration))
        loopGraph.setPropertyAnnotationValueFromId(numIterationProperty, "step", SDValueInt.sNew(1))
        loopGraph.setPropertyAnnotationValueFromId(numIterationProperty, "clamp", SDValueBool.sNew(True))
        loopGraph.setPropertyValue(startValueProperty, SDValueFloat.sNew(0))
        inputProperties.append(numIterationProperty)

        # Create Input Nodes
        inputGrayscaleResource = "sbs::compositing::input_grayscale"
        inputColorResource = "sbs::compositing::input_color"
        inputNodes = []
        for (srcInputNode, isGrayscale) in srcInputNodes:
            inputId = srcInputNode.getAnnotationPropertyValueFromId("identifier").get()
            inputNode = loopGraph.newNode(inputGrayscaleResource if isGrayscale else inputColorResource)
            inputNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(inputId))
            inputNodes.append(inputNode)
        # Create Input Feedback Nodes
        inputFeedbackNodes = []
        posX = -cGridSize
        posY = 1.5 * cGridSize
        for (srcInputFeedbackNode, isGrayscale) in srcInputFeedbackNodes:
            feedbackId = srcInputFeedbackNode.getAnnotationPropertyValueFromId("identifier").get()
            inputResource = inputGrayscaleResource if isGrayscale else inputColorResource
            inputFeedbackNode = loopGraph.newNode(inputResource)
            inputFeedbackNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(feedbackId))
            inputFeedbackNode.setPosition(float2(posX, posY))
            inputFeedbackNodes.append(inputFeedbackNode)
            posY += 1.5 * cGridSize

        # Create Iteration Nodes
        prevItrNode = None
        prevSwitchNodes = []
        blendSwitchPackage = PowerSDPackageUtils.findPackage("blend_switch")
        switchGrayscaleResource = PowerSDPackageUtils.findResource(blendSwitchPackage, "switch_grayscale")
        switchColorResource = PowerSDPackageUtils.findResource(blendSwitchPackage, "switch_color")
        for itr in range(maxIteration):
            posX = itr * 1.5 * cGridSize
            pos = float2(posX, 0)
            itrNode = loopGraph.newInstanceNode(srcResource)
            itrNode.setInputPropertyValueFromId("iteration", SDValueInt.sNew(itr))
            itrNode.setPosition(pos)

            # Create Input Property
            for inputProperty in inputProperties:
                PowerSDPropertyUtils.exposeInputProperty(itrNode, loopGraph, inputProperty)
            setIterationProperty(itrNode)

            switchNodes = []
            for feedbackIdx in range(len(srcInputFeedbackNodes)):
                (srcFeedbackNode, isGrayscale) = srcInputFeedbackNodes[feedbackIdx]
                feedbackId = srcFeedbackNode.getAnnotationPropertyValueFromId("identifier").get()

                # Create Switch Node
                switchResource = switchGrayscaleResource if isGrayscale else switchColorResource
                switchNode = loopGraph.newInstanceNode(switchResource)
                switchNode.setPosition(float2(posX + cGridSize, (feedbackIdx + 1) * 1.5 * cGridSize))
                switchProperty = switchNode.getPropertyFromId("switch", SDPropertyCategory.Input)
                switchGraph = switchNode.newPropertyGraph(switchProperty, "SDSBSFunctionGraph")
                curIterationNode = switchGraph.newNode("sbs::function::const_int1")
                curIterationNode.setInputPropertyValueFromId("__constant__", SDValueInt.sNew(itr))
                numIterationNode = switchGraph.newNode("sbs::function::get_integer1")
                numIterationNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("numiterations"))
                greaterNode = switchGraph.newNode("sbs::function::gt")
                numIterationNode.newPropertyConnectionFromId("unique_filter_output", greaterNode, "a")
                curIterationNode.newPropertyConnectionFromId("unique_filter_output", greaterNode, "b")
                switchGraph.setOutputNode(greaterNode, True)

                if prevItrNode is not None:
                    prevItrNode.newPropertyConnectionFromId(feedbackId, itrNode, feedbackId)
                    prevSwitchNode = prevSwitchNodes[feedbackIdx]
                    prevSwitchNode.newPropertyConnectionFromId("output", switchNode, "input_2")
                else:
                    inputFeedbackNode = inputFeedbackNodes[feedbackIdx]
                    inputFeedbackNode.newPropertyConnectionFromId("unique_filter_output", itrNode, feedbackId)
                    inputFeedbackNode.newPropertyConnectionFromId("unique_filter_output", switchNode, "input_2")
                itrNode.newPropertyConnectionFromId(feedbackId, switchNode, "input_1")
                switchNodes.append(switchNode)
            for inputIdx in range(len(srcInputNodes)):
                inputNode = inputNodes[inputIdx]
                (srcInputNode, isGrayscale) = srcInputNodes[inputIdx]
                inputId = srcInputNode.getAnnotationPropertyValueFromId("identifier").get()
                inputNode.newPropertyConnectionFromId("unique_filter_output", itrNode, inputId)
            prevItrNode = itrNode
            prevSwitchNodes = switchNodes

        # Create Output Nodes
        posX += 2.5 * cGridSize
        for feedbackIdx in range(len(srcInputFeedbackNodes)):
            (srcFeedbackNode, isGrayscale) = srcInputFeedbackNodes[feedbackIdx]
            feedbackId = srcFeedbackNode.getAnnotationPropertyValueFromId("identifier").get()
            prevSwitchNode = prevSwitchNodes[feedbackIdx]
            outputNode = loopGraph.newNode("sbs::compositing::output")
            outputNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(feedbackId))
            prevSwitchNode.newPropertyConnectionFromId("output", outputNode, "inputNodeOutput")
            outputNode.setPosition(float2(posX, (feedbackIdx + 1) * 1.5 * cGridSize))


def createLoopGraphWindow():
    uiMgr = PowerSDUIUtils.getUIMgr()
    graph = uiMgr.getCurrentGraph()
    if graph is None:
        return
    mainWindow = uiMgr.getMainWindow()
    url = os.path.join(PowerSDUtils.getPowerSDRootDir(), "CreateLoopGraph.ui")
    window = PowerSDUIUtils.loadUIFile(url, mainWindow)
    window.show()
    window.buttonBox.accepted.connect(lambda: createLoopGraph(graph, window.max_iterations.value()))


def setupIterationProperties():
    with SDHistoryUtils.UndoGroup("Setup Iteration Properties"):
        graph = PowerSDUIUtils.getUIMgr().getCurrentGraph()
        if graph is None:
            return
        iterationProperty = graph.getPropertyFromId("iteration", SDPropertyCategory.Input)
        if iterationProperty is None:
            iterationProperty = graph.newProperty("iteration", SDTypeInt.sNew(), SDPropertyCategory.Input)
        numiterationsProperty = graph.getPropertyFromId("numiterations", SDPropertyCategory.Input)
        if numiterationsProperty is None:
            numiterationsProperty = graph.newProperty("numiterations", SDTypeInt.sNew(), SDPropertyCategory.Input)
        valueProperty = graph.getPropertyFromId("value", SDPropertyCategory.Input)
        if valueProperty is None:
            valueProperty = graph.newProperty("value", SDTypeFloat.sNew(), SDPropertyCategory.Input)
        ivalueProperty = graph.getPropertyFromId("ivalue", SDPropertyCategory.Input)
        if ivalueProperty is None:
            ivalueProperty = graph.newProperty("ivalue", SDTypeInt.sNew(), SDPropertyCategory.Input)


def addFeedbackNode(identifier: str, isGrayscale: bool):
    with SDHistoryUtils.UndoGroup("Add Feedback Node"):
        graph = PowerSDUIUtils.getUIMgr().getCurrentGraph()
        if graph is None:
            return
        cGridSize = GraphGrid.sGetFirstLevelSize()
        inputFeedbackNode = graph.newNode("sbs::compositing::input_grayscale") \
            if isGrayscale else graph.newNode("sbs::compositing::input_color")
        identifier = "Feedback_{}".format(identifier)
        inputFeedbackNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(identifier))
        inputFeedbackNode.setPosition(float2(0, 0))
        outputFeedbackNode = graph.newNode("sbs::compositing::output")
        outputFeedbackNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(identifier))
        outputFeedbackNode.setPosition(float2(3 * cGridSize, 0))
        inputFeedbackNode.newPropertyConnectionFromId("unique_filter_output", outputFeedbackNode, "inputNodeOutput")


def addFeedbackNodeWindow():
    mainWindow = PowerSDUIUtils.getUIMgr().getMainWindow()
    url = os.path.join(PowerSDUtils.getPowerSDRootDir(), "AddFeedbackNode.ui")
    window = PowerSDUIUtils.loadUIFile(url, mainWindow)
    window.show()
    window.buttonBox.accepted.connect(lambda: addFeedbackNode(window.name.text(), window.color.currentText() == "Grayscale"))
    window.buttonBox.rejected.connect(lambda: window.close())


# Init
def initializeSDPlugin():
    PowerSDUIUtils.registerMenuItem("PowerSD/Loop/Setup Iteration Properties", setupIterationProperties)
    PowerSDUIUtils.registerMenuItem("PowerSD/Loop/Add Feedback Node", addFeedbackNodeWindow)
    PowerSDUIUtils.registerMenuItem("PowerSD/Loop/Create Loop Graph", createLoopGraphWindow)
