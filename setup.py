import os
from setuptools import setup, find_packages

version = "1.1dev1"

description = """""" 

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
    
long_description = read('README.rst')
    

setup(name='QuickApp',
      author="Andrea Censi",
      author_email="censi@mit.edu",
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
      package_dir={'':'src'},
      packages=find_packages('src'),

      install_requires=[
        'compmake', 
        'reprep', 
        'PyContracts', 
        'DecentLogs',
        'ConfTools',
      ],
      tests_require=['nose'],
)

