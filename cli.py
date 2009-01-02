import optparse
import sys

from ConfigParser import ConfigParser
from inspect import getargs
from optparse import Option, OptionParser

class Error(Exception):
    pass

class MainError(Error):
    pass

class Values(optparse.Values):
    delim = '.'

    def set(self, name, value):
        """Set option 'name' to 'value'.

        Options with delimiter characters in their names represent
        options several levels down in the Values tree. Create as
        many Values instances as necessary before setting the leaf
        instance to 'value'.
        """
        subnames = name.split(self.delim)
        name = subnames.pop()
        parent = self

        # Build the Values tree.
        for n in subnames:
            if not hasattr(parent, n):
                setattr(parent, n, self.__class__())
            parent = getattr(parent, n)

        parent._update_loose({name: value})

    def update_from_config(self, config_file):
        """Parse a configuration file and update the Values tree.

        The config file is read using ConfigParser.ConfigParser.
        All options are flattened into a single-level structure such
        that the following two options are equivalent:

            [one.two]
            three = four

            [one]
            two.three = four

        In each case, the value 'one.two.three' will equal 'four'.
        In cases where the same option name has multiple values, the
        last entry with that name will be used.
        """
        # XXX: seed the parser with defaults here?
        parser = ConfigParser()
        parser.read(config_file)

        for section in parser.sections():
            for option in parser.options(section):
                name = self.delim.join((section, option))
                value = parser.get(section, option)
                # XXX: hook in vars here?
                self.set(name, value)

    def update_from_env(self, env):
        """Parse 'env' and update the Values tree.

        'env' should be a dictionary similar to that provided by
        os.environ. Keys will be converted from 'FOO_BAR' notation
        to 'foo.bar'; values will be untouched.
        """
        for key, value in env.items():
            key = self.delim.join(key.lower().split('_'))
            self.set(key, value)

    def update_from_cli(self, options, argv):
        # XXX: hook usage into here.
        parser = OptionParser(option_list=options)

        opts, args = parser.parse_args(argv)

        return opts, args

class App(object):
    """A command-line application.

    Command-line applications (CLI apps) perform a task based in
    part on options and arguments passed on the command line. The
    App object makes it easy to develop simple CLI apps.

    Instantiated CLI apps parse options, arguments and (optionally)
    other configuration information and pass them to a single
    callable. This callable must support the App interface, which
    means its signature should be something like the following:

        def main(opts, args, app):

    Whether or not the callable actually _uses_ any of this
    information is optional, though it must accept them.
    """
    values_factory = Values
    optparser_factory = OptionParser
    opt_types = {
        type(''): 'string',
        type(1): 'int',
        type(1.0): 'float',
        type(complex(1)): 'complex'}

    def __init__(self, name, main=None, config_file=None, argv=None,
            env=None, exit_after_main=True):
        self.name = name
        self.main = self.find_main(main)
        self.config_file = config_file
        self.argv = argv
        self.env = env
        self.exit_after_main = exit_after_main

        self.options = []

    def add_option(self, name, default, help, action="store"):
        """Build an optparse.Option object and add it to the option list."""
        opt = Option(
            short ='-%s' % name[0],
            long = '--%s' % name.replace('_', '-'),
            dest = name,
            action = action,
            type = self.opt_types.get(type(default), 'string'),
            default = default,
            help = help)
        self.options.append(opt)

    @property
    def opts(self):
        """Parse all application options.

        In addition to the standard CLI options and arguments, this
        also includes environment variables and configuration file
        directives which are resolved to options and arguments.
        Options specified in more than one of the above sources are
        resolved in the following order, with the rightmost source
        winning:

            configuration -> environment -> CLI

        Returns a tuple (opts, args).
        """
        opts = self.values_factory()

        if self.config_file is not None:
            opts.update_from_config(self.config_file)
        if self.env is not None:
            # Filter env for variables starting with our name. A
            # mapping like {'OURAPP_FOO_BAR': 'foo'} will become
            # {'FOO_BAR': 'foo'}.
            env = dict([('_'.join(k.split('_')[1:]), v) \
                    for k, v in self.env.items() \
                    if k.lower().startswith(self.name.lower() + '_')])
            opts.update_from_env(env)

        opts.update_from_cli(self.options, self.argv)

        return opts

    @property
    def usage(self):
        return self.main.__doc__ or ''

    def find_main(self, main=None):
        """Find a suitable main() callable.

        If the supplied 'main' argument is not a callable, search
        globals() for a suitable callable. If no callable is found
        or the chosen callable doesn't support the App interface
        (see cli.App.__doc__ for more information), raise MainError.
        """
        if not callable(main):
            main = globals().get('main', None)

        if not callable(main):
            raise MainError("Could not find main()")

        args, varargs, varkw = getargs(main.func_code)

        if len(args) != 3 or (varargs or varkw):
            raise MainError("main() must take three arguments or varargs/varkw")

        return main

    def run(self):
        """Run the application's callable.

        If the callable hasn't already been determined, discover it
        and pass it the resolved options, arguments and Application
        object. If the App.exit_after_main is True, call sys.exit()
        with the return value of the application's callable.
        Otherwise, return the result.
        """
        returned = self.main(self.opts, self.args, self)

        if self.exit_after_main:
            sys.exit(returned)
        else:
            return returned

def main(opts, args, app=None):
    print 'cli.App test!'

if __name__ == '__main__':
    fake_env = {
            'OURAPP_DEFAULT_FOO': 'notbar',
            'OURAPP_FROBNITZ_SPAM': 'noteggs'}
    app = App('ourapp', config_file='sample.config', env=fake_env)

    print app.opts.default.foo
    print app.opts.frobnitz.foo.bar
    print app.opts.frobnitz.spam

    #app.run()
