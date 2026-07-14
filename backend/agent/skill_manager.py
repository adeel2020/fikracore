import os
import re
import sys
import asyncio
import subprocess
import importlib.util
from typing import Optional

class SkillItem:
    def __init__(self, name: str, description: str, argument_hint: list[str], role: str, path: str):
        self.name = name
        self.description = description
        self.argument_hint = argument_hint
        self.role = role
        self.path = path

class SkillManager:
    def __init__(self):
        # Resolve skills directory at workspace root
        self.skills_dir = os.path.join(os.path.dirname(__file__), "..", "..", "skills")
        self.skills_dir = os.path.abspath(self.skills_dir)
        self._skills_cache: dict[str, SkillItem] = {}
        self.discover_skills()

    def discover_skills(self) -> dict[str, SkillItem]:
        """Scan the skills directory and load metadata from SKILL.md for each skill."""
        skills = {}
        if not os.path.exists(self.skills_dir) or not os.path.isdir(self.skills_dir):
            print(f"[SkillManager] Skills directory '{self.skills_dir}' not found.")
            return skills

        for name in os.listdir(self.skills_dir):
            folder_path = os.path.join(self.skills_dir, name)
            if os.path.isdir(folder_path):
                skill_md_path = os.path.join(folder_path, "SKILL.md")
                
                # Default values
                description = f"Custom agent skill: {name}"
                argument_hint = []
                # Formulate a default role based on the folder name
                role = " ".join([word.capitalize() for word in name.split("-")]) + " Specialist"
                
                if os.path.exists(skill_md_path):
                    try:
                        with open(skill_md_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if content.startswith("---"):
                                parts = content.split("---", 2)
                                if len(parts) >= 3:
                                    frontmatter_text = parts[1]
                                    for line in frontmatter_text.splitlines():
                                        if ":" in line:
                                            key, val = line.split(":", 1)
                                            key = key.strip().lower()
                                            val = val.strip().strip('"').strip("'")
                                            if key == "name":
                                                name = val
                                            elif key == "description":
                                                description = val
                                            elif key == "role":
                                                role = val
                                            elif key == "argument-hint":
                                                # Parse bracketed list of hints
                                                try:
                                                    # Using safe evaluation/parsing for lists
                                                    cleaned_val = val.replace("[", "").replace("]", "").replace('"', '').replace("'", "")
                                                    argument_hint = [h.strip() for h in cleaned_val.split(",") if h.strip()]
                                                except Exception:
                                                    argument_hint = []
                    except Exception as e:
                        print(f"[SkillManager] Error parsing SKILL.md for {name}: {e}")

                skills[name] = SkillItem(
                    name=name,
                    description=description,
                    argument_hint=argument_hint,
                    role=role,
                    path=folder_path
                )
        
        self._skills_cache = skills
        return skills

    def get_skill(self, name: str) -> Optional[SkillItem]:
        """Fetch a skill by name. Re-runs discovery if cache is empty.
        Also tries normalized lookups to handle common input mismatches
        (e.g. /trace_analyzer vs trace-analyzer).
        """
        if not self._skills_cache:
            self.discover_skills()

        # Direct match first
        skill = self._skills_cache.get(name)
        if skill:
            return skill

        # Normalize: swap hyphens ↔ underscores
        normalized = name.replace("-", "_").replace("_", "-")
        if normalized != name:
            skill = self._skills_cache.get(normalized)
            if skill:
                return skill

        # Case-insensitive fallback
        name_lower = name.lower()
        for cache_key, cache_skill in self._skills_cache.items():
            if cache_key.lower().replace("-", "_").replace("_", "-") == name_lower:
                return cache_skill

        return None

    def get_skills_list(self) -> list:
        """Return a serializable list of skills for backend API endpoints."""
        self.discover_skills()
        return [
            {
                "name": item.name,
                "description": item.description,
                "role": item.role,
                "argument_hint": item.argument_hint
            }
            for item in self._skills_cache.values()
        ]

    async def execute_skill(self, skill_name: str, arguments: list[str]) -> tuple[str, str]:
        """Locate, execute, and format the output of a specific skill.
        
        Returns:
            tuple[str, str]: (formatted_output_text, agent_role)
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return (
                f"### ❌ Unknown Skill\n\nThe skill **/{skill_name}** could not be found in the current workspace.",
                "System Agent"
            )

        # Find the execution script
        script_path = None
        # Look in skills/{skill_name}/scripts/ or skills/{skill_name}/ for a python script
        search_dirs = [
            os.path.join(skill.path, "scripts"),
            skill.path
        ]
        
        for s_dir in search_dirs:
            if os.path.exists(s_dir) and os.path.isdir(s_dir):
                py_files = [f for f in os.listdir(s_dir) if f.endswith(".py") and not f.startswith("__") and f != "formatter.py"]
                if py_files:
                    main_files = [f for f in py_files if f.startswith("analyze") or "main" in f]
                    script_name = main_files[0] if main_files else py_files[0]
                    script_path = os.path.join(s_dir, script_name)
                    break

        if not script_path:
            return (
                f"### ❌ No Execution Script\n\nThe skill **/{skill_name}** does not contain any executable Python scripts.",
                skill.role
            )

        # Run script in a subprocess asynchronously
        try:
            loop = asyncio.get_event_loop()
            cmd = ["python3", script_path] + arguments
            
            # Run from DataEngine root so scripts (e.g., analyze_trace.py)
            # write their output reports to a consistent location (os.getcwd()).
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=workspace_root
                )
            )
            stdout = result.stdout
            stderr = result.stderr
        except Exception as e:
            return (
                f"### ❌ Subprocess Execution Failed\n\nFailed to start the skill script. Error: {str(e)}",
                skill.role
            )

        # Perform post-process formatting if a formatter script exists
        formatter_fn = self._load_formatter(skill.path)
        if formatter_fn:
            try:
                formatted_output = formatter_fn(arguments, stdout, stderr)
                return formatted_output, skill.role
            except Exception as e:
                return (
                    f"### ⚠️ Formatting Error\n\nThe skill executed successfully but post-processing failed.\n"
                    f"**Error**: {str(e)}\n\n"
                    f"**Raw Output (stdout)**:\n```\n{stdout}\n```\n"
                    f"**Raw Error (stderr)**:\n```\n{stderr}\n```",
                    skill.role
                )

        # Default fallback: Return raw output
        if result.returncode != 0:
            return (
                f"### ❌ Skill Execution Failed (Exit Code {result.returncode})\n\n"
                f"**stdout**:\n```\n{stdout}\n```\n"
                f"**stderr**:\n```\n{stderr}\n```",
                skill.role
            )
            
        return stdout or "Skill executed successfully with no output.", skill.role

    def _load_formatter(self, skill_dir: str):
        """Dynamically load format_output function from formatter.py if present."""
        formatter_paths = [
            os.path.join(skill_dir, "scripts", "formatter.py"),
            os.path.join(skill_dir, "formatter.py")
        ]
        
        for path in formatter_paths:
            if os.path.exists(path):
                try:
                    spec = importlib.util.spec_from_file_location("skill_formatter", path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "format_output"):
                            return module.format_output
                except Exception as e:
                    print(f"[SkillManager] Failed to load formatter from {path}: {e}")
        return None
