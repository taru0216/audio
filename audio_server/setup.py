#!/usr/bin/env python

from distutils.core import setup

setup(name='Makuhari',
      version='0.1',
      description='Makuhari Project',
      author='Masato Taruishi',
      author_email='taru0216@gmail.com',
      url=None,
      package_dir={'': 'lib'},
      packages=['makuhari', 'makuhari.audio_server'],
     )
