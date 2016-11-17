CREATE TABLE users (
  uid integer,
  fname text not null,
  lname text not null,
  address text,
  phone text,
  ssn text not null,
  email text not null,
  password text not null,
  PRIMARY KEY (uid)
);

CREATE TABLE bank_accounts (
  bankaccountid integer,
  bankid text not null,
  accountid text not null,
  uid integer not null,
  direct_deposit boolean not null,
  PRIMARY KEY (bankaccountid),
  FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
);
CREATE TABLE portfolio(
  portfolioid  integer,
  uid  integer not null,
  PRIMARY KEY (portfolioid) ,
  FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
);

CREATE TABLE cash_transactions (
  transactionid integer,
  date Date not null,
  uid integer not null,
  bankaccountid integer not null,
  portfolioid integer not null,
  amount float not null,
  PRIMARY KEY (transactionid),
  FOREIGN KEY (portfolioid) REFERENCES portfolio(portfolioid) ON DELETE CASCADE,
  FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
  FOREIGN KEY (bankaccountid) REFERENCES bank_accounts(bankaccountid) ON DELETE CASCADE
);

CREATE TABLE us_stock(
  ticker  text,
  cname  text not null,
  current_price  float not null,
  exchange  text not null,
  PRIMARY KEY (ticker)
);

CREATE TABLE stock_transactions(
  stockid  integer,
  ticker  text not null,
  uid  integer not null,
  portfolioid  integer not null,
  shares  integer not null,
  open_position_price  float,
  open_date Date,
  PRIMARY KEY (stockid),
  FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
  FOREIGN KEY (portfolioid) REFERENCES portfolio(portfolioid) ON DELETE CASCADE,
  FOREIGN KEY (ticker) REFERENCES us_stock(ticker)
);
