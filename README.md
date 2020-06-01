# Event-Density-Map
"Event Density Map" project includes the development of a web application which presents the event information by collecting and saving the event information from the sites which are regularly publish the events. It also includes creating the statistical results by using event database and filtering the events according to the user's choices.

One of the objectives of this study is to eliminate the need to use more than one website when investigating the activities will be performed. In addition to this purpose, the detailed filters provided in the application provide faster access to the desired. For this purpose, in addition to obtaining all information about the events from the sites, the irregular data given on the sites have been tried to be reached by using regex.

Another aim of this study is to ensure that detailed activity data collected can be used for various researches. These data were obtained by scanning sites using the BeautifulSoup and Selenium libraries.

<p align="center">
  <img src="https://user-images.githubusercontent.com/20224643/83420145-df4c6c80-a42e-11ea-8c1f-2a37543d5a29.png" width="600" >
</p>
<p align="center"><b>Image 1.</b> Main Page </p>

<p align="center"><img src="https://user-images.githubusercontent.com/20224643/83444609-4af50080-a454-11ea-86a6-654be3fd352b.png" width="600"> </p>
<p align="center"><b>Image 2.</b> Filters </p>

<p align="center"><img src="https://user-images.githubusercontent.com/20224643/83444232-c4402380-a453-11ea-9b21-09ecdefdcb12.png" width="600"> </p>
<p align="center"><b>Image 3.</b> Search Result </p>

<p align="center"><img src="https://user-images.githubusercontent.com/20224643/83444304-e0dc5b80-a453-11ea-937f-ed4ea8a906f2.png" width="600"> </p>
<p align="center"><b>Image 4.</b> Statistics Page </p>

## Getting Started
Adjustments are provided for the Linux operating system.  The [Code](https://github.com/cerenyasar/Event-Density-Map/tree/master/Code) folder must be imported to the desired IDE. The virtual environment should be installed and the directory would be arranged accordingly.While the virtual environment is active, the content should be loaded by running the command below in the same directory as the [requirements.txt](requirements.txt) : 
```
 pip install -r requirements.txt
```
### Database Installation
After installing MongoDB, the following command must be run to start the service: 
```
$sudo service mongod start
```
Database installation will be completed when the console commands below are run in the same directory with the .json files in the Code folder.

```
$ mongoimport --db eventMapDB --collection events <events.json

$ mongoimport --db eventMapDB --collection users <users.json

$ mongoimport --db eventMapDB --collection places <places.json
```

There are activities between 05.01.2019 and 07.02.2019 in the database.

### Running
The web application can be started by running the [index.py](https://github.com/cerenyasar/Event-Density-Map/blob/master/Code/venv/index.py) code.

One of the admins registered in the database to view the admin page:

>username: Admin

>Password: mysecret

After logging in with the information, the normal user or admin user can be made by editing the desired user on the user tab in the "Go to Admin Page" link on the main page to be opened.

### Database Update Code

The [databaseUpdate.py](https://github.com/cerenyasar/Event-Density-Map/blob/master/Code/venv/databaseUpdate.py) file works with a parameter and ensures that the database is updated for Biletix and TFF sites and new events are recorded.

Parameters and their meanings:

**-1 :** Retrieving all the activities available on Biletix.

__3  :__ Retrieving the 900 most recent events on Biletix site. Other positive natural numbers can be used as a parameter, the number entered * 300 most recent events will be drawn.

__-2 :__ Retrieving all football events from that day on the TV site.

**Note:** Depending on the internet speed, the time.sleep () times may need to be extended in order for the code to work properly.
Also, changes in the source code of the accessed sites may prevent this code from working correctly.

## Crontab adjustment

If you want to update the database automatically:

```
$crontab -e
```
must be run and the text in the [crontab.txt](crontab.txt) file must be copied and saved in the opened text editor.  

The part '/dev/pts/2' in the text may vary on your computer. Terminalde `tty` komutu ile o kısma yazılması gereken öğrenilebilir.  Also, the user name must be changed while the path is being given.

## License

This project is licensed under the GPL v3.0  License - see the [LICENSE](LICENSE) file for details

