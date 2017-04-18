#!/bin/sh

# vault-merge
# Benjamin Ragheb <ben@benzado.com>

# This shell script handles conflicts generated by attempts to merge encrypted
# Ansible Vault files. Run `git merge` as usual; when git warns of a merge
# conflict, run this command to attempt a merge on the unencrypted versions of
# the file. If there are conflicts, you will be given a chance to correct them
# in $EDITOR.

# First, we ensure we are inside the working directory of a git repo.

GIT_ROOT=`git rev-parse --show-toplevel`
if [ $? != 0 ]; then
    exit $?
fi

# Next, we set a default location for a vault password file, and allow the user
# to override it if desired.

VAULT_PASSWORD_FILE="$GIT_ROOT/.ansible-vault-password"

while getopts "p:" opt; do
    case $opt in
        p)
            VAULT_PASSWORD_FILE=$OPTARG
            ;;
        \?)
            # Invalid option (e.g., -p without an argument)
            exit 1
            ;;
    esac
done
shift $(($OPTIND - 1))

VAULT_OPT="--vault-password-file=$VAULT_PASSWORD_FILE"
VAULT_FILE=$1

# If no vault has been provided, abort!

if [ -z $VAULT_FILE ]; then
    echo "Usage: $0 [-p PASSWORD_FILE] VAULT_FILE"
    exit 1
fi

# If the password file doesn't exist, we prompt for the password and save it.

if [ ! -e $VAULT_PASSWORD_FILE ]; then
    read -s -p "Vault Password: " VAULT_PASSWORD
    echo
    echo "Remembering password in $VAULT_PASSWORD_FILE"
    echo $VAULT_PASSWORD > $VAULT_PASSWORD_FILE
else
    echo "Using password saved in $VAULT_PASSWORD_FILE"
fi

# Fetch the base (common ancestor) version of the encrypted vault file, save
# it to a temporary location, and decrypt it. (Hat Tip to the git-merge manual
# page for tipping me off to the `git show :1:path` notation.)

BASE=`mktemp ${VAULT_FILE}.base.XXXX`
git show :1:${VAULT_FILE} > $BASE 2> /dev/null
if [ $? != 0 ]; then
    echo "Path '${VAULT_FILE}' does not have any conflicts."
    rm $BASE
    exit 1
fi
ansible-vault decrypt $VAULT_OPT $BASE || exit $?

# Do the same with the current (branch we are merging INTO) version of the vault
# file.

CURRENT=`mktemp ${VAULT_FILE}.current.XXXX`
git show :2:${VAULT_FILE} > $CURRENT 2> /dev/null
ansible-vault decrypt $VAULT_OPT $CURRENT || exit $?

# And finally, with the other (branch we a merging FROM) version of the vault.

OTHER=`mktemp ${VAULT_FILE}.other.XXXX`
git show :3:${VAULT_FILE} > $OTHER 2> /dev/null
ansible-vault decrypt $VAULT_OPT $OTHER || exit $?

# Now that we have all three versions decrypted, ask git to attempt the merge
# again. If it fails again due to a conflict, open $EDITOR and let the user
# perform a manual merge.

git merge-file $CURRENT $BASE $OTHER
if [ $? == 0 ]; then
    echo "Merge OK"
else
    echo "Merge conflict; opening editor to resolve."
    $EDITOR $CURRENT
fi

# Now that we're done, encrypt the file and move it into the repo, and clean up
# the temporary files (they contain secrets!).

ansible-vault encrypt $VAULT_OPT $CURRENT
cp $CURRENT $VAULT_FILE
rm $BASE $CURRENT $OTHER
rm $VAULT_PASSWORD_FILE

echo "$VAULT_FILE has been updated."
echo "    (use \"git add $VAULT_FILE\" to mark as resolved)"
echo "    (or re-run this command to retry the merge)"
exit 0
