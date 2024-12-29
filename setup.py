from setuptools import setup, find_packages

setup(
    name='noteism',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'flask>=3.0.0',
        'markdown>=3.5.1',
        'python-dotenv>=2.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.4',
            'black>=23.12.1',
            'mypy>=1.7.1',
        ],
    },
    entry_points={
        'console_scripts': [
            'noteism=src.main:main',
        ],
    },
    author='CloudWerx Lab',
    author_email='contact@cloudwerxlab.com',
    description='A modern markdown editor with advanced features',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='http://cloudwerxlab.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
    ],
)
