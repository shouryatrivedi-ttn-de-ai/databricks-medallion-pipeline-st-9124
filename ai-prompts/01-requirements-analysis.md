# AI Prompt 01 — Initial Requirements Analysis

## Prompt Sent

We are starting a data engineering capability exercise based on the specification in:

docs/assignment.md

Read the ENTIRE assignment before making any changes.

Your first task is analysis only.

DO NOT:
- generate application/source code yet
- generate the data generator yet
- create Bronze/Silver/Gold implementation yet
- create dashboard code yet
- invent requirements that are not in the assignment
- modify docs/assignment.md

Analyze the assignment carefully and create the following:

1. requirements-analysis.md
2. data-model.md
3. design-notes.md
4. data-quality-strategy.md
5. .cursor/rules/project.mdc

For requirements-analysis.md, cover:
- Problem Statement
- Functional Requirements
- Non-Functional Requirements
- Inputs and Outputs
- Acceptance Criteria
- Assumptions
- Edge Cases
- Ambiguities / Inconsistencies in the specification
- Clarifications that would be useful

For data-model.md, document:
- customers
- orders
- products
- columns and data types
- primary keys
- foreign keys
- relationships
- important business fields

For design-notes.md, propose the implementation design for:
- Sample Data Generation
- Bronze Layer
- Silver Layer
- Gold Layer
- Data Quality Reporting
- Dashboard
- Testing
- Error Handling

For data-quality-strategy.md, identify:
- Completeness checks
- Uniqueness checks
- Referential integrity checks
- Type/business-rule validation
- Expected intentional data-quality issues
- How bad records should be flagged
- How quality metrics should be calculated

For .cursor/rules/project.mdc, create persistent project instructions that tell Cursor to:
- follow the assignment as the primary specification
- follow Bronze -> Silver -> Gold architecture
- preserve Bronze data without cleaning
- flag invalid Silver records rather than silently deleting them
- use readable, modular and maintainable Python/PySpark/SQL
- prefer explicit schemas where appropriate
- write testable code
- avoid hardcoded secrets or credentials
- explain assumptions and trade-offs
- avoid modifying unrelated files
- validate generated code before considering a task complete
- ask for clarification when requirements are genuinely ambiguous rather than silently inventing behavior

IMPORTANT:
The assignment contains some potential inconsistencies, particularly around the number/category of Silver-layer quality checks. Identify these explicitly in requirements-analysis.md rather than silently resolving them.

Do not implement anything beyond these analysis/design artifacts.

At the end, provide:
1. a summary of what you created
2. the key requirements you identified
3. every ambiguity or inconsistency you found
4. the assumptions you recommend
5. the proposed implementation task breakdown

## AI Response Summary

Cursor analyzed the assignment and created the initial requirements, data model, design notes, data-quality strategy, and Cursor project rules.

It identified the main pipeline requirements and several ambiguities, including the inconsistency around the number of Silver quality checks, customer segmentation rules, lifetime value calculation, order-status treatment, and other design decisions.

## What I Accepted

- The overall Bronze → Silver → Gold → Dashboard structure.
- The identification of explicit requirements versus assumptions.
- The identification of ambiguities in the assignment.
- The initial data model and data-quality areas.
- The use of persistent Cursor project rules.

## What I Changed

The initial analysis required further refinement after review. In particular, the interpretation of the four core Silver quality checks was refined in the next iteration.

## What I Rejected

I did not accept the initial interpretation of the Silver quality checks without review.

## Why

The assignment contains inconsistencies around the number and categories of Silver quality checks. I wanted to make this an explicit engineering decision rather than silently choosing one interpretation.

## Validation

The generated requirements analysis was reviewed against the assignment before implementation began.