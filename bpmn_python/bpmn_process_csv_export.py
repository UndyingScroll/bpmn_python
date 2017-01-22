# coding=utf-8
"""
"""
from __future__ import print_function

import copy
import errno
import os

import bpmn_diagram_exception as bpmn_exception


class BpmnDiagramGraphCsvExport:
    # TODO need to add support for lanes in import/export. After that, read user and add 'who' param
    #TODO Drop the assumption that gateway has only two outgoing flows
    # increase it to the size of alphabet - should be enough for normal users
    gateways_list = ["exclusiveGateway", "inclusiveGateway", "parallelGateway"]
    tasks_list = ["task", "subProcess"]
    '''
    Supported start event types: normal, timer, message.
    Supported end event types: normal, message.
    '''
    events_list = ["startEvent", "endEvent"]
    lanes_list = ["process", "laneSet", "lane"]

    def __init__(self):
        pass

    @staticmethod
    def export_process_to_csv(bpmn_diagram, directory, filename):
        """
        Adds Task node attributes to exported XML element

        :param node_params: dictionary with given task parameters,
        :param output_element: object representing BPMN XML 'task' element.
        """
        incoming_flows_list_param_name = "incoming"
        nodes = copy.deepcopy(bpmn_diagram.get_nodes())
        start_nodes = []
        export_elements = {}

        for node in nodes:
            incoming_list = node[1][incoming_flows_list_param_name]
            if len(incoming_list) == 0:
                start_nodes.append(node)
        if len(start_nodes) != 1:
            raise bpmn_exception.BpmnPythonError("Exporting to CSV format accepts only one start event")

        start_node = start_nodes.pop()
        nodes.remove(start_node)
        BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements, start_node, order=0, prefix="",
                                              condition="", who="")
        sorted_nodes, backward_flows = BpmnDiagramGraphCsvExport.topological_sort_node_ids(bpmn_diagram)

        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        file_object = open(directory + filename, "w")
        file_object.write("Order,Activity,Condition,Who,Subprocess,Terminated\n")
        BpmnDiagramGraphCsvExport.write_export_node_to_file(file_object, export_elements, sorted_nodes)
        file_object.close()

    @staticmethod
    def export_node(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        node_type = node[1]["type"]
        if node_type == "task":
            return BpmnDiagramGraphCsvExport.export_task(bpmn_diagram, export_elements, node, order=order,
                                                         prefix=prefix, condition=condition, who=who)
        elif node_type == "subProcess":
            return BpmnDiagramGraphCsvExport.export_sub_process(bpmn_diagram, export_elements, node, order=order,
                                                                prefix=prefix, condition=condition, who=who)
        elif node_type == "inclusiveGateway":
            return BpmnDiagramGraphCsvExport.export_inclusive_gateway(bpmn_diagram, export_elements, node, order=order,
                                                                      prefix=prefix, condition=condition, who=who)
        elif node_type == "exclusiveGateway":
            return BpmnDiagramGraphCsvExport.export_exclusive_gateway(bpmn_diagram, export_elements, node, order=order,
                                                                      prefix=prefix, condition=condition, who=who)
        elif node_type == "parallelGateway":
            return BpmnDiagramGraphCsvExport.export_parallel_gateway(bpmn_diagram, export_elements, node, order=order,
                                                                     prefix=prefix, condition=condition, who=who)
        elif node_type == "startEvent":
            return BpmnDiagramGraphCsvExport.export_start_event(bpmn_diagram, export_elements, node, order=order,
                                                                prefix=prefix, condition=condition, who=who)
        elif node_type == "endEvent":
            return BpmnDiagramGraphCsvExport.export_end_event(bpmn_diagram, export_elements, node, order=order,
                                                              prefix=prefix, condition=condition, who=who)

    @staticmethod
    def export_start_event(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        export_elements[node[0]] = ({"Order": prefix + str(order), "Activity": node[1]["node_name"],
                                                  "Condition": condition, "Who": who, "Subprocess": "",
                                                  "Terminated": ""})

        outgoing_flow_id = node[1]["outgoing"][0]
        outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
        outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])
        return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                     outgoing_node, order + 1, prefix, who)

    @staticmethod
    def export_end_event(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        export_elements[node[0]] = ({"Order": prefix + str(order), "Activity": node[1]["node_name"],
                                                  "Condition": condition, "Who": who, "Subprocess": "",
                                                  "Terminated": "yes"})

    @staticmethod
    def export_task(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        export_elements[node[0]] = ({"Order": prefix + str(order), "Activity": node[1]["node_name"],
                                                  "Condition": condition, "Who": who, "Subprocess": "",
                                                  "Terminated": ""})
        outgoing_flow_id = node[1]["outgoing"][0]
        outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
        outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])
        return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                     outgoing_node, order + 1, prefix, who)

    @staticmethod
    def export_sub_process(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        export_elements[node[0]] = ({"Order": prefix + str(order), "Activity": node[1]["node_name"],
                                                  "Condition": condition, "Who": who, "Subprocess": "yes",
                                                  "Terminated": ""})
        outgoing_flow_id = node[1]["outgoing"][0]
        outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
        outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])
        return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                     outgoing_node, order + 1, prefix, "", who)

    @staticmethod
    def export_exclusive_gateway(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        outgoing_flows = node[1]["outgoing"]
        if len(outgoing_flows) == 1:
            outgoing_flow_id = outgoing_flows[0]
            outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
            outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])

            return outgoing_node
        elif len(outgoing_flows) == 2:
            outgoing_flow_id_a = outgoing_flows[0]
            outgoing_flow_a = bpmn_diagram.get_flow_by_id(outgoing_flow_id_a)
            outgoing_node_a = bpmn_diagram.get_node_by_id(outgoing_flow_a[2]["target_id"])
            prefix_a = prefix + str(order) + 'a'
            BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                  outgoing_node_a, 1, prefix_a, condition, who)

            outgoing_flow_id_b = outgoing_flows[1]
            outgoing_flow_b = bpmn_diagram.get_flow_by_id(outgoing_flow_id_b)
            outgoing_node_b = bpmn_diagram.get_node_by_id(outgoing_flow_b[2]["target_id"])
            prefix_b = prefix + str(order) + 'b'
            next_node = BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                              outgoing_node_b, 2, prefix_b, "else", who)

            return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                         next_node, order + 1, prefix, "", who)
        else:
            raise bpmn_exception.BpmnPythonError("Exporting to CSV format: gateways must have 1 or 2 outgoing flows")

    @staticmethod
    def export_parallel_gateway(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        outgoing_flows = node[1]["outgoing"]
        if len(outgoing_flows) == 1:
            outgoing_flow_id = outgoing_flows[0]
            outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
            outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])

            return outgoing_node
        elif len(outgoing_flows) == 2:
            outgoing_flow_id_a = outgoing_flows[0]
            outgoing_flow_a = bpmn_diagram.get_flow_by_id(outgoing_flow_id_a)
            outgoing_node_a = bpmn_diagram.get_node_by_id(outgoing_flow_a[2]["target_id"])
            prefix_a = prefix + str(order) + 'a'
            BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                  outgoing_node_a, 1, prefix_a, condition, who)

            outgoing_flow_id_b = outgoing_flows[1]
            outgoing_flow_b = bpmn_diagram.get_flow_by_id(outgoing_flow_id_b)
            outgoing_node_b = bpmn_diagram.get_node_by_id(outgoing_flow_b[2]["target_id"])
            prefix_b = prefix + str(order) + 'b'
            next_node = BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                              outgoing_node_b, 2, prefix_b, "", who)
            return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                         next_node, order + 1, prefix, "", who)
        else:
            raise bpmn_exception.BpmnPythonError("Exporting to CSV format: gateways must have 1 or 2 outgoing flows")

    @staticmethod
    def export_inclusive_gateway(bpmn_diagram, export_elements, node, order=0, prefix="", condition="", who=""):
        outgoing_flows = node[1]["outgoing"]
        if len(outgoing_flows) == 1:
            outgoing_flow_id = outgoing_flows[0]
            outgoing_flow = bpmn_diagram.get_flow_by_id(outgoing_flow_id)
            outgoing_node = bpmn_diagram.get_node_by_id(outgoing_flow[2]["target_id"])

            return outgoing_node
        elif len(outgoing_flows) == 2:
            outgoing_flow_id_a = outgoing_flows[0]
            outgoing_flow_a = bpmn_diagram.get_flow_by_id(outgoing_flow_id_a)
            outgoing_node_a = bpmn_diagram.get_node_by_id(outgoing_flow_a[2]["target_id"])
            prefix_a = prefix + str(order) + 'a'
            condition_a = outgoing_flow_a[2]["name"]
            BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                  outgoing_node_a, 1, prefix_a, condition_a, who)

            outgoing_flow_id_b = outgoing_flows[1]
            outgoing_flow_b = bpmn_diagram.get_flow_by_id(outgoing_flow_id_b)
            outgoing_node_b = bpmn_diagram.get_node_by_id(outgoing_flow_b[2]["target_id"])
            prefix_b = prefix + str(order) + 'b'
            condition_b = outgoing_flow_b[2]["name"]
            next_node = BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                              outgoing_node_b, 2, prefix_b, condition_b, who)
            return BpmnDiagramGraphCsvExport.export_node(bpmn_diagram, export_elements,
                                                         next_node, order + 1, prefix, "", who)
        else:
            raise bpmn_exception.BpmnPythonError("Exporting to CSV format: gateways must have 1 or 2 outgoing flows")

    @staticmethod
    def write_export_node_to_file(file_object, export_elements, sorted_node_ids):
        for node_id in sorted_node_ids:
            export_element = export_elements[node_id]
            file_object.write(
                export_element["Order"] + "," + export_element["Activity"] + "," + export_element["Condition"] + "," +
                export_element["Who"] + "," + export_element["Subprocess"] + "," + export_element["Terminated"] + "\n")

    @staticmethod
    def topological_sort_node_ids(bpmn_graph):
        incoming_flows_list_param_name = "incoming"
        outgoing_flows_list_param_name = "outgoing"
        source_id_param_name = "source_id"
        target_id_param_name = "target_id"

        nodes = bpmn_graph.get_nodes()
        tmp_nodes = copy.deepcopy(bpmn_graph.get_nodes())
        sorted_node_ids = []
        no_incoming_flow_nodes = []
        backward_flows = []

        while tmp_nodes:
            for node in tmp_nodes:
                incoming_list = node[1][incoming_flows_list_param_name]
                if len(incoming_list) == 0:
                    no_incoming_flow_nodes.append(node)
            if len(no_incoming_flow_nodes) > 0:
                while len(no_incoming_flow_nodes) > 0:
                    node = no_incoming_flow_nodes.pop()
                    tmp_nodes.remove(node)

                    next_id = next((tmp_node[0] for tmp_node in nodes if tmp_node[0] == node[0]
                                    and tmp_node[1]["type"] not in BpmnDiagramGraphCsvExport.gateways_list), None)
                    if next_id is not None:
                        sorted_node_ids.append(next_id)

                    outgoing_list = list(node[1][outgoing_flows_list_param_name])
                    tmp_outgoing_list = list(outgoing_list)

                    for flow_id in tmp_outgoing_list:
                        outgoing_list.remove(flow_id)
                        node[1][outgoing_flows_list_param_name].remove(flow_id)

                        flow = bpmn_graph.get_flow_by_id(flow_id)
                        target_id = flow[2][target_id_param_name]
                        target = next(tmp_node
                                      for tmp_node in tmp_nodes
                                      if tmp_node[0] == target_id)
                        target[1][incoming_flows_list_param_name].remove(flow_id)
            else:
                for node in tmp_nodes:
                    if len(node[incoming_flows_list_param_name]) > 0:
                        incoming_list = list(node[1][incoming_flows_list_param_name])
                        tmp_incoming_list = list(incoming_list)
                        for flow_id in tmp_incoming_list:
                            incoming_list.remove(flow_id)
                            flow = bpmn_graph.get_flow_by_id(flow_id)

                            source_id = flow[2][source_id_param_name]
                            source = next(tmp_node
                                          for tmp_node in tmp_nodes
                                          if tmp_node[0] == source_id)
                            source[1][outgoing_flows_list_param_name].remove(flow_id)

                            target_id = flow[2][target_id_param_name]
                            target = next(tmp_node
                                          for tmp_node in tmp_nodes
                                          if tmp_node[0] == target_id)
                            target[1][incoming_flows_list_param_name].remove(flow_id)

                            backward_flows.append(flow)
        return sorted_node_ids, backward_flows