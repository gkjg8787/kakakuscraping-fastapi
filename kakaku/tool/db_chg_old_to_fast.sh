#!/bin/bash
chg_items(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE items RENAME TO items_temp;

CREATE TABLE items (
        item_id INTEGER NOT NULL,
        name VARCHAR NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        PRIMARY KEY (item_id)
);

INSERT INTO items(item_id, name)
  SELECT item_id, name FROM items_temp;

DROP TABLE items_temp;
.quit
EOF
}
chg_url(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE url RENAME TO url_temp;

CREATE TABLE url (
        url_id INTEGER NOT NULL,
        urlpath VARCHAR NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        PRIMARY KEY (url_id)
);

INSERT INTO url(url_id, urlpath)
  SELECT url_id, urlpath FROM url_temp;

DROP TABLE url_temp;
.quit
EOF
}
chg_siteupdate(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE siteupdate RENAME TO siteupdate_temp;

CREATE TABLE siteupdate (
        item_id INTEGER NOT NULL,
        url_id INTEGER NOT NULL,
        active VARCHAR NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        PRIMARY KEY (item_id, url_id)
);

INSERT INTO siteupdate(item_id, url_id, active)
  SELECT item_id, url_id, active FROM siteupdate_temp;

DROP TABLE siteupdate_temp;
.quit
EOF
}
chg_itemsprice(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE itemsprice RENAME TO itemsprice_temp;

CREATE TABLE itemsprice (
        log_id INTEGER NOT NULL,
        url_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        uniqname VARCHAR NOT NULL,
        usedprice INTEGER NOT NULL,
        newprice INTEGER NOT NULL,
        taxin VARCHAR NOT NULL,
        onsale VARCHAR NOT NULL,
        salename VARCHAR,
        issuccess VARCHAR NOT NULL,
        trendrate FLOAT NOT NULL,
        storename VARCHAR NOT NULL,
        PRIMARY KEY (log_id)
);

INSERT INTO itemsprice(log_id, url_id, created_at, uniqname, usedprice, newprice,
                      taxin, onsale, salename, issuccess, trendrate, storename) 
SELECT log_id, url_id, created_at, uniqname, usedprice, newprice,
       taxin ,onsale, ifnull(salename,""), issuccess, ifnull(trendrate,0), ifnull(storename,"")
    FROM itemsprice_temp;

DROP TABLE itemsprice_temp;
.quit
EOF
}

chg_newestitem(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE newestitem RENAME TO newestitem_temp;

CREATE TABLE newestitem (
        item_id INTEGER NOT NULL,
        url_id INTEGER,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        newestprice INTEGER NOT NULL,
        taxin VARCHAR NOT NULL,
        onsale VARCHAR NOT NULL,
        salename VARCHAR,
        trendrate VARCHAR NOT NULL,
        storename VARCHAR NOT NULL,
        lowestprice INTEGER NOT NULL,
        PRIMARY KEY (item_id)
);

INSERT INTO newestitem(item_id, url_id, created_at, newestprice, taxin,
                       onsale, salename, trendrate, storename, lowestprice) 
SELECT item_id, url_id, created_at, newestprice, taxin
       ,onsale, ifnull(salename,""), ifnull(trendrate, 0), ifnull(storename,""), lowestprice
    FROM newestitem_temp;

DROP TABLE newestitem_temp;

.quit
EOF
}
chg_groups(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE groups RENAME TO groups_temp;

CREATE TABLE groups (
        group_id INTEGER NOT NULL,
        groupname VARCHAR NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        PRIMARY KEY (group_id)
);

INSERT INTO groups(group_id, groupname)
  SELECT group_id, groupname FROM groups_temp;

DROP TABLE groups_temp;
.quit
EOF
}
chg_groupsitem(){
sqlite3 iteminfo.sqlite << EOF
ALTER TABLE groupsitem RENAME TO groupsitem_temp;

CREATE TABLE groupsitem (
        group_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
        PRIMARY KEY (group_id, item_id)
);

INSERT INTO groupsitem(group_id, item_id)
  SELECT group_id, item_id FROM groupsitem_temp;

DROP TABLE groupsitem_temp;
.quit
EOF
}

chg_alltable(){
  chg_items
  chg_url
  chg_siteupdate
  chg_itemsprice
  chg_newestitem
  chg_groups
  chg_groupsitem
}
main(){
  isold_newestitem=`sqlite3 --line iteminfo.sqlite ".schema newestitem" | grep "item_id" | grep -v "NOT NULL"`
  if [ ${#isold_newestitem} -ne 0 ]; then
    echo "change all db column"
    chg_alltable
  fi
}

main
