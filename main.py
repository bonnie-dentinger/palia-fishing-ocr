import screen_ocr
from datetime import datetime
from pymongo import MongoClient
import os
import time


def run_reader():
    ocr_reader = screen_ocr.Reader.create_fast_reader()

    results = ocr_reader.read_screen()
    results_as_string = results.as_string()

    # try to prevent false positives, work in progress
    needed_words = ['Press', 'Enter', 'to', 'chat']
    not_needed_words = ['Value', 'Inventory', 'Next shipment']
    if not all(word in results_as_string for word in needed_words) or any(word in results_as_string for word in not_needed_words):
        return
    
    fish_names = get_fish()
    found_name = get_fish_from_results(results_as_string, fish_names)

    if found_name:
        time_of_day = calculate_palia_tod()
        fish = db.fish_info.find_one({ 'name': found_name, 'time_of_day': time_of_day })
        initial_caught = fish['num_caught']
        fish_caught = initial_caught + 1
        data = db.fish_info.update_one({ 'name': found_name, 'time_of_day': time_of_day }, { '$set': { 'num_caught': fish_caught } })
        locations = fish['locations']
        bait = fish['bait']
        location = db.fishing_locations.find_one({'location': locations, 'time_of_day': time_of_day, 'bait': bait})
        initial_caught = location['total_caught']
        total_fish = initial_caught + 1
        data2 = db.fishing_locations.update_one({ 'location': locations, 'time_of_day': time_of_day, 'bait': bait }, { '$set': { 'total_caught': total_fish } })
        print(f'Caught {found_name}! Users have caught {fish_caught} {found_name} in the {time_of_day.lower()}.')
        time.sleep(20)

def calculate_palia_tod():

    # palia's time works as 1 day per every 1 real time hour. 1 real time hour = 1 palia day
    # palia's time is 24 hours, 1 day = 24 hours
    # palia's 12:00 PM == xx:30 irl
    # palia's 12:00 AM == xx:00 irl
    # palia's time (12 hour clock)

    # 2.5 irl minutes = 1 palia hour
    # 2.5 irl seconds = 1 palia minute
    # in one irl hour, # of palia seconds = 60 * 60 / 2.5 = 1440 (approximate)
    
    current_time = datetime.now()
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second
    palia_time_in_seconds = (hour * 60 * 60 + minute * 60 + second) / 2.5
    palia_hour = palia_time_in_seconds % 1440
    palia_hour = palia_hour / 60
    palia_hour = palia_hour % 24
    palia_hour = int(palia_hour)

    if palia_hour >= 3 and palia_hour < 6:
        time_of_day = 'Morning'
    elif palia_hour >= 6 and palia_hour < 18:
        time_of_day = 'Day'
    elif palia_hour >= 18 and palia_hour < 21:
        time_of_day = 'Evening'
    elif palia_hour >= 21 or palia_hour < 3:
        time_of_day = 'Night'
    
    return time_of_day

def get_fish():
    # get fish names from fish_list.txt
    with open('fish_list.txt', 'r') as f:
        fish_names = []
        for line in f:
            line = line.split(',')
            name = line[0]
            fish_names.append(name)

    return fish_names

def get_fish_from_results(results_string, fish_names):
    for fish in fish_names:
        fish_name = fish.strip()
        if fish_name in results_string:
            return fish_name
    return None

if __name__ == '__main__':
    print('Welcome to the Palia Fishing OCR! Press Ctrl+C to exit.')
    print('Make sure you have the Palia window open and and in windowed fullscreen mode.')
    print('Start fishing!')

    from config import MONGODB_URI
    client = MongoClient(MONGODB_URI)

    db = client['palia']

    while True:
        run_reader()
