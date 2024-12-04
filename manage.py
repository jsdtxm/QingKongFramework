import multiprocessing

from libs.commands import about, cli, migrate, proxy, runserver

cli.register_commands(runserver, proxy, migrate, about)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
