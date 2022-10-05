import requests
import os
import json
import logging

from time import localtime, strftime

logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

logging.info("starting deployment operator")

kube_proxy_url = 'http://127.0.0.1:8080'
namespace = os.getenv('NAMESPACE') or 'default'
logging.info("namespace is "+namespace)

def list_deployments(namespace):
        url = '{}/apis/apps/v1/namespaces/{}/deployments'.format(
                kube_proxy_url, namespace)
        deployments = requests.get(url)
        response = deployments.json()
        return response['items']

def uses_configmap(deployment, configmap):
        pod_spec = deployment['spec']['template']
        containers = pod_spec['spec']['containers']
        for container in containers:
                if 'env' in container:
                        for env_var in container['env']:
                                try:
                                        if env_var['valueFrom']['configMapKeyRef']['name'] == configmap:
                                                return True
                                except KeyError:
                                        continue
        return False

def rollout_restart(deployment, namespace):
        url = '{}/apis/apps/v1/namespaces/{}/deployments/{}?fieldManager=kubectl-rollout&pretty=true'.format(
                kube_proxy_url, namespace, deployment)
        patch_timestamp = str(strftime("%Y-%m-%dT%H:%M:%SZ", localtime()))
        data = '{{"spec": {{"template": {{"metadata": {{"annotations": {{"kubectl.kubernetes.io/restartedAt": "{0}"}}}}}}}}}}'.format(patch_timestamp)
        res = requests.patch(url,
                headers={'Content-Type': "application/strategic-merge-patch+json"},
                data=data)
        if res.status_code == 200:
                logging.info("restarted deployment "+deployment)
        else:
                logging.error("error restarting deployment "+deployment)
         
url = '{}/api/v1/namespaces/{}/configmaps?watch=true'.format(
        kube_proxy_url, namespace)
res = requests.get(url, stream=True)
for line in res.iter_lines():
        obj = json.loads(line)
        event = obj['type']
        configmap = obj['object']['metadata']['name']
        if event == "MODIFIED":
                logging.info("configmap "+configmap+" updated")
                url = '{}/apis/ashcorp.com/v1/namespaces/{}/appconfigs'.format(
                        kube_proxy_url, namespace)
                appconfigs = requests.get(url)
                response = appconfigs.json()
                for s in response['items']:
                        if configmap in s['spec']['configmaps']:
                                deployments = list_deployments(namespace)
                                for deployment in deployments:
                                        if uses_configmap(deployment, configmap):
                                                rollout_restart(deployment['metadata']['name'], namespace)
                    