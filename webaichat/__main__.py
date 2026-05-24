import sys

def main_cli():
    from .cli import main_cli as _main_cli
    _main_cli()

if __name__ == "__main__":
    main_cli()
