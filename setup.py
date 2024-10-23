#!/usr/bin/env python

from setuptools import setup

exec(open("pod5Viewer/__version__.py").read())

setup(name="pod5Viewer",
      version=__version__, # type: ignore (imported from __version__.py above)
      description="GUI for inspecting ONT pod5 files",
      author="Vincent Dietrich",
      author_email="dietricv@uni-mainz.de",
      url="https://github.com/dietvin/pod5Viewer",
      license="LICENSE",
      packages=["pod5Viewer", "pod5Viewer.constants"],
      package_data={"pod5Viewer": ["icon.ico"],},
      entry_points={"console_scripts": ["pod5Viewer = pod5Viewer.__main__:main",],},
      python_requires=">3.9",
      install_requires=["numpy==1.26.4",
                        "pod5==0.3.10",
                        "pyside6==6.5.2",
                        "matplotlib==3.9.2"],
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                   "Programming Language :: Python :: 3",
                   "Topic :: Scientific/Engineering :: Bio-Informatics",
                   "Operating System :: OS Independent"])