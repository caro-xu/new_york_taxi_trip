import json

def get_config_with_name(name):
    config_file= f"config/keplergl_config/{name}.json"
    with open(config_file,"r") as f:
        config=json.loads(f.read())
    return  config