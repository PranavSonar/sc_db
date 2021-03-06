# Author  : Vikas Chouhan
# License : GPLv2

import os, sys
import time
import argparse
import datetime
import shutil
from selenium import webdriver

def download_sharekhan_dp_statement(login_id, br_passwd, tr_passwd, file_name='~/sharekhan_mydp.xls', gen_report=True, brshow=True, timeout=60):
    login_url = 'https://newtrade.sharekhan.com/rmmweb/login/OldLoginPage.jsp'
    dmat_url  = 'https://newtrade.sharekhan.com/rmmweb/statements/excel/eq_dpsr_report.jsp?balance=-1'
    dmat_lurl = 'https://newtrade.sharekhan.com/rcs.sk?execute=dynamicreport&pType=905'
    down_dir  = '/tmp/chrome-downloads'

    options = webdriver.ChromeOptions()
    if not brshow:
        options.add_argument('headless')
    # endif
    options.add_experimental_option("prefs", {
        "download.default_directory"       : down_dir,
        "download.prompt_for_download"     : False,
        "download.directory_upgrade"       : True,
    })
    driver = webdriver.Chrome(chrome_options=options)

    # Create dir
    try:
        os.makedirs(down_dir)
    except:
        shutil.rmtree(down_dir)
        os.makedirs(down_dir)
    # endtry

    driver.get(login_url)
    driver.find_element_by_id('loginid').send_keys(login_id)
    driver.find_element_by_id('pwSignup').send_keys(br_passwd)
    driver.find_element_by_id('pwSignup1').send_keys(tr_passwd)
    driver.find_element_by_name('Login').click()
    driver.get(dmat_lurl)
    driver.get(dmat_url)
    time.sleep(2)

    # Filename
    bin_file = '{}/dpsr_report.xls'.format(down_dir)

    # Check if file was downloaded
    if not os.path.isfile(bin_file):
        print '{} does not exist !!. Download failed.'.format(bin_file)
        sys.exit(-1)
    # endif

    if gen_report:
        with open(os.path.expanduser(file_name), 'w') as f_out:
            f_out.write(open(bin_file, 'rb').read())
        # endwith
        return 'Report downloaded to {} !!'.format(file_name)
    else:
        # Get header and rows fro xls data
        # TODO
        from bs4 import BeautifulSoup
        soup_t = BeautifulSoup(open(bin_file, 'rb').read(), 'lxml')
        table_t = soup_t.find('table', {'border':1})
        row_l = table_t.find_all('tr')
        # Pop last row as it's some useless information
        row_l.pop(-1)
        # Pop header
        header_r = row_l.pop(0)
        header_l = [x.text for x in header_r.find_all('td')]
        # Extract rows
        scrip_l = []
        for r_t in row_l:
           scrip_l.append([x.text.replace('\t', '').replace('\r', '').replace('\n', '') for x in r_t.find_all('td')])
        # endfor

        # Remove dir
        shutil.rmtree(down_dir)

        return scrip_l, header_l
    # endif
# enddef

if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument('--auth',     help='Sharekhan Authentication (loginid,brpwd,trpwd)', type=str, default=None)
    parser.add_argument('--filename', help='Target filename', type=str, default=None)
    parser.add_argument('--genrep',   help='Generate Report', action='store_true')
    parser.add_argument('--brshow',   help='Browser show', action='store_true')
    parser.add_argument('--timeout',  help='Page load timeout', type=int, default=60)
    args    = parser.parse_args()

    if not args.__dict__['auth']:
        print '--auth is required !!'
        sys.exit(-1)
    # endif
    if not args.__dict__['filename']:
        file_name = '~/sharekhan_mydp_statement_{}.xls'.format(str(datetime.datetime.now()))
    else:
        file_name = args.__dict__['filename']
    # endif

    auth_l = args.__dict__['auth'].replace(' ', '').split(',')
    if len(auth_l) != 3:
        print '--auth should be in format "loginid,brpwd,trpwd"'
        sys.exit(-1)
    # endif

    # NOTE: There is a bug in chrome, wherein downloads are disabled in headless mode !!
    #brshow = args.__dict__['brshow']
    brshow = True

    # Download
    print download_sharekhan_dp_statement(auth_l[0], auth_l[1], auth_l[2], \
              file_name, args.__dict__['genrep'], brshow, args.__dict__['timeout'])
# endif
