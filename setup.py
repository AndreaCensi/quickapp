import os

from setuptools import find_packages, setup


def get_version(filename):
    import ast
    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version


version = get_version('src/quickapp/__init__.py')

description = """"""


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


long_description = read('README.rst')

line = 'z6'

install_requires = [
    'compmake-z6',
    'reprep-z6',
    'PyContracts3',
    'DecentLogs-z6',
    'ConfTools-z6',
]

setup(name=f'QuickApp-{line}',
      author="Andrea Censi",
      author_email="",
      url='http://github.com/AndreaCensi/quickapp',

      description=description,
      long_description=long_description,
      keywords="",
      license="",

      classifiers=[
          'Development Status :: 4 - Beta',
          # 'Intended Audience :: Developers',
          # 'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
          # 'Topic :: Software Development :: Quality Assurance',
          # 'Topic :: Software Development :: Documentation',
          # 'Topic :: Software Development :: Testing'
      ],

      version=version,
      download_url='http://github.com/AndreaCensi/quickapp/tarball/%s' % version,

      entry_points={
          'console_scripts': [
              # 'comptests = comptests:main_comptests'
          ]
      },
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=install_requires,
      tests_require=['nose'],
      )
