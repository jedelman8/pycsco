from distutils.core import setup
from setuptools import find_packages

setup(
  name='pycsco',
  packages=find_packages(),
  version='0.1.4',
  description='Python modules to simplify working with Cisco NX-OS devices ',
  author='Jason Edelman',
  author_email='jedelman8@gmail.com',
  url='https://github.com/jedelman8/pycsco',
  download_url='https://github.com/jedelman8/pycsco/tarball/0.1.4',
  install_requires=[
      'xmltodict==0.9.2',
  ],
)
