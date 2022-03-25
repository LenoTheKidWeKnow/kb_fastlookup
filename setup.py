from setuptools import setup, find_packages
import os

REQ_FILE = 'requirements.txt'
VERSION = '0.2.15'

def get_requires():
    thisdir = os.path.dirname(__file__)
    reqpath = os.path.join(thisdir, REQ_FILE)
    return [line.rstrip('\n') for line in open(reqpath)]

setup(name='kb_fastlookup',
      version=VERSION,
      url='https://github.com/LenoTheKidWeKnow/kb_fastlookup',
      license='MIT',
      author='Lenorandum',
      author_email='kimbh4932@gmail.com',
      description='Crawling KB Kookmin Bank transactions',
      packages=find_packages(),
      long_description=open('README.md', 'r', encoding="utf-8").read(),
      long_description_content_type="text/markdown",
      zip_safe=False,
      install_requires=get_requires(),
      include_package_data=True,
      classifiers=[
            "Programming Language :: Python :: 3",
      ],
)
