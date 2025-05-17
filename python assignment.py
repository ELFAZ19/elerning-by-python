import os
import sys
import datetime
import json
import hashlib
from cryptography.fernet import Fernet
from typing import Optional, Dict, List, Tuple
import getpass
from enum import Enum, auto

# Constants
MAX_ATTEMPTS = 3
MIN_PASSWORD_LENGTH = 8
PASSING_SCORE = 0.75  # 75% required to pass

# Enum for chapter status
class ChapterStatus(Enum):
    LOCKED = auto()
    UNLOCKED = auto()
    COMPLETED = auto()

# Generate or load encryption key
def get_encryption_key() -> bytes:
    key_file = os.path.join('data', 'secret.key')
    os.makedirs('data', exist_ok=True)
    
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

cipher_suite = Fernet(get_encryption_key())

class Student:
    def __init__(self):
        self.name: str = ""
        self.username: str = ""
        self.password_hash: str = ""
        self.email: str = ""
        self.progress: Dict[int, int] = {}  # chapter: score
        self.current_chapter: int = 1
        self.account_created: datetime.datetime = datetime.datetime.now()
        self.last_login: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'username': self.username,
            'password_hash': self.password_hash,
            'email': self.email,
            'progress': self.progress,
            'current_chapter': self.current_chapter,
            'account_created': self.account_created.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Student':
        student = cls()
        student.name = data['name']
        student.username = data['username']
        student.password_hash = data['password_hash']
        student.email = data.get('email', '')
        student.progress = data.get('progress', {})
        student.current_chapter = data.get('current_chapter', 1)
        student.account_created = datetime.datetime.fromisoformat(data['account_created'])
        student.last_login = datetime.datetime.fromisoformat(data['last_login']) if data['last_login'] else None
        return student

def encrypt_data(data: str) -> bytes:
    """Encrypt data using Fernet symmetric encryption"""
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt data using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_data).decode()

def hash_password(password: str) -> str:
    """Create a secure password hash with salt"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against stored hash"""
    salt, key = stored_hash.split(':')
    salt_bytes = bytes.fromhex(salt)
    key_bytes = bytes.fromhex(key)
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt_bytes, 100000)
    return new_key == key_bytes

def clear_screen() -> None:
    """Clear the console screen based on the operating system"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header(title: str) -> None:
    """Display a consistent header for different sections"""
    clear_screen()
    print("\n" + "=" * 80)
    print(f"\t * * * {title} * * *".center(80))
    print("=" * 80 + "\n")

def get_valid_input(prompt: str, 
                  validation_func=None, 
                  error_msg: str = "Invalid input. Please try again.",
                  hide_input: bool = False) -> str:
    """
    Get validated input from user with retry on invalid input
    """
    while True:
        try:
            user_input = getpass.getpass(prompt) if hide_input else input(prompt)
            user_input = user_input.strip()
            
            if not user_input:
                print("Input cannot be empty. Please try again.")
                continue
                
            if validation_func is None or validation_func(user_input):
                return user_input
                
            print(error_msg)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

def save_student_data(student: Student) -> bool:
    """Save student data to encrypted file"""
    try:
        os.makedirs('data/users', exist_ok=True)
        filename = os.path.join('data/users', f"{student.username}.dat")
        
        data = student.to_dict()
        encrypted_data = encrypt_data(json.dumps(data))
        
        with open(filename, 'wb') as f:
            f.write(encrypted_data)
            
        return True
    except Exception as e:
        print(f"Error saving student data: {str(e)}")
        return False

def load_student_data(username: str) -> Optional[Student]:
    """Load student data from encrypted file"""
    try:
        filename = os.path.join('data/users', f"{username}.dat")
        
        if not os.path.exists(filename):
            return None
            
        with open(filename, 'rb') as f:
            encrypted_data = f.read()
            data = json.loads(decrypt_data(encrypted_data))
            
        return Student.from_dict(data)
    except Exception as e:
        print(f"Error loading student data: {str(e)}")
        return None

def display_progress_bar(percentage: float, length: int = 40) -> str:
    """Display a visual progress bar"""
    filled = int(length * percentage)
    bar = '█' * filled + '-' * (length - filled)
    return f"[{bar}] {percentage:.1%}"

def handle_chapter(chapter_num: int, student: Student) -> None:
    """
    Handle each chapter's content and quiz
    """
    chapters = {
        1: {
            "title": "Introduction to Python",
            "content": """Python is a high-level, interpreted programming language known for:
* Simple, readable syntax
* Strong support for multiple programming paradigms
* Comprehensive standard library
* Dynamic typing and automatic memory management

Key Features:
* Created by Guido van Rossum, first released in 1991
* Uses indentation for code blocks instead of braces
* Supports object-oriented, imperative, and functional programming
* Extensive ecosystem of third-party packages (PyPI)""",
            "questions": [
                ("Python uses braces {} to define code blocks.", False),
                ("Python was first released in 1991.", True),
                ("Python is a compiled language like C++.", False),
                ("Python supports multiple programming paradigms.", True)
            ]
        },
        2: {
            "title": "Python Syntax",
            "content": """Basic Python Syntax Example:

# This is a comment

def greet(name):
    \"\"\"This function greets the user\"\"\"
    print(f"Hello, {name}!")

if __name__ == "__main__":
    user = input("Enter your name: ")
    greet(user)

Key Syntax Elements:
* Comments start with #
* Functions use def keyword
* Docstrings in triple quotes for documentation
* Colon (:) starts code blocks
* Indentation (4 spaces) defines block structure
* if __name__ == "__main__": for executable scripts""",
            "questions": [
                ("Python functions are defined using the 'function' keyword.", False),
                ("Indentation in Python is optional.", False),
                ("Triple-quoted strings can be used for multi-line comments.", True),
                ("if __name__ == '__main__': checks if the script is being run directly.", True)
            ]
        },
        3: {
            "title": "Python Comments & Docstrings",
            "content": """Python Documentation Features:

1. Single-line comments:
   # This is a single-line comment
   x = 5  # This is an inline comment

2. Multi-line strings as comments:
   \"\"\"
   This is a multi-line
   comment/string
   \"\"\"

3. Docstrings (documentation strings):
   def my_function():
       \"\"\"
       This is a docstring explaining
       what this function does.
       \"\"\"
       pass

Key Points:
* Comments are ignored by the interpreter
* Docstrings are accessible via __doc__ attribute
* PEP 8 recommends using docstrings for all public modules, functions, classes""",
            "questions": [
                ("Python has dedicated multi-line comment syntax like /* */ in C++.", False),
                ("Docstrings are accessible at runtime through __doc__ attribute.", True),
                ("PEP 8 recommends using docstrings for all public functions.", True),
                ("Inline comments should be separated by at least one space from code.", True)
            ]
        },
        4: {
            "title": "Final Exam",
            "content": "Comprehensive Python Knowledge Test\nThis exam covers all chapters. Answer at least 75% correctly to pass.",
            "questions": [
                ("Python uses braces {} to define code blocks.", False),
                ("Python was first released in 1991.", True),
                ("Python is a compiled language like C++.", False),
                ("Python supports multiple programming paradigms.", True),
                ("Python functions are defined using the 'function' keyword.", False),
                ("Indentation in Python is optional.", False),
                ("Triple-quoted strings can be used for multi-line comments.", True),
                ("if __name__ == '__main__': checks if the script is being run directly.", True),
                ("Python has dedicated multi-line comment syntax like /* */ in C++.", False),
                ("Docstrings are accessible at runtime through __doc__ attribute.", True),
                ("PEP 8 recommends using docstrings for all public functions.", True),
                ("Inline comments should be separated by at least one space from code.", True)
            ]
        },
        5: {
            "title": "Certificate of Completion",
            "content": "",
            "questions": []
        }
    }

    chapter = chapters.get(chapter_num)
    if not chapter:
        print("Invalid chapter number.")
        return

    display_header(f"Chapter {chapter_num}: {chapter['title']}")
    
    if chapter_num != 4:  # Not the final exam
        print(chapter['content'])
        print("\n" + "-" * 80)
        print(f"\t * * * Quiz {chapter_num}: True or False * * *")
        print("-" * 80 + "\n")
    else:
        print("\t * * * Comprehensive Python Knowledge Test * * *")
        print(chapter['content'] + "\n")

    points = 0
    total_questions = len(chapter['questions'])
    
    for i, (question, correct_answer) in enumerate(chapter['questions'], 1):
        while True:
            user_answer = input(f"{i}. {question}\nYour answer (true/false): ").lower()
            if user_answer in ('true', 'false', 't', 'f'):
                user_bool = user_answer.startswith('t')
                if user_bool == correct_answer:
                    print("✓ Correct!\n")
                    points += 1
                else:
                    print("✗ Incorrect\n")
                break
            print("Please enter 'true' or 'false'.")

    percentage = points / total_questions
    student.progress[chapter_num] = percentage
    
    if chapter_num == 4:  # Final exam
        if percentage >= PASSING_SCORE:
            student.current_chapter = 5
            save_student_data(student)
            print(f"\nCongratulations! You scored {percentage:.1%} and passed the final exam!")
            input("\nPress Enter to receive your certificate...")
            handle_chapter(5, student)
        else:
            print(f"\nYou scored {percentage:.1%}. You need at least {PASSING_SCORE:.0%} to pass.")
            print("Please review the material and try again.")
            input("\nPress Enter to continue...")
    elif chapter_num == 5:  # Certificate
        generate_certificate(student)
    else:
        if percentage >= PASSING_SCORE:
            student.current_chapter = chapter_num + 1
            save_student_data(student)
            print(f"\nCongratulations! You scored {percentage:.1%} and passed this chapter!")
            
            while True:
                choice = input("\nContinue to next chapter? (yes/no): ").lower()
                if choice in ('yes', 'y'):
                    print("\nProgress saved. Moving to next chapter...")
                    handle_chapter(chapter_num + 1, student)
                    break
                elif choice in ('no', 'n'):
                    print(f"\nGoodbye, {student.name}! Your progress has been saved.")
                    return
                print("Please enter 'yes' or 'no'.")
        else:
            print(f"\nYou scored {percentage:.1%}. Please review the material and try again.")
            input("\nPress Enter to continue...")

def generate_certificate(student: Student) -> None:
    """Generate a certificate of completion"""
    display_header("Certificate of Completion")
    certificate_file = os.path.join('data/certificates', f"certificate_{student.username}.txt")
    os.makedirs('data/certificates', exist_ok=True)
    
    try:
        cert_content = f"""
{'CERTIFICATE OF COMPLETION'.center(50)}
{'='*50}

THIS CERTIFICATE IS AWARDED TO:
\t{student.name.upper()}

FOR SUCCESSFULLY COMPLETING THE PYTHON PROGRAMMING COURSE
AT PYTHON LEARNING PLATFORM

{'='*50}
DATE: {datetime.date.today().strftime('%B %d, %Y')}

Overall Performance:
{display_progress_bar(sum(student.progress.values())/len(student.progress))}

Python is an excellent first language that scales
from beginner scripts to advanced applications.
Keep coding and never stop learning!
"""
        with open(certificate_file, 'w') as cert:
            cert.write(cert_content)

        print(cert_content)
        print(f"\nYour certificate has been saved as '{certificate_file}'")
        
    except IOError:
        print("\nError: Could not generate certificate. Please check file permissions.")
    
    input("\nPress Enter to exit...")
    sys.exit(0)

def learning_section(student: Student) -> None:
    """Display the learning section with chapter progression"""
    while True:
        display_header("Learning Portal")
        print(f"Welcome back, {student.name}!\n")
        
        # Calculate overall progress
        completed_chapters = len([c for c, score in student.progress.items() if score >= PASSING_SCORE])
        total_chapters = 4  # Excluding certificate
        overall_progress = completed_chapters / total_chapters
        
        print(f"Overall Progress: {display_progress_bar(overall_progress)}\n")
        print("Course Chapters:\n" + "-" * 40)
        
        for chapter_num in range(1, 6):
            status = ChapterStatus.LOCKED
            
            if chapter_num < student.current_chapter:
                status = ChapterStatus.COMPLETED
            elif chapter_num == student.current_chapter:
                status = ChapterStatus.UNLOCKED
            elif chapter_num == student.current_chapter + 1 and student.current_chapter < 5:
                # Check if previous chapter was completed
                if (student.current_chapter - 1) in student.progress and \
                   student.progress[student.current_chapter - 1] >= PASSING_SCORE:
                    status = ChapterStatus.UNLOCKED
            
            status_text = {
                ChapterStatus.LOCKED: "LOCKED",
                ChapterStatus.UNLOCKED: "UNLOCKED",
                ChapterStatus.COMPLETED: "COMPLETED"
            }[status]
            
            score = student.progress.get(chapter_num, 0)
            score_text = f" - Score: {score:.0%}" if chapter_num in student.progress else ""
            
            print(f"{chapter_num}. {chapters[chapter_num]['title'] if chapter_num in chapters else 'Certificate'}"
                  f"{' '*(30-len(str(chapter_num))-len(chapters[chapter_num]['title']))}"
                  f"{status_text}{score_text}")
        
        print("\nOptions:")
        print("1. Continue to current chapter")
        print("2. Review completed chapter")
        print("3. View progress details")
        print("4. Return to main menu")
        
        choice = get_valid_input("\nEnter your choice (1-4): ", 
                               lambda x: x in ('1', '2', '3', '4'),
                               "Please enter a number between 1 and 4")
        
        if choice == '1':
            handle_chapter(student.current_chapter, student)
        elif choice == '2':
            chapter = get_valid_input("Enter chapter number to review: ",
                                    lambda x: x.isdigit() and int(x) in student.progress,
                                    "Please enter a valid completed chapter number")
            handle_chapter(int(chapter), student)
        elif choice == '3':
            display_progress_details(student)
        elif choice == '4':
            return

def display_progress_details(student: Student) -> None:
    """Show detailed progress statistics"""
    display_header("Progress Details")
    
    print(f"Student: {student.name}")
    print(f"Username: {student.username}")
    print(f"Account created: {student.account_created.strftime('%Y-%m-%d')}")
    print(f"Last login: {student.last_login.strftime('%Y-%m-%d %H:%M') if student.last_login else 'Never'}")
    
    print("\nChapter Progress:")
    for chapter_num in range(1, 5):  # Chapters 1-4
        score = student.progress.get(chapter_num, 0)
        status = "PASSED" if score >= PASSING_SCORE else "FAILED" if score > 0 else "NOT ATTEMPTED"
        print(f"Chapter {chapter_num}: {score:.0%} - {status}")
    
    input("\nPress Enter to return to learning portal...")

def sign_in() -> None:
    """Handle user sign-in process"""
    display_header("Sign In")
    
    username = get_valid_input("Username: ").strip()
    student = load_student_data(username)
    
    if not student:
        print("\nUsername not found. Please register first.")
        input("Press Enter to continue...")
        return
    
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        password = get_valid_input("Password: ", hide_input=True)
        
        if verify_password(student.password_hash, password):
            student.last_login = datetime.datetime.now()
            save_student_data(student)
            
            print(f"\nAuthentication successful! Welcome back, {student.name}!")
            input("Press Enter to continue to your learning portal...")
            learning_section(student)
            return
            
        attempts += 1
        remaining = MAX_ATTEMPTS - attempts
        if remaining > 0:
            print(f"\nIncorrect password. {remaining} attempts remaining.")
    
    print("\nToo many failed attempts. Please try again later.")
    input("\nPress Enter to return to main menu...")

def sign_up() -> None:
    """Handle new user registration"""
    display_header("Registration")
    print("Create your account:\n")
    
    # Get validated username
    while True:
        username = get_valid_input(
            "Choose a username (letters and numbers only, 4-20 chars): ",
            lambda x: x.isalnum() and not x.isdigit() and 4 <= len(x) <= 20,
            "Username must be 4-20 chars with letters and may include numbers, but not all numbers."
        ).lower()
        
        if load_student_data(username):
            print("Username already taken. Please choose another.")
        else:
            break
    
    # Get validated name
    name = get_valid_input(
        "Your full name: ",
        lambda x: all(c.isalpha() or c.isspace() for c in x) and 2 <= len(x) <= 50,
        "Name must be 2-50 chars with letters and spaces only."
    ).title()
    
    # Get validated email
    email = get_valid_input(
        "Your email address: ",
        lambda x: '@' in x and '.' in x and 5 <= len(x) <= 100,
        "Please enter a valid email address (5-100 chars)."
    ).lower()
    
    # Get strong password
    while True:
        password = get_valid_input(
            f"Create a password (min {MIN_PASSWORD_LENGTH} chars with mix of letters, numbers and special chars): ",
            lambda x: len(x) >= MIN_PASSWORD_LENGTH and 
                     any(c.isdigit() for c in x) and 
                     any(c.isalpha() for c in x) and
                     any(not c.isalnum() for c in x),
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters with letters, numbers and special chars."
        )
        confirm = get_valid_input("Confirm password: ", hide_input=True)
        if password == confirm:
            break
        print("Passwords don't match. Please try again.")
    
    # Create student object
    student = Student()
    student.name = name
    student.username = username
    student.password_hash = hash_password(password)
    student.email = email
    student.current_chapter = 1
    
    if save_student_data(student):
        print("\nRegistration successful!")
        print(f"Welcome to Python Learning, {name}!")
        
        # Offer to start learning
        while True:
            choice = input("\nStart learning now? (yes/no): ").lower()
            if choice in ('yes', 'y'):
                learning_section(student)
                break
            elif choice in ('no', 'n'):
                print("\nYou can sign in anytime to continue learning.")
                input("Press Enter to return to main menu...")
                break
            print("Please enter 'yes' or 'no'.")
    else:
        print("\nError: Could not create your account. Please try again later.")
        input("Press Enter to continue...")

def show_description() -> None:
    """Display program description"""
    display_header("About This Program")
    print("""PYTHON LEARNING PLATFORM

This interactive program teaches Python programming fundamentals through:

* Progressive, hands-on chapters
* Interactive quizzes with instant feedback
* Secure account system with progress tracking
* Certificate upon completion

Technical Features:

* Secure credential storage using PBKDF2 hashing and Fernet encryption
* Progress tracking with encrypted data files
* Comprehensive input validation and error handling
* Clean, modular Python code following PEP 8 guidelines
* Cross-platform compatibility

Educational Approach:

* Bite-sized learning concepts
* Immediate application through quizzes
* Gradual difficulty progression
* Practical Python examples
* Performance tracking and feedback

The program demonstrates proper Python development practices while
teaching Python programming concepts.
""")
    input("\nPress Enter to return to main menu...")

def reset_password() -> None:
    """Handle password reset functionality"""
    display_header("Password Reset")
    
    username = get_valid_input("Enter your username: ").strip()
    student = load_student_data(username)
    
    if not student:
        print("\nUsername not found. Please register first.")
        input("Press Enter to continue...")
        return
    
    email = get_valid_input("Enter your registered email: ").strip().lower()
    
    if email != student.email:
        print("\nEmail does not match our records.")
        input("Press Enter to continue...")
        return
    
    # Get new password
    while True:
        new_password = get_valid_input(
            f"Create a new password (min {MIN_PASSWORD_LENGTH} chars with mix of letters, numbers and special chars): ",
            lambda x: len(x) >= MIN_PASSWORD_LENGTH and 
                     any(c.isdigit() for c in x) and 
                     any(c.isalpha() for c in x) and
                     any(not c.isalnum() for c in x),
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters with letters, numbers and special chars.",
            hide_input=True
        )
        confirm = get_valid_input("Confirm new password: ", hide_input=True)
        if new_password == confirm:
            break
        print("Passwords don't match. Please try again.")
    
    student.password_hash = hash_password(new_password)
    if save_student_data(student):
        print("\nPassword successfully reset!")
    else:
        print("\nError: Could not reset password. Please try again later.")
    
    input("Press Enter to continue...")

def main_menu() -> None:
    """Display and handle the main program menu"""
    while True:
        display_header("Python Learning Platform")
        print("MAIN MENU\n")
        print("1. Sign In")
        print("2. Register")
        print("3. Password Reset")
        print("4. Program Description")
        print("5. Exit")

        choice = get_valid_input("\nEnter your choice (1-5): ", 
                               lambda x: x in ('1', '2', '3', '4', '5'),
                               "Please enter a number between 1 and 5")
        
        if choice == '1':
            sign_in()
        elif choice == '2':
            sign_up()
        elif choice == '3':
            reset_password()
        elif choice == '4':
            show_description()
        elif choice == '5':
            print("\nThank you for using the Python Learning Platform. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    try:
        # Check if cryptography package is available
        from cryptography.fernet import Fernet
        main_menu()
    except ImportError:
        print("\nError: Required cryptography package not found.")
        print("Please install it by running: pip install cryptography")
        input("\nPress Enter to exit...")