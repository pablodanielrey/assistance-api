"""
    https://packaging.python.org/distributing/
    https://pypi.python.org/pypi?%3Aaction=list_classifiers
    http://semver.org/

    zero or more dev releases (denoted with a ”.devN” suffix)
    zero or more alpha releases (denoted with a ”.aN” suffix)
    zero or more beta releases (denoted with a ”.bN” suffix)
    zero or more release candidates (denoted with a ”.rcN” suffix)
"""

from setuptools import setup, find_packages

setup(name='assistance-api',
          version='1.0.3',
          description='Proyecto que implementa la api de asistencia',
          url='https://github.com/pablodanielrey/assistance-api',
          author='Desarrollo DiTeSi, FCE',
          author_email='ditesi@econo.unlp.edu.ar',
          classifiers=[
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5'
          ],
          packages=find_packages(exclude=['contrib', 'docs', 'test*']),
          install_requires=['psycopg2-binary',
                            'dateutils>=0.6.6',
                            'requests',
                            'redis==2.10.6',
                            'pymongo',
                            'SQLAlchemy',
                            'httplib2',
                            'pyjwt',  
                            'Flask',
                            'flask_jsontools',
                            'xmltodict',
                            'pytz',
                            'pyzk',
                            'gunicorn',
                            'microservices_common>=2.0.5a4',
                            'warden-api',
                            'python-telegram-bot',
                            'Flask-OIDC',
                            'users-model',
                            'sileg-model'],
          entry_points={
            'console_scripts': [
                'rest=assistance.api.rest.main:main'
            ]
          }
      )
