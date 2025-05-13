import click


class Group(click.Group):
    def register_commands(self, *commands):
        # TODO 检查是否已经注册app
        for command in commands:
            if isinstance(command, click.Command):
                self.add_command(command)
                continue
            self.command()(command)
