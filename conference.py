from threading import Lock
from datetime import datetime, timezone
from constants import MAX_TOPICS_PER_CONF
import booking
import cmsuser
import pprint

class Conference:
    conferences = {}
    conferences_lock = Lock()  # Lock to protect access to the conferences dictionary

    # Constructor
    def __init__(self, name, location, topics, start_date, end_date, available_slots):
        with Conference.conferences_lock:
            if not isinstance(name, str) or not all(char.isalnum() or char.isspace() for char in name):
                raise ValueError("Name must be alphanumeric")

            # if conference is already in the list, raise an error
            for conference in Conference.conferences.values():
                if conference.name == name:
                    raise ValueError("Conference already exists")
            self.name = name

            if not isinstance(location, str) or not all(char.isalnum() or char.isspace() for char in location):
                raise ValueError("Location must be alphanumeric")
            self.location = location

            if not isinstance(topics, str):
                raise ValueError("Topics must be a comma-separated string")
            topic_list = topics.split(',')
            self.topics = []
            if len(topic_list) > MAX_TOPICS_PER_CONF:
                raise ValueError("Number of topics cannot be more than", MAX_TOPICS_PER_CONF)
            for topic in topic_list:
                if not all(char.isalnum() or char.isspace() for char in topic):
                    raise ValueError("One of the topics contains special characters")
                self.topics.append(topic)

            # start date should be in UTC format
            if not isinstance(start_date, datetime) or start_date.tzinfo != timezone.utc:
                raise ValueError("Start date should be in UTC datetime format")

            # end date should be in UTC format
            if not isinstance(end_date, datetime) or end_date.tzinfo != timezone.utc:
                raise ValueError("End date should be in UTC datetime format")

            # end date should be greater than start date and duration should not exceed 12 hours
            if end_date < start_date or (end_date - start_date).total_seconds() > 43200:
                raise ValueError("End date should be greater than start date and duration should not exceed 12 hours")

            self.start_date = start_date
            self.end_date = end_date

            if not isinstance(available_slots, int) or available_slots <= 0:
                raise ValueError("Available slots should be greater than 0")
            self.available_slots = available_slots
            self.attendees = []
            self.waitlist = []

            Conference.conferences[name] = self

    def slots_remaining(self):
        with Conference.conferences_lock:
            return self.available_slots - len(self.attendees)

    def conference_overlap(self, conf2):
        with Conference.conferences_lock:
            if self.start_date < conf2.end_date and self.end_date > conf2.start_date:
                return True
            return False

    def remove_from_waitlisted_bookings(self):
        with Conference.conferences_lock:
            for user in self.waitlist:
                user.bookings.remove(self)
            for booking_id, booking_obj in list(booking.Bookings.bookings.items()):
                if booking_obj.conf_name == self.name:
                    booking.Bookings.bookings.pop(booking_id)
            self.waitlist = []

    def start_timer(self):
        with Conference.conferences_lock:
            slots = self.available_slots
            for _ in range(slots):
                if self.waitlist:
                    userId = self.waitlist[0]
                    current_user = cmsuser.User.users[userId]
                    for booking_obj in current_user.bookings.values():
                        if booking_obj.conf_name == self.name and booking_obj.status == "waitlisted":
                            booking_obj.slot_opening_time = datetime.now()
                else:
                    break

    def update_waitlist(self):
        with Conference.conferences_lock:
            # if it has been more than 1 hour since the booking's slot opening time, remove the user from the waitlist and add them to the end
            for userId in list(self.waitlist):
                current_user = cmsuser.User.users[userId]
                for booking_obj in current_user.bookings.values():
                    if booking_obj.conf_name == self.name and booking_obj.status == "waitlisted":
                        if (datetime.now() - booking_obj.slot_opening_time).total_seconds() > 3600:
                            self.waitlist.remove(userId)
                            self.waitlist.append(userId)
                            break

    @staticmethod
    def list_conferences(option):
        with Conference.conferences_lock:
            if option == "default":
                pprint.pprint(Conference.conferences)
            elif option == "detailed":
                # print conference details along with attendees and waitlist
                for conference in Conference.conferences.values():
                    print("Conference Name:", conference.name)
                    print("Location:", conference.location)
                    print("Topics:", conference.topics)
                    print("Start Date:", conference.start_date)
                    print("End Date:", conference.end_date)
                    print("Available Slots:", conference.available_slots)
                    print("Attendees:", conference.attendees)
                    print("Waitlist:", conference.waitlist)
                    print("\n")
