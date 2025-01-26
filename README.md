# Python-script

## [command-checking.py](./command-checking.py)  
This script is originally using for checking the aws alb IP changed or not by curling the upstream variable in nginx.(If it does,the script reload the nginx service to get the newest IPs)  

This script have some advantages down here:
1. This script can also be using for other commands as you want.
2. It would create log file to log things happened in process.
3. You can choose how long the process should run or terminate the process.
4. Sending telegram message to your own bot in your choosen group.(need to create telegram bot first.)
