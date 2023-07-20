from unittest import mock
from unittest.mock import MagicMock, call

import pytest
from oval_xml_feed_merge.xml_file import XMLFile

from oval_xml_feed_merge.xml_utils import XMLUtils
import xml.etree.ElementTree as ET


class EchoDict:
    def __getitem__(self, key):
        return key


class TestXMLFile:
    @pytest.mark.parametrize(
        ("raw_xml_file", "ns_prefix_map"),
        [
            (MagicMock(name="test_file.xml"), {"prefix": "URI"}),
        ],
    )
    @mock.patch.object(XMLUtils, "get_xml_root")
    @mock.patch.object(XMLUtils, "generate_id_map")
    def test_ctor(self, mock_generate_id_map, mock_get_xml_root, raw_xml_file, ns_prefix_map):
        """Test the constructor"""
        xml_file = XMLFile(raw_xml_file, ns_prefix_map)
        assert xml_file.raw_xml_file == raw_xml_file
        assert xml_file.name == raw_xml_file.name
        mock_get_xml_root.assert_called_with(raw_xml_file)
        mock_generate_id_map.assert_called()
        assert xml_file.ns_prefix_map == ns_prefix_map
        assert xml_file.type_to_referenced_ids_map == {}
        assert xml_file.type_to_referenced_ids_map["something"] == set()

    @pytest.mark.parametrize(
        ("raw_xml_file_name", "raw_xml_file_content", "expected_definition_element_strings"),
        [
            (
                "test_xml.xml",
                "<root>"
                "<definitions>"
                '<definition class="vulnerability">Definition0<metadata><title>pkg0</title></metadata></definition>'
                '<definition class="vulnerability">Definition1<metadata><title>pkg1</title></metadata></definition>'
                '<definition class="inventory">Definition3<metadata><title>pkg2</title></metadata></definition>'
                "</definitions>"
                "</root>",
                [
                    '<definition class="vulnerability">Definition0<metadata><title>pkg0</title></metadata>'
                    "</definition>",
                    '<definition class="vulnerability">Definition1<metadata><title>pkg1</title></metadata>'
                    "</definition>",
                ],
            )
        ],
    )
    def test_get_definition_trees(self, raw_xml_file_name, raw_xml_file_content, expected_definition_element_strings):
        """Test that get_definition_trees returns DefinitionTree objects with the right definition elements"""
        mock_raw_xml_file = MagicMock(name=raw_xml_file_name)
        mock_raw_xml_file.read.return_value = raw_xml_file_content
        xml_file = XMLFile(mock_raw_xml_file, {})
        actual_definition_element_strings = []
        for definition_tree in xml_file.get_definition_trees():
            definition_element_str = ET.tostring(definition_tree.definition_element, encoding="unicode")
            actual_definition_element_strings += [definition_element_str]
        assert sorted(actual_definition_element_strings) == sorted(expected_definition_element_strings)

    @pytest.mark.parametrize(
        ("type_to_referenced_ids", "id_to_element_map", "test_paths", "expected_element_ids_arr"),
        [
            (
                {"var": {"1", "2", "3"}, "test": {"3", "2", "1"}, "object": {"a", "b", "c"}},
                EchoDict(),
                ["./variables", "./tests", "./objects", "./states"],
                [["1", "2", "3"], ["1", "2", "3"], ["a", "b", "c"], []],
            )
        ],
    )
    @mock.patch.object(XMLUtils, "get_xml_root", new=MagicMock())
    @mock.patch.object(XMLUtils, "generate_id_map", new=MagicMock())
    def test_get_referenced_elements(
        self, type_to_referenced_ids, id_to_element_map, test_paths, expected_element_ids_arr
    ):
        """Make sure get_referenced_elements returns a sorted list of referenced element identifiers for given path"""
        xml_file = XMLFile(MagicMock(), {})
        xml_file.id_to_element_map = id_to_element_map
        xml_file.type_to_referenced_ids_map = type_to_referenced_ids
        for path, expected_element_ids in zip(test_paths, expected_element_ids_arr):
            actual_referenced_element_ids = xml_file.get_referenced_elements(path)
            assert expected_element_ids == actual_referenced_element_ids

    @pytest.mark.parametrize(
        "mock_xml_file_content, expected_results",
        [
            (
                [
                    '<oval_definitions xmlns="http://oval.mitre.org/XMLSchema/oval-definitions-5" '
                    'xmlns:ind-def="http://oval.mitre.org/XMLSchema/oval-definitions-5#independent" '
                    'xmlns:oval="http://oval.mitre.org/XMLSchema/oval-common-5" '
                    'xsi:schemaLocation="http://oval.mitre.org/XMLSchema/oval-common-5 oval-common-schema.xsd">'
                ],
                {
                    "": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
                    "ind-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5#independent",
                    "oval": "http://oval.mitre.org/XMLSchema/oval-common-5",
                },
            ),
            (
                [
                    "<oval_definitions "
                    'xsi:schemaLocation="http://oval.mitre.org/XMLSchema/oval-common-5 oval-common-schema.xsd">'
                ],
                {},
            ),
        ],
    )
    @mock.patch.object(XMLUtils, "get_xml_root", new=MagicMock())
    @mock.patch.object(XMLUtils, "generate_id_map", new=MagicMock())
    def test_update_namespace_map(self, mock_xml_file_content, expected_results):
        """Test that update_namespace_map updates the ns_prefix_map
        with new namespaces and their prefixes from the passed in XML file
        """
        mock_xml_file = MagicMock(name="test_xml.xml")
        mock_xml_file.__iter__.return_value = mock_xml_file_content
        mock_xml_file.read.return_value = "".join(mock_xml_file_content)
        xml_file = XMLFile(mock_xml_file, {})
        xml_file.update_namespace_map()
        assert xml_file.ns_prefix_map == expected_results

    @pytest.mark.parametrize(
        "mock_ns_prefix_map, expected_results",
        [
            (
                {"": "URI for empty prefix", "oval": "Oval prefix namespace URI"},
                [("", "URI for empty prefix"), ("oval", "Oval prefix namespace URI")],
            )
        ],
    )
    @mock.patch.object(XMLUtils, "get_xml_root", new=MagicMock())
    @mock.patch.object(XMLUtils, "generate_id_map", new=MagicMock())
    def test_register_namespaces(self, mock_ns_prefix_map, expected_results):
        """Test that register_namespaces registers the namespace prefixes and URIs present in the ns_prefix_map
        with the xml.etree.ElementTree module"""
        with mock.patch("oval_xml_feed_merge.xml_file.ET.register_namespace") as mock_reg_ns:
            xml_file = XMLFile(MagicMock(), {})
            xml_file.ns_prefix_map = mock_ns_prefix_map
            xml_file.register_namespaces()
            mock_reg_ns.assert_has_calls([call(value[0], value[1]) for value in expected_results])

    @mock.patch.object(XMLUtils, "get_xml_root", new=MagicMock())
    @mock.patch.object(XMLUtils, "generate_id_map", new=MagicMock())
    def test_update_ns_map_and_register_ns(self):
        """Test that update_ns_map_and_register_ns calls update_namespace_map
        and register_namespaces
        """
        with mock.patch.object(XMLFile, "update_namespace_map") as mock_update_ns_map, mock.patch.object(
            XMLFile, "register_namespaces"
        ) as mock_reg_ns:
            xml_file = XMLFile(MagicMock(), {})
            xml_file.update_ns_map_and_register_ns()
            mock_update_ns_map.assert_called()
            mock_reg_ns.assert_called()

    @pytest.mark.parametrize(
        ("xml_file_content", "paths_to_clear", "expected_output_xml"),
        [
            (
                "<root>"
                "<tests><test>Test</test><test>Test1</test></tests>"
                "<objects><object>Object</object><object>Object1</object></objects>"
                "<states><state>State</state></states>"
                "</root>",
                ["./tests", "./objects"],
                "<root>" "<tests /><objects />" "<states><state>State</state></states>" "</root>",
            ),
        ],
    )
    def test_clear_elements(self, xml_file_content, paths_to_clear, expected_output_xml):
        """Test that clear elements clears the specified element paths from the input XML"""
        raw_xml_file = MagicMock(name="test_xml.xml")
        raw_xml_file.read.return_value = xml_file_content
        xml_file = XMLFile(raw_xml_file, {})
        xml_file.clear_elements(paths_to_clear)
        assert ET.tostring(xml_file.xml_tree_root, encoding="unicode") == expected_output_xml

    @pytest.mark.parametrize(
        ("raw_xml_file_content", "append_at_paths", "elements_to_append", "expected_output_xml"),
        [
            (
                "<root>"
                "<tests><test>Test</test><test>Test1</test></tests>"
                "<objects><object>Object</object><object>Object1</object></objects>"
                "<states><state>State</state></states>"
                "</root>",
                ["./tests", "./states"],
                ["<test>Test2</test>", "<state>State1</state>"],
                "<root>"
                "<tests><test>Test</test><test>Test1</test><test>Test2</test></tests>"
                "<objects><object>Object</object><object>Object1</object></objects>"
                "<states><state>State</state><state>State1</state></states>"
                "</root>",
            )
        ],
    )
    def test_append_element_to_path(
        self, raw_xml_file_content, append_at_paths, elements_to_append, expected_output_xml
    ):
        """Test that append_element_to_path appends the input elements at the right place based on the given path
        in the input XML
        """
        raw_xml_file = MagicMock(name="test_xml.xml")
        raw_xml_file.read.return_value = raw_xml_file_content
        xml_file = XMLFile(raw_xml_file, {})
        for path, element in zip(append_at_paths, elements_to_append):
            xml_file.append_element_to_path(path, ET.fromstring(element))

        assert ET.tostring(xml_file.xml_tree_root, encoding="unicode") == expected_output_xml

    @pytest.mark.parametrize(
        ("raw_xml_file_content", "extend_at_paths", "seq_elements_to_extend", "expected_output_xml"),
        [
            (
                "<root>"
                "<tests><test>Test</test><test>Test1</test></tests>"
                "<objects><object>Object</object><object>Object1</object></objects>"
                "<states><state>State</state></states>"
                "</root>",
                ["./tests", "./states"],
                [
                    [ET.fromstring("<test>Test2</test>"), ET.fromstring("<test>Test3</test>")],
                    [ET.fromstring("<state>State1</state>"), ET.fromstring("<state>State2</state>")],
                ],
                "<root>"
                "<tests><test>Test</test><test>Test1</test><test>Test2</test><test>Test3</test></tests>"
                "<objects><object>Object</object><object>Object1</object></objects>"
                "<states><state>State</state><state>State1</state><state>State2</state></states>"
                "</root>",
            )
        ],
    )
    def test_extend_element_at_path(
        self, raw_xml_file_content, extend_at_paths, seq_elements_to_extend, expected_output_xml
    ):
        """Test that extend_element_at_path appends the sequence of input elements at the right place based on the
        given path in the input XML
        """
        raw_xml_file = MagicMock(name="test_xml.xml")
        raw_xml_file.read.return_value = raw_xml_file_content
        xml_file = XMLFile(raw_xml_file, {})
        for path, elements in zip(extend_at_paths, seq_elements_to_extend):
            xml_file.extend_element_at_path(path, elements)

        assert ET.tostring(xml_file.xml_tree_root, encoding="unicode") == expected_output_xml

    @pytest.mark.parametrize(
        ("raw_xml_file_content", "sys_exit_called"),
        [
            ('<root><def id="1"/><def id="2"/></root>', False),
            ('<root><def id="1"/><def id="1"/></root>', True),
        ],
    )
    @mock.patch("oval_xml_feed_merge.xml_file.sys.exit")
    def test_validate_xml_ids(self, mock_sys_exit, raw_xml_file_content, sys_exit_called):
        """Test that validate_xml_ids calls sys.exit when the XML file has duplicate ids"""
        raw_xml_file = MagicMock(name="test_xml.xml")
        raw_xml_file.read.return_value = raw_xml_file_content
        xml_file = XMLFile(raw_xml_file, {})
        xml_file.validate_xml_ids()
        if sys_exit_called:
            mock_sys_exit.assert_called()
        else:
            mock_sys_exit.assert_not_called()

    @pytest.mark.parametrize(
        ("raw_xml_file_content", "expected_xml_string"),
        [
            (
                "<root><child>Content</child></root>",
                '<?xml version="1.0" ?>\n' "<root>\n" "  <child>Content</child>\n" "</root>",
            ),
        ],
    )
    def test_dump_to_file(self, raw_xml_file_content, expected_xml_string):
        """Test that dump_to_file calls write on the output file object
        with the expected XML string
        """
        raw_xml_file = MagicMock(name="test_xml.xml")
        raw_xml_file.read.return_value = raw_xml_file_content
        mock_output_file = MagicMock()
        xml_file = XMLFile(raw_xml_file, {})
        xml_file.dump_to_file(mock_output_file)
        mock_output_file.write.assert_called_with(expected_xml_string)
