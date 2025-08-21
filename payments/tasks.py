from celery import shared_task
from django.core.mail import EmailMultiAlternatives

@shared_task
def send_ticket_reminder_email(user_email, username, event_name):
    subject = f'Reminder Buat Tiket yang Kamu Pesan'
    
    text_content = f"""Hellow {username},
    
        Aku sekedar mengingatkan saja,
    
        tiket "{event_name}" kamu akan dimulai dalam 2 Jam lagi.
    
        Maka dari itu, segera siapin diri dan aku tunggu kehadiranmu!
    
        Tim Dico Event
    
        Pesan ini tidak usah dibalas ya, ini dikirim otomatis:)
    """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color:#f9fafb; margin:0; padding:0;">
        <table align="center" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1); overflow:hidden;">
        <tr>
            <td style="background-color:#4f46e5; padding:20px; text-align:center; color:#ffffff;">
            <h1 style="margin:0; font-size:24px;">📢 Reminder Event</h1>
            </td>
        </tr>
        <tr>
            <td style="padding:30px; color:#333333; line-height:1.6;">
            <p style="font-size:18px;">Hello <strong>{username}</strong>, 👋</p>
            <p>Aku sekedar mengingatkan saja, tiket <strong>"{event_name}"</strong> kamu akan dimulai dalam <strong>2 Jam lagi</strong>.</p>

            <p>Maka dari itu, segera siapin diri dan aku tunggu <strong>kehadiranmu</strong>!</p>

            <p style="margin-top:30px;">Salam hangat,</p>
            <p style="font-weight:bold; color:#4f46e5;">Tim Dico Event</p>
            </td>
        </tr>
        <tr>
            <td style="background-color:#f9fafb; padding:15px; text-align:center; font-size:12px; color:#6b7280;">
            <p style="margin:0;">Pesan ini tidak usah dibalas ya, ini dikirim otomatis 🙂</p>
            </td>
        </tr>
        </table>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, text_content, 'no-reply@dicotickets.com', [user_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
    return f'Email sent to {user_email}'