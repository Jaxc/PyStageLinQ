# Changelog
Here follows a log of released versions of PyStageLinQ.

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

## [0.1.0] - Inital release
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
