import caldav
import datetime
import config
import main


def get_cd_calendar(name):
    with caldav.DAVClient(url=config.CD_URL, username=config.CD_USERNAME, password=config.CD_PASSWORD) as client:
        my_principal = client.principal()

        epitech_calendar = None
        for calendar in my_principal.calendars():
            if calendar.name == name:
                epitech_calendar = calendar
                break
        return epitech_calendar


def add_event(epi_event, caldav_calendar, is_project=False):
    if is_project:
        begin = datetime.datetime.strptime(epi_event['start'], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
        end = datetime.datetime.strptime(epi_event['end'], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
        end = (datetime.datetime.strptime(end, "%Y%m%d") + datetime.timedelta(days=1)).strftime("%Y%m%d")
    else:
        begin = datetime.datetime.strptime(epi_event['start'], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%dT%H%M%S")
        end = datetime.datetime.strptime(epi_event['end'], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%dT%H%M%S")

    return caldav_calendar.save_event(f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ZContent.net//Zap Calendar 1.0//EN
BEGIN:VEVENT
SUMMARY:{epi_event['title']}
UID:{epi_event['id']}
DTSTART;TZID=Europe/Paris:{begin}
DTEND:{end}
DTSTAMP:{datetime.datetime.now().strftime("%Y%m%dT%H%M%S")}
LOCATION:{epi_event['location'] if 'location' in epi_event else "Non défini"}
BEGIN:VALARM
TRIGGER:-PT30M
DESCRIPTION: {epi_event['title']}
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
""")


def synchronize(epi_events, epi_projects):
    try:
        cal = get_cd_calendar(config.CD_CALENDAR_NAME)
        cal_proj = get_cd_calendar(config.CD_PROJ_CALENDAR_NAME)
    except Exception as e:
        main.send_error_webhook(f"Error while getting calendar: {e}")

    for event in epi_events:
        print(f"\033[0mSync event \033[96m{event['start']} \033[94m{event['end']} : \033[1m\033[93m{event['title']} \033[0m({event['location']})")
        add_event(event, cal)

    for event in epi_projects:
        print(f"\033[0mSync project \033[96m{event['start']} \033[94m{event['end']} : \033[1m\033[93m{event['title']} \033")
        add_event(event, cal_proj, is_project=True)
    print("\033[0mDone!")