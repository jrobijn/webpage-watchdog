import dotenv
import os
import configparser

import time
import requests
import lxml.etree as etree
import hashlib

import telebot 


def load_config(path='config.txt'):
    config = configparser.ConfigParser()
    config.read(path)

    monitor = config['monitor']

    return monitor['url'], monitor['xpath'], int(monitor['interval'])


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
    url, xpath, interval = load_config()

    dotenv.load_dotenv()
    bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
    chat_id = int(os.getenv('CHAT_ID'))

    # Telegram doesn't support message titles
    alert_func = lambda title, message: bot.send_message(chat_id, message)

    monitor_webpage_section(url, xpath, interval, alert_func)