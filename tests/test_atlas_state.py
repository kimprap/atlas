from __future__ import annotations

import json
import hashlib

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_state  # noqa: E402


HASH_A = "a" * 64
HASH_B = "b" * 64
SOURCE_ID = "190b4acf8d15"
TOPIC_ID = "test-topic"
ARTIFACT = "summaries/sources/artifacts/2026/2026-07/example.md"
PASS_PATH = (
    "summaries/research/test/test-subdomain/topics/test-topic/"
    "passes/2026-07-15--pass.md"
)


def table(
    header: tuple[str, ...],
    rows: list[list[str]],
    *,
    newline: str = "\n",
    tail: str = "",
) -> str:
    rendered = [
        "---",
        "schema_version: 1",
        "---",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    rendered.extend("| " + " | ".join(row) + " |" for row in rows)
    text = newline.join(rendered)
    if tail:
        text += newline + tail
    return text


def manifest_row(
    *, content_hash: str = HASH_A, route_status: str = "unrouted"
) -> list[str]:
    return [
        "1",
        SOURCE_ID,
        "https://example.com/source",
        ARTIFACT,
        "2026-07-15",
        "2026-07-15",
        "2026-07-15",
        content_hash,
        "2027-07-15",
        route_status,
        "active",
    ]


def relation_row(
    *,
    content_hash: str = HASH_A,
    status: str = "pending",
    pass_path: str = "",
    relation: str = "direct",
    impact: str = "high",
    confidence: str = "high",
    notes: str | None = None,
) -> list[str]:
    if notes is None:
        notes = (
            "Verifier: Heading Example — Source establishes the mechanism "
            f"[relation={relation}; impact={impact}]"
        )
    return [
        atlas_state._edge_id(SOURCE_ID, TOPIC_ID, content_hash),
        "1",
        SOURCE_ID,
        ARTIFACT,
        content_hash,
        TOPIC_ID,
        relation,
        impact,
        confidence,
        status,
        "2026-07-15",
        pass_path,
        notes,
    ]


def topic_row(
    *,
    state: str = "current",
    pending: list[list[str]] | None = None,
    applied: list[list[str]] | None = None,
    last_synthesized: str = "",
) -> list[str]:
    pending = pending or []
    applied = applied or []
    pending = sorted(pending, key=lambda row: (int(row[1]), row[0]))
    return [
        TOPIC_ID,
        "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
        "test",
        "test-subdomain",
        "Test topic",
        "",
        "",
        "test",
        "",
        state,
        str(len(pending)),
        "; ".join(row[0] for row in pending),
        str(max((int(row[1]) for row in pending), default="")),
        last_synthesized,
        str(max((int(row[1]) for row in applied), default=0)),
        "same-as-topic-creation",
    ]


def documents(
    *,
    relations: list[list[str]] | None = None,
    state: str | None = None,
    content_hash: str = HASH_A,
    route_status: str | None = None,
    newline: str = "\n",
    final_newline: bool = True,
) -> dict[str, str]:
    relations = relations or []
    pending = [row for row in relations if row[9] == "pending"]
    applied = [row for row in relations if row[9] == "applied"]
    if state is None:
        state = "dirty" if pending else "current"
    if route_status is None:
        route_status = "routed" if pending or applied else "unrouted"
    values = {
        "manifest": table(
            atlas_state.MANIFEST_HEADER,
            [manifest_row(content_hash=content_hash, route_status=route_status)],
            newline=newline,
        ),
        "topics": table(
            atlas_state.TOPICS_HEADER,
            [topic_row(state=state, pending=pending, applied=applied)],
            newline=newline,
        ),
        "relations": table(atlas_state.RELATIONS_HEADER, relations, newline=newline),
    }
    if final_newline:
        values = {name: text + newline for name, text in values.items()}
    return values


def vocab_text(
    rows: list[list[str]],
    *,
    newline: str = "\n",
    final_newline: bool = True,
    tail: str = "",
) -> str:
    value = table(atlas_state.VOCAB_HEADER, rows, newline=newline, tail=tail)
    return value + newline if final_newline else value


def closed_vocab_rows(*, status: str = "active") -> list[list[str]]:
    return [
        ["article", "source-kind", "Article", "", "", status, ""],
        ["test", "domain", "Test", "", "", status, ""],
        [
            "test-subdomain",
            "subdomain",
            "Test subdomain",
            "test",
            "",
            status,
            "",
        ],
        ["source-tag", "tag", "Source tag", "", "", status, ""],
        ["topic-tag", "tag", "Topic tag", "", "", status, ""],
    ]


def source_projection(
    *,
    source_kind: str = "article",
    primary_domain: str = "test",
    secondary_domains: list[str] | None = None,
    subdomains: list[str] | None = None,
    canonical_tags: list[str] | None = None,
) -> dict[str, object]:
    return {
        "revision": "sha256:" + "c" * 64,
        "source_id": SOURCE_ID,
        "canonical_url": "https://example.com/source",
        "content_hash": HASH_A,
        "title": "Example",
        "tldr": "Example source",
        "key_points": "Example point",
        "source_kind": source_kind,
        "primary_domain": primary_domain,
        "secondary_domains": secondary_domains or [],
        "subdomains": subdomains if subdomains is not None else ["test-subdomain"],
        "canonical_tags": canonical_tags
        if canonical_tags is not None
        else ["source-tag"],
    }


def source_taxonomy_remediation_fixture(
    *,
    desired: bool = False,
) -> tuple[dict[str, str], str, dict[str, dict[str, object]], dict[str, str]]:
    rows: list[list[str]] = []
    projections: dict[str, dict[str, object]] = {}
    source_ids: dict[str, str] = {}
    for index, target in enumerate(
        atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS, start=1
    ):
        canonical_url = f"https://example.test/remediation/{target.source_id}"
        content_hash = f"{index:064x}"
        source_ids[canonical_url] = target.source_id
        rows.append(
            [
                str(index * 10),
                target.source_id,
                canonical_url,
                target.path,
                "2026-07-15",
                "2026-07-15",
                "2026-07-15",
                content_hash,
                "2027-07-15",
                "unrouted",
                "active",
            ]
        )
        if target.primary_domain_change is None:
            primary_domain = "agent-systems"
        else:
            primary_domain = target.primary_domain_change[1 if desired else 0]
        if target.subdomain_observations:
            subdomains = (
                ["harness"]
                if desired
                else [value for _, value in target.subdomain_observations]
            )
        else:
            subdomains = []
        projections[target.path] = {
            "revision": "sha256:" + f"{index + 100:064x}",
            "source_id": target.source_id,
            "canonical_url": canonical_url,
            "content_hash": content_hash,
            "title": f"Source {index}",
            "tldr": f"Source {index} summary",
            "key_points": f"Source {index} point",
            "source_kind": "article",
            "primary_domain": primary_domain,
            "secondary_domains": [],
            "subdomains": subdomains,
            "canonical_tags": [],
        }
    docs = {
        "manifest": table(atlas_state.MANIFEST_HEADER, list(reversed(rows))) + "\n",
        "topics": table(atlas_state.TOPICS_HEADER, []) + "\n",
        "relations": table(atlas_state.RELATIONS_HEADER, []) + "\n",
    }
    vocab = vocab_text(
        [
            ["article", "source-kind", "Article", "", "", "active", ""],
            ["web", "domain", "Web", "", "", "active", ""],
            [
                "agent-systems",
                "domain",
                "Agent systems",
                "",
                "",
                "active",
                "",
            ],
            [
                "harness",
                "subdomain",
                "Harness",
                "agent-systems",
                "",
                "active",
                "",
            ],
        ]
    )
    return docs, vocab, projections, source_ids


def route_event(*, content_hash: str = HASH_A) -> dict[str, object]:
    return {
        "type": "route-upsert",
        "source_id": SOURCE_ID,
        "content_hash": content_hash,
        "checked_on": "2026-07-15",
        "outcome": "routed",
        "edges": [
            {
                "topic_id": TOPIC_ID,
                "relation": "direct",
                "impact": "high",
                "confidence": "high",
                "reason": (
                    "Verifier: Heading Example — Source establishes the mechanism "
                    "[relation=direct; impact=high]"
                ),
            }
        ],
    }


def empty_documents() -> dict[str, str]:
    return {
        "manifest": table(atlas_state.MANIFEST_HEADER, []) + "\n",
        "topics": table(atlas_state.TOPICS_HEADER, [topic_row(state="current")]) + "\n",
        "relations": table(atlas_state.RELATIONS_HEADER, []) + "\n",
    }


def source_event(
    *,
    url: str = "https://example.com/new-source",
    content_hash: str = HASH_A,
    artifact: str | None = None,
) -> dict[str, object]:
    source_id = atlas_state.source_id_for(url)
    if artifact is None:
        artifact = (
            "summaries/sources/artifacts/2026/2026-07/"
            f"2026-07-19--{source_id}--new-source.md"
        )
    return {
        "type": "source-upsert",
        "source_id": source_id,
        "canonical_url": url,
        "artifact": artifact,
        "first_seen": "2026-07-19",
        "checked_on": "2026-07-19",
        "summarized_on": "2026-07-19",
        "content_hash": content_hash,
        "refresh_after": "2027-07-19",
        "classification": None,
    }


def apply_result(
    docs: dict[str, str], result: atlas_state.ReductionResult
) -> dict[str, str]:
    return {**docs, **result.documents}


def managed_index(names: tuple[str, ...], *, label: str) -> str:
    lines = ["---", "schema_version: 1", "---", "", f"# {label}", ""]
    for name in names:
        lines.extend(
            [
                f"## {name}",
                f"<!-- atlas:managed:start {name} -->",
                f"{label} {name}",
                f"<!-- atlas:managed:end {name} -->",
                "",
            ]
        )
    return "\n".join(lines)


def inspection_revisions() -> dict[str, str]:
    return {
        "manifest": "sha256:" + "1" * 64,
        "topics": "sha256:" + "2" * 64,
        "relations": "sha256:" + "3" * 64,
    }


def inspection_artifacts(
    docs: dict[str, str], purpose: str
) -> dict[str, dict[str, str]]:
    paths = atlas_state.select_topic_state(docs, TOPIC_ID).paths_for(purpose)
    result: dict[str, dict[str, str]] = {}
    for index, path in enumerate(paths, 4):
        if path.endswith("/topics/test-topic/INDEX.md"):
            text = managed_index(atlas_state.TOPIC_MANAGED_SECTIONS, label="topic")
        elif path.endswith("/test-subdomain/INDEX.md"):
            text = managed_index(
                atlas_state.SUBDOMAIN_MANAGED_SECTIONS, label="subdomain"
            )
        else:
            text = "# Source summary\n\nEvidence.\n"
        result[path] = {
            "revision": "sha256:" + str(index) * 64,
            "text": text,
        }
    return result


class AtlasStateTests(unittest.TestCase):
    def assert_valid(self, docs: dict[str, str]) -> None:
        self.assertEqual(
            atlas_state.validate_documents(
                docs["manifest"], docs["topics"], docs["relations"]
            ),
            [],
        )

    def test_source_taxonomy_remediation_candidate_replays_to_no_op(self) -> None:
        docs, vocab, projections, source_ids = source_taxonomy_remediation_fixture()
        with patch.object(
            atlas_state,
            "source_id_for",
            side_effect=lambda value: source_ids[value],
        ):
            result = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab,
                projections,
            )
            self.assertEqual(result.state, "candidate")
            self.assertEqual(len(result.targets), 13)
            self.assertEqual(
                [target.source_id for target in result.targets],
                [
                    target.source_id
                    for target in atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS
                ],
            )
            self.assertEqual(
                sum(
                    target.primary_domain_change is not None
                    for target in atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS
                ),
                5,
            )
            self.assertEqual(
                sum(
                    len(target.subdomain_observations)
                    for target in atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS
                ),
                14,
            )
            outputs = {
                path: {
                    **projection,
                    "secondary_domains": list(projection["secondary_domains"]),
                    "subdomains": list(projection["subdomains"]),
                    "canonical_tags": list(projection["canonical_tags"]),
                }
                for path, projection in projections.items()
            }
            for target in result.targets:
                for change in target.changes:
                    outputs[target.path][change["field"]] = change["after"]
            replay = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab,
                outputs,
            )
        self.assertEqual(replay.state, "no-op")
        self.assertEqual(replay.targets, ())
        self.assertEqual(replay.findings, ())

    def test_source_taxonomy_remediation_collapse_preserves_unrelated_order(
        self,
    ) -> None:
        values = [
            "before",
            "agentic-harness-architecture",
            "between",
            "harness",
            "ai-coding-workflow",
            "after",
            "lean-self-improving-agent-harness",
        ]
        self.assertEqual(
            atlas_state._source_taxonomy_remediation_subdomains(values),
            ["before", "harness", "between", "after"],
        )

    def test_source_taxonomy_remediation_rejects_drift_and_closure_defects(
        self,
    ) -> None:
        docs, vocab, projections, source_ids = source_taxonomy_remediation_fixture()
        target = atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS[8]
        moved = {
            path: {
                **projection,
                "subdomains": list(projection["subdomains"]),
            }
            for path, projection in projections.items()
        }
        moved[target.path]["subdomains"] = list(
            reversed(moved[target.path]["subdomains"])
        )
        unknown_tag = {
            path: {
                **projection,
                "canonical_tags": list(projection["canonical_tags"]),
            }
            for path, projection in projections.items()
        }
        unknown_tag[target.path]["canonical_tags"] = ["unknown-tag"]
        with patch.object(
            atlas_state,
            "source_id_for",
            side_effect=lambda value: source_ids[value],
        ):
            moved_result = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab,
                moved,
            )
            closure_result = (
                atlas_state.prepare_source_taxonomy_remediation_candidate(
                    docs["manifest"],
                    docs["topics"],
                    docs["relations"],
                    vocab,
                    unknown_tag,
                )
            )
            missing_web = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab.replace(
                    "| web | domain | Web |  |  | active |  |\n",
                    "",
                ),
                projections,
            )
            topic_result = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                table(atlas_state.TOPICS_HEADER, [topic_row()]) + "\n",
                docs["relations"],
                vocab,
                projections,
            )
        self.assertEqual(moved_result.state, "invalid")
        self.assertIn(
            "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH",
            {finding.code for finding in moved_result.findings},
        )
        self.assertEqual(closure_result.state, "invalid")
        self.assertIn(
            "SOURCE_TAXONOMY_INVALID",
            {finding.code for finding in closure_result.findings},
        )
        self.assertEqual(missing_web.state, "invalid")
        self.assertIn(
            "SOURCE_TAXONOMY_INVALID",
            {finding.code for finding in missing_web.findings},
        )
        self.assertEqual(topic_result.state, "invalid")
        topic_findings = [
            finding
            for finding in topic_result.findings
            if finding.code == "SOURCE_TAXONOMY_INVALID"
        ]
        self.assertEqual(len(topic_findings), 2)

    def test_source_taxonomy_remediation_output_closure_failure_is_complete(
        self,
    ) -> None:
        docs, vocab, projections, source_ids = source_taxonomy_remediation_fixture()
        original = atlas_state._source_taxonomy_remediation_closure_findings
        calls = 0

        def inject(*args: object, **kwargs: object) -> list[atlas_state.Finding]:
            nonlocal calls
            calls += 1
            if calls == 2:
                return [
                    atlas_state.Finding(
                        "SOURCE_TAXONOMY_INVALID",
                        "vault://atlas/synthetic-output",
                        detail="injected output closure defect",
                    )
                ]
            return original(*args, **kwargs)

        with (
            patch.object(
                atlas_state,
                "source_id_for",
                side_effect=lambda value: source_ids[value],
            ),
            patch.object(
                atlas_state,
                "_source_taxonomy_remediation_closure_findings",
                side_effect=inject,
            ),
        ):
            result = atlas_state.prepare_source_taxonomy_remediation_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab,
                projections,
            )
        self.assertEqual(result.state, "invalid")
        self.assertEqual(
            [finding.code for finding in result.findings],
            [
                "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
                "SOURCE_TAXONOMY_INVALID",
            ],
        )

    def test_source_taxonomy_remediation_target_binding_is_all_or_nothing(
        self,
    ) -> None:
        target = atlas_state._SOURCE_TAXONOMY_REMEDIATION_TARGETS[0]
        cases = ("missing", "inactive", "wrong-path", "changed-scalar", "extra")
        for case in cases:
            with self.subTest(case=case):
                docs, vocab, projections, source_ids = (
                    source_taxonomy_remediation_fixture()
                )
                projections = {
                    path: {
                        **projection,
                        "secondary_domains": list(projection["secondary_domains"]),
                        "subdomains": list(projection["subdomains"]),
                        "canonical_tags": list(projection["canonical_tags"]),
                    }
                    for path, projection in projections.items()
                }
                if case == "missing":
                    docs["manifest"] = "\n".join(
                        line
                        for line in docs["manifest"].splitlines()
                        if target.path not in line
                    ) + "\n"
                    projections.pop(target.path)
                elif case == "inactive":
                    docs["manifest"] = "\n".join(
                        (
                            line.rsplit("| active |", 1)[0] + "| archived |"
                            if target.path in line
                            else line
                        )
                        for line in docs["manifest"].splitlines()
                    ) + "\n"
                    projections.pop(target.path)
                elif case == "wrong-path":
                    wrong_path = target.path.replace(".md", "--wrong.md")
                    docs["manifest"] = docs["manifest"].replace(
                        target.path,
                        wrong_path,
                    )
                    projections[wrong_path] = projections.pop(target.path)
                elif case == "changed-scalar":
                    projections[target.path]["primary_domain"] = "agent-systems"
                else:
                    extra_url = "https://example.test/remediation/extra-legacy"
                    extra_id = atlas_state.source_id_for(extra_url)
                    extra_path = (
                        "summaries/sources/artifacts/2026/2026-07/"
                        f"2026-07-31--{extra_id}--extra-legacy.md"
                    )
                    extra_hash = "f" * 64
                    docs["manifest"] += (
                        f"| 999 | {extra_id} | {extra_url} | {extra_path} | "
                        "2026-07-31 | 2026-07-31 | 2026-07-31 | "
                        f"{extra_hash} | 2027-07-31 | unrouted | active |\n"
                    )
                    source_ids[extra_url] = extra_id
                    projections[extra_path] = {
                        "revision": "sha256:" + "e" * 64,
                        "source_id": extra_id,
                        "canonical_url": extra_url,
                        "content_hash": extra_hash,
                        "title": "Extra legacy",
                        "tldr": "Extra legacy summary",
                        "key_points": "Extra legacy point",
                        "source_kind": "article",
                        "primary_domain": "agent-systems",
                        "secondary_domains": [],
                        "subdomains": ["agentic-harness-architecture"],
                        "canonical_tags": [],
                    }
                with patch.object(
                    atlas_state,
                    "source_id_for",
                    side_effect=lambda value: source_ids[value],
                ):
                    result = (
                        atlas_state.prepare_source_taxonomy_remediation_candidate(
                            docs["manifest"],
                            docs["topics"],
                            docs["relations"],
                            vocab,
                            projections,
                        )
                    )
                self.assertEqual(result.state, "invalid")
                expected = (
                    "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH"
                    if case == "changed-scalar"
                    else "SOURCE_TAXONOMY_REMEDIATION_TARGET_MISMATCH"
                )
                self.assertIn(
                    expected,
                    {finding.code for finding in result.findings},
                )

    def test_source_taxonomy_remediation_requires_existing_canonical_vocab(
        self,
    ) -> None:
        docs, vocab, projections, source_ids = source_taxonomy_remediation_fixture()
        cases = {
            "web-missing": vocab.replace(
                "| web | domain | Web |  |  | active |  |\n",
                "",
            ),
            "web-wrong-type": vocab.replace(
                "| web | domain | Web |  |  | active |  |",
                "| web | tag | Web |  |  | active |  |",
            ),
            "agent-systems-missing": vocab.replace(
                "| agent-systems | domain | Agent systems |  |  | active |  |\n",
                "",
            ),
            "harness-missing": vocab.replace(
                "| harness | subdomain | Harness | agent-systems |  | active |  |\n",
                "",
            ),
            "harness-wrong-type": vocab.replace(
                "| harness | subdomain | Harness | agent-systems |  | active |  |",
                "| harness | tag | Harness | agent-systems |  | active |  |",
            ),
            "harness-wrong-parent": vocab.replace(
                "| harness | subdomain | Harness | agent-systems |  | active |  |",
                (
                    "| other-domain | domain | Other domain |  |  | active |  |\n"
                    "| harness | subdomain | Harness | other-domain |  | active |  |"
                ),
            ),
        }
        with patch.object(
            atlas_state,
            "source_id_for",
            side_effect=lambda value: source_ids[value],
        ):
            for name, changed_vocab in cases.items():
                with self.subTest(case=name):
                    result = (
                        atlas_state.prepare_source_taxonomy_remediation_candidate(
                            docs["manifest"],
                            docs["topics"],
                            docs["relations"],
                            changed_vocab,
                            projections,
                        )
                    )
                    self.assertEqual(result.state, "invalid")
                    self.assertTrue(
                        {
                            finding.code for finding in result.findings
                        }
                        & {"SOURCE_TAXONOMY_INVALID", "VOCAB_PARENT_INVALID"}
                    )
    def test_validate_vocab_accepts_seed_alias_overlap_and_rejects_malformed_rows(
        self,
    ) -> None:
        documents = empty_documents()
        vocab = (ROOT / "scaffold" / "summaries" / "registry" / "VOCAB.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(vocab.count("blog post; guide"), 1)
        self.assertEqual(vocab.count("| guide; manual |"), 1)
        self.assertEqual(
            atlas_state.validate_documents(
                documents["manifest"],
                documents["topics"],
                documents["relations"],
                vocab_text=vocab,
            ),
            [],
        )
        self.assertEqual(
            atlas_state.validate_documents(
                documents["manifest"],
                documents["topics"],
                documents["relations"],
            ),
            [],
        )

        article = (
            "| article | source-kind | Article |  | blog post; guide | active | "
            "Source summary kind. |"
        )
        cases = {
            "VOCAB_DUPLICATE_ID": vocab.replace(article, article + "\n" + article),
            "VOCAB_STATUS_INVALID": vocab.replace(
                article, article.replace("active", "broken")
            ),
            "VOCAB_PARENT_INVALID": vocab.replace(
                article, article.replace("|  | blog", "| cooking | blog")
            ),
            "VOCAB_ID_INVALID": vocab.replace(
                article, article.replace("| article |", "| Article |")
            ),
            "VOCAB_TYPE_INVALID": vocab.replace(
                article, article.replace("source-kind", "source")
            ),
        }
        for expected, malformed in cases.items():
            with self.subTest(expected=expected):
                findings = atlas_state.validate_documents(
                    documents["manifest"],
                    documents["topics"],
                    documents["relations"],
                    vocab_text=malformed,
                )
                self.assertIn(expected, {finding.code for finding in findings})

    def test_lookup_manifest_row_returns_canonical_hit(self) -> None:
        expected = dict(zip(atlas_state.MANIFEST_HEADER, manifest_row(), strict=True))
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [manifest_row()]) + "\n",
            "https://example.com/source",
        )

        self.assertEqual(findings, [])
        self.assertEqual(found, expected)

    def test_lookup_manifest_row_returns_unambiguous_absence(self) -> None:
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [manifest_row()]) + "\n",
            "https://example.com/absent",
        )

        self.assertEqual(findings, [])
        self.assertIsNone(found)

    def test_lookup_manifest_row_returns_archived_hit(self) -> None:
        archived = manifest_row()
        archived[-1] = "archived"
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [archived]) + "\n",
            "https://example.com/source",
        )

        self.assertEqual(findings, [])
        self.assertIsNotNone(found)
        self.assertEqual(found["Status"], "archived")

    def test_lookup_manifest_row_rejects_malformed_and_duplicate_tables(self) -> None:
        row = manifest_row()
        malformed = (
            table(
                atlas_state.MANIFEST_HEADER,
                [row],
                tail="End.\n\n| " + " | ".join(row) + " |",
            )
            + "\n"
        )
        duplicate = table(atlas_state.MANIFEST_HEADER, [row, row]) + "\n"

        malformed_row, malformed_findings = atlas_state.lookup_manifest_row(
            malformed, "https://example.com/source"
        )
        duplicate_row, duplicate_findings = atlas_state.lookup_manifest_row(
            duplicate, "https://example.com/source"
        )

        self.assertIsNone(malformed_row)
        self.assertEqual(
            {finding.code for finding in malformed_findings},
            {"MANIFEST_ROW_OUTSIDE_TABLE"},
        )
        self.assertIsNone(duplicate_row)
        self.assertEqual(
            {finding.code for finding in duplicate_findings},
            {
                "MANIFEST_DUPLICATE_SOURCE_ID",
                "MANIFEST_DUPLICATE_SOURCE_SEQ",
                "MANIFEST_DUPLICATE_CANONICAL_URL",
            },
        )

    def test_lookup_manifest_row_rejects_invalid_noncanonical_and_mismatched_identity(
        self,
    ) -> None:
        cases = [
            ("not a URL", SOURCE_ID, "MANIFEST_CANONICAL_URL_INVALID"),
            (
                "https://EXAMPLE.com/source",
                SOURCE_ID,
                "MANIFEST_CANONICAL_URL_NOT_NORMALIZED",
            ),
            (
                "https://example.com/source",
                "ffffffffffff",
                "MANIFEST_SOURCE_ID_URL_MISMATCH",
            ),
        ]
        for url, source_id, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                row = manifest_row()
                row[1] = source_id
                row[2] = url
                found, findings = atlas_state.lookup_manifest_row(
                    table(atlas_state.MANIFEST_HEADER, [row]) + "\n",
                    "https://example.com/source",
                )

                self.assertIsNone(found)
                self.assertIn(expected_code, {finding.code for finding in findings})

    def test_orphan_relation_rows_fail_and_repair_moves_only_rows(self) -> None:
        row = relation_row()
        docs = documents(relations=[], state="current", route_status="routed")
        docs["topics"] = (
            table(
                atlas_state.TOPICS_HEADER,
                [topic_row(state="dirty", pending=[row])],
            )
            + "\n"
        )
        docs["relations"] += (
            "\nUse these exact values.\n\n" + "| " + " | ".join(row) + " |\n"
        )
        findings = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual(
            [finding.code for finding in findings], ["RELATION_ROW_OUTSIDE_TABLE"]
        )

        result = atlas_state.reduce_event(
            docs, {"type": "repair-table-placement", "registry": "relations"}
        )
        self.assertTrue(result.ok)
        repaired = dict(docs)
        repaired.update(result.documents)
        self.assert_valid(repaired)
        self.assertLess(
            repaired["relations"].index(row[0]),
            repaired["relations"].index("Use these exact values."),
        )
        self.assertEqual(repaired["relations"].count(row[0]), 1)

    def test_route_inserts_inside_table_and_derives_cache(self) -> None:
        docs = documents()
        result = atlas_state.reduce_event(docs, route_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["dirty_count"], 1)
        edge_id = atlas_state._edge_id(SOURCE_ID, TOPIC_ID, HASH_A)
        self.assertEqual(result.derived[TOPIC_ID]["pending_edge_ids"], [edge_id])
        replacement = result.documents["relations"]
        self.assertIn(edge_id, replacement)
        self.assert_valid({**docs, **result.documents})

    def test_route_date_creates_relation_without_refreshing_source(self) -> None:
        docs = documents()
        before, findings = atlas_state.lookup_manifest_row(
            docs["manifest"], "https://example.com/source"
        )
        self.assertEqual(findings, [])
        self.assertIsNotNone(before)
        assert before is not None
        event = route_event()
        event["checked_on"] = "2026-08-17"

        result = atlas_state.reduce_event(docs, event)

        self.assertTrue(result.ok, result.findings)
        after, findings = atlas_state.lookup_manifest_row(
            result.documents["manifest"], "https://example.com/source"
        )
        self.assertEqual(findings, [])
        self.assertIsNotNone(after)
        assert after is not None
        preserved = (
            "First seen",
            "Last checked",
            "Last summarized",
            "Content hash",
            "Refresh after",
        )
        self.assertEqual(
            {field: after[field] for field in preserved},
            {field: before[field] for field in preserved},
        )
        relations = atlas_state._parse_table("relations", result.documents["relations"])
        self.assertEqual(relations.rows[0][10], "2026-08-17")

    def test_route_rejects_archived_source_and_manifest_hash_drift(self) -> None:
        archived = documents()
        archived["manifest"] = archived["manifest"].replace(
            "| active |", "| archived |"
        )
        archived_result = atlas_state.reduce_event(archived, route_event())
        self.assertFalse(archived_result.ok)
        self.assertEqual(archived_result.documents, {})
        self.assertEqual(
            [finding.code for finding in archived_result.findings],
            ["EVENT_SOURCE_ARCHIVED"],
        )

        mismatch_result = atlas_state.reduce_event(
            documents(), route_event(content_hash=HASH_B)
        )
        self.assertFalse(mismatch_result.ok)
        self.assertEqual(mismatch_result.documents, {})
        self.assertEqual(
            [finding.code for finding in mismatch_result.findings],
            ["EVENT_CONTENT_HASH_MISMATCH"],
        )

    def test_same_hash_route_does_not_reopen_applied_edge(self) -> None:
        applied = relation_row(status="applied", pass_path=PASS_PATH)
        docs = documents(relations=[applied], state="current")
        result = atlas_state.reduce_event(docs, route_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["dirty_count"], 0)
        self.assertEqual(result.derived[TOPIC_ID]["source_watermark"], 1)
        self.assertNotIn("relations", result.documents)

    def test_refresh_requires_complete_set_and_supports_start_complete(self) -> None:
        pending = relation_row()
        docs = documents(relations=[pending], state="dirty")
        bad = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-start",
                "topic_id": TOPIC_ID,
                "edge_ids": [],
                "started_at": "2026-07-15T00:00:00Z",
            },
        )
        self.assertFalse(bad.ok)
        self.assertEqual(bad.findings[0].code, "REFRESH_PENDING_SET_MISMATCH")

        edge_ids = [pending[0]]
        started = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-start",
                "topic_id": TOPIC_ID,
                "edge_ids": edge_ids,
                "started_at": "2026-07-15T00:00:00Z",
            },
        )
        self.assertTrue(started.ok, started.findings)
        refreshing = {**docs, **started.documents}
        self.assertEqual(started.derived[TOPIC_ID]["freshness_state"], "refreshing")

        completed = atlas_state.reduce_event(
            refreshing,
            {
                "type": "refresh-complete",
                "topic_id": TOPIC_ID,
                "edge_ids": edge_ids,
                "pass_path": PASS_PATH,
                "completed_on": "2026-07-15",
            },
        )
        self.assertTrue(completed.ok, completed.findings)
        self.assertEqual(completed.applied_edge_ids, edge_ids)
        self.assertEqual(completed.derived[TOPIC_ID]["freshness_state"], "current")
        self.assertEqual(completed.derived[TOPIC_ID]["dirty_count"], 0)
        self.assert_valid({**refreshing, **completed.documents})

    def test_refresh_fail_preserves_pending_and_blocks(self) -> None:
        pending = relation_row()
        docs = documents(relations=[pending], state="refreshing")
        result = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-fail",
                "topic_id": TOPIC_ID,
                "reason": "pass write failed",
            },
        )
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["freshness_state"], "blocked")
        self.assertEqual(result.derived[TOPIC_ID]["pending_edge_ids"], [pending[0]])
        self.assertNotIn("relations", result.documents)

    def test_invalid_edge_id_and_cache_fail_deterministically(self) -> None:
        pending = relation_row()
        pending[0] = "edge--wrong"
        docs = documents(relations=[pending], state="dirty")
        first = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        second = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual(first, second)
        self.assertIn("RELATION_EDGE_ID_INVALID", {finding.code for finding in first})

    def test_repair_notes_changes_only_notes(self) -> None:
        pending = relation_row(notes="old note")
        docs = documents(relations=[pending], state="dirty")
        reason = (
            "Verifier: Rule 1 — Source requires bounded state "
            "[relation=direct; impact=high]"
        )
        result = atlas_state.reduce_event(
            docs,
            {
                "type": "repair-relation-notes",
                "repairs": [{"edge_id": pending[0], "reason": reason}],
            },
        )
        self.assertTrue(result.ok, result.findings)
        before = atlas_state._parse_table("relations", docs["relations"]).rows[0]
        after = atlas_state._parse_table(
            "relations", result.documents["relations"]
        ).rows[0]
        self.assertEqual(before[:-1], after[:-1])
        self.assertEqual(after[-1], reason)

    def test_newline_and_final_newline_are_preserved(self) -> None:
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final_newline=final_newline):
                    docs = documents(newline=newline, final_newline=final_newline)
                    result = atlas_state.reduce_event(docs, route_event())
                    self.assertTrue(result.ok, result.findings)
                    for replacement in result.documents.values():
                        self.assertEqual(replacement.endswith(newline), final_newline)
                        if newline == "\r\n":
                            self.assertNotIn("\n", replacement.replace("\r\n", ""))

    def test_unknown_event_field_fails_without_documents(self) -> None:
        event = route_event()
        event["provider"] = "forbidden"
        result = atlas_state.reduce_event(documents(), event)
        self.assertFalse(result.ok)
        self.assertEqual(result.documents, {})
        self.assertIn(
            "EVENT_FIELD_UNKNOWN", {finding.code for finding in result.findings}
        )

    def test_source_upsert_requires_classification_field(self) -> None:
        event = source_event()
        del event["classification"]

        result = atlas_state.reduce_event(empty_documents(), event)

        self.assertFalse(result.ok)
        self.assertEqual(result.documents, {})
        self.assertEqual(
            [(finding.code, finding.detail) for finding in result.findings],
            [("EVENT_FIELD_MISSING", "classification")],
        )

    def test_source_upsert_same_hash_validates_nonnull_classification(self) -> None:
        event = source_event()
        docs = apply_result(
            empty_documents(), atlas_state.reduce_event(empty_documents(), event)
        )
        malformed = dict(event)
        malformed["classification"] = {}

        rejected = atlas_state.reduce_event(docs, malformed)

        self.assertFalse(rejected.ok)
        self.assertEqual(rejected.documents, {})
        self.assertEqual(
            [(finding.code, finding.path) for finding in rejected.findings],
            [("SOURCE_CLASSIFICATION_INVALID", "worker.classification")],
        )

        valid = dict(event)
        valid["classification"] = {
            "domain": None,
            "subdomain": None,
            "tags": [],
            "candidate_terms": [],
        }
        accepted = atlas_state.reduce_event(docs, valid)
        self.assertTrue(accepted.ok, accepted.findings)
        self.assertEqual(accepted.documents, {})

    def test_source_upsert_create_sequence_and_idempotent_replay(self) -> None:
        event = source_event()
        docs = empty_documents()
        result = atlas_state.reduce_event(docs, event)
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived["source"]["source_seq"], 1)
        self.assertTrue(result.derived["source"]["created"])
        candidate = apply_result(docs, result)
        self.assert_valid(candidate)

        replay = atlas_state.reduce_event(candidate, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})
        self.assertFalse(replay.derived["source"]["created"])
        self.assertFalse(replay.derived["source"]["content_changed"])

        second = atlas_state.reduce_event(documents(), source_event())
        self.assertTrue(second.ok, second.findings)
        self.assertEqual(second.derived["source"]["source_seq"], 2)

    def test_source_sequence_gaps_validate_and_allocate_after_max(self) -> None:
        second_url = "https://example.com/source-four"
        second = manifest_row()
        second[0] = "4"
        second[1] = atlas_state.source_id_for(second_url)
        second[2] = second_url
        second[3] = "summaries/sources/artifacts/2026/2026-07/source-four.md"
        docs = documents()
        docs["manifest"] = (
            table(
                atlas_state.MANIFEST_HEADER,
                [manifest_row(), second],
            )
            + "\n"
        )

        self.assert_valid(docs)
        result = atlas_state.reduce_event(docs, source_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived["source"]["source_seq"], 5)

    def test_source_upsert_same_hash_preserves_route_history(self) -> None:
        event = source_event()
        docs = apply_result(
            empty_documents(), atlas_state.reduce_event(empty_documents(), event)
        )
        route = {
            "type": "route-upsert",
            "source_id": event["source_id"],
            "content_hash": HASH_A,
            "checked_on": "2026-07-19",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": TOPIC_ID,
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: Heading Example — Source establishes the mechanism "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        routed_result = atlas_state.reduce_event(docs, route)
        self.assertTrue(routed_result.ok, routed_result.findings)
        routed = apply_result(docs, routed_result)
        replay = atlas_state.reduce_event(routed, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})
        self.assertEqual(replay.derived["source"]["route_status"], "routed")

    def test_source_upsert_changed_hash_supersedes_pending_and_resets_route(
        self,
    ) -> None:
        initial_event = source_event()
        docs = empty_documents()
        docs = apply_result(docs, atlas_state.reduce_event(docs, initial_event))
        route = {
            "type": "route-upsert",
            "source_id": initial_event["source_id"],
            "content_hash": HASH_A,
            "checked_on": "2026-07-19",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": TOPIC_ID,
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: Heading Example — Source establishes the mechanism "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        docs = apply_result(docs, atlas_state.reduce_event(docs, route))
        changed = atlas_state.reduce_event(docs, source_event(content_hash=HASH_B))
        self.assertTrue(changed.ok, changed.findings)
        candidate = apply_result(docs, changed)
        self.assert_valid(candidate)
        manifest = atlas_state._parse_table("manifest", candidate["manifest"]).rows[0]
        relation = atlas_state._parse_table("relations", candidate["relations"]).rows[0]
        topic = atlas_state._parse_table("topics", candidate["topics"]).rows[0]
        self.assertEqual(manifest[9], "unrouted")
        self.assertEqual(relation[9], "superseded")
        self.assertEqual(topic[9:13], ["current", "0", "", ""])

    def test_source_upsert_rejects_identity_archive_dates_and_paths(self) -> None:
        mismatch = source_event()
        mismatch["source_id"] = "0" * 12
        result = atlas_state.reduce_event(empty_documents(), mismatch)
        self.assertFalse(result.ok)
        self.assertIn(
            "EVENT_SOURCE_ID_URL_MISMATCH", {item.code for item in result.findings}
        )

        invalid_date = source_event()
        invalid_date["checked_on"] = "2026-02-30"
        result = atlas_state.reduce_event(empty_documents(), invalid_date)
        self.assertFalse(result.ok)
        self.assertIn("EVENT_DATE_INVALID", {item.code for item in result.findings})

        source_id = source_event()["source_id"]
        invalid_paths = (
            f"/summaries/sources/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            f"vault://atlas/summaries/sources/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/sources/artifacts/tmp/2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/sources/artifacts/2026/../2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/other/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            "summaries/sources/artifacts/2026/2026-07/wrong.md",
        )
        for artifact in invalid_paths:
            with self.subTest(artifact=artifact):
                result = atlas_state.reduce_event(
                    empty_documents(), source_event(artifact=artifact)
                )
                self.assertFalse(result.ok)
                self.assertTrue(
                    any(
                        item.code.startswith("EVENT_ARTIFACT_PATH")
                        for item in result.findings
                    )
                )

        event = source_event()
        docs = apply_result(
            empty_documents(), atlas_state.reduce_event(empty_documents(), event)
        )
        docs["manifest"] = docs["manifest"].replace("| active |", "| archived |")
        result = atlas_state.reduce_event(docs, event)
        self.assertFalse(result.ok)
        self.assertIn("EVENT_SOURCE_ARCHIVED", {item.code for item in result.findings})

        mismatch_path = dict(event)
        mismatch_path["artifact"] = str(event["artifact"]).replace(
            "new-source.md", "other.md"
        )
        active_docs = docs.copy()
        active_docs["manifest"] = active_docs["manifest"].replace(
            "| archived |", "| active |"
        )
        result = atlas_state.reduce_event(active_docs, mismatch_path)
        self.assertFalse(result.ok)
        self.assertIn(
            "EVENT_ARTIFACT_PATH_MISMATCH", {item.code for item in result.findings}
        )

    def test_transaction_recovery_truth_table_and_reverse_restore_order(self) -> None:
        artifact = "summaries/sources/artifacts/new.md"
        manifest = atlas_state.MANIFEST_PATH
        intent = {
            "targets": [
                {"path": artifact, "input_sha256": None, "output_sha256": HASH_A},
                {"path": manifest, "input_sha256": HASH_A, "output_sha256": HASH_B},
            ]
        }
        inputs = {artifact: None, manifest: HASH_A}
        self.assertEqual(
            atlas_state.plan_transaction_recovery(intent, None, inputs).action,
            "prepare",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, None, inputs, abort=True
            ).action,
            "aborted",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_B}
            ).action,
            "applied",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, {"version": 1}, inputs
            ).action,
            "rolled-back",
        )
        mixed = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_A}
        )
        self.assertEqual(mixed.action, "rollback")
        self.assertEqual(mixed.restore_paths, [artifact])
        both_output = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_B}
        )
        self.assertEqual(both_output.action, "applied")
        conflict = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: "c" * 64, manifest: HASH_A}
        )
        self.assertEqual(conflict.action, "manual-conflict")

        rollback_both = atlas_state.plan_transaction_recovery(
            intent,
            {"version": 1},
            {artifact: HASH_A, manifest: HASH_B},
        )
        self.assertEqual(rollback_both.action, "applied")
        four = {
            "targets": [
                {"path": artifact, "input_sha256": None, "output_sha256": HASH_A},
                {
                    "path": atlas_state.RELATIONS_PATH,
                    "input_sha256": HASH_A,
                    "output_sha256": HASH_B,
                },
                {
                    "path": atlas_state.TOPICS_PATH,
                    "input_sha256": HASH_A,
                    "output_sha256": "c" * 64,
                },
                {"path": manifest, "input_sha256": HASH_A, "output_sha256": HASH_B},
            ]
        }
        rollback = atlas_state.plan_transaction_recovery(
            four,
            {"version": 1},
            {
                artifact: HASH_A,
                atlas_state.RELATIONS_PATH: HASH_B,
                atlas_state.TOPICS_PATH: HASH_A,
                manifest: HASH_B,
            },
        )
        self.assertEqual(
            rollback.restore_paths,
            [manifest, atlas_state.RELATIONS_PATH, artifact],
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                {"targets": []}, {"version": 1}, {}
            ).action,
            "no-op",
        )

    def test_vocabulary_domain_insertion_candidate_is_exact_and_idempotent(
        self,
    ) -> None:
        existing = [
            ["article", "source-kind", "Article", "", "", "deprecated", "keep"]
        ]
        change = {
            "id": "web",
            "type": "domain",
            "label": "web",
            "parent": "",
            "allowed_aliases": [],
            "status": "active",
            "notes": "",
        }
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final=final_newline):
                    before = vocab_text(
                        existing,
                        newline=newline,
                        final_newline=final_newline,
                        tail="Unmanaged suffix — preserve exactly.",
                    )
                    expected = vocab_text(
                        [
                            *existing,
                            ["web", "domain", "web", "", "", "active", ""],
                        ],
                        newline=newline,
                        final_newline=final_newline,
                        tail="Unmanaged suffix — preserve exactly.",
                    )
                    result = (
                        atlas_state.prepare_vocabulary_domain_insertion_candidate(
                            before, "web"
                        )
                    )
                    self.assertEqual(result.state, "candidate", result.findings)
                    self.assertEqual(result.preimage_text, before)
                    self.assertEqual(result.text, expected)
                    self.assertEqual(result.changes, (change,))
                    self.assertEqual(
                        result.preimage_revision,
                        "sha256:" + hashlib.sha256(before.encode()).hexdigest(),
                    )
                    self.assertEqual(
                        result.output_revision,
                        "sha256:" + hashlib.sha256(expected.encode()).hexdigest(),
                    )
                    self.assertEqual(
                        expected.endswith(newline),
                        final_newline,
                    )
                    self.assertEqual(atlas_state.validate_vocab(expected), [])
                    replay = (
                        atlas_state.prepare_vocabulary_domain_insertion_candidate(
                            expected, "web"
                        )
                    )
                    self.assertEqual(replay.state, "no-op", replay.findings)
                    self.assertIsNone(replay.text)
                    self.assertEqual(replay.changes, ())

    def test_vocabulary_domain_insertion_compatible_existing_is_no_op(
        self,
    ) -> None:
        for status in ("active", "deprecated", "reserved"):
            with self.subTest(status=status):
                before = vocab_text(
                    [
                        [
                            "web",
                            "domain",
                            "World Wide Web",
                            "",
                            "browser; internet",
                            status,
                            "Existing presentation remains.",
                        ]
                    ],
                    tail="Unmanaged suffix.",
                )
                result = (
                    atlas_state.prepare_vocabulary_domain_insertion_candidate(
                        before, "web"
                    )
                )
                self.assertEqual(result.state, "no-op", result.findings)
                self.assertEqual(result.to_dict(), {"state": "no-op"})
                self.assertIsNone(result.preimage_text)
                self.assertIsNone(result.text)

    def test_vocabulary_domain_insertion_rejects_invalid_and_conflicting_ids(
        self,
    ) -> None:
        baseline = vocab_text(
            [["article", "source-kind", "Article", "", "", "active", ""]]
        )
        for domain_id in ("Web", " web", "web/site", ""):
            with self.subTest(invalid=repr(domain_id)):
                result = (
                    atlas_state.prepare_vocabulary_domain_insertion_candidate(
                        baseline, domain_id
                    )
                )
                self.assertEqual(result.state, "invalid")
                self.assertEqual(len(result.findings), 1)
                finding = result.findings[0]
                self.assertEqual(
                    finding.code, "VOCABULARY_DOMAIN_INSERTION_ID_INVALID"
                )
                self.assertEqual(finding.path, "args.domain_id")
                self.assertEqual(finding.row, domain_id)
                self.assertEqual(
                    finding.detail,
                    "expected exact lowercase kebab-case [a-z0-9][a-z0-9-]*",
                )
                self.assertIsNone(result.text)

        exact_conflicts = (
            [
                ["web", "tag", "Web", "", "", "active", ""],
            ],
            [
                ["parent", "domain", "Parent", "", "", "active", ""],
                ["web", "subdomain", "Web", "parent", "", "reserved", ""],
            ],
        )
        for rows in exact_conflicts:
            with self.subTest(exact=rows[-1][1:]):
                before = vocab_text(rows)
                result = (
                    atlas_state.prepare_vocabulary_domain_insertion_candidate(
                        before, "web"
                    )
                )
                self.assertEqual(result.state, "invalid")
                self.assertEqual(len(result.findings), 1)
                finding = result.findings[0]
                self.assertEqual(
                    finding.code, "VOCABULARY_DOMAIN_INSERTION_CONFLICT"
                )
                self.assertEqual(finding.row, "web")
                self.assertEqual(
                    json.loads(finding.detail)["contact_fields"], ["id"]
                )
                self.assertIsNone(result.text)
                self.assertEqual(before, vocab_text(rows))
        for status in ("active", "deprecated", "reserved"):
            with self.subTest(id_contact_status=status):
                before = vocab_text(
                    [["web", "tag", "Web", "", "", status, ""]]
                )
                result = (
                    atlas_state.prepare_vocabulary_domain_insertion_candidate(
                        before, "web"
                    )
                )
                self.assertEqual(result.state, "invalid")
                self.assertEqual(len(result.findings), 1)
                finding = result.findings[0]
                self.assertEqual(
                    finding.code,
                    "VOCABULARY_DOMAIN_INSERTION_CONFLICT",
                )
                self.assertEqual(
                    json.loads(finding.detail)["contact_fields"],
                    ["id"],
                )
                self.assertEqual(
                    json.loads(finding.detail)["observed_status"],
                    status,
                )
                self.assertIsNone(result.text)
                self.assertEqual(
                    before,
                    vocab_text(
                        [["web", "tag", "Web", "", "", status, ""]]
                    ),
                )

        for status in ("active", "deprecated", "reserved"):
            for field in ("label", "allowed_aliases"):
                with self.subTest(status=status, field=field):
                    row = [
                        "existing",
                        "tag",
                        "WEB" if field == "label" else "Existing",
                        "",
                        "web" if field == "allowed_aliases" else "",
                        status,
                        "",
                    ]
                    before = vocab_text([row])
                    result = (
                        atlas_state.prepare_vocabulary_domain_insertion_candidate(
                            before, "web"
                        )
                    )
                    self.assertEqual(result.state, "invalid")
                    self.assertEqual(len(result.findings), 1)
                    finding = result.findings[0]
                    detail = json.loads(finding.detail)
                    self.assertEqual(
                        set(detail),
                        {
                            "contact_fields",
                            "observed_id",
                            "observed_parent",
                            "observed_status",
                            "observed_type",
                        },
                    )
                    self.assertEqual(detail["contact_fields"], [field])
                    self.assertEqual(detail["observed_status"], status)
                    self.assertEqual(finding.row, "web")
                    self.assertIsNotNone(finding.line)
                    self.assertIsNone(result.text)

    def test_vocabulary_subdomain_insertion_candidate_is_exact_parent_bound_and_idempotent(
        self,
    ) -> None:
        existing = [
            [
                "markets",
                "domain",
                "Financial Markets",
                "",
                "finance; exchanges",
                "active",
                "Existing parent presentation.",
            ],
            ["article", "source-kind", "Article", "", "", "deprecated", "keep"],
        ]
        change = {
            "id": "trading",
            "type": "subdomain",
            "label": "trading",
            "parent": "markets",
            "allowed_aliases": [],
            "status": "active",
            "notes": "",
        }
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final=final_newline):
                    before = vocab_text(
                        existing,
                        newline=newline,
                        final_newline=final_newline,
                        tail="Unmanaged suffix — preserve exactly.",
                    )
                    expected = vocab_text(
                        [
                            *existing,
                            [
                                "trading",
                                "subdomain",
                                "trading",
                                "markets",
                                "",
                                "active",
                                "",
                            ],
                        ],
                        newline=newline,
                        final_newline=final_newline,
                        tail="Unmanaged suffix — preserve exactly.",
                    )
                    result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                        before,
                        "trading",
                        "markets",
                    )
                    self.assertEqual(result.state, "candidate", result.findings)
                    self.assertEqual(result.preimage_text, before)
                    self.assertEqual(result.text, expected)
                    self.assertEqual(result.changes, (change,))
                    self.assertEqual(
                        result.preimage_revision,
                        "sha256:" + hashlib.sha256(before.encode()).hexdigest(),
                    )
                    self.assertEqual(
                        result.output_revision,
                        "sha256:" + hashlib.sha256(expected.encode()).hexdigest(),
                    )
                    self.assertEqual(expected.endswith(newline), final_newline)
                    self.assertEqual(atlas_state.validate_vocab(expected), [])
                    replay = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                        expected,
                        "trading",
                        "markets",
                    )
                    self.assertEqual(replay.state, "no-op", replay.findings)
                    self.assertEqual(replay.to_dict(), {"state": "no-op"})

    def test_vocabulary_subdomain_insertion_compatible_existing_is_no_op(
        self,
    ) -> None:
        for status in ("active", "deprecated", "reserved"):
            with self.subTest(status=status):
                before = vocab_text(
                    [
                        [
                            "markets",
                            "domain",
                            "Financial Markets",
                            "",
                            "finance",
                            "active",
                            "Existing parent.",
                        ],
                        [
                            "trading",
                            "subdomain",
                            "Trading Systems",
                            "markets",
                            "execution; markets-trading",
                            status,
                            "Existing child presentation remains.",
                        ],
                    ],
                    tail="Unmanaged suffix.",
                )
                result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                    before,
                    "trading",
                    "markets",
                )
                self.assertEqual(result.state, "no-op", result.findings)
                self.assertEqual(result.to_dict(), {"state": "no-op"})
                self.assertIsNone(result.preimage_text)
                self.assertIsNone(result.text)
                self.assertEqual(
                    before,
                    vocab_text(
                        [
                            [
                                "markets",
                                "domain",
                                "Financial Markets",
                                "",
                                "finance",
                                "active",
                                "Existing parent.",
                            ],
                            [
                                "trading",
                                "subdomain",
                                "Trading Systems",
                                "markets",
                                "execution; markets-trading",
                                status,
                                "Existing child presentation remains.",
                            ],
                        ],
                        tail="Unmanaged suffix.",
                    ),
                )

    def test_vocabulary_subdomain_insertion_rejects_invalid_parent_and_conflicting_ids(
        self,
    ) -> None:
        baseline = vocab_text(
            [["markets", "domain", "Markets", "", "", "active", ""]]
        )
        invalid_cases = (
            ("Trading", "markets", ("args.subdomain_id",)),
            ("trading", "Markets", ("args.parent_domain_id",)),
            ("trading/path", " markets", ("args.parent_domain_id", "args.subdomain_id")),
            (None, 7, ("args.parent_domain_id", "args.subdomain_id")),
        )
        for subdomain_id, parent_domain_id, paths in invalid_cases:
            with self.subTest(
                subdomain_id=repr(subdomain_id),
                parent_domain_id=repr(parent_domain_id),
            ):
                result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                    baseline,
                    subdomain_id,  # type: ignore[arg-type]
                    parent_domain_id,  # type: ignore[arg-type]
                )
                self.assertEqual(result.state, "invalid")
                self.assertEqual(
                    tuple(finding.path for finding in result.findings),
                    paths,
                )
                self.assertTrue(
                    all(
                        finding.code
                        == "VOCABULARY_SUBDOMAIN_INSERTION_ID_INVALID"
                        for finding in result.findings
                    )
                )
                self.assertTrue(
                    all(
                        finding.detail
                        == "expected exact lowercase kebab-case [a-z0-9][a-z0-9-]*"
                        for finding in result.findings
                    )
                )
                self.assertIsNone(result.text)

        parent_cases = (
            (
                "missing",
                [["other", "domain", "Other", "", "", "active", ""]],
                "missing",
                None,
            ),
            (
                "wrong-type",
                [["markets", "tag", "Markets", "", "", "active", ""]],
                "incompatible",
                "tag",
            ),
            (
                "parented",
                [
                    ["root", "domain", "Root", "", "", "active", ""],
                    [
                        "markets",
                        "subdomain",
                        "Markets",
                        "root",
                        "",
                        "active",
                        "",
                    ],
                ],
                "incompatible",
                "subdomain",
            ),
            (
                "deprecated",
                [["markets", "domain", "Markets", "", "", "deprecated", ""]],
                "incompatible",
                "domain",
            ),
            (
                "reserved",
                [["markets", "domain", "Markets", "", "", "reserved", ""]],
                "incompatible",
                "domain",
            ),
            (
                "alias-only",
                [["other", "domain", "Other", "", "markets", "active", ""]],
                "missing",
                None,
            ),
        )
        for label, rows, observed_state, observed_type in parent_cases:
            with self.subTest(parent=label):
                before = vocab_text(rows)
                result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                    before,
                    "trading",
                    "markets",
                )
                self.assertEqual(result.state, "invalid")
                self.assertEqual(len(result.findings), 1)
                finding = result.findings[0]
                self.assertEqual(
                    finding.code,
                    "VOCABULARY_SUBDOMAIN_INSERTION_PARENT_CONFLICT",
                )
                self.assertEqual(finding.row, "markets")
                detail = json.loads(finding.detail)
                self.assertEqual(
                    set(detail),
                    {
                        "expected_parent",
                        "expected_status",
                        "expected_type",
                        "observed_parent",
                        "observed_state",
                        "observed_status",
                        "observed_type",
                    },
                )
                self.assertEqual(detail["expected_parent"], "")
                self.assertEqual(detail["expected_status"], "active")
                self.assertEqual(detail["expected_type"], "domain")
                self.assertEqual(detail["observed_state"], observed_state)
                self.assertEqual(detail["observed_type"], observed_type)
                self.assertEqual(finding.line is None, observed_state == "missing")
                self.assertIsNone(result.text)
                self.assertEqual(before, vocab_text(rows))

        conflict_cases = (
            (
                "same-child-parent",
                [["markets", "domain", "Markets", "", "", "active", ""]],
                "markets",
                "markets",
                ["id"],
            ),
            (
                "exact-wrong-type",
                [
                    ["markets", "domain", "Markets", "", "", "active", ""],
                    ["trading", "tag", "Trading", "", "", "reserved", ""],
                ],
                "trading",
                "markets",
                ["id"],
            ),
            (
                "exact-wrong-parent",
                [
                    ["markets", "domain", "Markets", "", "", "active", ""],
                    ["other", "domain", "Other", "", "", "active", ""],
                    [
                        "trading",
                        "subdomain",
                        "Trading",
                        "other",
                        "",
                        "deprecated",
                        "",
                    ],
                ],
                "trading",
                "markets",
                ["id"],
            ),
        )
        for label, rows, subdomain_id, parent_domain_id, contacts in conflict_cases:
            with self.subTest(conflict=label):
                result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                    vocab_text(rows),
                    subdomain_id,
                    parent_domain_id,
                )
                self.assertEqual(result.state, "invalid")
                finding = result.findings[0]
                self.assertEqual(
                    finding.code,
                    "VOCABULARY_SUBDOMAIN_INSERTION_CONFLICT",
                )
                detail = json.loads(finding.detail)
                self.assertEqual(detail["contact_fields"], contacts)
                self.assertEqual(detail["expected_parent"], parent_domain_id)
                self.assertIsNone(result.text)

        for status in ("active", "deprecated", "reserved"):
            for field in ("label", "allowed_aliases"):
                with self.subTest(status=status, field=field):
                    contact = [
                        "existing",
                        "tag",
                        "TRADING" if field == "label" else "Existing",
                        "",
                        "trading" if field == "allowed_aliases" else "",
                        status,
                        "",
                    ]
                    result = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
                        vocab_text(
                            [
                                [
                                    "markets",
                                    "domain",
                                    "Markets",
                                    "",
                                    "",
                                    "active",
                                    "",
                                ],
                                contact,
                            ]
                        ),
                        "trading",
                        "markets",
                    )
                    self.assertEqual(result.state, "invalid")
                    finding = result.findings[0]
                    self.assertEqual(
                        finding.code,
                        "VOCABULARY_SUBDOMAIN_INSERTION_CONFLICT",
                    )
                    self.assertEqual(
                        json.loads(finding.detail)["contact_fields"],
                        [field],
                    )
                    self.assertIsNone(result.text)

    def test_taxonomy_backfill_preserves_vocab_bytes_and_is_idempotent(self) -> None:
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final_newline=final_newline):
                    docs = documents(newline=newline, final_newline=final_newline)
                    topic = topic_row()
                    topic[6] = "topic-tag"
                    docs["topics"] = table(
                        atlas_state.TOPICS_HEADER,
                        [topic],
                        newline=newline,
                    )
                    if final_newline:
                        docs["topics"] += newline
                    before = vocab_text(
                        [
                            [
                                "article",
                                "source-kind",
                                "Article",
                                "",
                                "",
                                "deprecated",
                                "preserve",
                            ]
                        ],
                        newline=newline,
                        final_newline=final_newline,
                        tail="Unmanaged bytes — preserve exactly.",
                    )
                    result = atlas_state.prepare_taxonomy_backfill_candidate(
                        docs["manifest"],
                        docs["topics"],
                        docs["relations"],
                        before,
                        {
                            ARTIFACT: source_projection(
                                secondary_domains=["other-domain"],
                            )
                        },
                    )
                    self.assertEqual(result.state, "candidate", result.findings)
                    self.assertIsNotNone(result.text)
                    assert result.text is not None
                    self.assertEqual(result.text.endswith(newline), final_newline)
                    self.assertIn(
                        "Unmanaged bytes — preserve exactly.",
                        result.text,
                    )
                    self.assertIn(
                        "| article | source-kind | Article |  |  | deprecated | preserve |",
                        result.text,
                    )
                    self.assertEqual(
                        [change["id"] for change in result.changes],
                        [
                            "other-domain",
                            "test",
                            "test-subdomain",
                            "source-tag",
                            "topic-tag",
                        ],
                    )
                    self.assertEqual(
                        [change["type"] for change in result.changes],
                        ["domain", "domain", "subdomain", "tag", "tag"],
                    )
                    self.assertEqual(result.changes[2]["parent"], "test")
                    replay = atlas_state.prepare_taxonomy_backfill_candidate(
                        docs["manifest"],
                        docs["topics"],
                        docs["relations"],
                        result.text,
                        {
                            ARTIFACT: source_projection(
                                secondary_domains=["other-domain"],
                            )
                        },
                    )
                    self.assertEqual(replay.state, "no-op", replay.findings)
                    self.assertIsNone(replay.text)
                    self.assertEqual(replay.changes, ())

    def test_taxonomy_backfill_observes_only_locked_active_sources(self) -> None:
        docs = documents()
        active = manifest_row()
        archived = manifest_row()
        archived[0] = "2"
        archived[2] = "https://example.com/archived"
        archived[1] = atlas_state.source_id_for(archived[2])
        archived[3] = "summaries/sources/artifacts/2026/2026-07/archived.md"
        archived[10] = "archived"
        docs["manifest"] = table(atlas_state.MANIFEST_HEADER, [archived, active]) + "\n"
        result = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()),
            {ARTIFACT: source_projection()},
        )
        self.assertEqual(result.state, "no-op", result.findings)

        missing = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()),
            {},
        )
        self.assertEqual(missing.state, "invalid")
        self.assertEqual(
            {item.code for item in missing.findings},
            {"TAXONOMY_BACKFILL_SOURCE_SET_INVALID"},
        )

        drifted_projection = source_projection()
        drifted_projection["content_hash"] = HASH_B
        drifted = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()),
            {ARTIFACT: drifted_projection},
        )
        self.assertEqual(drifted.state, "invalid")
        self.assertEqual(
            {item.code for item in drifted.findings},
            {"TAXONOMY_BACKFILL_SOURCE_INVALID"},
        )

    def test_taxonomy_backfill_rejects_unsafe_bindings_completely(self) -> None:
        docs = documents()

        invalid_projection = source_projection(
            source_kind="Bad_ID",
            canonical_tags=["also_bad"],
        )
        invalid = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()),
            {ARTIFACT: invalid_projection},
        )
        self.assertEqual(invalid.state, "invalid")
        invalid_findings = [
            item
            for item in invalid.findings
            if item.code == "TAXONOMY_BACKFILL_ID_INVALID"
        ]
        self.assertEqual(len(invalid_findings), 2)
        self.assertEqual(
            {item.path for item in invalid_findings},
            {"vault://atlas/" + ARTIFACT},
        )
        for item in invalid_findings:
            detail = json.loads(item.detail)
            self.assertEqual(
                set(detail),
                {
                    "expected_parent_ids",
                    "expected_type",
                    "field",
                    "observed_parent",
                    "observed_state",
                    "observed_type",
                    "row_id",
                },
            )
            self.assertEqual(detail["observed_state"], "invalid-id")

        missing_kind = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()[1:]),
            {ARTIFACT: source_projection()},
        )
        self.assertIn(
            "TAXONOMY_BACKFILL_INSERT_UNSUPPORTED",
            {item.code for item in missing_kind.findings},
        )

        multi_type_topic = topic_row()
        multi_type_topic[2] = "shared"
        multi_type_topic[3] = "shared"
        multi_type_topic[1] = (
            "summaries/research/shared/shared/topics/test-topic/INDEX.md"
        )
        multi_type_docs = documents()
        multi_type_docs["topics"] = (
            table(atlas_state.TOPICS_HEADER, [multi_type_topic]) + "\n"
        )
        multi_type = atlas_state.prepare_taxonomy_backfill_candidate(
            multi_type_docs["manifest"],
            multi_type_docs["topics"],
            multi_type_docs["relations"],
            vocab_text(closed_vocab_rows()),
            {ARTIFACT: source_projection()},
        )
        self.assertIn(
            "TAXONOMY_BACKFILL_TYPE_CONFLICT",
            {item.code for item in multi_type.findings},
        )

        ambiguous = atlas_state.prepare_taxonomy_backfill_candidate(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text(closed_vocab_rows()),
            {
                ARTIFACT: source_projection(
                    secondary_domains=["other-domain"],
                    subdomains=["wide-subdomain"],
                )
            },
        )
        self.assertIn(
            "TAXONOMY_BACKFILL_PARENT_AMBIGUOUS",
            {item.code for item in ambiguous.findings},
        )

        shared_topic = topic_row()
        shared_topic[3] = "shared-subdomain"
        shared_topic[1] = (
            "summaries/research/test/shared-subdomain/topics/test-topic/INDEX.md"
        )
        shared_docs = documents()
        shared_docs["topics"] = table(atlas_state.TOPICS_HEADER, [shared_topic]) + "\n"
        parent_rows = [
            *closed_vocab_rows(),
            ["other", "domain", "Other", "", "", "reserved", ""],
            [
                "shared-subdomain",
                "subdomain",
                "Shared",
                "test",
                "",
                "deprecated",
                "",
            ],
        ]
        parent_conflict = atlas_state.prepare_taxonomy_backfill_candidate(
            shared_docs["manifest"],
            shared_docs["topics"],
            shared_docs["relations"],
            vocab_text(parent_rows),
            {
                ARTIFACT: source_projection(
                    primary_domain="other",
                    subdomains=["shared-subdomain"],
                )
            },
        )
        parent_findings = [
            item
            for item in parent_conflict.findings
            if item.code == "TAXONOMY_BACKFILL_PARENT_CONFLICT"
        ]
        self.assertEqual(len(parent_findings), 1)
        self.assertEqual(parent_findings[0].path, "vault://atlas/" + ARTIFACT)

    def test_taxonomy_backfill_rejects_token_contacts_in_every_status(self) -> None:
        docs = documents()
        projection = source_projection(canonical_tags=["new-tag"])
        for status in ("active", "deprecated", "reserved"):
            for token_field in ("label", "alias"):
                with self.subTest(status=status, token_field=token_field):
                    row = [
                        "existing-tag",
                        "tag",
                        "NEW-TAG" if token_field == "label" else "Existing tag",
                        "",
                        "new-tag" if token_field == "alias" else "",
                        status,
                        "",
                    ]
                    result = atlas_state.prepare_taxonomy_backfill_candidate(
                        docs["manifest"],
                        docs["topics"],
                        docs["relations"],
                        vocab_text([*closed_vocab_rows(), row]),
                        {ARTIFACT: projection},
                    )
                    self.assertIn(
                        "TAXONOMY_BACKFILL_TOKEN_CONFLICT",
                        {item.code for item in result.findings},
                    )

            wrong_type = atlas_state.prepare_taxonomy_backfill_candidate(
                docs["manifest"],
                docs["topics"],
                docs["relations"],
                vocab_text(
                    [
                        *closed_vocab_rows(),
                        ["new-tag", "source-kind", "New tag", "", "", status, ""],
                    ]
                ),
                {ARTIFACT: projection},
            )
            self.assertIn(
                "TAXONOMY_BACKFILL_TYPE_CONFLICT",
                {item.code for item in wrong_type.findings},
            )

    def test_vocabulary_resolver_preserves_source_degradation_and_blocks_topics(
        self,
    ) -> None:
        rows = [
            ["article", "source-kind", "Article", "", "guide", "reserved", ""],
            ["research", "domain", "Research", "", "science", "deprecated", ""],
            [
                "methods",
                "subdomain",
                "Methods",
                "research",
                "methodology",
                "reserved",
                "",
            ],
        ]
        classification = {
            "domain": {"id": "research", "label": "Science", "aliases": []},
            "subdomain": {
                "id": "methods",
                "label": "Methodology",
                "aliases": [],
                "parent": "research",
            },
            "tags": [{"id": "guide", "label": "Guide", "aliases": []}],
            "candidate_terms": ["seed"],
        }
        source_vocab, source_result, source_findings = (
            atlas_state.resolve_vocabulary_proposals(
                vocab_text(rows),
                classification,
                conflict_policy="candidate-term",
            )
        )
        self.assertEqual(source_findings, [])
        self.assertEqual(source_vocab, vocab_text(rows))
        assert source_result is not None
        self.assertEqual(source_result["primary_domain"], "research")
        self.assertEqual(source_result["subdomains"], ["methods"])
        self.assertEqual(source_result["canonical_tags"], [])
        self.assertEqual(source_result["candidate_terms"], ["seed", "Guide"])

        topic_vocab, topic_result, topic_findings = (
            atlas_state.resolve_vocabulary_proposals(
                vocab_text(rows),
                classification,
                conflict_policy="block",
            )
        )
        self.assertEqual(topic_vocab, vocab_text(rows))
        self.assertIsNone(topic_result)
        self.assertEqual(
            {item.code for item in topic_findings},
            {"TOPIC_VOCABULARY_CONFLICT"},
        )

    def test_research_complete_updates_only_topic_synthesis_date(self) -> None:
        docs = documents()
        event = {
            "type": "research-complete",
            "topic_id": TOPIC_ID,
            "inspection_sha256": "1" * 64,
            "pass_path": (
                "summaries/research/test/test-subdomain/topics/test-topic/"
                "passes/2026-07-20--initial-research.md"
            ),
            "pass_sha256": "2" * 64,
            "topic_index_sha256": "3" * 64,
            "subdomain_index_sha256": "4" * 64,
            "completed_on": "2026-07-20",
        }
        result = atlas_state.reduce_event(docs, event)
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(set(result.documents), {"topics"})
        candidate = apply_result(docs, result)
        self.assertIn("2026-07-20", candidate["topics"])
        replay = atlas_state.reduce_event(candidate, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})

    def test_select_topic_state_classifies_all_published_states(self) -> None:
        pending = relation_row(status="pending")
        cases = {
            "current": documents(),
            "dirty": documents(relations=[pending], state="dirty"),
            "refreshing": documents(relations=[pending], state="refreshing"),
            "blocked": documents(relations=[pending], state="blocked"),
        }
        for expected, docs in cases.items():
            with self.subTest(expected=expected):
                selection = atlas_state.select_topic_state(docs, TOPIC_ID)
                self.assertEqual(selection.state, expected)
                self.assertEqual(selection.topic["topic_id"], TOPIC_ID)
                self.assertEqual(selection.findings, ())

        absent = documents()
        absent["topics"] = table(atlas_state.TOPICS_HEADER, []) + "\n"
        self.assertEqual(
            atlas_state.select_topic_state(absent, TOPIC_ID).state, "absent"
        )
        archived = documents(state="archived")
        archived_selection = atlas_state.select_topic_state(archived, TOPIC_ID)
        self.assertEqual(archived_selection.state, "absent")
        self.assertIsNone(archived_selection.topic)

        invalid = documents(state="dirty")
        invalid_selection = atlas_state.select_topic_state(invalid, TOPIC_ID)
        self.assertEqual(invalid_selection.state, "invalid")
        self.assertIsNone(invalid_selection.topic)
        self.assertTrue(invalid_selection.findings)

    def test_inspection_rejects_absent_and_invalid_without_partial_context(
        self,
    ) -> None:
        absent = documents()
        absent["topics"] = table(atlas_state.TOPICS_HEADER, []) + "\n"
        invalid = documents(state="dirty")
        for expected, docs in (
            ("TOPIC_INSPECTION_ABSENT", absent),
            ("TOPIC_INSPECTION_INVALID", invalid),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(atlas_state.TopicInspectionError) as caught:
                    atlas_state.inspect_topic(
                        docs, {}, TOPIC_ID, "answer", inspection_revisions()
                    )
                self.assertEqual(caught.exception.code, expected)

    def test_inspection_hash_changes_with_pending_ids_not_bodies(self) -> None:
        first_edge = relation_row(status="pending", content_hash=HASH_A)
        first_docs = documents(
            relations=[first_edge], state="dirty", content_hash=HASH_A
        )
        first_artifacts = inspection_artifacts(first_docs, "refresh")
        first = atlas_state.inspect_topic(
            first_docs,
            first_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )

        changed_bodies = {
            path: {**artifact, "text": artifact["text"] + "\n"}
            for path, artifact in first_artifacts.items()
        }
        body_only = atlas_state.inspect_topic(
            first_docs,
            changed_bodies,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertEqual(first["inspection_sha256"], body_only["inspection_sha256"])

        second_edge = relation_row(status="pending", content_hash=HASH_B)
        second_docs = documents(
            relations=[second_edge], state="dirty", content_hash=HASH_B
        )
        second_artifacts = inspection_artifacts(second_docs, "refresh")
        second = atlas_state.inspect_topic(
            second_docs,
            second_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertNotEqual(first["pending_edge_ids"], second["pending_edge_ids"])
        self.assertNotEqual(first["inspection_sha256"], second["inspection_sha256"])

    def test_answer_inspection_is_bounded_and_hash_excludes_bodies(self) -> None:
        docs = documents()
        artifacts = inspection_artifacts(docs, "answer")
        result = atlas_state.inspect_topic(
            docs, artifacts, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertEqual(result["purpose"], "answer")
        self.assertEqual(set(result["payload"]), {"managed_sections", "freshness"})
        self.assertEqual(result["relations"], [])
        self.assertEqual(len(result["artifact_revisions"]), 1)

        topic_path = topic_row()[1]
        changed = {
            **artifacts,
            topic_path: {
                **artifacts[topic_path],
                "text": artifacts[topic_path]["text"].replace(
                    "topic current-answer", "changed current-answer"
                ),
            },
        }
        same_binding = atlas_state.inspect_topic(
            docs, changed, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertEqual(result["inspection_sha256"], same_binding["inspection_sha256"])
        changed[topic_path] = {
            **changed[topic_path],
            "revision": "sha256:" + "9" * 64,
        }
        changed_binding = atlas_state.inspect_topic(
            docs, changed, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertNotEqual(
            result["inspection_sha256"], changed_binding["inspection_sha256"]
        )

    def test_research_and_refresh_inspections_select_only_related_sources(
        self,
    ) -> None:
        applied = relation_row(status="applied", pass_path=PASS_PATH)
        research_docs = documents(relations=[applied], state="current")
        research_artifacts = inspection_artifacts(research_docs, "research")
        research = atlas_state.inspect_topic(
            research_docs,
            research_artifacts,
            TOPIC_ID,
            "research",
            inspection_revisions(),
        )
        research_summary = research["payload"]["source_summaries"][0]
        self.assertEqual(research_summary["source_id"], SOURCE_ID)
        self.assertEqual(
            {
                key: research_summary[key]
                for key in (
                    "relation",
                    "impact",
                    "confidence",
                    "answer_authoring_eligible",
                )
            },
            {
                "relation": "direct",
                "impact": "high",
                "confidence": "high",
                "answer_authoring_eligible": True,
            },
        )
        self.assertIn("subdomain_index", research["payload"])
        self.assertEqual(research["pending_edge_ids"], [])

        pending = relation_row(
            status="pending",
            relation="supporting",
            impact="low",
            confidence="medium",
        )
        refresh_docs = documents(relations=[pending], state="dirty")
        refresh_artifacts = inspection_artifacts(refresh_docs, "refresh")
        refresh = atlas_state.inspect_topic(
            refresh_docs,
            refresh_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertEqual(refresh["pending_edge_ids"], [pending[0]])
        self.assertEqual(
            refresh["payload"]["pending_edges"][0]["relation"]["edge_id"],
            pending[0],
        )
        refresh_summary = refresh["payload"]["pending_edges"][0]["source_summary"]
        self.assertEqual(
            {
                key: refresh_summary[key]
                for key in (
                    "relation",
                    "impact",
                    "confidence",
                    "answer_authoring_eligible",
                )
            },
            {
                "relation": "supporting",
                "impact": "low",
                "confidence": "medium",
                "answer_authoring_eligible": False,
            },
        )
        self.assertNotIn("subdomain_index", refresh["payload"])

    def test_inspection_fails_without_partial_payload_for_missing_artifact(
        self,
    ) -> None:
        docs = documents()
        artifacts = inspection_artifacts(docs, "answer")
        artifacts.clear()
        with self.assertRaises(atlas_state.TopicInspectionError) as caught:
            atlas_state.inspect_topic(
                docs, artifacts, TOPIC_ID, "answer", inspection_revisions()
            )
        self.assertEqual(caught.exception.code, "TOPIC_INSPECTION_UNAVAILABLE")

    def test_audit_instance_accepts_empty_scaffold_registries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                atlas_state.MANIFEST_PATH: table(atlas_state.MANIFEST_HEADER, [])
                + "\n",
                atlas_state.TOPICS_PATH: table(atlas_state.TOPICS_HEADER, []) + "\n",
                atlas_state.RELATIONS_PATH: table(atlas_state.RELATIONS_HEADER, [])
                + "\n",
                atlas_state.VOCAB_PATH: table(atlas_state.VOCAB_HEADER, []) + "\n",
            }
            for relative, text in paths.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            self.assertEqual(atlas_state.audit_instance(root), [])


if __name__ == "__main__":
    unittest.main()
