# VT Classes Parser
This is a piece of software meant to fetch data from the classes.vt.edu website for relevant courses based on a set of search queries. The data is exported to a *.csv file that contains concise information on each college course.

# Requirements
Python 12+ (untested on other versions)

# Running the App
1. Access ```classes.vt.edu``` and open the inspector by pressing F12, CTRL+SHIFT+I, or opening developer tools under more tools. Then open the ```Network``` tab.
2. Login with your VT account, otherwise not all relevant information will be disclosed.
3. You should see a new entry popup with the following information: <br>```200 POST classes.vt.edu https://classes.vt.edu/api/?page=sisproxy&action=studentdata```. Double click on this and a new tab should open with more details.
4. You'll see a field in the first line called "pers". You'll want to select the information in the ```id``` and ```idProof``` fields and input them when required by the software.
5. Run ```main.py``` after installing the requirements.txt with ```pip install -r requirements.txt```

# WIP
- [x] Backend
    - [ ] Auto parse keys from user input
- [ ] Frontend user interface
- [ ] Minimize server usage
- [ ] Executeable version

