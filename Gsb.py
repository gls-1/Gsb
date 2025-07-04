import os
import sys
import time
import json
import webbrowser
from difflib import get_close_matches

if os.name == "nt":
    import msvcrt
else:
    import tty
    import termios

# === Paths ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GSB_DIR = os.path.join(BASE_DIR)
MEDIA_DIR = GSB_DIR
USER_DIR = os.path.join(GSB_DIR, "Users")
METADATA_PATH = os.path.join(os.path.dirname(__file__), "metadata.json")

# === Startup ===
print("🌀 Booting Garrett Search Bar...")
os.makedirs(USER_DIR, exist_ok=True)

# === Workspace Memory ===
workspace_data = {
    "current": 0,
    "last": 0,
    "workspaces": {str(i): [] for i in range(10)}
}

def load_metadata():
    global workspace_data
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r") as f:
            workspace_data.update(json.load(f))

def save_metadata():
    with open(METADATA_PATH, "w") as f:
        json.dump(workspace_data, f, indent=2)

load_metadata()

def switch_workspace(n):
    workspace_data["last"] = workspace_data["current"]
    workspace_data["current"] = n
    save_metadata()

def add_to_workspace(entry):
    ws = str(workspace_data["current"])
    workspace_data["workspaces"].setdefault(ws, []).append(entry)
    save_metadata()

# === Select UI ===
def select_from_list(title, options):
    selected = 0

    def render():
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\n🔍 {title}\n")
        for i, item in enumerate(options):
            prefix = ">" if i == selected else " "
            print(f"{prefix} {item}")

    def read_key():
        if os.name == "nt":
            return msvcrt.getch()
        else:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                return sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    while True:
        render()
        key = read_key()
        if key in ("\t", b"\t"):  # Tab
            selected = (selected + 1) % len(options)
        elif key in ("\r", b"\r", "\n"):  # Enter
            return options[selected]
        elif key in ("\x03", b"\x03"):  # Ctrl+C
            return None

# === Search ===
def local_file_search(query):
    results = []
    for root, dirs, files in os.walk(MEDIA_DIR):
        for name in files:
            if query.lower() in name.lower():
                results.append(os.path.join(root, name))
    return results

def search_menu(query):
    options = []
    matches = local_file_search(query)
    for match in matches:
        options.append(match)
    options.append(f'Google "{query}"')
    options.append(f'ChatGPT "{query}"')

    choice = select_from_list(query, [os.path.basename(x) for x in options])
    full = next((o for o in options if os.path.basename(o) == choice or o == choice), None)
    if not full:
        return

    if full.startswith("Google"):
        webbrowser.open(f"https://www.google.com/search?q={query}")
        add_to_workspace(full)
    elif full.startswith("ChatGPT"):
        print(f"\n🤖 ChatGPT (stub): \"{query}\"")
        add_to_workspace(full)
    elif os.path.exists(full):
        print(f"📂 Opening {full}")
        os.system(f'start "" "{full}"' if os.name == "nt" else f'xdg-open "{full}"')
        add_to_workspace(full)

# === Virtual Environment ===
def launch_python_env():
    envs_dir = os.path.join(BASE_DIR, "Envs")
    os.makedirs(envs_dir, exist_ok=True)

    name = input("Enter virtualenv name: ").strip()
    path = os.path.join(envs_dir, name)
    if not os.path.exists(path):
        os.system(f"python3 -m venv '{path}'")
        print(f"✅ Created at {path}")

    if os.name == "nt":
        print(f"Run: {path}\\Scripts\\activate.bat")
    else:
        print(f"Run: source {path}/bin/activate")

    add_to_workspace(f"VENV: {name}")

# === Menu ===
def show_workspace():
    ws = str(workspace_data["current"])
    print(f"\n🧭 Workspace {ws}:")
    for item in workspace_data["workspaces"].get(ws, []):
        print("•", item)

def launcher():
    print("\n🚀 Launcher:")
    print("1. Launch Python Environment")
    print("2. Switch Workspace (0-9)")
    print("3. Last Workspace")
    print("4. Clear Other Workspaces")
    print("5. Back\n")

    choice = input("Choice: ").strip()
    if choice == "1":
        launch_python_env()
    elif choice == "2":
        target = input("Workspace #: ")
        if target.isdigit():
            switch_workspace(int(target))
    elif choice == "3":
        switch_workspace(workspace_data["last"])
    elif choice == "4":
        curr = str(workspace_data["current"])
        for k in workspace_data["workspaces"]:
            if k != curr:
                workspace_data["workspaces"][k] = []
        save_metadata()
        print("🧹 Cleared other workspaces.")
    elif choice == "5":
        return

# === Main Loop ===
while True:
    show_workspace()
    cmd = input("\n🔎 Search or type 'launcher' (q = quit): ").strip()
    if cmd.lower() == "q":
        print("👋 Shutting down.")
        save_metadata()
        break
    elif cmd.lower() == "launcher":
        launcher()
    elif cmd:
        search_menu(cmd)
      
