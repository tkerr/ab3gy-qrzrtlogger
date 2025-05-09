###############################################################################
# qrzrtlogger.py
# Author: Tom Kerr AB3GY
#
# Perform real-time QSO logging to QRZ.com from supported applications.
# Use of this class requires at least a QRZ.com XML logbook data subscription.
#
# QRZ.COM website: https://www.qrz.com/
#
# Designed for personal use by the author, but available to anyone under the
# license terms below.
###############################################################################

###############################################################################
# License
# Copyright (c) 2025 Tom Kerr AB3GY (ab3gy@arrl.net).
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,   
# this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,  
# this list of conditions and the following disclaimer in the documentation 
# and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without 
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
###############################################################################

# System level packages.
from datetime import datetime
import getopt
import os
import queue
import re
import sys
import threading
import time
import yaml

# Local packages.
import _env_init
from n1mmmon import n1mmmon
from qrzupload import qrzupload
from strutils import make_utf8
from wsjtxmon import wsjtxmon

##############################################################################
# Global objects and data.
##############################################################################
scriptname = os.path.basename(sys.argv[0])
adif_eoh_re = re.compile("\<EOH\>", re.IGNORECASE)
n1mm_monitor = None
n1mm_running = False
wsjtx_monitor = None
wsjtx_running = False
qso_queue = queue.Queue(maxsize=20)


##############################################################################
# Functions.
##############################################################################

#------------------------------------------------------------------------------
def print_usage():
    """
    Print a usage statement and exit.
    """
    global scriptname
    print('Usage: {} [-dhv] <yml_file>'.format(scriptname))
    print('Perform real-time QSO logging to QRZ.com from supported applications.')
    print('<yml_file> is a YAML configuration file.')
    print('Options:')
    print('  -d = Dryrun only, do lot log the QSO (used for test and debug)')
    print('  -h = Print this message and exit')
    print('  -v = Print verbose debug messages')
    sys.exit(1)

#------------------------------------------------------------------------------
def print_time(msg):
    """
    Print a message with a timestamp.
    """
    now = datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    print('{} {}'.format(ts, msg))

#------------------------------------------------------------------------------
def format_record(adif_in):
    """
    Format an incoming ADIF record suitable for logging.
    """
    global adif_eoh_re
    rec = make_utf8(adif_in).replace('\n', ' ').replace('\r', ' ')
    m = adif_eoh_re.search(rec)
    if m:
        idx = m.end()
        rec = rec[idx:]
    adif_out = rec.strip()
    return adif_out

#------------------------------------------------------------------------------
def n1mm_thread():
    """
    Run the N1MM+ real-time logger thread.
    """
    global n1mm_monitor
    global n1mm_running
    global qso_queue
    print_time('N1MM+ logging thread starting.')
    while n1mm_running:
        if n1mm_monitor.get_message():
            if (n1mm_monitor.message != 'timeout'):
                if qso_queue.full():
                    print_time('Queue full, N1MM+ QSO not queued.')
                else:
                    qso_queue.put(n1mm_monitor.message, block=False)
                    print_time('N1MM+ QSO queued')
        else:
            n1mm_running = False
    print_time('N1MM+ logging thread exiting.')

#------------------------------------------------------------------------------
def wsjtx_thread():
    """
    Run the WSJT-X real-time logger thread.
    """
    global wsjtx_monitor
    global wsjtx_running
    global qso_queue
    print_time('WSJT-X logging thread starting.')
    while wsjtx_running:
        if wsjtx_monitor.get_message():
            if (wsjtx_monitor.Message[0] == wsjtx_monitor.MSG_ADIF_LOGGED):
                #print(wsjtx_monitor.Message)
                qso = format_record(wsjtx_monitor.Message[2])
                if qso_queue.full():
                    print_time('Queue full, WSJT-X QSO not queued.')
                else:
                    qso_queue.put(qso, block=False)
                    print_time('WSJT-X QSO queued')
        else:
            wsjtx_running = False
    print_time('WSJT-X logging thread exiting.')


###############################################################################
# Main program.
###############################################################################
if __name__ == "__main__":
    
    dryrun = False
    verbose = False
    
    # Get command line options.
    # See print_usage() for details.
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'dhv')
    except (getopt.GetoptError) as err:
        print(str(err))
        print_usage()
        
    for (o, a) in opts:
        if (o == '-d'):
            dryrun = True
            print('Dryrun mode, no QSOs will be logged')
        elif (o == '-h'):
            print_usage()
        elif (o == '-v'):
            verbose = True
    
    # Load the YAML configuration file.
    if (len(args) < 1):
        print('No YAML configuration file specified.')
        print_usage()
    yaml_file = args[0]
    with open(yaml_file, 'r') as yf:
        config = yaml.safe_load(yf)
    
    # QRZ setup.
    qrz_config = config['qrz']
    qrz_logger = qrzupload(qrz_config['call'], qrz_config['api_key'], verbose)
    
    # WSJT-X listener thread setup.
    if 'wsjtx' in config.keys():
        wsjtx_config = config['wsjtx']
        wsjtx_monitor = wsjtxmon(verbose)
        (status, err_msg) = wsjtx_monitor.bind(wsjtx_config['ip'], wsjtx_config['port'], wsjtx_config['timeout'])
        if not status:
            print('WSJT-X bind error: {}'.format(err_msg))
            sys.exit(1)
        wsjtx_running = True
        wsjtxThread = threading.Thread(target=wsjtx_thread)
        wsjtxThread.start()
    
    # N1MM+ listener thread setup.
    if 'n1mm' in config.keys():
        n1mm_config = config['n1mm']
        n1mm_monitor = n1mmmon(verbose)
        (status, err_msg) = n1mm_monitor.bind(n1mm_config['ip'], n1mm_config['port'], n1mm_config['timeout'])
        if not status:
            print('N1MM+ bind error: {}'.format(err_msg))
            sys.exit(1)
        n1mm_running = True
        n1mmThread = threading.Thread(target=n1mm_thread)
        n1mmThread.start()
    
    print_time('Monitoring UDP ports for QSO messages.')
    try:
        while True:
            if qso_queue.empty():
                time.sleep(5)
            else:
                qso = qso_queue.get(block=False)
                if dryrun:
                    print_time('Dryrun mode, QSO not logged')
                    print(qso)
                else:
                    (upload_count, status, info) = qrz_logger.upload(qso)
                    if (upload_count == 1):
                        print_time('QSO logged')
                    else:
                        print_time('QSO NOT logged: {}'.format(info))
    except KeyboardInterrupt:
        print_time('Keyboard interrupt')
    except Exception as e:
        print_time('Exception: {}'.format(str(e)))
    n1mm_running = False
    wsjtx_running = False
    print_time('Waiting for threads to exit.')
    n1mmThread.join()
    wsjtxThread.join()
    print_time('{} exiting.'.format(scriptname))
    