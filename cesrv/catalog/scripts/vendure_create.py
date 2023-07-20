#!/usr/bin/env python3

import sys
#sys.path.append('..')
import json
import pprint
import requests
from dotenv import dotenv_values
from google.cloud import run_v2

# Create database

# Create cloud servers

def create_cloud_service(spec):
    #credentials = service_account.Credentials.from_service_account_file(auth_json)
    #scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
    #print(credentials)
    #print(scoped_credentials)
    auth_json = spec['service_account_file']
    project = spec['project']
    location = spec['location']
    service_id = spec['service_id']
    parent = 'projects/{}/locations/{}'.format(project, location)
    client = run_v2.ServicesClient.from_service_account_file(auth_json)
    env_list = []
    config = dotenv_values(spec['env_file'])
    for k in sorted(config.keys()):
        env_list.append(run_v2.types.EnvVar(
            name = k,
            value = config[k],
        ))
    request = run_v2.CreateServiceRequest(
        parent = parent,
        service = run_v2.types.Service(
            template = run_v2.types.RevisionTemplate(
                containers = [
                    run_v2.types.Container(
                        image = spec['image'],
                        command = spec['command'],
                        args = spec['args'],
                        env = env_list,
                        resources = run_v2.types.ResourceRequirements(
                            limits = {
                                'cpu': '1',
                                'memory': spec['memory'],
                            },
                        ),
                        ports = [
                            run_v2.types.ContainerPort(name = 'http1', container_port = 443)
                        ],
                    ),
                ],
            ),
        ),
        service_id = service_id,
    )
    operation = client.create_service(request=request)
    response = operation.result()
    print(response)

create_cloud_service({
    'service_account_file': 'keys/service-key.json',
    'project': 'atellix-network',
    'location': 'us-west1',
    'service_id': 'shop1',
    'env_file': 'keys/cloud.env',
    'image': 'us-west1-docker.pkg.dev/atellix-network/vendure/v2',
    'command': ['/usr/local/bin/yarn'],
    'args': ['start:server'],
    'memory': '512Mi',
})
