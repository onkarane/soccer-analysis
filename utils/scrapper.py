"import required libraries"
import pandas as pd
import time
import sys
from datetime import datetime

class Scrapper:

    '''
    The class includes functions to scrape premire league website
    using the selenium library. On the first run the functions will download 
    all the results, on the subsequent runs only additional results will be
    downloaded.
    '''

    def check_status():
        '''
        Function checks file if files exist in the data folder.
        If the files do not exist it will return status as initial 
        indicating all the functions need to run else the status will
        be update.

        INPUT:
            1. NONE
        
        OUTPUT:
            1. initial(string): if the program is running first time
            2. update(string): if the program is running an update
        '''
        try:
            f = open('data/teams.csv')
        except IOError:
            print('The file teams.csv does not exist! Program cannot run without that file!')
            sys.exit(1)

        try:
            f = open('data/players.csv')
            f = open('data/match.csv')
            f = open('data/stats.csv')
        except IOError:
            return "initial"
        
        return "update"

    def get_date():
        '''
        Function to get last date from the match data if it exists

        INPUT:
            1. NONE
        OUTPUT:
            date(string): last match date
        '''
        #read the file
        df_match = pd.read_csv('./data/match.csv')
        #get date
        date = df_match.Date.tail(1)\
                    .values.tolist()[0]

        return date
    
    def compare_dates(d1, d2):
        '''
        Function to compare two dates
        
        INPUT:
            1. d1(string): new date of match
            2. d2(string): date from the stored data
        
        OUTPUT:
            1. date_res(string): True if new date is greater else false
        '''
        newd1 = time.strptime(d1, "%m/%d/%Y")
        newd2 = time.strptime(d2, "%m/%d/%Y")
        
        if newd2 < newd1:
            date_res = True
        else:
            date_res = False
            
        return date_res
    
    def get_match_id():
        '''
        Function to get last match id from the match data if it exists

        INPUT:
            1. NONE
        OUTPUT:
            match_id(int): last match id
        '''
        df_match = pd.read_csv('./data/match.csv')
        match_id = df_match.MatchID.tail(1)\
                    .values.tolist()[0]
        match_id = match_id
        
        return match_id
    
    def get_match_details(driver):
        '''
        Function to scrape the premier league website to get chelsea match details.
        The details include, match date, opponent, game type, and links for fetch
        further details

        INPUT:
            1. driver(web driver obj): selenium driver object to parse the website
        
        OUTPUT:
            1. dates(string list): date of the matches
            2. opponents(string list): names of the opponents
            3. game_type(string list): type of game i.e away or home
            4. links(string list): list of links to further explore match details
            5. match_id(int list): integer values to uniquely each match
        '''

        def get_match_date(d_date):
            '''
            Function to get the match date value.

            INPUT: 
                1. d_date(driver object): driver object to extract date from div
            
            OUTPUT:
                1. date(string): cleaned match date
            '''
            date = d_date.get_attribute("data-competition-matches-list")
            date = date.split()[1:]
            date = '-'.join(date)
            date = datetime.strptime(date, '%d-%B-%Y').strftime('%m/%d/%Y')

            return date

        def get_opponent_and_game_type(d_opponents):
            '''
            Function to get the names of the opponents and calculate 
            the game type whether home or away.

            INPUT: 
                1. d_opponents(driver object): driver object to extract opponent name
            
            OUTPUT:
                1. opponent(string): name of the opponent
                2. game_type(string): game type either home or away
            '''
            #get the names of away and home teams names
            away = d_opponents.find_element_by_xpath('.//*[@class="matchFixtureContainer"]')\
                                .get_attribute("data-away")
            home = d_opponents.find_element_by_xpath('.//*[@class="matchFixtureContainer"]')\
                                .get_attribute("data-home")

            #check for the name and game type
            if away == "Chelsea":
                opponents = home
                game_type = 'away'
            else:
                opponents = away
                game_type = 'home'

            return opponents, game_type

        def get_stat_links(d_link):
            '''
            Function to get links to explore further details about the match

            INPUT: 
                1. d_link(driver object): driver object to extract link
            
            OUTPUT:
                1. link(string): link for score and stats of the match
            '''
            #get the link for game details
            link = d_link.find_element_by_xpath('.//*[@class="fixture postMatch"]')\
                            .get_attribute('data-href')
            #add https and append
            link = 'https:' + link
            
            return link

        #check the run status
        status = Scrapper.check_status()

        #perfrom operations depending on status
        if status == "update":
            date = Scrapper.get_date()
        else:
            date = None
        
        #initialize the lists
        dates = []          #to store dates
        opponents = []      #to store opponent names
        game_type = []      #to store game type
        links = []          #to store links for further searches

        #parse the initial div
        parent_div = driver.find_elements_by_xpath("""//*[@class="fixtures__matches-list"]""")
        #loop through the div
        for p in parent_div:
            #perform operations according to status
            if status == "initial":
                dates.append(get_match_date(p))
                links.append(get_stat_links(p))
                oppo, typ = get_opponent_and_game_type(p)
                opponents.append(oppo)
                game_type.append(typ)

            elif status == "update":
                #get the date
                match_date = get_match_date(p)
                date = Scrapper.get_date()
                #check if the date is less than stored date
                if Scrapper.compare_dates(match_date, date):
                    dates.append(match_date)
                    links.append(get_stat_links(p))
                    oppo, typ = get_opponent_and_game_type(p)
                    opponents.append(oppo)
                    game_type.append(typ)
                else:
                    continue
        #add match id as
        if status == "update":
            mid = Scrapper.get_match_id()
            lst = list(range(1, len(dates)+1))
            match_id = [x + mid for x in lst]
        else:
            match_id = list(range(1, len(dates) + 1))
            match_id.reverse()


        return dates, opponents, game_type, links, match_id


    def process_goal_stats(event):
        '''
        Function to process the stats realted to goal such as time and player.

        INPUT:
            1.event(driver object): object to extract the goal realted info from

        OUTPUT:
            1.name(string): name of the player scoring the goal
            2.time(int list): list containing the minutes of goals
        '''
        #split the event in list
        lst = event.text.split()
        #loop through the list
        for element in lst:
            #clean the minutes value and convert to int
            if element.strip("',").isdigit():

                #manage extra time and clean it
                if (element.strip("',") == '90') and \
                    ('+' in lst[lst.index(element)+1]) and \
                        (lst[lst.index(element)+1].strip("+''").isdigit()):
                        #add full time and extra time
                        extra_time = int(element.strip("',")) + \
                                     int(lst[lst.index(element)+1].strip("+''"))
                        #replace extra time in list position
                        lst[lst.index(element)] = extra_time
                #manage and clean minutes that are within the full time
                else:
                    #replace time string with int 
                    lst[lst.index(element)] = int(element.strip("',"))
        
        #remove words such as own goal, goal, og
        #keep only name of player and time of goal
        for element in lst:
            #get the index of the last int value in the list
            if str(element).isdigit():
                idx = lst.index(element)
        #filter anything after the last int value 
        #usually positions after last int value are own goal, goal etc
        lst = lst[:idx+1]

        #initialize the name and list variable for time
        name = None
        time = []

        #loop through the filtered list
        for value in lst:
            #add to time list if value is numeric
            if str(value).isnumeric():
                time.append(value)
            #initial name or append name
            elif name == None:
                name = value
            elif '(pen)' not in value:
                name = name + ' ' + value
        
        return name, time

    def get_goal_stats(event, match_id):
        '''
        Function to get the goal stats such as possesion details and minute of goal

        INPUT:
            1.event(driver object list): list of objects to extract the goal realted info from
            2.match_id(int): integer value to uniquely identify the match
        
        OUTPUT:
            1.player(list string): list of players who scored
            2.minutes(list int): list of minutes the player scored
            3.match_id_lst(list int): list of integers to uniquely identify the match
        '''
        #initialize lists
        player = []
        goal_time = []
        match_id_lst = []

        #if there were no goals append none
        if len(event) == 0:
            player.append(None)
            goal_time.append(None)
            match_id_lst.append(match_id)
        else:
            #loop through event list
            for e in event:

                #if the event is associated to card continue
                if 'Card' in e.text.split():
                    continue
                else:
                    #if the event is associated to goal
                    #call the method to process names and times
                    name, time = Scrapper.process_goal_stats(e)
                    #loop through time list
                    for t in time:
                        player.append(name)
                        goal_time.append(t)
                        match_id_lst.append(match_id)

        return player, goal_time, match_id_lst

    
    def get_match_stats(driver, game, links, match_id):
        '''
        Function to get match stats such as match scores, possesion, shots,
        player scoring the goal etc.

        INPUT:
            1. driver(web driver obj): selenium driver object to parse the website
            2. game(string list): list of string values denoting if the game home or away
            3. links(string list): list of links to get the stats for each match
            3. match_id(int list): int list of unique values to individually identify each match

        OUTPUT:
            1. score_lst(int list): list of chelsea's scores
            2. o_score_lst(int list): list of opponents's scores
            3. player (string list): list of players who scored in the match
            4. goal_time(int list): list of gaol times for the match
            5. match_id_lst(list int): list of integers to uniquely identify match
            7. poss(float list): list of possesion for games for chelsea
            8. o_poss(float list): list of possesion for games for opponents
            9. shot(int list): list of shots on target by chelsea
            10.o_shot(int list): list of shots on target by opponents
        '''
        
        def get_goals(score, game):
            '''
            Function to get the goals of match

            INPUT:
                1. score(driver object): driver object to extract the goals from
                2. game(string): denoting if the game home or away

            OUTPUT:
                1. goal(int): goal by chelsea
                2. o_goal(int): goal score by opponent
            '''
            #parse the goal div
            goals = score[0].find_element_by_xpath('.//*[@class="score fullTime"]').text
            #assign value depending on game type
            if game == "home":
                goal = goals.split('-')[0]
                o_goal = goals.split('-')[1]
            else:
                goal = goals.split('-')[1]
                o_goal = goals.split('-')[0]

            return goal, o_goal
        
        def get_stats(table, game):
            '''
            Function to get the stats of match such as possesion, shots on target

            INPUT:
                1. table(driver object): driver object to extract the stats from
                2. game(string): denoting if the game home or away

            OUTPUT:
                1. poss(float): possesion by chelsea
                2. o_poss(float): possesion by opponent
                3. shot(int): shots on target by chelsea
                4. o_shot(int): shots on target by opponent
            '''
            #initialize lists
            stats = []
            #get table element from list
            t = table[0]

            #loop through table rows
            for row in t.find_elements_by_xpath(".//tr"):
                stats.append(row.text)
            
            #get the stats
            for s in stats:
                #split the list element
                lst = s.split()

                #get the possesion stats
                if 'Possession' in lst:
                    if game == 'home':
                        poss = float(lst[0])
                        o_poss = float(lst[-1])
                    else:
                        poss = float(lst[-1])
                        o_poss = float(lst[0])
                #get the shots on target
                if 'target' in lst:
                    if game == 'home':
                        shot = int(lst[0])
                        o_shot = int(lst[-1])
                    else:
                        shot = int(lst[-1])
                        o_shot = int(lst[0])
            
            return poss, o_poss, shot, o_shot

        def goal_stats(score, match_id):
            '''
            Function to call appropriate methods to get cleaned 
            goal related stats such as posession, player scoring, minute,
            shots on target etc.

            INPUT:
                1. score(driver object): driver object to extract the goals from
                2. match_id(int): list of integers to uniquely identify the match
            OUTPUT: 
                1. p_list, gt_list, mid_list: list of value representing 
            '''
            #initialize lists
            p_list = []
            gt_list = []
            mid_list = []

            #get the home goals
            sc = score[0].find_element_by_xpath(
                    './/*[@class="matchEvents matchEventsContainer"]/div[@class="home"]')
            #get the event div
            event = sc.find_elements_by_class_name('event')
            #call the function to get goal stats
            player, goal_time, match_id_lst = Scrapper.get_goal_stats(event, match_id)
            #extend lists
            p_list.extend(player)
            gt_list.extend(goal_time)
            mid_list.extend(match_id_lst)

            #get the away goals
            sc = score[0].find_element_by_xpath(
                    './/*[@class="matchEvents matchEventsContainer"]/div[@class="away"]')
            #get the event div
            event = sc.find_elements_by_class_name('event')
            #call the function to get goal stats
            player, goal_time, match_id_lst = Scrapper.get_goal_stats(event, match_id)
            #extend lists
            p_list.extend(player)
            gt_list.extend(goal_time)
            mid_list.extend(match_id_lst)

            return p_list, gt_list, mid_list
        
        #initialize the lists
        score_lst = []      #goals scored by chelsea
        o_score_lst = []    #goals score by opponents
        player = []         #player scoring the goal
        goal_time = []      #time at which the goal was scored
        match_id_lst = []   #ids for the match
        poss = []           #chelsea possesion
        o_poss = []         #opponent possesion
        shot = []           #shots on target by chelsea
        o_shot = []         #shots on target by opponent
        #counter for cookies
        counter = 0

        #loop through the links
        for l in range(len(links)):
            #open driver window
            driver.get(links[l])
            #wait for page to load
            time.sleep(5)
            #accept cookies the first time
            if counter == 0:
                cookies = driver.find_elements_by_xpath("""//*[@class="btn-primary cookies-notice-accept"]""")
                cookies[0].click()
                counter +=1

            #parse score div
            score = driver.find_elements_by_xpath("""//*[@class="scoreboxContainer"]""")

            #get match goals
            g, opg = get_goals(score, game[l])
            #append
            score_lst.append(g)
            o_score_lst.append(opg)
            
            elem = driver.find_elements_by_xpath("""//*[@class="timeLine timeLineContainer"]""")
            driver.execute_script("arguments[0].scrollIntoView(true);", elem[0])

            #click stats tab
            stats_tab= driver.find_element_by_css_selector("li[data-tab-index='2']")
            stats_tab.click()
            #get the stats table
            time.sleep(5)
            table = driver.find_elements_by_xpath("""//*[@class="matchCentreStatsContainer"]""")
            #call the function to parse table
            p, opp, s, ops = get_stats(table, game[l])
            #append
            poss.append(p)
            o_poss.append(opp)
            shot.append(s)
            o_shot.append(ops)

            #get goal related stats
            p_list, gt_list, mid_list = goal_stats(score, match_id[l])
            #extend
            player.extend(p_list)
            goal_time.extend(gt_list)
            match_id_lst.extend(mid_list)

        return score_lst, o_score_lst, player, goal_time, match_id_lst, poss, o_poss, shot, o_shot

    
    def get_players(driver):
        '''
        Function to get the list of name and position of players for each team

        INPUT:
            1. driver(driver object): driver object to extract the players name and position

        OUTPUT:
            1. player(string list): names of all the players for all the teams
            2. position(string list): list of position where the corresponding player plays for.
            3. team_id(list int): list of team id int values associated to each player
        '''

        def process_players(driver, team_name, team_id):
            '''
            Function to get the list of name and position of players for specified team

            INPUT:
                1. driver(driver object): driver object to extract the players name and position
                2. team_name(string): name of the team to search the players for
                3. team_id(int): id of the team
            
            OUTPUT:
                1. player(string list): names of all the players for all the teams
                2. position(string list): list of position where the corresponding player plays for.
                3. team_id(list int): list of team id int values associated to each player
            '''
            #dictionary for mapping url
            url_dict = {
                'Arsenal': '1','Aston Villa': '2','Brighton': '131','Burnley': '43',
                'Chelsea': '4','Crystal Palace': '6','Everton': '7','Fulham': '34',
                'Leeds': '9','Leicester': '26','Liverpool': '10','Man City': '11',
                'Man Utd': '12','Newcastle': '23','Sheffield Utd': '18','Southampton': '20',
                'Spurs': '21','West Brom': '36','West Ham': '25','Wolves': '38'
                }
            #construct url
            url = 'https://www.premierleague.com/players?se=363&cl=' + url_dict[team_name]

            #initialize list
            player_name = []
            player_position = []
            team = []
            
            #set the driver
            driver.get(url)
            time.sleep(8)

            #parse the table
            t = driver.find_elements_by_xpath("""//*[@class="dataContainer indexSection"]""")
            for row in t[0].find_elements_by_xpath(".//tr"):
                player = row.find_elements_by_xpath(".//td")[0]
                position = row.find_elements_by_xpath(".//td")[1]
                #append
                player_name.append(player.text)
                player_position.append(position.text)
                team.append(team_id)

            return player_name, player_position, team

        #initialize list
        player = []
        position = []
        team_id = []

        #read the teams csv
        df = pd.read_csv('./data/teams.csv')
        #make two lists for team name and team id each
        id_lst = df.TeamID.to_list()
        name_lst = df.TeamName.to_list()

        #loop through each team
        for n in range(len(id_lst)):
            #call the function to get player names and position
            player_name, player_position, team = process_players(driver, name_lst[n], id_lst[n])
            #extend
            player.extend(player_name)
            position.extend(player_position)
            team_id.extend(team)

        return player, position, team_id

    def create_match_df(
        mid, date, oppo, gtype, cscore, 
        oscore, cposs, oposs, cshot, oshot):
        '''
        Function to create match dataframe
        
        INPUT:
            1. mid(list int): list of integers to uniquely identify match
            2. date(string list): list of date of match
            3. oppo(string list): list of opponents 
            4. gtype(string list): list of game type i.e home or away
            5. cscore(int list): list of chelsea's scores
            6. oscore(int list): list of opponents's scores
            7. cposs(float list): list of possesion for games for chelsea
            8. oposs(float list): list of possesion for games for opponents
            9. cshot(int list): list of shots on target by chelsea
            10.oshot(int list): list of shots on target by opponents
        
        OUTPUT:
            df_match(pandas dataframe): dataframe with relevant cols and values for match
        '''
        #define the columns for match
        match_cols = [
            'MatchID', 'Date', 'OpponentID', 
            'GameType', 'CScore', 'OScore', 
            'CPossesion', 'OPossesion', 'CShot', 'OShot']
        #data for match
        match_tup = list(zip(
            mid, date, oppo, gtype, 
            cscore, oscore, cposs, oposs, cshot, oshot))
        
        #create dataframe
        df_match = pd.DataFrame(match_tup, columns=match_cols)
        
        return df_match

    def create_players_df(team, name, posi):
        '''
        Function to create dataframe for players details
        
        INPUT:
            1.team(int int): list of team id for the associated player 
            2.name(string list): list of names of the players of all the teams
            3.posi(string list): list of poisitions the players play at
            
        OUTPUT:
            1.df_players(pandas dataframe): dataframe with relevant cols and values
                                            for players
        '''
        #define the columns for players
        player_cols = ['PlayerID', 'TeamID', 'PlayerName', 'PlayerPosition']
        
        #data for players
        player_id = list(range(1, len(name) + 1))
        player_tup = list(zip(player_id, team, name, posi))
        
        #dataframe for players
        df_players = pd.DataFrame(player_tup, columns=player_cols)
        
        return df_players

    def create_stats_df(match, player, minutes):
        '''
        Function to create dataframe for the stats of the match
        
        INPUT:
            1. match(int list): list of match id to identify match
            2. player(string list): list of player names who scored
            3. minutes(int list): list of minutes the goals were scored
            
        OUTPUT:
            1. df_stats(pandas dataframe): dataframe with relevant cols and values
                                            for match stats
        '''
        #define the columns for stats
        stats_cols = ['MatchID', 'PlayerID', 'Minute']
        
        #data for stats
        stats_tup = list(zip(match, player, minutes))
        
        #dataframe for stats
        df_stats = pd.DataFrame(stats_tup, columns=stats_cols)
        
        return df_stats

    def save_dataframes(match, players, stats):
        '''
        Function to save the dataframes in the data folder.
        If the file already is present the data will be appended
        
        INPUT:
            1.match(pandas dataframe): dataframe with relevant cols and values 
                                            for match
            2.players(pandas dataframe): dataframe with relevant cols and values
                                            for players
            3.stats(pandas dataframe): dataframe with relevant cols and values
                                            for match stats
        
        OUTPUT:
            1.NONE
            
        '''
        
        #call the function to check status
        status = Scrapper.check_status()
        
        #check the status for players
        if status == 'update':
            df_players = pd.read_csv('data/players.csv')
        else:
            df_players = players
        #read teams file
        df_teams = pd.read_csv('data/teams.csv')
        
        #create dictionaries
        player_dict = dict(zip(df_players.PlayerName, df_players.PlayerID))
        team_dict = dict(zip(df_teams.TeamName, df_teams.TeamID))
        
        #map the values
        stats['PlayerID'].replace(player_dict, inplace= True)
        match['OpponentID'].replace(team_dict, inplace=True)
        match = match.sort_values(by="MatchID")
        stats = stats.sort_values(by="MatchID")
        
        #save the files
        if status == 'update':
            match.to_csv('./data/match.csv', index=False, header=False, mode='a')
            stats.to_csv('./data/stats.csv', index=False, header=False, mode='a')
        else:
            match.to_csv('./data/match.csv', index=False)
            stats.to_csv('./data/stats.csv', index=False)
            players.to_csv('./data/players.csv', index=False)
        
    
    def main(driver, url):
        '''
        Function to perform all the actions in the class

        INPUT:
            1. driver(selenium webdriver): driver object to scrape the website
            2. url(string): link for initial page to scrape

        OUTPUT:
            1. NONE
        '''
        #call the function to check status
        status = Scrapper.check_status()
        #set driver
        driver.get(url)
        time.sleep(8)

        print('-' * 5 + 'Getting Match Details' + '-' * 5)
        #call the function to get match data
        dates, opponents, game_type, links, match_id = Scrapper.get_match_details(driver)

        if len(dates) == 0:
            return print('No Changes Detected!')
            driver.quit()

        print('-' * 5 + 'Getting Match Stats' + '-' * 5)
        #call the function to get match stats
        score_lst, o_score_lst, player, \
        goal_time, match_id_lst, poss, \
        o_poss, shot, o_shot = Scrapper.get_match_stats(driver, game_type, links, match_id)

        #if status is initial call the function to create players
        if status == 'initial':
            print('-' * 5 + 'Getting Players For Each Team' + '-' * 5)
            player_name, player_position, team = Scrapper.get_players(driver)
            #create dataframe
            df_players = Scrapper.create_players_df(team, player_name, player_position)
        else:
            df_players = 0
        
        print('-' * 5 + 'Creating DataFrames' + '-' * 5)
        #create match dataframe
        df_match = Scrapper.create_match_df(
            match_id,dates, opponents, game_type, score_lst, 
            o_score_lst, poss, o_poss, shot, o_shot )
        #create stats dataframe
        df_stats = Scrapper.create_stats_df(match_id_lst, player, goal_time)

        print('-' * 5 + 'Saving DataFrames' + '-' * 5)
        #call function to save dataframes
        Scrapper.save_dataframes(df_match, df_players, df_stats)
        driver.quit()

        if status == "update":
            print("Match and Stats data updated successfully!")
        else:
            print("Successfully created files players.csv, match.csv, stats.csv \
                    and saved them in data folder!")
        










        
            