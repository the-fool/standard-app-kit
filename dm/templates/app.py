# Common naming definitions
def get_billing_account_name(project_id):
    return "{}-billing".format(project_id)


def get_service_name(project_id, service):
    return "{}-{}".format(project_id, service)


def get_shared_vpc_name(project_id):
    return "{}-shared-vpc-host".format(project_id)


def generate_config(ctx):
    app_id = ctx.env["name"]

    props = ctx.properties
    dev_node = props["dev_node"]
    prd_node = props["prd_node"]
    billing_account_id = props["billing_account_id"]
    enabled_services = props["enabled_services"]
    use_network_project = props["use_network_project"]

    envs = [{"name": "dev", "id": dev_node}, {"name": "prd", "id": prd_node}]

    project_configs = make_project_configs(
        app_id, envs, enabled_services, use_network_project
    )

    resources = []

    # Add projects & associated billing accounts
    projects_and_billing = make_projects_and_billing_accounts(
        project_configs, billing_account_id
    )
    resources.extend(projects_and_billing)

    # Enable services (APIs) for projects
    for project_config in project_configs:
        project_id = project_config["id"]
        services = project_config["services"]
        enabled_services_resources = make_enabled_services(project_id, services)
        resources.extend(enabled_services_resources)

    return {"resources": resources}


def make_shared_vpc_service(service_project_id, host_project_id):
    compute_service = get_service_name(service_project_id, "compute.googleapis.com")
    host_project_resource_name = get_shared_vpc_name(host_project_id)

    return {
        "name": "{}-attach-vpc-service-{}".format(host_project_id, service_project_id),
        "type": "compute.beta.xpnResource",
        "metadata": {
            "dependsOn": [
                compute_service,
                host_project_resource_name,
                service_project_id,
            ]
        },
        "properties": {
            "project": host_project_id,
            "xpnResource": {"id": service_project_id, "type": "PROJECT"},
        },
    }


def make_shared_vpc_host(project_id):
    compute_service = get_service_name(project_id, "compute.googleapis.com")
    return {
        "name": get_shared_vpc_name(project_id),
        "type": "compute.beta.xpnHost",
        "metadata": {"dependsOn": [compute_service]},
        "properties": {"project": project_id},
    }


def make_project_configs(app_id, envs, services, use_network_project):
    project_configs = []

    base_services = [
        "stackdriver.googleapis.com",
        "logging.googleapis.com",
        "monitoring.googleapis.com",
        "cloudprofiler.googleapis.com",
    ]

    main_services = ["compute.googleapis.com"]

    network_services = ["compute.googleapis.com"]

    monitoring_services = []

    def merge_base(l1):
        return base_services + list(set(l1) - set(base_services))

    for env in envs:
        env_name = env["name"]
        env_node_id = env["id"]

        if use_network_project:
            configs = [
                {
                    "id": "{}-{}".format(app_id, env_name),
                    "parent_id": env_node_id,
                    "services": merge_base(main_services),
                    "shared_vpc_service": {
                        "host_project_id": "{}-net-{}".format(app_id, env_name)
                    },
                },
                {
                    "id": "{}-net-{}".format(app_id, env_name),
                    "parent_id": env_node_id,
                    "services": merge_base(network_services),
                    "shared_vpc_host": True,
                },
                {
                    "id": "{}-mon-{}".format(app_id, env_name),
                    "parent_id": env_node_id,
                    "services": merge_base(monitoring_services),
                },
            ]
        else:
            configs = [
                {
                    "id": "{}-{}".format(app_id, env_name),
                    "parent_id": env_node_id,
                    "services": merge_base(services),
                },
                {
                    "id": "{}-mon-{}".format(app_id, env_name),
                    "parent_id": env_node_id,
                    "services": merge_base(monitoring_services),
                },
            ]
        project_configs.extend(configs)

    return project_configs


def make_project(project_config):
    parent_id = project_config["parent_id"]
    project_id = project_config["id"]

    return {
        "name": project_id,
        "type": "cloudresourcemanager.v1.project",
        "properties": {
            "name": project_id,
            "projectId": project_id,
            "parent": {"type": "folder", "id": str(parent_id)},
        },
    }


def make_billing_account(project_id, billing_account_id):
    return {
        "name": get_billing_account_name(project_id),
        "type": "deploymentmanager.v2.virtual.projectBillingInfo",
        "metadata": {"dependsOn": [project_id]},
        "properties": {
            "name": "projects/{}".format(project_id),
            "billingAccountName": "billingAccounts/{}".format(billing_account_id),
        },
    }


def make_projects_and_billing_accounts(project_configs, billing_account_id):
    def make_vpc(project_id, vpc_name=None):
        resource_name = "{}-vpc".format(project_id)
        compute_service = get_service_name(project_id, "compute.googleapis.com")
        if vpc_name is None:
            vpc_name = resource_name
        return {
            "name": "{}-vpc".format(project_id),
            "type": "gcp-types/compute-v1:networks",
            "metadata": {"dependsOn": [project_id, compute_service]},
            "properties": {
                "name": vpc_name,
                "project": project_id,
                "autoCreateSubnetworks": False,
            },
        }

    resources = []
    for project_config in project_configs:
        project_id = project_config["id"]
        resources.extend(
            [
                make_project(project_config),
                make_billing_account(project_id, billing_account_id),
            ]
        )

        if project_config.get("shared_vpc_host", False):
            shared_vpc_host_resource = make_shared_vpc_host(project_id)
            resources.append(shared_vpc_host_resource)
            vpc_resource = make_vpc(project_id)
            resources.append(vpc_resource)

        elif project_config.get("shared_vpc_service"):
            host_project_id = project_config["shared_vpc_service"]["host_project_id"]
            vpc_service_resource = make_shared_vpc_service(project_id, host_project_id)
            resources.append(vpc_service_resource)

    return resources


def make_billing_accounts(project_ids, billing_account_id):
    def make_billing_account(project_id):
        return {
            "name": get_billing_account_name(project_id),
            "type": "deploymentmanager.v2.virtual.projectBillingInfo",
            "metadata": {"dependsOn": [project_id]},
            "properties": {
                "name": "projects/{}".format(project_id),
                "billingAccountName": "billingAccounts/{}".format(billing_account_id),
            },
        }

    return [make_billing_account(project_id) for project_id in project_ids]


def make_enabled_services(project_id, services):
    dependsOn = [project_id, get_billing_account_name(project_id)]
    resources = []
    for service in services:
        name = get_service_name(project_id, service)
        consumerId = "project:{}".format(project_id)
        resource = {
            "name": name,
            "type": "deploymentmanager.v2.virtual.enableService",
            "metadata": {"dependsOn": dependsOn[:]},
            "properties": {"consumerId": consumerId, "serviceName": service},
        }
        dependsOn.append(name)
        resources.append(resource)

    return resources
