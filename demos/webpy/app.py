from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import json
import os
import subprocess
import sys
import tempfile

import sh
import web
import web.form


def load_files(file_names):
    json_data = []
    for file_name in file_names:
        full_path = os.path.abspath(file_name)
        with open(full_path, 'r') as json_file:
            print('load program from', full_path)
            json_data.append(json.load(json_file))
    return json_data


g_render = web.template.render('templates/')


Wrapper_form = web.form.Form(
    web.form.Textarea("stdin"),
    web.form.Textbox("SET1"),
    web.form.Textbox("SET2"),
    web.form.Checkbox("-c, --complement", value="bug"),
    web.form.Checkbox("-d, --delete", value="bug"),
    web.form.Checkbox("-s, --squeeze-repeats", value="bug"),
    web.form.Checkbox("-t, --truncate-set1", value="bug"),
    web.form.Checkbox("--help", value="bug"),
    web.form.Checkbox("--version", value="bug"),
    web.form.Button("submit", type="submit", description="Send"),)


def form_get(self):
    #form = Wrapper_form()
    form = self._form_type
    return g_render.Wrapper(self._program, form, "", "", "true", "true")


def form_post(self):
    #form = Wrapper_form()
    form = self._form_type
    if (not form.validates()):
        return g_render.Wrapper(self._program, form, "", "", "true", "true")
    else:
        #print(form['SET1'].value)
        temp_file_names = []
        arguments = [self._program]
        arguments += self._arguments
        stdin = ''
        for something in form.inputs:
            #print(something)
            print()
            print(something.id)
            print(something.name)
            if (something.value is not None):
                print(
                    "value =",
                    repr(something.value.encode('utf-8').decode(
                        sys.stdout.encoding)))
            else:
                print("value = None")
            if (type(something).__name__ == 'Checkbox'):
                print('Checkbox')
                if (something.checked):
                    if (something.name.startswith('-')):
                        key = something.name.split(',')[0].rstrip('_')
                        arguments.append(key)
            elif ((something.value is not None) and
                    (len(something.value) > 0)):
                if ('stdin' == something.id):
                    stdin = something.value
                else:
                    if (type(something).__name__ == 'Checkbox'):
                        print('Checkbox')
                        key = something.name.split(',')[0].rstrip('_')
                        arguments.append(key)
                    elif (type(something).__name__ == 'Textbox'):
                        print('Textbox')
                        arguments.append(something.value.encode('utf-8'))
                    elif (type(something).__name__ == 'Textarea'):
                        print('Textarea')
                        temp_file_name = self.create_temp_file(something.value)
                        arguments.append(temp_file_name)
                        temp_file_names.append(temp_file_name)
            else:
                print('no value')
        stdin = stdin.encode('utf-8')
        print('arguments =\n' + repr(
            ','.join(map(str, arguments)).decode(sys.stdout.encoding)))
        print('stdin =', repr(stdin.decode(sys.stdout.encoding)))
        process = subprocess.Popen(
            arguments,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(stdin)
        map(self.delete_temp_file, temp_file_names)
        print("stdout =\n" + repr(stdout.decode(sys.stdout.encoding)))
        print("stderr =\n" + repr(stderr.decode(sys.stderr.encoding)))
        return g_render.Wrapper(
            self._program,
            form,
            stdout,
            stderr,
            "false",
            "false")


def create_temp_file(self, content):
    """Throws on failure."""
    handle, file_name = tempfile.mkstemp()
    with open(file_name, 'w') as output:
        output.write(content)
    print("Created temporary file: '%s'" % file_name)
    return file_name


def delete_temp_file(self, file_name):
    print("Delete temporary file: '%s'" % file_name)
    os.remove(file_name)


def main(argv=sys.argv[1:]):
    """
    `argv`: command line arguments without the name of the program (poped $0).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port",
        help="Port to serve on.",
        default=5000)
    parser.add_argument(
        "-j", "--json-file",
        dest='json_files',
        help="List of files to read a description from.",
        required=True,
        default=[],
        action='append')
    arguments = parser.parse_args(argv)
    json_programs = load_files(arguments.json_files)
    app = web.auto_application()
    handlers = []
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    for json_data in json_programs:
        #print(json_data['program']['name'])
        #print(json_data['program']['arguments'])
        name = json_data['program']['name']
        controls = []
        for argument in json_data['content']:
            if ((not 'control' in argument.keys()) or
                    (not 'name' in argument.keys())):
                # ignore pure text
                continue
            #pp.pprint('argument =')
            #pp.pprint(argument)

            arg_name = argument["name"]
            if ('textarea' == argument["control"]):
                builder = web.form.Textarea
            elif ('textbox' == argument["control"]):
                builder = web.form.Textbox
            elif ('checkbox' == argument["control"]):
                builder = web.form.Checkbox
            else:
                builder = None
            if (builder is not None):
                controls.append(builder(
                    arg_name))
        controls.append(
            web.form.Button("submit", type="submit", description="Send"))
        form_type = web.form.Form(*controls)
        handler = type(
            str(name),
            (app.page,),
            {
                '_program': name,
                '_arguments': json_data['program']['arguments'],
                '_form_type': form_type,
                'GET': form_get,
                'POST': form_post,
                'create_temp_file': create_temp_file,
                'delete_temp_file': delete_temp_file
            })
        handlers.append(handler)
        print('Created handler:', name)

    sys.argv = sys.argv[:1] + ["0.0.0.0:" + str(arguments.port)]
    app.run()


if ("__main__" == __name__):
    main()
