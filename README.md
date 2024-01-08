Tested for Windows 11 and Ubuntu 22.04
Python 3.11.7<br>
Requires:<br>
matplotlib (tested 3.8.2)<br>
astropy (tested 6.0.0)<br>
numpy (tested 1.25.2)<br>
argparse (tested 1.25.2)<br>
configobj (tested 5.0.8)<br>
wxPython (tested 4.2.1)<br>

wxPython in particular requires gtk3 so install that if it gives you errors :

`sudo apt-get install libgtk-3-dev` (Linux)

Within the directory run:

`python osv.py`

To run the GUI.

In general the possible commands are :

`python osv.py doconfig`

This lets you set a default directory and some other default values, so you don't have to input the everytime (for example the data directory)

`python osv.py getdata`

This is mainly used in the download script, but you can use it manually to download specific data 

`python osv.py checkdeps` 

Checks your dependencies

`python osv.py checkvers`

Checks the package versions of the modules above you have installed (good to verify reproducibility)

`python osv.py getconfig`

Prints out the current config file (not elegant at the moment) but it allows you to double check configurations without having to rerun "doconfig"

`python osv.py ver` 

Check osv.py version 
