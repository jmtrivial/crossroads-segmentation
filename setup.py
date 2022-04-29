import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# The version

VERSION = (HERE / "crseg" / "__init__.py").read_text().split("'")[1]

# This call to setup() does all the work
setup(
    name="crossroads-segmentation",
    version=VERSION,
    description="Crossroads segmentation is a python tool that produces automatic segmentations of data from OpenStreetMap.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/jmtrivial/crossroads-segmentation/",
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
    entry_points={
        'console_scripts': [
            'get_crossroad_segmentation = crseg.cmd:get_crossroad_segmentation_command',
        ],
    },
)
