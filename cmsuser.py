from threading import Lock
from constants import MAX_INTERESTS
import conference
import booking

class User:
    users = {}
    users_lock = Lock()  # Lock to protect access to the users dictionary
    
    def __init__(self, userId, interests):
        with User.users_lock:
            # check that userId is alphanumeric
            if not isinstance(userId, str) or not userId.isalnum():
                raise ValueError("userId must be alphanumeric")
            if userId in User.users.keys():
                raise ValueError("User already exists")
            self.userId = userId

            # interests is a comma-separated string of maximum 50 interests
            if not isinstance(interests, str):
                raise ValueError("Interests must be a comma-separated string")
            interest_list = interests.split(',')
            if len(interest_list) > MAX_INTERESTS:
                raise ValueError("Number of interests cannot be more than", MAX_INTERESTS)

            self.interests = []
            for interest in interest_list:
                # interest can be alphanumeric with spaces allowed
                if not all(char.isalnum() or char.isspace() for char in interest):
                    raise ValueError("One of the interests contains special characters")
                self.interests.append(interest)
            self.bookings = {}
            User.users[userId] = self
    
    def any_overlapping_conferences(self, conference: conference.Conference):
        with User.users_lock:
            for booking in self.bookings.values():
                if booking.status == "cancelled":
                    continue
                conf = conference.Conference.conferences[booking.conf_name]
                if conf.conference_overlaps(conference):
                    return True
        return False
    
    def get_overlapping_conferences(self, conference: conference.Conference):
        overlapping_conferences = []
        with User.users_lock:
            for booking in self.bookings.values():
                if booking.status == "cancelled":
                    continue
                conf = conference.Conference.conferences[booking.conf_name]
                if conf.conference_overlaps(conference):
                    overlapping_conferences.append(conf)
        return overlapping_conferences
    
    def get_booking_id(self, conference: conference.Conference):
        with User.users_lock:
            for booking in self.bookings.values():
                if booking.conf_name == conference.name and booking.status != "cancelled":
                    return booking.bookingId
        return None
    
    def remove_from_overlapping_waitlists(self, conference: conference.Conference):
        overlapping_conferences = self.get_overlapping_conferences(conference)
        with User.users_lock:
            for conf in overlapping_conferences:
                conf.waitlist.remove(self.userId)
                # remove it from his bookings for that conference as well
                for booking_id, booking in list(self.bookings.items()):
                    if booking.status == "cancelled":
                        continue
                    if booking.conf_name == conf.name:
                        self.bookings.pop(booking_id)
                        # remove it from the global bookings
                        booking.Booking.bookings.pop(booking_id)
                        break
                
    def get_booking_status(self, booking_id):
        with User.users_lock:
            if booking_id in self.bookings:
                booking = booking.Booking.bookings[booking_id]
                if booking.status == "waitlisted":
                    response = "Status: Waitlisted" 
                    if conference.Conference.conferences[booking.conf_name].available_slots > 0:
                        response += " - A slot is now available"
                    return response
        return None
    
    def confirm_waitlist_booking(self, booking_id):
        with User.users_lock:
            if booking_id in self.bookings:
                booking = booking.Booking.bookings[booking_id]
                if booking.status == "waitlisted":
                    conf = conference.Conference.conferences[booking.conf_name]
                    if conf.available_slots > 0:
                        conf.available_slots -= 1
                        conf.attendees.append(self.userId)
                        booking.status = "confirmed"
                        self.bookings[booking_id].status = "confirmed"
                        self.remove_from_overlapping_waitlists(conf)
                        return "Booking confirmed"
        return None
    
    def cancel_booking(self, booking_id):
        with User.users_lock:
            if booking_id in self.bookings:
                booking = booking.Booking.bookings[booking_id]
                if booking.status in ["confirmed", "waitlisted"]:
                    conf = conference.Conference.conferences[booking.conf_name]
                    conf.available_slots += 1
                    conf.attendees.remove(self.userId)
                    booking.status = "cancelled"
                    self.bookings[booking_id].status = "cancelled"
                    
                    # for this conference, set the timer for the person at front of waitlist to confirm
                    conf.start_timer()
                    return "Booking cancelled"
        return None
    
    @staticmethod
    def list_users(option):
        with User.users_lock:
            if option == "default":
                print(User.users)
            elif option == "detailed":
                for user in User.users.values():
                    print("User ID:", user.userId)
                    print("Interests:", user.interests)
                    print("User bookings:", user.bookings)
                    print()
