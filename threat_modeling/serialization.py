import time
import yaml

from typing import List, Optional, Tuple, Union

from threat_modeling.data_flow import (
    Element,
    Dataflow,
    BidirectionalDataflow,
    Process,
    ExternalEntity,
    Datastore,
    Boundary,
)
from threat_modeling.threats import Threat


node_dispatch = {
    "ExternalEntity": ExternalEntity,
    "Process": Process,
    "Element": Element,
    "Datastore": Datastore,
}


def load(
    config: str,
) -> Tuple[
    str,
    str,
    List[Union[Element, ExternalEntity, Process, Datastore]],
    List[Boundary],
    List[Union[Dataflow, BidirectionalDataflow]],
    List[Threat],
]:
    with open(config) as f:
        config_data = yaml.load(f, Loader=yaml.SafeLoader)

    nodes = []
    for node in config_data.get("nodes", []):
        if node["type"] not in node_dispatch.keys():
            raise TypeError("Invalid type for node: {}".format(node["type"]))
        identifier = node.get("id", None)
        description = node.get("description", None)
        node_obj = node_dispatch[node["type"]](node["name"], identifier, description)
        nodes.append(node_obj)

    boundaries = []
    for boundary in config_data.get("boundaries", []):
        identifier = boundary.get("id", None)
        name = boundary.get("name", None)
        description = boundary.get("description", None)
        members = boundary.get("members", [])
        parent = boundary.get("parent", None)
        boundary_obj = Boundary(name, members, identifier, description, parent)
        boundaries.append(boundary_obj)

    dataflows: List[Union[Dataflow, BidirectionalDataflow]] = []
    for dataflow in config_data.get("dataflows", []):
        bidirectional = dataflow.get("bidirectional", False)
        identifier = dataflow.get("id", None)
        description = dataflow.get("description", None)
        if bidirectional:
            bidataflow_obj = BidirectionalDataflow(
                dataflow["first_node"],
                dataflow["second_node"],
                dataflow["name"],
                identifier,
                description,
            )
            dataflows.append(bidataflow_obj)
        else:
            dataflow_obj = Dataflow(
                dataflow["first_node"],
                dataflow["second_node"],
                dataflow["name"],
                identifier,
                description,
            )
            dataflows.append(dataflow_obj)

    threats = []
    for threat in config_data.get("threats", []):
        identifier = threat.get("id", None)
        description = threat.get("description", None)
        name = threat.get("name", None)
        child_threat_ids = threat.get("child_threats", None)
        status = threat.get("status", None)
        base_impact = threat.get("base_impact", None)
        base_exploitability = threat.get("base_exploitability", None)
        threat_obj = Threat(
            name=name,
            identifier=identifier,
            description=description,
            status=status,
            base_impact=base_impact,
            base_exploitability=base_exploitability,
            child_threat_ids=child_threat_ids,
        )
        threats.append(threat_obj)

    name = config_data.get("name", None)
    description = config_data.get("description", None)

    return (name, description, nodes, boundaries, dataflows, threats)


def save(
    elements: List[Element],
    threats: List[Threat],
    name: Optional[str],
    description: Optional[str],
    config: Optional[str],
) -> str:

    if not config:
        config = "threat_model_{}.yaml".format(time.strftime("%Y%m%d-%H%M%S"))

    dataflows = []
    nodes = []
    boundaries = []
    for element in elements:
        element_dict = {"id": str(element.identifier)}
        if element.name:
            element_dict.update({"name": element.name})
        if element.description:
            element_dict.update({"description": element.description})
        if isinstance(element, (Dataflow, BidirectionalDataflow)):
            if isinstance(element, BidirectionalDataflow):
                element_dict.update({"bidirectional": str(True)})
            element_dict.update(
                {
                    "first_node": str(element.first_id),
                    "second_node": str(element.second_id),
                }
            )
            dataflows.append(element_dict)
        elif isinstance(element, Boundary):
            if element.parent:
                element_dict.update({"parent": str(element.parent.identifier)})
            element_dict.update({"members": str([str(x) for x in element.members])})
            boundaries.append(element_dict)
        else:
            element_dict.update({"type": type(element).__name__})
            nodes.append(element_dict)

    threats_to_save = []
    for threat in threats:
        threat_dict = {"id": str(threat.identifier)}
        if threat.name:
            threat_dict.update({"name": threat.name})
        if threat.description:
            threat_dict.update({"description": threat.description})
        if threat.status:
            threat_dict.update({"status": threat.status.name})
        if threat.base_impact:
            threat_dict.update({"base_impact": threat.base_impact.name})
        if threat.base_exploitability:
            threat_dict.update({"base_exploitability": threat.base_exploitability.name})
        if threat.child_threats:
            threat_dict.update(
                {
                    "child_threats": str(
                        [str(x.identifier) for x in threat.child_threats]
                    )
                }
            )
        threats_to_save.append(threat_dict)

    with open(config, "w") as f:
        yaml.dump({"name": name}, f)
        yaml.dump({"description": description}, f)
        yaml.dump({"nodes": nodes}, f)
        yaml.dump({"dataflows": dataflows}, f)
        yaml.dump({"boundaries": boundaries}, f)
        yaml.dump({"threats": threats_to_save}, f)

    return config
