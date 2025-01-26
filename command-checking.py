#!/usr/bin/python3
import os
import subprocess
import requests
import time
import concurrent.futures
import logging
import signal
import sys
sys.path.append('..')

log_dir = "/data/logs/vps_alb_check"
log_file = os.path.join(log_dir, "process.log")

os.makedirs(log_dir, exist_ok=True)
if not os.path.exists(log_file):
    with open(log_file, 'w'): pass

#Configure logger
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f'{log_file}'),
        logging.StreamHandler()
    ]
    )
logger = logging.getLogger(__name__)

def send_tg_msg(bot_token, chat_id, msg: str = ''):
    try:
        """
        发送 Telegram 群消息
        """
        base_url = "https://api.telegram.org"
        url = "{}/bot{}/sendMessage".format(base_url, bot_token)

        # 构造 payload
        payload = {
            "chat_id": chat_id,
            "text": msg
        }

        headers = {
            "Content-Type": "application/json"
        }

        # 发送 POST 请求
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        # 记录响应日志
        if response_data.get("ok"):
            logger.info("tg群消息发送成功: {}".format(response_data))
        else:
            logger.error("tg群消息发送失败: {}".format(response_data.get("description", "未知错误")))

    except Exception as e:
        logger.error("tg群消息错误: {}".format(e))

def ending_handler(signum, frame):
    """
    Setting for ending this program by 2 mins
    """
    final_msg = "Two minuites has passed away,interrupt vps_alb_check.py ,pls check any error in log file!!"
    logger.info(final_msg)
    bot_token = 'token_number:token_text'
    chat_id = '-chat_id'
    send_tg_msg(bot_token,chat_id,final_msg)
    # Perform any necessary cleanup here
    sys.exit(0)

def check_alb_port(port_name, port_number, check_port):
    for i in range(3):
        check_command = f"ssh root@18.162.44.208 -p {port_number} 'curl -I 127.0.0.1:{check_port}'"
        try:
            result = subprocess.run(
                check_command,
                timeout=10,         #subprocess timeout setting
                shell=True,
                text=True,
                capture_output=True
                )
            status = result.returncode
            if status == 0:
                #print(f"{port_name} {check_port} is OK")
                time.sleep(5) #監測間隔 *3 等於監測總時間
            else:
                print(f"Alb port check is failed for {port_name}")
                msg1 = nginx_reload(port_name,port_number)
                if "failed" not in msg1:
                    time.sleep(10)
                    msg2 = check_port_again(port_name, port_number, check_port)
                    msg = msg1 + msg2
                    return msg
                else:
                    msg = msg1
                    return msg

        except subprocess.TimeoutExpired as e:
            logger.warning(f"{port_name} {e}")
            return f"{port_name} {e}"

        except subprocess.CalledProcessError as e:
            logger.warning(f"{port_name} {e}")
            return f"{port_name} {e}"

    return f"{port_name} is OK."

def nginx_reload(port_name,port_number):
    """
    Reloading the nginx service.
    """
    nginx_test_command = f"ssh root@18.162.44.208 -p {port_number} 'nginx -t'"
    nginx_reload_command = f"ssh root@18.162.44.208 -p {port_number} 'nginx -s reload'"
    result = subprocess.run(nginx_test_command, shell=True, text=True, capture_output=True)
    status = result.returncode
    if status == 0:
        msg = ("nginx -t success , starting nginx_reload... ")
        result = subprocess.run(nginx_reload_command, shell=True, text=True, capture_output=True)
        status = result.returncode
        if status == 0:
            msg += f"{port_name} nginx reload success. "
            return msg
        else:
            msg = f"{port_name} nginx reload failed,pls check!! "
            msg += result.stderr
            return msg

    else:
        msg = "nginx -t failed , pls check!! "
        msg += result.stderr
        return msg

def check_port_again(port_name, port_number, check_port):
    """
    After the nginx -s reload , checking the alb connection status again.
    """
    check_command = f"ssh root@18.162.44.208 -p {port_number} 'curl -I 127.0.0.1:{check_port}'"
    for i in range(3):
        result = subprocess.run(
            check_command,
            timeout=10,         #subprocess timeout setting
            shell=True,
            text=True,
            capture_output=True
            )
        status = result.returncode

        if status == 0:
            #print(f"{port_name} {check_port} is OK")
            time.sleep(5) #監測間隔 *3 等於監測總時間
        else:
            return f"{port_name} {check_port} double check is failed ,pls check!!"

    return f"{port_name} {check_port} double check is OK."



def check_alb_connection():
    """
    Determing each connection port for machines and checking alb connection status.
    If check is failed,the process will auto reload the nginx service to get the newest IP.
    """
    ports = {
        #"vps5sz": 32233, #測試用
        "vps5hk": 32232,
        "vps6hk": 32134,
        "vps7hk": 32143,
        "vps8hk": 32146,
        "vps9hk": 32148,
        "web-cdn": 32121,
        "web-bak": 32132
    }

    def determine_check_port(port_name):
        return 8081 if port_name in ["vps8hk", "vps9hk"] else 8088

    results = {}

    #run check simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ports)) as executor:
        # Submit all port checks
        future_to_port = {
            executor.submit(
                check_alb_port,
                port_name,
                port_number,
                determine_check_port(port_name)
            ): port_name

            #the port_name here will create a dictionary like this
            #{
            #<Future for check_alb_port("vps5sz", 32233, 8088)>: "vps5sz",
            #<Future for check_alb_port("vps8hk", 32146, 8081)>: "vps8hk"
            #}

            for port_name, port_number in ports.items()
        }

        # Collect results
        for future in concurrent.futures.as_completed(future_to_port):
            name = future_to_port[future] #machine name
            try:
                result = future.result()
                results[name] = result
            except Exception as e:
                print(f'{name} generated an exception: {e}')
                results[name] = f"Exception: {e}"

        #check result for developers using
        #print(results)

        # Separate successful and failed machine
        successful_machine = [name for name, result in results.items() if 'OK' in result]
        logger.info(f"檢測成功的機器為: {successful_machine}")
        failed_machine = [name for name, result in results.items() if 'OK' not in result]
        logger.info(f"檢測失敗的機器為: {failed_machine}")

        # Generate detailed report
        if not failed_machine:
            return None
        else:
            failed_details = {name: results[name] for name in failed_machine}
            return f"檢測alb upstream port失敗的機器及訊息: {failed_details}"


def main():
    final_msg = check_alb_connection()
    if final_msg == None:
        logger.info("All machine's alb_upstream_ports are OK")
    else:
        logger.info(final_msg)
        bot_token = 'token_number:token_text'
        chat_id = '-chat_id'
        send_tg_msg(bot_token,chat_id,final_msg)

if __name__ == '__main__':
    signal.signal(signal.SIGALRM, ending_handler)
    signal.alarm(120)  # Set an alarm for 120 seconds (2 minutes)
    main()
