from rich.console import Console
from ui.menu import Menu

def main():
    console = Console()
    menu = Menu(console)
    menu.start()

if __name__ == "__main__":
    main() 