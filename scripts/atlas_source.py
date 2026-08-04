#!/usr/bin/env python3
"""Deterministic Atlas source artifact assembly."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import unicodedata
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

import atlas_quality
import atlas_state
import atlas_transaction
from atlas_url import normalize_canonical_url, source_id_for


VERSION = 1
ARTIFACT_PREFIX = "summaries/sources/artifacts/"
FRONTMATTER_KEYS = (
    "schema_version",
    "note_type",
    "managed_by",
    "source_id",
    "source_seq",
    "canonical_url",
    "source_kind",
    "title",
    "author",
    "publisher",
    "published",
    "primary_domain",
    "subdomains",
    "secondary_domains",
    "canonical_tags",
    "candidate_terms",
    "routing_status",
    "routed_at",
    "first_seen",
    "last_checked",
    "last_summarized",
    "refresh_after",
    "content_hash",
    "acquired_by",
    "acquisition_run",
    "coverage",
    "confidence",
    "evidence_strength",
    "practicality",
    "stability",
    "reuse_value",
    "recommended_posture",
)
LIST_FRONTMATTER_KEYS = {
    "subdomains",
    "secondary_domains",
    "canonical_tags",
    "candidate_terms",
}


def _validate_frontmatter_shapes(values: Mapping[str, str]) -> None:
    if values.get("schema_version") != "1":
        raise SourceError("frontmatter schema_version must be the unquoted integer 1")
    source_seq = values.get("source_seq", "")
    if re.fullmatch(r"0|[1-9]\d*", source_seq) is None:
        raise SourceError(
            "frontmatter source_seq must be an unquoted non-negative integer"
        )
    for key in LIST_FRONTMATTER_KEYS:
        raw = values.get(key, "")
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"frontmatter {key} must be a JSON array of strings"
            ) from exc
        if not isinstance(items, list) or any(
            not isinstance(item, str) for item in items
        ):
            raise SourceError(f"frontmatter {key} must be a JSON array of strings")


ROUTE_STATUSES = {"unrouted", "routed", "no-topic-match", "routing-blocked"}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")


class SourceError(ValueError):
    """A source artifact violates the canonical contract."""



_WORKER_SCHEMA_RESOURCE = "worker"
_PROPOSAL_SCHEMA_RESOURCE = "proposal"
_CHECKLIST_IDS = tuple(atlas_quality.CHECKLIST_IDS)


def project_worker_transport_schema(
    worker_schema: Mapping[str, Any],
    proposal_schema: Mapping[str, Any],
) -> dict[str, Any]:
    """Project canonical worker schemas into a finite native-output schema."""

    invalid_detail = "worker transport schema assets are invalid"
    removable_metadata = frozenset(
        {"$anchor", "$dynamicAnchor", "$id", "$schema", "$vocabulary"}
    )
    unsupported_reference_keywords = frozenset(
        {"$dynamicRef", "$recursiveAnchor", "$recursiveRef"}
    )
    try:
        worker = copy.deepcopy(worker_schema)
        proposal = copy.deepcopy(proposal_schema)
        if not isinstance(worker, Mapping) or not isinstance(proposal, Mapping):
            raise ValueError(invalid_detail)

        resources: dict[str, Mapping[str, Any]] = {
            _WORKER_SCHEMA_RESOURCE: worker,
            _PROPOSAL_SCHEMA_RESOURCE: proposal,
        }

        def mapping(value: Any) -> Mapping[str, Any]:
            if not isinstance(value, Mapping):
                raise ValueError(invalid_detail)
            return value

        def reject_unsupported(node: Any, active: set[int]) -> None:
            if isinstance(node, Mapping):
                marker = id(node)
                if marker in active:
                    raise ValueError(invalid_detail)
                active.add(marker)
                if unsupported_reference_keywords & set(node):
                    raise ValueError(invalid_detail)
                for child in node.values():
                    reject_unsupported(child, active)
                active.remove(marker)
            elif isinstance(node, list):
                marker = id(node)
                if marker in active:
                    raise ValueError(invalid_detail)
                active.add(marker)
                for child in node:
                    reject_unsupported(child, active)
                active.remove(marker)

        reject_unsupported(worker, set())
        reject_unsupported(proposal, set())

        worker_defs = mapping(worker.get("$defs"))
        mapping(proposal.get("$defs"))
        expected_variants = [
            "#/$defs/ready",
            "#/$defs/needs_input",
            "#/$defs/expanded",
            "#/$defs/no_write",
        ]
        worker_variants = worker.get("oneOf")
        if (
            not isinstance(worker_variants, list)
            or len(worker_variants) != len(expected_variants)
            or [
                item.get("$ref") if isinstance(item, Mapping) else None
                for item in worker_variants
            ]
            != expected_variants
            or any(
                not isinstance(item, Mapping) or set(item) != {"$ref"}
                for item in worker_variants
            )
        ):
            raise ValueError(invalid_detail)

        checklist = mapping(worker_defs.get("checklist"))
        if (
            checklist.get("type") != "array"
            or checklist.get("minItems") != len(_CHECKLIST_IDS)
            or checklist.get("maxItems") != len(_CHECKLIST_IDS)
            or checklist.get("items") is not False
        ):
            raise ValueError(invalid_detail)
        prefix_items = checklist.get("prefixItems")
        checklist_item = mapping(worker_defs.get("checklist_item"))
        if (
            not isinstance(prefix_items, list)
            or len(prefix_items) != len(_CHECKLIST_IDS)
            or not isinstance(checklist_item.get("properties"), Mapping)
        ):
            raise ValueError(invalid_detail)
        for index, item in enumerate(prefix_items):
            item_mapping = mapping(item)
            if set(item_mapping) != {"allOf"}:
                raise ValueError(invalid_detail)
            refinements = item_mapping["allOf"]
            if not isinstance(refinements, list) or len(refinements) != 2:
                raise ValueError(invalid_detail)
            base_ref, id_refinement = refinements
            if (
                not isinstance(base_ref, Mapping)
                or set(base_ref) != {"$ref"}
                or base_ref.get("$ref") != "#/$defs/checklist_item"
            ):
                raise ValueError(invalid_detail)
            id_refinement_mapping = mapping(id_refinement)
            if set(id_refinement_mapping) != {"properties"}:
                raise ValueError(invalid_detail)
            id_properties = id_refinement_mapping["properties"]
            if (
                not isinstance(id_properties, Mapping)
                or set(id_properties) != {"id"}
            ):
                raise ValueError(invalid_detail)
            id_schema = id_properties.get("id")
            if (
                not isinstance(id_schema, Mapping)
                or set(id_schema) != {"const"}
                or id_schema.get("const") != _CHECKLIST_IDS[index]
            ):
                raise ValueError(invalid_detail)

        def resolve_ref(
            resource_name: str, reference: Any
        ) -> tuple[Any, str, str]:
            if not isinstance(reference, str):
                raise ValueError(invalid_detail)
            target_resource = resource_name
            pointer = reference
            if reference == "source-summary-proposal.schema.json":
                if resource_name != _WORKER_SCHEMA_RESOURCE:
                    raise ValueError(invalid_detail)
                target_resource = _PROPOSAL_SCHEMA_RESOURCE
                pointer = "#"
            elif reference.startswith("source-summary-proposal.schema.json#"):
                if resource_name != _WORKER_SCHEMA_RESOURCE:
                    raise ValueError(invalid_detail)
                target_resource = _PROPOSAL_SCHEMA_RESOURCE
                pointer = reference.removeprefix("source-summary-proposal.schema.json")
            if pointer == "#":
                return resources[target_resource], target_resource, pointer
            if not pointer.startswith("#/$defs/"):
                raise ValueError(invalid_detail)
            definition_name = pointer.removeprefix("#/$defs/")
            if (
                not definition_name
                or "/" in definition_name
                or "~" in definition_name
            ):
                raise ValueError(invalid_detail)
            definitions = resources[target_resource].get("$defs")
            if not isinstance(definitions, Mapping):
                raise ValueError(invalid_detail)
            if definition_name not in definitions:
                raise ValueError(invalid_detail)
            return definitions[definition_name], target_resource, pointer

        def scan_refs(
            node: Any,
            resource_name: str,
            stack: tuple[tuple[str, str], ...],
            active: set[int],
        ) -> None:
            if isinstance(node, Mapping):
                marker = id(node)
                if marker in active:
                    raise ValueError(invalid_detail)
                active.add(marker)
                if "$ref" in node:
                    if set(node) != {"$ref"}:
                        raise ValueError(invalid_detail)
                    target, target_resource, target_pointer = resolve_ref(
                        resource_name, node["$ref"]
                    )
                    key = (target_resource, target_pointer)
                    if key in stack:
                        raise ValueError(invalid_detail)
                    scan_refs(target, target_resource, stack + (key,), active)
                else:
                    for child in node.values():
                        scan_refs(child, resource_name, stack, active)
                active.remove(marker)
            elif isinstance(node, list):
                marker = id(node)
                if marker in active:
                    raise ValueError(invalid_detail)
                active.add(marker)
                for child in node:
                    scan_refs(child, resource_name, stack, active)
                active.remove(marker)

        scan_refs(worker, _WORKER_SCHEMA_RESOURCE, (), set())
        scan_refs(proposal, _PROPOSAL_SCHEMA_RESOURCE, (), set())

        def expand(
            node: Any,
            resource_name: str,
            pointer: str,
            stack: tuple[tuple[str, str], ...],
        ) -> Any:
            if isinstance(node, list):
                return [
                    expand(item, resource_name, pointer, stack) for item in node
                ]
            if not isinstance(node, Mapping):
                return node
            if "$ref" in node:
                if set(node) != {"$ref"}:
                    raise ValueError(invalid_detail)
                target, target_resource, target_pointer = resolve_ref(
                    resource_name, node["$ref"]
                )
                key = (target_resource, target_pointer)
                if key in stack:
                    raise ValueError(invalid_detail)
                if (
                    target_resource == _WORKER_SCHEMA_RESOURCE
                    and target_pointer == "#/$defs/checklist"
                ):
                    return expand_checklist(
                        target,
                        target_resource,
                        target_pointer,
                        stack + (key,),
                    )
                return expand(target, target_resource, target_pointer, stack + (key,))
            if "allOf" in node or unsupported_reference_keywords & set(node):
                raise ValueError(invalid_detail)
            result: dict[str, Any] = {}
            for key, value in node.items():
                if key in removable_metadata or key == "$defs":
                    continue
                result[key] = expand(value, resource_name, pointer, stack)
            return result

        def expand_checklist(
            node: Any,
            resource_name: str,
            pointer: str,
            stack: tuple[tuple[str, str], ...],
        ) -> dict[str, Any]:
            checklist_node = mapping(node)
            concrete_items: list[dict[str, Any]] = []
            for index, item in enumerate(checklist_node["prefixItems"]):
                refinements = mapping(item)["allOf"]
                base_ref, _ = refinements
                base, base_resource, base_pointer = resolve_ref(
                    resource_name, base_ref["$ref"]
                )
                concrete = mapping(
                    expand(
                        base,
                        base_resource,
                        base_pointer,
                        stack + ((base_resource, base_pointer),),
                    )
                )
                properties = mapping(concrete["properties"])
                concrete_item = dict(concrete)
                concrete_properties = dict(properties)
                concrete_properties["id"] = {
                    **dict(mapping(properties["id"])),
                    "const": _CHECKLIST_IDS[index],
                }
                concrete_item["properties"] = concrete_properties
                concrete_items.append(concrete_item)
            result: dict[str, Any] = {}
            for key, value in checklist_node.items():
                if key in removable_metadata or key in {"$defs", "prefixItems"}:
                    continue
                result[key] = expand(value, resource_name, pointer, stack)
            result["prefixItems"] = concrete_items
            return result

        projected = expand(worker, _WORKER_SCHEMA_RESOURCE, "#", ())

        def assert_transport_shape(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    assert_transport_shape(item)
                return
            if not isinstance(node, Mapping):
                return
            if any(
                marker in node
                for marker in removable_metadata
                | unsupported_reference_keywords
                | {"$defs", "$ref", "allOf"}
            ):
                raise ValueError(invalid_detail)
            for value in node.values():
                assert_transport_shape(value)

        assert_transport_shape(projected)
        projected_mapping = mapping(projected)
        def variant_kind(node: Any) -> Any:
            if not isinstance(node, Mapping):
                return None
            properties = node.get("properties")
            if not isinstance(properties, Mapping):
                return None
            kind = properties.get("kind")
            if not isinstance(kind, Mapping):
                return None
            return kind.get("const")

        def checklist_id(node: Any) -> Any:
            if not isinstance(node, Mapping):
                return None
            properties = node.get("properties")
            if not isinstance(properties, Mapping):
                return None
            identifier = properties.get("id")
            if not isinstance(identifier, Mapping):
                return None
            return identifier.get("const")
        variants = projected_mapping.get("oneOf")
        if not isinstance(variants, list) or len(variants) != len(expected_variants):
            raise ValueError(invalid_detail)
        kinds = {variant_kind(item) for item in variants}
        if kinds != {"ready", "needs-input", "expanded", "no-write"}:
            raise ValueError(invalid_detail)
        ready = next(
            (item for item in variants if variant_kind(item) == "ready"),
            None,
        )
        if not isinstance(ready, Mapping):
            raise ValueError(invalid_detail)
        ready_properties = ready.get("properties")
        if not isinstance(ready_properties, Mapping):
            raise ValueError(invalid_detail)
        evidence_bundle = ready_properties.get("evidence_bundle")
        if (
            not isinstance(evidence_bundle, Mapping)
            or evidence_bundle.get("additionalProperties") is not True
        ):
            raise ValueError(invalid_detail)
        checklist_output = ready_properties.get("checklist")
        if not isinstance(checklist_output, Mapping):
            raise ValueError(invalid_detail)
        prefix_items_output = checklist_output.get("prefixItems")
        if not isinstance(prefix_items_output, list):
            raise ValueError(invalid_detail)
        if (
            len(prefix_items_output) != len(_CHECKLIST_IDS)
            or any(
                checklist_id(item) != _CHECKLIST_IDS[index]
                for index, item in enumerate(prefix_items_output)
            )
        ):
            raise ValueError(invalid_detail)
        return dict(projected_mapping)
    except SourceError:
        raise
    except (
        TypeError,
        ValueError,
        KeyError,
        IndexError,
        OverflowError,
        RecursionError,
    ) as exc:
        raise SourceError(invalid_detail) from exc


@dataclass(frozen=True)
class ParsedArtifact:
    values: dict[str, str]
    body: str


def parse_artifact(text: str) -> ParsedArtifact:
    if not isinstance(text, str):
        raise SourceError("artifact text must be a string")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        raise SourceError("artifact frontmatter is missing")
    boundary = normalized.find("\n---\n", 4)
    if boundary < 0:
        raise SourceError("artifact frontmatter is unterminated")
    values: dict[str, str] = {}
    list_items: dict[str, list[str]] = {}
    last_key: str | None = None
    for line in normalized[4:boundary].splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith(("  - ", "\t- ")):
            if last_key not in LIST_FRONTMATTER_KEYS or values.get(last_key) != "":
                raise SourceError(f"invalid frontmatter line: {line}")
            raw_item = line.split("-", 1)[1].strip()
            if not raw_item:
                raise SourceError(f"invalid frontmatter line: {line}")
            if raw_item.startswith('"'):
                try:
                    item = json.loads(raw_item)
                except json.JSONDecodeError as exc:
                    raise SourceError(f"invalid frontmatter line: {line}") from exc
                if not isinstance(item, str):
                    raise SourceError(f"invalid frontmatter line: {line}")
            elif len(raw_item) >= 2 and raw_item[0] == raw_item[-1] == "'":
                item = raw_item[1:-1].replace("''", "'")
            else:
                item = raw_item
            list_items.setdefault(last_key, []).append(item)
            continue
        if line[:1].isspace():
            raise SourceError(f"invalid frontmatter line: {line}")
        key, separator, raw = line.partition(":")
        if not separator or not key or key in values:
            raise SourceError(f"invalid frontmatter line: {line}")
        values[key] = raw.strip()
        last_key = key
    for key in LIST_FRONTMATTER_KEYS:
        if values.get(key) == "":
            items = list_items.get(key)
            if not items:
                raise SourceError(f"frontmatter {key} block sequence is empty")
            values[key] = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    missing = set(FRONTMATTER_KEYS) - set(values)
    unknown = set(values) - set(FRONTMATTER_KEYS)
    if missing or unknown:
        raise SourceError(
            f"artifact frontmatter keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    _validate_frontmatter_shapes(values)
    body = normalized[boundary + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    return ParsedArtifact(values, body)


def scalar(values: Mapping[str, str], key: str) -> str:
    raw = values[key]
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"frontmatter {key} is not a valid quoted scalar"
            ) from exc
        if not isinstance(value, str):
            raise SourceError(f"frontmatter {key} must be text")
        return value
    return raw


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_artifact(values: Mapping[str, str], body: str) -> str:
    missing = set(FRONTMATTER_KEYS) - set(values)
    unknown = set(values) - set(FRONTMATTER_KEYS)
    if missing or unknown:
        raise SourceError(
            f"render frontmatter keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    _validate_frontmatter_shapes(values)
    normalized_body = body.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    frontmatter = "\n".join(f"{key}: {values[key]}" for key in FRONTMATTER_KEYS)
    return f"---\n{frontmatter}\n---\n\n{normalized_body}\n"


_PROPOSAL_METADATA_KEYS = {
    "title",
    "author",
    "publisher",
    "published",
    "source_kind",
}
_PROPOSAL_ASSESSMENT_KEYS = {
    "coverage",
    "confidence",
    "evidence_strength",
    "practicality",
    "stability",
    "reuse_value",
    "recommended_posture",
}
_CALLER_CONTEXT_KEYS = {
    "note_type",
    "managed_by",
    "primary_domain",
    "subdomains",
    "secondary_domains",
    "canonical_tags",
    "candidate_terms",
    "routed_at",
    "last_checked",
    "last_summarized",
    "refresh_after",
    "acquired_by",
    "acquisition_run",
}


def _require_exact_keys(
    value: Any,
    expected: set[str],
    name: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise SourceError(f"{name} has invalid keys")
    return value


def _require_proposal(
    proposal: Mapping[str, Any],
) -> tuple[
    Mapping[str, Any],
    Mapping[str, Any],
    list[Mapping[str, Any]],
    list[Mapping[str, Any]],
]:
    proposal_value = _require_exact_keys(
        proposal,
        {"version", "metadata", "assessment", "claims", "links"},
        "proposal",
    )
    if proposal_value["version"] != VERSION:
        raise SourceError("proposal.version must be 1")
    metadata = _require_exact_keys(
        proposal_value["metadata"], _PROPOSAL_METADATA_KEYS, "proposal.metadata"
    )
    assessment = _require_exact_keys(
        proposal_value["assessment"],
        _PROPOSAL_ASSESSMENT_KEYS,
        "proposal.assessment",
    )
    if any(not isinstance(value, str) or not value for value in metadata.values()):
        raise SourceError("proposal.metadata values must be nonempty text")
    published = metadata["published"]
    if (
        published != "Unknown"
        and re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", published) is None
    ):
        raise SourceError("proposal.metadata.published is invalid")
    if metadata["source_kind"] not in {
        "article",
        "paper",
        "repo",
        "thread",
        "video",
        "docs",
        "other",
    }:
        raise SourceError("proposal.metadata.source_kind is invalid")
    if any(not isinstance(value, str) or not value for value in assessment.values()):
        raise SourceError("proposal.assessment values must be nonempty text")

    claims_value = proposal_value["claims"]
    if not isinstance(claims_value, list) or not claims_value:
        raise SourceError("proposal.claims must be a nonempty array")
    claims: list[Mapping[str, Any]] = []
    for index, claim_value in enumerate(claims_value):
        claim = _require_exact_keys(
            claim_value,
            {"statement", "evidence"},
            f"proposal.claims[{index}]",
        )
        statement = claim["statement"]
        evidence_value = claim["evidence"]
        if not isinstance(statement, str) or not statement:
            raise SourceError(f"proposal.claims[{index}].statement is invalid")
        if not isinstance(evidence_value, list) or not evidence_value:
            raise SourceError(f"proposal.claims[{index}].evidence is invalid")
        for evidence_index, evidence_value_item in enumerate(evidence_value):
            evidence = _require_exact_keys(
                evidence_value_item,
                {"locator", "ledger_id"},
                f"proposal.claims[{index}].evidence[{evidence_index}]",
            )
            if any(
                not isinstance(value, str) or not value for value in evidence.values()
            ):
                raise SourceError(
                    f"proposal.claims[{index}].evidence[{evidence_index}] is invalid"
                )
        claims.append(claim)

    links_value = proposal_value["links"]
    if not isinstance(links_value, list) or not links_value:
        raise SourceError("proposal.links must be a nonempty array")
    links: list[Mapping[str, Any]] = []
    for index, link_value in enumerate(links_value):
        link = _require_exact_keys(
            link_value,
            {"url", "relation", "locator", "ledger_id"},
            f"proposal.links[{index}]",
        )
        if (
            not isinstance(link["url"], str)
            or re.fullmatch(r"https?://\S+", link["url"]) is None
            or link["relation"] not in {"canonical", "related", "cited"}
            or not isinstance(link["locator"], str)
            or not link["locator"]
            or not isinstance(link["ledger_id"], str)
            or not link["ledger_id"]
        ):
            raise SourceError(f"proposal.links[{index}] is invalid")
        links.append(link)
    return metadata, assessment, claims, links


def render_summary_proposal(
    proposal: Mapping[str, Any],
    *,
    caller_context: Mapping[str, Any],
    source_state: Mapping[str, Any],
) -> str:
    """Render a validated semantic proposal with caller and reducer-owned fields."""
    metadata, assessment, claims, links = _require_proposal(proposal)
    context = _require_exact_keys(
        caller_context, _CALLER_CONTEXT_KEYS, "caller_context"
    )
    if context["note_type"] != "source-summary" or context["managed_by"] != "atlas":
        raise SourceError("caller_context note ownership is invalid")
    for key in (
        "primary_domain",
        "routed_at",
        "last_checked",
        "last_summarized",
        "refresh_after",
        "acquired_by",
        "acquisition_run",
    ):
        if not isinstance(context[key], str):
            raise SourceError(f"caller_context.{key} is invalid")
    for key in (
        "subdomains",
        "secondary_domains",
        "canonical_tags",
        "candidate_terms",
    ):
        if not isinstance(context[key], list) or any(
            not isinstance(value, str) for value in context[key]
        ):
            raise SourceError(f"caller_context.{key} is invalid")
    for key in ("last_checked", "last_summarized", "refresh_after"):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", context[key]) is None:
            raise SourceError(f"caller_context.{key} is invalid")
    if context["acquired_by"] not in {"manual", "acquisition-run", "research-acquire"}:
        raise SourceError("caller_context.acquired_by is invalid")

    source_id = _require_state(source_state, "source_id", str)
    canonical_url = _require_state(source_state, "canonical_url", str)
    content_hash = _require_state(source_state, "content_hash", str)
    first_seen = _require_state(source_state, "first_seen", str)
    route_status = _require_state(source_state, "route_status", str)
    source_seq = source_state.get("source_seq")
    if type(source_seq) is not int or source_seq < 0:
        raise SourceError("source_state.source_seq has invalid type")
    if (
        SOURCE_ID_RE.fullmatch(source_id) is None
        or normalize_canonical_url(canonical_url) != canonical_url
        or source_id_for(canonical_url) != source_id
        or HASH_RE.fullmatch(content_hash) is None
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}", first_seen) is None
        or route_status not in ROUTE_STATUSES
    ):
        raise SourceError("source_state identity is invalid")
    routed_at = context["routed_at"]
    if route_status == "unrouted":
        if routed_at:
            raise SourceError("unrouted source cannot have routed_at")
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", routed_at) is None:
        raise SourceError("terminal route status requires routed_at")

    values = {
        "schema_version": "1",
        "note_type": quoted(context["note_type"]),
        "managed_by": quoted(context["managed_by"]),
        "source_id": quoted(source_id),
        "source_seq": str(source_seq),
        "canonical_url": quoted(canonical_url),
        "source_kind": quoted(metadata["source_kind"]),
        "title": quoted(metadata["title"]),
        "author": quoted(metadata["author"]),
        "publisher": quoted(metadata["publisher"]),
        "published": quoted(metadata["published"]),
        "primary_domain": quoted(context["primary_domain"]),
        "subdomains": json.dumps(
            context["subdomains"], ensure_ascii=False, separators=(",", ":")
        ),
        "secondary_domains": json.dumps(
            context["secondary_domains"], ensure_ascii=False, separators=(",", ":")
        ),
        "canonical_tags": json.dumps(
            context["canonical_tags"], ensure_ascii=False, separators=(",", ":")
        ),
        "candidate_terms": json.dumps(
            context["candidate_terms"], ensure_ascii=False, separators=(",", ":")
        ),
        "routing_status": quoted(route_status),
        "routed_at": quoted(routed_at),
        "first_seen": quoted(first_seen),
        "last_checked": quoted(context["last_checked"]),
        "last_summarized": quoted(context["last_summarized"]),
        "refresh_after": quoted(context["refresh_after"]),
        "content_hash": quoted(content_hash),
        "acquired_by": quoted(context["acquired_by"]),
        "acquisition_run": quoted(context["acquisition_run"]),
        **{key: quoted(assessment[key]) for key in _PROPOSAL_ASSESSMENT_KEYS},
    }
    claim_lines = [f"- {claim['statement']}" for claim in claims]
    evidence_lines = [
        f"- **{evidence['locator']}**: {claim['statement']} [ledger: `{evidence['ledger_id']}`]"
        for claim in claims
        for evidence in claim["evidence"]
    ]
    link_lines = [
        f"- {link['relation'].title()}: {link['url']} — "
        f"{link['locator']} [ledger: `{link['ledger_id']}`]"
        for link in links
    ]
    locators = ", ".join(
        dict.fromkeys(
            str(evidence["locator"])
            for claim in claims
            for evidence in claim["evidence"]
        )
    )
    assessment_notes = {
        "coverage": f"The proposal is bounded to source evidence at {locators}.",
        "confidence": f"The claim at {locators} directly supports the summary.",
        "evidence_strength": f"{locators} provides a source-local claim and locator.",
        "practicality": f"The recorded claim at {locators} states the usable mechanism.",
        "stability": f"The captured source bytes are bound by content hash {content_hash[:12]}.",
        "reuse_value": f"The claim at {locators} answers a bounded source question.",
        "recommended_posture": (
            f"The evidence at {locators} supports the recorded "
            f"{assessment['recommended_posture']} posture."
        ),
    }
    assessment_labels = {
        "coverage": "Coverage",
        "confidence": "Confidence",
        "evidence_strength": "Evidence strength",
        "practicality": "Practicality",
        "stability": "Stability",
        "reuse_value": "Reuse value",
        "recommended_posture": "Recommended posture",
    }
    classification_lines = [
        f"- Primary domain: `{context['primary_domain']}`",
        "- Subdomains: "
        + (
            ", ".join(f"`{value}`" for value in context["subdomains"])
            if context["subdomains"]
            else "none recorded"
        ),
        "- Secondary domains: "
        + (
            ", ".join(f"`{value}`" for value in context["secondary_domains"])
            if context["secondary_domains"]
            else "none recorded"
        ),
        "- Canonical tags: "
        + (
            ", ".join(f"`{value}`" for value in context["canonical_tags"])
            if context["canonical_tags"]
            else "none recorded"
        ),
    ]
    caveat = (
        "The proposal is partial and does not establish claims outside the listed evidence."
        if assessment["coverage"] != "complete"
        else "The proposal establishes only the source-local claims bound to the listed evidence locators."
    )
    routing_lines = [
        f"- Route status: `{route_status}`.",
        f"- Routed at: {routed_at}." if routed_at else "- Routed at: not yet routed.",
        "- Candidate terms: "
        + (
            ", ".join(f"`{value}`" for value in context["candidate_terms"])
            if context["candidate_terms"]
            else "none recorded"
        ),
    ]
    reuse_lines = [
        f"- What evidence does the source give for this claim: {claim['statement']}"
        for claim in claims
    ]
    body = "\n".join(
        [
            f"# {metadata['title']}",
            "",
            f"**Source**: [{metadata['title']}]({canonical_url})  ",
            f"**Source ID**: `{source_id}`  ",
            f"**Source seq**: `{source_seq}`  ",
            f"**Kind**: `{metadata['source_kind']}`  ",
            f"**Author**: {metadata['author']}  ",
            f"**Publisher**: {metadata['publisher']}  ",
            f"**Published**: {metadata['published']}  ",
            f"**First seen**: {first_seen}  ",
            f"**Last checked**: {context['last_checked']}  ",
            f"**Last summarized**: {context['last_summarized']}  ",
            f"**Refresh after**: {context['refresh_after']}  ",
            f"**Route status**: `{route_status}`",
            "",
            f"> **TL;DR**: {claims[0]['statement']}",
            "",
            "## Assessment",
            "",
            "| Signal | Value | Notes |",
            "|---|---|---|",
            *[
                f"| {assessment_labels[key]} | `{assessment[key]}` | {assessment_notes[key]} |"
                for key in (
                    "coverage",
                    "confidence",
                    "evidence_strength",
                    "practicality",
                    "stability",
                    "reuse_value",
                    "recommended_posture",
                )
            ],
            "",
            "## Classification",
            "",
            *classification_lines,
            "",
            "## Key points",
            "",
            *claim_lines,
            "",
            "## Evidence / examples",
            "",
            *evidence_lines,
            "",
            "## Caveats / open questions",
            "",
            f"- {caveat}",
            "",
            "## Routing notes",
            "",
            *routing_lines,
            "",
            "## Reuse cues",
            "",
            *reuse_lines,
            "",
            "## Links",
            "",
            f"- Canonical: {canonical_url}",
            *link_lines,
        ]
    )
    return render_artifact(values, body)


def _replace_header(body: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^\*\*{re.escape(label)}\*\*:.*$", re.MULTILINE)
    replacement = f"**{label}**: {value}"
    updated, count = pattern.subn(lambda _: replacement, body)
    if count != 1:
        raise SourceError(f"artifact body must contain one rendered {label} field")
    return updated


def resolve_effective_content_hash(bundle: Mapping[str, Any]) -> str:
    """Return the effective content hash for one evidence bundle.

    Delegates to `atlas_quality.resolve_effective_content_hash` so source assembly
    and quality validation share one text-hash and projection owner. Raises
    SourceError when the envelope is invalid, incomplete, or not text-backed.
    """
    effective, findings = atlas_quality.resolve_effective_content_hash(bundle)
    if findings or effective is None:
        detail = findings[0].code if findings else "EVIDENCE_PAYLOAD_TEXT_INVALID"
        if findings and findings[0].detail:
            detail = f"{detail}: {findings[0].detail}"
        raise SourceError(f"evidence identity invalid: {detail}")
    return effective


def classify_hash_transition(
    previous_content_hash: str | None,
    evidence_bundle: Mapping[str, Any],
) -> str:
    """Return `same-hash` or `changed-hash` from proven text evidence only.

    Inaccessible, empty, media-backed, unbacked projection, or otherwise unproven
    evidence raises SourceError and is a no-write result—never a guessed transition.
    `hash_baseline_migration` is a reporting reason only and is not returned here.
    """
    effective = resolve_effective_content_hash(evidence_bundle)
    if previous_content_hash is None:
        return "changed-hash"
    if (
        not isinstance(previous_content_hash, str)
        or HASH_RE.fullmatch(previous_content_hash) is None
    ):
        raise SourceError("previous content_hash is invalid")
    return "same-hash" if previous_content_hash == effective else "changed-hash"


def _evidence_identity(bundle: Mapping[str, Any]) -> dict[str, str]:
    canonical_url = bundle.get("canonical_url")
    payload = bundle.get("payload_text")
    first_seen = bundle.get("first_seen", bundle.get("fetched_at"))
    if (
        not isinstance(canonical_url, str)
        or not isinstance(payload, str)
        or not isinstance(first_seen, str)
    ):
        raise SourceError(
            "evidence bundle lacks canonical_url, payload_text, or first_seen/fetched_at"
        )
    if payload == "":
        raise SourceError("evidence payload_text is empty")
    normalized = normalize_canonical_url(canonical_url)
    if normalized != canonical_url:
        raise SourceError("evidence canonical_url is not normalized")
    content_hash = resolve_effective_content_hash(bundle)
    return {
        "canonical_url": canonical_url,
        "source_id": source_id_for(canonical_url),
        "content_hash": content_hash,
        "first_seen": first_seen,
    }


def _require_state(
    source_state: Mapping[str, Any], name: str, expected_type: type
) -> Any:
    value = source_state.get(name)
    if not isinstance(value, expected_type):
        raise SourceError(f"source_state.{name} has invalid type")
    return value


def merge_artifact(
    staged_artifact_text: str,
    evidence_bundle: Mapping[str, Any],
    event: Mapping[str, Any],
    source_state: Mapping[str, Any],
    *,
    living_artifact_text: str | None = None,
    fresh_capture: bool = False,
) -> str:
    """Assemble one canonical source artifact from a selected staged artifact."""
    if event.get("type") != "source-upsert":
        raise SourceError("merge-artifact requires a source-upsert event")
    staged = parse_artifact(staged_artifact_text)
    evidence = _evidence_identity(evidence_bundle)
    created = _require_state(source_state, "created", bool)
    source_seq = _require_state(source_state, "source_seq", int)
    state_source_id = _require_state(source_state, "source_id", str)
    state_url = _require_state(source_state, "canonical_url", str)
    state_hash = _require_state(source_state, "content_hash", str)
    state_first_seen = _require_state(source_state, "first_seen", str)
    route_status = _require_state(source_state, "route_status", str)
    if route_status not in ROUTE_STATUSES:
        raise SourceError("source_state.route_status is invalid")
    event_source_id = event.get("source_id")
    event_url = event.get("canonical_url")
    event_hash = event.get("content_hash")
    if not isinstance(event_source_id, str) or not SOURCE_ID_RE.fullmatch(
        event_source_id
    ):
        raise SourceError("event source_id is invalid")
    if (
        not isinstance(event_url, str)
        or normalize_canonical_url(event_url) != event_url
    ):
        raise SourceError("event canonical_url is invalid")
    if not isinstance(event_hash, str) or not HASH_RE.fullmatch(event_hash):
        raise SourceError("event content_hash is invalid")
    identities = {
        scalar(staged.values, "source_id"),
        evidence["source_id"],
        event_source_id,
        state_source_id,
    }
    urls = {
        scalar(staged.values, "canonical_url"),
        evidence["canonical_url"],
        event_url,
        state_url,
    }
    hashes = {
        scalar(staged.values, "content_hash"),
        evidence["content_hash"],
        event_hash,
        state_hash,
    }
    if len(identities) != 1 or len(urls) != 1 or len(hashes) != 1:
        raise SourceError(
            "staged artifact, evidence, event, and reducer identity disagree"
        )
    if created and {
        scalar(staged.values, "first_seen"),
        evidence["first_seen"],
        str(event.get("first_seen")),
        state_first_seen,
    } != {state_first_seen}:
        raise SourceError("new-source first_seen values disagree")

    living = (
        parse_artifact(living_artifact_text)
        if living_artifact_text is not None
        else None
    )
    if created and living is not None:
        raise SourceError("new-source merge cannot receive a living artifact")
    if not created and living is None:
        raise SourceError("existing-source merge requires a living artifact")
    living_hash = scalar(living.values, "content_hash") if living is not None else None
    content_changed = living_hash is not None and living_hash != event_hash
    if content_changed and not fresh_capture:
        raise SourceError(
            "changed-hash merge requires fresh capture evidence and artifact"
        )

    values = dict(staged.values)
    values["source_id"] = quoted(state_source_id)
    values["source_seq"] = str(source_seq)
    values["canonical_url"] = quoted(state_url)
    values["first_seen"] = quoted(state_first_seen)
    values["last_checked"] = quoted(str(event.get("checked_on")))
    values["last_summarized"] = quoted(str(event.get("summarized_on")))
    values["refresh_after"] = quoted(str(event.get("refresh_after")))
    values["content_hash"] = quoted(state_hash)
    if created:
        values["routing_status"] = quoted("unrouted")
        values["routed_at"] = quoted("")
    else:
        assert living is not None
        values["acquired_by"] = living.values["acquired_by"]
        values["acquisition_run"] = living.values["acquisition_run"]
        if content_changed:
            values["routing_status"] = quoted("unrouted")
            values["routed_at"] = quoted("")
        else:
            values["routing_status"] = quoted(route_status)
            values["routed_at"] = living.values["routed_at"]

    body = staged.body
    body = _replace_header(body, "Source ID", f"`{state_source_id}`")
    body = _replace_header(body, "Source seq", f"`{source_seq}`")
    body = _replace_header(body, "First seen", state_first_seen)
    body = _replace_header(body, "Last checked", str(event.get("checked_on")))
    body = _replace_header(body, "Last summarized", str(event.get("summarized_on")))
    body = _replace_header(body, "Refresh after", str(event.get("refresh_after")))
    body = _replace_header(
        body, "Route status", f"`{scalar(values, 'routing_status')}`"
    )
    return render_artifact(values, body)


def _prepare_finding(code: str, path: str, detail: str = "") -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _normalize_prepare_findings(
    findings: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    unique = {(item["code"], item["path"], item["detail"]) for item in findings}
    return [
        {"code": code, "path": path, "detail": detail}
        for code, path, detail in sorted(
            unique, key=lambda item: (item[1], item[0], item[2])
        )
    ]


def _quality_findings(
    findings: Sequence[atlas_quality.Finding],
) -> list[dict[str, str]]:
    return [_prepare_finding(item.code, item.path, item.detail) for item in findings]

def _worker_checklist_structure_findings(value: Any) -> list[atlas_quality.Finding]:
    """Reject malformed checklist packets while deferring valid failure outcomes."""
    return [
        finding
        for finding in atlas_quality.validate_checklist(value)
        if finding.code != "CHECKLIST_ITEM_FAILED"
    ]


def validate_worker_result(value: Any) -> list[dict[str, str]]:
    """Validate the strict, non-authoritative source worker packet union."""
    findings: list[dict[str, str]] = []
    if not isinstance(value, Mapping):
        return [_prepare_finding("WORKER_PACKET_INVALID", "worker", "expected object")]
    kind = value.get("kind")
    expected_by_kind = {
        "ready": {
            "version",
            "kind",
            "identity",
            "evidence_bundle",
            "evidence_ledger",
            "proposal",
            "checklist",
            "refresh_after",
        },
        "needs-input": {"version", "kind", "identity", "reason", "choices"},
        "expanded": {"version", "kind", "identity", "children"},
        "no-write": {"version", "kind", "identity", "reason"},
    }
    if kind not in expected_by_kind:
        return [_prepare_finding("WORKER_KIND_INVALID", "worker.kind", str(kind))]
    if type(value.get("version")) is not int or value["version"] != VERSION:
        findings.append(
            _prepare_finding(
                "WORKER_VERSION_INVALID", "worker.version", str(value.get("version"))
            )
        )
    if set(value) != expected_by_kind[kind]:
        findings.append(
            _prepare_finding(
                "WORKER_FIELDS_INVALID", "worker", "packet fields are invalid"
            )
        )
    identity = value.get("identity")
    if not isinstance(identity, Mapping) or set(identity) != {
        "canonical_url",
        "source_id",
    }:
        findings.append(
            _prepare_finding(
                "WORKER_IDENTITY_INVALID",
                "worker.identity",
                "identity fields are invalid",
            )
        )
    else:
        canonical_url = identity.get("canonical_url")
        source_id = identity.get("source_id")
        try:
            normalized_url = (
                normalize_canonical_url(canonical_url)
                if isinstance(canonical_url, str)
                else None
            )
        except ValueError as exc:
            findings.append(
                _prepare_finding(
                    "WORKER_IDENTITY_INVALID", "worker.identity.canonical_url", str(exc)
                )
            )
        else:
            if normalized_url != canonical_url or source_id != source_id_for(
                canonical_url
            ):
                findings.append(
                    _prepare_finding(
                        "WORKER_IDENTITY_INVALID",
                        "worker.identity",
                        "canonical URL and source ID disagree",
                    )
                )
    if kind == "ready":
        for name in ("evidence_bundle", "evidence_ledger", "proposal"):
            if not isinstance(value.get(name), Mapping):
                findings.append(
                    _prepare_finding(
                        "WORKER_FIELD_INVALID", f"worker.{name}", "expected object"
                    )
                )
        refresh_after = value.get("refresh_after")
        if not isinstance(refresh_after, str):
            findings.append(
                _prepare_finding(
                    "WORKER_FIELD_INVALID", "worker.refresh_after", "expected date"
                )
            )
        else:
            try:
                date.fromisoformat(refresh_after)
            except ValueError:
                findings.append(
                    _prepare_finding(
                        "WORKER_FIELD_INVALID",
                        "worker.refresh_after",
                        "expected YYYY-MM-DD",
                    )
                )
        findings.extend(
            _quality_findings(
                _worker_checklist_structure_findings(value.get("checklist"))
            )
        )
    elif kind == "needs-input":
        if not isinstance(value.get("reason"), str) or not value["reason"].strip():
            findings.append(
                _prepare_finding(
                    "WORKER_FIELD_INVALID", "worker.reason", "expected nonempty text"
                )
            )
        if value.get("choices") not in (
            ["page-only", "expand", "stop-without-writing"],
            ["replacement-input", "bounded-acquisition", "stop-without-writing"],
        ):
            findings.append(
                _prepare_finding(
                    "WORKER_CHOICES_INVALID",
                    "worker.choices",
                    "choice set is invalid",
                )
            )
    elif kind == "expanded":
        children = value.get("children")
        if not isinstance(children, list) or not children:
            findings.append(
                _prepare_finding(
                    "WORKER_CHILDREN_INVALID",
                    "worker.children",
                    "expected nonempty array",
                )
            )
        else:
            for index, child in enumerate(children):
                if (
                    not isinstance(child, Mapping)
                    or set(child) != {"label", "reference"}
                    or not isinstance(child.get("label"), str)
                    or not child["label"].strip()
                    or not isinstance(child.get("reference"), str)
                    or not child["reference"].strip()
                ):
                    findings.append(
                        _prepare_finding(
                            "WORKER_CHILD_INVALID",
                            f"worker.children[{index}]",
                            "child fields are invalid",
                        )
                    )
    elif not isinstance(value.get("reason"), str) or not value["reason"].strip():
        findings.append(
            _prepare_finding(
                "WORKER_FIELD_INVALID", "worker.reason", "expected nonempty text"
            )
        )
    return _normalize_prepare_findings(findings)


def source_artifact_path(first_seen: str, source_id: str, title: str) -> str:
    """Return the canonical new-source path from façade-owned identity."""
    try:
        parsed_date = date.fromisoformat(first_seen)
    except ValueError as exc:
        raise SourceError("first_seen must be YYYY-MM-DD") from exc
    if not SOURCE_ID_RE.fullmatch(source_id):
        raise SourceError("source_id is invalid")
    if not isinstance(title, str) or not title.strip():
        raise SourceError("proposal title is invalid")
    normalized_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized_title).strip(".-")
    if not slug:
        slug = "source"
    return (
        f"{ARTIFACT_PREFIX}{parsed_date:%Y}/{parsed_date:%Y-%m}/"
        f"{first_seen}--{source_id}--{slug.lower()}.md"
    )


def _summary_context(
    *,
    checked_on: str,
    refresh_after: str,
    source_state: Mapping[str, Any],
    living_artifact_text: str | None,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "note_type": "source-summary",
        "managed_by": "atlas",
        "primary_domain": "",
        "subdomains": [],
        "secondary_domains": [],
        "canonical_tags": [],
        "candidate_terms": [],
        "routed_at": "",
        "last_checked": checked_on,
        "last_summarized": checked_on,
        "refresh_after": refresh_after,
        "acquired_by": "manual",
        "acquisition_run": "",
    }
    if living_artifact_text is None:
        return context
    values = parse_artifact(living_artifact_text).values
    context["primary_domain"] = scalar(values, "primary_domain")
    for key in (
        "subdomains",
        "secondary_domains",
        "canonical_tags",
        "candidate_terms",
    ):
        context[key] = json.loads(values[key])
    context["acquired_by"] = scalar(values, "acquired_by")
    context["acquisition_run"] = scalar(values, "acquisition_run")
    if source_state["route_status"] != "unrouted":
        context["routed_at"] = scalar(values, "routed_at")
    return context


def _source_prepare_rejected(code: str, path: str, detail: str) -> dict[str, Any]:
    return {
        "state": "rejected",
        "findings": [_prepare_finding(code, path, detail)],
    }


def prepare_source(
    documents: Mapping[str, str],
    *,
    canonical_url: str,
    checked_on: str,
    mode: str,
    worker: Any,
    living_artifact_text: str | None,
) -> dict[str, Any]:
    """Prepare one source event and artifact without reading or writing storage."""
    try:
        if normalize_canonical_url(canonical_url) != canonical_url:
            raise SourceError("canonical URL must be normalized")
        date.fromisoformat(checked_on)
    except (TypeError, ValueError) as exc:
        return _source_prepare_rejected(
            "SOURCE_PREPARE_INPUT_INVALID", "identity", str(exc)
        )
    if mode not in {"routine", "resummarize"}:
        return _source_prepare_rejected(
            "SOURCE_PREPARE_INPUT_INVALID", "mode", "mode is invalid"
        )
    state_findings = atlas_state.validate_documents(
        documents["manifest"], documents["topics"], documents["relations"]
    )
    if state_findings:
        return {
            "state": "rejected",
            "findings": _quality_findings(state_findings),
        }
    worker_findings = validate_worker_result(worker)
    if worker_findings:
        return {"state": "rejected", "findings": worker_findings}
    assert isinstance(worker, Mapping)
    source_id = source_id_for(canonical_url)
    identity = worker["identity"]
    if identity["canonical_url"] != canonical_url or identity["source_id"] != source_id:
        return _source_prepare_rejected(
            "WORKER_IDENTITY_MISMATCH",
            "worker.identity",
            "worker identity differs from inventory identity",
        )
    manifest_rows, manifest_findings = atlas_state.validated_manifest_rows(
        documents["manifest"]
    )
    if manifest_findings:
        return {
            "state": "rejected",
            "findings": _quality_findings(manifest_findings),
        }
    existing = next(
        (row for row in manifest_rows if row["Canonical URL"] == canonical_url),
        None,
    )
    if existing is not None and existing["Status"] == "archived":
        return {
            "state": "terminal",
            "outcome": "archived",
            "reason": "source is archived",
        }
    if mode == "resummarize" and existing is None:
        return _source_prepare_rejected(
            "SOURCE_NOT_FOUND", "identity.canonical_url", "resummarize source is absent"
        )
    if mode == "routine" and existing is not None:
        refresh_after = existing["Refresh after"]
        if refresh_after and refresh_after > checked_on:
            return {
                "state": "terminal",
                "outcome": "active-not-due",
                "reason": "source refresh is not due",
            }
    if worker["kind"] == "no-write":
        return {
            "state": "terminal",
            "outcome": "no-write",
            "reason": worker["reason"],
        }
    if worker["kind"] != "ready":
        return _source_prepare_rejected(
            "WORKER_PACKET_NOT_FINAL",
            "worker.kind",
            "source preparation accepts ready or no-write packets",
        )
    checklist_findings = atlas_quality.validate_checklist(worker["checklist"])
    if checklist_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(checklist_findings),
        }
    evidence_bundle = worker["evidence_bundle"]
    effective_evidence: Mapping[str, Any] = evidence_bundle
    if "first_seen" not in evidence_bundle and "fetched_at" not in evidence_bundle:
        effective_evidence = {**evidence_bundle, "first_seen": checked_on}
    try:
        evidence = _evidence_identity(effective_evidence)
    except (TypeError, ValueError, KeyError) as exc:
        return _source_prepare_rejected(
            "EVIDENCE_INVALID", "worker.evidence_bundle", str(exc)
        )
    if evidence["canonical_url"] != canonical_url or evidence["source_id"] != source_id:
        return _source_prepare_rejected(
            "EVIDENCE_IDENTITY_MISMATCH",
            "worker.evidence_bundle",
            "evidence identity differs from inventory identity",
        )
    content_hash = evidence["content_hash"]
    if (
        mode == "routine"
        and existing is not None
        and existing["Content hash"] == content_hash
    ):
        event = {
            "type": "source-upsert",
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": existing["Artifact"],
            "first_seen": existing["First seen"],
            "checked_on": checked_on,
            "summarized_on": existing["Last summarized"],
            "content_hash": content_hash,
            "refresh_after": existing["Refresh after"],
        }
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
        if not any(
            documents[name] != text for name, text in reduction.documents.items()
        ):
            return {
                "state": "terminal",
                "outcome": "unchanged",
                "reason": "source was already checked on this date",
            }
        return {
            "state": "prepared",
            "outcome": "checked-unchanged",
            "route_required": False,
            "event": event,
            "documents": reduction.documents,
            "artifact_text": None,
            "artifact_path": existing["Artifact"],
        }
    proposal_findings = atlas_quality.validate_proposal(
        worker["proposal"], worker["evidence_ledger"]
    )
    if proposal_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(proposal_findings),
        }
    try:
        first_seen = (
            existing["First seen"] if existing is not None else evidence["first_seen"]
        )
        artifact_path = (
            existing["Artifact"]
            if existing is not None
            else source_artifact_path(
                first_seen, source_id, worker["proposal"]["metadata"]["title"]
            )
        )
        event = {
            "type": "source-upsert",
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": artifact_path,
            "first_seen": first_seen,
            "checked_on": checked_on,
            "summarized_on": checked_on,
            "content_hash": content_hash,
            "refresh_after": worker["refresh_after"],
        }
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
        source_state = reduction.derived["source"]
        staged_artifact = render_summary_proposal(
            worker["proposal"],
            caller_context=_summary_context(
                checked_on=checked_on,
                refresh_after=worker["refresh_after"],
                source_state=source_state,
                living_artifact_text=living_artifact_text,
            ),
            source_state=source_state,
        )
        artifact_text = merge_artifact(
            staged_artifact,
            effective_evidence,
            event,
            source_state,
            living_artifact_text=living_artifact_text,
            fresh_capture=bool(
                existing is not None and existing["Content hash"] != content_hash
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _source_prepare_rejected("SOURCE_PREPARE_INVALID", "worker", str(exc))
    summary_findings = atlas_quality.validate_summary(
        artifact_text, effective_evidence, worker["checklist"]
    )
    if summary_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(summary_findings),
        }
    created = bool(source_state["created"])
    content_changed = bool(source_state["content_changed"])
    outcome = (
        "created"
        if created
        else (
            "changed-content-resummarized"
            if mode == "resummarize" and content_changed
            else (
                "materially-refreshed"
                if content_changed
                else "same-content-resummarized"
            )
        )
    )
    return {
        "state": "prepared",
        "outcome": outcome,
        "route_required": created or content_changed,
        "event": event,
        "documents": reduction.documents,
        "artifact_text": artifact_text,
        "artifact_path": artifact_path,
    }


def render_route_artifact(
    artifact_text: str,
    route_event: Mapping[str, Any],
    route_status: str,
) -> str:
    """Render the source artifact side of one validated terminal route-upsert."""
    if route_event.get("type") != "route-upsert":
        raise SourceError("route renderer requires a route-upsert event")
    checked_on = route_event.get("checked_on")
    if not isinstance(checked_on, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", checked_on
    ):
        raise SourceError("route event checked_on is invalid")
    if route_status not in ROUTE_STATUSES - {"unrouted"}:
        raise SourceError("route status must be terminal")
    edges = route_event.get("edges")
    if not isinstance(edges, list):
        raise SourceError("route event edges are invalid")
    reasons: list[str] = []
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise SourceError("route event edge is invalid")
        reason = edge.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise SourceError("route event edge reason is invalid")
        reasons.append(f"- {reason}")

    parsed = parse_artifact(artifact_text)
    values = dict(parsed.values)
    values["routing_status"] = quoted(route_status)
    values["routed_at"] = quoted(checked_on)
    body = _replace_header(parsed.body, "Route status", f"`{route_status}`")
    pattern = re.compile(
        r"(^## Routing notes\n)(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def replace_routing_notes(match: re.Match[str]) -> str:
        lines = [
            line
            for line in match.group(2).splitlines()
            if not line.strip().startswith("- Verifier:")
        ]
        while lines and not lines[-1].strip():
            lines.pop()
        lines.extend(reasons)
        return match.group(1) + "\n".join(lines) + "\n\n"

    body, count = pattern.subn(replace_routing_notes, body)
    if count == 0 and reasons:
        next_section = re.search(r"^## Reuse cues$", body, re.MULTILINE)
        if next_section is None:
            raise SourceError("artifact body must contain Routing notes or Reuse cues")
        body = (
            body[: next_section.start()]
            + "## Routing notes\n\n"
            + "\n".join(reasons)
            + "\n\n"
            + body[next_section.start() :]
        )
    elif count > 1:
        raise SourceError("artifact body contains duplicate Routing notes sections")
    return render_artifact(values, body)


def build_event_record(
    *,
    event_type: str,
    source_id: str,
    event: Mapping[str, Any],
    route_decision: Mapping[str, Any] | None,
    promotion_map_sha256: str | None = None,
    promotion_row_sha256: str | None = None,
    require_promotion: bool = False,
) -> dict[str, Any]:
    if event.get("type") != event_type or event.get("source_id") != source_id:
        raise SourceError("event record identity mismatch")
    for name, value in (
        ("promotion_map_sha256", promotion_map_sha256),
        ("promotion_row_sha256", promotion_row_sha256),
    ):
        if value is not None and (
            not isinstance(value, str) or HASH_RE.fullmatch(value) is None
        ):
            raise SourceError(f"{name} is invalid")
        if require_promotion and value is None:
            raise SourceError(f"{name} is required")
    return {
        "version": 1,
        "event_type": event_type,
        "source_id": source_id,
        "promotion_map_sha256": promotion_map_sha256,
        "promotion_row_sha256": promotion_row_sha256,
        "event": dict(event),
        "route_decision": None if route_decision is None else dict(route_decision),
    }


def _load_input(path: str) -> Mapping[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, Mapping) or value.get("version") != VERSION:
        raise SourceError("input.version must be 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render deterministic Atlas source artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    merge = subparsers.add_parser("merge-artifact")
    merge.add_argument("--input", required=True)
    route = subparsers.add_parser("render-route-artifact")
    route.add_argument("--input", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_input(args.input)
        if args.command == "merge-artifact":
            allowed = {
                "version",
                "staged_artifact_text",
                "evidence_bundle",
                "event",
                "source_state",
                "living_artifact_text",
                "fresh_capture",
            }
            if set(payload) != allowed:
                raise SourceError("merge-artifact input fields are invalid")
            artifact_text = merge_artifact(
                payload["staged_artifact_text"],
                payload["evidence_bundle"],
                payload["event"],
                payload["source_state"],
                living_artifact_text=payload["living_artifact_text"],
                fresh_capture=payload["fresh_capture"],
            )
        else:
            allowed = {"version", "artifact_text", "route_event", "route_status"}
            if set(payload) != allowed:
                raise SourceError("render-route-artifact input fields are invalid")
            artifact_text = render_route_artifact(
                payload["artifact_text"],
                payload["route_event"],
                payload["route_status"],
            )
        result = {
            "ok": True,
            "artifact_text": artifact_text,
            "artifact_sha256": atlas_transaction.sha256(artifact_text.encode("utf-8")),
        }
        sys.stdout.write(
            json.dumps(
                result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        )
        return 0
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        SourceError,
        ValueError,
    ) as exc:
        print(f"atlas-source: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
