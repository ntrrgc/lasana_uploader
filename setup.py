#/usr/bin/env python
#encoding: utf-8
from distutils.core import setup
import os

if os.name == 'nt':
    import py2exe

import glob

def find_data_files(source,target,patterns):
    """Locates the specified data-files and returns the matches
    in a data_files compatible format.

    source is the root of the source data tree.
        Use '' or '.' for current directory.
    target is the root of the target data tree.
        Use '' or '.' for the distribution directory.
    patterns is a sequence of glob-patterns for the
        files you want to copy.
    """
    if glob.has_magic(source) or glob.has_magic(target):
        raise ValueError("Magic not allowed in src, target")
    ret = {}
    for pattern in patterns:
        pattern = os.path.join(source,pattern)
        for filename in glob.glob(pattern):
            if os.path.isfile(filename):
                targetpath = os.path.join(target,os.path.relpath(filename,source))
                path = os.path.dirname(targetpath)
                ret.setdefault(path,[]).append(filename)
    return sorted(ret.items())

def get_data_files():
    if os.name == 'nt':
        return [("imageformats", glob.glob("imageformats/*.dll"))]
    elif os.name == 'posix':
        return [
                ('/usr/share/pixmaps/', ['lasana.png']),
                ('/usr/share/applications/', ['lasana.desktop']),
                ]

setup(name="lasana_uploader",
      version="0.1",
      description=u"Upload files to Lasaña from your desktop",
      author="Juan Luis Boya",
      author_email="ntrrgc@gmail.com",
      url="http://lasana.rufian.eu/",
      license="2-clause BSD",
      packages=['lasana_uploader'],
      package_data={"lasana_uploader": ["resources/*"]},
      data_files=get_data_files(),
      install_requires=[
          "PyQt >= 4.6",
          "requests > 1.0",
          "lxml > 3.0",
          "cssselect > 0.6",
          ],
      scripts=["bin/lasana"],
      windows=[{"script": "bin/lasana_windows",
                 "icon_resources": [(1, "lasana_uploader/resources/icon.ico")]}]
              if os.name == 'nt' else [],
      options={
        "py2exe": {
            "skip_archive": True, 
            #Does not work
            #"custom-boot-script": "boot_script.py",
            "dll_excludes": [
                "w9xpopen.exe"
            ],
            "includes": [
                "sip",
                "requests",
                "lxml",
                "lxml.cssselect",
                "lxml.etree",
                "lxml._elementpath",
                "cssselect",
            ]
        }
      })
