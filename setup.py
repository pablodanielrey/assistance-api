from setuptools import setup, find_packages

setup(name='assistance-api',
          version='2.0.0',
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
          install_requires=['google-api-python-client',
                            'google-auth-httplib2',
                            'google-auth-oauthlib',
                            'pyzk',
                            'pydantic'
          ],
          entry_points={
            'console_scripts': [
                'cron=assistance.infra.cron'
            ]
          }
      )
