import os

from setuptools import setup, find_packages

from model_adapter import VERSION

f = open(os.path.join(os.path.dirname(__file__), 'README.txt'))
readme = f.read()
f.close()

setup(
    name='django-model-adapter',
    version=".".join(map(str, VERSION)),
    description='django-model-adapter allows related field targets to be specified from settings',
    long_description=readme,
    author='Andy McCurdy',
    author_email='sedrik@gmail.com',
    url='http://github.com/andymccurdy/django-model-adapter',
    packages=('model_adapter',),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    test_suite='runtests.runtests'
)