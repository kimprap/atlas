#!/usr/bin/env python3
"""Deterministic Atlas source artifact assembly."""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

import atlas_quality
import atlas_state
import atlas_transaction
from atlas_url import normalize_canonical_url, source_id_for


VERSION = 1
SOURCE_ARTIFACT_VERSION = 2
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
    "classification_status",
    "routing_terms",
    "source_routing_sha256",
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
OBJECT_ARRAY_FRONTMATTER_KEYS = {"routing_terms"}
ROUTING_TERM_TYPES = {"domain", "subdomain", "tag", "topic"}
ROUTING_TERM_CONFIDENCES = {"high", "medium", "low"}
ROUTING_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _validate_routing_terms(value: Any, name: str) -> None:
    if not isinstance(value, list) or len(value) > 24:
        raise SourceError(f"{name} must contain at most 24 objects")
    seen: set[tuple[str, str]] = set()
    for index, term in enumerate(value):
        if not isinstance(term, dict) or set(term) != {"type", "value", "confidence"}:
            raise SourceError(f"{name}[{index}] has invalid shape")
        term_type = term["type"]
        term_value = term["value"]
        confidence = term["confidence"]
        if (
            term_type not in ROUTING_TERM_TYPES
            or confidence not in ROUTING_TERM_CONFIDENCES
            or not isinstance(term_value, str)
            or not term_value
            or unicodedata.normalize("NFKC", term_value).strip() != term_value
        ):
            raise SourceError(f"{name}[{index}] is invalid")
        identity = (term_type, term_value.casefold())
        if identity in seen:
            raise SourceError(f"{name} contains duplicate identity")
        seen.add(identity)


def _validate_frontmatter_shapes(values: Mapping[str, str]) -> None:
    if values.get("schema_version") != "2":
        raise SourceError("frontmatter schema_version must be the unquoted integer 2")
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
    if values.get("classification_status") not in {
        '"classified"',
        '"unclassified"',
    }:
        raise SourceError(
            "frontmatter classification_status must be classified or unclassified"
        )
    try:
        routing_terms = json.loads(values.get("routing_terms", ""))
    except json.JSONDecodeError as exc:
        raise SourceError(
            "frontmatter routing_terms must be a compact JSON object array"
        ) from exc
    _validate_routing_terms(routing_terms, "frontmatter routing_terms")
    routing_digest = scalar(values, "source_routing_sha256")
    if ROUTING_SHA256_RE.fullmatch(routing_digest) is None:
        raise SourceError("frontmatter source_routing_sha256 is invalid")


ROUTE_STATUSES = {"unrouted", "routed", "no-topic-match", "routing-blocked"}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")


class SourceError(ValueError):
    """A source artifact violates the canonical contract."""


_CAPTURE_KEYS = {
    "version",
    "requested_url",
    "final_url",
    "content_type",
    "method",
    "complete",
    "notes",
    "text",
}
_TEXT_MEDIA_TYPE = re.compile(r"(?i:text/[^;\s]+)(?:;.*)?\Z")


def _capture_text(value: Any, name: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise SourceError(f"{name} must be {'nonempty ' if nonempty else ''}text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise SourceError(f"{name} is not valid UTF-8 text") from exc
    return value


def normalize_capture(capture: Any) -> dict[str, Any]:
    """Validate and normalize one complete transport-neutral source capture."""

    if type(capture) is not dict or set(capture) != _CAPTURE_KEYS:
        raise SourceError("capture must contain exactly the canonical eight fields")
    if type(capture["version"]) is not int or capture["version"] != VERSION:
        raise SourceError("capture.version must be 1")
    if capture["complete"] is not True:
        raise SourceError("capture.complete must be true")

    requested = _capture_text(capture["requested_url"], "capture.requested_url")
    final = _capture_text(capture["final_url"], "capture.final_url")
    try:
        canonical_url = normalize_canonical_url(requested)
    except ValueError as exc:
        raise SourceError("capture.requested_url must be an HTTP(S) URL") from exc
    try:
        final_url = normalize_canonical_url(final)
    except ValueError as exc:
        raise SourceError("capture.final_url must be an HTTP(S) URL") from exc

    content_type = _capture_text(capture["content_type"], "capture.content_type")
    if _TEXT_MEDIA_TYPE.fullmatch(content_type) is None:
        raise SourceError("capture.content_type must be textual")
    method = _capture_text(capture["method"], "capture.method")
    if any(char in "\r\n" for char in content_type + method):
        raise SourceError("capture metadata contains a line boundary")

    notes_value = capture["notes"]
    if type(notes_value) is not list:
        raise SourceError("capture.notes must be an array of text")
    notes = [
        _capture_text(note, f"capture.notes[{index}]", nonempty=False)
        for index, note in enumerate(notes_value)
    ]
    text = _capture_text(capture["text"], "capture.text")
    payload = text.encode("utf-8")
    return {
        "version": VERSION,
        "canonical_url": canonical_url,
        "final_url": final_url,
        "content_type": content_type,
        "method": method,
        "complete": True,
        "notes": notes,
        "text": text,
        "content_hash": atlas_transaction.sha256(payload),
        "payload_bytes": len(payload),
    }


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
            if not isinstance(id_properties, Mapping) or set(id_properties) != {"id"}:
                raise ValueError(invalid_detail)
            id_schema = id_properties.get("id")
            if (
                not isinstance(id_schema, Mapping)
                or set(id_schema) != {"const"}
                or id_schema.get("const") != _CHECKLIST_IDS[index]
            ):
                raise ValueError(invalid_detail)

        def resolve_ref(resource_name: str, reference: Any) -> tuple[Any, str, str]:
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
            if not definition_name or "/" in definition_name or "~" in definition_name:
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
                return [expand(item, resource_name, pointer, stack) for item in node]
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
        if len(prefix_items_output) != len(_CHECKLIST_IDS) or any(
            checklist_id(item) != _CHECKLIST_IDS[index]
            for index, item in enumerate(prefix_items_output)
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


def project_classifier_transport_schema(
    worker_schema: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the intentionally open object-only classifier delivery schema."""
    definitions = worker_schema.get("$defs")
    if not isinstance(definitions, Mapping):
        raise SourceError("worker transport schema assets are invalid")
    delivery = definitions.get("classifierDelivery")
    if delivery != {"type": "object", "additionalProperties": True}:
        raise SourceError("worker transport schema assets are invalid")
    return {"type": "object", "additionalProperties": True}


_CLASSIFIER_KEYS = {
    "version",
    "primary_domain",
    "secondary_domains",
    "subdomains",
    "tags",
    "routing_terms",
}
_CLASSIFIER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _classification_unavailable(reason: str) -> dict[str, Any]:
    return {
        "version": 1,
        "status": "semantic-unavailable",
        "disposition": "SOURCE_CLASSIFICATION_UNAVAILABLE",
        "reason": reason,
    }


def map_classifier_result(value: Any) -> dict[str, Any]:
    """Map one fully decoded classifier object to the closed downstream union."""
    if not isinstance(value, Mapping):
        raise SourceError("classifier completion must decode as one object")
    if not _CLASSIFIER_KEYS.issubset(value):
        return _classification_unavailable("required-fields-incomplete")
    semantic_incomplete = value.get("primary_domain") is None
    try:
        if set(value) != _CLASSIFIER_KEYS or value.get("version") != 1:
            raise ValueError

        def normalized_text(item: Any) -> str:
            if not isinstance(item, str):
                raise ValueError
            normalized = unicodedata.normalize("NFKC", item).strip()
            if not normalized or normalized != item:
                raise ValueError
            normalized.encode("utf-8", "strict")
            return normalized

        def proposal(item: Any, *, parent: bool = False) -> dict[str, Any]:
            base = {"id", "label", "aliases"}
            if not isinstance(item, Mapping):
                raise ValueError
            if parent:
                if set(item) not in (base, base | {"parent"}):
                    raise ValueError
            elif set(item) != base:
                raise ValueError
            identifier = normalized_text(item.get("id"))
            if not _CLASSIFIER_ID_RE.fullmatch(identifier):
                raise ValueError
            label = normalized_text(item.get("label"))
            aliases_value = item.get("aliases")
            if not isinstance(aliases_value, list) or len(aliases_value) > 4:
                raise ValueError
            aliases = [normalized_text(alias) for alias in aliases_value]
            if len({alias.casefold() for alias in aliases}) != len(aliases):
                raise ValueError
            result: dict[str, Any] = {
                "id": identifier,
                "label": label,
                "aliases": sorted(aliases, key=lambda item: item.encode("utf-8")),
            }
            if parent:
                parent_value = item.get("parent")
                if parent_value is None:
                    result["parent"] = None
                elif isinstance(parent_value, str):
                    stripped = unicodedata.normalize("NFKC", parent_value).strip()
                    if stripped != parent_value:
                        raise ValueError
                    result["parent"] = stripped
                else:
                    raise ValueError
            return result

        primary_value = value.get("primary_domain")
        primary = None if primary_value is None else proposal(primary_value)

        def proposal_array(
            name: str, limit: int, *, parent: bool = False
        ) -> list[dict[str, Any]]:
            raw = value.get(name)
            if not isinstance(raw, list) or len(raw) > limit:
                raise ValueError
            items = [proposal(item, parent=parent) for item in raw]
            if len({item["id"].casefold() for item in items}) != len(items):
                raise ValueError
            return sorted(items, key=lambda item: item["id"].encode("utf-8"))

        secondary = proposal_array("secondary_domains", 3)
        subdomains = proposal_array("subdomains", 6, parent=True)
        domain_id_sequence = [
            item["id"].casefold()
            for item in ([primary] if primary is not None else []) + secondary
        ]
        if len(set(domain_id_sequence)) != len(domain_id_sequence):
            raise ValueError
        tags = proposal_array("tags", 12)
        all_domain_ids = {
            item["id"].casefold()
            for item in ([primary] if primary is not None else []) + secondary
        }
        for item in subdomains:
            parent_value = item["parent"]
            if (
                not isinstance(parent_value, str)
                or not parent_value
                or parent_value.casefold() not in all_domain_ids
            ):
                semantic_incomplete = True

        raw_terms = value.get("routing_terms")
        if not isinstance(raw_terms, list) or len(raw_terms) > 24:
            raise ValueError
        terms: list[dict[str, str]] = []
        identities: set[tuple[str, str]] = set()
        for raw_term in raw_terms:
            if not isinstance(raw_term, Mapping) or set(raw_term) != {
                "type",
                "value",
                "confidence",
            }:
                raise ValueError
            term_type = raw_term.get("type")
            confidence = raw_term.get("confidence")
            term_value = normalized_text(raw_term.get("value"))
            if (
                term_type not in ROUTING_TERM_TYPES
                or confidence not in ROUTING_TERM_CONFIDENCES
            ):
                raise ValueError
            identity = (str(term_type), term_value.casefold())
            if identity in identities:
                raise ValueError
            identities.add(identity)
            terms.append(
                {
                    "type": str(term_type),
                    "value": term_value,
                    "confidence": str(confidence),
                }
            )
        terms.sort(
            key=lambda item: (
                item["type"].encode("utf-8"),
                item["value"].encode("utf-8"),
                item["confidence"].encode("utf-8"),
            )
        )
    except (TypeError, UnicodeError, ValueError):
        return _classification_unavailable("schema-invalid")
    if semantic_incomplete:
        return _classification_unavailable("semantic-incomplete")
    return {
        "version": 1,
        "status": "classified",
        "result": {
            "version": 1,
            "primary_domain": primary,
            "secondary_domains": secondary,
            "subdomains": subdomains,
            "tags": tags,
            "routing_terms": terms,
        },
    }


def validate_classification_input(value: Any) -> dict[str, Any]:
    """Require one canonical closed classified-or-semantic-unavailable input."""
    if not isinstance(value, Mapping) or value.get("version") != 1:
        raise SourceError("classification input is invalid")
    if value.get("status") == "classified":
        if set(value) != {"version", "status", "result"}:
            raise SourceError("classification input is invalid")
        normalized = map_classifier_result(value.get("result"))
        if normalized.get("status") != "classified" or normalized != value:
            raise SourceError("classified input is not canonical")
        return dict(value)
    if (
        set(value) == {"version", "status", "disposition", "reason"}
        and value.get("status") == "semantic-unavailable"
        and value.get("disposition") == "SOURCE_CLASSIFICATION_UNAVAILABLE"
        and value.get("reason")
        in {"schema-invalid", "required-fields-incomplete", "semantic-incomplete"}
    ):
        return dict(value)
    raise SourceError("classification input is invalid")


@dataclass(frozen=True)
class ParsedArtifact:
    values: dict[str, str]
    body: str


_SOURCE_ARTIFACT_V1_FRONTMATTER_KEYS = tuple(
    key
    for key in FRONTMATTER_KEYS
    if key not in {"classification_status", "routing_terms", "source_routing_sha256"}
)


def _parse_artifact_fields(
    text: str,
    expected_keys: Sequence[str],
) -> ParsedArtifact:
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
    missing = set(expected_keys) - set(values)
    unknown = set(values) - set(expected_keys)
    if missing or unknown:
        raise SourceError(
            f"artifact frontmatter keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    body = normalized[boundary + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    return ParsedArtifact(values, body)


def _parse_source_artifact_v1(text: str) -> ParsedArtifact:
    artifact = _parse_artifact_fields(text, _SOURCE_ARTIFACT_V1_FRONTMATTER_KEYS)
    values = artifact.values
    if values.get("schema_version") != "1":
        raise SourceError("legacy source artifact schema_version must be 1")
    source_seq = values.get("source_seq", "")
    if re.fullmatch(r"0|[1-9]\d*", source_seq) is None:
        raise SourceError(
            "legacy source artifact source_seq must be an unquoted non-negative integer"
        )
    for key in LIST_FRONTMATTER_KEYS:
        raw = values.get(key, "")
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"legacy source artifact {key} must be a JSON array of strings"
            ) from exc
        if not isinstance(items, list) or any(
            not isinstance(item, str) for item in items
        ):
            raise SourceError(
                f"legacy source artifact {key} must be a JSON array of strings"
            )
    return artifact


def parse_artifact(text: str) -> ParsedArtifact:
    artifact = _parse_artifact_fields(text, FRONTMATTER_KEYS)
    _validate_frontmatter_shapes(artifact.values)
    return artifact


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


def _candidate_body_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    starts = [index for index, line in enumerate(lines) if line == f"## {heading}"]
    if len(starts) != 1:
        raise SourceError(f"candidate artifact {heading} section is invalid")
    start = starts[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    value = "\n".join(lines[start:end]).strip()
    if not value:
        raise SourceError(f"candidate artifact {heading} section is empty")
    return value


def candidate_artifact_projection(text: str, revision: str) -> dict[str, Any]:
    """Project one source artifact to bounded deterministic candidate fields."""
    parsed = parse_artifact(text)
    tldr_matches = re.findall(r"^> \*\*TL;DR\*\*: (.+)$", parsed.body, re.MULTILINE)
    if len(tldr_matches) != 1:
        raise SourceError("candidate artifact TL;DR is invalid")
    arrays: dict[str, list[Any]] = {}
    for name in (
        "secondary_domains",
        "subdomains",
        "canonical_tags",
        "routing_terms",
    ):
        try:
            value = json.loads(parsed.values[name])
        except json.JSONDecodeError as exc:
            raise SourceError(f"candidate artifact {name} is invalid") from exc
        if not isinstance(value, list):
            raise SourceError(f"candidate artifact {name} is invalid")
        arrays[name] = value
    projection = {
        "classification_status": scalar(parsed.values, "classification_status"),
        "primary_domain": scalar(parsed.values, "primary_domain"),
        "secondary_domains": arrays["secondary_domains"],
        "subdomains": arrays["subdomains"],
        "canonical_tags": arrays["canonical_tags"],
        "routing_terms": arrays["routing_terms"],
        "title": scalar(parsed.values, "title"),
        "tldr": tldr_matches[0].strip(),
        "key_points": _candidate_body_section(parsed.body, "Key points"),
    }
    routing_sha256 = atlas_state.source_routing_sha256(projection)
    if scalar(parsed.values, "source_routing_sha256") != routing_sha256:
        raise SourceError("candidate artifact source routing digest is invalid")
    return {
        "revision": revision,
        "source_id": scalar(parsed.values, "source_id"),
        "canonical_url": scalar(parsed.values, "canonical_url"),
        "content_hash": scalar(parsed.values, "content_hash"),
        "source_routing_sha256": routing_sha256,
        "source_kind": scalar(parsed.values, "source_kind"),
        **projection,
    }


def parse_source_taxonomy_remediation_artifact(text: str) -> ParsedArtifact:
    """Decode the immutable schema-1 artifact used by the named remediation."""
    return _parse_source_artifact_v1(text)


def source_taxonomy_remediation_artifact_projection(
    text: str,
    revision: str,
) -> dict[str, Any]:
    """Decode one immutable schema-1 source for the named remediation."""
    parsed = parse_source_taxonomy_remediation_artifact(text)
    tldr_matches = re.findall(r"^> \*\*TL;DR\*\*: (.+)$", parsed.body, re.MULTILINE)
    if len(tldr_matches) != 1:
        raise SourceError("legacy source artifact TL;DR is invalid")
    arrays: dict[str, list[Any]] = {}
    for name in ("secondary_domains", "subdomains", "canonical_tags"):
        try:
            value = json.loads(parsed.values[name])
        except json.JSONDecodeError as exc:
            raise SourceError(f"legacy source artifact {name} is invalid") from exc
        if not isinstance(value, list):
            raise SourceError(f"legacy source artifact {name} is invalid")
        arrays[name] = value
    return {
        "revision": revision,
        "source_id": scalar(parsed.values, "source_id"),
        "canonical_url": scalar(parsed.values, "canonical_url"),
        "content_hash": scalar(parsed.values, "content_hash"),
        "title": scalar(parsed.values, "title"),
        "tldr": tldr_matches[0].strip(),
        "key_points": _candidate_body_section(parsed.body, "Key points"),
        "source_kind": scalar(parsed.values, "source_kind"),
        "primary_domain": scalar(parsed.values, "primary_domain"),
        "secondary_domains": arrays["secondary_domains"],
        "subdomains": arrays["subdomains"],
        "canonical_tags": arrays["canonical_tags"],
    }


def candidate_artifact_probe(
    text: str,
    revision: str,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Collect candidate-only structural findings without weakening strict projection."""
    details: list[str] = []
    projection: dict[str, Any] | None = None
    try:
        projection = candidate_artifact_projection(text, revision)
    except ValueError as exc:
        strict_detail = str(exc)
        frontmatter, body, parse_findings = atlas_quality._parse_frontmatter(text)
        for finding in parse_findings:
            parts = [finding.code]
            if finding.line is not None:
                parts.append(f"line={finding.line}")
            if finding.detail:
                parts.append(f"detail={finding.detail}")
            details.append("; ".join(parts))
        for key in FRONTMATTER_KEYS:
            if key not in frontmatter:
                details.append(f"frontmatter key is missing: {key}")
        for key in frontmatter:
            if key not in FRONTMATTER_KEYS:
                details.append(f"frontmatter key is unknown: {key}")
        if frontmatter.get("schema_version") != "2":
            details.append("frontmatter schema_version must be the unquoted integer 2")
        source_seq = frontmatter.get("source_seq")
        if source_seq is not None and re.fullmatch(r"[1-9]\d*", source_seq) is None:
            details.append("frontmatter source_seq must be a positive integer")
        source_id = frontmatter.get("source_id")
        if source_id is not None and SOURCE_ID_RE.fullmatch(source_id) is None:
            details.append("frontmatter source_id is invalid")
        content_hash = frontmatter.get("content_hash")
        if content_hash is not None and HASH_RE.fullmatch(content_hash) is None:
            details.append("frontmatter content_hash is invalid")
        canonical_url = frontmatter.get("canonical_url")
        if canonical_url is not None:
            try:
                if normalize_canonical_url(canonical_url) != canonical_url:
                    details.append("frontmatter canonical_url is not canonical")
            except ValueError:
                details.append("frontmatter canonical_url is invalid")
        arrays: dict[str, list[Any]] = {}
        for key in (*sorted(LIST_FRONTMATTER_KEYS), "routing_terms"):
            raw = frontmatter.get(key)
            if raw is None:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                details.append(f"frontmatter {key} is not valid JSON")
                continue
            if not isinstance(value, list):
                details.append(f"frontmatter {key} must be an array")
                continue
            if key != "routing_terms" and any(
                not isinstance(item, str) for item in value
            ):
                details.append(f"frontmatter {key} must contain only strings")
                continue
            arrays[key] = value
        routing_terms = arrays.get("routing_terms")
        if routing_terms is not None:
            try:
                _validate_routing_terms(routing_terms, "frontmatter routing_terms")
            except SourceError as routing_exc:
                details.append(str(routing_exc))
        classification_status = frontmatter.get("classification_status")
        if classification_status not in {"classified", "unclassified"}:
            details.append(
                "frontmatter classification_status must be classified or unclassified"
            )
        elif classification_status == "classified" and not frontmatter.get(
            "primary_domain", ""
        ):
            details.append("classified source primary_domain is empty")
        elif classification_status == "unclassified" and (
            frontmatter.get("primary_domain", "")
            or arrays.get("secondary_domains")
            or arrays.get("subdomains")
            or arrays.get("canonical_tags")
            or routing_terms
        ):
            details.append("unclassified source contains routing classification")
        routing_digest = frontmatter.get("source_routing_sha256")
        if (
            routing_digest is not None
            and ROUTING_SHA256_RE.fullmatch(routing_digest) is None
        ):
            details.append("frontmatter source_routing_sha256 is invalid")
        tldr_matches = re.findall(r"^> \*\*TL;DR\*\*: (.+)$", body, re.MULTILINE)
        if len(tldr_matches) != 1:
            details.append("candidate artifact TL;DR is invalid")
        try:
            _candidate_body_section(body, "Key points")
        except SourceError as body_exc:
            details.append(str(body_exc))
        if not details:
            details.append(strict_detail)
    if projection is not None:
        if atlas_state.REVISION_RE.fullmatch(revision) is None:
            details.append("candidate artifact revision is invalid")
        if SOURCE_ID_RE.fullmatch(projection["source_id"]) is None:
            details.append("candidate artifact source_id is invalid")
        if HASH_RE.fullmatch(projection["content_hash"]) is None:
            details.append("candidate artifact content_hash is invalid")
        try:
            if (
                normalize_canonical_url(projection["canonical_url"])
                != projection["canonical_url"]
            ):
                details.append("candidate artifact canonical_url is not canonical")
        except ValueError:
            details.append("candidate artifact canonical_url is invalid")
        if projection["classification_status"] == "classified":
            if not projection["primary_domain"]:
                details.append("classified source primary_domain is empty")
        elif (
            projection["primary_domain"]
            or projection["secondary_domains"]
            or projection["subdomains"]
            or projection["canonical_tags"]
            or projection["routing_terms"]
        ):
            details.append("unclassified source contains routing classification")
    normalized = tuple(sorted(set(details), key=lambda item: item.encode("utf-8")))
    return (None if normalized else projection), normalized


_SOURCE_TAXONOMY_REMEDIATION_PRIMARY_CHANGES = {
    ("Unknown", "web"),
    ("Unknown", "agent-systems"),
    ("agent-systems/harness", "agent-systems"),
}
_SOURCE_TAXONOMY_REMEDIATION_SUBDOMAIN_VALUES = {
    "agentic-harness-architecture",
    "ai-coding-workflow",
    "lean-self-improving-agent-harness",
}


def _source_taxonomy_remediation_change(
    value: Mapping[str, Any] | None,
    field: str,
) -> tuple[Any, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"before", "after"}:
        raise SourceError(f"{field} remediation change is invalid")
    return value["before"], value["after"]


def _source_taxonomy_remediation_frontmatter_lines(
    text: str,
) -> tuple[list[tuple[int, int, str]], int]:
    lines: list[tuple[int, int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        end = offset + len(line)
        lines.append((offset, end, line))
        offset = end
    if not lines or lines[0][2].rstrip("\r\n") != "---":
        raise SourceError("artifact frontmatter is missing")
    closing = next(
        (
            index
            for index, (_, _, line) in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if closing is None:
        raise SourceError("artifact frontmatter is unterminated")
    return lines, closing


def _source_taxonomy_remediation_span(
    text: str,
    lines: Sequence[tuple[int, int, str]],
    closing: int,
    key: str,
    *,
    block_sequence: bool,
) -> tuple[int, int, str, str]:
    matches = [
        index for index in range(1, closing) if lines[index][2].startswith(key + ":")
    ]
    if len(matches) != 1:
        raise SourceError(f"frontmatter {key} span is invalid")
    index = matches[0]
    start, end, line = lines[index]
    newline = (
        "\r\n"
        if line.endswith("\r\n")
        else "\n"
        if line.endswith("\n")
        else "\r"
        if line.endswith("\r")
        else ""
    )
    body_end = end - len(newline)
    colon = start + len(key)
    raw = text[colon + 1 : body_end]
    if not block_sequence:
        if not raw.strip():
            raise SourceError(f"frontmatter {key} scalar span is empty")
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        value_start = colon + 1 + len(leading)
        value_end = body_end - len(trailing)
        return value_start, value_end, leading, trailing
    if raw.strip():
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        value_start = colon + 1 + len(leading)
        value_end = body_end - len(trailing)
        return value_start, value_end, "", ""
    cursor = index + 1
    if cursor >= closing or not lines[cursor][2].startswith(("  - ", "\t- ")):
        raise SourceError(f"frontmatter {key} block sequence span is invalid")
    while cursor < closing and lines[cursor][2].startswith(("  - ", "\t- ")):
        cursor += 1
    value_start = colon + 1
    value_end = lines[cursor - 1][1]
    return value_start, value_end, " ", newline


def _source_taxonomy_remediation_subdomains(values: Sequence[str]) -> list[str]:
    output: list[str] = []
    harness_seen = False
    for value in values:
        mapped = (
            "harness"
            if value in _SOURCE_TAXONOMY_REMEDIATION_SUBDOMAIN_VALUES
            else value
        )
        if mapped == "harness":
            if harness_seen:
                continue
            harness_seen = True
        output.append(mapped)
    return output


def render_source_taxonomy_remediation(
    artifact_text: str,
    *,
    expected_source_id: str,
    primary_domain_change: Mapping[str, Any] | None,
    subdomains_change: Mapping[str, Any] | None,
) -> str:
    """Render only the approved source-taxonomy frontmatter value spans."""

    if not isinstance(artifact_text, str):
        raise SourceError("artifact text must be a string")
    if (
        not isinstance(expected_source_id, str)
        or SOURCE_ID_RE.fullmatch(expected_source_id) is None
    ):
        raise SourceError("expected source ID is invalid")
    primary = _source_taxonomy_remediation_change(
        primary_domain_change, "primary_domain"
    )
    subdomains = _source_taxonomy_remediation_change(subdomains_change, "subdomains")
    if primary is None and subdomains is None:
        raise SourceError("source taxonomy remediation has no target field")
    before = _parse_source_artifact_v1(artifact_text)
    if scalar(before.values, "source_id") != expected_source_id:
        raise SourceError("source taxonomy remediation identity mismatch")

    replacements: list[tuple[int, int, str]] = []
    lines, closing = _source_taxonomy_remediation_frontmatter_lines(artifact_text)
    if primary is not None:
        primary_before, primary_after = primary
        if (
            not isinstance(primary_before, str)
            or not isinstance(primary_after, str)
            or (primary_before, primary_after)
            not in _SOURCE_TAXONOMY_REMEDIATION_PRIMARY_CHANGES
            or scalar(before.values, "primary_domain") != primary_before
        ):
            raise SourceError("primary_domain remediation change is invalid")
        start, end, _, _ = _source_taxonomy_remediation_span(
            artifact_text,
            lines,
            closing,
            "primary_domain",
            block_sequence=False,
        )
        replacements.append((start, end, primary_after))
    if subdomains is not None:
        subdomains_before, subdomains_after = subdomains
        if (
            not isinstance(subdomains_before, list)
            or not isinstance(subdomains_after, list)
            or any(not isinstance(value, str) for value in subdomains_before)
            or any(not isinstance(value, str) for value in subdomains_after)
            or not any(
                value in _SOURCE_TAXONOMY_REMEDIATION_SUBDOMAIN_VALUES
                for value in subdomains_before
            )
            or _source_taxonomy_remediation_subdomains(subdomains_before)
            != subdomains_after
        ):
            raise SourceError("subdomains remediation change is invalid")
        try:
            observed_subdomains = json.loads(before.values["subdomains"])
        except json.JSONDecodeError as exc:
            raise SourceError("subdomains remediation source is invalid") from exc
        if observed_subdomains != subdomains_before:
            raise SourceError("subdomains remediation precondition mismatch")
        start, end, leading, trailing = _source_taxonomy_remediation_span(
            artifact_text,
            lines,
            closing,
            "subdomains",
            block_sequence=True,
        )
        compact = json.dumps(
            subdomains_after, ensure_ascii=False, separators=(",", ":")
        )
        replacements.append((start, end, leading + compact + trailing))

    output = artifact_text
    for start, end, replacement in sorted(replacements, reverse=True):
        output = output[:start] + replacement + output[end:]
    after = _parse_source_artifact_v1(output)
    if scalar(after.values, "source_id") != expected_source_id:
        raise SourceError("source taxonomy remediation changed source identity")
    if primary is not None and scalar(after.values, "primary_domain") != primary[1]:
        raise SourceError("source taxonomy remediation primary output is invalid")
    if subdomains is not None:
        try:
            after_subdomains = json.loads(after.values["subdomains"])
        except json.JSONDecodeError as exc:
            raise SourceError("source taxonomy remediation output is invalid") from exc
        if after_subdomains != subdomains[1]:
            raise SourceError(
                "source taxonomy remediation subdomains output is invalid"
            )
    for key in _SOURCE_ARTIFACT_V1_FRONTMATTER_KEYS:
        if key not in {"primary_domain", "subdomains"} and (
            before.values[key] != after.values[key]
        ):
            raise SourceError(
                f"source taxonomy remediation changed non-target field {key}"
            )
    if before.body != after.body:
        raise SourceError("source taxonomy remediation changed source body")
    return output


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
    "classification_status",
    "routing_terms",
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
        "classification_status",
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
    _validate_routing_terms(context["routing_terms"], "caller_context.routing_terms")
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

    projection = {
        "classification_status": context["classification_status"],
        "primary_domain": context["primary_domain"],
        "secondary_domains": context["secondary_domains"],
        "subdomains": context["subdomains"],
        "canonical_tags": context["canonical_tags"],
        "routing_terms": context["routing_terms"],
        "title": metadata["title"],
        "tldr": str(claims[0]["statement"]).strip(),
        "key_points": "\n".join(f"- {claim['statement']}" for claim in claims),
    }
    values = {
        "schema_version": str(SOURCE_ARTIFACT_VERSION),
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
        "classification_status": quoted(context["classification_status"]),
        "routing_terms": json.dumps(
            context["routing_terms"], ensure_ascii=False, separators=(",", ":")
        ),
        "source_routing_sha256": quoted(atlas_state.source_routing_sha256(projection)),
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
        f"- Classification status: `{context['classification_status']}`",
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
        "- Routing terms: "
        + (
            ", ".join(
                f"`{term['type']}:{term['value']}:{term['confidence']}`"
                for term in context["routing_terms"]
            )
            if context["routing_terms"]
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


def _replace_body_section(body: str, living_body: str, heading: str) -> str:
    pattern = re.compile(
        rf"(^## {re.escape(heading)}\n.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    source_matches = list(pattern.finditer(living_body))
    target_matches = list(pattern.finditer(body))
    if len(source_matches) != 1 or len(target_matches) != 1:
        raise SourceError(f"artifact body must contain one {heading} section")
    replacement = source_matches[0].group(1)
    return (
        body[: target_matches[0].start()]
        + replacement
        + body[target_matches[0].end() :]
    )


_ROUTING_NOTES_RE = re.compile(
    r"(^## Routing notes\n)(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def _routing_verifier_lines(body: str) -> list[str]:
    matches = list(_ROUTING_NOTES_RE.finditer(body))
    if len(matches) > 1:
        raise SourceError("artifact body contains duplicate Routing notes sections")
    if not matches:
        return []
    return [
        line
        for line in matches[0].group(2).splitlines()
        if line.strip().startswith("- Verifier:")
    ]


def _replace_routing_verifier_lines(body: str, verifier_lines: Sequence[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        lines = [
            line
            for line in match.group(2).splitlines()
            if not line.strip().startswith("- Verifier:")
        ]
        while lines and not lines[-1].strip():
            lines.pop()
        if verifier_lines and not lines:
            lines.append("")
        lines.extend(verifier_lines)
        return match.group(1) + "\n".join(lines) + "\n\n"

    updated, count = _ROUTING_NOTES_RE.subn(replace, body)
    if count == 0 and verifier_lines:
        next_section = re.search(r"^## Reuse cues$", body, re.MULTILINE)
        if next_section is None:
            raise SourceError("artifact body must contain Routing notes or Reuse cues")
        return (
            body[: next_section.start()]
            + "## Routing notes\n\n"
            + "\n".join(verifier_lines)
            + "\n\n"
            + body[next_section.start() :]
        )
    if count > 1:
        raise SourceError("artifact body contains duplicate Routing notes sections")
    return updated


def classify_hash_transition(
    previous_content_hash: str | None,
    evidence_bundle: Mapping[str, Any],
) -> str:
    """Return `same-hash` or `changed-hash` from proven text evidence only.

    Inaccessible, empty, media-backed, unbacked projection, or otherwise unproven
    evidence raises SourceError and is a no-write result—never a guessed transition.
    `hash_baseline_migration` is a reporting reason only and is not returned here.
    """
    effective = evidence_identity(evidence_bundle)["content_hash"]
    if previous_content_hash is None:
        return "changed-hash"
    if (
        not isinstance(previous_content_hash, str)
        or HASH_RE.fullmatch(previous_content_hash) is None
    ):
        raise SourceError("previous content_hash is invalid")
    return "same-hash" if previous_content_hash == effective else "changed-hash"


def evidence_identity(bundle: Mapping[str, Any]) -> dict[str, str]:
    """Return canonical source identity from one proven evidence bundle."""
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
    effective, findings = atlas_quality.resolve_effective_content_hash(bundle)
    if findings or effective is None:
        detail = findings[0].code if findings else "EVIDENCE_PAYLOAD_TEXT_INVALID"
        if findings and findings[0].detail:
            detail = f"{detail}: {findings[0].detail}"
        raise SourceError(f"evidence identity invalid: {detail}")
    return {
        "canonical_url": canonical_url,
        "source_id": source_id_for(canonical_url),
        "content_hash": effective,
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
    evidence = evidence_identity(evidence_bundle)
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
        values["routing_status"] = quoted(route_status)
        values["routed_at"] = quoted(
            "" if route_status == "unrouted" else str(event.get("checked_on"))
        )
    else:
        assert living is not None
        values["acquired_by"] = living.values["acquired_by"]
        values["acquisition_run"] = living.values["acquisition_run"]
        if content_changed:
            values["routing_status"] = quoted(route_status)
            values["routed_at"] = quoted(
                "" if route_status == "unrouted" else str(event.get("checked_on"))
            )
        else:
            for name in (
                "primary_domain",
                "subdomains",
                "secondary_domains",
                "canonical_tags",
                "candidate_terms",
            ):
                values[name] = living.values[name]
            values["routing_status"] = quoted(route_status)
            values["routed_at"] = living.values["routed_at"]

    body = staged.body
    if not created and not content_changed:
        assert living is not None
        body = _replace_body_section(body, living.body, "Classification")
    body = _replace_header(body, "Source ID", f"`{state_source_id}`")
    body = _replace_header(body, "Source seq", f"`{source_seq}`")
    body = _replace_header(body, "First seen", state_first_seen)
    body = _replace_header(body, "Last checked", str(event.get("checked_on")))
    body = _replace_header(body, "Last summarized", str(event.get("summarized_on")))
    body = _replace_header(body, "Refresh after", str(event.get("refresh_after")))
    body = _replace_header(
        body, "Route status", f"`{scalar(values, 'routing_status')}`"
    )
    if not created and not content_changed and route_status == "routed":
        assert living is not None
        body = _replace_routing_verifier_lines(
            body, _routing_verifier_lines(living.body)
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
    findings: Sequence[atlas_quality.Finding] | Sequence[atlas_state.Finding],
) -> list[dict[str, str]]:
    return [_prepare_finding(item.code, item.path, item.detail) for item in findings]


def _worker_checklist_structure_findings(value: Any) -> list[atlas_quality.Finding]:
    """Reject malformed checklist packets while deferring valid failure outcomes."""
    return [
        finding
        for finding in atlas_quality.validate_checklist(value)
        if finding.code != "CHECKLIST_ITEM_FAILED"
    ]


def _worker_evidence_bundle_structure_findings(
    value: Any,
) -> list[dict[str, str]]:
    """Validate the unchanged worker evidence-bundle schema."""
    if not isinstance(value, Mapping):
        return [
            _prepare_finding(
                "WORKER_EVIDENCE_BUNDLE_INVALID",
                "worker.evidence_bundle",
                "expected object",
            )
        ]
    findings: list[dict[str, str]] = []
    if type(value.get("version")) is not int or value.get("version") != VERSION:
        findings.append(
            _prepare_finding(
                "WORKER_EVIDENCE_BUNDLE_INVALID",
                "worker.evidence_bundle.version",
                "expected version 1",
            )
        )
    for name in ("canonical_url", "payload_text"):
        field = value.get(name)
        if not isinstance(field, str) or not field:
            findings.append(
                _prepare_finding(
                    "WORKER_EVIDENCE_BUNDLE_INVALID",
                    f"worker.evidence_bundle.{name}",
                    "expected nonempty text",
                )
            )
    for name in ("first_seen", "fetched_at"):
        if name in value and not isinstance(value[name], str):
            findings.append(
                _prepare_finding(
                    "WORKER_EVIDENCE_BUNDLE_INVALID",
                    f"worker.evidence_bundle.{name}",
                    "expected text",
                )
            )
    return findings


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
    if not isinstance(kind, str) or kind not in expected_by_kind:
        return [_prepare_finding("WORKER_KIND_INVALID", "worker.kind", str(kind))]
    if type(value.get("version")) is not int or value["version"] != VERSION:
        findings.append(
            _prepare_finding(
                "WORKER_VERSION_INVALID", "worker.version", str(value.get("version"))
            )
        )
    expected = expected_by_kind[kind]
    if set(value) != expected:
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
        if not isinstance(canonical_url, str) or not isinstance(source_id, str):
            findings.append(
                _prepare_finding(
                    "WORKER_IDENTITY_INVALID",
                    "worker.identity",
                    "canonical URL and source ID must be text",
                )
            )
        else:
            try:
                normalized_url = normalize_canonical_url(canonical_url)
            except ValueError as exc:
                findings.append(
                    _prepare_finding(
                        "WORKER_IDENTITY_INVALID",
                        "worker.identity.canonical_url",
                        str(exc),
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
        findings.extend(
            _worker_evidence_bundle_structure_findings(value.get("evidence_bundle"))
        )
        findings.extend(
            _quality_findings(
                atlas_quality.validate_proposal_structure(
                    value.get("proposal"), value.get("evidence_ledger")
                )
            )
        )
        refresh_after = value.get("refresh_after")
        if (
            not isinstance(refresh_after, str)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", refresh_after) is None
        ):
            findings.append(
                _prepare_finding(
                    "WORKER_FIELD_INVALID", "worker.refresh_after", "expected date"
                )
            )
        findings.extend(
            _quality_findings(
                _worker_checklist_structure_findings(value.get("checklist"))
            )
        )
    elif kind == "needs-input":
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason.strip():
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
                if not isinstance(child, Mapping):
                    findings.append(
                        _prepare_finding(
                            "WORKER_CHILD_INVALID",
                            f"worker.children[{index}]",
                            "child fields are invalid",
                        )
                    )
                    continue
                label = child.get("label")
                reference = child.get("reference")
                if (
                    set(child) != {"label", "reference"}
                    or not isinstance(label, str)
                    or not label.strip()
                    or not isinstance(reference, str)
                    or not reference.strip()
                ):
                    findings.append(
                        _prepare_finding(
                            "WORKER_CHILD_INVALID",
                            f"worker.children[{index}]",
                            "child fields are invalid",
                        )
                    )
    else:
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason.strip():
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
    classification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "note_type": "source-summary",
        "managed_by": "atlas",
        "primary_domain": "",
        "subdomains": [],
        "secondary_domains": [],
        "canonical_tags": [],
        "classification_status": "unclassified",
        "routing_terms": [],
        "candidate_terms": [],
        "routed_at": "",
        "last_checked": checked_on,
        "last_summarized": checked_on,
        "refresh_after": refresh_after,
        "acquired_by": "manual",
        "acquisition_run": "",
    }
    if living_artifact_text is not None:
        values = parse_artifact(living_artifact_text).values
        context["primary_domain"] = scalar(values, "primary_domain")
        context["classification_status"] = scalar(values, "classification_status")
        for key in (
            "subdomains",
            "secondary_domains",
            "canonical_tags",
            "routing_terms",
            "candidate_terms",
        ):
            context[key] = json.loads(values[key])
        context["acquired_by"] = scalar(values, "acquired_by")
        context["acquisition_run"] = scalar(values, "acquisition_run")
        if source_state["route_status"] != "unrouted":
            context["routed_at"] = checked_on
    elif source_state["route_status"] != "unrouted":
        context["routed_at"] = checked_on
    if classification is not None:
        context["classification_status"] = classification.get(
            "classification_status", "classified"
        )
        for key in (
            "primary_domain",
            "subdomains",
            "secondary_domains",
            "canonical_tags",
            "routing_terms",
            "candidate_terms",
        ):
            if key in classification:
                context[key] = classification[key]
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
    classification: Any,
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
    worker_findings = validate_worker_result(worker)
    if worker_findings:
        return {"state": "rejected", "findings": worker_findings}
    assert isinstance(worker, Mapping)
    worker_kind = worker.get("kind")
    if worker_kind in {"needs-input", "expanded"}:
        return _source_prepare_rejected(
            "WORKER_PACKET_NOT_FINAL",
            "worker.kind",
            "source preparation accepts ready or no-write packets",
        )
    state_findings = atlas_state.validate_documents(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        vocab_text=documents.get("vocab"),
    )
    if state_findings:
        return {
            "state": "rejected",
            "findings": _quality_findings(state_findings),
        }
    source_id = source_id_for(canonical_url)
    identity = worker.get("identity")
    if not isinstance(identity, Mapping):
        return _source_prepare_rejected(
            "WORKER_IDENTITY_INVALID",
            "worker.identity",
            "identity fields are invalid",
        )
    if (
        identity.get("canonical_url") != canonical_url
        or identity.get("source_id") != source_id
    ):
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
        due_after = existing["Refresh after"]
        if due_after and due_after > checked_on:
            return {
                "state": "terminal",
                "outcome": "active-not-due",
                "reason": "source refresh is not due",
            }
    if worker_kind == "no-write":
        reason = worker.get("reason")
        if not isinstance(reason, str):
            return _source_prepare_rejected(
                "WORKER_FIELD_INVALID", "worker.reason", "expected nonempty text"
            )
        return {
            "state": "terminal",
            "outcome": "no-write",
            "reason": reason,
        }
    checklist = worker.get("checklist")
    checklist_findings = atlas_quality.validate_checklist(checklist)
    if checklist_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(checklist_findings),
        }
    evidence_bundle = worker.get("evidence_bundle")
    proposal = worker.get("proposal")
    evidence_ledger = worker.get("evidence_ledger")
    refresh_after = worker.get("refresh_after")
    if (
        not isinstance(evidence_bundle, Mapping)
        or not isinstance(proposal, Mapping)
        or not isinstance(evidence_ledger, Mapping)
        or not isinstance(refresh_after, str)
    ):
        return _source_prepare_rejected(
            "WORKER_FIELD_INVALID", "worker", "ready packet fields are invalid"
        )
    effective_evidence: Mapping[str, Any] = evidence_bundle
    if "first_seen" not in evidence_bundle and "fetched_at" not in evidence_bundle:
        effective_evidence = {**evidence_bundle, "first_seen": checked_on}
    try:
        evidence = evidence_identity(effective_evidence)
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
    if "vocab" not in documents:
        return _source_prepare_rejected(
            "VOCAB_DOCUMENT_REQUIRED",
            atlas_state.VOCAB_PATH,
            "source preparation requires VOCAB",
        )
    try:
        classification = validate_classification_input(classification)
    except SourceError as exc:
        return _source_prepare_rejected(
            "SOURCE_CLASSIFICATION_REQUIRED",
            "classification",
            str(exc),
        )
    if (
        mode == "routine"
        and existing is not None
        and existing["Content hash"] == content_hash
        and classification["status"] == "classified"
    ):
        event = {
            "version": 2,
            "type": "source-upsert",
            "mode": mode,
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": existing["Artifact"],
            "first_seen": existing["First seen"],
            "checked_on": checked_on,
            "summarized_on": existing["Last summarized"],
            "content_hash": content_hash,
            "refresh_after": existing["Refresh after"],
            "source_routing_sha256": existing["Source routing SHA-256"],
            "classification_action": "replace",
            "classification_input": dict(classification),
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
    proposal_findings = atlas_quality.validate_proposal(proposal, evidence_ledger)
    if proposal_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(proposal_findings),
        }
    try:
        first_seen = (
            existing["First seen"] if existing is not None else evidence["first_seen"]
        )
        metadata = proposal.get("metadata")
        if not isinstance(metadata, Mapping):
            raise SourceError("proposal metadata is invalid")
        title = metadata.get("title")
        if not isinstance(title, str):
            raise SourceError("proposal title is invalid")
        artifact_path = (
            existing["Artifact"]
            if existing is not None
            else source_artifact_path(first_seen, source_id, title)
        )
        event = {
            "version": 2,
            "type": "source-upsert",
            "mode": mode,
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": artifact_path,
            "first_seen": first_seen,
            "checked_on": checked_on,
            "summarized_on": checked_on,
            "content_hash": content_hash,
            "refresh_after": refresh_after,
            "source_routing_sha256": "sha256:" + "0" * 64,
            "classification_action": (
                "replace"
                if classification.get("status") == "classified"
                else "mark-unclassified"
            ),
            "classification_input": dict(classification),
        }
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
        source_state = reduction.derived.get("source")
        if not isinstance(source_state, Mapping):
            raise SourceError("source reduction result is invalid")
        staged_artifact = render_summary_proposal(
            proposal,
            caller_context=_summary_context(
                checked_on=checked_on,
                refresh_after=refresh_after,
                source_state=source_state,
                living_artifact_text=living_artifact_text,
                classification=reduction.derived.get("classification"),
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
        projection = candidate_artifact_projection(artifact_text, "sha256:" + "0" * 64)
        event["source_routing_sha256"] = projection["source_routing_sha256"]
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
        source_state = reduction.derived["source"]
    except (KeyError, TypeError, ValueError) as exc:
        return _source_prepare_rejected("SOURCE_PREPARE_INVALID", "worker", str(exc))
    summary_findings = atlas_quality.validate_summary(
        artifact_text, effective_evidence, checklist
    )
    if summary_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(summary_findings),
        }
    created = bool(source_state["created"])
    content_changed = bool(source_state["content_changed"])
    routing_changed = bool(source_state["routing_changed"])
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
    result: dict[str, Any] = {
        "state": "prepared",
        "outcome": outcome,
        "route_required": (
            classification["status"] == "classified"
            and (created or content_changed or routing_changed)
        ),
        "event": event,
        "documents": reduction.documents,
        "artifact_text": artifact_text,
        "artifact_path": artifact_path,
    }
    if classification["status"] == "semantic-unavailable":
        result["findings"] = [
            {
                "code": "SOURCE_CLASSIFICATION_UNAVAILABLE",
                "path": "classification",
                "detail": classification["reason"],
            }
        ]
    return result


def prepare_stored_correction(
    documents: Mapping[str, str],
    *,
    canonical_url: str,
    source_id: str,
    artifact_path: str,
    content_hash: str,
    mode: str,
    classification: Any,
    living_artifact_text: str,
) -> dict[str, Any]:
    """Prepare a classification-only correction from one bound living summary."""
    if mode not in {"resummarize", "reroute"}:
        return _source_prepare_rejected(
            "SOURCE_PREPARE_INPUT_INVALID", "mode", "correction mode is invalid"
        )
    findings = atlas_state.validate_documents(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        vocab_text=documents.get("vocab"),
    )
    if findings:
        return {"state": "rejected", "findings": _quality_findings(findings)}
    try:
        if (
            normalize_canonical_url(canonical_url) != canonical_url
            or source_id_for(canonical_url) != source_id
        ):
            raise SourceError("stored source identity is invalid")
        classification_input = validate_classification_input(classification)
        artifact = parse_artifact(living_artifact_text)
        if render_artifact(artifact.values, artifact.body) != living_artifact_text:
            raise SourceError("living source artifact is not canonical")
        manifest_rows, manifest_findings = atlas_state.validated_manifest_rows(
            documents["manifest"]
        )
        if manifest_findings:
            return {
                "state": "rejected",
                "findings": _quality_findings(manifest_findings),
            }
        row = next(
            (
                item
                for item in manifest_rows
                if item["Source ID"] == source_id
                and item["Canonical URL"] == canonical_url
            ),
            None,
        )
        if (
            row is None
            or row["Status"] != "active"
            or row["Artifact"] != artifact_path
            or row["Content hash"] != content_hash
            or scalar(artifact.values, "source_id") != source_id
            or scalar(artifact.values, "canonical_url") != canonical_url
            or scalar(artifact.values, "content_hash") != content_hash
            or row["Source routing SHA-256"]
            != scalar(artifact.values, "source_routing_sha256")
            or row["First seen"] != scalar(artifact.values, "first_seen")
            or row["Last checked"] != scalar(artifact.values, "last_checked")
            or row["Last summarized"] != scalar(artifact.values, "last_summarized")
            or row["Refresh after"] != scalar(artifact.values, "refresh_after")
        ):
            raise SourceError("stored source binding differs from living state")
        if "vocab" not in documents:
            raise SourceError("stored correction requires VOCAB")
        action = (
            "replace"
            if classification_input["status"] == "classified"
            else "mark-unclassified"
        )
        event: dict[str, Any] = {
            "version": 2,
            "type": "source-upsert",
            "mode": mode,
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": artifact_path,
            "first_seen": scalar(artifact.values, "first_seen"),
            "checked_on": scalar(artifact.values, "last_checked"),
            "summarized_on": scalar(artifact.values, "last_summarized"),
            "content_hash": content_hash,
            "refresh_after": scalar(artifact.values, "refresh_after"),
            "source_routing_sha256": "sha256:" + "0" * 64,
            "classification_action": action,
            "classification_input": classification_input,
        }
        preliminary = atlas_state.reduce_event(documents, event)
        if not preliminary.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(preliminary.findings),
            }
        resolved = preliminary.derived.get("classification")
        source_state = preliminary.derived.get("source")
        if not isinstance(resolved, Mapping) or not isinstance(source_state, Mapping):
            raise SourceError("stored classification reduction is invalid")
        values = dict(artifact.values)
        values["classification_status"] = quoted(str(resolved["classification_status"]))
        values["primary_domain"] = quoted(str(resolved["primary_domain"]))
        for key in (
            "subdomains",
            "secondary_domains",
            "canonical_tags",
            "routing_terms",
            "candidate_terms",
        ):
            values[key] = json.dumps(
                resolved[key], ensure_ascii=False, separators=(",", ":")
            )
        route_status = str(source_state["route_status"])
        values["routing_status"] = quoted(route_status)
        values["routed_at"] = quoted(
            "" if route_status == "unrouted" else event["checked_on"]
        )
        tldr_matches = re.findall(
            r"^> \*\*TL;DR\*\*: (.+)$", artifact.body, re.MULTILINE
        )
        if len(tldr_matches) != 1:
            raise SourceError("living source TLDR is invalid")
        routing_sha256 = atlas_state.source_routing_sha256(
            {
                "classification_status": resolved["classification_status"],
                "primary_domain": resolved["primary_domain"],
                "secondary_domains": resolved["secondary_domains"],
                "subdomains": resolved["subdomains"],
                "canonical_tags": resolved["canonical_tags"],
                "routing_terms": resolved["routing_terms"],
                "title": scalar(artifact.values, "title"),
                "tldr": tldr_matches[0].strip(),
                "key_points": _candidate_body_section(artifact.body, "Key points"),
            }
        )
        values["source_routing_sha256"] = quoted(routing_sha256)
        corrected = render_artifact(values, artifact.body)
        candidate_artifact_projection(corrected, "sha256:" + "0" * 64)
        event["source_routing_sha256"] = routing_sha256
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
    except (KeyError, TypeError, ValueError) as exc:
        return _source_prepare_rejected(
            "SOURCE_CORRECTION_INVALID", "correction", str(exc)
        )
    result: dict[str, Any] = {
        "state": "prepared",
        "outcome": (
            "classification-corrected"
            if corrected != living_artifact_text
            else "unchanged"
        ),
        "route_required": (
            classification_input["status"] == "classified"
            and corrected != living_artifact_text
        ),
        "event": event,
        "documents": reduction.documents,
        "artifact_text": corrected,
        "artifact_path": artifact_path,
    }
    if classification_input["status"] == "semantic-unavailable":
        result["findings"] = [
            {
                "code": "SOURCE_CLASSIFICATION_UNAVAILABLE",
                "path": "classification",
                "detail": classification_input["reason"],
            }
        ]
    return result


def prepare_promotion(
    documents: Mapping[str, str],
    *,
    staged_artifact_text: str,
    worker: Any,
    living_artifact_text: str | None,
) -> dict[str, Any]:
    """Prepare one frozen staged artifact/evidence pair without storage I/O."""
    state_findings = atlas_state.validate_documents(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        vocab_text=documents.get("vocab"),
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
    if worker.get("kind") != "ready":
        return _source_prepare_rejected(
            "WORKER_PACKET_NOT_FINAL",
            "worker.kind",
            "promotion accepts exactly one ready evidence packet",
        )
    checklist = worker.get("checklist")
    proposal = worker.get("proposal")
    evidence_ledger = worker.get("evidence_ledger")
    evidence_bundle = worker.get("evidence_bundle")
    worker_refresh_after = worker.get("refresh_after")
    if (
        not isinstance(proposal, Mapping)
        or not isinstance(evidence_ledger, Mapping)
        or not isinstance(evidence_bundle, Mapping)
        or not isinstance(worker_refresh_after, str)
    ):
        return _source_prepare_rejected(
            "WORKER_FIELD_INVALID", "worker", "ready packet fields are invalid"
        )
    checklist_findings = atlas_quality.validate_checklist(checklist)
    if checklist_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(checklist_findings),
        }
    proposal_findings = atlas_quality.validate_proposal(proposal, evidence_ledger)
    if proposal_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(proposal_findings),
        }
    staged_findings = atlas_quality.validate_summary(
        staged_artifact_text, evidence_bundle, checklist
    )
    if staged_findings:
        return {
            "state": "needs-revision",
            "findings": _quality_findings(staged_findings),
        }
    try:
        staged = parse_artifact(staged_artifact_text)
        canonical_url = scalar(staged.values, "canonical_url")
        source_id = scalar(staged.values, "source_id")
        checked_on = scalar(staged.values, "last_checked")
        summarized_on = scalar(staged.values, "last_summarized")
        refresh_after = scalar(staged.values, "refresh_after")
        if normalize_canonical_url(canonical_url) != canonical_url:
            raise SourceError("staged canonical URL is not normalized")
        if source_id_for(canonical_url) != source_id:
            raise SourceError("staged source identity is inconsistent")
        if worker["identity"] != {
            "canonical_url": canonical_url,
            "source_id": source_id,
        }:
            raise SourceError("worker identity differs from staged artifact")
        if worker_refresh_after != refresh_after:
            raise SourceError("worker refresh date differs from staged artifact")
        effective_evidence: Mapping[str, Any] = evidence_bundle
        if (
            "first_seen" not in effective_evidence
            and "fetched_at" not in effective_evidence
        ):
            effective_evidence = {
                **effective_evidence,
                "first_seen": scalar(staged.values, "first_seen"),
            }
        evidence = evidence_identity(effective_evidence)
        if (
            evidence["canonical_url"] != canonical_url
            or evidence["source_id"] != source_id
        ):
            raise SourceError("evidence identity differs from staged artifact")
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
        if (existing is None) != (living_artifact_text is None):
            raise SourceError("living artifact presence differs from manifest")
        if living_artifact_text is not None:
            living = parse_artifact(living_artifact_text)
            if (
                scalar(living.values, "canonical_url") != canonical_url
                or scalar(living.values, "source_id") != source_id
            ):
                raise SourceError("living artifact identity differs from manifest")
        first_seen = (
            existing["First seen"] if existing is not None else evidence["first_seen"]
        )
        artifact_path = (
            existing["Artifact"]
            if existing is not None
            else source_artifact_path(
                first_seen, source_id, scalar(staged.values, "title")
            )
        )
        staged_projection = candidate_artifact_projection(
            staged_artifact_text, "sha256:" + "0" * 64
        )
        event = {
            "version": 2,
            "type": "source-upsert",
            "mode": "promote",
            "source_id": source_id,
            "canonical_url": canonical_url,
            "artifact": artifact_path,
            "first_seen": first_seen,
            "checked_on": checked_on,
            "summarized_on": summarized_on,
            "content_hash": evidence["content_hash"],
            "refresh_after": refresh_after,
            "source_routing_sha256": staged_projection["source_routing_sha256"],
            "classification_action": "preserve",
        }
        reduction = atlas_state.reduce_event(documents, event)
        if not reduction.ok:
            return {
                "state": "rejected",
                "findings": _quality_findings(reduction.findings),
            }
        source_state = reduction.derived["source"]
        artifact_text = merge_artifact(
            staged_artifact_text,
            effective_evidence,
            event,
            source_state,
            living_artifact_text=living_artifact_text,
            fresh_capture=bool(
                existing is not None
                and existing["Content hash"] != evidence["content_hash"]
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _source_prepare_rejected(
            "SOURCE_PROMOTION_INVALID", "promotion", str(exc)
        )
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
    return {
        "state": "prepared",
        "outcome": (
            "created"
            if created
            else (
                "materially-refreshed"
                if content_changed
                else "same-content-resummarized"
            )
        ),
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
        if (
            not isinstance(reason, str)
            or atlas_quality.REASON_RE.fullmatch(reason) is None
        ):
            raise SourceError("route event edge reason is invalid")
        reasons.append(f"- {reason}")

    parsed = parse_artifact(artifact_text)
    values = dict(parsed.values)
    values["routing_status"] = quoted(route_status)
    values["routed_at"] = quoted(checked_on)
    body = _replace_header(parsed.body, "Route status", f"`{route_status}`")
    body = _replace_routing_verifier_lines(body, reasons)
    return render_artifact(values, body)


def build_event_record(
    *,
    event_type: str,
    source_id: str,
    event: Mapping[str, Any],
    route_decision: Mapping[str, Any] | None,
    promotion: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if event.get("type") != event_type or event.get("source_id") != source_id:
        raise SourceError("event record identity mismatch")
    if promotion is not None:
        expected = {
            "artifact_uri",
            "artifact_revision",
            "evidence_uri",
            "evidence_revision",
        }
        if set(promotion) != expected:
            raise SourceError("promotion provenance fields are invalid")
        for name in ("artifact_uri", "evidence_uri"):
            value = promotion[name]
            if not isinstance(value, str) or not value.startswith("vault://atlas/"):
                raise SourceError(f"promotion {name} is invalid")
        for name in ("artifact_revision", "evidence_revision"):
            value = promotion[name]
            if (
                not isinstance(value, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
            ):
                raise SourceError(f"promotion {name} is invalid")
    return {
        "version": 1,
        "event_type": event_type,
        "source_id": source_id,
        "promotion": None if promotion is None else dict(promotion),
        "event": dict(event),
        "route_decision": None if route_decision is None else dict(route_decision),
    }
