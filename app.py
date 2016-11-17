import os
import datetime
import psycopg2
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for, render_template, g, Response
global Gportfolioid
Gportfolioid = 0
global uid
uid = 0

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.debug = True
DATABASEURI = ""
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

"""
Login page and handling login errors including bad user and bad password
"""
@app.route('/')
def index():
    return render_template("login.html")

@app.route('/logout')
def logout():
    global uid
    uid = 0
    global Gportfolioid
    Gportfolioid = 0
    global currentcash
    currentcash = 0
    return redirect(url_for('index'))

@app.route('/check_login', methods=['POST'])
def checklogin():
    #set up variables
    link = []
    loginuid = request.form['uid']
    password = request.form['password']
    checkuser = ""
    #SQL query the user login
    args = [loginuid]
    cmd ="SELECT uid from users where uid=%s"
    cursor = g.conn.execute(cmd,args)
    for result in cursor:
        checkuser= result
    cursor.close()
    #check if loginuid is good in database
    if checkuser != "":
        args = [loginuid]
        cmd ="SELECT password from users where uid=%s"
        cursor = g.conn.execute(cmd,args)
        for result in cursor:
            checkpassword= result
        cursor.close()
        if checkpassword[0]==password:
            link = 'portfolio'
            #set global uid if uid is good
            global uid
            uid = checkuser[0]
        else:
            link = 'badpw'
    else:
        link = 'badlog'
    return redirect(url_for(link, passuid=int(loginuid), portfolioid=0))

@app.route('/incorrectlogon/<passuid>/<portfolioid>')
def badlog(passuid, portfolioid):
    return render_template("incorrectlogon.html", baduid=passuid)

@app.route('/incorrectpw/<passuid>/<portfolioid>')
def badpw(passuid, portfolioid):
    return render_template("incorrectpw.html", baduid=passuid)


"""
Load user portfolio including open and closed positions, includes:
- redirects from navigation page
- reload portfolio based on selection from drop down
- load portfolio page
"""

#User portfolio
@app.route('/portfolio/return')
def portfolioreturn():
    if uid == 0:
        return redirect(url_for('index'))
    return redirect(url_for('portfolio', passuid=uid, portfolioid=Gportfolioid))

@app.route('/portfolio/<passuid>/<portfolioid>', methods=['POST'])
def populateportfolio(passuid,portfolioid):
    if uid == 0:
        return redirect(url_for('index'))
    global Gportfolioid
    Gportfolioid = int(request.form['portfolio'])
    return redirect(url_for('portfolio', passuid=uid, portfolioid=Gportfolioid))

@app.route('/portfolio/<passuid>/<portfolioid>')
def portfolio(passuid, portfolioid):
    if uid == 0:
        return redirect(url_for('index'))
    #obtain user's list of portfolios
    args = [uid]
    cmd ="SELECT portfolioid FROM portfolio where uid=%s"
    cursor = g.conn.execute(cmd, args)
    portfolios = []
    for result in cursor:
        portfolios.append(result[0])
    cursor.close()

    #render user's portfoliodata
    args = [int(uid), int(Gportfolioid)]
    cmd ="SELECT t1.ticker, t1.netshares, t1.netcost, t2.current_price, (t1.netshares * t2.current_price) AS currentvalue FROM (SELECT ticker, SUM(shares) As netshares, SUM(shares * open_position_price*-1) AS netcost FROM stock_transactions WHERE uid=%s and portfolioid=%s GROUP BY ticker) AS t1, (SELECT ticker, current_price  FROM us_stock) AS t2 WHERE t1.ticker = t2.ticker;"
    cursor = g.conn.execute(cmd,args)
    transactions = []
    nettrades = 0
    for result in cursor:
        transactions.append(result)
        nettrades = nettrades + result[2]
    cursor.close()

    #net users input and output of cash for a specific portfolio
    args =[int(uid), int(Gportfolioid)]
    cmd ="SELECT amount FROM cash_transactions WHERE uid=%s AND portfolioid=%s;"
    cursor = g.conn.execute(cmd, args )
    netcash = 0

    #get net cash from cash transactions
    for result in cursor:
        netcash = netcash + result[0]
    cursor.close()
    global currentcash
    currentcash = netcash + nettrades
    #select user data
    args = [uid]
    cmd = "SELECT * FROM users where uid=%s"
    cursor = g.conn.execute(cmd,args)
    userinfo = []
    for result in cursor:
        userinfo=result
    cursor.close()

    cmd = "SELECT ticker, current_price FROM us_stock ORDER BY ticker"
    cursor = g.conn.execute(cmd)
    tickers = []
    for result in cursor:
        tickers.append(result)
    cursor.close()
    args = [uid]
    cmd = "SELECT bankaccountid FROM bank_accounts WHERE uid=%s ORDER BY bankaccountid"
    cursor = g.conn.execute(cmd,args)
    bankaccountids = []
    for result in cursor:
        bankaccountids.append(result[0])
    cursor.close()

    return render_template("portfolio.html", portfolioid=Gportfolioid, portfolios=portfolios, transactions=transactions, user=userinfo, tickers=tickers, bankaccountids=bankaccountids, currentcash='${:,.2f}'.format(currentcash))


"""
Updates to the database from the portfolio page:
- Create new portfolio
- Create a new bank account
- Execute trades
- Transfer cash in and out of accounts
"""
#create portfolio
@app.route('/post_portfolio', methods=['POST'])
def post_portfolio():
    if uid == 0:
        return redirect(url_for('index'))
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(portfolioid) FROM portfolio'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        portfolioid = result[0] + 1
    portfolioid = int(portfolioid)
    cursor.close()
    args = [portfolioid, uid]
    cmd = 'INSERT INTO portfolio VALUES (%s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('portfolio', passuid=uid, portfolioid=Gportfolioid))

#create bank account
@app.route('/post_bankaccount', methods=['POST'])
def post_bankaccount():
    if uid == 0:
        return redirect(url_for('index'))
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(bankaccountid) FROM bank_accounts'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        bankaccountid = result[0] + 1
    cursor.close()
    bankaccountid = int(bankaccountid)
    args = [bankaccountid, request.form['aba'], request.form['accountnumber'], uid, request.form['directdeposit']]
    cmd = 'INSERT INTO bank_accounts VALUES (%s, %s, %s, %s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('portfolio', passuid=uid, portfolioid=Gportfolioid))

#create bank account
@app.route('/post_bankaccount2', methods=['POST'])
def post_bankaccount2():
    if uid == 0:
        return redirect(url_for('index'))
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(bankaccountid) FROM bank_accounts'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        bankaccountid = result[0] + 1
    cursor.close()
    bankaccountid = int(bankaccountid)
    args = [bankaccountid, request.form['aba'], request.form['accountnumber'], uid, request.form['directdeposit']]
    cmd = 'INSERT INTO bank_accounts VALUES (%s, %s, %s, %s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('profile'))



#posting stock trades
@app.route('/post_trade', methods=['POST'])
def post_trade():
    if uid == 0:
        return redirect(url_for('index'))
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(stockid) FROM stock_transactions'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        stockid = result[0] + 1
    cursor.close()
    stockid = int(stockid)
    tdate = datetime.date.today()
    tdate = str(tdate)


    #render user's portfoliodata
    args = [int(uid), int(request.form['portfolio'])]
    cmd ="SELECT t1.ticker, t1.netshares, t1.netcost, t2.current_price, (t1.netshares * t2.current_price) AS currentvalue FROM (SELECT ticker, SUM(shares) As netshares, SUM(shares * open_position_price*-1) AS netcost FROM stock_transactions WHERE uid=%s and portfolioid=%s GROUP BY ticker) AS t1, (SELECT ticker, current_price  FROM us_stock) AS t2 WHERE t1.ticker = t2.ticker;"
    cursor = g.conn.execute(cmd, args)
    nettrades = 0
    for result in cursor:
        nettrades = nettrades + result[2]
    cursor.close()

    #net users input and output of cash for a specific portfolio
    args = [int(uid), int(request.form['portfolio'])]
    cmd ="SELECT amount FROM cash_transactions WHERE uid=%s AND portfolioid=%s;"
    cursor = g.conn.execute(cmd, args)
    netcash = 0
    #get net cash from cash transactions
    for result in cursor:
        netcash = netcash + result[0]
    cursor.close()
    thiscash = netcash + nettrades

    #select user data
    args = [uid]
    cmd = "SELECT * FROM users where uid=%s"
    cursor = g.conn.execute(cmd,args)
    userinfo = []
    for result in cursor:
        userinfo=result
    cursor.close()
    a = []
    a = request.form['ticker']
    b = a.rsplit(',', 1)[0]
    c = float(a.rsplit(',', 1)[1])

    if request.form['order']=='buy':
        shares = int(request.form['shares'])
    else:
        shares = int(request.form['shares'])*-1
    if (float(shares)*-1*float(c) + thiscash) <0:
        return redirect(url_for('insufficientfunds', passuid=uid, portfolioid=request.form['portfolio'], thiscash=thiscash))

    args = [stockid, b, uid, request.form['portfolio'], shares, c, tdate]
    cmd = 'INSERT INTO stock_transactions VALUES (%s, %s, %s, %s, %s, %s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('portfolio', passuid=uid, portfolioid=int(request.form['portfolio'])))

#transfer cash
@app.route('/post_cash', methods=['POST'])
def post_cash():
    if uid == 0:
        return redirect(url_for('index'))

    amount=[]
    tdate = ""
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(transactionid) FROM cash_transactions'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        transactionid = result[0] + 1
    cursor.close()
    transactionid = int(transactionid)
    #set transfer data
    tdate = datetime.date.today()
    tdate = str(tdate)
    #determine whether amount is positive or negative
    if request.form['order']=='In':
        amount = float(request.form['amount'])
    else:
        amount = float(request.form['amount'])*-1
    #render user's portfoliodata
    args = [int(uid), int(request.form['portfolio'])]
    cmd ="SELECT t1.ticker, t1.netshares, t1.netcost, t2.current_price, (t1.netshares * t2.current_price) AS currentvalue FROM (SELECT ticker, SUM(shares) As netshares, SUM(shares * open_position_price*-1) AS netcost FROM stock_transactions WHERE uid=%s and portfolioid=%s GROUP BY ticker) AS t1, (SELECT ticker, current_price  FROM us_stock) AS t2 WHERE t1.ticker = t2.ticker;"
    cursor = g.conn.execute(cmd, args)

    nettrades = 0
    for result in cursor:
        nettrades = nettrades + result[2]
    cursor.close()

    #net users input and output of cash for a specific portfolio
    args = [int(uid), int(request.form['portfolio'])]
    cmd ="SELECT amount FROM cash_transactions WHERE uid=%s AND portfolioid=%s;"
    cursor = g.conn.execute(cmd, args)
    netcash = 0

    #get net cash from cash transactions
    for result in cursor:
        netcash = netcash + result[0]
    cursor.close()
    thiscash = netcash + nettrades

    if (amount + thiscash) <0:
        return redirect(url_for('insufficientfunds', passuid=uid, portfolioid=request.form['portfolio'], thiscash=thiscash))
    #insert transaction into database
    args = [transactionid, tdate, uid, int(request.form['bankaccountid']), request.form['portfolio'], amount]
    cmd = 'INSERT INTO cash_transactions VALUES (%s, %s, %s, %s, %s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('portfolio', passuid=uid, portfolioid=request.form['portfolio']))


@app.route('/insufficientfunds/<passuid>/<portfolioid>/<thiscash>')
def insufficientfunds(passuid,portfolioid, thiscash):
    #obtain user's list of portfolios
    args = [uid]
    cmd ="SELECT portfolioid FROM portfolio where uid=%s"
    cursor = g.conn.execute(cmd, args)
    portfolios = []
    for result in cursor:
        portfolios.append(result[0])
    cursor.close()
    #obtain us tickers
    cmd = "SELECT ticker, current_price FROM us_stock ORDER BY ticker"
    cursor = g.conn.execute(cmd)
    tickers = []
    for result in cursor:
        tickers.append(result)
    cursor.close()
    #obtain backaccounts
    args = [uid]
    cmd = "SELECT bankaccountid FROM bank_accounts WHERE uid=%s ORDER BY bankaccountid"
    cursor = g.conn.execute(cmd, args)
    bankaccountids = []
    for result in cursor:
        bankaccountids.append(result[0])
    cursor.close()

    return render_template("notenoughfunds.html", portfolioid=portfolioid, portfolios=portfolios, tickers=tickers, bankaccountids=bankaccountids, thiscash='${:,.2f}'.format(float(thiscash)))


"""
Creating and editing user acounts and related information:
- Create new user
- Redirect after successful user creation communicate uid
- Render an existing user profile
- Update an existing user or delete
- Delete bank account
- Delete a portfolio
"""

#New User page and adding new user to database
@app.route('/newuser')
def newuser():
    return render_template("add_user.html")


#send a new users to the database
@app.route('/post_user', methods=['POST'])
def post_user():
    #find biggest primary key id and increment by 1
    cmd = 'SELECT MAX(uid) FROM users'
    cursor = g.conn.execute(cmd)
    for result in cursor:
        uid = result[0] + 1
    uid = int(uid)
    cursor.close()
    #fill out user data and store in database
    args = [uid, request.form['fname'], request.form['lname'], request.form['address'], request.form['phone'], request.form['ssn'], request.form['email'], request.form['password']]
    cmd = 'INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s)';
    g.conn.execute(cmd, args);
    return redirect(url_for('usercreated', uid=int(uid)))


@app.route('/usercreated/<uid>')
def usercreated(uid):
    return render_template("usercreated.html", uid=uid)

#Render user profile
@app.route('/profile')
def profile():
    if uid == 0:
        return redirect(url_for('index'))
    args = [uid]
    cmd = "SELECT * FROM users where uid=%s"
    cursor = g.conn.execute(cmd, args)
    userdata = []
    for result in cursor:
        userdata=result
    cursor.close()
    args = [uid]
    cmd ="SELECT portfolioid FROM portfolio where uid=%s"
    cursor = g.conn.execute(cmd, args)
    portfolios = []
    for result in cursor:
        portfolios.append(result[0])
    cursor.close()
    args = [uid]
    cmd = "SELECT * FROM bank_accounts WHERE uid=%s ORDER BY bankaccountid"
    cursor = g.conn.execute(cmd,args)
    bankaccountids = []
    for result in cursor:
        bankaccountids.append(result)
    cursor.close()

    return render_template("profile.html", userdata=userdata, portfolios=portfolios, bankaccountids=bankaccountids )


#update user profile
@app.route('/update_user', methods=['POST'])
def update_user():
    if uid == 0:
        return redirect(url_for('index'))
    #fill out user data and update in database
    args = [request.form['fname'], request.form['lname'], request.form['address'], request.form['phone'], request.form['ssn'], request.form['email'], request.form['password'], uid]
    cmd = 'UPDATE users SET (fname, lname, address, phone, ssn, email, password) = (%s, %s, %s, %s, %s, %s, %s) WHERE uid=%s';
    g.conn.execute(cmd, args);

    args = [uid]
    cmd = "SELECT * FROM users where uid=%s"
    cursor = g.conn.execute(cmd,args)
    userdata = []
    for result in cursor:
        userdata=result
    cursor.close()
    return redirect(url_for('profile'))

#delete user profile
@app.route('/delete_user', methods=['POST'])
def delete_user():
    if uid == 0:
        return redirect(url_for('index'))
    args = [uid]
    cmd = 'SELECT uid FROM bank_accounts WHERE uid=%s and direct_deposit = true'
    cursor = g.conn.execute(cmd, args)
    checkuser = []
    for result in cursor:
        checkuser = result[0]
    cursor.close()
    if checkuser == uid:
        args = [uid]
        cmd = 'DELETE FROM users WHERE uid=%s'
        g.conn.execute(cmd, args)
        return redirect(url_for('index'))
    return redirect(url_for('cantdelete'))

@app.route('/cannotdelete')
def cantdelete():
    return render_template("cantdelete.html")



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0') #default='localhost')
  @click.argument('PORT', default=8081, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    #print("running on" %s:%d) % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
