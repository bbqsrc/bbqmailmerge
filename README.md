# bbqmailmerge

Merge some mail, send some mail.

- Create a .csv file (eg `test.csv`) with all the necessary columns you wish to use for mail merge. `email` column is mandatory.
- Create a .json file (eg `test.json`) with your `from` address and `subject` line.
- Create a .txt file (eg `test.txt`) which is a Mako template with the actual mail to be merged.
- Run the application with the name of the series of files (eg `bbqmailmerge.py test`).

Add `-d` to do a dry-run to see if it will work before running the merge and send.
