# AB3GY QRZ Real-Time Logger
A Python application to perform real-time QSO logging to QRZ.com from supported applications.
Developed for personal use by the author, but available to anyone under the license terms below.  

Receives QSO records over a UDP network connection from supported applications and uploads them to a QRZ.com logbook.  

A QRZ.com subscription is required to use this application.

## Currently Supported Applications
* N1MM+ Logger
* WSJT-X 

## Dependencies
Written for Python 3.10+.

Requires the following packages from the ab3gy-pyutils repository:
* n1mmmon
* qrzupload
* strutils

Requires the following packages from the ab3gy-wsjtx repository:
* wsjtxmon

Copy these files to a local directory (or your current directory) and edit the `LOCAL_PACKAGE_PATH` variable in `_env_init.py` to point to them.  This is my non-pythonic but convenient way to pull local packages into my applications.

## Usage  
Copy the example YAML configuration file to `qrzrtlogger.yml` and edit it to match your configuration.  You will need your logbook callsign and QRZ.com API key.  See https://www.qrz.com/docs/logbook30/api  

For N1MM+ logger integration, edit the `n1mm` section IP address and port to match your contact broadcasting values.  See https://n1mmwp.hamdocs.com/appendices/external-udp-broadcasts/  

For WSJT-X integration, edit the `wsjtx` section IP address and port to match your Reporting UDP server fields. See https://wsjt.sourceforge.io/wsjtx-doc/wsjtx-main-2.6.1.html#REPORTING  

Run the application interactively in a console or terminal window, for example:  
`python -i qrzrtlogger.py qrzrtlogger.yml`  
The application will wait for logged QSO UDP messages over the specified ports and will format them and send them to QRZ.com.

The application starts multiple threads that run continuously.  To gracefully stop the threads and exit the application, type `stop()` in the console window and wait for the threads to exit. Exit Python by typing `quit()`.

## Author
Tom Kerr AB3GY
ab3gy@arrl.net

## License
Released under the 3-clause BSD license.
See license.txt for details.
