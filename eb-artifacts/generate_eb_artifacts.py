#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generates necessary artifacts for Multi-container Docker Elastic Beanstalk setup"""

import argparse
import json
import shutil
import os
import glob

__author__ = "Jean-Martin Archer"


DEFAULT_MEMORY = 7000
DEFAULT_PORT = 80
DEFAULT_LOG_PATH = '/var/log/containers'

# TODO: Support multiple containers.


def main():
    parser = argparse.ArgumentParser(description='Prepare Elastic Beanstalk artifacts, '
                                                 'ready to be packaged and published.')
    parser.add_argument('--name', help='name of service / docker image. "__SERVICE_NAME" in '
                                       'the ebextensions will be replaced with this.', required=True)
    parser.add_argument('--version', help='image version/tag to use', required=True)
    parser.add_argument('--container-port', help='container http port to expose on port 80', default=DEFAULT_PORT)
    parser.add_argument('--port-mappings', help='additional port to expose', nargs='*', default=[])
    parser.add_argument('--mount-points', help='list of mount points for volumes', nargs='*')
    parser.add_argument('--log-path', help='path for the service logs', default=DEFAULT_LOG_PATH)
    parser.add_argument('--memory',
                        help='Maximum amount of memory the container is allowed '
                             'to use. Must be lower than the EC2 instance memory.',
                        default=DEFAULT_MEMORY)
    parser.add_argument('--registry', help='Docker registry to use.')
    default_templates_path = os.path.join(os.path.dirname(__file__), 'templates')
    parser.add_argument('--templates',
                        help='Templates directory path. Needs to be absolute. Default="templates"',
                        default=default_templates_path)
    parser.add_argument('--extensions-filter', help='Regex for extensions to package, if not defined, '
                                                    'everything is used. Default is *. E.g.: '
                                                    '--extensions-filter 0[1-3]* will pick the '
                                                    'first 3 extensions only.'
                        , default='*')
    parser.add_argument('--output', help='Output directory, default: "output".', default='output')
    args = parser.parse_args()

    prepare(args)
    create_dockerrun(args)
    render_extensions(args)

    print('Done!')


def prepare(args):
    if os.path.isdir(args.output):
        shutil.rmtree(args.output)
    os.mkdir(args.output)
    os.mkdir('{output}/.ebextensions'.format(**args.__dict__))


def create_dockerrun(args):
    with open('{output}/Dockerrun.aws.json'.format(**args.__dict__), 'w') as fp:
        json.dump(build_docker_run(args), fp)


def create_volume_name(path):
    return os.path.basename(path)


def build_volumes_definition(mount_points):
    if mount_points:
        return [{'name': create_volume_name(mount_point), 'host': {'sourcePath': mount_point}} for mount_point in
            mount_points]

    return []


def build_docker_run(args):
    return {
        'AWSEBDockerrunVersion': 2,
        'volumes': build_volumes_definition(args.mount_points),
        'containerDefinitions': [
            build_container_definition(**args.__dict__)
        ]
    }


def build_mount_points(mount_points):
    if mount_points:
        return [{'sourceVolume': create_volume_name(mount_point),
                 'containerPath': mount_point
                 } for mount_point in mount_points]

    return []


def build_port_mappings(**kwargs):
    def build_mapping(host_port, container_port):
        return {
            'hostPort': int(host_port),
            'containerPort': int(container_port)
        }

    def build_mapping_from_string(entry):
        (host_port, container_port) = entry.split(':')
        return build_mapping(host_port, container_port)

    return [build_mapping(DEFAULT_PORT, kwargs['container_port'])] + \
           [build_mapping_from_string(entry) for entry in kwargs['port_mappings']]


def build_container_definition(**kwargs):
    return {
        'name': '{name}-service'.format(**kwargs),
        'image': '{registry}/service/{name}:{version}'.format(**kwargs),
        'essential': True,
        'memory': kwargs['memory'],
        'portMappings': build_port_mappings(**kwargs),
        'mountPoints': build_mount_points(kwargs['mount_points'])
    }


def render_extensions(args):
    glob_filter = '{templates}/.ebextensions/{extensions_filter}.config'.format(**args.__dict__)
    [render_extension(path, args) for path in glob.glob(glob_filter)]


def render_extension(path, args):
    output_path = os.path.join(args.output, os.path.relpath(path, args.templates))
    with open(output_path, 'w') as fp_out:
        with open(path, 'r') as fp:
            file_naive_render(args, fp, fp_out)

    print('Created: {}'.format(output_path))


def file_naive_render(args, fp_in, fp_out):
    [fp_out.write(naive_render(args, line)) for line in fp_in.readlines()]


def naive_render(args, line):
    return line\
        .replace("__SERVICE_NAME", args.name)\
        .replace("__SERVICE_LOG_PATH", args.log_path)

if __name__ == '__main__':
    main()
