import asyncio
from js import document
from pyodide import create_proxy
import pandas as pd
from lxml import etree
import json


def clean_namespace(root: etree.Element) -> etree.Element:
    """
    This take in a valid etree element and removes all namespaces
    from the XML tags. This just ensures that xpath queries do not
    need to reference the namespace as well.
    We re-assign the tag to the localname only and therefore remove any
    namespaces which previously exist.
    The final step is the cleanup_namespaces process to remove the
    namespace definitions from the tree
    """

    # first we visit each node in the tree and set the tag name to its localname
    # value; thus removing its namespace prefix

    for elem in root.getiterator():
        if not (type(elem) == etree._Comment):
            elem.tag = etree.QName(elem).localname

    # at this point there are no tags with namespaces, so we run the cleanup
    # process to remove the namespace definitions from within the tree.

    etree.cleanup_namespaces(root)
    return root


def processroutetable(output: str) -> list:

    """
    This will take in the XML output from the Juniper routing-table
    Ensure that the master tag sometimes seen in the CLI is removed
    Load the XML Output string into Etree
    Remove the namespaces using the clean_namespace function
    Iterate over each prefix using rt-destination and append the records
    into route_table to build up the dataset
    """

    route_table = []
    output = output.replace("{master}", "")
    out_xml = etree.fromstring(
        output, parser=etree.XMLParser(huge_tree=True, recover=True)
    )
    out_xml = clean_namespace(out_xml)
    prefixes = out_xml.xpath(".//rt-destination")
    for route in prefixes:
        routing_instance = "".join(
            route.xpath("ancestor::route-table/table-name/text()")
        )
        next_hop = route.xpath("following-sibling::rt-entry/nh/to/text()")
        next_hop.sort()
        next_hop = ", ".join(next_hop)
        via = route.xpath("following-sibling::rt-entry/nh/via/text()")
        via.sort()
        via = ", ".join(via)
        entry = {
            "routing_instance": routing_instance,
            "prefix": route.text,
            "next_hop": next_hop,
            "via": via,
        }
        route_table.append(entry)
    return route_table


def process_json(target) -> dict:
    """
    Pull the json output stored in the div and return
    back using json.loads
    """
    struct_data = document.getElementById(target).innerHTML
    struct_data = struct_data.replace("'", '"')
    struct_data = json.loads(struct_data)
    return struct_data


async def upload_file(event) -> None:
    """
    This needs to be handled as an async function
    It is called from the JS proxy
    In this case we take the outputs into Pandas Dataframes
    We then do a merge on the Dataframes to get any differences
    The output of the dataframe is then sent to construct_table
    which outputs the HTML Table back into the browser
    """

    fileoutput = event.target.files.to_py()

    for f in fileoutput:
        if f.name.startswith("prev"):
            target = "output1"
        if f.name.startswith("cur"):
            target = "output2"
        output = await f.text()
        route_table = processroutetable(output)
        document.getElementById(target).innerHTML = ""
        document.getElementById(target).innerHTML = route_table
        if target == "output2":
            pre = process_json("output1")
            post = process_json(target)
            df_pre = pd.DataFrame(pre)
            df_post = pd.DataFrame(post)
            merged_df = pd.merge(
                df_pre,
                df_post,
                how="outer",
                indicator=True,
                on=["routing_instance", "prefix"],
                suffixes=(f"_PRE", f"_CURR"),
            )
            df = merged_df.drop(merged_df[merged_df._merge == "both"].index)
            df = df.drop("_merge", axis=1)
            df = df.fillna(value="-")
            df = df.rename(
                columns={
                    "routing_instance": "routing instance",
                    "next_hop_PRE": "Previous Next Hop",
                    "via_PRE": "Previous Via",
                    "next_hop_CURR": "Current Next Hop",
                    "via_CURR": "Current Via",
                }
            )
            struct_data = df.to_dict("records")
            if struct_data:
                cols = [k for k in struct_data[0].keys()]
                id = f"final differences"
                outputdiv = construct_table(columns=cols, records=struct_data, id=id)
                document.getElementById("output1").innerHTML = ""
                document.getElementById("output2").innerHTML = ""
                Element("output1").element.appendChild(outputdiv)
                document.getElementById("myInput").style.display = "block"
            else:
                document.getElementById("output1").style.display = "none"
                document.getElementById("output2").style.display = "none"
                document.getElementById("output3").innerHTML = ""
                document.getElementById("output3").style.color = "DarkGreen"
                document.getElementById("output3").innerHTML = "NO DIFFERENCES DETECTED IN THE OUTPUTS"


def construct_table(columns, records, id) -> None:
    """
    This function will build a HTML Table
    from an empty div.
    It will return a complete HTML table element which
    will be returned back.
    """

    # Construct a new div element to contain the table
    outputdiv = document.createElement("div")
    span = document.createElement("span")
    outputdiv.appendChild(span)

    table = document.createElement("table")
    table.className = "table-arrows"
    table.id = f"{id} table"
    headingrow = document.createElement("tr")

    # Create the table headings
    for headentry in columns:
        tableheading = document.createElement("th")
        tableheading.innerHTML = headentry
        headingrow.appendChild(tableheading)

    table.appendChild(headingrow)

    # Process the table rows
    for entry in records:
        tablerow = document.createElement("tr")
        for col in entry.values():
            tabledata = document.createElement("td")
            tabledata.innerHTML = col
            if list(entry.values())[4] == "-":
                tabledata.style.backgroundColor = "#6FC244"
            else:
                tabledata.style.backgroundColor = "#F48980"
            tablerow.appendChild(tabledata)
        table.appendChild(tablerow)

    # Append the table to the div
    outputdiv.appendChild(table)
    return outputdiv


def main() -> None:
    """
    Create an EventListener and a proxy for JS
    The proxy makes the JavaScript object behave
    like a Python object.
    Triggered when the user attaches the 2nd file
    When this happens then the upload_file is called
    """
    document.getElementById("myInput").style.display = "none"
    file_event = create_proxy(upload_file)
    # access the DOM in Python
    event1 = document.getElementById("outputfile1")
    event1.addEventListener("change", file_event, False)
    event2 = document.getElementById("outputfile2")
    event2.addEventListener("change", file_event, False)


try:
    main()

except Exception as x:
    print("Error starting the routing-table app: \n {}".format(x))
    
