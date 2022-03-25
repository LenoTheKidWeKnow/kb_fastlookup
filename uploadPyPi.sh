rm -rf build
rm -rf dist
rm -rf kb_fastlookup.egg-info
python setup.py sdist
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
