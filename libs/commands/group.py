import click


class Group(click.Group):
    def register_commands(self, *commands):
        for command in commands:
            self.command()(command)
