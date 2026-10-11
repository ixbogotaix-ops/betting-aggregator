import re  
import sys  
channels = ['legalbet', 'bookmaker_ratings', 'vprognoze', 'intelbet', 'stavka_tv', 'bet_itors', 'capper_control', 'odds_portal_ru', 'metaratings_ru', 'championat_com', 'football_hub_ru', 'capper_football', 'goal_forecast', 'euro_football_chat', 'russian_premier_league', 'champions_league_bets', 'tactical_board', 'corner_cards_bets', 'xG_football_analytics', 'foot_analytics_pro', 'ice_hockey_bets', 'khl_analytics_pro', 'nhl_expert_tips', 'puck_and_goal', 'tennis_expert_pro', 'court_side_bets', 'tennis_stat_lab', 'basket_analytics', 'nba_night_picks', 'volleyball_expert_bets', 'mma_ufc_predictions', 'smart_betting_lab', 'value_bets_channel', 'roi_tracker_bot', 'betting_strategy_ru', 'math_betting_club', 'pro_capper_union', 'sure_bets_monitor']  
new_list = []  
for c in channels:  
    new_list.append('    {\" "name\: \ + c + \, \url\: \https://t.me/s/ + c + \, \roi\: 10.0, \winrate\: 55.0, \total_bets\: 500}')  
list_str = 'TARGET_CHANNELS = [\n' + ',\n'.join(new_list) + '\n]\n'  
content = open('app/telegram_scraper.py', encoding='utf-8').read()  
content = re.sub(r'TARGET_CHANNELS = \[.*?\]', list_str, content, flags=re.DOTALL)  
open('app/telegram_scraper.py', 'w', encoding='utf-8').write(content)  
