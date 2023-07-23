#!/usr/bin/env python3

import sys
#sys.path.append('..')
import json
import pprint
import asyncio
import requests
from dotenv import dotenv_values
from google.cloud import run_v2
from google.iam.v1 import iam_policy_pb2, policy_pb2

# Create database

# Create cloud servers

def cloud_run_client(spec):
    auth_json = spec['service_account_file']
    client = run_v2.ServicesAsyncClient.from_service_account_file(auth_json)
    return client

async def cloud_run_deploy_service(client, spec):
    project = spec['project']
    location = spec['location']
    service_id = spec['service_id']
    parent = 'projects/{}/locations/{}'.format(project, location)
    rsrc = f'{parent}/services/{service_id}'
    print(f'Run {rsrc}')
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
    response = await (await operation).result()
    print(response)

async def cloud_run_set_iam_policy(client, spec):
    # Add IAM Policy
    project = spec['project']
    location = spec['location']
    service_id = spec['service_id']
    parent = 'projects/{}/locations/{}'.format(project, location)
    rsrc = f'{parent}/services/{service_id}'
    print(f'Set IAM Policy {rsrc}')
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource = rsrc,
        policy = {
            'bindings': [{
                'role': 'roles/run.invoker',
                'members': {'allUsers'},
            }],
        },
    )
    response = await client.set_iam_policy(request=request)
    print(response)

async def create_cloud_service(spec):
    client = cloud_run_client(spec)
    await cloud_run_deploy_service(client, spec)
    await cloud_run_set_iam_policy(client, spec)

async def main():
    base = {
        'service_account_file': 'keys/service-key.json',
        'project': 'atellix-network',
        'location': 'us-west1',
        'env_file': 'keys/cloud.env',
        'image': 'us-west1-docker.pkg.dev/atellix-network/vendure/v2',
        'command': ['/usr/local/bin/yarn'],
        'args': ['start:server'],
        'memory': '512Mi',
    }
    shop_id = '1'
    server = base.copy()
    server['service_id'] = 'shop' + shop_id
    worker = base.copy()
    worker['service_id'] = 'worker' + shop_id
    tasks = [
        asyncio.create_task(create_cloud_service(server)),
        asyncio.create_task(create_cloud_service(worker)),
    ]
    await asyncio.wait(tasks)
    print('Done')
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())

