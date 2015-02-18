from distutils.core import setup
setup(
  name='pycsco',
  packages=['pycsco'],
  version='0.11',
  description='Python modules to simplify working with Cisco NX-OS devices ',
  author='Jason Edelman',
  author_email='jedelman8@gmail.com',
  url='https://github.com/jedelman8/pycsco',
  download_url='https://github.com/jedelman8/pycsco/tarball/0.11',
  install_requires=[
      'xmltodict==0.9.2',
  ],
)
