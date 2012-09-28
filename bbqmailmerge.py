import csv
import json
import time
from mako.template import Template
from bbqutils.email import Mailer


def parse_csv(csv_fn):
    f = open(csv_fn + ".csv", 'r')
    reader = csv.reader(f)
    header = reader.__next__()

    if "email" not in header:
        raise Exception("There is no email column")

    rows = []
    for row in reader:
        rows.append(dict(zip(header, row)))

    f.close()
    return rows


def parse_mailer_config(cfg_fn):
    if cfg_fn is None:
        cfg = {}
    else:
        cfg = json.load(open(cfg_fn))
    if 'mail_host' not in cfg:
        cfg['mail_host'] = "localhost"
    if 'mail_user' not in cfg:
        cfg['mail_user'] = None 
    if 'mail_pass' not in cfg:
        cfg['mail_pass'] = None

    return cfg


def parse_mail_config(json_fn):
    cfg = json.load(open(json_fn + ".json"))
    for key in ['from', 'subject']:
        if key not in cfg:
            raise Exception("Mandatory key missing '%s'" % key)
    return cfg


def parse_template(template_fn, **kwargs):
    template = Template(filename=template_fn + ".txt")
    return template.render(**kwargs)


def parse_mailouts(mailouts):
    mails = []

    for mailout in mailouts:
        csv = parse_csv(mailout)
        cfg = parse_mail_config(mailout)

        for row in csv:
            config = cfg.copy()
            config.update(row)

            try:
                mail = parse_template(mailout, **config)
                mails.append({
                    "frm": config['from'],
                    "to": config['email'],
                    "subject": config['subject'],
                    "text": mail
                })
            except Exception as e:
                print("Error creating mail for '%s'." % config['email'])
                continue
    return mails


def send_mail(emails, mailer_cfg, wait=None, interactive=False):
    mailer = Mailer(
        mailer_cfg['mail_host'],
        user=mailer_cfg['mail_user'],
        passwd=mailer_cfg['mail_pass']
    )
    mailer.connect()

    c = 0
    start_time = time.time()
    elen = len(emails)
    for mail in emails:
        c += 1
        try:
            mailer.send_email(**mail)
        except Exception as e:
            print(e)
            print("[%s/%s] Exception for '%s'." % (c, elen, mail['to']))
            continue
        
        if interactive:
            print("[%s/%s] Sent email to '%s'." % (c, elen, mail['to']))
        if wait:
            time.sleep(wait)
    
    if interactive:
        end_time = time.time()
        diff = end_time - start_time
        mps = elen / diff
        print("Mailing took %.2f seconds. %.2f mails per second." % (diff, mps))
    
    mailer.disconnect()


def merge(mailouts, config=None, dry_run=False, interactive=False, skip_confirm=False, wait=None):
    parsed_mail = parse_mailouts(mailouts)

    if dry_run:
        if interactive:
            print("%s emails will be sent." % len(parsed_mail))
        return len(parsed_mail)

    if interactive and not skip_confirm:
        x = input("%s emails will be sent. Do you want to continue [y/N]? "
                  % len(parsed_mail))
        if x.lower() != "y":
            print("Aborted.")
            return 0

    send_mail(parsed_mail, parse_mailer_config(config), wait, interactive)
    return len(parsed_mail)


def test(mailouts, **kwargs):
    from collections import Counter
    c = Counter()

    for mailout in mailouts:
        rows = parse_csv(mailout)
        for n, row in enumerate(rows):
            email = row.get('email', None)
            if email is None:
                print("Line %s: email field is missing" % n)
            elif email.strip() is "":
                print("Line %s: email is blank" % n)
            else:
                c[email] += 1
                if c[email] > 1:
                    print("Line %s: duplicate email '%s'" % (n, email))

if __name__ == "__main__":
    import sys
    import argparse
    p = argparse.ArgumentParser(
        description='Merge some mail.',
        epilog='Files must have a matching .txt and .json in the same directory to work successfully.')
    p.add_argument(
        '-d', '--dry-run', action='store_true', help='Emulate a mailout')
    p.add_argument('-c', '--config', help='Mailer config')
    p.add_argument('-w', '--wait', type=float,
        help='Delay between mail sending (Default: none)')
    p.add_argument(
        '-t', '--test', action='store_true', help='Verify CSV')
    p.add_argument(
        '-y', '--skip-confirm', action="store_true",
        help="Do not ask for confirmation")
    p.add_argument('mailouts', nargs='+', help="Mailout names")

    args = p.parse_args()
    if args.test:
        test(interactive=True, **vars(args))
    else:
        merge(interactive=True, **vars(args))
