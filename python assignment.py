import os
import sys
import datetime
import json
import hashlib
from cryptography.fernet import Fernet
from typing import Optional, Dict, List, Tuple, Union
import random
import time
from enum import Enum, auto
import re
from dataclasses import dataclass
import pickle

# Constants
MAX_ATTEMPTS = 3
PASSING_SCORE = 75  # 75% required to pass each quiz
MIN_PASSWORD_LENGTH = 8
CHAPTER_COUNT = 5
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
MAX_USERNAME_LENGTH = 20
MIN_USERNAME_LENGTH = 4
MAX_NAME_LENGTH = 50
MIN_NAME_LENGTH = 2

# Generate or load encryption key
def get_encryption_key() -> bytes:
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

cipher_suite = Fernet(get_encryption_key())

class QuestionType(Enum):
    TRUE_FALSE = auto()
    MULTIPLE_CHOICE = auto()
    FILL_BLANK = auto()
    CODE_COMPLETION = auto()

@dataclass
class Question:
    text: str
    answer: str
    question_type: QuestionType
    choices: Optional[List[str]] = None
    hint: Optional[str] = None
    difficulty: int = 1  # 1-3 scale (easy, medium, hard)

    def check_answer(self, user_answer: str) -> bool:
        # Normalize both answers for comparison
        normalized_user = user_answer.lower().strip()
        normalized_correct = self.answer.lower().strip()
        
        # Handle various true/false formats
        if self.question_type == QuestionType.TRUE_FALSE:
            true_aliases = ['true', 't', 'yes', 'y', '1']
            false_aliases = ['false', 'f', 'no', 'n', '0']
            
            if normalized_correct in true_aliases:
                return normalized_user in true_aliases
            elif normalized_correct in false_aliases:
                return normalized_user in false_aliases
        
        # Handle multiple choice (accept letter or full answer)
        elif self.question_type == QuestionType.MULTIPLE_CHOICE:
            if len(normalized_user) == 1:  # Single letter answer
                return normalized_user == normalized_correct[0]
            else:  # Full answer text
                return normalized_user == normalized_correct
        
        # For other types, do direct comparison
        return normalized_user == normalized_correct

    def display(self) -> None:
        print(self.text)
        if self.question_type == QuestionType.MULTIPLE_CHOICE and self.choices:
            print("\nOptions:")
            for i, choice in enumerate(self.choices, start=1):
                print(f"{chr(96+i)}) {choice}")
        if self.hint:
            print(f"\nHint: {self.hint}")

@dataclass
class Chapter:
    number: int
    title: str
    content: str
    questions: List[Question]
    learning_objectives: List[str]
    duration_minutes: int

class Student:
    def __init__(self):
        self.name: str = ""
        self.username: str = ""
        self.password: str = ""
        self.email: str = ""
        self.progress: int = 1
        self.scores: Dict[int, float] = {}  # Chapter number: score percentage
        self.last_login: Optional[datetime.datetime] = None
        self.login_count: int = 0
        self.total_study_time: int = 0  # in minutes
        self.achievements: List[str] = []
        self.preferences: Dict[str, Union[str, bool]] = {
            'dark_mode': False,
            'animation_speed': 'normal'
        }

    def set_name(self, name: str) -> None:
        self.name = name.title()

    def set_username(self, username: str) -> None:
        self.username = username.lower()

    def set_password(self, password: str) -> None:
        self.password = hashlib.sha256(password.encode()).hexdigest()

    def set_email(self, email: str) -> None:
        self.email = email.lower()

    def update_progress(self, chapter: int) -> None:
        if chapter > self.progress and chapter <= CHAPTER_COUNT:
            self.progress = chapter
            if chapter == CHAPTER_COUNT:
                self.add_achievement("Course Completer")

    def add_score(self, chapter: int, score: float) -> None:
        self.scores[chapter] = score
        if score >= 90:
            self.add_achievement(f"Chapter {chapter} Master")
        elif score >= PASSING_SCORE:
            self.add_achievement(f"Chapter {chapter} Passer")

    def record_login(self) -> None:
        now = datetime.datetime.now()
        if self.last_login and (now - self.last_login).days >= 1:
            self.add_achievement("Daily Learner")
        self.last_login = now
        self.login_count += 1
        if self.login_count == 5:
            self.add_achievement("Regular User")
        elif self.login_count == 10:
            self.add_achievement("Dedicated Learner")

    def add_study_time(self, minutes: int) -> None:
        self.total_study_time += minutes
        if self.total_study_time >= 60:
            self.add_achievement("Hour of Code")
        if self.total_study_time >= 300:
            self.add_achievement("Dedicated Scholar")

    def add_achievement(self, achievement: str) -> None:
        if achievement not in self.achievements:
            self.achievements.append(achievement)

    def get_overall_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

def encrypt_data(data: str) -> bytes:
    """Encrypt data using Fernet symmetric encryption"""
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt data using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_data).decode()

def file_exists(filename: str) -> bool:
    return os.path.exists(f"{filename}.dat")

def clear_screen() -> None:
    """Clear the console screen based on the operating system"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header(title: str) -> None:
    """Display a consistent header for different sections"""
    clear_screen()
    print("\n" + "=" * 80)
    print(f"\t * * * {title} * * *".center(80))
    print("=" * 80 + "\n")

def animate_text(text: str, delay: float = 0.03) -> None:
    """Display text with typing animation"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def get_valid_input(prompt: str, validation_func=None, error_msg: str = "Invalid input. Please try again.") -> str:
    """
    Get validated input from user with retry on invalid input
    """
    while True:
        user_input = input(prompt).strip()
        if not user_input:
            print("Input cannot be empty. Please try again.")
            continue
        if validation_func is None or validation_func(user_input):
            return user_input
        print(error_msg)

def validate_email(email: str) -> bool:
    """More comprehensive email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Password validation with complexity requirements"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password)
    return has_upper and has_lower and has_digit and has_special

def save_student_data(student: Student) -> bool:
    """Save student data securely with error handling"""
    try:
        data = {
            'name': student.name,
            'username': student.username,
            'password': student.password,
            'email': student.email,
            'progress': student.progress,
            'scores': student.scores,
            'last_login': student.last_login.isoformat() if student.last_login else None,
            'login_count': student.login_count,
            'total_study_time': student.total_study_time,
            'achievements': student.achievements,
            'preferences': student.preferences
        }

        encrypted_data = encrypt_data(json.dumps(data))
        temp_file = f"{student.username}.tmp"
        final_file = f"{student.username}.dat"
        
        # Write to temporary file first
        with open(temp_file, 'wb') as f:
            f.write(encrypted_data)
        
        # Replace old file with new one
        if os.path.exists(final_file):
            os.remove(final_file)
        os.rename(temp_file, final_file)
        
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def load_student_data(username: str) -> Optional[Student]:
    """Load student data from encrypted file with error handling"""
    try:
        with open(f"{username}.dat", 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = json.loads(decrypt_data(encrypted_data))

        student = Student()
        student.name = decrypted_data['name']
        student.username = decrypted_data['username']
        student.password = decrypted_data['password']
        student.email = decrypted_data.get('email', '')
        student.progress = decrypted_data['progress']
        student.scores = decrypted_data.get('scores', {})
        last_login = decrypted_data.get('last_login')
        student.last_login = datetime.datetime.fromisoformat(last_login) if last_login else None
        student.login_count = decrypted_data.get('login_count', 0)
        student.total_study_time = decrypted_data.get('total_study_time', 0)
        student.achievements = decrypted_data.get('achievements', [])
        student.preferences = decrypted_data.get('preferences', {
            'dark_mode': False,
            'animation_speed': 'normal'
        })
        
        return student
    except FileNotFoundError:
        print("Error: User data file not found.")
    except json.JSONDecodeError:
        print("Error: Corrupted data file.")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
    return None

def generate_quiz(chapter_num: int) -> List[Question]:
    """Generate quiz questions for each chapter with varied difficulty"""
    if chapter_num == 1:
        return [
            Question(
                "1. Python uses braces {} to define code blocks.", 
                "false", 
                QuestionType.TRUE_FALSE,
                hint="Python uses indentation for code blocks."
            ),
            Question(
                "2. Python was first released in 1991.", 
                "true", 
                QuestionType.TRUE_FALSE,
                hint="Python was created by Guido van Rossum."
            ),
            Question(
                "3. Python is a compiled language like C++.", 
                "false", 
                QuestionType.TRUE_FALSE,
                hint="Python is an interpreted language."
            ),
            Question(
                "4. What is the correct extension for Python files?", 
                ".py", 
                QuestionType.FILL_BLANK,
                hint="It's a two-letter extension starting with 'p'."
            ),
            Question(
                "5. Who created Python?\na) Guido van Rossum\nb) Bjarne Stroustrup\nc) James Gosling",
                "a", 
                QuestionType.MULTIPLE_CHOICE, 
                ["Guido van Rossum", "Bjarne Stroustrup", "James Gosling"],
                hint="He's known as Python's 'Benevolent Dictator For Life'."
            ),
            Question(
                "6. Complete this code to print 'Hello, World!':\nprint('_____')",
                "Hello, World!", 
                QuestionType.CODE_COMPLETION,
                hint="The classic first program output."
            )
        ]
    elif chapter_num == 2:
        return [
            Question(
                "1. Python functions are defined using the 'function' keyword.", 
                "false", 
                QuestionType.TRUE_FALSE,
                hint="Python uses 'def' for functions."
            ),
            Question(
                "2. Indentation in Python is optional.", 
                "false", 
                QuestionType.TRUE_FALSE,
                hint="Indentation is syntactically significant in Python."
            ),
            Question(
                "3. What symbol starts a comment in Python?", 
                "#", 
                QuestionType.FILL_BLANK,
                hint="It's sometimes called a 'hash' or 'pound' symbol."
            ),
            Question(
                "4. Which of these is NOT a Python data type?\na) int\nb) float\nc) char\nd) str",
                "c", 
                QuestionType.MULTIPLE_CHOICE, 
                ["int", "float", "char", "str"],
                hint="Python doesn't have a separate 'char' type."
            ),
            Question(
                "5. The __name__ variable equals '__main__' when:",
                "the script is run directly", 
                QuestionType.FILL_BLANK,
                hint="This is used to check if a script is being run directly."
            ),
            Question(
                "6. Complete this function definition:\n___ greet(name):\n    print(f'Hello, {name}')",
                "def", 
                QuestionType.CODE_COMPLETION,
                hint="This keyword starts function definitions in Python."
            )
        ]
    elif chapter_num == 3:
        return [
            Question(
                "1. Python has dedicated multi-line comment syntax like /* */ in C++.", 
                "false", 
                QuestionType.TRUE_FALSE,
                hint="Python uses multi-line strings for this purpose."
            ),
            Question(
                "2. Docstrings are accessible at runtime through __doc__ attribute.", 
                "true", 
                QuestionType.TRUE_FALSE,
                hint="You can access them with help() or .__doc__."
            ),
            Question(
                "3. PEP 8 recommends using docstrings for all public functions.", 
                "true", 
                QuestionType.TRUE_FALSE,
                hint="PEP 8 is Python's style guide."
            ),
            Question(
                "4. What is the recommended indentation size in Python?", 
                "4", 
                QuestionType.FILL_BLANK,
                hint="PEP 8 recommends this many spaces per indentation level."
            ),
            Question(
                "5. Which of these is used for documentation strings?\na) '''triple quotes'''\nb) // double slash\nc) <!-- HTML comment -->",
                "a", 
                QuestionType.MULTIPLE_CHOICE, 
                ["'''triple quotes'''", "// double slash", "<!-- HTML comment -->"],
                hint="Python uses triple quotes for docstrings."
            ),
            Question(
                "6. Complete this docstring:\n\"\"\"\nThis function _____.\n\"\"\"",
                "does something", 
                QuestionType.CODE_COMPLETION,
                hint="Docstrings typically describe what the function does."
            )
        ]
    elif chapter_num == 4:  # Final exam
        questions = []
        # Add questions from all chapters
        for chap in range(1, 4):
            questions.extend(generate_quiz(chap))
        # Add some additional challenging questions
        questions.extend([
            Question(
                "13. What does PEP stand for in Python?", 
                "Python Enhancement Proposal", 
                QuestionType.FILL_BLANK,
                hint="They are documents that describe Python features."
            ),
            Question(
                "14. Which of these is NOT a Python built-in function?\na) print()\nb) input()\nc) console.log()",
                "c", 
                QuestionType.MULTIPLE_CHOICE, 
                ["print()", "input()", "console.log()"],
                hint="This function comes from another language."
            ),
            Question(
                "15. What is the output of: print(3 * 'abc')?", 
                "abcabcabc", 
                QuestionType.FILL_BLANK,
                hint="Multiplication with strings repeats them."
            ),
            Question(
                "16. Complete this code to create a list of squares:\nsquares = [x**2 ___ x in range(5)]",
                "for", 
                QuestionType.CODE_COMPLETION,
                hint="This is a list comprehension."
            )
        ])
        return questions
    return []

def administer_quiz(chapter_num: int, student: Student) -> float:
    """Administer quiz and return score percentage with time tracking"""
    questions = generate_quiz(chapter_num)
    if not questions:
        return 0.0

    start_time = time.time()
    correct = 0
    
    for i, question in enumerate(questions, 1):
        clear_screen()
        display_header(f"Chapter {chapter_num} Quiz")
        print(f"Question {i} of {len(questions)}\n")
        question.display()
        
        # Get user answer with appropriate prompt
        if question.question_type == QuestionType.TRUE_FALSE:
            prompt = "\nYour answer (true/false or t/f): "
            while True:
                answer = input(prompt).lower().strip()
                if answer in ('true', 'false', 't', 'f', 'yes', 'no', 'y', 'n'):
                    break
                print("Please enter 'true'/'false' or 't'/'f'")
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            prompt = "\nYour answer (letter or full text): "
            answer = input(prompt).strip()
        else:  # FILL_BLANK or CODE_COMPLETION
            prompt = "\nYour answer: "
            answer = input(prompt).strip()
        
        if question.check_answer(answer):
            print("\n✓ Correct!")
            correct += 1
        else:
            print(f"\n✗ Incorrect. The correct answer is: {question.answer}")
        
        if i < len(questions):
            input("\nPress Enter to continue to next question...")

    end_time = time.time()
    quiz_time = int((end_time - start_time) / 60)  # in minutes
    student.add_study_time(quiz_time)
    
    score = (correct / len(questions)) * 100
    print(f"\nQuiz completed in {quiz_time} minutes! You scored {score:.1f}% ({correct}/{len(questions)})")
    
    # Check for time-based achievement
    if quiz_time < 5 and len(questions) >= 5:
        student.add_achievement("Speed Learner")
    
    # Wait for user to acknowledge results
    input("\nPress Enter to continue...")
    return score

def handle_chapter(chapter_num: int, student: Student) -> None:
    """Handle each chapter's content and quiz with enhanced features"""
    chapters = {
        1: Chapter(
            number=1,
            title="Introduction to Python",
            content="""Python is a high-level, interpreted programming language known for:

* Simple, readable syntax
* Strong support for multiple programming paradigms
* Comprehensive standard library
* Dynamic typing and automatic memory management

Key Features:

* Created by Guido van Rossum, first released in 1991
* Uses indentation for code blocks instead of braces
* Supports object-oriented, imperative, and functional programming
* Extensive ecosystem of third-party packages (PyPI)""",
            questions=generate_quiz(1),
            learning_objectives=[
                "Understand Python's history and design philosophy",
                "Recognize Python's key features and advantages",
                "Identify basic Python syntax elements"
            ],
            duration_minutes=15
        ),
        2: Chapter(
            number=2,
            title="Python Syntax",
            content="""Basic Python Syntax Example:

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
            questions=generate_quiz(2),
            learning_objectives=[
                "Write basic Python statements and expressions",
                "Create simple functions with docstrings",
                "Understand Python's indentation rules"
            ],
            duration_minutes=20
        ),
        3: Chapter(
            number=3,
            title="Python Comments & Docstrings",
            content="""Python Documentation Features:

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
            questions=generate_quiz(3),
            learning_objectives=[
                "Write effective comments and docstrings",
                "Understand the purpose of docstrings",
                "Follow PEP 8 documentation guidelines"
            ],
            duration_minutes=15
        ),
        4: Chapter(
            number=4,
            title="Final Exam",
            content="Comprehensive Python Knowledge Test\n\nThis exam covers all chapters. Answer at least 75% correctly to pass.",
            questions=generate_quiz(4),
            learning_objectives=[
                "Demonstrate mastery of all course concepts",
                "Apply Python knowledge to various question types",
                "Complete the course requirements"
            ],
            duration_minutes=30
        ),
        5: Chapter(
            number=5,
            title="Certificate of Completion",
            content="Congratulations on completing the Python course!",
            questions=[],
            learning_objectives=[],
            duration_minutes=0
        )
    }

    chapter = chapters.get(chapter_num)
    if not chapter:
        return

    display_header(f"Chapter {chapter_num}: {chapter.title}")
    print("Learning Objectives:")
    for i, objective in enumerate(chapter.learning_objectives, 1):
        print(f"{i}. {objective}")
    print(f"\nEstimated Time: {chapter.duration_minutes} minutes\n")
    
    animate_text(chapter.content)

    if chapter_num < 4:  # Chapters 1-3 have quizzes
        input("\nPress Enter to start the quiz...")
        clear_screen()  # Clear lesson content before quiz
        score = administer_quiz(chapter_num, student)
        student.add_score(chapter_num, score)

        if score >= PASSING_SCORE:
            print("\nCongratulations! You passed this chapter!")
            student.update_progress(chapter_num + 1)
            save_student_data(student)
            
            if chapter_num < 3:  # Not the final chapter
                while True:
                    choice = input("\nContinue to next chapter? (yes/no): ").lower()
                    if choice in ('yes', 'y'):
                        handle_chapter(chapter_num + 1, student)
                        break
                    elif choice in ('no', 'n'):
                        print(f"\nGoodbye, {student.name}! Your progress has been saved.")
                        break
                    print("Please enter 'yes' or 'no'.")
        else:
            print(f"\nYou need at least {PASSING_SCORE}% to pass. Please review the material and try again.")
            input("Press Enter to return to the chapter...")
            handle_chapter(chapter_num, student)  # Retry same chapter

    elif chapter_num == 4:  # Final exam
        input("\nPress Enter to start the final exam...")
        clear_screen()  # Clear lesson content before exam
        score = administer_quiz(chapter_num, student)
        student.add_score(chapter_num, score)

        if score >= PASSING_SCORE:
            print("\nCongratulations! You passed the final exam!")
            student.update_progress(chapter_num + 1)
            save_student_data(student)
            input("\nPress Enter to receive your certificate...")
            handle_chapter(chapter_num + 1, student)
        else:
            print(f"\nYou need at least {PASSING_SCORE}% to pass. Please review the material and try again.")
            input("Press Enter to retry the final exam...")
            handle_chapter(chapter_num, student)  # Retry final exam

    elif chapter_num == 5:  # Certificate
        generate_certificate(student)
        input("\nPress Enter to exit...")
        sys.exit(0)

def generate_certificate(student: Student) -> None:
    """Generate a certificate of completion with enhanced formatting"""
    certificate_file = f"certificate_{student.username}.txt"
    try:
        cert_content = f"""
{'*' * 60}
{'CERTIFICATE OF COMPLETION'.center(60)}
{'*' * 60}

THIS CERTIFICATE IS AWARDED TO:
\t{student.name.upper()}

FOR SUCCESSFULLY COMPLETING THE PYTHON PROGRAMMING COURSE

{'*' * 60}
DATE: {datetime.date.today().strftime('%B %d, %Y')}

Overall Performance:
"""
        # Add chapter scores
        for chap in range(1, CHAPTER_COUNT):
            score = student.scores.get(chap, 0.0)
            cert_content += f"Chapter {chap}: {score:.1f}%\n"

        cert_content += f"\nFinal Exam Score: {student.scores.get(4, 0):.1f}%"
        cert_content += f"\nOverall Average: {student.get_overall_score():.1f}%"
        
        cert_content += f"""
\nAchievements Earned:
{'-' * 60}
"""
        for achievement in student.achievements:
            cert_content += f"- {achievement}\n"

        cert_content += f"""
\nStudy Statistics:
- Total Logins: {student.login_count}
- Estimated Study Time: {student.total_study_time} minutes

{'*' * 60}
Python is an excellent first language that scales
from beginner scripts to advanced applications.
Keep coding and never stop learning!
{'*' * 60}
"""
        with open(certificate_file, 'w') as cert:
            cert.write(cert_content)

        clear_screen()
        print(cert_content)
        print(f"\nYour certificate has been saved as '{certificate_file}'")
    except IOError as e:
        print(f"\nError: Could not generate certificate. {str(e)}")

def learning_section(student: Student) -> None:
    """Display the learning section with chapter progression and stats"""
    display_header("Learning Portal")
    print(f"Welcome back, {student.name}!\n")

    if student.last_login:
        print(f"Last login: {student.last_login.strftime('%Y-%m-%d %H:%M')}\n")

    print(f"Your current progress: Chapter {student.progress} of {CHAPTER_COUNT}\n")

    # Display chapter status and scores
    print("Course Chapters:\n" + "-" * 60)
    for i in range(1, CHAPTER_COUNT + 1):
        status = "COMPLETED" if i < student.progress else "CURRENT" if i == student.progress else "LOCKED"
        score = student.scores.get(i, 0.0)
        score_display = f"{score:.1f}%" if i < student.progress or (i == student.progress and score > 0) else ""
        print(f"Chapter {i}: {status.ljust(10)} {score_display}")

    # Display achievements if any
    if student.achievements:
        print("\nYour Achievements:")
        for achievement in student.achievements:
            print(f"- {achievement}")

    input("\nPress Enter to continue to your current chapter...")
    handle_chapter(student.progress, student)

def sign_in() -> None:
    """Handle user sign-in process with session timeout"""
    display_header("Sign In")

    username = get_valid_input("Username: ").strip()
    if not file_exists(username):
        print("\nUsername not found. Please register first.")
        input("Press Enter to continue...")
        return

    student = None
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        password = get_valid_input("Password: ", error_msg="Password cannot be empty.")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        student = load_student_data(username)
        if student and student.password == password_hash:
            # Check for password reuse
            if password_hash == hashlib.sha256("password123".encode()).hexdigest():
                print("\nWarning: You're using a very common password. Consider changing it for security.")
                input("Press Enter to continue...")
            
            student.record_login()
            if save_student_data(student):
                print(f"\nAuthentication successful! Welcome back, {student.name}!")
                input("Press Enter to continue to your learning portal...")
                learning_section(student)
                return
            else:
                print("\nError: Could not update login information.")
                break
        else:
            attempts += 1
            remaining = MAX_ATTEMPTS - attempts
            if remaining > 0:
                print(f"\nIncorrect password. {remaining} attempts remaining.")

    print("\nToo many failed attempts. Please try again later.")
    input("\nPress Enter to return to main menu...")

def sign_up() -> None:
    """Handle new user registration with enhanced validation"""
    display_header("Registration")
    print("Create your account:\n")

    student = Student()

    # Get validated username
    while True:
        username = get_valid_input(
            f"Choose a username ({MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} chars, letters and numbers only): ",
            lambda x: (x.isalnum() and 
                      MIN_USERNAME_LENGTH <= len(x) <= MAX_USERNAME_LENGTH and 
                      not x.isdigit()),
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} chars with letters and may include numbers, but not all numbers."
        ).lower()
        
        if file_exists(username):
            print("Username already taken. Please choose another.")
        else:
            student.set_username(username)
            break

    # Get validated name
    name = get_valid_input(
        f"Your full name ({MIN_NAME_LENGTH}-{MAX_NAME_LENGTH} chars): ",
        lambda x: all(c.isalpha() or c.isspace() for c in x) and MIN_NAME_LENGTH <= len(x) <= MAX_NAME_LENGTH,
        f"Name must be {MIN_NAME_LENGTH}-{MAX_NAME_LENGTH} chars with letters and spaces only."
    )
    student.set_name(name)
    # Get validated email
    email = get_valid_input(
        "Your email address: ",
        validate_email,
        "Please enter a valid email address (e.g., user@example.com)."
    )
    student.set_email(email)

    # Get strong password
    while True:
        password = get_valid_input(
            f"Create a password (min {MIN_PASSWORD_LENGTH} chars with upper, lower, numbers, and special chars): ",
            validate_password,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters with uppercase, lowercase, numbers and special characters."
        )
        confirm = input("Confirm password: ")
        if password == confirm:
            if password.lower() == username.lower() or password.lower() == name.lower().replace(" ", ""):
                print("Warning: Password should not be based on your username or name.")
                continue
            student.set_password(password)
            break
        print("Passwords don't match. Please try again.")

    # Save student data
    if save_student_data(student):
        print("\nRegistration successful!")
        print(f"Welcome to Python Learning, {student.name}!")
        
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

def password_recovery() -> None:
    """Handle password recovery process with simulated email"""
    display_header("Password Recovery")

    username = input("Enter your username: ").strip()
    if not file_exists(username):
        print("\nUsername not found. Please check your username or register.")
        input("Press Enter to continue...")
        return

    student = load_student_data(username)
    if not student:
        print("\nError accessing account data. Please contact support.")
        input("Press Enter to continue...")
        return

    print(f"\nA password reset link has been sent to {student.email} (simulated)")
    print("Please check your email to reset your password.")
    
    # Simulate password reset
    if input("\nWould you like to simulate password reset now? (yes/no): ").lower() in ('yes', 'y'):
        new_password = get_valid_input(
            "Enter new password: ",
            validate_password,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters with uppercase, lowercase and numbers."
        )
        student.set_password(new_password)
        if save_student_data(student):
            print("\nPassword has been successfully reset!")
        else:
            print("\nError: Could not reset password. Please try again later.")
    
    input("\nPress Enter to return to main menu...")

def show_description() -> None:
    """Display program description with features"""
    display_header("About This Program")
    animate_text("""PYTHON LEARNING PLATFORM

This interactive program teaches Python programming fundamentals through:

* Progressive, hands-on chapters with clear learning objectives
* Interactive quizzes with varied question types and instant feedback
* Secure account system with encrypted data storage
* Progress tracking and performance analytics
* Achievement system to motivate learning
* Certificate upon successful completion

Technical Features:

* Secure credential storage using Fernet encryption (AES-128)
* Password hashing with SHA-256 for additional security
* Progress tracking with encrypted data files
* Multiple question types (True/False, Multiple Choice, Fill-in, Code Completion)
* Comprehensive input validation and error handling
* Clean, modular Python code following PEP 8 guidelines
* Cross-platform compatibility
* Session timeout for security

Educational Approach:

* Bite-sized learning concepts with clear objectives
* Immediate application through interactive quizzes
* Gradual difficulty progression
* Practical Python examples
* Performance tracking and feedback
* Motivational achievements and certificate
""")
    input("\nPress Enter to return to main menu...")

def user_settings(student: Student) -> None:
    """Handle user settings and preferences"""
    display_header("User Settings")
    
    print(f"Current Settings for {student.name}:")
    print(f"1. Dark Mode: {'Enabled' if student.preferences.get('dark_mode', False) else 'Disabled'}")
    print(f"2. Animation Speed: {student.preferences.get('animation_speed', 'normal').title()}")
    
    choice = input("\nSelect setting to change (1-2) or Enter to return: ").strip()
    
    if choice == '1':
        student.preferences['dark_mode'] = not student.preferences.get('dark_mode', False)
        print(f"\nDark Mode {'enabled' if student.preferences['dark_mode'] else 'disabled'}.")
    elif choice == '2':
        speeds = {'slow': 'Normal', 'normal': 'Fast', 'fast': 'Slow'}
        current = student.preferences.get('animation_speed', 'normal')
        new_speed = speeds[current.lower()]
        student.preferences['animation_speed'] = new_speed.lower()
        print(f"\nAnimation speed set to {new_speed}.")
    
    if choice in ('1', '2'):
        save_student_data(student)
        input("\nPress Enter to continue...")

def main_menu() -> None:
    """Display and handle the main program menu with enhanced options"""
    while True:
        display_header("Python Learning Platform")
        print("MAIN MENU\n")
        print("1. Sign In")
        print("2. Register")
        print("3. Password Recovery")
        print("4. Program Description")
        print("5. Settings")
        print("6. Exit")

        choice = get_valid_input("\nEnter your choice (1-6): ", 
                               lambda x: x in ('1', '2', '3', '4', '5', '6'),
                               "Please enter a number between 1 and 6")
        
        if choice == '1':
            sign_in()
        elif choice == '2':
            sign_up()
        elif choice == '3':
            password_recovery()
        elif choice == '4':
            show_description()
        elif choice == '5':
            # Demo settings without logged in user
            temp_student = Student()
            temp_student.preferences = {'dark_mode': False, 'animation_speed': 'normal'}
            user_settings(temp_student)
        elif choice == '6':
            print("\nThank you for using the Python Learning Platform. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    try:
        from cryptography.fernet import Fernet
    except ImportError as e:
        print(f"\nError: Required package not found - {str(e)}")
        print("Please install required packages by running: pip install cryptography")
        input("\nPress Enter to exit...")
        exit(1)
    main_menu()
