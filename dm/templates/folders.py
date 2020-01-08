def generate_config(ctx):
    props = ctx.properties
    root_node = ctx.env['name']
    parent_node = props['parent_node']
    owners = props['owners']
    root_parent_type = parent_node.get('type')
    root_parent_id = parent_node.get('id')
    root_parent = '{}s/{}'.format(root_parent_type, root_parent_id)

    resources = []

    folder_resource = {
        'name': root_node,
        'type': 'gcp-types/cloudresourcemanager-v2:folders',
        'properties': {
            'parent': root_parent,
            'displayName': root_node
        }
    }

    resources.append(folder_resource)

    root_node_id = '$(ref.{}.name)'.format(root_node)

    # Create Env Folders
    dev_folder = root_node + '-DEV'
    folder_dev_resource = {
        'name': dev_folder,
        'type': 'gcp-types/cloudresourcemanager-v2:folders',
        'metadata': {
            'dependsOn': [root_node]
        },
        'properties': {
            'parent': root_node_id,
            'displayName': dev_folder
        }
    }
    resources.append(folder_dev_resource)

    prd_folder = root_node + '-PRD'
    folder_prod_resource = {
        'name': prd_folder,
        'metadata': {
            'dependsOn': [root_node]
        },
        'type': 'gcp-types/cloudresourcemanager-v2:folders',
        'properties': {
            'parent': root_node_id,
            'displayName': prd_folder
        }
    }
    resources.append(folder_prod_resource)

    roles = [
        'roles/editor',
        'roles/resourcemanager.projectCreator',
        'roles/iam.securityAdmin',
        'roles/resourcemanager.folderAdmin',
        'roles/compute.xpnAdmin'
    ]

    for role in roles:
        for owner in owners:
            iam_binding = {
                'name': '{}-{}-{}'.format(root_node, owner, role),
                'type': 'gcp-types/cloudresourcemanager-v2:virtual.folders.iamMemberBinding',
                'metadata': {
                    'dependsOn': [root_node]
                },
                'properties': {
                    'resource': '$(ref.{}.name)'.format(root_node),
                    'role': role,
                    'member': owner
                }
            }
            resources.append(iam_binding)

    return {
        'resources': resources,
        'outputs': [
            {'name': 'dev', 'value': '$(ref.{}.name)'.format(dev_folder)},
            {'name': 'prd', 'value': '$(ref.{}.name)'.format(prd_folder)},
        ]
    }
