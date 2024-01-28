#!/bin/bash
baseBranchName='branch_custom_develop'
status=0
# Define colors for different message levels
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

debug() {
	echo -e "${GREEN}[DEBUG] $1${NC}"
}
info() {
	echo -e "${YELLOW}[INFO] $1${NC}"
}
error() {
	echo -e "${RED}[ERROR] $1${NC}" >&2
}

Check_branch_get_list() {
	existed_in_remote=$(git ls-remote --heads origin)
}

main() {
	if [[ $existed_in_remote != *$branchName* ]]; then
		main_process_git
	fi
}

main_process_git() {
	git checkout master
	message="[KRB]: normalized ingestion files for: '$tableName'"
	info "$message"
	debug "new branch $branchName"
	git branch -D "$branchName" &>/dev/null
	git checkout -b "$branchName"
	git checkout "$baseBranchName" '--' ./"$path"

	if [[ $(git status --porcelain | wc -l) -eq 5 ]]; then
		debug "adding $path"
		echo git checkout "$baseBranchName" '--' "$path"
		debug "making git commit :)"
		git commit -m "$message"
		git push origin -u HEAD --quiet
		status=1
	else
		error "No local changes to push."
	fi

}

cd ../

if [[ $(git branch --show-current) != "$baseBranchName" ]]; then
	echo "Tu rama deberia ser $baseBranchName, saliendo" && exit
fi

Check_branch_get_list

while IFS= read -r -d '' line; do
	path=$(dirname "$line")
	tableName=$(echo "$path" | awk 'BEGIN { FS = "/" } ; {print $(NF -1)}')
	branchName=krb/"$tableName"_custom
	main "$branchName"
done < <(find . -type f -name '*.conf' -a -path '*branch*' -print0)

git checkout "$baseBranchName"

if [[ "$status" == 1 ]]; then

	cd ./out/ || echo 'out folder dont exist' | exit
	Check_branch_get_list
	echo "$existed_in_remote" | awk '{print $2}' >branch-remote.txt

	read -r -p "Press any key to start pull request... " -n1 -s
	if [[ "$(python3 -V)" =~ "Python 3" ]] &>/dev/null; then
		python3 api_bitbucket.py
	else
		python api_bitbucket.py
	fi

else
	echo "Sin cambios realizados, saliendo" && exit
fi