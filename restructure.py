"""Script to reorganize metaprotocol to match spec directory structure."""

import os
import shutil
from pathlib import Path

# Root directory
metaprotocol_dir = Path("metaprotocol")

# Create directory structure (already done)
print("Directories already created")

# Move files to new locations
moves = [
    # Registry
    ("metaprotocol/embedding.py", "metaprotocol/registry/embedding.py"),
    ("metaprotocol/registry.py", "metaprotocol/registry/skill_registry.py"),
    
    # Reputation
    ("metaprotocol/reputation.py", "metaprotocol/reputation/reputation_system.py"),
    ("metaprotocol/disputes.py", "metaprotocol/reputation/dispute.py"),
    
    # Negotiation
    ("metaprotocol/negotiation.py", "metaprotocol/negotiation/engine.py"),
    
    # Team
    ("metaprotocol/team.py", "metaprotocol/team/formation.py"),
    ("metaprotocol/optimizer.py", "metaprotocol/team/optimizer_greedy.py"),
    
    # Serve
    ("metaprotocol/serve.py", "metaprotocol/serve/routes.py"),
    
    # CLI
    ("metaprotocol/cli.py", "metaprotocol/cli/main.py"),
    
    # Market (new, in root as market.py)
    ("metaprotocol/market.py", "metaprotocol/market.py"),
    
    # VAOS adapter (new, in root as vaos_adapter.py)
    ("metaprotocol/vaos_adapter.py", "metaprotocol/vaos_adapter.py"),
]

for src, dst in moves:
    src_path = Path(src)
    dst_path = Path(dst)
    if src_path.exists() and not dst_path.exists():
        print(f"Moving {src} -> {dst}")
        shutil.move(str(src_path), str(dst_path))
    elif dst_path.exists():
        print(f"Skipping {src} (already at {dst})")
    else:
        print(f"Skipping {src} (not found)")

# Delete old files that are no longer needed
to_delete = [
    "metaprotocol/models.py",  # Replaced by types.py
    "metaprotocol/storage.py",  # Replaced by store/sqlite.py
    "metaprotocol/postgres.py",  # Will be recreated in store/postgres.py
]

for path_str in to_delete:
    path = Path(path_str)
    if path.exists():
        print(f"Deleting {path_str}")
        path.unlink()

# Create __init__.py files for each subdirectory
init_files = [
    "metaprotocol/registry/__init__.py",
    "metaprotocol/reputation/__init__.py",
    "metaprotocol/negotiation/__init__.py",
    "metaprotocol/team/__init__.py",
    "metaprotocol/serve/__init__.py",
    "metaprotocol/cli/__init__.py",
]

for init_file in init_files:
    path = Path(init_file)
    if not path.exists():
        print(f"Creating {init_file}")
        path.write_text("")

print("\nRestructuring complete!")
print("Next steps:")
print("1. Create remaining __init__.py files with proper exports")
print("2. Split negotiation.py into separate modules")
print("3. Split team.py into separate modules")
print("4. Create missing modules (optimizer_ilp.py, etc.)")
print("5. Update imports throughout the codebase")
