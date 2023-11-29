import datetime
import requests
import caldav_manager
import config


def send_error_webhook(error):
    requests.post(config.ERR_WEBHOOK_URL, json={
        'content': f"```{error}```"
    })


def get_activities(start, end):
    res = requests.get("https://intra.epitech.eu/module/board/?format=json&start=" + start + "&end=" + end,
                       cookies={
                           "user": config.INTRA_TOKEN
                       })
    return res.json()


def get_planning(start, end):
    r = requests.get('https://intra.epitech.eu/planning/load', params={
        'start': start,
        'end': end,
        'format': 'json',
    }, cookies={
        'user': config.INTRA_TOKEN
    })
    if r.status_code != 200:
        send_error_webhook(f"Error while fetching planning: {r.status_code} {r.text}")
        return []
    return r.json()


def get_next_date(current, days):
    return (current + datetime.timedelta(days=days)).strftime("%Y-%m-%d")


def run():
    print("Starting synchronization")
    print("Fetching planning from intra")
    planning = get_planning(config.SYNC_START, config.SYNC_END)
    activities = get_activities(config.SYNC_START, config.SYNC_END)

    minified = []
    minified_activities = []

    print("Formatting data")
    for event in planning:
        if event['rdv_indiv_registered'] is None and event['rdv_group_registered'] is None:
            if event['semester'] not in [0, 1, 2]:
                continue
            if not event['module_registered']:
                continue
            if not event['register_student']:
                continue
        if not event['event_registered'] in ['present', 'registered']:
            continue

        if event['type_code'] == 'rdv':
            jkey = 'rdv_indiv_registered' if event['rdv_indiv_registered'] is not None else 'rdv_group_registered'
            if event[jkey] is None:
                start = event['start']
                end = event['end']
            else:
                start = event[jkey].split('|')[0]
                end = event[jkey].split('|')[1]
        else:
            start = event['start']
            end = event['end']

        minified.append({
            'id': event['codeevent'],
            'title': event['acti_title'],
            'start': start,
            'location': event['room']['code'].split('/')[-1] if event['room'] is not None and "code" in event[
                "room"] else "Pas de salle",
            'end': end,
            'type': event['type_code'],
        })

    for act in activities:
        if not act['registered']:
            continue
        if not act['type_acti_code'] == 'proj':
            continue

        beg_date = act["begin_acti"]
        end_date = act["end_acti"]
        minified_activities.append({
            'id': act['codeacti'],
            'title': act['acti_title'],
            'start': beg_date,
            'end': end_date,
        })

    print("Sorting data")
    minified.sort(key=lambda x: x['start'])

    print("Synchronizing data")
    caldav_manager.synchronize(minified, minified_activities)
    print("All events synchronized !")


if __name__ == '__main__':
    run()
    exit(0)
