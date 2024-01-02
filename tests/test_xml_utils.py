from io import StringIO
from unittest import mock
from unittest.mock import MagicMock

import pytest

from oval_xml_feed_merge.xml_utils import XMLUtils
import xml.etree.ElementTree as ET


class TestXMLUtils:
    @staticmethod
    def _mock_multiprocessing_pool_map(func, it, chunksize):
        print("Input", it)
        return map(func, it)

    def test_get_xml_root(self):
        """Test that XMLUtils.get_xml_root reads the passed in XML file and returns an XML root element object
        of the XML string read from the file
        """
        xml_string = "<root><child>Content</child></root>"
        expected = ET.fromstring(xml_string)
        mock_xml_file = MagicMock()
        mock_xml_file.read.return_value = xml_string
        actual = XMLUtils.get_xml_root(mock_xml_file)
        assert ET.tostring(actual) == ET.tostring(expected)
        mock_xml_file.seek.assert_called_with(0)

    @pytest.mark.parametrize(
        "id_to_search, xml_tree, expected_element",
        [
            ("1", ET.fromstring('<root><test id="1">Some data</test></root>'), '<test id="1">Some data</test>'),
            ("1", ET.fromstring('<root><test id="2"></test></root>'), None),
            ("1", ET.fromstring('<root><test id="1"></test><object id="1"></object></root>'), None),
        ],
    )
    def test_find_element_by_id(self, id_to_search, xml_tree, expected_element):
        """Test that find_element_by_id returns the right element on query and exits if ids are duplicate
        or do not exist"""
        if expected_element:
            actual_result = XMLUtils.find_element_by_id(id_to_search, xml_tree)
            assert ET.tostring(actual_result, encoding="unicode") == expected_element
        else:
            with pytest.raises(SystemExit):
                XMLUtils.find_element_by_id(id_to_search, xml_tree)

    @pytest.mark.parametrize(
        "xml_tree, expected_id_to_element_map",
        [
            (
                ET.fromstring('<root><test id="1">Some Test</test><var id="2">Some Var</var></root>'),
                {"1": ET.fromstring('<test id="1">Some Test</test>'), "2": ET.fromstring('<var id="2">Some Var</var>')},
            )
        ],
    )
    def test_generate_id_map(self, xml_tree, expected_id_to_element_map):
        actual_map = XMLUtils.generate_id_map(xml_tree)
        assert actual_map.keys() == expected_id_to_element_map.keys()

        assert {ET.tostring(ele, encoding="unicode") for ele in actual_map.values()} == {
            ET.tostring(ele, encoding="unicode") for ele in expected_id_to_element_map.values()
        }

    @pytest.mark.parametrize(
        "input_file_content, input_file_name, input_global_input_id_set, expected_content_after_test",
        [
            (
                "<root>"
                '<test id="oval:focal.tst:1234" >A test element</test>'
                '<var id="oval:focal.var:4567" >A var element</var>'
                "</root>",
                "random.xml",
                {"oval:focal.tst:1234"},
                "<root>"
                '<test id="oval:focal.tst:12340000000000000001" >A test element</test>'
                '<var id="oval:focal.var:4567" >A var element</var>'
                "</root>",
            ),
        ],
    )
    def test_as_string_io_with_regenerated_ids(
        self, input_file_content, input_file_name, input_global_input_id_set, expected_content_after_test
    ):
        """Test that as_string_io_with_regenerated_ids regenerates IDs and returns a StringIO object"""
        input_file = StringIO(input_file_content)
        input_file.name = input_file_name

        def int_gen():
            while True:
                yield 1

        result: StringIO = XMLUtils.as_string_io_with_regenerated_ids(input_file, int_gen(), input_global_input_id_set)
        assert result.getvalue() == expected_content_after_test
        assert result.name == input_file_name
        assert type(result) == StringIO

    @pytest.mark.parametrize(
        "input_file_content, input_file_name, input_global_input_id_set, expected_content_after_test",
        [
            (
                "<root>"
                '<test id="oval:focal.tst:1234" >A test element</test>'
                '<var id="oval:focal.var:4567" >A var element</var>'
                "</root>",
                "random.xml",
                {"oval:focal.tst:1234", "oval:focal.var:4567"},
                "<root>"
                '<test id="oval:focal.tst:12340000000000000001" >A test element</test>'
                '<var id="oval:focal.var:45670000000000000001" >A var element</var>'
                "</root>",
            ),
        ],
    )
    def test_regenerate_ids(
        self, input_file_content, input_file_name, input_global_input_id_set, expected_content_after_test
    ):
        """Test that regenerate_ids regenerates IDs and returns a str object"""
        input_file = StringIO(input_file_content)
        input_file.name = input_file_name

        def int_gen():
            while True:
                yield 1

        result: str = XMLUtils.regenerate_and_replace_ids(input_file, int_gen(), input_global_input_id_set)
        assert result == expected_content_after_test
        assert type(result) == str

    @pytest.mark.parametrize(
        "input_file_line, input_current_file_old_to_new_id_map, expected_return_value",
        [
            (
                '<test id="oval:focal.tst:1234" >A test element</test>'
                '<var ref_id="oval:focal.tst:1234" >A var element</var>',
                {"oval:focal.tst:1234": "oval:focal.tst:12340000000000000001"},
                '<test id="oval:focal.tst:12340000000000000001" >A test element</test>'
                '<var ref_id="oval:focal.tst:12340000000000000001" >A var element</var>',
            ),
        ],
    )
    def test_replace_element_ids(self, input_file_line, input_current_file_old_to_new_id_map, expected_return_value):
        """Test that replace_element_ids replaces IDs as expected from input XML"""

        result: str = XMLUtils.replace_element_ids(input_current_file_old_to_new_id_map, input_file_line)
        assert result == expected_return_value
        assert type(result) == str

    @pytest.mark.parametrize(
        "input_file_content, file_name, expected_id_map",
        [
            (
                "<root>"
                '<test id="oval:focal.tst:1234" >A test element</test>'
                '<var id="oval:focal.var:4567" >A var element</var>'
                "</root>",
                "random.xml",
                {
                    "oval:focal.tst:1234": None,
                    "oval:focal.var:4567": None,
                },
            )
        ],
    )
    def test_update_current_to_new_element_id_map(self, input_file_content, file_name, expected_id_map):
        global_id_set = set()
        current_file_old_to_new_id_map = {}

        def int_gen():
            while True:
                yield 1

        XMLUtils.update_current_to_new_element_id_map(
            current_file_old_to_new_id_map, int_gen(), global_id_set, input_file_content, file_name
        )
        assert current_file_old_to_new_id_map == expected_id_map

    @pytest.mark.parametrize(
        "input_file_content, file_name, duplicate_id, expected_id_map",
        [
            (
                "<root>"
                '<test id="oval:focal.tst:1234" >A test element</test>'
                '<test id="oval:focal.tst:1234" >A duplicate element</test>'
                "</root>",
                "random.xml",
                "oval:focal.tst:1234",
                {
                    "oval:focal.tst:1234": None,
                },
            )
        ],
    )
    @mock.patch("oval_xml_feed_merge.xml_utils.logging.warning")
    def test_update_current_to_new_element_id_map_log(
        self, mock_log_warn, input_file_content, file_name, duplicate_id, expected_id_map
    ):
        current_file_old_to_new_id_map = {}
        global_id_set = set()

        def int_gen():
            while True:
                yield 1

        XMLUtils.update_current_to_new_element_id_map(
            current_file_old_to_new_id_map, int_gen(), global_id_set, input_file_content, file_name
        )
        assert current_file_old_to_new_id_map == expected_id_map
        mock_log_warn.assert_called_with(f"Duplicate element ID: {duplicate_id} in {file_name}")
