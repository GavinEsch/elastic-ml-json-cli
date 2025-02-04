import click
from ml_json_cli.commands import load, search, compare, history, merge, export, undo


@click.group()
def cli():
    """Elastic ML JSON CLI Tool"""
    pass


cli.add_command(load.load)
cli.add_command(search.search)
cli.add_command(compare.compare)
cli.add_command(history.history)
cli.add_command(merge.merge)
cli.add_command(export.export)
cli.add_command(undo.undo)

if __name__ == "__main__":
    cli()
