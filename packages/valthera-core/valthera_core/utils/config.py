import configparser


def load_config(config_file):
    """Function to load configuration from a file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

# Example usage:
# config = load_config('example.ini')
# db_host = config['database']['host']
# db_port = config['database']['port']
