# coding=utf-8
"""
Class used for representing tEndEvent of BPMN 2.0 graph
"""
from graph.classes.events.throw_event_type import ThrowEvent


class EndEvent(ThrowEvent):
    """
    Class used for representing tEndEvent of BPMN 2.0 graph
    """

    def __init__(self):
        """
        Default constructor, initializes object fields with new instances.
        """
        super(EndEvent, self).__init__()