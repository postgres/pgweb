# email tools

This directory holds a few trivial email testing tools. They work on emails
that are in the `mailqueue` app, so they first have to be generated (with pgweb
that's typically done by approving news or using the `news_send_email` command),
and then referenced by their id number. They are used to test formats and markups.

## parse_email.py

This tool will simply parse and print the MIME structure of the email in question.

## send_email.py

This tools will take the email and send it out using SMTP/AUTH (hardcoded to always
have STARTTLS) according to the settings in `config.yaml` for end-to-end testing.

Note that emails are *not* removed from the queue when sent this way! This way they
can be sent to multiple addresses for testing.

## config.yaml

Used for both tools to find their database, and for `send_email.py` to know how to
connect to the server. See the `config.yaml.sample` file for example/docs.
