# -*- coding: utf-8 -*-

from __future__ import print_function

import click
import logging

from compath import managers
from compath.constants import DEFAULT_CACHE_CONNECTION

log = logging.getLogger(__name__)


def set_debug(level):
    log.setLevel(level=level)


def set_debug_param(debug):
    if debug == 1:
        set_debug(20)
    elif debug == 2:
        set_debug(10)


@click.group()
def main():
    """ComPath"""
    logging.basicConfig(level=10, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


@main.command()
def ls():
    """List registered managers"""
    for manager in managers:
        click.echo(manager)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--delete-first', is_flag=True)
def populate(debug, connection, delete_first):
    """Populate all databases"""
    set_debug_param(debug)

    for name, Manager in managers.items():
        m = Manager(connection=connection)

        if delete_first:
            click.echo('deleting {}'.format(name))
            m.drop_all()
            m.create_all()

        click.echo('populating {}'.format(name))
        m.populate()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop(debug, yes, connection):
    """Drop all databases"""
    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the databases for {}?'.format(', '.join(managers))):
        for name, Manager in managers.items():
            m = Manager(connection=connection)
            click.echo('deleting {}'.format(name))
            m.drop_all()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def web(debug, connection):
    """Run web service"""
    set_debug_param(debug)

    from compath.web import create_app
    app = create_app(connection=connection)
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()