from fcpx_marker_tool.interface import cli

def main():
    interface = cli.MenuBasedCLI()
    interface.run_cli()

if __name__ == "__main__":
    raise SystemExit(main())