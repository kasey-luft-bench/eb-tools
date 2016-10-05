#!/usr/bin/env python3

"""Generates and applies Elastic Beanstalk environment configuration for an application"""

import argparse
import boto3
from botocore.exceptions import ClientError
import yaml

__author__ = "Tessa Nordgren"


def parse_args():
    parser = argparse.ArgumentParser(description="Generates and applies EB environment configuration for an application.")
    parser.add_argument('applications', type=str, help="Application name(s) to update.",
                        nargs='+')
    parser.add_argument('-p', '--prefixes', action='append', default=[],
                        help="Environment prefix(es) to create/update. {default: prod}")
    parser.add_argument('-t', '--template', type=str, default="config.yml",
                        help="EB environment template to use. {default: config.yml}")
    parser.add_argument('-i', '--instance-type', type=str, default='m3.medium', dest='instance_type',
                        help='EC2 instance type to use in autoscaling group. {default: m3.medium}')
    parser.add_argument('-k', '--key-name', type=str, dest='key_name',
                        help='SSH key name to install on instances.')

    env_vars = [
        ('EXAMPLE_VAR', 'example_value')
    ]
    parser.add_argument('-e', '--env-var', type=lambda kv: kv.split('='),
                        action='append', default=env_vars, dest='env_vars',
                        help="EB environment variable(s), format is 'name=value'."
                        )

    args = parser.parse_args()
    if not args.prefixes:
        args.prefixes = ["prod"]
    args.env_vars = dict(args.env_vars)
    return args


# create_app creates named EB applications.
def create_apps(client, applications):
    # first check if already exists
    app_details = client.describe_applications(ApplicationNames=applications)['Applications']
    app_names = [app['ApplicationName'] for app in app_details]
    for application in applications:
        if application not in app_names:
            print(application, "doesn't exist, creating...")
            client.create_application(ApplicationName=application)


def latest_stack(client):
    stacks = client.list_available_solution_stacks()['SolutionStacks']
    multidocker = [x for x in stacks if x.find('Multi-container Docker') >= 0]
    return multidocker[0]


def create_sg(ec2, application):
    try:
        ec2.describe_security_groups(GroupNames=[application])
    except ClientError as e:
        if e.response['Error']['Code'] != 'InvalidGroup.NotFound':
            raise e
        print("security group %s missing, so creating..." % application)
        ec2.create_security_group(GroupName=application, Description='new SG for ' + application)


def update_create_template(client, application, prefix, config):
    template_name = prefix + "-" + application
    stackname = latest_stack(client)
    try:
        print("Updating config template", template_name)
        client.update_configuration_template(ApplicationName=application, TemplateName=template_name,
                                             OptionSettings=config['OptionSettings'])
    except ClientError as e:
        if e.response['Error']['Code'] != 'InvalidParameterValue':
            raise e
        print("Template missing, so creating new template: ", template_name)
        client.create_configuration_template(ApplicationName=application, TemplateName=template_name,
                                             SolutionStackName=stackname,
                                             OptionSettings=config['OptionSettings'])
    return template_name


def apply_config(client, application, prefix, config):
    template_name = update_create_template(client, application, prefix, config)
    environment = prefix + "-" + application
    try:
        # update the environment
        print("Updating environment", environment)
        client.update_environment(ApplicationName=application, EnvironmentName=environment, TemplateName=template_name)
    except ClientError as e:
        if e.response['Error']['Code'] != 'InvalidParameterValue':
            raise e
        # creates app environment if missing
        print("Environment missing, so creating", environment)
        client.create_environment(ApplicationName=application, EnvironmentName=environment, TemplateName=template_name,
                                  CNAMEPrefix=config['CName'])


def get_config(application, prefix, version, args):
    with open(args.template, 'r') as stream:
        config = yaml.load(stream)

    env_name = prefix + "-" + application
    config['EnvironmentName'] = env_name
    config['CName'] = env_name
    if version:
        config['VersionLabel'] = version
    config_file = prefix + '.conf'
    if prefix == 'prod':
        config_file = 'production.conf'
    config['OptionSettings'].extend([
        {'Namespace': 'aws:autoscaling:launchconfiguration',
         'OptionName': 'SecurityGroups',
         'Value': application + ',common-ssh-offices'},
        {'Namespace': 'aws:elasticbeanstalk:application:environment',
         'OptionName': 'STACK_PREFIX', 'Value': prefix},
        {'Namespace': 'aws:elasticbeanstalk:application:environment',
         'OptionName': 'CONFIG_FILE', 'Value': config_file},
        {'Namespace': 'aws:autoscaling:launchconfiguration',
         'OptionName': 'InstanceType', 'Value': args.instance_type},
        {'Namespace': 'aws:autoscaling:launchconfiguration',
         'OptionName': 'EC2KeyName', 'Value': args.key_name}
    ])
    for name, value in args.env_vars.items():
        config['OptionSettings'].append({
            'Namespace': 'aws:elasticbeanstalk:application:environment',
            'OptionName': name, 'Value': value})

    return config


def get_version(client, application):
    versions = client.describe_application_versions(ApplicationName=application)['ApplicationVersions']
    if not versions:
        return None
    else:
        return versions[0]['VersionLabel']


def main():
    args = parse_args()

    client = boto3.client('elasticbeanstalk')
    create_apps(client, args.applications)
    ec2 = boto3.client('ec2')

    for application in args.applications:
        create_sg(ec2, application)
        for prefix in args.prefixes:
            version = get_version(client, application)
            config = get_config(application, prefix, version, args)
            apply_config(client, application, prefix, config)


if __name__ == '__main__':
    main()
