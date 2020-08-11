import smtplib



class Gmail(object):
    def __init__(self, fromEmail, password):
        self.smtp_connect(fromEmail, password)

    def send_message(self, subject, body, toEmail):
        try:
            headers = [
                "From: " + self.fromEmail,
                "Subject: " + subject,
                "To: " + toEmail,
                "MIME-Version: 1.0",
                "Content-Type: text/html"]
            headers = "\r\n".join(headers)
            self.session.sendmail(
                self.fromEmail,
                toEmail,
                headers + "\r\n\r\n" + body)
            self.session.close()
        except Exception as error:
            self.smtp_connect(self.fromEmail, self.password)
            self.send_message(subject, body, toEmail)

    def smtp_connect(self, fromEmail, password):
        self.fromEmail = "hngquickthink@gmail.com"
        self.password = "Hngquickthink12@"
        self.server = 'smtp.gmail.com'
        self.port = 587
        session = smtplib.SMTP(self.server, self.port)
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.fromEmail,self.password)
        self.session = session