from unittest.mock import MagicMock

import pytest
import xml.etree.ElementTree as ET

from oval_xml_feed_merge.definition_tree import DefinitionTree


class TestDefinitionTree:
    @pytest.mark.parametrize(
        "def_element, pkg_name, ns_prefix_map, id_to_ele_map, type_to_ref_ids_map",
        [
            (
                ET.fromstring("<definition><metadata><title>docker.io</title></metadata></definition>"),
                "docker.io",
                {"prefix": "ns"},
                {"id": "element"},
                {"type": {"id1", "id2"}},
            ),
        ],
    )
    def test_ctor(self, def_element, pkg_name, ns_prefix_map, id_to_ele_map, type_to_ref_ids_map):
        """Test that the constructor initializes the object properly"""
        dt = DefinitionTree(def_element, ns_prefix_map, id_to_ele_map, type_to_ref_ids_map)
        assert ET.tostring(dt.definition_element, encoding="unicode") == ET.tostring(def_element, encoding="unicode")
        assert dt.pkg_name == pkg_name
        assert dt.ns_prefix_map == ns_prefix_map
        assert dt.id_to_element_map == id_to_ele_map
        assert dt.type_to_referenced_ids_map == type_to_ref_ids_map

    @pytest.mark.parametrize(
        "id_to_ele_map, list_of_list_ref_ids, expected_local_type_to_ref_ids_map",
        [
            (
                {"test1": MagicMock(iden="test1"), "object1": MagicMock(iden="object1")},
                [[("test", "test1")], [("object", "object1")]],
                {"test": {"test1"}, "object": {"object1"}},
            )
        ],
    )
    def test_build_referenced_elements_tree(
        self, id_to_ele_map, list_of_list_ref_ids, expected_local_type_to_ref_ids_map
    ):
        """Test that build_referenced_elements_tree finds the referenced elements, starting from the definition element
        traverses the rest of the tree of references and records them in local_type_to_referenced_ids_map"""

        def _mock_find_refs_in_tree(element):
            assert element.iden in id_to_ele_map.keys()
            if len(list_of_list_ref_ids) > 0:
                return list_of_list_ref_ids.pop()
            return []

        dt = DefinitionTree(list(id_to_ele_map.values())[0], {}, id_to_ele_map, {})
        dt.find_refs_in_tree = _mock_find_refs_in_tree
        dt.build_referenced_elements_tree()
        assert dt.local_type_to_referenced_ids_map == expected_local_type_to_ref_ids_map

    @pytest.mark.parametrize(
        "element, expected_ref_ids",
        [
            (ET.fromstring('<tests var_ref="var1" >' '<test object_ref="object1"/>' "</tests>"), [("var", "var1")]),
            (ET.fromstring("<state_ref>state1</state_ref>"), [("state", "state1")]),
        ],
    )
    def test_find_refs_in_element(self, element, expected_ref_ids):
        """Test that find_refs_in_element finds all referenced identifiers in a given element"""
        actual_ref_ids = []
        dt = DefinitionTree(MagicMock(), {}, {}, {})
        dt.find_refs_in_element(element, actual_ref_ids)
        assert sorted(actual_ref_ids) == sorted(expected_ref_ids)

    @pytest.mark.parametrize(
        "element_tree, expected_referenced_ids",
        [
            (
                ET.fromstring(
                    '<test var_ref="var1">'
                    '<state object_ref="object1">'
                    "<var_ref>var2</var_ref>"
                    "</state>"
                    "</test>"
                ),
                [("var", "var1"), ("object", "object1"), ("var", "var2")],
            )
        ],
    )
    def test_find_refs_in_tree(self, element_tree, expected_referenced_ids):
        """Test that find_refs_in_tree finds all referenced identifiers in the current element tree"""
        dt = DefinitionTree(MagicMock(), {}, {}, {})
        actual_referenced_ids = dt.find_refs_in_tree(element_tree)
        assert sorted(actual_referenced_ids) == sorted(expected_referenced_ids)

    @pytest.mark.parametrize(
        "local_type_to_referenced_ids_map, type_to_referenced_ids_map, expected_type_to_referenced_ids_map",
        [
            (
                {
                    "var": {"var1", "var2", "var3"},
                    "object": set(),
                    "state": {"state1", "state2"},
                    "test": {"test2", "test3"},
                },
                {"var": {"var1", "var2"}, "object": {"object1", "object2"}, "state": set(), "test": {"test1"}},
                {
                    "var": {"var1", "var2", "var3"},
                    "object": {"object1", "object2"},
                    "state": {"state1", "state2"},
                    "test": {"test1", "test2", "test3"},
                },
            )
        ],
    )
    def test_sync_referenced_element_ids_to_xml_file(
        self, local_type_to_referenced_ids_map, type_to_referenced_ids_map, expected_type_to_referenced_ids_map
    ):
        """Ensure that sync_referenced_element_ids_to_xml_file adds referenced identifiers to the XML file level
        type_to_referenced_ids_map
        """
        dt = DefinitionTree(MagicMock(), {}, {}, type_to_referenced_ids_map)
        dt.local_type_to_referenced_ids_map = local_type_to_referenced_ids_map
        dt.sync_referenced_element_ids_to_xml_file()
        assert dt.type_to_referenced_ids_map == expected_type_to_referenced_ids_map
