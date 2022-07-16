from setuptools import setup

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

with open("requirements.txt", encoding="utf8") as requirements_file:
    requirements = [line for line in requirements_file.read().splitlines() if line]

setup(
    name="spotify-to-musi",
    version="1.0.0",
    description="Transfer your Spotify playlists to Musi.",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    author="Hexiro",
    packages=["spotify_to_musi", "spotify_to_musi.typings"],
    package_data={"spotify_to_musi": ["py.typed"]},
    entry_points={
        "console_scripts": [
            "spotify_to_musi = spotify_to_musi.__main__:cli",
            "spotify-to-musi = spotify_to_musi.__main__:cli",
        ]
    },
    python_requires=">=3.7",
    license="GPLv3",
    zip_safe=False,
    classifiers=[
        "Natural Language :: English",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries ",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
