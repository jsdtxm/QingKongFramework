import multiprocessing

from libs.commands import about, cli, migrate, gateway, runserver, startapp

cli.register_commands(runserver, gateway, startapp, migrate, about)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
