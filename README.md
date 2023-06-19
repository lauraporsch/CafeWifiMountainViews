# CafeWifiMountainViews

https://cafewifimountainviews.onrender.com/

A website that lists Cafes in Banff with a focus on WiFi and Socket Availability as well as Mountain Views.
Rendered with Flask Framework.
Login or SignUp required for adding or reviewing Cafes. 
Login via Flask-LoginManager, Passwords get hashed and salted but are stored in a public DB, to show how webiste works, please do not use real data to test the website!

Admin-only functions, please get in touch with me to get the login data for admins to test out the website!

Users, Cafes and Reviews are all added to a SQLlite Database. 
Forms are based on WTForms.
Contact form is sent out to my private email via smtplib.

Includes RESTful API for using the data as JSON.

I used a template from Start Bootstrap (https://startbootstrap.com/themes/clean-blog) for the front-end design, which also includes Java Script Code that is NOT mine! All code in main.py as well as the Jinja/Python Code in the html files was written by me. For the front-end I only changed the CSS code in the file static/css/clean-blog.min.css slightly and marked the code as mine.

This is a work in progress.

Homepage, overview of Cafes, Navigation bar without User being logged in
![image](https://github.com/lauraporsch/CafeWifiMountainViews/assets/127047376/f827a966-54ca-46d6-a586-c33673e6f7e9)

all_cafes.html, showing all cafes with infos as table
![image](https://github.com/lauraporsch/CafeWifiMountainViews/assets/127047376/ebc98ef2-76a6-4a56-8405-95cd7f2b43d5)

Details for "Good Earth Cafe" (cafe.html) including reviews, admin-view
![image](https://github.com/lauraporsch/CafeWifiMountainViews/assets/127047376/04734bd6-6160-4dd5-9871-f8f09a557558)

Reviews by User (user-reviews.html), admin-view (admin-only)
![image](https://github.com/lauraporsch/CafeWifiMountainViews/assets/127047376/5f2a54fd-fdaf-46e7-803a-fcf288ab4bfb)





