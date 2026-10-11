import sys  
lines = open('app/capper_scraper.py', encoding='utf-8').readlines()  
out = []  
skip = False  
for l in lines:  
    if 'def _generate_simulated_predictions' in l: skip = True  
    if 'async def process_capper_predictions' in l: skip = False  
    if not skip: out.append(l)  
open('app/capper_scraper.py', 'w', encoding='utf-8').writelines(out)  
