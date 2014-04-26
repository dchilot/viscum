from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import json
import os

import sh
import formcreator
import sys


def load_files(file_names):
    json_data = []
    for file_name in file_names:
        full_path = os.path.abspath(file_name)
        with open(full_path, 'r') as json_file:
            print('load program from', full_path)
            json_data.append(json.load(json_file))
    return json_data


def get_command(json_data):
    def wrap(*args, **kwargs):
        #print(kwargs)
        command = json_data["program"]["name"]
        #print("command =", command)
        run = sh.Command(command)
        arguments = list(json_data["program"]["arguments"])
        stdin = None
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            if ('stdin' == key):
                stdin = value
                continue
            if (isinstance(value, bool)):
                if (value):
                    arguments.append(key)
            else:
                if (value):
                    if (key.startswith('-')):
                        arguments.append(key)
                    arguments.append(value)
        #print("arguments =", arguments)
        if (stdin is not None):
            output = str(run(arguments, _in=stdin))
        else:
            output = str(run(arguments))
        #print("output =", output)
        return output
    return wrap


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
    programs = []
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    for json_data in json_programs:
        #print(json_data['program']['name'])
        #print(json_data['program']['arguments'])
        program = formcreator.Form(
            get_command(json_data),
            name=json_data['program']['name'])
        for argument in json_data['content']:
            if ((not 'control' in argument.keys()) or
                    (not 'name' in argument.keys())):
                # ignore pure text
                continue
            #pp.pprint('argument =')
            #pp.pprint(argument)

            name = argument["name"]
            if ('textarea' == argument["control"]):
                builder = formcreator.TextArea
            elif ('textbox' == argument["control"]):
                builder = formcreator.Text
            elif ('checkbox' == argument["control"]):
                builder = formcreator.Boolean
            else:
                builder = None
            if (builder is not None):
                program += builder(
                    name,
                    cmd_opt=name.partition(',')[0])
            programs.append(program)

    #pp.pprint(programs)
    app = formcreator.MainApp(
        "Minimum",
        programs,
        host="0.0.0.0",
        not_public=False)
    app.run()


if ("__main__" == __name__):
    main()
