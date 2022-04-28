import math
from datetime import datetime

from django.shortcuts import render

# Create your views here.
from django_cte import CTEManager, With, CTEQuerySet
from django.http import HttpResponse, JsonResponse
from v4.models import *
from django.db.models import Sum, F, Value, Case, When, Q, TextField, FloatField, Count, Max, Subquery, OuterRef, \
    IntegerField, CharField
from django.db.models.functions import Coalesce, Cast, Round, RowNumber, Extract, Lead, Floor, Rank
from django.db.models.expressions import Window
import time

def index(request):
    return HttpResponse("Test")

#TODO ja nvm ako inak to spravit lebo tabulka patches nijako nesuvisi s tabulkou matches a spravit si patches a potom pre kazdy volat a hladat matche je hrozne pomale
def v4_patches(request):
    matches = Matches.objects.using('dota2').raw("SELECT 1 as id, patch_version, x.patch_start_date, x.patch_end_date, matches.id as match_id,"
                                                 " ROUND(matches.duration*1.0/60,2) as duration FROM matches RIGHT JOIN "
                                                    "(SELECT patches.name as patch_version, EXTRACT(epoch from patches.release_date) as patch_start_date"
                                                    ",EXTRACT(epoch from (lead(patches.release_date) over (ORDER BY patches.release_date)))"
                                                    "as patch_end_date FROM patches as patches) as x"
                                                    " ON matches.start_time BETWEEN x.patch_start_date and x.patch_end_date"
                                                    " ORDER BY patch_version")
    print(list(matches))
    processed_patches = []
    result = {
        "patches": []
    }
    for ma in matches:
        if ma.patch_version not in processed_patches:
            result["patches"].append({
                "patch_version": ma.patch_version,
                "patch_start_date": int(ma.patch_start_date),
                "patch_end_date": int(ma.patch_end_date),
                "matches": [
                    {
                        "match_id": ma.id,
                        "duration": ma.duration
                    }
                ]
            })
            processed_patches.append(ma.patch_version)
        else:
            i = processed_patches.index(ma.patch_version)
            result["patches"][i]["matches"].append({
                "match_id": ma.id,
                "duration": ma.duration
            })
    # p = Patches.objects.using('dota2').all().annotate(
    #     patch_end_date=Window(
    #         expression=Lead('release_date'),
    #         order_by=F('release_date').asc()
    #     )
    # ).values("patch_end_date", "release_date", "name")
    # for vals in p:
    #     # ten posledny je none neviem ako inak to osetrit
    #     if vals["patch_end_date"] is None:
    #         vals["patch_end_date"] = datetime.now()
    #     t = {
    #         "patch_version": vals["name"],
    #         "patch_start_date": round(vals["release_date"].timestamp()),
    #         "patch_end_date": round(vals["patch_end_date"].timestamp()),
    #         "matches": []
    #     }
    #     matches = Matches.objects.using('dota2').filter(start_time__gte=vals["release_date"].timestamp()).filter(start_time__lte=vals["patch_end_date"].timestamp()).annotate(
    #         m_duration=Round(Cast(F('duration'), output_field=FloatField())/60, 2)
    #     ).values("id", "m_duration")
    #     for match in matches:
    #         t["matches"].append({
    #             "match_id": match["id"],
    #             "duration": match["m_duration"]
    #         })
    #     result["patches"].append(t)
    return JsonResponse(result)

def v4_game_exp(request, player_id):
    # player = Players.objects.get(id=14944).select_related('')
    mpd = MatchesPlayersDetails.objects.using('dota2')\
        .filter(player=player_id).select_related('hero', 'player', 'match').\
        annotate(experiences_gained=Coalesce(F('xp_hero'), Value(0))+ Coalesce(F('xp_creep'), Value(0))+
                                    Coalesce(F('xp_other'), Value(0)) + Coalesce(F('xp_roshan'), Value(0)),
                 winner=Case(
                    When(Q(match__radiant_win=True) & Q(player_slot__gte=0) & Q(player_slot__lte=4), then=Value(True)),
                    When(Q(match__radiant_win=True) & Q(player_slot__gt=4), then=Value(False)),
                    When(Q(match__radiant_win=False) & Q(player_slot__lte=4), then=Value(False)),
                    When(Q(match__radiant_win=False) & Q(player_slot__gt=4), then=Value(True))
                ),
                nick=Coalesce('player__nick', Cast(Value('unknown'), output_field=TextField())),
                duration=Round(Cast(F('match__duration'), output_field=FloatField())/60, 2)).order_by('match__id')
    print(mpd[0].player_slot)
    for a in mpd:
        print(a.match.radiant_win, a.player_slot, a.winner)
    print(mpd[0].winner)
    print(mpd[0].experiences_gained)
    print(mpd[0].hero.localized_name)
    result = {
        "id": 14944,
        "player_nick": mpd[0].nick,
        "matches": []
    }
    for match in mpd:
        result["matches"].append({
            "match_id": match.match.id,
            "hero_localized_name": match.hero.localized_name,
            "match_duration_minutes": match.duration,
            "experiences_gained": match.experiences_gained,
            "level_gained": match.level,
            "winner": match.winner
        })
    return JsonResponse(result)

def v4_game_objectives(request, player_id):
    mpd = MatchesPlayersDetails.objects.using('dota2').filter(player=player_id).select_related('match', 'hero').prefetch_related('match_player_detail_id_1').annotate(
        nick=Coalesce('player__nick', Cast(Value('unknown'), output_field=TextField())),
        hero_action=Coalesce("match_player_detail_id_1__subtype", Cast(Value('NO_ACTION'), output_field=TextField())),
        count=Count(Coalesce("match_player_detail_id_1__subtype", Cast(Value('NO_ACTION'), output_field=TextField())))
    ).values(
        "player__id", "hero__localized_name",
        "match__id",
        "hero_action", "count", "nick"
    )
    print(mpd)
    result = {
        "id": 14944,
        "player_nick": mpd[0]["nick"],
        "matches": []
    }
    processed_matches = []
    for a in mpd:
        if a["match__id"] not in processed_matches:
            result["matches"].append({
                "match_id": a["match__id"],
                "hero_localized_name": a["hero__localized_name"],
                "actions": [{
                    "hero_action": a["hero_action"],
                    "count": a["count"]
                }]
            })
            processed_matches.append(a["match__id"])
        else:
            i = processed_matches.index(a["match__id"])
            result["matches"][i]["actions"].append({
                "hero_action": a["hero_action"],
                "count": a["count"]
            })
    return JsonResponse(result)

def v4_abilities(request, player_id):
    mpd = MatchesPlayersDetails.objects.using('dota2').filter(player=player_id).select_related('match', 'hero').prefetch_related('au').annotate(
        test=F('au__time'),
        nick=Coalesce('player__nick', Cast(Value('unknown'), output_field=TextField())),
        count=Count('au__ability__name'),
        upgrade_level=Max('au__level'),
        ability_name=F('au__ability__name')
    ).order_by('match__id', 'au__ability__name').values("hero__localized_name", "match__id", "ability_name", "upgrade_level", "count", "nick")
    result={
        "id": player_id,
        "player_nick": mpd[0]["nick"],
        "matches": []
    }
    print(mpd)
    processed_matches = []
    for a in mpd:
        if a["match__id"] not in processed_matches:
            result["matches"].append({
                "match_id": a["match__id"],
                "hero_localized_name": a["hero__localized_name"],
                "abilities": [{
                    "ability_name": a["ability_name"],
                    "count": a["count"],
                    "upgrade_level": a["upgrade_level"]
                }]
            })
            processed_matches.append(a["match__id"])
        else:
            i = processed_matches.index(a["match__id"])
            result["matches"][i]["abilities"].append({
                "ability_name": a["ability_name"],
                "count": a["count"],
                "upgrade_level": a["upgrade_level"]
            })
    return JsonResponse(result)

def v4_top_purchases(request, match_id):
    pl = PurchaseLogs.objects.using('dota2').filter(Q(match_player_detail_id__match__id=match_id) & ((Q(match_player_detail_id__player_slot__range=[0, 4]) &
                                                                                        Q(match_player_detail_id__match__radiant_win=True)) |
                                                                                       (Q(match_player_detail_id__player_slot__range=[128,
                                                                                                              132]) & Q(
                                                                                           match_player_detail_id__match__radiant_win=False)))).select_related(
        'match_player_detail').values('match_player_detail_id__hero__id', 'match_player_detail_id__hero__localized_name',
            'item__name', 'item__id', 'match_player_detail').annotate(
        purchases_count=Count('item__name'),
        row_number=Window(
            expression=RowNumber(),
            partition_by=[F('match_player_detail__id')],
            order_by=(Count('item__name').desc(), 'item__name')
        ),
    ).order_by('match_player_detail_id__hero__id', '-purchases_count').values('match_player_detail_id__hero__id', 'match_player_detail_id__hero__localized_name',
            'item__name', 'item__id', 'match_player_detail', 'row_number', 'purchases_count')

    filtered_purchases = PurchaseLogs.objects.using('dota2').raw("SELECT 1 as id,* FROM ({}) as f WHERE row_number<=5 ORDER BY f.hero_id, f.row_number".format(pl.query))
    print(list(filtered_purchases))
    print(filtered_purchases)
    print(pl.query)
    result = {
        "id": match_id,
        "heroes": []
    }
    processed_heroes = []
    for p in filtered_purchases:
        if p.match_player_detail.hero.id not in processed_heroes:
            result["heroes"].append({
                "id": p.match_player_detail.hero.id,
                "name": p.match_player_detail.hero.localized_name,
                "top_purchases": [{
                    "id": p.item.id,
                    "name": p.item.name,
                    "count": p.purchases_count
                }]
            })
            processed_heroes.append(p.match_player_detail.hero.id)
        else:
            i = processed_heroes.index(p.match_player_detail.hero.id)
            result["heroes"][i]["top_purchases"].append({
                "id": p.item.id,
                "name": p.item.name,
                "count": p.purchases_count
            })
    return JsonResponse(result)

#TODO asi hotovo len vymazat zbytocne veci
def v4_abilities_usage(request, ability_id):
    a = Abilities.objects.using('dota2').filter(id=ability_id).prefetch_related('au_f_a').annotate(
        winner=Case(
            When(Q(au_f_a__match_player_detail_id__match__radiant_win=True) & Q(au_f_a__match_player_detail_id__player_slot__range=[0, 4]), then=Value('winner')),
            When(Q(au_f_a__match_player_detail_id__match__radiant_win=False) & Q(au_f_a__match_player_detail_id__player_slot__range=[128, 132]), then=Value('winner')),
            default=Value('loser')
        ),
        test=Floor(F('au_f_a__time')*1.0*100/F('au_f_a__match_player_detail_id__match__duration'))).values('id', 'au_f_a__match_player_detail__hero__id', 'au_f_a__match_player_detail__hero__localized_name', 'name', 'winner', 'test').annotate(
        bucket=Case(
            When(test__range=[0, 9], then=Value('0-9')),
            When(test__range=[10, 19], then=Value('10-19')),
            When(test__range=[20, 29], then=Value('20-29')),
            When(test__range=[30, 39], then=Value('30-39')),
            When(test__range=[40, 49], then=Value('40-49')),
            When(test__range=[50, 59], then=Value('50-59')),
            When(test__range=[60, 69], then=Value('60-69')),
            When(test__range=[70, 79], then=Value('70-79')),
            When(test__range=[80, 89], then=Value('80-89')),
            When(test__range=[90, 99], then=Value('90-99')),
            When(test__gte=100, then=Value('100-109'))
        )
    )
    test = Abilities.objects.using('dota2').filter(id=ability_id).prefetch_related('au_f_a').annotate(
        winner=Case(
            When(Q(au_f_a__match_player_detail_id__match__radiant_win=True) & Q(au_f_a__match_player_detail_id__player_slot__range=[0, 4]), then=Value('winner')),
            When(Q(au_f_a__match_player_detail_id__match__radiant_win=False) & Q(au_f_a__match_player_detail_id__player_slot__range=[128, 132]), then=Value('winner')),
            default=Value('loser')
        ),
        test=Floor(F('au_f_a__time')*1.0*100/F('au_f_a__match_player_detail_id__match__duration'))).values('id', 'au_f_a__match_player_detail__hero__id', 'au_f_a__match_player_detail__hero__localized_name', 'name', 'winner', 'test').annotate(
        bucket=Case(
            When(test__range=[0, 9], then=Value('0-9')),
            When(test__range=[10, 19], then=Value('10-19')),
            When(test__range=[20, 29], then=Value('20-29')),
            When(test__range=[30, 39], then=Value('30-39')),
            When(test__range=[40, 49], then=Value('40-49')),
            When(test__range=[50, 59], then=Value('50-59')),
            When(test__range=[60, 69], then=Value('60-69')),
            When(test__range=[70, 79], then=Value('70-79')),
            When(test__range=[80, 89], then=Value('80-89')),
            When(test__range=[90, 99], then=Value('90-99')),
            When(test__gte=100, then=Value('100-109'))
        )
    ).values('id', 'au_f_a__match_player_detail__hero__id', 'au_f_a__match_player_detail__hero__localized_name', 'name', 'winner', 'bucket').annotate(count=Count(F('bucket'))).annotate(
        rank=Window(
        expression=Rank(),
        partition_by=[F('winner'), F('au_f_a__match_player_detail__hero__localized_name'), F('name')],
        order_by=Count(F('bucket')).desc()
    ))

    print("test", test)
    query, params = a.query.sql_with_params()
    query2, params2 = test.query.sql_with_params()
    final2 = Abilities.objects.using('dota2').raw("SELECT id,localized_name, name, winner, bucket, hero_id, count FROM("
                                                  "{}) as table3 WHERE rank=1 ORDER BY hero_id, winner DESC".format(query2), [*params2])
    print(list(final2))
    for a2 in final2:
        print(a2.localized_name)
    # final = Abilities.objects.using('dota2').raw("SELECT id,localized_name, name, winner, bucket, hero_id, count FROM ("
    #                 "SELECT *, rank() over (partition by winner,localized_name, name ORDER BY count DESC) FROM ( "
    #                 "SELECT id, tbl.winner, tbl.localized_name, tbl.name, tbl.bucket, tbl.hero_id, COUNT(tbl.bucket) as count"
    #                         " FROM ({}) as tbl"
    #                                     " GROUP BY id, tbl.winner, tbl.localized_name, tbl.name, tbl.bucket, tbl.hero_id "
    #                                     "ORDER BY count DESC) as table2) as table3 "
    #                                     "WHERE rank=1 ORDER BY hero_id, winner DESC".format(query), [*params])
    # print(list(final))
    # print(final)
    result = {
        "id": ability_id,
        "name": final2[0].name,
        "heroes": []
    }
    processed_heroes = []
    i = 0
    while i < len(list(final2)):
        print("vonku", final2[i].localized_name)
        row = final2[i]
        if row.hero_id not in processed_heroes:
            processed_heroes.append(row.hero_id)
        else:
            i+=1
            continue
        hero = {
            "id": row.hero_id,
            "name": row.localized_name
        }
        if row.winner == 'winner':
            hero["usage_winners"] = {
                "bucket": row.bucket,
                "count": int(row.count)
            }
        else:
            hero["usage_losers"] = {
                "bucket": row.bucket,
                "count": int(row.count)
            }
        j = i + 1
        while j < len(list(final2)) and final2[j].hero_id in processed_heroes:
            print("vnutri", final2[j].localized_name)
            new_row = final2[j]
            if new_row.winner == 'winner':
                hero["usage_winners"]={
                    "bucket": new_row.bucket,
                    "count": int(new_row.count)
                }
            else:
                hero["usage_loosers"] = {
                    "bucket": new_row.bucket,
                    "count": int(new_row.count)
                }
            j += 1
        result["heroes"].append(hero)
        i += 1
    return JsonResponse(result)


def v4_tower_kills(request):
    # uz viac nakombinovat to fakt neslo
    mpd2 = MatchesPlayersDetails.objects.using('dota2').filter(
        match_player_detail_id_1__subtype='CHAT_MESSAGE_TOWER_KILL').select_related('match', 'hero').prefetch_related(
        'match_player_detail_id_1').annotate(
        a=Window(
            expression=RowNumber(),
            partition_by=['match__id'],
            order_by=[F('match_player_detail_id_1__time')]),
        b=Window(
            expression=RowNumber(),
            partition_by=['hero__id', 'match__id'],
            order_by=[F('match_player_detail_id_1__time')])
    ).order_by('match__id', 'match_player_detail_id_1__time').values('hero__localized_name', 'hero__id', 'match__id',
                                                                     'match_player_detail_id_1__time', 'a', 'b').annotate(
        seq=F('a')-F('b')
    ).values('hero__localized_name', 'hero__id', 'match__id', 'seq', 'match_player_detail_id_1__time')
    query2, params2 = mpd2.query.sql_with_params()
    m3 = MatchesPlayersDetails.objects.using('dota2').raw("SELECT 1 as id, hero_id, localized_name, MAX(count) as max FROM ("
                                                          "SELECT localized_name, hero_id, count(tbl.localized_name) over (partition by match_id, hero_id, seq)"
                                                          " FROM ({}) as tbl"
                                                          ") as g GROUP BY localized_name, hero_id ORDER BY max DESC, localized_name"
                                                          .format(query2), [*params2])
    print(m3)
    print(list(m3))
    result = {
        "heroes": []
    }
    for m in m3:
        result["heroes"].append({
            "id": m.hero.id,
            "name": m.hero.localized_name,
            "tower_kills": m.max
        })
    return JsonResponse(result)

