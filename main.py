"""
Pulls-down files and writes to `output`
"""

from bs4 import BeautifulSoup
import requests
import csv
import sys
from copy import deepcopy
from config import *
from os import path
import json

def parse_td_elements(request_url, writer, query_div_id, datatype_dict, nestingHeader=''):
    """ Performs HTML request, parsing, and <td> element writing to .csv"""
    # TODO: refactor this entirely...
    # Helper functions
    hyperlink = lambda url, label: f'=HYPERLINK(\"{url}\",\"{label}\")'
    add_extension = lambda name, ext: f'{name}.{ext}'
    del_extension = lambda name: name[0:name.rfind('.')]
    # Soup-up HTML
    page = requests.get(request_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    html_body = soup.find('body')
    struct_table = html_body.find('div', {'id': query_div_id}).table
    # Add static data
    resource_name = del_extension(request_url[request_url.rfind('/')+1:]) # TODO: look 
    resource_link = hyperlink(request_url, resource_name) if AS_HYPERLINK else resource_name
    nesting = nestingHeader + resource_name # keep track of item nesting
    # hacky soln: add 8 lines of static resource data inherited from Resource, DomainResource
    # TODO: only add this if it's the base spec, otherwise get information elsewhere
    inherited_from_Resource = [
        [resource_link, add_extension(nesting, 'id'), 'id', 'Σ', '0..1', 'id', 'Logical id of this artifact'],
        [resource_link, add_extension(nesting, 'meta'), 'meta', 'Σ', '0..1', 'Meta', 'Metadata about the resource'],
        [resource_link, add_extension(nesting, 'implicitRules'), 'implicitRules', '?! Σ', '0..1', 'uri', 'A set of rules under which this content was created'],
        [resource_link, add_extension(nesting, 'language'), 'language', '', '0..1', 'code', 'Language of the resource contentLanguage  (Required)'],
    ]
    inherited_from_DomainResource = [
        [resource_link, add_extension(nesting, 'text'), 'text', 'I', '0..1', 'Narrative', 'Text summary of the resource, for human interpretation'],
        [resource_link, add_extension(nesting, 'contained'), 'contained', '', '0..*', 'Resource', 'Contained, inline Resources'],
        [resource_link, add_extension(nesting, 'extension'), 'extension', '', '0..*', 'Extension', 'Additional Content defined by implementations'],
        [resource_link, add_extension(nesting, 'modifierExtension'), 'modifierExtension', '?!', '0..*', 'Extension', 'Extensions that cannot be ignored'],
    ]
    writer.writerows(inherited_from_Resource)
    writer.writerows(inherited_from_DomainResource)
    # Add resource-specific data (each row contains 5 <td> elements)
    curr_row = [resource_link, nesting]
    count = 0
    for tr in struct_table.find_all('tr'):
        for td in tr.find_all('td'):
            curr_row.append(td.text.strip())
            count += 1
            # adjust nesting on 1st <td>
            if count % 5 == 1:
                # adjust based on <a title=...>
                tag = td.find('a')
                if tag != None:
                    if tag.title == None:
                        continue
                    curr_title = str(tag['title'])
                    curr_nesting = curr_title[:curr_title.find(' ')] # format: "Resource.dataElement"
                    curr_text = td.text.strip() # format: "dataElement"
                    # update nesting
                    if curr_text == resource_name:
                        continue
                    if curr_nesting[curr_nesting.rfind('.'):] != curr_text:
                        nesting = nestingHeader + curr_nesting
                        curr_row[1] = del_extension(nesting)
                        # handle [x] cases
                        if curr_nesting.rfind('[x]') != -1:
                            nesting = nestingHeader + del_extension(curr_nesting)
                curr_row[1] = add_extension(curr_row[1], td.text.strip())
            # append row every 5th item 
            if count % 5 == 0:
                writer.writerow(curr_row)
                # append datatype info when available
                dtype = curr_row[-2] # bold assumption
                if dtype in datatype_dict.keys():
                    for r in datatype_dict[dtype]:
                        new_row = curr_row[:2] + r
                        new_row[1] = new_row[1] + new_row[2]
                        writer.writerow(new_row)
                del curr_row[2:]
                curr_row[1] = nesting

def get_datatype_to_rows_dict(url, query_div_id):
    """ Returns a dict mapping FHIR core datatypes to primitive values """
    # TODO: Get Datatypes as something that can be 
    # # 1) stored in-memory
    # # 2) expanded to base primitive elements
    # Rn, it's a dict { 'TypeName' : [[Name, Flags, Cardinality, Datatype, Description], ...]}
    # Same div id: 'tbl-inner'
    ROWS_UPPER_BOUND = 100
    # Approach: pre-allocate to a reasonable upper-bound and clean-up/resort later (e.g. 100 rows)
    large_empty_list = lambda: [None] * ROWS_UPPER_BOUND
    res = dict()
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    html_body = soup.find('body')
    all_tbls = html_body.find_all('div', {'id': query_div_id})
    keys_to_primitive_expand = set()
    for tbl in all_tbls:
        # Get all <tr>s
        table_rows = tbl.find_all('tr')
        assert len(table_rows) > 3
        # table_rows[0] contains headers. table_rows[1] has first row of data
        # Assume first <tr> has element name. Find in first <td>.text. Use as key
        name = table_rows[1].td.text.strip()
        # Assume rest of <tr>s should be appended. Data from each <td> is compressed to 5-item list
        all_rows = large_empty_list()
        count = 0
        for i in range(2, len(table_rows)):
            curr_row = [''] * 5
            for td in table_rows[i].find_all('td'):
                idx = count % 5
                curr_row[idx] = td.text.strip()
                count += 1
                if count % 5 == 0:
                    all_rows[i-2] = curr_row
            # Flag if it still needs expanding
            if curr_row[3] != '' and curr_row[3][0].isupper():
                keys_to_primitive_expand.add((name, curr_row[3].strip()))
        res[name] = all_rows
    # Expand until all primitives, or over a certain limit
    remove_after_none = lambda l: l[:l.index(None)] if l.index(None) >= 0  else l
    count = 0
    while count < 100 and len(keys_to_primitive_expand) > 0:
        tup = next(iter(keys_to_primitive_expand))
        (curr_key, lookup_key) = tup
        keys_to_primitive_expand.remove(tup)
        if lookup_key not in res:
            continue
        base_insert_rows = remove_after_none(res[lookup_key])
        curr_rows = res[curr_key]
        # Find where to insert into the current rows
        idx_to_insert_key_map = dict() # Maps: idx_to_insert -> lookup_key
        for i, r in enumerate(curr_rows):
            if r == None:
                break
            if r[3].strip() == lookup_key:
                idx_to_insert_key_map[i+1] = lookup_key
        # Perform the insert (scoot elements as needed)
        n_inserted = len(base_insert_rows)
        for idx in idx_to_insert_key_map:
            # Append path prefix (e.g. `period.` in `period.start`)
            prefix = f'{curr_rows[idx-1][0]}.'
            insert_rows = deepcopy(base_insert_rows)
            for i in range(len(insert_rows)):
                insert_rows[i][0] = prefix + insert_rows[i][0]
            # Not great but fine... increases size of list
            temp = curr_rows[idx:]
            curr_rows[idx:idx + n_inserted] = insert_rows
            curr_rows[idx + n_inserted:] = temp
    # Cleanup None values
    for key in res:
        res[key] = remove_after_none(res[key])
    return res

def create_csv(url_list, fp, query_div_id, datatype_dict):
    """ Creates/overwrites csv file as name.csv """
    col_headers = ['Resource', 'Nesting', 'Resource Content Name', 'Flags', 'Cardinality', 'Datatype', 'Description']
    
    # TODO: add logic to handle other FHIR spec cases
    # Start writing .csv
    with open(fp, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(col_headers)
        for url in url_list:
            print(f"Parsing {url}...")
            parse_td_elements(url, writer, query_div_id, datatype_dict)

if __name__ == '__main__':
    # Get datatypes
    if path.exists(FHIR_DATATYPES_JSON_FP):
        with open (FHIR_DATATYPES_JSON_FP, 'r') as input:
            datatype_dict = json.load(input)
    else:
        datatype_dict = get_datatype_to_rows_dict(FHIR_DATATYPES_URL, FHIR_DATATYPES_QUERY_DIV_ID)
        with open(FHIR_DATATYPES_JSON_FP, 'w') as output:
            json.dump(datatype_dict, output)

    # Parse from URLs
    for output_fp, (input_fp, query_div_id) in INPUT_FILES.items():
        with open(input_fp) as f:
            url_list = f.readlines()
        url_list = [url.strip() for url in url_list]
        create_csv(url_list, output_fp, query_div_id, datatype_dict)