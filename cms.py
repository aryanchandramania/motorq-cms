"""Defines the main app"""

import cmsuser
import conference 
import booking 
from datetime import datetime

class App:
    
    def __init__(self):
        self.name = "My App"

    def run(self):
        print(f"Running {self.name}")
    
    def create_user(self, userId, interests):
        return cmsuser.User(userId, interests)
    
    def create_conference(self, name, location, topics, start_date, end_date, available_slots):
        return conference.Conference(name, location, topics, start_date, end_date, available_slots)
    
    def book_conference(self, conf_name, userId):
        return booking.Booking(conf_name, userId)
    
    def list_conferences(self, option="default"):
        return conference.Conference.list_conferences(option)
    
    def list_users(self, option="default"):
        return cmsuser.User.list_users(option)
    
    def cancel_booking(self, bookingId):
        return booking.Booking.cancel_booking(bookingId)
        
app = App()
app.run()

app.create_user("aryan", "hello")
app.create_user("harsh", "bye")

app.create_conference("icsa", "hyd", "se", datetime.now(), datetime.now(), 10)
app.create_conference("iros", "blr", "robotics", datetime.now(), datetime.now(), 20)

app.book_conference("icsa", "aryan")

app.list_users("detailed")
app.list_conferences("detailed")