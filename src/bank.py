"""NOT COMPLETED"""

from models import Session
import os
from getpass import getpass 
from exceptions import IncorrectOptionError
from currency import get_currencies, CURRENCY_CODES
t_width, t_height = os.get_terminal_size()


session = Session()
SEP = '>-----------------<'*3
SEP_N = '||' + SEP + '\n'

class Menu:
    
    
    def __init__(self, name, *options):
        self.__name__ = name
        self.options = options
        self.event = True
    
    def __call__(self): 
        self.event = True
        while self.event:
            Menu.header(self.__name__)
            Menu.display_options(*self.options)
            choice = self.get_user_input(message='|| --> ',
                                         valid_options=[option[0] for option in self.options]
                                         )
            if choice:
                selected_option = self.options[[x[0] for x in self.options].index(choice)]
                selected_action = selected_option[2]
                if selected_action.__name__ == 'menu_closer':
                    selected_action(self) 
                    if self.__name__ == 'ONLINE':
                        session.logout()
                else:
                    selected_action()
            else:
                input('|| ! Enter a valid option.')
 
    def menu_closer(self):
        self.event = False
    
    
    def get_user_input(self, message, valid_options):
        user_input = input(message)
        if user_input in valid_options:
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
            notification = session.payload['message']
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
        global profile_menu
        message_menu = Menu('MESSAGES',
                            ('1', 'Send Message', send_message_interface),
                            ('2', 'View Messages', view_messages),
                            ('3', 'Delete Message', delete_messages_interface),
                            ('0', 'Back to prev menu', Menu.menu_closer)
                            )
        transfer_menu = Menu('TRANSFERS',
                             ('1', 'Make Transfer', make_transfer_interface),
                             ('2', 'View Transactions', view_transactions_interface),
                             ('0', 'Back to prev menu', Menu.menu_closer)
                             )
        account_menu = Menu('ACCOUNTS',
                            ('1', 'Create Account', create_account_interface),
                            ('2', 'View Accounts', view_accounts_interface),
                            ('0', 'Back to prev menu', Menu.menu_closer)
                            )
        main_menu = Menu('OFFLINE',
                         ('1', 'Login', login_interface),
                         ('2', 'Sign Up', register_interface),
                         ('3', 'View Banks', bank_status_interface),
                         ('4', 'Switch Banks', bank_choice_interface),
                         ('0', 'Exit', Menu.menu_closer)
                         )
        profile_menu = Menu('PROFILE',
                           ('1', 'View Profile', view_profile_interface),
                           ('2', 'Delete Account', delete_user_interface),
                           ('0', 'Back to prev menu', Menu.menu_closer)
                           )
        online_menu = Menu('ONLINE',
                           ('1', 'Profile Operations', profile_menu),
                           ('2', 'Account Operations', account_menu),
                           ('3', 'Transfer Operations', transfer_menu),
                           ('4', 'Message Operations', message_menu),
                           ('0', 'Log out', Menu.menu_closer)
                           )

def delete_user_interface():
    Printer.print_accounts()
    print(f'{SEP_N}|| ? If you delete this user. You will lost all of your bank accounts. Please make sure you transfered your moneys.')
    decision = input(f'{SEP_N}|| Are you sure you want to delete this user ? (type "YES" for accept) -> ')
    if decision == 'YES':
        session._delete_current_user()
        input(f'{SEP_N}|| + User succesfully deleted.')
        profile_menu.menu_closer()
        online_menu.menu_closer()

    
        
class Printer:
    @classmethod
    def print_currencies(cls):
        print(f'||{SEP}')
        for i, currency_code in enumerate(CURRENCY_CODES):
            if i % 11 == 0 and i != 0:
                print(f'|| {currency_code}')
            else:
                print(f'|| {currency_code}', end='')
        print()
    
    @classmethod
    def print_banks(cls):
        print(rf'\\{SEP}')
        for bank_id, bank_name in session.database.banks.items():
            print(f'|| {bank_name} >< Id: {bank_id}')

        
    @classmethod
    def print_accounts(cls, account=None, clear_terminal=False):
        if clear_terminal:
            Menu.header('ACCOUNTS')
        if not account:
            print(f'{SEP_N}|| Owner ID || Account ID || Balance || Currency Code || Creation Date\n||{SEP}')
            for account in session.user.accounts.values():
                print(f'|| {account}')
        else:
            print(f'{SEP_N}|| Owner ID || Account ID || Balance || Currency Code || Creation Date\n||{SEP}')
            print(f'|| {account}')
    
    @classmethod
    def print_messages(cls, messages=None, clear_terminal=False):
        if clear_terminal:
            Menu.header('MESSAGES')
        if not messages:
            messages = list(session.user.messages.values())
        print(f'||{SEP}')
        for message in messages:
            if message[4] == 'reply':
                info, replied_message, user_message = message[-1].split('@Message:')
                print(f'|| Type: {message[4]} |Id: {message[0]} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}')
                print(f'|| Your message: {replied_message}\n|| Message: {user_message}')
            else:
                info, user_message = message[-1].split('@Message:')
                print(f'|| Type: {message[4]} |Id: {message[0]} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}\n|| Message: {user_message}')
            print(f'||{SEP}')  

    @classmethod
    def print_profile(cls):
        print(f'||{SEP}')
        for key, value in zip(['Bank ID', 
                               'Bank Name', 
                               'User ID', 
                               'Username', 
                               'Email',
                               'Date joined'
                               ], 
                              [session.bank.bank_id, 
                               session.bank.bank_name, 
                               session.user.user_id, 
                               session.user.username, 
                               session.user.email,
                               session.user.user_cd
                               ]):
            print(f'|| {key:<12}: {value}')



def view_profile_interface():
    Printer.print_profile()
    print(f'{SEP_N}|| Change Name  [1]\n|| Change Email [2]')
    
    choice = input(f'{SEP_N}|| --> ')
    if choice not in ('1', '2'):
        return
        
    elif choice == '1':
        print(f'||{SEP}')
        print(session.database._validate_username.__doc__)
        new_name = input(f'{SEP_N}|| Enter the new name -> ')
        try:
            response = session.user.change_profile_attribute(new_name, 
                                                             type='name'
                                                             )
        except Exception as e:
            input('|| ! There are already a user with this username.')
        else:
            if response == False:
                input('|| ! Please make sure the username meets requirements.')
            else:
                input('|| + Name succesfully changed.')
    elif choice == '2':
        print(f'||{SEP}')
        print(session.database._validate_email.__doc__)
        new_email = input(f'{SEP_N}|| Enter new email -> ')
        response = session.user.change_profile_attribute(new_email,
                                                         type='email'
                                                         )
        if response == False:
            input('|| ! Please make sure the email meets requirements.')
        else:
            input('|| + Email succesfully changed.')
            

            
def get_certain_input(message, valid_options, loop=False, warning_message=None):
    if not loop:
        user_input = input(f'{SEP_N}{message}').upper()
        if user_input not in valid_options:
            return None
        else:
            return user_input
    else:
        while True:
            user_input = input(f'{SEP_N}{message}').upper()
            if user_input not in valid_options:
                print(warning_message) if warning_message else input('|| Invalid option.')
            else:
                return user_input

def send_message_interface():       
    
    if len(session.bank.users) == 1:
        input(f'{SEP_N}|| ! There is no user you can send message')
        return
    
    def print_users():
        print(f'\\\\{SEP}\n|| Send Message:\n||{SEP}')
        print(*[f'|| {user[0]}: {user[1]}' for user in session.bank.users if user[0] != session.user.user_id])
    
    def print_type_choices():
        print(f'{SEP_N}|| Message Types:')
        print(*[f'|| {message_num}: {message_type}'
              for message_num, message_type
              in type_choices.items()])
    
    type_choices = {**session.database.message_types, 0: 'Back to menu'}
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
        message = input(f'{SEP_N}|| Enter your message -> ')
        session.send_message('message',
                             {'message': message},
                             receiver_id
                             )                      
        input('|| + Message sent successfully.')
    
    elif type_choice == '2':
        Printer.print_accounts()
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
            message = input(f'{SEP_N}|| Enter your message --> ')
            session.send_message('request',
                                 {'amount': amount,
                                  'account_id': int(account_id),
                                  'currency_code': session.user.accounts.get(int(account_id)).currency_code,
                                  'message': message
                                  },
                                 receiver_id
                                 )
            input('|| + Request sent successfully.')


def view_messages():
    session.payload['message'] = ''
    if len(session.user.messages) == 0:
        input(f'{SEP_N}|| ! You dont have any messages.')
        return
    def choose_account():
        print(f'{SEP_N}|| Your Accounts: ||')
        Printer.print_accounts()
        
        
        account_id = get_certain_input(message='|| Choose an account id -> ',
                                       valid_options=[str(account_id) for account_id in session.user.accounts.keys()]
                                       )
        if account_id: 
            return account_id
        input('|| Invalid account id')

    def examine_message(message):
        Printer.print_messages([message], clear_terminal=True)
        
        if message[4] == 'request':
            print('|| Accept Request [1]\n|| Reject Request [2]\n|| Delete Message [3]\n|| Cancel Selection [0]')
            choice = input(f'{SEP_N}|| --> ')
            
            if choice == '1':
                selected_account = choose_account()
                if selected_account is None:
                    return None
                else:
                    session.accept_request(message[0], int(selected_account))
                    input(f'|| + Request {message[0]} accepted succesfully')
            elif choice == '2':
                session.reject_request(message[0])
                input(f'|| ! Request {message[0]} succesfully rejected.')
            elif choice == '3':
                session.user.delete_messages([message[0]])
                input(f'|| ! Message {message[0]} succesfully deleted.')
        else:
            print('|| Delete Message   [1]\n|| Reply to message [2]\n|| Cancel Choice    [0]')
            choice = input(f'{SEP_N}|| --> ')
            
            if choice == '1':
                session.user.delete_messages([message[0]])
                input(f'|| + Message {message[0]} succesfully deleted.')
            elif choice == '2':
                reply = input(f'{SEP_N}|| Enter the reply message -> ')
                session.send_reply(message[0], reply)
                input('|| + Reply sent succesfully.')
                    
    while True:
        Menu.header('MESSAGES')
        print(f'\\\\{SEP}\n|| Manage Messages: ')
        Printer.print_messages()        
        selected_message_id = input('|| Enter a message id for select (0 for go back) -> ')
        
        if selected_message_id == '0':
            break
        elif selected_message_id.isdigit() and int(selected_message_id) in session.user.messages:
            examine_message(session.user.messages.get(int(selected_message_id)))
        else:
            input('|| Enter a valid number.')
            

                
            
def create_account_interface():
    print(f'\\\\{SEP}\n|| Create Account:\n||{SEP}')
    Printer.print_currencies()
    
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
    if len(session.user.messages) == 0:
        input(f'{SEP_N}|| ! You dont have any messages.')
        return

    while True:
        Menu.header('MESSAGES')
        print(f'{SEP_N}|| Delete Messages:')
        Printer.print_messages()
        
        print(f'|| ? Enter all the message ids you want to delete with a space between them. i.e (1 21 34 483). To go back, just type 0.')
        print(f'|| ? You can also delete with categories (e.g. 'message' or 'request' or 'feedback').')
        
        
        deletion = input(f'{SEP_N}|| -> ')
        if deletion.strip() == '0':
            break
        if deletion in ('message', 'request', 'feedback', 'transfer', 'reply'):
            message_ids = [message_id for message_id, message in session.user.messages.items() if message[4] == deletion]
            if message_ids:
                session.user.delete_messages(message_ids)
                input('|| + Messages succesfully deleted.')
            else:
                input('|| ! There is no message with this type.')
            break
        
        valid_ids = set()
        for message_id in deletion.split():
            if message_id.isdigit() and int(message_id) in session.user.messages:
                valid_ids.add(int(message_id))
        
        if valid_ids:
            print(f'{SEP_N}|| {valid_ids}')
            decision = input(f'{SEP_N}|| Are you sure want to delete these messages (1 to accept) --> ')
            if decision == '1':
                session.user.delete_messages(valid_ids)
                input('|| + Messages succesfully deleted.')
                break
            else:
                input('|| ! Deletion is canceled')
                
                
        else:
            input('|| ! You have not entered a valid id.')
                
        
def view_accounts_interface():
    def account_options(account):
        Printer.print_accounts(account)
        print(f'{SEP_N}|| Change Currency  [1]\n|| Delete Account   [2]\n|| Cancel Selection [0]')
        choice = input(f'{SEP_N}|| --> ')
        if choice == '1':
            Printer.print_currencies()
            chosen_currency = input(f'{SEP_N}|| Choose a currency --> ').upper()
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
        Printer.print_accounts(clear_terminal=True)
        selected_account_id = input(f'{SEP_N}|| Enter the account id for select (0 for go back) -> ')
                                                
        if selected_account_id == '0':
            break
        elif selected_account_id.isdigit() and int(selected_account_id) in session.user.accounts:
            account_options(session.user.accounts.get(int(selected_account_id)))
        else:
            input('|| ! Enter a valid number.')

        
    
def make_transfer_interface():
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
        Printer.print_accounts()
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
                
        
    

def view_transactions_interface():
    def print_transactions(account):
        Menu.header('TRANSACTIONS')
        print(f'||{SEP}')
        for transaction in account.transactions.values():
            print(transaction)
    
    while True:
        Printer.print_accounts(clear_terminal=True)
        
        account_id = get_certain_input(message='|| Choose an account id (0 to go back) -> ',
                                    valid_options=[str(account_id) for account_id in session.user.accounts.keys()] + ['0']
                                    )
        if not account_id:
            input('|| ! Invalid account id')
        elif account_id == '0':
            break
        else:
            account = session.user.accounts.get(int(account_id))
            if len(account.transactions) == 0:
                input('|| ! This account has no transaction.')
            else:
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
    print(f'//{SEP}\n|| Register :\n||{SEP}')
    
    for doc in (session.database._validate_username.__doc__,
                session.database._validate_password.__doc__,
                session.database._validate_email.__doc__
                ):
        for line in doc.split('\n'):
            print(f'|| {line.strip()}')
    print(f'||{SEP}')        
    
    username       = input('|| Username (a-Z, 0-9) -> ')
    password       = getpass('|| Password (^4, a-Z, 0-9) -> ')
    password_again = getpass('|| Password (again) -> ')
    email          = input('|| Email -> ')
    
    if password == password_again:
        response = session.create_user(username, password, email)
        input(response[1])
    else:
        input('|| The passwords did not match. Please make sure the passwords are the same.')
    
    
def bank_status_interface():
    print(f'//{SEP}\n|| Bank Status :')
    for key, value in zip(['ID', 
                           'Database', 
                           'Users'
                           ], 
                           [session.bank.bank_id, 
                            session.database.db_path, 
                            session.bank.users
                            ]):
        print(f'|| {key}: {value}')
    input(f'{SEP_N}|| + Press Enter to continue: ')
    
    
def bank_choice_interface():
    while True:
        Menu.header('START')
        Printer.print_banks()    
        bank_id = get_certain_input(message='|| Choose a bank id to connect -> ', 
                                    valid_options=[str(bank_id) for bank_id in session.database.banks]
                                    )
        if not bank_id:
            input('|| ! Please enter a valid bank id.')
        else:
            session.connect_bank(int(bank_id))
            break

def main():
    Menu.starter()
    bank_choice_interface()
    main_menu()
        
    
if __name__ == '__main__':

    main()
