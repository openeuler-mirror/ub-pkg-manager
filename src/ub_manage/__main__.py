import sys

from ub_manage.cli.cmd import CLIApplication


def ub_cli():
    """
    Main function for the ub-pkg-cli command
    """
    app = CLIApplication(name="ub-pkg-cli")
    sys.exit(app.run())


if __name__ == "__main__":
    sys.exit(ub_cli())
