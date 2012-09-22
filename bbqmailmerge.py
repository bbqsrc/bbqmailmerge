import csv
import json
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
		cfg['mail_user'] = ''
	if 'mail_pass' not in cfg:
		cfg['mail_pass'] = ''
	
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


def send_mail(emails, mailer_cfg):
	mailer = Mailer(
		mailer_cfg['mail_host'],
		user=mailer_cfg['mail_user'],
		passwd=mailer_config['mail_pass']
	)
	mailer.connect()
	
	for mail in emails:
		mailer.send_email(**mail)
		print("Send email to '%s'." % mail['to'])


if __name__ == "__main__":
	import sys, argparse
	p = argparse.ArgumentParser(
			description='Merge some mail.', 
			epilog='Files must have a matching .txt and .json in the same directory to work successfully.')
	p.add_argument('-d', '--dry-run', action='store_true', help='Emulate a mailout')
	p.add_argument('-c', '--config', help='Mailer config')
	p.add_argument('mailouts', nargs='+', help="Mailout names")
	args = p.parse_args()
	
	parsed_mail = parse_mailouts(args.mailouts)
	
	if args.dry_run:
		print("%s emails will be sent." % len(parsed_mail))
		sys.exit()
	send_mail(parsed_mail, parse_mailer_config(args.config))
