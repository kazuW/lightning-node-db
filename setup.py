from setuptools import setup, find_packages

setup(
    name='lightning-node-db',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A project to manage Lightning Network node channel data using SQLite3.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'sqlite3',
        'requests',  # Assuming requests might be needed for API calls
        'PyYAML',    # For handling YAML configuration
    ],
    entry_points={
        'console_scripts': [
            'lightning-node-db=cli.commands:main',  # Adjust based on your CLI entry point
        ],
    },
)