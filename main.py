import configparser
import getpass
import pykeepass

import time
import requests
import lxml.etree as etree
import hashlib
import logging

import smtplib
import email


def load_config(path='config.txt'):
    config = configparser.ConfigParser()
    config.read(path)

    keepass = config['keepass']
    smtp = config['smtp']
    monitor = config['monitor']

    return keepass, smtp, monitor


def load_keepass_database(path):
    master_pw = getpass.getpass(prompt='What is the Keepass database master password? ')
    return pykeepass.PyKeePass(path, password=master_pw)


def get_smtp_credentials_from_db(keepass_db, entry_path):
    credentials = keepass_db.find_entries(path=entry_path.split('/'), first=True)

    if not credentials:
        raise ValueError(f'Could not find credentials in loaded Keepass database')

    return {
        'username': credentials.username,
        'password': credentials.password
    }


def send_email(smtp_server, smtp_user, subject, msg):
    server = smtplib.SMTP(smtp_server['url'], smtp_server['port'])
    server.starttls()
    server.login(smtp_user['username'], smtp_user['password'])

    email_msg = email.message.EmailMessage()
    email_msg.set_content(msg)
    email_msg['Subject'] = subject
    email_msg['From'] = smtp_user['username']
    email_msg['To'] = smtp_user['username']

    server.send_message(email_msg)
    server.quit()


def monitor_webpage_section(url, xpath, interval, alert_func):
    print(f'Setting up webpage monitor with a {interval}-second interval.\nURL: {url}\nXPath: {xpath}\n---')
    current_md5 = None

    while True:
        response = requests.get(url)

        doc_tree = etree.HTML(response.text)
        page_section = doc_tree.xpath(xpath)[0]
        page_title = doc_tree.xpath('//title/text()')[0]

        new_md5 = hashlib.md5(etree.tostring(page_section)).hexdigest()

        if current_md5 and new_md5 != current_md5:
            alert_func(
                f'{page_title} --- Page updated',
                f'The monitored page section at the following URL has been updated:\n{url}')
            print(f'{time.ctime()} - Webpage has been updated - MD5: {new_md5}')
        else:
            print(f'{time.ctime()} - No changes detected - MD5: {new_md5}')

        current_md5 = new_md5
        time.sleep(interval)


if __name__ == '__main__':
    keepass, smtp_server, monitor = load_config()
    keepass_db = load_keepass_database(keepass['db_path'])
    smtp_user = get_smtp_credentials_from_db(keepass_db, keepass['entry_path'])

    alert_func = lambda title, message: send_email(smtp_server, smtp_user, title, message)

    monitor_webpage_section(monitor["url"], monitor["xpath"], int(monitor["interval"]), alert_func)

