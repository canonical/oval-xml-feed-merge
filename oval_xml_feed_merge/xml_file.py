import logging
import os
import re
import sys
from collections import defaultdict
from xml.dom import minidom

from oval_xml_feed_merge.definition_tree import DefinitionTree

from oval_xml_feed_merge.xml_utils import XMLUtils
import xml.etree.ElementTree as ET


class XMLFile:
    def __init__(self, raw_xml_file, ns_prefix_map):
        self.raw_xml_file = raw_xml_file  # Raw file object
        self.name = raw_xml_file.name  # Name of the file on disk or stdout
        self.xml_tree_root = XMLUtils.get_xml_root(raw_xml_file)  # Object of root element in the file
        self.id_to_element_map = XMLUtils.generate_id_map(self.xml_tree_root)  # A map that tracks element identifier
        # to the respective element object

        self.ns_prefix_map = ns_prefix_map  # A map of namespace prefix and URIs
        self.type_to_referenced_ids_map = defaultdict(set)  # A map of element type (test, variable, object, state,
        # definition) to a set of element identifiers that were directly or indirectly referenced by a definition
        # element in the file that is chosen to be written to the output file

    def get_definition_trees(self):
        """Find all definition elements in the current file, create a DefinitionTree object for them and return it"""
        for definition in self.xml_tree_root.find("./definitions", self.ns_prefix_map):
            if definition.attrib["class"] == "inventory":  # Definition elements with class "inventory" are preserved
                # only if referenced by a non-"inventory" definition element chosen to be written to the output file
                continue
            yield DefinitionTree(
                definition, self.ns_prefix_map, self.id_to_element_map, self.type_to_referenced_ids_map
            )

    def get_referenced_elements(self, path):
        """Return all elements relevant to the parameter "path" referenced directly or indirectly by a definition
        element chosen to be written to the output file
        """
        for ref_type, element_ids in self.type_to_referenced_ids_map.items():
            if ref_type in path:
                return [self.id_to_element_map[element_id] for element_id in sorted(element_ids)]  # Sort so that output
                # order is always deterministic

        return []

    def update_namespace_map(self):
        """Extract all namespace prefixes and URIs from the XML file and update ns_prefix_map"""
        xml_ns_regex_literal = (
            r'xmlns:?([a-z\-]*)="(https?:\/\/(?:www\.)?'
            r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*))"'
        )
        xml_ns_regex = re.compile(xml_ns_regex_literal)
        self.raw_xml_file.seek(0)

        for line in self.raw_xml_file:
            for match in xml_ns_regex.finditer(line):
                prefix = match.group(1) if match.group(1) else ""
                uri = match.group(2)
                self.ns_prefix_map[prefix] = uri
        logging.debug(
            "Extracted namespaces from {}.\nUpdated namespace map: {}".format(
                self.raw_xml_file.name, self.ns_prefix_map
            )
        )

    def register_namespaces(self):
        """Register namespace prefixes and URIs so that ET does not generate new namespace prefixes
        when creating the output XML string
        """
        for prefix, uri in self.ns_prefix_map.items():
            ET.register_namespace(prefix, uri)
            logging.debug("Registered namespace {} with prefix: {}".format(uri, prefix))

    def update_ns_map_and_register_ns(self):
        """Find namespaces in the XML file, update the internal ns_prefix_map and register namespaces with ET"""
        self.update_namespace_map()
        self.register_namespaces()

    def clear_elements(self, xml_elements_to_clear):
        """Clear all elements listed in "xml_elements_to_clear" from the current XML file"""
        for element in xml_elements_to_clear:
            logging.debug("Element: {}".format(element))
            self.xml_tree_root.find(element, self.ns_prefix_map).clear()

    def append_element_to_path(self, path, element):
        """Append a single element to the given path"""
        element_at_path = self.xml_tree_root.find(path, self.ns_prefix_map)
        element_at_path.append(element)

    def extend_element_at_path(self, path, elements):
        """Append a sequence of elements to the given path"""
        self.xml_tree_root.find(path, self.ns_prefix_map).extend(elements)

    def validate_xml_ids(self):
        """Validate that each element with an "id" attribute has a unique value for that attribute"""
        element_id_set = set()
        for element in self.xml_tree_root.findall(".//*[@id]"):
            element_id = element.attrib["id"]
            if element_id in element_id_set:
                logging.critical("Found elements with duplicate id '{}'".format(element_id))
                sys.exit(1)
            element_id_set.add(element_id)

    def dump_to_file(self, output_file):
        """Write XML to specified file"""
        output_string = ET.tostring(self.xml_tree_root, encoding="unicode")
        output_string = minidom.parseString(output_string).toprettyxml(indent="  ")
        pretty_output_string = os.linesep.join([s for s in output_string.splitlines() if s.strip()])
        output_file.write(pretty_output_string)
