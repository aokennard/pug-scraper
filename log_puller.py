import os.path
import json
import requests

LIST_PROTO_URL = "http://logs.tf/api/v1/log?uploader="
JSON_PROTO_URL = "http://logs.tf/json/"
SID64_erynn = "[U:1:55303461]"


def get_id_log_list(uploader=SID64_erynn, **kwargs):
    url_argument_count = 0
    if kwargs is not None:
        url_argument_count += sum([0 if arg is None else 1 for arg in kwargs.values()])
    
    log_list_url = LIST_PROTO_URL + uploader + "&"
    for arg_idx in range(url_argument_count):
        log_list_url += "{" + str(arg_idx) + "}"
    
    format_list = ["=".join([arg_name, arg]) + "&" for arg_name, arg in kwargs.items()]
    print(format_list, log_list_url)
    log_list_url = log_list_url.format(*format_list)
    log_list_url = log_list_url[:-1] # strip final &
    logs_req = requests.get(log_list_url).json()["logs"]
    log_id_list = []
    #not_seen(0)
    recent = 0#get_newest_log_time()
    for entry in logs_req:
        if "PugChamp" in entry["title"] and recent < int(entry["date"]):
            log_id_list.append(entry["id"])
    print(logs_req)
    return log_id_list

def make_json_list(id_list, of="pug-jsons.json"):
    data = {}
    if os.path.isfile(of):
        data = json.loads(of)
    else:
        out_f = open(of, "w")
    for game_id in id_list:
        game_log = requests.get(JSON_PROTO_URL + str(game_id))
        game_json = game_log.json()
        data[str(game_id)] = game_json
    
    json.dump(data, out_f)
    out_f.close()

def get_newest_log_time():
    if os.path.isfile("recent_ts"):
        time_f = open("recent_ts")
        line = time_f.readline()
        print(line)
        ts = int(line.strip())
        return ts
    _ = open("recent_ts", "w+")
    _.write("0")
    return 0
    

#for filtering out already observed logs from requests, using timestamp instead of actual ids
def not_seen(log_ts):
    pugfile = open("pug-jsons.json")
    json_f = json.load(pugfile)
    
    largest_ts = get_newest_log_time() # should cache the most recent ts later
    if largest_ts != 0:
        return log_ts > largest_ts
    for log_id in json_f:
        cur_ts = json_f[log_id]["info"]["date"]
        if cur_ts > largest_ts:
            largest_ts = cur_ts
    recent_ts_f = open("recent_ts", "w")
    recent_ts_f.write(str(largest_ts))
    if largest_ts < log_ts:
        # need to pull stuff
        return True
    return False


l = get_id_log_list(limit='50000')
#print("Writing to json file..")
make_json_list(l) 
