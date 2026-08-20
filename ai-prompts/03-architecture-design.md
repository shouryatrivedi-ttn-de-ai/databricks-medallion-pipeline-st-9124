# AI Prompt 03 — Architecture Design

## Prompt Sent

I've finished the requirements analysis. Before we start coding, I want to finalize the technical design.

Based on the assignment and the documents we've created so far, update the design notes and data model to describe how you think we should implement the pipeline from CSV → Bronze → Silver → Gold → Dashboard.

Keep the architecture simple and focused on the assignment. Don't introduce unnecessary technologies.

For Silver, make sure the design explains how the four core quality checks will work and how we'll retain bad records rather than silently dropping them.

For Gold, define how the three required aggregations will be built, including any assumptions we need to make around customer segmentation, lifetime value and order status.

Also include a practical testing approach and a step-by-step implementation order.

Where the assignment is ambiguous, clearly mark your proposal as an assumption rather than treating it as a requirement.

Don't write implementation code yet. I want to review the design first.

## AI Response Summary

Cursor updated the design notes and data model with a simple CSV → Bronze → Silver → Gold → Dashboard architecture.

The design includes the four core Silver checks, row-level quality flags, quality metrics, Gold aggregation rules, segmentation assumptions and a practical testing/implementation sequence.

During review, two design issues were identified and refined:
1. Customer segmentation needs a customers-first LEFT JOIN so inactive customers are retained.
2. Gold eligibility should be aggregation-specific rather than blindly excluding every Silver record with any quality failure.

## What I Accepted

- Simple Databricks Medallion architecture.
- Four core Silver checks.
- Row-level quality flags and failure reasons.
- Quality metrics as a separate reporting output.
- Customers-first LEFT JOIN for customer segmentation.
- Aggregation-specific Gold eligibility.
- Completed orders as the revenue basis.
- Explicitly documented segmentation assumptions.
- Practical phased testing approach.

## What I Changed

I asked Cursor to refine:
- how inactive customers are retained
- how critical versus non-critical Silver failures affect Gold

The resulting design uses customers-first LEFT JOIN for segmentation and aggregation-specific eligibility rules.

## What I Rejected

I rejected a blanket Gold rule where every Silver quality failure would automatically make a record unusable for every downstream aggregation.

## Why

Different quality failures have different consequences depending on the business aggregation. For example, a missing customer email does not necessarily make an otherwise valid order unusable for revenue analysis, while an orphan foreign key can make an order unsafe for customer-level aggregation.

## Validation

The architecture and data model were reviewed against the assignment requirements before implementation.