from setuptools import setup, find_packages

requirements = """
Flask==1.1.2
Flask-SQLAlchemy==2.4.4
iatikit==3.3.1
lxml==4.9.4
python-dateutil==2.8.1
six==1.15.0
voluptuous>=0.12.0
gunicorn==20.0.4
Unidecode==1.1.1
requests==2.25.0
xmltodict==0.12.0
gevent>=20.9.0
Markdown==3.3.3
Flask-RQ2==18.3
psycopg2==2.8.6
Sphinx==3.3.1
sphinx-rtd-theme==0.5.0
Flask-Cors==3.0.9
Flask-Migrate==2.5.3
Click==7.1.2
sentry-sdk[flask]==1.3.1
docutils==0.17.1
PyExcelerate==0.10.0
Flask-Babel==2.0.0
"""

tests_require = """
fabric==2.5.0
fakeredis==1.4.5
nose==1.3.7
mock==4.0.2
factory-boy==3.1.0
coveralls==2.2.0
coverage==5.3
openpyxl==3.0.9
pip-tools
"""


setup(
    name='IATI-Datastore',
    version='1.0.0b1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # If any package contains a .csv file include it
        '': ['*.csv'],
        # static web resources
        'iatilib.frontend': ['static/*', "templates/*", "doc/*"]
    },
    zip_safe=False,
    install_requires=requirements.strip().splitlines(),
    tests_require=tests_require.strip().splitlines(),
    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'iati = iatilib.console:cli',
        ]
    }
)
