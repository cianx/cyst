#!/usr/bin/env python
#
# Copyright 2017 Cian Montgomery
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import argparse
import traceback

import configparser
import os
import stat
import sys

from github import Github
import jenkins as Jenkins

GIT_REPO = 'hyperledger/sawtooth-core'
JENKINS_SERVER = 'https://build.sawtooth.me'
JENKINS_JOB = 'Sawtooth-Hyperledger/sawtooth-core'


def load_config():
    config_file = os.path.join(os.path.expanduser('~'), ".cyst")
    config = configparser.SafeConfigParser()
    config.add_section("github")
    config.set("github", "token", "")
    config.add_section("jenkins")
    config.set("jenkins", "username", "")
    config.set("jenkins", "password", "")
    if os.path.exists(config_file):
        config.read(config_file)
    return config


def config_error():
    config_file = os.path.join(os.path.expanduser('~'), ".cyst")
    if not os.path.exists(config_file):
        with open(config_file, "w") as w:
            w.write("""
[github]
# if you get rate limited by github provide a authorization token
# from: https://github.com/settings/tokens
# token = <your token here>

[jenkins]
# username = <your jenkings user Name>
# password = <your jenkins PW>
        """)
        os.chmod(config_file, stat.S_IRUSR|stat.S_IWUSR)
    print('In order to trigger builds please provide your jenkins '
          'credentials in {}'.format(config_file))


def add_status_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('status', parents=[parent_parser])

    parser.add_argument(
        '-p', '--pr',
        type=int,
        default=None,
        dest='pull_request',
        help='The PR number to report.')
    parser.add_argument(
        '-u', '--user',
        type=str,
        default=None,
        dest='user',
        help='GitHub user login to filter by.')


def add_build_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('build', parents=[parent_parser])
    parser.add_argument(
        dest='pull_request',
        type=int,
        help='The PR number to build.')


def add_logs_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('logs', parents=[parent_parser])
    parser.add_argument(
        dest='pull_request',
        type=int,
        help='The PR number to retreive the build logs for.')
    parser.add_argument(
        dest='build_number',
        nargs='?',
        type=int,
        default=None,
        help='The build number to pull logs for. Optional, defaults to the '
             'last build')


def create_parent_parser(program_name):
    parent_parser = argparse.ArgumentParser(prog=program_name, add_help=False)

    return parent_parser


def create_parser(program_name):
    parent_parser = create_parent_parser(program_name)
    parser = argparse.ArgumentParser(parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands',
                                       dest='command')
    add_status_parser(subparsers, parent_parser)
    add_build_parser(subparsers, parent_parser)
    add_logs_parser(subparsers, parent_parser)

    return parser


def open_github(config):
    repo = GIT_REPO
    token = config['github']['token'] or None
    github = Github(login_or_token=token)
    return github.get_repo(repo)


class JenkinHelper(object):
    def __init__(self, server, job, username, password):
        self.job = job
        self.authenticated = username is not None and \
            password is not None
        if self.authenticated:
            self.jenkins = Jenkins.Jenkins(
                server, username=username, password=password)
        else:
            self.jenkins = Jenkins.Jenkins(server)

    def get_job_info(self, pr_number):
        try:
            job_name = '{}/PR-{}'.format(self.job, pr_number)
            job_info = self.jenkins.get_job_info(job_name)
            return job_info
        except Jenkins.NotFoundException:
            return None

    def get_build_logs(self, pr_number, build_number=None):
        try:
            job_name = '{}/PR-{}'.format(self.job, pr_number)
            last_build_number = build_number
            if last_build_number is None:
                job_info = self.jenkins.get_job_info(job_name)
                last_build = job_info['lastBuild'] or {}
                last_build_number = last_build.get('number')
                if last_build_number is None:
                    return 'Unavailiable'

            build_logs = self.jenkins.get_build_console_output(
                job_name, last_build_number)
            return build_logs
        except Jenkins.NotFoundException:
            return "Not Found"

    def trigger_build(self, pr_number):
        job_name = '{}/PR-{}'.format(self.job, pr_number)
        self.jenkins.build_job(job_name)


def open_jenkins(config):
    server = JENKINS_SERVER
    job = JENKINS_JOB
    username = config['jenkins']['username'] or None
    password = config['jenkins']['password'] or None
    return JenkinHelper(server, job, username, password)


def get_pull_request_build_status(pr_number, jenkins):
    job_info = jenkins.get_job_info(pr_number)

    if not job_info:
        return "MIA"

    last_build = job_info['lastBuild']
    last_completed_build = job_info['lastCompletedBuild'] or {}
    last_failed_build = job_info['lastFailedBuild'] or {}
    last_successful_build = job_info['lastSuccessfulBuild'] or {}
    status = 'UNKNOWN'

    last_build_number = last_build.get('number')
    if last_build_number != last_completed_build.get('number', -1):
        status = 'BUILDING'
    elif last_build_number == last_failed_build.get('number', -1):
        status = 'FAILED'
    elif last_build_number == last_successful_build.get('number', -1):
        status = 'SUCCESS'

    return '{}({})'.format(last_build['number'], status)


def do_status(args, github, jenkins):
    print("Open Pull Requests for {}".format(github.name))

    pull_request_filter = args.pull_request
    user_filter = args.user

    line_format = '{:<8}{:<16}{:<10}{:<16}{}'
    print(line_format
          .format('PR#', 'SUBMITTER', 'STATUS', 'BUILD', 'TITLE'))

    show_count = 0
    count = 0
    pull_requests = github.get_pulls()
    for pull_request in pull_requests:
        count += 1
        show = True
        if user_filter:
            show = show and user_filter == pull_request.user.login
        if pull_request_filter:
            show = show and pull_request_filter == pull_request.number

        if show:
            show_count += 1
            build_status = get_pull_request_build_status(
                pull_request.number, jenkins)
            print(line_format
                  .format(pull_request.number,
                          pull_request.user.login,
                          pull_request.mergeable_state,
                          build_status,
                          pull_request.title
                          ))

    print('Displaying {} of {} Pull Requests.'.format(show_count, count))


def do_logs(args, github, jenkins):
    pull_request = args.pull_request
    build_number = args.build_number
    logs = jenkins.get_build_logs(pull_request, build_number)
    print(logs)


def do_build(args, github, jenkins):
    pull_request = args.pull_request
    if not jenkins.authenticated:
        config_error()
        exit(1)
    jenkins.trigger_build(pull_request)
    print("Build request submitted.")


def main(program_name, args):
    config = load_config()

    parser = create_parser(program_name)
    args = parser.parse_args(args)

    github = open_github(config)
    jenkins = open_jenkins(config)

    if args.command == 'status':
        do_status(args, github, jenkins)
    elif args.command == 'logs':
        do_logs(args, github, jenkins)
    elif args.command == 'build':
        do_build(args, github, jenkins)
    else:
        raise AssertionError("invalid command: {}".format(args.command))


def main_wrapper():
    # pylint: disable=bare-except
    try:
        program_name = os.path.basename(sys.argv[0])
        args = sys.argv[1:]
        main(program_name, args)
    except KeyboardInterrupt:
        pass
    except SystemExit as e:
        raise e
    except:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_wrapper()
