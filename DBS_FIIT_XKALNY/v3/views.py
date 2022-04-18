import json

import simplejson
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from DBS_FIIT_XKALNY.connection import *


# Create your views here.
def top_purchases(request, match_id):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hero_id, localized_name, array_agg(tbl.item_id  || ','||name ||',' || purchases||'') FROM ("
        "SELECT * FROM ("
        "SELECT heroes.id as hero_id,heroes.localized_name, items.name, items.id as item_id, count(items.name) as purchases,"
        "row_number() over (partition by pl.match_player_detail_id ORDER BY COUNT(items.name) DESC, items.name) as row_num "
        "FROM matches_players_details AS mpd"
        " JOIN matches ON mpd.match_id = matches.id"
        " JOIN purchase_logs AS pl ON mpd.id = pl.match_player_detail_id"
        " JOIN items ON pl.item_id = items.id"
        " JOIN heroes ON mpd.hero_id = heroes.id"
        " WHERE mpd.match_id = {} AND((matches.radiant_win = true AND mpd.player_slot BETWEEN 0 AND 4) OR ( matches.radiant_win = false AND mpd.player_slot BETWEEN 128 AND 132))"
        "GROUP BY heroes.id, items.name, heroes.localized_name, items.id, pl.match_player_detail_id"
        " ORDER BY heroes.id, purchases DESC "
        ") as fin"
        " WHERE fin.row_num <= 5 ORDER BY hero_id, row_num "
        ") as tbl"
        " GROUP BY hero_id, localized_name ".format(match_id))

    data = cursor.fetchall()
    #print(data)
    result = {
        "id": match_id,
        "heroes": []
    }
    for line in data:
        hero = {
            "id": line[0],
            "name": line[1],
            "top_purchases": []
        }
        for purchase in line[2]:
            purchase = purchase.split(',')
            print(purchase)
            hero["top_purchases"].append({
                "id": int(purchase[0]),
                "name": purchase[1],
                "count": int(purchase[2])
            })
        result["heroes"].append(hero)
    print(result)
    return JsonResponse(result)

def abilities_usage(request,ability_id):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute("SELECT id,localized_name, ability_name, winner, bucket, count FROM ("
	                "SELECT *, rank() over (partition by winner,localized_name, ability_name ORDER BY count DESC)FROM ("
		                "SELECT *" 
		                ",COUNT(tbl.bucket) as count "
		                "FROM ("
			                "SELECT heroes.id,heroes.localized_name,abilities.name as ability_name,"
			                "CASE "
				            "WHEN matches.radiant_win = true and mpd.player_slot between 0 and 4 then 'winner'"
				            "WHEN matches.radiant_win = false and mpd.player_slot between 128 and 132 then 'winner'"
				            "ELSE 'loser'"
				            "END as winner,"
			                "CASE "
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 0 and 9 then '0-9'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 10 and 19 then '10-19'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 20 and 29 then '20-29'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 30 and 39 then '30-39'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 40 and 49 then '40-49'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 50 and 59 then '50-59'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 60 and 69 then '60-69'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 70 and 79 then '70-79'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 80 and 89 then '80-89'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) between 90 and 99 then '90-99'"
                            "WHEN FLOOR(au.time*1.0/matches.duration*100) >= 100 then '100-109'"
                            " END as bucket"
			                " FROM abilities"
			                " JOIN ability_upgrades as au ON abilities.id = au.ability_id"
			                " JOIN matches_players_details as mpd ON mpd.id = au.match_player_detail_id"
                            " JOIN matches ON matches.id= mpd.match_id"
                            " JOIN heroes ON mpd.hero_id = heroes.id"
                            " WHERE abilities.id = {}"
		                ") as tbl"
		" GROUP BY tbl.id, tbl.winner, tbl.localized_name, tbl.ability_name, tbl.bucket"
		" ORDER BY count DESC"
        ") as table2 "
        ") as table3 "
        "WHERE rank=1 ORDER BY id, winner DESC ".format(ability_id))
    data = cursor.fetchall()
    print(data)
    result = {
        "id": ability_id,
        "name": data[0][2],
        "heroes": []
    }
    i = 0
    j = 0
    processed_heroes = []
    while i < len(data):
        row = data[i]
        hero_id = data[i][0]
        if hero_id not in processed_heroes:
            processed_heroes.append(hero_id)
        else:
            i+=1
            continue
        j = processed_heroes.index(hero_id)
        hero = {
            "id": hero_id,
            "name": data[i][1],
        }
        if row[3] == 'winner':
            hero["usage_winners"] = {
                "bucket": row[4],
                "count": int(row[5])
            }
        else:
            hero["usage_losers"] = {
                "bucket": row[4],
                "count": int(row[5])
            }
        j = i +1
        # tu prejdem toho hrdinu jedneho vsetky zaznamy o nom
        while j < len(data) and data[j][0] in processed_heroes:
            new_row = data[j]
            if new_row[3] == 'winner':
                hero["usage_winners"] = {
                    "bucket": new_row[4],
                    "count": int(new_row[5])
                }
            else:
                hero["usage_loosers"] = {
                    "bucket": new_row[4],
                    "count": int(new_row[5])
                }
            j += 1
        result["heroes"].append(hero)
        i += 1
    print(result)
    return JsonResponse(result)

def tower_kills(request):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute("SELECT hero_id, localized_name, MAX(count) FROM ("
	        "SELECT localized_name, hero_id, count(localized_name) over (partition by match_id, hero_id, seq) FROM ("
		    "SELECT localized_name, hero_id,a,b, (a-b) as seq, match_id FROM ("
			    "SELECT heroes.localized_name, heroes.id as hero_id, mpd.match_id, go.time,"
			    "row_number() over (partition by mpd.match_id order by go.time) as a,"
			    "row_number() over (partition by  heroes.id, mpd.match_id order by go.time) as b"
			    " FROM heroes"
			    " JOIN matches_players_details as mpd ON mpd.hero_id = heroes.id"
			    " JOIN game_objectives as go ON go.match_player_detail_id_1 = mpd.id  or go.match_player_detail_id_2 = mpd.id"
			    " WHERE go.subtype = 'CHAT_MESSAGE_TOWER_KILL'"
			" ORDER BY mpd.match_id, go.time"
		    ") as tbl"
	    ") as f"
	" ORDER BY count DESC, localized_name"
    ") as g"
    " GROUP BY localized_name, hero_id"
    " ORDER BY max DESC, localized_name")
    data = cursor.fetchall()
    print(data)
    result = {
        "heroes": []
    }
    for hero in data:
        result["heroes"].append({
            "id": int(hero[0]),
            "name": hero[1],
            "tower_kills": int(hero[2])
        })
    return JsonResponse(result)



