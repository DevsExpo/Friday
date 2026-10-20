# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

from __future__ import annotations

import gettext
import logging
import os
import struct
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger("friday.localization")


def compile_dict_to_mo(data: Dict[str, Any]) -> bytes:
    """
    Compiles a key-value dictionary into standard GNU gettext binary (.mo) format.
    Zero external dependency required. Includes UTF-8 MIME header for Python gettext compatibility.
    """
    full_data: Dict[str, str] = {
        "": "Content-Type: text/plain; charset=UTF-8\n"
    }
    for k, v in data.items():
        if isinstance(k, str) and k != "":
            full_data[k] = str(v) if v is not None else ""

    # GNU gettext requires msgids to be lexicographically sorted for binary search
    keys = sorted(full_data.keys())
    num_strings = len(keys)
    orig_table_offset = 28
    trans_table_offset = orig_table_offset + num_strings * 8

    orig_entries: List[Tuple[int, int]] = []
    trans_entries: List[Tuple[int, int]] = []
    current_offset = trans_table_offset + num_strings * 8

    orig_bytes_list: List[bytes] = []
    for k in keys:
        b = k.encode("utf-8") + b"\x00"
        orig_entries.append((len(b) - 1, current_offset))
        orig_bytes_list.append(b)
        current_offset += len(b)

    trans_bytes_list: List[bytes] = []
    for k in keys:
        b = full_data[k].encode("utf-8") + b"\x00"
        trans_entries.append((len(b) - 1, current_offset))
        trans_bytes_list.append(b)
        current_offset += len(b)

    # Header: Magic, Revision, NumStrings, OrigTabOffset, TransTabOffset, HashTabSize, HashTabOffset
    header = struct.pack(
        "<Iiiiiii",
        0x950412DE,
        0,
        num_strings,
        orig_table_offset,
        trans_table_offset,
        0,
        0,
    )
    orig_table = b"".join(struct.pack("<ii", length, offset) for length, offset in orig_entries)
    trans_table = b"".join(struct.pack("<ii", length, offset) for length, offset in trans_entries)

    return header + orig_table + trans_table + b"".join(orig_bytes_list) + b"".join(trans_bytes_list)


class LazyLangDict(Mapping):
    """
    Lightweight dict-like mapping for Friday.all_lang_strings to preserve 100%
    backwards compatibility for plugins (e.g. help.py) without loading catalogs into RAM.
    """

    def __init__(self, manager: LocalizationManager) -> None:
        self._manager = manager

    def __getitem__(self, lang: str) -> Dict[str, Any]:
        info = self._manager.available_languages.get(lang)
        if not info:
            raise KeyError(lang)
        return {
            "language": lang,
            "def": info.get("def", lang),
        }

    def __iter__(self):
        return iter(self._manager.available_languages)

    def __len__(self) -> int:
        return len(self._manager.available_languages)

    def __contains__(self, key: object) -> bool:
        return key in self._manager.available_languages

    def keys(self):
        return self._manager.available_languages.keys()

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._manager.available_languages:
            return self[key]
        return default


class LocalizationManager:
    """
    Enterprise-grade Hybrid GNU gettext + Two-Tier Lazy Loading manager.
    - Compiles YAML files into .mo binary tables on modification.
    - Loads ONLY the active language and English fallback into memory.
    - Employs a frozenset fast-path gate for O(1) non-key rejection.
    - Supports dynamic language switching with instant memory freeing.
    """

    def __init__(self, locales_dir: Path) -> None:
        self.locales_dir = Path(locales_dir).resolve()
        self.compiled_dir = self.locales_dir / "compiled"
        self.selected_lang: str = "english"
        self.available_languages: Dict[str, Dict[str, Any]] = {}
        self._valid_keys: frozenset[str] = frozenset()
        self._active_translation: gettext.NullTranslations = gettext.NullTranslations()
        self._fallback_translation: gettext.NullTranslations = gettext.NullTranslations()
        self.all_lang_strings: LazyLangDict = LazyLangDict(self)

    def setup_sync(self) -> None:
        """Scan, compile missing/updated YAMLs, and load base fallback and selected language."""
        self.compiled_dir.mkdir(parents=True, exist_ok=True)
        all_keys: Set[str] = set()

        if not self.locales_dir.exists():
            logger.warning(f"Locales directory does not exist: {self.locales_dir}")
            return

        for filepath in self.locales_dir.glob("*.y*ml"):
            if filepath.name.startswith("."):
                continue

            # Fast header metadata scan (avoids parsing entire YAML unless outdated)
            lang_name = filepath.stem
            def_name = lang_name
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for _ in range(5):
                        line = f.readline()
                        if not line:
                            break
                        if line.startswith("language:"):
                            lang_name = line.split(":", 1)[1].strip().strip("\"'")
                        elif line.startswith("def:"):
                            def_name = line.split(":", 1)[1].strip().strip("\"'")
            except Exception:
                pass

            if lang_name == "template":
                continue

            mo_name = f"{lang_name}.mo"
            mo_path = self.compiled_dir / mo_name
            needs_compile = not mo_path.exists() or mo_path.stat().st_mtime < filepath.stat().st_mtime

            if needs_compile:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.error(f"Failed to parse YAML {filepath}: {e}")
                    continue

                if not isinstance(data, dict):
                    continue

                lang_name = data.get("language", lang_name)
                def_name = data.get("def", def_name)

                try:
                    mo_bytes = compile_dict_to_mo(data)
                    with open(mo_path, "wb") as f_out:
                        f_out.write(mo_bytes)
                    logger.info(f"Compiled localization {filepath.name} -> {mo_name} ({len(mo_bytes)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to compile {filepath} to .mo: {e}")
                    continue

                for k in data.keys():
                    if isinstance(k, str) and k:
                        all_keys.add(k)

            # Canonical mapping
            self.available_languages[lang_name] = {
                "name": lang_name,
                "def": def_name,
                "mo_file": self.compiled_dir / f"{lang_name}.mo",
                "yaml_file": filepath,
            }

        # Load English fallback translation
        en_mo = self.compiled_dir / "english.mo"
        if en_mo.exists():
            try:
                with open(en_mo, "rb") as fp:
                    self._fallback_translation = gettext.GNUTranslations(fp)
                    if hasattr(self._fallback_translation, "_catalog"):
                        all_keys.update(self._fallback_translation._catalog.keys())
            except Exception as e:
                logger.error(f"Failed to load English fallback translation: {e}")

        self._valid_keys = frozenset(all_keys)

        # Set default active language
        self.set_language(self.selected_lang)

    def set_language(self, lang: str) -> bool:
        """
        Dynamically activate a language catalog.
        Frees previously active translation from heap to maintain low memory usage.
        """
        lang = lang.lower() if lang else "english"
        if lang not in self.available_languages and lang != "english":
            logger.warning(f"Language '{lang}' is not available. Falling back to english.")
            lang = "english"

        self.selected_lang = lang

        if lang == "english":
            self._active_translation = self._fallback_translation
            return True

        mo_path = self.compiled_dir / f"{lang}.mo"
        if not mo_path.exists():
            logger.warning(f"Compiled .mo not found for {lang} at {mo_path}. Using fallback.")
            self._active_translation = self._fallback_translation
            return False

        try:
            with open(mo_path, "rb") as fp:
                active_trans = gettext.GNUTranslations(fp)
                if hasattr(active_trans, "_catalog"):
                    # Fast update keys if any new locale-specific keys exist
                    if not self._valid_keys.issuperset(active_trans._catalog.keys()):
                        self._valid_keys = self._valid_keys.union(active_trans._catalog.keys())
                # Chain English fallback
                active_trans.add_fallback(self._fallback_translation)
                self._active_translation = active_trans
            return True
        except Exception as e:
            logger.error(f"Failed loading {lang}.mo: {e}")
            self._active_translation = self._fallback_translation
            return False

    def get_string(
        self,
        keyword: str,
        *args: Any,
        string_args: Any = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        O(1) string retrieval with fast non-key rejection and parameter formatting.
        """
        if not isinstance(keyword, str) or not keyword:
            return None

        # Fast gate: if keyword contains spaces or is not in catalog keys, instantly reject
        if " " in keyword or keyword not in self._valid_keys:
            return None

        # Lookup in active translation (with automatic fallback to English via gettext)
        str_ing = self._active_translation.gettext(keyword)
        if str_ing == keyword:
            # Check if key really existed with its own value == keyword
            has_in_active = (
                hasattr(self._active_translation, "_catalog")
                and keyword in self._active_translation._catalog
            )
            has_in_fallback = (
                hasattr(self._fallback_translation, "_catalog")
                and keyword in self._fallback_translation._catalog
            )
            if not has_in_active and not has_in_fallback:
                return None

        # Format parameters if provided
        fmt_args = string_args if string_args is not None else (args if args else None)
        if fmt_args is not None or kwargs:
            try:
                if fmt_args is not None and kwargs:
                    return (
                        str_ing.format(*fmt_args, **kwargs)
                        if isinstance(fmt_args, (list, tuple))
                        else str_ing.format(fmt_args, **kwargs)
                    )
                elif fmt_args is not None:
                    return (
                        str_ing.format(*fmt_args)
                        if isinstance(fmt_args, (list, tuple))
                        else str_ing.format(fmt_args)
                    )
                elif kwargs:
                    return str_ing.format(**kwargs)
            except Exception:
                return str_ing

        return str_ing
