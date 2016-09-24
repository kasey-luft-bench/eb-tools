# eb-envconf

This is a proof of concept for templating EB environment creation and
configuration.

Uses the template in `config.yml`, and
then creates the named applications and environments, including
creating or updating a saved EB config and applying it to the environments.

## Usage

```bash
$ ./eb-envconf.py -h
usage: eb-envconf.py [-h] [-p PREFIXES] [-t TEMPLATE] [-i INSTANCE_TYPE]
                   [-k KEY_NAME] [-e ENV_VARS]
                   applications [applications ...]

Generates and applies EB environment configuration for an application.

positional arguments:
  applications          Application name(s) to update.

optional arguments:
  -h, --help            show this help message and exit
  -p PREFIXES, --prefixes PREFIXES
                        Environment prefix(es) to create/update. {default:
                        prod}
  -t TEMPLATE, --template TEMPLATE
                        EB environment template to use. {default: config.yml}
  -i INSTANCE_TYPE, --instance-type INSTANCE_TYPE
                        EC2 instance type to use in autoscaling group.
                        {default: m3.medium}
  -k KEY_NAME, --key-name KEY_NAME
                        SSH key name to install on instances.
  -e ENV_VARS, --env-var ENV_VARS
                        EB environment variable(s), format is 'name=value'.
```

Default values for environment settings can be overridden as follows:

```bash
$ ./eb-envconf test-app -e "CONSUL_SERVERS=some ips"
```

## Examples

TODO