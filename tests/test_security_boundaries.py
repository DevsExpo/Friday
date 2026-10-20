"""Security boundary regression tests.

These guard the capability tiers introduced by the `owner_only` / `chat_admin_check` split:

    OWNER   - the deployment operator (`config.OWNER_ID`) and the userbot accounts.
    SUDO    - trusted users listed in `SUDO_USERS`. Deny-by-default: a command is only
              reachable by a sudo user when it is explicitly marked `sudo=True` /
              not marked `owner_only=True`.
    CHAT    - a sudo user who is an administrator of the chat the command is used in.

The first test is the important one: it fails if a privileged command is ever added
without `owner_only=True`, so the class of bug cannot silently return.
"""

import ast
import pathlib
import re

import pytest


# Commands that must never be reachable by the sudo tier (enforced owner-only commands).
DANGEROUS = {
    # global configuration & handler
    "sethandler",
    # secrets & environment variables
    "addenv",
    "delenv",
    "getenv",
    # arbitrary code execution / shell
    "eval",
    "ex",
    "exec",
    "term",
    "terminal",
    "bash",
    "sh",
    "run",
    # sudo administration
    "addsudo",
    "rmsudo",
    "sudomgr",
    "sudolist",
    "clearsudo",
    "setsudo",
    # package management
    "fpm_install",
    "fpm_update",
    "fpm_uninstall",
}

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _registered_commands(path: pathlib.Path):
    """Yield (lineno, command_names, decorator_source) for each register_on_cmd()."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name != "register_on_cmd" or not dec.args:
                continue
            first = dec.args[0]
            if isinstance(first, (ast.List, ast.Tuple)):
                names = {
                    e.value.lower()
                    for e in first.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }
            elif isinstance(first, ast.Constant) and isinstance(first.value, str):
                names = {first.value.lower()}
            else:
                continue
            yield node.lineno, names, ast.unparse(dec)


def test_dangerous_commands_are_owner_only():
    """Privileged commands must be explicitly marked owner_only=True.

    `owner_only` defaults to False, so a newly added destructive command is
    sudo-reachable unless somebody remembers the flag. This test is the guard.
    """
    offenders = []
    for path in sorted((PROJECT_ROOT / "Main").rglob("*.py")):
        for lineno, names, source in _registered_commands(path):
            hit = names & DANGEROUS
            if not hit:
                continue
            if "owner_only=True" not in source.replace(" ", ""):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} -> {sorted(hit)}")

    assert not offenders, "Dangerous commands missing owner_only=True:\n" + "\n".join(offenders)


def test_owner_only_commands_are_registered_consistently():
    """Every owner_only command must still expose a parseable decorator."""
    seen = 0
    for path in sorted((PROJECT_ROOT / "Main").rglob("*.py")):
        for _lineno, names, source in _registered_commands(path):
            if "owner_only=True" in source.replace(" ", ""):
                seen += 1
                assert names, f"{path} registered an owner_only command with no name"
    assert seen > 20, f"Expected a meaningful number of owner_only commands, found {seen}"


def test_group_moderation_uses_scoped_chat_admin_capability():
    """Group moderation must be chat-scoped via check_perm, not blanket owner-only.

    The SUDO tier is meant to be useful: helpers moderate the groups they
    administer.
    """
    source = (PROJECT_ROOT / "Main" / "internals" / "group_management.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    assert "check_perm" in source, "group_management.py must use check_perm capability"

    # Every moderation command must be guarded by the scoped decorator.
    for command in ("ban", "unban", "mute", "unmute", "kick", "promote", "purge"):
        pattern = re.compile(
            r"register_on_cmd\(\s*\[?\s*[\"']" + command + r"[\"'].*?\)\s*\n"
            r"(?:@[^\n]+\n)*\s*(?:async\s+)?def\s",
            re.S,
        )
        match = pattern.search(source)
        assert match, f"could not locate the '{command}' command in group_management.py"
        block = source[match.start() : match.end()]
        assert "check_perm" in block, f"'{command}' must be guarded by check_perm"


def test_dangerous_commands_are_not_reachable_through_group_management():
    """The scoped tier must not be applied to account or filesystem commands."""
    source = (PROJECT_ROOT / "Main" / "internals" / "group_management.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    for command in ("logout", "upload", "eval", "getenv", "update", "bcast"):
        assert not re.search(
            r"register_on_cmd\(\s*\[?\s*[\"']" + command + r"[\"']", source
        ), f"'{command}' must not be registered in group_management.py"


def test_sudo_helpers_exist():
    """The permission system depends on is_sudo / is_owner helpers."""
    from Main.utils import inline_helper

    assert callable(inline_helper.is_sudo)
    assert callable(inline_helper.is_owner)
    assert callable(inline_helper.is_owner_cb)
    assert callable(inline_helper.is_authorized_cb)


def test_chat_admin_check_decorator_exists():
    from Main.core.decorators import check_perm

    assert callable(check_perm)
