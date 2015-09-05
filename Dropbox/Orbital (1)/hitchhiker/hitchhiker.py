import cgi
import urllib
import webapp2
import jinja2
import os
import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import mail

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

# Datastore definitions
class Persons(ndb.Model):
    # Models a person. Key is the email.
    next_offer = ndb.IntegerProperty()
    next_request = ndb.IntegerProperty()
    next_received_offer = ndb.IntegerProperty()
    next_received_request = ndb.IntegerProperty()
    
class Offers(ndb.Model):
    # Models an offer. Key is person.next_offer
    number = ndb.IntegerProperty()
    owner = ndb.StringProperty()
    date = ndb.DateProperty()
    time = ndb.TimeProperty()
    start_location = ndb.StringProperty()
    start_zipcode = ndb.StringProperty()
    destination = ndb.StringProperty()
    destination_zipcode = ndb.StringProperty()
    remark = ndb.StringProperty()
    requested = ndb.StringProperty(default="No")
    offer_sent = ndb.StringProperty(default="No")

class Requests(ndb.Model):
    # Models a request. Key is person.next_request
    number = ndb.IntegerProperty()
    owner = ndb.StringProperty()
    date = ndb.DateProperty()
    time = ndb.TimeProperty()
    start_location = ndb.StringProperty()
    start_zipcode = ndb.StringProperty()
    destination = ndb.StringProperty()
    destination_zipcode = ndb.StringProperty()
    remark = ndb.StringProperty()
    offered = ndb.StringProperty(default="No")
    request_sent = ndb.StringProperty(default="No")

class ReceivedOffers(ndb.Model):
    # Models a received offer. Key is person.next_received_offer
    number = ndb.IntegerProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    offered_datetime = ndb.DateTimeProperty(auto_now_add=True)
    date = ndb.DateProperty()
    time = ndb.TimeProperty()
    start_location = ndb.StringProperty()
    start_zipcode = ndb.StringProperty()
    destination = ndb.StringProperty()
    destination_zipcode = ndb.StringProperty()
    remark = ndb.StringProperty()
    for_request = ndb.IntegerProperty()

class ReceivedRequests(ndb.Model):
    # Models a received request. Key is person.next_received_request
    number = ndb.IntegerProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    requested_datetime = ndb.DateTimeProperty(auto_now_add=True)
    date = ndb.DateProperty()
    time = ndb.TimeProperty()
    start_location = ndb.StringProperty()
    start_zipcode = ndb.StringProperty()
    destination = ndb.StringProperty()
    destination_zipcode = ndb.StringProperty()
    remark = ndb.StringProperty()
    for_offer = ndb.IntegerProperty()
    
class OfferDates(ndb.Model):
    # Models a date, isoformat() of date is the key
    date = ndb.DateProperty()
    #stores a list of all the offers on the date
    offers = ndb.PickleProperty()

class RequestDates(ndb.Model):
    # Models a date, isoformat() of date is the key
    date = ndb.DateProperty()
    #stores a list of all the requests on the date
    requests = ndb.PickleProperty()

# Handling Errors:
class InputError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class DatePassedError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# Handlers
class MainPage(webapp2.RequestHandler):
    # Handler for the front page.
    def get(self):
        template = jinja_environment.get_template('homepage.html')
        self.response.out.write(template.render())

class AboutUs(webapp2.RequestHandler):
    # Handler for About Us
    def get(self):
        user = users.get_current_user()
        if user: #already signed in
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('aboutusloggedin.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('aboutus.html')
            self.response.out.write(template.render())

class FAQ(webapp2.RequestHandler):
    # Handler for FAQ`
    def get(self):
        user = users.get_current_user()
        if user: #already signed in
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('faqloggedin.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('faq.html')
            self.response.out.write(template.render())

class MainPageUser(webapp2.RequestHandler):
    # Handler for the front page when logged in
    def get(self):
        user = users.get_current_user()
        if user: #already signed in
            # Retrieve person
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            
            template = jinja_environment.get_template('homepageloggedin.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class MakeOffer(webapp2.RequestHandler):
    # Handler for Make New Offer Page
    def get(self):
        user = users.get_current_user()
        if user: #already signed in                            
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            
            template = jinja_environment.get_template('makenewoffer.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

    def post(self):
        # Retrieve person
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()
        if person == None or person.next_offer == None:
            person = Persons(id=users.get_current_user().email())
            person.next_offer = 1
        try:
            offer = Offers(parent=parent, id=str(person.next_offer))
            offer.number = person.next_offer
            offer.owner = users.get_current_user().email()
            day = self.request.get('day')
            month = self.request.get('month')
            year = self.request.get('year')
            date = datetime.date(int(year), int(month), int(day))
            offer.date = date
            hour = self.request.get('hour')
            minute = self.request.get('min')
            offer.time = datetime.time(int(hour), int(minute), 0)
            offer.start_location = self.request.get('start_location')
            offer.start_zipcode = self.request.get('start_zipcode')
            offer.destination = self.request.get('destination')
            offer.destination_zipcode = self.request.get('destination_zipcode')
            offer.remark = self.request.get('remark')
            # checking if the input date has already passed
            current_datetime = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_date = current_datetime.date()
            current_time = current_datetime.time()

            if offer.start_location == '' or offer.start_zipcode == '' or offer.destination == '' or offer.destination_zipcode == '':
                raise InputError("Invalid input")
            elif offer.date < current_date:
                raise DatePassedError("Date has passed")
            elif offer.date == current_date and offer.time < current_time:
                raise DatePassedError("Date has passed")
            else:
                # Retrieve date
                offer_date_key = ndb.Key('OfferDates', date.isoformat())
                offer_date = offer_date_key.get()
                if offer_date == None:
                    offer_date = OfferDates(id=date.isoformat())
                    offer_date.date = date
                    offer_date.offers = []

                person.next_offer += 1
                person.put()
                offer.put()
                offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', str(offer.number))
                offer_date.offers.append(offer_key)
                offer_date.put()

                template_values = {
                    'user_mail': users.get_current_user().email(),
                    'logout': users.create_logout_url(self.request.host_url),
                    'person': person,
                    }
                template = jinja_environment.get_template('successfuloffer.html')
                self.response.out.write(template.render(template_values))
        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewoffer.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please choose a valid date."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewoffer.html')
            self.response.out.write(template.render(template_values))
        except DatePassedError:
            error = "Invalid date input: the date and time you chose has already passed. Please choose another date."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewoffer.html')
            self.response.out.write(template.render(template_values))
        
class ManageOffer(webapp2.RequestHandler):
    # Handler for Manage My Offers page
    def get(self):
        user = users.get_current_user()
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Offers "
                        "WHERE ANCESTOR IS :1 "
                        "ORDER BY date ASC",
                        parent_key)

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'offers': query,
        }
            
        template = jinja_environment.get_template('manageoffer.html')
        self.response.out.write(template.render(template_values))
        
class MakeRequest(webapp2.RequestHandler):
    # Handler for Make New Request Page
    def get(self):
        user = users.get_current_user()
        if user: #already signed in
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            
            template = jinja_environment.get_template('makenewrequest.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

    def post(self):
        # Retrieve person
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()
        if person == None or person.next_request == None:
            person = Persons(id=users.get_current_user().email())
            person.next_request = 1
        try:
            request = Requests(parent=parent, id=str(person.next_request))
            request.number = person.next_request
            request.owner = users.get_current_user().email()
            day = self.request.get('day')
            month = self.request.get('month')
            year = self.request.get('year')
            date = datetime.date(int(year), int(month), int(day))
            request.date = date
            hour = self.request.get('hour')
            minute = self.request.get('min')
            request.time = datetime.time(int(hour), int(minute), 0)
            request.start_location = self.request.get('start_location')
            request.start_zipcode = self.request.get('start_zipcode')
            request.destination = self.request.get('destination')
            request.destination_zipcode = self.request.get('destination_zipcode')
            request.remark = self.request.get('remark')
            # checking if the input date has already passed
            current_datetime = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_date = current_datetime.date()
            current_time = current_datetime.time()

            if request.start_location == '' or request.start_zipcode == '' or request.destination == '' or request.destination_zipcode == '':
                raise InputError("Invalid input")
            elif request.date < current_date:
                raise DatePassedError("Date has passed")
            elif request.date == current_date and request.time < current_time:
                raise DatePassedError("Date has passed")
            else:
                # Retrieve date
                request_date_key = ndb.Key('RequestDates', date.isoformat())
                request_date = request_date_key.get()
                if request_date == None:
                    request_date = RequestDates(id=date.isoformat())
                    request_date.date = date
                    request_date.requests = []

                person.next_request += 1
                person.put()
                request.put()
                request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', str(request.number))
                request_date.requests.append(request_key)
                request_date.put()

            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('successfulrequest.html')
            self.response.out.write(template.render(template_values))
        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewrequest.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please choose a valid date."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewrequest.html')
            self.response.out.write(template.render(template_values))
        except DatePassedError:
            error = "Invalid date input: the date and time you chose has already passed. Please choose another date."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('makenewrequest.html')
            self.response.out.write(template.render(template_values))

class ManageRequest(webapp2.RequestHandler):
    # Handler for Manage My Request page
    def get(self):
        user = users.get_current_user()
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Requests "
                        "WHERE ANCESTOR IS :1 "
                        "ORDER BY date ASC",
                        parent_key)
                            
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'requests': query,
        }
            
        template = jinja_environment.get_template('managerequest.html')
        self.response.out.write(template.render(template_values))

class DeleteOffer(webapp2.RequestHandler):
    # Delete an offer
    def post(self):
        offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
        offer = offer_key.get()       
        offer_date_key = ndb.Key('OfferDates', offer.date.isoformat())
        offer_date = offer_date_key.get()
        offer_date.offers.remove(offer_key)
        offer_date.put()
        offer_key.delete()
        self.redirect('/manageoffer')

class DeleteRequest(webapp2.RequestHandler):
    # Delete request
    def post(self):
        request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
        request = request_key.get()
        request_date_key = ndb.Key('RequestDates', request.date.isoformat())
        request_date = request_date_key.get()
        request_date.requests.remove(request_key)
        request_date.put()
        request_key.delete()
        self.redirect('/managerequest')

# For editing an offer
class GetOffer(webapp2.RequestHandler):
    # Get the details of offer that needs editing
    def post(self):
        user = users.get_current_user()
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve item that needs editing
        person = parent_key.get()
        edit_offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
        edit_offer = edit_offer_key.get()
        day = edit_offer.date.day
        month = edit_offer.date.month
        year = edit_offer.date.year
        hour = edit_offer.time.hour
        minute = edit_offer.time.minute
                           
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'edit_offer': edit_offer,
            'edit_offer_day': day,
            'edit_offer_month': month,
            'edit_offer_year': year,
            'edit_offer_hour': hour,
            'edit_offer_min': minute,
            }
            
        template = jinja_environment.get_template('editoffer.html')
        self.response.out.write(template.render(template_values))

class EditOffer(webapp2.RequestHandler):
    # Edit an offer's details
    def post(self):
        offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
        offer = offer_key.get()
        old_date = offer.date.isoformat()
        try:
            # Retrieve the list of offers on the date
            offer_date_key = ndb.Key('OfferDates', old_date)
            offer_date = offer_date_key.get()
            # forming date and time:
            day = self.request.get('day')
            month = self.request.get('month')
            year = self.request.get('year')
            date = datetime.date(int(year), int(month), int(day))
            hour = self.request.get('hour')
            minute = self.request.get('min')
            time = datetime.time(int(hour), int(minute), 0)
            # checking if the input date has already passed
            current_datetime = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            if self.request.get('start_location') == '' or self.request.get('start_zipcode') == '' or self.request.get('destination') == '' or self.request.get('destination_zipcode') == '':
                raise InputError("Incomplete form")
            elif date < current_date:
                raise DatePassedError("Date has passed")
            elif date == current_date and time < current_time:
                raise DatePassedError("Date has passed")

            offer.date = date
            offer.time = time
            offer.start_location = self.request.get('start_location')
            offer.start_zipcode = self.request.get('start_zipcode')
            offer.destination = self.request.get('destination')
            offer.destination_zipcode = self.request.get('destination_zipcode')
            offer.remark = self.request.get('remark')
            
            # Remove the offer from the list first
            offer_date.offers.remove(offer_key)
            # Update the list of offers for respective dates if dates are changed
            new_date = offer.date.isoformat()
            if old_date == new_date:
                offer_date.offers.append(offer_key)
            else:
                new_offer_date_key = ndb.Key('OfferDates', new_date)
                new_offer_date = new_offer_date_key.get()
                if new_offer_date == None:
                    new_offer_date = OfferDates(id=new_date)
                    new_offer_date.offers = []
                new_offer_date.offers.append(offer_key)
                new_offer_date.put()
            # Update the rest
            offer.put()
            offer_date.put()
            self.redirect('/manageoffer')
        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
            edit_offer = edit_offer_key.get()
            day = edit_offer.date.day
            month = edit_offer.date.month
            year = edit_offer.date.year
            hour = edit_offer.time.hour
            minute = edit_offer.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_offer': edit_offer,
                'edit_offer_day': day,
                'edit_offer_month': month,
                'edit_offer_year': year,
                'edit_offer_hour': hour,
                'edit_offer_min': minute,
                }
                
            template = jinja_environment.get_template('editoffer.html')
            self.response.out.write(template.render(template_values))
        except DatePassedError:
            error = "Invalid date input: the date and time you chose has already passed. Please choose another date."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
            edit_offer = edit_offer_key.get()
            day = edit_offer.date.day
            month = edit_offer.date.month
            year = edit_offer.date.year
            hour = edit_offer.time.hour
            minute = edit_offer.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_offer': edit_offer,
                'edit_offer_day': day,
                'edit_offer_month': month,
                'edit_offer_year': year,
                'edit_offer_hour': hour,
                'edit_offer_min': minute,
                }
                
            template = jinja_environment.get_template('editoffer.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please choose a valid date."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('offernumber'))
            edit_offer = edit_offer_key.get()
            day = edit_offer.date.day
            month = edit_offer.date.month
            year = edit_offer.date.year
            hour = edit_offer.time.hour
            minute = edit_offer.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_offer': edit_offer,
                'edit_offer_day': day,
                'edit_offer_month': month,
                'edit_offer_year': year,
                'edit_offer_hour': hour,
                'edit_offer_min': minute,
                }
                
            template = jinja_environment.get_template('editoffer.html')
            self.response.out.write(template.render(template_values))
      
# For editing a request
class GetRequest(webapp2.RequestHandler):
    # Get the details of request that needs editing
    def post(self):
        user = users.get_current_user()
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve item that needs editing
        person = parent_key.get()
        edit_request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
        edit_request = edit_request_key.get()
        day = edit_request.date.day
        month = edit_request.date.month
        year = edit_request.date.year
        hour = edit_request.time.hour
        minute = edit_request.time.minute
                           
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'edit_request': edit_request,
            'edit_request_day': day,
            'edit_request_month': month,
            'edit_request_year': year,
            'edit_request_hour': hour,
            'edit_request_min': minute,
            }
        
        template = jinja_environment.get_template('editrequest.html')
        self.response.out.write(template.render(template_values))

class EditRequest(webapp2.RequestHandler):
    # Edit a request's details
    def post(self):
        request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
        request = request_key.get()
        old_date = request.date.isoformat()
        try:
            # Retrieve the list of requests on the date
            request_date_key = ndb.Key('RequestDates', old_date)
            request_date = request_date_key.get()
            # forming date and time:
            day = self.request.get('day')
            month = self.request.get('month')
            year = self.request.get('year')
            date = datetime.date(int(year), int(month), int(day))
            hour = self.request.get('hour')
            minute = self.request.get('min')
            time = datetime.time(int(hour), int(minute), 0)
            # checking if the input date has already passed
            current_datetime = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            if self.request.get('start_location') == '' or self.request.get('start_zipcode') == '' or self.request.get('destination') == '' or self.request.get('destination_zipcode') == '':
                raise InputError("Incomplete form")
            elif date < current_date:
                raise DatePassedError("Date has passed")
            elif date == current_date and time < current_time:
                raise DatePassedError("Date has passed")
            
            request.date = date
            request.time = time
            request.start_location = self.request.get('start_location')
            request.start_zipcode = self.request.get('start_zipcode')
            request.destination = self.request.get('destination')
            request.destination_zipcode = self.request.get('destination_zipcode')
            request.remark = self.request.get('remark')
     
            # Remove the request from the list first
            request_date.requests.remove(request_key)
            # Update the list of requests for respective dates if dates are changed
            new_date = request.date.isoformat()
            if old_date == new_date:
                request_date.requests.append(request_key)
            else:
                new_request_date_key = ndb.Key('RequestDates', new_date)
                new_request_date = new_request_date_key.get()
                if new_request_date == None:
                    new_request_date = RequestDates(id=new_date)
                    new_request_date.requests = []
                new_request_date.requests.append(request_key)
                new_request_date.put()

            # Update the rest
            request.put()
            request_date.put()
            self.redirect('/managerequest')

        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
            edit_request = edit_request_key.get()
            day = edit_request.date.day
            month = edit_request.date.month
            year = edit_request.date.year
            hour = edit_request.time.hour
            minute = edit_request.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_request': edit_request,
                'edit_request_day': day,
                'edit_request_month': month,
                'edit_request_year': year,
                'edit_request_hour': hour,
                'edit_request_min': minute,
                }
            
            template = jinja_environment.get_template('editrequest.html')
            self.response.out.write(template.render(template_values))
        except DatePassedError:
            error = "Invalid date input: the date and time you chose has already passed. Please choose another date."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
            edit_request = edit_request_key.get()
            day = edit_request.date.day
            month = edit_request.date.month
            year = edit_request.date.year
            hour = edit_request.time.hour
            minute = edit_request.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_request': edit_request,
                'edit_request_day': day,
                'edit_request_month': month,
                'edit_request_year': year,
                'edit_request_hour': hour,
                'edit_request_min': minute,
                }
            
            template = jinja_environment.get_template('editrequest.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please choose a valid date."
            # Get the details of request that needs editing
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve item that needs editing
            person = parent_key.get()
            edit_request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('requestnumber'))
            edit_request = edit_request_key.get()
            day = edit_request.date.day
            month = edit_request.date.month
            year = edit_request.date.year
            hour = edit_request.time.hour
            minute = edit_request.time.minute
                               
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'edit_request': edit_request,
                'edit_request_day': day,
                'edit_request_month': month,
                'edit_request_year': year,
                'edit_request_hour': hour,
                'edit_request_min': minute,
                }
            
            template = jinja_environment.get_template('editrequest.html')
            self.response.out.write(template.render(template_values))

# For searching offers by date
class SearchOffer(webapp2.RequestHandler):
    def get(self):
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            }
            
        template = jinja_environment.get_template('searchoffer.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()
        date_id_inverted = self.request.get('dateid')
        date_id = date_id_inverted[6:] + "-" + date_id_inverted[3:5] + "-" + date_id_inverted[:2]
        try: 
            date_obj = datetime.date(int(date_id[:4]), int(date_id[5:7]), int(date_id[8:]))
            offer_date_key = ndb.Key('OfferDates', date_id)
            offer_date = offer_date_key.get()
            if offer_date == None:
                offers = None
            elif offer_date.offers == []:
                offers = None
            else:
                offers_all = offer_date.offers
                offers = []
                for off_key in offers_all:
                    off = off_key.get()
                    if off.owner != users.get_current_user().email():
                        offers.append(off)

                if offers == []:
                    offers = None
                        
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'date': self.request.get('dateid'),
                'offers': offers,
                }
            template = jinja_environment.get_template('searchresultoffers.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please enter a valid date following the format (DD-MM-YYYY)."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }

            template = jinja_environment.get_template('searchoffer.html')
            self.response.out.write(template.render(template_values)) 

# For searching requests by date
class SearchRequest(webapp2.RequestHandler):
    def get(self):
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            }
            
        template = jinja_environment.get_template('searchrequest.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()
        date_id_inverted = self.request.get('dateid')
        date_id = date_id_inverted[6:] + "-" + date_id_inverted[3:5] + "-" + date_id_inverted[:2]
        try:
            date_obj = datetime.date(int(date_id[:4]), int(date_id[5:7]), int(date_id[8:]))
            request_date_key = ndb.Key('RequestDates', date_id)
            request_date = request_date_key.get()
            if request_date == None:
                requests = None
            elif request_date.requests == []:
                requests = None
            else:
                requests = request_date.requests
                requests_all = request_date.requests
                requests = []
                for req_key in requests_all:
                    req = req_key.get()
                    if req.owner != users.get_current_user().email():
                        requests.append(req)

                if requests == []:
                    requests = None

            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'date': self.request.get('dateid'),
                'requests': requests,
                }
            template = jinja_environment.get_template('searchresultrequests.html')
            self.response.out.write(template.render(template_values))
        except ValueError:
            error = "Invalid date input: please enter a valid date following the format (DD-MM-YYYY)."
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                }

            template = jinja_environment.get_template('searchrequest.html')
            self.response.out.write(template.render(template_values)) 

# For someone to send somebody a request
class ContactOffer(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())
        date_id = self.request.get('offer_date')
        year = int(date_id[6:10])
        month = int(date_id[3:5])
        day = int(date_id[:2])
        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Requests "
                        "WHERE ANCESTOR IS :1 AND date = DATE(:2, :3, :4)"
                        "ORDER BY date ASC",
                        parent_key, year, month, day)
                            
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'requests': query,
            'offer_number': self.request.get('offer_number'),
            'offer_owner': self.request.get('offer_owner'),
            'offer_date' : self.request.get('offer_date'),
        }
            
        template = jinja_environment.get_template('contactoffer.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        # Retrieve person
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()

        offerer_key = ndb.Key('Persons', self.request.get('offer_owner'))
        offerer = offerer_key.get()
        offer_key = ndb.Key('Persons', self.request.get('offer_owner'), 'Offers', self.request.get('offer_number'))
        offer = offer_key.get()
        offer.requested = "Yes"
        if offerer.next_received_request == None:
            offerer.next_received_request = 1

        try:
            request_numbers = self.request.get_all('requestnumber')
            if len(request_numbers) == 0:
                raise InputError("No request selected")
            if self.request.get('phone') == '':
                raise InputError("No phone")
            
            for req_num in request_numbers:
                request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', req_num)
                request = request_key.get()
                request.request_sent = "Yes"
                received_req = ReceivedRequests(parent=offerer_key, id=str(offerer.next_received_request))

                received_req.number = offerer.next_received_request
                received_req.email = request.owner
                received_req.phone = self.request.get('phone')
                received_req.date = request.date
                received_req.time = request.time
                received_req.start_location = request.start_location
                received_req.start_zipcode = request.start_zipcode
                received_req.destination = request.destination
                received_req.destination_zipcode = request.destination_zipcode
                received_req.remark = request.remark
                received_req.for_offer = offer.number

                received_req.put()
                request.put()
                offerer.next_received_request += 1

            offer.put()    
            offerer.put()
            #send confirmation email
            message = mail.EmailMessage(sender="HitchHiker Team <nl.chuongthien@gmail.com>",
                                        subject="New Request for your Offer!")

            message.to = self.request.get('offer_owner')
            message.body = """
            Greetings from the HitchHiker Team!

            You have just received a new request for one of your offers.
            You can log in to http://hitchhiker-nus.appspot.com/ now
            and choose 'Manage Received Request' to find out the details of
            the received request.

            Have a good day!


            The HitchHiker Team
            """
            message.send()
            #end of sending confirmation email
            
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }

            template = jinja_environment.get_template('successfulcontactoffer.html')
            self.response.out.write(template.render(template_values))
        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            date_id = self.request.get('offer_date')
            year = int(date_id[6:10])
            month = int(date_id[3:5])
            day = int(date_id[:2])
            query = ndb.gql("SELECT * "
                            "FROM Requests "
                            "WHERE ANCESTOR IS :1 AND date = DATE(:2, :3, :4)"
                            "ORDER BY date ASC",
                            person_key, year, month, day)
                            
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'requests': query,
                'offer_number': self.request.get('offer_number'),
                'offer_owner': self.request.get('offer_owner'),
                'offer_date': self.request.get('offer_date'),
            }
            
            template = jinja_environment.get_template('contactoffer.html')
            self.response.out.write(template.render(template_values))

# To send an offer to someone
class ContactRequest(webapp2.RequestHandler):
    def get(self):
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())
        date_id = self.request.get('request_date')
        year = int(date_id[6:10])
        month = int(date_id[3:5])
        day = int(date_id[:2])
        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Offers "
                        "WHERE ANCESTOR IS :1 AND date = DATE(:2, :3, :4)"
                        "ORDER BY date ASC",
                        parent_key, year, month, day)
                            
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'offers': query,
            'request_number': self.request.get('request_number'),
            'request_owner': self.request.get('request_owner'),
            'request_date' : self.request.get('request_date'),
        }
            
        template = jinja_environment.get_template('contactrequest.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        # Retrieve person
        person_key = ndb.Key('Persons', users.get_current_user().email())
        person = person_key.get()

        requester_key = ndb.Key('Persons', self.request.get('request_owner'))
        requester = requester_key.get()
        request_key = ndb.Key('Persons', self.request.get('request_owner'), 'Requests', self.request.get('request_number'))
        request = request_key.get()
        request.offered = "Yes"
        if requester.next_received_offer == None:
            requester.next_received_offer = 1

        try:
            offer_numbers = self.request.get_all('offernumber')
            if len(offer_numbers) == 0:
                raise InputError("No offer selected")
            if self.request.get('phone') == '':
                raise InputError("No phone")
        
            for off_num in offer_numbers:
                offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', off_num)
                offer = offer_key.get()
                offer.offer_sent = "Yes"
                received_off = ReceivedOffers(parent=requester_key, id=str(requester.next_received_offer))

                received_off.number = requester.next_received_offer
                received_off.email = offer.owner
                received_off.phone = self.request.get('phone')
                received_off.date = offer.date
                received_off.time = offer.time
                received_off.start_location = offer.start_location
                received_off.start_zipcode = offer.start_zipcode
                received_off.destination = offer.destination
                received_off.destination_zipcode = offer.destination_zipcode
                received_off.remark = offer.remark
                received_off.for_request = request.number

                received_off.put()
                offer.put()
                requester.next_received_offer += 1

            request.put()    
            requester.put()
            #send confirmation email
            message = mail.EmailMessage(sender="HitchHiker Team <nl.chuongthien@gmail.com>",
                                        subject="New Offer for your Request!")

            message.to = self.request.get('request_owner')
            message.body = """
            Greetings from the HitchHiker Team!

            You have just received a new offer for one of your requests.
            You can log in to http://hitchhiker-nus.appspot.com/ now
            and choose 'Manage Received Offer' to find out the details of
            the received offer.

            Have a good day!


            The HitchHiker Team
            """
            message.send()
            #end of sending confirmation email
            
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }

            template = jinja_environment.get_template('successfulcontactrequest.html')
            self.response.out.write(template.render(template_values))
        except InputError:
            error = "Incomplete form: please make sure all compulsory fields are filled before submitting."
            date_id = self.request.get('request_date')
            year = int(date_id[6:10])
            month = int(date_id[3:5])
            day = int(date_id[:2])
            query = ndb.gql("SELECT * "
                            "FROM Offers "
                            "WHERE ANCESTOR IS :1 AND date = DATE(:2, :3, :4)"
                            "ORDER BY date ASC",
                            person_key, year, month, day)
                            
            template_values = {
                'error': error,
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'offers': query,
                'request_number': self.request.get('request_number'),
                'request_owner': self.request.get('request_owner'),
                'request_date': self.request.get('request_date'),
            }
            
            template = jinja_environment.get_template('contactrequest.html')
            self.response.out.write(template.render(template_values))

            

class ManageReceivedRequest(webapp2.RequestHandler):
    def get(self):
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Offers "
                        "WHERE ANCESTOR IS :1 "
                        "ORDER BY date ASC",
                        parent_key)

        query2 = ndb.gql("SELECT * "
                         "FROM ReceivedRequests "
                         "WHERE ANCESTOR IS :1 "
                         "ORDER BY requested_datetime ASC",
                         parent_key)

        
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'offers': query,
            'received_requests': query2,
            'time_adj': datetime.timedelta(hours=8)
        }
            
        template = jinja_environment.get_template('managereceivedrequest.html')
        self.response.out.write(template.render(template_values))
        
class ManageReceivedOffer(webapp2.RequestHandler):
    def get(self):
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve items
        query = ndb.gql("SELECT * "
                        "FROM Requests "
                        "WHERE ANCESTOR IS :1 "
                        "ORDER BY date ASC",
                        parent_key)

        query2 = ndb.gql("SELECT * "
                         "FROM ReceivedOffers "
                         "WHERE ANCESTOR IS :1 "
                         "ORDER BY offered_datetime ASC",
                         parent_key)

        
        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'requests': query,
            'received_offers': query2,
            'time_adj': datetime.timedelta(hours=8)
        }
            
        template = jinja_environment.get_template('managereceivedoffer.html')
        self.response.out.write(template.render(template_values))

class ViewRouteOffer(webapp2.RequestHandler):
    def post(self):
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve offer:
        offer_key = ndb.Key('Persons', users.get_current_user().email(), 'ReceivedOffers', str(self.request.get('received_offer_number')))
        offer = offer_key.get()

        # Retrieve request
        request_key = ndb.Key('Persons', users.get_current_user().email(), 'Requests', self.request.get('received_offer_for_request'))
        request = request_key.get()

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'offer_start_location': offer.start_location,
            'offer_start_zipcode': offer.start_zipcode,
            'request_start_location': request.start_location,
            'request_start_zipcode': request.start_zipcode,
            'request_destination': request.destination,
            'request_destination_zipcode': request.destination_zipcode,
            'offer_destination': offer.destination,
            'offer_destination_zipcode': offer.destination_zipcode,
        }

        template = jinja_environment.get_template('viewrouteoffer.html')
        self.response.out.write(template.render(template_values))

class ViewRouteRequest(webapp2.RequestHandler):
    def post(self):
        # Retrieve person
        parent_key = ndb.Key('Persons', users.get_current_user().email())

        # Retrieve offer:
        offer_key = ndb.Key('Persons', users.get_current_user().email(), 'Offers', self.request.get('received_request_for_offer'))
        offer = offer_key.get()

        # Retrieve request
        request_key = ndb.Key('Persons', users.get_current_user().email(), 'ReceivedRequests', str(self.request.get('received_request_number')))
        request = request_key.get()

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'offer_start_location': offer.start_location,
            'offer_start_zipcode': offer.start_zipcode,
            'request_start_location': request.start_location,
            'request_start_zipcode': request.start_zipcode,
            'request_destination': request.destination,
            'request_destination_zipcode': request.destination_zipcode,
            'offer_destination': offer.destination,
            'offer_destination_zipcode': offer.destination_zipcode,
        }

        template = jinja_environment.get_template('viewrouterequest.html')
        self.response.out.write(template.render(template_values))

class GetOpenId(webapp2.RequestHandler):
    def post(self):
        openid = self.request.get('openid').rstrip()
        self.redirect(users.create_login_url('/mainpageuser', None, federated_identity=openid))

class HandleOpenId(webapp2.RequestHandler):
    def get(self):
        self.redirect(self.request.host_url)
        
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/aboutus', AboutUs),
    ('/faq', FAQ),
    ('/mainpageuser', MainPageUser),
    ('/makeoffer', MakeOffer),
    ('/manageoffer', ManageOffer),
    ('/makerequest', MakeRequest),
    ('/managerequest', ManageRequest),
    ('/deleteoffer', DeleteOffer),
    ('/deleterequest', DeleteRequest),
    ('/getoffer', GetOffer),
    ('/editoffer', EditOffer),
    ('/getrequest', GetRequest),
    ('/editrequest', EditRequest),
    ('/searchoffer', SearchOffer),
    ('/searchrequest', SearchRequest),
    ('/contactoffer', ContactOffer),
    ('/contactrequest', ContactRequest),
    ('/managereceivedrequest', ManageReceivedRequest),
    ('/managereceivedoffer', ManageReceivedOffer),
    ('/viewrouteoffer', ViewRouteOffer),
    ('/viewrouterequest', ViewRouteRequest),
    ('/getopenid', GetOpenId),
    ('/_ah/login_required', HandleOpenId)],
    debug=False)
