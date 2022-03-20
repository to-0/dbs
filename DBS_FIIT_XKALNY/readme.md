# DBS SERVER

https://fiit-dbs-xkalny-app.azurewebsites.net

## Query k zadaniu 3

### 1. endpoint

    SELECT x.name as patch_version, x.patch_start_date, x.patch_end_date, matches.id as match_id
    ,ROUND(matches.duration*1.0/60,2) as duration FROM matches
    RIGHT JOIN (
        SELECT patches.name, EXTRACT(epoch from patches.release_date) as patch_start_date
        ,EXTRACT(epoch from (lead(patches.release_date) over (ORDER BY patches.release_date)))
        as patch_end_date FROM patches as patches) as x
    ON matches.start_time BETWEEN x.patch_start_date and x.patch_end_date
    ORDER BY x.name

### 2. endpoint

    SELECT players.id, COALESCE(players.nick,'unknown'), heroes.localized_name, ROUND(matches.duration*1.0/60,2),
    SUM(COALESCE(mpd.xp_hero,0)+COALESCE(mpd.xp_creep,0)+COALESCE(mpd.xp_other,0)+COALESCE(mpd.xp_roshan,0))
    AS experiences_gained, mpd.level as level_gained, matches.id as match_id,
    CASE matches.radiant_win
    WHEN true and mpd.player_slot >=0 and mpd.player_slot <= 4 then true
    WHEN true and mpd.player_slot > 4 then false
    WHEN false and mpd.player_slot <= 4 then false
    WHEN false  and mpd.player_slot > 4 then true END as winner
    FROM players JOIN matches_players_details as mpd ON players.id = mpd.player_id
    JOIN matches on mpd.match_id = matches.id JOIN heroes ON mpd.hero_id = heroes.id
    WHERE players.id = {id_hraca}
    GROUP BY players.id, players.nick, heroes.localized_name, matches.duration, mpd.level,
    matches.radiant_win, matches.id, mpd.player_slot ORDER BY match_id

### 3. endpoint

    SELECT players.id as player_id, COALESCE(players.nick,'unknown') as player_nick,
    heroes.localized_name, matches.id as match_id, COALESCE(gob.subtype,'NO_ACTION') as hero_action,
    count(COALESCE(gob.subtype,'NO_ACTION')) FROM players
    JOIN matches_players_details as mpd ON mpd.player_id = players.id
    JOIN matches ON mpd.match_id = matches.id
    JOIN heroes ON mpd.hero_id = heroes.id
    FULL JOIN game_objectives as gob ON
    gob.match_player_detail_id_1 = mpd.id
    WHERE players.id = {id_hraca}
    GROUP BY  players.id, heroes.localized_name, matches.id, gob.subtype
    ORDER BY matches.id

### 4. endpoint

    SELECT players.id as player_id, COALESCE(players.nick,'unknown') as player_nick,
    heroes.localized_name, matches.id as match_id, abilities.name as ability_name,
    count(abilities.name), max(au.level) as upgrade_level FROM players
    JOIN matches_players_details as mpd ON mpd.player_id = players.id
    JOIN matches ON mpd.match_id = matches.id
    JOIN heroes ON mpd.hero_id = heroes.id
    JOIN ability_upgrades as au ON au.match_player_detail_id = mpd.id
    JOIN abilities ON au.ability_id = abilities.id
    WHERE players.id = {id_hraca}
    GROUP BY  matches.id, players.id, heroes.localized_name,abilities.name
    ORDER BY matches.id, abilities.name
