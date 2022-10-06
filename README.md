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



