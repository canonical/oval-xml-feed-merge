"""Main module."""
import logging
from typing import List, IO, Dict

from oval_xml_feed_merge.utils import Utils
from oval_xml_feed_merge.xml_utils import XMLUtils

from oval_xml_feed_merge.definition_tree import DefinitionTree
from oval_xml_feed_merge.xml_file import XMLFile
import xml.etree.ElementTree as ET


class OvalXMLFeedMerge:

    """Objects in the following sections of the XML files referenced directly or indirectly by
    definition elements are tracked and merged"""

    xml_elements_to_merge = ["./definitions", "./tests", "./objects", "./states", "./variables"]

    def __init__(self, raw_xml_files: List[IO], output_file: IO):
        self.ns_prefix_map: Dict[str, str] = {}  # Map namespace prefix to URI
        self.pkgname_to_definition_tree: Dict[
            str, DefinitionTree
        ] = {}  # Map of the package name to "definition" XML element
        suffix_generator = Utils.next_int(0)
        global_input_id_set = set()  # A global set to track all seen OVAL IDs
        self.xml_files: List[XMLFile] = [
            XMLFile(
                XMLUtils.as_string_io_with_regenerated_ids(xml_file, suffix_generator, global_input_id_set),
                self.ns_prefix_map,
            )
            for xml_file in raw_xml_files
        ]  # Input files
        self.output_xml_file: XMLFile = self.setup_output_xml_file(raw_xml_files[-1])  # Bootstrap an object to store
        # the output XML

        self.output_file: IO = output_file

    def setup_output_xml_file(self, raw_xml_file: IO) -> XMLFile:
        """Setup an XMLFile object that will be updated with merged contents and finally written to disk or stdout"""
        xml_file = XMLFile(raw_xml_file, self.ns_prefix_map)
        xml_file.update_ns_map_and_register_ns()
        xml_file.clear_elements(OvalXMLFeedMerge.xml_elements_to_merge)
        return xml_file

    def update_package_to_definition_map(self, xml_file: XMLFile):
        """Update the pkgname_to_definition map with the package name and a DefinitionTree object that encapsulates
        its 'definition' element
        If the package already exits in the map, it is discarded and overwritten, thus enforcing the XML file order
        priority. Only the latest definition tree for a given package name is chosen to be written to the output file
        """
        for definition_tree in xml_file.get_definition_trees():
            self.pkgname_to_definition_tree[definition_tree.pkg_name] = definition_tree
            definition_tree.build_referenced_elements_tree()
            logging.debug("Updated definition XML for package: {}".format(definition_tree.pkg_name))

    def process_xml_file(self, xml_file: XMLFile):
        """This function does a couple of things:
        1. Extract namespaces and prefixes from xml_file and register them with ET
        2. Update pkgname_to_definition from the package entries in xml_file
        """
        xml_file.update_ns_map_and_register_ns()
        self.update_package_to_definition_map(xml_file)

    def process_xml_files(self):
        """Iterate over each input XML file and process it"""
        logging.debug("Processing files")
        for xml_file in self.xml_files:
            logging.debug("-" * 50)
            logging.debug("Processing {}".format(xml_file.name))
            self.process_xml_file(xml_file)
            logging.debug("Processing done for {}".format(xml_file.name))
            logging.debug("-" * 50)

    def update_definition_element_references_at_path(self, element_path: str):
        """Get elements directly or indirectly referenced by a definition element chosen to be written to the
        output file and add them to the output file as well"""
        referenced_elements: List[ET.Element] = []
        for xml_file in self.xml_files:
            referenced_elements += xml_file.get_referenced_elements(element_path)
        self.output_xml_file.extend_element_at_path(element_path, referenced_elements)

    def update_definitions_element_and_references(self):
        """Update the 'definitions' element along with all XML elements that are referenced by individual
        definition elemnts in the output XML from the pkgname_to_definition map"""
        for definition_tree in self.pkgname_to_definition_tree.values():
            self.output_xml_file.append_element_to_path("./definitions", definition_tree.definition_element)
            definition_tree.sync_referenced_element_ids_to_xml_file()

        for element_path in OvalXMLFeedMerge.xml_elements_to_merge:
            self.update_definition_element_references_at_path(element_path)
        logging.debug("Updated the 'definitions' element and its dependencies in the output XML")

    def validate_and_produce_output(self):
        """Validate and dump the output XML to a file"""
        self.output_xml_file.validate_xml_ids()
        logging.debug("Writing XML to: {}".format(self.output_file.name))
        self.output_xml_file.dump_to_file(self.output_file)

    def merge_oval_xml_feeds(self):
        """Self-explanatory"""
        self.process_xml_files()
        self.update_definitions_element_and_references()
        self.validate_and_produce_output()
