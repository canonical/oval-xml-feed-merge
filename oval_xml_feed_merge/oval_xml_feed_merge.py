"""Main module."""
import logging
import re
import xml.etree.ElementTree as ET
from typing import List


class XMLUtils:
    @staticmethod
    def get_xml_root(xml_file):
        """Get the root element object by parsing xml_file"""
        xml_file.seek(0)
        return ET.fromstring(xml_file.read())


class OvalXMLFeedMerge:
    """The contents of the following elements from input XML files are simply appended at the
    appropriate location to the output XML"""

    xml_elements_to_merge = ["./tests", "./objects", "./states", "./variables"]

    def __init__(self, xml_files: List, output_filename):
        self.xml_files = xml_files  # Input files
        self.ns_prefix_map = {}  # Map namespace prefix to URI
        self.pkgname_to_definition = {}  # Map of the package name to "definition" XML element
        self.output_xml_root: ET.Element = self.setup_output_xml_root(xml_files[-1])  # Bootstrap an object to store
        # the output XML
        self.output_file = output_filename

    def update_namespace_map(self, xml_file):
        """Extract all namespace prefixes and URIs from the XML file and update ns_prefix_map"""
        xml_ns_regex_literal = (
            r'xmlns:?([a-z\-]*)="(https?:\/\/(?:www\.)?'
            r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*))"'
        )
        xml_ns_regex = re.compile(xml_ns_regex_literal)
        for line in xml_file:
            for match in xml_ns_regex.finditer(line):
                prefix = match.group(1) if match.group(1) else ""
                uri = match.group(2)
                self.ns_prefix_map[prefix] = uri
        logging.debug(
            "Extracted namespaces from {}.\nUpdated namespace map: {}".format(xml_file.name, self.ns_prefix_map)
        )

    def register_namespaces(self):
        """Register namespace prefixes and URIs so that ET does not generate new namespace prefixes
        when creating the output XML string
        """
        for prefix, uri in self.ns_prefix_map.items():
            ET.register_namespace(prefix, uri)
            logging.debug("Registered namespace {} with prefix: {}".format(uri, prefix))

    def update_ns_map_and_register_ns(self, xml_file):
        """Find namespaces in the XML file and, update the internal ns_prefix_map and register namespaces with ET"""
        self.update_namespace_map(xml_file)
        self.register_namespaces()

    def setup_output_xml_root(self, xml_file):
        """Setup an ET.Element from xml_file that will hold the output XML.
        This will be updated as input files are processed
        """
        self.update_ns_map_and_register_ns(xml_file)
        xml_root = XMLUtils.get_xml_root(xml_file)
        for element in OvalXMLFeedMerge.xml_elements_to_merge:
            xml_root.find(element, self.ns_prefix_map).clear()
        return xml_root

    def update_package_to_definition_map(self, xml_tree_root):
        """Update the pkgname_to_definition map with the package name and its 'definition' element
        from the passed xml_tree_root"""
        for definition in xml_tree_root.find("./definitions", self.ns_prefix_map):
            pkg_name = definition.find("./metadata/title", self.ns_prefix_map).text
            if definition.attrib["class"] == "inventory":
                pkg_name = definition.attrib["id"]  # Preserve unique inventory entries, as they are referenced by other
                # 'definition' elements
                logging.debug('Preserving definition element with class "inventory" for id: {}'.format(pkg_name))
            self.pkgname_to_definition[pkg_name] = definition
            logging.debug("Updated definition XML for package: {}".format(pkg_name))

    def append_element_to_output(self, xml_root_src, element_path):
        """Append the element at element_path from xml_root_src to the output XML at element_path"""
        self.output_xml_root.find(element_path, self.ns_prefix_map).extend(
            xml_root_src.find(element_path, self.ns_prefix_map)
        )

    def process_xml_file(self, xml_file):
        """This function does a few things:
        1. Extract namespaces and prefixes from xml_file and register them with ET
        2. Update pkgname_to_definition from the package entries in xml_file
        3. Append elements listed in xml_elements_to_merge from xml_file into the output XML
        """
        self.update_ns_map_and_register_ns(xml_file)
        xml_tree_root = XMLUtils.get_xml_root(xml_file)
        self.update_package_to_definition_map(xml_tree_root)
        for element in OvalXMLFeedMerge.xml_elements_to_merge:
            self.append_element_to_output(xml_tree_root, element)
            logging.debug("Appended element: {} from file: {} to the output XML".format(element, xml_file.name))

    def process_xml_files(self):
        """Iterate over each input XML file and process it"""
        logging.debug("Processing files")
        for xml_file in self.xml_files:
            logging.debug("-" * 50)
            logging.debug("Processing {}".format(xml_file.name))
            self.process_xml_file(xml_file)
            logging.debug("Processing done for {}".format(xml_file.name))
            logging.debug("-" * 50)

    def update_definitions_element(self):
        """Update the 'definitions' element in the output XML from the pkgname_to_definition map"""
        definitions = self.output_xml_root.find("./definitions", self.ns_prefix_map)
        definitions.clear()
        for definition in self.pkgname_to_definition.values():
            definitions.append(definition)
        logging.debug('Updated the "definitions" element in the output XML')

    def produce_output(self):
        """Dump the output XML to a file"""
        logging.debug("Writing XML to: {}".format(self.output_file.name))
        output_string = ET.tostring(self.output_xml_root, encoding="unicode")
        self.output_file.write(output_string)

    def merge_oval_xml_feeds(self):
        """Self-explanatory"""
        self.process_xml_files()
        self.update_definitions_element()
        self.produce_output()
