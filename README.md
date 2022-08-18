# Networks
Instructions

Requirements:
•	Ensure you have python 3.8+ installed on the machine, and use it to run the system
•	Ensure you have installed the sympy module, as this is used to check prime. 
o	You can do this by doing “python(3.8+)  -m pip install sympy” in the command line
•	This has been tested only on windows based machines, any differing to this, is not tested and may affect performance
How To Run:
The Main Server:
1.	Start the server.py if you are going to be using the main server (my application supports running your own server in the client), the best way to do this is opening the file in CMD by going to the directory and typing “python(3.8+)”. 
2.	Then, copy the same steps but instead put “python(3.8+) client.py”, you will then be brought to the screen to enter your nickname, choose whatever you want as long as it’s not blank
3.	You will then be brought to the main menu in the command line, you can choose here to host your own server, join a server or exit. As we’re joining the main server, all you need to do enter 2
4.	This will then bring you to the option “Would You Like To Join The Main Chatroom: (Y) Or (N)”, type y or Y and this will bring you automatically into the main server, assuming that you’ve remembered to follow step one.
5.	Please wait for a couple of seconds (normally 5 – 10 seconds), as then the GUI comes up.
6.	That’s everything, if you wish to end the client or server simply close them

User Hosted Server:
1.	Rather than start server.py, all you do is start client.py by going into CMD, going to the directory and typing python(3.8+)
2.	Then, you will then be brought to the screen to enter your nickname, choose whatever you want as long as it’s not blank
3.	You will then be brought to the main menu in the command line, you can choose here to host your own server, join a server or exit. As we’re hosting our own, all you need to do enter 1
4.	This will then load up the server, assuming the port of 50001 is available
5.	Please wait for a couple of seconds (normally 5 – 10 seconds), as then the GUI comes up, as you’ll automatically get logged in.
6.	If you want someone else to join, then all you do is follow up to set 3, but instead of pressing, you press 2 to join a server
a.	This will then bring you to the option “Would You Like To Join The Main Chatroom: (Y) Or (N)”, type n or N
b.	Then they’ll have to type in the ip, you can see the ip in the title, where it’s got “CHAT:X.X.X.X”, you just need the numbers for that 
7.	Then you’re all finished
