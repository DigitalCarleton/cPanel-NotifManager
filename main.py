import json
import csv
import os
import time
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime

TIMEOUT = 5 #seconds
SLEEP = 0.3 #seconds

class Csv_Handler:
    def __init__(self, directory: str, file_name: str):
        self.directory = directory
        self.file_name = file_name

    def make_dir(self):
        # Make a directory for the csv file
        os.mkdir(self.directory)
    
    def write_to_csv(self, row_content: map):
        # If a directory for the csv file does not yet exist, make one
        if not os.path.exists(self.directory):
            self.make_dir()

        # Write the row contents to the CSV
        with open(f"{self.directory}/{self.file_name}.csv", 'a') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(row_content)


class Notifications:
    notif_status = []
    notif_config = []

    # Config selenium elements
    clone_error = None
    backup_error = None
    restore_error = None
    sync_complete = None
    sync_error = None
    update_available = None
    update_complete = None
    update_error = None
    add_on_update_complete = None
    add_on_update_error = None

    def __init__(self, notification_manager_href:str, driver:webdriver, wait:WebDriverWait):
        self.notification_manager_href = notification_manager_href
        self.driver = driver
        self.wait = wait

    def get_custom_notifications_config(self):
        # Open whmcs notification JSON for notification specification
        f = open('whmcs_notif_config.json',)
        data = json.load(f)
        f.close()

        return data["notifications"];

    def get_notification_status_all(self):
        # Deconstruct driver
        driver = self.driver

        self.notif_config = self.get_custom_notifications_config()

        self.clone_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_clone_error")
        self.backup_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_backup_error")
        self.restore_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_restore_error")
        self.sync_complete = driver.find_element(By.CSS_SELECTOR, "#field_nc_sync")
        self.sync_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_sync_error")
        self.update_available = driver.find_element(By.CSS_SELECTOR, "#field_nc_update_available")
        self.update_complete = driver.find_element(By.CSS_SELECTOR, "#field_nc_update")
        self.update_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_update_error")
        self.add_on_update_complete = driver.find_element(By.CSS_SELECTOR, "#field_nc_plugin_update")
        self.add_on_update_error = driver.find_element(By.CSS_SELECTOR, "#field_nc_plugin_update_error")

    def set_custom_notification_status_all(self) -> list:
        # Deconstruct driver and wait
        driver, wait = self.driver, self.wait

        # Get all (up to date) custom notifications & configurations first
        self.get_notification_status_all()
        
        # Set custom notifications based on JSON file configurations
        for key in self.notif_config:
            key_element = getattr(self, key)

            if self.notif_config[key] and not key_element.is_selected(): key_element.click()
            elif not self.notif_config[key] and key_element.is_selected(): key_element.click()

        # Clear old notif status & store new notif statuses
        self.notif_status = []

        for key in self.notif_config:
            key_element = getattr(self, key)

            if key_element.is_selected(): self.notif_status.append(key + ": Selected")
            else: self.notif_status.append(key + ": Deselected")

        def save_changes():
            # Wait a split second & click the "Save All" element
            time.sleep(SLEEP)
            driver.find_element(By.CSS_SELECTOR, "#i_button_next").click()

            try:
                # Wait for the changes to be fully saved (i.e. the redirect tab to load)
                wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-descr='View/edit details']")))
            except:
                print("Error when saving. Trying again...\n")
                save_changes()

        save_changes()

    def customize_notifications(self):
        # Deconstruct driver and wait
        driver, wait = self.driver, self.wait

        driver.get(self.notification_manager_href)

        # Set notification mode to manual
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#field_notification_mode_manual")))
        driver.find_element(By.CSS_SELECTOR, "#field_notification_mode_manual").click()

        # Set email notifications status (True/False)
        self.set_custom_notification_status_all()


class UserProfile:
    name:str = None
    whmcs_href:str = None
    notif_status_list:list = []


def main():
    # Ask user for their WHMCS Credentials
    print("\nScript Requires WHMCS Credentials:")
    username = input('Username: ')
    password = password = getpass("Password: ")

    # Initialize driver, and open WHMCS login page
    driver = webdriver.Chrome()
    driver.get("https://sites.carleton.edu/manage/whmcs-admin/login.php")
    driver.maximize_window()

    # Wait Instance
    wait = WebDriverWait(driver, TIMEOUT)

    # Login to WHMCS
    try:
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)

        # Login using user input
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        print("Logging in...")
    except:
        print("\nFailed to load login page. \nExiting Script...")
        exit(1)

    # Navigate to the products & services page
    driver.get("https://sites.carleton.edu/manage/whmcs-admin/index.php?rp=/whmcs-admin/services")

    # Check to see if user is logged in, and exit if not
    try:
        driver.find_element(By.CSS_SELECTOR, "#sortabletbl0 tr td:nth-child(2) a")
    except:
        print("\nFailed to login, possibly incorrect credentials. \nExiting Script...")
        exit(1)

    # Create CSV Handler Instance, Directory, and row header
    datef = datetime.now().strftime("%m-%d-%y %H.%M.%S")
    csv_handler = Csv_Handler("WHMCS_Users", "log_file " + datef)
    csv_handler.write_to_csv(["user", "whmcs_href", "notif_status"])

    # Get all users in all pages
    nextPage = True
    currPage = 1
    all_user_hrefs = []

    # Paginate through all the WHMCS pages and collect all the user_hrefs
    while nextPage:
        # Print current page & sleep for a bit to avoid rate limiting
        print("Currently on page: ", currPage)
        time.sleep(SLEEP)

        try:
            # Get all user hrefs in page & append to all_user_hrefs
            links = driver.find_elements(By.CSS_SELECTOR, "#sortabletbl0 tr td:nth-child(2) a")
            user_hrefs = [link.get_attribute("href") for link in links]
            all_user_hrefs += user_hrefs

            # Traverse to next page
            driver.find_element(By.PARTIAL_LINK_TEXT, "Next Page").click()
            currPage += 1
        except:
            # Stop Pagination, Print
            print("No more pagination buttons found")
            nextPage = False
            pass

    # Iterate through all user hrefs and customize their notifications
    for user_href in all_user_hrefs:
        # Define a function to SSO cPanel and manage notifications
        def cPanel_SSO():
            # Create a user profile, and update the WHMCS user_href
            userProfile = UserProfile()
            userProfile.whmcs_href = user_href
            print("User WHMCS href: ", user_href)

            # Open the user's page
            driver.get(user_href)

            try:
                # wait for the cPanel button to load
                cpanel_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@onclick=\"runModuleCommand('singlesignon'); return false\"]")))
            except:
                pass

            cpanel_button.click()

            # Get user name & create a userProfile
            user_name_el = driver.find_element(By.CSS_SELECTOR, ".name")
            user_name = user_name_el.get_attribute('innerHTML')
            userProfile.name = user_name

            # Switch to cPanel tab & wait for it to load
            wait.until(EC.new_window_is_opened(driver.window_handles))
            driver.switch_to.window(driver.window_handles[1])
            wait.until(EC.url_contains("https://carleton.reclaimhosting.com"))

            # Redirect to the my_apps webpage
            my_apps_anchor = driver.find_element(By.CSS_SELECTOR, "#item_myapps")
            user_apps_href = my_apps_anchor.get_attribute('href')
            driver.get(user_apps_href)

            # Redirect to the notifications center
            # Wait for description of my_apps to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".i_page_description.i_bg_page_description")))
            user_contains_apps = True

            try:
                # try to wait for the edit details button of apps to load
                wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-descr='View/edit details']")))
            except:
                print("There are no apps for this user")
                user_contains_apps = False

            #  Create an array to store user_notification status
            userProfile.notif_status_list = []

            if user_contains_apps:
                # Get all the app hrefs and add them to an iterable array
                edit_anchor = driver.find_elements(By.XPATH, "//a[@data-descr='View/edit details']")
                edit_anchor_hrefs = [elem.get_attribute('href') for elem in edit_anchor]

                # Customize user notifications for each app in the users cPanel, and return when done
                for edit_anchor_href in edit_anchor_hrefs:
                    # Create a Notifications object for user
                    user_notifs = Notifications(edit_anchor_href, driver, wait)
                    user_notifs.customize_notifications()

                    # Update userProfile with user_notifs status
                    userProfile.notif_status_list.append(user_notifs.notif_status)

            # Close user cPanel tab and switch back to the first tab
            time.sleep(SLEEP)
            driver.close()
            time.sleep(SLEEP)
            driver.switch_to.window(driver.window_handles[0])

            # Return the userProfile for csvHandler
            return userProfile
        
        # Use the cPanel_SSO() function to sign in and manage notifications
        def complete_user_info():
            try:
                userProfile = cPanel_SSO()

                # Update spreadsheet with userProfile and Notifs
                user_notif_status = userProfile.notif_status_list
                user_notif_status.insert(0, userProfile.whmcs_href)
                user_notif_status.insert(0, userProfile.name)
                csv_handler.write_to_csv(user_notif_status)

            except:
                print("Failed to get user information. Trying again...\n")
                # Close user cPanel tab and switch back to the first tab
                time.sleep(SLEEP)
                driver.close()
                time.sleep(SLEEP)
                driver.switch_to.window(driver.window_handles[0])
                
                # Run again
                complete_user_info()

        complete_user_info()

    # On Successful completion, exit script & close > quit driver instance
    print("End of Script. Exiting...")

    driver.close()
    driver.quit()

if __name__ == '__main__':
    main()