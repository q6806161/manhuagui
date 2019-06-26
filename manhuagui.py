#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:Lvcong Chen
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from multiprocessing import Process, Queue
import requests
import urllib3
import socket
import time
import random
import imp
import re
import sys
import os
import winsound
imp.reload(sys)
requests.packages.urllib3.disable_warnings()

class One_Punch_Man_Spider(object):
    
    
    def __init__(self):
        
        self.pattern_maxpage =  re.compile(r"""(
        <h2>(.*?)</h2>
        .*?<span\s+id=['|"]page['|"]>\d+</span>\W+(\d+)
        )""",re.VERBOSE|re.S)
        self.pattern_picture_download_url = re.compile(r"""(
        (id=['|"]mangaFile['|"]\s+src=['|"](.*?)['|"])                     # 图片下载地址提取
        )""",re.VERBOSE|re.S)
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Wi\
			n64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.\
			0.3729.108 Safari/537.36'}
        self.s = requests.Session()
        self.url_charpter_first_page_first = "https://www.manhuagui.com/comic/9637/438862.html"
    
    # 
    def chrome_set(self):
        """chorm的selenium设置"""
        chrome_options=Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        # chrome_options.add_argument('--headless')
        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"
        driver = webdriver.Chrome(desired_capabilities=capa, options=chrome_options)
        wait = WebDriverWait(driver,7)
        return (driver,wait)


    # 图片下载地址模块
    def picture_url_crawler(self,maxpage,driver,wait):
        page_turn = 1
        picture_url_list = []
        check_time = 0
        while page_turn <= int(maxpage) and check_time<=3:
            try:
                wait.until(EC.presence_of_element_located((By.ID,"mangaFile")))
                html_text = driver.page_source
                items = re.findall(self.pattern_picture_download_url,html_text)
                picture_url = re.sub(';','&',re.sub('&amp', '', items[0][-1]))
                picture_url_list.append(picture_url)
                page_next = wait.until(EC.element_to_be_clickable((By.ID,"next"))) # 点击下一页
                driver.execute_script("arguments[0].click();", page_next)
                time.sleep(random.uniform(1,3))
                page_turn += 1
            except TimeoutException as e:
                driver.refresh()
                check_time +=1
                self.alarm_sound(e)
                continue
        if check_time ==3:
            sys.exit()
        return picture_url_list


    # 警报音模块
    def alarm_sound(self,e):
        winsound.Beep(200, 3000)
        print("元素不存在",e)

    
    """获取每话首页渲染后的html"""
    def picture_url_list(self,q):
        driver,wait = self.chrome_set()
        try:
            driver.get(self.url_charpter_first_page_first)
            wait.until(EC.presence_of_element_located((By.ID,"tbBox")))
            driver.execute_script('window.stop()')
            end_flag = 1
            check_time = 0
        except TimeoutException as e:
            self.alarm_sound(e)
        else:
            while end_flag!=0 and check_time<=3:
                try:
                    url_now = driver.current_url
                    wait.until(EC.presence_of_element_located((By.ID,"mangaFile")))
                    html_text_maxpage = driver.page_source
                    maxpage = re.findall(self.pattern_maxpage,html_text_maxpage)[0][-1]
                    charpter = re.findall(self.pattern_maxpage,html_text_maxpage)[0][1]
                    referer = re.sub(r"#[p]{1}=\d+",'',driver.current_url)
                    if "卷" not in charpter:
                        print(f"{charpter}最大页数—{maxpage}")
                        picture_url_list = self.picture_url_crawler(maxpage,driver,wait)
                        time.sleep(2)
                        charpter_next = wait.until(EC.presence_of_element_located((By.CLASS_NAME,"nextC")))
                        driver.execute_script("arguments[0].click();", charpter_next) # 防止按键遮挡
                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME,"tip-alert")))
                            end_flag = 0
                            print("全部爬取完毕，congratulations！")
                        except NoSuchElementException:
                            pass
                    while True:
                        if q.empty():
                            q.put((referer,charpter,picture_url_list,end_flag))
                            break
                        time.sleep(1)
                except TimeoutException:
                    check_time += 1
                    driver.refresh()
                    continue


    """下载图片，并保存到文件夹中"""
    def picture_download(self,q):
        while True:
            charpter_url_list_endflag = q.get(True)
            picture_url_list = charpter_url_list_endflag[2]
            charpter = charpter_url_list_endflag[1]
            endflag = charpter_url_list_endflag[-1]
            referer = charpter_url_list_endflag[0]
            headers = {
            "Referer":referer,
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Wi\
                n64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.\
                0.3729.108 Safari/537.36'}
            page = 1
            print(f"正在下载{charpter}")
            for picture_url in picture_url_list:
                reload_time = 0
                while page <= len(picture_url_list) and reload_time <= 5:
                    try:
                        response = self.s.get(picture_url,headers=headers,timeout=5,verify=False)
                        os.makedirs(f"E:\黑色四叶操\{charpter}")
                        with open(f"E:\黑色四叶操\{charpter}\{page}.jpg","wb") as f:
                            writer = f.write(response.content)
                        break
                    except (requests.exceptions.ConnectionError,socket.timeout,urllib3.exceptions.ReadTimeoutError):
                        print("图片下载失败",e)
                        time.sleep(2)
                        reload_time += 1
                        continue
                    except FileExistsError:
                        with open(f"E:\黑色四叶操\{charpter}\{page}.jpg","wb") as f:
                            writer = f.write(response.content)
                        break
                page += 1
            if endflag ==0:
                return
        
if __name__=="__main__":
    q = Queue()
    one_punch_man_cartoon_downloader = One_Punch_Man_Spider()
    picture_url_writer = Process(target=one_punch_man_cartoon_downloader.picture_url_list,args=(q,))
    picture_save = Process(target=one_punch_man_cartoon_downloader.picture_download,args=(q,))
    picture_url_writer.start()
    picture_save.start()
    #等待proc_write1结束
    picture_url_writer.join()
    picture_save.join()
    #picture_save进程是死循环，强制结束
    # picture_save.terminate()
    os.system(r'E:\KuGou\1.mp3')

