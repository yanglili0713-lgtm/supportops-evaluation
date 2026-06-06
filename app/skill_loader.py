from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SKILLS_DIR = Path("skills")


@dataclass(frozen=True)
class SkillDocument:
    skill_name: str
    path: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


def list_skills(skills_dir: str | Path = DEFAULT_SKILLS_DIR) -> list[dict]:
    root = Path(skills_dir)
    if not root.exists():
        return []

    skills = []
    for path in sorted(root.glob("*/SKILL.md")):
        skills.append(
            SkillDocument(
                skill_name=path.parent.name,
                path=str(path),
                content=path.read_text(encoding="utf-8"),
            ).to_dict()
        )
    return skills


def get_skill(skill_name: str, skills_dir: str | Path = DEFAULT_SKILLS_DIR) -> dict | None:
    path = Path(skills_dir) / skill_name / "SKILL.md"
    if not path.exists():
        return None
    return SkillDocument(
        skill_name=skill_name,
        path=str(path),
        content=path.read_text(encoding="utf-8"),
    ).to_dict()
