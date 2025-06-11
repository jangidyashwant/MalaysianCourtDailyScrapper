import time
import os
import re
import  copy
from datetime import datetime
import requests
import yaml
import logging
import csv
from anticaptchaofficial.hcaptchaproxyless import hCaptchaProxyless
from typing import Optional, Dict, Any
from urllib3.exceptions import InsecureRequestWarning
from random import randint
from lxml import etree
# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Constants
# MAX_COURTS = 50
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'DATA')
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")

if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)


def setup_logging():
    log_folder = os.path.join(BASE_DIR, "LOGS")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    
    log_filename = os.path.join(log_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    return log_filename


def solve_hcaptcha(site_key: str, current_url: str) -> Optional[str]:
    """
    Solves hCaptcha using AntiCaptcha service.
    """
    logging.info(f"Extracted hCaptcha sitekey: {site_key}")
    captcha_response = None

    try:
        solver = hCaptchaProxyless()
        solver.set_verbose(1)  
        solver.set_key("5f857c7478df7a9fb1f04f024402b7de") 

        solver.set_website_url(current_url)
        solver.set_website_key(site_key)

        logging.info("Submitting hCaptcha challenge to AntiCaptcha...")
        captcha_response = solver.solve_and_return_solution()

        if captcha_response:
            logging.info("hCaptcha solved successfully.")
        else:
            logging.error(f"Failed to solve hCaptcha. Error: {solver.error_code}")

    except Exception as e:
        logging.error(f"Exception occurred while solving hCaptcha: {e}")

    return captcha_response


def get_url_resp(url: str,
                 headers: Optional[Dict[str, str]] = None,
                 session: Optional[requests.Session] = None,
                 request_type: str = "GET",
                 payload: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3
                 ) -> Optional[requests.Response]:
    
    attempt = 0
    while attempt < max_retries:
        try:
            if request_type.upper() == "GET":
                resp = session.get(url, headers=headers, timeout=30, verify=False)
            elif request_type.upper() == "POST":
                resp = session.post(url, data=payload, headers=headers, timeout=30, verify=False)
            else:
                logging.error(f"Invalid request type: {request_type}")
                return None

            logging.info(f"[{request_type.upper()}] {url} - Status Code: {resp.status_code}")

            if resp.status_code in [200, 201]:
                sleep_time = randint(2, 5)
                logging.info(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                return resp
            else:
                logging.warning(f"Unexpected status code {resp.status_code}. Retrying...")
            
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
        
        attempt += 1
        backoff_time = 2 ** attempt  
        logging.info(f"Retrying in {backoff_time} seconds... (Attempt {attempt}/{max_retries})")
        time.sleep(backoff_time)

    logging.error(f"All retry attempts failed for {url}")
    return None
    

def load_config_from_yaml(yaml_file):
    try:
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file not found: {yaml_file}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
    return {}


def get_parsed_data(resp_content: bytes, ele_parser: str) -> list:
    tree = etree.HTML(resp_content)
    try:
        return tree.xpath(ele_parser)
    except Exception as e:
        logging.error(f"Error parsing data using XPath '{ele_parser}': {e}")
        return []

def fetch_data(session, source_conf):
    today = datetime.today().strftime("%Y-%m-%d")
    logging.info(f"Search by Hearing Date {today}")

    # Step 1: Hit the homepage to initialize session
    base_resp = get_url_resp(source_conf['homepage'], source_conf['headers'], session, "GET")
    if base_resp is None:
        logging.error("Failed to fetch homepage. Exiting...")
        return
    
    # Step 2: Fetch court list JSON
    court_list_resp = get_url_resp(
        source_conf['causelist_api'],
        source_conf['headers'], session, "GET"
    )
    if court_list_resp is None:
        logging.error("Failed to fetch court list. Exiting...")
        return
    
    court_list = court_list_resp.json().get("CourtList", [])
    if not court_list:
        logging.warning("Court list is empty.")
        return
    
    # Step 3: Loop over all the courts
    for court in court_list:
        court_id = court['CourtID']
        court_name = court['CourtName']
        logging.info(f"Processing court: {court_name} (ID: {court_id})")

        court_url = (
            f"https://efs.kehakiman.gov.my//EFSWeb/CauseList/Window/SearchResultByHearingDate.aspx"
            f"?CourtID={court_id}&Date={today}"
        )
        
        court_resp = get_url_resp(court_url, source_conf['headers'], session, "GET")
        if court_resp is None:
            logging.error(f"Failed to fetch court page for {court_name}")
            continue
        
        # Step 4: Extract viewstate & form fields to pass in the POST API
        tree = etree.HTML(court_resp.content)
        try:
            viewstate = tree.xpath(source_conf['parser']['viewstate'])[0]
            viewstate1 = tree.xpath(source_conf['parser']['viewstate1'])[0]
            viewstate_generator = tree.xpath(source_conf['parser']['viewstate_generator'])[0]

            event_validation = tree.xpath(source_conf['parser']['event_validation'])[0]
            viewstate_count = tree.xpath(source_conf['parser']['viewstate_count'])[0]
        except IndexError:
            logging.error(f"Failed to extract form fields for {court_name}")
            continue
        
        # Step 5: Prepare payload for POST request
        api_payload = copy.deepcopy(source_conf['api_payload'])
        api_payload.update({
            '__VIEWSTATEFIELDCOUNT': viewstate_count,
            '__VIEWSTATE': viewstate,
            '__VIEWSTATE1': viewstate1,
            '__VIEWSTATEGENERATOR': viewstate_generator,
            '__EVENTVALIDATION': event_validation
        })
        
        # Step 6: Solve hCaptcha
        site_key = re.findall(r'data-sitekey="(.*?)"', court_resp.text, re.DOTALL)
        if not site_key:
            logging.error(f"hCaptcha sitekey not found for {court_name}")
            continue
        site_key = site_key[0]
        current_url = court_resp.url
        
        captcha_response = solve_hcaptcha(site_key, current_url)
        logging.info(f"Captcha Solved: {captcha_response}")
        
        api_payload.update({
            'ctl00$Body$hCaptchaTokenField': captcha_response,
            'g-recaptcha-response': captcha_response,
            'h-captcha-response': captcha_response
        })
        
        # Step 7: Submit POST request to get hearing details
        court_api_resp = get_url_resp(court_url, source_conf['api_headers'], session, "POST", api_payload)
        if court_api_resp is None:
            logging.error(f"Failed to fetch hearing data for {court_name}")
            continue
        
        # Step 8: Parse table data
        logging.info(f"Parsing table data for {court_name}")
        page_content = court_api_resp.content
        header_elements = get_parsed_data(page_content, source_conf['parser']['table_headers'])
        table_headers = [" ".join(td.xpath(".//text()")).strip() for td in header_elements]
        row_elements = get_parsed_data(page_content, source_conf['parser']['table_rows'])
        table_data = []

        for row in row_elements:
            cells = row.xpath('./td')
            values = []
            for cell in cells:
                cell_text = " ".join(cell.xpath(".//text()")).replace("¬†", " ").strip()
                values.append(cell_text)
            row_dict = dict(zip(table_headers, values))
            table_data.append(row_dict)
        
        # Step 9: Save data to CSV
        filename = court_name.lower().replace(" ", "_").replace("-", "_").strip()
        out_file = os.path.join(DATA_FOLDER, f"{filename}.csv")
        
        try:
            with open(out_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=table_headers)
                writer.writeheader()
                writer.writerows(table_data)
            logging.info(f"Data saved to {out_file}")
        except Exception as e:
            logging.error(f"Error saving data to CSV for {court_name}: {e}")


def main():
    setup_logging()
    configs = load_config_from_yaml(CONFIG_FILE)
    source_name = "ecourtservices.kehakiman.gov"

    source_conf = configs.get("source", {}).get(source_name, {})

    if not source_conf:
        logging.error(f"No configuration found for source: {source_name}")
        return

    session= requests.Session()
    fetch_data(session, source_conf )
    


if __name__ == "__main__":
    main()
