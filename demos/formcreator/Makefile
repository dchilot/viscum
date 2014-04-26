%.json: env/bin/activate
	. env/bin/activate && viscum ${subst data/,,${subst .json,,$@}} --stdin --json --pretty-json > $@

env/bin/activate:
	virtualenv env
	. env/bin/activate && pip install -r requirements.txt

json: data/sed.json data/tr.json

start: env/bin/activate json
	. env/bin/activate && python ./app.py -j data/sed.json -j data/tr.json
