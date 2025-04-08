import multiprocessing

from fastapp.commands import about, cli, migrate, gateway, runserver, startapp, serve_static

cli.register_commands(runserver, gateway, startapp, migrate, about, serve_static)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
