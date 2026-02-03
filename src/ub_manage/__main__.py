import sys

from ub_manage.cli.cmd import CLIApplication


def ub_cli():
    """
    Main function for the ub-cli command
    """
    app = CLIApplication(name="ub-cli")
    sys.exit(app.run())


if __name__ == "__main__":
    sys.exit(ub_cli())
