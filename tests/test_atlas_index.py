from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atlas_index  # noqa: E402
import atlas_state  # noqa: E402


DOMAIN = "research"
SUBDOMAIN = "methods"
TOPIC_ID = "new-topic"
TOPIC_PATH = (
    "vault://atlas/summaries/research/research/methods/topics/new-topic/INDEX.md"
)


def table(
    header: tuple[str, ...],
    rows: list[list[str]],
    *,
    newline: str = "\n",
    final_newline: bool = True,
) -> str:
    lines = [
        "---",
        "schema_version: 1",
        "---",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    if header == atlas_state.TOPICS_HEADER:
        rows = [current_topic_row(row) for row in rows]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    value = newline.join(lines)
    return value + newline if final_newline else value


def current_topic_row(row: list[str]) -> list[str]:
    if len(row) != 16:
        return row
    decoded = [atlas_index._decode_markdown_cell(value) for value in row]

    def values(raw: str) -> list[str]:
        if not raw:
            return []
        parsed = atlas_index._parse_semicolon(raw)
        return [] if parsed is None else parsed

    digest = atlas_state.topic_routing_scope_sha256(
        {
            "topic_id": decoded[0],
            "domain": decoded[2],
            "subdomain": decoded[3],
            "canonical_title": decoded[4],
            "aliases": values(decoded[5]),
            "canonical_tags": values(decoded[6]),
            "include_terms": values(decoded[7]),
            "exclude_terms": values(decoded[8]),
        }
    )
    return [*row[:9], digest, *row[9:]]


def with_current_topic_digests(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        cells = atlas_state.split_markdown_row(line)
        if (
            cells is None
            or len(cells) != len(atlas_state.TOPICS_HEADER)
            or cells[0] in {atlas_state.TOPICS_HEADER[0], "---"}
        ):
            continue
        updated = current_topic_row([*cells[:9], *cells[10:]])
        newline = (
            "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        )
        lines[index] = "| " + " | ".join(updated) + " |" + newline
    return "".join(lines)


def registries(
    *,
    topics: list[list[str]] | None = None,
    newline: str = "\n",
    final_newline: bool = True,
) -> tuple[str, str, str]:
    return (
        table(
            atlas_state.MANIFEST_HEADER,
            [],
            newline=newline,
            final_newline=final_newline,
        ),
        table(
            atlas_state.TOPICS_HEADER,
            [current_topic_row(row) for row in (topics or [])],
            newline=newline,
            final_newline=final_newline,
        ),
        table(
            atlas_state.RELATIONS_HEADER,
            [],
            newline=newline,
            final_newline=final_newline,
        ),
    )


def vocabulary_text(
    *,
    domain_status: str = "active",
    subdomain_status: str = "active",
    domain_aliases: str = "",
    subdomain_aliases: str = "",
    newline: str = "\n",
    final_newline: bool = True,
) -> str:
    return table(
        atlas_state.VOCAB_HEADER,
        [
            [
                DOMAIN,
                "domain",
                "Research",
                "",
                domain_aliases,
                domain_status,
                "",
            ],
            [
                SUBDOMAIN,
                "subdomain",
                "Methods",
                DOMAIN,
                subdomain_aliases,
                subdomain_status,
                "",
            ],
        ],
        newline=newline,
        final_newline=final_newline,
    )


def subdomain_text(
    *, newline: str = "\n", final_newline: bool = True, note: str = ""
) -> str:
    lines = [
        "---",
        "schema_version: 1",
        "note_type: subdomain-index",
        "managed_by: atlas",
        'domain: "research"',
        'subdomain: "methods"',
        'last_updated: "2026-07-01"',
        "tags: []",
        "---",
        "",
        "# Methods",
        "",
        "## Routing scope",
        "<!-- atlas:managed:start routing-scope -->",
        "- Domain: `research`",
        "- Subdomain: `methods`",
        "- Include: methods",
        "- Exclude: none",
        "<!-- atlas:managed:end routing-scope -->",
        "",
        "## Topic map",
        "<!-- atlas:managed:start topic-map -->",
        "| Topic | Default answer | Coverage | Freshness | Last updated | Link |",
        "|---|---|---|---|---|---|",
        "<!-- atlas:managed:end topic-map -->",
        "",
        "## Default lookup order",
        "<!-- atlas:managed:start default-lookup-order -->",
        "1. Check `vault://atlas/summaries/registry/TOPICS.md` for topic path and freshness.",
        "2. Read the topic `INDEX.md` when `Freshness state=current`.",
        "3. Read optional split files only when the topic `INDEX.md` points to them.",
        "<!-- atlas:managed:end default-lookup-order -->",
        "",
        "## Coverage map",
        "<!-- atlas:managed:start coverage-map -->",
        "- Sufficient: <topics with usable current answers>",
        "- Partial: <topics with known gaps>",
        "- Insufficient: <topics needing acquisition>",
        "<!-- atlas:managed:end coverage-map -->",
        "",
        "## Stale or weak areas",
        "<!-- atlas:managed:start stale-or-weak-areas -->",
        "- <topic or gap> — <reason>",
        "<!-- atlas:managed:end stale-or-weak-areas -->",
        "",
        "## Acquisition watchlist",
        "<!-- atlas:managed:start acquisition-watchlist -->",
        "- feeds — check later",
        "<!-- atlas:managed:end acquisition-watchlist -->",
    ]
    if note:
        lines.insert(10, note)
    value = newline.join(lines)
    return value + newline if final_newline else value


def request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "version": 3,
        "topic_id": TOPIC_ID,
        "topic_path": TOPIC_PATH,
        "domain": DOMAIN,
        "subdomain": SUBDOMAIN,
        "canonical_title": "New topic",
        "aliases": [],
        "canonical_tags": [],
        "include_terms": ["methods"],
        "exclude_terms": [],
        "related_topic_ids": [],
        "status": "active",
        "coverage_state": "insufficient",
        "confidence": "low",
        "refresh_model": "same-as-topic-creation",
        "created_on": "2026-08-01",
        "vocabulary": {
            "domain": {"id": DOMAIN, "label": "Research", "aliases": []},
            "subdomain": {
                "id": SUBDOMAIN,
                "label": "Methods",
                "aliases": [],
                "parent": DOMAIN,
            },
            "tags": [],
        },
    }
    value.update(overrides)
    vocabulary = value.get("vocabulary")
    if isinstance(vocabulary, dict) and set(vocabulary) == {"domain", "subdomain"}:
        value["vocabulary"] = {**vocabulary, "tags": []}
    return value


def prepare_topic(
    request_value: object,
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    subdomain_text_or_missing: str | None,
    topic_text_or_missing: str | None,
    *,
    vocab: str | None = None,
) -> atlas_index.TopicResult:
    return atlas_index.prepare_topic(
        request_value,
        manifest_text,
        topics_text,
        relations_text,
        vocabulary_text() if vocab is None else vocab,
        subdomain_text_or_missing,
        topic_text_or_missing,
    )


def empty_snapshot(
    **kwargs: object,
) -> tuple[dict[str, object], str, str, str, str, None]:
    manifest, topics, relations = registries(
        **{
            key: value
            for key, value in kwargs.items()
            if key in {"newline", "final_newline"}
        }
    )
    return (
        request(),
        manifest,
        topics,
        relations,
        subdomain_text(
            **{
                key: value
                for key, value in kwargs.items()
                if key in {"newline", "final_newline", "note"}
            }
        ),
        None,
    )


def topic_registry_row(
    topic_id: str = "old-topic",
    title: str = "Old topic",
    *,
    freshness: str = "current",
    path_topic_id: str | None = None,
) -> list[str]:
    path_topic_id = path_topic_id or topic_id
    return [
        topic_id,
        f"summaries/research/{DOMAIN}/{SUBDOMAIN}/topics/{path_topic_id}/INDEX.md",
        DOMAIN,
        SUBDOMAIN,
        atlas_index._escape_markdown_cell(title),
        "",
        "",
        "methods",
        "",
        freshness,
        "0",
        "",
        "",
        "",
        "0",
        "same-as-topic-creation",
    ]


def subdomain_topic_row(
    topic_id: str = "old-topic",
    title: str = "Old topic",
    *,
    freshness: str = "Current",
) -> str:
    return (
        f"| {title} | Existing answer | Insufficient | {freshness} | "
        f"2026-07-01 | summaries/research/{DOMAIN}/{SUBDOMAIN}/topics/{topic_id}/INDEX.md |"
    )


def evolved_existing_snapshot() -> tuple[dict[str, object], str, str, str, str, str]:
    args = empty_snapshot()
    initial = prepare_topic(*args)
    assert isinstance(initial, atlas_index.TopicPlan)
    topic = initial.candidate_topic_bytes.decode("utf-8")
    topics = initial.candidate_topics_bytes.decode("utf-8")
    subdomain = initial.candidate_subdomain_bytes.decode("utf-8")
    topic = topic.replace('coverage_state: "insufficient"', 'coverage_state: "partial"')
    topic = topic.replace('confidence: "low"', 'confidence: "medium"')
    topic = topic.replace(
        'last_researched: "2026-08-01"', 'last_researched: "2026-08-10"'
    )
    topic = topic.replace(
        "- No evidence-backed answer exists; acquisition and research are required.",
        "- Researched guidance is available, with known gaps.",
    )
    subdomain = subdomain.replace(
        'last_updated: "2026-08-01"', 'last_updated: "2026-08-10"'
    )
    subdomain = subdomain.replace(
        "| New topic | Research required | Insufficient | Current | 2026-08-01 |",
        "| New topic | Researched guidance | Partial | Current | 2026-08-10 |",
    )
    subdomain = subdomain.replace(
        "- Partial: <topics with known gaps>", "- Partial: New topic"
    )
    subdomain = subdomain.replace("- Insufficient: New topic", "- Insufficient: none")
    subdomain = subdomain.replace(
        "- New topic — No evidence-backed answer exists; acquisition/research is required.",
        "- New topic — current partial guidance retains known gaps.",
    )
    return args[0], args[1], topics, args[3], subdomain, topic


def related_topic_path(topic_id: str) -> str:
    return f"summaries/research/{DOMAIN}/{SUBDOMAIN}/topics/{topic_id}/INDEX.md"


class AtlasIndexTests(unittest.TestCase):
    def test_absent_request_returns_exact_three_target_plan(self) -> None:
        req, manifest, topics, relations, subdomain, missing = empty_snapshot()
        result = prepare_topic(req, manifest, topics, relations, subdomain, missing)
        self.assertIsInstance(result, atlas_index.TopicPlan)
        assert isinstance(result, atlas_index.TopicPlan)
        self.assertEqual(
            result.target_paths,
            (
                TOPIC_PATH,
                atlas_index._subdomain_uri(DOMAIN, SUBDOMAIN),
                atlas_index.TOPICS_URI,
            ),
        )
        self.assertEqual(result.event_record["event_type"], "topic-create")
        self.assertEqual(result.event_record["request"], req)
        self.assertIsNone(result.transaction)
        self.assertIsNone(result.receipt)
        self.assertTrue(
            result.targets[0].output_bytes.startswith(b"---\nschema_version: 2")
        )
        self.assertEqual(result.targets[0].input_bytes, None)
        self.assertEqual(len(result.targets), 3)

    def test_absent_parent_materializes_subdomain_and_topic(self) -> None:
        req, manifest, topics, relations, _subdomain, missing = empty_snapshot()
        result = prepare_topic(req, manifest, topics, relations, missing, missing)
        self.assertIsInstance(result, atlas_index.TopicPlan)
        assert isinstance(result, atlas_index.TopicPlan)
        self.assertIsNone(result.targets[0].input_bytes)
        self.assertIsNone(result.targets[1].input_bytes)
        subdomain = result.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn("note_type: subdomain-index", subdomain)
        self.assertIn(f'domain: "{DOMAIN}"', subdomain)
        self.assertIn(f'subdomain: "{SUBDOMAIN}"', subdomain)
        self.assertIn(TOPIC_ID, subdomain)
        self.assertIn("Research required", subdomain)
        self.assertEqual(
            result.validate_post_state(
                manifest,
                result.candidate_topics_bytes.decode("utf-8"),
                relations,
                result.candidate_vocab_bytes.decode("utf-8"),
                subdomain,
                result.candidate_topic_bytes.decode("utf-8"),
            ),
            (),
        )

    def test_existing_topic_without_parent_is_invalid(self) -> None:
        req, manifest, topics, relations, _subdomain, _missing = empty_snapshot()
        findings = prepare_topic(
            req,
            manifest,
            topics,
            relations,
            atlas_index.MISSING,
            "# present topic\n",
        )
        self.assertIsInstance(findings, tuple)
        self.assertTrue(findings)
        self.assertEqual(findings[0].code, "SUBDOMAIN_INVALID")

    def test_create_updates_spaced_last_updated_key_and_validates(self) -> None:
        req, manifest, topics, relations, subdomain, missing = empty_snapshot()
        spaced = subdomain.replace(
            'last_updated: "2026-07-01"',
            'last_updated : "2026-07-01"',
        )
        plan = prepare_topic(req, manifest, topics, relations, spaced, missing)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        candidate_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn('last_updated : "2026-08-01"', candidate_subdomain)
        self.assertEqual(
            plan.validate_post_state(
                manifest,
                plan.candidate_topics_bytes.decode("utf-8"),
                relations,
                plan.candidate_vocab_bytes.decode("utf-8"),
                candidate_subdomain,
                plan.candidate_topic_bytes.decode("utf-8"),
            ),
            (),
        )

    def test_identical_inputs_are_byte_and_order_deterministic(self) -> None:
        args = empty_snapshot()
        first = prepare_topic(*args)
        second = prepare_topic(*args)
        self.assertEqual(first, second)
        self.assertIsInstance(first, atlas_index.TopicPlan)
        assert isinstance(first, atlas_index.TopicPlan)
        self.assertEqual(
            tuple(item.output_sha256 for item in first.targets),
            tuple(item.output_sha256 for item in second.targets),
        )

    def test_request_rejection_matrix(self) -> None:
        manifest, topics, relations = registries()
        base = request()
        cases = (
            ("unknown", {**base, "unexpected": True}, "args.unexpected"),
            (
                "missing",
                {key: value for key, value in base.items() if key != "created_on"},
                "args.created_on",
            ),
            ("path", {**base, "topic_path": TOPIC_PATH + "?x=1"}, "args.topic_path"),
            ("date", {**base, "created_on": "2026-02-31"}, "args.created_on"),
            ("constant", {**base, "confidence": "medium"}, "args.confidence"),
            ("unordered", {**base, "aliases": ["z", "a"]}, "args.aliases"),
            (
                "duplicate",
                {**base, "include_terms": ["methods", "methods"]},
                "args.include_terms",
            ),
        )
        for name, candidate, path in cases:
            with self.subTest(name=name):
                result = prepare_topic(
                    candidate, manifest, topics, relations, subdomain_text(), None
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(
                        item.code == "INDEX_REQUEST_INVALID" and item.path == path
                        for item in result
                    )
                )

    def test_request_invalid_key_shapes_are_safe(self) -> None:
        invalid = "\ud800"
        candidate = request()
        candidate[invalid] = True
        candidate[17] = True

        normalized, findings = atlas_index._validate_request(candidate)

        self.assertIsNone(normalized)
        self.assertEqual(
            findings,
            (
                atlas_state.Finding(
                    "INDEX_REQUEST_INVALID",
                    "args",
                    detail="field names must be strings with valid UTF-8 encoding",
                ),
            ),
        )
        for item in findings:
            self.assertNotIn(invalid, item.path)
            self.assertNotIn(invalid, item.detail)
            item.path.encode("utf-8")
            item.detail.encode("utf-8")

    def test_request_unknown_and_missing_findings_are_deterministically_sorted(
        self,
    ) -> None:
        candidate = request()
        del candidate["created_on"]
        candidate["valid-extra"] = True

        first_normalized, first_findings = atlas_index._validate_request(candidate)
        second_normalized, second_findings = atlas_index._validate_request(candidate)

        self.assertIsNone(first_normalized)
        self.assertIsNone(second_normalized)
        self.assertEqual(first_findings, second_findings)
        self.assertEqual(
            [(item.path, item.detail) for item in first_findings],
            [
                ("args.created_on", "field is missing"),
                ("args.valid-extra", "field is unknown"),
            ],
        )

    def test_invalid_utf8_array_items_are_excluded_from_array_semantics(self) -> None:
        invalid = "\ud800"
        manifest, topics, relations = registries()
        result = prepare_topic(
            request(
                aliases=[invalid, "z", "a"],
                include_terms=[invalid, "methods", "methods"],
            ),
            manifest,
            topics,
            relations,
            subdomain_text(),
            None,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        findings = {(item.code, item.path, item.detail) for item in result}
        self.assertIn(
            (
                "INDEX_REQUEST_INVALID",
                "args.aliases[0]",
                "value is not valid UTF-8",
            ),
            findings,
        )
        self.assertIn(
            (
                "INDEX_REQUEST_INVALID",
                "args.include_terms[0]",
                "value is not valid UTF-8",
            ),
            findings,
        )
        self.assertIn(
            (
                "INDEX_REQUEST_INVALID",
                "args.aliases",
                "values must be UTF-8 byte ordered",
            ),
            findings,
        )
        self.assertIn(
            (
                "INDEX_REQUEST_INVALID",
                "args.include_terms",
                "values must be unique",
            ),
            findings,
        )

    def test_related_self_and_unknown_are_distinct(self) -> None:
        manifest, topics, relations = registries()
        self_result = prepare_topic(
            request(related_topic_ids=[TOPIC_ID]),
            manifest,
            topics,
            relations,
            subdomain_text(),
            None,
        )
        self.assertIsInstance(self_result, tuple)
        assert isinstance(self_result, tuple)
        self.assertEqual([item.code for item in self_result], ["RELATED_TOPIC_SELF"])
        unknown_result = prepare_topic(
            request(related_topic_ids=["other-topic"]),
            manifest,
            topics,
            relations,
            subdomain_text(),
            None,
        )
        self.assertIsInstance(unknown_result, tuple)
        assert isinstance(unknown_result, tuple)
        self.assertEqual(
            [item.code for item in unknown_result], ["RELATED_TOPIC_UNKNOWN"]
        )

    def test_initial_shell_and_post_validator(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.targets[0].output_bytes.decode("utf-8")
        subdomain = plan.targets[1].output_bytes.decode("utf-8")
        topics = plan.targets[2].output_bytes.decode("utf-8")
        self.assertIn('status: "active"', topic)
        self.assertIn('coverage_state: "insufficient"', topic)
        self.assertIn(
            "- No evidence-backed answer exists; acquisition and research are required.",
            topic,
        )
        self.assertIn(
            "- Evidence-backed answer unavailable — acquire and research relevant sources.",
            topic,
        )
        self.assertIn(
            "| New topic | Research required | Insufficient | Current | 2026-08-01 |",
            subdomain,
        )
        self.assertIn(
            "- New topic — No evidence-backed answer exists; acquisition/research is required.",
            subdomain,
        )
        self.assertEqual(
            plan.validate_post_state(
                args[1],
                topics,
                args[3],
                plan.candidate_vocab_bytes.decode("utf-8"),
                subdomain,
                topic,
            ),
            (),
        )

    def test_compatible_existing_confirmation_preserves_bytes(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        existing = prepare_topic(
            args[0],
            args[1],
            plan.targets[2].output_bytes.decode("utf-8"),
            args[3],
            plan.targets[1].output_bytes.decode("utf-8"),
            plan.targets[0].output_bytes.decode("utf-8"),
        )
        self.assertIsInstance(existing, atlas_index.TopicConfirmation)
        assert isinstance(existing, atlas_index.TopicConfirmation)
        self.assertEqual(existing.state, "confirmed")
        self.assertIsNone(existing.transaction)
        self.assertIsNone(existing.receipt)
        self.assertEqual(existing.revisions["topic"], plan.targets[0].output_revision)

    def test_stale_title_matching_is_injective_for_ambiguous_legacy_spelling(
        self,
    ) -> None:
        title = r"\;"
        ambiguous_label = r"\;"
        canonical_label = r"\\\;"
        suffix = (
            " — No evidence-backed answer exists; acquisition/research is required."
        )
        req = request(canonical_title=title)
        manifest, topics, relations, subdomain, missing = empty_snapshot()[1:]
        plan = prepare_topic(req, manifest, topics, relations, subdomain, missing)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        self.assertEqual(atlas_index._stale_projection_label(title), canonical_label)
        self.assertEqual((len(title), len(canonical_label)), (2, 4))
        confirmed = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            plan.candidate_subdomain_bytes.decode("utf-8"),
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)
        altered_subdomain = plan.candidate_subdomain_bytes.decode("utf-8").replace(
            f"- {canonical_label}{suffix}",
            f"- {ambiguous_label}{suffix}",
            1,
        )
        self.assertNotEqual(
            altered_subdomain, plan.candidate_subdomain_bytes.decode("utf-8")
        )
        conflict = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            altered_subdomain,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(conflict, tuple)
        assert isinstance(conflict, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                and item.path == atlas_index._subdomain_uri(DOMAIN, SUBDOMAIN)
                for item in conflict
            )
        )

        legacy_title = r"Literal \u{0041}"
        legacy_req = request(canonical_title=legacy_title)
        legacy_manifest, legacy_topics, legacy_relations, legacy_subdomain, _ = (
            empty_snapshot()[1:]
        )
        legacy_plan = prepare_topic(
            legacy_req,
            legacy_manifest,
            legacy_topics,
            legacy_relations,
            legacy_subdomain,
            None,
        )
        self.assertIsInstance(legacy_plan, atlas_index.TopicPlan)
        assert isinstance(legacy_plan, atlas_index.TopicPlan)
        legacy_subdomain = legacy_plan.candidate_subdomain_bytes.decode(
            "utf-8"
        ).replace(
            atlas_index._stale_entry(legacy_title),
            f"- {legacy_title}{suffix}",
            1,
        )
        legacy_confirmed = prepare_topic(
            legacy_req,
            legacy_manifest,
            legacy_plan.candidate_topics_bytes.decode("utf-8"),
            legacy_relations,
            legacy_subdomain,
            legacy_plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(legacy_confirmed, tuple)
        assert isinstance(legacy_confirmed, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in legacy_confirmed
            )
        )

    def test_alternate_raw_topic_id_spelling_cannot_confirm(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        altered_topics = plan.candidate_topics_bytes.decode("utf-8").replace(
            "| new-topic |",
            r"| \u{6e}ew-topic |",
            1,
        )
        result = prepare_topic(
            args[0],
            args[1],
            altered_topics,
            args[3],
            plan.candidate_subdomain_bytes.decode("utf-8"),
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(result)
        self.assertTrue(all(item.code == "REGISTRY_INVALID" for item in result))

    def test_noncanonical_topic_path_is_registry_invalid(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        canonical = atlas_index._topic_relative(DOMAIN, SUBDOMAIN, TOPIC_ID)
        altered_topics = plan.candidate_topics_bytes.decode("utf-8").replace(
            f"| {canonical} |",
            f"| {canonical.removeprefix('summaries/research/research/')} |",
            1,
        )
        result = prepare_topic(
            args[0],
            args[1],
            altered_topics,
            args[3],
            plan.candidate_subdomain_bytes.decode("utf-8"),
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertEqual(tuple(item.code for item in result), ("REGISTRY_INVALID",))

    def test_registry_canonical_title_mismatch_is_compatibility_conflict(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        altered_topics = with_current_topic_digests(
            plan.candidate_topics_bytes.decode("utf-8").replace(
                "| New topic |", "| Registry title |", 1
            )
        )
        result = prepare_topic(
            args[0],
            args[1],
            altered_topics,
            args[3],
            plan.candidate_subdomain_bytes.decode("utf-8"),
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                and item.path == atlas_index.TOPICS_URI
                for item in result
            )
        )

    def test_comma_and_non_placeholder_angle_titles_create_and_confirm(self) -> None:
        for title in ("Planning, memory", "<future planning>"):
            with self.subTest(title=title):
                req = request(canonical_title=title)
                manifest, topics, relations = registries()
                subdomain = subdomain_text()
                first = prepare_topic(req, manifest, topics, relations, subdomain, None)
                second = prepare_topic(
                    req, manifest, topics, relations, subdomain, None
                )
                self.assertEqual(first, second)
                self.assertIsInstance(first, atlas_index.TopicPlan)
                assert isinstance(first, atlas_index.TopicPlan)
                rendered_subdomain = first.candidate_subdomain_bytes.decode("utf-8")
                coverage = rendered_subdomain.split(
                    "<!-- atlas:managed:start coverage-map -->\n", 1
                )[1].split("<!-- atlas:managed:end coverage-map -->", 1)[0]
                buckets = [
                    line for line in coverage.splitlines() if line.startswith("- ")
                ]
                self.assertEqual(len(buckets), 3)
                self.assertIn(f"- Insufficient: {title}", buckets)
                self.assertIn(
                    "- Sufficient: <topics with usable current answers>", buckets
                )
                self.assertIn("- Partial: <topics with known gaps>", buckets)
                confirmed = prepare_topic(
                    req,
                    manifest,
                    first.candidate_topics_bytes.decode("utf-8"),
                    relations,
                    rendered_subdomain,
                    first.candidate_topic_bytes.decode("utf-8"),
                )
                self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_delimiter_titles_create_and_confirm_with_exact_candidates(self) -> None:
        for title in ("A | B", r"Back\slash", "A; B", "Planning — memory"):
            with self.subTest(title=title):
                req = request(canonical_title=title)
                manifest, topics, relations = registries()
                subdomain = subdomain_text()
                plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
                self.assertIsInstance(plan, atlas_index.TopicPlan)
                assert isinstance(plan, atlas_index.TopicPlan)
                self.assertEqual(
                    plan.validate_post_state(
                        manifest,
                        plan.candidate_topics_bytes.decode("utf-8"),
                        relations,
                        plan.candidate_vocab_bytes.decode("utf-8"),
                        plan.candidate_subdomain_bytes.decode("utf-8"),
                        plan.candidate_topic_bytes.decode("utf-8"),
                    ),
                    (),
                )
                confirmed = prepare_topic(
                    req,
                    manifest,
                    plan.candidate_topics_bytes.decode("utf-8"),
                    relations,
                    plan.candidate_subdomain_bytes.decode("utf-8"),
                    plan.candidate_topic_bytes.decode("utf-8"),
                )
                self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_scalar_and_list_projections_roundtrip_unicode_boundaries(self) -> None:
        controls = "\r\n\v\f\x85\u2028\u2029"
        combined = r"A\\ literal \| \; \u{000b} | ; " + controls + " Z"
        aliases = [combined, "none"]
        include_terms = [combined, "memory; planning"]
        exclude_terms = [r"literal \u{000b}", "none"]
        req = request(
            canonical_title=combined,
            aliases=aliases,
            include_terms=include_terms,
            exclude_terms=exclude_terms,
        )
        manifest, topics, relations = registries()
        plan = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        topics_candidate = plan.candidate_topics_bytes.decode("utf-8")
        for projection in (topic, subdomain, topics_candidate):
            for boundary in controls[2:]:
                self.assertNotIn(boundary, projection)
        for boundary in controls:
            self.assertIn(atlas_index._unicode_escape(boundary), topic)
        parsed_topic, error = atlas_index._parse_topic_document(topic)
        self.assertIsNone(error)
        assert parsed_topic is not None
        self.assertEqual(parsed_topic["heading"], combined)
        self.assertEqual(parsed_topic["aliases"], aliases)
        self.assertEqual(parsed_topic["scope_values"]["Include"], include_terms)
        self.assertEqual(parsed_topic["scope_values"]["Exclude"], exclude_terms)
        topics_table = atlas_state._parse_table("topics", topics_candidate)
        row = atlas_index._topic_table_rows(topics_table)[0]
        self.assertEqual(
            atlas_index._row_lists(row),
            (aliases, include_terms, exclude_terms),
        )
        self.assertEqual(
            plan.validate_post_state(
                manifest,
                topics_candidate,
                relations,
                plan.candidate_vocab_bytes.decode("utf-8"),
                subdomain,
                topic,
            ),
            (),
        )
        confirmed = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            subdomain,
            topic,
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_legacy_singleton_collisions_reject_at_scope_and_table(self) -> None:
        manifest, topics, relations = registries()
        cases = (
            ("delimiter", "a; b", r"a\; b"),
            ("empty sentinel", "none", r"\u{006e}one"),
        )
        for name, canonical_value, literal_value in cases:
            req = request(include_terms=[literal_value])
            plan = prepare_topic(
                req, manifest, topics, relations, subdomain_text(), None
            )
            self.assertIsInstance(plan, atlas_index.TopicPlan)
            assert isinstance(plan, atlas_index.TopicPlan)
            topic = plan.candidate_topic_bytes.decode("utf-8")
            subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
            registry = plan.candidate_topics_bytes.decode("utf-8")
            literal_scope = atlas_index._list_projection_value(
                [literal_value], empty="none"
            )
            canonical_scope = atlas_index._list_projection_value(
                [canonical_value], empty="none"
            )
            literal_table = atlas_index._escape_markdown_cell(
                atlas_index._list_projection_value([literal_value], empty="")
            )
            canonical_table = atlas_index._escape_markdown_cell(
                atlas_index._list_projection_value([canonical_value], empty="")
            )

            with self.subTest(name=name, projection="topic scope"):
                altered_topic = topic.replace(
                    f"- Include: {literal_scope}",
                    f"- Include: {canonical_scope}",
                    1,
                )
                self.assertNotEqual(altered_topic, topic)
                result = prepare_topic(
                    req,
                    manifest,
                    registry,
                    relations,
                    subdomain,
                    altered_topic,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(
                        item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                        and item.detail == "scope Include disagrees with request"
                        for item in result
                    )
                )

            with self.subTest(name=name, projection="TOPICS table"):
                altered_registry = registry.replace(literal_table, canonical_table, 1)
                altered_registry = with_current_topic_digests(altered_registry)
                self.assertNotEqual(altered_registry, registry)
                result = prepare_topic(
                    req,
                    manifest,
                    altered_registry,
                    relations,
                    subdomain,
                    topic,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(
                        item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                        and item.detail
                        == "canonical include terms disagree with request"
                        for item in result
                    )
                )

    def test_literal_none_is_distinct_from_empty_scope_and_table_lists(self) -> None:
        req = request(aliases=["none"], include_terms=["none"], exclude_terms=["none"])
        manifest, topics, relations = registries()
        plan = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        topics_candidate = plan.candidate_topics_bytes.decode("utf-8")
        parsed_topic, error = atlas_index._parse_topic_document(topic)
        self.assertIsNone(error)
        assert parsed_topic is not None
        self.assertEqual(parsed_topic["scope_values"]["Include"], ["none"])
        self.assertEqual(parsed_topic["scope_values"]["Exclude"], ["none"])
        topics_table = atlas_state._parse_table("topics", topics_candidate)
        self.assertEqual(
            atlas_index._row_lists(atlas_index._topic_table_rows(topics_table)[0]),
            (["none"], ["none"], ["none"]),
        )
        self.assertNotEqual(
            next(line for line in topic.splitlines() if line.startswith("- Include:")),
            "- Include: none",
        )
        confirmed = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            plan.candidate_subdomain_bytes.decode("utf-8"),
            topic,
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_coverage_insertion_preserves_existing_raw_items_and_separators(
        self,
    ) -> None:
        cases = (
            (
                "new-topic",
                TOPIC_PATH,
                "New topic",
                "Alpha ;  Beta",
            ),
            (
                "z-topic",
                "vault://atlas/summaries/research/research/methods/topics/z-topic/INDEX.md",
                "Zed",
                "Alpha;Beta",
            ),
        )
        for topic_id, topic_path, title, raw_value in cases:
            with self.subTest(topic_id=topic_id):
                req = request(
                    topic_id=topic_id, topic_path=topic_path, canonical_title=title
                )
                manifest, topics, relations = registries(
                    topics=[topic_registry_row("old-topic", "Alpha")]
                )
                subdomain = (
                    subdomain_text()
                    .replace(
                        "<!-- atlas:managed:end topic-map -->",
                        subdomain_topic_row("old-topic", "Alpha")
                        + "\n<!-- atlas:managed:end topic-map -->",
                    )
                    .replace(
                        "- <topic or gap> — <reason>",
                        "- Alpha — existing stale membership\n- <topic or gap> — <reason>",
                        1,
                    )
                    .replace(
                        "- Insufficient: <topics needing acquisition>",
                        "- Insufficient: " + raw_value,
                    )
                )
                plan = prepare_topic(
                    req,
                    manifest,
                    topics,
                    relations,
                    subdomain,
                    None,
                )
                self.assertIsInstance(plan, atlas_index.TopicPlan)
                assert isinstance(plan, atlas_index.TopicPlan)
                rendered = plan.candidate_subdomain_bytes.decode("utf-8")
                coverage_line = next(
                    line
                    for line in rendered.splitlines()
                    if line.startswith("- Insufficient:")
                )
                encoded_title = atlas_index._encode_projection_value(title)
                self.assertEqual(
                    coverage_line.removeprefix("- Insufficient: "),
                    (
                        encoded_title + "; " + raw_value
                        if topic_id == "new-topic"
                        else raw_value + "; " + encoded_title
                    ),
                )
                self.assertIn(raw_value, coverage_line)
                self.assertIn(
                    "- Sufficient: <topics with usable current answers>",
                    rendered,
                )
                self.assertIn("- Partial: <topics with known gaps>", rendered)

    def test_middle_coverage_insertion_preserves_original_separator_bytes(self) -> None:
        req = request(
            topic_id="middle-topic",
            topic_path="vault://atlas/summaries/research/research/methods/topics/middle-topic/INDEX.md",
            canonical_title="Middle",
        )
        manifest, topics, relations = registries(
            topics=[
                topic_registry_row("alpha-topic", "Alpha"),
                topic_registry_row("zulu-topic", "Zulu"),
            ]
        )
        original = r"Alpha \; one ;  Zulu\\path"
        subdomain = subdomain_text()
        subdomain = (
            subdomain.replace(
                "<!-- atlas:managed:end topic-map -->",
                subdomain_topic_row("alpha-topic", "Alpha")
                + "\n"
                + subdomain_topic_row("zulu-topic", r"Zulu\path")
                + "\n<!-- atlas:managed:end topic-map -->",
            )
            .replace(
                "- <topic or gap> — <reason>",
                "- Alpha — existing stale membership\n"
                r"- Zulu\\path — existing stale membership"
                "\n- <topic or gap> — <reason>",
                1,
            )
            .replace(
                "- Insufficient: <topics needing acquisition>",
                "- Insufficient: " + original,
            )
        )
        plan = prepare_topic(
            req,
            manifest,
            topics,
            relations,
            subdomain,
            None,
        )
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        rendered = plan.candidate_subdomain_bytes.decode("utf-8")
        coverage_line = next(
            line for line in rendered.splitlines() if line.startswith("- Insufficient:")
        )
        self.assertEqual(
            coverage_line.removeprefix("- Insufficient: "),
            r"Alpha \; one ;Middle;   Zulu\\path",
        )

    def test_duplicate_or_unknown_scope_lines_cannot_confirm(self) -> None:
        req = request()
        manifest, topics, relations = registries()
        plan = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        cases = (
            topic.replace(
                "- Include: methods\n",
                "- Include: wrong\n- Include: methods\n",
                1,
            ),
            topic.replace(
                "- Include: methods\n",
                "- Unknown: value\n- Include: methods\n",
                1,
            ),
        )
        for altered in cases:
            with self.subTest(altered=altered):
                result = prepare_topic(
                    req,
                    manifest,
                    plan.candidate_topics_bytes.decode("utf-8"),
                    relations,
                    plan.candidate_subdomain_bytes.decode("utf-8"),
                    altered,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in result)
                )

    def test_coverage_values_use_semicolons_without_splitting_commas(self) -> None:
        req = request(canonical_title="Planning, memory")
        manifest, topics, relations = registries()
        subdomain = subdomain_text().replace(
            "- Insufficient: <topics needing acquisition>",
            "- Insufficient: Existing, title; Another topic",
        )
        result = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(result, atlas_index.TopicPlan)
        assert isinstance(result, atlas_index.TopicPlan)
        rendered = result.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn(
            "- Insufficient: Existing, title; Another topic; Planning, memory",
            rendered,
        )
        coverage = rendered.split("<!-- atlas:managed:start coverage-map -->\n", 1)[
            1
        ].split("<!-- atlas:managed:end coverage-map -->", 1)[0]
        self.assertEqual(
            [line for line in coverage.splitlines() if line.startswith("- ")],
            [
                "- Sufficient: <topics with usable current answers>",
                "- Partial: <topics with known gaps>",
                "- Insufficient: Existing, title; Another topic; Planning, memory",
            ],
        )

    def test_exact_scaffold_titles_are_real_memberships_when_requested(self) -> None:
        titles = tuple(atlas_index.COVERAGE_PLACEHOLDERS.values()) + ("<topic or gap>",)
        for title in titles:
            with self.subTest(title=title):
                req = request(canonical_title=title)
                manifest, topics, relations = registries()
                plan = prepare_topic(
                    req, manifest, topics, relations, subdomain_text(), None
                )
                self.assertIsInstance(plan, atlas_index.TopicPlan)
                assert isinstance(plan, atlas_index.TopicPlan)
                rendered_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
                self.assertIn(f"- Insufficient: {title}", rendered_subdomain)
                self.assertIn(
                    f"- {title} — No evidence-backed answer exists; acquisition/research is required.",
                    rendered_subdomain,
                )
                confirmed = prepare_topic(
                    req,
                    manifest,
                    plan.candidate_topics_bytes.decode("utf-8"),
                    relations,
                    rendered_subdomain,
                    plan.candidate_topic_bytes.decode("utf-8"),
                )
                self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_duplicate_title_memberships_are_rendered_and_confirmed_independently(
        self,
    ) -> None:
        old_row = topic_registry_row("old-topic", "Planning")
        manifest, topics, relations = registries(topics=[old_row])
        subdomain = subdomain_text().replace(
            "<!-- atlas:managed:end topic-map -->",
            subdomain_topic_row("old-topic", "Planning")
            + "\n<!-- atlas:managed:end topic-map -->",
        )
        subdomain = subdomain.replace(
            "- Insufficient: <topics needing acquisition>",
            "- Insufficient: Planning; Unrelated",
        ).replace(
            "- <topic or gap> — <reason>",
            "- Planning — existing stale membership\n- Unrelated — preserve this entry",
        )
        req = request(canonical_title="Planning")
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        rendered_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn(
            "- Insufficient: Planning; Planning; Unrelated", rendered_subdomain
        )
        self.assertIn("- Planning — existing stale membership", rendered_subdomain)
        self.assertIn(
            "- Planning — No evidence-backed answer exists; acquisition/research is required.",
            rendered_subdomain,
        )
        self.assertIn("- Unrelated — preserve this entry", rendered_subdomain)
        confirmed = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            rendered_subdomain,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

        wrong_bucket = rendered_subdomain.replace(
            "- Partial: <topics with known gaps>",
            "- Partial: <topics with known gaps>; Planning",
        )
        conflict = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            wrong_bucket,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(conflict, tuple)
        assert isinstance(conflict, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in conflict)
        )

    def test_evolved_topic_confirms_matching_current_projection(self) -> None:
        req, manifest, topics, relations, subdomain, topic = evolved_existing_snapshot()
        result = prepare_topic(req, manifest, topics, relations, subdomain, topic)
        self.assertIsInstance(result, atlas_index.TopicConfirmation)
        assert isinstance(result, atlas_index.TopicConfirmation)
        self.assertEqual(result.state, "confirmed")
        self.assertEqual(result.output_bytes, ())
        self.assertEqual(
            result.revisions,
            {
                "vocab": "sha256:"
                + atlas_index.sha256(vocabulary_text().encode("utf-8")),
                "topic": "sha256:" + atlas_index.sha256(topic.encode("utf-8")),
                "subdomain": "sha256:" + atlas_index.sha256(subdomain.encode("utf-8")),
                "registry": "sha256:" + atlas_index.sha256(topics.encode("utf-8")),
            },
        )

    def test_evolved_initial_answer_still_requires_stale_membership(self) -> None:
        req, manifest, topics, relations, subdomain, missing = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, missing)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        topic = topic.replace(
            'coverage_state: "insufficient"', 'coverage_state: "sufficient"'
        )
        topic = topic.replace('confidence: "low"', 'confidence: "medium"')
        topic = topic.replace(
            'last_researched: "2026-08-01"', 'last_researched: "2026-08-10"'
        )
        evolved_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        evolved_subdomain = evolved_subdomain.replace(
            "| New topic | Research required | Insufficient | Current | 2026-08-01 |",
            "| New topic | Research required | Sufficient | Current | 2026-08-10 |",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Sufficient: <topics with usable current answers>",
            "- Sufficient: New topic",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Insufficient: New topic", "- Insufficient: none"
        )
        confirmed = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            evolved_subdomain,
            topic,
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_duplicate_requested_stale_projection_cannot_confirm(self) -> None:
        req, manifest, topics, relations, subdomain, missing = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, missing)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        candidate_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        stale_entry = (
            "- New topic — No evidence-backed answer exists; "
            "acquisition/research is required."
        )
        duplicated_subdomain = candidate_subdomain.replace(
            stale_entry,
            stale_entry + "\n" + stale_entry,
        )
        self.assertNotEqual(duplicated_subdomain, candidate_subdomain)
        result = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            duplicated_subdomain,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                and item.detail
                == "requested topic stale-or-weak projection is missing or duplicated"
                for item in result
            )
        )

    def test_required_stale_title_id_collision_cannot_confirm(self) -> None:
        req = request(canonical_title="old-topic")
        manifest, topics, relations = registries()
        plan = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        unrelated = topic_registry_row("old-topic", "Unrelated")
        topics_with_unrelated = table(
            atlas_state.TOPICS_HEADER,
            [unrelated, topic_registry_row(TOPIC_ID, "old-topic")],
        )
        candidate_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        candidate_subdomain = candidate_subdomain.replace(
            "<!-- atlas:managed:end topic-map -->",
            subdomain_topic_row("old-topic", "Unrelated")
            + "\n<!-- atlas:managed:end topic-map -->",
        )
        self.assertIn(atlas_index._stale_entry("old-topic"), candidate_subdomain)
        result = prepare_topic(
            req,
            manifest,
            topics_with_unrelated,
            relations,
            candidate_subdomain,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                and item.detail
                == "requested topic stale-or-weak projection is missing or duplicated"
                for item in result
            )
        )

    def test_sufficient_current_title_id_collision_is_unrelated(self) -> None:
        req = request(canonical_title="old-topic")
        manifest, topics, relations = registries()
        plan = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        unrelated = topic_registry_row("old-topic", "Unrelated")
        topics_with_unrelated = table(
            atlas_state.TOPICS_HEADER,
            [unrelated, topic_registry_row(TOPIC_ID, "old-topic")],
        )
        topic = plan.candidate_topic_bytes.decode("utf-8")
        topic = topic.replace(
            'coverage_state: "insufficient"', 'coverage_state: "sufficient"'
        )
        topic = topic.replace('confidence: "low"', 'confidence: "medium"')
        topic = topic.replace(
            'last_researched: "2026-08-01"', 'last_researched: "2026-08-10"'
        )
        topic = topic.replace(
            "- No evidence-backed answer exists; acquisition and research are required.",
            "- Researched guidance is available, with known gaps.",
        )
        evolved_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        evolved_subdomain = evolved_subdomain.replace(
            "<!-- atlas:managed:end topic-map -->",
            subdomain_topic_row("old-topic", "Unrelated")
            + "\n<!-- atlas:managed:end topic-map -->",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "| old-topic | Research required | Insufficient | Current | 2026-08-01 | "
            "summaries/research/research/methods/topics/new-topic/INDEX.md |",
            "| old-topic | Researched guidance | Sufficient | Current | 2026-08-10 | "
            "summaries/research/research/methods/topics/new-topic/INDEX.md |",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Sufficient: <topics with usable current answers>",
            "- Sufficient: old-topic",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Insufficient: old-topic", "- Insufficient: <topics needing acquisition>"
        )
        confirmed = prepare_topic(
            req,
            manifest,
            topics_with_unrelated,
            relations,
            evolved_subdomain,
            topic,
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)

    def test_stale_membership_uses_the_longest_complete_title(self) -> None:
        req = request(canonical_title="Alpha")
        old_row = topic_registry_row("old-topic", "Alpha — Beta")
        manifest, topics, relations = registries(topics=[old_row])
        old_map_row = subdomain_topic_row("old-topic", "Alpha — Beta").replace(
            "| Alpha — Beta | Existing answer | Insufficient |",
            "| Alpha — Beta | Existing answer | Sufficient |",
        )
        subdomain = subdomain_text().replace(
            "<!-- atlas:managed:end topic-map -->",
            old_map_row + "\n<!-- atlas:managed:end topic-map -->",
        )
        subdomain = subdomain.replace(
            "- Sufficient: <topics with usable current answers>",
            "- Sufficient: Alpha — Beta",
        ).replace(
            "- <topic or gap> — <reason>",
            "- Alpha — Beta — stale reason",
        )
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)

        topic = plan.candidate_topic_bytes.decode("utf-8")
        topic = topic.replace(
            'coverage_state: "insufficient"', 'coverage_state: "partial"'
        )
        topic = topic.replace('confidence: "low"', 'confidence: "medium"')
        topic = topic.replace(
            'last_researched: "2026-08-01"', 'last_researched: "2026-08-10"'
        )
        topic = topic.replace(
            "- No evidence-backed answer exists; acquisition and research are required.",
            "- Researched guidance is available, with known gaps.",
        )
        evolved_subdomain = plan.candidate_subdomain_bytes.decode("utf-8")
        evolved_subdomain = evolved_subdomain.replace(
            "| Alpha | Research required | Insufficient | Current | 2026-08-01 |",
            "| Alpha | Researched guidance | Partial | Current | 2026-08-10 |",
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Partial: <topics with known gaps>", "- Partial: Alpha"
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Insufficient: Alpha", "- Insufficient: none"
        )
        evolved_subdomain = evolved_subdomain.replace(
            "- Alpha — No evidence-backed answer exists; acquisition/research is required.\n",
            "",
        )
        result = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            evolved_subdomain,
            topic,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in result)
        )

    def test_evolved_topic_projection_mismatch_is_conflict(self) -> None:
        req, manifest, topics, relations, subdomain, topic = evolved_existing_snapshot()
        altered = subdomain.replace("- Partial: New topic", "- Partial: none")
        altered = altered.replace("- Insufficient: none", "- Insufficient: New topic")
        result = prepare_topic(req, manifest, topics, relations, altered, topic)
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in result)
        )

    def test_evolved_sufficient_current_allows_no_stale_projection(self) -> None:
        req, manifest, topics, relations, subdomain, topic = evolved_existing_snapshot()
        topic = topic.replace(
            'coverage_state: "partial"', 'coverage_state: "sufficient"'
        )
        subdomain = subdomain.replace(
            "| New topic | Researched guidance | Partial | Current | 2026-08-10 |",
            "| New topic | Researched guidance | Sufficient | Current | 2026-08-10 |",
        )
        subdomain = subdomain.replace(
            "- Sufficient: <topics with usable current answers>",
            "- Sufficient: New topic",
        )
        subdomain = subdomain.replace(
            "- Partial: New topic", "- Partial: <topics with known gaps>"
        )
        subdomain = subdomain.replace(
            "- New topic — current partial guidance retains known gaps.\n", ""
        )
        confirmed = prepare_topic(req, manifest, topics, relations, subdomain, topic)
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)
        assert isinstance(confirmed, atlas_index.TopicConfirmation)
        self.assertEqual(confirmed.output_bytes, ())
        self.assertEqual(
            confirmed.revisions,
            {
                "vocab": "sha256:"
                + atlas_index.sha256(vocabulary_text().encode("utf-8")),
                "topic": "sha256:" + atlas_index.sha256(topic.encode("utf-8")),
                "subdomain": "sha256:" + atlas_index.sha256(subdomain.encode("utf-8")),
                "registry": "sha256:" + atlas_index.sha256(topics.encode("utf-8")),
            },
        )
        with_stale = subdomain.replace(
            "<!-- atlas:managed:end stale-or-weak-areas -->",
            "- New topic — stale entry\n<!-- atlas:managed:end stale-or-weak-areas -->",
        )
        conflict = prepare_topic(req, manifest, topics, relations, with_stale, topic)
        self.assertIsInstance(conflict, tuple)
        assert isinstance(conflict, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in conflict)
        )

    def test_related_topic_links_use_canonical_paths_in_request_order(self) -> None:
        related = ["another-topic", "old-topic"]
        req = request(related_topic_ids=related)
        manifest, topics, relations = registries(
            topics=[
                topic_registry_row("old-topic", "Old topic"),
                topic_registry_row("another-topic", "Another topic"),
            ]
        )
        subdomain = subdomain_text()
        first = prepare_topic(req, manifest, topics, relations, subdomain, None)
        second = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertEqual(first, second)
        self.assertIsInstance(first, atlas_index.TopicPlan)
        assert isinstance(first, atlas_index.TopicPlan)
        rendered = first.candidate_topic_bytes.decode("utf-8")
        read_next = rendered.split("<!-- atlas:managed:start read-next -->\n", 1)[
            1
        ].split("<!-- atlas:managed:end read-next -->", 1)[0]
        self.assertEqual(
            read_next,
            (
                f"- [Another topic]({related_topic_path('another-topic')})\n"
                f"- [Old topic]({related_topic_path('old-topic')})\n"
            ),
        )

    def test_related_topic_paths_must_match_canonical_identity(self) -> None:
        canonical = related_topic_path("old-topic")
        cases = (
            ("external", "https://example.invalid/topic"),
            ("mismatch", canonical.replace("old-topic", "other-topic")),
            ("query", canonical + "?view=full"),
            ("fragment", canonical + "#read-next"),
            (
                "traversal",
                "summaries/research/research/methods/topics/../old-topic/INDEX.md",
            ),
            (
                "identity-confused",
                "summaries/research/other/methods/topics/old-topic/INDEX.md",
            ),
        )
        for name, invalid_path in cases:
            with self.subTest(name=name):
                row = topic_registry_row()
                row[1] = invalid_path
                manifest, topics, relations = registries(topics=[row])
                result = prepare_topic(
                    request(related_topic_ids=["old-topic"]),
                    manifest,
                    topics,
                    relations,
                    subdomain_text(),
                    None,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertFalse(
                    any(isinstance(item, atlas_index.TopicPlan) for item in result)
                )
                self.assertTrue(
                    any(
                        item.code == "REGISTRY_INVALID"
                        and item.path == atlas_index.TOPICS_URI
                        and item.row == "old-topic"
                        for item in result
                    )
                )

    def test_related_topic_labels_escape_backslashes_and_brackets(self) -> None:
        raw_title = r"Back\slash [topic] ]("
        req = request(related_topic_ids=["old-topic"])
        manifest, topics, relations = registries(
            topics=[topic_registry_row("old-topic", raw_title)]
        )
        result = prepare_topic(req, manifest, topics, relations, subdomain_text(), None)
        self.assertIsInstance(result, atlas_index.TopicPlan)
        assert isinstance(result, atlas_index.TopicPlan)
        escaped = (
            raw_title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        )
        rendered = result.candidate_topic_bytes.decode("utf-8")
        read_next = rendered.split("<!-- atlas:managed:start read-next -->\n", 1)[
            1
        ].split("<!-- atlas:managed:end read-next -->", 1)[0]
        self.assertEqual(
            read_next,
            f"- [{escaped}]({related_topic_path('old-topic')})\n",
        )
        registry_table = atlas_state._parse_table(
            "topics",
            result.candidate_topics_bytes.decode("utf-8"),
        )
        related_row = next(
            row
            for row in atlas_index._topic_table_rows(registry_table)
            if row["Topic ID"] == "old-topic"
        )
        self.assertEqual(related_row["Canonical title"], raw_title)

    def test_existing_structural_mismatch_is_conflict_not_confirmation(self) -> None:
        args = empty_snapshot()
        plan = prepare_topic(*args)
        assert isinstance(plan, atlas_index.TopicPlan)
        altered = (
            plan.targets[0]
            .output_bytes.decode("utf-8")
            .replace("# New topic", "# Other topic")
        )
        result = prepare_topic(
            args[0],
            args[1],
            plan.targets[2].output_bytes.decode("utf-8"),
            args[3],
            plan.targets[1].output_bytes.decode("utf-8"),
            altered,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in result)
        )

    def test_crlf_and_no_final_newline_are_preserved_for_existing_inputs(self) -> None:
        args = empty_snapshot(newline="\r\n", final_newline=False)
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        self.assertIn(b"\r\n", plan.targets[1].output_bytes)
        self.assertFalse(plan.targets[1].output_bytes.endswith(b"\r\n"))
        self.assertFalse(plan.targets[2].output_bytes.endswith(b"\r\n"))
        self.assertIn(b"\r\n", plan.targets[0].output_bytes)

    def test_unmanaged_subdomain_bytes_are_retained(self) -> None:
        args = empty_snapshot(note="User note: preserve this exact line.")
        plan = prepare_topic(*args)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        output = plan.targets[1].output_bytes.decode("utf-8")
        self.assertIn("User note: preserve this exact line.", output)
        self.assertIn("- feeds — check later", output)

    def test_orphan_and_invalid_registry_families(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        orphan_row = [
            TOPIC_ID,
            "summaries/research/research/methods/topics/new-topic/INDEX.md",
            DOMAIN,
            SUBDOMAIN,
            "New topic",
            "",
            "",
            "methods",
            "",
            "current",
            "0",
            "",
            "",
            "",
            "0",
            "same-as-topic-creation",
        ]
        result = prepare_topic(
            req,
            manifest,
            table(atlas_state.TOPICS_HEADER, [orphan_row]),
            relations,
            subdomain,
            None,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "TOPIC_ORPHAN" for item in result))
        malformed = topics.replace("Topic ID", "Topic ID broken", 1)
        result = prepare_topic(req, manifest, malformed, relations, subdomain, None)
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "REGISTRY_INVALID" for item in result))

    def test_subdomain_rejection_matrix(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        cases = (
            (
                "frontmatter",
                subdomain.replace("note_type: subdomain-index", "note_type: wrong"),
            ),
            (
                "marker",
                subdomain.replace(
                    "atlas:managed:end topic-map", "atlas:managed:end topic-map-broken"
                ),
            ),
            (
                "coverage",
                subdomain.replace(
                    "- Partial: <topics with known gaps>",
                    "- Partial: broken\n- Partial: duplicate",
                ),
            ),
            ("topic-map", subdomain.replace("|---|---|---|---|---|---|", "|---|---|")),
        )
        for name, candidate in cases:
            with self.subTest(name=name):
                result = prepare_topic(
                    req, manifest, topics, relations, candidate, None
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(
                        item.code
                        in {"SUBDOMAIN_INVALID", "SUBDOMAIN_PROJECTION_INVALID"}
                        for item in result
                    )
                )

    def test_crossed_nested_and_out_of_order_markers_reject_for_both_documents(
        self,
    ) -> None:
        for names in (atlas_index.SUBDOMAIN_MARKERS, atlas_index.TOPIC_MARKERS):
            first, second = names[:2]
            remaining = names[2:]

            def pairs_for(prefix: list[str]) -> list[str]:
                return prefix + [
                    item
                    for name in remaining
                    for item in (
                        f"<!-- atlas:managed:start {name} -->",
                        f"<!-- atlas:managed:end {name} -->",
                    )
                ]

            malformed_cases = (
                pairs_for(
                    [
                        f"<!-- atlas:managed:start {first} -->",
                        f"<!-- atlas:managed:start {second} -->",
                        f"<!-- atlas:managed:end {first} -->",
                        f"<!-- atlas:managed:end {second} -->",
                    ]
                ),
                pairs_for(
                    [
                        f"<!-- atlas:managed:start {first} -->",
                        f"<!-- atlas:managed:start {second} -->",
                        f"<!-- atlas:managed:end {second} -->",
                        f"<!-- atlas:managed:end {first} -->",
                    ]
                ),
                pairs_for(
                    [
                        f"<!-- atlas:managed:start {second} -->",
                        f"<!-- atlas:managed:end {second} -->",
                        f"<!-- atlas:managed:start {first} -->",
                        f"<!-- atlas:managed:end {first} -->",
                    ]
                ),
            )
            for malformed in malformed_cases:
                pairs, error = atlas_index._marker_pairs(malformed, names)
                self.assertEqual(pairs, {})
                self.assertIsNotNone(error)

    def test_requested_projection_mismatch_is_not_baseline_drift(self) -> None:
        req, manifest, empty_topics, relations, subdomain, _ = empty_snapshot()
        existing_topics = table(atlas_state.TOPICS_HEADER, [topic_registry_row()])
        existing_map = subdomain.replace(
            "<!-- atlas:managed:end topic-map -->",
            subdomain_topic_row()
            + "\n"
            + subdomain_topic_row(TOPIC_ID, "New topic")
            + "\n<!-- atlas:managed:end topic-map -->",
        )
        # The requested topic ID is absent, so an unrelated map row is a
        # baseline entry and is retained; a row for the request is an orphan.
        baseline_result = prepare_topic(
            req, manifest, existing_topics, relations, existing_map, None
        )
        self.assertIsInstance(baseline_result, tuple)
        assert isinstance(baseline_result, tuple)
        self.assertTrue(
            any(item.code == "SUBDOMAIN_PROJECTION_INVALID" for item in baseline_result)
        )

        plan = prepare_topic(req, manifest, empty_topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        altered_map = plan.candidate_subdomain_bytes.decode("utf-8").replace(
            "| New topic | Research required | Insufficient | Current | 2026-08-01 |",
            "| New topic | Research required | Partial | Current | 2026-08-01 |",
        )
        confirmation = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            altered_map,
            plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(confirmation, tuple)
        assert isinstance(confirmation, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in confirmation)
        )

    def test_id_and_path_conflicts_are_not_plans(self) -> None:
        req, manifest, _, relations, subdomain, _ = empty_snapshot()

        id_row = topic_registry_row(TOPIC_ID, "Other path")
        result = prepare_topic(
            req,
            manifest,
            table(atlas_state.TOPICS_HEADER, [id_row]),
            relations,
            subdomain,
            None,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "TOPIC_ORPHAN" for item in result))

        path_row = topic_registry_row(
            "other-topic", "Other topic", path_topic_id=TOPIC_ID
        )
        result = prepare_topic(
            req,
            manifest,
            table(atlas_state.TOPICS_HEADER, [path_row]),
            relations,
            subdomain,
            None,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "REGISTRY_INVALID" for item in result))

    def test_baseline_topic_map_drift_is_carried_and_unchanged(self) -> None:
        req, manifest, _, relations, subdomain, _ = empty_snapshot()
        old_topics = table(atlas_state.TOPICS_HEADER, [topic_registry_row()])
        drifted_map = subdomain.replace(
            "<!-- atlas:managed:end topic-map -->",
            subdomain_topic_row(freshness="Dirty")
            + "\n<!-- atlas:managed:end topic-map -->",
        )
        result = prepare_topic(req, manifest, old_topics, relations, drifted_map, None)
        self.assertIsInstance(result, atlas_index.TopicPlan)
        assert isinstance(result, atlas_index.TopicPlan)
        self.assertTrue(
            any(
                item.code == "SUBDOMAIN_TOPIC_MAP_DRIFT"
                for item in result.baseline_findings
            )
        )
        output = result.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn(subdomain_topic_row(freshness="Dirty"), output)
        self.assertIn(
            "| New topic | Research required | Insufficient | Current | 2026-08-01 |",
            output,
        )

    def test_unrelated_decoder_equivalent_link_spelling_is_baseline_drift(self) -> None:
        request_value, manifest, empty_topics, relations, subdomain, _ = (
            empty_snapshot()
        )
        topics = table(atlas_state.TOPICS_HEADER, [topic_registry_row()])
        escaped_link = r"summaries/research/research/methods/topics/old\-topic/INDEX.md"
        unrelated_row = subdomain_topic_row().replace(
            "summaries/research/research/methods/topics/old-topic/INDEX.md",
            escaped_link,
        )
        unrelated = subdomain.replace(
            "<!-- atlas:managed:end topic-map -->",
            unrelated_row + "\n<!-- atlas:managed:end topic-map -->",
        )
        plan = prepare_topic(
            request_value, manifest, topics, relations, unrelated, None
        )
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        self.assertTrue(
            any(
                item.code == "SUBDOMAIN_TOPIC_MAP_DRIFT"
                for item in plan.baseline_findings
            )
        )
        rendered = plan.candidate_subdomain_bytes.decode("utf-8")
        self.assertIn(escaped_link, rendered)
        self.assertIn(unrelated_row, rendered)

        malformed = unrelated.replace(escaped_link, escaped_link.replace("md", "txt"))
        rejected = prepare_topic(
            request_value, manifest, topics, relations, malformed, None
        )
        self.assertIsInstance(rejected, tuple)
        assert isinstance(rejected, tuple)
        self.assertTrue(
            any(item.code == "SUBDOMAIN_PROJECTION_INVALID" for item in rejected)
        )

        canonical_plan = prepare_topic(
            request_value, manifest, empty_topics, relations, subdomain, None
        )
        assert isinstance(canonical_plan, atlas_index.TopicPlan)
        requested_spelling = canonical_plan.candidate_subdomain_bytes.decode(
            "utf-8"
        ).replace(
            "summaries/research/research/methods/topics/new-topic/INDEX.md",
            r"summaries/research/research/methods/topics/new\-topic/INDEX.md",
        )
        requested_conflict = prepare_topic(
            request_value,
            manifest,
            canonical_plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            requested_spelling,
            canonical_plan.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(requested_conflict, tuple)
        assert isinstance(requested_conflict, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT"
                for item in requested_conflict
            )
        )

    def test_managed_projection_identity_matrix(self) -> None:
        request_value, manifest, empty_topics, relations, empty_subdomain, _ = (
            empty_snapshot()
        )
        old_topics = table(
            atlas_state.TOPICS_HEADER,
            [topic_registry_row("old-topic", "Old topic")],
        )
        old_link = related_topic_path("old-topic")

        def mapped(
            row: str,
            *,
            base: str = empty_subdomain,
        ) -> str:
            return base.replace(
                "<!-- atlas:managed:end topic-map -->",
                row + "\n<!-- atlas:managed:end topic-map -->",
            )

        canonical_unrelated = subdomain_topic_row("old-topic", "Old topic")
        escaped_unrelated = canonical_unrelated.replace(
            old_link,
            old_link.replace("old-topic", r"old\-topic"),
        )
        cases = (
            (
                "unresolved-id",
                request_value,
                empty_topics,
                mapped(subdomain_topic_row()),
                None,
                "reject",
            ),
            (
                "wrong-domain",
                request_value,
                old_topics,
                mapped(
                    canonical_unrelated.replace("research/methods", "other/methods")
                ),
                None,
                "reject",
            ),
            (
                "wrong-subdomain",
                request_value,
                old_topics,
                mapped(
                    canonical_unrelated.replace("research/methods", "research/other")
                ),
                None,
                "reject",
            ),
            (
                "wrong-path",
                request_value,
                old_topics,
                mapped(canonical_unrelated.replace(old_link, old_link + "?view=full")),
                None,
                "reject",
            ),
            (
                "malformed-link",
                request_value,
                old_topics,
                mapped(canonical_unrelated.replace(old_link, "not-a-topic-link")),
                None,
                "reject",
            ),
            (
                "unsafe-link",
                request_value,
                old_topics,
                mapped(
                    canonical_unrelated.replace(
                        old_link,
                        "summaries/research/research/methods/topics/../old-topic/INDEX.md",
                    )
                ),
                None,
                "reject",
            ),
            (
                "non-equivalent-spelling",
                request_value,
                old_topics,
                mapped(canonical_unrelated.replace(old_link, r"old\\\-topic")),
                None,
                "reject",
            ),
            (
                "unrelated-canonical",
                request_value,
                old_topics,
                mapped(canonical_unrelated),
                canonical_unrelated,
                "plan",
            ),
            (
                "unrelated-decoder-equivalent",
                request_value,
                old_topics,
                mapped(escaped_unrelated),
                escaped_unrelated,
                "plan",
            ),
        )
        for (
            name,
            candidate_request,
            candidate_topics,
            candidate_subdomain,
            preserved_row,
            outcome,
        ) in cases:
            with self.subTest(case=name):
                result = prepare_topic(
                    candidate_request,
                    manifest,
                    candidate_topics,
                    relations,
                    candidate_subdomain,
                    None,
                )
                if outcome == "plan":
                    self.assertIsInstance(result, atlas_index.TopicPlan)
                    assert isinstance(result, atlas_index.TopicPlan)
                    self.assertIn(
                        preserved_row,
                        result.candidate_subdomain_bytes.decode("utf-8"),
                    )
                else:
                    self.assertIsInstance(result, tuple)
                    assert isinstance(result, tuple)
                    self.assertTrue(result)
                    self.assertTrue(
                        any(
                            item.code == "SUBDOMAIN_PROJECTION_INVALID"
                            for item in result
                        )
                    )
                    self.assertFalse(
                        any(isinstance(item, atlas_index.TopicPlan) for item in result)
                    )

        initial = prepare_topic(
            request_value,
            manifest,
            empty_topics,
            relations,
            empty_subdomain,
            None,
        )
        self.assertIsInstance(initial, atlas_index.TopicPlan)
        assert isinstance(initial, atlas_index.TopicPlan)
        requested_noncanonical = initial.candidate_subdomain_bytes.decode(
            "utf-8"
        ).replace(
            old_link.replace("old-topic", "new-topic"),
            old_link.replace("old-topic", r"new\-topic"),
        )
        requested_result = prepare_topic(
            request_value,
            manifest,
            initial.candidate_topics_bytes.decode("utf-8"),
            relations,
            requested_noncanonical,
            initial.candidate_topic_bytes.decode("utf-8"),
        )
        self.assertIsInstance(requested_result, tuple)
        assert isinstance(requested_result, tuple)
        self.assertTrue(
            any(
                item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in requested_result
            )
        )

        related_request = request(related_topic_ids=["old-topic"])
        related_noncanonical = mapped(
            canonical_unrelated.replace(
                old_link,
                old_link.replace("old-topic", r"old\-topic"),
            )
        )
        related_result = prepare_topic(
            related_request,
            manifest,
            old_topics,
            relations,
            related_noncanonical,
            None,
        )
        self.assertIsInstance(related_result, tuple)
        assert isinstance(related_result, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in related_result)
        )

        related_canonical = prepare_topic(
            related_request,
            manifest,
            old_topics,
            relations,
            mapped(canonical_unrelated),
            None,
        )
        self.assertIsInstance(related_canonical, atlas_index.TopicPlan)

    def test_legacy_escape_projections_confirm_when_unambiguous(self) -> None:
        title = r"Literal \u{0041}"
        term = r"term \q"
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        req = request(canonical_title=title, include_terms=[term], exclude_terms=[term])
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        topics_candidate = plan.candidate_topics_bytes.decode("utf-8")
        subdomain_candidate = plan.candidate_subdomain_bytes.decode("utf-8")
        topic = topic.replace(atlas_index._encode_markdown_scalar(title), title)
        topic = topic.replace(
            atlas_index._list_projection_value([term], empty="none"), term
        )
        topics_candidate = topics_candidate.replace(
            atlas_index._escape_markdown_cell(title), title
        )
        topics_candidate = topics_candidate.replace(
            atlas_index._list_projection_value([term], empty=""), term
        )
        subdomain_candidate = subdomain_candidate.replace(
            atlas_index._escape_markdown_cell(title), title
        )
        subdomain_candidate = subdomain_candidate.replace(
            atlas_index._encode_projection_value(title), title
        )
        subdomain_candidate = subdomain_candidate.replace(
            atlas_index._stale_entry(title),
            "- "
            + title
            + " — No evidence-backed answer exists; acquisition/research is required.",
        )
        confirmed = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            subdomain_candidate,
            topic,
        )
        self.assertIsInstance(confirmed, tuple)
        assert isinstance(confirmed, tuple)
        self.assertTrue(any(item.code == "REGISTRY_INVALID" for item in confirmed))

    def test_alternate_escape_encoding_cannot_confirm_different_semantics(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        req = request(canonical_title="Alpha")
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        alternate = r"\u{41}lpha"
        topic = plan.candidate_topic_bytes.decode("utf-8").replace("Alpha", alternate)
        topics_candidate = plan.candidate_topics_bytes.decode("utf-8").replace(
            "Alpha", alternate
        )
        subdomain_candidate = plan.candidate_subdomain_bytes.decode("utf-8").replace(
            "Alpha", alternate
        )
        result = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            subdomain_candidate,
            topic,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "REGISTRY_INVALID" for item in result))

    def test_event_request_related_topic_validation_is_pure_and_complete(self) -> None:
        _, topics, _ = registries(topics=[topic_registry_row()])
        self_result = atlas_index._validate_event_request(
            request(related_topic_ids=[TOPIC_ID]), topics
        )
        self.assertIsNone(self_result[0])
        self.assertEqual([item.code for item in self_result[1]], ["RELATED_TOPIC_SELF"])

        unknown_result = atlas_index._validate_event_request(
            request(related_topic_ids=["missing-topic"]), topics
        )
        self.assertIsNone(unknown_result[0])
        self.assertEqual(
            [item.code for item in unknown_result[1]], ["RELATED_TOPIC_UNKNOWN"]
        )

        _, mismatched_topics, _ = registries(
            topics=[topic_registry_row(path_topic_id="other-topic")]
        )
        mismatch_result = atlas_index._validate_event_request(
            request(related_topic_ids=["old-topic"]), mismatched_topics
        )
        self.assertIsNone(mismatch_result[0])
        self.assertEqual(
            [item.code for item in mismatch_result[1]],
            ["REGISTRY_INVALID"],
        )

        valid_result = atlas_index._validate_event_request(
            request(related_topic_ids=["old-topic"]), topics
        )
        self.assertEqual(valid_result[1], ())
        self.assertEqual(valid_result[0], request(related_topic_ids=["old-topic"]))

    def test_noncanonical_topic_frontmatter_spellings_cannot_confirm(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        cases = (
            topic.replace('topic: "new-topic"', "topic: new-topic", 1),
            topic.replace("aliases: []", "aliases: [ ]", 1),
        )
        for altered_topic in cases:
            with self.subTest(topic=altered_topic):
                result = prepare_topic(
                    req,
                    manifest,
                    plan.candidate_topics_bytes.decode("utf-8"),
                    relations,
                    plan.candidate_subdomain_bytes.decode("utf-8"),
                    altered_topic,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertTrue(
                    any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in result)
                )

    def test_marker_sentinel_values_roundtrip_and_malformed_markers_reject(
        self,
    ) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        req = request(
            canonical_title="Literal atlas:managed: title",
            aliases=["atlas:managed: alias"],
            include_terms=["atlas:managed: include"],
        )
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        topic = plan.candidate_topic_bytes.decode("utf-8")
        topics_candidate = plan.candidate_topics_bytes.decode("utf-8")
        subdomain_candidate = plan.candidate_subdomain_bytes.decode("utf-8")
        confirmed = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            subdomain_candidate,
            topic,
        )
        self.assertIsInstance(confirmed, atlas_index.TopicConfirmation)
        malformed = topic.replace(
            "<!-- atlas:managed:end current-answer -->",
            "<!-- atlas:managed:end unknown -->",
            1,
        )
        rejected = prepare_topic(
            req,
            manifest,
            topics_candidate,
            relations,
            subdomain_candidate,
            malformed,
        )
        self.assertIsInstance(rejected, tuple)
        assert isinstance(rejected, tuple)
        self.assertTrue(
            any(item.code == "TOPIC_COMPATIBILITY_CONFLICT" for item in rejected)
        )

    def test_unrelated_unsorted_utf8_registry_list_rejects_before_topic_plan(
        self,
    ) -> None:
        unrelated = topic_registry_row("old-topic")
        unrelated[5] = "é; a"
        manifest, topics, relations = registries(topics=[unrelated])
        result = prepare_topic(
            request(),
            manifest,
            topics,
            relations,
            subdomain_text(),
            None,
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertTrue(any(item.code == "REGISTRY_INVALID" for item in result))
        self.assertFalse(
            any(isinstance(item, atlas_index.TopicPlan) for item in result)
        )

    def test_load_topic_binding_reconstructs_owner_inputs_without_facade_semantics(
        self,
    ) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        event = {
            "event_record": dict(plan.event_record),
            "attempt": 0,
            "predecessor_sha256": None,
            "targets": [
                {
                    "path": target.path.removeprefix(atlas_index.ROOT_URI),
                    "input_bytes": target.input_bytes,
                    "output_bytes": target.output_bytes,
                }
                for target in plan.targets
            ],
        }
        binding = atlas_index.load_topic_binding(event, atlas_index.MISSING)
        self.assertIsInstance(binding, atlas_index.TopicTransactionBinding)
        assert isinstance(binding, atlas_index.TopicTransactionBinding)
        self.assertEqual(binding.request, req)
        self.assertEqual(binding.target_paths, plan.target_paths)
        self.assertEqual(binding.owner_policy_version, "topic-post-v1")

    def test_zero_match_vocabulary_is_inserted_first_with_approved_presentation(
        self,
    ) -> None:
        req = request(
            vocabulary={
                "domain": {
                    "id": DOMAIN,
                    "label": "Research practice",
                    "aliases": ["science"],
                },
                "subdomain": {
                    "id": SUBDOMAIN,
                    "label": "Methods practice",
                    "aliases": ["methodology"],
                    "parent": DOMAIN,
                },
            }
        )
        manifest, topics, relations = registries()
        empty_vocab = table(atlas_state.VOCAB_HEADER, [])
        plan = prepare_topic(
            req,
            manifest,
            topics,
            relations,
            None,
            None,
            vocab=empty_vocab,
        )
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        self.assertEqual(
            plan.target_paths,
            (
                atlas_index.VOCAB_URI,
                TOPIC_PATH,
                "vault://atlas/summaries/research/research/methods/INDEX.md",
                atlas_index.TOPICS_URI,
            ),
        )
        self.assertEqual(
            dict(plan.target_roles),
            {
                "vocab": atlas_index.VOCAB_URI,
                "topic": TOPIC_PATH,
                "subdomain": (
                    "vault://atlas/summaries/research/research/methods/INDEX.md"
                ),
                "registry": atlas_index.TOPICS_URI,
            },
        )
        candidate_vocab = plan.candidate_vocab_bytes.decode("utf-8")
        self.assertIn(
            "| research | domain | Research practice |  | science | active |  |",
            candidate_vocab,
        )
        self.assertIn(
            "| methods | subdomain | Methods practice | research | methodology | active |  |",
            candidate_vocab,
        )
        self.assertEqual(
            plan.validate_post_state(
                manifest,
                plan.candidate_topics_bytes.decode("utf-8"),
                relations,
                candidate_vocab,
                plan.candidate_subdomain_bytes.decode("utf-8"),
                plan.candidate_topic_bytes.decode("utf-8"),
            ),
            (),
        )

        event = {
            "event_record": dict(plan.event_record),
            "attempt": 0,
            "predecessor_sha256": None,
            "targets": [
                {
                    "path": target.path.removeprefix(atlas_index.ROOT_URI),
                    "input_bytes": target.input_bytes,
                    "output_bytes": target.output_bytes,
                }
                for target in plan.targets
            ],
        }
        binding = atlas_index.load_topic_binding(event, atlas_index.MISSING)
        self.assertIsInstance(binding, atlas_index.TopicTransactionBinding)
        assert isinstance(binding, atlas_index.TopicTransactionBinding)
        self.assertEqual(binding.target_paths, plan.target_paths)
        self.assertEqual(
            binding.post_validation.expected_vocab_bytes, plan.candidate_vocab_bytes
        )

    def test_compatible_vocabulary_resolves_aliases_in_every_status(self) -> None:
        alias_request = request(
            vocabulary={
                "domain": {
                    "id": "science",
                    "label": "Science",
                    "aliases": [],
                },
                "subdomain": {
                    "id": "methodology",
                    "label": "Methodology",
                    "aliases": [],
                    "parent": "science",
                },
            }
        )
        manifest, topics, relations = registries()
        for status in ("active", "deprecated", "reserved"):
            with self.subTest(status=status):
                existing_vocab = vocabulary_text(
                    domain_status=status,
                    subdomain_status=status,
                    domain_aliases="science",
                    subdomain_aliases="methodology",
                )
                plan = prepare_topic(
                    alias_request,
                    manifest,
                    topics,
                    relations,
                    subdomain_text(),
                    None,
                    vocab=existing_vocab,
                )
                self.assertIsInstance(plan, atlas_index.TopicPlan)
                assert isinstance(plan, atlas_index.TopicPlan)
                self.assertEqual(
                    plan.target_paths,
                    (
                        TOPIC_PATH,
                        "vault://atlas/summaries/research/research/methods/INDEX.md",
                        atlas_index.TOPICS_URI,
                    ),
                )
                self.assertEqual(plan.candidate_vocab_bytes, existing_vocab.encode())

    def test_topic_vocabulary_conflicts_fail_before_planning(self) -> None:
        manifest, topics, relations = registries()
        cases = {
            "source-kind-contact": (
                request(
                    vocabulary={
                        "domain": {"id": "article", "label": "Article", "aliases": []},
                        "subdomain": {
                            "id": SUBDOMAIN,
                            "label": "Methods",
                            "aliases": [],
                            "parent": "article",
                        },
                    }
                ),
                table(
                    atlas_state.VOCAB_HEADER,
                    [["article", "source-kind", "Article", "", "", "active", ""]],
                ),
            ),
            "wrong-type": (
                request(),
                table(
                    atlas_state.VOCAB_HEADER,
                    [[DOMAIN, "tag", "Research", "", "", "active", ""]],
                ),
            ),
            "parent-mismatch": (
                request(),
                table(
                    atlas_state.VOCAB_HEADER,
                    [
                        [DOMAIN, "domain", "Research", "", "", "active", ""],
                        ["other", "domain", "Other", "", "", "active", ""],
                        [SUBDOMAIN, "subdomain", "Methods", "other", "", "active", ""],
                    ],
                ),
            ),
            "resolved-id-mismatch": (
                request(
                    vocabulary={
                        "domain": {"id": "science", "label": "Science", "aliases": []},
                        "subdomain": {
                            "id": SUBDOMAIN,
                            "label": "Methods",
                            "aliases": [],
                            "parent": "science",
                        },
                    }
                ),
                table(
                    atlas_state.VOCAB_HEADER,
                    [["other", "domain", "Other", "", "science", "active", ""]],
                ),
            ),
            "ambiguous": (
                request(
                    vocabulary={
                        "domain": {"id": "science", "label": "Science", "aliases": []},
                        "subdomain": {
                            "id": SUBDOMAIN,
                            "label": "Methods",
                            "aliases": [],
                            "parent": "science",
                        },
                    }
                ),
                table(
                    atlas_state.VOCAB_HEADER,
                    [
                        [DOMAIN, "domain", "Research", "", "science", "active", ""],
                        ["other", "domain", "Other", "", "science", "reserved", ""],
                    ],
                ),
            ),
        }
        for name, (candidate_request, candidate_vocab) in cases.items():
            with self.subTest(name=name):
                result = prepare_topic(
                    candidate_request,
                    manifest,
                    topics,
                    relations,
                    subdomain_text(),
                    None,
                    vocab=candidate_vocab,
                )
                self.assertIsInstance(result, tuple)
                assert isinstance(result, tuple)
                self.assertEqual(
                    {item.code for item in result},
                    {"TOPIC_VOCABULARY_CONFLICT"},
                )

    def test_public_v1_is_rejected_but_historical_v1_binding_loads(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        historical_request = {
            key: value
            for key, value in req.items()
            if key not in {"vocabulary", "canonical_tags"}
        }
        historical_request["version"] = 1
        rejected = prepare_topic(
            historical_request,
            manifest,
            topics,
            relations,
            subdomain,
            None,
        )
        self.assertIsInstance(rejected, tuple)
        assert isinstance(rejected, tuple)
        self.assertTrue(rejected)
        self.assertEqual(
            {item.code for item in rejected},
            {"INDEX_REQUEST_INVALID"},
        )

        targets = plan.targets
        request_sha256 = atlas_index.sha256(
            atlas_index.canonical_json(historical_request)
        )
        base_id = atlas_index.topic_base_transaction_id(
            historical_request,
            targets,
        )
        historical_record = {
            "version": 1,
            "event_type": atlas_index.TOPIC_CREATE_EVENT_TYPE,
            "owner": atlas_index.TOPIC_OWNER_ID,
            "topic_namespace_sha256": atlas_index.topic_namespace_sha256(
                historical_request
            ),
            "base_transaction_id": base_id,
            "request_sha256": request_sha256,
            "request": historical_request,
        }
        event = {
            "event_record": historical_record,
            "attempt": 0,
            "predecessor_sha256": None,
            "targets": [
                {
                    "path": target.path.removeprefix(atlas_index.ROOT_URI),
                    "input_bytes": target.input_bytes,
                    "output_bytes": target.output_bytes,
                }
                for target in targets
            ],
        }
        with patch.object(
            atlas_index,
            "_validate_request",
            side_effect=AssertionError("historical decoder called public validator"),
        ) as public_validator:
            binding = atlas_index.load_topic_binding(event, atlas_index.MISSING)
        public_validator.assert_not_called()
        self.assertIsInstance(binding, atlas_index.TopicTransactionBinding)
        assert isinstance(binding, atlas_index.TopicTransactionBinding)
        self.assertEqual(binding.request, historical_request)
        self.assertEqual(binding.base_transaction_id, base_id)
        self.assertEqual(
            dict(binding.target_roles),
            {
                "topic": TOPIC_PATH,
                "subdomain": (
                    "vault://atlas/summaries/research/research/methods/INDEX.md"
                ),
                "registry": atlas_index.TOPICS_URI,
            },
        )

    def test_existing_topic_with_missing_vocabulary_requires_migration(self) -> None:
        req, manifest, topics, relations, subdomain, _ = empty_snapshot()
        plan = prepare_topic(req, manifest, topics, relations, subdomain, None)
        self.assertIsInstance(plan, atlas_index.TopicPlan)
        assert isinstance(plan, atlas_index.TopicPlan)
        result = prepare_topic(
            req,
            manifest,
            plan.candidate_topics_bytes.decode("utf-8"),
            relations,
            plan.candidate_subdomain_bytes.decode("utf-8"),
            plan.candidate_topic_bytes.decode("utf-8"),
            vocab=table(atlas_state.VOCAB_HEADER, []),
        )
        self.assertIsInstance(result, tuple)
        assert isinstance(result, tuple)
        self.assertEqual(
            result,
            (
                atlas_state.Finding(
                    "TOPIC_VOCABULARY_MIGRATION_REQUIRED",
                    atlas_index.VOCAB_URI,
                    detail=(
                        '{"args":{},"operation":"migration.prepare_taxonomy_backfill"}'
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
