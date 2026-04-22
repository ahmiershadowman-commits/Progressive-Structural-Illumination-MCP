"""Source intake normalization and provenance audit helpers."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import ArtifactSnapshot, ArtifactType, SourceObject
from ..utils import unique_preserve_order

WINDOWS_PATH_PATTERN = r"[A-Za-z]:\\[^\r\n\"']+"
POSIX_PATH_PATTERN = r"(?<![A-Za-z]:)(/(?:[^\s\"']+/)+[^\s\"',.;:!?]+)"
TRAILING_PATH_PUNCTUATION = ".,;:!?)]}"


def _clean_path_candidate(candidate: str) -> str:
    return candidate.strip().strip("\"'").rstrip(TRAILING_PATH_PUNCTUATION)


def _extract_path_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for line in text.splitlines():
        windows_match = re.search(r"[A-Za-z]:\\", line)
        if windows_match:
            candidates.append(_clean_path_candidate(line[windows_match.start():]))
        candidates.extend(_clean_path_candidate(match) for match in re.findall(POSIX_PATH_PATTERN, line))
    return unique_preserve_order(candidate for candidate in candidates if candidate)


def _candidate_paths(source: SourceObject) -> list[str]:
    candidates: list[str] = []
    metadata = source.metadata or {}
    for value in metadata.get("path_candidates", []):
        if isinstance(value, str) and value:
            candidates.append(value)
    if candidates:
        return unique_preserve_order(candidates)[:8]
    for raw in (source.locator, source.title, metadata.get("first_line", "")):
        if not raw:
            continue
        candidates.extend(_extract_path_candidates(raw))
    return unique_preserve_order(candidates)[:8]


def _normalize_source(
    source: SourceObject,
    canonical_id: str,
    duplicate_of: str,
    artifact_types: set[ArtifactType],
) -> SourceObject:
    metadata = dict(source.metadata)
    issues: list[str] = []
    filesystem_checks: list[dict[str, object]] = []
    for candidate in _candidate_paths(source):
        exists = Path(candidate).exists()
        filesystem_checks.append({"path": candidate, "exists": exists})
        if not exists:
            issues.append(f"stale_reference:{candidate}")
            issues.append(f"missing_artifact:{candidate}")
    if not source.locator:
        issues.append("missing_locator")
    if duplicate_of:
        issues.append(f"duplicate_content:{duplicate_of}")
    if ArtifactType.SOURCE_REGISTER not in artifact_types:
        issues.append("unsynced_source_register")
    metadata.update(
        {
            "audit_issues": unique_preserve_order(issues),
            "filesystem_checks": filesystem_checks,
            "duplicate_of": duplicate_of,
            "path_candidates": _candidate_paths(source),
            "canonical_reason": "highest-priority non-duplicate source" if source.id == canonical_id else "",
        }
    )
    return source.model_copy(
        update={
            "canonical": source.id == canonical_id,
            "metadata": metadata,
        }
    )


def audit_source_objects(
    source_objects: list[SourceObject],
    artifacts: list[ArtifactSnapshot] | None = None,
) -> tuple[list[SourceObject], dict[str, object]]:
    artifacts = artifacts or []
    if not source_objects:
        return [], {
            "source_count": 0,
            "canonical_source_id": "",
            "duplicates": 0,
            "stale_references": 0,
            "missing_artifacts": 0,
            "issues": ["no_sources"],
        }

    artifact_types = {artifact.artifact_type for artifact in artifacts}
    content_index: dict[str, list[str]] = {}
    for source in source_objects:
        content_index.setdefault(source.content_hash or source.id, []).append(source.id)
    priority = {
        "context": 0,
        "task": 1,
        "diff": 2,
        "test_failure": 3,
        "draft": 4,
    }
    canonical_source = sorted(
        source_objects,
        key=lambda source: (
            priority.get(source.source_kind.value, 99),
            1 if content_index.get(source.content_hash or source.id, [source.id])[0] != source.id else 0,
            0 if _candidate_paths(source) else 1,
            source.title.lower(),
        ),
    )[0]

    audited: list[SourceObject] = []
    duplicate_count = 0
    stale_reference_count = 0
    missing_artifact_count = 0
    for source in source_objects:
        duplicates = content_index.get(source.content_hash or source.id, [])
        duplicate_of = ""
        if len(duplicates) > 1:
            duplicate_count += 1
            duplicate_of = next(candidate for candidate in duplicates if candidate != source.id)
        normalized = _normalize_source(
            source=source,
            canonical_id=canonical_source.id,
            duplicate_of=duplicate_of,
            artifact_types=artifact_types,
        )
        audit_issues = normalized.metadata.get("audit_issues", [])
        stale_reference_count += sum(1 for issue in audit_issues if str(issue).startswith("stale_reference:"))
        missing_artifact_count += sum(1 for issue in audit_issues if str(issue).startswith("missing_artifact:"))
        audited.append(normalized)

    return audited, {
        "source_count": len(audited),
        "canonical_source_id": canonical_source.id,
        "duplicates": duplicate_count,
        "stale_references": stale_reference_count,
        "missing_artifacts": missing_artifact_count,
        "issues": unique_preserve_order(
            issue
            for source in audited
            for issue in source.metadata.get("audit_issues", [])
        ),
    }
