import os
import re

def clean_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Remove try-except ImportError blocks for engine_core
                # Pattern: 
                # try:
                #     from .something import ...
                # except ImportError:
                #     from something import ...
                
                # Since I already ran some sed, it might look like:
                # try:
                #     from engine_core.something import ...
                # except ImportError:
                #     from something import ...
                
                new_content = re.sub(
                    r"try:\s+from engine_core\.(.*?) import (.*?)\s+except ImportError:\s+from (.*?) import (.*?)\s",
                    r"from engine_core.\1 import \2\n",
                    content, flags=re.MULTILINE
                )

                # Also handle simple "from . import"
                new_content = re.sub(
                    r"try:\s+from engine_core import (.*?)\s+except ImportError:\s+from (.*?) import (.*?)\s",
                    r"from engine_core import \1\n",
                    new_content, flags=re.MULTILINE
                )
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Cleaned imports in {path}")

if __name__ == "__main__":
    clean_imports("engine_core")
