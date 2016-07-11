#!/usr/bin/env python
"""
Usage:
    extractobot <key_name> <spec>
    extractobot --help
"""
import os
import logging
from pkg_resources import get_distribution
from docopt import docopt

__version__ = get_distribution('excerpt').version

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
def main():
    opts = docopt(__doc__)
    key_name, spec = opts['<key_name>'], opts['<spec>']
    import yaml
    with open(spec) as f:
        dump_spec = yaml.load(f)

    from core import init_container
    aws_config_ls = [
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SUBNET_ID"
        "AWS_ZONE",
    ]
    aws_config = {}

    for key in aws_config_ls:
        aws_config[key] = os.getenv(key)
    init_container(key_name, dump_spec, aws_config)

if __name__ == '__main__':
    main()


