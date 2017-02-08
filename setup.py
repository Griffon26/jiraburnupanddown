from setuptools import setup

setup(name='jiraburnupanddown',
      version='0.2',
      description='A Scrum burndown chart for Jira that also keeps track of hours spent on a separate fixed-size budget',
      url='https://github.com/Griffon26/jiraburnupanddown',
      author='Maurice van der Pot',
      author_email='griffon26@kfk4ever.com',
      license='GPLv3+',
      entry_points={
          'console_scripts': [
              'fakejira = jiraburnupanddown.fakejira:main',
          ],
          'gui_scripts': [
              'jiraburnupanddown = jiraburnupanddown.jiraburnupanddown:main',
          ]
      },
      packages = [ 'jiraburnupanddown' ],
      package_dir = {
          'jiraburnupanddown' : 'src'
      },
      package_data = {
          'jiraburnupanddown' : ['icons/document-save-as.png',
                                 'icons/edit-copy.png']
      },
      install_requires=[
          'numpy',
          'PyQt5',
          'pyqtgraph',
          'python-dateutil',
          'pytz',
          'requests',
          'tzlocal',
      ],
      classifiers=[
          # Status
          'Development Status :: 3 - Alpha',

          # Purpose
          'Intended Audience :: Developers',
          'Topic :: Software Development',

          # License
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

          # Supported python versions
          'Programming Language :: Python :: 3 :: Only'
      ],
      zip_safe=False)

