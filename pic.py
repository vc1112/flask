from flask import Flask, render_template, request, redirect , flash,session
import sqlite3 as sql
import time
from datetime import timedelta
import os
import random
import string
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from flask.helpers import url_for
application = app = Flask(__name__)


UPLOAD_FOLDER = 'static/'
 
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.permanent_session_lifetime = timedelta(minutes=5)
#ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
#def allowed_file(filename):
 #  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home() -> render_template:
   return render_template('home.html')

@app.route('/register',methods = ['POST', 'GET'])
def register():
   if request.method == 'POST':

      username = request.form['username']
      password = request.form['password']

      if(username=="" or password==""):   ## in case fields werent filled
         msg = "Fill all the details"
         return render_template("home.html",msg = msg )
      with sql.connect("photos.db") as con:
         cur = con.cursor()
         cur.execute("SELECT * FROM students WHERE username = ? ", (username, ) )
         rows = cur.fetchall()
         if(len(rows) != 0):  # check if user already exist
            msg = "it seems the username is already taken!!  try giving it some name"
            return render_template("home.html", msg=msg)
         else:
            hashPass = generate_password_hash(password, method='sha256')  ## generating password hash Method SHA 256
            cur.execute("INSERT INTO students (id,username,password) VALUES (?,?,?)",(str(time.time()),username,hashPass) ) # entering stuff inside the DB
            con.commit()   # saving the session and commiting stuff
            msg = "Successfully registered"
      con.close()
      session["user"] = username  # loging into our session after registernation
      return redirect(url_for("dashboard", username=username ))
   return render_template("home.html")


@app.route('/login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':

      username = request.form['username']
      password = request.form['password']

      if(username=="" or password==""):
         msg = "Fill all the details"
         return render_template("home.html",msg = msg )

      with sql.connect("photos.db") as con:
         cur = con.cursor()
         cur.execute("SELECT password FROM students WHERE username = ?", (username, ) )
         rows = cur.fetchall()
         #print(rows)
         if(len(rows) != 1) or not check_password_hash(rows[0][0],password): # in case we didnt get any field OR the password hash dosent match
            msg = "Check Id/Password once again"
         else:
            session["user"] = username # Logging into our session
            return redirect(url_for("dashboard", username=username ))
      con.close()
   return render_template("home.html",msg=msg)


@app.route('/dashboard/<username>')
def dashboard(username) -> render_template:
   username = session["user"]
   with sql.connect("photos.db") as con:
      cur = con.cursor()
      cur.execute("SELECT url FROM images WHERE id = ? ", (username,) )
      listImg = cur.fetchall()
      #print(listImg)
      images = []
      for i in listImg:
         images.append(i[0])
   con.close()
   return render_template("viewpics.html",username=username,listImg=images)


#
#


@app.route('/addpics/<username>', methods = ["GET", "POST"])
def addpics(username):
   username = session["user"]
   #print(request.files)
   if request.files:
      file = request.files['image']
      if file.filename == '':
         flash('No image selected for uploading')
         #print("++++++")
         return redirect(url_for("dashboard",username=username))
      if file:
         filename = secure_filename(file.filename)
         pichash = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(20))+filename  ## added random string here
         with sql.connect("photos.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM images WHERE id = ? AND url = ?", (username, pichash) )
            rows = cur.fetchall()
            if(len(rows) != 0):
               flash("Please Change the name of the file .. another file with that name exists in you account ... ")
               return redirect(url_for("dashboard",username=username))
         con.close()
         file.save(os.path.join(app.config['UPLOAD_FOLDER'],pichash ))
         flash('Image successfully uploaded and displayed below')
         #print("======")

         with sql.connect("photos.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO images (id, url) VALUES (?,?)", (username, pichash) )
            msg = "uploaded suceessfully"
            con.commit()
         con.close()
         return redirect(url_for("dashboard",username=username))
      else:
         flash('Allowed image types are - png, jpg, jpeg, gif')
         return redirect(url_for("dashboard",username=username))


@app.route('/deletepics/<username>', methods = ["GET"])
def deletepics(username):
   #print(request.method)
   if request.method == "GET":
      file = request.args.get('image')
      filename = file.split("/")[-1]
      try:
         os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      except FileNotFoundError:
         print("file does not exist")
      with sql.connect("photos.db") as con:
         cur = con.cursor()
         
         cur.execute("SELECT * FROM images WHERE id = ? AND url = ?", (username, filename) )
         rows = cur.fetchall()
         if(len(rows) == 0):
            flash("No file with that URL exists")
         else:
            cur.execute("DELETE FROM images WHERE id = ? AND url = ?", (username, filename) )
         con.commit()
      con.close()
      return redirect(url_for("dashboard",username=username))
   else:
      return redirect(url_for("dashboard",username=username))

@app.route("/logout")
def logout():
   session.pop("user", None)
   return redirect(url_for("home"))


if __name__ == '__main__':
   app.run(debug = True)