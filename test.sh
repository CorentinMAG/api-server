git tag -d 3.3.3
git push origin -d 3.3.3
git add .
git commit --amend --no-edit
git push -f
git tag -a 3.3.3 -m "TEST TAG"
git push --tags
