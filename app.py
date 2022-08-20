#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)

migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # missing fields
    
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    website = db.Column(db.String(250))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))
    
    shows = db.relationship("Show", backref="venue", lazy=True)
    
    def __repr__(self):
      return f"<Venue {self.id} name: {self.name}>"

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # missing fields
    
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    
    shows = db.relationship("Show", backref="artist", lazy=True)
    
    def __repr__(self):
      return f"<Artist {self.id} name: {self.name}>"

# Show model

class Show(db.Model):
  __tablename__ = 'Show'
  
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime,nullable = False,default=datetime.utcnow)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  
  def __repr(self):
    
    return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  venues = Venue.query.all()
  locations = set()
  
  for venue in venues:
    
    locations.add((venue.city,venue.state)) #creating a tuple
  
  for location in locations:
    
    data.append({
      "city": location[0],
      "state": location[1],
      "venues": []
    })
    
  for venue in venues:
    num_upcoming_shows = 0
    # get all shows based on the venue id
    shows = Show.query.filter_by(venue_id=venue.id).all()
    # get current date to filter num_upcoming_shows
    current_date = datetime.now()

    for show in shows:
      if show.start_time > current_date:
        num_upcoming_shows += 1
  
    
    for venue_location in data:
      if venue.state == venue_location['state'] and venue.city == venue_location['city']:
        venue_location['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

  response={
    "count": result.count(),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  #query db for venue with specific id
  venue = Venue.query.get(venue_id)
  if venue:
    
    #query db for shows with venue_id simillar to this venues_id
    shows = Show.query.filter_by(venue_id=venue_id).all()
    
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    
    #loop through the shows and compare show's start_time and current time to determine past and upcoming shows
    for show in shows:
      data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
          }
      if show.start_time > current_time:
        upcoming_shows.append(data)
      else:
        past_shows.append(data)
        
    data={
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description":venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
  else:
     return redirect(url_for('index'))#redirect user to index page in case they manually type an invalid id     
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    
    form  = VenueForm()
    #asigning form input to variables
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    genres = form.genres.data
    website = form.website_link.data
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data
    #creating venue object from form input
    venue = Venue(name=name, city=city, state=state, address=address,
                  phone=phone, image_link=image_link, facebook_link=facebook_link,
                  genres=genres, website=website, seeking_talent=seeking_talent,
                  seeking_description=seeking_description) 
    #opening session in database and add venue object to db
    db.session.add(venue)
    #commit venue object to database
    db.session.commit()
    # on successful db insert flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  except:
    
    db.session.rollback()
    #on unsuccessful db insert, flash an error
    flash('An error ocurred, Venue ' + request.form['name'] + ' could not be listed')
      
  finally:
    
    db.session.close()
  # on successful db insert, flash success
    
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    
    db.session.delete(venue) 
    db.session.commit()
    
    flash(' Venue ' + request.form['name'] + ' successfully deleted')
     
  except:
    
    db.session.rollback()
    flash('An error ocurred, Venue ' + request.form['name'] + ' not deleted')
      
  finally:
    
    db.session.close()
  
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
 
  artists = Artist.query.order_by(Artist.name).all() 
  
  data = []
  
  
  #loop through artists data and append an artist dictionary with name and id into a list
  for artist in artists:
    data.append({
      "id": artist.id,
    "name": artist.name
    })
    
 
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_term = request.form.get('search_term', '')

  result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))

  response = {
    'count': result.count(),
    'data': result
  }
  
 
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
 #query database for an artists with a specific id
  artist = Artist.query.get(artist_id)
  
  if artist:
    #query db for shows with artist_id simillar to this artist_id
    shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    
    #loop through the shows and compare show's start_time and current time to determine past and upcoming shows
    for show in shows:
      data = {
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'venue_image_link': show.venue.image_link,
        'start_time': format_datetime(str(show.start_time))
      }
      if show.start_time > current_time:
        upcoming_shows.append(data)
      else:
        past_shows.append(data)

    data = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'facebook_link': artist.facebook_link,
      'image_link': artist.image_link,
      'website':artist.website,
      'seeking_venue':artist.seeking_venue,
      'seeking_description':artist.seeking_description,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
  else:
    
    return redirect(url_for('index'))  #redirect users to index page incase they manually type an invalid id in the url bar

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  artist = Artist.query.get(artist_id)
  
  #populating edit form with values
  form = ArtistForm()
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.genres.data = artist.genres
  form.phone.data = artist.phone
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website
  form.seeking_description.data = artist.seeking_description
  form.seeking_venue.data = artist.seeking_venue
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    
    form  = ArtistForm()
    
    #get the artist with id 
    artist = Artist.query.get(artist_id)
    
    #update artist with data submitted
    artist.name = form.name.data  
    artist.city = form.city.data  
    artist.state = form.state.data  
    artist.genres = form.genres.data  
    artist.phone = form.phone.data  
    artist.facebook_link = form.facebook_link.data  
    artist.image_link = form.image_link.data 
    artist.website = form.website_link.data  
    artist.seeking_description = form.seeking_description.data
    artist.seeking_venue = form.seeking_venue.data  
    db.session.commit()
  except:  
    db.session.rollback()
    flash('An error ocurred, Artist ' + request.form['name'] + ' could not be updated') 
      
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  if venue:
  
  #populating edit form with values
    form = VenueForm()
    
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.genres.data = venue.genres
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_description.data = venue.seeking_description
    form.seeking_talent.data = venue.seeking_talent
  else:
    #redirect user to index page incase they manually type an id that doesn't exist
    return redirect(url_for("index")) 
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()
    
    venue = Venue.query.get(venue_id)
    
    #updating existing venue with submitted form data
    venue.name = form.name.data
    venue.city = form.city.data 
    venue.state = form.state.data
    venue.genres = form.genres.data
    venue.phone =  form.phone.data
    venue.address = form.address.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website = form.website_link.data
    venue.seeking_description = form.seeking_description.data
    venue.seeking_talent = form.seeking_talent.data 
    db.session.commit()
  except:
    
    db.session.rollback()
    
    flash('An error ocurred, Venue ' + request.form['name'] + ' could not be updated') 
   
  
  finally:
    db.session.rollback()
  
 
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  try:
    form = ArtistForm()
    
    #asigning form input to variables
    name = form.name.data
    city = form.city.data
    state = form.state.data 
    phone = form.phone.data
    genres = form.genres.data 
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data
    website = form.website_link.data
    facebook_link = form.facebook_link.data
    #creating artist object from form input
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, image_link=image_link, facebook_link=facebook_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
    #opening session in database and add artist object to db
    db.session.add(artist)
    #commit artist object to database
    db.session.commit()
    # on successful db insert flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
      
    db.session.rollback()
    #on unsuccessful db insert, flash an error
    flash('An error ocurred, Artist ' + request.form['name'] + ' could not be listed')
     
  finally:
    
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  #last show listed will be on top
  shows = Show.query.order_by(db.desc(Show.start_time))
  data = []
  
  for show in shows:
    data.append({
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist.id,
    "artist_name":show.artist.name ,
    "artist_image_link":show.artist.image_link ,
    "start_time": format_datetime(str(show.start_time))
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  
  try:
  
    form = ShowForm()
    
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    #creating show object from form input
    show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
    #opening session in database and add show object to db
    db.session.add(show)
    #commit show object to database
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
     
    db.session.rollback()
    #on unsuccessful db insert, flash an error
    flash('An error occured. show could not be listed')
    
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
