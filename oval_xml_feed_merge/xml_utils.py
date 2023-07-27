import sys
import xml.etree.ElementTree as ET
import logging
from typing import Dict, IO


class XMLUtils:
    @staticmethod
    def get_xml_root(xml_file: IO) -> ET.Element:
        """Get the root element object by parsing xml_file"""
        xml_file.seek(0)
        return ET.fromstring(xml_file.read())

    @staticmethod
    def find_element_by_id(element_id: str, xml_tree_root: ET.Element) -> ET.Element:
        """Return an element object with the attribute "id" equal to "element_id" in the given XML tree"""
        children = xml_tree_root.findall(".//*[@id='{}']".format(element_id))
        if not children:
            logging.critical("No element found with id '{}' ".format(element_id))
            sys.exit(1)
        if len(children) > 1:
            logging.critical("Found more than one element with same id: {}".format(element_id))
            sys.exit(1)
        return children[0]

    @staticmethod
    def generate_id_map(xml_tree_root: ET.Element) -> Dict[str, ET.Element]:
        """Generate and return a map of element identifier to the element object of all elements
        that have the "id" attribute
        """
        id_to_element_map = {}
        for element in xml_tree_root.findall(".//*[@id]"):
            element_id = element.attrib["id"]
            id_to_element_map[element_id] = element
        return id_to_element_map
