Tested for Windows 11 and Ubuntu 22.04<br>
Python 3.11.7<br>
Requires:<br>
matplotlib (tested 3.8.2)<br>
astropy (tested 6.0.0)<br>
numpy (tested 1.25.2)<br>
argparse (tested 1.25.2) (included in Python standard lib) <br>
configobj (tested 5.0.8)<br>
wxPython (tested 4.2.1)<br>

To quickly install all the pakcages, run within the project directory :
`python -m pip install -r requirements.txt`

wxPython in particular requires gtk3 so install that if it gives you errors :

`sudo apt-get install libgtk-3-dev` (Linux)

Within the directory run:

`python osv.py`

To run the GUI. <br>

If you want to run osv.py from any location (Linux) :

Create an alias of the command
`alias osv="python /<dir_of_osv>/osv.py"`<br>
Update bash or restart the terminal 
`source ~/.bash_profile`<br>
You should be able to run osv in any directory
`osv`<br>

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
