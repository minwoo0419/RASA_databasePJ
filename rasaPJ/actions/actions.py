from typing import Text, List, Any, Dict
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import re
import pymysql
import decimal
import random
from datetime import datetime, timedelta
name, weight, height, bmi = None, None, None, 0
db_config = {
    'host':'127.0.0.1',
    'user':'root',
    'password':'079381',
    'database':'chatbot'
}
class ActionName(Action):
    def name(self):
        return 'action_name'
    
    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        if name is None:
            dispatcher.utter_message(f"Hello! Please Tell me your name.")
        else:
            if height is not None or weight is not None:
                dispatcher.utter_message(f"Hi {name}! Your BMI is {bmi}. What kind of help do you need?")
            else:
                dispatcher.utter_message(f"Hello {name}! You are a new member of this service! Can you tell me your height, and weight?")
        return []
                
                
class ActionGreet(Action):
    def name(self):
        return 'action_greet'
    
    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        name = next(tracker.get_latest_entity_values("name"), None)
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                sql = f"SELECT * FROM `User` WHERE `name` = '{name}'"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    height_index = [i[0] for i in cursor.description].index('height')
                    weight_index = [i[0] for i in cursor.description].index('weight')
                    height = result[height_index]
                    weight = result[weight_index]
                    if height is not None and weight is not None:
                        bmi = weight / (height / 100) ** 2
                        bmi = bmi.quantize(decimal.Decimal('0.00'))
                        dispatcher.utter_message(f"Hi {name}! Your BMI is {bmi}. What kind of help do you need?")
                        return [
                            SlotSet("name", name),
                            SlotSet("height", height),
                            SlotSet("weight", weight)
                        ]
                    else:
                        dispatcher.utter_message(f"Hello {name}! You are a new member of this service! Can you tell me your height, and weight?")
                        return [SlotSet("name", name)]
                else:
                    # 사용자 정보가 없는 경우
                    insert_sql = f"INSERT INTO `User` (`name`) VALUES ('{name}')"
                    dispatcher.utter_message(f"Hello {name}! You are a new member of this service! Can you tell me your height, and weight?")
                    cursor.execute(insert_sql)
                    connection.commit()
                    return [SlotSet("name", name)]
        finally:
            connection.close()

class ActionInfo(Action):
    def name(self):
        return 'action_info'
    def preprocess_measurement(self, measurement_str):
        # measurement_str이 문자열 또는 바이트류 객체인지 확인
        if not isinstance(measurement_str, (str, bytes)):
            return None
        match = re.search(r'\d+(\.\d+)?', measurement_str)
        if match:
            return decimal.Decimal(match.group())
        return None

    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        t_height = next(tracker.get_latest_entity_values("height"), None)
        t_weight = next(tracker.get_latest_entity_values("weight"), None)
        print(t_height, t_weight)
        if t_height is None or t_weight is None:
            dispatcher.utter_message("Try again.")
            return []
        height = self.preprocess_measurement(t_height)
        weight = self.preprocess_measurement(t_weight)
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                if height is not None and weight is not None:
                    update_sql = f"UPDATE `User` SET `height` = {height}, `weight` = {weight} WHERE `name` = '{name}'"
                    cursor.execute(update_sql)
                    connection.commit()
                else:
                    sql = f"SELECT * FROM `User` WHERE `name` = '{name}'"
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    if result:
                        height_index = [i[0] for i in cursor.description].index('height')
                        weight_index = [i[0] for i in cursor.description].index('weight')
                        temp_height = result[height_index]
                        temp_weight = result[weight_index]
                        height = temp_height
                        weight = temp_weight
                bmi = weight / (height / 100) ** 2
                bmi = bmi.quantize(decimal.Decimal('0.00'))
                dispatcher.utter_message(f"Hi {name}! Your BMI is {bmi}. What kind of help do you need?")
                return [
                    SlotSet("height", height),
                    SlotSet("weight", weight)
                ]
        finally:
            connection.close()
class ActionUpdateInfo(Action):
    def name(self):
        return 'action_update_height_weight'
    def preprocess_measurement(self, measurement_str):
        # measurement_str이 문자열 또는 바이트류 객체인지 확인
        if not isinstance(measurement_str, (str, bytes)):
            return None
        match = re.search(r'\d+(\.\d+)?', measurement_str)
        if match:
            return decimal.Decimal(match.group())
        return None
    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        t_height = next(tracker.get_latest_entity_values("height"), None)
        t_weight = next(tracker.get_latest_entity_values("weight"), None)
        print(t_height, t_weight)
        if t_height is None or t_weight is None:
            dispatcher.utter_message("Try again.")
            return []
        height = self.preprocess_measurement(t_height)
        weight = self.preprocess_measurement(t_weight)
        connection = pymysql.connect(**db_config)
        try:
            dispatcher.utter_message(f"Okay {name}. I'll update your height, weight.")
            with connection.cursor() as cursor:
                # 데이터베이스에서 사용자 정보 가져오기
                update_sql = f"UPDATE `User` SET `height` = {height}, `weight` = {weight} WHERE `name` = '{name}'"
                cursor.execute(update_sql)
                connection.commit()
                bmi = weight / (height / 100) ** 2
                bmi = bmi.quantize(decimal.Decimal('0.00'))
                dispatcher.utter_message(f"Your height({height}cm) and weight({weight}kg) are updated! Now your bmi is {bmi}.")
                return []
        finally:
            connection.close()
        

class ActionRoutine(Action):
    def name(self):
        return 'action_recommand_routine'
    def run(self, dispatcher, tracker, domain):
        global name, bmi
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # 데이터베이스에서 사용자 정보 가져오기
                today_date = datetime.today().date()
                sql = f"SELECT * FROM `routine` WHERE `User_name` = '{name}' ORDER BY `date` DESC LIMIT 1"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    type_index = [i[0] for i in cursor.description].index('routinetype')
                    date_index= [i[0] for i in cursor.description].index('date')
                    temp_type = result[type_index]
                    temp_date = result[date_index]
                    dispatcher.utter_message(f"You most recently did a {temp_type} routine at {temp_date}")
                    temp_date = temp_date + timedelta(days=1)
                    print(temp_date, today_date)
                    if temp_date < today_date:
                        temp_date = today_date
                    if temp_type == 'Chest':
                        new_id = self.insert_routine(cursor, 'Back', temp_date)
                        self.find_exercise(cursor, 'Back', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Triceps', new_id, dispatcher)
                    elif temp_type == 'Back':
                        new_id = self.insert_routine(cursor, 'Legs', temp_date)
                        self.find_exercise(cursor, 'Legs', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Shoulders', new_id, dispatcher)
                    elif temp_type == 'Legs':
                        new_id = self.insert_routine(cursor, 'Chest', temp_date)
                        self.find_exercise(cursor, 'Chest', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Biceps', new_id, dispatcher)
                else:
                    dispatcher.utter_message(f"You don't have any workout routine. I'll recommand first at {today_date}.")
                    new_id = self.insert_routine(cursor, 'Chest', today_date)
                    self.find_exercise(cursor, 'Chest', new_id, dispatcher, today_date)
                    self.find_exercise_small(cursor, 'Biceps', new_id, dispatcher)
                connection.commit()
                self.find_exercise_cardio(cursor, dispatcher)
        finally:
            connection.close()
        return []
    def find_exercise(self, cursor, routinetype, new_id, dispatcher, date):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            exercises = [row[0] for row in result_exercise]
            dispatcher.utter_message(f"First, I'll recommand {routinetype}'s routine at {date}")
            for exercise_name in exercises:
                num_sets = random.randint(3, 5)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                elif num_sets == 5:
                    repetitions = 8
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_small(self, cursor, routinetype, new_id, dispatcher):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            dispatcher.utter_message(f"Second, I'll recommand {routinetype}'s routine")
            exercises = [row[0] for row in result_exercise]
            for exercise_name in exercises:
                num_sets = random.randint(3, 4)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_cardio(self, cursor, dispatcher):
        sql_exercise = "SELECT `name` FROM `exercise` WHERE `type` = 'Cardio' ORDER BY RAND() LIMIT 1"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchone()
        if result_exercise:
            exercise_name = result_exercise[0]
            if bmi > 25:
                dispatcher.utter_message(f"Since you are overweight, I recommend doing a lot of cardio. Here is My recommand cardio exercise")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 30 minutes.")
            elif bmi > 18.5:
                dispatcher.utter_message("Your BMI is normal. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 20 minutes.")
            else:
                dispatcher.utter_message("Your BMI is below normal. Adding cardio to your routine can be beneficial. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 15 minutes.")
    def insert_routine(self, cursor, type, date):
        insert_sql = f"INSERT INTO `routine` (`routinetype`,`User_name`, `date`) VALUES ('{type}', '{name}', '{date}')"
        cursor.execute(insert_sql)
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]

class ShowRoutineAction(Action):
    def name(self):
        return 'action_show_routines'
    def run(self, dispatcher, tracker, domain):
        global name
        print(name)
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                sql_routines = f"SELECT * FROM `routine` WHERE `User_name` = '{name}' ORDER BY `date` DESC"
                cursor.execute(sql_routines)
                recent_routines = cursor.fetchall()
                if recent_routines:
                    dispatcher.utter_message("Okay. Let me show your routines.")
                    for routine in recent_routines:
                        routine_id = routine[0]
                        routinetype = routine[1]
                        date = routine[2]
                        dispatcher.utter_message(f"Type: {routinetype}, Date: {date}")
                        sql_rounds = f"SELECT * FROM `round` WHERE `routine_id` = {routine_id}"
                        cursor.execute(sql_rounds)
                        rounds = cursor.fetchall()
                        for round_data in rounds:
                            exercise_name = round_data[0]
                            num_sets = round_data[2]
                            num_repetitions = round_data[3]
                            dispatcher.utter_message(f"Exercise: {exercise_name}, Sets: {num_sets}, Repetitions: {num_repetitions}")
                        dispatcher.utter_message("\n")
                else:
                    dispatcher.utter_message("You don't have any workout routine")
        finally:
            connection.close()
        return []

class DenyRoutineAction(Action):
    def name(self):
        return 'action_deny_routine'
    def run(self, dispatcher, tracker, domain):
        global name, bmi
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # 데이터베이스에서 사용자 정보 가져오기
                sql = f"SELECT * FROM `routine` WHERE `User_name` = '{name}' ORDER BY `date` DESC LIMIT 1"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    type_index = [i[0] for i in cursor.description].index('routinetype')
                    id_index = [i[0] for i in cursor.description].index('id')
                    date_index = [i[0] for i in cursor.description].index('date')
                    temp_type = result[type_index]
                    temp_id = result[id_index]
                    temp_date = result[date_index]
                    sql_delete_routine = f"DELETE FROM routine WHERE id = {temp_id}"
                    cursor.execute(sql_delete_routine)
                    dispatcher.utter_message(f"Okay, I'll recommand new {temp_type} routine at {temp_date}")
                    if temp_type == 'Chest':
                        new_id = self.insert_routine(cursor, 'Chest', temp_date)
                        self.find_exercise(cursor, 'Chest', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Biceps', new_id, dispatcher)
                    elif temp_type == 'Back':
                        new_id = self.insert_routine(cursor, 'Back', temp_date)
                        self.find_exercise(cursor, 'Back', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Triceps', new_id, dispatcher)
                    elif temp_type == 'Legs':
                        new_id = self.insert_routine(cursor, 'Legs', temp_date)
                        self.find_exercise(cursor, 'Legs', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Shoulders', new_id, dispatcher)
                else:
                    today_date = datetime.today().date()
                    dispatcher.utter_message(f"You don't have any workout routine. I'll recommand first at {today_date}.")
                    new_id = self.insert_routine(cursor, 'Chest', today_date)
                    self.find_exercise(cursor, 'Chest', new_id, dispatcher, today_date)
                    self.find_exercise_small(cursor, 'Biceps', new_id, dispatcher)
                connection.commit()
                self.find_exercise_cardio(cursor, dispatcher)
        finally:
            connection.close()
        return []
    def find_exercise(self, cursor, routinetype, new_id, dispatcher, date):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            exercises = [row[0] for row in result_exercise]
            dispatcher.utter_message(f"First, I'll recommand {routinetype}'s routine at {date}")
            for exercise_name in exercises:
                num_sets = random.randint(3, 5)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                elif num_sets == 5:
                    repetitions = 8
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_small(self, cursor, routinetype, new_id, dispatcher):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            dispatcher.utter_message(f"Second, I'll recommand {routinetype}'s routine")
            exercises = [row[0] for row in result_exercise]
            for exercise_name in exercises:
                num_sets = random.randint(3, 4)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_cardio(self, cursor, dispatcher):
        sql_exercise = "SELECT `name` FROM `exercise` WHERE `type` = 'Cardio' ORDER BY RAND() LIMIT 1"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchone()
        if result_exercise:
            exercise_name = result_exercise[0]
            if bmi > 25:
                dispatcher.utter_message(f"Since you are overweight, I recommend doing a lot of cardio. Here is My recommand cardio exercise")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 30 minutes.")
            elif bmi > 18.5:
                dispatcher.utter_message("Your BMI is normal. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 20 minutes.")
            else:
                dispatcher.utter_message("Your BMI is below normal. Adding cardio to your routine can be beneficial. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 15 minutes.")
    def insert_routine(self, cursor, type, date):
        insert_sql = f"INSERT INTO `routine` (`routinetype`,`User_name`, `date`) VALUES ('{type}', '{name}', '{date}')"
        cursor.execute(insert_sql)
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]

class UpdateRoutineAction(Action):
    def name(self):
        return 'action_update_routine'
    def run(self, dispatcher, tracker, domain):
        global name, bmi
        date = next(tracker.get_latest_entity_values("date"), None)
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        if date is None:
            dispatcher.utter_message("Try again.")
            return []
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # 데이터베이스에서 사용자 정보 가져오기
                sql = f"SELECT * FROM `routine` WHERE `User_name` = '{name}'and `date` = '{date}'"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    type_index = [i[0] for i in cursor.description].index('routinetype')
                    id_index = [i[0] for i in cursor.description].index('id')
                    date_index = [i[0] for i in cursor.description].index('date')
                    temp_type = result[type_index]
                    temp_id = result[id_index]
                    temp_date = result[date_index]
                    sql_delete_routine = f"DELETE FROM routine WHERE id = {temp_id}"
                    cursor.execute(sql_delete_routine)
                    dispatcher.utter_message(f"Okay, I'll update {temp_type} routine at {temp_date}")
                    if temp_type == 'Chest':
                        new_id = self.insert_routine(cursor, 'Chest', temp_date)
                        self.find_exercise(cursor, 'Chest', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Biceps', new_id, dispatcher)
                    elif temp_type == 'Back':
                        new_id = self.insert_routine(cursor, 'Back', temp_date)
                        self.find_exercise(cursor, 'Back', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Triceps', new_id, dispatcher)
                    elif temp_type == 'Legs':
                        new_id = self.insert_routine(cursor, 'Legs', temp_date)
                        self.find_exercise(cursor, 'Legs', new_id, dispatcher, temp_date)
                        self.find_exercise_small(cursor, 'Shoulders', new_id, dispatcher)
                    self.find_exercise_cardio(cursor, dispatcher)
                else:
                    dispatcher.utter_message(f"You don't have any workout routine at {date}.")
                connection.commit()
        finally:
            connection.close()
        return []
    def find_exercise(self, cursor, routinetype, new_id, dispatcher, date):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            exercises = [row[0] for row in result_exercise]
            dispatcher.utter_message(f"First, I'll recommand {routinetype}'s routine at {date}")
            for exercise_name in exercises:
                num_sets = random.randint(3, 5)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                elif num_sets == 5:
                    repetitions = 8
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_small(self, cursor, routinetype, new_id, dispatcher):
        num_exercises = random.randint(3, 4)
        sql_exercise = f"SELECT `name` FROM `exercise` WHERE `type` = '{routinetype}' ORDER BY RAND() LIMIT {num_exercises}"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchall()
        if result_exercise:
            dispatcher.utter_message(f"Second, I'll recommand {routinetype}'s routine")
            exercises = [row[0] for row in result_exercise]
            for exercise_name in exercises:
                num_sets = random.randint(3, 4)
                if num_sets == 3:
                    repetitions = 15
                elif num_sets == 4:
                    repetitions = 12
                insert_sql = f"INSERT INTO `round` (`exercise_name`, `routine_id`, `set`, `count`) VALUES ('{exercise_name}', {new_id}, {num_sets}, {repetitions})"
                cursor.execute(insert_sql)
                dispatcher.utter_message(f"For {exercise_name}, perform {num_sets} sets of {repetitions} repetitions.")
    def find_exercise_cardio(self, cursor, dispatcher):
        sql_exercise = "SELECT `name` FROM `exercise` WHERE `type` = 'Cardio' ORDER BY RAND() LIMIT 1"
        cursor.execute(sql_exercise)
        result_exercise = cursor.fetchone()
        if result_exercise:
            exercise_name = result_exercise[0]
            if bmi > 25:
                dispatcher.utter_message(f"Since you are overweight, I recommend doing a lot of cardio. Here is My recommand cardio exercise")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 30 minutes.")
            elif bmi > 18.5:
                dispatcher.utter_message("Your BMI is normal. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 20 minutes.")
            else:
                dispatcher.utter_message("Your BMI is below normal. Adding cardio to your routine can be beneficial. Here is a cardio exercise recommendation:")
                dispatcher.utter_message(f"For cardio, I recommend {exercise_name}. It's a great way to improve cardiovascular health. I suggest doing it for 15 minutes.")
    def insert_routine(self, cursor, type, date):
        insert_sql = f"INSERT INTO `routine` (`routinetype`,`User_name`, `date`) VALUES ('{type}', '{name}', '{date}')"
        cursor.execute(insert_sql)
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]

class CalAction(Action):
    def preprocess_measurement(self, measurement_str):
        if not isinstance(measurement_str, (str, bytes)):
            return None
        match = re.search(r'\d+(\.\d+)?', measurement_str)
        if match:
            return decimal.Decimal(match.group())
        return None
    def name(self):
        return 'action_recommand_diet'
    def run(self, dispatcher, tracker, domain):
        global name, bmi, weight
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        temp_kcal = next(tracker.get_latest_entity_values("calorie"), None)
        kcal = 0
        print(temp_kcal)
        if temp_kcal is not None:
            kcal = self.preprocess_measurement(temp_kcal)
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                today_date = datetime.today().strftime('%Y-%m-%d')
                sql_meal = f"SELECT * FROM `Meal` WHERE `date` = '{today_date}' and `User_name` = '{name}'"
                cursor.execute(sql_meal)
                result_meal = cursor.fetchone()
                if result_meal:
                    kcal_index = [i[0] for i in cursor.description].index('kcal')
                    id_index = [i[0] for i in cursor.description].index('id')
                    kcal += result_meal[kcal_index]
                    id = result_meal[id_index]
                    dispatcher.utter_message(f"You ate {kcal}kcal today.")
                    update_meal = f"UPDATE `Meal` SET `kcal` = {kcal} WHERE `id` = {id}"
                    cursor.execute(update_meal)
                else:
                    insert_meal = f"INSERT INTO `Meal` (`User_name`, `date`, `kcal`) VALUES ('{name}', '{today_date}', {kcal})"
                    cursor.execute(insert_meal)
                connection.commit()
                tot_kcal = self.calc_kcal(kcal, bmi, weight)
                carb, protein, fat = self.calc_nut(tot_kcal)
                meet = ['fork', 'beef', 'chicken']
                num_sets = random.randint(0,2)
                dispatcher.utter_message(f"You must eat {tot_kcal}kcal with {carb}g carbohydrate, {protein}g protein, {fat}g fat.")
                rice, chicken, amond = self.exchange(carb, protein, fat)
                dispatcher.utter_message(f"Ex) rice: {rice}g, {meet[num_sets]}: {chicken}g, amond: {amond}g.")
        finally:
            connection.close()
        return []
    def calc_kcal(self, kcal, bmi, weight):
        tot_kcal = weight * 33
        if bmi > 25:
            tot_kcal -= (300 + kcal)
        elif bmi > 18.5:
            tot_kcal -= kcal
        else:
            tot_kcal -= (kcal - 300)
        return tot_kcal
    def calc_nut(self, kcal):
        carb_ratio = decimal.Decimal('0.5')
        protein_ratio = decimal.Decimal('0.25')
        fat_ratio = decimal.Decimal('0.2')
        carb = (kcal * carb_ratio / 4).quantize(decimal.Decimal('0.00'))
        protein = (kcal * protein_ratio / 4).quantize(decimal.Decimal('0.00'))
        fat = (kcal * fat_ratio / 9).quantize(decimal.Decimal('0.00'))
        return carb, protein, fat
    def exchange(self, carb, protein, fat):
        chicken = decimal.Decimal('23')
        rice_carb = decimal.Decimal('75')
        rice_pro = decimal.Decimal('6')
        amond_pro = decimal.Decimal('6')
        amond_fat = decimal.Decimal('15')
        rice_cnt = (carb / rice_carb).quantize(decimal.Decimal('0.00'))
        protein -= rice_cnt * rice_pro
        amond_cnt = (fat / amond_fat).quantize(decimal.Decimal('0.00'))
        protein -= amond_cnt * amond_pro
        chicken_cnt = (protein / chicken).quantize(decimal.Decimal('0.00'))
        return rice_cnt * 210, chicken_cnt * 100, amond_cnt * 30

class showCalAction(Action):
    def name(self):
        return 'action_show_kcal'
    def run(self, dispatcher, tracker, domain):
        global name
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        kcal = 0
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                today_date = datetime.today().strftime('%Y-%m-%d')
                sql_meal = f"SELECT * FROM `Meal` WHERE `User_name` = '{name}' ORDER BY `date` DESC"
                cursor.execute(sql_meal)
                result_meals = cursor.fetchall()
                if result_meals:
                    for result_meal in result_meals:
                        kcal_index = [i[0] for i in cursor.description].index('kcal')
                        date_index = [i[0] for i in cursor.description].index('date')
                        kcal = result_meal[kcal_index]
                        date = result_meal[date_index]
                        dispatcher.utter_message(f"You ate {kcal}kcal at {date}.")
                else:
                    dispatcher.utter_message("You don't have any calorie intake")
        finally:
            connection.close()
        return []
class ShowInfoAction(Action):
    def name(self):
        return 'action_show_user_info'
    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        if name is None:
            dispatcher.utter_message("Please tell me your name")
            return []
        dispatcher.utter_message(f"Height: {height}cm")
        dispatcher.utter_message(f"Weight: {weight}kg")
        dispatcher.utter_message(f"BMI: {bmi}")
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                sql_routines = f"SELECT * FROM `routine` WHERE `User_name` = '{name}' ORDER BY `date` DESC"
                cursor.execute(sql_routines)
                recent_routines = cursor.fetchall()
                dispatcher.utter_message("================Workout routines================")
                if recent_routines:
                    for routine in recent_routines:
                        routine_id = routine[0]
                        routinetype = routine[1]
                        date = routine[2]
                        dispatcher.utter_message(f"Type: {routinetype}, Date: {date}")
                        sql_rounds = f"SELECT * FROM `round` WHERE `routine_id` = {routine_id}"
                        cursor.execute(sql_rounds)
                        rounds = cursor.fetchall()
                        for round_data in rounds:
                            exercise_name = round_data[0]
                            num_sets = round_data[2]
                            num_repetitions = round_data[3]
                            dispatcher.utter_message(f"Exercise: {exercise_name}, Sets: {num_sets}, Repetitions: {num_repetitions}")
                        dispatcher.utter_message("\n")
                else:
                    dispatcher.utter_message("You don't have any workout routine")
                sql_meal = f"SELECT * FROM `Meal` WHERE `User_name` = '{name}' ORDER BY `date` DESC"
                cursor.execute(sql_meal)
                result_meals = cursor.fetchall()
                dispatcher.utter_message("================Calories================")
                if result_meals:
                    for result_meal in result_meals:
                        kcal_index = [i[0] for i in cursor.description].index('kcal')
                        date_index = [i[0] for i in cursor.description].index('date')
                        kcal = result_meal[kcal_index]
                        date = result_meal[date_index]
                        dispatcher.utter_message(f"You ate {kcal}kcal at {date}.")
                else:
                    dispatcher.utter_message("You don't have any calorie intake")
        finally:
            connection.close()
            
class ByeAction(Action):
    def name(self):
        return 'action_goodbye'
    def run(self, dispatcher, tracker, domain):
        global name, height, weight, bmi
        if name is None:
            dispatcher.utter_message("Good bye!!")
            return []
        dispatcher.utter_message(f"Good bye {name}!!")
        name, height, weight, bmi = None, None, None, 0