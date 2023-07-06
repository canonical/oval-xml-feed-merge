#!/usr/bin/env python

"""Tests for `oval_xml_feed_merge` package."""
from unittest import mock
from unittest.mock import MagicMock, call

import pytest
import xml.etree.ElementTree as ET

from oval_xml_feed_merge.oval_xml_feed_merge import XMLUtils, OvalXMLFeedMerge


class TestXMLUtils:
    def test_get_xml_root(self):
        xml_string = "<root><child>Content</child></root>"
        expected = ET.fromstring(xml_string)
        mock_xml_file = MagicMock()
        mock_xml_file.read.return_value = xml_string
        actual = XMLUtils.get_xml_root(mock_xml_file)
        assert ET.tostring(actual) == ET.tostring(expected)
        mock_xml_file.seek.assert_called_with(0)


@mock.patch.object(OvalXMLFeedMerge, "setup_output_xml_root", lambda x, y: y)
class TestOvalXMLFeedMerge:
    def test_ctor(self):
        xml_files = ["first.xml", "second.xml"]
        oxfm = OvalXMLFeedMerge(xml_files, "some_file")
        assert oxfm.xml_files == xml_files
        assert oxfm.ns_prefix_map == {}
        assert oxfm.pkgname_to_definition == {}
        assert oxfm.output_xml_root == xml_files[-1]
        assert oxfm.output_file == "some_file"

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
    def test_update_namespace_map(self, mock_xml_file_content, expected_results):
        mock_xml_file = MagicMock(name="test_xml.xml")
        mock_xml_file.__iter__.return_value = mock_xml_file_content
        oxfm = OvalXMLFeedMerge(["something"], None)
        oxfm.update_namespace_map(mock_xml_file)
        assert oxfm.ns_prefix_map == expected_results

    @pytest.mark.parametrize(
        "mock_ns_prefix_map, expected_results",
        [
            (
                {"": "URI for empty prefix", "oval": "Oval prefix namespace URI"},
                [("", "URI for empty prefix"), ("oval", "Oval prefix namespace URI")],
            )
        ],
    )
    def test_register_namespaces(self, mock_ns_prefix_map, expected_results):
        with mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.ET.register_namespace") as mock_reg_ns:
            oxfm = OvalXMLFeedMerge(["something"], None)
            oxfm.ns_prefix_map = mock_ns_prefix_map
            oxfm.register_namespaces()
            mock_reg_ns.assert_has_calls([call(value[0], value[1]) for value in expected_results])

    @pytest.mark.parametrize("test_input, expected_results", [("mock_xml_file", "mock_xml_file")])
    def test_update_ns_map_and_register_ns(self, test_input, expected_results):
        with mock.patch.object(OvalXMLFeedMerge, "update_namespace_map") as mock_update_ns_map, mock.patch.object(
            OvalXMLFeedMerge, "register_namespaces"
        ) as mock_reg_ns:
            oxfm = OvalXMLFeedMerge(["something"], None)
            oxfm.update_ns_map_and_register_ns(test_input)
            mock_update_ns_map.assert_called_with(expected_results)
            mock_reg_ns.assert_called()

    @pytest.mark.parametrize(
        "xml_tree_root_content, mock_ns_prefix_map, expected_pkgname_to_definition_keys",
        [
            (
                '<root><definitions><definition class="non_inventory"><metadata><title>pkg1'
                "</title></metadata></definition></definitions></root>",
                {},
                ["pkg1"],
            ),
            (
                '<root><definitions><definition class="inventory" id="an_id"><metadata><title>pkg1'
                "</title></metadata></definition></definitions></root>",
                {},
                ["an_id"],
            ),
        ],
    )
    def test_update_package_to_definition_map(
        self, xml_tree_root_content, mock_ns_prefix_map, expected_pkgname_to_definition_keys
    ):
        xml_tree_root = ET.fromstring(xml_tree_root_content)
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.ns_prefix_map = mock_ns_prefix_map
        oxfm.update_package_to_definition_map(xml_tree_root)
        assert list(oxfm.pkgname_to_definition.keys()) == expected_pkgname_to_definition_keys

    @pytest.mark.parametrize(
        "element_path, mock_ns_prefix_map, orig_xml_content, xml_root_src_content, appended_xml_content",
        [
            (
                "./definitions",
                {},
                "<root><definitions><definition><metadata><title>pkg1"
                "</title></metadata></definition></definitions></root>",
                "<root><definitions><definition><metadata><title>pkg2"
                "</title></metadata></definition></definitions></root>",
                "<root><definitions>"
                "<definition><metadata><title>pkg1"
                "</title></metadata></definition>"
                "<definition><metadata><title>pkg2"
                "</title></metadata></definition>"
                "</definitions></root>",
            )
        ],
    )
    def test_append_element_to_output(
        self, element_path, mock_ns_prefix_map, orig_xml_content, xml_root_src_content, appended_xml_content
    ):
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.ns_prefix_map = mock_ns_prefix_map
        oxfm.output_xml_root = ET.fromstring(orig_xml_content)
        oxfm.append_element_to_output(ET.fromstring(xml_root_src_content), element_path)
        assert appended_xml_content == ET.tostring(oxfm.output_xml_root, encoding="unicode")

    @mock.patch.object(OvalXMLFeedMerge, "update_ns_map_and_register_ns")
    @mock.patch.object(XMLUtils, "get_xml_root")
    @mock.patch.object(OvalXMLFeedMerge, "update_package_to_definition_map")
    @mock.patch.object(OvalXMLFeedMerge, "append_element_to_output")
    def test_process_xml_file(
        self,
        mock_append_element_to_output,
        mock_update_package_to_definition_map,
        mock_get_xml_root,
        mock_update_ns_map_and_register_ns,
    ):
        mock_xml_tree_root = MagicMock()
        mock_get_xml_root.return_value = mock_xml_tree_root
        xml_file = MagicMock(name="xml_file.xml")
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.process_xml_file(xml_file)
        mock_update_ns_map_and_register_ns.assert_called_with(xml_file)
        mock_get_xml_root.assert_called_with(xml_file)
        mock_update_package_to_definition_map.assert_called_with(mock_xml_tree_root)
        calls = []
        for element in OvalXMLFeedMerge.xml_elements_to_merge:
            calls += [call(mock_xml_tree_root, element)]
        mock_append_element_to_output.assert_has_calls(calls)

    @pytest.mark.parametrize("xml_files", [([MagicMock(name="xml_file1.xml"), MagicMock(name="xml_file2.xml")])])
    @mock.patch.object(OvalXMLFeedMerge, "process_xml_file")
    def test_process_xml_files(self, mock_process_xml_file, xml_files):

        oxfm = OvalXMLFeedMerge(xml_files, None)
        oxfm.process_xml_files()
        calls = []
        for xml_file in xml_files:
            calls += [call(xml_file)]
        mock_process_xml_file.assert_has_calls(calls)

    @pytest.mark.parametrize(
        "mock_pkgname_to_definition, mock_ns_prefix_map, orig_output_xml, expected_output_xml",
        [
            (
                {
                    "pkg1": ET.fromstring("<definition>pkg1</definition>"),
                    "pkg2": ET.fromstring("<definition>pkg2</definition>"),
                },
                {},
                "<root><definitions>" "<definition>pkg0</definition>" "</definitions></root>",
                "<root><definitions>"
                "<definition>pkg1</definition>"
                "<definition>pkg2</definition>"
                "</definitions></root>",
            ),
            (
                {},
                {},
                "<root><definitions>" "<definition>pkg0</definition>" "</definitions></root>",
                "<root><definitions /></root>",
            ),
        ],
    )
    def test_update_definitions_element(
        self, mock_pkgname_to_definition, mock_ns_prefix_map, orig_output_xml, expected_output_xml
    ):
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.pkgname_to_definition = mock_pkgname_to_definition
        oxfm.ns_prefix_map = mock_ns_prefix_map
        oxfm.output_xml_root = ET.fromstring(orig_output_xml)
        oxfm.update_definitions_element()
        assert ET.tostring(oxfm.output_xml_root, encoding="unicode") == expected_output_xml

    @pytest.mark.parametrize("xml_content", ["<root><child>Content</child></root>"])
    def test_produce_output(self, xml_content):
        to_xml = ET.fromstring(xml_content)
        from_xml = ET.tostring(to_xml, encoding="unicode")
        mock_file = MagicMock()
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], mock_file)
        oxfm.output_xml_root = to_xml
        oxfm.produce_output()
        mock_file.write.assert_called_with(from_xml)

    @mock.patch.object(OvalXMLFeedMerge, "produce_output")
    @mock.patch.object(OvalXMLFeedMerge, "update_definitions_element")
    @mock.patch.object(OvalXMLFeedMerge, "process_xml_files")
    def test_merge_oval_xml_feeds(self, mock_process_xml_files, mock_update_definitions_element, mock_produce_output):
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.merge_oval_xml_feeds()
        mock_process_xml_files.assert_called_once()
        mock_update_definitions_element.assert_called_once()
        mock_produce_output.assert_called_once()


class TestNonPatchedOvalXMLFeedMerge:
    @staticmethod
    def _mock_xml_utils_get_xml_root(xml_file):
        mm = MagicMock()
        mm.xml_file = xml_file
        return mm

    @pytest.mark.parametrize(
        "xml_files, mock_ns_prefix_map",
        [
            (
                ["random_xml_file.xml"],
                {},
            )
        ],
    )
    @mock.patch.object(OvalXMLFeedMerge, "update_ns_map_and_register_ns")
    @mock.patch.object(XMLUtils, "get_xml_root", _mock_xml_utils_get_xml_root)
    def test_setup_output_xml_root(self, mock_update_ns_map_and_register_ns, xml_files, mock_ns_prefix_map):
        oxfm = OvalXMLFeedMerge(xml_files, None)
        mock_xml_root = oxfm.output_xml_root
        mock_xml_root.xml_file = xml_files[-1]
        mock_update_ns_map_and_register_ns.assert_called_with(xml_files[-1])
        calls = []
        for xml_element in OvalXMLFeedMerge.xml_elements_to_merge:
            calls += [call(xml_element, mock_ns_prefix_map), call().clear()]
        mock_xml_root.find.assert_has_calls(calls)
