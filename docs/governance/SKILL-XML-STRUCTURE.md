# Skill XML Structure 1.0

This document defines the canonical structure for XML instruction bodies in `SKILL.md`. YAML frontmatter remains the package metadata format and is not part of the XML body. Markdown/XML coexistence in an individual skill is not defined here: a body using this format contains one XML document and no surrounding Markdown.

## Why XML and what this validates

Named elements make each instruction part explicit and readable to people reviewing or authoring a skill. `scripts/validate/validate_skill_xml.py` checks syntax and this document's structural rules. It does not execute XML, load a skill, interpret instructions, prove that a model follows them, or establish compatibility with any runtime or channel.

## Required document shape

The document has exactly one `<skill_instructions version="1.0">` root. Its top-level sections appear at most once and in this order:

| Section | Required | Meaning |
| --- | --- | --- |
| `<purpose>` | Yes | The bounded task this skill helps complete. |
| `<guidelines>` | Yes | General constraints; contains one or more `<guideline>` text elements. |
| `<steps>` | Yes | Ordered procedure; contains one or more `<step id="S1">` text elements with unique sequential-style IDs. |
| `<decision_rules>` | No | Conditional choices; each `<rule id="D1">` contains `<when>`, `<action>`, and optional `<otherwise>` in that order. |
| `<input_context>` | No | Input descriptions; contains `<field name="…" type="…" required="true|false" trust="trusted|untrusted">description</field>`. |
| `<output_contract>` | Yes | What a successful result contains and how it is presented. |
| `<failure_handling>` | Yes | What to do when inputs, evidence, or an operation are unavailable. |
| `<quality_checks>` | No | Review criteria; contains one or more `<check>` text elements. |
| `<examples>` | No | One or more `<example id="E1">` records, each with `<input trust="trusted|untrusted">`, `<expected_behavior>`, and `<expected_output>` in that order. |
| `<references>` | No | Supporting sources; contains `<reference href="…">human-readable description</reference>` elements. |

`field` types are `text`, `string`, `integer`, `number`, `boolean`, `date`, `url`, or `json`. Names use unique lowercase snake_case identifiers. Step, rule, and example identifiers use `S1`, `D1`, and `E1` forms and are unique within their section. XML-escape reserved characters such as `&` and `<`; use CDATA when an example must show literal markup. The validator treats example text as data and never executes it.

Every leaf needs meaningful human-readable text. Empty text and obvious drafting markers (`TODO`, `TBD`, `FIXME`, `PLACEHOLDER`, `lorem ipsum`, and runs of three or more dots) are rejected. A validator cannot judge whether prose is useful or factually correct; reviewers still need to read it.

## Safe authoring and compatibility

The static validator rejects DTD and entity declarations, limits a body to 256 KB, and does not resolve external resources. XML content is plain text data. Untrusted inputs must be explicitly labeled and must not gain instruction authority by appearing in an example or field description.

This format is versioned independently from package metadata. The current validator is opt-in for XML bodies and is wired to check the authoring template; existing Markdown skill bodies are not implicitly reinterpreted. Changing a runtime loader, migrating existing skills, package/release behavior, or claiming model/channel compatibility requires separate implementation and evidence.

## Minimal example

The complete authoring example, including unchanged YAML frontmatter and optional sections, is [`../../templates/skill-template/SKILL.md`](../../templates/skill-template/SKILL.md).
