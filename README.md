# FHIR Spec to Spreadsheet

The provided script parses the information for each version of the [HL7 FHIR](https://www.hl7.org/fhir/) specification (up to R4) and returns each in a separate csv file. This allows FHIR devs to leverage standard spreadsheet features (Conditional Formatting, Filter, Search, etc.) and get a quick overview of the spec without clicking through multiple nested links.

### Spreadsheet Usage
The csv output files are in the [csv_as_hyperlink_true](/csv_as_hyperlink_true) and [csv_as_hyperlink_false](/csv_as_hyperlink_false) folders (the only difference is whether the Resource name in the first column is formatted as a hyperlink or a plaintext string in the csv file).

Alternatively, [here](https://docs.google.com/spreadsheets/d/1UvllrIFaPJLsM5I9lvm03DQiSxLQOxO3Ma2Jg_KT7eI/edit?usp=sharing) is a link to a Google Spreadsheet with all of the information appended together. Feel free download and/or create your own copy! Some use-cases of the spreadsheet include (though are not limited to):
- Find minimum required items (Conditional Formatting: starts with "1..")
- Compare resource differences between versions (Filter)
- Search keyword across entire specification (CTRL+F)
- ...etc.

### Script Usage
If you want to run the script yourself, here are the instructions:
1. Install Python3 (3.8.3 recommended)
2. Install requirements.txt (within the directory, `pip3 install -r requirements.txt`)
3. Run the script (within the directory, `python3 main.py`)
4. Follow the on-screen instructions

### Reporting Issues
If there are any errors with the output, please open an Issue on the [Issues Tab](https://github.com/ericpan64/fhir-spec-as-csv/issues) and I'll work on the fix. Alternatively feel free to add a pull request and I'll review. Thanks!
