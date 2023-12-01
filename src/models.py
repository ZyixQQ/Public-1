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
from re import findall, compile, match
load_dotenv()

class Session:
    
    def __init__(self, 
                 *, 
                 db_path: str = 'bank_manage.db', 
                 ) -> None:

        self.database = Database(db_path)
        self.bank = None
        self.user = None
        self.payload = {}

        
    
    # @manage_loading(5, '|| Verifying User')
    @logout_required
    def login(self, 
              username: str, 
              password: str
              ) -> bool:
        '''
        This function simulates the user logging in.
        '''
        try:
            user_exist, response, is_admin = self.database.db_authenticate_user(self.bank.bank_id,
                                                                            username, 
                                                                            password
                                                                            )
        except TypeError:
            input('|| ! Please make sure you entered connected a valid exist bank')
        if not user_exist:
            return False, '\r\\\\ ! Invalid username: There are no user with this username in this Bank.'
            
        elif not response:
            return False, '\r|| ! Invalid password: Try again.'
        else:
            self.user = User(self.database, *response, is_admin=True) if is_admin else User(self.database, *response)
            self.check_user_cache()
            return True, '\r|| + Succesfully verified, logged in.'
                

    @login_required
    def logout(self) -> None:
        '''
        This function simulates the user logging out.
        '''
        check_users_cache = '''
        SELECT * FROM user_cache WHERE user_id = ?
        '''
        update_user_cache_table = '''
        UPDATE user_cache SET message_count = ? WHERE user_id = ?;
        '''
        self.database.cursor.execute(update_user_cache_table,
                                (len(self.user.messages), self.user.user_id))                     
        self.database.conn.commit()
        self.user = None
    
    def check_user_cache(self):
        check_users_cache = '''
        SELECT message_count FROM user_cache WHERE user_id = ?
        '''
        
        get_last_transfer_table = '''
        SELECT * FROM user_messages WHERE user_id = ? AND message_id > ? AND message_type = ? ORDER BY message_id DESC;
        '''
        
        get_trasnfer_id_cache = '''
        SELECT last_transfer_id FROM user_cache WHERE user_id = ?;
        '''
        self.database.cursor.execute(check_users_cache,
                            (self.user.user_id,)
                            )
        message_count = self.database.cursor.fetchone()
        if not message_count:
            self.payload['message'] = ''
        elif message_count[0] < len(self.user.messages):
            self.payload['message'] = f'You have {len(self.user.messages) - message_count[0]} new message.'
        else:
            self.payload['message'] = ''

        
        
            
        
    
    @logout_required
    def connect_bank(self,  
                     bank_id: int
                     ) -> bool:
        '''
        This function allows user to switch banks in order to perform another operations
        '''
        
        if bank_id not in self.database.banks.keys():
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
            response = self.database.db_create_user(self.bank.bank_id, 
                                                    username, 
                                                    password, 
                                                    email
                                                    )
        except sqlite3.IntegrityError:
            return False, '\\\\ ! There is already a user with this username please choose another username.'
        except Exception as e:
            return False, f'\\\\ ! Error occured while creating new user: {e}'
            
        else:
            if response == True:
                return True, f'|| + New user created -> {username}'
            else:
                return False, f'|| ! {response[1]} does not meet requirements'
    
    
    @manage_loading(5, '|| Extracting all user data')   
    @admin_required
    def _all_user_data(self) -> list:
        '''
        This method starts a process that loads all users, accounts and account histories from the database. 
        It is set for development process and controls.
        '''
        
        users = []
        search_users = '''
        SELECT * FROM users WHERE bank_id = ?;
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
    

        
    #@manage_loading(5, '|| Transfer in progress')
    @login_required
    def initiate_transfer(self, 
                          amount: int,
                          sender_account_id: int, 
                          buyer_account_id: int,
                          send_feedback=False,
                          ) -> bool:
        '''
        This method starts the transfer process.
        '''
        get_buyer_id_table = '''
        SELECT user_id FROM accounts WHERE account_id = ?;
        '''
        
        sender_account = self.user.accounts.get(sender_account_id, None)


        if not sender_account:
            input("You don't have an account with this id !")
            return False
        if amount > sender_account._balance:
            input('You dont have enough money to perform this operation !')
            return False
        try:
            response = self.database.db_perform_transfer(amount,
                                                         sender_account_id, 
                                                         buyer_account_id,
                                                         )
        except UserNotExistError as e:
            input(f'UserNotExistError: Occured in perform_transfer: {e}') 
            return
        except Exception as e:
            input(f'DatabaseError: {e}')
            raise e
     
                
        if send_feedback:
            message = input('|| Enter the transfer message -> ')
            self.database.cursor.execute(get_buyer_id_table,
                                         (buyer_account_id,)
                                         )
            buyer_id = self.database.cursor.fetchone()[0]
            self.send_message('transfer',
                              dict(amount=amount,
                               currency_code=self.user.accounts.get(sender_account_id).currency_code,
                               account_id=buyer_account_id,
                               message=message
                               ),
                               buyer_id
                              )
        sender_account.update_account()     
        if buyer_account_id in self.user.accounts:
            self.user.accounts.get(buyer_account_id).update_account()
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
            'request': 'User with id <{id}>, named <{name}>, is requesting <{amount}-{currency_code}> for their account with id <{account_id}> from you. @Message: {message}',
            'message' : 'User with id <{id}> named <{name}> has a message for you. @Message: {message}',
            'transfer': 'User with id <{id}> named <{name}> transferred <{amount}-{currency_code}> to your account with id <{account_id}>. @Message: {message}',
            'reply': 'User with id <{id}> named <{name}> replied to your {message_type} with id <{message_id}>. @Message: {replied_message} @Message: {message}'
        }
        
        send_message_table = '''
        INSERT INTO user_messages (user_id, sender_id, sender_name, message_type, message_context) VALUES (?, ?, ?, ?, ?);
        '''
        
        self.database.cursor.execute(send_message_table,
                                     (receiver_id,
                                      self.user.user_id,
                                      self.user.username,
                                      message_type,
                                      templates.get(message_type.lower()).format(id=self.user.user_id, 
                                                                                 name=self.user.username, 
                                                                                 **message_context
                                                                                 )
                                      )
                                     )
        self.database.conn.commit()
    
    def send_reply(self, message_id, new_message):
        pattern = r'<(.*?)>'
        message = self.user.messages.get(message_id)
        message_text = message[-1].split('@Message:')

        replied_message = message_text[-1]
        receiver_id = int(findall(pattern, message_text[0])[0])
        
        reply_info = dict()
        
        reply_info = {
            'message_id': message_id,
            'replied_message': replied_message,
            'message': new_message,
            'message_type': message[4]
        }
        
        self.send_message('reply', reply_info, receiver_id)
                
        
        
        
        
        
    @login_required
    def extract_request_information(self, request_id):
        request_information = {}
        accepted_request = self.user.messages.get(request_id)
        message = accepted_request[-1]
        pattern = r'<(.*?)>'
        extracted_info = findall(pattern, message) 
        
        request_information['requestor_id'] = int(extracted_info[0])
        request_information['requestor_amount'] = int(extracted_info[2].split('-')[0])
        request_information['requestor_currency_code'] = extracted_info[2].split('-')[1]
        request_information['requestor_account_id'] = int(extracted_info[3])
        request_information['requestor_name'] = extracted_info[1]
        return request_information
        
    

    @login_required
    def accept_request(self, 
                       request_id, 
                       sender_account_id
                       ):       
        request_info = self.extract_request_information(request_id)
        sender_account = self.user.accounts.get(int(sender_account_id))
        sender_account_currency_code = sender_account.currency_code
        sender_account_balance = sender_account._balance
        
        if sender_account_currency_code != request_info.get('requestor_currency_code'):
            rate = exchange_rate(request_info.get('requestor_currency_code'),
                                 sender_account_currency_code)
            actual_amount = round(rate * float(request_info.get('requestor_amount')), 2)
        else:
            actual_amount = float(request_info.get('requestor_amount'))
        print('||>-----------------<')
        print(f'|| Requested Amount {actual_amount}-{sender_account_currency_code}')
        print(f'|| Account Balance {sender_account_balance}-{sender_account_currency_code}')
        if actual_amount > sender_account_balance:
            input('|| ! You dont have enough money.')
        else:
            decision = input('|| Are you sure you want to appect? (1 for accept): ')
            if decision == '1':
                message = input('|| Enter an acceptance message -> ')
                self.initiate_transfer(actual_amount,
                                       sender_account_id,
                                       request_info.get('requestor_account_id'))
                self.user.delete_messages([request_id])
                self.send_feedback(request_info.get('requestor_id'), 
                                   request_id,
                                   request_info, 
                                   message,
                                   acceptance_status=True
                                   )
                    

            
    @login_required
    def reject_request(self, request_id):
        request_info = self.extract_request_information(request_id)
        message = input('|| Enter a rejection message -> ')
        self.send_feedback(request_info.get('requestor_id'),
                           request_id,
                           request_info,
                           message,
                           acceptance_status=False
                           )
        self.user.delete_messages([request_id])
        
        
        
    @login_required                      
    def send_feedback(self, receiver_id, request_id, request_info, message, acceptance_status):
        send_feedback_table = '''
        INSERT INTO user_messages (user_id, sender_id, sender_name, message_type, message_context) VALUES (?, ?, ?, ?, ?);
        '''

        feedback_template = {
            True: 'Your request worth {amount}-{currency_code} with {request_id} id has been accepted by {sender_name} with id <{sender_id}>. @Message: {message}',
            False: 'Your request worth {amount}-{currency_code} with {request_id} id has been rejected by {sender_name} with id <{sender_id}>. @Message: {message} '
        }
        self.database.cursor.execute(send_feedback_table,
                                     (receiver_id,
                                      self.user.user_id,
                                      self.user.username,
                                      'feedback',
                                      feedback_template.get(acceptance_status).format(amount=request_info.get('requestor_amount'),
                                                                                      currency_code=request_info.get('requestor_currency_code'),
                                                                                      request_id=request_id,
                                                                                      sender_name=self.user.username,
                                                                                      sender_id=self.user.user_id,
                                                                                      message=message
                                                                                      )
                                        )
                                       )
                                       
        self.database.conn.commit()                      
                                      
                                      
    def _delete_current_user(self):
        delete_user_from_db_table = '''
        DELETE FROM users WHERE user_id = ?;
        '''
        
        delete_user_messages_table = '''
        DELETE FROM user_messages WHERE user_id = ?;
        '''
        
        delete_user_accounts_table = '''
        DELETE FROM accounts WHERE user_id = ?;
        '''
        
        delete_user_cache_table = '''
        DELETE FROM user_cache WHERE user_id = ?;
        '''
        
        
        for table in (delete_user_cache_table,
                      delete_user_accounts_table,
                      delete_user_messages_table,
                      delete_user_from_db_table
                      ):
            self.database.cursor.execute(table,
                                         (self.user.user_id,)
                                         )
        self.database.conn.commit()
        self.logout()

        
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
        self.message_types = {'1': 'message', '2': 'request'}
        self.db_create_tables()
    
    @property
    def banks(self):
        bank_dict = {bank[0]: bank[1] 
                     for bank 
                     in self._db_get_banks()}
        return bank_dict
    
    def _validate_username(self, username):
        '''\
        Username Requirements:
           # At least 4 chracthers
           # At least 1 letter
           # Should start with a letter
        '''
        pattern = r'^[a-zA-Z]\S{2,}$'
        return bool(match(pattern, username))
        
        
            
    def _validate_password(self, password):
        '''\
        Password Requirements:
           # At least 8 chrachters
           # At least 1 lowercase letter
           # At least 1 uppercase letter
           # At least 1 number
        '''
        pattern = compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()-_=+[\]{}|;:\'",.<>?/]).{8,}$')
        return bool(match(pattern, password))
    
    def _validate_email(self, email):
        '''\
        Email Requirements:
           # Only @ and . characters can be used.
           # It must not contain gaps.
           # Domain extension must be at least 2 letters
           # example: username@email_provider.domain_extension
        '''
        
        pattern = compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(match(pattern, email))
        
        
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
            sender_name TEXT,
            message_type TEXT,
            message_cd TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_context TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
            PRIMARY KEY("message_id" AUTOINCREMENT)
        );
        '''
        create_starter_banks = '''
        INSERT INTO banks (bank_name) VALUES ('Bank1'), ('Bank2'), ('Bank3');
        '''
        create_user_cache_table = '''
        CREATE TABLE IF NOT EXISTS user_cache (
            user_id INTEGER,
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        '''
        try:
            for table in (create_banks_table,
                          create_users_table,
                          create_accounts_table,
                          create_account_transaction_table,
                          create_user_messagebox_table,
                          create_user_cache_table
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
        
        if self._validate_username(username) == False:
            return False, 'username'
        elif self._validate_password(password) == False:
            return False, 'password'
        elif self._validate_email(email) == False:
            return False, 'email'
        
        create_user = '''
        INSERT INTO users (bank_id, username, password, email) VALUES (?, ?, ?, ?);
        '''
        hashed_password = self.hasher.hash(password)
        self.cursor.execute(create_user, (bank_id, username, hashed_password, email))
        user_id = self.cursor.lastrowid

        create_account = '''
        INSERT INTO accounts (user_id) VALUES (?);
        '''
        
        create_cache = '''
        INSERT INTO user_cache (user_id) VALUES (?);
        '''
        self.cursor.execute(create_account, (user_id,))
        self.cursor.execute(create_cache, (user_id,))
        self.conn.commit()
        return True
    
    
    def db_create_account(self, 
                          user_id: int, 
                          currency_code: str
                          ) -> None:
        '''
        This method creates a new account for the user corresponding to the user_id parameter.
        '''
        
        create_account_table = '''
        INSERT INTO accounts (user_id, currency_code) VALUES (?, ?);
        '''

        if not currency_code:
            currency_code = 'USD'
            
        self.cursor.execute(create_account_table,
                            (user_id, currency_code)
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

        if buyer_account_currency != sender_account_currency:
            rate = exchange_rate(sender_account_currency[0],
                                buyer_account_currency[0]
                                )
        else:
            rate = 1
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
        SELECT user_id FROM accounts WHERE account_id = ?
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
        self.bank_name = self.database.banks.get(self.bank_id, None)
    
    @property
    def users(self):
        return self._get_usernames()
    
   
    def _get_usernames(self) -> list:
        '''
        Returns all existing usernames in database.
        '''
        
        get_usernames_table = '''
        SELECT user_id, username FROM users WHERE bank_id = ?
        '''

        try:
            self.database.cursor.execute(get_usernames_table, 
                                         (self.bank_id,)
                                         )
        except Exception as e:
            print(f'Error occured while get_usernames: {e}')
        return self.database.cursor.fetchall()
    
    def does_user_exist(self, user_id):
        check_user_exist_table = '''
        SELECT * FROM users WHERE user_id = ?;
        '''
        
        self.database.cursor.execute(check_user_exist_table,
                            (user_id,)
                            )
        
        return self.database.cursor.fetchone() != None
        
    def does_account_exist(self, account_id):
        check_account_exist_table = '''
        SELECT * FROM accounts WHERE account_id = ?;
        '''
        
        self.database.cursor.execute(check_account_exist_table,
                                     (account_id,)
                                     )
        return self.database.cursor.fetchone() != None
        
        
        
    
    

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
        self.accounts = self._load_accounts() 
        self.messages = self._load_messages()

    

    def __repr__(self) -> str:
        return f'{self.bank_id:<4} || {self.user_id:<8} || {self.username}'
    

    @admin_required
    def _prepare(self) -> None:
        '''
        This method adds money to all accounts of a user.
        It is used for testing purposes and is not accessible to anyone other than authorized users.
        '''
        
        for account in self.accounts.values():
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
               self.accounts.values())
               )
  
        
    
    def _load_accounts(self) -> list:
        '''
        This module prepares the accounts attribute so that the user can access their accounts up to date.
        '''
        
        accounts = {}
        search_accounts = '''
        SELECT * FROM accounts WHERE user_id = ?
        '''
        self.database.cursor.execute(search_accounts, (self.user_id,))
        account_records = self.database.cursor.fetchall()
        for account_record in account_records:
            account = Account(self.database, *account_record)
            accounts[account.account_id] = account

        return accounts
        
    def _load_messages(self) -> list:
        
        search_messages = '''
        SELECT * FROM user_messages WHERE user_id = ?
        '''
        self.database.cursor.execute(search_messages, (self.user_id,))
        message_dict = {message[0]: message for message in self.database.cursor.fetchall()}
        return message_dict
        
    def delete_messages(self, message_ids):
        delete_message_table = '''
        DELETE FROM user_messages WHERE message_id = ?;
        '''
        for message_id in message_ids:
            self.database.cursor.execute(delete_message_table,
                                        (message_id,)
                                        )
            del self.messages[message_id]
        self.database.conn.commit()
        
    def change_profile_attribute(self, 
                                 new_attribute, 
                                 *,
                                 type: str
                                 ):
        change_tables = {
            'name': (self.database._validate_username, 'UPDATE users SET username = ? WHERE user_id = ?;'),
            'email': (self.database._validate_email, 'UPDATE users SET email = ? WHERE user_id = ?;')
        }

        validator, table = change_tables.get(type)

        if validator(new_attribute) == False:
            return False

        self.database.cursor.execute(table, 
                                     (new_attribute,
                                      self.user_id
                                      )
                                     )
        self.database.conn.commit()
        if type == 'name':
            self.username = new_attribute
        elif type == 'email':
            self.email = new_attribute

        


    def change_account_currency(self, account_id, new_currency_code):   
        account = self.accounts.get(account_id)
        current_currency = account.currency_code
        
        if account._balance > 1:
            rate = exchange_rate(current_currency, new_currency_code)
            new_balance = round(rate * float(account._balance), 2)
            account._balance = new_balance    
        
        
        account.currency_code = new_currency_code
        
        change_account_currency_table = '''
        UPDATE accounts SET currency_code = ?, balance = ? WHERE account_id = ?
        '''
        
        self.database.cursor.execute(change_account_currency_table,
                                     (new_currency_code, account._balance, account_id)
                                     )
        self.database.conn.commit()
    
    def create_account(self, 
                       currency_code: str = None
                       ) -> None:
        '''
        This method starts the creating new account process.
        '''
        
        get_account_information_table = '''
        SELECT * FROM accounts WHERE user_id = ? ORDER BY ROWID DESC LIMIT 1;
        '''

        if len(self.accounts) == 5:
            raise ValueError('Reached the account limit')
        try:
            self.database.db_create_account(self.user_id, 
                                            currency_code
                                            )
        except Exception as e:
            print(f'Error occured in create_new_account: {e}')
        else:
            self.database.cursor.execute(get_account_information_table,
                                         (self.user_id,)
                                         )
            account_info = self.database.cursor.fetchone()
            new_account = Account(self.database, *account_info)
            self.accounts[new_account.account_id] = new_account

            
    def delete_account(self, account_id, destination_account_id=None):
        if len(self.accounts) == 1:
            return False, 'You cant delete all your accounts.'
           
        delete_account_table = '''
        DELETE FROM accounts WHERE account_id = ?;
        '''
        
        transfer_money_table = '''
        UPDATE accounts SET balance = ? WHERE account_id = ?;
        '''
        
        to_be_deleted_account = self.accounts.get(account_id)
        destination_account = self.accounts.get(destination_account_id)
        
        if not destination_account_id:
            self.database.cursor.execute(delete_account_table, 
                                (account_id,)
                                )
            self.database.conn.commit()
            del self.accounts[account_id]
            return
        elif to_be_deleted_account.currency_code == destination_account.currency_code:
            self.database.cursor.execute(transfer_money_table,
                                         (to_be_deleted_account._balance,
                                          account_id
                                          )
                                         )
            actual_amount = to_be_deleted_account._balance
        else:
            rate = exchange_rate(to_be_deleted_account.currency_code, 
                                 destination_account.currency_code)
            actual_amount = round(rate * float(to_be_deleted_account._balance))
            
            self.database.cursor.execute(transfer_money_table,
                                         (actual_amount,
                                          destination_account_id
                                          )
                                         )
        self.database.cursor.execute(delete_account_table,
                                     (account_id,)
                                     )
        self.database.conn.commit()
        del self.accounts[account_id]
        destination_account._balance += actual_amount
        return True
                
                                          
    def get_all_actions(self):
        get_all_user_actions_table = '''
        SELECT * from account_transactions where account_id in (SELECT user_id from accounts where user_id = ?);
        '''
        self.database.cursor.execute(get_all_user_actions_table,
                                     (self.user_id,)
                                     )
            
            
        
        
        

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
        return f'{self.user_id:^8} || {self.account_id:^10} || {self._balance:^8} || {self.currency_code:^12} || {self.account_cd}'

    
    def _load_transactions(self) -> list:
        '''
        This module prepares the transactions attribute so that the accounts can access their transactions up to date.
        '''
        
        transactions_dict = {}

        search_transactions = '''
        SELECT * FROM account_transactions WHERE account_id = ?
        '''

        try:
            self.database.cursor.execute(search_transactions, (self.account_id,))
            transaction_records = self.database.cursor.fetchall()
            for transaction_record in transaction_records:
                transaction = Transaction(*transaction_record)
                transactions_dict[transaction.transaction_id] = transaction
        except Exception as e:
            print(f'Error occured while _load_transactions: {e}')
        return transactions_dict
    
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
        return f'|| ID: {self.transaction_id:<4} |Type: {self.transaction_type:<12} |Amount: {self.amount:<6} |Date: {self.transaction_date}'
        
