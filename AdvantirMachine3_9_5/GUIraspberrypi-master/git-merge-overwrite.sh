# overwrite master with contents of feature branch (develop > master)
git checkout develop    # source name
git merge -s ours master  # target name
git checkout master       # target name
git merge develop       # source name