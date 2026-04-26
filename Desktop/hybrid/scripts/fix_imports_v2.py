import os
import re

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    in_try_import = False
    
    for line in lines:
        # Remove "try:" if it's followed by an engine_core import
        if re.match(r"^\s*try:\s*$", line):
            in_try_import = True
            continue
        
        if in_try_import:
            if "from engine_core" in line:
                new_lines.append(line.lstrip())
                continue
            if "except ImportError:" in line or "from ." in line:
                continue
            if re.match(r"^\s*$", line):
                continue
            in_try_import = False
            
        # Fix leading spaces for already processed imports
        if line.startswith("    from engine_core"):
            new_lines.append(line.lstrip())
        else:
            new_lines.append(line)
            
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

for root, dirs, files in os.walk("engine_core"):
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))
