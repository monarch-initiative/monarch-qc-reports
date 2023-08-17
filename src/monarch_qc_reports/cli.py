"""Command line interface for Monarch_QC_Reports."""
import logging
import os

import click
import requests
import yaml

from monarch_qc_reports import __version__
from monarch_qc_reports.file_utils import read_kg, read_qc
from monarch_qc_reports.main import demo
from monarch_qc_reports.qc_utils import create_qc_report

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)

BASE_URL = "https://data.monarchinitiative.org/monarch-kg-dev/"
FILES = [
    "monarch-kg.tar.gz",
    "qc_report.yaml",
    "qc/monarch-kg-dangling-edges.tsv.gz",
    "qc/monarch-kg-duplicate-nodes.tsv.gz",
]


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """
    CLI for Monarch_QC_Reports.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


def download_file(url, destination):
    """Download a file from a URL."""
    response = requests.get(url, stream=True, timeout=10)
    if response.status_code == 200:
        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    else:
        logger.error(f"Failed to download {url}")


@main.command()
@click.option("-d", "--date", default="2023-06-04", help="Specify the date in the format YYYY-MM-DD or latest.")
def run(date: str):
    """Run Monarch_QC_Reports from the command line."""
    demo()

    kg_path = fetch_kg_data(date)

    # kg_path = os.path.join("kg_data", date)
    create_kg_qc_report(kg_path)


def fetch_kg_data(date: str) -> str:
    """Fetch the knowledge graph data for a given date."""
    date_directory = os.path.join("kg_data", date)
    qc_directory = os.path.join(date_directory, "qc")
    os.makedirs(qc_directory, exist_ok=True)

    for file in FILES:
        url = BASE_URL + date + "/" + file
        filename = os.path.basename(file)

        if file.startswith("qc/"):
            destination = os.path.join(date_directory, file)
        else:
            destination = os.path.join(date_directory, filename)

        logger.info(f"Downloading {filename} from {url}")
        download_file(url, destination)
        logger.info(f"{filename} downloaded successfully")

    return date_directory


def create_kg_qc_report(path: str):
    """Create a QC report for a knowledge graph."""
    kg = read_kg(path + "/monarch-kg.tar.gz")
    qc = read_qc(path + "/qc")
    qc_report = create_qc_report(kg, qc)
    os.makedirs("output", exist_ok=True)
    with open("output/qc_report.yaml", "w") as report_file:
        yaml.dump(qc_report, report_file)


if __name__ == "__main__":
    main()
