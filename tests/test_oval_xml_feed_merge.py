#!/usr/bin/env python

"""Tests for `oval_xml_feed_merge` package."""
from unittest import mock
from unittest.mock import MagicMock, call

import pytest
import xml.etree.ElementTree as ET


from oval_xml_feed_merge.oval_xml_feed_merge import OvalXMLFeedMerge


@mock.patch.object(OvalXMLFeedMerge, "setup_output_xml_file", lambda x, y: y)
class TestOvalXMLFeedMergeTestCtor:
    @pytest.mark.parametrize(("xml_file_names",), [(["first.xml", "second.xml"],)])
    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLFile")
    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLUtils.as_string_io_with_regenerated_ids")
    def test_ctor(self, mock_as_string_io, mock_xml_file, xml_file_names):
        """Test that OvalXMLFeedMerge constructor initializes all attributes to the expected values"""
        mock_as_string_io.side_effect = lambda x, y: x
        mock_output_file = MagicMock()
        oxfm = OvalXMLFeedMerge(xml_file_names, mock_output_file)
        calls = []
        for xml_file_name in xml_file_names:
            calls += [call(xml_file_name, {})]
        mock_xml_file.assert_has_calls(calls)
        assert mock_as_string_io.call_count == len(xml_file_names)
        assert oxfm.ns_prefix_map == {}
        assert oxfm.pkgname_to_definition_tree == {}
        assert oxfm.output_file == mock_output_file


@mock.patch.object(OvalXMLFeedMerge, "setup_output_xml_file", lambda x, y: y)
@mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLFile", new=MagicMock())
@mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLUtils.as_string_io_with_regenerated_ids", new=MagicMock())
class TestOvalXMLFeedMerge:
    @pytest.mark.parametrize(
        "definition_trees, expected_pkgnames",
        [
            ([MagicMock(pkg_name="docker.io"), MagicMock(pkg_name="vim")], ["docker.io", "vim"]),
        ],
    )
    def test_update_package_to_definition_map(self, definition_trees, expected_pkgnames):
        """Test that update_package_to_definition_map updates the pkgname_to_definition dictionary with the expected
        definition tree objects
        """
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        mock_xml_file = MagicMock()
        mock_xml_file.get_definition_trees.return_value = definition_trees
        oxfm.update_package_to_definition_map(mock_xml_file)
        assert list(oxfm.pkgname_to_definition_tree.keys()) == expected_pkgnames
        for definition_tree in definition_trees:
            definition_tree.build_referenced_elements_tree.assert_called()

    @pytest.mark.parametrize(
        "definition_trees, expected_pkgnames",
        [
            ([MagicMock(pkg_name="docker.io"), MagicMock(pkg_name="vim")], ["docker.io", "vim"]),
        ],
    )
    def test_process_xml_file(self, definition_trees, expected_pkgnames):
        """Test that process_xml_file calls update_package_to_definition_map and update_ns_map_and_register_ns"""
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        mock_xml_file = MagicMock()
        mock_xml_file.get_definition_trees.return_value = definition_trees
        oxfm.process_xml_file(mock_xml_file)
        mock_xml_file.update_ns_map_and_register_ns.assert_called()
        assert list(oxfm.pkgname_to_definition_tree.keys()) == expected_pkgnames
        for definition_tree in definition_trees:
            definition_tree.build_referenced_elements_tree.assert_called()

    @pytest.mark.parametrize("xml_files", [([MagicMock(name="xml_file1.xml"), MagicMock(name="xml_file2.xml")])])
    @mock.patch.object(OvalXMLFeedMerge, "process_xml_file")
    def test_process_xml_files(self, mock_process_xml_file, xml_files):
        """Test that process_xml_files iterates over the list of input XML files and calls process_xml_file on
        each file"""
        oxfm = OvalXMLFeedMerge(xml_files, None)
        oxfm.xml_files = xml_files
        oxfm.process_xml_files()
        calls = []
        for xml_file in xml_files:
            calls += [call(xml_file)]
        mock_process_xml_file.assert_has_calls(calls)

    @pytest.mark.parametrize(
        "element_path, xml_files_referenced_elements, expected_referenced_elements",
        [
            (
                "./tests",
                [["element1", "element2"], ["element3", "element4"]],
                ["element1", "element2", "element3", "element4"],
            )
        ],
    )
    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLFile", new=MagicMock())
    def test_update_definition_element_references_at_path(
        self, element_path, xml_files_referenced_elements, expected_referenced_elements
    ):
        """Test update_definition_element_references_at_path adds all the referenced elements across all input XML files
        to the output XML
        """
        mock_output_xml_file = MagicMock()
        xml_files = []
        for referenced_elements in xml_files_referenced_elements:
            xml_file = MagicMock()
            xml_file.get_referenced_elements.return_value = referenced_elements
            xml_files += [xml_file]

        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.xml_files = xml_files
        oxfm.output_xml_file = mock_output_xml_file
        oxfm.update_definition_element_references_at_path(element_path)
        for xml_file in xml_files:
            xml_file.get_referenced_elements.assert_called_with(element_path)

        mock_output_xml_file.extend_element_at_path.assert_called_with(element_path, expected_referenced_elements)

    @pytest.mark.parametrize(
        "pkgname_to_def_tree, definition_element_list, xml_elements_to_merge",
        [
            (
                {
                    "docker.io": MagicMock(definition_element="docker.io_xml"),
                    "vim": MagicMock(definition_element="vim_xml"),
                },
                ["docker.io_xml", "vim_xml"],
                ["./tests", "./definitions"],
            )
        ],
    )
    @mock.patch.object(OvalXMLFeedMerge, "update_definition_element_references_at_path")
    @mock.patch.object(OvalXMLFeedMerge, "xml_elements_to_merge", new=["./tests", "./definitions"])
    def test_update_definitions_element_and_references(
        self,
        mock_update_definition_element_references_at_path,
        pkgname_to_def_tree,
        definition_element_list,
        xml_elements_to_merge,
    ):
        """Test that definition_tree objects in pkgname_to_definition are appended to the output_xml_file,
        and elements referenced within those definition_tree objects are updated at their respective element paths
        """
        mock_output_xml_file = MagicMock()
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.pkgname_to_definition_tree = pkgname_to_def_tree
        oxfm.output_xml_file = mock_output_xml_file
        oxfm.update_definitions_element_and_references()

        calls = []
        for definition_element in definition_element_list:
            calls += [call("./definitions", definition_element)]
        mock_output_xml_file.append_element_to_path.assert_has_calls(calls)
        for def_tree in pkgname_to_def_tree.values():
            def_tree.sync_referenced_element_ids_to_xml_file.assert_called()
        mock_update_definition_element_references_at_path.assert_has_calls(
            [call(element) for element in xml_elements_to_merge]
        )

    def test_validate_and_produce_output(self):
        """Test that produce_output calls write on the output file object
        with the expected XML string"""
        mock_output_xml_file = MagicMock()
        mock_output_file = MagicMock()
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.output_xml_file = mock_output_xml_file
        oxfm.output_file = mock_output_file
        oxfm.validate_and_produce_output()
        mock_output_xml_file.validate_xml_ids.assert_called()
        mock_output_xml_file.dump_to_file.assert_called_with(mock_output_file)

    @mock.patch.object(OvalXMLFeedMerge, "validate_and_produce_output")
    @mock.patch.object(OvalXMLFeedMerge, "update_definitions_element_and_references")
    @mock.patch.object(OvalXMLFeedMerge, "process_xml_files")
    def test_merge_oval_xml_feeds(self, mock_process_xml_files, mock_update_definitions_element, mock_produce_output):
        """Test that merge_oval_xml_feeds calls the expected functions"""
        oxfm = OvalXMLFeedMerge(["test_xml.xml"], None)
        oxfm.merge_oval_xml_feeds()
        mock_process_xml_files.assert_called_once()
        mock_update_definitions_element.assert_called_once()
        mock_produce_output.assert_called_once()


class TestOvalXMLFeedMergeSetupOutputXMLFile:
    @pytest.mark.parametrize(
        "xml_files, xml_files_contents, expected_output_xml_file_contents, mock_ns_prefix_map",
        [
            (
                ["random_xml_file.xml"],
                [
                    "<root>"
                    "<tests><test>Test</test><test>Test1</test></tests>"
                    "<objects><object>Object</object><object>Object1</object></objects>"
                    "<states><state>State</state></states>"
                    "<variables><variable>1</variable></variables>"
                    "<definitions><definition>1</definition></definitions>"
                    "</root>",
                ],
                "<root>" "<tests />" "<objects />" "<states />" "<variables />" "<definitions />" "</root>",
                {},
            )
        ],
    )
    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLUtils.as_string_io_with_regenerated_ids")
    def test_setup_output_xml_file(
        self, mock_as_string_io, xml_files, xml_files_contents, expected_output_xml_file_contents, mock_ns_prefix_map
    ):
        """Test that the constructor calls setup_output_xml_file. Also test that setup_output_xml_file
        sets up a cleared output_xml_file
        """
        mock_as_string_io.side_effect = lambda x, y: x
        mock_xml_files = []
        for xml_file_name, content in zip(xml_files, xml_files_contents):
            mock_xml_file = MagicMock(name=xml_file_name)
            mock_xml_file.read.return_value = content
            mock_xml_files += [mock_xml_file]
        oxfm = OvalXMLFeedMerge(mock_xml_files, None)
        assert ET.tostring(oxfm.output_xml_file.xml_tree_root, encoding="unicode") == expected_output_xml_file_contents

    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLFile")
    @mock.patch("oval_xml_feed_merge.oval_xml_feed_merge.XMLUtils.as_string_io_with_regenerated_ids")
    def test_setup_output_xml_file_calls(self, mock_as_string_io, mock_xml_file):
        """Test that setup_output_xml_file makes the expected calls"""
        mock_as_string_io.side_effect = lambda x, y: x
        xml_file_object = MagicMock()
        mock_xml_file.return_value = xml_file_object
        xml_files = ["test_xml.xml"]
        OvalXMLFeedMerge(xml_files, None)
        calls = []
        for xml_file in xml_files:
            calls += [call(xml_file, {})]
        mock_xml_file.assert_has_calls(calls)
        xml_file_object.update_ns_map_and_register_ns.assert_called()
        xml_file_object.clear_elements.assert_called()
