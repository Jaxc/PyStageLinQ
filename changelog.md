# Changelog
Here follows a log of released versions of PyStageLinQ.

## [DEV] 
### Fixed
Invalid tokens are not generated, this used to cause issues when starting as a StageLinQ device does respond to clients
with invalid tokens.

README is now looking more nice, with some badges added.

Added Typehints to more functions

Various Documentation updates, things should be clearer and more informative now

Code now uses classes instead of raw data in several places.

### Added
PyStageLinQ can now send announcement messages and look for StageLinQ devices on all network interfaces.
To send on only one interface use `PyStageLinQ.__init__(..., ip=169.254.13.37, ...)`

Unit tests, code coverage is now 100%. Also added a lot to the CI builds to support this.
### Removed
Remove announcement_ip from `PyStageLinQ.__init__` as this can be derived from chosen ip. e.g. if 169.254.13.37 is chosen
announcement ip will be at 169.254.255.255.

## [0.1.2] - Documentation update again
A lot of small fixes and additions now makes the readthedocs.org link to actually work.
### Fixed
readthedocs documentation actually builds and is available.
### Added
Support for CircleCI for future builds and testing. Release script has been updated to be done automatically
in CI chain when a tag is created. In theory only this document needs to be updated for each release and a
tag added to git and all release work is done.

## [0.1.1] - Documentation update
Added documentation
### Added
docs/folder with documentation, run `make html` to create documentation. It is also available at h
https://pystagelinq.readthedocs.io/en/latest/

### Changes
Some code has been changed to better correspond to how it is used. This mostly means that functions has been marked
as private.

### Known Issues
Same known issues as for version 0.1.0.

## [0.1.0] - Initial release
Basic functionality done, but documentation needs to be done. I expect the API to change when I write this, so this is
a pre-release until Documentation is in place.
### Added
Everything
### Changes
Yes
### Fixed
Some things
### Security
No
### Known Issues
There are currently one known issue:
#### PyStageLinq cannot connect to device
For some reason that I cannot figure out PyStageLinQ cannot connect to my Prime Go sometimes. This seems to be
completely random and is because the device does not send a table of services when requested
