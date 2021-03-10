from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Fineas',
    version='0.1.0',
    description='Annotation-driven, Thread-safe, transition-focused Finite State Machines.',
    install_requires=[
        'wrapt>=1.12.1<1.13.0'
    ],
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Chris Blades',
    author_email='me@chrisdblades.com',
    url='https://github.com/cblades/fineas',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)