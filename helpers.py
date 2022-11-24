from reportlab.pdfgen import canvas
from functools import wraps
from datetime import datetime
from app import *
from pathlib import Path
from smtplib import *
from email.message import EmailMessage

def makepdf(inv_num, name, contact_num, address, company_name, uen_num, list_of_items):   
    #getting the date
    month_num = str(datetime.now().month)
    datetime_object = datetime.strptime(month_num, "%m")
    full_month_name = datetime_object.strftime("%B")

    date = str(datetime.now().day) + "-" + full_month_name + "-" + str(datetime.now().year)
    
    # Creating Canvas
    filename = (f"invoice{inv_num}.pdf")
    c = canvas.Canvas(filename, pagesize=(200,250), bottomup=0)
    font = "Times-Roman"
    # Logo Section
    # Setting th origin to (10,40)
    c.translate(10,40)
    # Inverting the scale for getting mirror Image of logo
    c.scale(1,-1)
    # Inserting Logo into the Canvas at required position
    c.drawImage("static/images/logo.jpg",0,0,width=50,height=30)

    # Title Section
    # Again Inverting Scale For strings insertion
    c.scale(1,-1)
    # Again Setting the origin back to (0,0) of top-left
    c.translate(-10,-40)
    # Setting the font for Name title of company
    c.setFont(font,10)
    # Inserting the name of the company
    c.drawCentredString(125,20,"Laptop.sg Pte Ltd")
    # For under lining the title
    c.line(70,22,180,22)
    # Changing the font size for Specifying Address
    c.setFont(font,5)
    c.drawCentredString(125,30,"1 Orchard Rd ")
    c.drawCentredString(125,35,"Singapore 238823")
    # Changing the font size for Specifying GST Number of firm
    c.setFont(font,6)
    c.drawCentredString(125,42,"Company Registration No.: 202009367E")

    # Line Seprating the page header from the body
    c.line(5,45,195,45)

    # Document Information
    # Changing the font for Document title
    c.setFont(font,8)
    c.drawCentredString(100,55,f"TAX-INVOICE {inv_num}")

    # This Block Consist of Costumer Details
    c.roundRect(15,63,170,40,10,stroke=1,fill=0)
    c.setFont(font,5)
    c.drawString(20,70,f"Company Name: {company_name}")
    c.drawRightString(180,70,f"UEN No.: {uen_num}")
    c.drawString(20,80,f"Address: {address}")
    c.drawString(20,90,f"Date: {date}")
    c.drawString(20,100,f"Contact Person: {name}")
    c.drawRightString(180,100,f"Phone No: {contact_num}")

    # Header
    c.roundRect(15,108,170,130,10,stroke=1,fill=0)
    c.line(15,120,185,120)
    c.drawString(20,118,"No.")
    c.drawString(75,118,"Item")
    c.drawString(142,118,"Price")
    c.drawString(158,118,"Qty")
    c.drawString(172,118,"Total")

    #Body
    #print first item
    y_axis = 125
    index = 1
    cart_total = 0
    for item in list_of_items:
        c.drawString(20,y_axis,f"{index}")
        c.drawString(35,y_axis,f"{item.name}")
        c.drawString(141,y_axis,f"${item.price}")
        c.drawString(159,y_axis,f'{item.qty}')
        c.drawString(171,y_axis,f'${item.total}')
        index += 1
        y_axis += 10
        cart_total += item.total

    c.drawString(171,217,f'${cart_total}')

    # Drawing table for Item Description
    c.line(15,210,185,210)
    c.line(30,108,30,220)
    c.line(140,108,140,220)
    c.line(155,108,155,220)
    c.line(170,108,170,220)

    # Footer
    c.line(15,220,185,220)
    c.line(100,220,100,238)
    c.drawString(20,225,"Laptop.sg Pte Ltd")
    c.drawString(20,230,"OCBC Bank")
    c.drawString(20,235,"Account Number: 601-109002-001")
    c.drawRightString(180,230,"No signature required")
    c.drawRightString(180,235,"for system generateed invoices")

    # End the Page and Start with new
    c.showPage()
    # Saving the PDF
    c.save()
    
    #move the file to invoice directory
    Path(f"{filename}").rename(f"invoices\{filename}")

def send_email(recipient, name, invoice_number):
    #declaring variables
    user = "laptopsginfo@gmail.com"
    #pwd = "testPassword1"
    app_pwd = "oltcywxyudjiodbm"
    subject = (f"Thank you for your purchase invoice no.{invoice_number}")
    body = (f"Dear {name}\n\nThank you for your purchase. We appreciate your prompt payment.\nkindly note that your selected model may have a lead time of at least 4 weeks. We would like to assure you that we are constantly replenishing our stocks and your selected model will be reserved for you upon you communicating to us your payment details.\nPlease do not hesitate to call us or email us for any enquires regarding your order. \n\nBest Regards\nGrace Fu\nSales Manager\nTel.no.:+6581234567\nEmail:{user}")
    pdf_file = (f'invoices\invoice{invoice_number}.pdf')

    #preparing email message
    email = EmailMessage()
    email['Subject'] = subject
    email['From'] = user
    email['To'] = recipient
    email.set_content(body)
    with open(pdf_file, 'rb') as content_file:
        content = content_file.read()
        email.add_attachment(content, maintype='application', subtype='pdf', filename=pdf_file)
    print("finished preparing email")
    #preparing server and send email
    try:
        server = SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        print("trying to log in")
        server.login(user, app_pwd)
        print("successfully logged in")
        server.send_message(email)
        server.close()
        print('successfully sent the mail')
    except:
        print("failed to send mail")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    #Decorate routes to require login.
    #https://flask.palletsprojects.com/en/2.2.x/patterns/viewdecorators/
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

    