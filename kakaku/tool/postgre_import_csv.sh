tables=(
"items" "url" "siteupdate"
"itemsprice" "pricelog_2days" "newestitem"
"groups" "groupsitem"
"stores" "store_postage"
)
dbuser="dbuser"
dbname="appdb"
fileextend=".csv"
importarchive="database_csv"
archiveextend=".tgz"
parentdirname="/tmp"
importdir="${parentdirname}/${importarchive}"

import_csv(){
psql -U ${dbuser} -d ${dbname} -c "\copy ${1} from ${importdir}/${1}${fileextend} with csv header"
}

if [ ! -f ${importdir}${archiveextend} ]; then
  echo "not exist archive : ${importdir}${archiveextend}"
  echo "end script"
  exit 1
fi
curdir=`pwd`
cd ${parentdirname}
tar zxf ${importdir}${archiveextend}

for i in "${!tables[@]}";
do
  import_csv "${tables[$i]}"
done

rm ${importarchive}/*${fileextend}
rmdir ${importarchive}
cd ${curdir}