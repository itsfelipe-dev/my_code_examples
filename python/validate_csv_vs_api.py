import requests
import json
import pandas as pd
import logging
import os
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from tabulate import tabulate


console = Console(theme=Theme({"logging.level.success": "green"}))
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%X",
    handlers=[
        RichHandler(rich_tracebacks=True, tracebacks_show_locals=True, console=console)
    ],
)
log = logging.getLogger("rich")

FILE_INPUT = "campos.csv"
FILE_OUTPUT = "campos_server.csv"
FILE_INPUT_COOKIES = "cookies.txt"
json_obj_list = []

"""
    Compare logical_format form ng_fields vs server
    Author      : Andres Orjuela
    Linkedin    : https://www.linkedin.com/in/itsfelipe/
"""


def check_files_exist(files):
    for file in files:
        if not os.path.isfile(file):
            return False
        if os.path.getsize(file) == 0:
            return False
    return True


file_list = [FILE_INPUT, FILE_INPUT_COOKIES]

if check_files_exist(file_list):
    log.info("Iniciando proceso.")
else:
    log.error(f"Los archivos necesarios no existen {file_list}.")
    log.info(f"En <{file_list[0]}> deberia contener el diccionario de NG_field")
    log.info(f"En <{file_list[1]}> deberia contener los cookies para la autenticacion")
    exit(1)


with open(FILE_INPUT_COOKIES, "r+") as r_cookies:
    cookies = r_cookies.readline().strip("\n")

headers = {
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Cookie": f"{cookies}",
    "Accept": "application/json",
}


def get_fields():
    """
    Read data from a CSV file, clean it, and return a DataFrame.

    Returns:
    pandas.DataFrame: Cleaned DataFrame containing the data.
    """
    df = pd.read_csv(FILE_INPUT, delimiter="\t", skip_blank_lines=True)
    data = pd.DataFrame(df)
    data.columns = [c.lower().replace(" ", "_") for c in data.columns]
    data = data.dropna(how="all")
    return data


def validate_server_vs_sheet(field, logicalFormatName_group):
    """
    Validate the logical format of a field against the CSV file, and compare if is the same or not.

    Args:
    field (str): The physical name of the field.
    logicalFormatName_group (str): The logical format of the field.

    Returns:
    tuple: A tuple containing the validation result (YES or NO) and the logical format from the CSV.
    """
    df_validate = get_fields()
    selected_rows = df_validate.loc[
        df_validate["physical_name_field"] == field, ["logical_format"]
    ]
    selected_rows = selected_rows.iloc[0, 0]

    if selected_rows == logicalFormatName_group:
        validation_result = "YES"
    else:
        validation_result = "NO"
    return validation_result, selected_rows


def download_file(field):
    """
     Get request to server filter by physical_name_field, building a json with logical_format_name_server logicalFormatName_group.
    Args:
        field (str) : expects a physical_name_field.
    Returns:
        none
    """
    targe_file_url = f"https://server/site/api&name={field}"
    response = requests.get(targe_file_url, headers=headers)
    if response.status_code == 200:
        try:
            response = json.loads(response.text)
        except:
            log.error("Revise el la autenticacion de cookies, respuesta vacia")
        logicalFormatName = response["data"][0]["logicalFormats"][0][
            "logicalFormatName"
        ]
        precisionName = response["data"][0]["logicalFormats"][0]["precisionName"]
        country = response["data"][0]["logicalFormats"][0]["country"]["nameSpanish"]

        if precisionName != None:
            logicalFormatName_group = f"{logicalFormatName}{precisionName}"
        else:
            logicalFormatName_group = logicalFormatName

        validation_result, logical_format_name_csv = validate_server_vs_sheet(
            field, logicalFormatName_group
        )
        json_obj_list.append(
            {
                "country": country,
                "physical_name_field": field,
                "logical_format_name_server": logicalFormatName_group,
                "logical_format_name_csv": logical_format_name_csv,
                "is_the_same_with_server": validation_result,
            }
        )

    else:
        log.exception(
            f"Failed to download. Status code: {response.status_code} , {targe_file_url}"
        )


def main():
    """
    Main function to orchestrate the process of downloading and validating data for multiple fields in server vs local data.
    """
    input_fields_df = get_fields()
    for field in input_fields_df["physical_name_field"]:
        log.info(f"Obteniendo: {field}")
        download_file(field)

    logging.addLevelName(70, "SUCCESS")
    logging.log(70, f"<RESULTANDO:>")
    reff = pd.json_normalize(json_obj_list)
    df = pd.DataFrame(data=reff)
    table = tabulate(df, headers="keys", tablefmt="grid")
    print(table)
    df.to_csv(FILE_OUTPUT, encoding="utf-8", index=False, header=True)
    logging.addLevelName(70, "SUCCESS")
    logging.log(70, f"Se escribe resultado en <{FILE_OUTPUT}>")


if __name__ == "__main__":
    main()