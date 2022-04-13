from interface.cli import MenuBasedCLI

def main():
    interface = MenuBasedCLI()
    interface.run_cli()

if __name__ == "__main__":
    raise SystemExit(main())