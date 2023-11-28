"""NOT COMPLETED"""

from models import Session
import os
from getpass import getpass 
from exceptions import IncorrectOptionError
from currency import get_currencies, CURRENCY_CODES
t_width, t_height = os.get_terminal_size()
session = Session()


SEP = '>-----------------<'*3
 

class Menu:
    def __init__(self, name, *options):
        self.name = name
        self.options = options
        self.event = True
    
    def __call__(self): 
        self.event = True
        while self.event:
            Menu.header(self.name)
            Menu.display_options(*self.options)
            choice = self.get_user_input(message='|| --> ',
                                         valid_options=[option[0] for option in self.options]
                                         )
            if not choice:
                input('|| ! Enter a valid option.')
            else:
                selected_option = self.options[[x[0] for x in self.options].index(choice)]
                selected_action = selected_option[2]
                if not hasattr(selected_action, 'options') and selected_action.__name__ == 'menu_closer':
                    selected_action(self) 
                    if self.name == 'ONLINE':
                        session.logout()
                else:
                    selected_action()
            
 
    def menu_closer(self):
        self.event = False
    
    
    def get_user_input(self, message, valid_options):
        user_input = input(message)
        if user_input not in valid_options:
            return None
        else:
            return user_input
    
    @classmethod
    def display_options(cls, *options):
        print(r'\\' + SEP)
        for i, option in enumerate(options):
            prefix = '//' if i % 2 == 0 else r'\\'
            print(f'{prefix} - {option[0]} <> {option[1]}')
        print(r'\\' + SEP if len(options) % 2 == 1 else '//' + SEP)
            
    
    @classmethod
    def header(cls, menu_name: str):
        Menu.clear_terminal()
        title = f' {"_"*9}{menu_name}{"_"*(t_width - 10 - len(menu_name))}'
        
        if session.user is not None:    
            user_info = '// ~ {id} >< {name} >< {email} > {notification}'
            notification = session.payload['message'] + session.payload['transfer']
            header_string = user_info.format(id=session.user.user_id, name=session.user.username, email=session.user.email, notification=notification)
            print(title, header_string, sep='\n')
        else:
            print(title)
            print(f'// ~ Not login yet')           
    
    @classmethod
    def clear_terminal(cls):
        os.system('clear') if os.name == 'posix' else os.system('cls')

    @classmethod
    def starter(cls):
        global account_menu
        global main_menu
        global transfer_menu
        global online_menu
        global message_menu
        message_menu = Menu('MESSAGES',
                            ('1', 'Send Message', send_message_interface),
                            ('2', 'View Messages', view_messages),
                            ('3', 'Delete Message', delete_messages_interface),
                            ('0', 'Back to prev menu', Menu.menu_closer)
                            )
        transfer_menu = Menu('TRANSFERS',
                             ('1', 'Make Transfer', make_transfer),
                             ('2', 'View Transactions', view_transactions),
                             ('0', 'Back to prev menu', Menu.menu_closer)
                             )
        account_menu = Menu('ACCOUNTS',
                            ('1', 'Create Account', create_account),
                            ('2', 'View Accounts', view_accounts),
                            ('0', 'Back to prev menu', Menu.menu_closer)
                            )
        main_menu = Menu('OFFLINE',
                         ('1', 'Login', login_interface),
                         ('2', 'Sign Up', register_interface),
                         ('3', 'View Banks', bank_status_interface),
                         ('4', 'Switch Banks', bank_choice_interface),
                         ('0', 'Exit', Menu.menu_closer)
                         )
        online_menu = Menu('ONLINE',
                           ('1', 'Account Operations', account_menu),
                           ('2', 'Transfer Operations', transfer_menu),
                           ('3', 'Session Operations', session_menu),
                           ('4', 'Message Operations', message_menu),
                           ('0', 'Log out', Menu.menu_closer)
                           )

def session_menu():...

def print_accounts(account=None, clear_terminal=False):
    if clear_terminal:
        Menu.header('ACCOUNTS')
    if not account:
        print(f'||{SEP}\n|| Owner ID || Account ID || Balance || Currency Code || Creation Date\n||{SEP}')
        for account in session.user.accounts.values():
            print(f'|| {account}')
    else:
        print(f'||{SEP}\n|| Owner ID || Account ID || Balance || Currency Code || Creation Date\n||{SEP}')
        print(f'|| {account}')



def get_certain_input(message, valid_options, loop=False, warning_message=None):
    if not loop:
        user_input = input(f'||{SEP}\n{message}').upper()
        if user_input not in valid_options:
            return None
        else:
            return user_input
    else:
        while True:
            user_input = input(f'||{SEP}\n{message}').upper()
            if user_input not in valid_options:
                print(warning_message) if warning_message else input('|| Invalid option.')
            else:
                return user_input

def send_message_interface():       
    type_choices = {**session.database.message_types, 0: 'Back to menu'}
    if len(session.bank.users) == 1:
        input('|| ! There is no user you can send message')
        return
    
    def print_users():
        print(f'\\\\{SEP}\n|| Send Message:\n||{SEP}')
        print(*[f'|| {user[0]}: {user[1]}' for user in session.bank.users if user[0] != session.user.user_id])
    
    def print_type_choices():
        print(f'||{SEP}\n|| Message Types:')
        print(*[f'|| {message_num}: {message_type}'
              for message_num, message_type
              in type_choices.items()])
    
    print_users()
    receiver_id = get_certain_input(message='|| Enter the user id you want to send message (0 to go back)-> ',
                                    valid_options=[str(user[0]) for user in session.bank.users if user[0] != session.user.user_id] + ['0']
                                    )
    if not receiver_id:
        input('|| ! Please enter a valid user id.')
        return
    if receiver_id == '0':
        return
        
    print_type_choices()
    type_choice = get_certain_input(message='|| Choose a message type -> ',
                                    valid_options=[type_num for type_num in session.database.message_types.keys()]
                                    )
    
    if not type_choice:
        input('|| ! Please enter a valid message type.')
        return
    
    if type_choice == '1':
        message = input(f'||\n|| Enter your message -> ')
        session.send_message('message',
                             {'message': message},
                             receiver_id
                             )                      
        input('|| + Message sent successfully.')
    
    elif type_choice == '2':
        print_accounts()
        account_id = get_certain_input(message='|| Select an account id for your request -> ',
                                       valid_options=[str(account_id) for account_id in session.user.accounts.keys()]
                                       )
        if not account_id:
            input('|| ! Invalid account id. Please make sure you enter a valid account id.')
            return
        try:
            amount = int(input('|| Enter the amount -> '))         
        except ValueError:
            input('|| ! Invalid amount. Please enter a valid amount.')
            return
        else:
            message = input('|| Enter the message --> ')
            session.send_message('request',
                                 {'amount': amount,
                                  'account_id': int(account_id),
                                  'currency_code': session.user.accounts.get(int(account_id)).currency_code,
                                  'message': message
                                  },
                                 receiver_id
                                 )
            input('|| + Request sent successfully.')




        

            
def print_messages(message=None):
        print(f'||{SEP}')
        if not message:
            for message_id, message in session.user.messages.items():
                info, user_message = message[-1].split('Message:')
                print(f'|| Type: {message[4]} |Id: {message_id} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}\n|| Message: {user_message}')
                print(f'||{SEP}')
        else:
            info, user_message = message[-1].split('Message:')
            print(f'|| Selected Message: ')
            print(f'|| Type: {message[4]} |Id: {message[0]} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}\n|| Message: {user_message}')
            print(f'||{SEP}')
            

def view_messages():
    session.payload['message'] = ''
    if len(session.user.messages) == 0:
        input(f'||{SEP}\n|| ! You dont have any messages.')
        return
    def choose_account():
        print(f'||{SEP}\n|| Your Accounts: ||', end='')
        for account in session.user.accounts.values():
            print(f'{account} <> ', end='')
        
        account_id = get_certain_input(message='\n|| Choose an account id -> ',
                                       valid_options=[str(account_id) for account_id in session.user.accounts.keys()]
                                       )
        if not account_id:
            input('|| Invalid account id')
            return None
        else:
            return account_id

    def examine_message(message):
        print_messages(message)
        
        if message[4] == 'request':
            print('|| Accept Request [1]\n|| Reject Request [2]\n|| Delete Message [3]\n|| Cancel Selection [0]')
            choice = input('|| --> ')
            
            if choice == '1':
                selected_account = choose_account()
                return None if selected_account is None else session.accept_request(message[0], int(selected_account))
                input(f'|| ! Request {message[0]} accepted succesfully')
            elif choice == '2':
                session.reject_request(message[0])
                input(f'|| ! Request {message[0]} succesfully rejected.')
            elif choice == '3':
                session.user.delete_messages([message[0]])
                input(f'|| ! Message {message[0]} succesfully deleted.')
        else:
            print('|| Delete Message [1]\n|| Cancel Choice  [0]')
            choice = input('|| --> ')
            
            if choice == '1':
                session.user.delete_messages([message[0]])
                
       
    while True:
        Menu.header('MESSAGES')
        print(f'\\\\{SEP}\n|| Manage Messages: ')
        print_messages()        
        selected_message_id = input('|| Enter a message id for select (0 for go back) -> ')
        
        if selected_message_id == '0':
            break
        elif selected_message_id.isdigit() and int(selected_message_id) in session.user.messages:
            examine_message(session.user.messages.get(int(selected_message_id)))
        else:
            input('|| Enter a valid number.')
            

def print_currencies():
    for i, x in enumerate(CURRENCY_CODES):
        if i % 11 == 0 and i != 0:
            print(f'|| {x}')
        else:
            print(f'|| {x}', end='')
    print()                    
            
def create_account():
    print(f'\\\\{SEP}\n|| Create Account:\n||{SEP}')
    print_currencies()
    
    chosen_currency = get_certain_input(message='|| Choose a currency_code for your new account (0 for go back)-> ',
                                        valid_options=CURRENCY_CODES + ['0'],
                                        loop=True,
                                        warning_message='|| ! Invalid currency code',
                                        )
    if chosen_currency == '0':
        return
    try:
        session.user.create_account(chosen_currency)
    except ValueError:
        input('|| ! You have reached the limit number of accounts.')
    else:
        input('|| + Account succesfully created')

    
def delete_messages_interface():
    print_messages()
    if len(session.user.messages) == 0:
        input('|| ! You dont have any messages.')
        return
    print(f"""|| Enter all the message ids you want to delete with a space between them. i.e (1 21 34 483). To go back, just type 0.
|| You can also delete with categories (e.g. 'message' or 'request' or 'feedback').""")
    
    while True:
        valid_ids = []
        deletion = input(f'||{SEP}\n|| -> ')
        if deletion.strip() == '0':
            break
        if deletion in ('message', 'request', 'feedback', 'transfer'):
            message_ids = [message_id for message_id, message in session.user.messages.items() if message[4] == deletion]
            if message_ids:
                session.user.delete_messages(message_ids)
                input('|| + Messages succesfully deleted.')
            else:
                input('|| ! There is no message with this type.')
            break
        for message_id in deletion.split():
            if message_id.isdigit() and int(message_id) in session.user.messages:
                valid_ids.append(int(message_id))
        if valid_ids:
            print(f'|| {valid_ids}')
            decision = input(f'|| Are you sure want to delete these messages (1 to accept) --> ')
            if decision == '1':
                session.user.delete_messages(valid_ids)
                input('|| + Messages succesfully deleted.')
                break
            else:
                input('|| Deletion is canceled')
                
        else:
            input('|| ! You have not entered a valid id.')
                
        
        
        
                
            

    
def view_accounts():
    def account_options(account):
        print_accounts(account)
        print(f'||{SEP}\n|| Change Currency  [1]\n|| Delete Account   [2]\n|| Cancel Selection [0]')
        choice = input('|| --> ')
        if choice == '1':
            print_currencies()
            chosen_currency = input(f'||{SEP}\n|| Choose a currency --> ').upper()
            if chosen_currency in CURRENCY_CODES:
                session.user.change_account_currency(account.account_id, chosen_currency)
                input('|| + Currency Code succesfully changed.')
            else:
                input('|| ! Invalid currency')
            
        elif choice == '2':
            destionation_account_id = 0
            if len(session.user.accounts) == 1:
                input('|| ! You cant delete all your accounts')
                return
            elif account._balance >= 1:
                destionation_account_id = get_certain_input(message='|| Enter destionation account id -> ',
                                                            valid_options=[str(account_id) for account_id in session.user.accounts.keys()]
                                                            )
                destionation_account_id = 0 if not destionation_account_id else destionation_account_id
            
            session.user.delete_account(account.account_id,
                                        int(destionation_account_id)
                                        )
            input('|| + Account succesfully deleted ')                                
        else:
            return
        
    while True: 
        print_accounts(clear_terminal=True)
        selected_account_id = input(f'||{SEP}\n|| Enter the account id for select (0 for go back) -> ')
                                                
        if selected_account_id == '0':
            break
        elif selected_account_id.isdigit() and int(selected_account_id) in session.user.accounts:
            account_options(session.user.accounts.get(int(selected_account_id)))
        else:
            input('|| ! Enter a valid number.')

        
    
def make_transfer():
    def choose_receiver_id(account_id):
        receiver_id = input('|| Enter a receiver account id -> ')
        if receiver_id.isdigit() and \
                session.bank.does_account_exist(int(receiver_id)) and \
                receiver_id != account_id:
            return int(receiver_id)
        else:
            input('|| ! Please enter a valid user id')
        
    while True:
        Menu.header('TRANSFER')
        print_accounts()
        account_id = get_certain_input(message='|| Enter the account ID  (0 to go back) -> ',
                                       valid_options=[str(account_id) for account_id in session.user.accounts.keys()] + ['0']
                                       )
        if not account_id:
            input('|| ! Invalid account id.')
        elif account_id == '0':
            break
        elif account_id.isdigit() and int(account_id) in session.user.accounts:
            sender_account_id = session.user.accounts.get(int(account_id))
            if sender_account_id._balance < 1:
                input('|| ! Not enough funds in this account.')
            else:
                receiver_id = choose_receiver_id(account_id)
                
                if receiver_id:
                    try:
                        amount = int(input('|| Enter the amount -> '))
                        if amount > session.user.accounts.get(int(account_id))._balance:
                            raise ValueError()
                    except ValueError:
                        input('|| ! Please enter a valid and positive amount with sufficient funds.')
                    else:
                        if receiver_id not in session.user.accounts:
                            session.initiate_transfer(amount, int(account_id), receiver_id, send_feedback=True)
                        else:
                            session.initiate_transfer(amount, int(account_id), receiver_id)
                        input('|| + Succesfully transfered')
        else:
            input('|| ! Invalid account id.')
                
        
    

def view_transactions():
    def print_transactions(account):
        Menu.header('TRANSACTIONS')
        print(f'||{SEP}')
        for transaction in account.transactions.values():
            print(transaction)
    
    while True:
        print_accounts(clear_terminal=True)
        
        account_id = get_certain_input(message='|| Choose an account id (0 to go back) -> ',
                                    valid_options=[str(account_id) for account_id in session.user.accounts.keys()] + ['0']
                                    )
        if not account_id:
            input('|| ! Invalid account id')
        elif account_id == '0':
            break
        else:
            account = session.user.accounts.get(int(account_id))
            print_transactions(account)
            input('|| Press enter to go back')
            

def login_interface():
    print(f'\\\\{SEP}\n|| Login :')
    username = input('|| Username @-> ')
    password = getpass('|| Password !-> ')
    response = session.login(username, password)
    input(response[1])
    if response[0]:
        online_menu()
           

def register_interface():
    print(f'//{SEP}\n|| Register :')
    username = input('|| Username (a-Z, 0-9) -> ')
    password = getpass('|| Password (^4, a-Z, 0-9) -> ')
    password_again = getpass('|| Password (again) -> ')
    email = input('|| Email -> ')
    if password == password_again:
        response = session.create_user(username, password, email)
        input(response[1])
    else:
        input('|| The passwords did not match. Please make sure the passwords are the same.')
    
    
def bank_status_interface():
    print(f'//{SEP}\n|| Bank Status :')
    print(f'|| ID: {session.bank.bank_id}\n|| Database: {session.database.db_path}')
    print(f'|| Users: {session.bank.users}')
    input(f'||\n\\\\ + Press Enter to continue: ')


                

def bank_choice_interface():
    while True:
        Menu.header('START')
        print(rf'\\{SEP}')
        for bank_id, bank_name in session.database.banks.items():
            print(f'|| {bank_name} >< Id: {bank_id}')
        print(f'||{SEP}')
        
        try:
            bank_id = int(input('|| Choose a bank id -> '))
            if bank_id not in session.database.banks.keys():
                raise ValueError('Invalid number')
        except ValueError:
            input('|| ! Please enter a valid bank id.')
        else:
            session.connect_bank(bank_id)
            break
    

