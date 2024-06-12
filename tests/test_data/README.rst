===================
TEST DATA
===================

In order for the blackbox tests in ``test_oval_ppa_merge.py`` to work, the following files need to be in the ``test_data`` directory:

* ``com.ubuntu.focal.pkg.oval.xml``
* ``com.ubuntu.fips-updates_focal.pkg.oval.xml``
* ``com.ubuntu.jammy.pkg.oval.xml``
* ``com.ubuntu.gke-1.27_jammy.pkg.oval.xml``
* ``com.ubuntu.gke-1.27_jammy.pkg.oval-duplicate-id.xml``
* ``com.ubuntu.gke-1.28_jammy.pkg.oval.xml``
* ``com.ubuntu.gke-1.28_jammy.pkg.oval.xml``
* ``com.ubuntu.gke-1.30_jammy.pkg.oval.xml``
* ``com.ubuntu.gke-1.31_jammy.pkg.oval.xml``


Overview
--------
``test_oval_ppa_merge.py`` is used for the verification on Customer PPA *package-based* OVAL data. The test file contains both the XML processing code along with the tests. The idea being that: given input x and y, where y is a customer ppa OVAL feed, the merged output will contain the expected components from each input.

The tests specifically look at the verification of: 

* definitions
* tests
* objects
* states
* variables

Each of these sections of the OVAL files are processed for testing in a way where the element ID is mapped to the entire component. Using this format, the logic of the tests is the same for each of the above xml elements in that, for every element in the merged output:

* if the element ID existed in both inputs
    * verify that only the element from the Customer PPA is in the merged output
* if the element ID existed in Customer PPA OVAL input but not in the other OVAL input 
    * verify that the element from the Customer PPA OVAL file is in the merged output
* if the element ID existed in other OVAL input but not in the Customer PPA OVAL input
    * verify that the element from the other OVAL file is in the merged output
* if the element ID didn't exist in either file
    * fail the test

The processing logic is found in the ``XMLDetails`` class, specifically under the ``extract_*`` functions. The test logic is then found in the ``BaseMerge`` class and it's subclasses, specifically under the ``test_pkg_*`` functions.

Definitions
^^^^^^^^^^^
For each definition, the element ID is represented by the definition ID (e.g ``<definition class="vulnerability" *id=...*``). The element this ID is mapped the remaining details embedded under this specific definition tag, including criteria and cve details. This is implemented with definition elements being represented using the following classes:

* Definition
    * id
    * title
    * Criteria class:
        * extended_def,
        * criterions (set of):
            * Criterion class
                * test_ref
                * comment
            * ExtendedDefintion class
                * test_ref
                * comment
                * applicability_check
    * cves (set of):
        * CVE class:
            * cve number,
            * href,
            * test_ref

Tests
^^^^^
For each test, the element ID is represented by the test ID (e.g ``<ind-def:family_test *id=...*>``). The element this ID is mapped the remaining details embedded under this specific tests tag, including object and state refs. This is implemented with test elements being represented as one of the following classes depending on the test type:

* DpkgInfoTest
* FamilyTest
* TextFileContent54Test
* UnameTest
* VariableTest

Objects
^^^^^^^
For each object, the element ID is represented by the object ID (e.g ``<ind-def:family_object *id=...*>``). The element this ID is mapped the remaining details embedded under this specific objects tag, including var refs (if present). This is implemented with object elements being represented as one of the following classes depending on the object type:

* DpkgInfoObject,
* FamilyObject,
* TextFileContent54Object
* UnameObject
* VariableObject

States
^^^^^^
For each state, the element ID is represented by the state ID (e.g ``<ind-def:family_state *id=...*>``). The element this ID is mapped the remaining details embedded under this specific states tag. This is implemented with state elements being represented as one of the following classes depending on the state type:

* DpkgInfoState
* FamilyState
* TextFileContent54State
* UnameState
* VariableState

Variables
^^^^^^^^^
For each variable, the element ID is represented by the variable ID (e.g ``<local_variable *id=...*>``). The element this ID is mapped the remaining details embedded under this specific variables tag. This is implemented with vairable elements being represented as one of the following classes depending on the variable type:

* LocalVariable
* ConstantVariable
