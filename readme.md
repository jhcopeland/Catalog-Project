# Catalog Project

This is an application that performs the following:

- Provides a list of items within a variety of categories.
- Provides a user registration and authentication system.
- Registered users will have the ability to post, edit and delete their own items.

Specifically, this project involves the use of a python program (application.py) to pull information from a PostgreSQL database for a catalog website.  This REST-ful web application uses the Python framework Flask along with a third-party OAuth authentication implementation to secure the database and various CRUD (create, read, update and delete) operations.


## Requirements

1. Computer (Windows or MAC)
2. Vagrant (https://www.vagrantup.com/)
3. VirtualBox (https://www.virtualbox.org/)
4. Python 2.7.12 or higher (https://www.python.org/)
5. Working knowledge of Vagrant and the virtual server
6. Ability to run python from command-line.
7. This ZIP file  (catalog-app.zip)


## Instructions

Make sure you have a working copy of the Linux-based virtual machine (VM) and Python 2.7.12 or higher installed on your computer (see requirement above for Vagrant, VirtualBox and Python).


### Extract the Zip Files & Run the Application

1. Extract all the zip files into your shared vagrant directory from which you will SSH into the Virtual Vagrant server.
2. SSH into the virtual server and cd into your 'vagrant' directory.
3. Run the application by typing python application.py and then enter.
4. Open your web browser and enter 'localhost:5000' into the address bar.
5. The application home screen will be displayed and prompt you to login.  (*All application functionality will be disabled until you login.*)
6. Once you have logged in, the home page will allow you to see the catalog, its catagories and associated items.
7. At this point you will be able to add, edit and delete items from the available catagories.
8. Select the logout button to log out of the application.
