import os
import re

def fix_type_checking(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Indent lines after "if TYPE_CHECKING:" until an empty line or a non-indented line starts
    lines = content.splitlines()
    new_lines = []
    indent_next = False
    
    for line in lines:
        if re.match(r"^if TYPE_CHECKING:\s*$", line):
            new_lines.append(line)
            indent_next = True
            continue
        
        if indent_next:
            if line.startswith("from ") or line.startswith("import "):
                new_lines.append("    " + line.lstrip())
                continue
            elif line.strip() == "":
                new_lines.append(line)
                continue
            else:
                indent_next = False
        
        new_lines.append(line)
        
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

for root, dirs, files in os.walk("engine_core/passives"):
    for file in files:
        if file.endswith(".py"):
            fix_type_checking(os.path.join(root, file))
