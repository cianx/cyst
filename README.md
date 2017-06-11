# CYST

Tool to report on the Hyperledger Sawtooth CI integration status, providing the ability to trigger builds and retrieve build logs from the jenkins CI server.

Cyst should run on all major operating systems but has only been tested on
Ubuntu 16.04.

## Overview

- `cyst status` - Display a table of the open pull-requests on the hyperledger/sawtooth-core

- `cyst build <pr #>` - trigger a build

- `cyst logs <pr #> <build #>` - Will retrieve the buiild logs from jenkins and
display them to stdout. The build number is valid between 1 and the build
number displayed on the status for that PR.


# INSTALLATION

Cyst requires the following components to be installed:

- python3
- python3-pip
- virtualenv ( install via pip)

The easiest way to install and run cyst is to. Clone cyst to your local maching, and call `cyst-cli status` from a command prompt. This will create a python virtual environment install the required dependencies and run cyst.
The first call to 'cyst-cli' will be slow and have lots of extra output as the
VirtualEnvironment is setup. Subsequent calls will behavior as you would expect.

cyst can also be installed via python setuptools.


# CONFIGURATION

Cyst requires user credentials in order to access Jenkins to trigger builds
and get a higher rate limit on Github for queries cyst will need credentials
to both of those systems. Cyst will run with out either of those credentials
however you will not be able to trigger jenkins builds and Github has a
low rate limit for unauthenticated requests so you may not be able to
retrieve status information very often.

When cyst is first run it will create a template configuration file at ~/.cyst,
this file is create with 600 permissions. Your Jenkins username and password
can be provided here and a GitHub token can be obtained here:
https://github.com/settings/tokens

# DEVELOPMENT

## Requirements

python3, python3-pip, virtualenv

```
sudo apt-get install python3, python3-pip
sudo pip3 install virtualenv

```

Clone the repo to your local machine.
Then from the clone directory
```
source cyst-dev
```
This will setup a python3 virtualenv and install the required dependencies in
that environment.

`cyst-cli`
