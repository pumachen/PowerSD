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
    itrValueProperty = itrNode.getPropertyFromId("value", SDPropertyCategory.Input)
    itrValueFunction = itrNode.newPropertyGraph(itrValueProperty, "SDSBSFunctionGraph")
    getIterationNode = itrValueFunction.newNode("sbs::function::get_integer1")
    getIterationNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("iteration"))
    getStartValueNode = itrValueFunction.newNode("sbs::function::get_float1")
    getStartValueNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("startvalue"))
    getIncrementNode = itrValueFunction.newNode("sbs::function::get_float1")
    getIncrementNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("increment"))
    addNode = itrValueFunction.newNode("sbs::function::add")
    mulNode = itrValueFunction.newNode("sbs::function::mul")
    toFloatNode = itrValueFunction.newNode("sbs::function::tofloat")
    getIterationNode.newPropertyConnectionFromId("unique_filter_output", toFloatNode, "value")
    toFloatNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "a")
    getIncrementNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "b")
    getStartValueNode.newPropertyConnectionFromId("unique_filter_output", addNode, "a")
    mulNode.newPropertyConnectionFromId("unique_filter_output", addNode, "b")
    itrValueFunction.setOutputNode(addNode, True)

    itrIValueProperty = itrNode.getPropertyFromId("ivalue", SDPropertyCategory.Input)
    itrIValueFunction = itrNode.newPropertyGraph(itrIValueProperty, "SDSBSFunctionGraph")
    getIterationNode = itrIValueFunction.newNode("sbs::function::get_integer1")
    getIterationNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("iteration"))
    getStartValueNode = itrIValueFunction.newNode("sbs::function::get_float1")
    getStartValueNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("startvalue"))
    getIncrementNode = itrIValueFunction.newNode("sbs::function::get_float1")
    getIncrementNode.setInputPropertyValueFromId("__constant__", SDValueString.sNew("increment"))
    addNode = itrIValueFunction.newNode("sbs::function::add")
    mulNode = itrIValueFunction.newNode("sbs::function::mul")
    toFloatNode = itrIValueFunction.newNode("sbs::function::tofloat")
    toIntNode = itrIValueFunction.newNode("sbs::function::toint1")
    getIterationNode.newPropertyConnectionFromId("unique_filter_output", toFloatNode, "value")
    toFloatNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "a")
    getIncrementNode.newPropertyConnectionFromId("unique_filter_output", mulNode, "b")
    getStartValueNode.newPropertyConnectionFromId("unique_filter_output", addNode, "a")
    mulNode.newPropertyConnectionFromId("unique_filter_output", addNode, "b")
    addNode.newPropertyConnectionFromId("unique_filter_output", toIntNode, "value")
    itrIValueFunction.setOutputNode(toIntNode, True)


def createForLoopGraph(compNode: SDSBSCompNode):
    maxIteration = 10
    srcResource = compNode.getReferencedResource()
    package = srcResource.getPackage()

    graph = SDSBSCompGraph.sNew(package)

    graph.setIdentifier(srcResource.getIdentifier().replace("Iteration", ""))
    cGridSize = GraphGrid.sGetFirstLevelSize()

    inputProperties = [
        graph.newProperty(property.getId(), property.getType(), SDPropertyCategory.Input)
        for property in compNode.getProperties(SDPropertyCategory.Input)
        if not property.getId().startswith("$")
        and not property.getId() == "numiterations"
        and not property.getId() == "iteration"
        and not property.getId() == "value"
        and not property.getId() == "ivalue"
        and not property.isConnectable()]
    inputFeedbackProperties = [
        property for property in compNode.getProperties(SDPropertyCategory.Input)
        if property.getId().startswith("Feedback_")]
    outputFeedbackProperties = [
        property for property in compNode.getProperties(SDPropertyCategory.Output)
        if property.getId().startswith("Feedback_")]
    feedbackProperties = inputFeedbackProperties
    numIterationProperty = graph.newProperty("numiterations", SDTypeInt.sNew(), SDPropertyCategory.Input)
    startValueProperty = graph.newProperty("startvalue", SDTypeFloat.sNew(), SDPropertyCategory.Input)
    incrementProperty = graph.newProperty("increment", SDTypeFloat.sNew(), SDPropertyCategory.Input)
    graph.setPropertyAnnotationValueFromId(numIterationProperty, "min", SDValueInt.sNew(0))
    graph.setPropertyAnnotationValueFromId(numIterationProperty, "max", SDValueInt.sNew(maxIteration))
    graph.setPropertyAnnotationValueFromId(numIterationProperty, "step", SDValueInt.sNew(1))
    graph.setPropertyAnnotationValueFromId(numIterationProperty, "clamp", SDValueBool.sNew(True))
    inputProperties.append(numIterationProperty)

    # Create Input Feedback Nodes
    inputFeedbackNodes = []
    posX = -cGridSize
    posY = 1.5 * cGridSize
    for feedbackProperty in feedbackProperties:
        feedbackId = feedbackProperty.getId()
        inputFeedbackNode = graph.newNode("sbs::compositing::input_grayscale")
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
        itrNode = graph.newInstanceNode(srcResource)
        itrNode.setInputPropertyValueFromId("iteration", SDValueInt.sNew(itr))
        itrNode.setPosition(pos)

        # Create Input Property
        for inputProperty in inputProperties:
            PowerSDNodeUtils.exposeInputProperty(itrNode, graph, inputProperty)
        setIterationProperty(itrNode)

        switchNodes = []
        for feedbackIdx in range(len(feedbackProperties)):
            feedbackProperty = feedbackProperties[feedbackIdx]
            feedbackId = feedbackProperty.getId()

            # Create Switch Node
            switchNode = graph.newInstanceNode(switchGrayscaleResource)
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
        prevItrNode = itrNode
        prevSwitchNodes = switchNodes

    # Create Output Nodes
    posX += 2.5 * cGridSize
    for feedbackIdx in range(len(feedbackProperties)):
        feedbackProperty = feedbackProperties[feedbackIdx]
        prevSwitchNode = prevSwitchNodes[feedbackIdx]
        outputNode = graph.newNode("sbs::compositing::output")
        feedbackId = feedbackProperty.getId()
        outputNode.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew(feedbackId))
        prevSwitchNode.newPropertyConnectionFromId("output", outputNode, "inputNodeOutput")
        outputNode.setPosition(float2(posX, (feedbackIdx + 1) * 1.5 * cGridSize))


def generateLoopGraph():
    selection = PowerSDUIUtils.getUIMgr().getCurrentGraphSelectedNodes()
    node = selection[0]
    if node.getClassName() == "SDSBSCompNode":
        createForLoopGraph(node)


PowerSDUIUtils.registerMenuItem("GenerateLoopGraph", generateLoopGraph)


# Init
# def initializeSDPlugin():
#     PowerSDUIUtils.registerMenuItem("GenerateLoopGraph", generateLoopGraph)
