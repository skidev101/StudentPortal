from rich.console import Console
from rich.table import Table
import random, string, hashlib, datetime, re, json
from Modules.User import User
from Modules.Utils import Utils
from Modules.Login import Login

# create object instance of console
console = Console()


"""
guest class to handle guest native commands
"""

class Guest(User):
    """
    constructor
    """
    def __init__(self, mainHandle):
        self.guestCommands = {
            'login': self.login,
            'logout': self.logout,
            'apply': self.applyAdmission,
            'check status': self.checkStatus,
            'cancel application': self.cancelApplication,
        }

        # call constructor of base class
        super().__init__(mainHandle)

        # check if there is a logged in user and set user data
        if self.loginCheck:
            self.setLoggedInData(self.mainHandleDict.get('loggedInUser')['id'])

        # execute given user command
        self.executeCommand()

    """
    execute user command
    """
    def executeCommand(self):
        if self.command in self.guestCommands.keys():
            self.guestCommands.get(self.command)()

    """
    check application status
    """
    def checkStatus(self):
        # check if user is logged in first
        if not self.loginCheck:
            console.print("[red]Oops, you need to be logged in to do that![/red]")
            return

        # check if user has been admitted and start student enrollment
        if self.applicationStatus == 'admitted':
            self.registerStudent()
        elif self.applicationStatus == 'rejected':
            self.deleteStudent()
        else:
            console.print(f"\nHello, {self.firstName.title()}! \nYour application status is: "\
                          f"[red]{self.applicationStatus}[/red]\n")

    """
    delete rejection student from applications list
    """
    def deleteStudent(self):
        # delete student
        del self.mainHandleDict.get('admissionApplications')[self.id]

        # print consolation message
        console.print("\n[red]Unfortunately, your application has been rejected![/red]\n\n"\
                      "Sorry to see you go.\nTry again another year, you've got this!\n")

        # log rejected user out
        self.logout()
        

    """
    register newly admitted student
    """
    def registerStudent(self):
        console.print(f"\n[green]CONGRATULATIONS, {self.firstName.title()}![/green] \n\n"\
                      f"Your application is successful!\n")
        table = Table(title="Programme Details")
        table.add_column('___')

        table.add_row("School", self.school.upper())
        table.add_row("Course", self.courseOfChoice.title())
        table.add_row("Course Code", self.courseCode.upper())
        table.add_row("Matric Number", self.matricNo.upper())

        console.print("\n", table, "\n")
        console.print("[red bold]Store your matric number safely![/red bold]\n")

        # ask to setup new password for student
        while True:
            confirm = input("Setup new password? [Y | N] : ")
            confirm = Utils.cleanString(confirm).lower()

            if confirm == 'y' or confirm == 'yes':
                password = input("Enter new password: ")
                check = Utils.validatePassword(password)

                if not check:
                    # hash password
                    password = hashlib.md5(password.encode())
                    password = password.hexdigest()
                    
                    # set new password for student
                    self.mainHandleDict.get('students').get(self.matricNo)['password'] = password
                    console.print("\n[green]Password updated![/green]\n")
                    break
                else:
                    console.print(f"\n[red]{check}[/red]\n")
            elif confirm == 'n' or confirm == 'no':
                console.print("\n[yellow]You've chosen to keep current password![/yellow]\n")
                break
            else:
                console.print("\n[red]ERROR[/red]\nInvalid option chosen!\n")

        console.print("[purple]Welcome to our school![/purple]\n"\
                      "[red]Your application account will be deleted[/red]\n")

        # set student setup status for newly registered student
        self.mainHandleDict['students'].get(self.matricNo)['studentSetup'] = True

        # delete user from application dictionary and logout
        del self.mainHandleDict.get('admissionApplications')[self.id]
        self.logout()

    """
    cancel application to school
    """
    def cancelApplication(self):
        # check if user is logged in first
        if not self.loginCheck:
            console.print("[red]Oops, you need to be logged in to do that![/red]")
            return

        confirmationKeys = ['y', 'n', 'yes', 'no']

        while True:
            confirmation = input(f"Are you sure you want to cancel "
            f"your application? [Y (Yes) | N (No)]:  ")

            try:
                confirmation = str(confirmation).lower()
                
                if confirmation in confirmationKeys:
                    if confirmation == 'y' or confirmation == 'yes':
                        # print goodbye message
                        console.print(f"Sorry to see you go, {self.firstName}.\n[blue]"\
                                      f"Goodluck with future applications.[/blue]\n")

                        # delete application from application dictionary and save storage
                        del self.mainHandleDict.get('admissionApplications')[self.id]
                        break
                    else:
                        console.print(f"[yellow]Operation Cancelled![/yellow]")
                        break
                else:
                    console.print("[yellow]Invalid value![/yellow]")
            except:
                console.print("[yellow]Invalid value![/yellow]")
                continue            

    """
    validate the state
    """
    def getValidState(self, prompt):
        while True:
            state = input(prompt).capitalize()
            if state in self.states:
                return state
            print("\n[yellow]Invalid state. Please enter a valid state.[/yellow]\n")

    """
    validate course of choice
    """
    def getValidCourse(self):
        programmes = Utils.loadProgrammes()
        schoolList = programmes.keys()

        # print available courses in the school
        Utils.viewProgrammes()

        # get and validate school under which course is
        while True:
            schoolName = input("Enter School to apply to: ").lower()
            schoolName = Utils.cleanString(schoolName)

            if schoolName in schoolList:
                departments = {}
                school = programmes.get(schoolName)

                # get all departments in chosen school
                for key, value in school.items():
                    x = {value.get('course'): value.get('course code')}
                    departments.update(x)

                # get course if chosen school has departments under it
                if departments:
                    # print courses/departments in chosen school
                    table = Table(title=f"[yellow italic]Courses in {schoolName.upper()}[/yellow italic]")
                    table.add_column('___')

                    for dept, code in departments.items():
                        table.add_row(code.upper(), dept.title())

                    console.print("\n", table, "\n")

                    while True:
                        course = input("Enter course to apply for: ")
                        course = Utils.cleanString(course).lower()

                        """
                        check if entered course is a department key or value \
                        from dictionary of departments in the chosen school \

                        if it is a key or value:  get the course info \
                        add the school key to it to hold the school name \
                        and instantiate class attribute to hold course info
                        """
                        if course in departments.keys():
                            chosenCourse = school.get(departments.get(course))
                            chosenCourse.update({'school': schoolName})

                            self.chosenCourseInfo = chosenCourse
                            return chosenCourse.get('course')
                        elif course in departments.values():
                            # get course info
                            for key, value in departments.items():
                                if value == course:
                                    chosenCourse = school.get(course)
                                    chosenCourse.update({'school': schoolName})

                                    self.chosenCourseInfo = chosenCourse
                                    return chosenCourse.get('course')
                        else:
                            console.print("\n[red]ERROR[/red]\n"\
                                          "Invalid Course chosen!\n")
                else:
                    console.print("\n[yellow]There are no departments"\
                                  " in chosen school, yet.[/yellow]\n")
            else:
                console.print("\n[red]ERROR[/red]\n"\
                              "Invalid School\n")

    """
    validate jamb score of applicant
    """
    def getValidJamb(self):
        # end execution if chosenCourseInfo dict doesn't exist
        if not self.__dict__.get('chosenCourseInfo'):
            return

        # get the cut off mark for chosen course
        courseCutOff = self.chosenCourseInfo.get('cut off')

        while True:
            try:
                score = int(input("Enter your UTME score: "))
                if 0 <= score <= 400:
                    if score < courseCutOff:
                        console.print(f"[yellow]Sorry, your UTME score of "\
                                      f"\b{score} is less than the cut off mark "\
                                      f"\b{courseCutOff}")
                        return
                    else:
                        return score
            except:
                pass

            console.print("\n[yellow]Invalid JAMB score.[/yellow]\n"\
                          "Please enter a valid JAMB score between 0 and 400.\n")

    """
    handle admission application for guests
    """
    def applyAdmission(self):
        # check and stop user from applying if logged in
        if self.loginCheck:
            console.print(f"[red]\nOops, you can't apply while logged in!\n[/red]")
            return

        id = f"uid{random.randint(0,9999):04}"

        # ensure generated ID is unique
        while id in self.admissionApplications.keys():
            id = f"uid{random.randint(0,9999):04}"

        # randomly generate and hash generated password for user
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        hashedPassword = hashlib.md5(password.encode())
        hashedPassword = hashedPassword.hexdigest()

        # get and check first name
        while True:
            firstName = input("Enter your First Name: ").strip().lower()
            check = Utils.validateName(firstName)

            if check:
                console.print(f"[red]{check}[/red]")
                continue

            break

        # get and check last name
        while True:
            lastName = input("Enter your Last name: ").strip().lower()
            check = Utils.validateName(lastName)

            if check:
                console.print(f"[red]{check}[/red]")
                continue

            break

        # get and check middle name
        while True:
            middleName = input("Enter your Middle name: ").strip().lower()

            if middleName == "":
                middleName = None
                break

            check = Utils.validateName(middleName)

            if check:
                console.print(f"[red]{check}[/red]")
                continue

            break

        email = input("Enter your email address: ").strip().lower()

        # validate email
        while not Utils.isValidEmail(email):
            print("Invalid email address. Please enter a valid email.")
            email = input("Enter your email address: ").strip().lower()
        
        # ensure email is unique
        Utils.ensureUniqueEmail(email)
            
        # loading available states as a list from states-and-cities.json
        self.states = Utils.loadStates('name')
        self.states = sorted(self.states)

        # print states
        console.print("\n[blue]Here are the valid states:[/blue]")
        for state in self.states:
            console.print(f"\t- {state}")

        stateOfOrigin = self.getValidState("Enter your State of Origin: ").lower()
        stateOfResidence = self.getValidState("Enter your State of Residence: ").lower()

        # collect and validate date of birth
        while True:
            # collect date of birth
            dateOfBirth = input("Enter your Date of Birth (DD-MM-YYYY): ")

            if len(dateOfBirth) == 8 or len(dateOfBirth) == 10:
                # strip possible dashes <-> from date of birth
                if '-' in dateOfBirth:
                    dateOfBirth = dateOfBirth.replace('-', '')

                # split date of birth into day, month and year
                try:
                    dayOfBirth = int(dateOfBirth[0:2])
                    monthOfBirth = int(dateOfBirth[2:4])
                    yearOfBirth = int(dateOfBirth[4:])
                    currentYear = datetime.datetime.now().year

                    # checking if user is within the age limit of 16-30 years
                    if 16 <= (currentYear - yearOfBirth) <= 30:
                        # make date of birth into a datetime object to validate date
                        dateOfBirth = datetime.date(yearOfBirth, monthOfBirth, dayOfBirth)
                        break
                    else:
                        console.print("\n[yellow]You must be between 16 and "\
                                      "30 years old to apply![/yellow]\n")
                        continue
                except:
                    console.print("\n[yellow]Invalid date. "\
                          "\nPlease enter a valid date of birth.[/yellow]\n")
                    continue
            else:
                console.print("\n[yellow]Oops, invalid value.\nTry again![/yellow]\n")
                continue

        dateOfBirth = f"{dayOfBirth:02}-{monthOfBirth:02}-{yearOfBirth}"

        # validate chosen course and Jamb score
        courseOfChoice = self.getValidCourse()
        jambScore = self.getValidJamb()

        # cancel application is UTME score is less than cutoff
        if not jambScore:
            console.print("[red]Sorry, you cannot continue with"\
                          " this application!\n[/red]")
            return

        # cast application date to str to pass json serialization
        applicationDate = datetime.datetime.now()
        school = self.chosenCourseInfo.get('school').lower()
        courseCode = self.chosenCourseInfo.get('course code').lower()

        userApplication = {
            id: {
                'id': id,
                'email': email,
                'firstName': firstName,
                'middleName': middleName,
                'lastName': lastName,
                'dateOfBirth': dateOfBirth,
                'stateOfOrigin': stateOfOrigin,
                'stateOfResidence': stateOfResidence,
                'jambScore': jambScore,
                'school': school,
                'courseOfChoice': courseOfChoice,
                'courseCode': courseCode,
                'applicationDate': applicationDate.strftime("%d-%m-%Y %H:%M:%S"),
                'password': hashedPassword,
                'applicationStatus': "pending"
                 }
        }

        self.admissionApplications.update(userApplication)

        # print confirmation message upon successful application
        console.print("\n[green]Congratulations, your application "\
                      "has been successfully received![/green]\n")
        console.print(f"Please, take note of your user id and password: "\
                      f"\nID: [yellow]{id}[/yellow]\nPASSWORD: [yellow]{password}[/yellow]\n")

        # save program state after application
        self.mainHandleDict.update(userApplication)
        self.mainHandle.saveStorage()


    """
    log the user into the portal
    """
    def login(self):
        login = Login(self.mainHandle)
        login.loginGuest()

    """
    refresh data if user is logged in
    """
    def setLoggedInData(self, userId):
        user = self.mainHandleDict['admissionApplications'].get(userId)

        if user:
            # set logged in user value for logged in user
            if not self.mainHandleDict.get('loggedInUser'):
                self.mainHandleDict['loggedInUser'] = user
                self.mainHandleDict['loggedInUser']['id'] = userId

            self.id = userId
            self.firstName = user.get('firstName')
            self.lastName = user.get('lastName')
            self.middleName = user.get('middleName')
            self.email = user.get('email')
            self.stateOfOrigin = user.get('stateOfOrigin')
            self.stateOfResidence = user.get('stateOfResidence')
            self.dateOfBirth = user.get('dateOfBirth')
            self.courseOfChoice = user.get('courseOfChoice')
            self.jambScore = user.get('jambScore')
            self.password = user.get('password')
            self.applicationStatus = user.get('applicationStatus')
            self.courseCode = user.get('courseCode')
            self.matricNo = user.get('matricNo')
            self.school = user.get('school')

            # set main handle class attributes
            self.mainHandle.user = 'guest'
            self.mainHandle.loggedIn = True            
            self.mainHandle.prompt = f"[yellow]({userId.upper()})   [/yellow]"
