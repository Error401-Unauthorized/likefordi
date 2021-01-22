import json
import requests
import time
import datetime
import sys
import os

# Globals
JsonFileLocation = "./config.json"
JsonData = ''
RunningData = {}
Token = ''
TokenLife = (0, 0)
IdTable = ''
Map = {}
IMap = {}


def read_json(file):
	with open(file) as f:
		data = json.load(f)
	return data


def make_running_file():
	print("Log: Writing new Running file")
	RunningData["day"] = datetime.datetime.today().strftime('%j')
	RunningData["likes"] = []
	RunningData["secondary-messages"] = [0, 0, 0]
	RunningData["group-messages"] = []
	RunningData["direct-messages"] = []
	with open(JsonData["running-data"], "w") as write_file:
		json.dump(RunningData, write_file, indent=4)


def ready_running_file():
	if os.path.exists(JsonData["running-data"]):
		global RunningData
		RunningData = read_json(JsonData["running-data"])
		if datetime.datetime.today().strftime('%j') > RunningData["day"] and datetime.datetime.now() > datetime.datetime.now().replace(hour=1, minute=30):
			print("Log: Running file is out of date. Removing")
			os.remove(JsonData["running-data"])
			make_running_file()
		else:
			print("Log: Resuming bot session from today. Day: {}. Likes: {}. Group messages: {}".format(RunningData["day"], len(RunningData["likes"]), RunningData["group-messages"]))
	else:
		make_running_file()


def save_running_data():
	os.remove(JsonData["running-data"])
	with open(JsonData["running-data"], "w") as write_file:
		json.dump(RunningData, write_file, indent=4)


def wait_to_start(hours=19, minutes=15, seconds=0):
	startTime = datetime.datetime.today().replace(hour=hours, minute=minutes, second=seconds)
	if startTime > datetime.datetime.now():
		wait = int(startTime.timestamp() - time.time())
		while wait:
			sys.stdout.write("\rLog: Bot sleeping. {}".format(str(datetime.timedelta(seconds=wait))))
			sys.stdout.flush()
			time.sleep(1)
			wait -= 1


# Mostly just a check for access to the group.  In the future, this can be used to send text messages to people as another reminder
def get_group_info():
	groupmeAPIKey = JsonData['groupme-api-key']
	groupId = JsonData["group-id"]
	url = "https://api.groupme.com/v3/groups/{}?token={}".format(groupId, groupmeAPIKey)
	headers = {'Content-Type': 'application/json'}
	response = requests.request("GET", url, headers=headers)
	if response.status_code != 200:
		print("Fatal: Groupme returned an error when trying to fetch your group info.  CHeck your internet or make sure you have permission for that group and your api key is right.")
		print(response.status_code)
		print(response.text)
		exit(1)
	return json.loads(response.text)


def send_group_message(message):
	if len(RunningData["group-messages"]) > 0 and RunningData["secondary-messages"][0] == 0:
		print("Log: Not sending a new group message.  Reusing {}".format(RunningData["group-messages"]))
		RunningData["secondary-messages"][0] = 1
	elif len(RunningData["group-messages"]) > 1 and RunningData["secondary-messages"][1] == 0:
		print("Log: Not sending a new second group message.  Reusing {}".format(RunningData["group-messages"]))
		RunningData["secondary-messages"][1] = 1
	elif RunningData["secondary-messages"][0] == 0 or RunningData["secondary-messages"][1] == 0:
		groupId = JsonData["group-id"]
		groupmeAPIKey = JsonData['groupme-api-key']
		url = "https://api.groupme.com/v3/groups/{}/messages?token={}".format(groupId, groupmeAPIKey)
		payload = '{"message": {"source_guid": "GUID", "text": "' + message + '"}}'
		headers = {'Content-Type': 'application/json'}
		if JsonData["simulate"] == 0:
			response = requests.request("POST", url, headers=headers, data=payload)
			if response.status_code != 201:
				print("Fatal: Groupme returned an error when trying to send a message.  Make sure you have permission for that group or your api key is right.")
				print(response.status_code)
				print(response.text)
				exit(1)
			print("Log: Group message '{}' sent".format(message))
			responseJson = json.loads(response.text)
			messageId = responseJson["response"]["message"]["id"]
			print("Log: Message id is: {}".format(messageId))
			RunningData["group-messages"].append(messageId)
		else:
			print("Log: Simulating group message, no message sent")
		# This system assumes the best
		if RunningData["secondary-messages"][0] == 0:
			RunningData["secondary-messages"][0] = 1
		elif RunningData["secondary-messages"][1] == 0:
			RunningData["secondary-messages"][1] = 1
	else:
		print("Fatal: send_group_message has been called 3 times?  How did this even happen?")
		exit(1)


def send_direct_messages(id, message):
	groupmeAPIKey = JsonData['groupme-api-key']
	url = "https://api.groupme.com/v3/direct_messages?token={}".format(groupmeAPIKey)
	payload = '{"direct_message": {"source_guid": "'+id+'","recipient_id": "' + id + '", "text\": "' + message + '"}}'
	headers = {'Content-Type': 'application/json'}
	if JsonData["simulate"] == 0:
		response = requests.request("POST", url, headers=headers, data=payload)
		if response.status_code != 201:
			print("Warning: Groupme dm to {}, id {} did not send.  Status code: {}. Response: {}".format(Map[id]["name"], id, response.status_code, response.text))
		else:
			responseJson = json.loads(response.text)
			messageId = responseJson["response"]["direct_message"]["id"]
			RunningData["direct-messages"].append([id, messageId])
			print("Log: Direct message sent to {}, id {} sent.  Message id: {}".format(Map[id]["name"], id, [id, messageId]))
	RunningData["secondary-messages"][2] = 1


def check_message_likes(type, id, message):
	likes = []
	groupmeAPIKey = JsonData["groupme-api-key"]
	if type == "group":
		url = "https://api.groupme.com/v3/groups/{}/messages/{}?token={}".format(id, message, groupmeAPIKey)
	elif type == "direct":
		url = "https://api.groupme.com/v3/direct_messages?token={}&other_user_id={}&since_id={}&before_id={}".format(groupmeAPIKey, id, str(int(message) - 1), str(int(message) + 1))
	headers = {'Content-Type': 'application/json'}
	response = requests.request("GET", url, headers=headers)
	if response.status_code != 200:
		print("Warning: Error getting likes of {} message {}:{}. Error code {}. Reponse: {}".format(type, id, message, response.status_code, response.text))
		print(url)
	else:
		responseJson = json.loads(response.text)
		if type == "group":
			likes = responseJson["response"]["message"]["favorited_by"]
		elif type == "direct":
			likes = responseJson["response"]["direct_messages"][0]["favorited_by"]
	return likes


def get_messages_likes():
	likes = []
	groupId = JsonData["group-id"]
	for message in RunningData["group-messages"]:
		likes.extend(check_message_likes("group", groupId, message))
	for user, message in RunningData["direct-messages"]:
		likes.extend(check_message_likes("direct", user, message))
	likes = list(set(likes))
	likes.sort()
	return likes


def get_new_likes(old, found):
	newLikes = []
	for x in found:
		if x not in old:
			newLikes.append(x)
	return newLikes


def load_id_table():
	lookupFile = JsonData["lookup-table-location"]
	ids = {}
	with open(lookupFile) as f:
		for line in f:
			gid, sid = line.rstrip().split(":")
			ids[gid] = sid
	return ids


def build_maps(groupInfo):
	for gid in IdTable:
		sid = IdTable[gid]
		name = ''
		for id in groupInfo["response"]["members"]:
			if id["user_id"] == gid:
				name = id["name"]
		if name == '':
			print("\nWarning: gid {}, sid {} name cannot be resolved when building maps".format(gid, sid))
		Map[gid] = {"sid": sid, "name": name}
	for gid in Map:
		sid = Map[gid]["sid"]
		name = Map[gid]["name"]
		IMap[sid] = {"gid": gid, "name": name}


def convert_ids(likes):
	newIDs = []
	for x in likes:
		new = IdTable[x]
		if new == 'null':
			name = Map[x]["name"]
			print("Warning: {}, id {} has liked the message but their sharepoint ID is null in the lookup table.  Can't sign DI".format(name, x))
		else:
			newIDs.append(IdTable[x])
	return newIDs


def get_token():
	global TokenLife
	global Token
	if TokenLife[0] + TokenLife[1] < int(time.time()):
		headers = {'Cookie': JsonData["sharepoint-cookie"], 'Accept': 'application/json;odata=verbose'}
		url = "https://usafa0.sharepoint.com/sites/LoFiDI/_api/contextinfo"
		response = requests.request("POST", url, headers=headers)
		if response.status_code != 200:
			print("Warning: Cannot update sharepoint token. Code: {}, message: {}".format(response.status_code, response.text))
			time.sleep(1)
			print("Warning: Retrying token update")
			get_token()
			return
		else:
			jsonResponse = json.loads(response.text)
			Token = jsonResponse["d"]["GetContextWebInformation"]["FormDigestValue"]
			TokenLife = (int(time.time()), jsonResponse["d"]["GetContextWebInformation"]["FormDigestTimeoutSeconds"])


def update_DI_times(ids):
	completed = []
	for id in ids:
		url = "https://usafa0.sharepoint.com/sites/LoFiDI/_api/web/lists/GetByTitle('{}')/Items/getbyid({})".format(JsonData["sharepoint-roster"], id)
		# Updating Token
		get_token()
		# Make header
		headers = {'X-Http-Method': 'MERGE', 'If-Match': '*', 'Content-Type': 'application/json', 'Cookie': JsonData["sharepoint-cookie"], 'X-RequestDigest': Token, 'Accept': 'application/json;odata=verbose'}
		# Sending new time to sharepoint
		if JsonData["simulate"] == 0:
			payload = '{"DI": "'+datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")+'"}'
			response = requests.request("POST", url, headers=headers, data=payload)
			if response.status_code != 204:
				name = IMap[id]["name"]
				print("Warning: Unable to update {} roster time, id {} DI time. Code: {}, Response: {}".format(name, id, response.status_code, response.text))
				continue
		completed.append(id)
	return completed


def get_user_info(id):
	headers = {'Cookie': JsonData["sharepoint-cookie"], 'Accept': 'application/json;odata=verbose', 'X-RequestDigest': Token}
	url = "https://usafa0.sharepoint.com/sites/LoFiDI/_api/web/lists/GetByTitle('{}')/Items/getbyid('{}')".format( JsonData["sharepoint-roster"], id)
	response = requests.request("GET", url, headers=headers)
	if response.status_code != 200:
		name = IMap[id]["name"]
		print("Warning: Unable to retrieve user info for {}, id {} DI time. Code: {}, Response: {}".format(name, id, response.status_code, response.text))
		return -1
	return response.text


def sign_di_roster(ids):
	completed = []
	url = "https://usafa0.sharepoint.com/sites/LoFiDI/_api/web/lists/GetByTitle('{}')/Items".format(JsonData["sharepoint-di"])
	for id in ids:
		# Updating Token
		get_token()
		userInfo = get_user_info(id)
		if userInfo == -1:
			break
		userInfo = json.loads(userInfo)
		headers = {'Cookie': JsonData["sharepoint-cookie"], 'Accept': 'application/json;odata=verbose', 'X-RequestDigest': Token, 'Content-Type': 'application/json'}
		payload = '{"'+JsonData["sharepoint-di-email"]+'": "'+userInfo["d"][JsonData["sharepoint-roster-email"]]+'", "'+JsonData["sharepoint-di-unit"]+'": "'+userInfo["d"][JsonData["sharepoint-roster-unit"]]+'", "'+JsonData["sharepoint-di-signat"]+'": "'+datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")+'", "'+JsonData["sharepoint-di-signby"]+'": "'+JsonData["bot-name"]+'", "'+JsonData["sharepoint-di-name"]+'": "'+userInfo["d"][JsonData["sharepoint-roster-name"]]+'"}'
		if JsonData["simulate"] == 0:
			response = requests.request("POST", url, headers=headers, data=payload)
			if response.status_code != 201:
				name = IMap[id]["name"]
				print("Warning: Unable to sign di roster for {}, id {} DI time. Code: {}, Response: {}".format(name, id, response.status_code, response.text))
				continue
		completed.append(id)
	return completed


def intersection_array(completedRoster, completedTimes):
	both = []
	for x in completedTimes:
		if x in completedRoster:
			both.append(x)
	return both


if __name__ == "__main__":
	# Wait until 7:15 to start body of script
	wait_to_start()
	print("Log: Starting bot at {}".format(datetime.datetime.now()))
	# Read config file
	JsonData = read_json(JsonFileLocation)
	# Load running file
	ready_running_file()
	RunningData = read_json(JsonData["running-data"])
	# Get group info
	groupInfo = get_group_info()
	# Send message to group
	if RunningData["secondary-messages"][0] == 0:
		send_group_message(JsonData["group-message-text"])
	# Convert groupme ids to sharepoint ids
	IdTable = load_id_table()
	# Build ID maps for reference
	print("Log: Building Maps", end='')
	build_maps(groupInfo)
	print("..Done")
	# Set times to send reminder messages and when to end the program
	secondMessageTime = datetime.datetime.today().replace(hour=20, minute=0, second=0, microsecond=0)
	dmTime = datetime.datetime.today().replace(hour=20, minute=30, second=0, microsecond=0)
	endTime = datetime.datetime.today().replace(hour=1, minute=30, second=0, microsecond=0) + datetime.timedelta(days=1)
	current = datetime.datetime.now()
	# Start loop to run checks for likes.  Will send new messages based on annoying parameter
	while current < endTime:
		# This print is for verbosity and to see that the program is still running
		print("Log: Loop at {}".format(datetime.datetime.now()))
		# Check if any message has likes
		foundLikes = get_messages_likes()
		# Compare against seen likes to get new likes
		newLikes = get_new_likes(RunningData["likes"], foundLikes)
		# Convert liked ids to sharepoint ids
		newIds = convert_ids(newLikes)
		# Update DI roster time
		completedTimes = update_DI_times(newIds)
		# Sign DI roster
		completedRoster = sign_di_roster(newIds)
		# Get ids in both completed sign and update
		completed = intersection_array(completedRoster, completedTimes)
		for id in completed:
			print("Log: Bot has signed for {}".format(IMap[id]["name"]))
			RunningData["likes"].append(IMap[id]["gid"])
		# If 9 pm send another message
		if current >= secondMessageTime and RunningData["secondary-messages"][1] == 0 and 2 <= JsonData["annoying-level"]:
			print("Log: Sending group text 2")
			send_group_message(JsonData["group-message-text2"])
		# If 10 pm send individual messages
		if current >= dmTime and RunningData["secondary-messages"][2] == 0 and 3 == JsonData["annoying-level"]:
			print("Log: Sending dms")
			missing = []
			for id in IdTable:
				if id not in RunningData["likes"] and IdTable[id] != 'null':
					missing.append(id)
			if len(missing) == 0:
				continue
			for id in missing:
				send_direct_messages(id, JsonData["dm-message-text"])
		save_running_data()
		time.sleep(60 - time.time() % 60)
		current = datetime.datetime.now()
	print("Log: LikeForDI should be all done. {}".format(datetime.datetime.now()))
