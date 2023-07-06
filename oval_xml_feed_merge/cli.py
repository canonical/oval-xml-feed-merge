"""Console script for oval_xml_feed_merge."""
import logging
import sys
import click

from oval_xml_feed_merge.oval_xml_feed_merge import OvalXMLFeedMerge


def setup_logging(verbose):
    logging_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(logging_level)
    logger_handler = logging.StreamHandler()
    logger_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger_handler.setStream(sys.stderr)
    logger.addHandler(logger_handler)


@click.command("OVAL XML Merge")
@click.argument("xml_files", nargs=-1, type=click.File("r"))
@click.option(
    "--output",
    type=click.File("w"),
    default=sys.stdout,
    help="If provided, the output XML will be written to this file else to stdout",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(xml_files, output, verbose):
    """XML_FILES: List of files to process in the order of increasing priority"""
    setup_logging(verbose)
    OvalXMLFeedMerge(xml_files, output).merge_oval_xml_feeds()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
