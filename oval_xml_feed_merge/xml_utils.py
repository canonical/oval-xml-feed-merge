import functools
import multiprocessing
import re
import sys
import xml.etree.ElementTree as ET
import logging
from io import StringIO
from math import ceil
from typing import Dict, IO, Generator


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

    @staticmethod
    def as_string_io_with_regenerated_ids(raw_xml_file: IO, suffix_int_generator: Generator[int, None, None]) -> IO:
        """Returns content within "raw_xml_file" as a StringIO object with new IDs for OVAL elements
        generated using the suffix_int_generator"""
        xml_file_contents = XMLUtils.regenerate_and_replace_ids(raw_xml_file, suffix_int_generator)
        xml_file_as_io = StringIO(xml_file_contents)
        xml_file_as_io.name = raw_xml_file.name
        return xml_file_as_io

    @staticmethod
    def regenerate_and_replace_ids(raw_xml_file: IO, suffix_int_generator: Generator[int, None, None]) -> str:
        """Finds and replaces OVAL element IDs with new IDs in the "raw_xml_file".
        raw_xml_file contents are split and processed by multiple worker processes
        Result is returned as a str"""
        logging.debug("Regenerating OVAL IDs in {}, this may take a while...".format(raw_xml_file.name))
        xml_file_contents = raw_xml_file.read()
        raw_xml_file.seek(0)
        current_to_new_id_map = {}
        XMLUtils.update_current_to_new_element_id_map(
            current_to_new_id_map, suffix_int_generator, xml_file_contents, raw_xml_file.name
        )
        curried_replace_element_ids_func = functools.partial(XMLUtils.replace_element_ids, current_to_new_id_map)
        pool = multiprocessing.Pool(8)
        xml_file_lines = xml_file_contents.splitlines()
        xml_file_lines = pool.map(curried_replace_element_ids_func, xml_file_lines, ceil(len(xml_file_lines) / 8))
        return "\n".join(xml_file_lines)

    @staticmethod
    def replace_element_ids(current_to_new_id_map: Dict[str, str], xml_file_line: str) -> str:
        """Replaces all keys from current_to_new_id_map present in xml_file_line
        with the replacement mapped in current_to_new_id_map and returns the result str"""
        for current_element_id, new_element_id in current_to_new_id_map.items():
            xml_file_line = xml_file_line.replace(current_element_id, new_element_id)
        return xml_file_line

    @staticmethod
    def update_current_to_new_element_id_map(
        current_to_new_id_map: Dict[str, str],
        suffix_int_generator: Generator[int, None, None],
        xml_file_content: str,
        raw_xml_file_name: str,
    ):
        """Finds OVAL element IDs in xml_file_content and updates current_to_new_id_map with the found
        IDs mapped to new generated ID. IDs are generated using suffix_int_generator"""
        element_id_regex = re.compile(r'id="(oval:.*?)"\s+')
        for match in element_id_regex.finditer(xml_file_content):
            element_id = match.group(1)
            if element_id not in current_to_new_id_map:
                current_to_new_id_map[element_id] = element_id + f"{next(suffix_int_generator):016d}"
                # 16 decimal digits, enough to cover 2^48 ints
            else:
                logging.warning(f"Duplicate element ID: {element_id} in {raw_xml_file_name}")
