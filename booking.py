from threading import Lock
import conference
import cmsuser
from datetime import datetime

class Booking:
    bookings = {}
    bookings_lock = Lock()  # Lock to protect access to the bookings dictionary

    # Constructor
    def __init__(self, conf_name, userId):
        with Booking.bookings_lock:
            if conf_name not in conference.Conference.conferences:
                raise ValueError("Conference does not exist")
            
            conf = conference.Conference.conferences[conf_name]
            user = cmsuser.User.users.get(userId)
            
            if not user:
                raise ValueError("User does not exist")
            if user in conf.attendees:
                bookingId = user.get_booking_id(conf)
                raise ValueError("User is already registered for this conference with booking ID", bookingId)
            
            if conf.available_slots == 0:
                conf.waitlist.append(userId)
                self.status = "waitlisted"
            else:
                if user.any_overlapping_conferences(conf):
                    raise ValueError("User is already registered for a conference at the same time")
                conf.attendees.append(userId)
                conf.available_slots -= 1
                self.status = "confirmed"

            self.conf_name = conf_name
            self.userId = userId
            self.bookingId = len(Booking.bookings) + 1
            
            # Add booking to the global bookings dictionary
            Booking.bookings[self.bookingId] = self
            # Add booking to the user's bookings
            user.bookings[self.bookingId] = self

    @staticmethod
    def cancel_booking(bookingId):
        with Booking.bookings_lock:
            booking = Booking.bookings.get(bookingId)
            if not booking:
                return "Booking does not exist"
            
            user = cmsuser.User.users.get(booking.userId)
            if not user:
                return "User does not exist"
            
            return user.cancel_booking(bookingId)
