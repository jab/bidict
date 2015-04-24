from setuptools import setup

setup(
    name='bidict',
    version='0.3.2-dev',
    author='Joshua Bronson',
    author_email='jab@math.brown.edu',
    description="Bidirectional dict with convenient slice syntax: d[65] = 'A' <-> d[:'A'] == 65",
    long_description= 'Please see https://bidict.readthedocs.org/ for more information.',
    keywords='dict, dictionary, mapping, bidirectional, two-way, 2-way, double, inverse, reverse',
    url='https://github.com/jab/bidict',
    license='ISCL',
    py_modules=['bidict'],
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    test_suite='test',
    extras_require=dict(
        dev=['pre-commit'],
    ),
)
