from setuptools import setup

setup(
    name='bidict',
    version='0.2.2-dev',
    author='Joshua Bronson',
    author_email='jab@math.brown.edu',
    description="2-way dict with convenient slice syntax: d[65] = 'A' -> d[:'A'] == 65",
    long_description= 'Please see https://bidict.readthedocs.org/ for documentation.',
    keywords='bidirectional, two-way, inverse, reverse, dict, dictionary, mapping',
    url='https://github.com/jab/bidict',
    license='ISCL',
    py_modules=['bidict'],
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Natural Language :: English',
        ],
    )
