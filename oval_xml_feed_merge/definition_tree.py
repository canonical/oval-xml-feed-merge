import re
from collections import defaultdict


class DefinitionTree:
    def __init__(self, definition_element, ns_prefix_map, id_to_element_map, type_to_referenced_ids_map):
        self.definition_element = definition_element  # XML Element object
        self.pkg_name = definition_element.find("./metadata/title", ns_prefix_map).text  # Package name
        self.ns_prefix_map = ns_prefix_map  # A map of namespace prefix and URIs
        self.id_to_element_map = id_to_element_map  # A map that tracks element identifier
        # to the respective element object

        self.type_to_referenced_ids_map = type_to_referenced_ids_map  # A map of element type (test, variable, object,
        # state, definition) to a set of element identifiers that were directly or indirectly referenced by a
        # definition element that is chosen to be written to the output file. The current DefinitionTree
        # object will update this map only when chosen to be written to the output file

        self.local_type_to_referenced_ids_map = defaultdict(set)  # A map of element type (test, variable, object,
        # state, definition) to a set of element identifiers that were directly or indirectly referenced by a
        # definition element.

        self.ref_attr_regex = re.compile(r"([a-z]+)_ref")  # Regex to find references to other XML elements

    def build_referenced_elements_tree(self):
        """Find all the element identifiers and the element objects themselves referenced directly or indirectly by
        the current definition element
        """
        referenced_ids = self.find_refs_in_tree(self.definition_element)
        while referenced_ids:
            ref_type, referenced_id = referenced_ids.pop()
            referenced_element = self.id_to_element_map[referenced_id]
            self.local_type_to_referenced_ids_map[ref_type].add(referenced_id)
            referenced_ids += self.find_refs_in_tree(referenced_element)

    def find_refs_in_element(self, element, referenced_ids):
        """Find references to the identifiers of other XML elements in the given element
        and return them
        """

        for attr, val in element.attrib.items():
            match = self.ref_attr_regex.match(attr)
            if match:
                referenced_ids += [(match.group(1), val)]
        match = self.ref_attr_regex.search(element.tag)
        if match:
            referenced_ids += [(match.group(1), element.text)]

    def find_refs_in_tree(self, root_element):
        """Find references to the identifiers of other XML elements in the given element and its children
        and return them"""
        referenced_ids = []
        for child in root_element.iter():
            self.find_refs_in_element(child, referenced_ids)
        return referenced_ids

    def sync_referenced_element_ids_to_xml_file(self):
        """This DefinitionTree object's definition element has been chosen to be written to the output XML.
        Add all the elements from the local_type_to_referenced_ids_map to the associated XML file's
        type_to_referenced_ids_map
        """
        for ref_type, referenced_element_ids in self.local_type_to_referenced_ids_map.items():
            self.type_to_referenced_ids_map[ref_type] |= referenced_element_ids
