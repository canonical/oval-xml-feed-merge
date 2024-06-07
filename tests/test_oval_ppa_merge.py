#!/usr/bin/env python

"""Tests for `oval_xml_feed_merge` output using customer ppa data."""
import pytest
import xml.etree.ElementTree as ET
import re

from oval_xml_feed_merge.oval_xml_feed_merge import OvalXMLFeedMerge


class Criterion:
    def __init__(self, ref, comment):
        self.ref = ref
        self.comment = comment
        self.set_attributes()

    def set_attributes(self):
        self.attributes = (self.ref, self.comment)

    def __eq__(self, other):
        return self.ref == other.ref and self.comment == other.comment

    def __hash__(self):
        return hash(self.attributes)

    def __str__(self):
        return f"Criterion:\n\t{self.ref}\n\t{self.comment}"


class ExtendedDefintion(Criterion):
    def __init__(self, ref, comment, applicability_check):
        self.applicability_check = applicability_check
        super().__init__(ref, comment)

    def set_attributes(self):
        self.attributes = (self.ref, self.comment, self.applicability_check)

    def __eq__(self, other):
        return super().__eq__(other) and self.applicability_check == other.applicability_check

    def __str__(self):
        return f"Extended Defintion:\n\t{self.ref}\n\t{self.comment}\n\t{self.applicability_check}"


class Criteria:
    def __init__(self, extend_def, criterion):
        self.extend_def = extend_def
        self.criterion = criterion

    def __eq__(self, other):
        return isinstance(other, Criteria) and self.extend_def == other.extend_def and self.criterion == other.criterion

    def __hash__(self):
        return hash((self.extend_def, self.criterion))

    def __str__(self):
        criterion = "".join(["\n\t" + str(crit) for crit in self.criterion])
        return f"Criteria:\n\t{self.extend_def}\n\t{criterion}"


class CVE:
    def __init__(self, cve, href, test_ref):
        self.cve = cve
        self.href = href
        self.test_ref = test_ref

    def __eq__(self, other):
        return self.cve == other.cve and self.href == other.href and self.test_ref == other.test_ref

    def __hash__(self):
        return hash((self.cve, self.href, self.test_ref))

    def __str__(self):
        return f"CVE:\n\t{self.cve}\n\t{self.href}\n\t{self.test_ref}"


class TypeTest:
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        self.tag = tag
        self.test_id = test_id
        self.check_existence = check_existence
        self.check = check
        self.version = version
        self.comment = comment
        self.object_ref = None
        self.state_ref = None

    def set_object_ref(self, object_ref):
        self.object_ref = object_ref

    def set_state_ref(self, state_ref):
        self.state_ref = state_ref

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tag == other.tag
            and self.test_id == other.test_id
            and self.check_existence == other.check_existence
            and self.check == other.check
            and self.version == other.version
            and self.comment == other.comment
            and self.object_ref == other.object_ref
            and self.state_ref == other.state_ref
        )

    def __hash__(self):
        return hash(
            (
                self.tag,
                self.test_id,
                self.object_ref,
                self.state_ref,
                self.check_existence,
                self.check,
                self.version,
                self.comment,
            )
        )

    def __str__(self):
        return f"{self.__class__}:\n\t{self.test_id}\n\t{self.object_ref}\n\t{self.state_ref}"


class DpkgInfoTest(TypeTest):
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        super().__init__(tag, test_id, version, check_existence, check, comment)


class FamilyTest(TypeTest):
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        super().__init__(tag, test_id, version, check_existence, check, comment)


class TextFileContent54Test(TypeTest):
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        super().__init__(tag, test_id, version, check_existence, check, comment)


class UnameTest(TypeTest):
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        super().__init__(tag, test_id, version, check_existence, check, comment)


class VariableTest(TypeTest):
    def __init__(self, tag, test_id, version, check_existence, check, comment):
        super().__init__(tag, test_id, version, check_existence, check, comment)


class TypeObject:
    def __init__(self, tag, object_id, version, comment):
        self.tag = tag
        self.object_id = object_id
        self.version = version
        self.comment = comment

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tag == other.tag
            and self.object_id == other.object_id
            and self.version == other.version
            and self.comment == other.comment
        )

    def __hash__(self):
        return hash((self.tag, self.object_id, self.version, self.comment))

    def __str__(self):
        return f"{self.__class__}\n\t{self.object_id}"


class VariableBasedObject(TypeObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)
        self.var_ref = None

    def set_var_ref(self, var_ref):
        self.var_ref = var_ref

    def __eq__(self, other):
        return super().__eq__(other) and self.var_ref == other.var_ref

    def __hash__(self):
        return hash((self.tag, self.object_id, self.version, self.comment, self.var_ref))

    def __str__(self):
        return super().__str__() + f"\n\t{self.var_ref}"


class DpkgInfoObject(VariableBasedObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)
        self.var_check = None

    def set_var_check(self, var_check):
        self.var_check = var_check

    def __eq__(self, other):
        return super().__eq__(other) and self.var_check == other.var_check

    def __hash__(self):
        return hash((self.tag, self.object_id, self.version, self.comment, self.var_ref, self.var_check))

    def __str__(self):
        return super().__str__() + f"\n\t{self.var_check}"


class FamilyObject(TypeObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)


class TextFileContent54Object(TypeObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)
        self.filepath = None
        self.pattern = ()
        self.instance = ()

    def set_filepath(self, filepath):
        self.filepath = filepath

    def set_pattern(self, pattern):
        self.pattern = pattern

    def set_instance(self, instance):
        self.instance = instance

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.filepath == other.filepath
            and self.pattern == other.pattern
            and self.instance == other.instance
        )

    def __hash__(self):
        return hash((self.tag, self.object_id, self.version, self.comment, self.filepath, self.pattern, self.instance))

    def __str__(self):
        return super().__str__() + f"\n\t{self.object_id}\n\t{self.version}\n\t{self.comment}"


class UnameObject(TypeObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)


class VariableObject(VariableBasedObject):
    def __init__(self, tag, object_id, version, comment):
        super().__init__(tag, object_id, version, comment)


class TypeState:
    def __init__(self, tag, state_id, version, comment):
        self.tag = tag
        self.state_id = state_id
        self.version = version
        self.comment = comment

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tag == other.tag
            and self.state_id == other.state_id
            and self.version == other.version
            and self.comment == other.comment
        )

    def __hash__(self):
        return hash((self.tag, self.state_id, self.version, self.comment))

    def __str__(self):
        return f"{self.__class__}\n\t{self.state_id}"


class VariableBasedState(TypeState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)
        self.operation = None
        self.value = None
        self.datatype = None

    def set_operation(self, operation):
        self.operation = operation

    def set_value(self, value):
        self.value = value

    def set_datatype(self, datatype):
        self.datatype = datatype

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.operation == other.operation
            and self.value == other.value
            and self.datatype == other.datatype
        )

    def __hash__(self):
        return hash((self.tag, self.state_id, self.version, self.comment, self.operation, self.value, self.datatype))

    def __str__(self):
        return super().__str__() + f"\n\t{self.operation}\n\t{self.value}\n\t{self.datatype}"


class DpkgInfoState(VariableBasedState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)


class FamilyState(TypeState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)
        self.family = None

    def set_family(self, family):
        self.family = family

    def __eq__(self, other):
        return super().__eq__(other) and self.family == other.family

    def __hash__(self):
        return hash((self.tag, self.state_id, self.version, self.comment, self.family))


class TextFileContent54State(TypeState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)
        self.subexpression = None

    def set_subexpression(self, subexpression):
        self.subexpression = subexpression

    def __eq__(self, other):
        return super().__eq__(other) and self.subexpression == other.subexpression

    def __hash__(self):
        return hash((self.tag, self.state_id, self.version, self.comment, self.subexpression))


class UnameState(VariableBasedState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)


class VariableState(VariableBasedState):
    def __init__(self, tag, state_id, version, comment):
        super().__init__(tag, state_id, version, comment)


class TypeVariable:
    def __init__(self, tag, var_id, version, comment, datatype):
        self.tag = tag
        self.var_id = var_id
        self.version = version
        self.comment = comment
        self.datatype = datatype

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tag == other.tag
            and self.var_id == other.var_id
            and self.version == other.version
            and self.comment == other.comment
            and self.datatype == other.datatype
        )

    def __hash__(self):
        return hash((self.tag, self.var_id, self.version, self.comment, self.datatype))

    def __str__(self):
        return f"{self.__class__}\n\t{self.var_id}"


class ConstantVariable(TypeVariable):
    def __init__(self, tag, var_id, version, comment, datatype):
        super().__init__(tag, var_id, version, comment, datatype)
        self.values = set()

    def add_value(self, value):
        self.values.add(value)

    def __eq__(self, other):
        return super().__eq__(other) and self.values == other.values

    def __hash__(self):
        return hash((self.tag, self.var_id, self.version, self.comment, self.datatype, tuple(self.values)))

    def __str__(self):
        values = "".join(["\n\t" + str(value) for value in self.values])
        return super().__str__() + f"{values}"


class LocalVariable(TypeVariable):
    def __init__(self, tag, var_id, version, comment, datatype):
        super().__init__(tag, var_id, version, comment, datatype)
        self.literal_component = None
        self.pattern = None
        self.object_ref = None
        self.item_field = None

    def set_literal_component(self, literal_component):
        self.literal_component = literal_component

    def set_pattern(self, pattern):
        self.pattern = pattern

    def set_object_ref(self, object_ref):
        self.object_ref = object_ref

    def set_item_field(self, item_field):
        self.item_field = item_field

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.literal_component == other.literal_component
            and self.pattern == other.pattern
            and self.object_ref == other.object_ref
            and self.item_field == other.item_field
        )

    def __hash__(self):
        return hash((self.tag, self.var_id, self.version, self.comment, self.datatype, tuple(self.values)))

    def __str__(self):
        return (
            super().__str__()
            + f"\n\t{self.literal_component}\n\t"
            + f"{self.pattern}\n\t{self.object_ref}\n\t{self.item_field}"
        )


TEST_TYPES = {
    "dpkginfo_test": DpkgInfoTest,
    "family_test": FamilyTest,
    "textfilecontent54_test": TextFileContent54Test,
    "uname_test": UnameTest,
    "variable_test": VariableTest,
}

OBJECT_TYPES = {
    "dpkginfo_object": DpkgInfoObject,
    "family_object": FamilyObject,
    "textfilecontent54_object": TextFileContent54Object,
    "uname_object": UnameObject,
    "variable_object": VariableObject,
}

STATE_TYPES = {
    "dpkginfo_state": DpkgInfoState,
    "family_state": FamilyState,
    "textfilecontent54_state": TextFileContent54State,
    "uname_state": UnameState,
    "variable_state": VariableState,
}

VARAIBLE_TYPES = {
    "local_variable": LocalVariable,
    "constant_variable": ConstantVariable,
}


class XMLDetails:
    def __init__(self, filename: str):
        self.ns_map = self.update_namespace_map(filename)
        xml = ET.parse(filename)
        self.root = xml.getroot()
        self.extract_defintion_data()
        self.extract_tests_data()
        self.extract_object_data()
        self.extract_state_data()
        self.extract_variable_data()

    def extract_variable_data(self):
        variables = {}

        for var in self.get_variables()[0].iterfind("./", self.ns_map):
            var_id = var.attrib["id"]
            tag = var.tag.split("}")[-1].strip()

            variables[var_id] = VARAIBLE_TYPES[tag](
                var.tag,
                var_id,
                var.get("version"),
                var.get("comment"),
                var.get("comment"),
            )

            for child in var.iterfind("./", self.ns_map):
                if child.tag.endswith("value"):
                    variables[var_id].add_value(child.text.strip())

                if child.tag.endswith("concat"):
                    variables[var_id].set_literal_component(child.find("./literal_component", self.ns_map).text)
                    variables[var_id].set_pattern(child.find("./regex_capture", self.ns_map).get("pattern"))
                    variables[var_id].set_object_ref(
                        child.find("./regex_capture/object_component", self.ns_map).get("object_ref")
                    )
                    variables[var_id].set_item_field(
                        child.find("./regex_capture/object_component", self.ns_map).get("item_field")
                    )
        self.variables = variables

    def extract_state_data(self):
        states = {}

        for state in self.get_states()[0].iterfind("./", self.ns_map):
            state_id = state.attrib["id"]
            tag = state.tag.split("}")[-1].strip()

            states[state_id] = STATE_TYPES[tag](state.tag, state_id, state.get("version"), state.get("comment"))

            for child in state.iterfind("./", self.ns_map):
                if child.tag.endswith("family"):
                    states[state_id].set_family(child.text.strip())
                    continue

                if child.tag.endswith("subexpression"):
                    states[state_id].set_subexpression(child.text.strip())
                    continue

                if not child.tag.endswith("os_release"):
                    states[state_id].set_datatype(child.get("datatype"))

                states[state_id].set_operation(child.get("operation"))
                states[state_id].set_value(child.text.strip())

        self.states = states

    def extract_object_data(self):
        objects = {}

        for obj in self.get_objects()[0].iterfind("./", self.ns_map):
            object_id = obj.get("id")
            tag = obj.tag.split("}")[-1].strip()

            objects[object_id] = OBJECT_TYPES[tag](obj.tag, object_id, obj.get("version"), obj.get("comment"))

            for child in obj.iterfind("./", self.ns_map):
                if child.tag.endswith("name"):
                    objects[object_id].set_var_ref(child.get("var_ref"))
                    objects[object_id].set_var_check(child.get("var_check"))
                    continue

                if child.tag.endswith("var_ref"):
                    objects[object_id].set_var_ref(child.get("var_ref"))
                    continue

                if child.tag.endswith("filepath"):
                    objects[object_id].set_filepath(child.text.strip())
                    continue

                attrib = tuple(child.attrib.items())
                if child.tag.endswith("pattern"):
                    objects[object_id].set_pattern(attrib)

                if child.tag.endswith("instance"):
                    objects[object_id].set_instance(attrib)

        self.objects = objects

    def extract_tests_data(self):
        tests = {}

        for test in self.get_tests()[0].iterfind("./", self.ns_map):
            test_id = test.get("id")
            tag = test.tag.split("}")[-1].strip()

            tests[test_id] = TEST_TYPES[tag](
                test.tag,
                test_id,
                test.get("version"),
                test.get("check_existence"),
                test.get("check"),
                test.get("comment"),
            )

            for child in test.iterfind("./", self.ns_map):
                if child.tag.endswith("object"):
                    tests[test_id].set_object_ref(child.get("object_ref"))

                if child.tag.endswith("state"):
                    tests[test_id].set_state_ref(child.get("state_ref"))

        self.tests = tests

    def extract_defintion_data(self):
        package_vulnerabilities = {}

        for definition in self.get_definitions():
            pkg = definition.find("./metadata/title", self.ns_map).text

            # Extract details from CVE tags
            cves = {
                CVE(cve.text, cve.get("href"), cve.get("test_ref"))
                for cve in definition.findall("./metadata/advisory/cve", self.ns_map)
            }

            # Extract criterion data
            paths = ["./criteria/criteria/criteria/criterion", "./criteria/criteria/criterion", "./criteria/criterion"]
            criterion = set()
            for path in paths:
                criterion_details = definition.findall(path, self.ns_map)
                if not criterion_details:
                    continue
                criterion = criterion.union(
                    {Criterion(crit.get("test_ref"), crit.get("comment")) for crit in criterion_details}
                )

            extended_def_path = "./criteria/extend_definition"
            extended_def_elements = definition.findall(extended_def_path, self.ns_map)
            if not extended_def_elements:
                # Set an an empty ExtendedDefintion (this is for inventory)
                extended_def = ExtendedDefintion(None, None, None)
            else:
                extended_def_elements = extended_def_elements[0]
                extended_def = ExtendedDefintion(
                    extended_def_elements.get("definition_ref"),
                    extended_def_elements.get("comment"),
                    extended_def_elements.get("applicability_check"),
                )

            criteria = Criteria(extended_def, criterion)

            package_vulnerabilities[pkg] = {"cves": cves, "criteria": criteria}
        self.package_vulnerabilities = package_vulnerabilities

    def update_namespace_map(self, raw_xml_file):
        """Extract all namespace prefixes and URIs from the XML file and update ns_prefix_map"""
        xml_ns_regex_literal = (
            r'xmlns:?([a-z\-]*)="(https?:\/\/(?:www\.)?'
            r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*))"'
        )
        xml_ns_regex = re.compile(xml_ns_regex_literal)
        # raw_xml_file.seek(0)

        ns_prefix_map = {}
        with open(raw_xml_file, "r") as fd:
            for line in fd:
                for match in xml_ns_regex.finditer(line):
                    prefix = match.group(1) if match.group(1) else ""
                    uri = match.group(2)
                    ns_prefix_map[prefix] = uri

        for prefix, uri in ns_prefix_map.items():
            ET.register_namespace(prefix, uri)
        return ns_prefix_map

    def get_definitions(self):
        return self.root.findall("./definitions", self.ns_map)[0].findall("./definition", self.ns_map)

    def get_tests(self):
        return self.root.findall("./tests", self.ns_map)

    def get_objects(self):
        return self.root.findall("./objects", self.ns_map)

    def get_states(self):
        return self.root.findall("./states", self.ns_map)

    def get_variables(self):
        return self.root.findall("./variables", self.ns_map)


class BaseMerge:
    MAIN_FILE = "com.ubuntu.jammy.pkg.oval.xml"

    @pytest.fixture
    def setup(self, request):
        test_data_path = request.path.parent.joinpath("test_data")
        main_data_path = test_data_path.joinpath(self.MAIN_FILE)
        ppa_data_path = test_data_path.joinpath(self.PPA_FILE)
        merged_data_path = test_data_path.joinpath(self.MERGED_FILE)

        if not main_data_path.exists():
            pytest.skip(f"{self.MAIN_FILE} not in {test_data_path}")

        if not ppa_data_path.exists():
            pytest.skip(f"{self.PPA_FILE} not in {test_data_path}")

        input_main = XMLDetails(main_data_path)
        input_ppa = XMLDetails(ppa_data_path)

        if not merged_data_path.exists():
            input_main_xml_file = open(main_data_path, "r")
            input_ppa_xml_file = open(ppa_data_path, "r")
            xml_files = [input_main_xml_file, input_ppa_xml_file]
            output_xml_file = open(merged_data_path, "w")

            OvalXMLFeedMerge(xml_files, output_xml_file).merge_oval_xml_feeds()
            input_main_xml_file.close()
            input_ppa_xml_file.close()
            output_xml_file.close()

        output = XMLDetails(merged_data_path)
        yield input_main, input_ppa, output

    def check_merged(self, input_main, input_ppa, output):
        for element_id, details in output.items():
            # ID or package existed in both inputs
            if element_id in input_ppa and element_id in input_main:
                assert details == input_ppa[element_id]
                assert details != input_main[element_id]

            # ID existed in ppa OVAL input but not main OVAL input
            elif element_id in input_ppa and element_id not in input_main:
                assert details == input_ppa[element_id]

            # ID existed in main OVAL input but not ppa OVAL input
            elif element_id not in input_ppa and element_id in input_main:
                assert details == input_main[element_id]

            # ID didn't exist in either input file
            else:
                pytest.fail("Shouldn't have a case where both ID's are kept")

    def test_pkg_defintion_merge(self, setup):
        main, ppa, merged = setup
        merged_details = merged.package_vulnerabilities
        main_details = main.package_vulnerabilities
        ppa_details = ppa.package_vulnerabilities

        self.check_merged(main_details, ppa_details, merged_details)

    def test_pkg_test_merge(self, setup):
        main, ppa, merged = setup
        merged_details = merged.tests
        main_details = main.tests
        ppa_details = ppa.tests

        self.check_merged(main_details, ppa_details, merged_details)

    def test_pkg_object_merge(self, setup):
        main, ppa, merged = setup
        merged_details = merged.objects
        main_details = main.objects
        ppa_details = ppa.objects

        self.check_merged(main_details, ppa_details, merged_details)

    def test_pkg_state_merge(self, setup):
        main, ppa, merged = setup
        merged_details = merged.states
        main_details = main.states
        ppa_details = ppa.states

        self.check_merged(main_details, ppa_details, merged_details)

    def test_pkg_variable_merge(self, setup):
        main, ppa, merged = setup
        merged_details = merged.variables
        main_details = main.variables
        ppa_details = ppa.variables

        self.check_merged(main_details, ppa_details, merged_details)


class TestGKE127Merge(BaseMerge):
    PPA_FILE = "com.ubuntu.gke-1.27_jammy.pkg.oval.xml"
    MERGED_FILE = "com.ubuntu.merged_gke-1.27_jammy.pkg.oval.xml"


class TestGKE128Merge(BaseMerge):
    PPA_FILE = "com.ubuntu.gke-1.28_jammy.pkg.oval.xml"
    MERGED_FILE = "com.ubuntu.merged_gke-1.28_jammy.pkg.oval.xml"


class TestGKE129Merge(BaseMerge):
    PPA_FILE = "com.ubuntu.gke-1.29_jammy.pkg.oval.xml"
    MERGED_FILE = "com.ubuntu.merged_gke-1.29_jammy.pkg.oval.xml"


class TestGKE130Merge(BaseMerge):
    PPA_FILE = "com.ubuntu.gke-1.30_jammy.pkg.oval.xml"
    MERGED_FILE = "com.ubuntu.merged_gke-1.30_jammy.pkg.oval.xml"


class TestGKE131Merge(BaseMerge):
    PPA_FILE = "com.ubuntu.gke-1.31_jammy.pkg.oval.xml"
    MERGED_FILE = "com.ubuntu.merged_gke-1.31_jammy.pkg.oval.xml"
