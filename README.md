# GitGeneral
Testing my new setup
How to integrate your new local machine(windows) through ssh with your existing Github account
Background: I have an existing Github account, but I switched to a new machine(HP).
I have an active email address already and a username- So i checked for these two info in my github account to be used to setup my ssh key.
Steps- Get my github username and password from my github account
Open up a command prompt and run: "git config --global user.name "github username"
Run this command next: "git config --global user.email "email in your github"
Run this command next: "ssh-keygen -t rsa -C "your email"
Click "Enter" for the next set of commands, for the key-pair that is generated to be stored in the default location-- c:/users/.ssh
Go and grab your public key(id rsapublic or when you check the 2 files, the one that ends with your email address and does not have private key text on it) from the .ssh folder in the previous step- copy it.
Go to your Github account and follow this path -- 
The dropdown on your profile at the extreme right
Select "Settings" from the drop down
Select "SSH and GPG Keys" from the navigation pane on the left
Enter a name for your key e.g "New Key"
Paste the key that you copied from your machine into the box provided for the ssh key.
Click on "Add SSH Key" button at the bottom
You can go to your "repositories" next. In my own case, i have some existing repositories
Go to the "Code" button (the only green button), at the extreme right of the main page and click on the dropdown
Select SSH and copy the link provided
Go to your visual studio code on your local machine and clone the repo into it by running
git clone  e.g "git clone git@github.com:Needium66/artifact.git"
Go to the location of your repo and check for its branch e.g "git branch"
Run this command to see if your connection is active "git config --list"