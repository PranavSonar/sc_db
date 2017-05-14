#!/usr/bin/env python
# Author  : Vikas Chouhan (presentisgood@gmail.com)
# License : GPLv2
#
# This script pulls data from screener.in using one of the user's screen or any
# other public screen & using screened companies to scan for techincal analysis.
# Right now it uses ema crossover but anything can be applied.
#
# The goal is to find out the right timings for entry in the stocks selected via
# a fundamental screener.
# Say for example you get a list of top 30 companies satisfying magic formula criteria
# (Joel Greenblatt), but still to maximize your returns you also want to apply some
# form of moving average crossover. This script is supposed to achieve things like
# that (Thus a sort of techno-fundamental screener).

import spynner
import json
import pprint
import sys
import re
import urllib, urllib2, json
import datetime
import pandas
import argparse
import copy
import time
import os
import math
import contextlib, warnings
import pprint

##################################################################
# INVESTING.COM FUNCTIONS
#

sock = "bcbf3d08f70aaf07b860dc2f481beee5/1473605026"
res_tbl = {
              "1m"     : 1,
              "5m"     : 5,
              "15m"    : 15,
              "30m"    : 30,
              "1h"     : 60,
              "1D"     : "D",
              "1W"     : "W",
              "1M"     : "M",
          }

def g_sock():
    urlt = g_burlb()
    with contextlib.closing(urllib2.urlopen(urlt)) as s:
        return '/'.join(re.search('carrier=(\w+)&time=(\d+)&', s.read()).groups())
    # endwith
    assert(False)
# enddef

def g_burlb():
    return "http://tvc4.forexpros.com"
def g_burl(soc_idf):
    return g_burlb() + "/{}/1/1/8/history?".format(soc_idf)

def strdate_to_unixdate(str_date):
    return int(time.mktime(datetime.datetime.strptime(str_date, '%d/%m/%Y').timetuple()))
# enddef

def unixdate_now():
    return int(time.mktime(datetime.datetime.now().timetuple()))
# enddef
def strdate_now():
    return datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
# enddef

# Fetch from investing.com
def fetch_data(ticker, resl, t_from=None):
    if t_from == None:
        t_from = strdate_to_unixdate("01/01/1992")
    # endif
    ftch_tout = 5
    t_indx    = 0

    assert(resl in res_tbl.keys())

    while t_indx < ftch_tout:
        t_to     = unixdate_now()
        this_url = g_burl(sock) + "symbol={}&resolution={}&from={}&to={}".format(ticker, res_tbl[resl], t_from, t_to)

        #print "{} : Fetching {}".format(strdate_now(), this_url)
        response = urllib.urlopen(this_url)
        j_data   = json.loads(response.read())
        if not bool(j_data):
            print "{} : Not able to fetch.".format(strdate_now())
        else:
            break
        # endif
        t_indx   = t_indx + 1
    # endwhile

    if (t_indx >= ftch_tout):
        #print "{} : Retries exceeded !!".format(strdate_now())
        # Exit
        sys.exit(-1)
    # endif

    # Get basic pb_frame
    def g_pdbase(j_data):
        x_alt_a  = range(0, len(j_data['c']))
        t_data   = [ datetime.datetime.fromtimestamp(int(x)) for x in j_data['t'] ]
        d_frame  = pandas.DataFrame(index=x_alt_a)
    
        d_frame['c'] = j_data['c']
        d_frame['o'] = j_data['o']
        d_frame['h'] = j_data['h']
        d_frame['l'] = j_data['l']
        d_frame['t'] = t_data
        d_frame['T'] = j_data['t']

        if 'v' in j_data:
            d_frame['v']  = j_data['v']
        # endif
        if 'vo' in j_data:
            d_frame['vo'] = j_data['vo']
        # endif
    
        return d_frame
    # enddef

    #print "{} : Fetched data. done !!".format(strdate_now())
    return g_pdbase(j_data)
# enddef

##############################################################
# SCREENER.IN functions

# @args
#     user      : screener.in username
#     passwd    : screener.in password
#     screen_no : screen no
def screener_pull_screener_results(user, passwd, screen_no=17942):
    def screener_screener_page(page_this, screen_no=screen_no):
        return 'https://www.screener.in/api/screens/{}/?page={}'.format(screen_no, curr_page)
    # enddef
    
    sec_list = []
    ratios_l = []
    sec_dict = {}
    url_this = 'https://www.screener.in/login/'
    browser  = spynner.Browser()
    browser.load(url_this)
    
    # Login to screener.in
    browser.wk_fill('input[name=username]', user)
    browser.wk_fill('input[name=password]', passwd)
    browser.wk_click('button[type=submit]', wait_load=True)
    
    # Pull data
    curr_page = 1
    while True:
        sys.stdout.write('\r>> Querying page {:03}'.format(curr_page))
        sys.stdout.flush()
        sdict_this = json.loads(browser.download(screener_screener_page(curr_page)))
        n_pages    = sdict_this['page']['total']
        ratios_l   = sdict_this['page']['ratios']
        sec_list   = sec_list + sdict_this['page']['results']
    
        # Increment
        curr_page = curr_page + 1
    
        # Check
        if curr_page > n_pages:
            break
        # endif
    # endwhile
    
    sec_dict = {
                   "results" : sec_list,
                   "ratios"  : ratios_l,
               }
    
    sys.stdout.write("\nDone !!\n")
    sys.stdout.flush()
    return sec_dict
# endif

def get_sec_name_list(sec_dict):
    sec_list = sec_dict["results"]
    sec_list = [ re.search(r'/company/([\d\w\-]+)/*', x[0]).groups()[0] for x in sec_list]
    return sec_list
# enddef

def screener_dot_in_pull_screener_codes(user, passwd, screen_no=17942):
    sec_dict = screener_pull_screener_results(user, passwd, screen_no)
    return get_sec_name_list(sec_dict)
# enddef

################################################
# GENERIC

# Function to parse checkpoint file
def parse_dict_file(file_name=None):
    if file_name == None:
        return {}
    else:
        return eval(open(file_name, 'r').read())
    # endif
# endif

def populate_sym_list(invs_dict_file, sec_list):
    # Convert inv_dot_com_db_list to dict:
    inv_dot_com_db_dict = parse_dict_file(invs_dict_file)
    # Generate nse dict
    nse_dict = {}
    for item_this in inv_dot_com_db_dict.values():
        if u'nse_code' in item_this and item_this[u'nse_code']:
            nse_dict[item_this[u'nse_code']] = item_this
        # endif
    # endfor
    # Generate bse dict
    bse_dict = {}
    for item_this in inv_dot_com_db_dict.values():
        if u'bse_code' in item_this and item_this[u'bse_code']:
            bse_dict[item_this[u'bse_code']] = item_this
        # endif
    # endfor

    # code list
    nse_keys = nse_dict.keys()
    bse_keys = [unicode(x) for x in bse_dict.keys()]

    # Search for tickers
    sec_dict = {}
    not_f_l  = []
    for sec_this in sec_list:
        # Search
        if sec_this in nse_keys:
            sec_dict[sec_this] = nse_dict[sec_this][u'ticker']
        elif sec_this in bse_keys:
            sec_dict[sec_this] = bse_dict[sec_this][u'ticker']
        else:
            not_f_l.append(sec_this)
        # endif
    # endfor
    print '{} not found in investing.com db'.format(not_f_l)

    return sec_dict
# enddef

####################################################
# SCANNERS
#
# Get mean generating f
def g_rmean_f(**kwargs):
    se_st = kwargs.get('type', 's')    # "s" or "e"
    if se_st == 's':
        return lambda s, t: pandas.rolling_mean(s, t)
    elif se_st == 'e':
        return lambda s, t: pandas.Series.ewm(s, span=t, adjust=False).mean()
    else:
        assert(False)
    # endif
# enddef

# EMA

def s_mode(f_frame, mode='c'):
    m_list = ['o', 'c', 'h', 'l', 'hl2', 'hlc3', 'ohlc4']
    if not mode in m_list:
        print "mode should be one of {}".format(m_list)
        sys.exit(-1)
    # endif

    if mode == 'o':
        return f_frame['o']
    elif mode == 'c':
        return f_frame['c']
    elif mode == 'h':
        return f_frame['h']
    elif mode == 'l':
        return f_frame['l']
    elif mode == 'hl2':
        return (f_frame['h'] + f_frame['l'])/2.0
    elif mode == 'hlc3':
        return (f_frame['h'] + f_frame['l'] + f_frame['c'])/3.0
    elif mode == 'ohlc4':
        return (f_frame['o'] + f_frame['h'] + f_frame['l'] + f_frame['c'])/4.0
    else:
        assert(False)
    # endif
# enddef

def v_i(s, indx):
    return s.values[indx]
# enddef

# Comparator functions
def c_f_0(ma_p0, ma_p1, ma_p2, lag=30):
    if ma_p0.shape[0] <= lag or ma_p1.shape[0] <= lag or ma_p2.shape[0] <= lag:
        return False
    # endif
    if (v_i(ma_p0, -1) >= v_i(ma_p1, -1) >= v_i(ma_p2, -1)) and \
            (v_i(ma_p0, -1-lag) <= v_i(ma_p1, -1-lag) <= v_i(ma_p2, -1-lag)):
        return True
    # endif
    return False
# endif
def c_f_1(ma_p0, ma_p1, lag=30):
    if ma_p0.shape[0] <= lag or ma_p1.shape[0] <= lag:
        return False
    # endif
    if (v_i(ma_p0, -1) >= v_i(ma_p1, -1)) and \
            (v_i(ma_p0, -1-lag) <= v_i(ma_p1, -1-lag)):
        return True
    # endif
    return False
# endif

# Strategy
def run_ema(o_frame, mode='c', lag=30):
    d_s     = s_mode(o_frame, mode)
    rmean   = g_rmean_f(type='e')

    ## Get values
    ma_p0   = rmean(d_s, 14)
    ma_p1   = rmean(d_s, 21)
    #ma_p2   = rmean(d_s, 21)

    return c_f_1(ma_p0, ma_p1, lag=lag)
# enddef

#########################################################
# Main

if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument("--auth", help="Screener.in authentication in form user:passwd", type=str, default=None)
    parser.add_argument("--invs", help="Investing.com database file (populated by eq_scan_on_investing_dot_com.py)", type=str, default=None)
    args    = parser.parse_args()

    if not args.__dict__["auth"]:
        print "--auth is required !!"
        sys.exit(-1)
    # endif
    if not args.__dict__["invs"]:
        print "--invs is required !!"
        sys.exit(-1)
    # endif

    # Vars
    auth_info  = args.__dict__["auth"].replace(' ', '').split(',')
    invs_db_f  = os.path.expanduser(args.__dict__["invs"])

    # Get security list from screener.in using default screen_no=17942
    sec_list   = screener_dot_in_pull_screener_codes(auth_info[0], auth_info[1], screen_no=17942)
    print 'Found {} securities from Screener.in matching criteria.'.format(len(sec_list))
    sec_tick_d = populate_sym_list(invs_db_f, sec_list)

    #pprint.pprint(sec_tick_d)
    # Start scan
    #sec_list   = []
    for sec_code in sec_tick_d.keys():
        #sys.stdout.write('.')
        #sys.stdout.flush()
        d_this = fetch_data(sec_tick_d[sec_code], '1W')
        status = run_ema(d_this, lag=12)
        if (status==True):
            sys.stdout.write('{}, '.format(sec_code))
            sys.stdout.flush()
            #sec_list.append(sec_code)
        # endif
    # endfor

    # Newline
    sys.stdout.write('None\n')
    sys.stdout.flush()

    # Print scan results
    #if len(sec_list) > 0:
    #    print 'Passed criteria : {}'.format(sec_list)
    ## endif
# endif