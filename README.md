# Pyscript Juniper Routing Table Compare
Web app to compare Juniper Routing tables without needing access to the platforms

This is purely a demonstration of what can be done with pyscript and is not intended
for Production use but requires lots of aspects of using pyscript.

This has only been used on very small routing table output included int the repo

The pyscript CDN is used instead of local machine installation

![Screenshot from 2022-06-21 14-35-13](https://user-images.githubusercontent.com/63735312/174812550-adaf8805-eb9b-4637-9e06-a79c9cbbf06e.png)

**Installation - Option 1 - Web Hosted**

1) Clone the repo

2) Host the static folder on a simple web server such as the inbuilt python one.`python -m http. server 8000`

3) In your browser navigate to the HTML file at the appropriate URL 

**Installation - Option 2 - No Web Hosting**

1) Clone the repo

2) To avoid using the need to host the file. Copy/Paste the python script into the HTML file within the ```<pyscript>``` tags
  
3) Make the change in the HTML file from ```<py-script src="/static/junosroute.py">``` to ```<pyscript>``` i.e. empty tag

**Using the app**
  
Upload the **previous\*.txt** file in first and then upload the **current\*.txt** one where the EventListener will trigger the python script

