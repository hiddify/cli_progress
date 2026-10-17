#!/usr/bin/env bash
# The commits since the previous tag (all of them for the first release), grouped by author.
previous_tag=$(git tag --sort=-creatordate | sed -n 2p)
git shortlog ${previous_tag:+"${previous_tag}.."} HEAD | sed 's/^./    &/'
