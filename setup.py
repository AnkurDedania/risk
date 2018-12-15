from setuptools import setup, find_packages

with open('README.rst') as fp:
    readme = fp.read()

with open('HISTORY.rst') as fp:
    history = fp.read()

with open('requirements.txt') as fp:
    requirements = fp.readlines()

with open('requirements-dev.txt') as fp:
    test_requirements = fp.readlines()


setup(
    author="Ankur Dedania",
    author_email='AbsoluteMSTR@gmail.com',
    description="Discord IHL Bot",
    entry_points={
        'console_scripts': [
            'risk=risk.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='risk, discord',
    name='risk',
    packages=find_packages(include=['risk']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/AnkurDedania/risk',
    version='0.0.1',
    zip_safe=False,
)
