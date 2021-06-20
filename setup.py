import setuptools
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
        name='mbclient',
        version='1.1.0',
        description='A client for the Moessbauer experiment of the KIT-Physics Laboratory course',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/phylex/mbclient',
        author='Alexander Becker',
        author_email='galax.becker@live.de',
        license='GPL v3',
        install_requires=['numpy',
            'matplotlib',
            'websockets',
            'argparse',
            'pyyaml',
        ],
        packages=['mbclient'],
        entry_points={
            "console_scripts": [
                "mb-client = mbclient.cli:main"],},
        python_requires=">=3.8",
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Framework :: AsyncIO',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.9',
            'Topic :: Education :: Computer Aided Instruction (CAI)',
            'Topic :: Scientific/Engineering :: Physics',
            'Topic :: Scientific/Engineering :: Visualization',
        ],
)
