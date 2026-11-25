#!/usr/bin/env python3
"""Kontrollerar strukturen i ett Home Assistant-repo.

Tre sorters repo, en kontroll:

  integration  custom_components/<domän>/manifest.json
  app          repository.yaml + <app>/config.yaml
  config       configuration.yaml

Körs av .github/workflows/ha-structure.yml. Arbetsflödet bär med sig den här
koden, så det finns alltid en källa. Den ligger här för läsning, och för att
tools/verify-structure.sh ska kunna köra exakt samma kod lokalt.

Avslutar 1 vid fel. Varningar fäller inte körningen.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SECRET_LITERAL = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY)"
)
SECRET_FILES = {"secrets.yaml", ".env"}
SECRET_FILE_EXCEPTIONS = {
    "secrets.fake.yaml",
    "secrets.yaml.tmpl",
    "fakesecrets.yaml",
    ".env.example",
}
SKIP_DIRS = {
    ".git",
    ".storage",
    ".venv",
    ".venv-ci",
    "node_modules",
    "build",
    "__pycache__",
}
ARCHIVED_TOP_DIRS = {"legacy", "agent-archive", "archive"}

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001 - vi rapporterar felet, inte typen
        error(f"{path}: ogiltig JSON: {exc}")
        return None
    if not isinstance(data, dict):
        error(f"{path}: förväntade ett JSON-objekt")
        return None
    return data


def load_yaml(path: str) -> dict | None:
    try:
        import yaml
    except ImportError:
        warn(f"{path}: pyyaml saknas, djupkontrollen hoppades över")
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        error(f"{path}: ogiltig YAML: {exc}")
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        error(f"{path}: förväntade en YAML-mappning")
        return None
    return data


def walk_files(base: str, suffixes: tuple[str, ...]):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(suffixes):
                yield os.path.join(dirpath, name)


def tracked_files(root: str) -> list[str] | None:
    """Filerna git känner till, eller None om det inte är ett git-repo.

    Att gå igenom katalogen fungerar inte här: HomeLab har SMB-monteringar och
    arkiv i trädet, och en kontroll ska bara se det som faktiskt är commitat.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", root, "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in result.stdout.decode("utf-8", "replace").split("\0") if p]


def check_secret_files(root: str) -> None:
    """Samma spärr som i varje repo: en hemlig fil får aldrig vara commitad.

    Undantaget är `legacy/` och det agenten arkiverat: där ligger gammalt
    material som flyttas ut, och det ska synas som en notis i stället för att
    fälla hela kontrollen för alla andra ändringar.
    """
    paths = tracked_files(root)
    if paths is None:
        paths = [rel(root, path) for path in walk_files(root, ("",))]
    for path in paths:
        name = os.path.basename(path)
        if name in SECRET_FILE_EXCEPTIONS:
            continue
        if not (
            name in SECRET_FILES
            or name.startswith(".env.")
            or name.endswith((".pem", ".key", ".p12", ".pfx"))
            or ".tfstate" in name
        ):
            continue
        if path.split("/")[0] in ARCHIVED_TOP_DIRS:
            warn(f"{path}: hemlig fil i arkiverat material")
        else:
            error(f"{path}: hemlig fil är commitad")


def check_secret_literals(root: str, path: str) -> None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return
    for match in SECRET_LITERAL.finditer(text):
        error(
            f"{rel(root, path)}: ser ut som en riktig hemlighet ({match.group(1)[:8]}…)"
        )


def check_integration(root: str) -> None:
    base = os.path.join(root, "custom_components")
    found: list[tuple[str, str]] = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            manifest = os.path.join(base, name, "manifest.json")
            if os.path.isfile(manifest):
                found.append((name, manifest))

    if not found:
        error("custom_components/<domän>/manifest.json saknas")
        return

    for folder, manifest_path in found:
        label = rel(root, manifest_path)
        data = load_json(manifest_path)
        if data is None:
            continue

        for key in ("domain", "name", "version", "codeowners", "documentation"):
            if not data.get(key):
                error(f"{label}: '{key}' saknas")

        if data.get("domain") and data["domain"] != folder:
            error(f"{label}: domain '{data['domain']}' matchar inte mappen '{folder}'")

        version = str(data.get("version") or "")
        if version and not SEMVER.match(version):
            error(f"{label}: version '{version}' är inte semver (X.Y.Z)")

        integration_dir = os.path.dirname(manifest_path)
        flow = os.path.join(integration_dir, "config_flow.py")
        if data.get("config_flow") and not os.path.isfile(flow):
            error(f"{label}: config_flow: true men config_flow.py saknas")
        if os.path.isfile(flow) and not data.get("config_flow"):
            error(f"{label}: config_flow.py finns men manifest saknar config_flow: true")

        for requirement in data.get("requirements") or []:
            if not re.search(r"[=~<>!]", str(requirement)):
                warn(f"{label}: kravet '{requirement}' är inte versionerat")

        strings = os.path.join(integration_dir, "strings.json")
        if os.path.isfile(strings):
            load_json(strings)

        translations = os.path.join(integration_dir, "translations")
        if os.path.isdir(translations):
            for path in walk_files(translations, (".json",)):
                load_json(path)

        services = os.path.join(integration_dir, "services.yaml")
        if os.path.isfile(services):
            load_yaml(services)

        check_secret_literals(root, manifest_path)

    hacs = os.path.join(root, "hacs.json")
    if os.path.isfile(hacs):
        data = load_json(hacs)
        if data is not None and not data.get("name"):
            error(f"{rel(root, hacs)}: 'name' saknas")
    else:
        warn("hacs.json saknas (behövs bara om komponenten ska installeras via HACS)")


def check_app(root: str) -> None:
    repository = os.path.join(root, "repository.yaml")
    if not os.path.isfile(repository):
        error("repository.yaml saknas (app-repots rot)")
    else:
        data = load_yaml(repository)
        if data is not None and not data.get("name"):
            error(f"{rel(root, repository)}: 'name' saknas")

    apps: list[tuple[str, str]] = []
    for name in sorted(os.listdir(root)):
        if name.startswith("."):
            continue
        config = os.path.join(root, name, "config.yaml")
        if os.path.isfile(config):
            apps.append((name, config))

    if not apps:
        error("hittar inga appar: ingen <mapp>/config.yaml")
        return

    slugs: dict[str, str] = {}
    for folder, config_path in apps:
        label = rel(root, config_path)
        data = load_yaml(config_path)
        if data is None:
            continue

        for key in ("name", "version", "slug", "description", "arch"):
            if not data.get(key):
                error(f"{label}: '{key}' saknas")

        version = str(data.get("version") or "")
        if version and not SEMVER.match(version):
            error(f"{label}: version '{version}' är inte semver (X.Y.Z)")

        slug = str(data.get("slug") or "")
        if slug:
            if not SLUG.match(slug):
                error(f"{label}: slug '{slug}' får bara innehålla a-z, 0-9, _ och -")
            if slug in slugs:
                error(f"{label}: slug '{slug}' används också av '{slugs[slug]}'")
            else:
                slugs[slug] = folder

        app_dir = os.path.dirname(config_path)
        if not os.path.isfile(os.path.join(app_dir, "Dockerfile")) and not data.get(
            "build"
        ):
            warn(f"{label}: varken Dockerfile eller build")

        options = data.get("options") or {}
        schema = data.get("schema") or {}
        if isinstance(schema, dict) and isinstance(options, dict):
            for key in options:
                if key not in schema:
                    error(f"{label}: options.{key} beskrivs inte i schema")
            for key in schema:
                if key not in options:
                    warn(f"{label}: schema.{key} har ingen standard i options")

        check_secret_literals(root, config_path)
        for path in walk_files(app_dir, (".json",)):
            if f"{os.sep}rootfs{os.sep}" in path:
                continue
            load_json(path)


def check_config(root: str) -> None:
    bases: list[str] = []
    if os.path.isfile(os.path.join(root, "configuration.yaml")):
        bases.append(root)
    shared = os.path.join(root, "homeassistant", "base", "configuration.yaml")
    if os.path.isfile(shared):
        bases.append(os.path.dirname(shared))

    if not bases:
        error("configuration.yaml saknas")
        return

    secret_names: set[str] = set()
    for base in bases:
        for path in walk_files(base, (".yaml", ".yml")):
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            secret_names.update(re.findall(r"!secret\s+([A-Za-z0-9_]+)", text))

    if not secret_names:
        return

    candidates = [
        os.path.join(root, "homeassistant", "ci", "secrets.fake.yaml"),
        os.path.join(root, "ci", "secrets.fake.yaml"),
        os.path.join(root, "secrets.fake.yaml"),
        os.path.join(root, "fakesecrets.yaml"),
        os.path.join(root, "secrets.yaml.tmpl"),
    ]
    placeholder = next((c for c in candidates if os.path.isfile(c)), None)
    if placeholder is None:
        error(
            "!secret används men ingen platshållarfil finns "
            "(homeassistant/ci/secrets.fake.yaml)"
        )
        return

    data = load_yaml(placeholder)
    if data is None:
        return

    missing = sorted(secret_names - set(data))
    if missing:
        error(
            f"{rel(root, placeholder)}: platshållare saknas för: {', '.join(missing)}"
        )


def detect(root: str) -> str | None:
    base = os.path.join(root, "custom_components")
    if os.path.isdir(base) and any(
        os.path.isfile(os.path.join(base, name, "manifest.json"))
        for name in os.listdir(base)
    ):
        return "integration"
    if os.path.isfile(os.path.join(root, "repository.yaml")):
        return "app"
    if os.path.isfile(os.path.join(root, "configuration.yaml")) or os.path.isfile(
        os.path.join(root, "homeassistant", "base", "configuration.yaml")
    ):
        return "config"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Kontroll av HA-repots struktur")
    parser.add_argument("--root", default=".", help="repo som ska kontrolleras")
    parser.add_argument(
        "--kind",
        default="auto",
        choices=("auto", "integration", "app", "config"),
        help="vilken sorts repo det är; auto avgör själv",
    )
    parser.add_argument("--json", action="store_true", help="maskinläsbart resultat")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"Kontroll: {root} finns inte", file=sys.stderr)
        return 2

    kind = args.kind
    if kind == "auto":
        kind = detect(root) or ""
        if not kind:
            print(
                f"Kontroll: kan inte avgöra sort för {root} "
                "(ingen custom_components, repository.yaml eller configuration.yaml)",
                file=sys.stderr,
            )
            return 2

    {"integration": check_integration, "app": check_app, "config": check_config}[kind](
        root
    )
    check_secret_files(root)

    if args.json:
        json.dump(
            {"root": root, "kind": kind, "errors": errors, "warnings": warnings},
            sys.stdout,
            indent=2,
        )
        print()
        return 1 if errors else 0

    print(f"Struktur: {kind} i {root}")
    if os.environ.get("GITHUB_ACTIONS"):
        for message in errors:
            print(f"::error::{message}")
        for message in warnings:
            print(f"::warning::{message}")
    else:
        for message in errors:
            print(f"FEL   {message}")
        for message in warnings:
            print(f"NOTIS {message}")

    if errors:
        print(f"{len(errors)} fel, {len(warnings)} notiser")
    else:
        print(f"OK — 0 fel, {len(warnings)} notiser")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
