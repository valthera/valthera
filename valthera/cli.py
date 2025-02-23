import click

@click.command()
@click.argument('prompt')
def main(prompt):
    """Simple CLI tool that takes a prompt and returns 'hello world'"""
    click.echo(f"Received prompt: {prompt}")
    click.echo("hello world")

if __name__ == '__main__':
    main()
