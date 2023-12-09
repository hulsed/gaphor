from gaphor.diagram.drop import drop
from gaphor.UML import uml
from gaphor.UML.actions.activity import ActivityItem, ActivityParameterNodeItem


def test_activity_parameter_drop_with_single_activity_and_parameter(
    diagram, element_factory
):
    activity = element_factory.create(uml.Activity)
    activity_item = diagram.create(ActivityItem, subject=activity)

    activity_parameter_node = element_factory.create(uml.ActivityParameterNode)
    activity.node = activity_parameter_node

    parameter_item = drop(activity_parameter_node, diagram, 0, 0)
    assert isinstance(parameter_item, ActivityParameterNodeItem)
    assert parameter_item.subject is activity_parameter_node
    assert parameter_item.parent is activity_item


def test_activity_parameter_drop_with_multiple_activities_and_parameters(
    diagram, element_factory
):
    activity_1 = element_factory.create(uml.Activity)
    activity_2 = element_factory.create(uml.Activity)
    activity_item_1 = diagram.create(ActivityItem, subject=activity_1)
    activity_item_2 = diagram.create(ActivityItem, subject=activity_2)

    activity_parameter_node_1 = element_factory.create(uml.ActivityParameterNode)
    activity_parameter_node_2 = element_factory.create(uml.ActivityParameterNode)
    activity_1.node = activity_parameter_node_1
    activity_2.node = activity_parameter_node_2

    parameter_item_1 = drop(activity_parameter_node_1, diagram, 0, 0)
    parameter_item_2 = drop(activity_parameter_node_2, diagram, 20, 30)

    assert isinstance(parameter_item_1, ActivityParameterNodeItem)
    assert isinstance(parameter_item_2, ActivityParameterNodeItem)
    assert parameter_item_1.subject is activity_parameter_node_1
    assert parameter_item_2.subject is activity_parameter_node_2
    assert parameter_item_1.parent is activity_item_1
    assert parameter_item_2.parent is activity_item_2


def test_activity_parameter_drop_with_two_same_activity_items(diagram, element_factory):
    activity = element_factory.create(uml.Activity)
    activity_item_1 = diagram.create(ActivityItem, subject=activity)
    activity_item_2 = diagram.create(ActivityItem, subject=activity)
    activity_item_1.matrix.translate(50, 50)
    activity_item_2.matrix.translate(300, -200)

    activity_parameter_node = element_factory.create(uml.ActivityParameterNode)
    activity.node = activity_parameter_node

    parameter_item_1 = drop(activity_parameter_node, diagram, 0, 0)
    parameter_item_2 = drop(activity_parameter_node, diagram, 320, -230)

    assert isinstance(parameter_item_1, ActivityParameterNodeItem)
    assert parameter_item_1.subject is activity_parameter_node
    assert parameter_item_1.parent is activity_item_1

    assert isinstance(parameter_item_2, ActivityParameterNodeItem)
    assert parameter_item_2.subject is activity_parameter_node
    assert parameter_item_2.parent is activity_item_2
