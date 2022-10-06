# Simple Kubernetes Operator Example

## Overview

* This repository is a practical example of how Kubernetes [Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) function
* The custom controller (implemented as a simple Python application) performs a fully automated rolling restart of [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) when [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/) used by the Pods are edited
* The ConfigMaps to be continuously monitored/watched for edit/modification events are determined with the help of [CustomResourceDefinitions (CRDs)](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)

## Setup

* The first step involves creating a CRD called 'AppConfig' which stores a list of ConfigMaps and [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
* A [Role](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole) with permissions to access and edit the CRD along with ConfigMaps, Secrets, and Deployments is also created (since the Operator Pod will require permissions to fetch the object data and restart workloads that meet the criteria discussed above)

-  [crd.yml](manifests/crds/crd.yml) (Contains the CustomResourceDefinition and the Role with RBAC permissions on the Custom Resource and associated objects)
-  [appconfig-monitor.yml](manifests/crds/appconfig-monitor.yml) (Contains the YAML definition for an example 'AppConfig' resource)

    ```bash
    $ kubectl apply -f manifests/crds/crd.yml
    ```
    ```bash
    $ kubectl apply -f manifests/crds/appconfig-monitor.yml
    ```

* A [Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/) must be created and bound to the Role created with the CRD in order to permit the Operator to track changes and execute the required actions (application restarts)
* Create the account by referring to [crd_sa.yml](manifests/accounts/crd_sa.yml)

    ```bash
    kubectl apply -f manifests/accounts/crd_sa.yml
    ```

* Next, bind the account to the Role

    ```bash
    $ kubectl apply -f manifests/rbac/appconfig-rolebinding.yml
    ```

* Deploy the Operator

    ```bash
    $ kubectl apply -f manifests/deployments/operator-deployment.yml
    ```

* NOTE: The container image for the operator was built using:

    ```bash
    $ docker build --platform=linux/amd64 -t ashbourne1990/k8s-deployment-envconfig-operator:latest .
    ```

* Validate that the Operator was deployed successfully

    ```bash
    $ kubectl get pods

    NAME                                  READY   STATUS    RESTARTS   AGE
    appconfig-operator-659f5868ff-tlf4f   2/2     Running   0          31s
    ```

* Check the Operator Pod logs for the following messages

    ```bash
    $ kubectl logs appconfig-operator-659f5868ff-tlf4f  -c custom-controller

    INFO:2022-10-06 22:33:19,356 starting deployment operator
    INFO:2022-10-06 22:33:19,356 namespace is default
    DEBUG:2022-10-06 22:33:19,358 Starting new HTTP connection (1): 127.0.0.1:8080
    DEBUG:2022-10-06 22:33:19,394 http://127.0.0.1:8080 "GET /api/v1/namespaces/default/configmaps?watch=true HTTP/1.1" 200 None
    ```

* Create a new ConfigMap

    ```bash
    $ kubectl create cm node-app-config --from-literal=n_items=5000 --from-literal=f_prob=0.03
    ```

* Deploy the sample application which consumes the above ConfigMap

    ```bash
    $ kubectl apply -f manifests/sample-apps/sample-node-app.yml
    ```

* Confirm that the sample application is running

    ```bash
    $ kubectl get pods -l app=node-api

    NAME                               READY   STATUS    RESTARTS   AGE
    sample-node-api-67699d5dc4-v8m98   1/1     Running   0          71s
    ```

* Edit the ConfigMap used by the application by adding a new key-value pair

    ```bash
    $ kubectl edit cm node-app-config  
    ```

* Checks the Operator Pod logs for the deployment restart message

    ```bash
    $ kubectl logs appconfig-operator-659f5868ff-tlf4f  -c custom-controller

    INFO:2022-10-06 22:51:26,971 configmap node-app-config updated
    DEBUG:2022-10-06 22:51:26,972 Starting new HTTP connection (1): 127.0.0.1:8080
    DEBUG:2022-10-06 22:51:27,010 http://127.0.0.1:8080 "GET /apis/ashcorp.com/v1/namespaces/default/appconfigs HTTP/1.1" 200 1144
    DEBUG:2022-10-06 22:51:27,011 Starting new HTTP connection (1): 127.0.0.1:8080
    DEBUG:2022-10-06 22:51:27,018 http://127.0.0.1:8080 "GET /apis/apps/v1/namespaces/default/deployments HTTP/1.1" 200 None
    DEBUG:2022-10-06 22:51:27,020 Starting new HTTP connection (1): 127.0.0.1:8080
    DEBUG:2022-10-06 22:51:27,036 http://127.0.0.1:8080 "PATCH /apis/apps/v1/namespaces/default/deployments/sample-node-api?fieldManager=kubectl-rollout&pretty=true HTTP/1.1" 200 None
    INFO:2022-10-06 22:51:27,037 restarted deployment sample-node-api
    ```

* List the Pods to confirm the rolling restart

    ```bash
    $ kubectl get pods -l app=node-api

    NAME                               READY   STATUS        RESTARTS   AGE
    sample-node-api-5d66694fd7-ndxlk   1/1     Running       0          2s
    sample-node-api-69668fdf89-dc59z   1/1     Terminating   0          37s

    NAME                               READY   STATUS    RESTARTS   AGE
    sample-node-api-5d66694fd7-ndxlk   1/1     Running   0          89s
    ```

* NOTE: A separate controller can be created to monitor changes made to Secrets used by the applications in the [Namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)