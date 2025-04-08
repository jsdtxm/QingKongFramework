import click


class Group(click.Group):
    def register_commands(self, *commands):
        # TODO 检查是否已经注册app
        for command in commands:
            self.command()(command)
