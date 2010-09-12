#!/usr/bin/python2.5
"""
New BSD License

Copyright 2010 stickybits, inc. All Rights Reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

'''A simple python interface for the stickybits API


View documentation with example API responses on the stickybits wiki: 
  http://code.google.com/p/stickybits/w/apiReference

Join the discussion group: 
  http://groups.google.com/group/stickybits-discuss
  
Create a stickybits developer account: 
  http://www.stickybits.com/api
  
'''

__author__ = 'james levy <james@stickybits.com>'
__copyright__ = "Copyright 2010, stickybits, inc."
__title__ = 'python-stickybits'
__version__ = '0.42'
__license__ = "BSD"

import os
import datetime
import base64
import weakref, new
import urllib
import urllib2
from urllib2 import HTTPError, URLError 

try:
    # Python 2.6
    import json
    json.loads
except:
    try: 
        import simplejson as json
    except ImportError:
        # django or GAE
        from django.utils import simplejson as json

API_VERSION = 1
BASE_URL = "http://api.stickybits.com/api/%d/" % API_VERSION
SANDBOX_URL = "http://dev3.stickybits.com/api/%d/" % API_VERSION

DEFAULT_API_KEY = "YOUR_API_KEY" 
API_KEY = DEFAULT_API_KEY # Visit http://www.stickybits.com/api to obtain an API key



class childClass(object):
    """
    Descriptor for making child classes.
    Adds parent instance as 'parent' property to the child class.
    """

    # Use a weakref dict to memoise previous results so that
    # instance.Inner() always returns the same inner classobj.
    #
    def __init__(self, inner):
        self.inner= inner
        self.instances= weakref.WeakKeyDictionary()

    # Not thread-safe - consider adding a lock.
    #
    def __get__(self, instance, _):
        if instance is None:
            return self.inner
        if instance not in self.instances:
            self.instances[instance]= new.classobj(
                self.inner.__name__, (self.inner,), {'parent': instance}
            )
        return self.instances[instance]


class stickybitsAuth(object):
    """ base authorization class
    """
    def __init__(self, *args, **kwargs):
      pass
    
    def send_request(self, url, method="GET", data=None, headers=None,
                     cache=None, timeout=None):
                     
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        if type(data) == dict: 
          data = urllib.urlencode(data)
        self._request = urllib2.Request(url=url, data=data)
        self._request.get_method = lambda: method
        self._request.add_header('Accept', 'application/json')
        self._request.add_header('User-Agent', __title__)
        for k,v in headers.items():
          self._request.add_header(k,v)

        try:                        
            response = opener.open(self._request)
            response_body = response.read()
            return response_body
        except HTTPError, e:
            if e.code in range(200, 205):
                pass
            elif e.code == 400:
                raise InvalidError(e.read())
            elif e.code == 401 or e.code == 403:
                raise AuthError(e)
            elif e.code == 404:
                raise NotFoundError(e)
            elif e.code == 405:
                raise NotAllowedError(e)
            elif e.code == 406:
                raise NotAcceptableError(e)
            elif e.code == 500:
                raise ServerError(e)
            else:
                raise StickybitsError(e)
        except URLError, e:
            raise ConnectionError(e)
          
class basicAuth(stickybitsAuth):
    """ make a request with HTTP header authentication
    """
    def __init__(self, username, password, **kwargs):
      if not username or not password:
        raise AuthError("username and password are required")
      self.username, self.password = username, password
    
    def send_request(self, *args, **kwargs):
        if not kwargs.get('headers'): kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = ('Basic %s' %
        base64.encodestring('%s:%s' % (self.username, self.password))[:-1])
        return super(basicAuth, self).send_request(*args, **kwargs)


  
def user_authenticated(fxn):
    def _exec(*args, **kw):
        kw['user_authenticated'] = True
        return fxn(*args, **kw)
    return _exec    
    
    
class Stickybits(object):
    """
    stickybits API client
    """
    cache = None
    timeout = None
    
    def __init__(self, apikey=API_KEY, cache=None, timeout=None):
        self.base_url = BASE_URL
        self.cache = cache
        self.timeout = timeout
        self.apikey = apikey
        self.auth = None
        if not self.apikey or self.apikey == DEFAULT_API_KEY:
          raise AuthError('an API Key is required')
          
    def anonAuth(self, *args, **kwargs):
      ''' make anonymous requests '''
      self.auth = stickybitsAuth(*args, **kwargs)

    def basicAuth(self, *args, **kwargs):
      ''' authenticate with HTTP basic auth '''
      self.auth = basicAuth(*args, **kwargs)

    def request(self, method_path, params, 
    method="GET", data=None, headers=None):
        '''Make a request to the stickybits server'''
        if not self.auth:
          if params.get("user_authenticated"):
            raise AuthError("This request requires authentication")  
          else: 
            self.anonAuth()
        else:
          if not isinstance(self.auth, stickybitsAuth):
            raise AuthError("auth must be instance of stickybitsAuth class")
        if params.get("user_authenticated"): 
          del params["user_authenticated"]
        params['apikey'] = self.apikey
        if params.get('sandbox') is True:
          request_base_url = SANDBOX_URL
        else:
          request_base_url = self.base_url 
        url = request_base_url + method_path
        url += ("?" + urllib.urlencode(params))
        if headers is None: 
          headers = {}
        response_body = self.auth.send_request(
        url, method=method, data=data, headers=headers,
        cache=self.cache, timeout=self.timeout)
        try:
            json_response = json.loads(response_body)
        except:
            raise JsonError('Unable to decode response to %s request: %s' 
            % (method_path, response_body))
        return json_response
    
    
    
    #####################
    # Code API Methods
    #####################
    
    class code(object):
      
      @classmethod
      def get(self, codeid, **kwargs):
        '''
        
          Get information about a code.
        
        Request:
        
          Required args:
            * codeid - identifier for code
            * codepw - password. *** Only required for private codes. ***
            
          Optional params:
            * skip - number of media items to skip. useful for pagination
            * limit - Maximum media items to return, up to 30
            * order - Use 'desc' or 'asc' to order media items. Default is ascending.
            * responses - set to False to not have responses included
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get code 
            >>> response = sb.code.get("1", limit=10,order='desc')
            
        Response:
          * code: dictionary of information on the retrieved code.
          * media: list of media attached to the retrieved code.
          
        '''
        kwargs['codeid'] = codeid
        return self.parent.request('code.get', kwargs, "GET")


      @classmethod
      def popular(self, **kwargs):
        '''
        
          Get recently popular codes.
        
        Request:
        
          Required args:
            none
        
          Optional params:
            * skip - number of items to skip. useful for pagination
            * limit - Maximum items to return, up to 30
            * since - 'day','week','month','all' 
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get popular codes
            >>> response = sb.code.popular(limit=30,since='week')

        Response:
          * codes: list containing dictionaries of information on popular codes.
        
        '''
        return self.parent.request('code.popular', kwargs, "GET")

      @classmethod
      def nearby(self, lat, lon, **kwargs):
        '''
        
          Get codes sorted by proximity to a location
          
        Request:
        
          Required args:
            * lat - latitude of target geo-location
            * lon - longitude of target geo-location
        
          Optional params:
            * radius - km length of query radius. Default is 1km.
            * limit - Maximum items to return. Default is 25.
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get nearby codes
            >>> response = sb.code.nearby(lat=97,lon=30.4)

        Response:
          * codes: list containing dictionaries of information on nearby codes.
          
        '''
        kwargs['lat'] = lat
        kwargs['long'] = lon
        return self.parent.request('code.nearby', kwargs, "GET")

      @classmethod
      def create(self, **kwargs):
        '''
        
          Create a new code.
        
        Request:
        
          Required args:
            none
            
          Optional params:
            none
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # create a new code
            >>> response = sb.code.create()

        Response:
          * code: dictionary of information on the created code
          
        '''
        return self.parent.request('code.create', kwargs, "GET")
        
      @classmethod
      @user_authenticated
      def update(self, codeid, **kwargs):
        '''
        
          Update an existing code.
        
        Request:
        
          Required args:
            * codeid - identifier for code
            * codepw - password *** Only required for private codes. ***
        
          Optional params:
            * password - set a new code password
            * title - set a new code title
            
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # update a code
            >>> response = sb.code.update("1", title="New code title", password="pw5678")

        Response:
          * success: boolean value indicating success of update
          * error: provided if success is false
          
        '''
        kwargs['codeid'] = codeid
        return self.parent.request('code.update', kwargs, "GET")
        
                     
    code=childClass(code)




    #####################
    # Bit API Methods
    #####################  
    
        
    class bit(object):

      @classmethod
      def stream(self, **kwargs):
        '''
        
          Get real-time stream of bit activity.
        
        Request:
        
          Required args:
            none

          Optional params:
            * responses - set to False to not have responses included
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get bit stream
            >>> response = sb.bit.stream()
            
        Response:
          * media: list of recent bit activity.
          
        '''
        return self.parent.request('bit.stream', kwargs, "GET")
                            
    
      @classmethod
      @user_authenticated
      def add(self, codeid, **kwargs):
        '''
        
          Add a new bit to a code, or add a response to a bit
        
        Request:
        
          Required args:
            * codeid - string identifier for code
            * codepw - password *** Only required for private codes. ***
          
          Optional params:
            * file - attached mov|jpg|mp3|pdf|zip|etc. Compress before sending. 
            * text - up to 1024 chars of text *** required if file param is not included ***
            * password - set a new bit password
            * quiet - do not publicize bit 
            * title - set a new bit title
            * parent - ID of parent bit if this bit is a response
              ** Note: Parent bits cannot be responses. **
            
          Social params:
            * status - status message to use 
              The default status code is "I just attached a bit to this barcode" and a link.
            
            Twitter:
              * twituname - a user's twitter username
              * twitpw - a user's twitter password
            Foursquare:
              * fsqruname - a user's foursquare email address or phone number
              * fsqrpw - a user's foursquare
              * vid - the foursquare venue id
            Facebook:
              * facebook - sessionid from facebook. Requires publish_stream permission.

 
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # add new bit to code 1
            >>> response = sb.bit.add('1', text="i drink a glass every morning", title="my favorite juice")
            
        Response:
          * success: boolean value indicating success of bit upload
          * error: provided if success is false
          *** note: id is not sent back because bit creation is queued. ***
          
        '''
        kwargs['codeid'] = codeid
        data = {}
        headers = None
        if kwargs.get('file'): 
          data['file'] = kwargs['file']
          del kwargs['file']
          # TODO: also support URL for server-side download?
          try:
            content_type, body = file_encode(data['file'])
          except:
            raise FileEncodingError
          import mimetypes
          headers = { 
            'Content-Type': content_type
          }
          data = body

        return self.parent.request('bit.add', kwargs, "POST",
        data=data, headers=headers)

      @classmethod
      @user_authenticated
      def remove(self, id, codeid, **kwargs):
        '''
        
          Remove a bit from a code. 
        
        Request:
        
          Required args:
            * id    - identifier for bit
            * codeid - identifier for code
            * codepw - password *** Only required for private codes. ***

          Optional params:
            none
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # remove bit 3 from code 1
            >>> response = sb.bit.remove(3,1)
            
        Response:
          * success: boolean value indicating success of bit removal
          * error: provided if success is false
          
        '''
        kwargs['id'] = id
        kwargs['codeid'] = codeid
        return self.parent.request('bit.remove', kwargs, "GET")

      @classmethod
      @user_authenticated
      def vote(self, id, vote, **kwargs):
        '''
        
          Upvote or downvote a code
        
        Request:
        
          Required args:
            * id   - identifier for bit
            * vote - "up" or "down"

          Optional params:
            none
        
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # upvote bit 3
            >>> response = sb.bit.vote(3,"up")
            
        Response:
          * success: boolean value indicating success of bit removal
          * error: provided if success is false
          
        '''
        kwargs['id'] = id
        kwargs['vote'] = vote
        return self.parent.request('bit.vote', kwargs, "GET")
      
    bit=childClass(bit)



    #####################
    # Scan API Methods
    #####################  
    
        
    class scan(object):

      @classmethod
      @user_authenticated
      def create(self, codeid, **kwargs):
        '''
        
          A scan is created each time a user scans a code.
        
        Request:
        
          Required args:
            * codeid - identifier for code
            * codepw - password *** Only required for private codes. ***
          
          Optional params:
            * lat - latitude of scan action
            * long - latitude of scan action
 
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # create a scan for a user scan action
            >>> response = sb.scan.create("1", lat=30.32, long=-97.64)
            
        Response:
          * success: boolean value indicating success of scan creation
          * error: provided if success is false
          
        '''
        kwargs['codeid'] = codeid
        return self.parent.request('scan.create', kwargs, "GET")

      @classmethod
      def upload(self, code_image, **kwargs):

        data = {}
        headers = None
        data['code_image'] = code_image
        # TODO: also support URL for server-side download?
        #try:
        content_type, body = file_encode(data['code_image'])
        #except:
        #    raise FileEncodingError
        import mimetypes
        headers = { 
        'Content-Type': content_type
        }
        data = body

        return self.parent.request('scan.create', {'codeid':'none'}, "POST",
        data=data, headers=headers)


      @classmethod
      @user_authenticated
      def remove(self, id, codeid, **kwargs):
        '''
        
          Remove a scan from a code.
        
        Request:
        
          Required args:
            *id - identifier for scan
            * codeid - identifier for code
            * codepw - password *** Only required for private codes. ***
            
          Optional params:
            none
         
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # create a scan for a user scan action
            >>> response = sb.scan.remove(3)
            
        Response:
          * success: boolean value indicating success of scan removal
          * error: provided if success is false
          
        '''
        kwargs['id'] = id
        kwargs['codeid'] = codeid
        return self.parent.request('scan.remove', kwargs, "GET")

      @classmethod
      @user_authenticated
      def recent(self, **kwargs):
        '''
        
          Get the most recent scans for a user
        
        Request:
        
          Required args:
            none

          Optional params:
            none
         
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # get billy's most recent scans
            >>> response = sb.scan.recent()
            
        Response:
          * scans: scans listed in descending order by date.
          
        '''
        return self.parent.request('scan.recent', kwargs, "GET")
                    
    scan=childClass(scan)    
    


    #####################
    # User API Methods
    #####################    

    class user(object):

      @classmethod
      def exists(self, username, **kwargs):
        '''
        
          Check if there is a stickybits user account matching a username
        
        Request:
        
          Required args:
            * username - stickybits username
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get boolean response if user exists
            >>> response = sb.user.exists('billy')
            
        Response:
          * exists: boolean value indicating if user exists for given username  
          
        '''
        kwargs['username'] = username
        return self.parent.request('user.exists', kwargs, "GET")
        
      @classmethod
      def info(self, username, **kwargs):
        '''
        
          Get information about a stickybits user

        Request:
        
          Required args:
            * username - stickybits username

          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get user info dictionary
            >>> response = sb.user.info('billy')
            
        Response:
          * user: dictionary of information about a user 
          
        '''
        kwargs['username'] = username
        return self.parent.request('user.info', kwargs, "GET")
        
      @classmethod
      def bits(self, username, **kwargs):
        '''
        
        Get a list of the most recent bits created by a user

        Request:
        
          Required args:
            * username - stickybits username
            
          Optional params:
            * skip - number of items to skip. useful for pagination
            * limit - Maximum items to return. Default is 25.
            
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # get user bits lists
            >>> response = sb.user.bits('billy')
            
        Response:
          * bits: list of bits created by a user
          
        '''
        kwargs['username'] = username
        return self.parent.request('user.bits', kwargs, "GET")

      @classmethod
      @user_authenticated
      def signin(self, **kwargs):
        '''
        
        Sign in a user.

        Request:
        
          Required args:
            none 
            
          Optional params:
            none
            
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # sign in as billy
            >>> response = sb.user.signin()
            
        Response:
          * success: boolean value indicating success of signin
          * error: provided if success is false
          
        '''
        return self.parent.request('user.signin', kwargs, "GET")

      @classmethod
      @user_authenticated
      def find(self, search, **kwargs):
        '''
        
        Finds friends for a user

        Request:
        
          Required args:
            * search - query for friend names
            
          Optional params:
            none
            
          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # get billy's friends matching query 'joe'
            >>> response = sb.user.find('joe')
            
        Response:
          * results: list of friends of user matching search query
          
        '''
        kwargs['search'] = search
        return self.parent.request('user.find', kwargs, "GET")
        
    user=childClass(user)



    #####################
    # Friend API Methods
    #####################    

    class friend(object):

      @classmethod
      @user_authenticated
      def list(self,**kwargs):
        '''
        
          Get friend lists for a user
        
        Request:
        
          Required args:
            none
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # get a list of billy's friends
            >>> response = sb.friend.list()
            
        Response:
          * approve: list of friends that need to be approved by this user
          * waiting: friends this user is waiting to be approved by
          * friends: this user's current friends  
          
        '''
        return self.parent.request('friend.list', kwargs, "GET")

      @classmethod
      @user_authenticated
      def add(self, friend, **kwargs):
        '''
        
          Add a new friend for a user
        
        Request:
        
          Required args:
            * friend - stickybits username of new friend
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # add joe as billy's new friend
            >>> response = sb.friend.add('joe')
            
        Response:
          * success: boolean value indicating success of friend addition
          * error: provided if success is false
          
        '''
        kwargs['friend'] = friend
        return self.parent.request('friend.add', kwargs, "GET")

      @classmethod
      @user_authenticated
      def remove(self, friend, **kwargs):
        '''
        
          Remove a friend for a user
        
        Request:
        
          Required args:
            * friend - stickybits username of friend to remove
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # remove joe as billy's friend
            >>> response = sb.friend.remove('joe')
            
        Response:
          * success: boolean value indicating success of friend removal
          * error: provided if success is false
          
        '''
        kwargs['friend'] = friend
        return self.parent.request('friend.remove', kwargs, "GET")
        
      @classmethod
      @user_authenticated
      def approve(self, friend, **kwargs):
        '''
        
          Approve a friend for a user
        
        Request:
        
          Required args:
            * friend - stickybits username of friend to approve
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # billy wants to approve joe
            >>> response = sb.friend.approve('joe')
            
        Response:
          * success: boolean value indicating success of friend approval.
          * error: provided if success is false
          
        '''
        kwargs['friend'] = friend
        return self.parent.request('friend.approve', kwargs, "GET")
        
      @classmethod
      @user_authenticated
      def ignore(self, friend, **kwargs):
        '''
        
          Ignore a friend request, or remove friend approval
        
        Request:
        
          Required args:
            * friend - stickybits username of friend to ignore
            
          Optional params:
            none

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # billy wants to ignore joe
            >>> response = sb.friend.ignore('joe')
            
        Response:
          * success: boolean value indicating success of friend ignoral.
          * error: provided if success is false
          
        '''
        kwargs['friend'] = friend
        return self.parent.request('friend.ignore', kwargs, "GET")

      @classmethod
      @user_authenticated
      def from_friends(self,**kwargs):
        '''
        
          Get recent media uploaded by a user's friends
        
        Request:
        
          Required args:
            none
            
          Optional params:
            * skip - number of media items to skip. useful for pagination
            * limit - Maximum media items to return, up to 30
            * order - Use 'desc' or 'asc' to order media items. Default is ascending.

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # get recent content uploaded by billy's friends
            >>> response = sb.friend.from_friends()
            
        Response:
          * media: list of media items uploaded by friends.
          
        '''
        return self.parent.request('friend.from_friends', kwargs, "GET")
                                
    friend=childClass(friend)        
        


    #####################
    # Notify API Methods
    #####################    

    class notify(object):

      @classmethod
      @user_authenticated
      def set(self, codeid, **kwargs):
        '''
        
          Create or update notification settings for a code
        
        Request:
        
          Required args:
            * codeid - identifier of code that will trigger notification
            
          Optional params:
            * add|remove - comma delimited list containing any of the following:
              * scans - get notifications when this code is scanned
              * content - get notifications when there are new bits attached
              * latlong - get notifications when the code is scanned in a new location
            

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # set notifications for code 1
            >>> response = sb.notify.set("1", add='scans,content', remove='latlong')
            
        Response:
          * success: boolean value indicating success of notification change.
          * error: provided if success is false
          
        '''
        kwargs['codeid'] = codeid
        return self.parent.request('notify.set', kwargs, "GET")

      @classmethod
      @user_authenticated
      def get(self, codeid, **kwargs):
        '''
        
          Get notifications for a code
        
        Request:
        
          Required args:
            * codeid - identifier of code for notifications
            
          Optional params:
            none
            

          Example request:
            # create the client 
            >>> sb = stickybits.Stickybits()
            # add HTTP Basic Authentication
            >>> sb.basicAuth('billy', 'pw1234')
            # get notifications for code 1
            >>> response = sb.notify.get("1")
            
        Response:
          * notifications: list of enabled notifiers (scans, content, latlong)
          
        '''
        kwargs['codeid'] = codeid
        return self.parent.request('notify.get', kwargs, "GET")
        
    notify=childClass(notify)  


def file_encode (file_path, fields=[]):
    BOUNDARY = '----------boundary------'
    CRLF = '\r\n'
    body = []
    # Add the metadata about the upload first
    for key, value in fields:
        body.extend(
          ['--' + BOUNDARY,
           'Content-Disposition: form-data; name="%s"' % key,
           '',
           value,
           ])
    # Now add the file itself
    file_name = os.path.basename(file_path)
    try:
      f = open(file_path, 'rb')
      file_content = f.read()
      f.close()
    except:
      raise FileAccessError
    body.extend(
      ['--' + BOUNDARY,
       'Content-Disposition: form-data; name="file"; filename="%s"'
       % file_name,
       # The upload server determines the mime-type, no need to set it.
       'Content-Type: application/octet-stream',
       '',
       file_content,
       ])
    # Finalize the form body
    body.extend(['--' + BOUNDARY + '--', ''])
    return 'multipart/form-data; boundary=%s' % BOUNDARY, CRLF.join(body)  
  
  
class StickybitsError(Exception):
    """base API error."""
    pass

class AuthError(StickybitsError):
    """Authorization error."""
    pass

class JsonError(StickybitsError):
    """JSON decoding error."""
    pass

class InvalidError(StickybitsError):
    """Invalid request error."""
    pass

class NotFoundError(StickybitsError):
    """Resource not found error."""
    pass

class NotAllowedError(StickybitsError):
    """Request not allowed error."""
    pass

class NotAcceptableError(StickybitsError):
    """Request not acceptable error."""
    pass

class ServerError(StickybitsError):
    """ Unexpected server error."""
    pass
    
class ConnectionError(StickybitsError):
    """ Unable to make connection """
    pass

class FileAccessError(StickybitsError):            
    """ Unable to find or open file """
    pass
        
class FileEncodingError(StickybitsError):            
    """ Unable to encode POST file upload """
    pass

__all__ = ["Stickybits"]


