===================
OVAL XML Feed Merge
===================

A tool to merge OVAL XML feeds. `oval-xml-feed-merge` accepts a list of OVAL XML files in increasing priority.
Any OVAL data present in the XML files in this list will replace any equivalent data in the preceding XML files.
The tool can write the merged XML to `stdout` or to a file specified through the `--output` option.
The `--verbose` flag enables logging. Logs are written to `stderr`.

A sample invocation: `oval-xml-feed-merge --verbose com.ubuntu.jammy.pkg.oval.xml com.ubuntu.gke-1.27_jammy.pkg.oval.xml --output output.xml`

This repository is a temporary home for the OVAL XML Feed Merge tool. The Public Cloud Security team plans to consolidate all OVAL related tooling in a single project and create a common snap for all tools within that project. This tool will eventually be moved there.

Current Usage
-------
1. Setup a virtual environment and activate it.
2. Run `make install`. This installs the package to the active Python's site-packages.
3. Invoke the tool using `oval-xml-feed-merge [--verbose] [--output FILENAME] [XML_FILES]...`.
4. You can print the help message using `oval-xml-feed-merge --help`.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
