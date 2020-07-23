# FHIR Spec to Spreadsheet

## Overview
The provided script parses the information for each version of the [HL7 FHIR](https://www.hl7.org/fhir/) specification (up to R4) and returns each in a single handy-dandy .csv file to work with. This allows FHIR devs to leverage standard spreadsheet features (Conditional Formatting, Filter, Search, etc.) and get a quick overview of the spec without clicking through multiple nested links.


### Spreadsheet Usage
- Use separate .csv files
- Use included excel spreadsheet (includes all 3 versions in one spreadsheet)
- Example benefits -- conditional formatting on cardinality (starts with "1..") will highlight minimum required fields

### Script Usage
- install requirements
- `python3 main.py`
- include example run picture
- Note basic QA, if issues found feel free to open github issue and I'll look into it, or add your own pull request!