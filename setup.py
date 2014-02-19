from setuptools import setup, find_packages

setup(
    name='django-debug-toolbar-line-profiler',
    version='0.4.0',
    description='A panel for django-debug-toolbar that integrates ' +
                'information from line_profiler',
    long_description=open('README.rst').read(),
    author='Dave McLain',
    author_email='python@davemclain.com',
    url='https://github.com/dmclain/django-debug-toolbar-line-profiler',
    download_url='https://pypi.python.org/pypi/django-debug-toolbar-line-profiler',
    license='BSD',
    packages=find_packages(exclude=('tests', 'example')),
    install_requires=[
        'django-debug-toolbar>=1.0',
        'line_profiler>=1.0b3',
    ],
    include_package_data=True,
    zip_safe=False,                 # because we're including static files
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
