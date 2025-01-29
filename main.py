
import json
import re
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email sending function
def send_email(subject, body, recipient_email):
    sender_email = "talhahaider074@gmail.com"
    sender_password = "bnjclnkuihyjwgrg"
    
    # Set up the server and login
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    
    # Set up the email content
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()

def remove_special_characters(text):
    cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', text) 
    cleaned_text = cleaned_text.replace('\n', ' ').replace('\r', '')
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def load_existing_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []

def compare_and_update_data(existing_data, new_data, filename):
    new_records = []

    existing_lot_info = {record['Lot info'] for record in existing_data}

    for record in new_data:
        if record['Lot info'] not in existing_lot_info:
            new_records.append(record)

    if new_records:
        for record in reversed(new_records):
            existing_data.insert(0, record)
        
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, ensure_ascii=False, indent=4)
        
        # Prepare the email content
        new_data_details = "\n".join([json.dumps(record, ensure_ascii=False, indent=4) for record in new_records])
        subject = "New Data Added to Copart"
        body = f"New data has been added:\n\n{new_data_details}"

        recipient_email = "test@yopmail.com"
        send_email(subject, body, recipient_email)

        for record in new_records:
            print(f"New Record: {json.dumps(record, ensure_ascii=False, indent=4)}")
    else:
        print("No new records found.")

driver = webdriver.Chrome()
driver.maximize_window()

url = "https://www.copart.com/lotSearchResults?free=false&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%209999999%5D%22%5D,%22YEAR%22:%5B%22lot_year:%5B2015%20TO%202026%5D%22%5D,%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D&displayStr=AUTOMOBILE,%5B0%20TO%209999999%5D,%5B2015%20TO%202026%5D&from=%2FvehicleFinder&fromSource=widget&qId=67c4262c-faa1-4f1e-a31d-6427dd596ef9-1737961677438"
date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

existing_filename = 'copart_data.json'
existing_data = load_existing_data(existing_filename)

try:
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    
    dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sort-dropdown .p-dropdown-label")))
    dropdown.click() 
    
    buy_now_option = wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(@aria-label, 'Buy it now')]")))
    buy_now_option.click() 
    time.sleep(5)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    table = driver.find_element(By.TAG_NAME, "table")
    
    headers = table.find_elements(By.TAG_NAME, "th")
    column_names = [header.text.strip() for header in headers]
    
    rows = table.find_elements(By.TAG_NAME, "tr")
    new_data = []
    
    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 0:
                row_data = {}
                for idx, col in enumerate(cols):
                    row_data[column_names[idx]] = remove_special_characters(col.text.strip()) if idx < len(column_names) else ""
                new_data.append(row_data)
        
        except Exception as e:
            print(f"Error extracting data for a row: {e}")

    compare_and_update_data(existing_data, new_data, existing_filename)

finally:
    driver.quit()
