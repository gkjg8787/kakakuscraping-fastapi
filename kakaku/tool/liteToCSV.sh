tables=(
"items" "url" "siteupdate"
"itemsprice" "pricelog_2days" "newestitem"
"groups" "groupsitem"
"stores" "store_postage"
)

dbname="iteminfo.sqlite"
outputdir="database_csv"
archiveextend=".tgz"
fileextend=".csv"


output_to_csv(){
sqlite3 ${dbname} << EOF
.headers on 
.mode csv
.output ${1}${2}
SELECT * FROM ${1}
;
.quit
EOF
}

if [ ! -d ${outputdir} ]; then
  mkdir ${outputdir}
else
  echo "exist dir ${outputdir}"
  echo "end script"
  exit 1
fi
if [ -f ${outputdir}${archiveextend} ]; then
  echo "exist file ${outputdir}${archiveextend}"
  echo "end script"
  exit 1
fi
if [ ! -f ${dbname} ]; then
  echo "not exist db ${dbname}"
  echo "end script"
  exit 1
fi

for i in "${!tables[@]}";
do
  output_to_csv "${tables[$i]}" ${fileextend}
  mv ${tables[$i]}${fileextend} ${outputdir}/${tables[$i]}${fileextend}
done

tar zcf ${outputdir}${archiveextend} ${outputdir}
rm ${outputdir}/*${fileextend}
rmdir ${outputdir}
echo "output directory archive : ${outputdir}${archiveextend}"

