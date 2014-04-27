from nose.tools import assert_equal
from nose.tools import assert_true
from nose.tools import assert_false
import unittest
import viscum.main as wrapper


class SplitFeeder(unittest.TestCase):
    def test_1(self):
        sf = wrapper.SplitFeeder("""This is a sample string.""", " ")
        expected = ["This ", "is ", "a ", "sample ", "string.", None]
        found = False
        while (found is not None):
            found = sf.next()
            assert_equal(expected.pop(0), found)

    def test_2(self):
        sf = wrapper.SplitFeeder("", " ")
        assert_equal(sf.next(), None)

    def test_3(self):
        sf = wrapper.SplitFeeder("Nospaceinhere.", " ")
        assert_equal(sf.next(), "Nospaceinhere.")
        assert_equal(sf.next(), None)

    def test_4(self):
        sf = wrapper.SplitFeeder("endswithaspace ", " ")
        assert_equal(sf.next(), "endswithaspace ")
        assert_equal(sf.next(), None)

    def test_5(self):
        sf = wrapper.SplitFeeder("1 2 3", " ")
        assert_equal(sf.next(), "1 ")
        assert_equal(sf.next(), "2 ")
        sf.reset()
        assert_equal(sf.next(), "1 ")
        assert_equal(sf.next(), "2 ")
        assert_equal(sf.next(), "3")
        assert_equal(sf.next(), None)
        assert_equal(sf.next(), None)
        sf.reset()
        assert_equal(sf.next(), "1 ")


class IsOptionStart(unittest.TestCase):
    def test_1(self):
        assert_true(wrapper.is_option_start("    -x"))
        assert_true(wrapper.is_option_start("-x"))
        assert_true(wrapper.is_option_start("--xx"))
        assert_true(wrapper.is_option_start("   --xx"))

    def test_2(self):
        assert_false(wrapper.is_option_start("Text   --xx"))
        assert_false(wrapper.is_option_start(" Text   -x"))
        assert_false(wrapper.is_option_start(" Text   -x flag -y"))

    def test_3(self):
        assert(not wrapper.is_option_start("--color=auto, color codes are"))
        assert(wrapper.is_option_start("  -v, --verbose     Verbose mode."))
        assert(wrapper.is_option_start(
            "file   : program read from script file"))
        assert(wrapper.is_option_start("-      : program read"))
        assert(wrapper.is_option_start("arg ...: arguments"))

    def test_4(self):
        assert(not wrapper.is_option_start(
            "PYTHONSTARTUP: "
            "file executed on interactive startup (no default)"))
        assert(not wrapper.is_option_start("Other environment variables:"))
        assert(wrapper.is_option_start(
            "  -E, --extended-regexp     "
            "PATTERN is an extended regular expression"))
        assert(wrapper.is_option_start(
            "  -L, --files-without-match "
            "only print FILE names containing no match"))

    def test_5(self):
        assert(wrapper.is_option_start(
            "-n, --quiet, --silent                  "
            "suppress automatic printing of pattern space"))
        assert(wrapper.is_option_start("-e script, --expression=script"))
        assert(wrapper.is_option_start("-i[SUFFIX], --in-place[=SUFFIX]"))

    def test_6(self):
        assert(wrapper.is_option_start("  -u                       (ignored)"))

    def test_7(self):
        assert(not wrapper.is_option_start(
            "-t may be used only when translating.  "
            "SET2 is extended to length of"))


class ParseText(unittest.TestCase):
    def test_1(self):
        sf = wrapper.SplitFeeder("""This is some text.
On more than one line. It is important: there is a trap !""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        assert_equal(1, len(items))
        assert_equal(
            "This is some text.\nOn more than one line."
            " It is important: there is a trap !", str(items[0]))

    def test_2(self):
        sf = wrapper.SplitFeeder("""Single line.
""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        assert_equal(1, len(items))
        assert_equal("Single line.\n", str(items[0]))

    def test_3(self):
        sf = wrapper.SplitFeeder("""One line before an empty one.

And then an other line.""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        print(items)
        #assert_equal(1, len(items))
        #assert_equal(
            #"One line before an empty one.\n"
            #"\n"
            #"And then an other line.", str(items[0]))
        assert_equal(3, len(items))
        assert_equal("One line before an empty one.\n", str(items[0]))
        assert_equal("\n", str(items[1]))
        assert_equal("And then an other line.", str(items[2]))

    def test_4(self):
        sf = wrapper.SplitFeeder("""Be careful.
  --this is  an options (wrongly formatted)""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        print(items)
        assert_equal(2, len(items))
        assert_equal("Be careful.\n", str(items[0]))

    def test_5(self):
        sf = wrapper.SplitFeeder("""This:
Is not an option !""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        assert_equal(1, len(items))
        assert_equal("This:\nIs not an option !", str(items[0]))


class ParseAsOption(unittest.TestCase):
    def test_1(self):
        parsed_option = wrapper.parse_as_option(
            " --option parameter   Short description of the option.")
        assert_equal("--option", "".join(parsed_option.first_option))
        assert_equal("parameter", parsed_option.parameter)
        assert_equal(
            "Short description of the option.",
            "".join("".join(parsed_option.description)))

    def test_2(self):
        parsed_option = wrapper.parse_as_option(
            " -o, --option param   Short description of the option.")
        assert_equal("-o", "".join(parsed_option.first_option))
        print("parsed_option.other_options")
        print(parsed_option.other_options)
        assert_equal(
            "--option",
            "".join(parsed_option.other_options[0].option))
        assert_equal(
            "param",
            "".join(parsed_option.other_options[0].parameter))
        assert_equal(
            "Short description of the option.",
            "".join("".join(parsed_option.description)))

    def test_3(self):
        parsed_option = wrapper.parse_as_option(
            " -w, --word  Short description of the option.")
        assert_equal("-w", "".join(parsed_option.first_option))
        assert_equal("--word", "".join(parsed_option.other_options[0]))
        assert_equal("", parsed_option.parameter)
        assert_equal(
            "Short description of the option.",
            "".join("".join(parsed_option.description)))

    def test_4(self):
        parsed_option = wrapper.parse_as_option(
            "  -w, --word  Short description of the option.")
        assert_equal("-w", "".join(parsed_option.first_option))
        assert_equal("--word", "".join(parsed_option.other_options[0]))
        assert_equal("", parsed_option.parameter)
        assert_equal(
            "Short description of the option.",
            "".join("".join(parsed_option.description)))

    def test_5(self):
        parsed_option = wrapper.parse_as_option(
            """ --xx Xxx
    Here is the description.""")
        assert_equal("--xx", "".join(parsed_option.first_option))
        assert_equal("Xxx", parsed_option.parameter)
        assert_equal(
            "\nHere is the description.",
            "".join("".join(parsed_option.description)))

    def test_6(self):
        parsed_option = wrapper.parse_as_option(
            """ --yy Yyy
    Here is the description. And it is
    on more than one line.""")
        assert_equal("--yy", "".join(parsed_option.first_option))
        assert_equal("Yyy", parsed_option.parameter)
        assert_equal(
            """\nHere is the description. And it is
on more than one line.""", "".join("".join(parsed_option.description)))

    def test_7(self):
        wrapper.parse_as_option("""\
      --block-size=SIZE      use SIZE-byte blocks""")

    def test_8(self):
        wrapper.parse_with(
            wrapper.gOptionDescription,
            "-c cmd : program passed in as string (terminates option list)")

    def test_9(self):
        wrapper.parse_with(wrapper.gOptionDescription,
                           """file   : program read from script file""")

    def test_10(self):
        wrapper.parse_with(
            wrapper.gOptionDescription,
            """  -q, --quiet, --silent     suppress all normal output""")

    def test_11(self):
        parsed_option = wrapper.parse_with(
            wrapper.gOptionDescription,
            """  -e script, --expression=script
                 add the script to the commands to be executed""")
        assert_equal("-e", "".join(parsed_option.first_option))
        assert_equal("--expression", "".join(
            parsed_option.other_options[0].option))
        assert_equal("script", parsed_option.parameter)
        assert_equal(
            "\nadd the script to the commands to be executed",
            "".join("".join(parsed_option.description)))


class ParseAsName(unittest.TestCase):
    def test_1(self):
        wrapper.parse_with(wrapper.gName,
                           """python""")
            #usage: python [option] ... [-c cmd | -m mod | file | -] [arg] ...


class ParseAsParameters(unittest.TestCase):
    def test_1(self):
        wrapper.parse_with(
            wrapper.gParameters,
            """[option] ... [-c cmd | -m mod | file | -] [arg] ...""")


class ParseAsUsage(unittest.TestCase):
    def test_1(self):
        wrapper.parse_with(
            wrapper.gUsage,
            """usage: python [option] ... """
            """[-c cmd | -m mod | file | -] [arg] ...""")


class ParseOption(unittest.TestCase):
    def test_1(self):
        sf = wrapper.SplitFeeder("""\
  -f, --file name   Give a file to process.
  -v, --verbose     Verbose mode.""")
        items = []
        current_line = sf.next()
        og = wrapper.OptionGroup()
        wrapper.parse_option(current_line, sf, items, og)
        assert_equal(1, len(items))
        assert_equal("""\
o -f, --file name | Give a file to process.
o -v, --verbose | Verbose mode.
""", str(items[0]))

    def test_2(self):
        sf = wrapper.SplitFeeder("""\
  -f, --file name   Give a file to process.
  -v, --verbose     Verbose mode.
""")
        items = []
        current_line = sf.next()
        og = wrapper.OptionGroup()
        wrapper.parse_option(current_line, sf, items, og)
        assert_equal(1, len(items))
        assert_equal("""\
o -f, --file name | Give a file to process.
o -v, --verbose | Verbose mode.
""", str(items[0]))

    def test_3(self):
        sf = wrapper.SplitFeeder("""\
  -i[SUFFIX], --in-place[=SUFFIX]
                 edit files in place (makes backup if extension supplied)
""")
        items = []
        current_line = sf.next()
        og = wrapper.OptionGroup()
        wrapper.parse_option(current_line, sf, items, og)
        assert_equal(1, len(items))
        assert_equal("""\
o -i, --in-place [SUFFIX] | edit files in place """
                     """(makes backup if extension supplied)
""", str(items[0]))

    def test_4(self):
        sf = wrapper.SplitFeeder("""\
  -L, --files-without-match only print FILE names containing no match
""")
        items = []
        current_line = sf.next()
        og = wrapper.OptionGroup()
        wrapper.parse_option(current_line, sf, items, og)
        assert_equal(1, len(items))
        assert_equal("""\
o -L, --files-without-match | only print FILE names containing no match
""", str(items[0]))


class ParseText2(unittest.TestCase):
    def test_1(self):
        sf = wrapper.SplitFeeder("""\
Description ... to be completed.

Options:
  -f    Description of flag f.
        Continued description.
  --flag
        Description on a different line.
""")
        items = []
        current_line = sf.next()
        wrapper.parse_text(current_line, sf, items)
        assert_equal(3, len(items))
        assert_equal("Description ... to be completed.\n", str(items[0]))
        assert_equal("\n", str(items[1]))
        assert_equal("""\
Options:
o -f | Description of flag f. Continued description.
o --flag | Description on a different line.
""", str(items[2]))


class MockForm(object):
    """Class to make sure the form is built properly"""

    def __init__(self):
        pass

    def Break(self):
        return "Break"

    def Radio(self, name, args):
        return "Radio:" + str(name)

    def Checkbox(self, name, checked=False, value=""):
        return "Checkbox:" + str(name) + " " + str(checked)

    def Text(self, content):
        return "Text:" + content

    def Textarea(self, name):
        return "Textarea:" + str(name)

    def Textbox(self, name):
        return "Textbox:" + str(name)


class ParseHelp(unittest.TestCase):
    def test_1(self):
        ls_help = """
Usage: ls [OPTION]... [FILE]...
List information about the FILEs (the current directory by default).
Sort entries alphabetically if none of -cftuvSUX nor --sort.

Mandatory arguments to long options are mandatory for short options too.
  -a, --all                  do not ignore entries starting with .
  -A, --almost-all           do not list implied . and ..
      --author               with -l, print the author of each file
  -b, --escape               print octal escapes for nongraphic characters
      --block-size=SIZE      use SIZE-byte blocks
  -B, --ignore-backups       do not list implied entries ending with ~
  -c                         with -lt: sort by, and show, ctime (time of last
                               modification of file status information)
                               with -l: show ctime and sort by name
                               otherwise: sort by ctime
  -C                         list entries by columns
      --color[=WHEN]         control whether color is used to distinguish file
                               types.  WHEN may be `never', `always', or `auto'
  -d, --directory            list directory entries instead of contents,
                               and do not dereference symbolic links
  -D, --dired                generate output designed for Emacs' dired mode
  -f                         do not sort, enable -aU, disable -ls --color
  -F, --classify             append indicator (one of */=>@|) to entries
      --file-type            likewise, except do not append `*'
      --format=WORD          across -x, commas -m, horizontal -x, long -l,
                               single-column -1, verbose -l, vertical -C
      --full-time            like -l --time-style=full-iso
  -g                         like -l, but do not list owner
      --group-directories-first
                             group directories before files
  -G, --no-group             in a long listing, don't print group names
  -h, --human-readable       with -l, print sizes in human readable format
                               (e.g., 1K 234M 2G)
      --si                   likewise, but use powers of 1000 not 1024
  -H, --dereference-command-line
                             follow symbolic links listed on the command line
      --dereference-command-line-symlink-to-dir
                             follow each command line symbolic link
                             that points to a directory
      --hide=PATTERN         do not list implied entries matching shell PATTERN
                               (overridden by -a or -A)
      --indicator-style=WORD  append indicator with style WORD to entry names:
                               none (default), slash (-p),
                               file-type (--file-type), classify (-F)
  -i, --inode                print the index number of each file
  -I, --ignore=PATTERN       do not list implied entries matching shell PATTERN
  -k                         like --block-size=1K
  -l                         use a long listing format
  -L, --dereference          when showing file information for a symbolic
                               link, show information for the file the link
                               references rather than for the link itself
  -m                         fill width with a comma separated list of entries
  -n, --numeric-uid-gid      like -l, but list numeric user and group IDs
  -N, --literal              print raw entry names (don't treat e.g. control
                               characters specially)
  -o                         like -l, but do not list group information
  -p, --indicator-style=slash
                             append / indicator to directories
  -q, --hide-control-chars   print ? instead of non graphic characters
      --show-control-chars   show non graphic characters as-is (default
                             unless program is `ls' and output is a terminal)
  -Q, --quote-name           enclose entry names in double quotes
      --quoting-style=WORD   use quoting style WORD for entry names:
                               literal, locale, shell, shell-always, c, escape
  -r, --reverse              reverse order while sorting
  -R, --recursive            list subdirectories recursively
  -s, --size                 print the size of each file, in blocks
  -S                         sort by file size
      --sort=WORD            sort by WORD instead of name: none -U,
                             extension -X, size -S, time -t, version -v
      --time=WORD            with -l, show time as WORD instead of modification
                             time: atime -u, access -u, use -u, ctime -c,
                             or status -c; use specified time as sort key
                             if --sort=time
      --time-style=STYLE     with -l, show times using style STYLE:
                             full-iso, long-iso, iso, locale, +FORMAT.
                             FORMAT is interpreted like `date'; if FORMAT is
                             FORMAT1<newline>FORMAT2, FORMAT1 applies to
                             non-recent files and FORMAT2 to recent files;
                             if STYLE is prefixed with `posix-', STYLE
                             takes effect only outside the POSIX locale
  -t                         sort by modification time
  -T, --tabsize=COLS         assume tab stops at each COLS instead of 8
  -u                         with -lt: sort by, and show, access time
                               with -l: show access time and sort by name
                               otherwise: sort by access time
  -U                         do not sort; list entries in directory order
  -v                         sort by version
  -w, --width=COLS           assume screen width instead of current value
  -x                         list entries by lines instead of by columns
  -X                         sort alphabetically by entry extension
  -Z, --context              print any SELinux security context of each file
  -1                         list one file per line
      --append-exe           append .exe if cygwin magic was needed
      --help     display this help and exit
      --version  output version information and exit

SIZE may be (or may be an integer optionally followed by) one of following:
kB 1000, K 1024, MB 1000*1000, M 1024*1024, and so on for G, T, P, E, Z, Y.

By default, color is not used to distinguish types of files.  That is
equivalent to using --color=none.  Using the --color option without the
optional WHEN argument is equivalent to using --color=always.  With
--color=auto, color codes are output only if standard output is connected
to a terminal (tty).  The environment variable LS_COLORS can influence the
colors, and can be set easily by the dircolors command.

Exit status is 0 if OK, 1 if minor problems, 2 if serious trouble.

Report bugs to <bug-coreutils@gnu.org>.
"""
        items = wrapper.parse_help(ls_help)
        assert_equal(13, len(items))
        assert_equal(
            "List information about the FILEs (the current directory "
            "by default).\nSort entries alphabetically if none of "
            "-cftuvSUX nor --sort.\n",
            str(items[1]))
        print("items parsed:")
        for item in items:
            print(item)
#        assert(False)

    def test_2(self):
        python_help = """
usage: python [option] ... [-c cmd | -m mod | file | -] [arg] ...
Options and arguments (and corresponding environment variables):
-c cmd : program passed in as string (terminates option list)
-d     : debug output from parser (also PYTHONDEBUG=x)
-E     : ignore environment variables (such as PYTHONPATH)
-h     : print this help message and exit (also --help)
-i     : inspect interactively after running script, (also PYTHONINSPECT=x)
         and force prompts, even if stdin does not appear to be a terminal
-m mod : run library module as a script (terminates option list)
-O     : optimize generated bytecode (a tad; also PYTHONOPTIMIZE=x)
-OO    : remove doc-strings in addition to the -O optimizations
-Q arg : division options: -Qold (default), -Qwarn, -Qwarnall, -Qnew
-S     : don't imply 'import site' on initialization
-t     : issue warnings about inconsistent tab usage (-tt: issue errors)
-u     : unbuffered binary stdout and stderr (also PYTHONUNBUFFERED=x)
         see man page for details on internal buffering relating to '-u'
-v     : verbose (trace import statements) (also PYTHONVERBOSE=x)
-V     : print the Python version number and exit (also --version)
-W arg : warning control (arg is action:message:category:module:lineno)
-x     : skip first line of source, allowing use of non-Unix forms of #!cmd
file   : program read from script file
-      : program read from stdin (default; interactive mode if a tty)
arg ...: arguments passed to program in sys.argv[1:]
Other environment variables:
PYTHONSTARTUP: file executed on interactive startup (no default)
PYTHONPATH   : ':'-separated list of directories prefixed to the
               default module search path.  The result is sys.path.
PYTHONHOME   : alternate <prefix> directory (or <prefix>:<exec_prefix>).
               The default module search path uses <prefix>/pythonX.X.
PYTHONCASEOK : ignore case in 'import' statements (Windows).

"""
        items = wrapper.parse_help(python_help)
        assert_equal(4, len(items))
        print("items parsed:")
        for item in items:
            print(item)
        # the end of the help is not parsed properly but it is not important
        # for now because it is not to be used to generate anything to be used
        # to compute the GUI
#        assert(False)

    def test_3(self):
        sed_help = """
Usage: sed [OPTION]... {script-only-if-no-other-script} [input-file]...

  -n, --quiet, --silent
                 suppress automatic printing of pattern space
  -e script, --expression=script
                 add the script to the commands to be executed
  -f script-file, --file=script-file
                 add the contents of script-file to the commands to be executed
  -i[SUFFIX], --in-place[=SUFFIX]
                 edit files in place (makes backup if extension supplied)
  -l N, --line-length=N
                 specify the desired line-wrap length for the `l' command
  --posix
                 disable all GNU extensions.
  -r, --regexp-extended
                 use extended regular expressions in the script.
  -s, --separate
                 consider files as separate rather than as a single continuous
                 long stream.
  -b, --binary
                 do not convert DOS to UNIX lineendings (only on systems
                 supporting different lineendings).
  -u, --unbuffered
                 load minimal amounts of data from the input files and flush
                 the output buffers more often
      --help     display this help and exit
      --version  output version information and exit

If no -e, --expression, -f, or --file option is given, then the first
non-option argument is taken as the sed script to interpret.  All
remaining arguments are names of input files; if no input files are
specified, then the standard input is read.

E-mail bug reports to: bonzini@gnu.org .
Be sure to include the word ``sed'' somewhere in the ``Subject:'' field.
"""
        items = wrapper.parse_help(sed_help)
        print("items parsed:")
        for i, item in enumerate(items):
            print(i)
            print(item)
        assert_equal(7, len(items))
        #assert(False)

    def test_4(self):
        grep_help = """
Usage: grep [OPTION]... PATTERN [FILE] ...
Search for PATTERN in each FILE or standard input.
Example: grep -i 'hello world' menu.h main.c

Regexp selection and interpretation:
  -E, --extended-regexp     PATTERN is an extended regular expression
  -F, --fixed-strings       PATTERN is a set of newline-separated strings
  -G, --basic-regexp        PATTERN is a basic regular expression
  -e, --regexp=PATTERN      use PATTERN as a regular expression
  -f, --file=FILE           obtain PATTERN from FILE
  -i, --ignore-case         ignore case distinctions
  -w, --word-regexp         force PATTERN to match only whole words
  -x, --line-regexp         force PATTERN to match only whole lines
  -z, --null-data           a data line ends in 0 byte, not newline

Miscellaneous:
  -s, --no-messages         suppress error messages
  -v, --invert-match        select non-matching lines
  -V, --version             print version information and exit
      --help                display this help and exit
      --mmap                use memory-mapped input if possible

Output control:
  -b, --byte-offset         print the byte offset with output lines
  -n, --line-number         print line number with output lines
  -H, --with-filename       print the filename for each match
  -h, --no-filename         suppress the prefixing filename on output
  -q, --quiet, --silent     suppress all normal output
      --binary-files=TYPE   assume that binary files are TYPE
                            TYPE is 'binary', 'text', or 'without-match'.
  -a, --text                equivalent to --binary-files=text
  -I                        equivalent to --binary-files=without-match
  -d, --directories=ACTION  how to handle directories
                            ACTION is 'read', 'recurse', or 'skip'.
  -r, --recursive           equivalent to --directories=recurse.
  -L, --files-without-match only print FILE names containing no match
  -l, --files-with-matches  only print FILE names containing matches
  -c, --count               only print a count of matching lines per FILE
  -Z, --null                print 0 byte after FILE name

Context control:
  -B, --before-context=NUM  print NUM lines of leading context
  -A, --after-context=NUM   print NUM lines of trailing context
  -C, --context[=NUM]       print NUM (default 2) lines of output context
                            unless overridden by -A or -B
  -NUM                      same as --context=NUM
  -U, --binary              do not strip CR characters at EOL (MSDOS)
  -u, --unix-byte-offsets   report offsets as if CRs were not there (MSDOS)

`egrep' means `grep -E'.  `fgrep' means `grep -F'.
With no FILE, or when FILE is -, read standard input.  If less than
two FILEs given, assume -h.  Exit status is 0 if match, 1 if no match,
and 2 if trouble.

Report bugs to <bug-gnu-utils@gnu.org>.
"""
        items = wrapper.parse_help(grep_help)
        assert_equal(14, len(items))
        print("items parsed:")
        for i, item in enumerate(items):
            print(i)
            print(item)
        #assert(False)

    cat_help = """
Usage: cat [OPTION] [FILE]...
Concatenate FILE(s), or standard input, to standard output.

  -A, --show-all           equivalent to -vET
  -b, --number-nonblank    number nonblank output lines
  -e                       equivalent to -vE
  -E, --show-ends          display $ at end of each line
  -n, --number             number all output lines
  -s, --squeeze-blank      never more than one single blank line
  -t                       equivalent to -vT
  -T, --show-tabs          display TAB characters as ^I
  -u                       (ignored)
  -v, --show-nonprinting   use ^ and M- notation, except for LFD and TAB
      --help               display this help and exit
      --version            output version information and exit

With no FILE, or when FILE is -, read standard input.

  -B, --binary             use binary writes to the console device.


Report bugs to <bug-textutils@gnu.org>.
"""

    def test_5(self):
        items = wrapper.parse_help(ParseHelp.cat_help)
        assert_equal(11, len(items))
        expected = [
            """name = cat
  g [a OPTION]
  g [a FILE]\n""",
            "Concatenate FILE(s), or standard input, to standard output.\n",
            "\n",
            """o -A, --show-all | equivalent to -vET
o -b, --number-nonblank | number nonblank output lines
o -e | equivalent to -vE
o -E, --show-ends | display $ at end of each line
o -n, --number | number all output lines
o -s, --squeeze-blank | never more than one single blank line
o -t | equivalent to -vT
o -T, --show-tabs | display TAB characters as ^I
o -u | (ignored)
o -v, --show-nonprinting | use ^ and M- notation, except for LFD and TAB
o --help | display this help and exit
o --version | output version information and exit\n""",
            "\n",
            "With no FILE, or when FILE is -, read standard input.\n",
            "\n",
            "o -B, --binary | use binary writes to the console device.\n",
            "\n",
            "\n",
            "Report bugs to <bug-textutils@gnu.org>.\n",
        ]
        print("items parsed:")
        for i, item in enumerate(items):
            print(i)
            print(item)
            assert_equal(expected.pop(0), str(item))
        #assert(False)

    def test_6(self):
        tr_help_light = """
Usage: tr [OPTION]... SET1 [SET2]
Translate, squeeze, and/or delete characters from standard input,
writing to standard output.

  -c, --complement        first complement SET1
  -d, --delete            delete characters in SET1, do not translate
  -s, --squeeze-repeats   replace sequence of characters with one
  -t, --truncate-set1     first truncate SET1 to length of SET2
      --help              display this help and exit
      --version           output version information and exit
"""
        items = wrapper.parse_help(tr_help_light)
        assert_equal(4, len(items))
        assert_equal("""name = tr
  g [a OPTION]
  a SET1
  g [a SET2]
""", str(items[0]))
        assert_equal(
            """Translate, squeeze, and/or delete characters """
            """from standard input,\nwriting to standard output.\n""",
            str(items[1]))
        assert_equal("\n", str(items[2]))
        print(items[3])
        assert_equal("""\
o -c, --complement | first complement SET1
o -d, --delete | delete characters in SET1, do not translate
o -s, --squeeze-repeats | replace sequence of characters with one
o -t, --truncate-set1 | first truncate SET1 to length of SET2
o --help | display this help and exit
o --version | output version information and exit
""", str(items[3]))

    def test_build_1(self):
        items = wrapper.parse_help(ParseHelp.cat_help)
        content = []
        mock = MockForm()
        for item in items:
            print("Call build on " + str(item))
            item.build(mock, content)
        print(content)
        expected = [
            'Textarea:FILE',
            'Text:Concatenate FILE(s), or standard input, '
            'to standard output.\n',
            'Break',
            'Checkbox:-A, --show-all False',
            'Checkbox:-b, --number-nonblank False',
            'Checkbox:-e False',
            'Checkbox:-E, --show-ends False',
            'Checkbox:-n, --number False',
            'Checkbox:-s, --squeeze-blank False',
            'Checkbox:-t False',
            'Checkbox:-T, --show-tabs False',
            'Checkbox:-u False',
            'Checkbox:-v, --show-nonprinting False',
            'Checkbox:--help False',
            'Checkbox:--version False',
            'Break',
            'Text:With no FILE, or when FILE is -, read standard input.\n',
            'Break',
            'Checkbox:-B, --binary False',
            'Break',
            'Break',
            'Text:Report bugs to <bug-textutils@gnu.org>.\n',
        ]
        assert_equal(expected, content)

    def test_build_2(self):
        tr_help = """
Usage: tr [OPTION]... SET1 [SET2]
Translate, squeeze, and/or delete characters from standard input,
writing to standard output.

  -c, --complement        first complement SET1
  -d, --delete            delete characters in SET1, do not translate
  -s, --squeeze-repeats   replace sequence of characters with one
  -t, --truncate-set1     first truncate SET1 to length of SET2
      --help              display this help and exit
      --version           output version information and exit

SETs are specified as strings of characters.  Most represent themselves.
Interpreted sequences are:

  \\NNN            character with octal value NNN (1 to 3 octal digits)
  \\\\              backslash
  \\a              audible BEL
  \\b              backspace
  \\f              form feed
  \\n              new line
  \\r              return
  \\t              horizontal tab
  \\v              vertical tab
  CHAR1-CHAR2     all characters from CHAR1 to CHAR2 in ascending order
  [CHAR1-CHAR2]   same as CHAR1-CHAR2, if both SET1 and SET2 use this
  [CHAR*]         in SET2, copies of CHAR until length of SET1
  [CHAR*REPEAT]   REPEAT copies of CHAR, REPEAT octal if starting with 0
  [:alnum:]       all letters and digits
  [:alpha:]       all letters
  [:blank:]       all horizontal whitespace
  [:cntrl:]       all control characters
  [:digit:]       all digits
  [:graph:]       all printable characters, not including space
  [:lower:]       all lower case letters
  [:print:]       all printable characters, including space
  [:punct:]       all punctuation characters
  [:space:]       all horizontal or vertical whitespace
  [:upper:]       all upper case letters
  [:xdigit:]      all hexadecimal digits
  [=CHAR=]        all characters which are equivalent to CHAR

Translation occurs if -d is not given and both SET1 and SET2 appear.
-t may be used only when translating.  SET2 is extended to length of
SET1 by repeating its last character as necessary.  Excess characters
of SET2 are ignored.  Only [:lower:] and [:upper:] are guaranteed to
expand in ascending order; used in SET2 while translating, they may
only be used in pairs to specify case conversion.  -s uses SET1 if not
translating nor deleting; else squeezing uses SET2 and occurs after
translation or deletion.

Report bugs to <bug-textutils@gnu.org>.
"""
        items = wrapper.parse_help(tr_help)
        content = []
        mock = MockForm()
        for item in items:
            print("Call build on " + str(item))
            item.build(mock, content)
            print(content[-1])
        print("content:")
        print(content)
        expected = [
            'Textbox:SET1',
            'Textbox:SET2',
            'Text:Translate, squeeze, and/or delete characters from '
            'standard input,\nwriting to standard output.\n',
            'Break',
            'Checkbox:-c, --complement False',
            'Checkbox:-d, --delete False',
            'Checkbox:-s, --squeeze-repeats False',
            'Checkbox:-t, --truncate-set1 False',
            'Checkbox:--help False',
            'Checkbox:--version False',
            'Break',
            'Text:SETs are specified as strings of characters.  '
            'Most represent themselves.\nInterpreted sequences are:\n',
            'Break',
            'Text:  \\NNN            '
            'character with octal value NNN (1 to 3 octal digits)\n'
            '  \\\\              backslash\n'
            '  \\a              audible BEL\n'
            '  \\b              backspace\n'
            '  \\f              form feed\n'
            '  \\n              new line\n'
            '  \\r              return\n'
            '  \\t              horizontal tab\n'
            '  \\v              vertical tab\n'
            '  CHAR1-CHAR2     all characters '
            'from CHAR1 to CHAR2 in ascending order\n'
            '  [CHAR1-CHAR2]   same as CHAR1-CHAR2, '
            'if both SET1 and SET2 use this\n'
            '  [CHAR*]         in SET2, copies of CHAR until length of SET1\n'
            '  [CHAR*REPEAT]   REPEAT copies of CHAR, REPEAT octal '
            'if starting with 0\n'
            '  [:alnum:]       all letters and digits\n'
            '  [:alpha:]       all letters\n'
            '  [:blank:]       all horizontal whitespace\n'
            '  [:cntrl:]       all control characters\n'
            '  [:digit:]       all digits\n'
            '  [:graph:]       all printable characters, '
            'not including space\n'
            '  [:lower:]       all lower case letters\n'
            '  [:print:]       all printable characters, including space\n'
            '  [:punct:]       all punctuation characters\n'
            '  [:space:]       all horizontal or vertical whitespace\n'
            '  [:upper:]       all upper case letters\n'
            '  [:xdigit:]      all hexadecimal digits\n'
            '  [=CHAR=]        all characters which are equivalent to CHAR\n',
            'Break',
            'Text:Translation occurs if -d is not given and both '
            'SET1 and SET2 appear.\n-t may be used only when translating.'
            '  SET2 is extended to length of\nSET1 by repeating its last '
            'character as necessary.  Excess characters\nof SET2 are ignored.'
            '  Only [:lower:] and [:upper:] are guaranteed to\nexpand in '
            'ascending order; used in SET2 while translating, they may\nonly '
            'be used in pairs to specify case conversion.  -s uses SET1 '
            'if not\ntranslating nor deleting; else squeezing uses SET2 '
            'and occurs after\ntranslation or deletion.\n',
            'Break',
            'Text:Report bugs to <bug-textutils@gnu.org>.\n'
        ]
        assert_equal(expected, content)


class GetHelp(unittest.TestCase):
    def test_1(self):
        wrapper.get_help('ls', [], '--help')


class DumpJson(unittest.TestCase):
    def test_1(self):
        git_checkout_help = """\
usage: git checkout [options] <branch>
   or: git checkout [options] [<branch>] -- <file>...

    -q, --quiet           suppress progress reporting
    -b <branch>           create and checkout a new branch
    -B <branch>           create/reset and checkout a branch
    -l                    create reflog for new branch
    --detach              detach the HEAD at named commit
    -t, --track           set upstream info for new branch
    --orphan <new branch>
                          new unparented branch
    -2, --ours            checkout our version for unmerged files
    -3, --theirs          checkout their version for unmerged files
    -f, --force           force checkout (throw away local modifications)
    -m, --merge           perform a 3-way merge with the new branch
    --overwrite-ignore    update ignored files (default)
    --conflict <style>    conflict style (merge or diff3)
    -p, --patch           select hunks interactively

"""
        dump = wrapper.dump_json(
            "git",
            ["checkout"],
            "/usr/bin/git",
            git_checkout_help,
            False)
        import json
        expected_pretty_json = """\
{
    "content": [
        {
            "control": "textbox",
            "name": "checkout"
        },
        {
            "content": "branch>\\n"""\
"""   or: git checkout [options] [<branch>] -- <file>...\\n",
            "control": "text"
        },
        {
            "control": "break"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-q, --quiet"
        },
        {
            "control": "textbox",
            "name": "-b"
        },
        {
            "control": "textbox",
            "name": "-B"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-l"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "--detach"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-t, --track"
        },
        {
            "control": "textbox",
            "name": "--orphan"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-2, --ours"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-3, --theirs"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-f, --force"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-m, --merge"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "--overwrite-ignore"
        },
        {
            "control": "textbox",
            "name": "--conflict"
        },
        {
            "checked": false,
            "control": "checkbox",
            "name": "-p, --patch"
        },
        {
            "control": "break"
        }
    ],
    "program": {
        "arguments": [
            "checkout"
        ],
        "name": "git",
        "path": "/usr/bin/git"
    }
}"""
        expected_json = json.loads(expected_pretty_json)
        generated_json = json.loads(dump)
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(expected_json)
        pp.pprint(generated_json)
        assert_equal(expected_json, generated_json)
        assert_equal(
            expected_pretty_json,
            wrapper.dump_json(
                "git",
                ["checkout"],
                "/usr/bin/git",
                git_checkout_help,
                False,
                True))

#ipdb debugging


#def main():
    #from ipdb import launch_ipdb_on_exception

    #with launch_ipdb_on_exception():
        #tester = DumpJson()
        #tester.test_1()

#if ("__main__" == __name__):
    #main()
