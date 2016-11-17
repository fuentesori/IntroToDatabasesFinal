#Columbia - COMS 4111 Introduction to Databases

Project goal is to produce a web application that interacts with a Postgres database
stored on Google Cloud. The application must allow the user to interact with different
tables and relations in the database without facing errors, entering SQL code nor
exposing the database to SQL injections. The following are used:

* Python Flask
* Postgres
* SQL
* HTML
* CSS

# Personal Stock Portfolio

## Introduction:
The website offers personal equity investment portfolios for US stocks (NYSE,
and NASDAQ). Users can open portfolios and contribute to them with funds from
either one or several personal bank accounts. They will be able to view and manage
portfolios from an online portal. The website will provide insight into performance
of individual and overall portfolios, current stock prices and the ability to
buy or short equity. The main entities will be the users and portfolios. Main
operations will be contributing or removing cash from portfolios, and buying
or selling stock. Cash operations are saved to a table with their respective
date, user, funding/drawing bank account and corresponding portfolio. Stock
transactions are saved in a table with corresponding date, user, stock ticker,
price and amount. Both transaction tables along with a table of US stocks and
current prices will be used to calculate updated positions of portfolios: total
amount in cash, total amount invested and performance to date.

## Functions of the portfolio:
Users may either create an account or log in using an existing account. once in
their account the following operations are available:
* Add portfolios
* View a portfolio
* Add a bank account
* Execute a stock transaction
* Execute a cash transaction
They can also view their profile information, edit it or delete their profile,
the later is only allowed if the user has at least one bank account set up with
direct deposit.

## Navigating the Application:
### Login:
The user arrives at the login page, where they may either log in or create a new
account for themselves. They must enter their first and last name, email, street
address, phone number, SSN, and create a password. Upon account creation, the
user will receive their user id so they can log in again in the future.

### Portfolio:
A logged in user gets redirected to the portfolios page where they may view
their portfolios, add new portfolios or bank accounts, perform stock
transactions and finance their portfolios using their bank accounts.

### Profile:
From the Portfolio page user may navigate to their profile to edit their
information, add bank account information, or delete their accounts. They may also
click logout to leave the application and clear their data so another user is
unable to see their information.

## Restrictions:
### Login:
Users must enter a valid portfolio id number, using only numerical input.
If they do not enter a valid id number they will be redirected to a page letting
them know their id was invalid that redirects back to the login page. The login
must also match up to the correct password given in the database. The password
must only contain numbers, letters and underscores.

### Add User:
Each field has restrictions to ensure a clean database and to prevent sql
injection on the front end (it is also rejected in the application itself. The
  restrictions are as follows:
  * First and last name: must only contain letters
  * Email: must be formatted as an email with the appropriate characters, @ symbol
  appropriately placed, et cetera
  * Address: must be formatted as an address with only alphanumeric characters plus
  white space, commas and dashes
  * Phone: only numbers, dashes and parentheses, formatted as shown on the page
  * SSN: only numbers and dashes, formatted as shown on the page
  * Password: only alphanumeric characters and underscores

### Portfolio:
The user may select portfolios from the drop down menu. They may add bank
accounts, restricting ABA numbers to 8 numerical digits and Account numbers to
10 numerical digits. Users may transfer funds between their bank accounts and
portfolios and buy stocks with the money in their portfolios, as long as the
funds in the portfolio do not go below 0.

### Profile:
Users may update their profiles with new information if they choose (all formats
are the same as in the Add User section). They may also add more bank accounts
in this section. Users may delete their accounts as long as at least one bank
account is set with direct deposit so that the application will return the money
once the user deletes their account.

### Transactions:
Users can only transfer cash out of an account or buy stocks if they have enough
funds to do so, they can always short stock or transfer funds in as these aggregate
cash to the accounts. In case there is not enough cash the user will be prompted
to sell stocks or fund their portfolio with cash.

## Queries:
The following complex queries are used:
* Calculating net value of a portfolio by netting out buy and sale transactions
for a specific user for a specific portfolio with all cash transactions in and out
of that portfolio and calculating the current value of the stocks remaining.
* Calculating whether the user can execute a transaction by verifying whether the
value of the transaction is over the current funds of the portfolio
* Verifying whether a specific user has direct deposit set up on at least one of
their accounts

## Use cases:
* Log into existing account
* View portfolio
* Create Account
* Log into account
* Create portfolio
* Try to buy without funding
* Fund portfolio
* Buy stocks
* Sell Stocks
* Delete account

## Diferences from proposal:
There are two differences:
* The cash value of a portfolio is calculated by netting stock purchases and sales
with cash transactions (in and out from bank accounts) instead of being statically maintained in a table
* The stock transactions table does not have separate columns for buys and sales,
instead sales are indicated by a negative share amount - which is more syntactically
consistent with the process of regular sales and short stock sales.
