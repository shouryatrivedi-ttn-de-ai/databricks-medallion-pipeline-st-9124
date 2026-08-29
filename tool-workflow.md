# AI Tool Workflow

## Primary AI Tool Used

The primary AI tool used for this project was Cursor, supported by AI-assisted conversations for requirement clarification, technical reasoning, debugging, and documentation review.

AI was used as a development assistant rather than as an automatic code generator. The workflow involved providing project context, breaking the assignment into layers, generating or refining implementation ideas, running the code independently, validating outputs, and iterating when issues were discovered.

---

## How I Provided Project Context

Before implementing individual components, I established the project context around the assignment requirements and repository structure.

The recurring context included:

- E-commerce Medallion Architecture pipeline
- Bronze → Silver → Gold → Dashboard flow
- Databricks and Unity Catalog environment
- PySpark for ingestion and data quality processing
- SQL for Gold aggregations and dashboard queries
- Three source datasets: customers, orders, and products
- Intentional data quality issues in the generated sample data
- Requirement to flag bad records instead of deleting them
- Requirement to document AI usage and development decisions

I also maintained project-level Cursor instructions in:

`.cursor/rules/project.mdc`

The assignment document, repository structure, existing source files, and previous implementation decisions were used as context when working on later layers.

---

## How I Used AI for Requirement Analysis

AI was used to break the assignment into smaller technical and documentation requirements.

The requirement analysis focused on identifying:

- Required source datasets and schemas
- Expected sample data volumes
- Intentional data quality defects
- Bronze layer responsibilities
- Silver layer quality checks
- Gold aggregation requirements
- Dashboard requirements
- Validation expectations
- Documentation and AI prompt history requirements

The initial interpretation was refined during implementation when practical Databricks constraints and repository structure became clearer.

The resulting requirement analysis was documented in:

- `requirements-analysis.md`
- `data-model.md`
- `data-quality-strategy.md`

AI suggestions were treated as input for planning rather than as requirements by themselves. The assignment specification remained the source of truth.

---

## How I Used AI for Pipeline Design

AI was used to explore and refine the overall Medallion Architecture design.

The final design separated responsibilities by layer:

### Bronze

Bronze preserves source data with minimal transformation.

Responsibilities include:

- Reading CSV files
- Applying explicit schemas
- Writing Delta tables
- Adding ingestion metadata
- Recording ingestion information

### Silver

Silver performs data quality validation while retaining all source records.

The implemented checks include:

- Completeness
- Uniqueness
- Type/domain validation
- Referential integrity

Instead of deleting invalid records, Silver adds:

- `quality_check_result`
- `quality_failure_reasons`
- `_silver_processed_at`

This decision was made to preserve auditability and allow downstream logic to decide which failures are relevant to a particular metric.

### Gold

Gold creates business-ready aggregations.

The implemented tables are:

- `sales_by_product`
- `revenue_by_customer`
- `customer_segmentation`

AI helped evaluate eligibility logic, but the final design intentionally avoided filtering every Silver `FAIL` record globally. Instead, entity-specific critical failure codes determine whether records can contribute to specific Gold metrics.

---

## How I Used AI for Code Generation

AI was used to assist with implementation across Python, PySpark, and SQL.

Examples include:

- Sample data generation structure
- PySpark ingestion patterns
- Explicit schemas
- Delta table writes
- Data quality validation logic
- Window functions for duplicate detection
- Referential integrity joins
- Gold aggregation SQL
- Validation scripts
- Databricks execution troubleshooting

Generated suggestions were not accepted blindly.

The workflow was generally:

1. Define the requirement or problem
2. Provide relevant project context
3. Request a focused implementation or explanation
4. Review the proposed code
5. Adapt it to the existing repository architecture
6. Run it independently
7. Validate outputs
8. Debug failures
9. Refine the implementation

Prompt history documenting this process is available under:

`ai-prompts/`

---

## How I Validated AI-Generated Code and Logic

AI-generated or AI-assisted code was validated through execution and independent checks.

Validation included:

### Sample Data

The generated datasets were checked for:

- Expected row counts
- Expected schemas
- Intentional NULL values
- Duplicate identifiers
- Referential integrity violations

The generator also includes validation logic to verify the expected defects.

### Bronze

Bronze validation checks:

- Source row counts
- Delta table row counts
- Metadata columns
- Successful ingestion of all three datasets

Validation logic is documented in:

`src/bronze/validate_bronze.py`

### Silver

Silver validation checks:

- Bronze-to-Silver row retention
- Intentional defects being flagged
- Quality result columns
- Failure reason codes
- Quality metrics

Validation logic is documented in:

`src/silver/validate_silver.py`

### Gold

Gold validation checks:

- Aggregation calculations
- Revenue consistency
- Cross-table consistency
- Eligibility logic

Validation logic is documented in:

`src/gold/validate_gold.py`

This validation process was important because several issues were discovered only after executing the AI-assisted implementation.

---

## How I Used AI for Testing and Validation

AI was used to suggest validation scenarios and help reason about expected results.

However, validation was performed using repository scripts and actual Databricks execution rather than relying on AI confirmation.

The project includes validation at multiple layers:

- Sample data validation
- Bronze validation
- Silver validation
- Gold validation

This provided a meaningful testing layer focused on data pipeline correctness and intentional data quality defects.

Where validation results disagreed with expectations, the implementation or validation baseline was investigated rather than assuming the AI-generated logic was correct.

---

## How I Used AI for Debugging

AI was used as a debugging assistant by providing:

- Error messages
- Relevant code sections
- Expected behavior
- Actual behavior
- Databricks environment constraints

A typical debugging workflow was:

1. Reproduce the failure
2. Capture the error
3. Identify the relevant layer
4. Ask AI for possible causes
5. Compare suggestions against Spark or Databricks behavior
6. Implement a focused fix
7. Re-run validation
8. Commit the verified change

Examples of issues encountered include:

### Window Function Filtering

A Silver uniqueness implementation attempted to filter directly on a window function and resulted in:

`WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`

The solution was to materialize the duplicate count as a temporary column, filter using that column, and remove the helper column before writing.

### Gold Validation Baseline

Gold validation initially compared customer-level metrics against a broader eligible-order population.

The pipeline output was correct, but the validation baseline was inconsistent with the aggregation population. The validation logic was corrected and additional cross-table revenue consistency checks were added.

### Unity Catalog and Volume Paths

Databricks execution required adjustments for:

- Three-part Unity Catalog table names
- Volume paths
- Path resolution behavior
- Python imports from the Databricks Git repository

These issues were resolved through execution and iterative debugging.

---

## How I Used AI for Data Quality Checks

AI was used to help structure the data quality framework and individual checks.

The implementation uses modular quality checks rather than embedding all validation logic in one script.

The checks include:

- Completeness checks for critical fields
- Uniqueness checks for identifiers
- Type and domain validation
- Referential integrity validation

Standardized failure codes were used so downstream logic could distinguish between different failure types.

Examples include:

- `COMPLETENESS_EMAIL`
- `RI_CUSTOMER`

A key design decision was that a failed quality check does not automatically mean a record is unusable for every downstream metric. Gold eligibility uses failure codes to determine which issues are critical for a specific aggregation.

---

## Information I Avoided Sharing with AI Tools

This project uses synthetic sample data.

I avoided using:

- Real customer information
- Production credentials
- Access keys
- Secrets or tokens
- Internal production data
- Personally identifiable customer information
- Sensitive configuration values

When discussing debugging or implementation, only the minimum technical context required to understand the issue was shared.

For a real production pipeline, this would be especially important when working with customer data, infrastructure configuration, and authentication details.

---

## How I Would Reuse This Workflow in a Production Pipeline

The workflow can be reused as a structured AI-assisted development process:

1. Start with requirement analysis
2. Convert requirements into explicit technical contracts
3. Create a design before implementation
4. Break work into small, testable tasks
5. Provide AI with focused context
6. Review generated suggestions instead of accepting them automatically
7. Execute code independently
8. Add automated validation
9. Debug using actual error evidence
10. Document accepted, modified, and rejected AI suggestions
11. Capture reusable patterns for future projects

For production work, I would extend this with:

- Formal automated tests
- CI/CD validation
- Code review
- Secrets management
- Data contracts
- Monitoring and alerting
- Structured logging
- Versioned deployment workflows

---

## Lessons Learned

The most useful AI workflow was iterative rather than one-shot.

AI was effective for:

- Breaking down problems
- Explaining Spark and SQL behavior
- Generating implementation starting points
- Suggesting debugging directions
- Reviewing documentation

AI was less reliable when:

- It lacked complete repository context
- It assumed APIs or Databricks behavior without execution
- It suggested generic solutions that did not match the existing architecture
- Validation assumptions differed from the actual business logic

The main lesson from this project is that AI accelerates implementation, but execution and validation remain the responsibility of the engineer.

The strongest workflow was:

**Context → focused task → AI suggestion → review → implementation → execution → validation → debugging → documentation**

This workflow is reusable beyond this assignment because it keeps AI assistance connected to engineering evidence rather than treating generated code as automatically correct.