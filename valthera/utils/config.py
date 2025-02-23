import configparser
from pydantic import BaseSettings

class Config(BaseSettings):
    # Define your configuration fields here
    # Example:
    # database_url: str
    # api_key: str
    pass

def load_config(file_path: str) -> Config:
    config_parser = configparser.ConfigParser()
    config_parser.read(file_path)
    
    config_dict = {section: dict(config_parser.items(section)) for section in config_parser.sections()}
    
    return Config(**config_dict)
