# Development Environment Setup Instructions
To set up Monarch_QC_Reports for development, we recommend using pyenv for managing your Python versions, the native Python module venv for managing your virtual environments and poetry for managing your dependencies. See the [initial Setup](#initial-setup) section for instructions on how these tools were used to set up the initial development environment for this project.

# Initial Setup
## Install pyenv
pyenv is a tool for managing multiple versions of Python on a single machine. It provides a command line interface to install, uninstall, and switch between different versions of Python. It also provides a mechanism for managing virtual environments. See the [pyenv documentation]() for more information.

### Install pyenv on Ubuntu
```bash
sudo apt-get update
sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
curl https://pyenv.run | bash
```

I will also need to add the following to your .bashrc file:
```bash
# Use pyenv to manage Python versions
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

I also have some scripting I added to my .bashrc to use my PS1 prompt to show me which Python version I am using in my current shell. This is not necessary, but I find it useful. If you are interested in this, please reach out and I will share it with you.

## Install Python 3.11.4
We are using the most current version of Python, 3.11.4. To install this version of Python and use it locally within the Monarch_QC_Reports project, run the following commands:
```bash
pyenv install 3.11.4
pyenv local 3.11.4
```

## Initialize a virtual environment
We are using the native Python module venv to manage our virtual environments. To create and activate a virtual environment for this project, run the following command:
```bash
python -m venv .venv
source .venv/bin/activate
```

To deactivate the virtual environment run the following command in the root of your repository.
```shell
deactivate
```

I create a file named `venv_name.txt` in the root of the venv directory. This file contains a nickname of the virtual environment. I use this in my .bashrc to read the name and track which virtual environment I have active in $PS1. This is optional but I find it useful. If you would like to know how to do this please reach out and I'll share my .bashrc.
```shell
echo "qcr" > .venv/venv_name.txt
````

## Poetry
Poetry is a Python dependency manager. It allows you to manage Python dependencies for a project. Poetry will also create a virtual environment for the project and install the dependencies in that environment. This allows you to install the exact versions of dependencies required for the DST.

Install poetry with pip in the virtual environment then initialize with the following commands.
```shell
pip install poetry
poetry install
```

## Make the initial git commit
```shell
git add .
git commit -m "Initial commit with setup"
```
