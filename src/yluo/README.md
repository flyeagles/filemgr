This folder should contain SQLite db file:  db.sqlite3.

## How to migrate the database after model change
Reference: https://docs.djangoproject.com/en/2.0/topics/migrations/#workflow

<pre><code>
$ python manage.py makemigrations
</code></pre>

Then
<pre><code>
$ python manage.py migrate
</code></pre>
