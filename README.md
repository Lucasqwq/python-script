# Python-script

## [command-checking.py](./command-checking.py)  
This script is originally using for checking the aws alb IP changed or not by curling the upstream variable in nginx.(If it does,the script reload the nginx service to get the newest IPs)  

Script advantages:
1. This script can also be using for other commands as you want.
2. It would create log file to log things happened in process.
3. You can choose how long the process should run or terminate the process.
4. Sending telegram message to your own bot in your choosen group.(need to create telegram bot first.)

## [create_conf.py](./create_conf.py)  
This script is using for creating nginx.conf by giving template,it will create one conf in each domain in domains.txt file.

Script advantages:
1. You can customized your own template in your script.
2. Once the creation is done,you can review your conf in the creation directory first, then move it to the specified directory.
