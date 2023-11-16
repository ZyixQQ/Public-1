"""
Bank Models

This module contains required data structures for simulating bank system.
Manages database operations reletad to the bank, users, accounts and transactions.
"""

import sqlite3
from argon2 import PasswordHasher
from decos import admin_required



class Database:
    '''
    This class manages database operations.
    All database operations should be performed here unless necessary.
    '''
    
    def __init__(self, 
                 db_path
                 ):
        self.conn = sqlite3.connect(rf'..\Databases\{db_path}')
        self.cursor = self.conn.cursor()
        self.hasher = PasswordHasher()
        self.create_tables()

    
    def create_tables(self):
        '''
        This method creates required tables and applies initial actions.
        '''
        
        create_banks_table = '''
        CREATE TABLE IF NOT EXISTS "banks" (
        	"bank_id"	INTEGER,
	        "bank_name"	TEXT NOT NULL UNIQUE,
        	PRIMARY KEY("bank_id" AUTOINCREMENT)
        );
        '''
        
        create_users_table = '''
        CREATE TABLE IF NOT EXISTS "users" (
        	"user_id"	INTEGER,
        	"bank_id"	INTEGER,
        	"username"	TEXT NOT NULL UNIQUE,
        	"password"	TEXT NOT NULL,
        	"email"	TEXT NOT NULL,
        	'user_cd' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        	FOREIGN KEY("bank_id") REFERENCES "banks"("bank_id"),
        	PRIMARY KEY("user_id" AUTOINCREMENT)
        );
        '''

        create_accounts_table = '''
        CREATE TABLE IF NOT EXISTS "accounts" (
	        "account_id"	INTEGER,
        	"user_id"	INTEGER,
    	    "balance"	REAL DEFAULT 0.0,
    	    "account_cd"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "currency_code" TEXT DEFAULT 'USD',
	        FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
        	PRIMARY KEY("account_id" AUTOINCREMENT)
        );
        '''

        create_account_transaction_table = '''
        CREATE TABLE IF NOT EXISTS account_transactions (
        	transaction_id INTEGER PRIMARY KEY,
        	account_id INTEGER,
        	amount DECIMAL(10, 2),
        	transaction_type VARCHAR(50) NOT NULL,
        	transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        	FOREIGN KEY (account_id)  REFERENCES accounts(account_id)
        );
        '''
        
        create_starter_banks = '''
        INSERT INTO banks (bank_name) VALUES ('Bank1'), ('Bank2'), ('Bank3');
        '''
        try:
            for table in (create_banks_table,
                          create_users_table,
                          create_accounts_table,
                          create_account_transaction_table,
                          ):
                self.cursor.execute(table)
            self.cursor.execute('SELECT * FROM banks;')
            if not self.cursor.fetchall():
                self.cursor.execute(create_starter_banks)
                
        except Exception as e:
            raise e

        self.conn.commit()
    

        
    def _hash_password(self, password):
        return self.hasher.hash(password)
        

    def create_user(self, 
                     bank_id, 
                     username, 
                     password, 
                     email
                     ):
        '''
        This method creates a new user in database according to the parameters.
        Passwords are saved after hashing.
        '''
        
        create_user = '''
        INSERT INTO users (bank_id, username, password, email) VALUES (?, ?, ?, ?);
        '''
        hashed_password = self._hash_password(password)
        self.cursor.execute(create_user, (bank_id, username, hashed_password, email))
        user_id = self.cursor.lastrowid

        create_account = '''
        INSERT INTO accounts (user_id) VALUES (?);
        '''
        self.cursor.execute(create_account, (user_id,))
        self.conn.commit()
    
    def create_new_account(self, 
                           user_id, 
                           currency_code
                           ):
        '''
        This method creates a new account for the user corresponding to the user_id parameter.
        '''
        
        if not currency_code:
            currency_code = 'USD'
        create_account_table = '''
        INSERT INTO accounts (user_id, currency_code) VALUES (?, ?);
        '''
        
        try:
            self.cursor.execute(create_account_table, 
                                         (user_id, 
                                          currency_code
                                          )
                                         )
            
        except Exception as e:
            print(e)
        self.conn.commit()
        return 0
    
    def authanticate_user(self, 
                          username, 
                          password
                          ):
        '''
        This module compares the given username and password with the data in database.
        Returns all user data if the user corresponding to the username exists and the password is correct.
        '''

        get_password_table = '''
        SELECT password FROM users WHERE username = ?;
        '''

        check_user_table = '''
        SELECT * FROM users WHERE username = ? AND password = ?;
        '''
        
         

        try:
            self.cursor.execute(get_password_table, (username,))
            hashed_password = self.cursor.fetchone()[0]
            self.hasher.verify(hashed_password, password)
            self.cursor.execute(check_user_table, (username, hashed_password))
        except Exception as e:
            print(e)
        response = self.cursor.fetchone()
        if response:
            return response
        else:
            return

    def perform_transfer(self, 
                         amount, 
                         sender_id, buyer_id,
                         sender_account_id, buyer_account_id
                         ):
        '''
        This method exchanges money and updates the data in the database accordingly.
        '''
        
        check_if_buyer_exists_table = '''
        SELECT * FROM accounts WHERE user_id = ? AND account_id = ?
        '''
        
        self.cursor.execute(check_if_buyer_exists_table,
                            (buyer_id,
                             buyer_account_id
                             )
                            )
        
        response = self.cursor.fetchone()
        
        if not response:
            raise ValueError('There are no buyer with this ids')
            return 1
        
        take_transfer = '''
        UPDATE accounts SET balance = balance - ? WHERE user_id = ?
        '''

        initiate_transfer = '''
        UPDATE accounts SET balance = balance + ? WHERE user_id = ?
        '''
        
        update_sender_transactions = '''
        INSERT INTO account_transactions (account_id, amount, transaction_type) VALUES (?, ?, ?)
        '''
        
        update_buyer_transactions = '''
        INSERT INTO account_transactions (account_id, amount, transaction_type) VALUES (?, ?, ?)
        '''
        
        try:
            for table, variables in zip([take_transfer,
                                         initiate_transfer,
                                         update_sender_transactions,
                                         update_buyer_transactions
                                         ],
                                        [(amount, sender_id,),
                                         (amount, buyer_id,),
                                         (sender_account_id, amount, 'deposit'),
                                         (buyer_account_id, amount, 'withdrawal')
                                         ]):
                self.cursor.execute(table, variables)
        except Exception as e:
            print(e)
        self.conn.commit()
        return 0





class Bank:
    '''
    This class manages all users and accounts within it.
    '''
    
    def __init__(self, 
                 database,
                 bank_id
                 ):
        self.database = database
        self.bank_id = bank_id
        self.users = self.get_usernames()
    
    def _load_all_users(self):
        '''
        This method starts a process that loads all users, accounts and account histories in the database. 
        It is set for development process and controls.
        '''
        
        users = []
        search_users = '''
        SELECT * FROM users WHERE bank_id = ?
        '''
        try:
            self.database.cursor.execute(search_users, (self.bank_id,))
            user_records = self.database.cursor.fetchall()
            for user_record in user_records:
                user = User(self.database, *user_record)
                user._load_accounts()
                users.append(user)
        except Exception as e:
            print(e)
        return users
    
    def get_usernames(self):
        '''
        Returns all existing usernames in database.
        '''
        
        get_usernames_table = '''
        SELECT username FROM users WHERE bank_id = ?
        '''

        try:
            self.database.cursor.execute(get_usernames_table, 
                                         (self.bank_id,)
                                         )
        except sqlite3.IntegrityError as e:
            print(e)
        except Exception as e:
            print(e)
        return self.database.cursor.fetchall()

    
    def check_user(self, 
                   username, 
                   password
                   ):
        '''
        This module starts the process for user control.
        '''
        
        return self.database.authanticate_user(username,
                                               password
                                               )

    def create_new_user(self, 
                        username, 
                        password, 
                        email
                        ):
        '''
        This module starts the process for creating new user.
        '''
        
        self.database.create_user(self.bank_id, 
                                  username, 
                                  password, 
                                  email
                                  )
        return 0       
        
    
    

class User:
    '''
    This is a basic user class that manages money transactions and can create and delete accounts.
    '''
    
    def __init__(self, 
                 database, 
                 user_id, 
                 bank_id, 
                 username, 
                 password, 
                 email, 
                 user_cd,
                 *,
                 is_admin=False
                 ):
        self.database = database
        self.user_id = user_id
        self.bank_id = bank_id
        self.username = username
        self.password = password
        self.email = email
        self.user_cd = user_cd
        self.accounts = self._load_accounts()
        self.is_admin = is_admin
    
    def __repr__(self):
        return f'{self.bank_id}|{self.user_id} | {self.username}'
    
    
    def create_account(self, currency_code=None):
        '''
        This method starts the creating new account process.
        '''
        
        self.database.create_new_account(self.user_id, 
                                         currency_code
                                         )
        return 0
    
    @admin_required
    def _prepare(self):
        '''
        This method adds money to all accounts of a user.
        It is used for testing purposes and is not accessible to anyone other than authorized users.
        '''
        
        for account in self.accounts:
            self.database.cursor.execute('''
            UPDATE accounts SET balance = 1000 WHERE user_id = ?
            ''', 
            (self.user_id,)
            )
            
        self.database.conn.commit()
        return 0    
        
        
    def take_accounts_by(self, attribute, value):
        '''
        This module allows the user to filter accounts by given attribute and value.
        '''
        
        return list(
               filter(
               lambda x: 
               str(getattr(x, attribute, None)) == str(value), 
               self.accounts)
               )
  
        
    def get_accounts(self, account_id=None):
        '''
        This module allows user to acces the account's datas
        corresponding to the account_id if the account exists.
        '''
        
        account_search_table = '''
        SELECT * FROM accounts WHERE user_id = ?
        '''

        try:
            self.database.cursor.execute(account_search_table,
                                         (self.user_id,)
                                         )
        except Exception as e:
            print(e)
        
        found_accounts = self.database.cursor.fetchall()
        
        if account_id:
            for account in found_accounts:
                if account[0] == account_id:
                    return account
            return
        return found_accounts

    def _load_accounts(self):
        '''
        This module prepares the accounts attribute so that the user can access their accounts up to date.
        '''
        
        accounts = []
        search_accounts = '''
        SELECT * FROM accounts WHERE user_id = ?
        '''

        try:
            self.database.cursor.execute(search_accounts, (self.user_id,))
            account_records = self.database.cursor.fetchall()
            for account_record in account_records:
                account = Account(self.database, *account_record)
                accounts.append(account)
        except Exception as e:
            print(e)
        return accounts

class Account:
    '''
    This class is for accounts that users create specific to their currency (USD by default).
    '''
    
    def __init__(self, 
                 database,
                 account_id, 
                 user_id, 
                 balance, 
                 account_cd,
                 currency_code
                 ):
        self.database = database
        self.account_id = account_id
        self.user_id = user_id
        self._balance = balance
        self.currency_code = currency_code
        self.account_cd = account_cd.split()[0]
        self.transactions = self._load_transactions()

    def __repr__(self):
        return f'{self.user_id}|{self.account_id} | {self._balance} {self.currency_code}-{self.account_cd}'

    def _load_transactions(self):
        '''
        This module prepares the transactions attribute so that the accounts can access their transactions up to date.
        '''
        
        transactions = []

        search_transactions = '''
        SELECT * FROM account_transactions WHERE account_id = ?
        '''

        try:
            self.database.cursor.execute(search_transactions, (self.account_id,))
            transaction_records = self.database.cursor.fetchall()
            for transaction_record in transaction_records:
                transaction = Transaction(*transaction_record)
                transactions.append(transaction)
        except Exception as e:
             print(e)
        return transactions
    
    def update_account(self):
        '''
        This method updates the changed values in the database on the object after the transfer operations.
        '''
        
        get_balance_table = '''
        SELECT balance FROM accounts WHERE user_id = ? AND account_id = ?;
        '''

        try:
            self.database.cursor.execute(get_balance_table,
                                         (self.user_id,
                                          self.account_id
                                          )
                                         )
        except Exception as e:
            print(e)

        else:
            self._balance = self.database.cursor.fetchone()[0]
            return 0
        return 1



    def initiate_transfer(self, 
                          amount, 
                          buyer_id, 
                          buyer_account_id
                          ):
        '''
        This method starts the transfer process.
        '''
        
        if amount > self._balance:
            raise ValueError()
        request = self.database.perform_transfer(amount,
                                               self.user_id, buyer_id,
                                               self.account_id, buyer_account_id,
                                               )
        if request:
            self.update_account()
            return 0
        return 1






class Transaction:
    '''
    This class represents each transactions of the accounts.
    '''
    
    def __init__(self, 
                 transaction_id, 
                 account_id, 
                 amount, 
                 transaction_type, 
                 transaction_date
                 ):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.transaction_date = transaction_date

    def __repr__(self):
        return f'{self.transaction_id} | {self.transaction_type}: {self.amount} {self.transaction_date}'
        
        