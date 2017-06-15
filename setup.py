from setuptools import setup

setup(
    name='hagraph',
    version='1.0.4',
    description='Graph Home Assistant configurations',
    url='https://github.com/happyleavesaoc/home-assistant-graph/',
    license='MIT',
    author='happyleaves',
    author_email='happyleaves.tfr@gmail.com',
    packages=['hagraph'],
    install_requires=['networkx==1.11', 'homeassistant>=0.37', 'pygraphviz>=1.4rc1'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'hagraph=hagraph.__main__:main',
        ],
    }
)
