# Customer churn — native Power BI project

Open **CustomerChurn.pbip** in Power BI Desktop. Keep the .Report and .SemanticModel folders beside it. This is a real PBIP/PBIR project with a TMDL semantic model, not a renamed PBIX or a set of DAX instructions.

## First opening

1. Open CustomerChurn.pbip (or CustomerChurn.Report/definition.pbir).
2. Select Home > Refresh to materialize the embedded Power Query table. There is intentionally no machine-specific cache.abf, so report visuals may be empty until this first refresh.
3. Check the overview against 7,043 customers, 1,869 churned, 26.5% churn rate and $139,130.85 observed churned monthly charges (card rounds to $139,131).
4. Visit Segment explorer. Choose exactly one Dimension, then optionally a Segment. Clear selections to return to the default Contract view.
5. Save in Desktop. If desired, use File > Save as to create a PBIX locally after successful refresh.

Power BI Desktop 2.159.1231.0 has now opened the PBIP and the genuine exported PBIX. Embedded data materialized, all three pages rendered, and Dimension/Segment slicers passed the Electronic check test (2,365 customers, 1,071 churned, 45.3%). See validation/native-runtime-result.json. No online Power BI publication has been performed.

## Report contents

Three pages and 23 native visuals: executive KPIs and four segment-rate bar charts; a segment explorer with Dimension/Segment slicers, four KPIs, two charts and a detailed table; and a definitions page. The overview is fixed to the full sample. Its independent charts do not cross-filter each other. The explorer's fields can filter only one independent dimension, not a joint customer cohort.

Data uses only the project's approved 17 segment rows from ../data/aggregates/segments.csv and the full-sample churned-monthly-charges total from summary.csv. The smallest source segment contains 1,024 customers. No customer identifiers, individual records, private source paths or credentials are embedded.

Each dimension summarizes the SAME 7,043 customers. The dynamic DAX measures select exactly one Dimension (Contract when none is selected), so counts and charges are not added across dimensions. If several dimensions are selected, they fall back to Contract if included; otherwise results are blank. Raw numeric columns are hidden and set to no default summarization. The overview's full-sample measures are deliberately fixed. Do not replace them with an unrestricted SUM of segment rows.

Observed churned MRR is a full-sample historical exposure measure: MonthlyCharges summed for Churn=Yes. It is not future revenue loss, ARR, intervention savings or CLV. Segment Monthly Charges includes both retained and churned customers. No payment-delay field exists. No joint segment effects, event trends or prediction timeline can be inferred from these summaries.

See ../DATA_PROVENANCE.md for pinned IBM source details and licensing uncertainty. The repository's code license does not establish a separate dataset license. Do not describe the dataset as CC0/public-domain or publish raw records.

## Reproduce and validate

From the project directory on Windows:

    python powerbi/scripts/build_powerbi.py
    .venv/Scripts/python.exe powerbi/scripts/validate_powerbi.py

The builder reads only the aggregate CSVs, then writes the PBIP, report JSON, TMDL, embedded Power Query, measures and data reconciliation summary. All JSON report documents declare Microsoft's public schemas. Twenty-four official schema documents, including referenced dependencies, are cached in schemas/registry.json for offline validation. The validator requires jsonschema (available in the project virtual environment).

validation/schema-validation.json records schema checks and bounded static reference checks. validation/data-summary.json records reconciliation. measures.dax and power-query/ChurnSegments.pq show exact model definitions; the operative copies are in the TMDL table.

## Format references used

- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
- https://github.com/microsoft/Analysis-Services/tree/master/pbidevmode/fabricps-pbip/SamplePBIP
- https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition

Microsoft's Sales sample was read for PBIP, PBIR, PBISM and an embedded #table partition. PBIR visual/role/formatting shapes were checked against Microsoft's public JSON schemas. Some web-search leads to newer skills-for-fabric chart examples returned 404 on direct fetch and were not copied as source files.

## Desktop test follow-up

The first Desktop test loaded the model but showed a blank report. The report-loader metadata has since been repaired against Microsoft CLI 0.5.0 scaffold defaults, including report-content version 2.0.0 (distinct from PBIR wrapper 4.0), platform metadata, base theme, and current card bindings. The revised report has since passed native Desktop reopen/render validation. See validation/RUNTIME_DIAGNOSIS.md.

## Ready-to-use files

CustomerChurn.pbix is the actual Desktop-exported, data-bearing report and has been reopened successfully. previews/ contains clean captures from that reopened PBIX, not mockups. The PBIP and report/model folders remain editable source. Latest Desktop saves reference some not-yet-public schema versions; runtime testing now takes precedence over the earlier schema-only report. The generator is a reproducible baseline and does not reproduce every Desktop-normalized formatting property.
