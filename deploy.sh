#!/bin/bash


LV=`cat auto/last_version`
PNAME=`cat auto/project_name`

echo "Select the version to deploy (last: $LV)"

read version

echo "Insert the changelog for this version"

read changelog

echo "$version - $changelog" >> auto/changelog

echo "$version" > auto/last_version

git add . && \
git add -u && \
git commit -m "$changelog" && \
git push

yes | gcloud app deploy --version "$version" --project "$PNAME"
