# Commit checklist
* Make sure unit tests are successful
* make sure changelog.md has been updated
* Check if the update affects the documentation, and if so update it
* If CI has stopped working it is fine to update it in the commit

# Release checklist
* Recheck changelog.md and docs/ to make sure they are updated properly
* Before a real release is to be created, create a dev release to make sure the release process works as intended.
It is not possible to re-release a version number so better to first release to a test.
* This is done by adding a tag in git. The CI will then automatically build and publish the release.
* Once the dev release is out, do additional testing. Currently, I'll test it for a few streams to make sure it seems 
stable but this process could be done better.
* Once the dev release seems stable, create another tag on the same commit with the real release version
* Once the release is deployed, create a release in GitHub, use changelog.md to make sure the changelog is correct on
the release
* IMMEDIATELY after release is done, create a new commit that adds a new section to changelog.md to the new version. The new release shall only have the patch incremented by one, if at a later date the
next release gets upgraded to a new minor or major version this has to be changed again.

# Versioning
PyStageLinQ uses the standard major.minor.patch version convention. 

The major version is to indicate incompatibility with previous software, except for version 1.0.0.
The plan is to push for release 1.0.0 to avoid
getting stuck in the 0.x.y pitfall with having stable software but not a version 1.0.0 release. After that no new major
release is planned.

Minors versions are ment to indicate new functionality, while a patch version is a smaller fix that should not affect
the usage of the code.

There is also the possibility for dev-releases, these are a test version released before a real version, either to test
a fix or to test the release flow. These are indicated by having devx in the end, e.g. 0.2.2.dev1