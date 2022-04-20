from setuptools import setup

VERSION = "0.9.0"

setup(
    name="observable-export",
    version=VERSION,
    description="Script and API to export ObservableHQ notebooks to different formats",
    license="Revised BSD License",
    author="Sébastien Pierre",
    download_url=f"http://github.com/sebastien/observable-export/tarball/{VERSION}",
    author_email="sebastien.pierre@gmail.com",
    url="https://github.com/sebastien/observable-export",
    package_dir={"": "src/py"},
    packages=["observableexport"],
)

# EOF
