import os
import yaml
# document = """
# version: '2.3'
# services:
#   media-server:
#     image: tiangolo/nginx-rtmp
# """
# data = yaml.load(document)
# print(yaml.dump(data, default_flow_style=False))


def generate_yaml_content(override_services):
    final_content = {
        'version': '2.3',
        'services': {}
    }
    final_content['services'].update(override_services)
    return yaml.dump(final_content, default_flow_style=False)


def create_override_yaml_file(path, file_name, override_services):
    file_content = generate_yaml_content(override_services)
    file_path = os.path.join(path, file_name)
    with open(file_path, 'w') as f:
        f.write(file_content)
    return file_path

# {'version': '2.3',
#  'services': {'media-server': {'image': 'tiangolo/nginx-rtmp'}}}