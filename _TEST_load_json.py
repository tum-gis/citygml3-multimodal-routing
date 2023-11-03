# Script to load the json file
import json


def load_json(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        data = json.load(f)
    return data

if __name__ == '__main__':
    data = load_json('trafficSignCodes.json')
    print(data)