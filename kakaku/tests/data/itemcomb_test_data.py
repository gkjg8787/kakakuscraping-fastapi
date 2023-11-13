
storeconf = {
    "静岡本店": [ { "boundary": "0<=","postage":"300" } ]
    ,"駿河屋": [
        {"boundary": "1000>", "postage":"440"}
        ,{"boundary": "1000<=:1500>", "postage":"385"}
        ,{"boundary": "5000>", "postage":"240" }
        ]
    ,"函館美原": [ {"boundary": "0<=","postage":"600" } ]
    ,"室蘭弥生": [ {"boundary": "0<=","postage":"600" } ]
    ,"ネットオフ": [ {"boundary": "1500>","postage":"440" } ]
    ,"うねめ通り": [ {"boundary": "0<=","postage":"300" } ]
    ,"いわき平": [ {"boundary": "0<=","postage":"300" } ]
    ,"日本橋": [ {"boundary": "0<=","postage":"300" } ]
    ,"名古屋大須": [ {"boundary": "0<=","postage":"300" } ]
    ,"高槻": [ {"boundary": "0<=","postage":"350" } ]
    ,"福島北": [ {"boundary": "0<=","postage":"300" } ]
    ,"利府": [ {"boundary": "0<=","postage":"300" } ]
    ,"秋葉原本館": [ {"boundary": "0<=","postage":"300" } ]
    ,"千葉中央": [ {"boundary": "0<=","postage":"300" } ]
    ,"南瀬名": [ {"boundary": "0<=","postage":"350" } ]
    ,"宇都宮": [ {"boundary": "0<=","postage":"400" } ]
}

item_list_case_1 = {
    "itemlist":[
        {"itemname":"となりのトトロ", "storename":"駿河屋", "price":"2200" }
        ,{"itemname":"となりのトトロ", "storename":"静岡本店", "price":"1900" }
        ,{"itemname":"風の谷のナウシカ", "storename":"駿河屋", "price":"1500" }
        ,{"itemname":"風の谷のナウシカ", "storename":"静岡本店", "price":"1900" }
        ,{"itemname":"ゲド戦記", "storename":"静岡本店", "price":"1800" }
    ],
    "storeconf":storeconf,
    "result":{
        "sum_pos_in": 5740,
        "sum_postage": 540,
        "静岡本店": {
            "items": [
                {
                    "itemname":"となりのトトロ",
                    "price":1900
                },
                {
                    "itemname":"ゲド戦記",
                    "price":1800
                }
            ],
            "postage": 300,
            "sum_pos_out": 3700
        },
        "駿河屋": {
            "items": [
                {
                    "itemname":"風の谷のナウシカ",
                    "price":1500
                }
            ],
            "postage": 240,
            "sum_pos_out": 1500
        }
    }
}
item_list_case_2 = {
    "itemlist":[
        {"itemname":"もののけ姫", "storename":"駿河屋", "price":"2200" }
        ,{"itemname":"もののけ姫", "storename":"静岡本店", "price":"1900" }
        ,{"itemname":"耳をすませば", "storename":"駿河屋", "price":"2500" }
        ,{"itemname":"耳をすませば", "storename":"静岡本店", "price":"1900" }
        ,{"itemname":"千と千尋の神隠し", "storename":"駿河屋", "price":"1200" }
        ,{"itemname":"千と千尋の神隠し", "storename":"静岡本店", "price":"1800" }
    ],
    "storeconf":storeconf,
    "result":{
        "sum_pos_in": 5840,
        "sum_postage": 540,
        "静岡本店": {
            "items": [
                {
                    "itemname":"耳をすませば",
                    "price":1900
                }
            ],
            "postage": 300,
            "sum_pos_out": 1900
        },
        "駿河屋": {
            "items": [
                {
                    "itemname":"もののけ姫",
                    "price":2200
                 },
                 {
                    "itemname":"千と千尋の神隠し",
                    "price":1200
                }
            ],
            "postage": 240,
            "sum_pos_out": 3400
        }
    }
}
item_list_case_3 = {
    "itemlist":[
        {"itemname":"天空の城ラピュタ", "storename":"駿河屋", "price":"1500" }
        ,{"itemname":"天空の城ラピュタ", "storename":"函館美原", "price":"1350" }
        ,{"itemname":"機動戦士ガンダム", "storename":"静岡本店", "price":"1912" }
        ,{"itemname":"機動戦士ガンダム", "storename":"室蘭弥生", "price":"2178" }
        ,{"itemname":"機動戦士ガンダム", "storename":"ネットオフ", "price":"2598" }
        ,{"itemname":"耳をすませば", "storename":"ネットオフ", "price":"3198" }
        ,{"itemname":"耳をすませば", "storename":"高槻", "price":"2480" }
        ,{"itemname":"耳をすませば", "storename":"福島北", "price":"2611" }
        ,{"itemname":"耳をすませば", "storename":"名古屋大須", "price":"2811" }
        ,{"itemname":"耳をすませば", "storename":"函館美原", "price":"2850" }
        ,{"itemname":"耳をすませば", "storename":"いわき平", "price":"2880" }
        ,{"itemname":"耳をすませば", "storename":"うねめ通り", "price":"3011" }
        ,{"itemname":"帰ってきたドラえもん", "storename":"うねめ通り", "price":"2211" }
    ],
    "storeconf":storeconf,
    "result":{
        "sum_pos_in": 9293,
        "sum_postage": 1190,
        "うねめ通り": {
            "items": [
                {
                    "itemname":"帰ってきたドラえもん",
                    "price":2211
                }
            ],
            "postage": 300,
            "sum_pos_out": 2211
        },
        "静岡本店": {
            "items": [
                {
                    "itemname":"機動戦士ガンダム",
                    "price":1912
                }
            ],
            "postage": 300,
            "sum_pos_out": 1912
        },
        "駿河屋": {
            "items": [
                {
                    "itemname":"天空の城ラピュタ",
                    "price":1500
                }
            ],
            "postage": 240,
            "sum_pos_out": 1500
        },
        "高槻": {
            "items": [
                {
                    "itemname":"耳をすませば",
                    "price":2480
                }
            ],
            "postage": 350,
            "sum_pos_out": 2480
        }
    }
}
item_list_case_4 = {
    "itemlist":[
        {"itemname":"ラジオの時間", "storename":"利府", "price":"2511" }
        ,{"itemname":"ラジオの時間", "storename":"高槻", "price":"2480" }
        ,{"itemname":"マトリックス", "storename":"利府", "price":"1311" }
        ,{"itemname":"マトリックス", "storename":"静岡本店", "price":"1411" }
        ,{"itemname":"のぼうの城", "storename":"静岡本店", "price":"1911" }
        ,{"itemname":"のぼうの城", "storename":"ネットオフ", "price":"2598" }
        ,{"itemname":"ラジオの時間", "storename":"ネットオフ", "price":"3198" }
    ],
    "storeconf":storeconf,
    "result":{
        "sum_pos_in": 6333,
        "sum_postage": 600,
        "利府": {
            "items": [
                {
                    "itemname":"ラジオの時間",
                    "price":2511
                },
                {
                    "itemname":"マトリックス",
                    "price":1311
                }
            ],
            "postage": 300,
            "sum_pos_out": 3822
        },
        "静岡本店": {
            "items": [
                {
                    "itemname":"のぼうの城",
                    "price":1911
                }
            ],
            "postage": 300,
            "sum_pos_out": 1911
        }
    }
}
item_list_case_5 = {
    "itemlist":[
        {"itemname":"となりのトトロ", "storename":"駿河屋", "price":"2200" }
        ,{"itemname":"となりのトトロ", "storename":"静岡本店", "price":"1900" }
        ,{"itemname":"となりのトトロ", "storename":"函館美原", "price":"1600" }
        ,{"itemname":"となりのトトロ", "storename":"室蘭弥生", "price":"1600" }
        ,{"itemname":"となりのトトロ", "storename":"うねめ通り", "price":"1800" }
    ],
    "storeconf":storeconf,
    "result":{
        "sum_pos_in": 2100,
        "sum_postage": 300,
        "うねめ通り": {
            "items": [
                {
                    "itemname":"となりのトトロ",
                    "price":1800
                }
            ],
            "postage": 300,
            "sum_pos_out": 1800
        }
    }
}
item_list_case_6 = {
    "itemlist":[
        {"itemname":"A", "storename":"駿河屋", "price":"1500" }
        ,{"itemname":"A", "storename":"函館美原", "price":"1350" }
        ,{"itemname":"A", "storename":"静岡本店", "price":"1912" }
        ,{"itemname":"A", "storename":"室蘭弥生", "price":"2178" }
        ,{"itemname":"A", "storename":"ネットオフ", "price":"2598" }
        ,{"itemname":"A", "storename":"千葉中央", "price":"2598" }
        ,{"itemname":"A", "storename":"利府", "price":"2598" }
        ,{"itemname":"B", "storename":"ネットオフ", "price":"3198" }
        ,{"itemname":"B", "storename":"高槻", "price":"2480" }
        ,{"itemname":"B", "storename":"福島北", "price":"2611" }
        ,{"itemname":"B", "storename":"名古屋大須", "price":"2811" }
        ,{"itemname":"B", "storename":"函館美原", "price":"2850" }
        ,{"itemname":"B", "storename":"いわき平", "price":"2880" }
        ,{"itemname":"B", "storename":"うねめ通り", "price":"3011" }
        ,{"itemname":"C", "storename":"駿河屋", "price":"1000" }
        ,{"itemname":"C", "storename":"静岡本店", "price":"1000" }
        ,{"itemname":"C", "storename":"室蘭弥生", "price":"1200" }
        ,{"itemname":"C", "storename":"南瀬名", "price":"1400" }
        ,{"itemname":"C", "storename":"秋葉原本館", "price":"1401" }
        ,{"itemname":"C", "storename":"高槻", "price":"1708" }
        ,{"itemname":"C", "storename":"宇都宮", "price":"2211" }
        ,{"itemname":"D", "storename":"室蘭弥生", "price":"2400" }
        ,{"itemname":"D", "storename":"いわき平", "price":"2500" }
        ,{"itemname":"D", "storename":"室蘭弥生", "price":"2600" }
        ,{"itemname":"D", "storename":"南瀬名", "price":"2900" }
        ,{"itemname":"D", "storename":"秋葉原本館", "price":"3000" }
        ,{"itemname":"D", "storename":"高槻", "price":"3000" }
        ,{"itemname":"D", "storename":"宇都宮", "price":"3010" }
        ,{"itemname":"E", "storename":"ネットオフ", "price":"800" }
        ,{"itemname":"E", "storename":"いわき平", "price":"950" }
        ,{"itemname":"E", "storename":"室蘭弥生", "price":"1100" }
        ,{"itemname":"E", "storename":"駿河屋", "price":"1100" }
        ,{"itemname":"E", "storename":"秋葉原本館", "price":"1200" }
        ,{"itemname":"E", "storename":"高槻", "price":"1300" }
        ,{"itemname":"E", "storename":"宇都宮", "price":"1301" }
        ,{"itemname":"F", "storename":"ネットオフ", "price":"800" }
        ,{"itemname":"F", "storename":"いわき平", "price":"950" }
        ,{"itemname":"F", "storename":"室蘭弥生", "price":"1100" }
        ,{"itemname":"F", "storename":"駿河屋", "price":"1100" }
        ,{"itemname":"F", "storename":"秋葉原本館", "price":"1200" }
        ,{"itemname":"F", "storename":"高槻", "price":"1300" }
        ,{"itemname":"F", "storename":"宇都宮", "price":"1301" }
        ,{"itemname":"G", "storename":"秋葉原本館", "price":"600" }
        ,{"itemname":"G", "storename":"函館美原", "price":"700" }
        ,{"itemname":"G", "storename":"千葉中央", "price":"750" }
        ,{"itemname":"G", "storename":"ネットオフ", "price":"780" }
        ,{"itemname":"G", "storename":"秋葉原本館", "price":"781" }
        ,{"itemname":"G", "storename":"日本橋", "price":"900" }
        ,{"itemname":"G", "storename":"福島北", "price":"1200" }
    ],
    "storeconf":storeconf,
    "result":{
        'sum_pos_in': 10750,
        'sum_postage': 890, 
        'いわき平': {
            'items': [{'itemname': 'D', 'price': 2500}],
            'postage': 300,
            'sum_pos_out': 2500
        },
        'ネットオフ': {
            'items': [
                {'itemname': 'E', 'price': 800},
                {'itemname': 'F', 'price': 800},
                {'itemname': 'G', 'price': 780}
            ],
            'postage': 0,
            'sum_pos_out': 2380
        },
        '駿河屋': {
            'items': [
                {'itemname': 'A', 'price': 1500},
                {'itemname': 'C', 'price': 1000}
            ],
            'postage': 240,
            'sum_pos_out': 2500
        },
        '高槻': {
            'items': [{'itemname': 'B', 'price': 2480}],
            'postage': 350,
            'sum_pos_out': 2480
        }
    }
}    