import sys

submodule_paths = [entry for entry in sys.path if "submodules/" in entry]
for path in submodule_paths:
    sys.path.remove(path)

sys.path.insert(0,"submodules/oemof_household")


from oemof_app import run

run()