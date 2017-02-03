all:

.PHONY:	dist update
dist:
	rm -f dist/*.whl dist/*.tar.gz
	python setup.py sdist
test:
	tox

release:
	twine upload dist/*.tar.gz
