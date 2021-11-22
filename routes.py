from collections import deque

from flask import Flask, redirect, render_template as render, url_for, request, flash, current_app as app
import pymongo

from app import db
db = db.db

recents = deque([], maxlen=10)

# Index
@app.route('/')
def index():
    key = request.args.get('key', default='')
    if key:
        return go(key)
    return render(
        'index.html',
        urls=[(record['key'], record['url']) for record in db.urls.find()],
        recents=recents,
        hits=[(record['key'], record['count']) for record in db.hits.find().sort('count', pymongo.DESCENDING).limit(10)],
        misses=[(record['key'], record['count']) for record in db.misses.find().sort('count', pymongo.DESCENDING).limit(10)],
    )

# Default route - Capture /key and /key/
@app.route('/', defaults={'key': ''})
@app.route('/<key>/')
def go(key):
    jump = False
    if '#' in key:
        key, jump = key.split('#', 1)
    # Query and save in one step.
    if (query := db.urls.find_one({'key': key})):
        url = query['url']
        db.hits.update_one({'key': key}, {'$inc': {'count': 1}})
        recents.appendleft(f'{key}{"#"+jump if jump else ""}')
        return redirect(f'http://{url}{"#"+jump if jump else ""}')
    else:
        # Increment miss counter by 1, inserting if it doesn't already exist.
        db.misses.update_one({'key': key}, {'$inc': {'count': 1}}, upsert=True)
        flash(f'Error - The requested keyword {key} does not exist. Create it?', 'warning')
        return redirect(url_for('create', key=key))


# Create - Landing page
@app.route('/create/', methods=['GET'])
def create():
    return render('create.html', key=request.args.get('key', default=''))


# Create - Form action
@app.route('/create/', methods=['POST'])
def create_submit():
    key = request.form['key']
    url = request.form['url']
    overwrite = 'overwrite' in request.form

    if not db.urls.find_one({'key': key}) or overwrite:
        db.urls.update_one({'key': key}, {'$set': {'url': url}}, upsert=True)
        db.hits.update_one({'key': key}, {'$set': {'count': 0}}, upsert=True)
        db.misses.delete_one({'key': key})
        flash(f'Success - Added go/{key}', 'success')
    else:
        flash(f"Error - Can't overwrite existing key {key}", 'danger')

    return create()
