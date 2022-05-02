from setuptools import setup, find_packages

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

with open("requirements.txt", encoding="utf8") as requirements_file:
    requirements = [line for line in requirements_file.read().splitlines() if line]

setup(
    name="spotify-to-musi",
    version="0.0.1b1",
    description="desc",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    author="Hexiro",
    # packages=["autorequests"] + [("autorequests." + x) for x in find_packages(where="autorequests")],
    # entry_points={"console_scripts": ["autorequests = autorequests.__main__:main"]},
    python_requires=">=3.7",
    license="MPL2",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
)
