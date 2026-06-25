# Release flow

The release flow is triggered automatically after each migration, and picks up the latest
file in data/releases/ (ordered by filename, must end in `.yaml`) and makes a release
accordingly.

## User steps

* Create a news embargo
* Create a news article with all details, leaving as unapproved
* Create a `data/releases/<date>.yaml` file
* If this is the first alpha/beta/rc, create a Version record for this version
* `git push`

### Version mixing

Normally, on a *major release* or on *first beta version*, a single
release should be in the `yaml` file. This will trigger a "full"
announcement on the website. In these cases, set the `announcetext`
key in the yaml to the full details.

If more than one version is listed, it is *always* treated as a set of
minor releases. This can either be a general set of scheduled minor
releases, or it can be a combination of a beta and minors for
example. Even a major version can be included, but it will be treated
as a minor version on the website.

## Resulting actions

* Release date is adjusted to date from yaml file
* Latest minor version on the Version object is adjusted to the one
  from the `yaml` file (note that this happens even if it's
  decreased!) This includes setting alpha/beta/rc number on testing
  releases.
* If the previous version was a testing one and the new one is a `.0`
  major release, the testing flag is turned off and the new `.0` is
  set to both current and supported. Note that if a release directly
  moves from alpha/beta/rc to a minor (such as a `.1`), only the minor
  numbers will be updated and it will not be set to supported/current
  (because this is a non-standard workflow).
* All CVEs listed in the `yaml` (normally only on minor, but
  works for all) set to public and has their announcement linked to
  the news article specified
* News article has date set to date from yaml file and is
  approved, bypassing embargo, and emailed
