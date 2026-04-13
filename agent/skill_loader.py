"""
skill_loader.py - Download skills from S3 into .claude/skills/ before agent runs.

S3 structure:
    s3://qdojo-skill-files-costco/skills/{session_id}/{skill_name}/SKILL.md
    s3://qdojo-skill-files-costco/skills/{session_id}/{skill_name}/config.json
    ...

Local target:
    .claude/skills/{skill_name}/SKILL.md
    .claude/skills/{skill_name}/config.json
    ...
"""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Callable, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger("SKILL_LOADER")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
S3_BUCKET  = os.environ.get("S3_SKILL_BUCKET", "qdojo-skill-files-costco")
S3_PREFIX  = os.environ.get("S3_SKILL_PREFIX", "skills")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-west-2"))

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR   = PROJECT_ROOT / ".claude" / "skills"

# ---------------------------------------------------------------------------
# Pretty printer — writes to stdout AND calls optional WebSocket emitter
# ---------------------------------------------------------------------------

def _print(msg: str, emit: Optional[Callable] = None) -> None:
    """Print to console and optionally forward as a skill_log event."""
    print(msg, flush=True)
    logger.info(msg)
    if emit:
        emit({"type": "skill_log", "text": msg})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_skills_for_session(
    session_id: str,
    emit: Optional[Callable] = None,
) -> List[str]:
    """
    Download all skills for a given session from S3 into .claude/skills/.
    Falls back to local skills if S3 is unreachable or folder is empty.

    Args:
        session_id : S3 folder name under the configured prefix.
        emit       : Optional callback(event_dict) to forward log events
                     to a WebSocket/queue in real time.

    Returns:
        List of skill names that are now ready in .claude/skills/.
    """
    sep  = "=" * 58
    sep2 = "-" * 58
    prefix = f"{S3_PREFIX}/{session_id}/"

    _print("", emit)
    _print(sep, emit)
    _print("  SKILL LOADER — STARTING", emit)
    _print(sep, emit)
    _print(f"  Session ID  : {session_id}", emit)
    _print(f"  S3 Bucket   : {S3_BUCKET}", emit)
    _print(f"  S3 Path     : s3://{S3_BUCKET}/{prefix}", emit)
    _print(f"  Local Target: {SKILLS_DIR}", emit)
    _print(sep2, emit)

    t0 = time.time()

    try:
        _print("", emit)
        _print("  Step 1: Connecting to AWS S3 ...", emit)
        s3 = boto3.client("s3", region_name=AWS_REGION)
        _print(f"  -> Connected  (region: {AWS_REGION})", emit)

        _print("", emit)
        _print(f"  Step 2: Scanning s3://{S3_BUCKET}/{prefix} ...", emit)
        skill_names = _discover_skills(s3, prefix, emit)

        if not skill_names:
            _print("", emit)
            _print("  -> No skills found in S3 for this session.", emit)
            _print("  -> Falling back to existing local skills.", emit)
            local = _list_local_skills()
            _print_summary(local, source="local", elapsed=time.time() - t0, emit=emit)
            return local

        _print(f"  -> Discovered {len(skill_names)} skill(s): {skill_names}", emit)

        _print("", emit)
        _print("  Step 3: Downloading skill files from S3 ...", emit)
        downloaded = _download_skills(s3, prefix, skill_names, emit)

        _print("", emit)
        _print("  Step 4: Activating skills in .claude/skills/ ...", emit)
        _activate_skills(downloaded, emit)

        _print_summary(list(downloaded.keys()), source="S3", elapsed=time.time() - t0, emit=emit)
        return sorted(downloaded.keys())

    except NoCredentialsError:
        _print("", emit)
        _print("  [ERROR] AWS credentials not found!", emit)
        _print("  -> Set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY in .env", emit)
        _print("  -> Falling back to local skills.", emit)
        local = _list_local_skills()
        _print_summary(local, source="local (fallback)", elapsed=time.time() - t0, emit=emit)
        return local

    except ClientError as e:
        code = e.response["Error"]["Code"]
        _print("", emit)
        _print(f"  [ERROR] S3 ClientError: {code} — {e}", emit)
        _print("  -> Falling back to local skills.", emit)
        local = _list_local_skills()
        _print_summary(local, source="local (fallback)", elapsed=time.time() - t0, emit=emit)
        return local

    except Exception as e:
        _print("", emit)
        _print(f"  [ERROR] Unexpected: {e}", emit)
        _print("  -> Falling back to local skills.", emit)
        local = _list_local_skills()
        _print_summary(local, source="local (fallback)", elapsed=time.time() - t0, emit=emit)
        return local


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _discover_skills(s3_client, prefix: str, emit: Optional[Callable]) -> List[str]:
    """List all skill sub-folders under the session prefix."""
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix, Delimiter="/")

    skills = []
    for page in pages:
        for cp in page.get("CommonPrefixes", []):
            # cp["Prefix"] = skills/{session_id}/{skill_name}/
            skill_name = cp["Prefix"].rstrip("/").split("/")[-1]
            _print(f"     Found skill folder: {skill_name}", emit)
            skills.append(skill_name)

    return sorted(skills)


def _download_skills(
    s3_client,
    prefix: str,
    skill_names: List[str],
    emit: Optional[Callable],
) -> dict:
    """
    Download all files for each skill.
    Returns { skill_name: [list of local file paths] }
    """
    result = {}

    for skill_name in skill_names:
        skill_prefix = f"{prefix}{skill_name}/"
        _print("", emit)
        _print(f"     Skill: [{skill_name}]", emit)
        _print(f"     S3   : s3://{S3_BUCKET}/{skill_prefix}", emit)

        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=skill_prefix)

        files = []
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                size_kb = round(obj["Size"] / 1024, 1)

                # relative path from session root
                rel = key[len(prefix):]          # {skill_name}/file.md
                if not rel or rel.endswith("/"):
                    continue

                local_path = SKILLS_DIR / rel
                local_path.parent.mkdir(parents=True, exist_ok=True)

                _print(f"       Downloading: {rel}  ({size_kb} KB)", emit)
                s3_client.download_file(S3_BUCKET, key, str(local_path))
                _print(f"       -> Saved to: {local_path}", emit)
                files.append(local_path)

        result[skill_name] = files
        _print(f"     [{skill_name}] — {len(files)} file(s) downloaded", emit)

    return result


def _activate_skills(downloaded: dict, emit: Optional[Callable]) -> None:
    """
    Read each downloaded skill's SKILL.md and confirm it's ready.
    This is the 'loading into .claude' step.
    """
    for skill_name, files in downloaded.items():
        skill_dir = SKILLS_DIR / skill_name
        skill_md  = skill_dir / "SKILL.md"

        _print("", emit)
        _print(f"     Activating: {skill_name}", emit)
        _print(f"     Location  : {skill_dir}", emit)

        file_names = [f.name for f in files]
        _print(f"     Files     : {', '.join(file_names)}", emit)

        if skill_md.exists():
            # Read first line of SKILL.md as a description
            first_line = skill_md.read_text(encoding="utf-8").splitlines()[0].strip("#").strip()
            _print(f"     SKILL.md  : \"{first_line[:80]}\"", emit)

        _print(f"     Status    : ACTIVE — ready for agent", emit)


def _print_summary(
    skill_names: List[str],
    source: str,
    elapsed: float,
    emit: Optional[Callable],
) -> None:
    sep  = "=" * 58
    sep2 = "-" * 58
    _print("", emit)
    _print(sep2, emit)
    _print("  SKILL LOADER — COMPLETE", emit)
    _print(sep2, emit)
    _print(f"  Source        : {source}", emit)
    _print(f"  Skills ready  : {len(skill_names)}", emit)
    for name in skill_names:
        skill_dir = SKILLS_DIR / name
        file_count = len(list(skill_dir.glob("*"))) if skill_dir.exists() else 0
        _print(f"    -> {name}  ({file_count} files)", emit)
    _print(f"  Time taken    : {elapsed:.2f}s", emit)
    _print(f"  Agent starts  : NOW", emit)
    _print(sep, emit)
    _print("", emit)


def _list_local_skills() -> List[str]:
    """Return skill names already present in .claude/skills/."""
    if not SKILLS_DIR.exists():
        return []
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir())
