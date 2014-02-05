from setuptools import setup, find_packages

EXCLUDE_FROM_PACKAGES = []

# Grab the current version
version = __import__('stackdio').get_version()

setup(
    name='stackd.io',
    version=version,
    url='http://stackd.io',
    author='Digital Reasoning Systems, Inc.',
    author_email='stackdio@digitalreasoning.com',
    description=('A cloud deployment, automation, and orchestration '
                 'platform for everyone.'),
    license='Apache 2.0',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
    ],
)
