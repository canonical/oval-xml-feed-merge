from unittest.mock import MagicMock

import pytest

from oval_xml_feed_merge.xml_utils import XMLUtils
import xml.etree.ElementTree as ET


class TestXMLUtils:
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
