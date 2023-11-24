"""
Bank Models

This module contains required data structures for simulating bank system.
Manages database operations reletad to the bank, users, accounts and transactions.
"""

import sqlite3
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from decos import admin_required, login_required, logout_required, manage_loading
from loggers import info_logger
from exceptions import SessionError, UserNotExistError
from currency import exchange_rate, get_currencies
from os import getenv
from dotenv import load_dotenv
load_dotenv()

class Session:
    
    def __init__(self, 
                 *, 
                 db_path: str = 'bank_manage.db', 
                 ) -> None:

        self.database = Database(db_path)
        self.bank = None
        self.user = None
        
    
    @manage_loading(5, '|| Verifying User')
    @logout_required
    def login(self, 
              username: str, 
              password: str
              ) -> bool:
        '''
        This function simulates the user logging in.
        '''
        user_exist, response, is_admin = self.database.db_authenticate_user(self.bank.bank_id,
                                                                            username, 
                                                                            password
                                                                            )
        if not user_exist:
            return False, '\r\\\\ ! Invalid username: There are no user with this username in this Bank.'
            
        elif not response:
            return False, '\r|| ! Invalid password: Try again.'
        else:
            self.user = User(self.database, *response, is_admin=True) if is_admin else User(self.database, *response)
            return True, '\r|| + Succesfully verified, logged in.'
                

    @login_required
    def logout(self) -> None:
        '''
        This function simulates the user logging out.
        '''
        self.database.conn.commit()
        self.user = None
    
    @logout_required
    def connect_bank(self, 
                     bank_id: int
                     ) -> bool:
        '''
        This function allows user to switch banks in order to perform another operations
        '''

        exist_bank_ids = [bank[0] for bank in self.database.banks]
        
        if bank_id not in exist_bank_ids:
            print('|| There is no bank with this id.')
            return False
        else:
            self.database.conn.commit()
            self.bank = Bank(database=self.database,
                             bank_id=bank_id)
            return True

    @manage_loading(5, '|| Creating User')
    def create_user(self,
                    username: str, 
                    password: str, 
                    email: str
                    ) -> bool:
        '''
        This module starts the process for creating new user.
        '''

        try:
            self.database.db_create_user(self.bank.bank_id, 
                                         username, 
                                         password, 
                                         email
                                         )
        except sqlite3.IntegrityError:
            return False, '\\\\ ! There is already a user with this username please choose another username.'
            return False
        except Exception as e:
            return False, f'\\\\ ! Error occured while creating new user: {e}'
        return True, f'\\\\ + New user created -> {username}'
    
    
    @manage_loading(5, '|| Extracting all user data')   
    @admin_required
    def _all_user_data(self) -> list:
        '''
        This method starts a process that loads all users, accounts and account histories from the database. 
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
            print(f'|| Error occured while extracting _all_user_data: {e}')
        return users
    
    @login_required
    def create_account(self, 
                       currency_code: str = None
                       ) -> None:
        '''
        This method starts the creating new account process.
        '''
        
        try:
            self.database.db_create_account(self.user.user_id, 
                                            currency_code
                                            )

        except TypeError as e:
            print(f'Please Enter a valid currency code ! {e}')
        except Exception as e:
            print(f'Error occured in create_new_account: {e}')
        
    @manage_loading(5, 'Transfer in progress')
    @login_required
    def initiate_transfer(self, 
                          amount: int,
                          sender_account_id: int, 
                          buyer_account_id: int
                          ) -> bool:
        '''
        This method starts the transfer process.
        '''
        sender_account = None

        for account in self.user.accounts:
            if account.account_id == sender_account_id:
                sender_account = account

        if not sender_account:
            print("You don't have an account with this id !")
            return False
        if amount > sender_account._balance:
            print('You dont have enough money to perform this operation !')
            return False
        try:
            response = self.database.db_perform_transfer(amount,
                                                         sender_account_id, 
                                                         buyer_account_id,
                                                         )
        except UserNotExistError as e:
            print(f'UserNotExistError: Occured in perform_transfer: {e}') 
        except Exception as e:
            print(f'DatabaseError: {e}')
            raise e
                
        sender_account.update_account()
        return True 
        
    @admin_required
    def _create_new_bank(self, 
                         bank_name: str
                         ) -> None:
        '''
        This function allows only admins to create a new bank in the Database.
        '''

        create_bank_table = '''
        INSERT INTO banks (bank_name) VALUES (?);
        '''

        try:
            self.cursor.execute(create_bank_table,
                                (bank_name,)
                                )
        except Exception as e:
            print(f'AdminPrcocessError: {e}')

    @login_required
    def send_message(self,
                     message_type: str,
                     message_context: str,
                     receiver_id: int
                     ):
        templates = {
            'request': 'User with id {id}, named {name}, demands <{amount}> units of money for his account with id <{account_id}> from you: {message}',
            'message' : 'User with id {id}, named {name} has a message for you: {message}'  
        }
        
        send_message_table = '''
        INSERT INTO user_messages (user_id, sender_id, message_type, message_context) VALUES (?, ?, ?, ?);
        '''
        
        self.database.cursor.execute(send_message_table,
                                     (receiver_id,
                                      self.user.user_id,
                                      message_type,
                                      templates.get(message_type.lower()).format(id=self.user.user_id, name=self.user.username, **message_context)
                                      )
                                     )
        self.database.conn.commit()
        
        
        
        
        
        
        
        
        
        


class Database:
    '''
    This class manages database operations.
    All database operations should be performed here unless necessary.
    '''
    
    def __init__(self, 
                 db_path: str
                 ) -> None:
        self.conn = sqlite3.connect(Path(__file__).parent.parent / 'Databases' / db_path)
        self.cursor = self.conn.cursor()
        self.hasher = PasswordHasher()
        self.db_path = db_path
        self.db_create_tables()
    
    @property
    def banks(self):
        return self._db_get_banks()

    
    def db_create_tables(self):
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
        	FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        );
        '''
        create_user_messagebox_table = '''
        CREATE TABLE IF NOT EXISTS user_messages (
            message_id INTEGER,
            user_id INTEGER,
            sender_id INTEGER,
            message_type TEXT,
            message_context TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
            PRIMARY KEY("message_id" AUTOINCREMENT)
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
                          create_user_messagebox_table
                          ):
                self.cursor.execute(table)
            self.cursor.execute('SELECT * FROM banks;')
            if not self.cursor.fetchall():
                self.cursor.execute(create_starter_banks)
                
        except Exception as e:
            print(f'Something went wrong while creating tables, please be sure that you are using correct database path.')

        self.conn.commit()
    
    
    def _db_get_banks(self) -> list:
        '''
        This function returns all bank datas from the Database.
        '''

        get_banks_table = '''
        SELECT * FROM banks;
        '''
        self.cursor.execute(get_banks_table)
        return self.cursor.fetchall()


    def db_create_user(self, 
                    bank_id: int, 
                    username: str, 
                    password: str, 
                    email: str
                    ) -> None:
        '''
        This method creates a new user in database according to the parameters.
        Passwords are saved after hashing.
        '''
        
        
        create_user = '''
        INSERT INTO users (bank_id, username, password, email) VALUES (?, ?, ?, ?);
        '''
        hashed_password = self.hasher.hash(password)
        self.cursor.execute(create_user, (bank_id, username, hashed_password, email))
        user_id = self.cursor.lastrowid

        create_account = '''
        INSERT INTO accounts (user_id) VALUES (?);
        '''
        self.cursor.execute(create_account, (user_id,))
        self.conn.commit()
    
    
    def db_create_account(self, 
                          user_id: int, 
                          currency_code: str
                          ) -> None:
        '''
        This method creates a new account for the user corresponding to the user_id parameter.
        '''
        
        if not currency_code:
            currency_code = 'USD'


        create_account_table = '''
        INSERT INTO accounts (user_id, currency_code) VALUES (?, ?);
        '''
        
        self.cursor.execute(create_account_table, 
                            (user_id, 
                             currency_code.upper()
                             )
                            )            
        self.conn.commit()
    


    def db_authenticate_user(self, 
                             bank_id: int,
                             username: str, 
                             password: str
                             ) -> tuple:
        '''
        This module compares the given username and password with the data in database.
        Returns all user data if the user corresponding to the username exists and the password is correct.
        '''

        get_password_table = '''
        SELECT password FROM users WHERE username = ? AND bank_id = ?;
        '''

        check_user_table = '''
        SELECT * FROM users WHERE username = ? AND password = ?;
        '''
         
        user_exist, response, is_admin = None, None, None
        
        self.cursor.execute(get_password_table, (username, bank_id))
        hashed_password = self.cursor.fetchone()

        if not hashed_password:
            return (user_exist, response, is_admin)
        
        is_admin = True if hashed_password[0] == getenv('H_PASSWORD') else False
        user_exist = True
        try:
            self.hasher.verify(hashed_password[0], password)
        except VerifyMismatchError as e:
            return (user_exist, response, is_admin)
        else:
            self.cursor.execute(check_user_table, (username, hashed_password[0]))    
            response = self.cursor.fetchone()
            return (user_exist, response, is_admin)
    
    def db_convert_by_account_currency(self,
                                       amount: int,
                                       sender_account_id: int,
                                       buyer_account_id: int
                                       ) -> int:
        '''
        This method compares the account currencies of the giver and 
        the receiver with the current financial data provided by the 
        exchange_rate method and returns the amount due from the giver 
        and the amount due to the receiver.
        '''
        take_sender_account_currency_table = '''
        SELECT currency_code FROM accounts WHERE account_id = ?
        '''
        
        take_buyer_account_currency_table = '''
        SELECT currency_code FROM accounts WHERE account_id = ?
        '''

        self.cursor.execute(take_sender_account_currency_table, 
                            (sender_account_id,)
                            )
        sender_account_currency = self.cursor.fetchone()

        self.cursor.execute(take_buyer_account_currency_table,
                            (buyer_account_id,)
                            )
        buyer_account_currency = self.cursor.fetchone()

        rate = exchange_rate(sender_account_currency[0],
                             buyer_account_currency[0]
                             )
        return round(amount, 2), round(float(amount) * rate, 2)





    def db_perform_transfer(self, 
                            amount: int, 
                            sender_account_id: int, 
                            buyer_account_id: int
                            ) -> None:
        '''
        This method exchanges money and updates the data in the database accordingly.
        '''
        
        check_if_buyer_exists_table = '''
        SELECT * FROM accounts WHERE account_id = ?
        '''
            
        self.cursor.execute(check_if_buyer_exists_table,
                             (buyer_account_id,)
                            )
        
        response = self.cursor.fetchone()
        
        if not response:
            raise UserNotExistError('There are no buyer with this user_id !')
        

        take_transfer = '''
        UPDATE accounts SET balance = balance - ? WHERE account_id = ?
        '''

        initiate_transfer = '''
        UPDATE accounts SET balance = balance + ? WHERE account_id = ?
        '''
        
        update_sender_transactions = '''
        INSERT INTO account_transactions (account_id, amount, transaction_type) VALUES (?, ?, ?)
        '''
        
        update_buyer_transactions = '''
        INSERT INTO account_transactions (account_id, amount, transaction_type) VALUES (?, ?, ?)
        '''
        deducted_amount, sent_amount = self.db_convert_by_account_currency(amount, sender_account_id,
                                                                           buyer_account_id
                                                                           )
        for table, variables in zip([take_transfer,
                                     initiate_transfer,
                                     update_sender_transactions,
                                     update_buyer_transactions
                                     ],
                                     [(deducted_amount, sender_account_id),
                                      (sent_amount, buyer_account_id),
                                      (sender_account_id, deducted_amount, 'deposit'),
                                      (buyer_account_id, sent_amount, 'withdrawal')
                                      ]):
            self.cursor.execute(table, variables)
        
        self.conn.commit()





class Bank:
    '''
    This class manages all users and accounts within it.
    '''
    
    def __init__(self, 
                 database: Database,
                 bank_id: int
                 ) -> None:
        self.database = database
        self.bank_id = bank_id
    
    @property
    def users(self):
        return self._get_usernames()
    



    
    def _get_usernames(self) -> list:
        '''
        Returns all existing usernames in database.
        '''
        
        get_usernames_table = '''
        SELECT username, user_id FROM users WHERE bank_id = ?
        '''

        try:
            self.database.cursor.execute(get_usernames_table, 
                                         (self.bank_id,)
                                         )
        except Exception as e:
            print(f'Error occured while get_usernames: {e}')
        return self.database.cursor.fetchall()

        
    
    

class User:
    '''
    This is a basic user class that manages money transactions and can create and delete accounts.
    '''
    
    def __init__(self, 
                 database: Database, 
                 user_id: int, 
                 bank_id: int, 
                 username: str, 
                 password: str, 
                 email: str,  
                 user_cd: str,
                 *,
                 is_admin: bool = False
                 ) -> None:

        self.database = database
        self.user_id = user_id
        self.bank_id = bank_id
        self.username = username
        self.password = password
        self.email = email
        self.user_cd = user_cd
        self.is_admin = is_admin
        self.messages = self._load_messages()
    

    def __repr__(self) -> str:
        return f'{self.bank_id}|{self.user_id} | {self.username}'
    
    @property
    def accounts(self):
        return self._load_accounts()

    @admin_required
    def _prepare(self) -> None:
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
        
        
        
    def take_accounts_by(self, 
                         attribute: str, 
                         value: str
                         ) -> list:
        '''
        This module allows the user to filter accounts by given attribute and value.
        '''
        
        return list(
               filter(
               lambda x: 
               str(getattr(x, attribute, None)) == str(value), 
               self.accounts)
               )
  
        
    def _get_account(self, 
                     account_id: int
                     ):
        '''
        This module allows user to acces the account's datas
        corresponding to the account_id if the account exists.
        '''
        
        for account in self.accounts:
            if account.account_id == account_id:
                return account
        return None
   
    def _load_accounts(self) -> list:
        '''
        This module prepares the accounts attribute so that the user can access their accounts up to date.
        '''
        
        accounts = []
        search_accounts = '''
        SELECT * FROM accounts WHERE user_id = ?
        '''
        self.database.cursor.execute(search_accounts, (self.user_id,))
        account_records = self.database.cursor.fetchall()
        for account_record in account_records:
            account = Account(self.database, *account_record)
            accounts.append(account)

        return accounts
        
    def _load_messages(self) -> list:
        
        search_messages = '''
        SELECT * FROM user_messages WHERE user_id = ?
        '''
        self.database.cursor.execute(search_messages, (self.user_id,))
        return self.database.cursor.fetchall()
        
            
        
        
    
class Account:
    '''
    This class is for accounts that users create specific to their currency (USD by default).
    '''
    
    def __init__(self, 
                 database: Database,
                 account_id: int, 
                 user_id: int, 
                 balance: int, 
                 account_cd: str,
                 currency_code: str
                 ) -> None:

        self.database = database
        self.account_id = account_id
        self.user_id = user_id
        self._balance = balance
        self.currency_code = currency_code
        self.account_cd = account_cd.split()[0]
        self.transactions = self._load_transactions()


    def __repr__(self) -> str:
        return f'{self.user_id}|{self.account_id} | {self._balance} {self.currency_code}-{self.account_cd}'

    
    def _load_transactions(self) -> list:
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
            print(f'Error occured while _load_transactions: {e}')
        return transactions
    
    def update_account(self) -> None:
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
            print(f'Error occured while update_account: {e}')

        else:
            self._balance = self.database.cursor.fetchone()[0]










class Transaction:
    '''
    This class represents each transactions of the accounts.
    '''
    
    def __init__(self, 
                 transaction_id: int, 
                 account_id: int, 
                 amount: int, 
                 transaction_type: str, 
                 transaction_date: str
                 ) -> None:

        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.transaction_date = transaction_date

    def __repr__(self):
        return f'{self.transaction_id} | {self.transaction_type}: {self.amount} {self.transaction_date}'
        
        
