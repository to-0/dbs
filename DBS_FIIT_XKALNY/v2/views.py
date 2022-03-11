from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from DBS_FIIT_XKALNY.connection import *
# Create your views here.
def patches(request):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute("SELECT x.name as patch_version, x.patch_start_date, x.patch_end_date, matches.id as match_id"
                   ", ROUND(matches.duration*1.0/60,2) as duration FROM matches "
                   "JOIN (SELECT patches.name, EXTRACT(epoch from patches.release_date) as patch_start_date"
                   ",COALESCE(EXTRACT(epoch from (lead(patches.release_date) over (ORDER BY patches.release_date))),"
                   "EXTRACT(epoch from CURRENT_DATE)) as patch_end_date FROM patches as patches) as x "
                   "ON matches.start_time BETWEEN x.patch_start_date and x.patch_end_date"
                   " ORDER BY x.name")
    data = cursor.fetchall()
    print(data[0])
    print(len(data))
    # return [a + [b[1]] for (a, b) in zip(lst1, lst2)]
    #test = [a + [b[1], b[2]] for (a, b) in zip(data[0], data[1])]]
    result = {"patches": []}
    procc_patches= []
    length = len(data)
    i = 0
    while i < length:
        row = data[i]
        patch_name = data[i][0]
        # najdem prvy nespracovany patch, teda vsetky zapasy z predosleho patchu uz skoncili
        if patch_name not in procc_patches:
            prev_patch_name = patch_name
            procc_patches.append(patch_name)
            matches = list()
            # zaznamenam prvy match
            matches.append({"match_id": row[3], "duration": float(row[4])})
            i += 1
            if i <length:
                patch_name = data[i][0]
            # prechadzam dalsie riadky pokial nenajdem novy patch
            while patch_name in procc_patches and i < length:
                next_row = data[i]
                matches.append({"match_id": next_row[3], "duration": float(next_row[4])})
                i += 1
                if i < length:
                    patch_name = data[i][0]
            # vsetky informacie o patchi a matchov v nom si ulozim a pokracujem dalej
            result["patches"].append({
                "patch_version": prev_patch_name,
                "patch_start_date": row[1],
                "patch_end_date": row[2],
                "matches": matches
            })

    print(result)
    #return HttpResponse(data)
    return JsonResponse(result)

def game_exp(request, player_id):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute("SELECT players.id, COALESCE(players.nick,'unknown'), heroes.localized_name, ROUND(matches.duration*1.0/60,20),"
                   "SUM(COALESCE(mpd.xp_hero,0)+COALESCE(mpd.xp_creep,0)+COALESCE(mpd.xp_other,0)+COALESCE(mpd.xp_roshan,0)) "
                   "AS experiences_gained, mpd.level as level_gained, matches.id as match_id, "
                   "CASE matches.radiant_win "
                   "WHEN true and mpd.player_slot >=0 and mpd.player_slot <= 4 then true "
                   "WHEN true and mpd.player_slot > 4 then false "
                   "WHEN false and mpd.player_slot <= 4 then false "
                   "WHEN false  and mpd.player_slot > 4 then true END as winner "
                   "FROM players JOIN matches_players_details as mpd ON players.id = mpd.player_id "
                   "JOIN matches on mpd.match_id = matches.id JOIN heroes ON mpd.hero_id = heroes.id "
                   "WHERE players.id = {} "
                   "GROUP BY players.id, players.nick, heroes.localized_name, matches.duration, mpd.level, "
                   "matches.radiant_win, matches.id, mpd.player_slot ORDER BY match_id".format(player_id))
    data = cursor.fetchall()
    print(data)
    result = {
        "id": player_id,
        "player_nick": data[0][1]
    }
    matches = list()
    for row in data:
        matches.append({
            "match_id": row[6],
            "hero_localized_name": row[2],
            "match_duration_minutes": row[3],
            "experiences_gained": row[4],
            "level_gained": row[5],
            "winner": row[7]
        })
    result["matches"] = matches
    return JsonResponse(result)


def game_objectives(request, player_id):
    if request.method != 'GET':
        return HttpResponse("Wrong method")
    cursor = conn.cursor()
    cursor.execute("SELECT players.id as player_id, COALESCE(players.nick,'unknown') as player_nick, "
                   "heroes.localized_name, matches.id as match_id, gob.subtype as hero_action, "
                   "count(gob.subtype) FROM players "
                   "JOIN matches_players_details as mpd ON mpd.player_id = players.id "
                   "JOIN matches ON mpd.match_id = matches.id "
                   "JOIN heroes ON mpd.hero_id = heroes.id "
                   "JOIN game_objectives as gob ON "
                   "gob.match_player_detail_id_1 = mpd.id OR "
                   "gob.match_player_detail_id_2 = mpd.id "
                   "WHERE players.id = {} "
                   "GROUP BY  players.id, heroes.localized_name, matches.id, gob.subtype "
                   "ORDER BY matches.id ".format(player_id))
    data = cursor.fetchall()

    length = len(data)
    i = 0
    processed_matches = list()
    response = {
        "id": player_id,
        "player_nick": data[0][1],
        "matches": []
    }
    while i < length:
        row = data[i]
        match_id = row[3]
        matches = list()
        if match_id not in processed_matches:
            processed_matches.append(match_id)
            match = {
                "match_id": match_id,
                "hero_localized_name": row[2]
            }
            actions = list()
            actions.append({
                "hero_action": row[4],
                "count": row[5]
            })
            i += 1
            # po rade prejdem vsetky akcie v ramci jedneho matchu
            while i < length and data[i][3] in processed_matches:
                new_row = data[i]
                actions.append({
                    "hero_action": new_row[4],
                    "count": new_row[5]
                })
                i+=1
            # uz mam vsetky akcie v ramci jedneho zapasu
            response["matches"].append({
                "match_id": match_id,
                "hero_localized_name": row[2],
                "actions": actions
            })
    return JsonResponse(response)

