# My family website

This is probably not interesting to anyone other than me

The technologies in use are:

* Python
* Flask
* Google App Engine

## Set up instructions

*Note: As with most development projects, it'll be easier to run this on either Linux or a Mac.  If you have Windows, I recommend running Ubuntu inside a virtual machine.*

1. Install Python 2.7 and pip

	* I highly recommend installing virtualenv and virtualenvwrapper too
	
2. Install Google App Engine SDK

	* https://developers.google.com/appengine/downloads
	
3. Go to your top-level projects folder (where you want this to live) and type:

    git clone https://github.com/trungly/thelyfamily.git
    
    cd thelyfamily
	
4. Create your virtual environment here

	mkvirtualenv thelyfamily

5. Install the Python package called PIL (Python Image Library).  On Mac, it is called pillow, so the command would be:

	pip install pillow
	
	***Note**: PIL is only needed locally for manipulating images; Google App Engine takes care of this for us on the production server.*
	
6. Install the rest of the python packages from requirements.txt into the server/lib directory by doing this:

	pip install -r requirements.txt -t server/lib
	
7. Run the server

	dev_appserver.py .
	
8. In your web browser, go to:

	localhost:8080
	
9. You can go to `http://localhost:8000` if you want to mess with things like viewing the Datastore (database)
