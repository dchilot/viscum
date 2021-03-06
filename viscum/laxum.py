from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals


import abc
import argparse
import sys
import re
import json


from pyparsing import Literal
from pyparsing import Optional
from pyparsing import Group
from pyparsing import Or
from pyparsing import Regex
from pyparsing import Word
from pyparsing import ZeroOrMore
from pyparsing import OneOrMore
from pyparsing import FollowedBy
from pyparsing import alphas
from pyparsing import alphanums
from pyparsing import srange
from pyparsing import printables
from pyparsing import restOfLine

#      _
#     / \
#    / | \
#   /  |  \
#  /   O   \
# /_________\
#
# Following code is ugly

gAnything = Regex(".*").suppress()

gSpace = Literal(" ")
gSpaces = ZeroOrMore(gSpace).suppress()
gEOL = Regex("\n").suppress()
gEOL_keep = Regex("\n")
gImportantSpaces = ZeroOrMore(gSpace)
gInnerArgument = Word(alphas, alphanums + '_-').setResultsName("argument")
gArgument = gSpace + gInnerArgument
gInnerParameter = Word(alphas, alphanums + '_-')
gExtendedInnerParameter = Word(alphas, alphanums + '_- ')
gInnerParameterPlus = Or([gSpace, Literal('=')]).suppress() + gInnerParameter
gInnerParameterPlusLess = \
    Optional(Or([gSpace, Literal('=')]).suppress()) + gInnerParameter
gParameter = (Or([
    Group(gSpace + Literal('<') + gExtendedInnerParameter + Literal('>')),
    Group(Literal('[') + gInnerParameterPlusLess + Literal(']')),
    gInnerParameterPlus + FollowedBy(
        Or([
            gEOL,
            Optional(gSpace) + Literal(','),
            gSpace + gSpace,
            gSpace + Literal(':')])
    )])).setResultsName("parameter")
gStdin = Literal("-").setResultsName("stdin")
gRawOption = \
    Literal("-") + Optional(Literal('-')) + Word(alphanums, alphanums + '_-')
gRawOption1 = \
    Literal("-") + Optional(Literal('-')) + Word(alphas, alphanums + '_-')
gRawOption2 = \
    Literal("-") + Optional(Literal('-')) + Word(alphas, alphanums + '_-')

gOption = Group(gRawOption).setResultsName("option") + Optional(gArgument)
gElement = gSpaces + Or([gOption, gInnerArgument, gStdin]) + gSpaces
gElements = gElement.setResultsName("first_element") + ZeroOrMore(
    Group(gSpaces + Literal("|").suppress() + gElement))\
    .setResultsName("other_elements")
gRepetition = gSpaces + Optional(Literal("...").setResultsName("repetition"))
gCurlyGroup = (
    Literal("{") + gSpaces +
    gElements +
    gSpaces + Literal("}") + gRepetition).setResultsName("curly_group")
gSquareGroup = (
    Literal("[") + gSpaces +
    gElements +
    gSpaces + Literal("]") + gRepetition).setResultsName("square_group")
gGroup = Or([gCurlyGroup, gSquareGroup])
gParameters = Optional(
    OneOrMore(Group(Or([gGroup, gElement])) + gSpaces))\
    .setResultsName("parameters")
gName = Word(printables).setResultsName("name")
gUsage = Group(Or([
    Literal("Usage:"),
    Literal("usage:")]) +
    gSpace + gName + gSpaces + gParameters).setResultsName("usage")
gEmptyLine = gSpaces + gEOL
gShortText = Optional(
    Word(srange("[A-Z]") + srange("[a-z]")) + restOfLine) + gEOL_keep
#gText = OneOrMore(gShortText)
#gIntroduction = Optional(
    #Group(Word(srange("[A-Z]") + srange("[a-z]")) + Regex(".*:$"))
    #.setResultsName("introduction"))
gOptionDescriptionText = \
    Optional(gRepetition + Literal(':')) + \
    OneOrMore(
        Optional(Regex("\n")) + gSpaces + Optional(Literal('(')) +
        Word(alphas, alphanums + '_') + restOfLine)\
    .setResultsName("description")
gOptionDescriptionOption = gSpaces + \
    gRawOption.setResultsName("first_option") + Optional(gParameter) + \
    ZeroOrMore(
        Group(
            Literal(",").suppress() + gSpace.suppress() +
            gRawOption.setResultsName("option") + Optional(gParameter)))\
    .setResultsName("other_options")
gOptionDescriptionSwitch = Or([
    gOptionDescriptionOption,
    gInnerParameter,
    gStdin])
gOptionDescription = (gOptionDescriptionSwitch + gOptionDescriptionText)\
    .setResultsName("option_description")
#gBidule = gIntroduction + gOptionDescription
#gSubNext = Or([gBidule, gShortText.setResultsName("short_text")])
#gNext = Dict(ZeroOrMore(Group(gSubNext))).setResultsName("next")
gRest = Regex("(.*\n?)*").setResultsName("rest")
gHelp = Optional(gEmptyLine) + gUsage + gRest


class Stdin(object):
    def __str__(self):
        return '-'

    def build(self, form, content):
        content.append(form.Textarea("stdin"))


class Option(object):
    def __init__(self, parsed_option):
        self._raw = parsed_option
        #print('Option')
        #print('\tself._raw = ' + self._raw)
        self._names = ["".join(parsed_option.first_option)]
        parameters = []
        #if ("other_options" in parsed_option.keys()):
            #print('parsed_option["other_options"]')
            #print(parsed_option["other_options"])
        if (len(parsed_option.parameter) > 0):
            parameters.append("".join(parsed_option.parameter))
        if (0 != len(parsed_option.other_options)):
            #print("parsed_option.dump()")
            #print(parsed_option.dump())
            for other_option in parsed_option.other_options:
                #print("other_option")
                #print(type(other_option))
                #print(other_option.keys())
                self._names.append("".join(other_option.option))
                if (len(other_option.parameter) > 0):
                    #print(other_option["parameter"])
                    parameters.append("".join(other_option.parameter))
        if (len(parameters) > 0):
            # maybe comparing the different values could be interesting
            self._parameter = parameters[-1]
        else:
            self._parameter = None
        if (0 != len(parsed_option.description)):
            self._description = "".join("".join(parsed_option.description))
            self._description = self._description.replace("\n", " ")
            self._description = self._description.lstrip(" ")
            #print("\tself._description = '" + self._description + "'")
        else:
            self._description = None

    def __str__(self):
        result = "o " + ", ".join(self._names)
        if (self._parameter is not None):
            result += " " + str(self._parameter)
        if (self._description is not None):
            result += " | " + str(self._description)
        return result

    def build(self, form, content):
        if (self._parameter is None):
            content.append(form.Checkbox(", ".join(self._names)))
            #content.append(form.Radio(", ".join(self._names), ["on", "off"]))
        else:
            content.append(form.Textarea(", ".join(self._names)))


class Argument(object):
    def __init__(self, parsed_argument):
        self._raw = parsed_argument
        self._name = parsed_argument.argument

    @property
    def name(self):
        return self._name

    def __str__(self):
        return "a " + self._name

    def build(self, form, content):
        upper = self._name.upper()
        if (("OPTION" != upper) and ("OPTIONS" != upper)):
            if ("FILE" in upper):
                content.append(form.Textarea(self._name))
            else:
                content.append(form.Textbox(self._name))


class Parameter(object):
    def __init__(self, parsed_parameter):
        self._raw = parsed_parameter
        self._name = parsed_parameter.parameter

    @property
    def name(self):
        return self._name

    def __str__(self):
        return "p " + self._name

    def build(self, form, content):
        raise NotImplementedError


class BaseGroup(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _left(self):
        """Left delimiter for the group."""
        pass

    @abc.abstractmethod
    def _right(self):
        """Right delimiter for the group."""
        pass

    def __init__(self, parsed_group):
        self._raw = parsed_group
        self._elements = []
        self._build_element(parsed_group.first_element)
        for element in parsed_group.other_elements:
            self._build_element(element)

    def _build_element(self, element):
        if (len(element.option) > 0):
            self._elements.append(Option(element))
        elif (len(element.argument) > 0):
            self._elements.append(Argument(element))
        elif (len(element.stdin) > 0):
            self._elements.append(Stdin())

    def __str__(self):
        result = "g " + self._left
        result += ", ".join(map(str, self._elements))
        result += self._right
        return result

    def build(self, form, content):
        for element in self._elements:
            element.build(form, content)


class CurlyGroup(BaseGroup):
    def __init__(self, parsed_curly_group):
        BaseGroup.__init__(self, parsed_curly_group)

    @property
    def _left(self):
        return "{"

    @property
    def _right(self):
        return "}"


class SquareGroup(BaseGroup):
    def __init__(self, parsed_square_group):
        BaseGroup.__init__(self, parsed_square_group)

    @property
    def _left(self):
        return "["

    @property
    def _right(self):
        return "]"


class Usage(object):
    def __init__(self, parsed_usage):
        self._raw = parsed_usage
        self._name = parsed_usage.name
        self._options = []
        for parsed in parsed_usage.parameters:
            if (len(parsed.curly_group) > 0):
                #print "add as CurlyGroup: " + str(parsed.curly_group)
                self._options.append(CurlyGroup(parsed))
            elif (len(parsed.square_group) > 0):
                #print "add as SquareGroup: " + str(parsed.square_group)
                self._options.append(SquareGroup(parsed))
            elif (len(parsed.parameter) > 0):
                #print "add as Parameter: " + str(parsed.parameter)
                self._options.append(Parameter(parsed))
            elif (len(parsed.argument) > 0):
                self._options.append(Argument(parsed))

    @property
    def options(self):
        return self._options

    @property
    def name(self):
        return self._name

    def __str__(self):
        result = "name = {name}\n".format(name=self._name)
        for option in self._options:
            result += "  {option}\n".format(option=str(option))
        return result

    def build(self, form, content):
        for option in self._options:
            option.build(form, content)


class EmptyLine(object):
    def __str__(self):
        return "\n"

    def build(self, form, content):
        content.append(form.Break())
        #raise NotImplementedError


class Text(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    def build(self, form, content):
        content.append(form.Text(self.text))
        #raise NotImplementedError


class OptionGroup(object):
    def __init__(self):
        self.introduction = None
        self._options = []

    def add_option(self, option):
        self._options.append(option)

    def __str__(self):
        result = ""
        if (self.introduction is not None):
            #result += self.introduction + "\n"
            result += self.introduction
        for option in self._options:
            result += str(option) + "\n"
        return result

    def build(self, form, content):
        for option in self._options:
            option.build(form, content)


class SplitFeeder(object):
    def __init__(self, string, splitter="\n"):
        self._string = string
        self._splitter = splitter
        self._position = 0

    def __iter__(self):
        self._position = 0
        while ((self._position is not None) and
                (self._position != len(self._string))):
            start_index = self._position
            finish_index = self._string.find(self._splitter, self._position)
            if (-1 != finish_index):
                self._position = finish_index + 1
                yield self._string[start_index:self._position]
            else:
                self._position = None
                yield self._string[start_index:]

    def next(self):
        if ((self._position is not None) and
                (self._position != len(self._string))):
            start_index = self._position
            finish_index = self._string.find(self._splitter, self._position)
            if (-1 != finish_index):
                self._position = finish_index + 1
                return self._string[start_index:self._position]
            else:
                self._position = None
                return self._string[start_index:]
        else:
            return None

    def reset(self):
        self._position = 0


def parse_with(py_parsing_expression, string):
    return py_parsing_expression.leaveWhitespace().parseWithTabs().parseString(
        string)


def parse_as_option(string):
    #print "parse_as_option('%s')" % string
    return parse_with(gOptionDescription, string)


RE_IS_NOT_OPTION_START = re.compile(
    r"""^--?[A-Za-z0-9][-A-Za-z0-9_]*( [-A-Za-z0-9_]+,?)+\..*""")
RE_IS_OPTION_START = re.compile(
    r"\s*(--?[A-Za-z0-9][-A-Za-z0-9_]*"
    r"((\[=?[A-Za-z0-9][-A-Za-z0-9_]*])|([= ][A-Za-z0-9][-A-Za-z0-9_]*))?)"
    r"(, (--?[A-Za-z0-9][-A-Za-z0-9_]*("
    r"(\[=?[A-Za-z0-9][-A-Za-z0-9_]*])|([= ][A-Za-z0-9][-A-Za-z0-9_]*))?))*"
    r"(( :? ?.*)|)$")
RE_IS_PSEUDO_OPTION_START = re.compile(r"\s*(-|[a-z]+) +((...)?:)? [A-Za-z].*")


def is_option_start(line):
    if (line is None):
        return False
    else:
        line = line.strip('\n')
        return ((RE_IS_NOT_OPTION_START.match(line) is None) and
                ((RE_IS_OPTION_START.match(line) is not None) or
                    (RE_IS_PSEUDO_OPTION_START.match(line) is not None)))


def parse_text(text, feeder, items):
    #print('parse_text')
    eot = False
    current_line = text
    text = ""
    while (not eot):
        #print("current_line = '" + str(current_line) + "'")
        if (current_line is None):
            #print("None")
            items.append(Text(text))
            eot = True
        elif ('\n' == current_line):
            #print("-Empty-")
            if (0 != len(text)):
                items.append(Text(text))
            items.append(EmptyLine())
            current_line = feeder.next()
            parse_start(current_line, feeder, items)
            eot = True
        elif (is_option_start(current_line)):
            #print("option")
            if (0 != len(text)):
                items.append(Text(text))
            og = OptionGroup()
            parse_option(current_line, feeder, items, og)
            eot = True
        elif (current_line.endswith(":\n")):
            #print("...:")
            #if ((0 != len(text)) and (not text.endswith(" "))):
                #text += " "
            text += current_line
            current_line = feeder.next()
            if (is_option_start(current_line)):
                og = OptionGroup()
                og.introduction = text
                parse_option(current_line, feeder, items, og)
                eot = True
        else:
            #print("something else")
            #if ((0 != len(text)) and (not text.endswith(" "))):
                #text += " "
            text += current_line
            current_line = feeder.next()


def parse_option(option_text, feeder, items, option_group):
    #print('parse_option')
    can_parse = False
    finished = False
    is_empty = False
    while (not can_parse):
        current_line = feeder.next()
        if (current_line is None):
            can_parse = True
            finished = True
        elif (0 == len(current_line)):
            finished = True
            is_empty = True
            can_parse = True
        else:
            if (is_option_start(current_line)):
                can_parse = True
            else:
                if (not current_line.startswith(' ')):
                    finished = True
                    is_empty = True
                    can_parse = True
                #else:
                    #option_text += "\n" + current_line
                else:
                    option_text += current_line
    #print("option_text")
    #print(option_text)
    parsed_option = gOptionDescription.leaveWhitespace().\
        parseWithTabs().parseString(option_text)
    option_group.add_option(Option(parsed_option))
    if (finished):
        items.append(option_group)
        if (is_empty):
            parse_start(current_line, feeder, items)
    else:
        parse_option(current_line, feeder, items, option_group)


def parse_start(current_line, feeder, items):
    #print('parse_start')
    if (current_line is not None):
        if (is_option_start(current_line)):
            parse_option(current_line, feeder, items, OptionGroup())
        else:
            parse_text(current_line, feeder, items)


def parse_more_help(input, usage):
    """The input should contain help without the usage part."""
    feeder = SplitFeeder(input)
    current_line = feeder.next()
    items = []
    parse_start(current_line, feeder, items)
    return items


def parse_help(input, stdin=False):
    parsed = gHelp.leaveWhitespace().parseWithTabs().parseString(input)
    #print 'parsed ...'
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #print "".join(map(str, parsed.usage.asList()))
    #pp.pprint(parsed.asDict())
    items = [Usage(parsed.usage)]
    #print items[0]
    items += parse_more_help(parsed.rest[1:], parsed.usage)
    if (stdin):
        items.append(Stdin())
    return items


def get_help(program, arguments, help_command):
    import sh
    run = sh.Command(program)
    args = arguments + [help_command.lstrip(' ')]
    #print("args =", args)
    return str(run(
        args,
        _ok_code=list(range(0, 255))))


class JsonForm(object):
    """Class used to build the json."""

    def __init__(self):
        pass

    def Radio(self, name, args):
        dico = {
            'control': 'radio',
            'name': name,
            'args': args,
        }
        return dico

    def Break(self):
        dico = {
            'control': 'break',
        }
        return dico

    def Checkbox(self, name, checked=False):
        dico = {
            'control': 'checkbox',
            'name': name,
            'checked': checked,
        }
        return dico

    def Text(self, content):
        dico = {
            'control': 'text',
            'content': content,
        }
        return dico

    def Textarea(self, name):
        dico = {
            'control': 'textarea',
            'name': name,
        }
        return dico

    def Textbox(self, name):
        dico = {
            'control': 'textbox',
            'name': name,
        }
        return dico


def dump_json(name, arguments, path, help_text, stdin, pretty=False):
    json_form = JsonForm()
    content = []
    for item in parse_help(help_text, stdin):
        item.build(json_form, content)
    output = {
        'program': {
            'name': name,
            'arguments': arguments,
            'path': path,
        },
        'content': content,
    }
    if (pretty):
        return json.dumps(
            output,
            sort_keys=True,
            indent=4, separators=(',', ': '))
    else:
        return json.dumps(output)


def main(argv):
    """
    `argv`: command line arguments without the name of the program (poped $0).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j", "--json",
        help="Dump as json.",
        default=False,
        action='store_true')
    parser.add_argument(
        "--pretty-json",
        help="Try to make json output pretty.",
        default=False,
        action='store_true')
    parser.add_argument(
        "--stdin",
        help="Generate a control for stdin.",
        default=False,
        action='store_true')
    parser.add_argument(
        "-x", "--extra-arguments",
        help="Extra argument you need to pass to the program.",
        default=[],
        action='append')
    parser.add_argument(
        "-c", "--help-command",
        help="What needs to be given to make the program display help.",
        default="--help")
    parser.add_argument("program")
    arguments = parser.parse_args(argv)
    help_text = get_help(
        arguments.program,
        arguments.extra_arguments,
        arguments.help_command)
    import os
    program = os.path.basename(arguments.program)
    path = os.path.abspath(arguments.program)
    if (not os.path.exists(path)):
        import sh
        path = sh.which(arguments.program)
    #print(help_text)
    if (arguments.json):
        print(dump_json(
            program,
            arguments.extra_arguments,
            path,
            help_text,
            arguments.stdin,
            arguments.pretty_json))
    else:
        for item in parse_help(help_text, arguments.stdin):
            print(item)


if ("__main__" == __name__):
    main(sys.argv[1:])  # pragma: no coverage
