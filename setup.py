#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Ankush Vijay Pathak",
    author_email="ankush.pathak@canonical.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="A tool to merge the OVAL XML feeds for different Ubuntu images",
    entry_points={
        "console_scripts": [
            "oval-xml-feed-merge=oval_xml_feed_merge.cli:main",
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="oval_xml_feed_merge",
    name="oval_xml_feed_merge",
    packages=find_packages(include=["oval_xml_feed_merge", "oval_xml_feed_merge.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/canonical/oval-xml-feed-merge",
    version="0.1.5",
    zip_safe=False,
)
