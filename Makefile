test:
	nosetests

coverage:
	nosetests --with-coverage --cover-package=viscum --cover-tests

clean:
	coverage erase
