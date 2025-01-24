from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
import smtplib
from email.message import EmailMessage
import qrcode
import base64
import io
import os
from PIL import Image
import csv

app = Flask(__name__)
app.secret_key = "h68gfv544ASF"

EMAIL_ADDRESS = "noreply@eastwind.dog"
EMAIL_PASSWORD = "EPX8IIYds0teJU7"

# EMAIL_ADDRESS = "nourelsabbagh3@gmail.com"
# EMAIL_PASSWORD = "kniumggwumgzeopx"

# registrations = []

ADMIN_USERNAME = "eastwind_admin"
ADMIN_PASSWORD = "d0gSD4y0uT."

def init_csv():
    if not os.path.exists("registrations.csv"):
        with open("registrations.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Email", "Mobile", "Persons", "Dogs"])

def send_email(to_email, name, persons, dogs, qr_image_data):
    print(f"Sending email to: {to_email}, Name: {name}, Persons: {persons}, Dogs: {dogs}")  # Debug info
    msg = EmailMessage()
    msg["Subject"] = "Your Event QR Code"
    msg["From"] = f"EASTWIND <{EMAIL_ADDRESS}>"
    msg["To"] = to_email

    body_with_inline_qr = (
        f"<p>Dear {name},</p>"
        f"<p>Thank you for registering for <b>EASTWIND Dog's Day Out</b>!</p>"
        f"<p>Number of Persons: {persons}<br>"
        f"Number of Dogs: {dogs}</p>"
        f"<p>Please download the attached QR code to show it at the entrance for smooth check-in.</p>"
        f"<p><b>Event Rules:</b></p>"
        f"<ul>"
        f"<li>Please ensure your dog is free of fleas and ticks.</li>"
        f"<li>Dogs in heat are not allowed.</li>"
        f"<li>Dogs are such fun, but we’d like to keep the experience safe for everyone aged 16 and above.</li>"
        f"<li>For the safety of everyone, dogs showing aggressive behavior may need to wear a muzzle</li>"
        f"<li>Dogs must remain on a leash at all times, except in designated off-leash areas.</li>"
        f"<li>Please clean up after your dog to help keep the space welcoming for everyone.</li>"
        f"</ul>"
        f"<p>Best regards,<br>EASTWIND Team.</p>"
    )
    msg.set_content("Plain text version of the email.")
    msg.add_alternative(body_with_inline_qr, subtype="html")

    msg.add_attachment(
        qr_image_data,
        maintype="image",
        subtype="png",
        filename="event_qr_code.png",
    )

    try:
        with smtplib.SMTP("smtp-hve.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            print("Login successful. Session set.")
            return redirect(url_for("registrations"))
        else:
            print("Invalid credentials. Please try again.")
            return redirect(url_for("login"))

    return '''
        <form method="POST">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required><br>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route("/registrations", methods=["GET", "POST"])
def registrations():
    print("Session logged_in:", session.get("logged_in"))

    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            mobile = request.form["mobile"]
            persons = request.form["persons"]
            dogs = request.form["dogs"]

            with open("registrations.csv", "r") as file:
                reader = csv.DictReader(file)
                if any(row["Email"] == email for row in reader):
                    return "Error: Email already registered.", 400

            qr_data = f"Name: {name}\nEmail: {email}\nMobile Number: {mobile}\nPersons: {persons}\nDogs: {dogs}"
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="rgb(33, 67, 135)", back_color="white").convert("RGB")
            logo_path = "logo.png"  # Path to your logo file
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)

                # Resize the logo to fit within the QR code
                logo_size = qr_img.size[0] // 4  # Logo size is 1/4th of the QR code width
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

                # Calculate the position to center the logo
                logo_position = (
                    (qr_img.size[0] - logo.size[0]) // 2,
                    (qr_img.size[1] - logo.size[1]) // 2,
                )

                # Paste the logo onto the QR code
                qr_img.paste(logo, logo_position, logo if logo.mode == "RGBA" else None)

            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_image_data = buffer.getvalue()

            with open("registrations.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([name, email, mobile, persons, dogs])

            send_email(email, name, persons, dogs, qr_image_data)
            return redirect(url_for("success"))

    return render_template("form.html")
  
@app.route("/success")
def success():
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Success</title>
        </head>
        <body>
            <h1>Registration Successful!</h1>
            <p>The email with the QR code has been sent.</p>
            <button onclick="window.location.href='/registrations'">Register Another User</button>
            <button onclick="window.location.href='/logout'">Log Out</button>
        </body>
        </html>
    '''


@app.route("/logout") 
def logout():
    session.pop("logged_in", None) 
    flash("You have been logged out.")  
    return redirect(url_for("login"))  

if __name__ == "__main__":
    init_csv()
    app.run(debug=True)
