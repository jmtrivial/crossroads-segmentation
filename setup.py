import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="crossroads-segmentation",
    version="0.1.1",
    description="Crossroads segmentation is a python tool that produces automatic segmentations of data from OpenStreetMap.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.limos.fr/jmafavre/crossroads-segmentation/",
    author="Jean-Marie Favreau",
    author_email="j-marie.favreau@uca.fr",
    license="AGPL-3.0",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["crseg"],
    include_package_data=True,
)
