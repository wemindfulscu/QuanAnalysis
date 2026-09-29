import smtplib
from email.mime.text import MIMEText

sender_email = "prof_dgw@163.com"
sender_password = "NSYfqsVRKU8ucQxC"  # ← NOT your login password!

# Use SMTP_SSL for port 465
server = smtplib.SMTP_SSL("smtp.163.com", 465)
server.login(sender_email, sender_password)

msg = MIMEText("Test alert message")
msg["Subject"] = "Monitor Alert"
msg["From"] = sender_email
msg["To"] = "1242556354@qq.com"

server.send_message(msg)
server.quit()