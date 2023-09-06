tables=(
"items"
"url"
"siteupdate"
"itemsprice"
"pricelog_2days"
"newestitem"
"groups"
"groupsitem"
"stores"
"store_postage"
)
seq_tables=(
  "items:items_item_id"
  "url:url_url_id"
  "itemsprice:itemsprice_log_id"
  "pricelog_2days:pricelog_2days_log_id"
  "newestitem:newestitem_item_id"
  "groups:groups_group_id"
  "stores:stores_store_id"
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
reset_seq(){
  t_base=${1%:*}
  t_seq=${1#*:}
  t_clm=${t_seq#*${t_base}_}
  psql -U ${dbuser} -d ${dbname} -c "SELECT SETVAL('${t_seq}_seq', (SELECT MAX(${t_clm}) FROM ${t_base}) )"
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
for i in "${!seq_tables[@]}";
do
  reset_seq "${seq_tables[$i]}"
done

rm ${importarchive}/*${fileextend}
rmdir ${importarchive}
cd ${curdir}