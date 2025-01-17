from django.contrib.auth.models import User
from django.contrib.auth import login # importing login
from django.http.response import JsonResponse
from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from datetime import datetime, timedelta
from dateutil import tz, parser
from Authentication.auth_helper import get_sign_in_flow, get_token_from_code, store_user, remove_user_and_token, get_token
from Authentication.graph_helper import *
from django.contrib import messages
from . import forms

# <HomeViewSnippet>
def home(request):
  context = initialize_context(request)

  return render(request, 'Authentication/home.html', context)
# </HomeViewSnippet>

# <InitializeContextSnippet>
def initialize_context(request):
  context = {}

  # Check for any errors in the session
  error = request.session.pop('flash_error', None)

  if error != None:
    context['errors'] = []
    context['errors'].append(error)

  # Check for user in the session
  context['user'] = request.session.get('user', {'is_authenticated': False})
  return context
# </InitializeContextSnippet>

# <SignInViewSnippet>
def sign_in(request):
  # Get the sign-in flow
  
  flow = get_sign_in_flow()
  # Save the expected flow so we can use it in the callback
  try:
    request.session['auth_flow'] = flow
  except Exception as e:
    print(e)
  # Redirect to the Azure sign-in page
  return HttpResponseRedirect(flow['auth_uri'])
# </SignInViewSnippet>

# <SignOutViewSnippet>
def sign_out(request):
  # Clear out the user and token
  remove_user_and_token(request)

  return HttpResponseRedirect(reverse('home'))
# </SignOutViewSnippet>

# <CallbackViewSnippet>
def callback(request):
  # Make the token request
  result = get_token_from_code(request)
  print(result)
  #Get the user's profile
  user = get_user(result['access_token'])
  # Store user
  store_user(request, user)
  print(user)
  print(user['displayName'])
  print(user['mail'])
  try:
    user_object = User.objects.get(username = user["displayName"])
  except:
    user_object = User.objects.create(username = user['displayName'], email = user['mail'])
    user_object.save()
  if user_object is not None: 
    login(request,user_object)  # we call the login function to bind a user to current session, this way they get automatically logged in to django admin website
  user_object.is_staff = True # we also need to set is_staff permission to true so that they have access to admin dashboard
  user_object.save()
  return HttpResponseRedirect(reverse('admin:index')) # now we just redirect to admin view, search for httpresponseredirect on django docs for more info.
# </CallbackViewSnippet>

# <NewEventViewSnippet>
def newevent(request):
  context = initialize_context(request)
  user = context['user']

  if request.method == 'POST':
    # Validate the form values
    # Required values
    if (not request.POST['ev-subject']) or \
       (not request.POST['ev-start']) or \
       (not request.POST['ev-end']):
      context['errors'] = [
        { 'message': 'Invalid values', 'debug': 'The subject, start, and end fields are required.'}
      ]
      return render(request, 'auth/newevent.html', context)

    attendees = None
    if request.POST['ev-attendees']:
      attendees = request.POST['ev-attendees'].split(';')
    body = request.POST['ev-body']

    # Create the event
    token = get_token(request)

    create_event(
      token,
      request.POST['ev-subject'],
      request.POST['ev-start'],
      request.POST['ev-end'],
      attendees,
      request.POST['ev-body'],
      user['timeZone'])

    # Redirect back to calendar view
    return HttpResponseRedirect(reverse('calendar'))
  else:
    # Render the form
    return render(request, 'auth/newevent.html', context)
  print('hello')
# </NewEventViewSnippet>

def calendarAPI(request):
  context = initialize_context(request)
  
  user = context['user']
  print(user)
  # Load the user's time zone
  # Microsoft Graph can return the user's time zone as either
  # a Windows time zone name or an IANA time zone identifier
  # Python datetime requires IANA, so convert Windows to IANA
  time_zone = get_iana_from_windows('India Standard Time')
  tz_info = tz.gettz(time_zone)

  # Get midnight today in user's time zone
  today = datetime.now(tz_info).replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0)

  # Based on today, get the start of the week (Sunday)
  if (today.weekday() != 6):
    start = today - timedelta(days=today.isoweekday())
  else:
    start = today

  end = start + timedelta(days=7)

  token = get_token(request)

  events = get_calendar_events(
    token,
    start.isoformat(timespec='seconds'),
    end.isoformat(timespec='seconds'),
    'India Standard Time')
  print(events)
  if events:
    # Convert the ISO 8601 date times to a datetime object
    # This allows the Django template to format the value nicely
    for event in events['value']:
      event['start']['dateTime'] = parser.parse(event['start']['dateTime'])
      event['end']['dateTime'] = parser.parse(event['end']['dateTime'])

    context['events'] = events['value']

  return JsonResponse(events)
# </CalendarViewSnippet>

def userDetails(request):
 
  user_objects = OutlookUser.objects.all()
  current_user_object = user_objects[len(user_objects)-1]
  detail = {"name":current_user_object.name,"email":current_user_object.email}
  return JsonResponse(detail)

def teamDetails(request):
  team_objects = Team.objects.all()
  print(team_objects)
  team_dic = {}
  i = 0
  for team in team_objects:
    team_dic[str(i)] = {"team_name" : team.team_name, "start_date" : team.start_date, "end_date" : team.end_date}
    i= i+1
  return JsonResponse(team_dic)

def formDetails(request):
  if request.method == 'POST':
      form = forms.AdditionForm(request.POST, request.FILES)
      if form.is_valid():
          form.save()
          messages.success(request, f'Post Successful')
          return redirect('home')
  else:
      form = forms.AdditionForm()
  return render(request, 'auth/newAddition.html', {'form': form})

def MinuteDetails(request):
  if request.method == 'POST':
      form = forms.MinuteForm(request.POST, request.FILES)
      if form.is_valid():
          form.save()
          messages.success(request, f'Post Successful')
          return redirect('home')
  else:
      form = forms.MinuteForm()
  return render(request, 'auth/minuteAddition.html', {'form': form})