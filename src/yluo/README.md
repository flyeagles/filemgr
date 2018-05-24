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


## Use JavaScript Module Reference

According to this [StackOverflow answer|https://stackoverflow.com/a/44086319], they are supported in Chrome 61, Firefox 54(behind the dom.moduleScripts.enabled setting in about:config) and MS Edge 16, with only Safari 10.1 providing support without flags.

Once ES6 Modules are commonplace, here is how you would go about using them:

<pre><code>
// module.js
export function hello() {
  return "Hello";
}
</code></pre>
<pre><code>
// main.js
import {hello} from 'module'; // or './module'
let val = hello(); // val is "Hello";
</code></pre>

Another Stackoverflow answer is [here|https://stackoverflow.com/questions/42237388/syntaxerror-import-declarations-may-only-appear-at-top-level-of-a-module]:
You also need 
-  Add type="module" to your script tag where you import the js file
<pre><code>  <script type="module" src="appthatimports.js"></script> </code></pre>
-  Import files have to be prefixed (./, /, ../ or http:// before)
<pre><code>import * from "./mylib.js"  </code></pre>


## JavaScript syntax check

Firefox version 59 is much strict on the usage of "var" for variables. 

## Display RAID1 disk with different icon
RAID1 disk will be displaed as green double files.

## Return items in a specific folder duplicated with items in RAID1 disk
Crawl target folder. Get list of file items, with fname and fsize.
Use that list to filter all the file objects in RAID1 disks.
Show that list in browser.

Now we need be able to use that list to locate the file items in target folder.
