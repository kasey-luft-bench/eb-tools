# eb-artifacts

Script to generate necessary artifacts for Elastic Beanstalk setup, including:

- Dockerrun.aws.json file
- .ebextensions files

Existing files in `.ebextensions` folder can be used as an example, but you don't need to include them by default.

## Usage

    > ./eb-artifacts.py -h
    usage: eb-artifacts.py [-h] --name NAME --version VERSION
                                    [--container-port CONTAINER_PORT]
                                    [--port-mappings [PORT_MAPPINGS [PORT_MAPPINGS ...]]]
                                    [--mount-points [MOUNT_POINTS [MOUNT_POINTS ...]]]
                                    [--log-path LOG_PATH] [--memory MEMORY]
                                    [--registry REGISTRY] [--templates TEMPLATES]
                                    [--extensions-filter EXTENSIONS_FILTER]
                                    [--output OUTPUT]

    Prepare Elastic Beanstalk artifacts, ready to be packaged and published.

    optional arguments:
      -h, --help            show this help message and exit
      --name NAME           name of service / docker image. "__SERVICE_NAME" in
                            the ebextensions will be replaced with this.
      --version VERSION     image version/tag to use
      --container-port CONTAINER_PORT
                            container http port to expose on port 80
      --port-mappings [PORT_MAPPINGS [PORT_MAPPINGS ...]]
                            additional port to expose
      --mount-points [MOUNT_POINTS [MOUNT_POINTS ...]]
                            list of mount points for volumes
      --log-path LOG_PATH   path for the service logs
      --memory MEMORY       Maximum amount of memory the container is allowed to
                            use. Must be lower than the EC2 instance memory.
      --registry REGISTRY   Docker registry to use.
      --templates TEMPLATES
                            Templates directory path. Needs to be absolute.
                            Default="templates"
      --extensions-filter EXTENSIONS_FILTER
                            Regex for extensions to package, if not defined,
                            everything is used. Default is *. E.g.: --extensions-
                            filter 0[1-3]* will pick the first 3 extensions only.
      --output OUTPUT       Output directory, default: "output".


## Examples

> $ ./eb-artifacts.py --name 'something' --version '189-04b80b4' --registry YOUR_REGISTRY_URL

> $ ./eb-artifacts.py --name 'something' --version '189-04b80b4' --extensions-filter '0[1-3]*' --registry YOUR_REGISTRY_URL

> $ ./eb-artifacts.py --name 'something' --version '189-04b80b4' --container-port 8080 --log-path /mnt-logs/logs --mount-points /mnt-bla/upload /mnt-logs/logs --registry YOUR_REGISTRY_URL
