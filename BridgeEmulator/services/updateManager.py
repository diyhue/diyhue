import requests
import configManager
import logManager
import json
from datetime import datetime, timezone
import subprocess

bridgeConfig = configManager.bridgeConfig.yaml_config
logging = logManager.logger.get_logger(__name__)

def versionCheck():
    swversion = bridgeConfig["config"]["swversion"]
    url = "https://firmware.meethue.com/v1/checkupdate/?deviceTypeId=BSB002&version=" + swversion
    response = requests.get(url)
    if response.status_code == 200:
        device_data = json.loads(response.text)
        if len(device_data["updates"]) != 0:
            new_version = str(device_data["updates"][len(device_data["updates"])-1]["version"])
            new_versionName = str(device_data["updates"][len(device_data["updates"])-1]["versionName"])
            if new_version > swversion:
                logging.info("swversion number update from Philips, old: " + swversion + " new:" + new_version)
                bridgeConfig["config"]["swversion"] = new_version
                bridgeConfig["config"]["apiversion"] = new_versionName
                bridgeConfig["config"]["swupdate2"]["lastchange"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                bridgeConfig["config"]["swupdate2"]["bridge"]["lastinstall"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            else:
                logging.info("swversion higher than Philips")
        else:
            logging.info("no swversion number update")

def githubCheck():
    #creation_time = 2024-02-18 19:50:15.000000000 +0100
    creation_time = subprocess.run("stat -c %y HueEmulator3.py", shell=True, capture_output=True, text=True)
    creation_time = creation_time.stdout.replace("\n", "")
    creation_time_arg1 = creation_time.split(" ")
    creation_time_arg2 = creation_time_arg1[1].split(".")
    creation_time = creation_time_arg1[0] + " " + creation_time_arg2[0] + " " + creation_time_arg1[2]
    creation_time = datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S %z")
    creation_time = creation_time.astimezone(timezone.utc)
    creation_time = creation_time.strftime("%Y-%m-%d %H")

    url = "https://api.github.com/repos/diyhue/diyhue/branches/master"
    response = requests.get(url)
    if response.status_code == 200:
        device_data = json.loads(response.text)
        publish_time = device_data["commit"]["commit"]["author"]["date"]
        publish_time = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%SZ")
        publish_time = publish_time.strftime("%Y-%m-%d %H")

    logging.info("creation_time strftime: " + str(creation_time))
    logging.info("publish_time          : " + str(publish_time))

    if publish_time > creation_time:
        logging.info("update on github")
        bridgeConfig["config"]["swupdate2"]["state"] = "allreadytoinstall"
        bridgeConfig["config"]["swupdate2"]["bridge"]["state"] = "allreadytoinstall"
    else:
        logging.info("no update on github")
        bridgeConfig["config"]["swupdate2"]["state"] = "noupdates"
        bridgeConfig["config"]["swupdate2"]["bridge"]["state"] = "noupdates"

    bridgeConfig["config"]["swupdate2"]["checkforupdate"] = False
