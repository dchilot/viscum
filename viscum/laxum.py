import argparse


from pyparsing import Literal
from pyparsing import Optional
from pyparsing import Group
from pyparsing import Dict
from pyparsing import Or
from pyparsing import Regex
from pyparsing import Word
from pyparsing import ZeroOrMore
from pyparsing import OneOrMore
from pyparsing import FollowedBy
from pyparsing import alphas
from pyparsing import alphanums
from pyparsing import srange
from pyparsing import restOfLine
import re

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
gImportantSpaces = ZeroOrMore(gSpace)
gInnerArgument = Word(alphas, alphanums + '_-').setResultsName("argument")
gArgument = gSpace + gInnerArgument
gInnerParameter = Word(alphas, alphanums + '_-')
gInnerParameterPlus = Or([gSpace, Literal('=')]).suppress() + gInnerParameter
gInnerParameterPlusLess = \
    Optional(Or([gSpace, Literal('=')]).suppress()) + gInnerParameter
gParameter = (Or([
    Group(Literal('[') + gInnerParameterPlusLess + Literal(']')),
    gInnerParameterPlus + FollowedBy(
        Or([
            gEOL,
            gSpace + Literal(','),
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
gName = (Word(alphas + "/.", alphanums + '_' + "/.")).setResultsName("name")
gUsage = Group(Or([
    Literal("Usage:"),
    Literal("usage:")]) +
    gSpace + gName + gSpaces + gParameters).setResultsName("usage")
gEmptyLine = gSpaces + gEOL
gShortText = Optional(
    Word(srange("[A-Z]") + srange("[a-z]")) + restOfLine) + gEOL
gText = OneOrMore(gShortText)
gIntroduction = Optional(
    Group(Word(srange("[A-Z]") + srange("[a-z]")) + Regex(".*:$"))
    .setResultsName("introduction"))
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
gBidule = gIntroduction + gOptionDescription
gSubNext = Or([gBidule, gShortText.setResultsName("short_text")])
gNext = Dict(ZeroOrMore(Group(gSubNext))).setResultsName("next")
gRest = Regex("(.*\n?)*").setResultsName("rest")
gHelp = Optional(gEmptyLine) + gUsage + gRest


class Stdin(object):
    def __str__(self):
        return '-'


class Option(object):
    def __init__(self, parsed_option):
        self._raw = parsed_option
        self._names = ["".join(parsed_option.first_option)]
        parameters = []
        #if ("other_options" in parsed_option.keys()):
            #print 'parsed_option["other_options"]'
            #print parsed_option["other_options"]
        if (len(parsed_option.parameter) > 0):
            parameters.append("".join(parsed_option.parameter))
        if (0 != len(parsed_option.other_options)):
            #print "parsed_option.dump()"
            #print parsed_option.dump()
            for other_option in parsed_option.other_options:
                #print "other_option"
                #print type(other_option)
                #print other_option.keys()
                self._names.append("".join(other_option.option))
                if (len(other_option.parameter) > 0):
                    #print other_option["parameter"]
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
            #print "self._description = '" + self._description + "'"
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
            content.append(form.Checkbox(", ".join(self._names), value="bug"))
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
        pass


class BaseGroup(object):
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
        pass


class Text(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    def build(self, form, content):
        pass


class OptionGroup(object):
    def __init__(self):
        self.introduction = None
        self._options = []

    def add_option(self, option):
        self._options.append(option)

    def __str__(self):
        result = ""
        if (self.introduction is not None):
            result += self.introduction + "\n"
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

    def next(self):
        if ((self._position is not None) and
                (self._position != len(self._string))):
            start_index = self._position
            finish_index = self._string.find(self._splitter, self._position)
            if (-1 != finish_index):
                self._position = finish_index + 1
                return self._string[start_index:finish_index]
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


RE_IS_NOT_OPTION_START = re.compile("""^--?[A-Za-z0-9][-A-Za-z0-9_]*( [-A-Za-z0-9_]+,?)+\..*""")
RE_IS_OPTION_START = re.compile("""\s*(--?[A-Za-z0-9][-A-Za-z0-9_]*((\[=?[A-Za-z0-9][-A-Za-z0-9_]*])|([= ][A-Za-z0-9][-A-Za-z0-9_]*))?)(, (--?[A-Za-z0-9][-A-Za-z0-9_]*((\[=?[A-Za-z0-9][-A-Za-z0-9_]*])|([= ][A-Za-z0-9][-A-Za-z0-9_]*))?))*(( :? ?.*)|)$""")
RE_IS_PSEUDO_OPTION_START = re.compile("""\s*(-|[a-z]+) +((...)?:)? [A-Za-z].*""")


def is_option_start(line):
    if (line is None):
        return False
    else:
        return ((RE_IS_NOT_OPTION_START.match(line) is None) and
                ((RE_IS_OPTION_START.match(line) is not None) or
                (RE_IS_PSEUDO_OPTION_START.match(line) is not None)))


def parse_text(text, feeder, items):
    eot = False
    current_line = text
    text = ""
    while (not eot):
        #print "current_line = '" + str(current_line) + "'"
        if (current_line is None):
            #print "None"
            items.append(Text(text))
            eot = True
        elif (0 == len(current_line)):
            #print "-Empty-"
            if (0 != len(text)):
                items.append(Text(text))
            items.append(EmptyLine())
            current_line = feeder.next()
            parse_start(current_line, feeder, items)
            eot = True
        elif (is_option_start(current_line)):
            if (0 != len(text)):
                items.append(Text(text))
            og = OptionGroup()
            parse_option(current_line, feeder, items, og)
            eot = True
        elif (current_line.endswith(":")):
            #print "...:"
            if ((0 != len(text)) and (not text.endswith(" "))):
                text += " "
            text += current_line
            current_line = feeder.next()
            if (is_option_start(current_line)):
                og = OptionGroup()
                og.introduction = text
                parse_option(current_line, feeder, items, og)
                eot = True
        else:
            #print "something else"
            if ((0 != len(text)) and (not text.endswith(" "))):
                text += " "
            text += current_line
            current_line = feeder.next()


def parse_option(option_text, feeder, items, option_group):
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
                else:
                    option_text += "\n" + current_line
    #print "option_text"
    #print option_text
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


def parse_help(input):
    parsed = gHelp.leaveWhitespace().parseWithTabs().parseString(input)
    #print 'parsed ...'
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #print "".join(map(str, parsed.usage.asList()))
    #pp.pprint(parsed.asDict())
    items = [Usage(parsed.usage)]
    #print items[0]
    items += parse_more_help(parsed.rest[1:], parsed.usage)
    return items


def get_help(program, help_command):
    import sh
    run = sh.Command(program)
    return str(run(help_command))


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
        "-c", "--help-command",
        help="What needs to be given to make the program display help.",
        default="--help")
    parser.add_argument("program")
    arguments = parser.parse_args(argv)
    if (arguments.json):
        print 'json dump requested but not available yet.'
    help_text = get_help(arguments.program, arguments.help_command)
    print help_text
    for item in parse_help(help_text):
        print item


if ("__main__" == __name__):
    import sys
    main(sys.argv[1:])
