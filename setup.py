from setuptools import setup

setup(name='jiraburnupanddown',
      version='0.1',
      description='A Scrum burndown chart for Jira that also keeps track of hours spent on a separate fixed-size budget',
      url='https://github.com/Griffon26/jiraburnupanddown',
      author='Maurice van der Pot',
      author_email='griffon26@kfk4ever.com',
      license='GPLv3+',
      py_modules=['jiraburnupanddown', 'fakejira'],
      entry_points={
          'console_scripts': [
              'fakejira = fakejira:main',
          ],
          'gui_scripts': [
              'jiraburnupanddown = jiraburnupanddown:main',
          ]
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

