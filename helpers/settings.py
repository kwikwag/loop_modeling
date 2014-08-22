settings_path = 'settings.conf'

def install():
    import os.path
    if not os.path.exists(settings_path):
        print '''\
Settings related to compiling rosetta and connecting to the database are kept
in 'settings.conf'.  Please answer the following questions to create this file:
'''
        load()

def load(interactive=True):
    import getpass
    import ConfigParser as configparser
    import subprocess
    from . import utilities

    parser = configparser.SafeConfigParser()
    parser.read(settings_path)

    # Read all the settings from the config file.

    global rosetta, db_name, db_user, db_password, db_host, db_port

    def get_setting(parser, section, setting, prompt, default=None):
        try:
            return parser.get(section, setting)
        except configparser.Error:
            if not interactive: raise
            if default: prompt += ' [{0}]'.format(default)
            value = raw_input(prompt + ': ') or default
            if not parser.has_section(section): parser.add_section(section)
            parser.set(section, setting, value)
            return value


    rosetta = get_setting(parser, 'rosetta', 'path', prompt="Path to rosetta")
    db_name = get_setting(parser, 'database', 'name', prompt="Database name", default='loops_modeling_benchmark')
    db_user = get_setting(parser, 'database', 'user', prompt="Database user", default=getpass.getuser())
    db_password_cmd = get_setting(parser, 'database', 'password', prompt="Command to get database password", default='echo pa55w0rd')
    db_host = get_setting(parser, 'database', 'host', prompt="Database host", default='guybrush-pi.compbio.ucsf.edu')
    db_port = get_setting(parser, 'database', 'port', prompt="Database port", default='3306')

    # Write any user-specified values to the config file.

    with open(settings_path, 'w') as file:
        parser.write(file)

    # Invoke the password command to get the database password.

    db_password = subprocess.check_output(db_password_cmd, shell=True).strip()


# These values are filled in by the install() and load() functions.

rosetta = ''
db_name = ''
db_user = ''
db_password = ''
db_host = ''
db_port = ''