## Gamers Club Scrapper
A selenium based scrapper that extracts files for matches on Gamers Club site and writes the files to remote drive
NOTE: The scrapper downloads the files to local machine (default download folder)

### Installation
Ensure rclone is installed. [Refer to](https://rclone.org/install/)

Ensure Python3 is installed

Clone the project from Github

Navigate to the project folder

Install the requirements.txt file

```
pip3 install -r requirements.txt
```
## Variables and secrets
Set the following variables

### login page credentials
USERNAME = "username" // gamers-club username
PASSWORD = "password" // gamers club passwor

# copy files
RCLONE_CONF_LOCATION = "rclone config file path" // you can obtain this by running `rclone config file`
RCLONE_REMOTE_FOLDER = "remote folder which your local rclone point to"

### Run program
Run scrapper.py file
```
python3 scrapper.py
```
