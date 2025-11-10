class UIC():
    def __init__(self):
        self.UI = self.GetUserInterface()
    def GetUserInterface(self):
        print('Enter a t for a terminal interface or g for a graphical interface:')
        while True:
            choice = input().strip().lower()
            if choice == 't':
                return TUIC()
            elif choice == 'g':
                return GUIC()
            else:
                print('Invalid choice. Please enter "t" or "g":')
    def GetLoginDetails(self) -> tuple[str,str]:
        return self.UI.GetLoginDetails()
    def GetLogin_or_Register(self):
        return self.UI.GetLogin_or_Register()
    def GetRegisterDetails(self) -> tuple[str,str]:
        return self.UI.GetRegisterDetails()
class TUIC(UIC):
    def __init__(self):
        pass
    def DisplayMessage(self,message:str):
        print(message)
    
    def GetLogin_or_Register(self):
        print('Do you want to (l)ogin or (r)egister?')
        while True:
            choice = input().strip().lower()
            if choice == 'l':
                return 'login'
            elif choice == 'r':
                return 'register'
            else:
                print('Invalid choice. Please enter "l" or "r":')

    def GetLoginDetails(self) -> tuple[str,str]:
        username = input('Enter username: ')
        password = input('Enter password: ')
        return (username,password)
    
    def GetRegisterDetails(self) -> tuple[str,str]:
        username = input('Enter desired username: ')
        password = input('Enter desired password: ')
        return (username,password)
    

class GUIC(UIC):
    pass
