#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Kale Kundert
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os

def get_benchmark_root():
    libraries_dir = os.path.dirname(__file__)
    libraries_dir = os.path.realpath(libraries_dir)
    return os.path.dirname(libraries_dir)

def get_settings_path():
    return os.path.join(get_benchmark_root(), 'settings.conf')

def load(arguments={}, interactive=True):
    """
    Load the various settings needed by the benchmark either from the command 
    line or from 'settings.conf'.  The settings are loaded into module level 
    variables for convenient access.  If the 'arguments' variable is provided, 
    it should be a dictionary containing command line arguments in the format 
    generated by docopt.  Settings will be taken from certain recognized flags.
    If the 'interactive' argument is True, the user will be asked for missing 
    settings.  This is the default behavior, but should be turned off for jobs 
    running on the cluster.
    """
    import getpass
    import ConfigParser as configparser
    import subprocess
    from . import utilities

    # Parse the settings file.

    parser = configparser.SafeConfigParser()
    parser.read(get_settings_path())

    # Read all the settings from the config file.

    def get_setting(parser, setting, prompt, default=None, flag=None):
        custom_section = arguments.get('--config')
        default_section = 'DEFAULT'

        # Make sure that any manually-specified sections exist.

        if custom_section and not parser.has_section(custom_section):
            print "No section [{0}] in 'settings.conf'.".format(custom_section)
            raise SystemExit

        # If the setting was given on the command-line, use it.

        if flag and arguments.get(flag):
            return arguments.get(flag)

        # If the setting is overridden in the given section, use it.

        elif custom_section and parser.has_option(custom_section, setting):
            return parser.get(custom_section, setting)

        # If the setting has a default value, use it.

        elif parser.has_option(default_section, setting):
            return parser.get(default_section, setting)

        # If the setting doesn't have a default value, prompt for one.

        elif interactive:
            if get_setting.first_prompt:
                get_setting.first_prompt = False
                print '''\
Settings related to running and analyzing the loop modeling benchmark are kept 
in 'settings.conf'.  Default values for the following settings are needed:
'''
            if default:
                prompt += ' [{0}]'.format(default)

            try:
                value = raw_input(prompt + ': ') or default
            except KeyboardInterrupt:
                print
                raise SystemExit

            parser.set(default_section, setting, value)

            with open(get_settings_path(), 'w') as file:
                parser.write(file)

            return value

        # If the user can't be prompted (i.e. cluster job), complain and die.

        else:
            raise SystemExit("No value for setting '{0}'.".format(setting))


    get_setting.first_prompt = True

    global rosetta
    rosetta = get_setting(
            parser, 'rosetta',
            prompt="Path to rosetta",
            flag='--rosetta',
    )
    global author
    author = get_setting(
            parser, 'author',
            prompt="Your full name",
            flag='--author',
    )
    global db_name
    db_name = get_setting(
            parser, 'db_name',
            prompt="Database name",
            default='{0}_loops_benchmark'.format(getpass.getuser()),
            flag='--db-name', 
    )
    global db_user
    db_user = get_setting(
            parser, 'db_user',
            prompt="Database user",
            default=getpass.getuser(),
            flag='--db-user',
    )
    db_password_cmd = get_setting(
            parser, 'db_password',
            prompt="Command to get database password",
            default='echo pa55w0rd',
            flag='--db-passwd-cmd',
    )
    global db_host
    db_host = get_setting(
            parser, 'db_host',
            prompt="Database host",
            default='guybrush-pi.compbio.ucsf.edu',
            flag='--db-host',
    )
    global db_port
    db_port = get_setting(
            parser, 'db_port',
            prompt="Database port",
            default='3306',
            flag='--db-port',
    )

    # Invoke the password command to get the database password.

    global db_password
    db_password = subprocess.check_output(db_password_cmd, shell=True).strip()

def show():
    print 'rosetta:  ', rosetta
    print 'author:   ', author
    print 'db_name:  ', db_name
    print 'db_user:  ', db_user
    print 'db_passwd:', db_password
    print 'db_host:  ', db_host
    print 'db_port:  ', db_port


# These values are filled in by the load() function.

rosetta = ''
author = ''
db_name = ''
db_user = ''
db_password = ''
db_host = ''
db_port = ''

# These values can be passed to docopt to parse settings-related arguments.

config_args = """\
    --config CONFIG -c CONFIG
        Specify an alternative set of settings to use.  The given config name 
        must correspond to a [section] in 'settings.conf'.
""".strip()

rosetta_args = """\
    --rosetta PATH
        Override the default rosetta path setting.
""".strip()

database_args = """\
    --db-name NAME
        Override the default database name setting.

    --db-user USER
        Override the default database user setting.

    --db-passwd-cmd CMD
        Override the default database password command setting.  Note that this 
        should be a command that returns a password, not a password itself.

    --db-host HOST
        Override the default database host setting.

    --db-port PORT
        Override the default database port setting.
""".strip()

