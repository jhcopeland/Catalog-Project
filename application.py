from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, CatUser, Category, CatItem

# Imports for antiforgery
from flask import session as login_session
import os, random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = json.loads(
    open('/var/www/catalog/web_client_secret.json', 'r').read())['web']['client_id']


# Connect to Database ----------------------------
#engine = create_engine('sqlite:///usercategoryitem.db', connect_args={'check_same_thread':False})
engine = create_engine('postgresql://catalog:sunshine25@localhost/usercategoryitem')
Base.metadata.bind = engine

# Create database session ------------------------
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token ----------------
# Store it in login_session for later validation -
@app.route('/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
#    return "The current session state is %s" % login_session['state']
#    return render_template('login.html')
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions
def createUser(login_session):
    newUser = CatUser(name=login_session['username'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(CatUser).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(CatUser).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(CatUser).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token
# and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is: ', access_token
    print 'User name is: ', login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        #flash("Logout Successful. Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show catalog home -------------------------------
@app.route('/catalog')
def showCatalog():
    db_category = session.query(Category)
    db_catItem = session.query(CatItem).order_by(CatItem.id.desc()).limit(9)
    #flash("%s Hello!" % login_session['username'])
    return render_template('catalog.html', dbcategories = db_category, dbitems = db_catItem)

# Show items in category --------------------------
@app.route('/catalog/<int:category_id>/')
def showCategory(category_id):
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        db_category = session.query(Category)
        category = session.query(Category).filter_by(id=category_id).one()
        cat_items = session.query(CatItem).filter_by(cat_id=category_id).all()
        return render_template('category.html', dbcategories = db_category, category=category, catitems=cat_items)

# Show item description ---------------------------
@app.route('/catalog/description/<int:item_id>/')
def showItemDescr(item_id):
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        cat_item = session.query(CatItem).filter_by(id=item_id).one()
        return render_template('description.html', catitem=cat_item)

# Add item to category --------------------------------------------------------
@app.route('/catalog/add/<int:category_id>', methods=['GET', 'POST'])
def addItem(category_id):
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        category = session.query(Category).filter_by(id=category_id).one()
        if request.method == 'POST':
            if request.form['name']:
                if request.form['descr']:
                    description = request.form['descr']
                else:
                    description = 'void'
                catItem = CatItem(user_id=login_session['user_id'], name=request.form['name'], description=description, category=category)
                session.add(catItem)
                session.commit()
                flash('New Item %s Successfully Added. Item Description = %s' % (request.form['name'], description))
            else:
                flash('ERROR: Item name cannot be empty for successful add.')
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            return render_template('additem.html', category=category)


# Edit a category item ----------------------------
@app.route('/catalog/edit/<int:item_id>/', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        cat_item = session.query(CatItem).filter_by(id=item_id).one()
        if cat_item.user_id != login_session['user_id']:
            flash("You do not have permission to edit this item!")
            return redirect(url_for('showCategory', category_id=cat_item.cat_id))
        if request.method == 'POST':
            if request.form['name']:
                cat_item.name=request.form['name']
            if request.form['descr']:
                cat_item.description=request.form['descr']
            session.add(cat_item)
            session.commit()
            flash('%s Item Successfully Edited' % cat_item.category.name)
            return redirect(url_for('showCategory', category_id=cat_item.cat_id))
        else:
            return render_template('edititem.html', catitem=cat_item)


# Delete a category item ------------------------------------------------------
@app.route('/catalog/delete/<int:item_id>/', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        cat_item = session.query(CatItem).filter_by(id=item_id).one()
        category = cat_item.category
        if cat_item.user_id != login_session['user_id']:
            flash("You do not have permission to delete this item!")
            return redirect(url_for('showCategory', category_id=category.id))
        if request.method == 'POST':
            session.delete(cat_item)
            session.commit()
            flash('%s Item Successfully Deleted' % category.name)
            return redirect(url_for('showCategory', category_id=category.id))
        else:
            return render_template('deleteitem.html', catitem=cat_item)


# JSON API methods --------------------------------
@app.route('/catalog/JSON')
def catalogJSON():
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        db_category = session.query(Category).order_by(Category.id)
        db_catItem = session.query(CatItem).order_by(CatItem.cat_id)
        return jsonify(Category = [c.serialize for c in db_category], Item = [i.serialize for i in db_catItem])


@app.route('/category/JSON')
def categoryJSON():
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        db_category = session.query(Category)
        return jsonify(Category = [c.serialize for c in db_category])


@app.route('/item/JSON')
def itemJSON():
    if 'username' not in login_session:
        #flash("Please login to utlize this application!")
        #return render_template('pubcatalog.html')
        return redirect(url_for('showLogin'))
    else:
        db_catItem = session.query(CatItem)
        return jsonify(Item = [i.serialize for i in db_catItem])


#-------------------------------------------------
if __name__ == '__main__':
	#app.secret_key = 'secret'
	#app.config['SESSION_TYPE'] = 'filesystem'
	#app.debug = True
	#app.run(host = '0.0.0.0', port = 5000)
	app.run()
