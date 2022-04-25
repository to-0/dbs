from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from v4.models import *
from django.db.models import Sum, F, Value, Case, When, Q, TextField, FloatField, Count, Max
from django.db.models.functions import Coalesce, Cast, Round, RowNumber
from django.db.models.expressions import Window

def index(request):
    return HttpResponse("Test")

def v4_patches(request):
    p = Patches.objects.using('dota2').all().annotate(
    )

def v4_game_exp(request, player_id):
    test = Matches.objects.using('dota2').filter(id=69)
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
    # keby tam nedam values tak to je takto ale to query by bralo aj stlpce co nepotrebujem
    # for a in mpd:
    #     if a.match.id not in processed_matches:
    #         result["matches"].append({
    #             "match_id": a.match.id,
    #             "hero_localized_name": a.hero.localized_name,
    #             "actions": [{
    #                 "hero_action": a.hero_action,
    #                 "count": a.count
    #             }]
    #         })
    #         processed_matches.append(a.match.id)
    #     else:
    #         i = processed_matches.index(a.match.id)
    #         result["matches"][i]["actions"].append({
    #             "hero_action": a.hero_action,
    #             "count": a.count
    #         })
    return JsonResponse(result)

def v4_abilities(request, player_id):
    aub = AbilityUpgrades.objects.using('dota2').all().select_related('ability')
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

#TODO
def v4_top_purchases(request, match_id):
    mpd = MatchesPlayersDetails.objects.using('dota2').filter(match__id=match_id).select_related('match', 'hero')
    return HttpResponse("Yo")

def v4_tower_kills(request):
    mpd = MatchesPlayersDetails.objects.using('dota2').all().select_related('match', 'hero').prefetch_related(
        'match_player_detail_id_1').annotate(
        a=Window(expression=RowNumber(), partition_by=[F('match__id')], order_by=F('match_player_detail_id_1__time'))
    )
    print(mpd[0].a)
    return HttpResponse("Yo")

