import smtplib

USERNAME = input("").strip()
PASSWORD = input("").strip()
MESSAGE = input("Enter your message: ")

SENDER_EMAIL = input("").strip()
TARGET_EMAIL = input("").strip()


MAIL = smtplib.SMTP("smtp.gmail.com",587)
MAIL.starttls()
MAIL.login(USERNAME,PASSWORD)


MAIL.sendmail(SENDER_EMAIL,TARGET_EMAIL,MESSAGE)
MAIL.close()
