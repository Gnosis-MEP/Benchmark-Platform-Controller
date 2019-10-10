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


# {'version': '2.3',
#  'services': {'media-server': {'image': 'tiangolo/nginx-rtmp'}}}