from bs4 import BeautifulSoup
import requests
import csv
import sys

def get_html_body(url):
    """ Returns BeautifulSoup tag object with HTML body """
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    html_body = soup.find('body')
    return html_body

def get_resource_list(base_url):
    """ Returns list of html filenames """
    list_ext = 'resourcelist.html'
    html_body = get_html_body(base_url + list_ext)
    body_tables = html_body.find_all('table')
    ul_tags = body_tables[1].find_all('ul')
    resource_list = [] # parsed list of individual resource html pages
    for ul in ul_tags:
        li_tags = ul.find_all('li')
        for li in li_tags:
            text = li.text[:-2].split(' ')[0] + '.html'
            resource_list.append(text)
    return resource_list

def parse_write_td_elements(base_url, writer, resource, as_hyperlink, nestingHeader=''):
    """ Performs HTML request, parsing, and <td> element writing to .csv"""
    # Helper functions
    hyperlink = lambda url, label: '=HYPERLINK(\"%s\",\"%s\")' % (url, label)
    add_extension = lambda name, ext: '%s.%s' % (name, ext)
    del_extension = lambda name: name[0:name.rfind('.')]
    request_url = base_url + resource
    struct_table = get_html_body(request_url).find('div', {'id': 'tbl-inner'}).table
    # Add static data
    resource_name = del_extension(resource)
    resource_link = hyperlink(request_url, resource_name) if as_hyperlink else resource_name
    nesting = nestingHeader + resource_name # keep track of item nesting
    curr_row = [resource_link, nesting]
    # hacky soln: add 8 lines of static resource data inherited from Resource, DomainResource
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
    # Add resource-specific data
    # hacky soln: keep count of every 5th <td> element, and add row then
    count = 0
    for tr in struct_table.find_all('tr'):
        for td in tr.find_all('td'):
            curr_row.append(td.text.strip())
            count += 1
            # adjust nesting on 1st item
            if count % 5 == 1:
                # check nesting update where item has an <a> tag to validate
                tag = td.find('a')
                if tag != None: 
                    curr_title = str(tag['title'])
                    curr_nesting = curr_title[:curr_title.find(' ')] # format: "Resource.dataElement"
                    curr_text = td.text.strip() # format: "dataElement"
                    # update nesting
                    if curr_text == resource_name:
                        continue # handles base case
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
                del curr_row[2:] # keep first two items
                curr_row[1] = nesting

def create_csv(base_url, resource_list, name, as_hyperlink=True):
    """ Creates/overwrites csv file as name.csv """
    filename = name + '.csv'
    col_headers = ['Resource', 'Nesting', 'Resource Content Name', 'Flags', 'Cardinality', 'Datatype', 'Description']
    
    # Start writing .csv
    with open(filename, 'w', newline='') as csvfile:
        # progress bar from: https://stackoverflow.com/a/3160819
        toolbar_width = len(resource_list) // 3
        toolbar_count = 0
        sys.stdout.write("Creating %s.csv\n" % name)
        sys.stdout.write("[%s]" % (" " * toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(col_headers)
        # track in progress bar
        # add 'Resource' and 'DomainResource' to .csv first
        for resource in resource_list:
            # get request, grab table for resource
            parse_write_td_elements(base_url, writer, resource, as_hyperlink)
            # update bar every third resource
            toolbar_count += 1
            if toolbar_count % 3 == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("]\n")

if __name__ == '__main__':
    as_hyperlink = False
    # save FHIR main pages
    fhir_base_urls = [
        'https://www.hl7.org/fhir/DSTU2/',
        'https://www.hl7.org/fhir/STU3/',
        'https://www.hl7.org/fhir/R4/'
    ]

    # create csvs
    start = len('https://www.hl7.org/fhir/')
    for base_url in fhir_base_urls:
        base_list = get_resource_list(base_url)
        name = base_url[start:base_url.find('/', start)]
        create_csv(base_url, base_list, name, as_hyperlink=as_hyperlink)
