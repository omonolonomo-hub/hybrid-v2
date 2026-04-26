#!/usr/bin/env python3
"""
Import Path Fixer - Reorganizasyon sonrası import statement'ları günceller
"""

import re
from pathlib import Path
from typing import List, Tuple

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")


class ImportFixer:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.fixes: List[Tuple[Path, int]] = []
        
        # Import değiştirme kuralları
        self.replacements = [
            # src.autochess_sim_v06 → engine_core.autochess_sim_v06
            (r'from src\.autochess_sim_v06 import', 'from engine_core.autochess_sim_v06 import'),
            (r'import src\.autochess_sim_v06', 'import engine_core.autochess_sim_v06'),
            (r'from src import autochess_sim_v06', 'from engine_core import autochess_sim_v06'),
            
            # sys.path.insert için src → engine_core
            (r"sys\.path\.insert\(0, ['\"]src['\"]\)", "sys.path.insert(0, 'engine_core')"),
            (r"sys\.path\.insert\(0, os\.path\.join\(.*?, ['\"]src['\"]\)\)", 
             "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine_core'))"),
            
            # Relative imports
            (r'from \.\.src\.', 'from ..engine_core.'),
            (r'from \.src\.', 'from .engine_core.'),
        ]
        
        # Asset path değiştirme kuralları
        self.asset_replacements = [
            # cards.json path
            (r'os\.path\.join\(base_dir, ["\']cards\.json["\']\)',
             'os.path.join(base_dir, "..", "assets", "data", "cards.json")'),
            
            (r'["\']data/cards\.json["\']',
             '"assets/data/cards.json"'),
            
            (r'["\']data/passives\.txt["\']',
             '"assets/data/passives.txt"'),
        ]
    
    def find_python_files(self) -> List[Path]:
        """Tüm Python dosyalarını bul"""
        python_files = []
        
        # Taranacak klasörler
        scan_dirs = [
            "engine_core",
            "gameplay",
            "scripts",
            "tests",
            "tools",
        ]
        
        for dir_name in scan_dirs:
            dir_path = self.root / dir_name
            if dir_path.exists():
                python_files.extend(dir_path.rglob("*.py"))
        
        return python_files
    
    def fix_file(self, file_path: Path) -> int:
        """Bir dosyadaki import'ları düzelt"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            changes = 0
            
            # Import replacements
            for pattern, replacement in self.replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes += content.count(pattern)
                    content = new_content
            
            # Asset path replacements
            for pattern, replacement in self.asset_replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes += 1
                    content = new_content
            
            # Değişiklik varsa dosyayı güncelle
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                return changes
            
            return 0
            
        except Exception as e:
            log_warning(f"Dosya işlenemedi: {file_path}: {e}")
            return 0
    
    def run(self):
        """Tüm dosyaları tara ve düzelt"""
        print("\n" + "="*60)
        print("🔧 Import Path Fixer")
        print("="*60 + "\n")
        
        log_info("Python dosyaları taranıyor...")
        python_files = self.find_python_files()
        log_info(f"{len(python_files)} Python dosyası bulundu")
        
        total_changes = 0
        fixed_files = 0
        
        for file_path in python_files:
            changes = self.fix_file(file_path)
            if changes > 0:
                fixed_files += 1
                total_changes += changes
                log_success(f"{file_path.relative_to(self.root)}: {changes} değişiklik")
        
        print("\n" + "="*60)
        print(f"{Colors.GREEN}✅ Import düzeltme tamamlandı!{Colors.END}")
        print("="*60 + "\n")
        
        print(f"📊 Özet:")
        print(f"  - Taranan dosya: {len(python_files)}")
        print(f"  - Düzeltilen dosya: {fixed_files}")
        print(f"  - Toplam değişiklik: {total_changes}")
        print()


if __name__ == "__main__":
    fixer = ImportFixer()
    fixer.run()
